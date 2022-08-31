import json

import pytest

from sg_policy.providers.terraform_plan import handler


def load_terraform_plan_json(json_path):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        return data
    except Exception:
        return False


input_data = load_terraform_plan_json("./input.json")

provider_inputs_1 = {
    "input_type": "resource_changes",
    "resource_type": "aws_vpc",
    "attribute": "enable_dns_hostnames",
}

provider_inputs_2 = {
    "input_type": "resource_changes",
    "resource_type": "aws_vpc",
    "attribute": "enable_dns_support",
}


@pytest.mark.passingattr
def test_get_attribute_name_passing1():
    res = handler.provide(provider_inputs_1, input_data)
    assert res == [
        {
            "value": False,
            "meta": {
                "address": "aws_vpc.this[0]",
                "mode": "managed",
                "type": "aws_vpc",
                "name": "this",
                "index": 0,
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "assign_generated_ipv6_cidr_block": False,
                        "cidr_block": "10.0.0.0/18",
                        "enable_dns_hostnames": False,
                        "enable_dns_support": True,
                        "instance_tenancy": "default",
                        "tags": {"Name": ""},
                        "tags_all": {},
                    },
                    "after_unknown": {
                        "arn": True,
                        "default_network_acl_id": True,
                        "default_route_table_id": True,
                        "default_security_group_id": True,
                        "dhcp_options_id": True,
                        "enable_classiclink": True,
                        "enable_classiclink_dns_support": True,
                        "id": True,
                        "ipv6_association_id": True,
                        "ipv6_cidr_block": True,
                        "main_route_table_id": True,
                        "owner_id": True,
                        "tags": {},
                        "tags_all": {"Name": True},
                    },
                },
            },
            "err": None,
        }
    ]


@pytest.mark.passingattr
def test_get_attribute_name_passing2():
    res = handler.provide(provider_inputs_1, input_data)
    assert res[0]["value"] == False


@pytest.mark.passingattr
def test_get_attribute_name_passing3():
    res = handler.provide(provider_inputs_2, input_data)
    print(res)
    assert res == [
        {
            "value": True,
            "meta": {
                "address": "aws_vpc.this[0]",
                "mode": "managed",
                "type": "aws_vpc",
                "name": "this",
                "index": 0,
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "assign_generated_ipv6_cidr_block": False,
                        "cidr_block": "10.0.0.0/18",
                        "enable_dns_hostnames": False,
                        "enable_dns_support": True,
                        "instance_tenancy": "default",
                        "tags": {"Name": ""},
                        "tags_all": {},
                    },
                    "after_unknown": {
                        "arn": True,
                        "default_network_acl_id": True,
                        "default_route_table_id": True,
                        "default_security_group_id": True,
                        "dhcp_options_id": True,
                        "enable_classiclink": True,
                        "enable_classiclink_dns_support": True,
                        "id": True,
                        "ipv6_association_id": True,
                        "ipv6_cidr_block": True,
                        "main_route_table_id": True,
                        "owner_id": True,
                        "tags": {},
                        "tags_all": {"Name": True},
                    },
                },
            },
            "err": None,
        }
    ]


@pytest.mark.passingattr
def test_get_attribute_name_passing4():
    res = handler.provide(provider_inputs_2, input_data)
    assert res[0]["value"] == True


# actions
provider_inputs_4 = {
    "input_type": "resource_changes_actions",
    "resource_type": "aws_vpc",
    "attribute": "actions",
}


@pytest.mark.passingattr
def test_get_attribute_name_passing5():
    res = handler.provide(provider_inputs_4, input_data)
    assert res[0]["value"] == ["create"]


@pytest.mark.failingattr
def test_get_attribute_name_failing6():
    res = handler.provide(provider_inputs_4, input_data)
    assert res[0]["value"] != ["create"]


# count
provider_inputs_3 = {
    "input_type": "resource_changes_count",
    "resource_type": "aws_vpc",
    "attribute": "index",
}


@pytest.mark.passingattr
def test_get_attribute_name_passing7():
    res = handler.provide(provider_inputs_3, input_data)
    assert res[0]["value"] >= 0


@pytest.mark.failingattr
def test_get_attribute_name_failing8():
    res = handler.provide(provider_inputs_3, input_data)
    assert res[0]["value"] == 0
