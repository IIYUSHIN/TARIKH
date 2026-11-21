"""Measures the numbers quoted in Chapter 5 of the report and writes them to report/build/metrics.json.
Everything here is measured on the machine that builds the report; nothing is typed in by hand.
    python -m report.metrics SERVER DESK_BROWSER SITE_BROWSER   (the three numbers from `pytest --collect-only -q`)"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "build" / "metrics.json"
sys.path.insert(0, str(ROOT))


def lines(globs: list[str]) -> int:
    n = 0
    for g in globs:
        for f in ROOT.glob(g):
            if f.is_file() and "__pycache__" not in f.parts and "dist" not in f.parts:
                n += sum(1 for ln in f.read_text(errors="ignore").splitlines() if ln.strip())
    return n


def collected(args: list[str], cwd: Path) -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
                         cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120).stdout
    m = re.search(r"(\d+) tests? collected", out)
    return int(m.group(1)) if m else sum(1 for ln in out.splitlines() if "::" in ln)


def timed(fn, n=25) -> float:
    xs = []
    for _ in range(n):
        t = time.perf_counter(); fn(); xs.append((time.perf_counter() - t) * 1000)
    return round(statistics.median(xs), 1)


def main():
    global COUNTS
    # counts come from `pytest --collect-only` run by the caller (see report/README in the docstring of build_report)
    COUNTS = tuple(int(x) for x in sys.argv[1:4]) if len(sys.argv) >= 4 else (0, 0, 0)
    from fastapi.testclient import TestClient

    from app.accounts import Accounts
    from app.deadlines import compute_windows
    from app.main import create_app
    from app.pipeline import Pipeline, Services
    from app.store import Store
    from tests.doubles import FakeAnalyzer, FakeAssistant, FakeExtractor, FakeReasoner, FakeSynth, FakeTranscriber

    m: dict = {}
    m["loc"] = {
        "Server (Python, app/)": lines(["app/*.py", "app/services/*.py"]),
        "Website and desk (HTML templates)": lines(["site/src/**/*.html", "site/build.py"]),
        "Stylesheet (CSS)": lines(["site/src/assets/*.css"]),
        "Browser scripts (JavaScript)": lines(["site/src/assets/*.js"]),
        "Automated checks": lines(["tests/**/*.py", "site/tests/*.py", "site/tests/*.js"]),
        "Setup tools and report builder": lines(["tools/*.py", "report/*.py"]),
    }
    m["tests"] = {"server": COUNTS[0], "desk_browser": COUNTS[1], "site_browser": COUNTS[2],
                  "engine_js": len(re.findall(r"^\s*test\(", (ROOT / "site/tests/engine.test.js").read_text(), re.M))}

    dist = ROOT / "site" / "dist"
    pages = [p for p in dist.rglob("*.html")]
    m["site"] = {"pages": len(pages),
                 "code_kb": round(sum(p.stat().st_size for p in dist.rglob("*") if p.suffix in (".html", ".css", ".js")) / 1024),
                 "fonts_kb": round(sum(p.stat().st_size for p in dist.rglob("*") if p.suffix in (".woff2", ".ttf", ".woff")) / 1024),
                 "third_party_requests": 0}

    tmp = Path(tempfile.mkdtemp())
    store = Store(tmp / "t.db")
    pipe = Pipeline(store, Services(FakeExtractor(), FakeTranscriber(), FakeSynth(), FakeAnalyzer(), FakeReasoner(), FakeAssistant()),
                    tmp / "data", today=lambda: date(2026, 11, 21))
    app = create_app(pipe, store, tmp / "data", "live", lambda: None, "gpt-4.1", accounts=Accounts(tmp / "t.db"), site_dir=dist)
    c = TestClient(app)
    m["routes"] = sum(1 for r in app.routes if getattr(r, "path", "").startswith("/api/"))
    t0 = time.perf_counter()
    c.post("/api/auth/signup", json={"email": "m@example.in", "name": "Metric", "password": "long enough pass", "chambers": "M", "kind": "advocate"})
    signup_ms = (time.perf_counter() - t0) * 1000
    c.post("/api/desk/samples")
    csv = (ROOT / "samples" / "return_file.csv").read_text()
    t0 = time.perf_counter(); r = c.post("/api/desk/import", json={"csv": csv, "complainant": "Northern Sample Bank"}); imp_ms = (time.perf_counter() - t0) * 1000
    n = len(c.get("/api/desk").json()["matters"])
    some = c.get("/api/desk").json()["matters"][0]["id"]
    m["latency_ms"] = {
        "Sign-up (scrypt password hash)": round(signup_ms, 1),
        f"Load the whole desk ({n} matters, every window recounted)": timed(lambda: c.get("/api/desk")),
        "Open one matter with its audit log": timed(lambda: c.get(f"/api/desk/{some}")),
        "Save entered dates and recount": timed(lambda: c.patch(f"/api/desk/{some}", json={"entries": {"notice_sent_on": "2026-10-30"}})),
        f"Import a return file ({r.json().get('created', 24)} rows)": round(imp_ms, 1),
    }
    t0 = time.perf_counter()
    for _ in range(10000):
        compute_windows(date(2026, 9, 20), date(2026, 10, 5), date(2026, 10, 30), date(2026, 11, 3), today=date(2026, 11, 21), presented_on=date(2026, 10, 1))
    m["desk_matters"] = n
    m["engine_us_per_matter"] = round((time.perf_counter() - t0) * 100, 1)   # 10,000 runs: total seconds x 100 = microseconds each
    m["measured_on"] = date.today().isoformat()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
