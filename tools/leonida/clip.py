"""Echte Videoszenen aus den offiziellen Trailern als Hintergrund.

Pro Szene wird einmalig ein Ausschnitt (9:16, ohne schwarze Kino-Balken) aus dem 4K-Trailer
geschnitten und als hochwertiger Zwischenclip (1440x2560) gespeichert. Beim Rendern wird daraus
Bild für Bild gelesen und mit einer weichen Kamerafahrt (Zoom/Schwenk) auf 1080x1920 gebracht.

cam (alles optional):
  x, y  = Mittelpunkt des Ausschnitts im Bild (0..1, y bezogen auf die Fläche ohne Balken)
  h     = Höhe des Ausschnitts als Anteil der Bildhöhe ohne Balken (1 = volle Höhe)
  zoom  = [Anfang, Ende] Zoom während der Szene (1 = kein Zoom)
  pan   = [[dx, dy] Anfang, [dx, dy] Ende] Verschiebung in Anteilen der Bildgröße
  speed = Abspielgeschwindigkeit (1 = normal)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROXY_DIR = os.path.join(ROOT, "assets", "official", "video", "proxy")
PW, PH = 1440, 2560


def _probe(path: str) -> tuple[int, int, float]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "json", path], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den)


def _active_area(path: str, ss: float, dur: float) -> tuple[int, int]:
    """(y, h) der Bildfläche ohne schwarze Balken in diesem Abschnitt (häufigster cropdetect-Wert)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{ss:.3f}", "-i", path, "-t", f"{min(dur, 2.0):.3f}",
                        "-vf", "cropdetect=24:2:0", "-f", "null", "-"], capture_output=True, text=True)
    vals = [ln.split("crop=")[1].split()[0] for ln in r.stderr.splitlines() if "crop=" in ln]
    if not vals:
        return 0, _probe(path)[1]
    w, h, x, y = (int(v) for v in Counter(vals).most_common(1)[0][0].split(":"))
    return y + 2, h - 4                                          # 2 px Sicherheitsrand gegen Kantenreste


class VideoClip:
    def __init__(self, path: str, W=1080, H=1920, ss: float = 0.0, dur: float = 2.0, cam: dict | None = None,
                 extra: float = 0.6):
        self.src = os.path.join(ROOT, path)
        self.W, self.H = W, H
        c = dict(x=0.5, y=0.5, h=1.0, zoom=[1.0, 1.08], pan=[[0, 0], [0, 0]], speed=1.0)
        c.update(cam or {})
        self.c = c
        self.dur = dur
        sw, sh, self.fps = _probe(self.src)
        need = dur * c["speed"] + extra
        key = hashlib.sha1(json.dumps([path, ss, round(need, 3), c["x"], c["y"], c["h"]]).encode()).hexdigest()[:14]
        os.makedirs(PROXY_DIR, exist_ok=True)
        self.proxy = os.path.join(PROXY_DIR, f"{key}.mp4")
        if not os.path.exists(self.proxy):
            ay, ah = _active_area(self.src, ss, need)
            ch = int(ah * c["h"]) // 2 * 2
            cw = int(ch * 9 / 16) // 2 * 2
            cx = int(np.clip(c["x"] * sw - cw / 2, 0, sw - cw))
            cy = int(np.clip(ay + c["y"] * ah - ch / 2, ay, ay + ah - ch))
            tmp = self.proxy + ".tmp.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.3f}", "-i", self.src, "-t", f"{need:.3f}",
                            "-vf", f"crop={cw}:{ch}:{cx}:{cy},scale={PW}:{PH}:flags=lanczos", "-an",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-pix_fmt", "yuv420p", tmp],
                           check=True)
            os.replace(tmp, self.proxy)
        self.cap = None
        self.idx = -1
        self.cur = None
        self.n = int(cv2.VideoCapture(self.proxy).get(cv2.CAP_PROP_FRAME_COUNT))

    def _read_to(self, i: int):
        i = max(0, min(i, self.n - 1))
        if self.cap is None or i < self.idx:
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.proxy)
            self.idx = -1
        while self.idx < i:
            ok, fr = self.cap.read()
            if not ok:
                break
            self.idx += 1
            self.cur = fr

    def frame(self, p: float) -> Image.Image:
        local = max(p, 0.0) * self.dur * self.c["speed"]
        self._read_to(int(local * self.fps + 1e-6))
        q = min(max(p, 0.0), 1.3)
        z = self.c["zoom"][0] + (self.c["zoom"][1] - self.c["zoom"][0]) * q
        (dx0, dy0), (dx1, dy1) = self.c["pan"]
        dx, dy = dx0 + (dx1 - dx0) * q, dy0 + (dy1 - dy0) * q
        k = self.W / PW * z
        M = np.array([[k, 0, self.W / 2 - k * PW / 2 + dx * self.W],
                      [0, k, self.H / 2 - k * PH / 2 + dy * self.H]], dtype=np.float32)
        out = cv2.warpAffine(self.cur, M, (self.W, self.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
