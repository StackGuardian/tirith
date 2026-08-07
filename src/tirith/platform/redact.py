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

import copy

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
            if isinstance(call, dict):
                if isinstance(call.get("module"), dict):
                    call = {**call, "module": _scrub_config_module(call["module"])}
                else:
                    call = dict(call)
                # A module's own arguments are literals too. Dropped whether or not the call
                # carries an inlined `module` body -- it did not when the module came from a
                # registry or a git source, which is the common case, and the arguments passed to
                # it are literals either way.
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

    scrubbed = dict(resource)

    expressions = scrubbed.get("expressions")
    if isinstance(expressions, dict):
        scrubbed["expressions"] = {k: _keep_references(v) for k, v in expressions.items()}

    # A provisioner carries its own expressions one level down -- `connection.password`, and the
    # `inline` script itself. Scrubbing only the resource's own expressions left those verbatim,
    # and a provisioner block is exactly where a password tends to be written literally.
    provisioners = scrubbed.get("provisioners")
    if isinstance(provisioners, list):
        scrubbed["provisioners"] = [_scrub_config_resource(p) for p in provisioners]

    # count/for_each are expressions in their own right, and a `for_each` over a map of literals
    # carries those literals.
    for key in ("count_expression", "for_each_expression"):
        if key in scrubbed:
            scrubbed[key] = _keep_references(scrubbed[key])

    return scrubbed


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


def _mask_resource_change(resource_change):
    """Mask one `resource_changes`/`resource_drift` entry by its own before/after markers."""
    if not isinstance(resource_change, dict):
        return resource_change

    masked = dict(resource_change)
    change = masked.get("change")
    if isinstance(change, dict):
        masked_change = dict(change)
        for value_key, marker_key in (("before", "before_sensitive"), ("after", "after_sensitive")):
            if value_key in masked_change:
                masked_change[value_key] = _mask_by_marker(masked_change[value_key], masked_change.get(marker_key))
        masked["change"] = masked_change
    return masked


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

    # resource_drift has the same shape and the same sensitivity markers as resource_changes, and
    # terraform emits it whenever a refresh finds drift -- so a masked resource_changes sitting
    # beside an unmasked resource_drift shipped the same secret in plaintext one key away.
    for section in ("resource_changes", "resource_drift"):
        entries = redacted.get(section)
        if isinstance(entries, list):
            redacted[section] = [_mask_resource_change(entry) for entry in entries]

    output_changes = redacted.get("output_changes")
    if isinstance(output_changes, dict):
        redacted["output_changes"] = {name: _redact_output_change(change) for name, change in output_changes.items()}

    # Rebuild planned_values from what we just masked. slim_plan dropped terraform's own copy
    # because it carries no sensitivity markers; this one is derived from the masked
    # resource_changes, so it holds the same redacted values.
    planned_values = rebuild_planned_values(redacted.get("resource_changes"))
    if planned_values:
        redacted["planned_values"] = planned_values

    return redacted


def rebuild_planned_values(masked_resource_changes):
    """
    Reconstruct `planned_values` from already-masked `resource_changes`.

    Infracost and Checkov both read `planned_values` and nothing else -- give them a plan without
    it and they return a clean, empty, entirely wrong answer. Measured against infracost 0.10.27
    with a real API key: the same t3.medium prices at $39.80 with the key present and $0.00
    without, differing only by this one section.

    Terraform's own copy cannot be shipped: it mirrors every value with NO sensitivity markers, so
    masking `resource_changes` leaves the same secret in plaintext there -- a real plan leaked a
    `local_sensitive_file` body through exactly that path. This rebuild sidesteps that because it
    reads the *masked* values, after `_mask_by_marker` has run over them.

    Only `after` is used, and only for resources that will exist. A destroy has no planned value,
    and `before` is the pre-change state that `prior_state` carries -- which is dropped for the
    same marker-less reason.
    """
    if not isinstance(masked_resource_changes, list):
        return None

    root = {"resources": [], "child_modules": []}
    modules = {}

    for resource_change in masked_resource_changes:
        if not isinstance(resource_change, dict):
            continue
        change = resource_change.get("change")
        if not isinstance(change, dict):
            continue
        if "delete" in (change.get("actions") or []) and "create" not in (change.get("actions") or []):
            # Nothing is planned to exist, so there is nothing to price or scan.
            continue
        after = change.get("after")
        if after is None:
            continue

        resource = {
            key: resource_change[key]
            for key in ("address", "mode", "type", "name", "index", "provider_name")
            if key in resource_change
        }
        resource["values"] = after

        module_address = resource_change.get("module_address")
        if module_address:
            modules.setdefault(module_address, {"address": module_address, "resources": []})["resources"].append(
                resource
            )
        else:
            root["resources"].append(resource)

    if modules:
        # Flat rather than a true nesting tree. Verified equivalent for pricing, and both tools
        # address resources by their full `address`, which already encodes the module path.
        root["child_modules"] = sorted(modules.values(), key=lambda m: m["address"])
    else:
        root.pop("child_modules")

    if not root["resources"] and not root.get("child_modules"):
        return None

    return {"root_module": root}


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
            masked_attributes = copy.deepcopy(attributes)
            for sensitive_attribute in sensitive_attributes:
                _mask_attribute_path(masked_attributes, _attribute_steps(sensitive_attribute))
            masked["attributes"] = masked_attributes

        masked_instances.append(masked)

    return {**resource, "instances": masked_instances}


def _attribute_steps(sensitive_attribute):
    """
    Normalise one `sensitive_attributes` entry into a list of path steps.

    Terraform writes each entry as a PATH -- a list of steps -- not a single key:

        [[{"type": "get_attr", "value": "content_base64"}],
         [{"type": "get_attr", "value": "content"}]]

    Reading only the flat forms silently masked nothing at all on real state, because a list is
    neither a dict nor a string. Verified against `terraform state pull` output for a
    `local_sensitive_file`; the earlier unit tests passed only because their fixture invented the
    flat shape.

    The two flat forms are still accepted: some providers and older state versions emit them.
    """
    if isinstance(sensitive_attribute, list):
        entries = sensitive_attribute
    else:
        entries = [sensitive_attribute]

    steps = []
    for entry in entries:
        if isinstance(entry, dict):
            steps.append(entry.get("value"))
        elif isinstance(entry, (str, int)):
            steps.append(entry)
        else:
            # An unrecognised step means the path cannot be trusted; masking a guessed location
            # would be worse than reporting nothing.
            return []
    return steps


def _mask_attribute_path(container, steps):
    """
    Replace the value at `steps` within `container` with the sentinel.

    A path may descend through nested objects and list indices -- `[{"get_attr": "config"},
    {"index": 0}, {"get_attr": "token"}]` -- so this walks rather than assuming one level.
    """
    if not steps:
        return

    *parents, leaf = steps
    node = container
    for step in parents:
        if isinstance(node, dict) and step in node:
            node = node[step]
        elif isinstance(node, list) and isinstance(step, int) and 0 <= step < len(node):
            node = node[step]
        else:
            return

    if isinstance(node, dict) and leaf in node:
        node[leaf] = SENTINEL
    elif isinstance(node, list) and isinstance(leaf, int) and 0 <= leaf < len(node):
        node[leaf] = SENTINEL


def count_redactions(document):
    """Count sentinel occurrences, for the attestation the action sends with the upload."""
    if isinstance(document, dict):
        return sum(count_redactions(v) for v in document.values())
    if isinstance(document, list):
        return sum(count_redactions(v) for v in document)
    return 1 if document == SENTINEL else 0
