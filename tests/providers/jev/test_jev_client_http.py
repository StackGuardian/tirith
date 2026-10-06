import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tirith.providers.jev import client

API_KEY = "sk-test-secret"
QUESTION = {"type": "noul", "instructions": "Is anything public?"}
OK_BODY = json.dumps(
    {
        "model": "jev-1.13.0",
        "answers": {client.QUESTION_ID: {"type": "noul", "noul": 0.95}},
        "usage": {"input_tokens": 296, "output_tokens": 20},
    }
).encode("utf-8")


class Recorder(BaseHTTPRequestHandler):
    def _reply(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.seen.append(
            {
                "method": self.command,
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "body": body,
            }
        )
        status, headers, payload = self.server.replies.pop(0)
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_POST = _reply
    do_GET = _reply

    def log_message(self, *args):
        pass


@pytest.fixture
def server(monkeypatch):
    httpd = HTTPServer(("127.0.0.1", 0), Recorder)
    httpd.seen = []
    httpd.replies = []
    httpd.base_url = "http://127.0.0.1:{}".format(httpd.server_address[1])
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(client, "API_URL", httpd.base_url + "/v1/systemone")
    monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
    monkeypatch.setenv(client.API_KEY_ENV_VAR, API_KEY)
    yield httpd
    httpd.shutdown()
    httpd.server_close()
    thread.join()


def test_a_real_request_carries_the_key_and_the_payload(server):
    server.replies = [(200, {"Content-Type": "application/json"}, OK_BODY)]

    result = client.ask({"a": 1}, "jev-latest", QUESTION)

    assert result["answer"] == {"type": "noul", "noul": 0.95}
    (seen,) = server.seen
    assert seen["method"] == "POST"
    assert seen["path"] == "/v1/systemone"
    assert seen["authorization"] == "Bearer " + API_KEY
    assert json.loads(seen["body"]) == {
        "state": {"a": 1},
        "model": "jev-latest",
        "questions": {client.QUESTION_ID: QUESTION},
    }


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_a_redirect_is_not_followed_so_the_key_goes_nowhere_else(server, status):
    server.replies = [(status, {"Location": server.base_url + "/elsewhere"}, b""), (200, {}, OK_BODY)]

    with pytest.raises(client.JevRequestError, match="HTTP {}".format(status)):
        client.ask("state", "jev-latest", QUESTION)

    assert [seen["path"] for seen in server.seen] == ["/v1/systemone"]


def test_a_validation_error_surfaces_the_api_message(server):
    server.replies = [(422, {"Content-Type": "application/json"}, b'{"detail": "criteria is required"}')]

    with pytest.raises(client.JevRequestError) as raised:
        client.ask("state", "jev-latest", QUESTION)

    assert str(raised.value) == 'Jev API returned HTTP 422: {"detail": "criteria is required"}'
    assert len(server.seen) == 1


def test_an_overloaded_reply_is_retried(server):
    server.replies = [(529, {}, b""), (200, {"Content-Type": "application/json"}, OK_BODY)]

    assert client.ask("state", "jev-latest", QUESTION)["answer"]["noul"] == 0.95
    assert len(server.seen) == 2
