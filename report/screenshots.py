"""Screenshots of the running application for the report. Uses the test-double server, so the readings shown are fixtures
until the live evidence run replaces them (see report/content.py PENDING markers)."""
import subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "build"
PORT = 8792
URL = f"http://127.0.0.1:{PORT}/"


def main():
    proc = subprocess.Popen([sys.executable, "-m", "tests.ui_server", str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(URL + "api/mode", timeout=0.5); break
            except Exception:
                time.sleep(0.2)
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
            pg.goto(URL); pg.wait_for_timeout(600)
            pg.screenshot(path=OUT / "shot_home.png")
            pg.click("text=Open the fictional sample matter"); pg.wait_for_selector("[data-testid=clock]"); pg.wait_for_timeout(700)
            pg.screenshot(path=OUT / "shot_desk.png")
            pg.locator("[data-testid=clock]").scroll_into_view_if_needed()
            for label, val in [("Memo received by payee", "2026-10-05"), ("Notice posted on", "2026-10-30"), ("Notice received by drawer", "2026-11-03")]:
                pg.get_by_label(label, exact=True).fill(val); pg.keyboard.press("Tab")
                pg.wait_for_function("document.querySelector('[data-testid=answer]').innerText.length>0")
            pg.wait_for_timeout(600)
            pg.locator("[data-testid=clock]").screenshot(path=OUT / "shot_clock.png")
            pg.get_by_role("button", name="Draft the brief").click(); pg.wait_for_selector("[data-testid=brief]")
            pg.get_by_label("Reviewing advocate").fill("Adv. R. Sharma")
            pg.get_by_role("button", name="Approve brief").click(); pg.wait_for_selector(".memo--approved"); pg.wait_for_timeout(400)
            pg.locator("[data-testid=brief]").screenshot(path=OUT / "shot_brief.png")
            ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            ph.goto(URL); ph.click("text=Open the fictional sample matter"); ph.wait_for_selector("[data-testid=clock]"); ph.wait_for_timeout(700)
            ph.screenshot(path=OUT / "shot_phone.png")
            b.close()
    finally:
        proc.terminate()


if __name__ == "__main__":
    main(); print("shots ok")
