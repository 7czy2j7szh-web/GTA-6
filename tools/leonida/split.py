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
    def __init__(self, W: int, H: int, top: dict, bottom: dict, dur: float, reveal: float, t0: float = 0.0):
        self.W, self.H, self.h2 = W, H, H // 2
        self.dur, self.reveal, self.t0 = dur, reveal, t0
        self.rays = bottom.get("rays")
        if self.rays:                                      # Strahlenkranz (z. B. Gold für einen Schatz)
            import numpy as np
            yy, xx = np.mgrid[0:self.h2, 0:W].astype(np.float32)
            cx, cy = W / 2, self.h2 * 0.52
            self._ang = np.arctan2(yy - cy, xx - cx)
            self._rad = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (W * 0.75)
        if "clip" in top:
            from .clip import VideoClip
            self.top = VideoClip(top["clip"], W, self.h2, ss=top.get("ss", 0.0), dur=dur, cam=top.get("cam"))
        else:
            from .drone import DroneShot
            self.top = DroneShot(top["drone"], W, self.h2, cam=top.get("cam"))
        if self.rays:
            return
        src = Image.open(os.path.join(ROOT, bottom["image"])).convert("RGB")
        scale = max(W * 1.6 / src.width, self.h2 * 1.6 / src.height)
        if scale < 1:                                       # nur verkleinern, nie hochskalieren
            src = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS)
        self.src = src
        self.b = dict(zoom=[1.0, 1.08], x=[0.5, 0.5], y=[0.5, 0.5]); self.b.update(bottom)

    def _bottom(self, q: float) -> Image.Image:
        L = lambda a: a[0] + (a[1] - a[0]) * q
        z = L(self.b["zoom"]); sw, sh = self.src.size
        cover = min(sw / self.W, sh / self.h2)
        cw, ch = self.W * cover / z, self.h2 * cover / z
        cx = min(max(L(self.b["x"]) * sw, cw / 2), sw - cw / 2)
        cy = min(max(L(self.b["y"]) * sh, ch / 2), sh - ch / 2)
        return self.src.resize((self.W, self.h2), Image.LANCZOS, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

    def _rays(self, t: float) -> Image.Image:
        import numpy as np
        r = self.rays
        c1 = np.array(r.get("c1", [255, 196, 40]), np.float32)     # Strahl
        c2 = np.array(r.get("c2", [70, 20, 90]), np.float32)       # Hintergrund
        n = r.get("n", 14)
        a = (np.sin(self._ang * n + (self.t0 + t) * r.get("speed", 0.6)) + 1) / 2
        a = np.clip(a ** 3, 0, 1) * np.clip(1.15 - self._rad, 0, 1)
        glow = np.clip(1 - self._rad * 1.6, 0, 1) ** 2
        img = c2 * (1 - a[..., None] * 0.55) + c1 * a[..., None] * 0.55 + np.array([255, 220, 120]) * glow[..., None] * 0.45
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

    def frame(self, p: float) -> Image.Image:
        t = max(p, 0.0) * self.dur
        q = min(max(p, 0.0), 1.2)
        top = self.top.frame(p).convert("RGB")
        bot = self._rays(t) if self.rays else self._bottom(q)
        a = min(max((t - self.reveal) / 0.35, 0.0), 1.0)
        if a < 1.0 and not self.rays:                 # verschwommen + dunkel bis zur Auflösung
            blur = bot.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.55))
            bot = Image.blend(blur, bot, a * a * (3 - 2 * a))
        out = Image.new("RGB", (self.W, self.H))
        out.paste(top, (0, 0)); out.paste(bot, (0, self.h2))
        ImageDraw.Draw(out).rectangle([0, self.h2 - 3, self.W, self.h2 + 3], fill=PINK)
        return out
