"""Accounts, sessions and the desk API: a person signs up, sees only their own matters, and every change is kept."""
from datetime import date

from fastapi.testclient import TestClient

from app.accounts import Accounts
from app.main import create_app
from app.pipeline import Pipeline, Services
from app.store import Store
from tests.doubles import FakeAnalyzer, FakeAssistant, FakeExtractor, FakeReasoner, FakeSynth, FakeTranscriber


def make(tmp_path):
    store = Store(tmp_path / "t.db")
    services = Services(FakeExtractor(), FakeTranscriber(), FakeSynth(), FakeAnalyzer(), FakeReasoner(), FakeAssistant())
    pipe = Pipeline(store, services, tmp_path / "data", today=lambda: date(2026, 11, 20))
    app = create_app(pipe, store, tmp_path / "data", mode="live", recorded_at=lambda: None, deployment="t",
                     accounts=Accounts(tmp_path / "t.db"), site_dir=tmp_path)
    return lambda: TestClient(app)


def signup(c, email="asha@chambers.in", name="Asha Grewal"):
    return c.post("/api/auth/signup", json={"name": name, "email": email, "password": "correct horse", "chambers": "Grewal & Associates"})


def test_api_refuses_without_a_session(tmp_path):
    c = make(tmp_path)()
    assert c.get("/api/desk").status_code == 401
    assert c.get("/api/me").json()["user"] is None


def test_signup_signin_signout(tmp_path):
    new = make(tmp_path)
    c = new()
    assert signup(c).status_code == 200
    assert c.get("/api/me").json()["user"]["name"] == "Asha Grewal"
    assert signup(new()).json()["error"].startswith("An account with this email")
    c.post("/api/auth/signout")
    assert c.get("/api/desk").status_code == 401
    bad = c.post("/api/auth/signin", json={"email": "asha@chambers.in", "password": "wrong password"})
    assert bad.status_code == 422
    assert c.post("/api/auth/signin", json={"email": "ASHA@chambers.in ", "password": "correct horse"}).status_code == 200


def test_signup_explains_what_is_wrong(tmp_path):
    c = make(tmp_path)()
    assert "password" in c.post("/api/auth/signup", json={"name": "A", "email": "a@b.in", "password": "short"}).json()["error"]
    assert "email" in c.post("/api/auth/signup", json={"name": "A", "email": "nope", "password": "long enough"}).json()["error"]


def test_people_see_only_their_own_matters(tmp_path):
    new = make(tmp_path)
    a, b = new(), new()
    signup(a)
    signup(b, "ravi@firm.in", "Ravi Sood")
    mid = a.post("/api/matters", json={"complainant": "Gill Tractors", "accused": "Mehra Agro"}).json()["id"]
    assert [m["accused"] for m in a.get("/api/desk").json()["matters"]] == ["Mehra Agro"]
    assert b.get("/api/desk").json()["matters"] == []
    assert b.get(f"/api/desk/{mid}").status_code == 404
    assert b.patch(f"/api/desk/{mid}", json={"stage": "settled"}).status_code == 404


def test_new_matter_with_entered_dates_is_counted(tmp_path):
    c = make(tmp_path)()
    signup(c)
    mid = c.post("/api/matters", json={"complainant": "Sharma Steel", "accused": "Kalra Fabricators", "amount": "485000",
                                       "entries": {"cheque_date": "2026-09-20", "memo_received_on": "2026-10-05",
                                                   "notice_sent_on": "2026-10-30", "notice_delivered_on": "2026-11-03"}}).json()["id"]
    v = c.get(f"/api/desk/{mid}").json()
    complaint = next(w for w in v["windows"] if w["key"] == "complaint")
    assert (complaint["opens"], complaint["closes"]) == ("2026-11-19", "2026-12-19")
    assert v["stage"] == "file" and v["amount"] == 485000
    assert c.post("/api/matters", json={"entries": {"cheque_date": "20/09/2026"}}).status_code == 422


def test_hearings_settlement_and_draft_approval_are_kept_and_audited(tmp_path):
    c = make(tmp_path)()
    signup(c)
    mid = c.post("/api/matters", json={"complainant": "X", "accused": "Y"}).json()["id"]
    v = c.post(f"/api/desk/{mid}/hearings", json={"date": "2026-11-18", "purpose": "Appearance of accused",
                                                  "outcome": "Adjourned", "next_date": "2026-12-03", "next_purpose": "Evidence"}).json()
    assert v["next"] == ["2026-12-03", "Evidence"] and len(v["hearings"]) == 1
    v = c.post(f"/api/desk/{mid}/settlement", json={"total": 90000, "parts": 3, "paid": 1}).json()
    assert v["settlement"]["paid"] == 1
    v = c.post(f"/api/desk/{mid}/drafts/approve", json={"title": "Demand notice"}).json()
    assert v["drafts"][0] == {"t": "Demand notice", "s": "Approved", "by": "Asha Grewal"}
    actions = [row[0] for row in c.get(f"/api/desk/{mid}").json()["log"]]
    assert "Draft approved" in actions and "Hearing recorded" in actions


def test_samples_load_once_and_return_file_imports(tmp_path):
    c = make(tmp_path)()
    signup(c)
    assert c.post("/api/desk/samples").json()["created"] == 13
    assert c.post("/api/desk/samples").json()["created"] == 0
    r = c.post("/api/desk/import", json={"sample": True}).json()
    assert r["created"] == 24 and r["problems"] == []
    r = c.post("/api/desk/import", json={"csv": "drawer,cheque_date\nAhuja Tyres,2026-11-01\nBad Row,01/11/2026\n"}).json()
    assert r["created"] == 1 and "Row 3" in r["problems"][0]
    assert len(c.get("/api/desk").json()["matters"]) == 38
