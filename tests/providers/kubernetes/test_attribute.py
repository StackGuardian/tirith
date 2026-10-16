import os

import yaml

from tirith.core.core import start_policy_evaluation
from tirith.providers.common import ProviderError
from tirith.providers.kubernetes.handler import provide


def _load_input():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(test_dir, "input.yml")) as f:
        return list(yaml.safe_load_all(f))


def test_get_value():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    input_path = os.path.join(test_dir, "input.yml")
    policy_path = os.path.join(test_dir, "policy.json")

    result = start_policy_evaluation(policy_path=policy_path, input_path=input_path)
    assert result["final_result"] is False

    # This provider does not attach a result context, so its messages carry no prefix
    for item in result["evaluators"][0]["result"]:
        assert "context" not in item
        assert item["message"].startswith("Found ")


def test_kind_not_found():
    result = provide(
        {"operation_type": "attribute", "kubernetes_kind": "ConfigMap", "attribute_path": "metadata.name"},
        _load_input(),
    )

    assert len(result) == 1
    assert result[0]["err"] == "kind: ConfigMap is not found"
    assert isinstance(result[0]["value"], ProviderError)
    assert result[0]["value"].severity_value == 1


def test_plain_path():
    result = provide(
        {"operation_type": "attribute", "kubernetes_kind": "Role", "attribute_path": "metadata.name"},
        _load_input(),
    )

    assert result == [{"value": "access-role", "meta": None, "err": None}]


def test_wildcard_path():
    result = provide(
        {
            "operation_type": "attribute",
            "kubernetes_kind": "Deployment",
            "attribute_path": "spec.selector.matchLabels.*",
        },
        _load_input(),
    )

    assert result == [{"value": ["wfs-demo", "wfs-demp"], "meta": None, "err": None}]


def test_missing_attribute():
    result = provide(
        {"operation_type": "attribute", "kubernetes_kind": "RoleBinding", "attribute_path": "metadata.labels"},
        _load_input(),
    )

    assert result == [{"value": None, "meta": None, "err": None}]
