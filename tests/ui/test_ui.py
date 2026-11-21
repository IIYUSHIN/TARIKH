"""Browser tests against the real front end (Chromium) with test doubles behind the API and the clock fixed at 21 Nov 2026."""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[2]
PORT = 8791
URL = f"http://127.0.0.1:{PORT}/"


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen([sys.executable, "-m", "tests.ui_server", str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(URL + "api/mode", timeout=0.5)
            break
        except Exception:
            time.sleep(0.2)
    yield
    proc.terminate()


@pytest.fixture()
def page(server):
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
        yield pg
        assert pg.errors == [], pg.errors
        b.close()


def open_sample(pg):
    pg.goto(URL + "classic/")
    pg.click("text=Open the fictional sample matter")
    pg.wait_for_selector("[data-testid=clock]")


def enter_dates(pg):
    for label, val in [("Memo received by payee", "2026-10-05"), ("Notice posted on", "2026-10-30"), ("Notice received by drawer", "2026-11-03")]:
        pg.get_by_label(label, exact=True).fill(val)
        pg.keyboard.press("Tab")
        pg.wait_for_function("document.querySelector('[data-testid=answer]').innerText.length>0")
    pg.wait_for_timeout(400)


def test_missing_dates_are_named_never_guessed(page):
    open_sample(page)
    txt = page.locator("[data-testid=answer]").inner_text()
    assert "cannot be worked out" in txt and "date the drawer received the notice" in txt
    assert page.locator('[data-window=complaint][data-status=unknown]').count() == 1


def test_entering_three_dates_opens_the_complaint_window_and_scrubbing_closes_it(page):
    open_sample(page)
    enter_dates(page)
    assert "open" in page.locator("[data-testid=answer]").inner_text()
    assert "19 Dec 2026" in page.locator("[data-testid=answer]").inner_text()
    assert "18 Dec 2026" in page.locator("[data-testid=answer]").inner_text()   # the conservative date is offered, not hidden
    assert page.locator('[data-window=payment]').inner_text().count("Ended") == 1
    page.locator(".today__grip").focus()
    for _ in range(5):   # four weeks from 21 Nov is the last day, 19 Dec; the fifth press passes it
        page.keyboard.press("PageUp")
    page.wait_for_function("document.querySelector('[data-testid=answer]').innerText.includes('closed')")
    page.get_by_role("button", name="Today").click()
    page.wait_for_function("document.querySelector('[data-testid=answer]').innerText.includes('is open')")


def test_show_on_paper_outlines_the_region_and_names_the_reading(page):
    open_sample(page)
    page.locator(".fact[data-key=cheque_number]").first.get_by_role("button", name="Show on paper: Cheque number").click()
    assert page.locator(".scan polygon").count() == 1
    assert "Cheque number: 004718" in page.locator(".sheet__cap").inner_text()


def test_low_confidence_reading_is_flagged_in_words(page):
    open_sample(page)
    row = page.locator(".fact[data-key=return_date]")
    assert "Read at 58%" in row.inner_text() and "Check against the paper" in row.inner_text()


def test_brief_cites_facts_and_cannot_be_approved_without_a_name(page):
    open_sample(page)
    page.get_by_role("button", name="Draft the brief").click()
    page.wait_for_selector("[data-testid=brief]")
    assert page.locator("[data-testid=brief] .src").count() >= 1
    assert page.get_by_role("button", name="Approve brief").is_disabled()
    assert "Enter the reviewing advocate" in page.locator("#adv-why").inner_text()
    page.get_by_label("Reviewing advocate").fill("Adv. Hari Haran")
    page.get_by_role("button", name="Approve brief").click()
    page.wait_for_selector(".memo--approved")
    assert page.get_by_role("button", name="Read to the client").is_enabled()


def test_voice_upload_shows_original_and_masked_text_side_by_side(page, tmp_path):
    open_sample(page)
    wav = tmp_path / "v.wav"
    wav.write_bytes(b"RIFF" + b"0" * 64)
    page.set_input_files("#aud", str(wav))
    page.wait_for_selector("[data-testid=transcript]")
    t = page.locator("[data-testid=transcript]")
    assert "98765 43210" in t.inner_text() and "[PHONENUMBER]" in t.inner_text()
    assert page.locator("mark.masked").count() == 1


def test_ask_shows_answer(page):
    open_sample(page)
    page.get_by_label("Question about this matter").fill("When must the complaint be filed?")
    page.get_by_role("button", name="Ask", exact=True).click()
    page.wait_for_selector("text=echo: When must the complaint be filed?")


def test_phone_width_has_no_sideways_scroll_and_stacks_the_desk(server):
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 844})
        open_sample(pg)
        enter_dates(pg)
        assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        b.close()


def test_a_wrong_file_is_refused_with_its_reason(page, tmp_path):
    open_sample(page)
    bad = tmp_path / "x.png"
    bad.write_bytes(b"not an image")
    page.set_input_files("#up-cheque", str(bad))
    page.wait_for_selector("text=not a PNG")
    page.errors.clear()  # the browser logs the 422 it was meant to receive
