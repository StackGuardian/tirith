import ast
import json
import logging
import re
import yaml

from typing import Dict, List, Tuple, Optional

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

    # If there are no evaluator inputs, it means the provider didn't find any resources
    # In this case, the evaluation should fail
    if not evaluator_inputs:
        has_evaluation_passed = False
        evaluation_results = [{"passed": False, "message": _no_input_value_message(provider_inputs)}]
    else:
        # Roll-up across resources: any failure fails the evaluator; otherwise it passes if at least
        # one resource was actually evaluated; only when every resource was tolerated away is the
        # verdict None (skipped). Tracked as two flags and decided once at the end, so a skip can
        # never overwrite a failure or a pass that came before it (issue #293).
        has_failure = False
        has_valid_evaluation = False

        for evaluator_input in evaluator_inputs:
            # A provider reported an error without attaching a ProviderError severity. That means a
            # malformed provider call -- an unsupported operation_type, a missing required argument --
            # not a policy violation. Surface the message and fail hard: error_tolerance exists to
            # tolerate missing data, never to mask a broken policy. Without this branch the error text
            # is discarded and `None` is evaluated against the condition, so a typo'd operation_type
            # reads as a genuine violation.
            if evaluator_input.get("err") and not isinstance(evaluator_input["value"], ProviderError):
                context = evaluator_input.get("context")
                err_result = {"passed": False, "message": format_context_prefix(context) + evaluator_input["err"]}
                if context:
                    err_result["context"] = context
                evaluation_results.append(err_result)
                has_failure = True
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
                    has_failure = True
                    continue
                # Within tolerance: this resource is skipped and does not touch the verdict
                err_result.update(dict(passed=None))
                evaluation_results.append(err_result)
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
                has_failure = True

        if has_failure:
            has_evaluation_passed = False
        elif has_valid_evaluation:
            has_evaluation_passed = True
        else:
            has_evaluation_passed = None

    result["result"] = evaluation_results
    result["passed"] = has_evaluation_passed
    return result


# An eval_expression is a handful of ids joined by `&&`, `||`, `!` and parentheses. 10k characters is
# orders of magnitude beyond any real policy and keeps a hostile expression from exhausting the parser.
MAX_EVAL_EXPRESSION_LENGTH = 10_000

# The only AST node types an expression may contain after `&&`/`||`/`!` have been rewritten to
# `and`/`or`/`not`. This is an allow-list: anything not named here (calls, lambdas, attribute access,
# subscripts, comprehensions, comparisons, arithmetic, f-strings, ...) is rejected before evaluation.
_ALLOWED_EVAL_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.Constant,
    ast.Name,
    ast.Load,  # the read-context marker every ast.Name carries; it is not an operation
)


def _unsupported_eval_nodes(tree: ast.AST) -> List[str]:
    """
    List the node types in `tree` that an eval_expression is not allowed to contain, in source order.

    Constants other than True, False and None (numbers, strings, ...) are rejected too: the language
    has no literals, and nothing in a policy expression needs one.
    """
    found: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_EVAL_NODES):
            name = type(node).__name__
        elif isinstance(node, ast.Constant) and not (node.value is None or isinstance(node.value, bool)):
            name = "Constant"
        else:
            continue
        if name not in found:
            found.append(name)
    return found


def _evaluate_tree(node: ast.AST, deleted_var_names: List[str]) -> Optional[bool]:
    """
    Evaluate an already-validated expression tree without compiling or executing any Python code.

    Tri-state: returns True/False, or None for "nothing left to evaluate". A skipped check (substituted
    as the literal `None`) and an undefined id are both dropped from the expression rather than being
    treated as false: a `not` of a dropped operand is dropped, a `and`/`or` ignores dropped operands,
    and if every operand is dropped the whole thing is dropped. Undefined ids are appended to
    `deleted_var_names`.

    Every operand is visited even when the result is already decided, so that all undefined ids are
    reported, not only those before the first short-circuit.

    :param node:              A node from a tree that passed `_unsupported_eval_nodes`
    :param deleted_var_names: Collects the undefined ids that were dropped
    """
    if isinstance(node, ast.Expression):
        return _evaluate_tree(node.body, deleted_var_names)
    if isinstance(node, ast.Constant):
        return node.value  # True, False or None; anything else was rejected by the allow-list
    if isinstance(node, ast.Name):
        deleted_var_names.append(node.id)
        return None
    if isinstance(node, ast.UnaryOp):  # only `not` is on the allow-list
        operand = _evaluate_tree(node.operand, deleted_var_names)
        return None if operand is None else (not operand)
    if isinstance(node, ast.BoolOp):
        operands = [_evaluate_tree(value, deleted_var_names) for value in node.values]
        operands = [operand for operand in operands if operand is not None]
        if not operands:
            return None
        return all(operands) if isinstance(node.op, ast.And) else any(operands)
    # Unreachable while the allow-list and this function agree; failing closed if they ever stop doing so.
    raise ValueError(f"Unsupported syntax in eval_expression: {type(node).__name__}")


def final_evaluator(eval_string: str, eval_id_values: Dict[str, Optional[bool]]) -> Tuple[Optional[bool], List[str]]:
    """
    Evaluate a given boolean expression string `eval_string` based on the boolean
    values provided by `eval_id_values`.

    Variable that has the value of `None` (we use it to mark a check as skipped) will
    be removed from the expression. This is due to the truthy value of None equals to False
    which will interfere with the final evaluation result.

    All variables that are used within `eval_string` but not in `eval_id_values` will be
    removed from the `eval_string` prior processing the `eval_string`.

    The expression is parsed into a syntax tree and walked by `_evaluate_tree`; it is never compiled
    to code or passed to `eval`. Only ids, `&&`, `||`, `!` and parentheses are accepted. Anything else
    makes this return `(False, [<error>])` without evaluating any part of the expression.

    :raises ValueError:  If the expression uses `&` or `|`, other operators, or is too long
    :raises SyntaxError: If the expression cannot be parsed

    Example usage:
    >>> final_evaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
        "pol_check_1":False,
        "pol_check_2":True,
        "pol_check_3":True,
        "pol_check_4":False
    })
    """
    logger.debug("Running final evaluator")
    if len(eval_string) > MAX_EVAL_EXPRESSION_LENGTH:
        raise ValueError(f"eval_expression is longer than the {MAX_EVAL_EXPRESSION_LENGTH} characters allowed.")

    for key in eval_id_values:
        regex_string = "\\b" + re.escape(key) + "\\b"
        eval_string = re.sub(regex_string, str(eval_id_values[key]), eval_string)

    # TODO: shall we use and, or and not instead of symbols?
    eval_string = (
        eval_string.replace(" ", "").replace("&&", " and ").replace("||", " or ").replace("!", " not ").strip()
    )
    logger.debug(f"eval_str: {eval_string}")

    try:
        tree = ast.parse(eval_string, mode="eval")

        # `&` and `|` parse as BinOp. Name the operator instead of telling a user to file a bug against
        # their own typo -- the README documented `&` in two examples, so this was reachable by copying
        # the docs. Raised, not returned: an unparseable expression aborts the run (documented, exit 1).
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                operators = {ast.BitAnd: ("&", "&&"), ast.BitOr: ("|", "||")}
                wrong, right = operators.get(type(node.op), (None, None))
                if wrong:
                    raise ValueError(f"Unsupported operator '{wrong}' in eval_expression. Use '{right}' instead.")
                raise ValueError("Unsupported operator in eval_expression. Only '&&', '||' and '!' are supported.")

        unsupported = _unsupported_eval_nodes(tree)
        if unsupported:
            return False, [
                "Unsupported syntax in eval_expression: "
                + ", ".join(unsupported)
                + ". Only evaluator ids, '&&', '||', '!' and parentheses are allowed."
            ]

        deleted_var_names: List[str] = []
        final_eval_result = _evaluate_tree(tree, deleted_var_names)
    except (RecursionError, MemoryError):
        # Too much nesting surfaces differently by interpreter: the 3.8 parser reports "parser stack
        # overflow" as MemoryError, newer ones as RecursionError, and walking a deep tree is a
        # RecursionError everywhere. The length cap rules out a genuine out-of-memory here.
        raise ValueError("eval_expression is nested too deeply to evaluate.")

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
            input_data = list(yaml.safe_load_all(f))
            if len(input_data) == 1:
                input_data = input_data[0]
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
