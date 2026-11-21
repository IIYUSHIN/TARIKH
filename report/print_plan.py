"""Which pages of the report need colour ink, measured from the rendered PDF, and two print-ready PDFs.

A page counts as colour when more than 20 of its pixels (at 50 dpi) are visibly coloured. Every diagram and the Azure
screens are pure grey, so text and grey pages measure exactly 0 and a page with even one red chip measures in the hundreds.
    python -m report.print_plan"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

BUILD = Path(__file__).resolve().parent / "build"
NAME = "Piyush_Kumar_Brahmbhatt_Industrial_Internship_Report"


def ranges(nums: list[int]) -> str:
    out, start, prev = [], None, None
    for n in nums + [None]:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = n
    return ", ".join(out)


def labels(pdf: Path) -> list[str]:
    """The number printed in each page's footer (roman in the front matter, none on the cover)."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout.split("\f")
    out = []
    for pg in txt[: -1 if not txt[-1].strip() else None]:
        last = [ln for ln in pg.splitlines() if ln.strip()]
        tail = last[-1].split()[-1] if last else ""
        out.append(tail if "Specialization" in (last[-1] if last else "") else "cover")
    return out


def main() -> int:
    pdf = BUILD / f"{NAME}.pdf"
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(["pdftoppm", "-r", "50", "-png", str(pdf), str(tmp / "p")], check=True)
    pages = sorted(tmp.glob("p-*.png"))
    colour = []
    for i, f in enumerate(pages, 1):
        a = np.asarray(Image.open(f).convert("RGB")).astype(int)
        n = int(((a.max(axis=2) - a.min(axis=2)) > 38).sum())
        if n > 20:
            colour.append(i)
    bw = [i for i in range(1, len(pages) + 1) if i not in colour]
    lab = labels(pdf)
    lines = [f"Report: {pdf.name}", f"Sheets in the PDF: {len(pages)}", "",
             f"COLOUR pages ({len(colour)}), PDF page numbers: {ranges(colour)}",
             f"BLACK AND WHITE pages ({len(bw)}), PDF page numbers: {ranges(bw)}", "",
             "Page by page (PDF page -> number printed in the footer -> ink):"]
    lines += [f"  {i:>2}  {lab[i - 1]:>6}  {'COLOUR' if i in colour else 'black and white'}" for i in range(1, len(pages) + 1)]
    (BUILD / "PRINT_PLAN.txt").write_text("\n".join(lines) + "\n")
    for kind, nums in (("COLOUR_pages", colour), ("BW_pages", bw)):
        subprocess.run(["qpdf", "--empty", "--pages", str(pdf), ",".join(map(str, nums)), "--", str(BUILD / f"{NAME}_{kind}.pdf")], check=True)
    print("\n".join(lines[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
