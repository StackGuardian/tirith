from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers.common import ProviderError
from tirith.providers.terraform_plan import handler

OFFICIAL_CLOUD_PROVIDERS = (
    r"^(registry\.(terraform\.io|opentofu\.org)/hashicorp/(aws|google|google-beta|azurerm|azuread)"
    r"|(?!.*/(aws|google|google-beta|azurerm|azuread)$).*)$"
)


def _plan(*resources):
    return {
        "resource_changes": [
            {
                "address": f"{resource_type}.this",
                "type": resource_type,
                "provider_name": provider_name,
                "change": {"actions": ["create"], "after": {}},
            }
            for resource_type, provider_name in resources
        ]
    }


def _official_providers_policy():
    return {
        "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan"},
        "evaluators": [
            {
                "id": "official_cloud_providers",
                "provider_args": {"operation_type": "provider_name", "terraform_resource_type": "*"},
                "condition": {"type": "RegexMatch", "value": OFFICIAL_CLOUD_PROVIDERS},
            }
        ],
        "eval_expression": "official_cloud_providers",
    }


def test_returns_the_provider_of_every_matching_resource():
    plan = _plan(
        ("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"),
        ("random_id", "registry.terraform.io/hashicorp/random"),
    )

    result = handler.provide({"operation_type": "provider_name", "terraform_resource_type": "*"}, plan)

    assert [r["value"] for r in result] == [
        "registry.terraform.io/hashicorp/aws",
        "registry.terraform.io/hashicorp/random",
    ]
    assert result[0]["context"]["resource_address"] == "aws_s3_bucket.this"


def test_filters_by_resource_type():
    plan = _plan(
        ("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"),
        ("random_id", "registry.terraform.io/hashicorp/random"),
    )

    result = handler.provide({"operation_type": "provider_name", "terraform_resource_type": "random_id"}, plan)

    assert [r["value"] for r in result] == ["registry.terraform.io/hashicorp/random"]


def test_skips_excluded_resource_types_on_wildcard():
    plan = _plan(
        ("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"),
        ("random_id", "registry.terraform.io/hashicorp/random"),
    )

    result = handler.provide(
        {"operation_type": "provider_name", "terraform_resource_type": "*", "exclude_resource_types": ["random_id"]},
        plan,
    )

    assert [r["value"] for r in result] == ["registry.terraform.io/hashicorp/aws"]


def test_missing_resource_type_is_severity_1():
    plan = _plan(("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"))

    result = handler.provide({"operation_type": "provider_name", "terraform_resource_type": "google_bucket"}, plan)

    assert isinstance(result[0]["value"], ProviderError)
    assert result[0]["value"].severity_value == 1


def test_official_and_non_cloud_providers_pass_a_regex_policy():
    plan = _plan(
        ("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"),
        ("google_storage_bucket", "registry.opentofu.org/hashicorp/google"),
        ("random_id", "registry.terraform.io/hashicorp/random"),
        ("kubernetes_namespace", "registry.terraform.io/hashicorp/kubernetes"),
    )

    result = start_policy_evaluation_from_dict(_official_providers_policy(), plan)

    assert result["final_result"] is True


def test_lookalike_cloud_provider_fails_a_regex_policy():
    plan = _plan(
        ("aws_s3_bucket", "registry.terraform.io/hashicorp/aws"),
        ("aws_instance", "registry.terraform.io/acme/aws"),
    )

    result = start_policy_evaluation_from_dict(_official_providers_policy(), plan)

    assert result["final_result"] is False
