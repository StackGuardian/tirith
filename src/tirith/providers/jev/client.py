import http.client
import json
import math
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict

API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY_ENV_VAR = "TYPESAFE_API_KEY"
QUESTION_ID = "answer"
TIMEOUT_SECONDS = 30
RETRY_DELAYS_SECONDS = (1, 2)
RATE_LIMITED_STATUS = 429
FIRST_SERVER_ERROR_STATUS = 500
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_ERROR_DETAIL_CHARS = 300
REDACTED = "[redacted]"


class JevRequestError(Exception):
    """The request cannot succeed as written, so retrying or tolerating it is pointless."""


class JevUnavailableError(Exception):
    """The service was unreachable or overloaded, so the same request may succeed later."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    # urllib re-sends the Authorization header to wherever a redirect points
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def ask(state: Any, model: str, question: Dict) -> Dict:
    """
    Ask Jev one question about a state.

    :param state: The content to judge: a string, an object or an array
    :param model: The model id or alias
    :param question: The question object, with ``type``, ``instructions`` and optional ``criteria``
    :returns: The ``answer`` object, and the ``model`` and ``usage`` the API reported
    :raises JevRequestError: When the request cannot succeed as written
    :raises JevUnavailableError: When the service stayed unavailable through every retry
    """
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        raise JevRequestError(f"{API_KEY_ENV_VAR} is not set")

    payload = {"state": state, "model": model, "questions": {QUESTION_ID: question}}
    try:
        # default=str: a YAML input can hold dates, which JSON has no type for
        data = json.dumps(payload, default=str).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as e:
        raise JevRequestError(f"The state cannot be encoded as JSON: {e}") from e

    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        response = _send_with_retries(request)
    except (JevRequestError, JevUnavailableError) as e:
        # Whatever the far end or the network echoed back, the key stays out of the result document
        raise type(e)(str(e).replace(api_key, REDACTED)) from None

    answers = response.get("answers") if isinstance(response, dict) else None
    answer = answers.get(QUESTION_ID) if isinstance(answers, dict) else None
    if not isinstance(answer, dict):
        raise JevRequestError("Jev API response carries no answer")
    return {"answer": answer, "model": response.get("model"), "usage": response.get("usage")}


def _send_with_retries(request: urllib.request.Request) -> Any:
    for delay in RETRY_DELAYS_SECONDS:
        try:
            return _send(request)
        except JevUnavailableError:
            time.sleep(delay)
    return _send(request)


def _send(request: urllib.request.Request) -> Any:
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as e:
        if e.code == RATE_LIMITED_STATUS or e.code >= FIRST_SERVER_ERROR_STATUS:
            raise JevUnavailableError(f"Jev API returned HTTP {e.code}") from e
        detail = _error_detail(e)
        raise JevRequestError(f"Jev API returned HTTP {e.code}" + (f": {detail}" if detail else "")) from e
    except (OSError, http.client.HTTPException) as e:
        raise JevUnavailableError(f"Jev API could not be reached: {e}") from e
    except ValueError as e:
        # http.client refuses a header value that holds a newline or another control character
        raise JevRequestError(f"{API_KEY_ENV_VAR} holds characters an HTTP header cannot carry") from e

    if len(body) > MAX_RESPONSE_BYTES:
        raise JevRequestError(f"Jev API response is larger than {MAX_RESPONSE_BYTES} bytes")
    try:
        return json.loads(body.decode("utf-8"), parse_float=_finite_float, parse_constant=_finite_float)
    except (ValueError, RecursionError) as e:
        raise JevRequestError("Jev API returned a response that is not JSON") from e


def _finite_float(text: str) -> float:
    # Python's json accepts NaN and Infinity, and NaN compares false to everything, threshold checks included
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"{text} is not a JSON number")
    return value


def _error_detail(error: urllib.error.HTTPError) -> str:
    """
    Return the API's own description of a rejected request, or an empty string.

    Only its message fields are used, never the raw body: a validation error can echo the
    offending input back, and that input is the state.
    """
    try:
        body = json.loads(error.read(MAX_RESPONSE_BYTES).decode("utf-8"))
    except (OSError, http.client.HTTPException, ValueError, RecursionError):
        return ""
    detail = body.get("detail") if isinstance(body, dict) else None
    entries = detail if isinstance(detail, list) else [detail]
    text = "; ".join(filter(None, (_error_entry_text(entry) for entry in entries)))
    return "".join(character for character in text if character.isprintable())[:MAX_ERROR_DETAIL_CHARS]


def _error_entry_text(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, dict):
        return ""
    message = entry.get("message") or entry.get("msg")
    if not isinstance(message, str):
        return ""
    location = entry.get("loc")
    if isinstance(location, list):
        return ".".join(str(part) for part in location) + ": " + message
    return message
