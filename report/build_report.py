"""Builds the industrial internship report (.docx and a PDF render) in the Chandigarh University format.

    python -m report.figures          # draw figures
    python -m report.screenshots      # capture screens
    python -m report.build_report     # build; add --final to refuse while any [PENDING ...] marker remains

Two things make the table of contents trustworthy: the document is rendered to PDF, the page of every heading is read back
from the PDF, and the contents page is rebuilt with those numbers until the numbers stop changing.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.deadlines import compute_windows, month_period_end  # noqa: E402
from report import content as C  # noqa: E402

BUILD = Path(__file__).resolve().parent / "build"
FONT, MONO = "Times New Roman", "Courier New"
TEXT_WIDTH_IN = 8.27 - 1.4 - 1.0
LABELS: dict[str, str] = {}          # "fig:arch" -> "3.1", filled on one pass and used on the next
OUT_NAME = "Piyush_Kumar_Brahmbhatt_Industrial_Internship_Report"


def fmt(d: date) -> str:
    return f"{d.day} {d:%b %Y}"


def fmt_long(d: date) -> str:
    return f"{d.day} {d:%B %Y}"


def roman(n: int) -> str:
    out = ""
    for v, s in [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]:
        while n >= v:
            out, n = out + s, n - v
    return out


# --------------------------------------------------------------------------- checks computed by the real engine
def deadline_cases() -> list[list[str]]:
    def one(d, m):
        return month_period_end(d, m)

    w = lambda delivered, today: {x.key: x for x in compute_windows(None, None, None, delivered, today=today)}  # noqa: E731
    rows = []
    assert one(date(2026, 1, 10), 3) == date(2026, 4, 9)
    rows.append(["Cheque validity of three months", "Cheque dated 10 Jan 2026", "Ends 9 Apr 2026"])
    assert one(date(2026, 1, 31), 1) == date(2026, 2, 28)
    rows.append(["One month into a shorter month", "Starts 31 Jan 2026", "Ends 28 Feb 2026"])
    assert one(date(2024, 1, 31), 1) == date(2024, 2, 29)
    rows.append(["One month in a leap year", "Starts 31 Jan 2024", "Ends 29 Feb 2024"])
    p = w(date(2017, 5, 5), date(2017, 5, 10))["payment"]
    assert (p.opens, p.closes) == (date(2017, 5, 6), date(2017, 5, 20))
    rows.append(["Drawer's 15 days", "Notice received 5 May 2017", "6 May to 20 May 2017"])
    x = w(date(2026, 3, 23), date(2026, 4, 10))
    assert (x["payment"].closes, x["complaint"].opens, x["complaint"].closes) == (date(2026, 4, 7), date(2026, 4, 8), date(2026, 5, 8))
    rows.append(["Complaint period after the 15 days", "Notice received 23 Mar 2026", "15 days end 7 Apr; complaint 8 Apr to 8 May 2026 (7 May if counted from the cause-of-action day)"])
    j = w(date(2020, 1, 8), date(2020, 2, 1))
    assert j["payment"].closes == date(2020, 1, 23) and (j["complaint"].opens, j["complaint"].closes) == (date(2020, 1, 24), date(2020, 2, 24))
    assert j["complaint"].opens <= date(2020, 2, 20) <= j["complaint"].closes
    rows.append(["Timeline in a High Court judgment {c:sk}", "Notice received 8 Jan 2020", "15 days end 23 Jan; complaint 24 Jan to 24 Feb; filing on 20 Feb is inside"])
    m = {x.key: x for x in compute_windows(None, None, date(2026, 10, 30), None, today=date(2026, 11, 21))}
    assert m["payment"].closes is None and m["complaint"].closes is None and m["payment"].status == "unknown"
    rows.append(["Delivery date missing, posting date known", "Notice posted 30 Oct 2026", "Payment and complaint periods: cannot be worked out; no date assumed"])
    return rows


def worked_cases() -> list[list[str]]:
    today = date(2026, 11, 21)
    ws = compute_windows(cheque_date=date(2026, 9, 20), memo_received_on=date(2026, 10, 5), notice_sent_on=date(2026, 10, 30),
                         notice_delivered_on=date(2026, 11, 3), today=today, presented_on=date(2026, 10, 1))
    words = {"met": "Met", "expired": "Ended", "open": "Open", "closing": "Closing", "upcoming": "Not started", "unknown": "Cannot be worked out"}
    rows = []
    for x in ws:
        st = words[x.status]
        if x.key == "payment" and x.status == "expired":
            st = "Ended"
        if x.days_left is not None:
            st += f", {x.days_left} days left"
        names = {"validity": "Cheque presented within validity", "notice": "Demand notice to the drawer",
                 "payment": "Drawer's time to pay", "complaint": "Complaint before the Magistrate"}
        rows.append([names[x.key], fmt(x.opens), fmt(x.closes), st])
    return rows


def working_days() -> list[date]:
    out, d = [], C.START
    while d < C.END:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


# --------------------------------------------------------------------------- low-level docx helpers
def set_fonts(run, size=None, bold=None, italic=None, name=FONT):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)


def style_font(style, size, bold=False, name=FONT):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = False
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for k in list(rf.attrib):
        if "Theme" in k:
            del rf.attrib[k]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)


def shade(cell, hex_fill):
    tcpr = cell._element.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hex_fill)
    tcpr.append(sh)


def add_field(paragraph, instr, size=10):
    run = paragraph.add_run()
    set_fonts(run, size)
    for typ in ("begin", None, "separate", "text", "end"):
        if typ is None:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "
            run._element.append(it)
        elif typ == "text":
            t = OxmlElement("w:t"); t.text = "1"; run._element.append(t)
        else:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), typ); run._element.append(fc)


def set_pgnum(section, fmt_, start=1):
    sect = section._sectPr
    pg = sect.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        cols = sect.find(qn("w:cols"))
        if cols is not None:
            cols.addprevious(pg)
        else:
            sect.append(pg)
    pg.set(qn("w:fmt"), fmt_); pg.set(qn("w:start"), str(start))


def bottom_border(paragraph, sz=4):
    ppr = paragraph._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    for k, v in (("val", "single"), ("sz", str(sz)), ("space", "4"), ("color", "000000")):
        top.set(qn(f"w:{k}"), v)
    b.append(top); ppr.append(b)


# --------------------------------------------------------------------------- the build
class Build:
    def __init__(self, outline: list[dict], pages: dict[str, str]):
        self.prev_outline, self.pages = outline, pages
        self.outline: list[dict] = []
        self.refs: list[str] = []
        self.pending: list[str] = []
        self.ch = 0
        self.sec = 0
        self.cur = ""
        self.counters: dict[str, int] = {}
        self.doc = Document()
        self._setup()

    # ---- setup
    def _setup(self):
        d = self.doc
        s = d.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin, s.right_margin = Inches(1.4), Inches(1.0)
        s.top_margin, s.bottom_margin = Inches(1.0), Inches(1.0)
        s.footer_distance = Inches(0.45)
        n = d.styles["Normal"]
        style_font(n, 12)
        n.paragraph_format.line_spacing = 1.5
        n.paragraph_format.space_after = Pt(6)
        n.paragraph_format.space_before = Pt(0)
        for name, size, align in (("Heading 1", 18, WD_ALIGN_PARAGRAPH.CENTER), ("Heading 2", 12, WD_ALIGN_PARAGRAPH.LEFT),
                                  ("Heading 3", 12, WD_ALIGN_PARAGRAPH.LEFT)):
            h = d.styles[name]
            style_font(h, size, bold=True)
            pf = h.paragraph_format
            pf.alignment = align
            pf.keep_with_next = True
            pf.space_before = Pt(0 if name == "Heading 1" else 12)
            pf.space_after = Pt(12 if name == "Heading 1" else 6)
            pf.line_spacing = 1.5 if name == "Heading 1" else 1.15
            pf.page_break_before = name == "Heading 1"
        style_font(d.styles["List Bullet"], 12)
        d.styles["List Bullet"].paragraph_format.line_spacing = 1.5
        d.styles["List Bullet"].paragraph_format.space_after = Pt(3)
        zoom = d.settings.element.find(qn("w:zoom"))
        if zoom is not None and zoom.get(qn("w:percent")) is None:
            zoom.set(qn("w:percent"), "100")
        d.core_properties.title = "Industrial Internship Report: Tarikh"
        d.core_properties.author = C.STUDENT
        s.different_first_page_header_footer = True
        set_pgnum(s, "lowerRoman", 1)
        self._footer(s)

    def _footer(self, section):
        f = section.footer
        f.is_linked_to_previous = False
        p = f.paragraphs[0]
        p.text = ""
        bottom_border(p)                      # first, so that python-docx places its own properties after it in schema order
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_WIDTH_IN), WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run(f"{C.STUDENT}  |  UID: {C.UID}  |  Specialization: AIML\t")
        set_fonts(r, 10)
        add_field(p, "PAGE", 10)

    # ---- references, labels, text
    def cite(self, key: str) -> int:
        if key not in self.refs:
            self.refs.append(key)
        return self.refs.index(key) + 1

    def resolve(self, t: str) -> str:
        t = re.sub(r"\{c:(\w+)\}", lambda m: f"[{self.cite(m.group(1))}]", t)
        t = re.sub(r"\{fig:(\w+)\}", lambda m: "Fig. " + LABELS.get("fig:" + m.group(1), "?.?"), t)
        t = re.sub(r"\{tab:(\w+)\}", lambda m: "Table " + LABELS.get("tab:" + m.group(1), "?.?"), t)
        return t

    def runs(self, p, text: str, size=12, bold=False, italic=False):
        text = self.resolve(text)
        if "[PENDING" in text:
            self.pending.append(re.search(r"\[PENDING[^\]]*\]", text).group(0))
        for part in re.split(r"(\*\*.+?\*\*|`.+?`|\*[^*]+?\*)", text):
            if not part:
                continue
            if part.startswith("**"):
                r = p.add_run(part[2:-2]); set_fonts(r, size, True, italic)
            elif part.startswith("`"):
                r = p.add_run(part[1:-1]); set_fonts(r, size - 1.5, bold, italic, MONO)
            elif part.startswith("*") and len(part) > 2:
                r = p.add_run(part[1:-1]); set_fonts(r, size, bold, True)
            else:
                r = p.add_run(part); set_fonts(r, size, bold, italic)

    def p(self, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, spacing=1.5, after=6, before=0, bold=False, italic=False, keep=False, style=None):
        para = self.doc.add_paragraph(style=style)
        pf = para.paragraph_format
        pf.alignment, pf.line_spacing, pf.space_after, pf.space_before, pf.keep_with_next = align, spacing, Pt(after), Pt(before), keep
        self.runs(para, text, size, bold, italic)
        return para

    def bullets(self, items):
        for t in items:
            para = self.doc.add_paragraph(style="List Bullet")
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            self.runs(para, t)

    # ---- headings
    def h1(self, title):
        self.ch += 1
        self.sec = 0
        self.cur = str(self.ch)
        para = self.doc.add_paragraph(style="Heading 1")
        for i, line in enumerate((f"CHAPTER - {self.ch}", title.upper())):
            r = para.add_run(line); set_fonts(r, 18, True)
            if i == 0:
                r.add_break(WD_BREAK.LINE)
        self.outline.append(dict(level=1, num=f"{self.ch}.", title=title, key=f"CHAPTER - {self.ch}", id=f"c{self.ch}"))

    def h2(self, title):
        self.sec += 1
        num = f"{self.ch}.{self.sec}"
        para = self.doc.add_paragraph(style="Heading 2")
        r = para.add_run(f"{num} {title}"); set_fonts(r, 12, True)
        self.outline.append(dict(level=2, num=num, title=title, key=f"{num} {title}", id=f"s{num}"))

    def h1a(self, letter, title):
        self.cur = letter
        self.counters = {k: v for k, v in self.counters.items() if not k.endswith("|" + letter)}
        para = self.doc.add_paragraph(style="Heading 1")
        r = para.add_run(f"APPENDIX - {letter}"); set_fonts(r, 18, True); r.add_break(WD_BREAK.LINE)
        r = para.add_run(title.upper()); set_fonts(r, 18, True)
        self.outline.append(dict(level=1, num=f"Appendix {letter}.", title=title, key=f"APPENDIX - {letter}", id=f"a{letter}"))

    def references(self):
        para = self.doc.add_paragraph(style="Heading 1")
        r = para.add_run("REFERENCES"); set_fonts(r, 18, True)
        self.outline.append(dict(level=1, num="", title="References", key="REFERENCES", id="refs"))
        for i, key in enumerate(self.refs, 1):
            q = self.doc.add_paragraph()
            q.paragraph_format.left_indent = Inches(0.4)
            q.paragraph_format.first_line_indent = Inches(-0.4)
            q.paragraph_format.line_spacing = 1.15
            q.paragraph_format.space_after = Pt(8)
            q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            self.runs(q, f"{i}.\t" + C.REFERENCES[key].replace("*", ""))

    # ---- figures and tables
    def number(self, kind, key):
        k = f"{kind}|{self.cur}"
        self.counters[k] = self.counters.get(k, 0) + 1
        label = f"{self.cur}.{self.counters[k]}"
        LABELS[f"{kind}:{key}"] = label
        return label

    def figure(self, key, fname, caption, width):
        label = self.number("fig", key)
        pic = self.doc.add_paragraph()
        pf = pic.paragraph_format
        pf.alignment, pf.line_spacing, pf.space_before, pf.space_after, pf.keep_with_next = WD_ALIGN_PARAGRAPH.CENTER, 1.0, Pt(6), Pt(4), True
        path = BUILD / fname
        if path.exists():
            pic.add_run().add_picture(str(path), width=Inches(width))
        else:
            self.runs(pic, f"[PENDING: figure {fname}]")
        cap = self.p("", align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0, after=12)
        r = cap.add_run(f"Fig. {label}  "); set_fonts(r, 12, True)
        self.runs(cap, caption)

    def table(self, key, caption, header, rows, widths):
        label = self.number("tab", key)
        cap = self.p("", align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0, after=4, before=6, keep=True)
        r = cap.add_run(f"Table {label}  "); set_fonts(r, 12, True)
        self.runs(cap, caption)
        self._grid(header, rows, widths, keep=len(rows) <= 8)     # a short table never leaves a row behind on the next page
        self.p("", spacing=1.0, after=6)

    def _grid(self, header, rows, widths, size=11, header_fill="D9D9D9", first_bold=False, keep=False):
        t = self.doc.add_table(rows=(1 if header else 0) + len(rows), cols=len(widths))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        tblpr = t._tbl.tblPr
        mar = OxmlElement("w:tblCellMar")
        for side, w in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
            e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), str(w)); e.set(qn("w:type"), "dxa"); mar.append(e)
        look = tblpr.find(qn("w:tblLook"))
        (look.addprevious(mar) if look is not None else tblpr.append(mar))   # t.autofit = False already wrote tblLayout=fixed
        for ci, w in enumerate(widths):
            t.columns[ci].width = Inches(w)
        allrows = ([header] if header else []) + rows
        for ri, row in enumerate(allrows):
            tr = t.rows[ri]
            trpr = tr._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit"); trpr.append(cs)
            if header and ri == 0:
                th = OxmlElement("w:tblHeader"); trpr.append(th)
            for ci, val in enumerate(row):
                cell = tr.cells[ci]
                cell.width = Inches(widths[ci])
                para = cell.paragraphs[0]
                pf = para.paragraph_format
                pf.line_spacing, pf.space_after, pf.space_before, pf.alignment = 1.0, Pt(0), Pt(0), WD_ALIGN_PARAGRAPH.LEFT
                pf.keep_with_next = keep and ri < len(allrows) - 1
                head = bool(header) and ri == 0
                self.runs(para, val, size, bold=head or (first_bold and ci == 0))
                if head:
                    shade(cell, header_fill)
        return t

    def code(self, text):
        for line in text.strip("\n").split("\n"):
            para = self.doc.add_paragraph()
            pf = para.paragraph_format
            pf.line_spacing, pf.space_after, pf.left_indent, pf.alignment = 1.0, Pt(1), Inches(0.2), WD_ALIGN_PARAGRAPH.LEFT
            r = para.add_run(line or " "); set_fonts(r, 9.5, name=MONO)
        self.p("", spacing=1.0, after=4)

    # ---- weekly report
    def weeks(self):
        days = working_days()
        blocks = [days[i:i + 5] for i in range(0, len(days), 5)]
        entries = list(C.WEEKS)
        assert len(blocks) == len(entries) + 1, (len(blocks), len(entries))
        for i, block in enumerate(blocks, 1):
            span = f"{fmt(block[0])} to {fmt(block[-1])}" if len(block) > 1 else fmt(block[0])
            self.p(f"WEEK {i}     DATES ({span})", align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=2, before=10, bold=True, keep=True)
            if i <= len(entries):
                topic, tasks, learned = entries[i - 1]
            else:
                topic, tasks, learned = "Final checks and submission", [C.CLOSING_DAY[0]], "The report, the code and the viva notes have to agree with each other."
            self.p(f"TOPIC COVERED: {topic}", align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=3, keep=True)
            assert len(tasks) == len(block), (i, len(tasks), len(block))
            rows = [[f"DAY-{n}", f"{d:%a} {d.day} {d:%b}", txt] for n, (d, txt) in enumerate(zip(block, tasks), 1)]
            self._grid(None, rows, [0.6, 0.9, 4.35], size=11, first_bold=True, keep=True)
            self.p(f"*What I learned:* {learned}", align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=4, before=3, size=11)

    # ---- front matter
    def cover(self):
        def line(text, size, bold=False, italic=False, before=0, after=6):
            self.p(text, align=WD_ALIGN_PARAGRAPH.CENTER, size=size, bold=bold, italic=italic, before=before, after=after, spacing=1.5)
        line("INDUSTRIAL INTERNSHIP REPORT", 16, True, after=14)
        line(C.TITLE, 18, True, after=22)
        line("Submitted in Partial Fulfillment of the Requirements for the Degree of", 14, after=6)
        line(C.DEGREE, 14, True, after=2)
        line("in", 14, after=2)
        line(f"{C.PROGRAMME.upper()} - ({C.SPECIALIZATION.upper()})", 14, True, after=14)
        line("by", 14, italic=True, after=6)
        line(C.STUDENT, 16, True, after=0)
        line(f"(UID: {C.UID})", 16, after=2)
        line(f"Class: {C.CLASS}", 14, after=18)
        logo = ROOT / "assets" / "cu_logo.png"
        pic = self.doc.add_paragraph()
        pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if logo.exists():
            pic.add_run().add_picture(str(logo), height=Inches(1.15))
        else:
            self.runs(pic, "[PENDING: university logo, save it as assets/cu_logo.png]")
        for t in ("AIT - Computer Science and Engineering", "University Institute of Engineering", "Chandigarh University, Gharuan", C.SUBMISSION):
            self.p(t, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, after=0, spacing=1.3)

    def pagebreak(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def bonafide(self):
        self.p("BONAFIDE CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, size=16, bold=True, after=18, spacing=1.5).paragraph_format.page_break_before = True
        self.p(f"This is to certify that the industrial internship report entitled \"{C.TITLE}\" submitted by \"{C.STUDENT.upper()}, UID: {C.UID}, "
               f"Class: {C.CLASS}\" in partial fulfillment of the requirements for the award of the Degree {C.DEGREE} in \"{C.PROGRAMME} "
               f"({C.SPECIALIZATION})\" is a bonafide record of the work carried out from \"{fmt_long(C.START)}\" to \"{fmt_long(C.END)}\" "
               f"under my guidance and supervision at Chandigarh University, Gharuan.", size=14, spacing=2.0, after=24)
        for t in ("SIGNATURE", f"{C.LEADER}", f"{C.LEADER_TITLE}, {C.SPECIALIZATION}",
                  "Department of Computer Science and Engineering"):
            self.p(t, align=WD_ALIGN_PARAGRAPH.LEFT, size=14, spacing=1.2, after=2, bold=(t == "SIGNATURE"))
        self.p("This project report was evaluated by us on ____________________ (date).", align=WD_ALIGN_PARAGRAPH.LEFT, size=14, spacing=1.5, before=36, after=24)
        self.p("EXTERNAL EXAMINER", align=WD_ALIGN_PARAGRAPH.LEFT, size=14, bold=True, spacing=1.2, after=2)
        self.p("Faculty Name and EID: ______________________________", align=WD_ALIGN_PARAGRAPH.LEFT, size=14, spacing=1.2, after=2)

    def declaration(self):
        self.p("DECLARATION BY CANDIDATE", align=WD_ALIGN_PARAGRAPH.CENTER, size=16, bold=True, after=18).paragraph_format.page_break_before = True
        self.p("This is to declare that this report has been written by me. No part of the report is plagiarized from other sources. "
               "All information included from other sources have been duly acknowledged. I aver that if any part of the report is found to be "
               "plagiarized, I shall take full responsibility for it.", size=14, spacing=2.0, after=36)
        for t in ("Signature of Candidate: ______________________", f"Name of Candidate: {C.STUDENT}", f"UID: {C.UID}", "",
                  "Place: ____________________", "Date: _____________________"):
            self.p(t, align=WD_ALIGN_PARAGRAPH.LEFT, size=14, spacing=1.5, after=2)

    def abstract(self):
        self.p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, after=12).paragraph_format.page_break_before = True
        for t in C.abstract():
            self.p(t, spacing=1.0, after=8)
        self.p(f"**Keywords:** {C.KEYWORDS}", spacing=1.0, after=0, align=WD_ALIGN_PARAGRAPH.LEFT)

    def toc(self):
        self.p("TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, after=10).paragraph_format.page_break_before = True
        head = self.p("CHAPTER NO.\tTITLE\tPAGE NO.", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, bold=True, spacing=1.0, after=6)
        head.paragraph_format.tab_stops.add_tab_stop(Inches(1.15), WD_TAB_ALIGNMENT.LEFT)
        head.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_WIDTH_IN), WD_TAB_ALIGNMENT.RIGHT)
        rows = [dict(level=0, num="", title="Abstract", id="abs"), dict(level=0, num="", title="Table of Contents", id="toc"),
                dict(level=0, num="", title="List of Abbreviations", id="abbr")] + self.prev_outline
        for e in rows:
            pg = self.pages.get(e["id"], "00")
            para = self.doc.add_paragraph()
            pf = para.paragraph_format
            pf.alignment, pf.line_spacing, pf.space_after = WD_ALIGN_PARAGRAPH.LEFT, 1.0, Pt(0 if e["level"] == 2 else 2)
            if e["level"] == 2:
                pf.left_indent = Inches(1.15)
                pf.tab_stops.add_tab_stop(Inches(1.7), WD_TAB_ALIGNMENT.LEFT)
            else:
                pf.tab_stops.add_tab_stop(Inches(1.15), WD_TAB_ALIGNMENT.LEFT)
            pf.tab_stops.add_tab_stop(Inches(TEXT_WIDTH_IN), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            num = e["num"]
            if e["level"] == 1:
                text = f"{num}\t{e['title']}\t{pg}" if num else f"\t{e['title']}\t{pg}"
            elif e["level"] == 2:
                text = f"{num}\t{e['title']}\t{pg}"
            else:
                text = f"\t{e['title']}\t{pg}"
            self.runs(para, text, 11, bold=e["level"] == 1)

    def abbreviations(self):
        self.p("LIST OF ABBREVIATIONS", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, after=12).paragraph_format.page_break_before = True
        for a, b in C.ABBREVIATIONS:
            para = self.p(f"**{a}**\t{b}", align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.3, after=2)
            para.paragraph_format.tab_stops.add_tab_stop(Inches(1.3), WD_TAB_ALIGNMENT.LEFT)

    # ---- assemble
    def render(self):
        self.cover()
        self.bonafide()
        self.declaration()
        self.abstract()
        self.toc()
        self.abbreviations()
        sec2 = self.doc.add_section(WD_SECTION.NEW_PAGE)
        sec2.different_first_page_header_footer = False
        set_pgnum(sec2, "decimal", 1)
        self._footer(sec2)
        for item in C.chapters(deadline_cases(), worked_cases()) + C.appendices():
            kind = item[0]
            if kind == "h1":
                self.h1(item[1])
            elif kind == "h2":
                self.h2(item[1])
            elif kind == "p":
                self.p(item[1])
            elif kind == "bul":
                self.bullets(item[1])
            elif kind == "table":
                self.table(item[1], item[2], item[3], item[4], item[5])
            elif kind == "fig":
                self.figure(item[1], item[2], item[3], item[4])
            elif kind == "weeks":
                self.weeks()
            elif kind == "h1a":
                self.h1a(item[1], item[2])
            elif kind == "certificate":
                if item[1]:
                    para = self.doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    para.add_run().add_picture(item[1], width=Inches(5.2))
                # without an image the page stays clear, for the printed certificate to be placed on it
            elif kind == "code":
                self.code(item[1])
        self.references()      # the university lists appendices first and references last

    def save(self, path: Path):
        self.doc.save(path)


# --------------------------------------------------------------------------- render, read back page numbers
def to_pdf(docx: Path) -> Path:
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
    return docx.with_suffix(".pdf")


def pdf_pages(pdf: Path) -> list[list[str]]:
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    pages = txt.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [[re.sub(r"\s+", " ", ln).strip() for ln in pg.splitlines()] for pg in pages]


def locate(outline: list[dict], pages: list[list[str]]) -> tuple[dict[str, str], int, int]:
    main = next(i for i, ls in enumerate(pages) if "CHAPTER - 1" in ls)
    out: dict[str, str] = {}
    for key, line in (("abs", "ABSTRACT"), ("toc", "TABLE OF CONTENTS"), ("abbr", "LIST OF ABBREVIATIONS")):
        i = next(i for i in range(main) if line in pages[i])
        out[key] = roman(i + 1)
    cur = main
    end_page = None
    for e in outline:
        i = cur
        while i < len(pages):
            hit = any((l == e["key"]) if e["level"] == 1 else l.startswith(e["key"][:30]) for l in pages[i])
            if hit:
                break
            i += 1
        if i >= len(pages):
            raise RuntimeError(f"heading not found in PDF: {e['key']}")
        cur = i
        out[e["id"]] = str(i - main + 1)
        if end_page is None and e["id"][0] in "ar" and e["id"] != "abs":
            end_page = i
    return out, main, end_page


def main() -> int:
    final = "--final" in sys.argv
    BUILD.mkdir(exist_ok=True)
    for f in (Path(__file__).resolve().parent / "azure").glob("*.png"):     # greyscale crops of the Azure portal screens
        shutil.copy(f, BUILD / f.name)
    docx = BUILD / f"{OUT_NAME}.docx"
    outline: list[dict] = []
    pages: dict[str, str] = {}
    info = None
    for attempt in range(7):
        b = Build(outline, pages)
        b.render()
        b.save(docx)
        pdf = to_pdf(docx)
        pp = pdf_pages(pdf)
        new, main_i, refs_i = locate(b.outline, pp)
        if new == pages and b.outline == outline:
            info = (b, len(pp), main_i, refs_i)
            break
        outline, pages = b.outline, new
    if info is None:
        print("page numbers did not settle"); return 2
    b, total, main_i, refs_i = info
    body = refs_i - main_i
    print(f"pages: {total} in all, front matter {main_i}, main chapters {body}, references and appendices {total - refs_i}")
    pend = sorted(set(b.pending))
    for m in pend:
        print("PENDING:", m)
    ok = True
    if not 20 <= body <= 30:
        print(f"FAIL: main content is {body} pages, the university asks for 20 to 30"); ok = False
    if final and pend:
        print("FAIL: --final refuses to build while PENDING markers remain"); ok = False
    unresolved = any("?.?" in l for pg in pp for l in pg)
    if unresolved:
        print("FAIL: unresolved figure or table reference"); ok = False
    subprocess.run(["zip", "-d", str(docx), "*/"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
