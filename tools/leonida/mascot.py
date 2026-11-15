"""Maskottchen: Bigfoot im Hawaiihemd (eigene Figur, per Programm gezeichnet).

build() zeichnet alle Zustände als deckungsgleiche PNGs (gleiche Pose, gleicher Ausschnitt):
  m0..m3  Mund zu / leicht offen / offen / weit offen (Augen offen)
  blink   Augen zu (Mund zu)
  laugh, surprised, sceptical   Gesichtsausdrücke für Pointen
Puppet setzt daraus pro Frame die Figur zusammen: Mund nach Lautstärke, Blinzeln, Wippen,
Wechsel zwischen groß (Mitte) und klein (unten links, schräg hereinlehnend).
"""
from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "mascot")
W, H, SS = 1200, 1800, 2

FUR = (122, 78, 44)
FUR_D = (84, 52, 28)
FUR_L = (156, 104, 62)
SKIN = (168, 120, 88)
SKIN_D = (140, 96, 68)
MUZZLE = (196, 148, 112)
LINE = (46, 26, 14)
SHIRT = (245, 137, 155)       # Plum-Verlauf: Koralle
SHIRT_D = (214, 98, 130)
LEAF = (75, 47, 84)           # Plum-Karte (dunkel)
FLOWER = (255, 255, 153)
FLOWER2 = (255, 212, 168)
FRAME = (233, 99, 188)
LENS = (34, 22, 44)


def S(v):
    return v * SS


def fur_outline(cx, cy, rx, ry, tufts, depth, seed, a0=0.0, a1=2 * math.pi, steps=900):
    rnd = random.Random(seed)
    amp = [0.6 + 0.8 * rnd.random() for _ in range(tufts + 2)]
    pts = []
    for k in range(steps + 1):
        a = a0 + (a1 - a0) * k / steps
        u = (a - a0) / (2 * math.pi) * tufts
        i = int(u)
        f = u - i
        tri = 1 - abs(f * 2 - 1)                       # Zacke 0..1..0
        r = 1 + depth * (tri ** 1.6 - 0.35) * amp[i % len(amp)]
        pts.append((S(cx + rx * r * math.cos(a)), S(cy + ry * r * math.sin(a))))
    return pts


def poly(d, pts, fill, outline=LINE, width=7):
    d.polygon(pts, fill=fill)
    if outline:
        d.line(pts + [pts[0]], fill=outline, width=S(width), joint="curve")


def ellipse(d, cx, cy, rx, ry, fill, outline=LINE, width=6):
    d.ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)], fill=fill,
              outline=outline, width=S(width) if outline else 0)


def strands(d, cx, cy, rx, ry, n, seed, color=FUR_D, length=28, width=4, skip=None):
    rnd = random.Random(seed)
    for _ in range(n):
        a = rnd.random() * 2 * math.pi
        rr = math.sqrt(rnd.random())
        x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
        if skip and skip(x, y):
            continue
        ang = -math.pi / 2 + (x - cx) / rx * 0.9 + rnd.uniform(-0.25, 0.25)
        L = length * rnd.uniform(0.6, 1.2)
        d.line([S(x), S(y), S(x + L * math.cos(ang) * 0.35), S(y - L * 0.9)], fill=color, width=S(width))


def _body(d):
    # breite, hängende Schultern: Fellmasse unter dem Kopf (kein Hals, typisch Bigfoot)
    poly(d, fur_outline(600, 1060, 500, 300, 44, 0.06, 13), FUR)
    strands(d, 600, 960, 420, 120, 70, 17, length=26, width=5)
    # Hemd mit Ärmeln bis zum Bildrand
    shirt = [(S(-20), S(1800)), (S(-20), S(1230)), (S(60), S(1120)), (S(200), S(1050)), (S(340), S(1000)),
             (S(470), S(980)), (S(600), S(1120)), (S(730), S(980)), (S(860), S(1000)), (S(1000), S(1050)),
             (S(1140), S(1120)), (S(1220), S(1230)), (S(1220), S(1800))]
    poly(d, shirt, SHIRT)
    # Muster: Palmblätter + Hibiskus
    rnd = random.Random(7)
    for _ in range(40):
        x, y = rnd.uniform(40, 1160), rnd.uniform(1080, 1780)
        if abs(x - 600) < 150 and y < 1280:
            continue
        if y < 1030 + abs(x - 600) * 0.12:
            continue
        if rnd.random() < 0.55:                        # Blatt
            ang = rnd.uniform(0, math.pi)
            for k in range(-3, 4):
                a = ang + k * 0.28
                d.line([S(x), S(y), S(x + 70 * math.cos(a)), S(y + 70 * math.sin(a))], fill=LEAF, width=S(13))
        else:                                          # Blüte
            col = FLOWER if rnd.random() < 0.5 else FLOWER2
            for k in range(5):
                a = k * 2 * math.pi / 5
                ellipse(d, x + 26 * math.cos(a), y + 26 * math.sin(a), 22, 22, col, outline=None)
            ellipse(d, x, y, 12, 12, SHIRT_D, outline=None)
    d.line(shirt, fill=LINE, width=S(7), joint="curve")
    # V-Ausschnitt mit Brustfell + Kragen
    v = [(S(470), S(980)), (S(600), S(1270)), (S(730), S(980)), (S(600), S(1000))]
    poly(d, v, FUR)
    strands(d, 600, 1090, 70, 80, 40, 21, length=22, width=4)
    for sx in (-1, 1):
        col = [(S(600 + sx * 135), S(978)), (S(600 + sx * 20), S(1125)), (S(600 + sx * 90), S(1190)),
               (S(600 + sx * 250), S(1012))]
        poly(d, col, SHIRT_D)
    for by in (1300, 1390, 1480, 1570, 1660, 1750):
        ellipse(d, 615, by, 12, 12, FLOWER2, width=4)


def _head(d):
    head = fur_outline(600, 570, 335, 395, 52, 0.05, 5)
    head = [(x, y - S(max(0.0, 100 - abs(x / SS - 600) * 0.5)) * max(0.0, min(1.0, (S(560) - y) / S(260))))
            for x, y in head]                          # Scheitelkamm (Kegelkopf)
    poly(d, head, FUR)
    strands(d, 600, 460, 270, 320, 190, 9, length=30, width=5,
            skip=lambda x, y: (abs(x - 600) < 225 and 470 < y < 870))
    # Wangenbart: hängende Fellzotteln seitlich
    for sx in (-1, 1):
        poly(d, fur_outline(600 + sx * 250, 760, 110, 150, 12, 0.10, 30 + sx, steps=300), FUR)
        strands(d, 600 + sx * 250, 760, 80, 120, 30, 40 + sx, length=26, width=5)
    face = fur_outline(600, 645, 220, 245, 26, 0.03, 8)
    poly(d, face, SKIN, width=6)
    ellipse(d, 600, 745, 160, 112, SKIN_D, outline=None)
    ellipse(d, 600, 738, 150, 104, MUZZLE, outline=None)
    # schwerer Stirnwulst
    poly(d, [(S(395), S(540)), (S(470), S(488)), (S(600), S(500)), (S(730), S(488)), (S(805), S(540)),
             (S(730), S(522)), (S(600), S(532)), (S(470), S(522))], SKIN_D, outline=None)


def _brows(d, mode="normal"):
    # (innen, außen) relative Höhe; negativ = höher
    cfg = {"normal": {-1: (-10, 6), 1: (-10, 6)}, "surprised": {-1: (-52, -36), 1: (-52, -36)},
           "sceptical": {-1: (10, 12), 1: (-44, -30)}, "laugh": {-1: (-16, -2), 1: (-16, -2)}}[mode]
    for sx in (-1, 1):
        di, do = cfg[sx]
        xi, xo = 600 + sx * 28, 600 + sx * 172
        yi, yo = 500 + di, 506 + do
        xm, ym = (xi + xo) / 2, min(yi, yo) - 16
        top = [(xi, yi - 6), (xm, ym), (xo, yo - 2)]
        bot = [(xo, yo + 22), (xm, ym + 34), (xi, yi + 30)]
        poly(d, [(S(x), S(y)) for x, y in top + bot], FUR_D, width=5)


def _eyes(d, mode="open", look=(0, 0)):
    for sx in (-1, 1):
        cx, cy = 600 + sx * 95, 590
        if mode == "closed":
            d.arc([S(cx - 52), S(cy - 30), S(cx + 52), S(cy + 34)], 20, 160, fill=LINE, width=S(9))
            continue
        if mode == "laugh":
            d.arc([S(cx - 52), S(cy - 10), S(cx + 52), S(cy + 60)], 200, 340, fill=LINE, width=S(10))
            continue
        r = 54 if mode == "surprised" else 50
        ellipse(d, cx, cy, r, r + 8, (255, 255, 255), width=6)
        pr = 20 if mode == "surprised" else 27
        px, py = cx + look[0] * 14, cy + 6 + look[1] * 10
        ellipse(d, px, py, pr, pr + 2, (52, 30, 18), outline=None)
        ellipse(d, px, py, pr * 0.55, pr * 0.55, (10, 6, 4), outline=None)
        ellipse(d, px - pr * 0.45, py - pr * 0.5, pr * 0.32, pr * 0.32, (255, 255, 255), outline=None)


def _nose(d):
    pts = [(S(540), S(655)), (S(600), S(628)), (S(660), S(655)), (S(650), S(690)), (S(600), S(704)), (S(550), S(690))]
    poly(d, pts, (58, 34, 22), width=5)
    for sx in (-1, 1):
        ellipse(d, 600 + sx * 26, 682, 12, 9, (20, 10, 6), outline=None)
    ellipse(d, 584, 650, 16, 7, (120, 84, 64), outline=None)


def _mouth_open(im, w, h, cy=770):
    cx = 600
    y0 = cy - h * 0.35
    top = [(cx - w + 2 * w * k / 40, y0 + h * 0.10 * math.sin(math.pi * k / 40)) for k in range(41)]
    bot = [(cx + w * math.cos(math.pi * k / 40), y0 + h * math.sin(math.pi * k / 40) ** 0.9) for k in range(41)]
    shape = [(S(x), S(y)) for x, y in top + bot]
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.polygon(shape, fill=(64, 18, 26))
    if h >= 34:
        ld.ellipse([S(cx - w * 0.58), S(y0 + h * 0.62), S(cx + w * 0.58), S(y0 + h * 1.35)], fill=(226, 96, 112))
    if h >= 26:
        ld.rectangle([S(cx - w * 0.62), S(y0 - 4), S(cx + w * 0.62), S(y0 + max(9, h * 0.2))], fill=(250, 246, 236))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(shape, fill=255)
    im.paste(layer, (0, 0), mask)
    ImageDraw.Draw(im).line(shape + [shape[0]], fill=LINE, width=S(8), joint="curve")


def _mouth(im, d, state):
    cx, cy = 600, 770
    if state == "smirk":
        d.arc([S(cx - 80), S(cy - 60), S(cx + 100), S(cy + 22)], 25, 125, fill=LINE, width=S(11))
        return
    if state == 0:
        d.arc([S(cx - 95), S(cy - 66), S(cx + 95), S(cy + 22)], 28, 152, fill=LINE, width=S(11))
        return
    if state == "o":
        ellipse(d, cx, cy + 10, 44, 54, (64, 18, 26), width=8)
        ellipse(d, cx, cy + 40, 26, 14, (226, 96, 112), outline=None)
        return
    w, h = {1: (78, 24), 2: (92, 48), 3: (104, 76), "laugh": (122, 84)}[state]
    _mouth_open(im, w, h, cy)


def _shades(d):
    # hochgeschobene Sonnenbrille auf der Stirn
    for sx in (-1, 1):
        cx = 600 + sx * 108
        d.rounded_rectangle([S(cx - 92), S(352), S(cx + 92), S(442)], radius=S(40), fill=LENS,
                            outline=FRAME, width=S(12))
        d.line([S(cx - 55), S(372), S(cx - 10), S(372)], fill=(150, 110, 190), width=S(9))
        d.line([S(cx - 60), S(392), S(cx - 35), S(392)], fill=(150, 110, 190), width=S(7))
    d.arc([S(560), S(370), S(640), S(420)], 200, 340, fill=FRAME, width=S(12))
    for sx in (-1, 1):
        d.line([S(600 + sx * 196), S(380), S(600 + sx * 300), S(420)], fill=FRAME, width=S(12))


def draw(eyes="open", mouth=0, brows="normal", look=(0, 0)) -> Image.Image:
    im = Image.new("RGBA", (S(W), S(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _body(d)
    _head(d)
    _brows(d, brows)
    _eyes(d, eyes, look)
    _nose(d)
    _mouth(im, d, mouth)
    _shades(d)
    return im.resize((W, H), Image.LANCZOS)


STATES = {
    "m0": dict(mouth=0), "m1": dict(mouth=1), "m2": dict(mouth=2), "m3": dict(mouth=3),
    "blink": dict(eyes="closed", mouth=0),
    "laugh": dict(eyes="laugh", mouth="laugh", brows="laugh"),
    "surprised": dict(eyes="surprised", mouth="o", brows="surprised"),
    "sceptical": dict(eyes="open", mouth="smirk", brows="sceptical", look=(1, 0)),
}


def build(force=False) -> dict:
    os.makedirs(OUT, exist_ok=True)
    paths = {}
    for name, kw in STATES.items():
        p = os.path.join(OUT, f"bigfoot_{name}.png")
        if force or not os.path.exists(p):
            draw(**kw).save(p)
        paths[name] = p
    return paths


def mouth_levels(wav_path: str, offset: float, n_frames: int, fps: int = 30):
    """Mundstufe 0..3 und Pegel 0..1 je Videoframe aus der Lautstärke der Stimme (wie im Leitfaden)."""
    import wave
    w = wave.open(wav_path)
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // fps
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x), hop)])
    amp = np.clip(rms / (np.percentile(rms, 95) or 1), 0, 1)
    # Silben betonen: weit offen nur an lokalen Spitzen (komprimierte TTS-Stimme ist sonst fast immer "laut")
    loc = np.array([amp[max(0, i - 3):i + 4].max() for i in range(len(amp))])
    score = amp * (0.55 + 0.45 * amp / np.maximum(loc, 1e-6))
    lvl = np.digitize(score, [0.10, 0.40, 0.80])
    for i in range(1, len(lvl) - 1):                   # einzelne Zuck-Frames entfernen
        if lvl[i] != lvl[i - 1] and lvl[i] != lvl[i + 1]:
            lvl[i] = lvl[i - 1]
    mouth, level = np.zeros(n_frames, int), np.zeros(n_frames)
    o = int(round(offset * fps)) - 1                   # Mund 1 Frame vor dem Ton (wirkt synchroner)
    for i in range(len(lvl)):
        if 0 <= i + o < n_frames:
            mouth[i + o], level[i + o] = lvl[i], amp[i]
    return mouth.tolist(), level.tolist()


def _spring(t: float, zeta=0.6, omega=10.0) -> float:
    """Feder 0 -> 1 (Standard: Dämpfung 12, Steifigkeit 100 -> zeta 0,6)."""
    if t <= 0:
        return 0.0
    wd = omega * math.sqrt(1 - zeta ** 2)
    return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + zeta * omega / wd * math.sin(wd * t))


def _smooth(t: float, omega=9.0) -> float:
    """kritisch gedämpft, ohne Überschwingen (für groß <-> klein)."""
    return 0.0 if t <= 0 else 1 - (1 + omega * t) * math.exp(-omega * t)


class Puppet:
    """Setzt die Figur pro Frame zusammen.

    mouth/level: je Frame (aus mouth_levels); poses: [{"pose": "laugh", "from": s, "to": s}];
    to_side/to_centre: Zeiten, an denen die Figur nach unten links bzw. zurück in die Mitte gleitet.
    """

    def __init__(self, mouth, level, poses=None, to_side=(), to_centre=(), enter=0.0, fps=30,
                 big_w=680, small_w=520, top_big=1130, top_small=1250):
        self.img = {k: Image.open(v).convert("RGBA") for k, v in build().items()}
        self.mouth, self.level, self.fps = mouth, level, fps
        self.poses = poses or []
        self.to_side, self.to_centre = list(to_side), list(to_centre)
        self.enter = enter
        self.big_w, self.small_w = big_w, small_w
        self.top_big, self.top_small = top_big, top_small
        rnd = random.Random(4)
        self.blinks, f = [], 60
        while f < 100000:                              # alle ~95 Frames, leicht versetzt, nie in Frame 0
            self.blinks.append(f)
            f += 95 + rnd.randint(-18, 18)
        ch = sorted([p["from"] for p in self.poses] + [p["to"] for p in self.poses])
        self.changes = ch + self.to_side + self.to_centre
        self.cache: dict = {}

    def _scaled(self, name, w, sx=1.0, sy=1.0):
        key = (name, w, round(sx, 3), round(sy, 3))
        if key not in self.cache:
            im = self.img[name]
            h = int(im.height * w / im.width)
            self.cache[key] = im.resize((max(int(w * sx), 4), max(int(h * sy), 4)), Image.LANCZOS)
            if len(self.cache) > 400:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def state(self, t: float) -> str:
        for p in self.poses:
            if p["from"] <= t < p["to"]:
                return p["pose"]
        f = int(round(t * self.fps))
        if any(b <= f < b + 3 for b in self.blinks if b - 3 <= f):
            return "blink"
        m = self.mouth[f] if 0 <= f < len(self.mouth) else 0
        return f"m{m}"

    def side(self, t: float) -> float:
        a = sum(_smooth(t - ts) for ts in self.to_side) - sum(_smooth(t - tc) for tc in self.to_centre)
        return min(max(a, 0.0), 1.0)

    def squash(self, t: float) -> float:
        """0,97 -> 1,025 -> 1 über ~9 Frames nach einem Posenwechsel."""
        k = 1.0
        for c in self.changes:
            dt = t - c
            if 0 <= dt < 0.3:
                k *= 1 - 0.03 * math.exp(-dt * 9) * math.cos(dt * 21)
        return k

    def place(self, canvas: Image.Image, t: float):
        f = int(round(t * self.fps))
        lv = self.level[f] if 0 <= f < len(self.level) else 0.0
        s = self.side(t)
        w = self.big_w + (self.small_w - self.big_w) * s
        sq = self.squash(t)
        sc = 1 + lv * 0.012                            # atmet mit der Lautstärke
        im = self._scaled(self.state(t), int(w * sc) // 2 * 2, 1 / math.sqrt(sq) if sq != 1 else 1.0, sq)
        rot = -15 * s + math.sin(t * 1.1) * 1.0       # klein: lehnt schräg von links herein
        if abs(rot) > 0.05:
            im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        CW, CH = canvas.size
        bob = math.sin(t * math.pi) * 6 + lv * 6
        enter = (1 - _spring(t - self.enter)) * 900 if t < self.enter + 2 else 0.0
        if t < self.enter:
            return
        ratio = self.img["m0"].height / self.img["m0"].width
        h_big, h_small = self.big_w * ratio, self.small_w * ratio
        # groß: mittig, Kopf ab ~y 1130; klein: links herausgeschoben (linke Kante -150), Kopf ab ~y 1250
        cx = (CW / 2) * (1 - s) + (-150 + self.small_w / 2) * s
        top = self.top_big * (1 - s) + self.top_small * s
        cy = top + (h_big * (1 - s) + h_small * s) / 2 + bob + enter
        from .design import paste
        paste(canvas, im, cx - im.width / 2, cy - im.height / 2)


if __name__ == "__main__":
    print(build(force=True))
