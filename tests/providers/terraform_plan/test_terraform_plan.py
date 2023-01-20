import json
import os
import pytest
from tirith.providers.common import ProviderError

from tirith.providers.terraform_plan import handler


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_terraform_plan_json("input.json")
input_data_with_no_resource_changes = load_terraform_plan_json("input_with_no_resource_changes.json")

#  1 and 2 -----> To check output of the attribute that if the functionality is active or not
provider_args_1 = {
    "operation_type": "attribute",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "enable_dns_hostnames",
}

provider_args_2 = {
    "operation_type": "attribute",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "enable_dns_support",
}


# To check if the resources deployed are in sync with what user defined
provider_args_3 = {
    "operation_type": "count",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "index",
}

# To check on the actions the service is providing is equal to what the user expected it ito be
provider_args_4 = {
    "operation_type": "action",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "actions",
}


# If the value of the attribute "enable_dns_hostnames" is given false, the test case should pass, otherwise fail case should pass
@pytest.mark.passing
def test_awsvpc_attribute_status_pass():
    res = handler.provide(provider_args_1, input_data)
    assert res[0]["value"] == False


def test_awsvpc_attribute_status_fail():
    res = handler.provide(provider_args_1, input_data)
    assert res[0]["value"] != True


# input_data
# If the value of the attribute "enable_dns_support" is expected to be True, then the pass test test case should be considered or else the fail case should be considered
@pytest.mark.passing
def test_awsvpc_attribute_status_pass():
    res = handler.provide(provider_args_2, input_data)
    assert res[0]["value"] == True


@pytest.mark.failing
def test_awsvpc_attribute_status_fail():
    res = handler.provide(provider_args_2, input_data)
    assert bool(res[0]["value"] != False) == True


# If the actions expected by the user is performed by the service, then the pass test caset to be considered and if not then the fail test case to be considered
@pytest.mark.passing
def test_awsvpc_actions_pass():
    res = handler.provide(provider_args_4, input_data)
    assert bool(res[0]["value"] == "create") == True


@pytest.mark.failing
def test_awsvpc_actions_fail():
    res = handler.provide(provider_args_4, input_data)
    assert bool(res[0]["value"] != "create") == False  # output to be False


# If the count of the resources matches with what user expects, then the pass test caset to be considered and if not then the fail test case to be considered
@pytest.mark.passing
def test_count_value_passing():
    res = handler.provide(provider_args_3, input_data)
    assert res[0]["value"] > 0


@pytest.mark.failing
def test_count_value_failing():
    res = handler.provide(provider_args_3, input_data)
    assert res[0]["value"] != 0


# if count == 0, no services deployed
# if count > 0 services deployed


@pytest.mark.passing
def test_skip_when_no_resource_changes():
    res = handler.provide(provider_args_1, input_data_with_no_resource_changes)
    assert len(res) == 1

    res = res[0]
    assert res["err"] == "Key `resource_changes` is not found in the input_data, skipping the check"
    assert isinstance(res["value"], ProviderError)
    assert res["value"].severity_value == 0
