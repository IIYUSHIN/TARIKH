"""End to end against a real Tarikh server (fake Azure services): sign up, load samples, work a matter, import, allocate, sign out."""
import socket, sys, threading, time
from datetime import date
from pathlib import Path

import pytest
import uvicorn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.accounts import Accounts  # noqa: E402
from app.main import create_app  # noqa: E402
from app.pipeline import Pipeline, Services  # noqa: E402
from app.store import Store  # noqa: E402
from tests.doubles import FakeAnalyzer, FakeAssistant, FakeExtractor, FakeReasoner, FakeSynth, FakeTranscriber  # noqa: E402


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    import subprocess
    subprocess.run([sys.executable, "build.py"], cwd=ROOT / "site", check=True, capture_output=True)
    tmp = tmp_path_factory.mktemp("live")
    store = Store(tmp / "t.db")
    pipe = Pipeline(store, Services(FakeExtractor(), FakeTranscriber(), FakeSynth(), FakeAnalyzer(), FakeReasoner(), FakeAssistant()),
                    tmp / "data", today=lambda: date(2026, 11, 20))
    app = create_app(pipe, store, tmp / "data", "live", lambda: None, "t", accounts=Accounts(tmp / "t.db"), site_dir=ROOT / "site" / "dist")
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}/"
    server.should_exit = True


def test_full_account_journey(live, browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    p = ctx.new_page()
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))
    p.goto(live + "app/index.html")
    p.wait_for_url("**/signin.html?next=*")
    p.click("text=Create an account")
    p.fill("#a-name", "Asha Grewal"); p.fill("#a-chambers", "Grewal & Associates")
    p.fill("#a-email", "asha@chambers.in"); p.fill("#a-pass", "short")
    p.click("button[type=submit]")
    p.wait_for_selector("#a-msg:has-text('8 characters')")
    p.fill("#a-pass", "correct horse battery")
    p.click("button[type=submit]")
    p.wait_for_url("**/app/index.html")
    p.wait_for_selector("text=Your desk is empty")
    assert p.inner_text("[data-me=name]") == "Asha Grewal"
    p.click("#load-samples")
    p.wait_for_selector("text=Deadlines, most urgent first")
    # open a matter, enter the missing memo date: it is saved on the server
    p.goto(live + "app/matters.html")
    p.click("text=Preet Bakers")
    p.wait_for_selector("#f-memo_received_on")
    p.fill("#f-memo_received_on", "2026-11-14")
    p.click("text=Save and count")
    p.wait_for_selector("text=Notice must go by 14 December 2026")
    p.reload(); p.wait_for_selector("#f-memo_received_on")
    assert p.input_value("#f-memo_received_on") == "2026-11-14"
    # record a hearing
    p.click("button[data-t=hearings]")
    p.fill("#h-d", "2026-11-19"); p.fill("#h-p", "Appearance of accused"); p.fill("#h-nd", "2026-12-10"); p.fill("#h-np", "Evidence")
    p.click("text=Save hearing")
    p.wait_for_selector("text=10 December 2026 · next")
    p.click("button[data-t=activity]")
    assert "Hearing recorded" in p.inner_text("#mt")
    # open a new matter from scratch
    p.goto(live + "app/matters.html")
    p.click("button[data-new]")
    p.fill("#nm-c", "Gill Tractors"); p.fill("#nm-a", "Brar Implements"); p.fill("#nm-amt", "2,10,000")
    p.fill("#nm-memo_received_on", "2026-11-10")
    p.click("text=Open matter")
    p.wait_for_selector("h1:has-text('Brar Implements')")
    # import the sample return file and allocate the unassigned matters
    p.goto(live + "app/portfolio.html")
    p.click("#imp"); p.click("#impsample")
    p.wait_for_selector("text=24 matters opened")
    p.select_option("#fa", "none")
    p.check("#sall"); p.click("#bgo")
    p.wait_for_selector("text=allocated to")
    p.wait_for_function("document.querySelectorAll('tbody tr[data-id]').length === 0")
    # sign out ends the session
    p.click("#signout")
    p.wait_for_url("**/signin.html")
    p.goto(live + "app/index.html")
    p.wait_for_url("**/signin.html?next=*")
    assert errors == []
    ctx.close()
