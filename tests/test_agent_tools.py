import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.deadlines import compute_windows
from app.matter_dates import windows_for_matter
from app.models import DocType, Document, Fact
from app.services.agent import ToolRegistry, run_tool_loop
from app.services.errors import ServiceError
from app.store import Store


def _fact(doc, key, value):
    return Fact(id=f"{doc}-{key}", doc_id=doc, key=key, label=key, value=value)


@pytest.fixture
def matter(tmp_path):
    s = Store(tmp_path / "t.db")
    m = s.create_matter("Fictional matter")
    s.save_document(m.id, Document(id="dc", matter_id=m.id, doc_type=DocType.CHEQUE, filename="c", path="c",
                                   facts=[_fact("dc", "cheque_date", "2026-09-20")]))
    s.save_document(m.id, Document(id="dm", matter_id=m.id, doc_type=DocType.RETURN_MEMO, filename="m", path="m",
                                   facts=[_fact("dm", "presented_on", "2026-10-01"),
                                          _fact("dm", "memo_received_on", "2026-10-05")]))
    s.save_document(m.id, Document(id="dn", matter_id=m.id, doc_type=DocType.DEMAND_NOTICE, filename="n", path="n",
                                   facts=[_fact("dn", "notice_sent_on", "2026-10-30"),
                                          _fact("dn", "notice_delivered_on", "not a date")]))
    return s, m.id


def test_windows_for_matter_reads_facts_and_treats_garbage_dates_as_missing(matter):
    s, mid = matter
    w = {x.key: x for x in windows_for_matter(s.get_matter(mid), today=date(2026, 11, 21))}
    assert w["validity"].status == "met"            # presented 1 Oct, within 3 months of 20 Sep
    assert w["notice"].status == "met"              # posted 30 Oct, inside 30 days of 5 Oct
    assert w["payment"].status == "unknown"         # 'not a date' is never turned into a date


def test_get_deadlines_tool_returns_engine_output_verbatim(matter):
    s, mid = matter
    s.update_fact(f"dn-notice_delivered_on", "2026-11-03", actor="Adv.")
    reg = ToolRegistry(s, mid, today=lambda: date(2026, 11, 21))
    out = reg.call("get_deadlines", {})
    expected = compute_windows(date(2026, 9, 20), date(2026, 10, 5), date(2026, 10, 30), date(2026, 11, 3),
                               date(2026, 11, 21), presented_on=date(2026, 10, 1))
    assert [(w["key"], w["opens"], w["closes"], w["status"]) for w in out["windows"]] == \
           [(w.key, w.opens and w.opens.isoformat(), w.closes and w.closes.isoformat(), w.status) for w in expected]
    assert out["as_of"] == "2026-11-21"


def test_unknown_tool_name_is_rejected(matter):
    s, mid = matter
    with pytest.raises(ValueError, match="unknown tool"):
        ToolRegistry(s, mid).call("delete_matter", {})


def test_tool_arguments_cannot_reach_another_matter(matter):
    s, mid = matter
    other = s.create_matter("Someone else's matter")
    out = ToolRegistry(s, mid).call("get_fact", {"matter_id": other.id, "key": "cheque_date"})
    assert out["value"] == "2026-09-20"


def test_get_fact_unknown_key_returns_an_error_dict_not_an_exception(matter):
    s, mid = matter
    assert "error" in ToolRegistry(s, mid).call("get_fact", {"key": "nonsense"})


def _resp(text="", calls=()):
    out = [SimpleNamespace(type="function_call", call_id=f"c{i}", name=n, arguments=a) for i, (n, a) in enumerate(calls)]
    return SimpleNamespace(output=out, output_text=text)


def test_tool_loop_runs_calls_sends_outputs_back_and_returns_final_text(matter):
    s, mid = matter
    sent = []
    replies = iter([_resp(calls=[("get_fact", json.dumps({"key": "cheque_date"}))]), _resp(text="Dated 20 September 2026.")])

    def create(inp):
        sent.append(inp)
        return next(replies)

    ans = run_tool_loop(create, "What date is on the cheque?", ToolRegistry(s, mid))
    assert ans.text == "Dated 20 September 2026."
    assert [(t.name, t.result["value"]) for t in ans.tool_calls] == [("get_fact", "2026-09-20")]
    assert sent[1][0]["type"] == "function_call_output" and sent[1][0]["call_id"] == "c0"


def test_tool_loop_survives_malformed_arguments(matter):
    s, mid = matter
    replies = iter([_resp(calls=[("get_fact", "{oops")]), _resp(text="I could not find that.")])
    ans = run_tool_loop(lambda inp: next(replies), "?", ToolRegistry(s, mid))
    assert ans.text == "I could not find that." and "error" in ans.tool_calls[0].result


def test_tool_loop_gives_up_after_max_rounds(matter):
    s, mid = matter
    with pytest.raises(ServiceError, match="too many steps"):
        run_tool_loop(lambda inp: _resp(calls=[("get_deadlines", "{}")]), "?", ToolRegistry(s, mid), max_rounds=3)
