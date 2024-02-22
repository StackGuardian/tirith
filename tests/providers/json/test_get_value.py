import json
import os

from tirith.core.core import start_policy_evaluation_from_dict


# TODO: Need to split this into multiple tests
def test_get_value():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(test_dir, "input.json")) as f:
        input_data = json.load(f)
    with open(os.path.join(test_dir, "policy.json")) as f:
        policy = json.load(f)

    result = start_policy_evaluation_from_dict(policy, input_data)
    assert result["final_result"] == True
