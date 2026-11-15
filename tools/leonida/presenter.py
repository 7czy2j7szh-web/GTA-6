"""Moderatorin als 2D-Puppe aus drei freigestellten Ansichten (vorne, Profil, hinten).

Vorne (stehend): Mund nach Lautstärke (8 Stufen), Blinzeln, Kopf nicken/neigen/schauen, Atmen/Wiegen,
  Arm mit Glas anheben, freier Unterarm hebt sich zum Zeigen/Präsentieren (Gelenk am Ellbogen).
Profil: seitliches Laufen (gespiegelt für die andere Richtung), Schritt-Wippen.
Hinten: dreht sich um und schaut auf die Szene.
Die Bühne (Stage) setzt alles nach einer Aktionsliste zusammen: gehen, umdrehen, Gesten.
Alle Bewegungen werden in 1,4-facher Auflösung gerechnet (Lanczos) und dann verkleinert -> scharf.
Koordinaten beziehen sich auf die jeweiligen Originalbilder.
"""
from __future__ import annotations

import math

import cv2
import numpy as np
from PIL import Image, ImageFilter

RS = 1.4
PADL, PADR, PADT = 220, 640, 160

MOUTH = dict(cx=741, gate0=645, gate1=649, chin=705, neck=765, half_w=36, fall_w=74, line=646)
EYES = [dict(cx=666, cy=482, rx=31, ry=11, tilt=0.0), dict(cx=810, cy=480, rx=36, ry=11, tilt=-7.0)]
HEAD_PIVOT, HEAD_Y0, HEAD_Y1 = (735, 800), 735, 860
FACE_C, FACE_R = (738, 560), (150, 190)
ANCHOR = (720, 2576)                       # unten Mitte (Bildkante = Oberschenkel)
HEAD_TOP = (735, 175)

FOREARM = [(305, 1345), (360, 1325), (430, 1300), (470, 1255), (540, 1210), (575, 1150), (566, 1093), (862, 1093),
           (852, 1122), (762, 1236), (728, 1290), (778, 1298), (795, 1342), (775, 1362), (802, 1386), (792, 1412),
           (738, 1430), (742, 1494), (808, 1504), (812, 1532), (700, 1548), (608, 1532), (612, 1500), (688, 1488),
           (692, 1440), (620, 1432), (520, 1432), (450, 1462), (390, 1492), (330, 1522), (282, 1560), (252, 1600),
           (236, 1655), (262, 1520)]
FOREARM_PIVOT = (200, 1560)
# freier (hängender) Arm: Ellbogen-Gelenk + Trennlinien zum Rock (dort lag ein dunkler Saum vom Hintergrund)
ELBOW, ELBOW_R, ELBOW_Y = (1134, 1600), 112, 1600
SKIRT_CUT = [(1062, 1700), (1090, 1756), (1100, 1772), (1107, 1790), (1113, 1810), (1122, 1830), (1136, 1836),
             (1139, 1850), (1134, 1862), (1142, 1886), (1153, 1900), (1166, 1950), (1173, 1978), (1182, 2010),
             (1190, 2050), (1192, 2090), (1191, 2150), (1190, 2200), (1185, 2250), (1181, 2272)]
ARM_SEED = (1190, 1800)


def _env(t, t0, dur, a=0.3, r=0.4):
    """Hüllkurve einer Geste: weich hoch, halten, weich runter."""
    if t < t0 or t > t0 + dur:
        return 0.0
    e = min(1.0, (t - t0) / a, (t0 + dur - t) / r)
    return e * e * (3 - 2 * e)


def _smooth(q):
    q = min(max(q, 0.0), 1.0)
    return q * q * (3 - 2 * q)


class FrontRig:
    def __init__(self, cut_path, level, fps=30, k_disp=0.427, seed=3):
        self.fps = fps
        src = np.asarray(Image.open(cut_path).convert("RGBA")).astype(np.float32)
        H0, W0 = src.shape[:2]
        canvas = np.zeros((H0 + PADT, W0 + PADL + PADR, 4), np.float32)
        canvas[PADT:, PADL:PADL + W0] = src
        self.CH, self.CW = canvas.shape[:2]
        self.k_disp, self.k = k_disp, k_disp * RS
        off = np.array([PADL, PADT], np.float32)
        alpha = canvas[..., 3] / 255
        yy, xx = np.mgrid[0:self.CH, 0:self.CW].astype(np.float32)
        y0, x0 = yy - PADT, xx - PADL

        # --- Unterarm mit Glas (vor dem Körper) ---
        hf = np.zeros((self.CH, self.CW), np.uint8)
        cv2.fillPoly(hf, [np.int32(np.array(FOREARM) + off)], 255)
        hf = cv2.dilate(hf, np.ones((9, 9), np.uint8))
        core = cv2.erode(hf, np.ones((7, 7), np.uint8)) > 0
        fa = cv2.GaussianBlur(hf.astype(np.float32) / 255, (0, 0), 1.0) * alpha
        near_f = ((x0 - FOREARM_PIVOT[0]) ** 2 + (y0 - FOREARM_PIVOT[1]) ** 2) < 200 ** 2
        behind_f = (x0 > 345) | near_f | (y0 < 1470)
        body_alpha = alpha.copy()
        body_alpha[core & ~behind_f] = 0
        rgb = canvas[..., :3].astype(np.uint8)
        filled = cv2.inpaint(rgb, core.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32)

        # --- freier Unterarm + Hand: zusammenhängendes Stück unterhalb des Ellbogens ---
        cut = np.zeros((self.CH, self.CW), np.uint8)
        cv2.polylines(cut, [np.int32(np.array(SKIRT_CUT) + off)], False, 255, 7)
        seam = cut > 0                                        # dunkler Saum zwischen Arm und Rock -> entfernen
        split = np.zeros((self.CH, self.CW), np.uint8)
        cv2.line(split, (1000 + PADL, ELBOW_Y + PADT), (1300 + PADL, ELBOW_Y + PADT), 255, 3)
        solid = ((alpha > 0.5) & ~seam & (split == 0)).astype(np.uint8)
        _, lab = cv2.connectedComponents(solid, connectivity=4)
        arm = lab == lab[ARM_SEED[1] + PADT, ARM_SEED[0] + PADL]
        arm = cv2.dilate(arm.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0     # weiche Kante mitnehmen
        arm &= (y0 > ELBOW_Y - 2) & (x0 > 1040) & ~seam
        r_el = np.sqrt((x0 - ELBOW[0]) ** 2 + (y0 - ELBOW[1]) ** 2)
        disc = np.clip((ELBOW_R - r_el) / 14.0, 0, 1)                             # weiches Gelenk
        in_arm_col = (x0 > 1023) & (y0 > 1470)
        la = alpha * np.maximum(arm.astype(np.float32), disc * in_arm_col * (y0 <= ELBOW_Y + 1))
        la[seam & (y0 > 1690)] = 0
        body_alpha = body_alpha * np.where(arm, disc, 1.0)                        # Körper behält den runden Stumpf
        body_alpha[seam & (y0 > 1690) & (x0 > 1040)] = 0
        self.arm_px = int(arm.sum())

        body = np.dstack([filled, body_alpha * 255])
        farm = np.dstack([canvas[..., :3], fa * 255])
        larm = np.dstack([canvas[..., :3], la * 255])
        # Gesichts-Varianten (Mund 0..7 x Lid offen/halb/zu) in voller Auflösung, dann verkleinert
        self.face_box = (600 + PADL, 430 + PADT, 900 + PADL, 790 + PADT)
        bx0, by0, bx1, by1 = self.face_box
        base_face = body[by0:by1, bx0:bx1].copy()
        self.faces = {}
        for m in range(8):
            fm = self._mouth(base_face, m * 2.0, bx0 - PADL, by0 - PADT)
            for b, c in (("o", 0.0), ("h", 0.55), ("c", 1.0)):
                self.faces[(m, b)] = self._scale(self._blink(fm, c, bx0 - PADL, by0 - PADT))
        self.body, self.farm, self.larm = self._scale(body), self._scale(farm), self._scale(larm)
        self.fb = tuple(int(round(v * self.k)) for v in self.face_box)
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
        self.size = (int(round(w / RS)), int(round(h / RS)))
        self.head = ((HEAD_TOP[0] + PADL) * k_disp, (HEAD_TOP[1] + PADT) * k_disp)

    def _scale(self, img):
        h, w = img.shape[:2]
        return cv2.resize(img, (int(round(w * self.k)), int(round(h * self.k))), interpolation=cv2.INTER_AREA)

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

    def _blink_state(self, f):
        for b in self.blinks:
            if b <= f < b + 5:
                return ["h", "c", "c", "h", "h"][f - b]
            if b > f:
                break
        return "o"

    def render(self, t: float, pose: dict) -> Image.Image:
        """pose: glass, arm (0..1 Unterarm heben), lean, nod, yaw, pitch (je -1..1 bzw. 0..1)."""
        f = int(round(t * self.fps))
        op = float(self.open[f]) if 0 <= f < len(self.open) else 0.0
        slow = float(self.slow[f]) if 0 <= f < len(self.slow) else 0.0
        face = self.faces[(int(round(op * 7)), self._blink_state(f))]
        body = self.body.copy()
        x0, y0, _, _ = self.fb
        fh, fw = face.shape[:2]
        body[y0:y0 + fh, x0:x0 + fw] = face
        k = self.k
        g_glass, g_arm, g_lean, g_nod = (pose.get(n, 0.0) for n in ("glass", "arm", "lean", "nod"))
        yaw, pitch = pose.get("yaw", 0.0), pose.get("pitch", 0.0)
        breath = 1 + 0.0035 * math.sin(t * 2 * math.pi / 3.6)
        sway = 0.5 * math.sin(t * 2 * math.pi / 6.5) + 0.3 * math.sin(t * 2 * math.pi / 2.9 + 1) + pose.get("sway", 0.0)
        lean = 1 + 0.05 * g_lean
        ax, ay = (ANCHOR[0] + PADL) * k, (ANCHOR[1] + PADT) * k
        head_rot = 1.6 * math.sin(t * 0.9) + 1.6 * slow * math.sin(t * 3.1) - 1.5 * g_glass + 3.0 * yaw - 2.5 * g_arm
        head_nod = (2.2 * slow * max(0.0, math.sin(t * 4.3)) + 8.0 * g_nod + 5.0 * g_lean + 6.0 * pitch) * k
        hx, hy = (HEAD_PIVOT[0] + PADL) * k, (HEAD_PIVOT[1] + PADT) * k
        th = math.radians(-sway)
        X, Y = self.gx - ax, self.gy - ay
        cs, sn = math.cos(th), math.sin(th)
        Xb = (X * cs - Y * sn) / lean + ax
        Yb = (X * sn + Y * cs) / (lean * breath) + ay
        out = np.zeros_like(body)
        layers = [(body, None, 0.0), (self.larm, ELBOW, -150.0 * g_arm), (self.farm, FOREARM_PIVOT, -7.0 * g_glass)]
        for img, pivot, ang in layers:
            mx, my = Xb, Yb
            if pivot is None:
                wy = np.clip(1 - ((my / k - PADT) - HEAD_Y0) / (HEAD_Y1 - HEAD_Y0), 0, 1)
                wy = wy * wy * (3 - 2 * wy)
                a = math.radians(-head_rot)
                dx, dy = mx - hx, my - hy - head_nod
                rx = dx * math.cos(a) - dy * math.sin(a) + hx
                ry = dx * math.sin(a) + dy * math.cos(a) + hy
                mx = mx + wy * (rx - mx)
                my = my + wy * (ry - my)
                if abs(yaw) > 0.01 or abs(pitch) > 0.01:              # Blickrichtung: Gesichtszüge leicht verschieben
                    fx, fy = (FACE_C[0] + PADL) * k, (FACE_C[1] + PADT) * k
                    q = ((mx - fx) / (FACE_R[0] * k)) ** 2 + ((my - fy) / (FACE_R[1] * k)) ** 2
                    wf = np.clip(1 - q, 0, 1) ** 2
                    mx = mx - yaw * 11 * k * wf
                    my = my - pitch * 7 * k * wf
            elif abs(ang) > 0.01:
                px, py = (pivot[0] + PADL) * k, (pivot[1] + PADT) * k
                a = math.radians(-ang)
                dx, dy = mx - px, my - py
                mx = dx * math.cos(a) - dy * math.sin(a) + px
                my = dx * math.sin(a) + dy * math.cos(a) + py
            warped = cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LANCZOS4,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            a_ = np.clip(warped[..., 3:4] / 255, 0, 1)
            out[..., :3] = out[..., :3] * (1 - a_) + warped[..., :3] * a_
            out[..., 3:4] = out[..., 3:4] * (1 - a_) + 255 * a_
        disp = cv2.resize(np.clip(out, 0, 255), self.size, interpolation=cv2.INTER_AREA)
        return Image.fromarray(disp.astype(np.uint8), "RGBA")


class Sprite:
    """Starre Ansicht (Profil/Rücken) mit Wippen, Wiegen und leichtem Nicken."""

    def __init__(self, cut_path, k_disp, head_top, pivot, crop=None, mirror=False):
        im = Image.open(cut_path).convert("RGBA")
        if crop:
            im = im.crop(crop)
            head_top = (head_top[0] - crop[0], head_top[1] - crop[1])
            pivot = (pivot[0] - crop[0], pivot[1] - crop[1])
        a = np.asarray(im).astype(np.float32)
        pad = 80
        c = np.zeros((a.shape[0] + 2 * pad, a.shape[1] + 2 * pad, 4), np.float32)
        c[pad:-pad, pad:-pad] = a
        self.k_disp, self.k = k_disp, k_disp * RS
        h, w = c.shape[:2]
        self.img = cv2.resize(c, (int(round(w * self.k)), int(round(h * self.k))), interpolation=cv2.INTER_AREA)
        self.head = ((head_top[0] + pad) * k_disp, (head_top[1] + pad) * k_disp)
        self.pivot = ((pivot[0] + pad) * self.k, (pivot[1] + pad) * self.k)
        h2, w2 = self.img.shape[:2]
        self.size = (int(round(w2 / RS)), int(round(h2 / RS)))

    def render(self, rot=0.0, flip=False) -> tuple[Image.Image, tuple]:
        h, w = self.img.shape[:2]
        M = cv2.getRotationMatrix2D(self.pivot, -rot, 1.0)
        out = cv2.warpAffine(self.img, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        disp = cv2.resize(np.clip(out, 0, 255), self.size, interpolation=cv2.INTER_AREA).astype(np.uint8)
        head = self.head
        if flip:
            disp = disp[:, ::-1].copy()
            head = (self.size[0] - head[0], head[1])
        return Image.fromarray(disp, "RGBA"), head


class Stage:
    """Bühne: spielt eine Aktionsliste ab und stellt die Figur ins Video.

    actions: {"t", "walk": x_ziel, "speed"}  -> dreht sich ins Profil, läuft, dreht sich zurück
             {"t", "turn": "back", "dur"}    -> dreht sich um, schaut auf die Szene, dreht sich zurück
             {"t", "gesture": "glass"|"point"|"present"|"lean"|"nod"|"hop", "dur", "amount"}
             {"t", "look": [yaw, pitch], "dur"}   yaw: -1 links .. 1 rechts, pitch: -1 hoch .. 1 runter
    """
    TURN = 0.22

    def __init__(self, paths: dict, level, fps, actions, x0=600, head_y=925, k_front=0.427, zoom_side=1.22,
                 zoom_back=1.12):
        self.fps, self.level = fps, level
        self.front = FrontRig(paths["front"], level, fps=fps, k_disp=k_front)
        self.k_front = k_front
        self.sidev = Sprite(paths["side"], k_front * 1.41 * zoom_side, head_top=(300, 424), pivot=(250, 1560))
        self.backv = Sprite(paths["back"], k_front * 1.04 * zoom_back, head_top=(930, 64), pivot=(880, 1560))
        self.head_y = {"front": head_y, "side": head_y + 100, "back": head_y + 20}
        self.x0 = x0
        self.acts = sorted(actions, key=lambda a: a["t"])
        # Lauf-/Dreh-Abschnitte vorberechnen
        self.segs, x = [], x0
        for a in self.acts:
            if "walk" in a:
                d = abs(a["walk"] - x) / a.get("speed", 300.0)
                self.segs.append(dict(kind="walk", t0=a["t"], t1=a["t"] + self.TURN, t2=a["t"] + self.TURN + d,
                                      t3=a["t"] + 2 * self.TURN + d, xa=x, xb=a["walk"], enter=a.get("enter", False)))
                x = a["walk"]
            elif "turn" in a:
                self.segs.append(dict(kind="turn", t0=a["t"], t1=a["t"] + self.TURN, t2=a["t"] + self.TURN + a["dur"],
                                      t3=a["t"] + 2 * self.TURN + a["dur"], xa=x, xb=x))
        lv = np.array(level, dtype=float)
        sl, acc = np.zeros_like(lv), 0.0
        for i, v in enumerate(lv):
            acc += (v - acc) * 0.12
            sl[i] = acc
        self.lv = sl

    def side(self, t):
        return 1.0

    def _gest(self, t, kind):
        return max([_env(t, a["t"], a["dur"]) * a.get("amount", 1.0) for a in self.acts if a.get("gesture") == kind]
                   or [0.0])

    def _state(self, t):
        """-> (ansicht, x, stauchung 0..1, übergangsanteil zur anderen Ansicht, richtung, laufanteil, laufzeit)"""
        x = self.x0
        for s in self.segs:
            if t >= s["t3"]:
                x = s["xb"]
                continue
            if t < s["t0"]:
                break
            other = "side" if s["kind"] == "walk" else "back"
            direction = 1 if s["xb"] >= s["xa"] else -1
            if s["kind"] == "walk" and s.get("enter") and t < s["t1"]:
                return other, s["xa"], 1.0, 1.0, direction, 0.0, 0.0     # kommt direkt im Profil herein
            if t < s["t1"]:                                    # eindrehen
                q = (t - s["t0"]) / self.TURN
                return ("front" if q < 0.5 else other), s["xa"], abs(math.cos(math.pi * q)) * 0.75 + 0.25, _smooth(q), \
                    direction, 0.0, 0.0
            if t < s["t2"]:                                    # laufen / Rücken zeigen
                q = (t - s["t1"]) / max(s["t2"] - s["t1"], 1e-3)
                e = q if s["kind"] == "turn" else (0.5 - 0.5 * math.cos(math.pi * q)) * 0.35 + q * 0.65
                return other, s["xa"] + (s["xb"] - s["xa"]) * e, 1.0, 1.0, direction, \
                    (1.0 if s["kind"] == "walk" else 0.0), t - s["t1"]
            q = (t - s["t2"]) / self.TURN                      # zurückdrehen
            return (other if q < 0.5 else "front"), s["xb"], abs(math.cos(math.pi * q)) * 0.75 + 0.25, 1 - _smooth(q), \
                direction, 0.0, 0.0
        return "front", x, 1.0, 0.0, 1, 0.0, 0.0

    def place(self, canvas: Image.Image, t: float):
        from .design import paste, SHADOW
        view, x, squash, mix, direction, walking, wt = self._state(t)
        f = int(round(t * self.fps))
        lv = float(self.lv[f]) if 0 <= f < len(self.lv) else 0.0
        hop = self._gest(t, "hop")
        dy = -26 * math.sin(math.pi * min(hop * 1.0, 1.0)) if hop > 0 else 0.0
        if view == "front":
            look = [a for a in self.acts if "look" in a]
            yaw = sum(_env(t, a["t"], a["dur"]) * a["look"][0] for a in look)
            pitch = sum(_env(t, a["t"], a["dur"]) * a["look"][1] for a in look)
            g_point, g_pres = self._gest(t, "point"), self._gest(t, "present")
            pose = dict(glass=self._gest(t, "glass"), arm=max(g_point, 0.55 * g_pres), lean=self._gest(t, "lean"),
                        nod=self._gest(t, "nod"), yaw=yaw - 0.4 * g_point, pitch=pitch - 0.6 * g_point)
            im, head = self.front.render(t, pose), self.front.head
            zoom = 1 + 0.10 * pose["lean"]
            if zoom != 1.0:
                im = im.resize((int(im.width * zoom), int(im.height * zoom)), Image.LANCZOS)
                head = (head[0] * zoom, head[1] * zoom)
                dy += 30 * pose["lean"]
        else:
            sp = self.sidev if view == "side" else self.backv
            step = 2.15                                         # Schritte pro Sekunde
            bob = -abs(math.sin(math.pi * step * wt)) * 11 * walking
            rock = math.sin(math.pi * step * wt) * 1.3 * walking
            rot = rock + (2.2 * walking if view == "side" else 0.0) + lv * 0.8 + 0.6 * math.sin(t * 1.7)
            im, head = sp.render(rot=rot, flip=(view == "side" and direction < 0))
            dy += bob + 2.5 * math.sin(t * 2 * math.pi / 3.6)
        if squash < 0.999:
            w2 = max(int(im.width * squash), 2)
            im = im.resize((w2, im.height), Image.LANCZOS)
            head = (head[0] * squash, head[1])
        other = "front" if view != "front" else ("side" if any(s["kind"] == "walk" and s["t0"] <= t < s["t3"]
                                                               for s in self.segs) else "back")
        m = mix if view == "front" else mix                     # Kopfhöhe gleitet zwischen den Ansichten
        hy_a, hy_b = self.head_y["front"], self.head_y[other if view == "front" else view]
        hy = hy_a + (hy_b - hy_a) * m
        px, py = x - head[0], hy + dy - head[1]
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.5))
        sh = Image.merge("RGBA", (*[Image.new("L", im.size, v) for v in SHADOW], a))
        paste(canvas, sh, px + 10, py + 14)
        paste(canvas, im, px, py)
