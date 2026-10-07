import os

import pytest

from tirith.providers.jev import client, handler

pytestmark = pytest.mark.skipif(
    not os.environ.get(client.API_KEY_ENV_VAR),
    reason="calls the real Jev API; set TYPESAFE_API_KEY to run it",
)

STATE = {"message": "Help! My payouts have been failing for 3 days."}


def test_live_noul():
    (result,) = handler.provide({"operation_type": "noul", "instructions": "Does this convey urgency?"}, STATE)

    assert result["err"] is None
    assert 0 <= result["value"] <= 1


def test_live_choice():
    criteria = {"billing": "Payments, invoicing, refunds", "sales": "Pricing, upgrades, new accounts"}
    provider_args = {"operation_type": "choice", "instructions": "Which team should handle this?", "criteria": criteria}

    (result,) = handler.provide(provider_args, STATE)

    assert result["err"] is None
    assert result["value"] in criteria
    assert 0 <= result["meta"]["confidence"] <= 1


def test_live_score():
    criteria = ["Calm", "Frustrated", "Very angry"]
    provider_args = {"operation_type": "score", "instructions": "How frustrated is the customer?", "criteria": criteria}

    (result,) = handler.provide(provider_args, STATE)

    assert result["err"] is None
    assert 0 <= result["value"] <= len(criteria) - 1
    assert set(result["meta"]["legend"]) == {"0", "1", "2"}
