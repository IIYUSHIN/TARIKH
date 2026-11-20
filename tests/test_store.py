import pytest

from app.models import Brief, Claim, DocType, Document, Fact
from app.store import Store


def _doc(matter_id: str) -> Document:
    return Document(
        id="d1", matter_id=matter_id, doc_type=DocType.CHEQUE,
        filename="cheque.png", path="data/d1.png",
        facts=[Fact(id="f1", doc_id="d1", key="amount_figures",
                    label="Amount", value="50,000")],
    )


def test_update_fact_writes_audit_entry(tmp_path):
    s = Store(tmp_path / "t.db")
    m = s.create_matter("Fictional Traders v. Sample Co")
    s.save_document(m.id, _doc(m.id))

    s.update_fact("f1", "55,000", actor="Adv. Hari Haran")

    fact = s.get_matter(m.id).documents[0].facts[0]
    assert fact.value == "55,000" and fact.verified is True
    entries = [e for e in s.audit(m.id) if e.action == "fact_updated"]
    assert len(entries) == 1
    assert entries[0].actor == "Adv. Hari Haran"
    assert entries[0].detail == {"fact_id": "f1", "old": "50,000", "new": "55,000"}


def test_approve_requires_brief(tmp_path):
    s = Store(tmp_path / "t.db")
    m = s.create_matter("No brief yet")
    with pytest.raises(ValueError, match="brief"):
        s.approve(m.id, actor="Adv. Hari Haran")


def test_approve_after_brief_records_actor_and_audit(tmp_path):
    s = Store(tmp_path / "t.db")
    m = s.create_matter("With brief")
    s.save_brief(m.id, Brief(claims=[Claim(text="Cheque dishonoured", fact_ids=["f1"])],
                             flagged=[], model="test-deployment"))
    s.approve(m.id, actor="Adv. Hari Haran")
    got = s.get_matter(m.id)
    assert got.approved_by == "Adv. Hari Haran" and got.approved_at is not None
    assert [e.action for e in s.audit(m.id)][-1] == "approved"


def test_list_matters_newest_first(tmp_path):
    s = Store(tmp_path / "t.db")
    a = s.create_matter("first")
    b = s.create_matter("second")
    assert [m.id for m in s.list_matters()] == [b.id, a.id]


def test_get_unknown_matter_raises_keyerror(tmp_path):
    with pytest.raises(KeyError):
        Store(tmp_path / "t.db").get_matter("nope")
