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
    """`sensitive_attributes` names the keys to mask, in the get_attr shape terraform writes."""
    state = {
        "resources": [
            {
                "type": "aws_db_instance",
                "name": "main",
                "instances": [
                    {
                        "attributes": {"id": "db-1", "password": SECRET},
                        "sensitive_attributes": [{"type": "get_attr", "value": "password"}],
                    }
                ],
            }
        ]
    }

    redacted = redact.redact_state(state)
    attributes = redacted["resources"][0]["instances"][0]["attributes"]

    assert attributes["password"] == redact.SENTINEL
    assert attributes["id"] == "db-1"
    assert SECRET not in json.dumps(redacted)


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
