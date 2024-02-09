from tirith.providers.common import ProviderError
from tirith.providers.terraform_plan import handler
from utils import load_terraform_plan_json


def test_get_terraform_provider_get_region():
    provider_args_dict = {
        "operation_type": "provider_config",
        "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
        "attribute": "region",
    }
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_instance_deps_s3.json"))

    assert len(result) == 1
    assert result[0]["value"] == "eu-central-1"


def test_get_terraform_provider_get_region_not_found():
    provider_args_dict = {
        "operation_type": "provider_config",
        "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
        "attribute": "region",
    }
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_instance_deps_s3_no_region.json"))

    assert len(result) == 1
    assert isinstance(result[0]["value"], ProviderError)
    assert result[0]["value"].severity_value == 2
    assert result[0]["err"] == "`region` is not found in the provider_config (severity_value: 2)"


def test_get_terraform_provider_get_version_constraint_not_found():
    provider_args_dict = {
        "operation_type": "provider_config",
        "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
        "attribute": "version_constraint",
    }
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_instance_deps_s3.json"))

    assert len(result) == 1
    assert isinstance(result[0]["value"], ProviderError)
    assert result[0]["value"].severity_value == 2
    assert result[0]["err"] == "`version_constraint` is not found in the provider_config (severity_value: 2)"


def test_get_terraform_provider_get_version_constraint():
    provider_args_dict = {
        "operation_type": "provider_config",
        "terraform_provider_full_name": "registry.terraform.io/hashicorp/azurerm",
        "attribute": "version_constraint",
    }
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_vnet_destroy_new.json"))

    assert len(result) == 1
    assert result[0]["value"] == ">= 3.11.0, < 4.0.0"
