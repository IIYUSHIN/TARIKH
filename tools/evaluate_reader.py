"""Field-by-field accuracy of the paper reader on the held-out validation papers (data/finetune/validation.jsonl).

Each validation example carries the paper image and the answer a person wrote for it. This tool sends the image to the
deployed reader exactly as the desk does (ModelExtractor), compares every field with the written answer, and prints a table.
It needs the same .env and `az login` as the server. Nothing is stored; the papers are fictional.

    python -m tools.evaluate_reader                 # all validation papers
    python -m tools.evaluate_reader --json out.json # also save the table
"""
from __future__ import annotations

import base64
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def norm(v) -> str:
    if v is None:
        return ""
    return re.sub(r"[\s,.\-/]+", "", str(v)).upper()


def examples(path: Path):
    for line in path.read_text().splitlines():
        msgs = json.loads(line)["messages"]
        user = msgs[1]["content"]
        doc_type = user[0]["text"].split(":", 1)[1].strip()
        url = user[1]["image_url"]["url"]
        mime, b64 = url[5:].split(";base64,", 1)
        yield doc_type, base64.b64decode(b64), mime, json.loads(msgs[2]["content"])["fields"]


def main() -> int:
    from app.config import Settings
    from app.models import DocType
    from app.services.extraction import ModelExtractor

    reader = ModelExtractor(Settings.from_env())
    right, total, wrong = defaultdict(int), defaultdict(int), []
    for i, (doc_type, content, mime, truth) in enumerate(examples(ROOT / "data" / "finetune" / "validation.jsonl"), 1):
        got = {f.key: f.value for f in reader.extract(DocType(doc_type), content, mime)}
        for key, want in truth.items():
            total[key] += 1
            if norm(got.get(key)) == norm(want):
                right[key] += 1
            else:
                wrong.append((i, doc_type, key, want, got.get(key)))
    print(f"{'Field':<18}{'Correct':>8}{'Of':>5}")
    for key in total:
        print(f"{key:<18}{right[key]:>8}{total[key]:>5}")
    all_r, all_t = sum(right.values()), sum(total.values())
    print(f"{'All fields':<18}{all_r:>8}{all_t:>5}   ({100 * all_r / all_t:.1f}%)")
    for w in wrong:
        print("  paper %d (%s) %s: expected %r, read %r" % w)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(
            {"right": right, "total": total, "wrong": wrong}, indent=2, default=list))
    return 0


if __name__ == "__main__":
    sys.exit(main())
