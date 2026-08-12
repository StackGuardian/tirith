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


# A value shorter than this is not swept. `_sweep_known_secrets` replaces exact string matches
# everywhere, and a two-character secret would also match ids, regions and resource names -- mangling
# the document the policies then evaluate. A real credential is longer than this; a two-character one
# that leaks is the lesser harm against breaking every policy on the plan.
MIN_SWEPT_SECRET_LENGTH = 6


def _collect_sensitive_values(value, marker, found):
    """Gather the plaintext strings terraform marked sensitive, so they can be swept elsewhere."""
    if marker is True:
        if isinstance(value, str) and len(value) >= MIN_SWEPT_SECRET_LENGTH:
            found.add(value)
        elif isinstance(value, (dict, list)):
            _collect_all_strings(value, found)
        return

    if isinstance(marker, dict) and isinstance(value, dict):
        for key, item in value.items():
            _collect_sensitive_values(item, marker.get(key), found)
    elif isinstance(marker, list) and isinstance(value, list):
        for index, item in enumerate(value):
            _collect_sensitive_values(item, marker[index] if index < len(marker) else None, found)


def _collect_all_strings(node, found):
    """Every string under a subtree terraform marked sensitive wholesale."""
    if isinstance(node, dict):
        for item in node.values():
            _collect_all_strings(item, found)
    elif isinstance(node, list):
        for item in node:
            _collect_all_strings(item, found)
    elif isinstance(node, str) and len(node) >= MIN_SWEPT_SECRET_LENGTH:
        found.add(node)


def _sweep_known_secrets(node, secrets):
    """
    Replace any value terraform told us was sensitive *somewhere* with the sentinel *everywhere*.

    The markers alone are not enough. A provider that computes a mirror of an attribute does not
    inherit its sensitivity: an `aws_instance` with a sensitive value in `tags` is marked
    `after_sensitive.tags.Password = true`, while `after_sensitive.tags_all` comes back `{}` even
    though `tags_all` holds the identical plaintext. Every AWS resource with tags has `tags_all`, so
    that single gap leaks any secret ever used in a tag.

    Caught by an end-to-end test that downloaded the uploaded bundle and grepped it, not by the unit
    suite -- which asserted the markers were honoured, and they were.

    Exact string matches only: it cannot know that a *substring* is the secret without guessing, and a
    guess here corrupts the document the policies read.
    """
    if not secrets:
        return node
    if isinstance(node, dict):
        return {k: _sweep_known_secrets(v, secrets) for k, v in node.items()}
    if isinstance(node, list):
        return [_sweep_known_secrets(item, secrets) for item in node]
    if isinstance(node, str) and node in secrets:
        return SENTINEL
    return node


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

    # Collect the sensitive plaintext BEFORE masking replaces it, and before `variables` is dropped --
    # a sensitive root variable is often the origin of the value that reappears elsewhere unmarked.
    secrets = set()
    for section in ("resource_changes", "resource_drift"):
        for entry in redacted.get(section) or []:
            change = (entry or {}).get("change") if isinstance(entry, dict) else None
            if isinstance(change, dict):
                for value_key, marker_key in (("before", "before_sensitive"), ("after", "after_sensitive")):
                    _collect_sensitive_values(change.get(value_key), change.get(marker_key), secrets)
    for name, variable in (redacted.get("variables") or {}).items():
        if isinstance(variable, dict):
            _collect_all_strings(variable.get("value"), secrets)

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

    # Last, over the whole document: anything terraform called sensitive somewhere is masked
    # everywhere, including the unmarked provider-computed mirrors the markers miss.
    return _sweep_known_secrets(redacted, secrets)


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

    Handles BOTH shapes a caller can plausibly hand us:

      - the raw state (`terraform state pull`): top-level `resources` / `outputs`, with each
        instance naming its own `sensitive_attributes`;
      - `terraform show -json <state>`: resources nested under `values.root_module.resources`, with
        sensitivity carried in a parallel `sensitive_values` tree.

    Handling only the first was a silent leak. The function returned the document unchanged for the
    second -- no error, no warning -- so a state produced with `show -json`, which is the natural
    way to get a readable one, shipped every attribute in plaintext. Caught by an end-to-end run,
    not by a unit test, because the unit tests all used the shape the code already understood.
    """
    if not isinstance(state, dict):
        return state

    redacted = dict(state)

    # Every plaintext we are about to mask, collected as we go and swept from the whole document at the
    # end -- the same two-pass shape as redact_plan, and for the same reason.
    #
    # Marker-driven masking alone is not enough, because a provider writes computed *mirrors* of an
    # attribute with no sensitivity marker of their own. The confirmed case is `tags_all`: a secret in
    # `tags.Password` is masked there and shipped in plaintext one key away. A pen test found this exact
    # hole in state after the equivalent had been closed for plans -- and state is the worse place for
    # it, since state carries every attribute of every resource and the bundle is retained.
    secrets = set()

    values = redacted.get("values")
    if isinstance(values, dict):
        redacted["values"] = _redact_show_json_values(values, secrets)

    outputs = redacted.get("outputs")
    if isinstance(outputs, dict):
        masked_outputs = {}
        for name, output in outputs.items():
            if isinstance(output, dict) and output.get("sensitive"):
                _collect_all_strings(output.get("value"), secrets)
                masked_outputs[name] = {**output, "value": SENTINEL}
            else:
                masked_outputs[name] = output
        redacted["outputs"] = masked_outputs

    resources = redacted.get("resources")
    if isinstance(resources, list):
        redacted["resources"] = [_redact_state_resource(r, secrets) for r in resources]

    return _sweep_known_secrets(redacted, secrets)


def _redact_show_json_values(values, secrets=None):
    """
    Mask the `values` tree of `terraform show -json <state>` output.

    Same marker convention as a plan: a parallel `sensitive_values` tree whose truthy leaves name
    the attributes to replace, so _mask_by_marker does the work. Recurses through child_modules,
    since a module's resources are nested rather than flattened.
    """
    if not isinstance(values, dict):
        return values

    if secrets is None:
        secrets = set()

    masked = dict(values)
    root = masked.get("root_module")
    if isinstance(root, dict):
        masked["root_module"] = _redact_show_json_module(root, secrets)

    outputs = masked.get("outputs")
    if isinstance(outputs, dict):
        masked_outputs = {}
        for name, o in outputs.items():
            if isinstance(o, dict) and o.get("sensitive"):
                _collect_all_strings(o.get("value"), secrets)
                masked_outputs[name] = {**o, "value": SENTINEL}
            else:
                masked_outputs[name] = o
        masked["outputs"] = masked_outputs
    return masked


def _redact_show_json_module(module, secrets=None):
    if not isinstance(module, dict):
        return module

    if secrets is None:
        secrets = set()

    masked = dict(module)

    resources = masked.get("resources")
    if isinstance(resources, list):
        out = []
        for resource in resources:
            if not isinstance(resource, dict):
                out.append(resource)
                continue
            entry = dict(resource)
            if "values" in entry:
                # Collect before masking. The marker convention here is identical to a plan's, so this
                # is the same call redact_plan makes over `change.before` / `change.after`.
                _collect_sensitive_values(entry["values"], entry.get("sensitive_values"), secrets)
                entry["values"] = _mask_by_marker(entry["values"], entry.get("sensitive_values"))
            out.append(entry)
        masked["resources"] = out

    children = masked.get("child_modules")
    if isinstance(children, list):
        masked["child_modules"] = [_redact_show_json_module(c, secrets) for c in children]

    return masked


def _redact_state_resource(resource, secrets=None):
    if not isinstance(resource, dict):
        return resource

    if secrets is None:
        secrets = set()

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
                steps = _attribute_steps(sensitive_attribute)
                # Read from the untouched original, not from the copy being masked: once the first path
                # is masked the copy holds the sentinel there, and sweeping for that would do nothing.
                plaintext = _read_attribute_path(attributes, steps)
                if plaintext is not _ABSENT:
                    _collect_all_strings(plaintext, secrets)
                _mask_attribute_path(masked_attributes, steps)
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


_ABSENT = object()


def _read_attribute_path(container, steps):
    """
    Return the value at `steps` within `container`, or `_ABSENT`.

    The mirror of `_mask_attribute_path` below, and deliberately the same walk: the two have to agree
    on what a path means, or the sweep collects a different value from the one that was masked.
    """
    if not steps:
        return _ABSENT

    node = container
    for step in steps:
        if isinstance(node, dict) and step in node:
            node = node[step]
        elif isinstance(node, list) and isinstance(step, int) and 0 <= step < len(node):
            node = node[step]
        else:
            return _ABSENT
    return node


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
