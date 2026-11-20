import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import DocType
from app.pipeline import Pipeline, Services
from app.services.errors import ServiceError
from app.store import Store
from tests.doubles import (FakeAnalyzer, FakeAssistant, FakeExtractor, FakeReasoner, FakeSynth, FakeTranscriber)

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
JPG = b"\xff\xd8\xff\xe0" + b"0" * 64


def make(tmp_path, transcriber=None, reasoner=None):
    store = Store(tmp_path / "t.db")
    services = Services(FakeExtractor(), transcriber or FakeTranscriber(), FakeSynth(), FakeAnalyzer(),
                        reasoner or FakeReasoner(), FakeAssistant())
    pipe = Pipeline(store, services, tmp_path / "data")
    return TestClient(create_app(pipe, store, tmp_path / "data", mode="live", recorded_at=lambda: None, deployment="t")), store


def matter(c):
    return c.post("/api/matters", json={"title": "Fictional Traders v. Sample Co"}).json()["id"]


def upload(c, mid, doc_type="cheque", name="cheque.png", data=PNG, ctype="image/png"):
    return c.post(f"/api/matters/{mid}/documents", data={"doc_type": doc_type}, files={"file": (name, data, ctype)})


def test_upload_cheque_returns_source_facts_and_observations(tmp_path):
    c, _ = make(tmp_path)
    r = upload(c, matter(c))
    assert r.status_code == 200
    body = r.json()
    assert {f["key"] for f in body["document"]["facts"]} >= {"cheque_number", "cheque_date", "amount_figures"}
    assert body["document"]["observations"][0]["key"] == "signature" and body["warnings"] == []


def test_inspection_failure_keeps_the_facts_and_warns(tmp_path):
    c, _ = make(tmp_path, reasoner=FakeReasoner(fail_inspect=True))
    r = upload(c, matter(c))
    assert r.status_code == 200 and r.json()["document"]["facts"] and "busy" in r.json()["warnings"][0]


@pytest.mark.parametrize("name,data,ctype,expect", [
    ("photo.heic", b"\x00\x00\x00\x18ftypheic", "image/heic", "HEIC"),
    ("note.png", b"not really an image", "image/png", "not a PNG"),
    ("big.png", PNG + b"0" * (16 * 1024 * 1024), "image/png", "MB"),
    ("empty.png", b"", "image/png", "empty"),
])
def test_bad_uploads_are_rejected_with_a_reason(tmp_path, name, data, ctype, expect):
    c, _ = make(tmp_path)
    r = upload(c, matter(c), name=name, data=data, ctype=ctype)
    assert r.status_code == 422 and expect in r.json()["error"]


def test_voice_failure_keeps_documents_and_reports_retryable(tmp_path):
    c, _ = make(tmp_path, transcriber=FakeTranscriber(error=ServiceError("speech", "Azure is rate limiting.", True)))
    mid = matter(c)
    upload(c, mid)
    r = c.post(f"/api/matters/{mid}/voice", data={"locale": "en-IN"}, files={"audio": ("v.webm", b"abc", "audio/webm")})
    assert r.status_code == 502 and r.json()["retryable"] is True and "rate limiting" in r.json()["error"]
    assert len(c.get(f"/api/matters/{mid}").json()["matter"]["documents"]) == 1


def test_voice_note_is_redacted_before_it_is_stored_for_the_model(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    r = c.post(f"/api/matters/{mid}/voice", data={"locale": "en-IN"}, files={"audio": ("v.webm", b"abc", "audio/webm")})
    t = r.json()
    assert "98765" in t["text"] and "98765" not in t["redacted_text"] and "[PHONENUMBER]" in t["redacted_text"]


def test_empty_audio_is_rejected(tmp_path):
    c, _ = make(tmp_path)
    r = c.post(f"/api/matters/{matter(c)}/voice", data={"locale": "en-IN"}, files={"audio": ("v.webm", b"", "audio/webm")})
    assert r.status_code == 422


def test_brief_refused_until_a_cheque_is_added(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    assert c.post(f"/api/matters/{mid}/brief").status_code == 422
    upload(c, mid)
    assert c.post(f"/api/matters/{mid}/brief").status_code == 200


def test_approval_gate_and_audit_trail(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    upload(c, mid)
    assert c.post(f"/api/matters/{mid}/approve", json={"actor": "Adv. Hari Haran"}).status_code == 422
    c.post(f"/api/matters/{mid}/brief")
    assert c.post(f"/api/matters/{mid}/approve", json={"actor": "  "}).status_code == 422
    assert c.post(f"/api/matters/{mid}/approve", json={"actor": "Adv. Hari Haran"}).status_code == 200
    actions = [a["action"] for a in c.get(f"/api/matters/{mid}").json()["audit"]]
    assert actions[-1] == "approved"


def test_brief_is_read_aloud_only_after_approval(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    upload(c, mid)
    c.post(f"/api/matters/{mid}/brief")
    assert c.post(f"/api/matters/{mid}/speak", json={"locale": "en-IN"}).status_code == 422
    c.post(f"/api/matters/{mid}/approve", json={"actor": "Adv."})
    r = c.post(f"/api/matters/{mid}/speak", json={"locale": "en-IN"})
    assert r.status_code == 200 and r.content.startswith(b"MP3:")


def test_fact_edit_marks_verified_and_rejects_non_dates_for_date_facts(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    doc = upload(c, mid).json()["document"]
    fid = next(f["id"] for f in doc["facts"] if f["key"] == "cheque_date")
    assert c.patch(f"/api/facts/{fid}", json={"value": "20/09/2026"}).status_code == 422
    ok = c.patch(f"/api/facts/{fid}", json={"value": "2026-09-21", "actor": "Adv."})
    assert ok.status_code == 200 and ok.json()["verified"] is True
    assert c.patch("/api/facts/nope", json={"value": "x"}).status_code == 404


def test_deadlines_follow_the_today_parameter_and_never_guess_missing_dates(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    upload(c, mid)
    w = {x["key"]: x for x in c.get(f"/api/matters/{mid}/deadlines", params={"today": "2026-11-21"}).json()["windows"]}
    assert w["payment"]["status"] == "unknown" and w["payment"]["closes"] is None
    memo = upload(c, mid, "return_memo", "m.png", PNG + b"1").json()["document"]
    notice = upload(c, mid, "demand_notice", "n.png", PNG + b"2").json()["document"]
    for doc, key, val in [(memo, "memo_received_on", "2026-10-05"), (notice, "notice_sent_on", "2026-10-30"),
                          (notice, "notice_delivered_on", "2026-11-03")]:
        fid = next(f["id"] for f in doc["facts"] if f["key"] == key)
        assert c.patch(f"/api/facts/{fid}", json={"value": val}).status_code == 200
    w = {x["key"]: x for x in c.get(f"/api/matters/{mid}/deadlines", params={"today": "2026-11-21"}).json()["windows"]}
    assert (w["payment"]["closes"], w["complaint"]["opens"], w["complaint"]["closes"]) == ("2026-11-18", "2026-11-19", "2026-12-19")
    assert w["complaint"]["status"] == "open"
    assert c.get(f"/api/matters/{mid}/deadlines", params={"today": "tomorrow"}).status_code == 422


def test_ask_mode_and_unknown_matter(tmp_path):
    c, _ = make(tmp_path)
    mid = matter(c)
    assert c.post(f"/api/matters/{mid}/ask", json={"question": "When must I file?"}).json()["text"] == "echo: When must I file?"
    assert c.post(f"/api/matters/{mid}/ask", json={"question": "  "}).status_code == 422
    assert c.get("/api/mode").json()["mode"] == "live"
    assert c.get("/api/matters/m_nope").status_code == 404


def test_sample_matter_loads_the_three_fictional_papers_and_says_so(tmp_path):
    c, _ = make(tmp_path)
    r = c.post("/api/sample-matter")
    assert r.status_code == 200
    m = r.json()
    assert "sample" in m["title"].lower() and "fictional" in m["title"].lower()
    assert sorted(d["doc_type"] for d in m["documents"]) == ["cheque", "demand_notice", "return_memo"]
    again = c.post("/api/sample-matter").json()
    assert again["id"] != m["id"]  # each demo run is its own matter, nothing is overwritten


def test_mode_reports_the_servers_own_today_so_the_screen_and_the_engine_share_one_clock(tmp_path):
    c, _ = make(tmp_path)
    assert c.get("/api/mode").json()["today"] == Pipeline(Store(tmp_path / "x.db"), None, tmp_path).today().isoformat()
