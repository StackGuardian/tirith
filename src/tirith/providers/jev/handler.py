import json
from typing import Any, Callable, Dict, List, Optional

from ..common import ProviderError, create_result_dict, get_path_value_from_input
from . import client

DEFAULT_MODEL = "jev-latest"
MAX_CHOICE_OPTIONS = 255
MIN_SCORE_LEVELS = 2
MAX_SCORE_LEVELS = 10
LOW_CONFIDENCE_SEVERITY = 1
STATE_NOT_FOUND_SEVERITY = 2
UNAVAILABLE_SEVERITY = 2
ANSWER_META_KEYS = ("confidence", "probabilities", "legend")
KNOWN_ARGS = frozenset(("operation_type", "instructions", "criteria", "state_path", "model", "min_confidence"))


def _noul_criteria_error(criteria: Any) -> Optional[str]:
    if criteria is not None and not isinstance(criteria, dict):
        return "criteria must be an object with `true` and `false` descriptions"
    return None


def _choice_criteria_error(criteria: Any) -> Optional[str]:
    if not isinstance(criteria, dict) or not 1 <= len(criteria) <= MAX_CHOICE_OPTIONS:
        return f"criteria must be an object of 1 to {MAX_CHOICE_OPTIONS} options"
    return None


def _score_criteria_error(criteria: Any) -> Optional[str]:
    if not isinstance(criteria, list) or not MIN_SCORE_LEVELS <= len(criteria) <= MAX_SCORE_LEVELS:
        return f"criteria must be a list of {MIN_SCORE_LEVELS} to {MAX_SCORE_LEVELS} levels"
    return None


SUPPORTED_OPS: Dict[str, Callable] = {
    "noul": _noul_criteria_error,
    "choice": _choice_criteria_error,
    "score": _score_criteria_error,
}


def _is_number_between(value: Any, low: float, high: float) -> bool:
    # False for NaN, which would otherwise slip through every threshold comparison
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def _min_confidence_error(min_confidence: Any, operation_type: str) -> Optional[str]:
    if min_confidence is None:
        return None
    if operation_type == "noul":
        return "min_confidence is not supported for operation_type 'noul', which reports no confidence"
    if not _is_number_between(min_confidence, 0, 1):
        return "min_confidence must be a number from 0 to 1"
    return None


def _args_error(provider_args: Dict, operation_type: str) -> Optional[str]:
    # Other providers ignore a key they do not read. Here a mistyped state_path would send the whole document
    unknown_args = sorted(set(provider_args) - KNOWN_ARGS)
    if unknown_args:
        return f"unsupported arguments: {', '.join(unknown_args)}"
    if not provider_args.get("instructions"):
        return "instructions must be provided"
    criteria_error = SUPPORTED_OPS[operation_type](provider_args.get("criteria"))
    if criteria_error:
        return criteria_error
    if not isinstance(provider_args.get("state_path", ""), str):
        return "state_path must be a string"
    model = provider_args.get("model", DEFAULT_MODEL)
    if not isinstance(model, str) or not model:
        return "model must be a non-empty string"
    return _min_confidence_error(provider_args.get("min_confidence"), operation_type)


def _result(context: Dict, value: Any = None, meta: Optional[Dict] = None, err: Optional[str] = None) -> Dict:
    return dict(create_result_dict(value=value, meta=meta, err=err), context=context)


def _question(provider_args: Dict, operation_type: str) -> Dict:
    question = {"type": operation_type, "instructions": provider_args["instructions"]}
    if provider_args.get("criteria") is None:
        return question
    return dict(question, criteria=provider_args["criteria"])


def _state(values: List[Any]) -> Any:
    state = values[0] if len(values) == 1 else values
    # Jev accepts a string, an object or an array, so a bare number, boolean or null goes as its JSON text
    return state if isinstance(state, (str, dict, list)) else json.dumps(state, default=str)


def _meta(response: Dict) -> Dict:
    answer = response["answer"]
    candidates = dict(
        {key: answer.get(key) for key in ANSWER_META_KEYS},
        model=response.get("model"),
        usage=response.get("usage"),
    )
    return {key: value for key, value in candidates.items() if value is not None}


def _is_usable_value(value: Any, operation_type: str, criteria: Any) -> bool:
    if operation_type == "choice":
        return isinstance(value, str) and value in criteria
    highest = 1 if operation_type == "noul" else len(criteria) - 1
    return _is_number_between(value, 0, highest)


def _result_from_response(response: Dict, provider_args: Dict, context: Dict) -> Dict:
    operation_type = provider_args["operation_type"]
    answer = response["answer"]
    value = answer.get(operation_type)
    # A value outside the question's own terms is not an answer, and judging it could pass a check
    if not _is_usable_value(value, operation_type, provider_args.get("criteria")):
        return _result(context, err=f"Jev API response carries no usable `{operation_type}` value")

    min_confidence = provider_args.get("min_confidence")
    if min_confidence is not None:
        confidence = answer.get("confidence")
        if not _is_number_between(confidence, 0, 1):
            return _result(context, err="Jev API response carries no confidence to compare with min_confidence")
        if confidence < min_confidence:
            return _result(
                context,
                value=ProviderError(severity_value=LOW_CONFIDENCE_SEVERITY),
                err=f"`{value}` has confidence {confidence}, below min_confidence {min_confidence} "
                f"(severity: {LOW_CONFIDENCE_SEVERITY})",
            )

    return _result(context, value=value, meta=_meta(response))


def provide(provider_args: Dict, input_data: Any) -> List[Dict]:
    operation_type = provider_args.get("operation_type")
    if not isinstance(operation_type, str) or operation_type not in SUPPORTED_OPS:
        return [create_result_dict(err=f"operation_type: '{operation_type}' is not supported")]

    args_error = _args_error(provider_args, operation_type)
    if args_error:
        return [create_result_dict(err=args_error)]

    context = {"label": "jev", "attribute": operation_type}
    state_path = provider_args.get("state_path", "")
    state_values = get_path_value_from_input(state_path, input_data)
    if not state_values:
        return [
            _result(
                context,
                value=ProviderError(severity_value=STATE_NOT_FOUND_SEVERITY),
                err=f"state_path: `{state_path}` is not found (severity: {STATE_NOT_FOUND_SEVERITY})",
            )
        ]

    try:
        response = client.ask(
            _state(state_values),
            provider_args.get("model", DEFAULT_MODEL),
            _question(provider_args, operation_type),
        )
    except client.JevRequestError as e:
        return [_result(context, err=str(e))]
    except client.JevUnavailableError as e:
        return [
            _result(
                context,
                value=ProviderError(severity_value=UNAVAILABLE_SEVERITY),
                err=f"{e} (severity: {UNAVAILABLE_SEVERITY})",
            )
        ]

    return [_result_from_response(response, provider_args, context)]
