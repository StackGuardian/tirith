from tirith.core.evaluators import VersionCompare
from pytest import mark

# Define test cases
checks_passing = [
    ("1.0.0", {"value": "1.0.1", "operation": "LessThan"}),
    ("1.0.0", {"value": "1.0.0", "operation": "Equals"}),
    ("2.0.0", {"value": "1.0.0", "operation": "GreaterThan"}),
    ("1.0.0", {"value": "1.1.0", "operation": "LessThanOrEquals"}),
    ("1.1.0", {"value": "1.1.0", "operation": "LessThanOrEquals"}),
    ("1.2.0", {"value": "1.1.0", "operation": "GreaterThanOrEquals"}),
    ("1.1.0", {"value": "1.1.0", "operation": "GreaterThanOrEquals"}),
]

checks_failing = [
    ("1.0.0", {"value": "1.0.1", "operation": "GreaterThan"}),
    ("1.0.0", {"value": "1.0.0", "operation": "LessThan"}),
    ("1.0.1", {"value": "1.0.0", "operation": "LessThan"}),
    ("1.1.0", {"value": "1.0.0", "operation": "Equals"}),
]


evaluator = VersionCompare()


# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    operation = evaluator_data["operation"]
    assert result == {"passed": True, "message": f"{evaluator_input} is {operation} {evaluator_data}"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    operation = evaluator_data["operation"]
    assert result == {"passed": False, "message": f"{evaluator_input} is not {operation} {evaluator_data}"}
