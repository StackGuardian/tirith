from .base_evaluator import BaseEvaluator
from packaging.version import Version
import re


    # Compares two version strings based on the provided operation.

    # Args:
    #     evaluator_input (str): The first version string to compare.
    #     evaluator_data (str): The second version string to compare.
    #     operation (str): The comparison operation to perform.
    #         Supported values: "LessThan", "LessThanOrEquals", "Equals", "GreaterThan", "GreaterThanOrEquals".

    # Returns:
    #     dict: A dictionary containing the comparison result (`passed`) and a descriptive message.

    # Example:
    #
    #     >>> comparator = VersionCompare()
    #     >>> comparator.evaluate("1.0.0", {"value": "1.0.1", "operation": "lessThan"})
    #     {'passed': True, 'message': '1.0.0 is less than 1.0.1'}
    #     >>> comparator.evaluate("1.0.0", {"value": "1.0.0", "operation": "equal"})
    #     {'passed': True, 'message': '1.0.0 is equal to 1.0.0'}
    #     >>> comparator.evaluate("2.0.0", {"value": "1.0.0", "operation": "greaterThan"})
    #     {'passed': True, 'message': '2.0.0 is greater than 1.0.0'}


    # .. versionadded:: 1.0.0



class VersionCompare(BaseEvaluator):
    """Compares two version strings based on the provided operation."""

    def parse_version(self, version_string):
        """Parses a version string and returns a comparable version object."""
        # Extract the version part from the string
        match = re.search(r'[\d]+(\.[\d]+)*(\-[a-zA-Z0-9]+)?$', version_string)
        if match:
            try:
                return Version(match.group(0))
            except Exception as e:
                raise ValueError(f"Invalid version format: {version_string}. Error: {str(e)}")
        else:
            raise ValueError(f"Invalid version format: {version_string}")

    def evaluate(self, evaluator_input, evaluator_data):
        """Compares two version strings based on the provided operation."""
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            v1 = self.parse_version(evaluator_input)
            v2 = self.parse_version(evaluator_data['value'])
            operation = evaluator_data['operation']

            if operation == "LessThan":
                evaluation_result["passed"] = v1 < v2
            elif operation == "LessThanOrEquals":
                evaluation_result["passed"] = v1 <= v2
            elif operation == "Equals":
                evaluation_result["passed"] = v1 == v2
            elif operation == "GreaterThan":
                evaluation_result["passed"] = v1 > v2
            elif operation == "GreaterThanOrEquals":
                evaluation_result["passed"] = v1 >= v2

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            if evaluation_result["passed"]:
                evaluation_result["message"] = f"{evaluator_input} is {operation.replace('_', ' ')} {evaluator_data}"
            else:
                evaluation_result["message"] = f"{evaluator_input} is not {operation.replace('_', ' ')} {evaluator_data}"

            return evaluation_result

        except ValueError as e:
            evaluation_result["message"] = str(e)
            return evaluation_result

