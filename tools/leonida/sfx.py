"""Selbst erzeugte Soundeffekte (keine Lizenzfragen), bewusst leise und weich.

Klangpalette:
- pop:    kurzer, runder "Plopp" für Text-Einblendungen
- whoosh: sanftes, dunkles Luftgeräusch für Szenenwechsel
- hit:    weicher tiefer "Thump" für Stempel (ohne Verzerrung)
- chime:  helles, warmes Glöckchen für große Zahlen / Auflösungen
- riser:  leises Anschwellen beim Hochzählen
- tick:   ganz leises Klicken
"""
from __future__ import annotations

import os
import wave

import numpy as np

SR = 48000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
rng = np.random.default_rng(7)

# Ziel-Spitzenpegel des fertigen Effekt-Tracks (~ -18 dBFS). Der Trend-Sound
# aus der TikTok-App soll klar im Vordergrund stehen.
TARGET_PEAK = 0.125


def _onepole_lowpass(x: np.ndarray, cutoff_hz: float) -> np.ndarray:
    a = 1 - np.exp(-2 * np.pi * cutoff_hz / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def _fade(sig: np.ndarray, fade_in=0.004, fade_out=0.02) -> np.ndarray:
    n = len(sig)
    a, b = min(int(fade_in * SR), n), min(int(fade_out * SR), n)
    sig = sig.copy()
    if a:
        sig[:a] *= np.linspace(0, 1, a)
    if b:
        sig[-b:] *= np.linspace(1, 0, b)
    return sig


def pop(length=0.09):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 520 + 260 * np.exp(-t * 60)          # leicht fallende Tonhöhe = "runder" Plopp
    phase = 2 * np.pi * np.cumsum(f) / SR
    return _fade(np.sin(phase) * np.exp(-t * 38) * 0.55)


def whoosh(length=0.5):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    noise = _onepole_lowpass(rng.standard_normal(n), 900)   # dunkel, kein Zischen
    noise = noise - _onepole_lowpass(noise, 120)            # Rumpeln raus
    env = np.sin(np.pi * t) ** 2
    return _fade(noise * env * 1.6)


def hit(length=0.45):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 55 + 45 * np.exp(-t * 25)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 9)
    return _fade(body * 0.9, fade_in=0.006)


def chime(length=1.1):
    n = int(length * SR)
    t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 880 * t) * 1.0
            + np.sin(2 * np.pi * 1320 * t) * 0.35
            + np.sin(2 * np.pi * 1760 * t) * 0.12)
    return _fade(tone * np.exp(-t * 4.5) * 0.30, fade_in=0.008, fade_out=0.1)


def riser(length=1.5):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    f = 220 + 440 * t ** 2
    phase = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(phase) * 0.6 + np.sin(phase * 1.5) * 0.15
    return _fade(tone * t ** 2 * 0.35, fade_out=0.06)


def tick(length=0.04):
    n = int(length * SR)
    t = np.arange(n) / SR
    return _fade(np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 150) * 0.25, fade_in=0.001)


GEN = {"pop": pop, "whoosh": whoosh, "hit": hit, "chime": chime, "riser": riser, "tick": tick}

# Relative Lautstärke je Effekt im Mix
MIX_GAIN = {"pop": 0.55, "whoosh": 0.45, "hit": 0.8, "chime": 0.6, "riser": 0.45, "tick": 0.4}


# Hintergrundmusik. Standard: "chase" (episch, schnell, vom User gewählt).
# Alternativen: "vice_anthem" (episch, getragener), "leonida_nights" (ruhig).
# gain = Pegel im fertigen Video (~ -19 bzw. -20 LUFS), fade_in kurz beim epischen Track,
# damit der BRAAM-Schlag in Sekunde 0 voll wirkt.
DEFAULT_TRACK = "chase"
TRACKS = {
    "chase": dict(module="epic", comp="chase", gain=0.50, fade_in=0.01),
    "vice_anthem": dict(module="epic", comp="vice_anthem", gain=0.50, fade_in=0.01),
    "leonida_nights": dict(module="music", gain=0.40, fade_in=0.3),
}
MUSIC_FADE_OUT = 1.0


def music_bed(duration: float, name: str = DEFAULT_TRACK, offset: float = 0.0) -> np.ndarray:
    """offset = Startposition im Track (s), z. B. damit der Crash genau auf die Enthüllung fällt."""
    import importlib
    cfg = TRACKS[name]
    mod = importlib.import_module(f".{cfg['module']}", __package__)  # lazy: scipy nur bei Bedarf
    track = mod.load(cfg["comp"]) if "comp" in cfg else mod.load()
    n = int(duration * SR)
    o = int((offset % (len(track) / SR)) * SR)
    reps = int(np.ceil((n + o) / len(track))) + 1
    bed = np.tile(track, (reps, 1))[o:o + n].copy()     # Tracks sind nahtlose Schleifen
    a, b = max(int(cfg["fade_in"] * SR), 1), int(MUSIC_FADE_OUT * SR)
    bed[:a] *= np.linspace(0, 1, a)[:, None]
    bed[-b:] *= np.linspace(1, 0, b)[:, None] ** 1.5
    return bed * cfg["gain"]


VOICE_PEAK = 0.70      # Erzählstimme klar vorne
DUCK = 0.35            # Musik läuft unter der Stimme auf ~35 % (ca. -9 dB)


def voice_track(lines: list[dict], duration: float):
    """lines = [{"t": Start in s, "wav": Pfad}] -> (stereo Stimme, Hüllkurve 0..1)."""
    from . import voice as voicemod
    n = int(duration * SR)
    v = np.zeros(n)
    for ln in lines:
        x = voicemod.load(os.path.join(ROOT, ln["wav"]), SR)
        i = int(ln["t"] * SR)
        j = min(i + len(x), n)
        if i < n:
            v[i:j] += x[: j - i]
    peak = np.max(np.abs(v)) or 1
    v = v / peak * VOICE_PEAK
    env = _onepole_lowpass(np.abs(v), 6)
    env = np.clip(env / (np.max(env) or 1) * 4, 0, 1)
    env = _onepole_lowpass(env, 3)                 # weiches Ein-/Ausblenden der Absenkung
    return np.stack([v, v], axis=1), np.clip(env, 0, 1)


def render_track(events: list[dict], duration: float, path: str, music=True, voice=None, music_offset=0.0):
    n = int(duration * SR) + SR
    mix = np.zeros(n)
    cache = {}
    for ev in events:
        kind = ev["type"]
        key = (kind, ev.get("len"))
        if key not in cache:
            cache[key] = GEN[kind](ev["len"]) if ev.get("len") else GEN[kind]()
        s = cache[key] * ev.get("gain", 1.0) * MIX_GAIN.get(kind, 0.5)
        i = int(ev["t"] * SR)
        j = min(i + len(s), n)
        mix[i:j] += s[: j - i]
    mix = mix[: int(duration * SR)]
    mix = _onepole_lowpass(mix, 7000)          # Höhen weich machen
    peak = np.max(np.abs(mix)) or 1
    mix = np.stack([mix, mix], axis=1) / peak * TARGET_PEAK
    vstereo, venv = (None, None)
    if voice:
        vstereo, venv = voice_track(voice, duration)
        mix = mix * (1 - 0.5 * venv[:, None])      # Effekte unter der Stimme leiser
    if music:
        bed = music_bed(duration, music if isinstance(music, str) else DEFAULT_TRACK, music_offset)
        if venv is not None:
            bed = bed * (1 - (1 - DUCK) * venv[:, None])
        mix = mix + bed
    if vstereo is not None:
        mix = mix + vstereo
    # Sicherheitsbegrenzer auf die *echten* Spitzen (4x überabgetastet), mit Reserve für AAC
    from scipy.signal import resample_poly
    top = max(np.max(np.abs(resample_poly(mix[:, c], 4, 1))) for c in range(2))
    if top > 0.70:
        mix *= 0.70 / top
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
