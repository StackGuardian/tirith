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

# Considered test cases based on totalMonthlyCost and totalHourlyCost of the services deployed
@pytest.mark.passing
def test_get_monthly_cost_pass():
    res = handler.provide(provider_inputs_1, input_data)
    assert res[0]["value"] != 0


# if value not equals 0 that means some cost is generated as the service is running


@pytest.mark.failing
def test_get_monthly_cost_fail():
    res = handler.provide(provider_inputs_1, input_data)
    assert bool(res[0]["value"] == 0) == False


# if value equals 0 that means no cost generated and hence the service is not deployed

provider_inputs_2 = {
    "resource_type": "aws_s3_bucket",
    "costType": "totalHourlyCost",
}


@pytest.mark.passing
def test_get_hourly_cost_pass():
    res = handler.provide(provider_inputs_2, input_data)
    assert res[0]["value"] != 0


# if value not equals 0 that means no cost generated and hence the service is not deployed


@pytest.mark.failing
def test_get_hourly_cost_fail():
    res = handler.provide(provider_inputs_2, input_data)
    assert bool(res[0]["value"] == 0) == False


# if value equals 0 that means the service is deployed and is generating hourly costs


provider_inputs_3 = {
    "resource_type": "module.s3_bucket.aws_s3_bucket.this[0]",
    "costType": "totalMonthlyCost",
}


@pytest.mark.passing
def test_cost_s3_bucket_module_pass():
    res = handler.provide(provider_inputs_3, input_data)
    assert res[0]["value"] != 0


@pytest.mark.failing
def test_cost_s3_bucket_module_fail():
    res = handler.provide(provider_inputs_3, input_data)
    assert bool(res[0]["value"] == 0) == False


# the above test case is to check for the module
# "name": "module.s3_bucket.aws_s3_bucket.this[0]" line 21 in input.json

# if value equals 0 that means the service is deployed and is generating hourly costs
# if value not equals 0 that means no cost is generated and hence the service is not deployed
