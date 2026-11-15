"""Plum-Designsystem für das Kanal-Format (nach dem Leitfaden tutorial-kurzvideo-kanal.md).

Regeln: keine Konturen um Text (nur weicher Schatten + dunkles Glühen), keine Kategorie-Labels,
alles gleitet herein, Karten ohne Rand mit sanftem Glühen oben. Schriften: Barlow Condensed
(Titel, Großbuchstaben) und Albert Sans (Fließtext, Pillen, Untertitel).

Alle Bausteine liefern RGBA-Bilder mit symmetrischem Rand (PAD), damit sie über den Mittelpunkt
platziert werden können.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(ROOT, "assets", "fonts")
W, H = 1080, 1920


def hexc(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Grundfarben (GTA-VI-Webseite) + Stimmung "Plum"
GROUND, SHADOW, CREAM = hexc("#0c0d1b"), hexc("#070810"), hexc("#fff9cb")
CARD, LIGHT, ACCENT, SECOND = hexc("#4b2f54"), hexc("#fbd9e0"), hexc("#ffd4a8"), hexc("#ffc2d0")
NEAR_WHITE = hexc("#fdfbff")
GLOW = [hexc("#ffff99"), hexc("#f5899b"), hexc("#e963bc")]
BIG = [hexc("#ffd687"), hexc("#fc5243"), hexc("#9d2f6a")]
STRIKE = hexc("#f4717c")
COLORS = {"cream": CREAM, "accent": ACCENT, "second": SECOND, "light": LIGHT, "white": NEAR_WHITE,
          "ground": GROUND, "strike": STRIKE}

# TikTok-Zonen (1080x1920)
SAFE = dict(x0=70, x1=890, y0=270, y1=1630, top_bar=255, btn_x=906, btn_y0=817, btn_y1=1888,
            cap_x1=773, cap_y=1644, card_y0=280, card_y1=818)
PAD = 40                                   # Rand für Schatten/Glühen um jedes Element


def col(c):
    return COLORS.get(c, c) if isinstance(c, str) else tuple(c)


@lru_cache(maxsize=64)
def barlow(size: int, extra: bool = True) -> ImageFont.FreeTypeFont:
    name = "BarlowCondensed-ExtraBold.ttf" if extra else "BarlowCondensed-Bold.ttf"
    return ImageFont.truetype(os.path.join(FONTS, name), size)


@lru_cache(maxsize=64)
def albert(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(os.path.join(FONTS, "AlbertSans[wght].ttf"), size)
    f.set_variation_by_name(weight)
    return f


def shadowed(img: Image.Image, blur=14, alpha=0.6, dy=5, glow=0.0, glow_blur=40) -> Image.Image:
    """Weicher Schatten (und optional dunkles Glühen) unter ein RGBA-Bild legen. Bild muss PAD-Rand haben."""
    a = img.getchannel("A")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if glow:
        g = a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(glow_blur))
        out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, v) for v in SHADOW],
                                                  g.point(lambda v: int(v * glow)))))
    s = a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    sh = Image.merge("RGBA", (*[Image.new("L", img.size, v) for v in SHADOW], s))
    out.alpha_composite(sh, (0, dy))
    out.alpha_composite(img)
    return out


def _gradient(size, stops, horizontal=False) -> Image.Image:
    w, h = size
    n = w if horizontal else h
    t = np.linspace(0, 1, max(n, 2))
    k = len(stops) - 1
    seg = np.minimum((t * k).astype(int), k - 1)
    f = (t * k - seg)[:, None]
    s = np.array(stops, dtype=np.float32)
    line = s[seg] * (1 - f) + s[seg + 1] * f
    arr = np.repeat(line[None, :, :], h, 0) if horizontal else np.repeat(line[:, None, :], w, 1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def _text_mask(lines, font, spacing, align="center", tracking=0):
    """Mehrzeiliger Text als Maske (L) ohne Rand; gibt (Maske, Zeilenbreiten) zurück."""
    asc, desc = font.getmetrics()
    lh = asc + desc
    widths = [font.getlength(ln) + tracking * max(len(ln) - 1, 0) for ln in lines]
    w = int(max(widths)) + 4
    h = int(lh * len(lines) + spacing * (len(lines) - 1))
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for i, ln in enumerate(lines):
        x = (w - widths[i]) / 2 if align == "center" else 0
        y = i * (lh + spacing)
        if tracking:
            for ch in ln:
                d.text((x, y), ch, font=font, fill=255)
                x += font.getlength(ch) + tracking
        else:
            d.text((x, y), ln, font=font, fill=255)
    bb = m.getbbox() or (0, 0, w, h)
    # vertikal auf die echte Tinte zuschneiden, horizontal die volle Breite behalten (Zentrierung)
    return m.crop((0, bb[1], w, bb[3]))


def text(s: str, font, fill="cream", spacing=None, shadow=True, glow=0.35, tracking=0) -> Image.Image:
    lines = s.split("\n")
    spacing = int(font.size * 0.12) if spacing is None else spacing
    m = _text_mask(lines, font, spacing, tracking=tracking)
    img = Image.new("RGBA", (m.width + 2 * PAD, m.height + 2 * PAD), (*col(fill), 0))
    img.putalpha(Image.new("L", img.size, 0))
    layer = Image.new("RGBA", m.size, (*col(fill), 255))
    layer.putalpha(m)
    img.alpha_composite(layer, (PAD, PAD))
    return shadowed(img, glow=glow) if shadow else img


def gradient_text(s: str, font, stops=BIG, spacing=None, glow=0.45, tracking=0) -> Image.Image:
    """Großer Text mit Farbverlauf (oben gelb -> rot -> plum), weicher Schatten."""
    lines = s.split("\n")
    spacing = int(font.size * 0.02) if spacing is None else spacing
    m = _text_mask(lines, font, spacing, tracking=tracking)
    g = _gradient(m.size, stops).convert("RGBA")
    g.putalpha(m)
    img = Image.new("RGBA", (m.width + 2 * PAD, m.height + 2 * PAD), (0, 0, 0, 0))
    img.alpha_composite(g, (PAD, PAD))
    return shadowed(img, blur=18, alpha=0.7, dy=8, glow=glow)


def card(w: int, h: int, radius=40, fill=CARD, alpha=0.94) -> Image.Image:
    """Karte ohne Rand: Plum-Fläche, sanftes radiales Glühen oben, weicher Schatten."""
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    base = Image.new("RGBA", (w, h), (*fill, 255))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy + h * 0.05) / (min(h, 420) * 0.95)) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 1.6 * 0.20
    tint = Image.new("RGBA", (w, h), (*LIGHT, 255))
    tint.putalpha(Image.fromarray((glow * 255).astype(np.uint8)))
    base.alpha_composite(tint)
    base.putalpha(m.point(lambda v: int(v * alpha)))
    img.alpha_composite(base, (PAD, PAD))
    return shadowed(img, blur=26, alpha=0.55, dy=14)


def pill(s: str, bg="accent", fg="ground", size=36, h=84, padx=40, weight="SemiBold", min_w=0) -> Image.Image:
    f = albert(size, weight)
    tw = f.getlength(s)
    w = int(max(tw + 2 * padx, min_w, h))
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD, PAD, PAD + w - 1, PAD + h - 1], radius=h // 2, fill=(*col(bg), 255))
    asc, desc = f.getmetrics()
    d.text((PAD + (w - tw) / 2, PAD + (h - asc - desc) / 2 + 1), s, font=f, fill=(*col(fg), 255))
    return shadowed(img, blur=14, alpha=0.5, dy=6)


def glow_pill(s: str, size=40, h=96, padx=48, weight="Bold") -> Image.Image:
    """Hervorgehobene Pille mit dem Glüh-Verlauf (gelb -> koralle -> pink) und farbigem Schein."""
    f = albert(size, weight)
    tw = f.getlength(s)
    w = int(tw + 2 * padx)
    P = PAD + 20
    img = Image.new("RGBA", (w + 2 * P, h + 2 * P), (0, 0, 0, 0))
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([P, P, P + w - 1, P + h - 1], radius=h // 2, fill=255)
    halo = _gradient(img.size, GLOW, horizontal=True).convert("RGBA")
    halo.putalpha(m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.8)))
    img.alpha_composite(halo)
    body = _gradient(img.size, GLOW, horizontal=True).convert("RGBA")
    body.putalpha(m)
    img.alpha_composite(body)
    asc, desc = f.getmetrics()
    ImageDraw.Draw(img).text((P + (w - tw) / 2, P + (h - asc - desc) / 2 + 1), s, font=f, fill=(*GROUND, 255))
    return img


def row(items: list[Image.Image], gap=18) -> Image.Image:
    """Bausteine (mit PAD-Rand) nebeneinander setzen; Ränder überlappen, damit der Abstand stimmt."""
    w = sum(i.width for i in items) - 2 * PAD * (len(items) - 1) + gap * (len(items) - 1)
    h = max(i.height for i in items)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i in items:
        out.alpha_composite(i, (x, (h - i.height) // 2))
        x += i.width - 2 * PAD + gap
    return out


# ---------- Untertitel: 1-3 Wörter pro Seite, aktives Wort auf Akzent-Pille ----------
SUB_SIZE, SUB_BOX = 76, 700


def subtitle(words: list[str], active: int, pop: float = 1.0, size=SUB_SIZE) -> Image.Image:
    f = albert(size, "ExtraBold")
    asc, desc = f.getmetrics()
    padx, pady = int(size * 0.24), int(size * 0.10)
    gap = int(size * 0.26) + padx
    ws = [f.getlength(w) for w in words]
    total = sum(ws) + gap * (len(ws) - 1)
    lh = asc + desc
    w = int(total + 2 * padx + 2 * PAD + 60)
    h = int(lh + 2 * pady + 2 * PAD + 40)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # dunkles radiales Glühen hinter der Zeile
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).rounded_rectangle([PAD + 10, PAD + 14, w - PAD - 10, h - PAD - 14], radius=60, fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), v) for v in SHADOW], glow)))
    x = (w - total) / 2
    y = (h - lh) / 2
    txt = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    for i, word in enumerate(words):
        if i == active:
            k = 0.7 + 0.3 * pop
            cx = x + ws[i] / 2
            hw, hh = ws[i] / 2 + padx * k, lh / 2 + pady * k
            d.rounded_rectangle([cx - hw, y + lh / 2 - hh + 4, cx + hw, y + lh / 2 + hh + 4], radius=int(hh * 0.55),
                                fill=(*ACCENT, 255))
            d.text((x, y), word, font=f, fill=(*GROUND, 255))
        else:
            d.text((x, y), word, font=f, fill=(*CREAM, 255))
        x += ws[i] + gap
    img.alpha_composite(shadowed(txt, blur=10, alpha=0.55, dy=4))
    return img


def safe_mask() -> Image.Image:
    """Rote Prüfmaske: Bereiche, die die TikTok-Oberfläche verdeckt (nur für Kontroll-Standbilder)."""
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    red = (255, 0, 0, 90)
    d.rectangle([0, 0, W, SAFE["top_bar"]], fill=red)
    d.rectangle([SAFE["btn_x"], SAFE["btn_y0"], W, SAFE["btn_y1"]], fill=red)
    d.rectangle([0, SAFE["cap_y"], SAFE["cap_x1"], H], fill=red)
    d.rectangle([0, 0, 52, H], fill=(255, 0, 0, 50))
    d.rectangle([W - 52, 0, W, H], fill=(255, 0, 0, 50))
    d.rectangle([SAFE["x0"], SAFE["card_y0"], SAFE["x1"], SAFE["card_y1"]], outline=(0, 255, 120, 200), width=3)
    return m


def paste(canvas: Image.Image, im: Image.Image, x: float, y: float, opacity: float = 1.0):
    """RGBA-Bild an (x, y) = linke obere Ecke einsetzen; erlaubt negative Koordinaten und Deckkraft."""
    if opacity <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if r <= l or b <= t:
        return
    part = im.crop((l, t, r, b)) if (l, t, r, b) != (0, 0, im.width, im.height) else im
    if opacity < 0.997:
        part = part.copy()
        part.putalpha(part.getchannel("A").point(lambda v: int(v * opacity)))
    canvas.alpha_composite(part, (x + l, y + t))
