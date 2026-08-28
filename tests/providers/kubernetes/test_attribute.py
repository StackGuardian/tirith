import os

from tirith.core.core import start_policy_evaluation


def test_get_value():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    input_path = os.path.join(test_dir, "input.yml")
    policy_path = os.path.join(test_dir, "policy.json")

    result = start_policy_evaluation(policy_path=policy_path, input_path=input_path)
    assert result["final_result"] is False

    # This provider does not attach a result context, so its messages carry no prefix
    for item in result["evaluators"][0]["result"]:
        assert "context" not in item
        assert item["message"].startswith("Found ")
