"""3D-Kamerafahrt durch echte GTA-6-Screenshots (2.5D-Parallax).

1. Ein Tiefen-Modell (MiDaS small, ONNX) schätzt pro Pixel, was vorne/hinten ist.
2. Pro Frame wird ein 9:16-Ausschnitt aus dem 4K-Screenshot genommen; die Kamera
   schwenkt/zoomt, und Vordergrund bewegt sich stärker als Hintergrund.
3. Rendering mit cv2.remap in voller Auflösung (1080x1920) – keine Pixelstufen.
"""
from __future__ import annotations

import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL = os.path.join(ROOT, "models", "midas_small.onnx")
DEPTH_DIR = os.path.join(ROOT, "assets", "official", "depth")
_session = None


def _midas():
    global _session
    if _session is None:
        import onnxruntime as ort
        _session = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    return _session


def depth_map(path: str) -> np.ndarray:
    """Normierte Tiefe 0 (fern) … 1 (nah) in Bildauflösung, gecacht als .npy."""
    os.makedirs(DEPTH_DIR, exist_ok=True)
    cache = os.path.join(DEPTH_DIR, os.path.basename(path) + ".npy")
    img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    if os.path.exists(cache):
        d = np.load(cache)
    else:
        sess = _midas()
        x = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        x = x.transpose(2, 0, 1)[None].astype(np.float32)
        out = sess.run(None, {sess.get_inputs()[0].name: x})[0].squeeze()
        lo, hi = np.percentile(out, 2), np.percentile(out, 98)
        d = np.clip((out - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)
        np.save(cache, d)
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
    d = cv2.GaussianBlur(d, (0, 0), sigmaX=w / 220)            # weiche Tiefe -> keine Risse
    d = cv2.dilate(d, np.ones((9, 9), np.uint8))               # Vordergrund minimal verbreitern
    return np.clip(d, 0, 1)


class ParallaxShot:
    """Eine Kamerafahrt durch einen Screenshot.

    cam: x/y = Mittelpunkt des Ausschnitts (0..1) am Anfang/Ende,
         zoom = Zoom am Anfang/Ende (1 = volle Bildhöhe),
         par = seitliche Kamerabewegung (Pixel im Quellbild bei Tiefe 1) Anfang/Ende,
         dolly = Vordergrund wächst beim Reinfahren stärker (Tiefenwirkung).
    """

    def __init__(self, path: str, W=1080, H=1920, cam: dict | None = None, focus: float = 0.35):
        full = os.path.join(ROOT, path)
        self.src = cv2.cvtColor(cv2.imread(full), cv2.COLOR_BGR2RGB)
        self.depth = depth_map(full)
        self.sh, self.sw = self.src.shape[:2]
        self.W, self.H = W, H
        c = dict(x=[0.5, 0.5], y=[0.5, 0.5], zoom=[1.0, 1.1], par=[-30, 30], dolly=0.05)
        c.update(cam or {})
        self.c = c
        self.focus = focus
        u, v = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        self.u, self.v = u - W / 2, v - H / 2

    @staticmethod
    def _lerp(a, p):
        return a[0] + (a[1] - a[0]) * p

    def frame(self, p: float) -> Image.Image:
        """Kamerapose bei Fortschritt p (0..1, >1 = Weiterflug während der Überblendung).

        Drohnen-Parameter (alle optional):
          fly   = Vorwärtsflug: naher Boden wächst/zieht schneller vorbei als der Horizont
          rise  = Steigen in Quellpixeln (naher Boden wandert nach unten weg)
          par   = seitliches Gleiten (Quellpixel bei Tiefe 1), Anfang/Ende
          roll  = Schräglage in Grad, Anfang/Ende
          linear= True -> konstante Geschwindigkeit wie eine Drohne
        """
        c = self.c
        if c.get("linear", False):
            q = p
        else:
            q = 0.5 - 0.5 * np.cos(np.pi * min(max(p, 0), 1))
            q = q if p <= 1 else 1 + (p - 1) * 0.5
        zoom = self._lerp(c["zoom"], q)
        crop_h = self.sh / zoom
        crop_w = crop_h * self.W / self.H
        cx = self._lerp(c["x"], q) * self.sw
        cy = self._lerp(c["y"], q) * self.sh
        cx = float(np.clip(cx, crop_w / 2 + 2, self.sw - crop_w / 2 - 2))
        cy = float(np.clip(cy, crop_h / 2 + 2, self.sh - crop_h / 2 - 2))
        s = crop_h / self.H                                    # Quellpixel pro Ausgabepixel
        roll = np.radians(self._lerp(c.get("roll", [0, 0]), q))
        u, v = self.u, self.v
        if abs(roll) > 1e-4:
            cr, sr = np.cos(roll), np.sin(roll)
            u, v = u * cr - v * sr, u * sr + v * cr
        bx = (cx + u * s).astype(np.float32)
        by = (cy + v * s).astype(np.float32)
        d = cv2.remap(self.depth, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        rel = d - self.focus
        par = self._lerp(c["par"], q)
        dolly = c["dolly"] * q
        fly = c.get("fly", 0.0) * q
        rise = c.get("rise", 0.0) * q
        mx = bx + par * rel - (bx - cx) * (dolly * rel + fly * d)
        my = by + par * 0.15 * rel - (by - cy) * (dolly * rel + fly * d) - rise * d
        out = cv2.remap(self.src, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(out)
