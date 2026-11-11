"""Drohnen-Kamera ohne Verzerrung: virtuelle Kamera dreht/neigt/rollt und fliegt vor.

Das Quellbild wird wie ein Foto einer Lochkamera behandelt. Für jede Kamerapose wird
eine Homographie berechnet (K_src · R · K_out⁻¹). Das ist für Kameradrehungen exakt –
gerade Linien bleiben gerade, Details verziehen sich nicht. Der Vorwärtsflug wird über
eine wachsende Brennweite (Zoom) dargestellt.
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rot(yaw, pitch, roll):
    y, p, r = (math.radians(a) for a in (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


class DroneShot:
    """cam-Parameter (je [Anfang, Ende]):
         x, y   = Blickpunkt im Quellbild (0..1)
         yaw    = Schwenk links/rechts in Grad (zusätzlich zum Blickpunkt)
         pitch  = Neigung hoch/runter in Grad
         roll   = Schräglage in Grad
         zoom   = Vorwärtsflug (1 = volle Bildhöhe sichtbar)
         hfov   = angenommener horizontaler Bildwinkel des Screenshots (Standard 70°)
    """

    def __init__(self, path: str, W=1080, H=1920, cam: dict | None = None):
        self.src = cv2.cvtColor(cv2.imread(os.path.join(ROOT, path)), cv2.COLOR_BGR2RGB)
        self.sh, self.sw = self.src.shape[:2]
        self.W, self.H = W, H
        c = dict(x=[0.5, 0.5], y=[0.5, 0.5], yaw=[0, 0], pitch=[0, 0], roll=[0, 0], zoom=[1.15, 1.25], hfov=70)
        c.update(cam or {})
        self.c = c
        self.f_src = (self.sw / 2) / math.tan(math.radians(c["hfov"] / 2))
        self.K_src = np.array([[self.f_src, 0, self.sw / 2], [0, self.f_src, self.sh / 2], [0, 0, 1]])
        self._ensure_inside()

    @staticmethod
    def _lerp(a, q):
        return a[0] + (a[1] - a[0]) * q

    def _H(self, q):
        c = self.c
        # Blickpunkt (x, y) als Grund-Schwenk/-Neigung
        yaw0 = math.degrees(math.atan((self._lerp(c["x"], q) - 0.5) * self.sw / self.f_src))
        pitch0 = math.degrees(math.atan((self._lerp(c["y"], q) - 0.5) * self.sh / self.f_src))
        R = _rot(yaw0 + self._lerp(c["yaw"], q), pitch0 + self._lerp(c["pitch"], q), self._lerp(c["roll"], q))
        f_out = self.f_src * self._lerp(c["zoom"], q) * self.H / self.sh
        K_out = np.array([[f_out, 0, self.W / 2], [0, f_out, self.H / 2], [0, 0, 1]])
        return self.K_src @ R @ np.linalg.inv(K_out)

    def _corners_inside(self, q, margin=2):
        Hm = self._H(q)
        pts = np.array([[0, 0, 1], [self.W, 0, 1], [0, self.H, 1], [self.W, self.H, 1],
                        [self.W / 2, 0, 1], [self.W / 2, self.H, 1], [0, self.H / 2, 1], [self.W, self.H / 2, 1]]).T
        m = Hm @ pts
        x, y = m[0] / m[2], m[1] / m[2]
        return (x.min() >= margin and y.min() >= margin and x.max() <= self.sw - margin and y.max() <= self.sh - margin)

    def _ensure_inside(self):
        """Falls der Bildausschnitt irgendwo über den Rand ragt: Zoom leicht erhöhen (für den ganzen Flug)."""
        for _ in range(40):
            if all(self._corners_inside(q) for q in np.linspace(0, 1.15, 13)):
                return
            self.c["zoom"] = [z * 1.03 for z in self.c["zoom"]]

    def frame(self, p: float) -> Image.Image:
        q = p                                     # konstante Geschwindigkeit; > 1 = Weiterflug in der Überblendung
        out = cv2.warpPerspective(self.src, self._H(q), (self.W, self.H),
                                  flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(out)
