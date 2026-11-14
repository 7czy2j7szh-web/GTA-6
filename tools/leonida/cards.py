"""Info-Karten im Erklärvideo-Stil: dunkles Panel, farbiger Rahmen, Icon im Ring, Titel + Untertitel.

Kartentypen (alle als dict im Spec, Feld "card" eines Beats):
  info   : {"type":"info", "icon":"badge", "title":"…", "subtitle":"…", "border":"green"}
  stars  : {"type":"stars", "title":"…", "subtitle":"…", "total":6, "at":0.15, "step":0.1, "border":"red"}
  grid   : {"type":"grid", "title":"…", "border":"red",
            "tiles":[{"icon":"face", "label":"Gesicht", "at":0.1, "strike":-1}, …]}
  choice : {"type":"choice", "question":"…", "qcolor":"green",
            "options":[{"label":"Trennen", "color":"green", "at":0.1, "strike":-1}, …]}
"at"/"strike" = Zeitpunkte relativ zum Beat-Start (s); -1 = nie.
Alles wird 2x überabgetastet gezeichnet (glatte Kanten) und nach Animationszustand gecacht.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
SS = 2                                    # Überabtastung

WHITE = (255, 255, 255)
PANEL = (24, 25, 33)
COLORS = {"green": (61, 220, 110), "red": (236, 64, 64), "pink": (255, 45, 149), "yellow": (255, 214, 64),
          "teal": (0, 209, 193), "white": WHITE, "orange": (255, 138, 0), "blue": (64, 156, 255)}

_fonts: dict = {}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    return _fonts[key]


def col(c) -> tuple:
    return COLORS.get(c, c) if isinstance(c, str) else tuple(c)


def ease_out_back(x: float, s: float = 1.7) -> float:
    x = min(max(x, 0.0), 1.0) - 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_cubic(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- Icons (Strichgrafik, weiß)

def icon(name: str, size: int, color=WHITE) -> Image.Image:
    """Einfaches, eindeutiges Symbol in einem Quadrat der Kantenlänge size (bereits überabgetastet)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size
    c = color + (255,)

    def person(cx, cy, k=1.0):
        r = 0.16 * s * k
        d.ellipse([cx - r, cy - 0.30 * s * k - r, cx + r, cy - 0.30 * s * k + r], fill=c)
        w, h = 0.30 * s * k, 0.34 * s * k
        d.pieslice([cx - w, cy - 0.04 * s * k, cx + w, cy - 0.04 * s * k + 2 * h], 180, 360, fill=c)

    if name == "person":
        person(s / 2, s / 2 + 0.06 * s)
    elif name == "duo":
        person(s * 0.36, s / 2 + 0.08 * s, 0.82)
        person(s * 0.64, s / 2 + 0.08 * s, 0.82)
    elif name == "face":
        lw = max(int(s * 0.085), 2)
        d.ellipse([s * 0.10, s * 0.10, s * 0.90, s * 0.90], outline=c, width=lw)
        for ex in (0.37, 0.63):
            d.ellipse([s * ex - s * 0.065, s * 0.32, s * ex + s * 0.065, s * 0.46], fill=c)
        d.arc([s * 0.30, s * 0.36, s * 0.70, s * 0.72], 25, 155, fill=c, width=lw)
    elif name == "shirt":
        pts = [(0.34, 0.18), (0.42, 0.18), (0.5, 0.26), (0.58, 0.18), (0.66, 0.18), (0.88, 0.34), (0.78, 0.48),
               (0.70, 0.42), (0.70, 0.84), (0.30, 0.84), (0.30, 0.42), (0.22, 0.48), (0.12, 0.34)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=c)
    elif name == "car":
        d.rounded_rectangle([s * 0.08, s * 0.44, s * 0.92, s * 0.68], radius=s * 0.08, fill=c)
        d.polygon([(s * 0.26, s * 0.46), (s * 0.36, s * 0.28), (s * 0.66, s * 0.28), (s * 0.78, s * 0.46)], fill=c)
        for wx in (0.28, 0.72):
            d.ellipse([s * wx - s * 0.11, s * 0.58, s * wx + s * 0.11, s * 0.80], fill=c)
            d.ellipse([s * wx - s * 0.05, s * 0.64, s * wx + s * 0.05, s * 0.74], fill=PANEL + (255,))
        d.polygon([(s * 0.40, s * 0.33), (s * 0.49, s * 0.33), (s * 0.49, s * 0.44), (s * 0.34, s * 0.44)],
                  fill=PANEL + (255,))
        d.polygon([(s * 0.53, s * 0.33), (s * 0.63, s * 0.33), (s * 0.70, s * 0.44), (s * 0.53, s * 0.44)],
                  fill=PANEL + (255,))
    elif name in ("star", "star_off"):
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            r = 0.46 * s if k % 2 == 0 else 0.19 * s
            pts.append((s / 2 + r * math.cos(a), s / 2 + 0.03 * s + r * math.sin(a)))
        if name == "star":
            d.polygon(pts, fill=c)
        else:
            d.polygon(pts, outline=color + (110,), width=max(int(s * 0.05), 2))
    elif name == "badge":
        pts = [(0.5, 0.10), (0.84, 0.22), (0.80, 0.56), (0.5, 0.90), (0.20, 0.56), (0.16, 0.22)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=c)
        star = icon("star", int(s * 0.46), PANEL)
        im.alpha_composite(star, (int(s * 0.27), int(s * 0.27)))
    elif name == "eye":
        lw = max(int(s * 0.08), 2)
        n = 40
        top = [(s * (0.08 + 0.84 * k / n), s * (0.5 - 0.26 * math.sin(math.pi * k / n))) for k in range(n + 1)]
        bot = [(x, s - y) for x, y in top[::-1]]
        d.line(top + bot + [top[0]], fill=c, width=lw, joint="curve")
        d.ellipse([s * 0.36, s * 0.36, s * 0.64, s * 0.64], fill=c)
    elif name == "bookmark":
        d.polygon([(s * 0.28, s * 0.12), (s * 0.72, s * 0.12), (s * 0.72, s * 0.88), (s * 0.5, s * 0.68),
                   (s * 0.28, s * 0.88)], fill=c)
    elif name == "split":                                  # zwei Pfeile auseinander
        lw = max(int(s * 0.08), 2)
        d.line([s * 0.5, s * 0.86, s * 0.5, s * 0.52], fill=c, width=lw)
        for sx in (-1, 1):
            ex, ey = s * (0.5 + sx * 0.30), s * 0.18
            d.line([s * 0.5, s * 0.54, ex, ey], fill=c, width=lw)
            ang = math.atan2(ey - s * 0.54, ex - s * 0.5)
            for da in (2.6, -2.6):
                d.line([ex, ey, ex + s * 0.16 * math.cos(ang + da), ey + s * 0.16 * math.sin(ang + da)],
                       fill=c, width=lw)
    return im


def icon_ring(name: str, d_px: int, ring) -> Image.Image:
    """Icon in einem farbigen Ring (wie in Erklärvideos)."""
    D = d_px * SS
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    lw = int(D * 0.06)
    dr.ellipse([0, 0, D - 1, D - 1], fill=(14, 15, 20, 255), outline=col(ring) + (255,), width=lw)
    g = icon(name, int(D * 0.56))
    im.alpha_composite(g, ((D - g.width) // 2, (D - g.height) // 2))
    return im


# ---------------------------------------------------------------- Bausteine

def _text(d: ImageDraw.ImageDraw, xy, txt, f, fill, anchor="mm"):
    d.text(xy, txt, font=f, fill=fill, anchor=anchor)


def _panel(w: int, h: int, border, radius=44, alpha=236) -> Image.Image:
    """Panel mit weichem Schatten (alles in Überabtastung)."""
    pad = 40 * SS
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14 * SS, pad + w, pad + h + 14 * SS], radius=radius * SS,
                                         fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18 * SS)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius=radius * SS, fill=PANEL + (alpha,),
                        outline=col(border) + (255,), width=6 * SS)
    return im


def _strike(im: Image.Image, box, p: float, width_px=9):
    """Roter Strich schräg durch box (x0,y0,x1,y1), wächst mit p von links oben nach rechts unten."""
    if p <= 0:
        return
    x0, y0, x1, y1 = box
    ex, ey = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    d = ImageDraw.Draw(im)
    w = width_px * SS
    d.line([x0, y0, ex, ey], fill=(0, 0, 0, 255), width=w + 6 * SS)
    d.line([x0, y0, ex, ey], fill=COLORS["red"] + (255,), width=w)
    for px, py in ((x0, y0), (ex, ey)):
        d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=COLORS["red"] + (255,))


def _paste_scaled(dst: Image.Image, src: Image.Image, cx: float, cy: float, scale: float, alpha: float):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        src = src.copy()
        src.putalpha(src.getchannel("A").point(lambda v: int(v * alpha)))
    dst.alpha_composite(src, (int(cx - src.width / 2), int(cy - src.height / 2)))


def _pop(lt: float, at: float, dur=0.24):
    """(Skalierung, Deckkraft) eines Elements, das bei at erscheint."""
    if at == 0:                                        # von Anfang an sichtbar (Karte selbst animiert)
        return 1.0, 1.0
    if at < 0 or lt < at:
        return 0.0, 0.0
    q = (lt - at) / dur
    return 0.6 + 0.4 * ease_out_back(q), min(1.0, q * 2.5)


def _q(x: float, n=14) -> int:
    return int(round(min(max(x, 0.0), 1.0) * n))


# ---------------------------------------------------------------- Kartentypen

def _info(c: dict, lt: float) -> Image.Image:
    W = int(c.get("width", 800)) * SS
    tf = font(c.get("font", "Poppins-Bold.ttf"), int(c.get("title_size", 72)) * SS)
    sf = font("Poppins-SemiBold.ttf", int(c.get("sub_size", 46)) * SS)
    ic = c.get("icon")
    ring = 132 * SS if ic else 0
    title_lines = c["title"].split("\n")
    sub_lines = c.get("subtitle", "").split("\n") if c.get("subtitle") else []
    th, sh = int(tf.size * 1.18), int(sf.size * 1.25)
    H = 46 * SS + (ring + 22 * SS if ic else 0) + th * len(title_lines) + sh * len(sub_lines) + 40 * SS
    im = _panel(W, H, c.get("border", "green"))
    pad = 40 * SS
    d = ImageDraw.Draw(im)
    y = pad + 46 * SS
    if ic:
        s, a = _pop(lt, c.get("icon_at", 0.08))
        _paste_scaled(im, icon_ring(ic, 132, c.get("border", "green")), pad + W / 2, y + ring / 2, s, a)
        y += ring + 22 * SS
    for ln in title_lines:
        _text(d, (pad + W / 2, y + th / 2), ln, tf, WHITE)
        y += th
    for ln in sub_lines:
        _text(d, (pad + W / 2, y + sh / 2), ln, sf, (232, 232, 238))
        y += sh
    return im


def _stars(c: dict, lt: float) -> Image.Image:
    W = int(c.get("width", 820)) * SS
    n = int(c.get("total", 6))
    tf = font("Poppins-Bold.ttf", int(c.get("title_size", 68)) * SS)
    sf = font("Poppins-SemiBold.ttf", 46 * SS)
    st = 92 * SS
    th, sh = int(tf.size * 1.18), int(sf.size * 1.25)
    H = 50 * SS + st + 26 * SS + th + (sh if c.get("subtitle") else 0) + 40 * SS
    im = _panel(W, H, c.get("border", "red"))
    pad = 40 * SS
    d = ImageDraw.Draw(im)
    y = pad + 50 * SS
    gap = 12 * SS
    x0 = pad + (W - (n * st + (n - 1) * gap)) / 2
    off = icon("star_off", st)
    for k in range(n):
        cx = x0 + k * (st + gap) + st / 2
        im.alpha_composite(off, (int(cx - st / 2), int(y)))
        s, a = _pop(lt, c.get("at", 0.15) + k * c.get("step", 0.1), 0.2)
        _paste_scaled(im, icon("star", st, col(c.get("star_color", "white"))), cx, y + st / 2, s, a)
    y += st + 26 * SS
    _text(d, (pad + W / 2, y + th / 2), c["title"], tf, WHITE)
    y += th
    if c.get("subtitle"):
        _text(d, (pad + W / 2, y + sh / 2), c["subtitle"], sf, (232, 232, 238))
    return im


def _grid(c: dict, lt: float) -> Image.Image:
    W = int(c.get("width", 800)) * SS
    tiles = c["tiles"]
    cols = int(c.get("cols", 2))
    rows = math.ceil(len(tiles) / cols)
    tf = font("Poppins-Bold.ttf", int(c.get("title_size", 58)) * SS)
    lf = font("Poppins-Bold.ttf", int(c.get("label_size", 44)) * SS)
    th = int(tf.size * 1.3) if c.get("title") else 0
    gap = 22 * SS
    tw = (W - 2 * 34 * SS - (cols - 1) * gap) / cols
    tile_h = 214 * SS
    H = 34 * SS + th + rows * tile_h + (rows - 1) * gap + 34 * SS
    im = _panel(W, H, c.get("border", "red"))
    pad = 40 * SS
    d = ImageDraw.Draw(im)
    if c.get("title"):
        _text(d, (pad + W / 2, pad + 34 * SS + th / 2), c["title"], tf, WHITE)
    for k, t in enumerate(tiles):
        r_, c_ = divmod(k, cols)
        x = pad + 34 * SS + c_ * (tw + gap)
        y = pad + 34 * SS + th + r_ * (tile_h + gap)
        s, a = _pop(lt, t.get("at", 0.1))
        if a <= 0:
            continue
        struck = t.get("strike", -1)
        sp = 0.0 if struck < 0 or lt < struck else min(1.0, (lt - struck) / 0.16)
        tile = Image.new("RGBA", (int(tw), int(tile_h)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        tcol = col(t.get("color", c.get("border", "red")))
        td.rounded_rectangle([0, 0, tw - 1, tile_h - 1], radius=28 * SS, fill=(38, 40, 52, 255),
                             outline=tcol + (255,), width=4 * SS)
        g = icon_ring(t["icon"], 104, tcol)
        tile.alpha_composite(g, (int((tw - g.width) / 2), 22 * SS))
        _text(td, (tw / 2, 22 * SS + g.height + 40 * SS), t["label"], lf, WHITE)
        if sp > 0:                                    # durchgestrichen: abdunkeln + roter Strich
            dim = Image.new("RGBA", tile.size, (16, 16, 22, int(150 * sp)))
            mask = tile.getchannel("A")
            tile.alpha_composite(Image.composite(dim, Image.new("RGBA", tile.size, (0, 0, 0, 0)), mask))
            _strike(tile, (tw * 0.12, tile_h * 0.18, tw * 0.88, tile_h * 0.82), sp, 11)
        _paste_scaled(im, tile, x + tw / 2, y + tile_h / 2, s, a)
    return im


def _choice(c: dict, lt: float) -> Image.Image:
    W = int(c.get("width", 840)) * SS
    opts = c["options"]
    pf = font("Poppins-Bold.ttf", int(c.get("label_size", 48)) * SS)
    qf = font("Poppins-Bold.ttf", int(c.get("q_size", 66)) * SS)
    ph = 96 * SS
    qh = int(qf.size * 1.3)
    H = 52 * SS + ph + 38 * SS + qh + 40 * SS
    im = _panel(W, H, c.get("border", "white"), alpha=230)
    pad = 40 * SS
    d = ImageDraw.Draw(im)
    gap = 36 * SS
    pw = (W - 2 * 50 * SS - (len(opts) - 1) * gap) / len(opts)
    for k, o in enumerate(opts):
        x = pad + 50 * SS + k * (pw + gap)
        y = pad + 52 * SS
        s, a = _pop(lt, o.get("at", 0.1))
        if a <= 0:
            continue
        pill = Image.new("RGBA", (int(pw), int(ph)), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        oc = col(o.get("color", "green"))
        pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph / 2, fill=(40, 42, 54, 255), outline=oc + (255,),
                             width=5 * SS)
        _text(pd, (pw / 2, ph / 2), o["label"], pf, WHITE)
        st = o.get("strike", -1)
        if st >= 0 and lt >= st:
            _strike(pill, (pw * 0.06, ph * 0.12, pw * 0.94, ph * 0.88), min(1.0, (lt - st) / 0.16), 8)
        _paste_scaled(im, pill, x + pw / 2, y + ph / 2, s, a)
    qy = pad + 52 * SS + ph + 38 * SS + qh / 2
    s, a = _pop(lt, c.get("q_at", 0.2))
    if a > 0:
        q = Image.new("RGBA", (W, qh), (0, 0, 0, 0))
        _text(ImageDraw.Draw(q), (W / 2, qh / 2), c["question"], qf, col(c.get("qcolor", "green")))
        _paste_scaled(im, q, pad + W / 2, qy, s, a)
    return im


RENDER = {"info": _info, "stars": _stars, "grid": _grid, "choice": _choice}


def state_key(c: dict, lt: float) -> tuple:
    """Animationszustand (quantisiert) -> Cache-Schlüssel."""
    ts = []
    if c["type"] == "info":
        ts = [c.get("icon_at", 0.08)] if c.get("icon") else []
    elif c["type"] == "stars":
        ts = [c.get("at", 0.15) + k * c.get("step", 0.1) for k in range(int(c.get("total", 6)))]
    elif c["type"] == "grid":
        ts = [t.get("at", 0.1) for t in c["tiles"]]
    elif c["type"] == "choice":
        ts = [o.get("at", 0.1) for o in c["options"]] + [c.get("q_at", 0.2)]
    k = [(-1 if lt < t else _q((lt - t) / 0.24)) for t in ts]
    strikes = [t.get("strike", -1) for t in c.get("tiles", [])] + [o.get("strike", -1) for o in c.get("options", [])]
    k += [(-1 if s < 0 or lt < s else _q((lt - s) / 0.16, 8)) for s in strikes]
    return tuple(k)


def render(c: dict, lt: float) -> Image.Image:
    """Karte im Zustand lt (Sekunden seit Beat-Start) in Endauflösung."""
    big = RENDER[c["type"]](c, lt)
    return big.resize((big.width // SS, big.height // SS), Image.LANCZOS)
