import json

import pytest

from app.models import Fact
from app.services.errors import ServiceError
from app.services.reasoning import SYSTEM_BRIEF, parse_observations, parse_json, validate_brief

FACTS = [
    Fact(id="d1-cheque_number", doc_id="d1", key="cheque_number", label="Cheque number", value="004718"),
    Fact(id="d1-cheque_date", doc_id="d1", key="cheque_date", label="Date on cheque", value=None, flag="Not read"),
]


def _raw(*claims):
    return {"claims": [{"section": "instrument", "text": t, "fact_ids": ids} for t, ids in claims]}


def test_claim_without_fact_id_is_flagged_not_kept():
    b = validate_brief(_raw(("The cheque is for a large sum.", []), ("Cheque 004718.", ["d1-cheque_number"])), FACTS)
    assert [c.text for c in b.claims] == ["Cheque 004718."]
    assert len(b.flagged) == 1 and "large sum" in b.flagged[0]


def test_claim_with_unknown_fact_id_is_flagged():
    b = validate_brief(_raw(("Cheque 004718.", ["d1-cheque_number", "d9-invented"])), FACTS)
    assert b.claims == [] and "invented" in b.flagged[0]


def test_transcript_is_a_valid_source_only_when_a_transcript_exists():
    raw = _raw(("The client says payment was promised.", ["transcript"]))
    assert len(validate_brief(raw, FACTS, has_transcript=True).claims) == 1
    assert validate_brief(raw, FACTS, has_transcript=False).claims == []


def test_system_prompt_forbids_legal_advice_and_date_arithmetic():
    p = SYSTEM_BRIEF.lower()
    assert "do not give legal advice" in p
    assert "never calculate" in p and "deadline" in p
    assert "fact_ids" in p and "transcript" in p


def test_unknown_observation_keys_are_ignored_and_bad_status_becomes_unclear():
    raw = {"observations": [
        {"key": "signature", "label": "Signature", "status": "present", "note": "blue ink"},
        {"key": "colour_of_pen", "label": "Pen", "status": "present", "note": ""},
        {"key": "crossing", "label": "A/c payee crossing", "status": "maybe", "note": ""}]}
    obs = parse_observations(raw)
    assert [(o.key, o.status) for o in obs] == [("signature", "present"), ("crossing", "unclear")]


def test_unreadable_model_reply_is_a_retryable_service_error():
    with pytest.raises(ServiceError) as e:
        parse_json("this is not json")
    assert e.value.retryable is True
    assert parse_json(json.dumps({"claims": []})) == {"claims": []}
