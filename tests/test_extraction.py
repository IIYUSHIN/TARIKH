import pytest

from app.analyzers import FIELD_SPECS, analyzer_id, build_analyzer_definition
from app.models import DocType, doc_id_for
from app.services.extraction import map_result


def _raw(fields: dict, width=1800, height=800):
    return {"contents": [{"kind": "document", "fields": fields,
                          "pages": [{"pageNumber": 1, "width": width, "height": height, "unit": "pixel"}]}]}


def _fact(facts, key):
    return next(f for f in facts if f.key == key)


def test_map_result_normalises_polygon_to_unit_square():
    raw = _raw({"cheque_number": {"type": "string", "valueString": "004718", "confidence": 0.97,
                                  "source": "D(1,180,80,900,80,900,160,180,160)"}})
    f = _fact(map_result(DocType.CHEQUE, raw, "d_abc"), "cheque_number")
    assert f.value == "004718" and f.confidence == 0.97
    assert f.source.polygon == [0.1, 0.1, 0.5, 0.1, 0.5, 0.2, 0.1, 0.2]
    assert f.source.page == 1 and f.id == "d_abc-cheque_number"


def test_unreadable_date_becomes_none_with_flag_not_a_guess():
    facts = map_result(DocType.CHEQUE, _raw({"cheque_date": {"type": "date"}}), "d_abc")
    f = _fact(facts, "cheque_date")
    assert f.value is None and "Enter it" in f.flag
    assert _fact(facts, "amount_figures").value is None  # absent field is also None


def test_ambiguous_day_month_is_flagged_but_clear_date_is_not():
    amb = _fact(map_result(DocType.CHEQUE, _raw({"cheque_date": {"type": "date", "valueDate": "2026-10-03", "confidence": 0.95}}), "d"), "cheque_date")
    clear = _fact(map_result(DocType.CHEQUE, _raw({"cheque_date": {"type": "date", "valueDate": "2026-10-20", "confidence": 0.95}}), "d"), "cheque_date")
    assert "either way" in amb.flag and amb.confidence <= 0.6
    assert clear.flag is None and clear.confidence == 0.95


def test_amount_is_a_plain_number_string():
    f = _fact(map_result(DocType.CHEQUE, _raw({"amount_figures": {"type": "number", "valueNumber": 485000.0}}), "d"), "amount_figures")
    assert f.value == "485000"


def test_manual_facts_exist_and_are_empty():
    memo = map_result(DocType.RETURN_MEMO, _raw({}), "d")
    notice = map_result(DocType.DEMAND_NOTICE, _raw({}), "d")
    assert _fact(memo, "memo_received_on").manual and _fact(memo, "memo_received_on").value is None
    assert _fact(notice, "notice_delivered_on").manual and _fact(notice, "notice_delivered_on").value is None


@pytest.mark.parametrize("doc_type", list(DocType))
def test_analyzer_definition_requests_grounding_for_every_extracted_field(doc_type):
    d = build_analyzer_definition(doc_type)
    extracted = [s.key for s in FIELD_SPECS[doc_type] if not s.manual]
    assert set(d["fieldSchema"]["fields"]) == set(extracted)
    assert d["config"]["estimateFieldSourceAndConfidence"] is True
    assert all(f["estimateSourceAndConfidence"] and f["method"] == "extract" for f in d["fieldSchema"]["fields"].values())
    assert d["baseAnalyzerId"] == "prebuilt-document" and analyzer_id(doc_type).startswith("tarikh-")


def test_doc_id_is_derived_from_content():
    assert doc_id_for(b"same") == doc_id_for(b"same") != doc_id_for(b"other")
