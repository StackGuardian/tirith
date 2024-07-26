import pytest
from utils import load_terraform_plan_json

from tirith.providers.terraform_plan import handler

input_data = load_terraform_plan_json("input.json")

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


def test_direct_dependencies():
    provider_args_dict = {"operation_type": "direct_dependencies", "terraform_resource_type": "aws_instance"}
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_instance_deps_s3.json"))

    assert len(result) == 1
    assert result[0]["value"] == ["aws_s3_bucket"]


def test_direct_references():
    provider_args_dict = {"operation_type": "direct_references", "terraform_resource_type": "aws_elb"}
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_implicit_elb_secgroup.json"))

    # There are two aws_elbs one with aws_security_group and one without
    assert len(result) == 2
    assert result[0]["value"] == ["aws_security_group"]
    assert result[1]["value"] == []


def test_get_terraform_version():
    provider_args_dict = {"operation_type": "terraform_version"}
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_instance_deps_s3.json"))

    assert len(result) == 1
    assert result[0]["value"] == "1.4.5"
