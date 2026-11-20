"""Build the Tarikh site: Jinja2 pages in src/pages -> dist/.
Run from the site folder:  python build.py
Links are relative so the site opens from a folder, a file share or any static host."""
import shutil, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).parent
SRC, DIST = HERE / "src", HERE / "dist"

PRODUCTS = [
    ("D", "Tarikh Desk", "For advocates and chambers. Every matter, date and draft in one place.", "desk.html"),
    ("R", "Tarikh Recover", "For lenders and businesses. Hundreds of bounced cheques, one portfolio.", "recover.html"),
    ("C", "Tarikh Check", "Free for anyone. Is your cheque case still in time?", "check.html"),
    ("A", "Tarikh API", "The deadline engine and paper reading, inside your own systems.", "api.html"),
]
NAV = [("platform", "Platform", "platform.html"), ("law", "The law", "law.html"), ("pricing", "Pricing", "pricing.html"), ("trust", "Trust", "trust.html"), ("company", "Company", "company.html")]
FOOT = {
    "Products": [("Tarikh Desk", "desk.html"), ("Tarikh Recover", "recover.html"), ("Tarikh Check", "check.html"), ("Tarikh API", "api.html"), ("Open the demo", "app/index.html")],
    "Platform": [("Read", "platform.html#read"), ("Count", "platform.html#count"), ("Draft", "platform.html#draft"), ("Diary", "platform.html#diary"), ("Settle", "platform.html#settle")],
    "Resources": [("The law, counted", "law.html"), ("The 2025 Supreme Court directions", "law.html#directions"), ("Compounding costs", "law.html#compounding"), ("Pricing", "pricing.html")],
    "Company": [("About", "company.html"), ("Trust and security", "trust.html"), ("Early access", "contact.html"), ("Privacy", "privacy.html"), ("Terms", "terms.html")],
}
GITHUB = "https://github.com/IIYUSHIN/TARIKH"


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(SRC / "assets", DIST / "assets")
    env = Environment(loader=FileSystemLoader(str(SRC)), undefined=StrictUndefined, autoescape=False, trim_blocks=True, lstrip_blocks=True)
    count = 0
    for page in sorted((SRC / "pages").rglob("*.html")):
        rel = page.relative_to(SRC / "pages")
        depth = len(rel.parts) - 1
        root = "../" * depth
        out = DIST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        tpl = env.get_template("pages/" + rel.as_posix())
        out.write_text(tpl.render(root=root, NAV=NAV, FOOT=FOOT, PRODUCTS=PRODUCTS, GITHUB=GITHUB, page=rel.as_posix()), encoding="utf-8")
        count += 1
    print(f"built {count} pages -> {DIST}")


if __name__ == "__main__":
    build()
