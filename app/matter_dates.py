"""Bridge between a stored matter and the deadline engine: read the dates the facts hold, never invent one."""
from __future__ import annotations

from datetime import date

from .deadlines import Window, compute_windows
from .models import Matter


def fact_value(matter: Matter, key: str) -> str | None:
    for d in matter.documents:
        for f in d.facts:
            if f.key == key and f.value:
                return f.value
    return None


def _date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None  # a value that is not a date is treated as missing, never repaired


def windows_for_matter(matter: Matter, today: date) -> list[Window]:
    return compute_windows(
        cheque_date=_date(fact_value(matter, "cheque_date")),
        memo_received_on=_date(fact_value(matter, "memo_received_on")),
        notice_sent_on=_date(fact_value(matter, "notice_sent_on")),
        notice_delivered_on=_date(fact_value(matter, "notice_delivered_on")),
        today=today,
        presented_on=_date(fact_value(matter, "presented_on")),
    )


def window_dict(w: Window) -> dict:
    return {"key": w.key, "label": w.label, "opens": w.opens.isoformat() if w.opens else None,
            "closes": w.closes.isoformat() if w.closes else None, "status": w.status,
            "days_left": w.days_left, "rule": w.rule}
