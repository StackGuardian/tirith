import ast
import json
import logging
import re
import yaml
from types import CodeType

from typing import Any, Dict, List, Tuple, Optional

from tirith.providers.common import ProviderError, format_context_prefix
from ..providers import PROVIDERS_DICT
from .evaluators import EVALUATORS_DICT
from .policy_parameterization import get_policy_with_vars_replaced

logger = logging.getLogger(__name__)

# Provider arguments named in the "could not find input value" message, in the order they
# are rendered. Providers use different argument names, so only the present ones are used.
_NO_INPUT_VALUE_DESCRIBED_ARGS = (
    "operation_type",
    "terraform_resource_type",
    "terraform_resource_attribute",
    "terraform_provider_full_name",
    "kubernetes_kind",
    "attribute_path",
    "attribute",
)


def get_evaluator_inputs_from_provider_inputs(provider_inputs, provider_module, input_data):
    # TODO: Get the inputs from given providers
    provider_func = PROVIDERS_DICT.get(provider_module)

    if provider_func is None:
        logger.error(f"Provider '{provider_module}' is not found")
        return []
    return provider_func(provider_inputs, input_data)


def _no_input_value_message(provider_inputs: Optional[Dict]) -> str:
    """
    Build the message used when a provider returns no inputs at all.

    The bare "Could not find input value" says nothing about what was looked for, so name
    the provider arguments that produced no value whenever they are available.

    :param provider_inputs: The `provider_args` of the evaluator
    :type provider_inputs: Optional[Dict]

    :returns: The message to report against the failed evaluation
    :rtype: str
    """
    BASE_MESSAGE = "Could not find input value"

    if not provider_inputs:
        return BASE_MESSAGE

    described_args = ", ".join(
        f"{key}: '{provider_inputs[key]}'" for key in _NO_INPUT_VALUE_DESCRIBED_ARGS if provider_inputs.get(key)
    )

    if not described_args:
        return BASE_MESSAGE

    return f"{BASE_MESSAGE} for {described_args}"


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
        # Always populate "result" before returning. Consumers (the pretty printer, the
        # workflow-step templates, the platform) index into it unconditionally, and an
        # early return without it used to raise KeyError far away from the real cause.
        result["result"] = [{"passed": False, "message": f"`{evaluator_name}` is not a supported evaluator"}]
        return result

    evaluator_instance = evaluator_class()
    evaluation_results = []
    has_evaluation_passed = True

    # If there are no evaluator inputs, it means the provider didn't find any resources
    # In this case, the evaluation should fail
    if not evaluator_inputs:
        has_evaluation_passed = False
        evaluation_results = [{"passed": False, "message": _no_input_value_message(provider_inputs)}]
    else:
        # Track if we've had at least one valid evaluation (not skipped)
        has_valid_evaluation = False

        for evaluator_input in evaluator_inputs:
            # A provider reported an error without attaching a ProviderError severity. That means a
            # malformed provider call -- an unsupported operation_type, a missing required argument --
            # not a policy violation. Surface the message and fail hard: error_tolerance exists to
            # tolerate missing data, never to mask a broken policy. Without this branch the error text
            # is discarded and `None` is evaluated against the condition, so a typo'd operation_type
            # reads as a genuine violation.
            if evaluator_input.get("err") and not isinstance(evaluator_input["value"], ProviderError):
                evaluation_results.append({"passed": False, "message": evaluator_input["err"]})
                has_evaluation_passed = False
                continue

            if isinstance(evaluator_input["value"], ProviderError) and evaluator_input.get("err", None):
                severity_value = evaluator_input["value"].severity_value
                context = evaluator_input.get("context")
                err_result = dict(message=format_context_prefix(context) + evaluator_input["err"])
                if context:
                    err_result["context"] = context

                if severity_value > evaluator_error_tolerance:
                    err_result.update(dict(passed=False))
                    evaluation_results.append(err_result)
                    has_evaluation_passed = False
                    continue
                # Mark as skipped evaluation
                err_result.update(dict(passed=None))
                evaluation_results.append(err_result)
                # A skip says "nothing to inspect here". It must not erase a `False` a sibling
                # input already produced: the order the provider emits resources is not part of
                # the policy, and an unconditional assignment here made the verdict depend on it.
                # A plan whose first matching resource fails and whose second is a tolerated miss
                # reported `None` (exit 1) instead of the failure (exit 3).
                if has_evaluation_passed is not False:
                    has_evaluation_passed = None
                continue

            evaluation_result = evaluator_instance.evaluate(evaluator_input["value"], evaluator_data)
            context = evaluator_input.get("context")
            if context:
                # Say which resource and attribute the evaluated value came from, both in the
                # message and as structured fields for whoever reads the result document
                evaluation_result["message"] = format_context_prefix(context) + evaluation_result["message"]
                evaluation_result["context"] = context
            evaluation_result["meta"] = evaluator_input.get("meta")
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

    # `&` and `|` parse as BinOp, which nothing below handles: the tree stays uncompilable, the retry
    # loop exhausts, and the caller reports "Could not evaluate the eval expression. Please report this
    # error" -- telling a user to file a bug against their own typo. The README documented `&` in two
    # examples, so this was reachable by copying the docs. Name the operator instead.
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            operators = {ast.BitAnd: ("&", "&&"), ast.BitOr: ("|", "||")}
            wrong, right = operators.get(type(node.op), (None, None))
            if wrong:
                raise ValueError(f"Unsupported operator '{wrong}' in eval_expression. Use '{right}' instead.")
            raise ValueError("Unsupported operator in eval_expression. Only '&&', '||' and '!' are supported.")

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

    input_data = _load_input(input_path)
    merged_var_dict = _load_vars(var_paths, inline_vars)

    return start_policy_evaluation_from_dict(policy_data, input_data, merged_var_dict)


def _load_input(input_path: str):
    """
    Read and parse the input document.

    :param input_path: Path to the input file; parsed as YAML for .yaml/.yml, JSON otherwise
    :return: The parsed document
    """
    with open(input_path) as f:
        if input_path.endswith(".yaml") or input_path.endswith(".yml"):
            input_data = list(yaml.safe_load_all(f))
            if len(input_data) == 1:
                input_data = input_data[0]
        else:
            input_data = json.load(f)
    # TODO: validate input_data using the optionally available validate function in provider
    return input_data


def _load_vars(var_paths: List[str], inline_vars: List[str]) -> dict:
    """
    Merge every variable file, then every inline `-var name=json`, into one dictionary.

    Later sources win, so an inline variable overrides the same name read from a file.

    :param var_paths:   List of paths to the variable files
    :param inline_vars: List of `name=<json>` strings
    :return:            A merged dictionary
    """
    # TODO: Move this logic into another module
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

    return merged_var_dict


def start_policy_set_evaluation(
    policy_paths: List[Tuple[str, str]],
    input_path: str,
    var_paths: List[str] = [],
    inline_vars: List[str] = [],
) -> Dict:
    """
    Evaluate many policies against one input document, and roll their verdicts up into one.

    The input document and the variables are read once and shared, so running a pack of a
    thousand policies parses the plan once rather than a thousand times.

    Each policy keeps its own result document unchanged -- a set run is the single-policy result
    repeated, plus a summary -- so anything that already reads a tirith result can read one
    element of `policies` without knowing it came from a set.

    `skipped` is a first-class outcome and deliberately not a failure. A policy whose resource
    type is absent from the input returns `final_result: None`, and for any pack worth running
    that is the *modal* outcome: most checks do not apply to most plans. Counting those as
    errors would make every pack run red regardless of the infrastructure.

    :param policy_paths: (name, path) pairs; `name` is what the result reports the policy as
    :param input_path:   Path to the input file
    :param var_paths:    List of paths to the variable files
    :param inline_vars:  List of `name=<json>` strings
    :return: {"summary": {...}, "final_result": True|False|None, "policies": [...]}
    """
    input_data = _load_input(input_path)
    merged_var_dict = _load_vars(var_paths, inline_vars)

    results = []
    counts = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errored": 0}

    for name, path in policy_paths:
        counts["total"] += 1
        try:
            with open(path) as f:
                policy_data = json.load(f)
            result = start_policy_evaluation_from_dict(policy_data, input_data, merged_var_dict)
        except Exception as exc:  # noqa: BLE001 - a broken policy is a result we want to report
            # One unreadable policy must not take the run down with it: a pack is shipped
            # content, and the useful answer is "these 999 ran, this one is broken".
            logger.error(f"Could not evaluate policy '{name}': {exc}")
            counts["errored"] += 1
            results.append({"policy": name, "errors": [f"{type(exc).__name__}: {exc}"]})
            continue

        final_result = result.get("final_result")
        if "final_result" not in result:
            # The missing-variables path returns `errors` and no result at all.
            counts["errored"] += 1
        elif final_result is True:
            counts["passed"] += 1
        elif final_result is False:
            counts["failed"] += 1
        else:
            counts["skipped"] += 1

        results.append(dict(policy=name, **result))

    if counts["failed"]:
        set_result = False
    elif counts["passed"]:
        set_result = True
    else:
        # Nothing ran, or nothing that ran reached a verdict. Not a pass.
        set_result = None

    return {"summary": counts, "final_result": set_result, "policies": results}


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

    # Pass policy-declared metadata through to the result, but only the keys that are actually
    # present. Absent keys are omitted rather than emitted as null, so the output of a policy
    # that declares none of them is byte-identical to what it was before this was added.
    final_output_meta = {"version": policy_meta.get("version"), "required_provider": provider_module}
    for meta_key in ("id", "name", "description", "severity", "enforcement", "tags", "remediation"):
        if meta_key in policy_meta:
            final_output_meta[meta_key] = policy_meta[meta_key]

    final_output = {
        "meta": final_output_meta,
        "final_result": final_evaluation_result,
        "evaluators": eval_results,
        "errors": errors,
        "eval_expression": final_evaluation_policy_string,
    }
    return final_output
