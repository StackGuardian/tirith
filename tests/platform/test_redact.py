"""
Tests for plan/state redaction.

This is the security-critical module: it is the only thing standing between a customer's secrets
and StackGuardian's storage. The tests assert on the *serialized bytes* wherever a leak would
matter, because a value nested somewhere unexpected still leaks even if the top-level shape looks
masked.
"""

import json
import os
import sys


from tirith.platform import redact

SECRET = "hunter2-this-must-never-leave-the-runner"


def test_slim_drops_prior_state_and_planned_values():
    """
    `planned_values` is the important one. It mirrors every resource's values in a second place
    and carries NO sensitivity markers, so masking `resource_changes` alone leaves the same secret
    in plaintext there. A real plan leaked a local_sensitive_file body through exactly this path.
    """
    plan = {
        "format_version": "1.2",
        "terraform_version": "1.5.7",
        "resource_changes": [],
        "prior_state": {"values": {"secret": SECRET}},
        "planned_values": {"root_module": {"resources": [{"values": {"content": SECRET}}]}},
    }

    slimmed = redact.slim_plan(plan)

    assert "prior_state" not in slimmed
    assert "planned_values" not in slimmed
    assert slimmed["resource_changes"] == []
    assert slimmed["terraform_version"] == "1.5.7"
    assert SECRET not in json.dumps(slimmed)


def test_planned_values_leak_is_closed_end_to_end():
    """The exact shape that leaked in QA: masked in resource_changes, plaintext in planned_values."""
    plan = {
        "resource_changes": [
            {
                "type": "local_sensitive_file",
                "change": {"after": {"content": SECRET}, "after_sensitive": {"content": True}},
            }
        ],
        "planned_values": {
            "root_module": {"resources": [{"type": "local_sensitive_file", "values": {"content": SECRET}}]}
        },
    }

    redacted = redact.redact_plan(plan)

    assert SECRET not in json.dumps(redacted)


def test_configuration_is_kept_because_three_operations_read_it():
    """
    Dropping `configuration` would silently break direct_dependencies, direct_references and
    provider_config: policies would stop finding what they look for rather than failing loudly.
    """
    plan = {
        "resource_changes": [],
        "configuration": {
            "root_module": {"resources": [{"address": "aws_vpc.main", "depends_on": ["aws_x.y"]}]},
            "provider_config": {
                "aws": {
                    "name": "aws",
                    "full_name": "registry.terraform.io/hashicorp/aws",
                    "version_constraint": "~> 5.0",
                    "expressions": {
                        "region": {"constant_value": "eu-central-1"},
                        "secret_key": {"constant_value": SECRET},
                        "assume_role": {"role_arn": {"constant_value": SECRET}},
                    },
                }
            },
        },
    }

    slimmed = redact.slim_plan(plan)
    aws = slimmed["configuration"]["provider_config"]["aws"]

    # What the provider_config operation reads survives ...
    assert aws["full_name"] == "registry.terraform.io/hashicorp/aws"
    assert aws["version_constraint"] == "~> 5.0"
    assert aws["expressions"]["region"]["constant_value"] == "eu-central-1"
    # ... and the reference graph the other two operations walk survives ...
    assert slimmed["configuration"]["root_module"]["resources"][0]["depends_on"] == ["aws_x.y"]
    # ... while hardcoded credentials do not.
    assert "secret_key" not in aws["expressions"]
    assert "assume_role" not in aws["expressions"]
    assert SECRET not in json.dumps(slimmed)


def test_hcl_literals_are_scrubbed_from_resource_expressions():
    """
    The third instance of the `planned_values` pattern, caught in QA: a hardcoded value is masked
    in `resource_changes` and sits in plaintext under
    `configuration.root_module.resources[].expressions[].constant_value`, which carries no
    sensitivity markers at all.

    Dropping it is lossless -- direct_references reads only `references`, direct_dependencies only
    `depends_on`.
    """
    plan = {
        "resource_changes": [
            {
                "type": "local_sensitive_file",
                "change": {"after": {"content": SECRET}, "after_sensitive": {"content": True}},
            }
        ],
        "configuration": {
            "root_module": {
                "resources": [
                    {
                        "address": "local_sensitive_file.creds",
                        "depends_on": ["null_resource.a"],
                        "expressions": {
                            "content": {"constant_value": SECRET},
                            "filename": {"references": ["path.module"]},
                        },
                    }
                ]
            }
        },
    }

    redacted = redact.redact_plan(plan)
    expressions = redacted["configuration"]["root_module"]["resources"][0]["expressions"]

    assert SECRET not in json.dumps(redacted)
    # The reference graph the operations walk survives ...
    assert expressions["filename"]["references"] == ["path.module"]
    assert redacted["configuration"]["root_module"]["resources"][0]["depends_on"] == ["null_resource.a"]
    # ... the literal does not.
    assert "constant_value" not in expressions["content"]


def test_nested_and_repeated_block_literals_are_scrubbed():
    """A block argument is a dict of expressions and a repeated block is a list of them."""
    plan = {
        "resource_changes": [],
        "configuration": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_instance.web",
                        "expressions": {
                            "root_block_device": {"kms_key_id": {"constant_value": SECRET}},
                            "ebs_block_device": [
                                {"snapshot_id": {"constant_value": SECRET}},
                                {"volume_id": {"references": ["aws_ebs_volume.a.id"]}},
                            ],
                        },
                    }
                ]
            }
        },
    }

    redacted = redact.redact_plan(plan)

    assert SECRET not in json.dumps(redacted)
    ebs = redacted["configuration"]["root_module"]["resources"][0]["expressions"]["ebs_block_device"]
    assert ebs[1]["volume_id"]["references"] == ["aws_ebs_volume.a.id"]


def test_child_module_literals_are_scrubbed():
    plan = {
        "resource_changes": [],
        "configuration": {
            "root_module": {
                "module_calls": {
                    "db": {
                        "source": "./modules/db",
                        "expressions": {"password": {"constant_value": SECRET}},
                        "module": {
                            "resources": [
                                {
                                    "address": "aws_db_instance.main",
                                    "expressions": {"password": {"constant_value": SECRET}},
                                }
                            ]
                        },
                    }
                }
            }
        },
    }

    redacted = redact.redact_plan(plan)

    assert SECRET not in json.dumps(redacted)


def test_variable_defaults_and_outputs_are_scrubbed():
    """A `default` on a sensitive variable is a literal in the configuration too."""
    plan = {
        "resource_changes": [],
        "configuration": {
            "root_module": {
                "variables": {"db_password": {"default": SECRET, "sensitive": True}},
                "outputs": {"conn": {"expression": {"constant_value": SECRET}}},
            }
        },
    }

    redacted = redact.redact_plan(plan)

    assert SECRET not in json.dumps(redacted)
    # The declaration itself survives; only the value goes.
    assert redacted["configuration"]["root_module"]["variables"]["db_password"]["sensitive"] is True


def test_scrub_tolerates_a_provider_config_without_expressions():
    plan = {"resource_changes": [], "configuration": {"provider_config": {"null": {"name": "null"}}}}

    slimmed = redact.slim_plan(plan)

    assert slimmed["configuration"]["provider_config"]["null"] == {"name": "null"}


def test_redact_masks_marked_attributes():
    plan = {
        "resource_changes": [
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"identifier": "main", "password": SECRET, "port": 5432},
                    "after_sensitive": {"password": True},
                },
            }
        ]
    }

    redacted = redact.redact_plan(plan)
    after = redacted["resource_changes"][0]["change"]["after"]

    assert after["password"] == redact.SENTINEL
    assert after["identifier"] == "main", "non-sensitive values must survive"
    assert after["port"] == 5432
    assert SECRET not in json.dumps(redacted)


def test_redact_masks_a_whole_sensitive_subtree():
    """A marker of `true` above an object masks everything beneath it."""
    plan = {
        "resource_changes": [
            {
                "address": "aws_secretsmanager_secret_version.v",
                "change": {
                    "after": {"secret_string": {"user": "admin", "pass": SECRET}},
                    "after_sensitive": {"secret_string": True},
                },
            }
        ]
    }

    redacted = redact.redact_plan(plan)

    assert redacted["resource_changes"][0]["change"]["after"]["secret_string"] == redact.SENTINEL
    assert SECRET not in json.dumps(redacted)


def test_redact_masks_inside_lists_positionally():
    plan = {
        "resource_changes": [
            {
                "change": {
                    "after": {"items": [{"k": "public"}, {"k": SECRET}]},
                    "after_sensitive": {"items": [{}, {"k": True}]},
                }
            }
        ]
    }

    redacted = redact.redact_plan(plan)
    items = redacted["resource_changes"][0]["change"]["after"]["items"]

    assert items[0]["k"] == "public"
    assert items[1]["k"] == redact.SENTINEL
    assert SECRET not in json.dumps(redacted)


def test_redact_masks_before_as_well_as_after():
    """A destroy or update leaves the old secret in `before`; it leaks just as badly."""
    plan = {
        "resource_changes": [
            {
                "change": {
                    "actions": ["delete"],
                    "before": {"password": SECRET},
                    "before_sensitive": {"password": True},
                    "after": None,
                }
            }
        ]
    }

    redacted = redact.redact_plan(plan)

    assert redacted["resource_changes"][0]["change"]["before"]["password"] == redact.SENTINEL
    assert SECRET not in json.dumps(redacted)


def test_redact_drops_root_variables_entirely():
    """
    The plan does not reliably mark which root variables were declared sensitive, so the only safe
    assumption is that any of them might be.
    """
    plan = {"resource_changes": [], "variables": {"db_password": {"value": SECRET}}}

    redacted = redact.redact_plan(plan)

    assert "variables" not in redacted
    assert SECRET not in json.dumps(redacted)


def test_redact_masks_sensitive_output_changes():
    plan = {
        "resource_changes": [],
        "output_changes": {
            "db_url": {"actions": ["create"], "after": SECRET, "sensitive": True},
            "region": {"actions": ["create"], "after": "eu-central-1", "sensitive": False},
        },
    }

    redacted = redact.redact_plan(plan)

    assert redacted["output_changes"]["db_url"]["after"] == redact.SENTINEL
    assert redacted["output_changes"]["region"]["after"] == "eu-central-1"
    assert SECRET not in json.dumps(redacted)


def test_redact_leaves_unmarked_values_alone():
    """
    Documents the known limitation honestly: terraform's markers are not exhaustive, so a secret
    that arrives unmarked is NOT masked. Slimming and the variables drop limit the blast radius;
    this test exists so the gap is visible rather than assumed away.
    """
    plan = {"resource_changes": [{"change": {"after": {"password_from_locals": SECRET}, "after_sensitive": {}}}]}

    redacted = redact.redact_plan(plan)

    assert redacted["resource_changes"][0]["change"]["after"]["password_from_locals"] == SECRET


def test_redact_plan_tolerates_junk():
    assert redact.redact_plan({}) == {}
    assert redact.redact_plan({"resource_changes": "not-a-list"})["resource_changes"] == "not-a-list"
    assert redact.redact_plan([]) == []


# --- state -------------------------------------------------------------------------------------


def test_redact_state_masks_sensitive_outputs():
    state = {
        "version": 4,
        "outputs": {
            "db_password": {"value": SECRET, "type": "string", "sensitive": True},
            "region": {"value": "eu-central-1", "type": "string"},
        },
        "resources": [],
    }

    redacted = redact.redact_state(state)

    assert redacted["outputs"]["db_password"]["value"] == redact.SENTINEL
    assert redacted["outputs"]["region"]["value"] == "eu-central-1"
    assert SECRET not in json.dumps(redacted)


def test_redact_state_masks_sensitive_attributes():
    """
    The shape `terraform state pull` actually writes: each entry is a PATH -- a list of steps --
    not a single key.

    Captured verbatim from a real `local_sensitive_file`. The previous fixture here invented the
    flat form, so this passed while real state was not masked at all: a list is neither a dict nor
    a string, so every entry was skipped.
    """
    state = {
        "resources": [
            {
                "type": "local_sensitive_file",
                "name": "s",
                "instances": [
                    {
                        "attributes": {"id": "e590ef", "content": SECRET, "content_base64": SECRET},
                        "sensitive_attributes": [
                            [{"type": "get_attr", "value": "content_base64"}],
                            [{"type": "get_attr", "value": "content"}],
                        ],
                    }
                ],
            }
        ]
    }

    redacted = redact.redact_state(state)
    attributes = redacted["resources"][0]["instances"][0]["attributes"]

    assert attributes["content"] == redact.SENTINEL
    assert attributes["content_base64"] == redact.SENTINEL
    assert attributes["id"] == "e590ef", "non-sensitive attributes must survive"
    assert SECRET not in json.dumps(redacted)


def test_redact_state_masks_a_nested_attribute_path():
    """A path can descend through objects and list indices, not just name a top-level key."""
    state = {
        "resources": [
            {
                "instances": [
                    {
                        "attributes": {"config": [{"token": SECRET, "url": "https://ok"}]},
                        "sensitive_attributes": [
                            [
                                {"type": "get_attr", "value": "config"},
                                {"type": "index", "value": 0},
                                {"type": "get_attr", "value": "token"},
                            ]
                        ],
                    }
                ]
            }
        ]
    }

    redacted = redact.redact_state(state)
    config = redacted["resources"][0]["instances"][0]["attributes"]["config"][0]

    assert config["token"] == redact.SENTINEL
    assert config["url"] == "https://ok"


def test_redact_state_does_not_mutate_the_input():
    """The caller still holds the original; masking must not reach back into it."""
    state = {
        "resources": [
            {
                "instances": [
                    {
                        "attributes": {"password": SECRET},
                        "sensitive_attributes": [[{"type": "get_attr", "value": "password"}]],
                    }
                ]
            }
        ]
    }

    redact.redact_state(state)

    assert state["resources"][0]["instances"][0]["attributes"]["password"] == SECRET


def test_redact_state_accepts_the_flat_get_attr_form():
    """Some providers and older state versions emit a single step rather than a path."""
    state = {
        "resources": [
            {
                "instances": [
                    {
                        "attributes": {"password": SECRET},
                        "sensitive_attributes": [{"type": "get_attr", "value": "password"}],
                    }
                ]
            }
        ]
    }

    redacted = redact.redact_state(state)

    assert redacted["resources"][0]["instances"][0]["attributes"]["password"] == redact.SENTINEL


def test_redact_state_accepts_bare_string_sensitive_attributes():
    """Older state versions write these as plain strings rather than objects."""
    state = {"resources": [{"instances": [{"attributes": {"secret": SECRET}, "sensitive_attributes": ["secret"]}]}]}

    redacted = redact.redact_state(state)

    assert redacted["resources"][0]["instances"][0]["attributes"]["secret"] == redact.SENTINEL


def test_redact_state_tolerates_junk():
    assert redact.redact_state({}) == {}
    assert redact.redact_state({"resources": "nope"})["resources"] == "nope"
    assert redact.redact_state({"outputs": None})["outputs"] is None


def test_count_redactions():
    document = {"a": redact.SENTINEL, "b": [redact.SENTINEL, "fine"], "c": {"d": redact.SENTINEL}}

    assert redact.count_redactions(document) == 3
    assert redact.count_redactions({"a": "fine"}) == 0


# --- output_changes marker spellings -------------------------------------------------------------
#
# These exist because a real plan slipped through: the code originally checked only a top-level
# `sensitive` key, but modern terraform emits `before_sensitive` / `after_sensitive` per side, so
# every sensitive output in a current plan went unmasked.


def test_output_change_masked_via_after_sensitive():
    """The spelling modern terraform actually uses."""
    plan = {
        "resource_changes": [],
        "output_changes": {
            "db_url": {"actions": ["update"], "before": "old", "after": SECRET, "after_sensitive": True}
        },
    }

    redacted = redact.redact_plan(plan)

    assert redacted["output_changes"]["db_url"]["after"] == redact.SENTINEL
    assert SECRET not in json.dumps(redacted)


def test_output_change_masks_each_side_independently():
    """An output can become sensitive without having been so before, and vice versa."""
    plan = {
        "resource_changes": [],
        "output_changes": {
            "rotated": {
                "actions": ["update"],
                "before": SECRET,
                "after": "now-public",
                "before_sensitive": True,
                "after_sensitive": False,
            }
        },
    }

    redacted = redact.redact_plan(plan)
    change = redacted["output_changes"]["rotated"]

    assert change["before"] == redact.SENTINEL
    assert change["after"] == "now-public"
    assert SECRET not in json.dumps(redacted)


def test_output_change_legacy_sensitive_key_masks_both_sides():
    plan = {
        "resource_changes": [],
        "output_changes": {"k": {"before": SECRET, "after": SECRET, "sensitive": True}},
    }

    redacted = redact.redact_plan(plan)

    assert redacted["output_changes"]["k"]["before"] == redact.SENTINEL
    assert redacted["output_changes"]["k"]["after"] == redact.SENTINEL


def test_output_change_does_not_invent_absent_keys():
    """
    A create whose value is not yet known has no `after` at all (`after_unknown: true`). Adding a
    sentinel would fabricate data the plan never carried, and would misrepresent the plan to any
    policy reading it.
    """
    plan = {
        "resource_changes": [],
        "output_changes": {
            "pw": {"actions": ["create"], "before": None, "after_unknown": True, "after_sensitive": True}
        },
    }

    redacted = redact.redact_plan(plan)
    change = redacted["output_changes"]["pw"]

    assert "after" not in change
    assert change["before"] is None


def test_unknown_create_values_are_simply_absent_from_the_plan():
    """
    Documents a property that made an earlier end-to-end test weaker than intended: for a create,
    terraform does not know the value yet, so it is absent from `after` rather than present and
    masked. Nothing leaks -- but a test that expects to see a sentinel here is testing nothing.
    """
    plan = {
        "resource_changes": [
            {
                "type": "random_password",
                "change": {
                    "actions": ["create"],
                    "after": {"length": 32},
                    "after_unknown": {"result": True},
                    "after_sensitive": {"result": True},
                },
            }
        ]
    }

    redacted = redact.redact_plan(plan)
    after = redacted["resource_changes"][0]["change"]["after"]

    assert "result" not in after
    assert redact.count_redactions(redacted) == 0


def test_known_sensitive_value_at_plan_time_is_masked():
    """
    The case that DOES exercise marker-driven redaction: a hardcoded sensitive attribute is known
    at plan time, so it really is in `after` and really must be replaced.
    """
    plan = {
        "resource_changes": [
            {
                "type": "local_sensitive_file",
                "change": {
                    "actions": ["create"],
                    "after": {"filename": "out.txt", "content": SECRET},
                    "after_sensitive": {"content": True},
                },
            }
        ]
    }

    redacted = redact.redact_plan(plan)

    assert redacted["resource_changes"][0]["change"]["after"]["content"] == redact.SENTINEL
    assert redacted["resource_changes"][0]["change"]["after"]["filename"] == "out.txt"
    assert SECRET not in json.dumps(redacted)


# --- planned_values reconstruction ----------------------------------------------------------


def _plan_with(resource_changes, **extra):
    plan = {"format_version": "1.2", "terraform_version": "1.5.7", "resource_changes": resource_changes}
    plan.update(extra)
    return plan


def test_planned_values_is_rebuilt_so_infracost_and_checkov_have_something_to_read():
    """
    Both tools read planned_values and nothing else. Measured against infracost 0.10.27 with a
    real key: the same t3.medium prices at $39.80 with this section and $0.00 without.
    """
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.app",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "app",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {"actions": ["create"], "after": {"instance_type": "t3.medium"}},
                }
            ]
        )
    )

    resources = out["planned_values"]["root_module"]["resources"]
    assert [r["address"] for r in resources] == ["aws_instance.app"]
    assert resources[0]["values"]["instance_type"] == "t3.medium"
    assert resources[0]["provider_name"] == "registry.terraform.io/hashicorp/aws"


def test_the_rebuilt_planned_values_carries_masked_values_not_raw_ones():
    """
    The whole reason terraform's own copy is dropped: it mirrors every value with no sensitivity
    markers, so masking resource_changes leaves the secret in plaintext there. A real plan leaked
    a local_sensitive_file body through exactly that path. This copy is derived post-masking.
    """
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "local_sensitive_file.creds",
                    "mode": "managed",
                    "type": "local_sensitive_file",
                    "name": "creds",
                    "change": {
                        "actions": ["create"],
                        "after": {"content": "hunter2", "filename": "/tmp/c"},
                        "after_sensitive": {"content": True},
                    },
                }
            ],
            planned_values={
                "root_module": {
                    "resources": [{"address": "local_sensitive_file.creds", "values": {"content": "hunter2"}}]
                }
            },
        )
    )

    assert "hunter2" not in json.dumps(out)
    values = out["planned_values"]["root_module"]["resources"][0]["values"]
    assert values["content"] == redact.SENTINEL
    assert values["filename"] == "/tmp/c", "non-sensitive attributes must survive"


def test_terraform_own_planned_values_is_never_passed_through():
    """It is replaced, not merged -- otherwise the unmarked original would leak straight through."""
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.app",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "app",
                    "change": {"actions": ["create"], "after": {"instance_type": "t3.medium"}},
                }
            ],
            planned_values={
                "root_module": {
                    "resources": [{"address": "ghost.resource", "values": {"secret": "leaked-from-original"}}]
                }
            },
        )
    )

    assert "leaked-from-original" not in json.dumps(out)
    assert [r["address"] for r in out["planned_values"]["root_module"]["resources"]] == ["aws_instance.app"]


def test_a_destroyed_resource_has_no_planned_value():
    """Nothing is planned to exist, so there is nothing to price or scan."""
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.gone",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "gone",
                    "change": {"actions": ["delete"], "before": {"instance_type": "m5.large"}, "after": None},
                }
            ]
        )
    )

    assert "planned_values" not in out
    assert out["resource_changes"], "the destroy is still a change policies evaluate"


def test_a_replacement_is_planned_because_it_ends_up_existing():
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.app",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "app",
                    "change": {"actions": ["delete", "create"], "after": {"instance_type": "t3.large"}},
                }
            ]
        )
    )

    assert out["planned_values"]["root_module"]["resources"][0]["values"]["instance_type"] == "t3.large"


def test_module_resources_are_grouped_under_child_modules():
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.app",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "app",
                    "change": {"actions": ["create"], "after": {"instance_type": "t3.medium"}},
                },
                {
                    "address": "module.db.aws_instance.replica",
                    "module_address": "module.db",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "replica",
                    "change": {"actions": ["create"], "after": {"instance_type": "m5.large"}},
                },
            ]
        )
    )

    root = out["planned_values"]["root_module"]
    assert [r["address"] for r in root["resources"]] == ["aws_instance.app"]
    assert [m["address"] for m in root["child_modules"]] == ["module.db"]
    assert root["child_modules"][0]["resources"][0]["address"] == "module.db.aws_instance.replica"


def test_child_modules_is_absent_when_there_are_none():
    out = redact.redact_plan(
        _plan_with(
            [
                {
                    "address": "aws_instance.app",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "app",
                    "change": {"actions": ["create"], "after": {"instance_type": "t3.medium"}},
                }
            ]
        )
    )

    assert "child_modules" not in out["planned_values"]["root_module"]


def test_an_empty_plan_gets_no_planned_values():
    assert "planned_values" not in redact.redact_plan(_plan_with([]))


# --- resource_drift and configuration literals ---------------------------------------------------


def test_resource_drift_is_masked_like_resource_changes():
    """
    resource_drift has the identical shape and the identical sensitivity markers, and terraform
    emits it whenever a refresh finds drift. Masking resource_changes and leaving this alone shipped
    the same secret one key away -- the planned_values failure a third time.
    """
    plan = {
        "format_version": "1.2",
        "resource_drift": [
            {
                "address": "aws_secretsmanager_secret_version.db",
                "type": "aws_secretsmanager_secret_version",
                "change": {
                    "actions": ["update"],
                    "before": {"secret_string": "hunter2-before"},
                    "after": {"secret_string": "hunter2-after"},
                    "before_sensitive": {"secret_string": True},
                    "after_sensitive": {"secret_string": True},
                },
            }
        ],
    }

    out = redact.redact_plan(plan)
    drift = out["resource_drift"][0]["change"]

    assert drift["before"]["secret_string"] == redact.SENTINEL
    assert drift["after"]["secret_string"] == redact.SENTINEL
    assert "hunter2-before" not in json.dumps(out)
    assert "hunter2-after" not in json.dumps(out)


def test_provisioner_literals_are_scrubbed_from_configuration():
    """
    A provisioner carries its own expressions one level below the resource's, and a connection block
    is exactly where a password gets written literally. Scrubbing only the resource's own
    expressions left these verbatim -- and configuration ships even with `source-dir: ""`.
    """
    plan = {
        "format_version": "1.2",
        "configuration": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_instance.app",
                        "expressions": {"ami": {"constant_value": "ami-123"}},
                        "provisioners": [
                            {
                                "type": "remote-exec",
                                "expressions": {
                                    "inline": {"constant_value": ["echo s3cr3t-inline"]},
                                    "connection": {"password": {"constant_value": "s3cr3t-conn"}},
                                },
                            }
                        ],
                    }
                ]
            }
        },
    }

    out = json.dumps(redact.redact_plan(plan))

    assert "s3cr3t-conn" not in out
    assert "s3cr3t-inline" not in out


def test_module_call_arguments_are_dropped_even_without_an_inlined_module():
    """
    A module sourced from a registry or a git ref carries no inlined `module` body, which is the
    common case -- and its arguments are literals either way.
    """
    plan = {
        "format_version": "1.2",
        "configuration": {
            "root_module": {
                "module_calls": {
                    "db": {
                        "source": "terraform-aws-modules/rds/aws",
                        "expressions": {"password": {"constant_value": "s3cr3t-mod"}},
                    }
                }
            }
        },
    }

    assert "s3cr3t-mod" not in json.dumps(redact.redact_plan(plan))


def test_a_show_json_state_is_masked_not_passed_through():
    """
    The leak an end-to-end run found. `terraform show -json <state>` is the natural way to get a
    readable state, and its shape nests resources under values.root_module with a parallel
    sensitive_values tree -- nothing like the raw state this function was written for. It returned
    the document unchanged: no error, no warning, every attribute in plaintext.
    """
    document = {
        "format_version": "1.0",
        "values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_db_instance.main",
                        "type": "aws_db_instance",
                        "values": {"identifier": "prod-db", "password": "hunter2"},
                        "sensitive_values": {"password": True},
                    }
                ],
                "child_modules": [
                    {
                        "address": "module.net",
                        "resources": [
                            {
                                "address": "module.net.aws_secretsmanager_secret_version.k",
                                "values": {"secret_string": "hunter3"},
                                "sensitive_values": {"secret_string": True},
                            }
                        ],
                    }
                ],
            },
            "outputs": {"db_url": {"value": "postgres://hunter4@host", "sensitive": True}},
        },
    }

    out = redact.redact_state(document)
    blob = json.dumps(out)

    assert out["values"]["root_module"]["resources"][0]["values"]["password"] == redact.SENTINEL
    # A module's resources are nested, not flattened -- masking only the root would miss them.
    assert (
        out["values"]["root_module"]["child_modules"][0]["resources"][0]["values"]["secret_string"] == redact.SENTINEL
    )
    assert out["values"]["outputs"]["db_url"]["value"] == redact.SENTINEL
    for secret in ("hunter2", "hunter3", "hunter4"):
        assert secret not in blob, secret


def test_the_raw_state_shape_still_works():
    """The shape this function was written for must keep working alongside the new one."""
    document = {
        "version": 4,
        "resources": [
            {
                "type": "aws_db_instance",
                "instances": [{"attributes": {"password": "hunter2"}, "sensitive_attributes": ["password"]}],
            }
        ],
        "outputs": {"token": {"value": "hunter5", "sensitive": True}},
    }

    out = redact.redact_state(document)

    assert out["resources"][0]["instances"][0]["attributes"]["password"] == redact.SENTINEL
    assert out["outputs"]["token"]["value"] == redact.SENTINEL
