"""Screen captures for the report, taken from a running Tarikh server (the real interface, the fictional sample matters).
Only screens whose content does not come from an Azure model are captured, so every word in them is produced by the platform's
own code: the website, accounts, the desk, the clocks, hearings, drafts (templates), settlement, the audit log, diary and portfolio.
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


def shot(name, fn):
    try:
        fn(); print("ok  ", name)
    except Exception as e:  # one failed capture must not lose the others
        print("FAIL", name, type(e).__name__, str(e)[:160])


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
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2, locale="en-IN", timezone_id="Asia/Kolkata")
        pg = ctx.new_page()

        # ---------------- the public website
        pg.goto(url + "index.html"); pg.wait_for_timeout(1200)
        pg.screenshot(path=OUT / "shot_home.png")

        def menu():
            pg.goto(url + "index.html"); pg.wait_for_timeout(600)
            pg.hover("button[aria-controls=dd-products]"); pg.click("button[aria-controls=dd-products]"); pg.wait_for_timeout(900)
            pg.screenshot(path=OUT / "g_menu.png")
        shot("menu", menu)

        def section(sel, name):
            def f():
                pg.goto(url + "index.html"); pg.wait_for_timeout(400)
                el = pg.locator(sel)
                el.scroll_into_view_if_needed(); pg.mouse.wheel(0, 1); pg.wait_for_timeout(1600)
                el.screenshot(path=OUT / name)
            return f
        shot("why", section("section[aria-labelledby=why-h]", "g_why.png"))
        shot("directions", section("#directions", "g_directions.png"))

        def check():
            pg.goto(url + "check.html"); pg.wait_for_timeout(500)
            pg.click("#ck-sample"); pg.wait_for_timeout(1200)
            pg.locator("#check-result").scroll_into_view_if_needed(); pg.wait_for_timeout(900)
            pg.screenshot(path=OUT / "g_check.png", full_page=False)
        shot("check", check)

        def platform():
            pg.goto(url + "platform.html"); pg.wait_for_timeout(1300)
            pg.screenshot(path=OUT / "g_platform.png")
        shot("platform", platform)

        # ---------------- accounts
        pg.goto(url + "signup.html"); pg.wait_for_timeout(500)
        pg.fill("#a-name", "Simran Grewal"); pg.fill("#a-chambers", "Grewal & Associates"); pg.fill("#a-email", "simran@grewal.example")
        pg.screenshot(path=OUT / "shot_signup.png")
        pg.fill("#a-pass", "a long sample password"); pg.click("button[type=submit]"); pg.wait_for_url("**/app/index.html")
        pg.wait_for_selector("#load-samples"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / "g_empty.png")
        pg.click("#load-samples"); pg.wait_for_selector("text=Deadlines, most urgent first"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / "shot_desk.png")

        ids = pg.evaluate("fetch('/api/desk').then(r=>r.json()).then(j=>Object.fromEntries(j.matters.map(m=>[m.ref,m.id])))")
        mid = ids["KF-1042"]
        pg.evaluate("""async (id) => {
          const post = (u, j) => fetch(u, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(j)});
          await post('/api/desk/' + id + '/hearings', {date: '2026-11-18', purpose: 'Appearance of accused', outcome: 'Accused appeared; bail bond furnished; copies supplied',
                                                         next_date: '2026-12-09', next_purpose: 'Notice of accusation under Section 251'});
          await post('/api/desk/' + id + '/settlement', {total: 485000, parts: 3, paid: 1});
        }""", mid)

        def tab(name, fname, prep=None):
            def f():
                pg.goto(url + "app/matter.html#" + mid); pg.wait_for_selector(".tabs"); pg.wait_for_timeout(300)
                pg.click(f".tabs button[data-t={name}]"); pg.wait_for_timeout(600)
                if prep:
                    prep()
                pg.screenshot(path=OUT / fname, full_page=False)
            return f

        pg.goto(url + "app/matter.html#" + mid); pg.wait_for_selector(".lt-date"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / "shot_matter.png")

        def hearing():
            pg.fill("form input[type=date] >> nth=0", "2026-11-20") if pg.locator("form input[type=date]").count() else None
        shot("hearings", tab("hearings", "g_hearings.png"))
        shot("drafts-tab", tab("drafts", "g_drafts_tab.png"))

        def settle_prep():
            pg.check("input[name=stage][value='5']", force=True); pg.wait_for_timeout(500)
        shot("settle", tab("settle", "g_settle.png", settle_prep))

        def clocks_scroll():
            pg.mouse.wheel(0, 640); pg.wait_for_timeout(700)
        shot("dates", tab("clocks", "g_dates.png", clocks_scroll))

        def add_hearing():
            pg.goto(url + "app/matter.html#" + mid); pg.wait_for_selector(".tabs")
            pg.click(".tabs button[data-t=settle]"); pg.wait_for_timeout(400)
            pg.click(".tabs button[data-t=activity]"); pg.wait_for_timeout(600)
            pg.screenshot(path=OUT / "g_activity.png")
        shot("activity", add_hearing)

        # a matter with no papers shows the reading step itself
        other = next(v for k, v in ids.items() if k != "KF-1042")

        def papers():
            pg.goto(url + "app/matter.html#" + other); pg.wait_for_selector(".tabs"); pg.click(".tabs button[data-t=papers]"); pg.wait_for_timeout(600)
            pg.screenshot(path=OUT / "g_papers.png")
        shot("papers", papers)

        def page(path, fname, wait="main", extra=None):
            def f():
                pg.goto(url + path); pg.wait_for_selector(wait); pg.wait_for_timeout(900)
                if extra:
                    extra()
                pg.screenshot(path=OUT / fname)
            return f
        shot("matters", page("app/matters.html", "g_matters.png"))
        shot("diary", page("app/diary.html", "g_diary.png"))
        shot("drafts", page("app/drafts.html", "g_drafts.png"))

        def palette():
            pg.keyboard.press("Control+k"); pg.wait_for_timeout(400); pg.keyboard.type("kalra"); pg.wait_for_timeout(500)
        shot("palette", page("app/index.html", "g_palette.png", extra=palette))

        def rail():
            pg.click(".app .collapse"); pg.wait_for_timeout(700)
        shot("rail", page("app/index.html", "g_rail.png", extra=rail))
        pg.evaluate("try{localStorage.removeItem('tarikh.rail')}catch(e){}")

        def portfolio():
            pg.goto(url + "app/portfolio.html"); pg.wait_for_selector("#imp"); pg.click("#imp"); pg.wait_for_timeout(500)
            pg.screenshot(path=OUT / "g_import.png")
            pg.click("#impsample"); pg.wait_for_selector("text=24 matters opened"); pg.wait_for_timeout(2900)
            pg.screenshot(path=OUT / "shot_portfolio.png")
        shot("portfolio", portfolio)

        ph = ctx.new_page(); ph.set_viewport_size({"width": 390, "height": 844})

        def phone():
            ph.goto(url + "app/index.html"); ph.wait_for_selector("text=Deadlines, most urgent first"); ph.wait_for_timeout(500)
            ph.screenshot(path=OUT / "shot_phone.png")
        shot("phone", phone)

        def phone_home():
            ph.goto(url + "index.html"); ph.wait_for_timeout(1200)
            ph.screenshot(path=OUT / "g_phone_home.png")
            ph.click(".menu-btn"); ph.wait_for_timeout(800)
            ph.screenshot(path=OUT / "g_phone_menu.png")
        shot("phone_home", phone_home)

        def phone_matter():
            ph.goto(url + "app/matter.html#" + mid); ph.wait_for_selector(".tabs"); ph.wait_for_timeout(700)
            ph.screenshot(path=OUT / "g_phone_matter.png")
        shot("phone_matter", phone_matter)

        def signin():
            c2 = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2, locale="en-IN", timezone_id="Asia/Kolkata"); q = c2.new_page()
            q.goto(url + "signin.html"); q.wait_for_timeout(700); q.fill("#a-email", "simran@grewal.example")
            q.screenshot(path=OUT / "g_signin.png"); c2.close()
        shot("signin", signin)
        b.close()
    server.should_exit = True


def frame():
    """A thin grey rule round each capture, so a white screen does not melt into the white page; phones side by side."""
    from PIL import Image, ImageOps
    for f in list(OUT.glob("g_*.png")) + list(OUT.glob("shot_*.png")):
        if f.name == "g_phones.png":
            continue
        im = Image.open(f).convert("RGB")
        ImageOps.expand(im.crop((2, 2, im.width - 2, im.height - 2)), border=2, fill="#B8B8B8").save(f)
    ims = [Image.open(OUT / n).convert("RGB") for n in ("g_phone_home.png", "g_phone_menu.png", "g_phone_matter.png")]
    h, gap = 1600, 60
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    c = Image.new("RGB", (sum(i.width for i in ims) + gap * 2, h), "white"); x = 0
    for i in ims:
        c.paste(i, (x, 0)); x += i.width + gap
    c.save(OUT / "g_phones.png")


if __name__ == "__main__":
    main(); frame(); print("shots done")
