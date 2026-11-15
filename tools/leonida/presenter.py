"""Freigestellte Moderatorin als 2D-Puppe (aus einem einzigen Foto).

Ebenen: Körper (Arme herausgerechnet und dahinter aufgefüllt), Unterarm mit Glas, hängender Arm.
Bewegungen per Rückwärts-Abbildung (cv2.remap, Lanczos) in 1,4-facher Auflösung, dann sauber verkleinert:
  - Mund öffnet sich nach Lautstärke (8 Stufen, Unterlippe + Kinn gleiten nach unten, Mundraum dunkel)
  - Blinzeln (Lid aus der Haut darüber gestreckt, Wimpernlinie)
  - Kopf: Nicken/Neigen beim Sprechen; Körper: Atmen + leichtes Wiegen
  - Gesten: "glass" (Glas anheben), "arm" (Arm zur Seite heben), "lean" (nach vorne lehnen), "nod"
Koordinaten unten beziehen sich auf das Originalfoto (1438 x 2576).
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np
from PIL import Image

PADL, PADR, PADT = 220, 300, 160

MOUTH = dict(cx=741, gate0=645, gate1=649, chin=705, neck=765, half_w=36, fall_w=74, line=646)
EYES = [dict(cx=666, cy=482, rx=31, ry=11, tilt=0.0), dict(cx=810, cy=480, rx=36, ry=11, tilt=-7.0)]
HEAD_PIVOT, HEAD_Y0, HEAD_Y1 = (735, 800), 735, 860
ANCHOR = (720, 2576)                       # unten Mitte (Bildkante = Oberschenkel)

FOREARM = [(305, 1345), (360, 1325), (430, 1300), (470, 1255), (540, 1210), (575, 1150), (566, 1093), (862, 1093),
           (852, 1122), (762, 1236), (728, 1290), (778, 1298), (795, 1342), (775, 1362), (802, 1386), (792, 1412),
           (738, 1430), (742, 1494), (808, 1504), (812, 1532), (700, 1548), (608, 1532), (612, 1500), (688, 1488),
           (692, 1440), (620, 1432), (520, 1432), (450, 1462), (390, 1492), (330, 1522), (282, 1560), (252, 1600),
           (236, 1655), (262, 1520)]
FOREARM_PIVOT = (200, 1560)
ARM = [(1018, 1002), (1122, 958), (1127, 1050), (1137, 1200), (1152, 1350), (1167, 1500), (1187, 1650), (1212, 1800),
       (1237, 1950), (1257, 2100), (1277, 2200), (1302, 2290), (1314, 2385), (1284, 2448), (1232, 2446), (1212, 2382),
       (1222, 2322), (1198, 2282), (1193, 2200), (1188, 2050), (1178, 1900), (1148, 1750), (1113, 1652), (1093, 1522),
       (1078, 1402), (1063, 1252), (1048, 1102)]
ARM_PIVOT = (1068, 985)


def _env(t, t0, dur, a=0.35, r=0.45):
    """Hüllkurve einer Geste: weich hoch, halten, weich runter."""
    if t < t0 or t > t0 + dur:
        return 0.0
    x = t - t0
    up = min(1.0, x / a)
    down = min(1.0, (t0 + dur - t) / r)
    e = min(up, down)
    return e * e * (3 - 2 * e)


class Presenter:
    def __init__(self, cut_path, level, fps=30, display_h=1130, gestures=(), seed=3, rs=1.4):
        self.fps, self.gestures = fps, list(gestures)
        src = np.asarray(Image.open(cut_path).convert("RGBA")).astype(np.float32)
        H0, W0 = src.shape[:2]
        self.H0, self.W0 = H0, W0
        canvas = np.zeros((H0 + PADT, W0 + PADL + PADR, 4), np.float32)
        canvas[PADT:, PADL:PADL + W0] = src
        self.CH, self.CW = canvas.shape[:2]
        self.k_disp = display_h / H0                     # Anzeige-Maßstab (Bildhöhe Foto -> Pixel im Video)
        self.k = self.k_disp * rs                        # Arbeits-Maßstab (überabgetastet)
        off = np.array([PADL, PADT], np.float32)

        def poly_mask(pts, feather=2.5):
            m = np.zeros((self.CH, self.CW), np.uint8)
            cv2.fillPoly(m, [np.int32(np.array(pts) + off)], 255)
            m = m.astype(np.float32) / 255
            return cv2.GaussianBlur(m, (0, 0), feather)

        alpha = canvas[..., 3] / 255

        def hard(pts, grow=5):
            m = np.zeros((self.CH, self.CW), np.uint8)
            cv2.fillPoly(m, [np.int32(np.array(pts) + off)], 255)
            return cv2.dilate(m, np.ones((2 * grow + 1, 2 * grow + 1), np.uint8))

        hf = hard(FOREARM, grow=4)
        core = cv2.erode(hf, np.ones((7, 7), np.uint8)) > 0       # 3 px innerhalb des Rands
        fa = cv2.GaussianBlur(hf.astype(np.float32) / 255, (0, 0), 1.0) * alpha
        yy, xx = np.mgrid[0:self.CH, 0:self.CW].astype(np.float32)
        y0, x0 = yy - PADT, xx - PADL
        near_f = ((x0 - FOREARM_PIVOT[0]) ** 2 + (y0 - FOREARM_PIVOT[1]) ** 2) < 140 ** 2
        behind_f = (x0 > 345) | near_f | (y0 < 1470)                # Torso bzw. Oberarm hinter dem Unterarm
        body_alpha = alpha.copy()
        body_alpha[core & ~behind_f] = 0
        rgb = canvas[..., :3].astype(np.uint8)
        filled = cv2.inpaint(rgb, core.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
        body = np.dstack([filled.astype(np.float32), body_alpha * 255])
        farm = np.dstack([canvas[..., :3], fa * 255])
        harm = None
        # Gesichts-Varianten (Mund 0..7 x Lid offen/halb/zu) in voller Auflösung, dann verkleinert
        self.face_box = (600 + PADL, 430 + PADT, 900 + PADL, 790 + PADT)
        bx0, by0, bx1, by1 = self.face_box
        base_face = body[by0:by1, bx0:bx1].copy()
        self.faces = {}
        for m in range(8):
            fm = self._mouth(base_face, m * 2.0, bx0 - PADL, by0 - PADT)
            for b, c in (("o", 0.0), ("h", 0.55), ("c", 1.0)):
                self.faces[(m, b)] = self._scale(self._blink(fm, c, bx0 - PADL, by0 - PADT))
        self.body = self._scale(body)
        self.farm = self._scale(farm)
        self.fb = tuple(int(round(v * self.k)) for v in self.face_box)
        # Lautstärke -> geglättete Mundöffnung
        lv = np.array(level, dtype=float)
        sm, acc = np.zeros_like(lv), 0.0
        for i, v in enumerate(lv):
            tgt = np.clip((v - 0.08) / 0.75, 0, 1)
            acc += (tgt - acc) * (0.7 if tgt > acc else 0.35)
            sm[i] = acc
        self.open = sm
        slow, acc = np.zeros_like(lv), 0.0
        for i, v in enumerate(lv):
            acc += (v - acc) * 0.05
            slow[i] = acc
        self.slow = slow
        rnd = np.random.RandomState(seed)
        self.blinks, f = [], 50
        while f < 100000:
            self.blinks.append(f)
            f += int(rnd.randint(80, 125))
        h, w = self.body.shape[:2]
        self.gy, self.gx = np.mgrid[0:h, 0:w].astype(np.float32)

    # ---------- Vorberechnung ----------
    def _scale(self, img):
        h, w = img.shape[:2]
        out = cv2.resize(img, (int(round(w * self.k)), int(round(h * self.k))), interpolation=cv2.INTER_AREA)
        return out

    @staticmethod
    def _mouth(face, d, ox, oy):
        """Unterlippe + Kinn um d Pixel (Originalmaß) nach unten; Spalt wird dunkler Mundraum (folgt der Lippenlinie)."""
        if d <= 0:
            return face.copy()
        M = MOUTH
        h, w = face.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        Y, X = yy + oy, xx + ox
        u = (X - M["cx"]) / 64.0                               # Lippenlinie: Mitte tiefer, Mundwinkel höher
        yl = 645.0 - np.where(u > 0, 13.0, 8.0) * u * u
        g = np.clip((Y - yl - 6) / 3, 0, 1)
        g *= np.clip(1 - (Y - M["chin"]) / (M["neck"] - M["chin"]), 0, 1)
        dx = np.abs(X - M["cx"])
        hw = np.clip(1 - (dx - M["half_w"]) / (M["fall_w"] - M["half_w"]), 0, 1)
        Wt = g * (hw * hw * (3 - 2 * hw))
        out = cv2.remap(face, xx, (yy - d * Wt).astype(np.float32), cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
        taper = np.clip(1 - (dx / 60.0) ** 2, 0, 1) ** 0.6
        hgt = np.maximum(d * taper, 1e-3)
        rel = (Y - (yl + 2)) / (hgt + 4.0)
        cav = np.clip(rel * 3, 0, 1) * np.clip((1 - rel) * 3, 0, 1) * (taper > 0.05)
        cav = cv2.GaussianBlur(cav.astype(np.float32), (0, 0), 0.9)
        col = np.array([62, 26, 32], np.float32)
        out[..., :3] = out[..., :3] * (1 - 0.85 * cav[..., None]) + col * 0.85 * cav[..., None]
        return out

    @staticmethod
    def _blink(face, c, ox, oy):
        if c <= 0:
            return face
        out = face.copy()
        h, w = face.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        for e in EYES:
            cx, cy, rx, ry = e["cx"] - ox, e["cy"] - oy, e["rx"], e["ry"]
            top = cy - ry - 3
            edge = top + (2 * ry + 5) * c                          # Lidkante
            m = np.zeros((h, w), np.float32)
            cv2.ellipse(m, (int(cx), int(cy)), (int(rx + 1), int(ry + 3)), e["tilt"], 0, 360, 1.0, -1)
            m *= np.clip((edge - yy) / 1.5 + 0.5, 0, 1)
            m = cv2.GaussianBlur(m, (0, 0), 1.3)
            # Lidhaut: Haut unter dem Auge gespiegelt (echte Struktur), leicht abgedunkelt
            src_y = (cy + ry + 7) + (edge - yy) * 0.9
            lid = cv2.remap(face, xx, src_y.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)[..., :3]
            lid = lid * 0.8
            out[..., :3] = out[..., :3] * (1 - m[..., None]) + lid * m[..., None]
            lash = np.zeros((h, w), np.float32)
            cv2.ellipse(lash, (int(cx), int(round(edge - ry * 0.35))), (int(rx), int(ry * 0.4)), e["tilt"], 20, 160,
                        1.0, 2)
            lash = cv2.GaussianBlur(lash, (0, 0), 0.8) * min(1.0, c * 1.3)
            out[..., :3] = out[..., :3] * (1 - 0.75 * lash[..., None]) + np.array([34, 22, 22], np.float32) * 0.75 * lash[..., None]
        return out

    # ---------- pro Frame ----------
    def _gest(self, t, kind):
        return max([_env(t, g["t"], g["dur"]) * g.get("amount", 1.0) for g in self.gestures if g["type"] == kind] or [0.0])

    def _blink_state(self, f):
        for b in self.blinks:
            if b <= f < b + 5:
                return ["h", "c", "c", "h", "h"][f - b] if f - b < 5 else "o"
            if b > f:
                break
        return "o"

    def render(self, t: float) -> Image.Image:
        """RGBA-Bild der Figur in Anzeige-Größe (Breite/Höhe = Leinwand * k_disp)."""
        f = int(round(t * self.fps))
        op = float(self.open[f]) if 0 <= f < len(self.open) else 0.0
        slow = float(self.slow[f]) if 0 <= f < len(self.slow) else 0.0
        m = int(round(op * 7))
        face = self.faces[(m, self._blink_state(f))]
        body = self.body.copy()
        x0, y0, x1, y1 = self.fb
        fh, fw = face.shape[:2]
        body[y0:y0 + fh, x0:x0 + fw] = face
        k = self.k
        # Gesten-Stärken
        g_glass, g_arm, g_lean, g_nod = (self._gest(t, n) for n in ("glass", "arm", "lean", "nod"))
        # Körper: Atmen, Wiegen, nach vorne lehnen (um Unterkante Mitte)
        breath = 1 + 0.0035 * math.sin(t * 2 * math.pi / 3.6)
        sway = 0.45 * math.sin(t * 2 * math.pi / 6.5) + 0.25 * math.sin(t * 2 * math.pi / 2.9 + 1)
        lean = 1 + 0.045 * g_lean
        ax, ay = (ANCHOR[0] + PADL) * k, (ANCHOR[1] + PADT) * k
        # Kopf: Neigen/Nicken (beim Sprechen lebhafter)
        head_rot = 1.6 * math.sin(t * 0.9) + 1.4 * slow * math.sin(t * 3.1) - 1.5 * g_glass
        head_nod = (2.0 * slow * max(0.0, math.sin(t * 4.3)) + 7.0 * g_nod + 5.0 * g_lean) * k   # px nach unten
        hx, hy = (HEAD_PIVOT[0] + PADL) * k, (HEAD_PIVOT[1] + PADT) * k
        out = np.zeros_like(body)
        layers = [(body, None), (self.farm, ("forearm", -7.0 * g_glass))]
        # inverse Körpertransformation: p -> Koordinaten vor Wiegen/Lehnen/Atmen
        th = math.radians(-sway)
        X, Y = self.gx - ax, self.gy - ay
        cs, sn = math.cos(th), math.sin(th)
        Xb = (X * cs - Y * sn) / lean + ax
        Yb = (X * sn + Y * cs) / (lean * breath) + ay
        for img, limb in layers:
            mx, my = Xb.copy(), Yb.copy()
            if limb is None:
                # Kopf (gewichtet): Rotation um den Hals + Nicken
                wy = np.clip(1 - ((my / k - PADT) - HEAD_Y0) / (HEAD_Y1 - HEAD_Y0), 0, 1)
                wy = wy * wy * (3 - 2 * wy)
                a = math.radians(-head_rot)
                dx, dy = mx - hx, my - hy - head_nod
                rx = dx * math.cos(a) - dy * math.sin(a) + hx
                ry = dx * math.sin(a) + dy * math.cos(a) + hy
                mx = mx + wy * (rx - mx)
                my = my + wy * (ry - my)
            else:
                name, ang = limb
                if abs(ang) < 0.01:
                    pass
                else:
                    px, py = (np.array(ARM_PIVOT if name == "arm" else FOREARM_PIVOT) + [PADL, PADT]) * k
                    a = math.radians(ang)
                    dx, dy = mx - px, my - py
                    mx = dx * math.cos(a) - dy * math.sin(a) + px
                    my = dx * math.sin(a) + dy * math.cos(a) + py
            warped = cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            a_ = np.clip(warped[..., 3:4] / 255, 0, 1)
            out[..., :3] = out[..., :3] * (1 - a_) + warped[..., :3] * a_
            out[..., 3:4] = out[..., 3:4] * (1 - a_) + 255 * a_
        h, w = out.shape[:2]
        disp = cv2.resize(np.clip(out, 0, 255), (int(round(w / 1.4)), int(round(h / 1.4))), interpolation=cv2.INTER_AREA)
        return Image.fromarray(disp.astype(np.uint8), "RGBA")

    def anchor_display(self):
        """Position der Unterkante-Mitte im Anzeige-Bild (für das Platzieren)."""
        return (ANCHOR[0] + PADL) * self.k_disp, (ANCHOR[1] + PADT) * self.k_disp


class PresenterPlacer:
    """Stellt die Figur ins Video (unten, Unterkante leicht unter dem Bildrand) mit weichem Schatten."""

    def __init__(self, cut_path, level, fps, x=640, bottom=1950, display_h=1130, gestures=(), enter=0.0):
        self.p = Presenter(cut_path, level, fps=fps, display_h=display_h, gestures=gestures)
        self.x, self.bottom, self.enter = x, bottom, enter

    def side(self, t):
        return 1.0                                       # Untertitel in normaler Höhe

    def place(self, canvas: Image.Image, t: float):
        from .design import paste, SHADOW
        from PIL import ImageFilter
        if t < self.enter:
            return
        im = self.p.render(t)
        axd, ayd = self.p.anchor_display()
        rise = 0.0
        if t < self.enter + 0.6:                         # Auftritt: gleitet von unten herein
            q = (t - self.enter) / 0.6
            rise = (1 - (1 - (1 - q) ** 3)) * 0 + (1 - q) ** 3 * 500
        x, y = self.x - axd, self.bottom - ayd + rise
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
        sh = Image.merge("RGBA", (*[Image.new("L", im.size, v) for v in SHADOW], a))
        paste(canvas, sh, x + 10, y + 14)
        paste(canvas, im, x, y)
