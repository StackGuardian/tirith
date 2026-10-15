from tirith.providers.kubernetes.handler import provide


def test_missing_kubernetes_kind():
    result = provide({"operation_type": "attribute", "attribute_path": "spec"}, [{"kind": "Pod", "spec": {}}])
    assert len(result) == 1
    assert result[0]["err"] == "kubernetes_kind must be provided"
    assert result[0]["value"].severity_value == 99


def test_missing_attribute_path():
    result = provide({"operation_type": "attribute", "kubernetes_kind": "Pod"}, [{"kind": "Pod", "spec": {}}])
    assert len(result) == 1
    assert result[0]["err"] == "attribute_path must be provided"
    assert result[0]["value"].severity_value == 99
