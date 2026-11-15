"""Moderatorin als Porträt-Karte (statt gezeichnetem Maskottchen).

Kein Lippen-Sync auf dem Foto (wirkt unecht): Die Karte „spricht“ über ein Neon-Glühen und kleine
Equalizer-Balken, beides gesteuert von der Lautstärke der Stimme. Groß mittig für Einstieg und Schluss,
klein unten links (Bild-im-Bild) dazwischen. Gleiche Schnittstelle wie mascot.Puppet (side, place).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import design as D
from .mascot import _smooth, _spring

RATIO = 1.04            # Höhe/Breite der Karte


class HostCard:
    def __init__(self, img_path: str, level, to_side=(), to_centre=(), enter=0.0, fps=30,
                 big_w=600, small_w=340, top_big=1110, top_small=1250, zoom=(1.0, 1.05), duration=10.0):
        self.level, self.fps = level, fps
        self.to_side, self.to_centre, self.enter = list(to_side), list(to_centre), enter
        self.big_w, self.small_w, self.top_big, self.top_small = big_w, small_w, top_big, top_small
        self.zoom, self.duration = zoom, duration
        src = Image.open(img_path).convert("RGB")
        self.HW = 900                                   # Arbeitsgröße der Karte
        self.HH = int(self.HW * RATIO)
        sw, sh = src.size                               # Quelle auf das Kartenformat zuschneiden (mittig oben)
        tw = min(sw, int(sh / RATIO))
        th = int(tw * RATIO)
        self.src = src.crop(((sw - tw) // 2, 0, (sw - tw) // 2 + tw, th)).resize(
            (int(self.HW * zoom[1]) + 4, int(self.HH * zoom[1]) + 4), Image.LANCZOS)
        r = 54
        self.mask = Image.new("L", (self.HW, self.HH), 0)
        ImageDraw.Draw(self.mask).rounded_rectangle([0, 0, self.HW - 1, self.HH - 1], radius=r, fill=255)
        P = 70
        self.P = P
        ring = Image.new("L", (self.HW + 2 * P, self.HH + 2 * P), 0)
        dr = ImageDraw.Draw(ring)
        dr.rounded_rectangle([P - 9, P - 9, P + self.HW + 8, P + self.HH + 8], radius=r + 9, fill=255)
        dr.rounded_rectangle([P, P, P + self.HW - 1, P + self.HH - 1], radius=r, fill=0)
        grad = D._gradient(ring.size, D.GLOW, horizontal=True).convert("RGBA")
        self.border = grad.copy()
        self.border.putalpha(ring)
        self.halo = grad.copy()
        self.halo.putalpha(ring.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(26)))
        sh_m = Image.new("L", ring.size, 0)
        ImageDraw.Draw(sh_m).rounded_rectangle([P, P + 18, P + self.HW, P + self.HH + 18], radius=r, fill=170)
        self.shadow = Image.merge("RGBA", (*[Image.new("L", ring.size, v) for v in D.SHADOW],
                                           sh_m.filter(ImageFilter.GaussianBlur(30))))
        # Pegel geglättet (Glühen soll atmen, nicht flackern)
        lv = np.array(level, dtype=float)
        sm = np.zeros_like(lv)
        acc = 0.0
        for i, v in enumerate(lv):
            acc = acc + (v - acc) * (0.55 if v > acc else 0.18)
            sm[i] = acc
        self.lv = sm

    def side(self, t: float) -> float:
        a = sum(_smooth(t - ts) for ts in self.to_side) - sum(_smooth(t - tc) for tc in self.to_centre)
        return min(max(a, 0.0), 1.0)

    def _card(self, t: float, lvl: float) -> Image.Image:
        q = min(max(t / max(self.duration, 0.1), 0.0), 1.0)
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * q
        w, h = int(self.HW * z), int(self.HH * z)
        photo = self.src.resize((w, h), Image.BILINEAR) if (w, h) != self.src.size else self.src
        x0, y0 = (w - self.HW) // 2, int((h - self.HH) * 0.25)
        photo = photo.crop((x0, y0, x0 + self.HW, y0 + self.HH))
        P = self.P
        out = Image.new("RGBA", (self.HW + 2 * P, self.HH + 2 * P), (0, 0, 0, 0))
        out.alpha_composite(self.shadow)
        halo = self.halo.copy()
        halo.putalpha(halo.getchannel("A").point(lambda v: int(v * (0.35 + 0.65 * lvl))))
        out.alpha_composite(halo)
        ph = photo.convert("RGBA")
        ph.putalpha(self.mask)
        out.alpha_composite(ph, (P, P))
        # Equalizer-Balken unten rechts (spricht gerade)
        d = ImageDraw.Draw(out)
        bx, by = P + self.HW - 150, P + self.HH - 46
        d.rounded_rectangle([bx - 22, by - 78, bx + 112, by + 18], radius=30, fill=(*D.GROUND, 150))
        for k in range(4):
            amp = lvl * (0.55 + 0.45 * math.sin(t * (9 + 3 * k) + k * 1.7) ** 2)
            hh = 12 + 52 * amp
            x = bx + k * 26
            d.rounded_rectangle([x, by - hh, x + 14, by], radius=7, fill=(*D.ACCENT, 255))
        out.alpha_composite(self.border)
        return out

    def place(self, canvas: Image.Image, t: float):
        if t < self.enter:
            return
        f = int(round(t * self.fps))
        lvl = float(self.lv[f]) if 0 <= f < len(self.lv) else 0.0
        s = self.side(t)
        w = self.big_w + (self.small_w - self.big_w) * s
        w *= 1 + 0.012 * lvl
        card = self._card(t, lvl)
        k = w / self.HW
        im = card.resize((int(card.width * k), int(card.height * k)), Image.LANCZOS)
        rot = -3.0 * s
        if abs(rot) > 0.05:
            im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        CW, CH = canvas.size
        h = w * RATIO
        cx = (CW / 2) * (1 - s) + (70 + self.small_w / 2) * s
        top = self.top_big * (1 - s) + self.top_small * s
        bob = math.sin(t * math.pi) * 5
        enter = (1 - _spring(t - self.enter)) * 900 if t < self.enter + 2 else 0.0
        cy = top + h / 2 + bob + enter
        D.paste(canvas, im, cx - im.width / 2, cy - im.height / 2)
