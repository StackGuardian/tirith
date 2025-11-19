import json
import os

from tirith.core.core import start_policy_evaluation, start_policy_evaluation_from_dict


# TODO: Need to split this into multiple tests
def test_get_value():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(test_dir, "input.json")) as f:
        input_data = json.load(f)
    with open(os.path.join(test_dir, "policy.json")) as f:
        policy = json.load(f)

    result = start_policy_evaluation_from_dict(policy, input_data)
    assert result["final_result"] is True


def test_get_value_playbook():
    """Test get_value with playbook YAML data using wildcard path"""
    test_dir = os.path.dirname(os.path.realpath(__file__))
    input_path = os.path.join(test_dir, "playbook.yml")
    policy_path = os.path.join(test_dir, "policy_playbook.json")

    result = start_policy_evaluation(policy_path=policy_path, input_path=input_path)
    assert result["final_result"] is True
