import ast
import json
import logging
import re
import yaml
from types import CodeType

from typing import Any, Dict, List, Tuple, Optional

from tirith.providers.common import ProviderError
from ..providers import PROVIDERS_DICT
from .evaluators import EVALUATORS_DICT
from .policy_parameterization import get_policy_with_vars_replaced


logger = logging.getLogger(__name__)


def get_evaluator_inputs_from_provider_inputs(provider_inputs, provider_module, input_data):
    # TODO: Get the inputs from given providers
    provider_func = PROVIDERS_DICT.get(provider_module)

    if provider_func is None:
        logger.error(f"Provider '{provider_module}' is not found")
        return []
    return provider_func(provider_inputs, input_data)


def generate_evaluator_result(evaluator_obj, input_data, provider_module):
    DEFAULT_ERROR_TOLERANCE = 0

    eval_id = evaluator_obj.get("id")
    provider_inputs = evaluator_obj.get("provider_args")
    condition = evaluator_obj.get("condition")
    evaluator_name: str = condition.get("type")
    evaluator_data = condition.get("value")
    evaluator_error_tolerance: int = condition.get("error_tolerance", DEFAULT_ERROR_TOLERANCE)

    if not condition:
        logger.error("condition key is not supplied.")

    evaluator_inputs = get_evaluator_inputs_from_provider_inputs(
        provider_inputs, provider_module, input_data
    )  # always an array of inputs for evaluators

    result = {
        "id": eval_id,
        "passed": False,
    }
    evaluator_class = EVALUATORS_DICT.get(evaluator_name)
    if evaluator_class is None:
        logger.error(f"{evaluator_name} is not a supported evaluator")
        return result

    evaluator_instance = evaluator_class()
    evaluation_results = []
    has_evaluation_passed = True

    # If there are no evaluator inputs, it means the provider didn't find any resources
    # In this case, the evaluation should fail
    if not evaluator_inputs:
        has_evaluation_passed = False
        evaluation_results = [{"passed": False, "message": "Could not find input value"}]
    else:
        # Track if we've had at least one valid evaluation (not skipped)
        has_valid_evaluation = False

        for evaluator_input in evaluator_inputs:
            if isinstance(evaluator_input["value"], ProviderError) and evaluator_input.get("err", None):
                severity_value = evaluator_input["value"].severity_value
                err_result = dict(message=evaluator_input["err"])

                if severity_value > evaluator_error_tolerance:
                    err_result.update(dict(passed=False))
                    evaluation_results.append(err_result)
                    has_evaluation_passed = False
                    continue
                # Mark as skipped evaluation
                err_result.update(dict(passed=None))
                evaluation_results.append(err_result)
                has_evaluation_passed = None
                continue

            # Run evaluation on the provider's input value
            evaluation_result = evaluator_instance.evaluate(evaluator_input["value"], evaluator_data)

            # Copy metadata and address if provided by the provider
            if "meta" in evaluator_input:
                evaluation_result["meta"] = evaluator_input["meta"]

            # Copy address directly if provided
            if "address" in evaluator_input:
                evaluation_result["address"] = evaluator_input["address"]

            evaluation_results.append(evaluation_result)
            has_valid_evaluation = True

            if not evaluation_result["passed"]:
                has_evaluation_passed = False

        # If all evaluations were skipped, we need to make sure the overall result is 'None'
        if not has_valid_evaluation and has_evaluation_passed is None:
            has_evaluation_passed = None

    result["result"] = evaluation_results
    result["passed"] = has_evaluation_passed
    return result


def generate_compiled_code_without_none_and_variables(eval_str: str) -> Tuple[Optional[CodeType], List[str]]:
    # To make sure that the AST tree loop doesn't run forever
    MAX_TRIES = 2000

    logger.debug(f"eval_str: {eval_str}")

    deleted_var_names: List[str] = []

    class RemoveNoneConstantAndName(ast.NodeTransformer):
        def visit_Constant(self, node: ast.Constant) -> Any:
            if node.value is None:
                return None
            self.generic_visit(node)
            return node

        def visit_Name(self, node: ast.Name) -> Any:
            deleted_var_names.append(node.id)
            return None

    class FixBoolOp(ast.NodeTransformer):
        def visit_BoolOp(self, node: ast.BoolOp) -> Any:
            if len(node.values) == 1:
                # When there's only one child of a BoolOp, make that child
                # as the parent so the tree becomes valid
                return node.values[0]
            if len(node.values) == 0:
                # Consider if we need to return a True node here instead
                return None
            self.generic_visit(node)
            return node

    class FixUnaryOp(ast.NodeTransformer):
        def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
            if getattr(node, "operand", None) is None:
                # When UnaryOp has no child, delete the node
                return None
            self.generic_visit(node)
            return node

    tree = ast.parse(eval_str, mode="eval")

    compiled_code = None
    tries_count = 0
    is_tree_compilable = False
    while not is_tree_compilable and tries_count <= MAX_TRIES:
        try:
            tries_count += 1
            # Clean the tree from None (skip mark) and any variable names
            tree = RemoveNoneConstantAndName().visit(tree)

            if getattr(tree, "body", None) is None:
                tree.body = ast.Constant(value=None)

            ast.fix_missing_locations(tree)
            compiled_code = compile(tree, "<string>", "eval")
            is_tree_compilable = True
        except ValueError as e:
            logger.debug(e)
            tree = FixBoolOp().visit(tree)
        except TypeError as e:
            logger.debug(e)
            tree = FixUnaryOp().visit(tree)

    return compiled_code, deleted_var_names


def final_evaluator(eval_string: str, eval_id_values: Dict[str, Optional[bool]]) -> Tuple[bool, List[str]]:
    """
    Evaluate a given boolean expression string `eval_string` based on the boolean
    values provided by `eval_id_values`.

    Variable that has the value of `None` (we use it to mark a check as skipped) will
    be removed from the expression. This is due to the truthy value of None equals to False
    which will interfere with the final evaluation result.

    All variables that are used within `eval_string` but not in `eval_id_values` will be
    removed from the `eval_string` prior processing the `eval_string`.

    Example usage:
    >>> final_evaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
        "pol_check_1":False,
        "pol_check_2":True,
        "pol_check_3":True,
        "pol_check_4":False
    })
    """
    logger.debug("Running final evaluator")
    for key in eval_id_values:
        regex_string = "\\b" + key + "\\b"
        eval_string = re.sub(regex_string, str(eval_id_values[key]), eval_string)
        # eval_string = eval_string.replace(key, str(eval_id_values[key]["passed"]))
        # print (eval_string)

    # TODO: shall we use and, or and not instead of symbols?
    eval_string = (
        eval_string.replace(" ", "").replace("&&", " and ").replace("||", " or ").replace("!", " not ").strip()
    )

    compiled_code, deleted_var_names = generate_compiled_code_without_none_and_variables(eval_string)
    if compiled_code is None:
        return False, [
            "Could not evaluate the eval expression. Please report this error to https://github.com/StackGuardian/tirith"
        ]

    if compiled_code.co_names:
        # Since every variables has been replaced by its literal value (True, False, None) or removed
        # prior to this (if undefined or None), any names that exist after this are mostly trying
        # to do some kind of malicious act
        error = "The following symbols are not allowed: " + ", ".join(compiled_code.co_names)
        return False, [error]

    # Remove local and global variables scope from eval environment so that it is safe
    final_eval_result = eval(compiled_code, {"__builtins__": {}}, {})

    if deleted_var_names:
        error = "The following evaluator ids are not defined and have been removed: " + ", ".join(deleted_var_names)
        return final_eval_result, [error]
    return final_eval_result, []


def start_policy_evaluation(
    policy_path: str, input_path: str, var_paths: List[str] = [], inline_vars: List[str] = []
) -> Dict:
    """
    Start Tirith policy evaluation from policy file, input file, and optional variable files.

    :param policy_path: Path to the policy file
    :param input_path: Path to the input file
    :param var_paths: List of paths to the variable files
    :return: Policy evaluation result
    """
    with open(policy_path) as f:
        policy_data = json.load(f)
    # TODO: validate policy_data against schema

    with open(input_path) as f:
        if input_path.endswith(".yaml") or input_path.endswith(".yml"):
            # safe_load_all returns a generator, we need to convert it into a
            # dictionary because start_policy_evaluation_from_dict expects a dictionary
            input_data = dict(yamls=list(yaml.safe_load_all(f)))
        else:
            input_data = json.load(f)
    # TODO: validate input_data using the optionally available validate function in provider

    # TODO: Move this logic into another module
    # Merge policy variables into one dictionary
    var_dicts = []
    for var_path in var_paths:
        with open(var_path, encoding="utf-8") as f:
            var_dicts.append(json.load(f))

    merged_var_dict = _merge_var_dicts(var_dicts)

    variable_pattern = re.compile(r"(?P<var_name>\w+)=(?P<var_json>.+)")
    for inline_var in inline_vars:
        match = re.fullmatch(variable_pattern, inline_var)
        if match:
            try:
                merged_var_dict[match.group("var_name")] = json.loads(match.group("var_json"))
            except json.JSONDecodeError:
                logger.error(f"Failed to parse inline variable: {inline_var}")
        else:
            logger.error(f"Invalid inline variable: {inline_var}")

    return start_policy_evaluation_from_dict(policy_data, input_data, merged_var_dict)


def _merge_var_dicts(var_dicts: List[dict]) -> dict:
    """
    Utility to merge var_dicts

    :param var_dicts:  List of var dictionaries
    :return:           A merged dictionary
    """
    merged_var_dict = {}
    for var_dict in var_dicts:
        merged_var_dict.update(var_dict)
    return merged_var_dict


def start_policy_evaluation_from_dict(policy_dict: Dict, input_dict: Dict, var_dict: Dict = {}) -> Dict:
    policy_dict, not_found_vars = get_policy_with_vars_replaced(policy_dict, var_dict)
    if not_found_vars:
        return {"errors": [f"Variables not found: {', '.join(not_found_vars)}"]}

    policy_meta = policy_dict.get("meta")
    eval_objects = policy_dict.get("evaluators")

    final_evaluation_policy_string = policy_dict.get("eval_expression")
    provider_module = policy_meta.get("required_provider", "core")
    # TODO: Write functionality for dynamically importing evaluators from other modules.
    eval_results = []
    eval_results_obj = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        eval_description = eval_obj.get("description")
        logger.debug(f"Processing evaluator '{eval_id}'")
        eval_result = generate_evaluator_result(eval_obj, input_dict, provider_module)
        eval_result["id"] = eval_id
        eval_result["description"] = eval_description
        eval_results_obj[eval_id] = eval_result["passed"]
        eval_results.append(eval_result)
    final_evaluation_result, errors = final_evaluator(final_evaluation_policy_string, eval_results_obj)

    final_output = {
        "meta": {"version": policy_meta.get("version"), "required_provider": provider_module},
        "final_result": final_evaluation_result,
        "evaluators": eval_results,
        "errors": errors,
        "eval_expression": final_evaluation_policy_string,
    }
    return final_output
