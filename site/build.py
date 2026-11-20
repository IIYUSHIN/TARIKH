"""Build the Tarikh site: Jinja2 pages in src/pages -> dist/.
Run from the site folder:  python build.py
Links are relative so the site opens from a folder, a file share or any static host."""
import shutil, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).parent
SRC, DIST = HERE / "src", HERE / "dist"

NAV = [
    ("desk", "The desk", "desk.html"),
    ("clocks", "The clocks", "clocks.html"),
    ("trust", "Trust", "trust.html"),
    ("security", "Security", "security.html"),
    ("docs", "How it is built", "docs.html"),
    ("about", "About", "about.html"),
]
FOOT = {
    "Product": [("The desk", "desk.html"), ("How the clocks are counted", "clocks.html"), ("Open the sample matter", "app/docket.html")],
    "Responsible use": [("Trust", "trust.html"), ("Security and privacy", "security.html"), ("How it is built", "docs.html")],
    "Company": [("About", "about.html"), ("Contact", "contact.html"), ("Privacy", "privacy.html"), ("Terms", "terms.html")],
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
        out.write_text(tpl.render(root=root, NAV=NAV, FOOT=FOOT, GITHUB=GITHUB, page=rel.as_posix()), encoding="utf-8")
        count += 1
    print(f"built {count} pages -> {DIST}")


if __name__ == "__main__":
    build()
