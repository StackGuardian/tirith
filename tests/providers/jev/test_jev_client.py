import datetime
import http.client
import io
import json
import socket
import urllib.error

import pytest

from tirith.providers.jev import client

API_KEY = "sk-test-secret"
QUESTION = {"type": "noul", "instructions": "Is anything public?"}
NOUL_ANSWER = {"type": "noul", "noul": 0.95}
USAGE = {"input_tokens": 296, "output_tokens": 20}


class FakeResponse:
    def __init__(self, body):
        self._body = body

    def read(self, amount=None):
        return self._body if amount is None else self._body[:amount]

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def _ok(answer=NOUL_ANSWER):
    body = {"model": "jev-1.13.0", "answers": {client.QUESTION_ID: answer}, "usage": USAGE}
    return FakeResponse(json.dumps(body).encode("utf-8"))


API_ERROR_BODY = (
    b'{"detail": {"error_type": "authentication_error", "message": "Cannot authenticate with the server."}}'
)


def _http_error(code, body=API_ERROR_BODY):
    return urllib.error.HTTPError(client.API_URL, code, "error", {}, io.BytesIO(body))


TRANSIENT_FAILURES = {
    "429": lambda: _http_error(429),
    "500": lambda: _http_error(500),
    "529": lambda: _http_error(529),
    "connection": lambda: urllib.error.URLError("connection refused"),
    "timeout": lambda: socket.timeout("timed out"),
    "truncated": lambda: http.client.IncompleteRead(b""),
}


class Transport:
    def __init__(self, sleeps):
        self.script = []
        self.requests = []
        self.timeouts = []
        self.sleeps = sleeps

    def open(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        outcome = self.script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def transport(monkeypatch):
    monkeypatch.setenv(client.API_KEY_ENV_VAR, API_KEY)
    sleeps = []
    monkeypatch.setattr(client.time, "sleep", sleeps.append)
    fake = Transport(sleeps)
    monkeypatch.setattr(client, "_OPENER", fake)
    return fake


def test_request_carries_the_state_model_question_and_key(transport):
    transport.script = [_ok()]

    client.ask({"a": 1}, "jev-latest", QUESTION)

    (request,) = transport.requests
    assert request.full_url == "https://api.typesafe.ai/v1/systemone"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer " + API_KEY
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {
        "state": {"a": 1},
        "model": "jev-latest",
        "questions": {client.QUESTION_ID: QUESTION},
    }
    assert transport.timeouts == [client.TIMEOUT_SECONDS]


def test_answer_model_and_usage_are_returned(transport):
    transport.script = [_ok()]

    assert client.ask("state", "jev-latest", QUESTION) == {
        "answer": NOUL_ANSWER,
        "model": "jev-1.13.0",
        "usage": USAGE,
    }


def test_missing_api_key_fails_before_any_request(transport, monkeypatch):
    monkeypatch.delenv(client.API_KEY_ENV_VAR)

    with pytest.raises(client.JevRequestError, match="TYPESAFE_API_KEY is not set"):
        client.ask("state", "jev-latest", QUESTION)

    assert transport.requests == []


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_client_errors_fail_at_once_with_the_api_message(transport, status):
    transport.script = [_http_error(status)]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert str(raised.value) == "Jev API returned HTTP {}: Cannot authenticate with the server.".format(status)
    assert len(transport.requests) == 1
    assert transport.sleeps == []


def test_a_long_error_message_is_truncated(transport):
    transport.script = [_http_error(422, json.dumps({"detail": "x" * 5000}).encode("utf-8"))]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert len(str(raised.value)) < 400


def test_a_redirect_is_an_error_not_a_second_request(transport):
    transport.script = [_http_error(302)]

    with pytest.raises(client.JevRequestError, match="HTTP 302"):
        client.ask("state", "jev-latest", QUESTION)

    assert len(transport.requests) == 1


def test_the_real_opener_refuses_to_follow_redirects():
    handlers = [h for h in client._OPENER.handlers if isinstance(h, client._NoRedirectHandler)]

    assert len(handlers) == 1
    assert handlers[0].redirect_request(None, None, 302, "Found", {}, "https://elsewhere.example") is None


@pytest.mark.parametrize("failure", sorted(TRANSIENT_FAILURES))
def test_transient_failures_are_retried_until_one_succeeds(transport, failure):
    make = TRANSIENT_FAILURES[failure]
    transport.script = [make(), make(), _ok()]

    assert client.ask("state", "jev-latest", QUESTION)["answer"] == NOUL_ANSWER
    assert len(transport.requests) == 3
    assert transport.sleeps == [1, 2]


@pytest.mark.parametrize("failure", sorted(TRANSIENT_FAILURES))
def test_transient_failures_give_up_after_two_retries(transport, failure):
    make = TRANSIENT_FAILURES[failure]
    transport.script = [make(), make(), make()]

    with pytest.raises(client.JevUnavailableError):
        client.ask("state", "jev-latest", QUESTION)

    assert len(transport.requests) == 3


def test_a_body_that_is_not_json_is_a_request_error(transport):
    transport.script = [FakeResponse(b"<html>Sign in to the network</html>")]

    with pytest.raises(client.JevRequestError, match="not JSON"):
        client.ask("state", "jev-latest", QUESTION)

    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    "body",
    [[], {}, {"answers": {}}, {"answers": []}, {"answers": {client.QUESTION_ID: "yes"}}],
)
def test_a_response_without_an_answer_is_a_request_error(transport, body):
    transport.script = [FakeResponse(json.dumps(body).encode("utf-8"))]

    with pytest.raises(client.JevRequestError, match="carries no answer"):
        client.ask("state", "jev-latest", QUESTION)


ECHOING_FAILURES = dict(
    TRANSIENT_FAILURES,
    echoed_in_message=lambda: _http_error(401, json.dumps({"detail": {"message": "bad key " + API_KEY}}).encode()),
    echoed_in_detail=lambda: _http_error(401, json.dumps({"detail": API_KEY + " is not valid"}).encode()),
    echoed_by_the_network=lambda: urllib.error.URLError("proxy rejected Bearer " + API_KEY),
)


@pytest.mark.parametrize("failure", sorted(ECHOING_FAILURES))
def test_the_api_key_never_appears_in_an_error(transport, failure):
    make = ECHOING_FAILURES[failure]
    transport.script = [make(), make(), make()]

    with pytest.raises((client.JevRequestError, client.JevUnavailableError)) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert API_KEY not in str(raised.value)


def test_a_value_json_cannot_encode_is_sent_as_text(transport):
    transport.script = [_ok()]

    client.ask({"created": datetime.date(2026, 1, 2)}, "jev-latest", QUESTION)

    assert json.loads(transport.requests[0].data)["state"] == {"created": "2026-01-02"}


def test_non_ascii_state_survives_the_round_trip(transport):
    transport.script = [_ok()]

    client.ask("naïve — 日本", "jev-latest", QUESTION)

    assert json.loads(transport.requests[0].data.decode("utf-8"))["state"] == "naïve — 日本"


VALIDATION_BODY = json.dumps(
    {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "questions", "answer", "criteria"],
                "msg": "Field required",
                "input": {"db_password": "hunter2"},
            }
        ]
    }
).encode("utf-8")


def test_a_validation_error_names_the_field_and_never_echoes_the_input(transport):
    transport.script = [_http_error(422, VALIDATION_BODY)]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask({"db_password": "hunter2"}, "jev-latest", QUESTION)

    assert str(raised.value) == "Jev API returned HTTP 422: body.questions.answer.criteria: Field required"


@pytest.mark.parametrize(
    "body",
    [
        b"<html>Forbidden: hunter2</html>",
        b'{"error": "hunter2"}',
        b'["hunter2"]',
        b'{"detail": {"input": "hunter2"}}',
        b"",
    ],
)
def test_an_error_body_in_an_unknown_shape_is_not_shown(transport, body):
    transport.script = [_http_error(403, body)]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert str(raised.value) == "Jev API returned HTTP 403"


def test_control_characters_in_an_error_message_are_dropped(transport):
    transport.script = [_http_error(401, json.dumps({"detail": "bad\x1b[31m key\n::error::x"}).encode("utf-8"))]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert str(raised.value) == "Jev API returned HTTP 401: bad[31m key::error::x"


def test_an_error_body_that_cannot_be_read_still_gives_a_request_error(transport):
    class Truncated(io.BytesIO):
        def read(self, *args):
            raise http.client.IncompleteRead(b"")

    transport.script = [urllib.error.HTTPError(client.API_URL, 422, "error", {}, Truncated())]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert str(raised.value) == "Jev API returned HTTP 422"


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_a_number_json_does_not_define_is_a_request_error(transport, number):
    body = '{"answers": {"answer": {"type": "noul", "noul": %s}}}' % number
    transport.script = [FakeResponse(body.encode("utf-8"))]

    with pytest.raises(client.JevRequestError, match="not JSON"):
        client.ask("state", "jev-latest", QUESTION)


def test_an_oversized_response_is_a_request_error(transport):
    transport.script = [FakeResponse(b" " * (client.MAX_RESPONSE_BYTES + 1))]

    with pytest.raises(client.JevRequestError, match="larger than"):
        client.ask("state", "jev-latest", QUESTION)


def test_a_deeply_nested_response_is_a_request_error(transport):
    transport.script = [FakeResponse(b"[" * 100000)]

    with pytest.raises(client.JevRequestError, match="not JSON"):
        client.ask("state", "jev-latest", QUESTION)


def test_whitespace_around_the_api_key_is_ignored(transport, monkeypatch):
    monkeypatch.setenv(client.API_KEY_ENV_VAR, API_KEY + "\n")
    transport.script = [_ok()]

    client.ask("state", "jev-latest", QUESTION)

    assert transport.requests[0].get_header("Authorization") == "Bearer " + API_KEY


def _circular():
    state = []
    state.append(state)
    return state


@pytest.mark.parametrize(
    "state",
    [{datetime.date(2026, 1, 2): "shipped"}, {("a", "b"): 1}, _circular()],
    ids=["date key", "tuple key", "circular"],
)
def test_a_state_json_cannot_carry_is_a_request_error_and_nothing_is_sent(transport, state):
    with pytest.raises(client.JevRequestError, match="cannot be encoded as JSON"):
        client.ask(state, "jev-latest", QUESTION)

    assert transport.requests == []
