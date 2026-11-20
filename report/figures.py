"""Figures for the report, drawn from the project itself. Black on white with one accent, so they print in grayscale."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "build"
for f in (ROOT / "tools" / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
SERIF, MONO = "Gelasio", "IBM Plex Mono"
INK, GREY, LIGHT, RED = "#17140F", "#5E5748", "#EAE3D3", "#A3221B"
plt.rcParams.update({"font.family": SERIF, "text.color": INK, "axes.edgecolor": INK})


def box(ax, x, y, w, h, title, sub="", fill="white", ls="-", lw=1.2, tfs=9.5, sfs=7.8, bold=True, subfont=MONO):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.04", fc=fill, ec=INK, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2 + (0.13 if sub else 0), title, ha="center", va="center", fontsize=tfs, fontweight="bold" if bold else "normal")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.17, sub, ha="center", va="center", fontsize=sfs, color=GREY, family=subfont)


def arrow(ax, x1, y1, x2, y2, label="", ls="-", rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1, ls=ls, shrinkA=0, shrinkB=0, connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, label, ha="center", fontsize=7.5, color=GREY, style="italic",
                bbox=dict(fc="white", ec="none", pad=0.6))


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def architecture():
    fig, ax = canvas(6.3, 4.6)
    ax.text(0.1, 4.42, "Laptop (everything the advocate touches)", fontsize=8, color=GREY, style="italic")
    box(ax, 0.1, 3.45, 1.7, 0.75, "Browser", "static HTML+JS", fill=LIGHT)
    box(ax, 2.15, 3.45, 2.0, 0.75, "FastAPI", "app/main.py", fill=LIGHT)
    box(ax, 4.5, 3.45, 1.7, 0.75, "Pipeline", "app/pipeline.py", fill=LIGHT)
    arrow(ax, 1.8, 3.82, 2.15, 3.82); arrow(ax, 4.15, 3.82, 4.5, 3.82)
    box(ax, 0.1, 2.2, 1.7, 0.75, "SQLite store", "facts, audit", sfs=7.2)
    box(ax, 2.15, 2.2, 2.0, 0.75, "Deadline engine", "plain code, tested", lw=2.0, sfs=7.2)
    box(ax, 4.5, 2.2, 1.7, 0.75, "Recorder", "live / replay", ls="--", sfs=7.2)
    arrow(ax, 5.35, 3.45, 5.35, 2.95)
    for tx in (3.15, 0.95):   # elbow connectors so no line crosses a box
        ax.plot([4.75, 4.75, tx, tx][:3], [3.45, 3.2, 3.2], color=INK, lw=1.1)
        arrow(ax, tx, 3.2, tx, 2.95)
    ax.plot([4.75, 4.75], [3.45, 3.2], color=INK, lw=1.1)
    ax.add_patch(Rectangle((0.1, 0.05), 6.1, 1.62, fc="none", ec=INK, lw=1.0, ls=(0, (4, 3))))
    ax.text(0.2, 1.5, "Azure (Entra ID sign-in, no keys in files)", fontsize=8, color=GREY, style="italic")
    names = [("Content\nUnderstanding", "cheque, memo,\nnotice"), ("AI Language", "mask PII"), ("Speech", "voice in,\nvoice out"), ("Foundry\nmodel", "brief, image"), ("Foundry\nagent", "2 read-only\ntools")]
    for i, (t, s) in enumerate(names):
        box(ax, 0.2 + i * 1.19, 0.15, 1.1, 1.15, t, s, tfs=7.6, sfs=6.4)
    arrow(ax, 5.35, 2.2, 5.35, 1.67, "calls")
    fig.savefig(OUT / "fig_architecture.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)


def workflow():
    fig, ax = canvas(6.3, 2.3)
    steps = [("1  Add", "cheque, memo,\nnotice"), ("2  Read", "fields and\nwhere found"), ("3  Check", "advocate edits\nand ticks"),
             ("4  Count", "four statutory\nwindows"), ("5  Draft", "each line cites\na fact"), ("6  Approve", "advocate signs\nand is logged")]
    w, gap = 0.88, 0.16
    for i, (t, s_) in enumerate(steps):
        x = 0.02 + i * (w + gap)
        box(ax, x, 1.0, w, 1.15, t, s_, tfs=8.2, sfs=7, fill=LIGHT if i in (2, 5) else "white", lw=2.0 if i == 3 else 1.2, subfont=SERIF)
        if i < len(steps) - 1:
            arrow(ax, x + w, 1.57, x + w + gap, 1.57)
    ax.text(0.02, 0.62, "Shaded steps are human decisions. The heavy border marks the step that is plain code, not a model.", fontsize=7.4, color=GREY, style="italic")
    ax.text(0.02, 0.25, "Voice note (optional): transcribe, mask personal details, then only the masked text may reach the model.", fontsize=7.4, color=GREY, style="italic")
    fig.savefig(OUT / "fig_workflow.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)


def windows():
    from app.deadlines import compute_windows
    today = date(2026, 11, 21)
    ws = compute_windows(cheque_date=date(2026, 9, 20), memo_received_on=date(2026, 10, 5), notice_sent_on=date(2026, 10, 30),
                         notice_delivered_on=date(2026, 11, 3), today=today, presented_on=date(2026, 10, 1))
    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    d0 = date(2026, 9, 10).toordinal()
    ax.set_xticks([])
    for i, w in enumerate(ws):
        y = len(ws) - 1 - i
        s, e = w.opens.toordinal(), w.closes.toordinal()
        hatch = {"met": "", "open": "", "expired": "////"}.get(w.status, "")
        color = {"met": "#C9C1AE", "open": RED, "expired": "white"}.get(w.status, "white")
        if w.key == "payment":
            color, hatch = GREY, ""
        ax.barh(y, e - s + 1, left=s - d0, height=0.42, zorder=2, color=color, edgecolor=INK, hatch=hatch, lw=1.0)
        ax.text(-47, y + 0.0, w.label.replace("Cheque presented within validity","Cheque presented in time"), ha="left", va="center", fontsize=8)
        ax.text(e - d0 + 2.0, y, f"to {w.closes.day} {w.closes.strftime('%b')}", va="center", fontsize=7.2, family=MONO, color=GREY,
                zorder=6, bbox=dict(fc="white", ec="none", pad=0.8))
    t = today.toordinal() - d0
    ax.axvline(t, color=INK, lw=1.4); ax.text(t, len(ws) - 0.35, "21 Nov 2026", ha="center", fontsize=7.5, family=MONO, bbox=dict(fc="white", ec=INK, pad=1.5))
    ticks = [date(2026, m, 1) for m in (10, 11, 12)]
    ax.set_xticks([x.toordinal() - d0 for x in ticks]); ax.set_xticklabels([x.strftime("%b %Y") for x in ticks], fontsize=7.5, family=MONO)
    ax.set_yticks([]); ax.set_xlim(-48, 112); ax.set_ylim(-0.6, len(ws) - 0.1)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    fig.savefig(OUT / "fig_windows.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)


def datamodel():
    fig, ax = canvas(6.3, 3.7)
    ax.add_patch(FancyBboxPatch((0.05, 0.15), 1.15, 3.3, boxstyle="round,pad=0,rounding_size=0.04", fc=LIGHT, ec=INK, lw=1.2))
    ax.text(0.625, 1.95, "Matter", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.text(0.625, 1.6, "one cheque\ncase", ha="center", va="center", fontsize=7, color=GREY, family=MONO)
    rows = [(2.85, "Document", "1 to 3 papers"), (1.95, "Brief", "drafted by model"), (1.05, "Transcript", "original + masked"), (0.15, "Audit entry", "who, what, when")]
    for y, t, sub in rows:
        box(ax, 1.75, y, 1.8, 0.6, t, sub, tfs=9, sfs=6.8)
        arrow(ax, 1.2, y + 0.3, 1.75, y + 0.3)
    box(ax, 4.15, 2.85, 1.95, 0.6, "Fact", "value, page, box", fill=LIGHT, tfs=9, sfs=6.8)
    box(ax, 4.15, 1.95, 1.95, 0.6, "Claim", "text + fact ids", tfs=9, sfs=6.8)
    arrow(ax, 3.55, 3.15, 4.15, 3.15, "reads")
    arrow(ax, 3.55, 2.25, 4.15, 2.25)
    arrow(ax, 5.12, 2.55, 5.12, 2.85)
    ax.text(5.25, 2.7, "cites", fontsize=7.5, color=GREY, style="italic", va="center")
    fig.savefig(OUT / "fig_datamodel.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    architecture(); workflow(); windows(); datamodel()
    print("figures ok")
