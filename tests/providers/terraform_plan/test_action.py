from tirith.providers.terraform_plan import handler
from utils import load_terraform_plan_json


def test_action_star_resource_type_should_include_every_resource_types() -> None:
    provider_args_dict = {"operation_type": "action", "terraform_resource_type": "*"}
    result = handler.provide(provider_args_dict, load_terraform_plan_json("input_implicit_elb_secgroup.json"))

    assert len(result) == 4
