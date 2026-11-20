from datetime import date

import pytest

from app.deadlines import compute_windows, month_after, month_period_end


@pytest.mark.parametrize("start, months, expected", [
    (date(2026, 4, 8), 1, date(2026, 5, 7)),      # ordinary: day before the same date next month
    (date(2026, 1, 10), 3, date(2026, 4, 9)),     # cheque validity shape
    (date(2026, 1, 31), 1, date(2026, 2, 28)),    # shorter month: ends on its last day
    (date(2024, 1, 31), 1, date(2024, 2, 29)),    # leap year
    (date(2026, 11, 30), 3, date(2027, 2, 28)),   # three months, shorter month
])
def test_month_period_end(start, months, expected):
    assert month_period_end(start, months) == expected


def _by_key(windows):
    return {w.key: w for w in windows}


def test_all_unknown_when_no_dates_given():
    w = _by_key(compute_windows(None, None, None, None, today=date(2026, 5, 1)))
    assert [w[k].status for k in ("validity", "notice", "payment", "complaint")] == ["unknown"] * 4
    assert w["payment"].closes is None and w["complaint"].closes is None


def test_payment_window_matches_published_example_2017():
    # Published example: notice served 5 May 2017, 15 days run 6 May to 20 May.
    w = _by_key(compute_windows(None, None, None, date(2017, 5, 5), today=date(2017, 5, 10)))
    assert (w["payment"].opens, w["payment"].closes) == (date(2017, 5, 6), date(2017, 5, 20))


def test_complaint_window_matches_published_march_april_example():
    # Published example: notice delivered 23 March, drawer's 15 days end 7 April, complaint filed 2 May.
    w = _by_key(compute_windows(None, None, None, date(2026, 3, 23), today=date(2026, 4, 10)))
    assert w["payment"].closes == date(2026, 4, 7)
    assert w["complaint"].opens == date(2026, 4, 8)
    assert w["complaint"].opens <= date(2026, 5, 2) <= w["complaint"].closes
    # Econ Antri v. Rom Industries (2013): the day the cause of action arose is excluded, so the month
    # ends on the same calendar date. The one-day-earlier reading is kept as the conservative date.
    assert w["complaint"].closes == date(2026, 5, 8)
    assert w["complaint"].conservative_closes == date(2026, 5, 7)


@pytest.mark.parametrize("start, months, expected", [
    (date(2026, 11, 19), 1, date(2026, 12, 19)),   # same calendar date next month
    (date(2026, 12, 19), 1, date(2027, 1, 19)),    # across a year end
    (date(2026, 1, 31), 1, date(2026, 2, 28)),     # no such date: last day of the shorter month
    (date(2024, 1, 31), 1, date(2024, 2, 29)),     # leap year
])
def test_month_after_is_the_same_calendar_date(start, months, expected):
    assert month_after(start, months) == expected


def test_notice_to_complaint_example_in_the_site_demo():
    # Notice delivered 3 Nov 2026: drawer's 15 days end 18 Nov, complaint 19 Nov to 19 Dec, aim for 18 Dec.
    w = _by_key(compute_windows(None, None, None, date(2026, 11, 3), today=date(2026, 11, 20)))
    assert (w["complaint"].opens, w["complaint"].closes) == (date(2026, 11, 19), date(2026, 12, 19))
    assert w["complaint"].conservative_closes == date(2026, 12, 18)
    assert w["complaint"].days_left == 29


def test_complaint_window_month_end_leap_year():
    w = _by_key(compute_windows(None, None, None, date(2024, 1, 15), today=date(2024, 1, 20)))
    assert w["payment"].closes == date(2024, 1, 30)
    assert (w["complaint"].opens, w["complaint"].closes) == (date(2024, 1, 31), date(2024, 2, 29))


def test_missing_delivery_date_never_guessed_even_if_sent_date_known():
    w = _by_key(compute_windows(None, date(2026, 3, 1), date(2026, 3, 10), None, today=date(2026, 3, 12)))
    assert w["payment"].status == "unknown" and w["payment"].closes is None
    assert w["complaint"].status == "unknown" and w["complaint"].closes is None
    assert "date" in w["payment"].rule.lower()


def test_notice_window_thirty_days_and_met_or_expired():
    base = dict(cheque_date=None, memo_received_on=date(2026, 3, 1), notice_delivered_on=None, today=date(2026, 4, 20))
    on_time = _by_key(compute_windows(notice_sent_on=date(2026, 3, 31), **base))["notice"]
    late = _by_key(compute_windows(notice_sent_on=date(2026, 4, 1), **base))["notice"]
    assert on_time.closes == date(2026, 3, 31) and on_time.status == "met"
    assert late.status == "expired"


def test_status_closing_within_five_days_else_open():
    five = _by_key(compute_windows(None, None, None, date(2026, 6, 1), today=date(2026, 6, 11)))["payment"]
    six = _by_key(compute_windows(None, None, None, date(2026, 6, 1), today=date(2026, 6, 10)))["payment"]
    assert (five.closes, five.status, five.days_left) == (date(2026, 6, 16), "closing", 5)
    assert (six.status, six.days_left) == ("open", 6)


def test_status_upcoming_and_expired_for_complaint():
    before = _by_key(compute_windows(None, None, None, date(2026, 6, 1), today=date(2026, 6, 5)))["complaint"]
    after = _by_key(compute_windows(None, None, None, date(2026, 6, 1), today=date(2026, 8, 1)))["complaint"]
    assert before.status == "upcoming" and before.days_left is None
    assert after.status == "expired"


def test_validity_uses_presentation_date():
    ok = _by_key(compute_windows(date(2026, 1, 10), None, None, None, today=date(2026, 5, 1), presented_on=date(2026, 4, 9)))
    stale = _by_key(compute_windows(date(2026, 1, 10), None, None, None, today=date(2026, 5, 1), presented_on=date(2026, 4, 10)))
    unknown = _by_key(compute_windows(date(2026, 1, 10), None, None, None, today=date(2026, 5, 1)))
    assert ok["validity"].status == "met" and ok["validity"].closes == date(2026, 4, 9)
    assert stale["validity"].status == "expired"
    assert unknown["validity"].status == "unknown" and unknown["validity"].closes == date(2026, 4, 9)


def test_rules_state_the_convention_and_lawyer_checks():
    w = _by_key(compute_windows(date(2026, 1, 10), date(2026, 3, 1), date(2026, 3, 5), date(2026, 3, 8), today=date(2026, 3, 9)))
    assert all(x.rule for x in w.values())
    c = w["complaint"].rule.lower()
    assert "holiday" in c and "condonation" in c and "earlier" in c
