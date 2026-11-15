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
    def __init__(self, segments, scale=1.35, top=742, x=540, moves=(), lo=14.0, hi=32.0, sharpen=0.45):
        self.segs = sorted(segments, key=lambda s: s["t"])
        self.scale0, self.top0, self.x = scale, top, x
        self.moves = sorted(moves, key=lambda m: m["t0"])
        self.lo, self.hi, self.sharpen = lo, hi, sharpen
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
        f = bgr.astype(np.float32)
        b, g, r = f[..., 0], f[..., 1], f[..., 2]
        m = np.maximum(r, b)
        key = g - m                                              # Grün-Überschuss
        q = np.clip((key - self.lo) / (self.hi - self.lo), 0, 1)
        alpha = 1 - q * q * (3 - 2 * q)
        alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8))      # Kante 1 px nach innen (kein heller Saum)
        alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
        alpha = np.clip((alpha - 0.35) / 0.55, 0, 1)
        g2 = np.minimum(g, m)                                    # Grünstich aus Kanten/Haaren/Glas nehmen
        # Randpixel: Farbe von weiter innen übernehmen (kein aufgehellter Rand)
        solid = (alpha > 0.98).astype(np.float32)
        wsum = cv2.GaussianBlur(solid, (0, 0), 2.0) + 1e-4
        rgb = np.dstack([r, g2, b])
        inner = cv2.GaussianBlur(rgb * solid[..., None], (0, 0), 2.0) / wsum[..., None]
        edge = ((alpha < 0.98) & (wsum > 0.05))[..., None]
        rgb = np.where(edge, inner, rgb)
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
        rgba = self._key(frame)
        top, sc = self._params(t)
        h, w = rgba.shape[:2]
        big = cv2.resize(rgba, (int(round(w * sc)), int(round(h * sc))), interpolation=cv2.INTER_LANCZOS4)
        if self.sharpen:
            rgb = big[..., :3]
            blur = cv2.GaussianBlur(rgb, (0, 0), 1.2)
            big[..., :3] = np.clip(rgb + (rgb - blur) * self.sharpen, 0, 255)
        im = Image.fromarray(np.clip(big, 0, 255).astype(np.uint8), "RGBA")
        paste(canvas, im, self.x - im.width / 2, top)
