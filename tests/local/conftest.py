"""Fixtures shared by the local-mode tests."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

# A policy that fails on the plan below, and passes when the instance type is t3.micro.
POLICY = {
    "meta": {
        "id": "instance-type",
        "name": "instance types are approved",
        "required_provider": "stackguardian/terraform_plan",
        "version": "v1",
    },
    "evaluators": [
        {
            "id": "ev",
            "description": "instance_type must be t3.micro",
            "condition": {"type": "Equals", "value": "t3.micro", "error_tolerance": 0},
            "provider_args": {
                "operation_type": "attribute",
                "terraform_resource_attribute": "instance_type",
                "terraform_resource_type": "aws_instance",
            },
        }
    ],
    "eval_expression": "ev",
}


def plan(instance_type="m5.24xlarge", secret=None):
    """
    A one-resource terraform plan.

    `secret` lands in `after` *and* is named in `after_sensitive`, which is the shape masking exists
    for -- a value terraform itself marked sensitive.
    """
    after = {"instance_type": instance_type}
    after_sensitive = {}
    if secret is not None:
        after["password"] = secret
        after_sensitive["password"] = True
    return {
        "format_version": "1.2",
        "terraform_version": "1.5.7",
        "resource_changes": [
            {
                "address": "aws_instance.app",
                "mode": "managed",
                "type": "aws_instance",
                "name": "app",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": after,
                    "after_sensitive": after_sensitive,
                },
            }
        ],
    }


@pytest.fixture
def workspace(tmp_path):
    """A directory holding one policy and one plan, with helpers to vary either."""

    class Workspace:
        def __init__(self, root):
            self.root = root
            self.policies = root / "policies"
            self.policies.mkdir()

        def policy(self, name="instance-type.tirith.json", document=None):
            path = self.policies / name
            path.write_text(json.dumps(POLICY if document is None else document))
            return path

        def raw(self, name, text):
            path = self.policies / name
            path.write_text(text)
            return path

        def plan(self, name="plan.json", **kwargs):
            path = self.root / name
            path.write_text(json.dumps(plan(**kwargs)))
            return path

        def argv(self, *extra):
            return [
                "local",
                "check",
                "--policy-path",
                str(self.policies),
                "--input-path",
                str(self.root / "plan.json"),
                "--output-json",
                str(self.root / "out.json"),
                "--output-markdown",
                str(self.root / "out.md"),
            ] + list(extra)

        def result(self):
            with open(self.root / "out.json") as f:
                return json.load(f)

        def markdown(self):
            with open(self.root / "out.md") as f:
                return f.read()

    return Workspace(tmp_path)


def policy_with_enforcement(value):
    """The shared policy, relabelled with a `meta.enforcement` value."""
    document = json.loads(json.dumps(POLICY))
    document["meta"]["enforcement"] = value
    return document
