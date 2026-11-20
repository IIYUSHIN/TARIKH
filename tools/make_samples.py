"""Generate fictional cheque, bank return memo and demand notice for demos and tests.

Everything here is invented: parties, bank, advocate, numbers. Each image carries a visible
"FICTIONAL SAMPLE" band and a PNG/JPEG metadata marker so it can never pass as a real record.
Dates are chosen so that around 21 Nov 2026 the complaint window is open.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, PngImagePlugin

from app.models import DocType

FONTS = Path(__file__).parent / "fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


@dataclass(frozen=True)
class Scenario:
    drawer: str = "Kalra Fabricators"
    payee: str = "Sharma Steel Traders"
    bank: str = "Northern Sample Bank"
    branch: str = "Sector 22 Branch, Chandigarh"
    cheque_no: str = "004718"
    cheque_date: date = date(2026, 9, 20)
    presented_on: date = date(2026, 10, 1)
    memo_date: date = date(2026, 10, 3)
    notice_date: date = date(2026, 10, 30)
    amount: int = 485000
    amount_words: str = "Four Lakh Eighty-Five Thousand only"
    reason: str = "FUNDS INSUFFICIENT"
    reason_code: str = "51"
    advocate: str = "R. K. Sandhu"
    speed_post: str = "EE000000000IN"


def dmy(d: date) -> str:
    return d.strftime("%d-%m-%Y")


def inr(n: int) -> str:
    s = str(n)
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def band(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    f = font("IBMPlexMono_500Medium.ttf", max(16, img.width // 80))
    text = "FICTIONAL SAMPLE  -  NOT A REAL INSTRUMENT  -  FOR DEMONSTRATION ONLY"
    d.rectangle([0, img.height - 46, img.width, img.height], fill=(33, 33, 33))
    d.text((img.width / 2, img.height - 23), text, font=f, fill=(240, 236, 226), anchor="mm")


def signature(d: ImageDraw.ImageDraw, xy: tuple[int, int], name: str, size: int = 70) -> None:
    d.text(xy, name, font=font("Caveat_700Bold.ttf", size), fill=(20, 38, 110))
    x, y = xy
    d.line([(x - 10, y + size - 6), (x + size * 2.6, y + size - 22)], fill=(20, 38, 110), width=3)


def make_cheque(s: Scenario) -> Image.Image:
    W, H = 1800, 800
    img = Image.new("RGB", (W, H), (226, 236, 228))
    d = ImageDraw.Draw(img)
    for i in range(0, H, 14):  # security-pattern lines
        pts = [(x, i + 6 * math.sin(x / 55 + i / 40)) for x in range(0, W, 12)]
        d.line(pts, fill=(208, 223, 213), width=2)
    d.rectangle([14, 14, W - 14, H - 14], outline=(70, 100, 85), width=3)
    ink = (28, 40, 36)
    d.text((50, 40), s.bank.upper(), font=font("Gelasio.ttf", 50), fill=(22, 70, 58))
    d.text((52, 104), s.branch, font=font("Gelasio.ttf", 28), fill=ink)
    # date boxes
    d.text((1150, 44), "DATE", font=font("IBMPlexMono_500Medium.ttf", 24), fill=ink)
    digits = s.cheque_date.strftime("%d%m%Y")
    for i, ch in enumerate(digits):
        x = 1230 + i * 62 + (14 if i >= 2 else 0) + (14 if i >= 4 else 0)
        d.rectangle([x, 34, x + 52, 96], outline=ink, width=2)
        d.text((x + 12, 30), ch, font=font("Caveat_700Bold.ttf", 58), fill=(20, 38, 110))
    # A/c payee crossing
    d.line([(60, 190), (210, 148)], fill=ink, width=3)
    d.line([(80, 214), (230, 172)], fill=ink, width=3)
    d.text((72, 176), "A/c Payee", font=font("Gelasio.ttf", 22), fill=ink)
    lab = font("Gelasio.ttf", 30)
    hand = font("Caveat_700Bold.ttf", 64)
    d.text((60, 270), "Pay", font=lab, fill=ink)
    d.text((170, 244), s.payee, font=hand, fill=(20, 38, 110))
    d.line([(160, 322), (1500, 322)], fill=ink, width=2)
    d.text((1530, 286), "or Bearer", font=lab, fill=ink)
    d.text((60, 370), "Rupees", font=lab, fill=ink)
    d.text((220, 346), s.amount_words, font=hand, fill=(20, 38, 110))
    d.line([(210, 424), (1330, 424)], fill=ink, width=2)
    d.rectangle([1360, 350, 1750, 440], outline=ink, width=3)
    d.text((1378, 368), f"₹ {inr(s.amount)}/-", font=font("Caveat_700Bold.ttf", 62), fill=(20, 38, 110))
    d.text((1060, 520), f"For {s.drawer.upper()}", font=font("Gelasio.ttf", 32), fill=ink)
    signature(d, (1120, 560), "K. Kalra")
    d.text((1160, 680), "Authorised Signatory", font=font("Gelasio.ttf", 24), fill=ink)
    d.text((60, 520), f"Cheque No. {s.cheque_no}", font=font("IBMPlexMono_500Medium.ttf", 30), fill=ink)
    d.text((60, 575), "A/c No. 0012345678  IFSC NSBL0000221", font=font("IBMPlexMono_400Regular.ttf", 26), fill=ink)
    d.text((60, 705), f"C{s.cheque_no}C  160002012A  0012345678C  31", font=font("IBMPlexMono_500Medium.ttf", 40), fill=(50, 50, 50))
    return img


def make_memo(s: Scenario) -> Image.Image:
    W, H = 1240, 1754
    img = Image.new("RGB", (W, H), (250, 248, 242))
    d = ImageDraw.Draw(img)
    ink = (30, 30, 30)
    d.text((90, 90), s.bank.upper(), font=font("Gelasio.ttf", 56), fill=(22, 70, 58))
    d.text((90, 160), s.branch, font=font("Gelasio.ttf", 30), fill=ink)
    d.line([(90, 215), (W - 90, 215)], fill=(22, 70, 58), width=4)
    d.text((90, 260), "CHEQUE RETURN MEMO", font=font("Gelasio.ttf", 46), fill=ink)
    mono = font("CourierPrime_400Regular.ttf", 32)
    d.text((90, 340), f"Memo No.  CRM/{s.memo_date.year}/10382", font=mono, fill=ink)
    d.text((W - 460, 340), f"Date  {dmy(s.memo_date)}", font=mono, fill=ink)
    rows = [
        ("Cheque No.", s.cheque_no),
        ("Cheque Date", dmy(s.cheque_date)),
        ("Amount", f"Rs. {inr(s.amount)}/-"),
        ("Drawer / A/c Holder", s.drawer),
        ("Drawer A/c No.", "0012345678"),
        ("Payee / Presented by", s.payee),
        ("Presented On", dmy(s.presented_on)),
        ("Returned On", dmy(s.memo_date)),
        ("Return Reason", f"{s.reason_code} - {s.reason}"),
    ]
    y = 440
    for k, v in rows:
        d.line([(90, y + 70), (W - 90, y + 70)], fill=(205, 200, 190), width=2)
        d.text((90, y + 14), k, font=font("Gelasio.ttf", 30), fill=(90, 90, 90))
        d.text((520, y + 12), v, font=mono, fill=ink)
        y += 84
    d.text((90, y + 40), "The above cheque is returned unpaid for the reason stated. Please\n"
                         "contact your branch for further information.",
           font=font("Gelasio.ttf", 30), fill=ink, spacing=10)
    stamp = Image.new("RGBA", (520, 150), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([4, 4, 515, 145], outline=(176, 30, 40, 235), width=7)
    sd.text((34, 40), "RETURNED UNPAID", font=font("IBMPlexMono_500Medium.ttf", 48), fill=(176, 30, 40, 235))
    stamp = stamp.rotate(8, expand=True, resample=Image.BICUBIC)
    img.paste(stamp, (80, H - 430), stamp)
    signature(d, (W - 480, H - 360), "S. Verma", 64)
    d.text((W - 520, H - 270), "Authorised Signatory", font=font("Gelasio.ttf", 26), fill=ink)
    return img


def make_notice(s: Scenario) -> Image.Image:
    W, H = 1240, 1754
    img = Image.new("RGB", (W, H), (252, 251, 247))
    d = ImageDraw.Draw(img)
    ink = (28, 28, 28)
    serif, serif_b = font("Gelasio.ttf", 31), font("CrimsonText-SemiBold.ttf", 40)
    d.text((W / 2, 90), f"{s.advocate.upper()}, ADVOCATE", font=font("Gelasio.ttf", 44), fill=ink, anchor="mm")
    d.text((W / 2, 140), "Chamber No. 14, District Courts, Chandigarh  (fictional)", font=font("Gelasio.ttf", 26), fill=(90, 90, 90), anchor="mm")
    d.line([(90, 175), (W - 90, 175)], fill=ink, width=3)
    d.text((W / 2, 235), "LEGAL NOTICE UNDER SECTION 138 OF THE", font=serif_b, fill=ink, anchor="mm")
    d.text((W / 2, 280), "NEGOTIABLE INSTRUMENTS ACT, 1881", font=serif_b, fill=ink, anchor="mm")
    d.text((90, 345), f"Date: {dmy(s.notice_date)}", font=serif, fill=ink)
    d.text((W - 90, 345), f"By Speed Post No. {s.speed_post}", font=serif, fill=ink, anchor="ra")
    d.text((90, 410), f"To,\n{s.drawer},\nPlot 41, Industrial Area, Phase II,\nChandigarh - 160002", font=serif, fill=ink, spacing=8)
    body = [
        f"Under instructions from my client, {s.payee}, I give you this notice.",
        f"1. You issued cheque No. {s.cheque_no} dated {dmy(s.cheque_date)} for Rs. {inr(s.amount)}/- "
        f"drawn on {s.bank}, {s.branch}, in discharge of a legally enforceable liability to my client.",
        f"2. My client presented the cheque on {dmy(s.presented_on)}. It was returned unpaid on {dmy(s.memo_date)} "
        f"with the remark \"{s.reason.title()}\", as shown in the bank's return memo.",
        f"3. You are hereby called upon to pay Rs. {inr(s.amount)}/- within fifteen days of receipt of this notice, "
        "failing which my client will initiate proceedings against you under Section 138 of the "
        "Negotiable Instruments Act, 1881, at your risk as to costs and consequences.",
    ]
    y = 590
    for para in body:
        for line in wrap(d, para, serif, W - 180):
            d.text((90, y), line, font=serif, fill=ink)
            y += 46
        y += 22
    signature(d, (W - 470, y + 40), s.advocate.split()[-1], 70)
    d.text((W - 480, y + 140), f"({s.advocate}), Advocate", font=serif, fill=ink)
    return img


def photoize(img: Image.Image, seed: int = 7) -> Image.Image:
    """Make a clean render look like a phone photo: tilt, uneven light, blur, grain."""
    rnd = random.Random(seed)
    img = img.rotate(rnd.uniform(-2.4, 2.4), expand=True, resample=Image.BICUBIC, fillcolor=(58, 54, 50))
    w, h = img.size
    vignette = Image.radial_gradient("L").resize((w, h)).point(lambda v: v * 120 // 255)
    img = Image.composite(Image.new("RGB", (w, h), (70, 64, 56)), img, vignette)
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    px = img.load()
    for _ in range(w * h // 40):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r, g, b = px[x, y]
        n = rnd.randint(-14, 14)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def make_all(out_dir: Path, photo: bool = False, scenario: Scenario | None = None) -> dict[DocType, Path]:
    s = scenario or Scenario()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    makers = {DocType.CHEQUE: make_cheque, DocType.RETURN_MEMO: make_memo, DocType.DEMAND_NOTICE: make_notice}
    out: dict[DocType, Path] = {}
    for t, fn in makers.items():
        img = fn(s)
        band(img)
        if photo:
            img = photoize(img)
            path = out_dir / f"{t.value}.jpg"
            img.save(path, "JPEG", quality=82, comment=b"tarikh-sample=fictional")
        else:
            meta = PngImagePlugin.PngInfo()
            meta.add_text("tarikh-sample", "fictional")
            path = out_dir / f"{t.value}.png"
            img.save(path, "PNG", pnginfo=meta)
        out[t] = path
    return out


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "samples")
    for p in make_all(target).values():
        print(p)
    for p in make_all(target / "photo", photo=True).values():
        print(p)
