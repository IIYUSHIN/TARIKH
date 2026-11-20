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


def test_home_live_table_starts_on_the_sample_matter(page, base):
    page.goto(base + "index.html")
    assert page.inner_text("#count .lt-date .big") == "19 December"


def test_moving_the_notice_pin_moves_the_complaint_window(page, base):
    page.goto(base + "index.html")
    page.locator("#count input[aria-label='Date the demand notice was sent']").focus()
    for _ in range(10):
        page.keyboard.press("ArrowRight")
    assert page.inner_text("#count .lt-date .big") == "25 December"
    page.click("#count >> text=Back to the real dates")
    assert page.inner_text("#count .lt-date .big") == "19 December"


def test_hero_today_window_is_computed_from_the_sample_data(page, base):
    page.goto(base + "index.html")
    rows = page.locator("[data-mini-today] .row b").all_inner_texts()
    assert rows[0] == "Dhillon Cold Storage"
    assert "5 days to file" in page.inner_text("[data-mini-today]")


def test_check_tool_counts_from_the_dates_entered(page, base):
    page.goto(base + "check.html")
    page.click("text=Count my dates")
    assert "return memo" in page.inner_text("#ck-err")
    page.click("#ck-sample")
    assert page.inner_text("[data-r=lead]") == "File the complaint by 19 December 2026."
    page.fill("#ck-sent", "")
    page.fill("#ck-delivered", "")
    page.click("text=Count my dates")
    assert "notice" in page.inner_text("[data-r=lead]").lower()


def test_settlement_calculator_uses_the_2025_stages(page, base):
    page.goto(base + "index.html")
    box = page.locator("#settle [data-settle]")
    box.locator("input[name=amount]").fill("100000")
    box.locator("input[value='7.5']").check()
    assert box.locator("[data-o=cost]").inner_text() == "₹7,500"
    assert box.locator("[data-o=total]").inner_text() == "₹1,07,500"


def test_matters_are_ordered_by_urgency(page, base):
    page.goto(base + "app/matters.html")
    names = page.locator(".dtable tbody tr td:first-child b").all_inner_texts()
    assert names[:2] == ["Preet Bakers", "Dhillon Cold Storage"]
    page.click("button[data-f=closed]")
    assert page.locator(".dtable tbody tr").count() == 1


def test_entering_a_missing_date_starts_the_clocks(page, base):
    page.goto(base + "app/matter.html#PB-1130")
    page.fill("#f-memo", "2026-11-14")
    page.click("text=Save and count")
    assert "Notice must go by 14 December 2026" in page.inner_text("#mt")


def test_draft_cannot_be_approved_with_facts_missing(page, base):
    page.goto(base + "app/drafts.html#RM-1121")
    page.click("button[data-d=complaint]")
    page.fill("#apn", "S. Grewal")
    page.check("#apc")
    page.click("text=Approve draft")
    assert "still to be entered" in page.inner_text("#ape")


def test_draft_approval_needs_name_and_tick(page, base):
    page.goto(base + "app/drafts.html#KF-1042")
    page.click("text=Approve draft")
    assert "Type your name" in page.inner_text("#ape")
    page.fill("#apn", "S. Grewal")
    page.click("text=Approve draft")
    assert "Tick the box" in page.inner_text("#ape")
    page.check("#apc")
    page.click("text=Approve draft")
    assert page.inner_text("#ape") == ""


def test_portfolio_bulk_assign(page, base):
    page.goto(base + "app/portfolio.html")
    page.select_option("#fa", "none")
    n = page.locator("tbody tr[data-id]").count()
    assert n == 7
    page.check("#sall")
    page.click("#bgo")
    page.select_option("#fa", "none")
    assert page.locator("tbody tr[data-id]").count() == 0


def test_command_palette_finds_a_matter(page, base):
    page.goto(base + "app/index.html")
    page.keyboard.press("Control+k")
    page.fill("#palette-q", "kalra")
    page.keyboard.press("Enter")
    page.wait_for_url("**/matter.html#KF-1042")
    assert "Kalra Fabricators" in page.inner_text("h1")


def test_early_access_prepares_a_github_issue_and_sends_nothing(page, base):
    sent = []
    page.on("request", lambda r: sent.append(r.url) if r.method == "POST" else None)
    page.goto(base + "contact.html")
    page.click("text=Prepare my request")
    assert page.inner_text("#c-name-err") == "This field is required."
    page.fill("#c-name", "Asha")
    page.fill("#c-msg", "About 200 matters")
    page.click("text=Prepare my request")
    href = page.get_attribute("#form-link", "href")
    assert href.startswith("https://github.com/IIYUSHIN/TARIKH/issues/new?title=")
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
    assert len(seen) == 19  # every page except 404, which nothing links to


def test_no_third_party_requests(browser, base):
    p = browser.new_page()
    external = []
    p.on("request", lambda r: external.append(r.url) if not r.url.startswith(base) and not r.url.startswith("data:") else None)
    for u in ["index.html", "platform.html", "check.html", "app/index.html", "app/portfolio.html"]:
        p.goto(base + u)
    p.close()
    assert external == []


def test_phone_menu_opens_and_closes_with_escape(browser, base):
    p = browser.new_page(viewport={"width": 390, "height": 844})
    p.goto(base + "index.html")
    assert not p.is_visible("#mainnav")
    p.click(".menu-btn")
    assert p.is_visible("#mainnav")
    p.keyboard.press("Escape")
    assert not p.is_visible("#mainnav")
    p.close()


def test_reduced_motion_shows_everything(browser, base):
    ctx = browser.new_context(reduced_motion="reduce", viewport={"width": 1440, "height": 900})
    p = ctx.new_page()
    p.goto(base + "index.html")
    assert p.evaluate("getComputedStyle(document.querySelector('.fact')).opacity") == "1"
    ctx.close()
