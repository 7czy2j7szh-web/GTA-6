"""„Neon Drive": selbst animierter Synthwave-Hintergrund (komplett eigene Grafik).

Nachtfahrt auf einer Neon-Straße Richtung Sonnenuntergang: Sternenhimmel,
gestreifte Sonne, Skyline-Silhouette, Neon-Bodenraster, Palmen, die exakt im
Beat vorbeifliegen, und ein generischer Sportwagen von hinten.
Gerendert in halber Auflösung (Neon-Look verträgt die Weichheit) und hochskaliert.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

PINK = (255, 45, 149)
ORANGE = (255, 138, 0)
TEAL = (0, 209, 193)


class NeonDrive:
    animated = True

    def __init__(self, W=1080, H=1920, bpm=118, scale=0.5, car=True, seed=3, horizon=0.47):
        self.W, self.H = W, H
        self.w, self.h = int(W * scale), int(H * scale)
        self.cx = self.w / 2
        self.beat = 60 / bpm
        self.bar = 4 * self.beat
        self.hy = int(self.h * horizon)
        self.f = self.h - self.hy                       # z = 1 -> unterer Bildrand (Kamerahöhe 1)
        self.road = 0.62                                # halbe Straßenbreite (Welt)
        self.S = 10.0                                   # Palmenabstand je Seite
        self.v = self.S / (2 * self.beat)               # -> auf jedem Beat fliegt eine Palme vorbei
        self.rng = np.random.default_rng(seed)
        self.base = self._static_scene()
        self.palm = self._palm_sprite()
        self.car = self._car_sprite() if car else None
        n = 140
        self.stars = np.stack([self.rng.random(n) * self.w, self.rng.random(n) * self.hy * 0.8,
                               self.rng.random(n) * 6.28, 0.5 + self.rng.random(n) * 1.5], axis=1)

    # ------------------------------------------------------------ statische Teile
    def _static_scene(self) -> Image.Image:
        w, h, hy = self.w, self.h, self.hy
        y = np.arange(h)[:, None].astype(float)
        sky_stops = [(0.0, (10, 3, 30)), (0.45, (45, 8, 75)), (0.80, (150, 25, 120)), (1.0, (255, 95, 120))]
        img = np.zeros((h, w, 3))
        t = np.clip(y / hy, 0, 1)
        for c in range(3):
            xs = [s for s, _ in sky_stops]
            ys = [col[c] for _, col in sky_stops]
            img[:hy, :, c] = np.interp(t[:hy], xs, ys) * np.ones((1, w))
        # Boden: dunkles Violett mit leichtem Verlauf
        g = np.clip((y[hy:] - hy) / (h - hy), 0, 1)
        for c, (a, b) in enumerate(((40, 8), (8, 2), (60, 18))):
            img[hy:, :, c] = (a + (b - a) * g) * np.ones((1, w))
        base = Image.fromarray(img.astype(np.uint8))

        # Sonne (gestreift), hinter der Skyline
        sun_r = int(w * 0.30)
        sun = Image.new("RGBA", (2 * sun_r, 2 * sun_r), (0, 0, 0, 0))
        yy, xx = np.mgrid[0:2 * sun_r, 0:2 * sun_r]
        d = np.sqrt((xx - sun_r) ** 2 + (yy - sun_r) ** 2)
        k = yy / (2 * sun_r)
        col = np.stack([np.full_like(k, 255), 220 - 170 * k, 90 + 60 * k], -1)
        alpha = (d < sun_r).astype(float)
        stripes = (yy > sun_r * 0.95) & (np.sin((yy - sun_r) * 0.11 * (1 + k)) > 0.55)
        alpha[stripes] = 0
        sun_arr = np.dstack([col, alpha * 255]).astype(np.uint8)
        sun = Image.fromarray(sun_arr, "RGBA")
        m = 80                                                  # Rand, damit das Leuchten nicht eckig abgeschnitten wird
        glow = Image.new("RGBA", (2 * sun_r + 2 * m, 2 * sun_r + 2 * m), (0, 0, 0, 0))
        glow.paste(sun, (m, m), sun)
        glow = glow.filter(ImageFilter.GaussianBlur(30))
        sx, sy = int(self.cx - sun_r), hy - int(sun_r * 1.55)
        base.paste(glow, (sx - m, sy - m), glow)
        base.paste(sun, (sx, sy), sun)

        # Skyline-Silhouette mit beleuchteten Fenstern
        sky = ImageDraw.Draw(base)
        x = -10
        while x < w + 10:
            bw = int(self.rng.integers(18, 46))
            bh = int(self.rng.integers(25, 150) * (1.3 if abs(x - self.cx) > w * 0.25 else 0.8))
            sky.rectangle([x, hy - bh, x + bw, hy], fill=(22, 6, 38))
            for wy in range(hy - bh + 6, hy - 4, 7):
                for wx in range(x + 4, x + bw - 3, 6):
                    if self.rng.random() < 0.28:
                        c = [(255, 200, 120), (255, 90, 180), (90, 230, 220)][int(self.rng.integers(0, 3))]
                        sky.rectangle([wx, wy, wx + 1, wy + 2], fill=c)
            x += bw + int(self.rng.integers(-4, 4))
        sky.line([(0, hy), (w, hy)], fill=PINK, width=2)
        return base

    def _palm_sprite(self) -> Image.Image:
        """Palmen-Silhouette: leicht gebogener Stamm, gewölbte, gezackte Wedel, pinker Randschein."""
        S = 700
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        dark = (14, 4, 26, 255)
        # Stamm: fast senkrecht, nach oben dünner, leicht gebogen
        n = 24
        base_x, base_y, top_y = S * 0.50, S - 2, S * 0.42
        pts = []
        for i in range(n + 1):
            u = i / n
            pts.append((base_x + 30 * math.sin(u * 1.4), base_y - u * (base_y - top_y)))
        for i in range(n):
            d.line([pts[i], pts[i + 1]], fill=dark, width=int(30 - 14 * i / n))
        top = pts[-1]

        def bez(p0, p1, p2, u):
            return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1])

        # Wedel: gewölbter Bogen nach außen und unten, gezackte Kanten
        for ang, L in ((-178, 250), (-150, 270), (-118, 220), (-62, 220), (-30, 270), (-2, 250),
                       (-200, 200), (20, 200), (-90, 150)):
            a = math.radians(ang)
            dx, dy = math.cos(a), math.sin(a)
            p0 = top
            p1 = (top[0] + dx * L * 0.55, top[1] + dy * L * 0.55 - L * 0.30)
            p2 = (top[0] + dx * L, top[1] + dy * L * 0.2 + L * 0.42)
            left, right = [], []
            steps = 28
            for i in range(steps + 1):
                u = i / steps
                x, y = bez(p0, p1, p2, u)
                x2, y2 = bez(p0, p1, p2, min(1, u + 0.01))
                tx, ty = x2 - x, y2 - y
                norm = math.hypot(tx, ty) or 1
                nx, ny = -ty / norm, tx / norm
                wdt = 26 * math.sin(math.pi * min(u * 1.1, 1)) ** 0.8
                wdt *= 1.0 if i % 2 == 0 else 0.45          # gezackte Blattkante
                left.append((x + nx * wdt, y + ny * wdt))
                right.append((x - nx * wdt * 0.6, y - ny * wdt * 0.6))
            d.polygon(left + right[::-1], fill=dark)
        # pinker Randschein
        edge = im.filter(ImageFilter.MaxFilter(5))
        a = edge.split()[3]
        rim = Image.merge("RGBA", (Image.new("L", im.size, 255), Image.new("L", im.size, 60),
                                   Image.new("L", im.size, 170), a.point(lambda v: int(v * 0.75))))
        rim.alpha_composite(im)
        return rim

    def _car_sprite(self) -> Image.Image:
        Wc, Hc = 520, 200
        im = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        body = [(20, 150), (40, 95), (110, 80), (165, 30), (355, 30), (410, 80), (480, 95), (500, 150), (490, 175), (30, 175)]
        d.polygon(body, fill=(12, 4, 22, 255))
        d.polygon([(175, 40), (345, 40), (390, 82), (130, 82)], fill=(40, 10, 70, 255))   # Heckscheibe
        d.line(body + [body[0]], fill=PINK + (255,), width=4)
        for x0 in (50, 400):                                                                   # Räder
            d.rounded_rectangle([x0, 160, x0 + 70, 198], radius=8, fill=(5, 2, 10, 255))
        glow = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle([60, 102, 460, 122], radius=8, fill=(255, 30, 60, 255))           # Rücklicht-Leiste
        glow_b = glow.filter(ImageFilter.GaussianBlur(12))
        out = Image.new("RGBA", (Wc, Hc + 40), (0, 0, 0, 0))
        out.alpha_composite(glow_b, (0, 0))
        out.alpha_composite(im, (0, 0))
        out.alpha_composite(glow, (0, 0))
        return out

    # ------------------------------------------------------------ pro Frame
    def _project(self, X, z):
        return self.cx + self.f * X / z, self.hy + self.f / z

    def frame_at(self, t: float) -> Image.Image:
        w, h = self.w, self.h
        img = self.base.copy()
        dist = self.v * t
        beat_ph = (t % self.beat) / self.beat
        pulse = math.exp(-beat_ph * 5)                       # Puls auf jedem Beat
        bar_in_cycle = int(t // self.bar) % 4
        riser = (bar_in_cycle == 3) * ((t % self.bar) / self.bar)
        crash = math.exp(-(t % (4 * self.bar)) * 3.5)       # Schlag am Anfang jedes 4-Takt-Blocks

        d = ImageDraw.Draw(img)
        # Sterne
        for sx, sy, ph, sp in self.stars:
            b = int(140 + 110 * math.sin(t * sp * 2 + ph))
            d.point((sx, sy), fill=(b, b, min(255, b + 40)))

        neon = Image.new("RGB", (w, h), (0, 0, 0))
        nd = ImageDraw.Draw(neon)
        far = 60.0
        inten = 0.55 + 0.45 * pulse + 0.4 * riser + 0.6 * crash
        # Längslinien des Rasters
        for k in range(-14, 15):
            X = k * 0.9
            if abs(X) < self.road:
                continue
            x1, y1 = self._project(X, 1.0)
            x2, y2 = self._project(X, far)
            c = tuple(int(v * min(1, inten * 0.8)) for v in (200, 40, 160))
            nd.line([(x1, y1), (x2, y2)], fill=c, width=2)
        # Querlinien (bewegen sich auf die Kamera zu)
        G = 2.5
        z = G - (dist % G)
        while z < far:
            if z > 0.9:
                y = self.hy + self.f / z
                a = min(1.0, 2.0 / z) * inten
                c = tuple(int(v * min(1, a)) for v in (230, 50, 180))
                nd.line([(0, y), (w, y)], fill=c, width=max(1, int(3 / max(z, 1) + 1)))
            z += G
        # Straße
        xl1, yb = self._project(-self.road, 1.0)
        xr1, _ = self._project(self.road, 1.0)
        xl2, yf = self._project(-self.road, far)
        xr2, _ = self._project(self.road, far)
        d.polygon([(xl1, yb), (xr1, yb), (xr2, yf), (xl2, yf)], fill=(16, 4, 28))
        ec = tuple(int(v * min(1, 0.7 + 0.5 * pulse + 0.5 * crash)) for v in PINK)
        nd.line([(xl1, yb), (xl2, yf)], fill=ec, width=4)
        nd.line([(xr1, yb), (xr2, yf)], fill=ec, width=4)
        # Mittelstreifen
        D = 4.0
        z = D - (dist % D)
        while z < far:
            z2 = z + 1.6
            if z > 0.6:
                x1, y1 = self._project(0, z)
                x2, y2 = self._project(0, z2)
                nd.line([(x1, y1), (x2, y2)], fill=(255, 200, 120), width=max(1, int(8 / z)))
            z += D

        glow = neon.filter(ImageFilter.GaussianBlur(5))
        img = ImageChops.add(img, glow)
        img = ImageChops.add(img, neon)

        # Palmen (hinten nach vorne zeichnen)
        palms = []
        for side, off in ((-1, 0.0), (1, self.S / 2)):
            n0 = math.floor((dist - off) / self.S)
            for n in range(n0, n0 + 8):
                zr = n * self.S + off - dist + 0.6
                if 0.45 < zr < far:
                    palms.append((zr, side))
        for zr, side in sorted(palms, reverse=True):
            X = side * (self.road + 0.75)
            px, py = self._project(X, zr)
            ph = self.f * 3.0 / zr
            if ph < 4:
                continue
            sp = self.palm.resize((max(1, int(ph)), max(1, int(ph))), Image.BILINEAR)
            if side > 0:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            img.paste(sp, (int(px - ph / 2), int(py - ph)), sp)

        # Auto
        if self.car is not None:
            cw = int(w * 0.52)
            ch = int(self.car.height * cw / self.car.width)
            car = self.car.resize((cw, ch), Image.BILINEAR)
            bob = int(2 * math.sin(2 * math.pi * t / self.beat))
            img.paste(car, (int(self.cx - cw / 2), int(h * 0.80) + bob), car)

        out = img.resize((self.W, self.H), Image.BICUBIC)
        if crash > 0.05:                                     # leichte Kamera-Erschütterung beim Crash
            dx = int(10 * crash * math.sin(t * 90))
            dy = int(8 * crash * math.cos(t * 70))
            out = ImageChops.offset(out, dx, dy)
        return out
