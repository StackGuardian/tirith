"""
Guardrails on the shape of the result document.

The StackGuardian platform and the workflow-step templates parse this output, so its shape is a
contract rather than an implementation detail. `test_legacy_json_output_is_byte_identical` holds
the line: the golden file was captured before the engine changes landed, so any drift in the
single-policy output is a regression until proven otherwise.
"""

import json
import os

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN_PATH = os.path.join(REPO_ROOT, "tests", "golden", "json_policy_output.json")


@mark.passing
def test_legacy_json_output_is_byte_identical():
    with open(os.path.join(REPO_ROOT, "tests", "providers", "json", "policy.json")) as f:
        policy = json.load(f)
    with open(os.path.join(REPO_ROOT, "tests", "providers", "json", "input.json")) as f:
        input_data = json.load(f)

    result = start_policy_evaluation_from_dict(policy, input_data)

    with open(GOLDEN_PATH) as f:
        # The golden file was captured from the CLI, whose print() adds a trailing newline
        # that json.dumps does not produce.
        expected = f.read().rstrip("\n")

    # indent=3 matches what the CLI emits (cli.py), so the golden file doubles as a
    # record of the exact bytes a --json consumer receives.
    assert json.dumps(result, indent=3) == expected


@mark.passing
def test_meta_passthrough_omits_absent_keys():
    """A policy declaring no optional metadata must produce exactly the two original keys."""
    policy = {
        "meta": {"version": "v1", "required_provider": "stackguardian/json"},
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {"operation_type": "get_value", "key_path": "a"},
                "condition": {"type": "Equals", "value": 1},
            }
        ],
        "eval_expression": "check0",
    }

    result = start_policy_evaluation_from_dict(policy, {"a": 1})

    assert result["meta"] == {"version": "v1", "required_provider": "stackguardian/json"}


@mark.passing
def test_meta_passthrough_carries_declared_keys():
    policy = {
        "meta": {
            "version": "v1",
            "required_provider": "stackguardian/json",
            "id": "no-public-ingress",
            "name": "No 0.0.0.0/0 ingress",
            "description": "Public ingress is not permitted",
            "severity": "HIGH",
            "enforcement": "hard_mandatory",
            "tags": ["cis", "network"],
            "remediation": "Restrict the CIDR or use a security-group reference",
        },
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {"operation_type": "get_value", "key_path": "a"},
                "condition": {"type": "Equals", "value": 1},
            }
        ],
        "eval_expression": "check0",
    }

    result = start_policy_evaluation_from_dict(policy, {"a": 1})

    assert result["meta"]["id"] == "no-public-ingress"
    assert result["meta"]["name"] == "No 0.0.0.0/0 ingress"
    assert result["meta"]["severity"] == "HIGH"
    assert result["meta"]["enforcement"] == "hard_mandatory"
    assert result["meta"]["tags"] == ["cis", "network"]
    assert result["meta"]["remediation"] == "Restrict the CIDR or use a security-group reference"
    # The originals survive alongside the additions.
    assert result["meta"]["version"] == "v1"
    assert result["meta"]["required_provider"] == "stackguardian/json"


@mark.passing
def test_meta_passthrough_supports_variables():
    """
    Variable substitution already covers the whole meta dict, so the new fields get
    {{ var.x }} support without any extra plumbing. This pins that behaviour.
    """
    policy = {
        "meta": {
            "version": "v1",
            "required_provider": "stackguardian/json",
            "severity": "{{ var.sev }}",
        },
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {"operation_type": "get_value", "key_path": "a"},
                "condition": {"type": "Equals", "value": 1},
            }
        ],
        "eval_expression": "check0",
    }

    result = start_policy_evaluation_from_dict(policy, {"a": 1}, {"sev": "CRITICAL"})

    assert result["meta"]["severity"] == "CRITICAL"
