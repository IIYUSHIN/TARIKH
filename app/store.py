"""SQLite persistence. A matter is stored as one JSON document (small, local, easy to explain);
the audit log is a real table because it is append-only and queried on its own."""
from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from .models import AuditEntry, Brief, Document, Matter, Transcript, utcnow


class Store:
    def __init__(self, path: Path | str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS matters(
                    id TEXT PRIMARY KEY, seq INTEGER, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, matter_id TEXT NOT NULL,
                    ts TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
                """
            )

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    # -- matters -------------------------------------------------------------
    def create_matter(self, title: str) -> Matter:
        m = Matter(id="m_" + secrets.token_hex(4), title=title)
        with closing(self._db()) as db, db:
            seq = db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM matters").fetchone()[0]
            db.execute("INSERT INTO matters(id, seq, body) VALUES (?,?,?)",
                       (m.id, seq, m.model_dump_json()))
        return m

    def get_matter(self, matter_id: str) -> Matter:
        with closing(self._db()) as db:
            row = db.execute("SELECT body FROM matters WHERE id=?", (matter_id,)).fetchone()
        if row is None:
            raise KeyError(matter_id)
        return Matter.model_validate_json(row["body"])

    def list_matters(self) -> list[Matter]:
        with closing(self._db()) as db:
            rows = db.execute("SELECT body FROM matters ORDER BY seq DESC").fetchall()
        return [Matter.model_validate_json(r["body"]) for r in rows]

    def _put(self, m: Matter) -> None:
        with closing(self._db()) as db, db:
            db.execute("UPDATE matters SET body=? WHERE id=?", (m.model_dump_json(), m.id))

    # -- documents and facts -------------------------------------------------
    def save_document(self, matter_id: str, doc: Document) -> None:
        m = self.get_matter(matter_id)
        m.documents = [d for d in m.documents if d.id != doc.id] + [doc]
        self._put(m)
        self._log(matter_id, "system", "document_added",
                  {"doc_id": doc.id, "doc_type": doc.doc_type.value, "facts": len(doc.facts)})

    def matter_id_for_fact(self, fact_id: str) -> str:
        for m in self.list_matters():
            for d in m.documents:
                if any(f.id == fact_id for f in d.facts):
                    return m.id
        raise KeyError(fact_id)

    def update_fact(self, fact_id: str, value: str | None, actor: str) -> None:
        m = self.get_matter(self.matter_id_for_fact(fact_id))
        for d in m.documents:
            for f in d.facts:
                if f.id == fact_id:
                    old, f.value, f.verified = f.value, value, True
                    self._put(m)
                    self._log(m.id, actor, "fact_updated",
                              {"fact_id": fact_id, "old": old, "new": value})
                    return

    # -- voice, brief, approval ---------------------------------------------
    def save_transcript(self, matter_id: str, t: Transcript) -> None:
        m = self.get_matter(matter_id)
        m.transcript = t
        self._put(m)
        self._log(matter_id, "system", "transcript_saved",
                  {"language": t.language, "route": t.redaction_route})

    def save_brief(self, matter_id: str, brief: Brief) -> None:
        m = self.get_matter(matter_id)
        m.brief, m.approved_by, m.approved_at = brief, None, None  # a new draft needs a new approval
        self._put(m)
        self._log(matter_id, "system", "brief_saved",
                  {"claims": len(brief.claims), "flagged": len(brief.flagged), "model": brief.model})

    def approve(self, matter_id: str, actor: str) -> None:
        m = self.get_matter(matter_id)
        if m.brief is None:
            raise ValueError("cannot approve: no brief has been drafted")
        m.approved_by, m.approved_at = actor, utcnow()
        self._put(m)
        self._log(matter_id, actor, "approved", {})

    # -- audit ---------------------------------------------------------------
    def _log(self, matter_id: str, actor: str, action: str, detail: dict) -> None:
        with closing(self._db()) as db, db:
            db.execute("INSERT INTO audit(matter_id, ts, actor, action, detail) VALUES (?,?,?,?,?)",
                       (matter_id, utcnow().isoformat(), actor, action, json.dumps(detail)))

    def audit(self, matter_id: str) -> list[AuditEntry]:
        with closing(self._db()) as db:
            rows = db.execute("SELECT * FROM audit WHERE matter_id=? ORDER BY id", (matter_id,)).fetchall()
        return [AuditEntry(id=r["id"], matter_id=r["matter_id"], ts=r["ts"], actor=r["actor"],
                           action=r["action"], detail=json.loads(r["detail"])) for r in rows]
