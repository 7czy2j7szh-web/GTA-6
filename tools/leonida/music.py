"""„Leonida Nights": eigener Erkennungs-Track des Accounts (komplett selbst komponiert).

Stil: 80er-Synthwave / Vice-City-Sonnenuntergang. Warme Flächen, Arpeggio mit
Ping-Pong-Echo, Drumcomputer mit Gated-Reverb-Snare, sanfte Lead-Melodie und
ein leichtes Kassetten-Leiern (Wow & Flutter) für das Nostalgie-Gefühl.

Melodie, Akkordfolge und Arrangement sind eigene Kompositionen. Es wird
keine bestehende GTA-Melodie verwendet, damit TikTok nichts stummschaltet
und der Track dem Account gehört.

Aufruf:  python3 -m tools.leonida.music   (oder über engine automatisch)
"""
from __future__ import annotations

import os
import wave

import numpy as np
from scipy import signal

SR = 48000
BPM = 92
BEAT = 60 / BPM
BAR = 4 * BEAT
BARS = 16
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "music", "leonida_nights.wav")

rng = np.random.default_rng(1986)

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def m(name: str) -> int:
    """'A4' -> MIDI 69"""
    return NOTE[name[:-1]] + 12 * (int(name[-1]) + 1)


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


# ------------------------------------------------------------- Komposition
# Akkorde (1 Takt je Akkord): Am9 – Fmaj7(9) – Cmaj7 – G6, zweimal pro 8 Takte
CHORDS = [
    dict(bass="A1", pad=["A3", "C4", "E4", "G4", "B4"], arp=["A4", "C5", "E5", "G5", "B5"]),
    dict(bass="F1", pad=["F3", "A3", "C4", "E4", "G4"], arp=["F4", "A4", "C5", "E5", "G5"]),
    dict(bass="C2", pad=["G3", "C4", "E4", "G4", "B4"], arp=["C5", "E5", "G5", "B5", "C6"]),
    dict(bass="G1", pad=["G3", "B3", "D4", "E4", "G4"], arp=["G4", "B4", "D5", "E5", "G5"]),
]

# Lead-Melodie über 8 Takte: (Note | None für Pause, Dauer in Beats)
MELODY = [
    # Takt 1–4
    ("E5", 1.5), ("D5", 0.5), ("C5", 1), ("B4", 1),
    ("C5", 1.5), ("A4", 0.5), ("A4", 2),
    ("G4", 1), ("C5", 1), ("E5", 1), ("G5", 1),
    ("E5", 2), ("D5", 1.5), ("B4", 0.5),
    # Takt 5–8
    ("E5", 1.5), ("D5", 0.5), ("C5", 1), ("E5", 1),
    ("A5", 2), ("G5", 1), ("E5", 1),
    ("G5", 1.5), ("E5", 0.5), ("D5", 1), ("C5", 1),
    ("D5", 2), ("B4", 1), (None, 1),
]

ARP_PATTERN = [0, 1, 2, 3, 4, 3, 2, 1, 0, 2, 1, 3, 2, 4, 3, 1]


# ------------------------------------------------------------- Bausteine

def lowpass(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def highpass(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x, axis=0)


def saw(freq, n, phase0=0.0):
    ph = (phase0 + freq * np.arange(n) / SR) % 1.0
    return 2 * ph - 1


def square(freq, n, duty=0.5):
    ph = (freq * np.arange(n) / SR) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def triangle(freq_curve):
    ph = np.cumsum(freq_curve) / SR % 1.0
    return 4 * np.abs(ph - 0.5) - 1


def adsr(n, a, d, s, r, hold):
    """Hüllkurve: Attack, Decay, Sustain-Pegel, Release; hold = Notenlänge in s."""
    t = np.arange(n) / SR
    env = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = t > hold
    env[rel] *= np.exp(-(t[rel] - hold) / max(r, 1e-4))
    return env


def place(buf, sig, start_s):
    i = int(start_s * SR)
    if i >= len(buf):
        return
    j = min(i + len(sig), len(buf))
    buf[i:j] += sig[: j - i]


def stereo(mono, pan=0.0):
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    return np.stack([mono * l, mono * r], axis=1)


# ------------------------------------------------------------- Instrumente

def build(total_s):
    n = int(total_s * SR)
    pad = np.zeros((n, 2))
    bass = np.zeros(n)
    arp = np.zeros((n, 2))
    lead = np.zeros(n)
    kick = np.zeros(n)
    snare = np.zeros(n)
    hats = np.zeros(n)
    kick_env = np.zeros(n)

    for bar in range(BARS):
        ch = CHORDS[bar % 4]
        t0 = bar * BAR

        # Pad: 3 verstimmte Sägezähne pro Ton, breit im Stereobild
        hold = BAR
        ln = int((BAR + 1.2) * SR)
        env = adsr(ln, 0.35, 1.5, 0.75, 0.6, hold)
        for note in ch["pad"]:
            f = hz(m(note))
            for det, pan in ((-0.07, -0.7), (0.0, 0.0), (0.07, 0.7)):
                v = saw(f * 2 ** (det / 12), ln, rng.random()) * env * 0.05
                place_st = stereo(v, pan)
                i = int(t0 * SR)
                j = min(i + ln, n)
                pad[i:j] += place_st[: j - i]

        # Bass: treibende Achtel, jede 4. Achtel eine Oktave höher
        for k in range(8):
            note = m(ch["bass"]) + (12 if k % 4 == 3 else 0)
            ln = int(BEAT / 2 * SR)
            f = hz(note)
            v = (saw(f, ln) * 0.6 + square(f / 2, ln) * 0.4) * adsr(ln, 0.004, 0.12, 0.35, 0.05, BEAT / 2 - 0.03)
            place(bass, v * 0.5, t0 + k * BEAT / 2)

        # Arpeggio: Sechzehntel, Pluck-Sound
        for k in range(16):
            note = ch["arp"][ARP_PATTERN[k]]
            ln = int(0.35 * SR)
            v = square(hz(m(note)), ln, 0.3) * adsr(ln, 0.002, 0.09, 0.0, 0.05, 0.1)
            vel = 0.85 if k % 4 == 0 else 0.6
            place(arp[:, 0], v * 0.16 * vel, t0 + k * BEAT / 4)

        # Drums: Kick auf 1 & 3 (+ „und" von 3 jeden 2. Takt), Snare auf 2 & 4, Hi-Hats Achtel
        kicks = [0, 2] + ([2.5] if bar % 2 == 1 else [])
        for b in kicks:
            ln = int(0.45 * SR)
            t = np.arange(ln) / SR
            f = 45 + 105 * np.exp(-t * 30)
            v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
            v += bandpass(rng.standard_normal(ln), 2500, 5000) * np.exp(-t * 160) * 0.25
            place(kick, v * 0.9, t0 + b * BEAT)
            place(kick_env, np.exp(-t * 6), t0 + b * BEAT)
        for b in (1, 3):
            ln = int(0.3 * SR)
            t = np.arange(ln) / SR
            noise = bandpass(rng.standard_normal(ln), 1200, 6000) * np.exp(-t * 18)
            tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
            place(snare, (noise * 0.9 + tone * 0.5) * 0.55, t0 + b * BEAT)
        for k in range(8):
            ln = int(0.06 * SR)
            t = np.arange(ln) / SR
            v = highpass(rng.standard_normal(ln), 7000) * np.exp(-t * 70)
            place(hats, v * (0.12 if k % 2 else 0.07), t0 + k * BEAT / 2)

    # Lead-Melodie (alle 8 Takte wiederholt)
    for rep in range(BARS // 8):
        t = rep * 8 * BAR
        for note, beats in MELODY:
            dur = beats * BEAT
            if note:
                ln = int((dur + 0.5) * SR)
                tt = np.arange(ln) / SR
                vib = 1 + 0.0045 * np.sin(2 * np.pi * 5.2 * tt) * np.clip((tt - 0.25) / 0.3, 0, 1)
                f = hz(m(note)) * vib
                ph = np.cumsum(f) / SR % 1.0
                v = triangle(f) * 0.55 + (2 * ph - 1) * 0.25 + np.sin(2 * np.pi * np.cumsum(f / 2) / SR) * 0.2
                v *= adsr(ln, 0.03, 0.4, 0.8, 0.22, dur - 0.04)
                place(lead, v * 0.22, t)
            t += dur

    return dict(pad=pad, bass=bass, arp=arp[:, 0], lead=lead, kick=kick, snare=snare, hats=hats, kick_env=kick_env)


def reverb_ir(seconds=2.4, damp=5000, seed=0):
    r = np.random.default_rng(seed)
    ln = int(seconds * SR)
    t = np.arange(ln) / SR
    ir = r.standard_normal((ln, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
    ir = lowpass(ir, damp)
    return ir / np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))


def convolve_st(mono_or_st, ir):
    x = mono_or_st if mono_or_st.ndim == 2 else np.stack([mono_or_st, mono_or_st], axis=1)
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)


def pingpong(x, delay_s, feedback=0.4, repeats=6):
    n = len(x)
    out = np.stack([x, x], axis=1) * 0.0
    out[:, 0] += x
    out[:, 1] += x
    d = int(delay_s * SR)
    g = 1.0
    for k in range(1, repeats + 1):
        g *= feedback
        ch = k % 2
        if k * d < n:
            out[k * d:, ch] += lowpass(x[: n - k * d], 3500) * g
    return out


def tape(x, wow_hz=0.55, wow_depth=0.0022, flutter_hz=6.5, flutter_depth=0.0004):
    """Kassetten-Leiern: leichte, langsame Tonhöhenschwankung + sanfte Sättigung."""
    n = len(x)
    t = np.arange(n) / SR
    off = (wow_depth * SR / (2 * np.pi * wow_hz)) * np.sin(2 * np.pi * wow_hz * t) \
        + (flutter_depth * SR / (2 * np.pi * flutter_hz)) * np.sin(2 * np.pi * flutter_hz * t)
    idx = np.clip(np.arange(n) + off, 0, n - 1)
    y = np.stack([np.interp(idx, np.arange(n), x[:, c]) for c in range(2)], axis=1)
    return np.tanh(y * 1.3) / np.tanh(1.3)


def render(path: str = OUT) -> str:
    total = BARS * BAR
    s = build(total + 2.5)
    n = len(s["bass"])
    duck = 1 - 0.45 * np.clip(s["kick_env"], 0, 1)          # Sidechain-Pumpen (80er-Feeling)

    pad = highpass(lowpass(s["pad"], 2600), 160) * duck[:, None]
    bass = highpass(lowpass(s["bass"], 1100), 40) * duck
    arp = pingpong(highpass(lowpass(s["arp"], 4800), 250), 0.75 * BEAT, 0.42)
    lead = highpass(lowpass(s["lead"], 6500), 200)
    snare_gated = convolve_st(s["snare"], reverb_ir(0.45, 6000, 3))
    gate = np.ones(n)  # Gated Reverb: Hall nach ~0,28 s hart abschneiden
    for bar in range(BARS):
        for b in (1, 3):
            i = int((bar * BAR + b * BEAT + 0.28) * SR)
            gate[i:i + int(0.05 * SR)] = np.linspace(1, 0, int(0.05 * SR))[: max(0, min(int(0.05 * SR), n - i))]
            gate[i + int(0.05 * SR):int((bar * BAR + b * BEAT + BEAT * 0.95) * SR)] = 0
    snare = stereo(s["snare"]) * 0.8 + snare_gated * gate[:, None] * 0.55

    dry = (pad * 0.75 + stereo(bass) * 0.38 + arp * 1.0 + stereo(lead, 0.05) * 1.7
           + stereo(s["kick"]) * 0.42 + snare * 0.7 + stereo(s["hats"], 0.25) * 1.6)
    send = pad * 0.30 + arp * 0.25 + stereo(lead) * 0.55
    wet = convolve_st(send, reverb_ir(2.6, 4500, 1))
    mix = dry + wet * 0.35

    mix = highpass(mix, 45)
    mix = tape(mix)
    mix = lowpass(mix, 14000)
    hiss = lowpass(rng.standard_normal((n, 2)), 6000) * 0.0025
    mix = mix + hiss

    # Nahtlose Schleife: den Hall-Ausklang des Endes auf den Anfang legen
    L = int(total * SR)
    tail = mix[L:]
    mix = mix[:L].copy()
    mix[: len(tail)] += tail

    mix /= np.max(np.abs(mix)) / 0.89                      # -1 dBFS Spitze
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def load(path: str = OUT) -> np.ndarray:
    if not os.path.exists(path):
        render(path)
    with wave.open(path, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2)
    return data.astype(np.float64) / 32767


if __name__ == "__main__":
    print(render())
