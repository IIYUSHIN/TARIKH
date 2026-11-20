"""The report builder's own guarantees: citations, labels, boundary cases and the refusal to finish with open markers.
The LibreOffice render and page-count check run in `python -m report.build_report`, not here."""
import re
from datetime import date

from report import content as C
from report.build_report import Build, deadline_cases, roman, worked_cases, working_days


def test_roman_numbers_for_front_matter():
    assert [roman(n) for n in (1, 4, 6, 9, 10)] == ["i", "iv", "vi", "ix", "x"]


def test_boundary_cases_are_computed_by_the_real_engine_and_fail_loudly_if_it_changes():
    rows = deadline_cases()
    assert len(rows) == 7
    assert rows[0][2] == "Ends 9 Apr 2026"
    assert "cannot be worked out" in rows[-1][2]


def test_worked_example_matches_the_screen():
    rows = worked_cases()
    assert rows[2] == ["Drawer's time to pay", "4 Nov 2026", "18 Nov 2026", "Ended"]
    assert rows[3][3] == "Open, 27 days left"


def test_citations_are_numbered_in_order_of_first_use():
    b = Build([], {})
    assert b.resolve("{c:rbi}{c:nia}{c:rbi}") == "[1][2][1]"
    assert b.refs == ["rbi", "nia"]


def test_every_cited_key_has_a_reference_and_every_reference_is_cited():
    text = repr(C.chapters(deadline_cases(), worked_cases()) + C.appendices()) + repr(deadline_cases())
    cited = set(re.findall(r"\{c:(\w+)\}", text))
    assert cited <= set(C.REFERENCES), cited - set(C.REFERENCES)
    assert set(C.REFERENCES) <= cited, set(C.REFERENCES) - cited


def test_the_internship_fills_eighteen_five_day_blocks_ending_on_30_october():
    days = working_days()
    assert days[0] == date(2026, 7, 3) and days[-1] == date(2026, 10, 30) and len(days) == 86
    assert len(C.WEEKS) == 17


def test_open_markers_are_collected_so_final_can_refuse(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "evidence", lambda: None)
    b = Build([], {})
    b.render()
    assert any("live run" in m or "result sentence" in m for m in b.pending)
