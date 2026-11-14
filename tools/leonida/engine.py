"""Leonida-Renderer: baut TikTok-Videos (1080x1920) aus einer JSON-Spezifikation.

Ein Spec beschreibt Hintergrund-Szenen (Bilder mit Ken-Burns-Bewegung),
Text-"Beats" mit Animationen und Soundeffekte. Gerendert wird Frame für Frame
mit Pillow, kodiert mit ffmpeg. Keine Stimme nötig: der Text trägt das Video,
der Trend-Sound wird später in der TikTok-App darübergelegt.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import sfx as sfxmod

W, H = 1080, 1920
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

# Account-Look
PINK = (255, 45, 149)
ORANGE = (255, 138, 0)
TEAL = (0, 209, 193)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 225, 60)
RED = (235, 30, 45)
GREEN = (40, 220, 110)
COLORS = {"pink": PINK, "orange": ORANGE, "teal": TEAL, "white": WHITE, "yellow": YELLOW, "red": RED, "green": GREEN}

# TikTok-Safe-Zone (oben Tabs, unten Caption, rechts Buttons)
SAFE_LEFT, SAFE_RIGHT = 70, W - 150
SAFE_TOP, SAFE_BOTTOM = 230, H - 430

STYLES = {
    "hook": dict(font="Anton-Regular.ttf", size=104, stroke=9, color=WHITE),
    "body": dict(font="Anton-Regular.ttf", size=86, stroke=8, color=WHITE),
    "big": dict(font="Anton-Regular.ttf", size=210, stroke=12, color=PINK),
    "huge": dict(font="Anton-Regular.ttf", size=300, stroke=14, color=PINK),
    "small": dict(font="BebasNeue-Regular.ttf", size=72, stroke=6, color=WHITE),
    "label": dict(font="BebasNeue-Regular.ttf", size=70, stroke=0, color=WHITE, pill=PINK),
    "stamp": dict(font="Anton-Regular.ttf", size=150, stroke=10, color=WHITE),
    "note": dict(font="Poppins-SemiBold.ttf", size=38, stroke=5, color=WHITE),
    # Suchleiste (generisch, keine Marke): weiße Pille, dunkler Text, Lupe links
    "search": dict(font="Inter-SemiBold.otf", size=56, stroke=0, color=(32, 33, 36), pill=WHITE,
                   icon="search", min_width=880, align="left"),
}


@lru_cache(maxsize=64)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def ease_out_back(x: float, s: float = 1.7) -> float:
    x = min(max(x, 0.0), 1.0) - 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_cubic(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


# ---------------------------------------------------------------- Text

def parse_markup(text: str, base_color, accent):
    """'Das ist *wichtig*-ish' -> Wörter als Segment-Listen [[(text, farbe), ...], ...].

    *...* = Akzentfarbe. Ein Wort kann mehrfarbig sein ("*Series S*-Besitzer")."""
    words: list[list[tuple[str, tuple]]] = []
    cur: list[tuple[str, tuple]] = []
    for i, part in enumerate(re.split(r"\*", text)):
        color = accent if i % 2 == 1 else base_color
        pieces = part.split(" ")
        for j, piece in enumerate(pieces):
            if j > 0 and cur:          # Leerzeichen -> Wortgrenze
                words.append(cur)
                cur = []
            if piece:
                cur.append((piece, color))
    if cur:
        words.append(cur)
    return words


def _word_len(f, word) -> float:
    return sum(f.getlength(s) for s, _ in word)


def render_text(text: str, style: str = "body", accent="pink", color=None,
                max_width: int = SAFE_RIGHT - SAFE_LEFT, align: str = "center",
                size: int | None = None) -> Image.Image:
    st = STYLES[style]
    f = font(st["font"], size or st["size"])
    stroke = st["stroke"]
    base = COLORS.get(color, color) if color else st["color"]
    acc = COLORS.get(accent, accent)
    space = f.getlength(" ")
    lines: list[list] = []
    for raw_line in text.split("\n"):
        line: list = []
        for word in parse_markup(raw_line, base, acc):
            trial = sum(_word_len(f, w) for w in line + [word]) + space * len(line)
            if line and trial + 2 * stroke > max_width:
                lines.append(line)
                line = [word]
            else:
                line.append(word)
        lines.append(line)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.02)
    widths = [sum(_word_len(f, w) for w in ln) + space * max(len(ln) - 1, 0) for ln in lines]
    pad = stroke + 24
    pill = st.get("pill")
    icon = st.get("icon")
    align = st.get("align", align)
    pill_px, pill_py = (34, 14) if pill else (0, 0)
    icon_w = int(lh * 0.9) if icon else 0
    content_w = max(max(widths) + icon_w, st.get("min_width", 0) - 2 * pad - 2 * pill_px)
    img_w = int(content_w + 2 * pad + 2 * pill_px)
    img_h = int(lh * len(lines) + 2 * pad + 2 * pill_py)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if pill:
        r = 26 if not icon else (img_h - 2 * pad + 12) // 2
        d.rounded_rectangle([pad - 6, pad - 6, img_w - pad + 6, img_h - pad + 6], radius=r, fill=pill + (255,))
    if icon == "search":
        cx, cy, rr = pad + pill_px + lh * 0.30, pad + pill_py + lh * 0.46, lh * 0.20
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(95, 99, 104), width=6)
        d.line([cx + rr * 0.7, cy + rr * 0.7, cx + rr * 1.6, cy + rr * 1.6], fill=(95, 99, 104), width=7)
    # Schatten-Ebene
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    y = pad + pill_py
    for ln, lw in zip(lines, widths):
        x = (img_w - lw) / 2 if align == "center" else pad + pill_px + icon_w
        for word in ln:
            for seg, c in word:
                if not pill:
                    sd.text((x + 6, y + 8), seg, font=f, fill=(0, 0, 0, 160), stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
                d.text((x, y), seg, font=f, fill=c, stroke_width=stroke, stroke_fill=BLACK)
                x += f.getlength(seg)
            x += space
        y += lh
    if not pill:
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        shadow.alpha_composite(img)
        img = shadow
    return img


def render_card(path: str, width: int = 620) -> Image.Image:
    """Bild als Karte: abgerundet, pinker Rahmen, weicher Schatten."""
    src = Image.open(os.path.join(ROOT, path)).convert("RGB")
    h = int(src.height * width / src.width)
    src = src.resize((width, h), Image.LANCZOS)
    pad, border, r = 40, 8, 28
    card = Image.new("RGBA", (width + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 12, pad + width, pad + h + 12], radius=r, fill=(0, 0, 0, 170))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    mask = Image.new("L", (width, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, width - 1, h - 1], radius=r, fill=255)
    card.paste(src, (pad, pad), mask)
    ImageDraw.Draw(card).rounded_rectangle([pad, pad, pad + width, pad + h], radius=r, outline=PINK + (255,), width=border)
    return card


def render_karaoke(words: list[str], shown: int, active: int, size: int = 104,
                   max_width: int = SAFE_RIGHT - SAFE_LEFT, font_name: str = "Anton-Regular.ttf",
                   hl=YELLOW, stroke: int = 9) -> Image.Image:
    """Untertitel im Karaoke-Stil: der ganze Block steht, das gerade gesprochene Wort ist gelb
    und etwas größer. Jedes Wort hat einen festen Platz (Breite der großen Variante) -> nichts
    springt, nichts überlappt. shown < len(words) blendet spätere Wörter aus (optional)."""
    f = font(font_name, size)
    fa = font(font_name, int(size * 1.12))
    space = f.getlength(" ") * 1.1
    slot = [fa.getlength(w) for w in words]
    lines, line = [], []
    for i in range(len(words)):
        trial = sum(slot[j] for j in line + [i]) + space * len(line)
        if line and trial + 2 * stroke > max_width:
            lines.append(line)
            line = [i]
        else:
            line.append(i)
    lines.append(line)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.02)
    asc_a, _ = fa.getmetrics()
    widths = [sum(slot[i] for i in ln) + space * max(len(ln) - 1, 0) for ln in lines]
    pad = stroke + 24 + int(size * 0.12)
    img_w, img_h = int(max(widths) + 2 * pad), int(lh * len(lines) + 2 * pad)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(img), ImageDraw.Draw(shadow)
    y = pad
    for ln, lw in zip(lines, widths):
        x = (img_w - lw) / 2
        for i in ln:
            if i < shown:
                ff, col, yy = (fa, hl, y - (asc_a - asc)) if i == active else (f, WHITE, y)
                pos = (x + (slot[i] - ff.getlength(words[i])) / 2, yy)
                sd.text((pos[0] + 6, pos[1] + 8), words[i], font=ff, fill=(0, 0, 0, 170),
                        stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
                d.text(pos, words[i], font=ff, fill=col, stroke_width=stroke, stroke_fill=BLACK)
            x += slot[i] + space
        y += lh
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    shadow.alpha_composite(img)
    return shadow


def render_ring(value: float, r: int, color, label: str, size: int, label_color) -> Image.Image:
    """Wertungs-Ring: Bogen füllt sich bis value/100, Zahl in der Mitte (2x überabgetastet)."""
    ss, th, pad = 2, int(r * 0.15), 46
    D = 2 * (r + pad)
    c, R, T = D * ss / 2, r * ss, th * ss
    base = Image.new("RGBA", (D * ss, D * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.ellipse([c - R - 6 * ss, c - R - 6 * ss, c + R + 6 * ss, c + R + 6 * ss], fill=(0, 0, 0, 125))
    box = [c - R, c - R, c + R, c + R]
    d.arc(box, 0, 360, fill=(255, 255, 255, 70), width=T)
    frac = min(max(value / 100, 0), 1)
    if frac > 0.002:
        arc = Image.new("RGBA", base.size, (0, 0, 0, 0))
        da = ImageDraw.Draw(arc)
        a0, a1 = -90, -90 + 360 * frac
        da.arc(box, a0, a1, fill=color + (255,), width=T)
        rc = R - T / 2
        for ang in (a0, a1):                                   # runde Enden
            px, py = c + rc * math.cos(math.radians(ang)), c + rc * math.sin(math.radians(ang))
            da.ellipse([px - T / 2, py - T / 2, px + T / 2, py + T / 2], fill=color + (255,))
        glow = arc.filter(ImageFilter.GaussianBlur(16 * ss))
        base.alpha_composite(glow)
        base.alpha_composite(arc)
    img = base.resize((D, D), Image.LANCZOS)
    if label:
        t = render_text(label, "huge", color=label_color, size=size)
        img.alpha_composite(t, (int(D / 2 - t.width / 2), int(D / 2 - t.height / 2)))
    return img


# ---------------------------------------------------------------- Hintergrund

def synth_background(preset: str = "sunset") -> Image.Image:
    """Eigener, lizenzfreier Retro-Hintergrund: Verlauf + Sonne + Gitter."""
    w, h = int(W * 1.3), int(H * 1.3)
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    palettes = {
        "sunset": [(24, 8, 52), (120, 20, 110), (255, 45, 149), (255, 138, 0)],
        "night": [(5, 5, 20), (30, 10, 60), (80, 20, 120), (0, 120, 140)],
        "red": [(30, 0, 0), (120, 0, 20), (220, 20, 40), (255, 90, 60)],
        "green": [(0, 25, 15), (0, 90, 60), (0, 180, 120), (120, 255, 170)],
    }
    stops = palettes.get(preset, palettes["sunset"])
    horizon = 0.62
    t = np.clip(y / horizon, 0, 1)
    seg = np.minimum((t * (len(stops) - 1)).astype(int), len(stops) - 2)
    f = t * (len(stops) - 1) - seg
    arr = np.zeros((h, w, 3))
    for c in range(3):
        a = np.array([s[c] for s in stops])
        arr[..., c] = (a[seg] * (1 - f) + a[seg + 1] * f) * np.ones((1, w))
    # Sonne mit Streifen
    cx, cy, r = 0.5, horizon - 0.08, 0.26
    dist = np.sqrt(((x - cx) * w / h) ** 2 + (y - cy) ** 2)
    sun = (dist < r) & ~((np.sin((y - cy) * 120) > 0.55) & (y > cy))
    sun_col = np.stack([np.full_like(y, 255.0), 180 - (y - (cy - r)) / (2 * r) * 140, 60 + 0 * y], -1)
    arr = np.where(sun[..., None], np.broadcast_to(sun_col, arr.shape), arr)
    # Boden mit Perspektiv-Gitter
    below = y > horizon
    arr = np.where(below[..., None], np.array(stops[0]) * 0.6, arr)
    gy = (y - horizon) / (1 - horizon)
    with np.errstate(divide="ignore", invalid="ignore"):
        rows = np.abs(np.sin(np.pi * 6 / np.maximum(gy, 1e-3))) < 0.08 * (1 + gy * 3)
        cols = np.abs(np.sin(np.pi * ((x - 0.5) / np.maximum(gy, 1e-3)) * 6)) < 0.06
    grid = below & (rows | cols)
    arr = np.where(grid[..., None], np.array(stops[2]), arr)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


class Background:
    """Bild, das den Frame füllt, mit Ken-Burns-Zoom/-Schwenk."""

    def __init__(self, path, zoom=(1.0, 1.12), pan=((0.5, 0.5), (0.5, 0.5)), grade: float = 0.0, blur: float = 0):
        if isinstance(path, Image.Image):
            src = path.convert("RGB")
        elif path.startswith("synth:"):
            src = synth_background(path.split(":", 1)[1])
        else:
            src = Image.open(os.path.join(ROOT, path)).convert("RGB")
        # auf sinnvolle Arbeitsgröße bringen (2x Zielhöhe reicht für Zoom)
        scale = max(W * 1.35 / src.width, H * 1.35 / src.height)
        if scale < 1:
            src = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS)
        if blur:
            src = src.filter(ImageFilter.GaussianBlur(blur))
        self.src = src
        self.zoom = zoom
        self.pan = pan
        self.grade = grade

    def frame(self, p: float) -> Image.Image:
        e = ease_in_out(p)
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * e
        px = self.pan[0][0] + (self.pan[1][0] - self.pan[0][0]) * e
        py = self.pan[0][1] + (self.pan[1][1] - self.pan[0][1]) * e
        sw, sh = self.src.size
        # Ausschnitt mit 9:16, der das Bild füllt
        cover = min(sw / W, sh / H)
        cw, ch = W * cover / z, H * cover / z
        cx = cw / 2 + (sw - cw) * px
        cy = ch / 2 + (sh - ch) * py
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        return self.src.resize((W, H), Image.BICUBIC, box=box)


def make_overlay() -> Image.Image:
    """Abdunklung oben/unten + Vignette, damit Text immer lesbar ist."""
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    top = np.clip(1 - y / 0.30, 0, 1) ** 1.6 * 0.55
    bottom = np.clip((y - 0.55) / 0.45, 0, 1) ** 1.4 * 0.75
    mid = 0.12  # leichte Grundabdunklung für Textkontrast
    vign = np.clip((x ** 2) * 0.35, 0, 1)
    a = np.clip(top + bottom + mid + vign, 0, 0.92)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ---------------------------------------------------------------- Beats

@dataclass
class Beat:
    t: float
    end: float
    text: str
    style: str = "body"
    y: float = 0.45          # vertikale Mitte (Anteil der Höhe)
    x: float = 0.5
    anim: str = "pop"         # pop | slide | fade | count | type | stamp
    accent: str = "pink"
    color: str | None = None
    count_from: float = 0
    count_to: float = 0
    count_fmt: str = "{:,.0f}"
    size: int | None = None
    rotate: float = 0
    exit: str = "fade"        # fade | cut
    shake: float = 0          # Wackel-Amplitude in px (erste 0,35 s)
    type_cps: float = 25      # Tipp-Geschwindigkeit (Zeichen/s) für anim=type
    image: str | None = None  # statt Text: Bild als schwebende Karte
    card_w: int = 620         # Kartenbreite in px
    count_dur: float | None = None   # Dauer des Hochzählens (Standard: min(1,6 s, Länge-0,3))
    words: list | None = None        # Karaoke: [[Wort, Startzeit relativ zum Beat], ...]
    ring_r: int = 230                # Wertungs-Ring: Radius in px
    enter: str = ""                  # Eingangs-Animation überschreiben (z. B. "punch" für einen Ring)
    strike_at: float = -1            # roter Durchstreich-Strich ab dieser Zeit (relativ), -1 = aus
    card: dict | None = None         # Info-Karte (siehe cards.py)
    kfont: str = "Anton-Regular.ttf" # Karaoke-Schrift
    khl: str = "yellow"              # Karaoke-Farbe des aktiven Worts
    kstroke: int = 9                 # Karaoke-Kontur

    def count_p(self, lt: float) -> float:
        cd = self.count_dur if self.count_dur else min(1.6, self.end - self.t - 0.3)
        return ease_out_cubic(lt / max(cd, 0.05))

    def text_at(self, lt: float) -> str:
        if self.anim == "count":
            p = self.count_p(lt)
            v = self.count_from + (self.count_to - self.count_from) * p
            num = self.count_fmt.format(v).replace(",", ".")
            return self.text.replace("{n}", num)
        if self.anim == "type":
            n = min(len(self.text), int(lt * self.type_cps) + 1)
            return self.text[:n] if n else ""
        return self.text


class Renderer:
    def __init__(self, spec: dict):
        self.spec = spec
        self.fps = spec.get("fps", 30)
        self.duration = spec["duration"]
        self.scenes = []
        drive_cache = {}
        for sc in spec["scenes"]:
            if sc["image"].startswith("anim:drive"):
                # animierter Neon-Drive-Hintergrund; eine Instanz pro Video, damit die Fahrt durchläuft
                key = (sc.get("bpm", 118), sc.get("car", True))
                if key not in drive_cache:
                    from .drive import NeonDrive
                    drive_cache[key] = NeonDrive(W, H, bpm=key[0], car=key[1])
                bg = drive_cache[key]
            elif sc["image"].startswith("clip:"):
                # echte Videoszene aus einem offiziellen Trailer
                from .clip import VideoClip
                bg = VideoClip(sc["image"][5:], W, H, ss=sc.get("ss", 0.0), dur=sc["end"] - sc["start"],
                               cam=sc.get("cam"))
            elif sc["image"].startswith("drone:"):
                # Drohnen-Kamera ohne Verzerrung (Homographie: drehen/neigen/rollen + Vorwärtszoom)
                from .drone import DroneShot
                bg = DroneShot(sc["image"][6:], W, H, cam=sc.get("cam"))
            elif sc["image"].startswith("shot:"):
                # 3D-Kamerafahrt durch einen echten Screenshot (Tiefen-Parallax)
                from .parallax import ParallaxShot
                bg = ParallaxShot(sc["image"][5:], W, H, cam=sc.get("cam"), focus=sc.get("focus", 0.35))
            else:
                bg = Background(sc["image"], tuple(sc.get("zoom", (1.0, 1.12))),
                                tuple(tuple(p) for p in sc.get("pan", ((0.5, 0.5), (0.5, 0.5)))),
                                blur=sc.get("blur", 0))
            self.scenes.append((sc["start"], sc["end"], bg, sc.get("flash", True)))
        self.fades = [sc.get("fade", spec.get("fade", 0.0)) for sc in spec["scenes"]]
        self.beats = [Beat(**b) for b in spec["beats"]]
        self.overlay = make_overlay()
        k = spec.get("overlay_strength", 1.0)          # weniger Abdunklung bei hellen/animierten Hintergründen
        if k != 1.0:
            self.overlay.putalpha(self.overlay.getchannel("A").point(lambda v: int(v * k)))
        self.cache: dict = {}
        self.badge = spec.get("badge")
        self.progress = spec.get("progress", True)
        self.watermark = spec.get("watermark")
        self.flash_strength = spec.get("flash_strength", 110)  # sanfter Blitz bei Bildwechsel (0 = aus)
        # Zoom-Stöße des Hintergrunds auf Schlägen: [[Zeit, Stärke], ...]
        self.pulses = [tuple(p) if isinstance(p, (list, tuple)) else (p, 0.05) for p in spec.get("pulses", [])]

    def _karaoke_img(self, beat: Beat, lt: float) -> Image.Image:
        ws = beat.words or []
        active = max(sum(1 for _, wt in ws if wt <= lt + 1e-6) - 1, 0)
        key = (id(beat), "k", active)
        if key not in self.cache:
            self.cache[key] = render_karaoke([w for w, _ in ws], len(ws), active, size=beat.size or 104,
                                             font_name=beat.kfont, hl=COLORS.get(beat.khl, beat.khl),
                                             stroke=beat.kstroke)
        return self.cache[key]

    def _card_img(self, beat: Beat, lt: float) -> Image.Image:
        from . import cards
        key = (id(beat), "c", cards.state_key(beat.card, lt))
        if key not in self.cache:
            self.cache[key] = cards.render(beat.card, lt)
        return self.cache[key]

    def _ring_img(self, beat: Beat, lt: float) -> Image.Image:
        v = beat.count_from + (beat.count_to - beat.count_from) * beat.count_p(lt)
        label = beat.text.replace("{n}", f"{round(v):d}")
        key = (id(beat), "r", round(v * 2), label)
        if key not in self.cache:
            col = COLORS.get(beat.accent, beat.accent) if isinstance(beat.accent, str) else tuple(beat.accent)
            lab_col = COLORS.get(beat.color, WHITE) if beat.color else WHITE
            self.cache[key] = render_ring(v, beat.ring_r, col, label, beat.size or 170, lab_col)
        return self.cache[key]

    def _strike(self, canvas: Image.Image, img: Image.Image, x: int, y: int, beat: Beat, lt: float):
        p = min(1.0, (lt - beat.strike_at) / 0.14)
        key = ("strike", id(beat), img.size, int(p * 24))
        if key not in self.cache:
            ss, w, h = 2, img.width, img.height
            layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            x0, y0 = 0.10 * w * ss, 0.66 * h * ss
            x1, y1 = x0 + p * 0.80 * w * ss, y0 - p * 0.30 * h * ss
            t = max(int(h * 0.085), 10) * ss
            for width, col in ((t + 12 * ss, BLACK), (t, RED)):
                d.line([x0, y0, x1, y1], fill=col + (255,), width=width)
                for px, py in ((x0, y0), (x1, y1)):
                    d.ellipse([px - width / 2, py - width / 2, px + width / 2, py + width / 2], fill=col + (255,))
            self.cache[key] = layer.resize((w, h), Image.LANCZOS)
        canvas.alpha_composite(self.cache[key], (max(x, -img.width), y))

    def _text_img(self, beat: Beat, text: str) -> Image.Image:
        key = (id(beat), text)
        if key not in self.cache:
            if beat.image:
                self.cache[key] = render_card(beat.image, beat.card_w)
            else:
                self.cache[key] = render_text(text, beat.style, beat.accent, beat.color, size=beat.size)
            if beat.rotate:
                self.cache[key] = self.cache[key].rotate(beat.rotate, expand=True, resample=Image.BICUBIC)
        return self.cache[key]

    def _place(self, canvas: Image.Image, img: Image.Image, beat: Beat, lt: float, life: float):
        scale, alpha, dy = 1.0, 1.0, 0.0
        anim = beat.enter or beat.anim
        if anim in ("pop", "count", "ring"):
            scale = 0.55 + 0.45 * ease_out_back(lt / 0.28)
            alpha = min(1, lt / 0.08)
        elif anim == "card":                            # Karte springt weich auf
            scale = 0.86 + 0.14 * ease_out_back(lt / 0.26)
            alpha = min(1, lt / 0.1)
        elif anim == "karaoke":                         # kurzer Plopp, wenn ein neuer Untertitel kommt
            scale = 0.82 + 0.18 * ease_out_back(lt / 0.16)
            alpha = min(1, lt / 0.05)
        elif anim == "stamp":
            scale = 2.2 - 1.2 * ease_out_cubic(lt / 0.18)
            alpha = min(1, lt / 0.06)
        elif anim == "slide":
            dy = 140 * (1 - ease_out_cubic(lt / 0.35))
            alpha = min(1, lt / 0.2)
        elif anim == "fade":
            alpha = min(1, lt / 0.35)
        elif anim == "punch":                      # ab Frame 0 voll lesbar, schrumpft mit Ruck auf 100 %
            scale = 1.18 - 0.18 * ease_out_cubic(lt / 0.35)
        if beat.anim == "ring":                         # Ring "landet": kurzer Stoß, wenn die Zahl steht
            cd = beat.count_dur if beat.count_dur else min(1.6, beat.end - beat.t - 0.3)
            if 0 <= lt - cd < 0.3 and beat.count_to != beat.count_from:
                scale *= 1 + 0.09 * (1 - ease_out_cubic((lt - cd) / 0.3))
        # Ausblenden
        out = life - lt
        if beat.exit == "fade" and out < 0.18:
            alpha *= max(out / 0.18, 0)
        if alpha <= 0.01:
            return
        if abs(scale - 1) > 0.01:
            img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
        if alpha < 0.999:
            a = img.getchannel("A").point(lambda v: int(v * alpha))
            img = img.copy()
            img.putalpha(a)
        sx = sy = 0.0
        if beat.shake and lt < 0.35:
            k = beat.shake * (1 - lt / 0.35)
            sx, sy = k * math.sin(lt * 90), k * math.cos(lt * 73)
        x = int(W * beat.x - img.width / 2 + sx)
        y = int(H * beat.y - img.height / 2 + dy + sy)
        canvas.alpha_composite(img, (max(x, -img.width), y))
        if beat.strike_at >= 0 and lt >= beat.strike_at:
            self._strike(canvas, img, x, y, beat, lt)

    def _chrome(self, canvas: Image.Image, t: float):
        if t < self.spec.get("chrome_from", 0):   # Badge/Balken erst nach dem Hook
            return
        d = ImageDraw.Draw(canvas)
        if self.progress:
            y0 = 212
            d.rounded_rectangle([SAFE_LEFT, y0, SAFE_RIGHT, y0 + 10], radius=5, fill=(255, 255, 255, 70))
            xe = SAFE_LEFT + (SAFE_RIGHT - SAFE_LEFT) * min(t / self.duration, 1)
            d.rounded_rectangle([SAFE_LEFT, y0, max(xe, SAFE_LEFT + 10), y0 + 10], radius=5, fill=PINK + (255,))
        if self.badge:
            key = ("badge", self.badge)
            if key not in self.cache:
                self.cache[key] = render_text(self.badge, "label")
            b = self.cache[key]
            canvas.alpha_composite(b, (int(W / 2 - b.width / 2), 238))
        if self.watermark:
            key = ("wm", self.watermark)
            if key not in self.cache:
                wm = render_text(self.watermark, "small", size=46)
                a = wm.getchannel("A").point(lambda v: int(v * 0.75))
                wm.putalpha(a)
                self.cache[key] = wm
            wm = self.cache[key]
            canvas.alpha_composite(wm, (int(W / 2 - wm.width / 2), SAFE_BOTTOM - 10))

    def _scene_img(self, i: int, t: float) -> Image.Image:
        s, e, bg, _ = self.scenes[i]
        if getattr(bg, "animated", False):
            return bg.frame_at(t).convert("RGBA")
        return bg.frame((t - s) / max(e - s, 0.01)).convert("RGBA")

    def frame(self, t: float) -> Image.Image:
        canvas = None
        for i, (s, e, bg, flash) in enumerate(self.scenes):
            if s <= t < e or (i == len(self.scenes) - 1 and t >= s):
                canvas = self._scene_img(i, t)
                fade = self.fades[i]
                if i > 0 and fade > 0 and t - s < fade:
                    # weiche Überblendung: vorherige Szene fährt weiter und blendet aus
                    a = (t - s) / fade
                    a = a * a * (3 - 2 * a)
                    canvas = Image.blend(self._scene_img(i - 1, t), canvas, a)
                flash_amt = max(0.0, 1 - (t - s) / 0.10) if (flash and i > 0) else 0
                break
        if canvas is None:
            # Absicherung gegen Lücken zwischen Szenen: nie ein dunkles Ersatzbild zeigen,
            # sondern die zuletzt begonnene Szene weiterlaufen lassen
            prev = [i for i, sc in enumerate(self.scenes) if sc[0] <= t]
            if prev:
                canvas = self._scene_img(prev[-1], t)
            else:
                canvas = Image.new("RGBA", (W, H), (20, 10, 30, 255))
            flash_amt = 0
        for pt, amt in self.pulses:                     # Zoom-Stoß auf dem Schlag
            dt = t - pt
            if 0 <= dt < 0.3:
                k = 1 + amt * (1 - ease_out_cubic(dt / 0.3))
                cw, ch = W / k, H / k
                canvas = canvas.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        canvas.alpha_composite(self.overlay)
        for b in self.beats:
            if b.t <= t < b.end:
                lt = t - b.t
                if b.anim == "karaoke":
                    self._place(canvas, self._karaoke_img(b, lt), b, lt, b.end - b.t)
                    continue
                if b.anim == "ring":
                    self._place(canvas, self._ring_img(b, lt), b, lt, b.end - b.t)
                    continue
                if b.card:
                    self._place(canvas, self._card_img(b, lt), b, lt, b.end - b.t)
                    continue
                txt = b.text_at(lt)
                if txt or b.image:
                    self._place(canvas, self._text_img(b, txt), b, lt, b.end - b.t)
        self._chrome(canvas, t)
        if flash_amt > 0:
            canvas.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(self.flash_strength * flash_amt))))
        return canvas.convert("RGB")

    def render(self, out_path: str, audio: bool = True):
        out_path = os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        n = int(round(self.duration * self.fps))
        wav = None
        if audio:
            wav = out_path.rsplit(".", 1)[0] + ".sfx.wav"
            events = self.spec.get("sfx") or auto_sfx(self.spec)
            sfxmod.render_track(events, self.duration, wav, music=self.spec.get("music", True), voice=self.spec.get("voice_lines"), music_offset=self.spec.get("music_offset", 0.0), duck=self.spec.get("duck"), music_gain=self.spec.get("music_gain"))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(self.fps), "-i", "-"]
        if wav:
            cmd += ["-i", wav]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart"]
        if wav:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd += [out_path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            proc.stdin.write(self.frame(i / self.fps).tobytes())
            if i % (self.fps * 2) == 0:
                print(f"\r  Frame {i}/{n}", end="", file=sys.stderr, flush=True)
        proc.stdin.close()
        proc.wait()
        print(f"\r  fertig: {out_path}            ", file=sys.stderr)
        if wav and os.path.exists(wav):
            os.remove(wav)
        return out_path

    def remux_audio(self, out_path: str):
        """Nur die Effekt-Tonspur neu erzeugen und ins vorhandene MP4 legen (Bild bleibt)."""
        out_path = os.path.join(ROOT, out_path)
        wav = out_path.rsplit(".", 1)[0] + ".sfx.wav"
        tmp = out_path.rsplit(".", 1)[0] + ".tmp.mp4"
        events = self.spec.get("sfx") or auto_sfx(self.spec)
        sfxmod.render_track(events, self.duration, wav, music=self.spec.get("music", True), voice=self.spec.get("voice_lines"), music_offset=self.spec.get("music_offset", 0.0), duck=self.spec.get("duck"), music_gain=self.spec.get("music_gain"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_path, "-i", wav,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, out_path)
        os.remove(wav)
        return out_path

    def still(self, t: float, out_path: str):
        out_path = os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        self.frame(t).save(out_path, quality=92)
        return out_path


def auto_sfx(spec: dict) -> list[dict]:
    """Standard-Sounddesign (leise & weich): Plopp bei Text, Thump + Glöckchen bei
    großen Zahlen/Stempeln, Riser beim Hochzählen, sanfter Whoosh bei Szenenwechseln."""
    ev = []
    for b in spec["beats"]:
        st = b.get("style", "body")
        if b.get("anim") == "count":
            rise = min(1.6, b["end"] - b["t"] - 0.3)
            ev.append({"t": b["t"], "type": "riser", "len": rise})
            ev.append({"t": b["t"] + rise, "type": "chime"})
        elif st in ("big", "huge"):
            ev.append({"t": b["t"], "type": "hit"})
            ev.append({"t": b["t"], "type": "chime"})
        elif b.get("anim") == "stamp" or st == "stamp":
            ev.append({"t": b["t"], "type": "hit", "gain": 0.8})
        elif st == "label":
            ev.append({"t": b["t"], "type": "tick"})
        elif b.get("anim") != "none":
            ev.append({"t": b["t"], "type": "pop"})
    for sc in spec["scenes"][1:]:
        ev.append({"t": max(sc["start"] - 0.15, 0), "type": "whoosh"})
    return ev


def load_spec(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
