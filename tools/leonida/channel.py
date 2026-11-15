"""Kanal-Renderer (Plum-Look + Bigfoot-Maskottchen) für News-Shorts.

Reihenfolge je Frame: Trailer-Szene -> 20 % Abdunklung -> Karten/Zahlen -> Maskottchen -> Untertitel.

Spec (dict):
  duration, fps=30, crf=16, preset="slow", darken=0.2
  scenes:   [{"clip": Pfad, "ss": s, "start": s, "end": s, "cam": {...}}]  oder {"image": Pfad, ...}
  voice:    {"wav": Pfad (gekürzte Aufnahme), "t": Start im Video}
  subs:     [{"t": s, "end": s, "words": [[Wort, Zeit absolut], ...]}]     1-3 Wörter pro Seite
  elements: [{"t", "end", "y" (Mitte), "card": bool, "w": 936, "motion": "card"|"punch"|"glide",
              "rows": [{"type": "big"|"title"|"text"|"pills"|"glowpill", ..., "at": s relativ}]}]
  mascot:   {"enter": s, "to_side": [s], "to_centre": [s], "poses": [{"pose", "from", "to"}]}
  music:    Trackname oder False;  sfx: [{"t", "type", "gain"}]
"""
from __future__ import annotations

import math
import os
import subprocess
import sys

from PIL import Image

from . import design as D
from . import sfx as sfxmod
from .mascot import Puppet, mouth_levels

ROOT = D.ROOT
W, H = D.W, D.H


def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def spring(t, zeta=0.55, omega=16.0):
    if t <= 0:
        return 0.0
    wd = omega * math.sqrt(1 - zeta ** 2)
    return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + zeta * omega / wd * math.sin(wd * t))


def motion(kind: str, life: float, fps=30):
    """-> (Deckkraft, dy, Skalierung). glide: 36 px über 14 Frames; punch: 0,8 -> 1 + 44 px; card: 80 px, 0,96 -> 1."""
    if kind == "none":
        return 1.0, 0.0, 1.0
    if kind == "glide":
        e = ease_out_cubic(life / (14 / fps))
        return e, 36 * (1 - e), 1.0
    s = spring(life)
    op = min(1.0, life / 0.1)
    if kind == "punch":
        return op, 44 * (1 - s), 0.8 + 0.2 * s
    return op, 80 * (1 - s), 0.96 + 0.04 * s           # card


def build_row(r: dict) -> Image.Image:
    t = r["type"]
    if t == "big":
        return D.gradient_text(r["text"], D.barlow(r.get("size", 260)), tracking=r.get("tracking", 0))
    if t == "title":
        return D.text(r["text"].upper(), D.barlow(r.get("size", 92)), fill=r.get("color", "cream"),
                      tracking=r.get("tracking", 1))
    if t == "text":
        return D.text(r["text"], D.albert(r.get("size", 44), r.get("weight", "SemiBold")), fill=r.get("color", "light"),
                      glow=r.get("glow", 0.2), spacing=r.get("spacing"))
    if t == "pills":
        return D.row([D.pill(p, bg=r.get("bg", "accent")) for p in r["items"]], gap=r.get("gap", 18))
    if t == "glowpill":
        return D.glow_pill(r["text"], size=r.get("size", 40))
    if t == "image":
        im = Image.open(os.path.join(ROOT, r["path"])).convert("RGBA")
        w = r.get("w", 400)
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        out = Image.new("RGBA", (im.width + 2 * D.PAD, im.height + 2 * D.PAD), (0, 0, 0, 0))
        out.alpha_composite(im, (D.PAD, D.PAD))
        return D.shadowed(out)
    raise ValueError(t)


class Element:
    def __init__(self, e: dict):
        self.e = e
        self.t, self.end = e["t"], e["end"]
        self.rows = [(r, build_row(r)) for r in e["rows"]]
        gap = e.get("gap", 20)
        inner = [im.height - 2 * D.PAD for _, im in self.rows]
        ch = sum(inner) + gap * (len(inner) - 1)
        if e.get("card", True):
            pad = e.get("pad", 56)
            self.cw = e.get("w", 936)
            self.chh = ch + 2 * pad
            self.bg = D.card(self.cw, self.chh)
            top = D.PAD + pad
        else:
            self.cw = max(im.width for _, im in self.rows) - 2 * D.PAD
            self.chh = ch
            self.bg = None
            top = D.PAD
        self.size = (self.cw + 2 * D.PAD, self.chh + 2 * D.PAD)
        self.pos, y = [], top
        for (r, im), ih in zip(self.rows, inner):
            self.pos.append((self.size[0] / 2 - im.width / 2, y - D.PAD))
            y += ih + gap

    def frame(self, canvas: Image.Image, t: float):
        if not (self.t <= t < self.end):
            return
        life = t - self.t
        op, dy, sc = motion(self.e.get("motion", "card" if self.bg else "glide"), life)
        op *= min(1.0, (self.end - t) / 0.18) if self.e.get("exit", True) else 1.0
        img = Image.new("RGBA", self.size, (0, 0, 0, 0))
        if self.bg:
            img.alpha_composite(self.bg)
        for k, ((r, im), (x, y)) in enumerate(zip(self.rows, self.pos)):
            rl = life - r.get("at", 0.08 * k if self.bg else 0.0)
            if rl < 0:
                continue
            rop, rdy, rsc = motion(r.get("motion", "glide"), rl)
            if rsc != 1.0:
                im = im.resize((max(int(im.width * rsc), 2), max(int(im.height * rsc), 2)), Image.BICUBIC)
                x, y = x + (self.rows[k][1].width - im.width) / 2, y + (self.rows[k][1].height - im.height) / 2
            D.paste(img, im, x, y + rdy, rop)
        if sc != 1.0:
            img = img.resize((int(img.width * sc), int(img.height * sc)), Image.BICUBIC)
        cx, cy = self.e.get("x", W / 2), self.e["y"] + dy
        D.paste(canvas, img, cx - img.width / 2, cy - img.height / 2, op)


class Channel:
    def __init__(self, spec: dict):
        self.spec = spec
        self.fps = spec.get("fps", 30)
        self.duration = spec["duration"]
        self.n = int(round(self.duration * self.fps))
        from .clip import VideoClip
        from .engine import Background
        self.scenes = []
        for sc in spec["scenes"]:
            dur = sc["end"] - sc["start"]
            if "clip" in sc:
                bg = VideoClip(sc["clip"], W, H, ss=sc.get("ss", 0.0), dur=dur, cam=sc.get("cam"))
            else:
                bg = Background(sc["image"], tuple(sc.get("zoom", (1.0, 1.08))),
                                tuple(tuple(p) for p in sc.get("pan", ((0.5, 0.5), (0.5, 0.5)))))
            self.scenes.append((sc["start"], sc["end"], bg))
        self.elements = [Element(e) for e in spec.get("elements", [])]
        self.subs = spec.get("subs", [])
        self.dark = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * spec.get("darken", 0.2))))
        self.puppet = None
        if spec.get("mascot") is not None:
            m = spec["mascot"]
            v = spec["voice"]
            mouth, level = mouth_levels(os.path.join(ROOT, v["wav"]), v["t"], self.n, self.fps)
            self.puppet = Puppet(mouth, level, poses=m.get("poses"), to_side=m.get("to_side", ()),
                                 to_centre=m.get("to_centre", ()), enter=m.get("enter", 0.0), fps=self.fps)
        self.sub_cache: dict = {}
        self.mask = False

    def _scene(self, t):
        for s0, s1, bg in self.scenes:
            if s0 <= t < s1:
                return bg.frame((t - s0) / (s1 - s0)).convert("RGBA")
        s0, s1, bg = self.scenes[-1]
        return bg.frame(min((t - s0) / (s1 - s0), 1.0)).convert("RGBA")

    def _subtitle(self, canvas, t):
        for pg in self.subs:
            if not (pg["t"] <= t < pg["end"]):
                continue
            words = [w for w, _ in pg["words"]]
            act = max([i for i, (_, wt) in enumerate(pg["words"]) if wt <= t] or [0])
            pop = ease_out_cubic((t - pg["words"][act][1]) / 0.12)
            key = (id(pg), act, round(pop, 2))
            if key not in self.sub_cache:
                if len(self.sub_cache) > 300:
                    self.sub_cache.clear()
                self.sub_cache[key] = D.subtitle(words, act, pop)
            im = self.sub_cache[key]
            side = self.puppet.side(t) if self.puppet else 1.0
            y = 900 + (1050 - 900) * side
            op, dy, _ = motion("glide", t - pg["t"]) if pg.get("glide", True) else (1, 0, 1)
            dy *= 0.35
            D.paste(canvas, im, W / 2 - im.width / 2, y - im.height / 2 + dy, op)

    def _grade(self, c: Image.Image) -> Image.Image:
        g = self.spec.get("grade")
        if not g:
            return c
        import numpy as np
        a = np.asarray(c.convert("RGB"), dtype=np.float32) / 255
        if g.get("contrast", 1.0) != 1.0:
            a = (a - 0.5) * g["contrast"] + 0.5
        if g.get("sat", 1.0) != 1.0:
            lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
            a = lum[..., None] + (a - lum[..., None]) * g["sat"]
        return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).convert("RGBA")

    def frame(self, t: float) -> Image.Image:
        c = self._grade(self._scene(t))
        c.alpha_composite(self.dark)
        for e in self.elements:
            e.frame(c, t)
        if self.puppet:
            self.puppet.place(c, t)
        self._subtitle(c, t)
        if self.mask:
            c.alpha_composite(D.safe_mask())
        return c.convert("RGB")

    def still(self, t: float, path: str, mask=False):
        self.mask = mask
        self.frame(t).save(path, quality=92)
        self.mask = False

    def _audio(self, wav: str, music):
        v = self.spec["voice"]
        sfxmod.render_track(self.spec.get("sfx", []), self.duration, wav, music=music,
                            voice=[{"t": v["t"], "wav": v["wav"]}], duck=self.spec.get("duck"))

    def render(self, out_path: str, no_music_copy=True):
        """Bild einmal rendern; Tonspur mit Musik und (optional) zweite Datei ohne Musik."""
        out_path = os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        silent = out_path.rsplit(".", 1)[0] + ".video.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(self.fps), "-i", "-", "-c:v", "libx264", "-preset", self.spec.get("preset", "slow"),
               "-crf", str(self.spec.get("crf", 16)), "-pix_fmt", "yuv420p", "-profile:v", "high", silent]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(self.n):
            proc.stdin.write(self.frame(i / self.fps).tobytes())
            if i % (self.fps * 2) == 0:
                print(f"\r  Frame {i}/{self.n}", end="", file=sys.stderr, flush=True)
        proc.stdin.close()
        proc.wait()
        outs = [(out_path, self.spec.get("music", "chase"))]
        if no_music_copy:
            outs.append((out_path.rsplit(".", 1)[0] + "_ohne-musik.mp4", False))
        for path, music in outs:
            wav = path.rsplit(".", 1)[0] + ".wav"
            self._audio(wav, music)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", path],
                           check=True)
            os.remove(wav)
        os.remove(silent)
        print(f"\r  fertig: {out_path}            ", file=sys.stderr)
        return [p for p, _ in outs]
