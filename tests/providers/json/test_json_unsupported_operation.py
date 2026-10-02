from tirith.providers.json.handler import provide


def test_unknown_operation_type_is_rejected():
    result = provide({"operation_type": "nope"}, {})

    assert result == [{"value": None, "meta": None, "err": "operation_type: 'nope' is not supported"}]
