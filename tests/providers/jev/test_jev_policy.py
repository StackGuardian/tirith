import copy
import json
import os

import pytest

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers.jev import client, handler

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def _load(name):
    with open(os.path.join(TEST_DIR, name)) as f:
        return json.load(f)


POLICY = _load("policy.json")
INPUT = _load("input.json")


def _evaluator(result, evaluator_id):
    (found,) = [evaluator for evaluator in result["evaluators"] if evaluator["id"] == evaluator_id]
    return found


def _with_tolerance(tolerance):
    policy = copy.deepcopy(POLICY)
    for evaluator in policy["evaluators"]:
        if tolerance is None:
            evaluator["condition"].pop("error_tolerance", None)
        else:
            evaluator["condition"]["error_tolerance"] = tolerance
    return policy


@pytest.fixture
def jev(monkeypatch):
    def install(noul=0.05, choice_confidence=0.9, score=0.4, error=None):
        answers = {
            "noul": {"type": "noul", "noul": noul},
            "choice": {
                "type": "choice",
                "choice": "routine",
                "confidence": choice_confidence,
                "probabilities": {"routine": 0.9, "destructive": 0.1},
            },
            "score": {
                "type": "score",
                "score": score,
                "confidence": 0.8,
                "legend": {"0": "Nothing", "1": "One service", "2": "Several services or shared infrastructure"},
                "probabilities": {"0": 0.6, "1": 0.4, "2": 0.0},
            },
        }
        calls = []

        def fake_ask(state, model, question):
            calls.append({"state": state, "model": model, "question": question})
            if error:
                raise error
            usage = {"input_tokens": 100, "output_tokens": 5}
            return {"answer": answers[question["type"]], "model": "jev-1.13.0", "usage": usage}

        monkeypatch.setattr(handler.client, "ask", fake_ask)
        return calls

    return install


def test_a_policy_passes_when_every_answer_satisfies_its_condition(jev):
    calls = jev()

    result = start_policy_evaluation_from_dict(POLICY, INPUT)

    assert result["final_result"] is True
    (noul_result,) = _evaluator(result, "no_public_exposure")["result"]
    assert noul_result["message"].startswith("[jev] noul: ")
    assert noul_result["context"] == {"label": "jev", "attribute": "noul"}
    assert noul_result["meta"]["model"] == "jev-1.13.0"
    assert calls[0]["state"] == INPUT["resource_changes"]
    assert calls[1]["state"] == INPUT
    assert calls[1]["model"] == "jev-1.13.0"


def test_a_policy_fails_when_an_answer_violates_its_condition(jev):
    jev(noul=0.93)

    result = start_policy_evaluation_from_dict(POLICY, INPUT)

    assert result["final_result"] is False
    assert _evaluator(result, "no_public_exposure")["passed"] is False
    assert _evaluator(result, "blast_radius")["passed"] is True


def test_a_score_between_levels_is_compared_as_a_number(jev):
    jev(score=1.6)

    result = start_policy_evaluation_from_dict(POLICY, INPUT)

    assert _evaluator(result, "blast_radius")["passed"] is False


def test_low_confidence_is_skipped_when_tolerated(jev):
    jev(choice_confidence=0.3)

    result = start_policy_evaluation_from_dict(POLICY, INPUT)

    assert _evaluator(result, "change_kind")["passed"] is None
    assert result["final_result"] is True


def test_low_confidence_fails_when_not_tolerated(jev):
    jev(choice_confidence=0.3)

    result = start_policy_evaluation_from_dict(_with_tolerance(None), INPUT)

    change_kind = _evaluator(result, "change_kind")
    assert change_kind["passed"] is False
    assert "below min_confidence 0.6" in change_kind["result"][0]["message"]
    assert result["final_result"] is False


@pytest.mark.parametrize("tolerance, expected", [(None, False), (1, False), (2, None)])
def test_an_outage_fails_closed_unless_tolerance_reaches_2(jev, tolerance, expected):
    jev(error=client.JevUnavailableError("Jev API returned HTTP 529"))

    result = start_policy_evaluation_from_dict(_with_tolerance(tolerance), INPUT)

    assert [evaluator["passed"] for evaluator in result["evaluators"]] == [expected] * 3


def test_a_rejected_request_fails_whatever_the_tolerance(jev):
    jev(error=client.JevRequestError("Jev API returned HTTP 401"))

    result = start_policy_evaluation_from_dict(_with_tolerance(99), INPUT)

    assert [evaluator["passed"] for evaluator in result["evaluators"]] == [False] * 3
    assert result["final_result"] is False


def test_without_an_api_key_every_check_fails_and_nothing_is_sent(monkeypatch):
    class NoNetwork:
        def open(self, request, timeout=None):
            raise AssertionError("a request was sent without an API key")

    monkeypatch.delenv(client.API_KEY_ENV_VAR, raising=False)
    monkeypatch.setattr(client, "_OPENER", NoNetwork())

    result = start_policy_evaluation_from_dict(POLICY, INPUT)

    assert result["final_result"] is False
    for evaluator in result["evaluators"]:
        assert "TYPESAFE_API_KEY is not set" in evaluator["result"][0]["message"]
