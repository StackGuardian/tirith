import http.client
import json
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
MAX_ERROR_DETAIL_CHARS = 300


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
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        raise JevRequestError(f"{API_KEY_ENV_VAR} is not set")

    payload = {"state": state, "model": model, "questions": {QUESTION_ID: question}}
    request = urllib.request.Request(
        API_URL,
        # default=str: a YAML input can hold dates, which JSON has no type for
        data=json.dumps(payload, default=str).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    response = _send_with_retries(request)

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
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == RATE_LIMITED_STATUS or e.code >= FIRST_SERVER_ERROR_STATUS:
            raise JevUnavailableError(f"Jev API returned HTTP {e.code}") from e
        detail = e.read().decode("utf-8", errors="replace")[:MAX_ERROR_DETAIL_CHARS].strip()
        raise JevRequestError(f"Jev API returned HTTP {e.code}" + (f": {detail}" if detail else "")) from e
    except (OSError, http.client.HTTPException) as e:
        raise JevUnavailableError(f"Jev API could not be reached: {e}") from e
    except ValueError as e:
        raise JevRequestError("Jev API returned a response that is not JSON") from e
