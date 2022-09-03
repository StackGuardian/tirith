import json
import os
import pytest

from sg_policy.providers.infracost import handler


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_terraform_plan_json("input.json")

provider_inputs_1 = {
    "resource_type": "aws_s3_bucket",
    "costType": "totalMonthlyCost",
}

provider_inputs_2 = {
    "resource_type": "aws_s3_bucket",
    "costType": "totalHourlyCost",
}

# @pytest.mark.passing
def test_get_attribute_name_passing1():
    res = handler.provide(provider_inputs_1,input_data)
    assert res[0]["value"] != 0

# @pytest.mark.failing
def test_get_attribute_name_failing1():
    res = handler.provide(provider_inputs_1,input_data)
    assert res[0]["value"] == 0

# @pytest.mark.passing
def test_get_attribute_name_passing2():
    res = handler.provide(provider_inputs_2,input_data)
    assert res[0]["value"] != 0

# @pytest.mark.failing
def test_get_attribute_name_failing2():
    res = handler.provide(provider_inputs_2,input_data)
    assert res[0]["value"] == 0

    # module.s3_bucket.aws_s3_bucket.this[0]

provider_inputs_3 = {
    "resource_type": "module.s3_bucket.aws_s3_bucket.this[0]",
    "costType": "totalMonthlyCost",
}

# @pytest.mark.passing
def test_get_attribute_name_passing3():
    res = handler.provide(provider_inputs_3,input_data)
    assert res[0]["value"] != 0

# @pytest.mark.failing
def test_get_attribute_name_failing3():
    res = handler.provide(provider_inputs_3,input_data)
    assert res[0]["value"] == 0
