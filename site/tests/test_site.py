"""Browser tests for the Tarikh site. Run from site/:  python -m pytest tests -q
Builds the site, serves dist/ locally, drives it in Chromium."""
import functools, http.server, posixpath, socketserver, subprocess, sys, threading
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def base():
    subprocess.run([sys.executable, "build.py"], cwd=SITE, check=True, capture_output=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(SITE / "dist")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser, base):
    p = browser.new_page(viewport={"width": 1440, "height": 900})
    yield p
    p.close()


def test_home_table_starts_on_the_real_dates(page, base):
    page.goto(base + "index.html")
    assert page.inner_text("#table .lt-date .big") == "19 December"
    assert "29 days left" in page.inner_text("#table .pill")


def test_moving_the_notice_pin_with_the_keyboard_moves_the_window(page, base):
    page.goto(base + "index.html")
    notice = page.locator("#table input[aria-label='Date the demand notice was sent']")
    notice.focus()
    for _ in range(10):
        page.keyboard.press("ArrowRight")
    # notice now sent 9 Nov, which also pushes delivery to 9 Nov: window 25 Nov to 25 Dec
    assert page.inner_text("#table .lt-date .big") == "25 December"
    assert "moved from" in page.inner_text("#table .lt-legend")


def test_a_late_notice_is_called_out_not_hidden(page, base):
    page.goto(base + "clocks.html")
    notice = page.locator("input[aria-label='Date the demand notice was sent']")
    notice.focus()
    for _ in range(15):
        page.keyboard.press("ArrowRight")
    assert "after its 30 days closed" in page.inner_text(".lt-date .note")


def test_reset_restores_the_real_dates(page, base):
    page.goto(base + "index.html")
    page.locator("#table input[aria-label='Date the demand notice was sent']").focus()
    page.keyboard.press("ArrowRight")
    page.click("text=Back to the real dates")
    assert page.inner_text("#table .lt-date .big") == "19 December"


def test_docket_is_ordered_by_urgency_with_computed_status(page, base):
    page.goto(base + "app/docket.html")
    names = page.locator(".docket .nm").all_inner_texts()
    assert names == ["Dhillon Cold Storage", "Kalra Fabricators", "Mehra Agro Supplies", "Bhatia Timber Mart"]
    assert page.locator(".docket .st").first.inner_text() == "5 days left"
    assert "closed 27 days ago" in page.locator(".docket .st").last.inner_text()


def test_approval_needs_a_name_and_a_tick(page, base):
    page.goto(base + "app/brief.html")
    page.click("text=Approve brief")
    assert "Type your name" in page.inner_text("#approver-err")
    page.fill("#approver", "R. K. Sandhu")
    page.click("text=Approve brief")
    assert "Tick the box" in page.inner_text("#approver-err")
    page.check("#approve-check")
    page.click("text=Approve brief")
    assert "Approved by R. K. Sandhu" in page.inner_text("#approve-ok")


def test_contact_form_prepares_a_github_issue_and_sends_nothing(page, base):
    sent = []
    page.on("request", lambda r: sent.append(r.url) if r.method == "POST" else None)
    page.goto(base + "contact.html")
    page.click("text=Prepare my message")
    assert page.inner_text("#c-name-err") == "This field is required."
    page.fill("#c-name", "Asha")
    page.fill("#c-msg", "Walkthrough please")
    page.click("text=Prepare my message")
    href = page.get_attribute("#form-link", "href")
    assert href.startswith("https://github.com/IIYUSHIN/TARIKH/issues/new?title=")
    assert "Walkthrough%20please" in href
    assert sent == []


def test_every_internal_link_resolves(browser, base):
    p = browser.new_page()
    seen, queue, bad = set(), ["index.html"], []
    while queue:
        u = queue.pop()
        if u in seen:
            continue
        seen.add(u)
        r = p.goto(base + u)
        if r.status != 200:
            bad.append(u)
            continue
        for h in p.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
            if h.startswith(("http", "mailto", "#")):
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(u), h.split("#")[0]))
            if target not in seen:
                queue.append(target)
    p.close()
    assert not bad, bad
    assert len(seen) == 13  # every page except 404, which nothing links to
    assert (SITE / "dist" / "404.html").exists()


def test_no_third_party_requests_on_any_page(browser, base):
    p = browser.new_page()
    external = []
    p.on("request", lambda r: external.append(r.url) if not r.url.startswith(base) and not r.url.startswith("data:") else None)
    for u in ["index.html", "desk.html", "clocks.html", "app/matter.html", "docs.html"]:
        p.goto(base + u)
    p.close()
    assert external == []


def test_phone_menu_opens_and_closes_with_escape(browser, base):
    p = browser.new_page(viewport={"width": 390, "height": 844})
    p.goto(base + "index.html")
    assert not p.is_visible("#site-nav")
    p.click(".menu-btn")
    assert p.is_visible("#site-nav")
    p.keyboard.press("Escape")
    assert not p.is_visible("#site-nav")
    p.close()


def test_reduced_motion_shows_everything_without_scrolling(browser, base):
    ctx = browser.new_context(reduced_motion="reduce", viewport={"width": 1440, "height": 900})
    p = ctx.new_page()
    p.goto(base + "index.html")
    assert p.evaluate("getComputedStyle(document.querySelector('.clock')).opacity") == "1"
    ctx.close()
