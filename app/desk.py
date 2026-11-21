"""The desk view: one flat, display-ready shape per matter, built from papers, entries and the profile.
Statuses are not stored here either: the browser counts them with the same engine the tests cover."""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path

from .matter_dates import fact_value, window_dict, windows_for_matter
from .models import DocType, Matter

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
FIELD_TO_VIEW = {"cheque_date": "cheque", "presented_on": "presented", "return_date": "returned",
                 "memo_received_on": "memo", "notice_sent_on": "sent", "notice_delivered_on": "delivered"}
STAGES = ["notice", "payment", "file", "cognizance", "summons", "evidence", "arguments", "settled", "decided"]


def _amount(m: Matter) -> int:
    raw = m.profile.get("amount") or fact_value(m, "amount_figures") or fact_value(m, "demand_amount") or 0
    try:
        return int(float(str(raw).replace(",", "").replace("₹", "")))
    except ValueError:
        return 0


def view(m: Matter, today: date, audit: list | None = None) -> dict:
    p = m.profile
    v = {
        "id": m.id, "ref": p.get("ref") or m.id.upper().replace("M_", "TK-"), "title": m.title,
        "sample": bool(p.get("sample")),
        "complainant": p.get("complainant") or fact_value(m, "payee_name") or "Complainant not entered",
        "accused": p.get("accused") or fact_value(m, "drawer_name") or "Drawer not entered",
        "amount": _amount(m), "chequeNo": p.get("chequeNo") or fact_value(m, "cheque_number") or "",
        "bank": p.get("bank") or fact_value(m, "bank_name") or "",
        "reason": p.get("reason") or fact_value(m, "return_reason") or "",
        "court": p.get("court") or "Court not entered", "city": p.get("city") or "",
        "filed": p.get("filed"), "caseNo": p.get("caseNo"), "email": p.get("email"), "phone": p.get("phone"),
        "hearings": p.get("hearings") or [], "next": p.get("next"), "settlement": p.get("settlement"),
        "drafts": p.get("drafts") or [], "advocate": p.get("advocate"),
        "papers": [{"id": d.id, "type": d.doc_type.value, "filename": d.filename,
                    "url": f"/api/matters/{m.id}/documents/{d.id}/file",
                    "facts": [f.model_dump() for f in d.facts],
                    "observations": [o.model_dump() for o in d.observations]} for d in m.documents],
        "brief": m.brief.model_dump(mode="json") if m.brief else None,
        "transcript": m.transcript.model_dump(mode="json") if m.transcript else None,
        "approved_by": m.approved_by, "created_at": m.created_at.isoformat(),
    }
    for key, name in FIELD_TO_VIEW.items():
        v[name] = fact_value(m, key)
    v["windows"] = [window_dict(w) for w in windows_for_matter(m, today)]
    v["stage"] = p.get("stage") or _derive_stage(v)
    if audit is not None:
        v["log"] = [[a.action.replace("_", " ").capitalize(), a.actor, a.ts.isoformat()] for a in reversed(audit)]
    return v


def _derive_stage(v: dict) -> str:
    if v["filed"]:
        return "cognizance"
    if not v["sent"]:
        return "notice"
    w = {x["key"]: x for x in v["windows"]}
    return "payment" if w.get("complaint", {}).get("status") == "upcoming" else "file"


def sample_profiles() -> list[tuple[str, dict]]:
    """The thirteen fictional desk matters, as profiles with entered dates (no papers except the first)."""
    out = []
    for s in json.loads((SAMPLES / "desk_matters.json").read_text(encoding="utf-8")):
        entries = {k: s.get(v) for k, v in FIELD_TO_VIEW.items() if s.get(v)}
        prof = {"sample": True, "ref": s["id"], "complainant": s["complainant"], "accused": s["accused"],
                "amount": s["amount"], "chequeNo": s["chequeNo"], "bank": s["bank"], "reason": s["reason"],
                "court": s["court"], "stage": s["stage"], "filed": s.get("filed"), "caseNo": s.get("caseNo"),
                "email": s.get("email"), "phone": s.get("phone"), "next": s.get("next"),
                "hearings": s.get("hearings") or [], "settlement": s.get("settlement"),
                "drafts": s.get("drafts") or [], "entries": entries}
        out.append((f"{s['complainant']} v. {s['accused']}", prof))
    return out


CSV_COLUMNS = {"reference": "ref", "drawer": "accused", "city": "city", "amount": "amount",
               "cheque_date": "cheque_date", "presented_on": "presented_on", "memo_received_on": "memo_received_on",
               "notice_sent_on": "notice_sent_on", "notice_delivered_on": "notice_delivered_on",
               "complainant": "complainant", "cheque_number": "chequeNo"}


def parse_return_file(text: str, complainant: str) -> tuple[list[tuple[str, dict]], list[str]]:
    """One matter per row. Dates must be YYYY-MM-DD; a row with a bad date is skipped and reported, never repaired."""
    rows, problems = [], []
    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames or "drawer" not in [f.strip().lower() for f in reader.fieldnames]:
        return [], ["The file needs a header row with at least a 'drawer' column."]
    for n, raw in enumerate(reader, start=2):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not r.get("drawer"):
            problems.append(f"Row {n}: no drawer name, skipped.")
            continue
        entries, bad = {}, None
        for col in ("cheque_date", "presented_on", "memo_received_on", "notice_sent_on", "notice_delivered_on"):
            if r.get(col):
                try:
                    date.fromisoformat(r[col])
                    entries[col] = r[col]
                except ValueError:
                    bad = col
        if bad:
            problems.append(f"Row {n}: {bad} is not a date like 2026-11-21, skipped.")
            continue
        prof = {"ref": r.get("reference") or None, "accused": r["drawer"], "city": r.get("city") or "",
                "complainant": r.get("complainant") or complainant, "amount": r.get("amount") or 0,
                "chequeNo": r.get("cheque_number") or "", "court": f"Judicial Magistrate First Class, {r['city']}" if r.get("city") else "",
                "entries": entries}
        rows.append((f"{prof['complainant']} v. {r['drawer']}", prof))
    return rows, problems
