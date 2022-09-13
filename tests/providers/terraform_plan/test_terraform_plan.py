import json
import os
import pytest

from sg_policy.providers.terraform_plan import handler


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_terraform_plan_json("input.json")

provider_args_1 = {
    "operation_type": "resource_changes",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "enable_dns_hostnames",
}

provider_args_2 = {
    "operation_type": "resource_changes",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "enable_dns_support",
}


@pytest.mark.passing
def test_get_attribute_name_passing1():
    res = handler.provide(provider_args_1, input_data)
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


@pytest.mark.passing
def test_get_attribute_name_passing2():
    res = handler.provide(provider_args_1, input_data)
    assert res[0]["value"] == False


@pytest.mark.passing
def test_get_attribute_name_passing3():
    res = handler.provide(provider_args_2, input_data)
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


@pytest.mark.passing
def test_get_attribute_name_passing4():
    res = handler.provide(provider_args_2, input_data)
    assert res[0]["value"] == True


# actions
provider_args_4 = {
    "operation_type": "resource_changes_actions",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "actions",
}


@pytest.mark.passing
def test_get_attribute_name_passing5():
    res = handler.provide(provider_args_4, input_data)
    assert res[0]["value"] == ["create"]


@pytest.mark.failing
def test_get_attribute_name_failing6():
    res = handler.provide(provider_args_4, input_data)
    assert res[0]["value"] != ["create"]


# count
provider_args_3 = {
    "operation_type": "resource_changes_count",
    "terraform_resource_type": "aws_vpc",
    "terraform_resource_attribute": "index",
}


@pytest.mark.passing
def test_get_attribute_name_passing7():
    res = handler.provide(provider_args_3, input_data)
    assert res[0]["value"] >= 0


@pytest.mark.failing
def test_get_attribute_name_failing8():
    res = handler.provide(provider_args_3, input_data)
    assert res[0]["value"] == 0
