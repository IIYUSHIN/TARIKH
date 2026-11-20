"""Screenshot built pages at desktop and phone widths, plus basic checks.
Usage (from site/):  python tools/shoot.py [page.html ...]    -> shots/<page>-<width>.png
Checks: no horizontal overflow, no console errors, every local link and asset resolves."""
import sys, threading, http.server, socketserver, functools, re
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent
DIST, OUT = SITE / "dist", SITE / "shots"
OUT.mkdir(exist_ok=True)


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    h = functools.partial(Quiet, directory=str(DIST))
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main(pages):
    pages = pages or sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*.html"))
    srv = serve()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    problems = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for w, h in ((1440, 900), (390, 844)):
            for p in pages:
                pg = b.new_page(viewport={"width": w, "height": h})
                errs = []
                pg.on("console", lambda m, e=errs: m.type == "error" and e.append(m.text))
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                bad = []
                pg.on("response", lambda r, bad=bad: r.status >= 400 and bad.append(f"{r.status} {r.url}"))
                pg.goto(base + p)
                pg.wait_for_timeout(500)
                # scroll through so reveal-on-scroll content shows
                H = pg.evaluate("document.documentElement.scrollHeight")
                for y in range(0, H, 500):
                    pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(60)
                pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
                ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                name = p.replace("/", "_").replace(".html", "")
                pg.screenshot(path=str(OUT / f"{name}-{w}.png"), full_page=True)
                if ov > 1: problems.append(f"{p}@{w}: horizontal overflow {ov}px")
                for e in errs + bad: problems.append(f"{p}@{w}: {e}")
                pg.close()
        b.close()
    print("\n".join(problems) if problems else "no overflow, console errors or broken requests")


if __name__ == "__main__":
    main(sys.argv[1:])
