"""Statutory windows for a Section 138 (Negotiable Instruments Act, 1881) matter.

Plain date arithmetic, no model involved. Two conventions, each tied to its source:

* Cheque validity (three months) and anything else that counts the first day: the period ends on the
  day BEFORE the same calendar date three months later (banking practice).
* The complaint month (Section 142(1)(b)): the day the cause of action arose is excluded
  (Section 9, General Clauses Act; Econ Antri v. Rom Industries, 2013), so the month ends on the SAME
  calendar date one month later. The reading one day earlier is kept as `conservative_closes`.

If the corresponding date does not exist (31 Jan + 1 month) the period ends on the last day of the
shorter month. See docs/decisions/0004 and docs/research/02-legal-rules.md.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

Status = Literal["unknown", "upcoming", "open", "closing", "expired", "met"]
CLOSING_DAYS = 5


@dataclass(frozen=True)
class Window:
    key: str
    label: str
    opens: date | None
    closes: date | None
    status: Status
    rule: str
    days_left: int | None
    conservative_closes: date | None = None


def month_period_end(start: date, months: int) -> date:
    """Last day of a period of `months` calendar months beginning on `start` (day 1 = start)."""
    index = start.year * 12 + (start.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    if start.day > last:                      # corresponding date does not exist
        return date(year, month, last)
    return date(year, month, start.day) - timedelta(days=1)


def month_after(start: date, months: int) -> date:
    """The same calendar date `months` later; the last day of the month when that date does not exist."""
    index = start.year * 12 + (start.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def _status(opens: date | None, closes: date | None, today: date) -> tuple[Status, int | None]:
    if opens is None or closes is None:
        return "unknown", None
    if today < opens:
        return "upcoming", None
    if today > closes:
        return "expired", None
    left = (closes - today).days
    return ("closing" if left <= CLOSING_DAYS else "open"), left


def compute_windows(
    cheque_date: date | None,
    memo_received_on: date | None,
    notice_sent_on: date | None,
    notice_delivered_on: date | None,
    today: date,
    presented_on: date | None = None,
) -> list[Window]:
    """Four windows in order: validity, notice, payment, complaint."""
    # 1. Presentation within the cheque's three-month validity (proviso (a)).
    v_closes = month_period_end(cheque_date, 3) if cheque_date else None
    if cheque_date is None:
        v_status: Status = "unknown"
    elif presented_on is None:
        v_status = "unknown"
    else:
        v_status = "met" if presented_on <= v_closes else "expired"
    validity = Window(
        "validity", "Cheque presented within validity", cheque_date, v_closes, v_status,
        "Three months from the date on the cheque (proviso (a)); shown as the day before the same "
        "calendar date. Needs the date the cheque was presented to the bank.", None)

    # 2. Demand notice within 30 days of receiving the bank's information (proviso (b)).
    n_opens = memo_received_on
    n_closes = memo_received_on + timedelta(days=30) if memo_received_on else None
    if notice_sent_on is not None and n_closes is not None:
        n_status: Status = "met" if notice_sent_on <= n_closes else "expired"
        n_left = None
    else:
        n_status, n_left = _status(n_opens, n_closes, today)
    notice = Window(
        "notice", "Demand notice to the drawer", n_opens, n_closes, n_status,
        "Within 30 days of receiving the bank's information that the cheque was returned. "
        "Needs the date the return memo was received.", n_left)

    # 3. Drawer's fifteen days to pay, counted from the day after receipt of the notice (proviso (c)).
    p_opens = notice_delivered_on + timedelta(days=1) if notice_delivered_on else None
    p_closes = notice_delivered_on + timedelta(days=15) if notice_delivered_on else None
    p_status, p_left = _status(p_opens, p_closes, today)
    payment = Window(
        "payment", "Drawer's time to pay", p_opens, p_closes, p_status,
        "Fifteen days from the day after the drawer received the notice. "
        + ("" if notice_delivered_on else "Needs the date the drawer received the notice; "
           "no date is assumed."), p_left)

    # 4. Complaint within one month from the day after the fifteen days end (s.142(1)(b)).
    c_opens = p_closes + timedelta(days=1) if p_closes else None
    c_closes = month_after(c_opens, 1) if c_opens else None
    c_safe = month_period_end(c_opens, 1) if c_opens else None
    c_status, c_left = _status(c_opens, c_closes, today)
    complaint = Window(
        "complaint", "Complaint before the Magistrate", c_opens, c_closes, c_status,
        "One month from the day payment fell due, the first day excluded (Econ Antri v. Rom Industries), "
        "so the last day has the same date one month on. Counting from the cause-of-action day gives a "
        "date one day earlier, kept as the conservative date. Court holidays and delay condonation are "
        "not applied: lawyer to confirm.",
        c_left, c_safe)

    return [validity, notice, payment, complaint]
