import pytest

from tirith.providers.common import ProviderError
from tirith.providers.jev import client, handler

MODEL = "jev-1.13.0"
USAGE = {"input_tokens": 360, "output_tokens": 39}
NOUL = {"answer": {"type": "noul", "noul": 0.93}, "model": MODEL, "usage": USAGE}
CHOICE_PROBABILITIES = {"routine": 0.9, "destructive": 0.1}
CHOICE = {
    "answer": {"type": "choice", "choice": "routine", "confidence": 0.82, "probabilities": CHOICE_PROBABILITIES},
    "model": MODEL,
    "usage": USAGE,
}
SCORE_LEGEND = {"0": "Low", "1": "Medium", "2": "High"}
SCORE_PROBABILITIES = {"0": 0.0, "1": 0.57, "2": 0.43}
SCORE = {
    "answer": {
        "type": "score",
        "score": 1.43,
        "confidence": 0.35,
        "legend": SCORE_LEGEND,
        "probabilities": SCORE_PROBABILITIES,
    },
    "model": MODEL,
    "usage": USAGE,
}

RESOURCES = [{"type": "aws_s3_bucket", "name": "logs"}, {"type": "aws_instance", "name": "web"}]
INPUT = {"resource_changes": RESOURCES, "terraform_version": "1.9.0", "count": 3, "enabled": True, "nothing": None}

NOUL_ARGS = {"operation_type": "noul", "instructions": "Is anything public?"}
CHOICE_CRITERIA = {"routine": "Config tweaks", "destructive": "Deletes data"}
CHOICE_ARGS = {"operation_type": "choice", "instructions": "What kind of change?", "criteria": CHOICE_CRITERIA}
SCORE_CRITERIA = ["Low", "Medium", "High"]
SCORE_ARGS = {"operation_type": "score", "instructions": "How risky?", "criteria": SCORE_CRITERIA}


def _context(operation_type):
    return {"label": "jev", "attribute": operation_type}


@pytest.fixture
def ask(monkeypatch):
    def install(outcome):
        calls = []

        def fake_ask(state, model, question):
            calls.append({"state": state, "model": model, "question": question})
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        monkeypatch.setattr(handler.client, "ask", fake_ask)
        return calls

    return install


def test_noul_returns_the_probability(ask):
    calls = ask(NOUL)

    result = handler.provide(NOUL_ARGS, INPUT)

    assert result == [
        {"value": 0.93, "meta": {"model": MODEL, "usage": USAGE}, "err": None, "context": _context("noul")}
    ]
    assert calls == [
        {"state": INPUT, "model": "jev-latest", "question": {"type": "noul", "instructions": "Is anything public?"}}
    ]


def test_choice_returns_the_option_and_keeps_the_distribution(ask):
    calls = ask(CHOICE)

    (result,) = handler.provide(CHOICE_ARGS, INPUT)

    assert result["value"] == "routine"
    assert result["meta"] == {
        "confidence": 0.82,
        "probabilities": CHOICE_PROBABILITIES,
        "model": MODEL,
        "usage": USAGE,
    }
    assert result["context"] == _context("choice")
    assert calls[0]["question"] == {
        "type": "choice",
        "instructions": "What kind of change?",
        "criteria": CHOICE_CRITERIA,
    }


def test_score_returns_the_position_and_keeps_the_legend(ask):
    calls = ask(SCORE)

    (result,) = handler.provide(SCORE_ARGS, INPUT)

    assert result["value"] == 1.43
    assert result["meta"] == {
        "confidence": 0.35,
        "probabilities": SCORE_PROBABILITIES,
        "legend": SCORE_LEGEND,
        "model": MODEL,
        "usage": USAGE,
    }
    assert calls[0]["question"]["criteria"] == SCORE_CRITERIA


def test_noul_criteria_and_a_pinned_model_are_passed_through(ask):
    calls = ask(NOUL)
    criteria = {"true": "Reachable from 0.0.0.0/0", "false": "Private only"}

    handler.provide(dict(NOUL_ARGS, criteria=criteria, model="jev-1.13.0"), INPUT)

    assert calls[0]["model"] == "jev-1.13.0"
    assert calls[0]["question"]["criteria"] == criteria


@pytest.mark.parametrize("min_confidence", [0, 0.5, 0.82])
def test_an_answer_at_or_above_min_confidence_is_returned(ask, min_confidence):
    ask(CHOICE)

    (result,) = handler.provide(dict(CHOICE_ARGS, min_confidence=min_confidence), INPUT)

    assert result["value"] == "routine"
    assert result["err"] is None


def test_an_answer_below_min_confidence_is_a_severity_1_error(ask):
    ask(CHOICE)

    (result,) = handler.provide(dict(CHOICE_ARGS, min_confidence=0.9), INPUT)

    assert isinstance(result["value"], ProviderError)
    assert result["value"].severity_value == 1
    assert result["err"] == "`routine` has confidence 0.82, below min_confidence 0.9 (severity: 1)"
    assert result["context"] == _context("choice")


def test_min_confidence_needs_a_confidence_in_the_answer(ask):
    answer = {"type": "choice", "choice": "routine"}
    ask(dict(CHOICE, answer=answer))

    (result,) = handler.provide(dict(CHOICE_ARGS, min_confidence=0.5), INPUT)

    assert result["value"] is None
    assert result["err"] == "Jev API response carries no confidence to compare with min_confidence"


INVALID_ARGS = [
    ({"operation_type": "nope"}, "operation_type: 'nope' is not supported"),
    ({}, "operation_type: 'None' is not supported"),
    ({"operation_type": ["noul"]}, "operation_type: '['noul']' is not supported"),
    ({"operation_type": "noul"}, "instructions must be provided"),
    ({"operation_type": "noul", "instructions": ""}, "instructions must be provided"),
    (dict(NOUL_ARGS, criteria=["yes", "no"]), "criteria must be an object with `true` and `false` descriptions"),
    ({"operation_type": "choice", "instructions": "Which?"}, "criteria must be an object of 1 to 255 options"),
    (dict(CHOICE_ARGS, criteria={}), "criteria must be an object of 1 to 255 options"),
    (dict(CHOICE_ARGS, criteria=["a", "b"]), "criteria must be an object of 1 to 255 options"),
    (
        dict(CHOICE_ARGS, criteria={str(n): None for n in range(256)}),
        "criteria must be an object of 1 to 255 options",
    ),
    ({"operation_type": "score", "instructions": "How?"}, "criteria must be a list of 2 to 10 levels"),
    (dict(SCORE_ARGS, criteria=["only"]), "criteria must be a list of 2 to 10 levels"),
    (dict(SCORE_ARGS, criteria=[str(n) for n in range(11)]), "criteria must be a list of 2 to 10 levels"),
    (dict(SCORE_ARGS, criteria={"0": "Low", "1": "High"}), "criteria must be a list of 2 to 10 levels"),
    (dict(NOUL_ARGS, state_path=3), "state_path must be a string"),
    (dict(NOUL_ARGS, model=""), "model must be a non-empty string"),
    (dict(NOUL_ARGS, model=13), "model must be a non-empty string"),
    (
        dict(NOUL_ARGS, min_confidence=0.5),
        "min_confidence is not supported for operation_type 'noul', which reports no confidence",
    ),
    (dict(CHOICE_ARGS, min_confidence="0.5"), "min_confidence must be a number from 0 to 1"),
    (dict(CHOICE_ARGS, min_confidence=True), "min_confidence must be a number from 0 to 1"),
    (dict(CHOICE_ARGS, min_confidence=1.5), "min_confidence must be a number from 0 to 1"),
    (dict(SCORE_ARGS, min_confidence=-0.1), "min_confidence must be a number from 0 to 1"),
]


@pytest.mark.parametrize("provider_args, expected_err", INVALID_ARGS)
def test_invalid_arguments_fail_without_asking(ask, provider_args, expected_err):
    calls = ask(NOUL)

    assert handler.provide(provider_args, INPUT) == [{"value": None, "meta": None, "err": expected_err}]
    assert calls == []


STATE_CASES = [
    ("resource_changes", INPUT, RESOURCES),
    ("terraform_version", INPUT, "1.9.0"),
    ("resource_changes.*.type", INPUT, ["aws_s3_bucket", "aws_instance"]),
    ("items.*.name", {"items": [{"name": "only"}]}, "only"),
    ("count", INPUT, "3"),
    ("enabled", INPUT, "true"),
    ("nothing", INPUT, "null"),
]


@pytest.mark.parametrize("state_path, input_data, expected_state", STATE_CASES)
def test_state_path_selects_what_is_sent(ask, state_path, input_data, expected_state):
    calls = ask(NOUL)

    handler.provide(dict(NOUL_ARGS, state_path=state_path), input_data)

    assert calls[0]["state"] == expected_state


def test_a_multi_document_input_is_sent_whole(ask):
    calls = ask(NOUL)
    documents = [{"kind": "Pod"}, {"kind": "Service"}]

    handler.provide(NOUL_ARGS, documents)

    assert calls[0]["state"] == documents


def test_a_state_path_that_matches_nothing_is_a_severity_2_error(ask):
    calls = ask(NOUL)

    (result,) = handler.provide(dict(NOUL_ARGS, state_path="missing.path"), INPUT)

    assert isinstance(result["value"], ProviderError)
    assert result["value"].severity_value == 2
    assert result["err"] == "state_path: `missing.path` is not found (severity: 2)"
    assert calls == []


def test_a_request_error_always_fails(ask):
    ask(client.JevRequestError("Jev API returned HTTP 401: bad key"))

    assert handler.provide(NOUL_ARGS, INPUT) == [
        {"value": None, "meta": None, "err": "Jev API returned HTTP 401: bad key", "context": _context("noul")}
    ]


def test_an_unavailable_service_is_a_severity_2_error(ask):
    ask(client.JevUnavailableError("Jev API returned HTTP 529"))

    (result,) = handler.provide(NOUL_ARGS, INPUT)

    assert isinstance(result["value"], ProviderError)
    assert result["value"].severity_value == 2
    assert result["err"] == "Jev API returned HTTP 529 (severity: 2)"


MALFORMED_ANSWERS = [
    (NOUL_ARGS, {"type": "noul"}),
    (NOUL_ARGS, {"type": "noul", "noul": "yes"}),
    (NOUL_ARGS, {"type": "noul", "noul": True}),
    (CHOICE_ARGS, {"type": "choice", "choice": 3, "confidence": 0.9}),
    (SCORE_ARGS, {"type": "score", "score": None, "confidence": 0.9}),
]


@pytest.mark.parametrize("provider_args, answer", MALFORMED_ANSWERS)
def test_an_answer_of_the_wrong_type_always_fails(ask, provider_args, answer):
    ask({"answer": answer, "model": MODEL, "usage": USAGE})

    (result,) = handler.provide(provider_args, INPUT)

    assert result["value"] is None
    assert result["err"] == "Jev API response carries no usable `{}` value".format(provider_args["operation_type"])
