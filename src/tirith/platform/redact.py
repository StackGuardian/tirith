"""
Slim and mask terraform documents before they leave the runner.

This runs client-side on purpose. Once bytes reach StackGuardian the exposure has already
happened, so masking on the server would be theatre. Everything here is a pure function over
parsed JSON so it can be tested exhaustively.

A caveat worth stating plainly, and repeated in the README: terraform's `*_sensitive` markers are
NOT exhaustive. A value that flows through `locals`, or comes from a provider that did not mark
its schema, arrives marked `false` and will not be masked by marker-driven redaction. Slimming and
the `variables` drop below exist partly to limit that blast radius.
"""

SENTINEL = "__SG_REDACTED__"

# Top-level plan sections tirith's terraform_plan provider never reads, verified against
# providers/terraform_plan/handler.py:
#
#   resource_changes   -> attribute / action / count operations
#   configuration      -> direct_dependencies, direct_references, provider_config  (KEPT)
#   terraform_version  -> terraform_version operation
#
# `planned_values` is the dangerous one. It mirrors every resource's values in a second place and
# carries NO sensitivity markers of its own, so marker-driven redaction of `resource_changes`
# leaves the same secret in plaintext here. Dropping it is lossless for evaluation and closes that
# hole; a real plan leaked a `local_sensitive_file` body through exactly this path.
SLIM_DROP_KEYS = ("prior_state", "planned_values")

# Provider blocks whose `expressions` can hold hardcoded credentials. `configuration` cannot be
# dropped wholesale -- three tirith operations read it -- so the credential-bearing part is
# scrubbed instead, keeping the two fields provider_config_operator actually consults.
_PROVIDER_CONFIG_KEEP = ("name", "full_name", "version_constraint", "module_address", "alias")


def slim_plan(plan):
    """
    Drop plan sections that are irrelevant to evaluation.

    Typically removes 60-90% of the bytes. `configuration` is deliberately retained but scrubbed
    (see `_scrub_configuration`), because dropping it would silently break the
    `direct_dependencies`, `direct_references` and `provider_config` operations -- policies would
    stop finding what they are looking for rather than failing loudly.
    """
    if not isinstance(plan, dict):
        return plan

    slimmed = {k: v for k, v in plan.items() if k not in SLIM_DROP_KEYS}
    if isinstance(slimmed.get("configuration"), dict):
        slimmed["configuration"] = _scrub_configuration(slimmed["configuration"])
    return slimmed


def _scrub_configuration(configuration):
    """
    Strip credential-bearing expressions from `configuration` while keeping what tirith reads.

    Two places hold literals, and both have to be scrubbed:

    `provider_config[].expressions` -- `provider_config_operator` reads only `version_constraint`
    and `expressions.region.constant_value`, so access keys, tokens and assume-role blocks can go.

    `root_module.resources[].expressions[].constant_value` -- every literal written in the HCL,
    including a hardcoded password. This is a third instance of the `planned_values` pattern: a
    place values live that carries no sensitivity markers, so marker-driven masking of
    `resource_changes` never touches it. Caught in QA -- a `local_sensitive_file` body was masked
    in `resource_changes` and sat in plaintext here in the same document.

    Dropping `constant_value` is lossless: `direct_references_operator` reads only `references`
    from these expressions, and `direct_dependencies_operator` reads only `depends_on`
    (providers/terraform_plan/handler.py:329, :385-388).
    """
    scrubbed = dict(configuration)

    provider_config = scrubbed.get("provider_config")
    if isinstance(provider_config, dict):
        cleaned = {}
        for name, block in provider_config.items():
            if not isinstance(block, dict):
                cleaned[name] = block
                continue
            kept = {k: v for k, v in block.items() if k in _PROVIDER_CONFIG_KEEP}
            region = (block.get("expressions") or {}).get("region")
            if region is not None:
                kept["expressions"] = {"region": region}
            cleaned[name] = kept
        scrubbed["provider_config"] = cleaned

    root_module = scrubbed.get("root_module")
    if isinstance(root_module, dict):
        scrubbed["root_module"] = _scrub_config_module(root_module)

    return scrubbed


def _scrub_config_module(module):
    """Recursively drop literal values from a configuration module, keeping the reference graph."""
    scrubbed = dict(module)

    resources = scrubbed.get("resources")
    if isinstance(resources, list):
        scrubbed["resources"] = [_scrub_config_resource(r) for r in resources]

    # Child modules nest the same shape under module_calls[].module.
    module_calls = scrubbed.get("module_calls")
    if isinstance(module_calls, dict):
        calls = {}
        for name, call in module_calls.items():
            if isinstance(call, dict) and isinstance(call.get("module"), dict):
                call = {**call, "module": _scrub_config_module(call["module"])}
                # A module's own arguments are literals too.
                call.pop("expressions", None)
            calls[name] = call
        scrubbed["module_calls"] = calls

    # Variable defaults and output values are literals with no operation reading them.
    for section in ("variables", "outputs"):
        if isinstance(scrubbed.get(section), dict):
            scrubbed[section] = _scrub_config_section(scrubbed[section])

    return scrubbed


def _scrub_config_resource(resource):
    if not isinstance(resource, dict):
        return resource

    expressions = resource.get("expressions")
    if not isinstance(expressions, dict):
        return resource

    return {**resource, "expressions": {k: _keep_references(v) for k, v in expressions.items()}}


def _keep_references(expression):
    """
    Reduce one expression to just its `references`, dropping every literal.

    Terraform nests expressions arbitrarily: a block argument is a dict of expressions, and a
    repeated block is a list of them, so this recurses rather than looking one level deep.
    """
    if isinstance(expression, list):
        return [_keep_references(item) for item in expression]
    if not isinstance(expression, dict):
        return expression
    if "references" in expression or "constant_value" in expression:
        # A leaf: keep only the reference graph.
        return {"references": expression["references"]} if "references" in expression else {}
    return {k: _keep_references(v) for k, v in expression.items()}


def _scrub_config_section(section):
    """Drop `default` / `expression` literals from variables and outputs."""
    cleaned = {}
    for name, entry in section.items():
        if isinstance(entry, dict):
            entry = {k: v for k, v in entry.items() if k not in ("default", "expression", "value")}
        cleaned[name] = entry
    return cleaned


def _mask_by_marker(value, marker):
    """
    Walk `value` alongside terraform's parallel sensitivity structure `marker`.

    A marker node of `true` masks the whole subtree beneath it. Dicts and lists are walked in
    lockstep; anything else is returned untouched.
    """
    if marker is True:
        return SENTINEL

    if isinstance(marker, dict) and isinstance(value, dict):
        return {k: _mask_by_marker(v, marker.get(k)) for k, v in value.items()}

    if isinstance(marker, list) and isinstance(value, list):
        # Terraform emits a marker list positionally aligned with the value list. A shorter
        # marker list means the tail is not sensitive.
        return [_mask_by_marker(item, marker[i] if i < len(marker) else None) for i, item in enumerate(value)]

    return value


def redact_plan(plan):
    """
    Slim, then mask every value terraform flagged sensitive, then drop root `variables`.

    `variables` goes wholesale because the plan does not reliably mark which root variables were
    declared `sensitive = true` -- so the only safe assumption is that all of them might be.
    """
    plan = slim_plan(plan)
    if not isinstance(plan, dict):
        return plan

    redacted = dict(plan)
    redacted.pop("variables", None)

    resource_changes = redacted.get("resource_changes")
    if isinstance(resource_changes, list):
        masked_changes = []
        for resource_change in resource_changes:
            if not isinstance(resource_change, dict):
                masked_changes.append(resource_change)
                continue

            masked = dict(resource_change)
            change = masked.get("change")
            if isinstance(change, dict):
                masked_change = dict(change)
                for value_key, marker_key in (("before", "before_sensitive"), ("after", "after_sensitive")):
                    if value_key in masked_change:
                        masked_change[value_key] = _mask_by_marker(
                            masked_change[value_key], masked_change.get(marker_key)
                        )
                masked["change"] = masked_change
            masked_changes.append(masked)
        redacted["resource_changes"] = masked_changes

    output_changes = redacted.get("output_changes")
    if isinstance(output_changes, dict):
        redacted["output_changes"] = {name: _redact_output_change(change) for name, change in output_changes.items()}

    return redacted


def _redact_output_change(change):
    """
    Mask a sensitive output's before/after values.

    Terraform spells the marker differently across versions: older plans carry a single
    `sensitive`, newer ones carry `before_sensitive` / `after_sensitive` per side. Checking only
    `sensitive` silently missed every modern plan, so all three are honoured -- and each side is
    masked independently, since an output can become sensitive without having been so before.

    Only keys that are actually present are replaced. Adding an `after` to a create whose value is
    still unknown (`after_unknown: true`) would invent data the plan never contained.
    """
    if not isinstance(change, dict):
        return change

    masked = dict(change)
    whole = bool(change.get("sensitive"))

    for side in ("before", "after"):
        if side not in masked:
            continue
        if whole or change.get(f"{side}_sensitive") is True:
            masked[side] = SENTINEL

    return masked


def redact_state(state):
    """
    Mask a terraform state document.

    State is more dangerous than a plan: it holds every resource attribute in plaintext, including
    values no plan would surface. Two rules, matching what the platform's terraform step applies:

      - `outputs[k].sensitive` is true  -> replace that output's value
      - each key named in an instance's `sensitive_attributes` -> replace that attribute

    Expects the raw state shape (top-level `resources` / `outputs`), not `terraform show -json`
    output, which nests resources under `values.root_module.resources`.
    """
    if not isinstance(state, dict):
        return state

    redacted = dict(state)

    outputs = redacted.get("outputs")
    if isinstance(outputs, dict):
        masked_outputs = {}
        for name, output in outputs.items():
            if isinstance(output, dict) and output.get("sensitive"):
                masked_outputs[name] = {**output, "value": SENTINEL}
            else:
                masked_outputs[name] = output
        redacted["outputs"] = masked_outputs

    resources = redacted.get("resources")
    if isinstance(resources, list):
        redacted["resources"] = [_redact_state_resource(r) for r in resources]

    return redacted


def _redact_state_resource(resource):
    if not isinstance(resource, dict):
        return resource

    instances = resource.get("instances")
    if not isinstance(instances, list):
        return resource

    masked_instances = []
    for instance in instances:
        if not isinstance(instance, dict):
            masked_instances.append(instance)
            continue

        masked = dict(instance)
        attributes = masked.get("attributes")
        sensitive_attributes = masked.get("sensitive_attributes") or []

        if isinstance(attributes, dict) and sensitive_attributes:
            masked_attributes = dict(attributes)
            for sensitive_attribute in sensitive_attributes:
                # Terraform writes these either as {"type": "get_attr", "value": "<key>"} or,
                # in older state versions, as a bare string.
                key = sensitive_attribute.get("value") if isinstance(sensitive_attribute, dict) else sensitive_attribute
                if isinstance(key, str) and key in masked_attributes:
                    masked_attributes[key] = SENTINEL
            masked["attributes"] = masked_attributes

        masked_instances.append(masked)

    return {**resource, "instances": masked_instances}


def count_redactions(document):
    """Count sentinel occurrences, for the attestation the action sends with the upload."""
    if isinstance(document, dict):
        return sum(count_redactions(v) for v in document.values())
    if isinstance(document, list):
        return sum(count_redactions(v) for v in document)
    return 1 if document == SENTINEL else 0
