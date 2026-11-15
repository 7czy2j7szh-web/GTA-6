"""Moderatorin aus KI-Videoclips vor Grün: Clips nach Schnittliste abspielen, Grün entfernen, ins Bild setzen.

segments: [{"src": Pfad, "a": Quelle von (s), "b": Quelle bis (s), "t": Start im fertigen Video (s)}]
moves:    [{"t0", "t1", "top", "scale"}]  -> Position/Größe gleitet (z. B. beim Weglaufen: Beine ins Bild holen)
Gleiche Schnittstelle wie die anderen Figuren (side, place).
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def _smooth(q):
    q = min(max(q, 0.0), 1.0)
    return q * q * (3 - 2 * q)


class GreenClip:
    def __init__(self, segments, scale=1.35, top=742, x=540, moves=(), lo=14.0, hi=32.0, sharpen=0.45, fade_out=None):
        self.segs = sorted(segments, key=lambda s: s["t"])
        self.scale0, self.top0, self.x = scale, top, x
        self.moves = sorted(moves, key=lambda m: m["t0"])
        self.lo, self.hi, self.sharpen, self.fade_out = lo, hi, sharpen, fade_out
        self.caps: dict = {}
        self.fps = {}
        for s in self.segs:
            if s["src"] not in self.fps:
                cap = cv2.VideoCapture(s["src"])
                self.fps[s["src"]] = cap.get(cv2.CAP_PROP_FPS) or 24.0
                cap.release()

    def side(self, t):
        return 1.0

    def _read(self, src, idx):
        st = self.caps.get(src)
        if st is None or idx < st["idx"]:
            if st is not None:
                st["cap"].release()
            st = {"cap": cv2.VideoCapture(src), "idx": -1, "frame": None}
            self.caps[src] = st
        while st["idx"] < idx:
            ok, fr = st["cap"].read()
            if not ok:
                break
            st["idx"] += 1
            st["frame"] = fr
        return st["frame"]

    def _key(self, bgr):
        """Grün entfernen – arbeitet auf dem bereits vergrößerten Bild, damit die Kante glatt bleibt."""
        f = bgr.astype(np.float32)
        b, g, r = f[..., 0], f[..., 1], f[..., 2]
        m = np.maximum(r, b)
        key = g - m                                              # Grün-Überschuss
        q = np.clip((key - self.lo) / (self.hi - self.lo), 0, 1)
        core = 1 - q * q * (3 - 2 * q)
        alpha = cv2.erode(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))   # Kante nach innen
        alpha = cv2.GaussianBlur(alpha, (0, 0), 1.3)
        alpha = np.clip((alpha - 0.30) / 0.60, 0, 1)
        g2 = np.minimum(g, m)                                    # Grünstich entfernen
        rgb = np.dstack([r, g2, b])
        # Randpixel: Farbe von weiter innen übernehmen (kein heller Saum)
        solid = (alpha > 0.98).astype(np.float32)
        wsum = cv2.GaussianBlur(solid, (0, 0), 2.6) + 1e-4
        inner = cv2.GaussianBlur(rgb * solid[..., None], (0, 0), 2.6) / wsum[..., None]
        edge = ((alpha < 0.98) & (wsum > 0.05))[..., None]
        rgb = np.where(edge, inner, rgb)
        if self.sharpen:                                         # nur das Innere schärfen
            blur = cv2.GaussianBlur(rgb, (0, 0), 1.2)
            rgb = np.where(solid[..., None] > 0, np.clip(rgb + (rgb - blur) * self.sharpen, 0, 255), rgb)
        # Glas/Glanzlichter retten: Stellen, die heller sind als der grüne Hintergrund dahinter
        h, w = key.shape
        sm = cv2.resize(f, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
        ksm = sm[..., 1] - np.maximum(sm[..., 0], sm[..., 2])
        bgm = (ksm > self.hi).astype(np.float32)
        lum_s = 0.114 * sm[..., 0] + 0.587 * sm[..., 1] + 0.299 * sm[..., 2]
        bw = cv2.GaussianBlur(bgm, (0, 0), 14) + 1e-4
        bg_lum = cv2.resize(cv2.GaussianBlur(lum_s * bgm, (0, 0), 14) / bw, (w, h), interpolation=cv2.INTER_LINEAR)
        lum = 0.114 * b + 0.587 * g + 0.299 * r
        near = cv2.GaussianBlur(cv2.dilate(solid, np.ones((61, 61), np.uint8)), (0, 0), 6)   # nur nahe der Figur
        glass = np.clip((lum - bg_lum - 7) / 34, 0, 1) * (core < 0.5) * near
        glass = cv2.GaussianBlur(glass.astype(np.float32), (0, 0), 0.9) * 0.9
        body = np.clip(cv2.GaussianBlur(glass, (0, 0), 5.0) * 2.4, 0, 0.30)      # zarter Glaskörper um die Glanzlichter
        glass = np.maximum(glass, body * (core < 0.5))
        white = np.clip(np.dstack([m, m, m]) * 1.25 + 30, 0, 255)                             # entfärbtes Glas
        mix = np.clip(glass / np.maximum(alpha + glass, 1e-4), 0, 1)[..., None] * (alpha < 0.5)[..., None]
        rgb = rgb * (1 - mix) + white * mix
        alpha = np.maximum(alpha, glass)
        return np.dstack([rgb, alpha * 255])

    def _params(self, t):
        top, sc = self.top0, self.scale0
        for m in self.moves:
            if t <= m["t0"]:
                break
            q = _smooth((t - m["t0"]) / max(m["t1"] - m["t0"], 1e-3))
            top = top + (m.get("top", top) - top) * q
            sc = sc + (m.get("scale", sc) - sc) * q
        return top, sc

    def place(self, canvas: Image.Image, t: float):
        from .design import paste
        seg = None
        for s in self.segs:
            if s["t"] <= t < s["t"] + (s["b"] - s["a"]):
                seg = s
        if seg is None:
            seg = self.segs[-1] if t >= self.segs[-1]["t"] else None
            if seg is None:
                return
        src_t = min(seg["a"] + (t - seg["t"]), seg["b"] - 1e-3)
        frame = self._read(seg["src"], int(round(src_t * self.fps[seg["src"]])))
        if frame is None:
            return
        top, sc = self._params(t)
        h, w = frame.shape[:2]
        big = cv2.resize(frame, (int(round(w * sc)), int(round(h * sc))), interpolation=cv2.INTER_CUBIC)
        rgba = self._key(big)
        fade = 1.0
        if self.fade_out and t > self.fade_out[0]:
            fade = 1 - _smooth((t - self.fade_out[0]) / max(self.fade_out[1] - self.fade_out[0], 1e-3))
            rgba[..., 3] *= fade
        if fade <= 0.003:
            return
        im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
        paste(canvas, im, self.x - im.width / 2, top)
