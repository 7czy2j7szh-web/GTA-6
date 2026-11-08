"""Selbst erzeugte Soundeffekte (keine Lizenzfragen): Whoosh, Bass-Schlag, Riser, Tick."""
from __future__ import annotations

import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def _env(n, attack, release):
    a = max(int(attack * SR), 1)
    env = np.ones(n)
    env[:a] = np.linspace(0, 1, a)
    env[a:] = np.exp(-np.linspace(0, 1, n - a) * release)
    return env


def _lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def whoosh(length=0.45):
    n = int(length * SR)
    noise = rng.standard_normal(n)
    # Bandpass-Sweep: Tiefpass mit steigender Grenzfrequenz minus stärkerer Tiefpass
    t = np.linspace(0, 1, n)
    alpha = 0.02 + 0.25 * np.sin(np.pi * t) ** 2
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += alpha[i] * (noise[i] - acc)
        y[i] = acc
    y = y - _lowpass(y, 0.01)
    env = np.sin(np.pi * t) ** 1.5
    return y * env * 0.9


def hit(length=0.9):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 38 + 70 * np.exp(-t * 18)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * _env(n, 0.003, 5.5)
    click = rng.standard_normal(n) * np.exp(-t * 90) * 0.35
    return np.tanh((body + click) * 1.8) * 0.9


def riser(length=1.5):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    f = 180 + 900 * t ** 2
    phase = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(phase) * 0.25 + np.sin(phase * 2.01) * 0.12
    noise = rng.standard_normal(n) * 0.12
    return (tone + noise) * t ** 1.5 * 0.8


def tick(length=0.06):
    n = int(length * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 120) * 0.5


GEN = {"whoosh": whoosh, "hit": hit, "riser": riser, "tick": tick}


def render_track(events: list[dict], duration: float, path: str):
    n = int(duration * SR) + SR
    mix = np.zeros(n)
    cache = {}
    for ev in events:
        kind = ev["type"]
        key = (kind, ev.get("len"))
        if key not in cache:
            cache[key] = GEN[kind](ev["len"]) if ev.get("len") else GEN[kind]()
        s = cache[key] * ev.get("gain", 1.0)
        i = int(ev["t"] * SR)
        j = min(i + len(s), n)
        mix[i:j] += s[: j - i]
    mix = mix[: int(duration * SR)]
    peak = np.max(np.abs(mix)) or 1
    mix = mix / peak * 0.5  # bewusst leise: Trend-Sound kommt in der App obendrauf
    pcm = (np.stack([mix, mix], axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
