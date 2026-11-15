"""Geteiltes Vergleichsbild (9:16): oben GTA 6 (Trailer-Clip oder Screenshot), unten ein echtes Foto.

Das Foto ist bis zur Auflösung stark verschwommen und abgedunkelt und wird dann in 0,35 s scharf.
scene: {"image": "split:", "top": {"clip": pfad, "ss": s, "cam": {...}} | {"drone": pfad, "cam": {...}},
        "bottom": {"image": pfad, "zoom": [a, b], "x": [a, b], "y": [a, b]}, "reveal": Sekunden (relativ)}
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PINK = (255, 45, 149)


class SplitScene:
    def __init__(self, W: int, H: int, top: dict, bottom: dict, dur: float, reveal: float):
        self.W, self.H, self.h2 = W, H, H // 2
        self.dur, self.reveal = dur, reveal
        if "clip" in top:
            from .clip import VideoClip
            self.top = VideoClip(top["clip"], W, self.h2, ss=top.get("ss", 0.0), dur=dur, cam=top.get("cam"))
        else:
            from .drone import DroneShot
            self.top = DroneShot(top["drone"], W, self.h2, cam=top.get("cam"))
        src = Image.open(os.path.join(ROOT, bottom["image"])).convert("RGB")
        scale = max(W * 1.25 / src.width, self.h2 * 1.25 / src.height)
        self.src = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS)
        self.b = dict(zoom=[1.0, 1.08], x=[0.5, 0.5], y=[0.5, 0.5]); self.b.update(bottom)

    def _bottom(self, q: float) -> Image.Image:
        L = lambda a: a[0] + (a[1] - a[0]) * q
        z = L(self.b["zoom"]); sw, sh = self.src.size
        cover = min(sw / self.W, sh / self.h2)
        cw, ch = self.W * cover / z, self.h2 * cover / z
        cx = min(max(L(self.b["x"]) * sw, cw / 2), sw - cw / 2)
        cy = min(max(L(self.b["y"]) * sh, ch / 2), sh - ch / 2)
        return self.src.resize((self.W, self.h2), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

    def frame(self, p: float) -> Image.Image:
        t = max(p, 0.0) * self.dur
        q = min(max(p, 0.0), 1.2)
        top = self.top.frame(p).convert("RGB")
        bot = self._bottom(q)
        a = min(max((t - self.reveal) / 0.35, 0.0), 1.0)
        if a < 1.0:                                   # verschwommen + dunkel bis zur Auflösung
            blur = bot.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.55))
            bot = Image.blend(blur, bot, a * a * (3 - 2 * a))
        out = Image.new("RGB", (self.W, self.H))
        out.paste(top, (0, 0)); out.paste(bot, (0, self.h2))
        ImageDraw.Draw(out).rectangle([0, self.h2 - 3, self.W, self.h2 + 3], fill=PINK)
        return out
