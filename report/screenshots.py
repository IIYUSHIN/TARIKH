"""Screen captures for the report, taken from a running Tarikh server with recorded-style test services (no Azure).
Every screen shown is the real interface; the matters are the fictional samples.
    python -m report.screenshots"""
import socket, subprocess, sys, threading, time
from datetime import date
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "build"
sys.path.insert(0, str(ROOT))
from app.accounts import Accounts  # noqa: E402
from app.main import create_app  # noqa: E402
from app.pipeline import Pipeline, Services  # noqa: E402
from app.store import Store  # noqa: E402
from tests.doubles import FakeAnalyzer, FakeAssistant, FakeExtractor, FakeReasoner, FakeSynth, FakeTranscriber  # noqa: E402


def main():
    import tempfile
    subprocess.run([sys.executable, "build.py"], cwd=ROOT / "site", check=True, capture_output=True)
    tmp = Path(tempfile.mkdtemp())
    store = Store(tmp / "t.db")
    pipe = Pipeline(store, Services(FakeExtractor(), FakeTranscriber(), FakeSynth(), FakeAnalyzer(), FakeReasoner(), FakeAssistant()),
                    tmp / "data", today=lambda: date(2026, 11, 20))
    app = create_app(pipe, store, tmp / "data", "live", lambda: None, "gpt-4.1", accounts=Accounts(tmp / "t.db"), site_dir=ROOT / "site" / "dist")
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    url = f"http://127.0.0.1:{port}/"
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        pg = ctx.new_page()
        pg.goto(url + "index.html"); pg.wait_for_timeout(1200)
        pg.screenshot(path=OUT / "shot_home.png")
        pg.goto(url + "signup.html"); pg.wait_for_timeout(500)
        pg.fill("#a-name", "Simran Grewal"); pg.fill("#a-chambers", "Grewal & Associates"); pg.fill("#a-email", "simran@grewal.example")
        pg.screenshot(path=OUT / "shot_signup.png")
        pg.fill("#a-pass", "a long sample password"); pg.click("button[type=submit]"); pg.wait_for_url("**/app/index.html")
        pg.wait_for_selector("#load-samples"); pg.click("#load-samples"); pg.wait_for_selector("text=Deadlines, most urgent first"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / "shot_desk.png")
        mid = pg.evaluate("fetch('/api/desk').then(r=>r.json()).then(j=>j.matters.find(m=>m.ref==='KF-1042').id)")
        pg.goto(url + "app/matter.html#" + mid); pg.wait_for_selector(".lt-date"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / "shot_matter.png")
        pg.goto(url + "app/portfolio.html"); pg.wait_for_selector("#imp"); pg.click("#imp"); pg.click("#impsample"); pg.wait_for_selector("text=24 matters opened"); pg.wait_for_timeout(2900)
        pg.screenshot(path=OUT / "shot_portfolio.png")
        ph = ctx.new_page(); ph.set_viewport_size({"width": 390, "height": 844})
        ph.goto(url + "app/index.html"); ph.wait_for_selector("text=Deadlines, most urgent first"); ph.wait_for_timeout(500)
        ph.screenshot(path=OUT / "shot_phone.png")
        b.close()
    server.should_exit = True


if __name__ == "__main__":
    main(); print("shots ok")
