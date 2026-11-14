"""Erzählstimme über die Gemini-TTS-API (Schlüssel wird vom Proxy der Umgebung eingesetzt).

- generate(text, voice) -> WAV-Pfad (24 kHz mono), gecacht nach Text+Stimme+Stil
- Jeder Satz wird einzeln erzeugt, damit er exakt auf seinen Beat gelegt werden kann.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "assets", "voice_cache")
MODEL = "gemini-3.8-flash-tts"
DEFAULT_VOICE = "Puck"
# Kurze englische Regieanweisung im Gemini-Format ("Say …: <Text>") – wird nicht mitgesprochen.
STYLE = ""  # Regieanweisungen werden von den TTS-Modellen mitgesprochen -> weglassen
SR = 24000


def _request(text: str, voice: str, style: str, model: str) -> bytes:
    body = {
        "contents": [{"parts": [{"text": style + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    import time
    wait = 35
    for _ in range(5):                                   # kostenloses Kontingent: bei 429 warten und erneut
        r = subprocess.run(["curl", "-sS", "-m", "120", "-H", "Content-Type: application/json",
                            "-d", json.dumps(body), url], capture_output=True, text=True)
        d = json.loads(r.stdout)
        if d.get("error", {}).get("code") != 429:
            break
        time.sleep(wait)
        wait *= 2
    try:
        part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
    except (KeyError, IndexError):
        raise RuntimeError("TTS-Fehler: " + r.stdout[:400])
    return base64.b64decode(part["data"])


def _trim(pcm: np.ndarray, thresh=0.012, pad=0.03) -> np.ndarray:
    """Stille am Anfang/Ende abschneiden, damit der Satz genau auf dem Beat beginnt."""
    a = np.abs(pcm.astype(np.float32) / 32768)
    idx = np.where(a > thresh)[0]
    if len(idx) == 0:
        return pcm
    s = max(idx[0] - int(pad * SR), 0)
    e = min(idx[-1] + int(pad * SR), len(pcm))
    return pcm[s:e]


def _strip_edge_clicks(pcm: np.ndarray, min_gap=0.15, max_len=0.25) -> np.ndarray:
    """Die TTS-Ausgabe hat manchmal ein lautes Knacken ganz am Anfang/Ende (kurzer Ausschlag,
    durch Stille von der Sprache getrennt). Solche Randstücke entfernen."""
    win = int(0.01 * SR)
    x = np.abs(pcm.astype(np.float32) / 32768)
    n = len(x) // win
    if n < 3:
        return pcm
    e = x[: n * win].reshape(n, win).mean(axis=1)
    on = e > 0.006
    segs, i = [], 0
    while i < n:                                   # zusammenhängende Ton-Abschnitte
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            segs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for a, b in segs:                              # kurze Lücken (< min_gap) gehören zur Sprache
        if merged and (a - merged[-1][1]) * 0.01 < min_gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) * 0.01 <= max_len:
        merged.pop(0)
    if len(merged) > 1 and (merged[-1][1] - merged[-1][0]) * 0.01 <= max_len:
        merged.pop()
    if not merged:
        return pcm
    return pcm[max(merged[0][0] - 3, 0) * win: min(merged[-1][1] + 3, n) * win]


def generate(text: str, voice: str = DEFAULT_VOICE, style: str = STYLE, model: str = MODEL) -> str:
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(f"{model}|{voice}|{style}|{text}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{voice}_{key}.wav")
    if os.path.exists(path):
        return path
    pcm = np.frombuffer(_request(text, voice, style, model), dtype=np.int16)
    pcm = _trim(_strip_edge_clicks(pcm))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def load(path: str, sr_out: int = 48000) -> np.ndarray:
    """WAV laden und auf die Mix-Abtastrate hochrechnen (mono float)."""
    from math import gcd
    from scipy.signal import resample_poly
    with wave.open(path, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        sr = w.getframerate()
    if sr != sr_out:                                    # sauberes Hochrechnen (kein Aliasing)
        g = gcd(sr, sr_out)
        x = resample_poly(x, sr_out // g, sr // g)
    f = min(int(0.008 * sr_out), len(x) // 4)           # 8 ms Ein-/Ausblenden gegen Knackser
    if f > 0:
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    return x


def split(full_path: str, approx_bounds: list[float], out_prefix: str, search: float = 0.35) -> list[dict]:
    """Ganze Aufnahme an den leisesten Stellen nahe den (ungefähren) Satzgrenzen zerschneiden.

    approx_bounds: Zeitpunkte zwischen den Sätzen (z. B. aus einer Abschrift mit Zeitstempeln).
    Gibt [{"wav": Pfad, "dur": Sekunden}] zurück (Stille an den Rändern abgeschnitten)."""
    with wave.open(full_path) as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    x = np.abs(pcm.astype(np.float32) / 32768)
    win = int(0.01 * sr)
    e = np.array([x[i:i + win].mean() for i in range(0, len(x) - win, win)])
    e = np.convolve(e, np.ones(8) / 8, mode="same")
    total = len(pcm) / sr
    cuts = [0.0]
    for b in approx_bounds:
        a, z = max(int((b - search) / 0.01), 1), min(int((b + search) / 0.01), len(e) - 1)
        cuts.append((a + int(np.argmin(e[a:z]))) * 0.01)
    cuts.append(total)
    out = []
    for k in range(len(cuts) - 1):
        seg = _trim(pcm[int(cuts[k] * sr):int(cuts[k + 1] * sr)], thresh=0.01, pad=0.02)
        path = f"{out_prefix}_{k + 1}.wav"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(seg.tobytes())
        out.append({"wav": path, "dur": round(len(seg) / sr, 2)})
    return out
