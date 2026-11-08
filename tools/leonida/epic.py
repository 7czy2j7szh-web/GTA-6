"""„Vice Anthem": epischer Erkennungs-Track (komplett selbst komponiert).

Trailer-Gefühl trifft 80er-Vice-City: BRAAM-Schlag in Sekunde 0, Taiko-Trommeln,
Gated-Reverb-Snare, Crash-Becken, Supersaw-Streicher und -Lead, Chor-Fläche,
treibendes Streicher-Ostinato, Riser vor jedem Abschnitt.

Harmonik (8 Takte): Dm – B♭ – F – C | Dm – B♭ – Gm – A (A-Dur = Spannung zurück nach Dm)
Melodie, Akkorde und Arrangement sind eigene Kompositionen, keine GTA-Melodie.

Aufruf:  python3 -m tools.leonida.epic
"""
from __future__ import annotations

import os
import wave

import numpy as np

from .music import (SR, adsr, bandpass, convolve_st, highpass, hz, lowpass, m, pingpong,
                    place, reverb_ir, saw, square, stereo)

BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT          # 2,5 s
BARS = 16               # 40 s, nahtlose Schleife
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "music", "vice_anthem.wav")

rng = np.random.default_rng(2026)

CHORDS = [
    dict(bass="D2", pad=["D3", "A3", "D4", "F4", "A4"]),     # Dm
    dict(bass="A#1", pad=["A#2", "F3", "A#3", "D4", "F4"]),  # B♭
    dict(bass="F2", pad=["C3", "F3", "A3", "C4", "F4"]),     # F
    dict(bass="C2", pad=["C3", "G3", "C4", "E4", "G4"]),     # C
    dict(bass="D2", pad=["D3", "A3", "D4", "F4", "A4"]),     # Dm
    dict(bass="A#1", pad=["A#2", "F3", "A#3", "D4", "F4"]),  # B♭
    dict(bass="G2", pad=["G2", "D3", "G3", "A#3", "D4"]),    # Gm
    dict(bass="A1", pad=["A2", "E3", "A3", "C#4", "E4"]),    # A (Dur, Spannung)
]

MELODY = [  # (Note | None, Beats) – 8 Takte, heldenhaft mit Sprüngen nach oben
    ("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1),
    ("F5", 2.5), ("E5", 0.5), ("D5", 1),
    ("C5", 1), ("F5", 1), ("A5", 2),
    ("G5", 2), ("E5", 1), ("C5", 1),
    ("A4", 1), ("D5", 1), ("E5", 1), ("F5", 1),
    ("F5", 1.5), ("G5", 0.5), ("F5", 1), ("D5", 1),
    ("A#5", 2), ("A5", 1), ("G5", 1),
    ("A5", 2), ("E5", 1), ("C#5", 1),
]

# ------------------------------------------------------------- Kompositionen
# "chase" = Variante 4 aus den Hörproben (vom User gewählt, Standard in allen Videos)
COMPOSITIONS = {
    "vice_anthem": dict(bpm=96, seed=2026, chords=CHORDS, melody=MELODY,
                        out=os.path.join(ROOT, "assets", "music", "vice_anthem.wav")),
    "chase": dict(
        bpm=118, seed=7,
        out=os.path.join(ROOT, "assets", "music", "chase.wav"),
        chords=[  # Am – F – G – Em | Am – F – G – E (E-Dur = Spannung zurück nach Am)
            dict(bass="A1", pad=["A2", "E3", "A3", "C4", "E4"]),
            dict(bass="F2", pad=["F3", "A3", "C4", "F4", "A4"]),
            dict(bass="G1", pad=["G2", "D3", "G3", "B3", "D4"]),
            dict(bass="E2", pad=["E3", "B3", "E4", "G4", "B4"]),
            dict(bass="A1", pad=["A2", "E3", "A3", "C4", "E4"]),
            dict(bass="F2", pad=["F3", "A3", "C4", "F4", "A4"]),
            dict(bass="G1", pad=["G2", "D3", "G3", "B3", "D4"]),
            dict(bass="E2", pad=["E3", "B3", "E4", "G#4", "B4"]),
        ],
        melody=[  # rasende Achtel-Läufe, 8 Takte
            ("A4", .5), ("C5", .5), ("E5", .5), ("A5", .5), ("G5", .5), ("E5", .5), ("C5", .5), ("E5", .5),
            ("F5", 1.5), ("E5", .5), ("C5", 1), ("A4", 1),
            ("B4", .5), ("D5", .5), ("G5", .5), ("B5", .5), ("A5", .5), ("G5", .5), ("D5", .5), ("G5", .5),
            ("E5", 2), ("B4", 1), ("E5", 1),
            ("A4", .5), ("C5", .5), ("E5", .5), ("A5", .5), ("B5", .5), ("A5", .5), ("E5", .5), ("A5", .5),
            ("C6", 1.5), ("A5", .5), ("F5", 1), ("C5", 1),
            ("B5", .5), ("A5", .5), ("G5", .5), ("D5", .5), ("G5", 1), ("B5", 1),
            ("G#5", 2), ("E5", 1), ("B4", 1),
        ]),
}


def use(name: str):
    """Setzt Tempo, Akkorde und Melodie der gewählten Komposition."""
    global BPM, BEAT, BAR, CHORDS, MELODY, rng
    c = COMPOSITIONS[name]
    BPM = c["bpm"]
    BEAT = 60 / BPM
    BAR = 4 * BEAT
    CHORDS, MELODY = c["chords"], c["melody"]
    rng = np.random.default_rng(c["seed"])
    return c


OSTINATO = [0, 0, 12, 0, 7, 0, 12, 7]                      # Streicher-Achtel (Intervalle)
TAIKO = [(0, 1.0), (0.75, 0.45), (1.5, 0.6), (2, 0.9), (2.75, 0.45), (3.5, 0.7)]


def supersaw(freq, n, voices=7, spread=0.18, width=0.9):
    """Mehrere leicht verstimmte Sägezähne, breit im Stereobild."""
    out = np.zeros((n, 2))
    for i in range(voices):
        x = (i / (voices - 1)) * 2 - 1 if voices > 1 else 0
        f = freq * 2 ** (x * spread / 12)
        v = saw(f, n, rng.random())
        out += stereo(v, x * width)
    return out / voices


def formant_choir(x_st):
    """Grober Vokal „Aah": zwei Formant-Bänder."""
    return bandpass(x_st, 600, 1000) * 1.0 + bandpass(x_st, 1050, 1400) * 0.6 + bandpass(x_st, 2400, 3000) * 0.2


def compressor(x, thresh=0.25, ratio=3.0):
    env = lowpass(np.abs(x).max(axis=1), 8)
    env = np.maximum(env, 1e-6)
    gain = np.where(env > thresh, (thresh / env) ** (1 - 1 / ratio), 1.0)
    gain = lowpass(gain, 15)
    return x * gain[:, None]


def build(total_s):
    n = int(total_s * SR)
    B = {k: np.zeros((n, 2)) for k in ("strings", "choir", "lead", "osti", "brass")}
    M = {k: np.zeros(n) for k in ("bass", "kick", "taiko", "snare", "hats", "crash", "fx", "kenv")}

    for bar in range(BARS):
        ch = CHORDS[bar % 8]
        t0 = bar * BAR
        sec = bar % 8

        # Streicher/Supersaw-Fläche + Chor
        ln = int((BAR + 1.0) * SR)
        env = adsr(ln, 0.12, 2.0, 0.85, 0.5, BAR)
        for note in ch["pad"]:
            v = supersaw(hz(m(note)), ln) * env[:, None] * 0.06
            i = int(t0 * SR); j = min(i + ln, n)
            B["strings"][i:j] += v[: j - i]
            cv = supersaw(hz(m(note)), ln, voices=5, spread=0.12) * adsr(ln, 0.45, 2.0, 0.9, 0.6, BAR)[:, None] * 0.08
            B["choir"][i:j] += cv[: j - i]

        # Blech-Stoß auf Schlag 1 (Akkord, kurzer Filter-Anschlag)
        ln = int(0.9 * SR)
        st_env = adsr(ln, 0.01, 0.25, 0.25, 0.2, 0.45)
        for note in ch["pad"][1:4]:
            v = supersaw(hz(m(note)), ln, voices=3, spread=0.08) * st_env[:, None]
            v = lowpass(v, 2200) * 0.12 * (1.3 if sec in (0, 4) else 1.0)
            i = int(t0 * SR); j = min(i + ln, n)
            B["brass"][i:j] += v[: j - i]

        # Streicher-Ostinato (Achtel, spiccato)
        for k in range(8):
            note = m(ch["bass"]) + 12 + OSTINATO[k]
            ln = int(0.3 * SR)
            v = supersaw(hz(note), ln, voices=3, spread=0.1) * adsr(ln, 0.004, 0.1, 0.0, 0.05, 0.12)[:, None]
            i = int((t0 + k * BEAT / 2) * SR); j = min(i + ln, n)
            B["osti"][i:j] += v[: j - i] * (0.11 if k % 2 == 0 else 0.08)

        # Bass: pulsierende Achtel + Sub
        for k in range(8):
            ln = int(BEAT / 2 * SR)
            f = hz(m(ch["bass"]))
            v = (saw(f, ln) * 0.6 + np.sin(2 * np.pi * f * np.arange(ln) / SR) * 0.3)
            v *= adsr(ln, 0.004, 0.15, 0.5, 0.04, BEAT / 2 - 0.03)
            place(M["bass"], v * 0.45, t0 + k * BEAT / 2)

        # Kick (1 & 3) + Taiko-Muster
        for b in (0, 2):
            ln = int(0.45 * SR); t = np.arange(ln) / SR
            f = 45 + 120 * np.exp(-t * 32)
            v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
            v += bandpass(rng.standard_normal(ln), 2500, 5000) * np.exp(-t * 150) * 0.25
            place(M["kick"], v, t0 + b * BEAT)
            place(M["kenv"], np.exp(-t * 7), t0 + b * BEAT)
        for b, vel in TAIKO:
            ln = int(0.7 * SR); t = np.arange(ln) / SR
            f = 62 + 70 * np.exp(-t * 18)
            v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5) * 0.7
            v += bandpass(rng.standard_normal(ln), 180, 1200) * np.exp(-t * 20) * 0.9
            place(M["taiko"], v * vel, t0 + b * BEAT)
        # Taiko-Wirbel am Ende jedes 8-Takt-Abschnitts
        if sec == 7:
            for k in range(8):
                ln = int(0.4 * SR); t = np.arange(ln) / SR
                f = 70 + 70 * np.exp(-t * 20)
                v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
                v += bandpass(rng.standard_normal(ln), 200, 1200) * np.exp(-t * 30) * 0.5
                place(M["taiko"], v * (0.35 + 0.08 * k), t0 + 2 * BEAT + k * BEAT / 4)

        # Snare 2 & 4
        for b in (1, 3):
            ln = int(0.35 * SR); t = np.arange(ln) / SR
            v = bandpass(rng.standard_normal(ln), 1000, 7000) * np.exp(-t * 15) + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 22) * 0.6
            place(M["snare"], v * 0.6, t0 + b * BEAT)
        # Hi-Hats Sechzehntel
        for k in range(16):
            ln = int(0.05 * SR); t = np.arange(ln) / SR
            v = highpass(rng.standard_normal(ln), 8000) * np.exp(-t * 90)
            place(M["hats"], v * (0.09 if k % 4 == 2 else 0.045), t0 + k * BEAT / 4)

        # Crash + BRAAM + Sub-Drop am Abschnittsanfang
        if sec in (0, 4):
            ln = int(3.0 * SR); t = np.arange(ln) / SR
            place(M["crash"], highpass(rng.standard_normal(ln), 4500) * np.exp(-t * 1.6) * 0.35, t0)
        if sec == 0:
            ln = int(3.5 * SR); t = np.arange(ln) / SR
            braam = sum(saw(hz(m(nm)) * 2 ** (d / 12), ln, rng.random())
                        for nm in ("D1", "D2", "A2", "D3") for d in (-0.12, 0.0, 0.12))
            braam = np.tanh(braam * 0.9) * np.exp(-t * 1.1) * np.minimum(t / 0.015, 1)
            braam = highpass(lowpass(braam, 1400), 70) * 0.5
            sub = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.5) + 40) / SR) * np.exp(-t * 2.5) * 0.2
            place(M["fx"], braam + sub, t0)
        # Riser in den nächsten Abschnitt (letzter Takt vor Takt 5 bzw. 1)
        if sec in (3, 7):
            ln = int(BAR * SR); t = np.linspace(0, 1, ln)
            noise = bandpass(rng.standard_normal(ln), 800, 6000) * t ** 2.2 * 0.25
            f = 200 + 1600 * t ** 2
            tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * t ** 2 * 0.08
            place(M["fx"], noise + tone, t0)

    # Lead-Melodie (zweimal), Supersaw + Oktave tiefer
    for rep in range(BARS // 8):
        t = rep * 8 * BAR
        for note, beats in MELODY:
            dur = beats * BEAT
            if note:
                ln = int((dur + 0.6) * SR)
                f = hz(m(note))
                v = supersaw(f, ln, voices=5, spread=0.1, width=0.5) * 0.8
                v += stereo(square(f / 2, ln, 0.4)) * 0.12
                v *= adsr(ln, 0.015, 0.5, 0.8, 0.28, dur - 0.03)[:, None]
                i = int(t * SR); j = min(i + ln, n)
                B["lead"][i:j] += v[: j - i] * 0.22
            t += dur

    return B, M


def render(path: str | None = None, comp: str = "vice_anthem") -> str:
    from .music import tape  # gleiche Kassetten-Wärme, nur dezenter
    c = use(comp)
    path = path or c["out"]
    total = BARS * BAR
    B, M = build(total + 3.0)
    n = len(M["bass"])
    duck = 1 - 0.35 * np.clip(lowpass(M["kenv"], 40), 0, 1)

    strings = highpass(lowpass(B["strings"], 4200), 140) * duck[:, None]
    choir = formant_choir(B["choir"]) * 1.2
    brass = highpass(B["brass"], 180)
    osti = highpass(lowpass(B["osti"], 3000), 160)
    lead = highpass(lowpass(B["lead"], 7000), 220)
    lead_fx = pingpong(lead.mean(axis=1), 0.75 * BEAT, 0.35, 4)
    bass = highpass(lowpass(M["bass"], 900), 45) * duck

    snare_room = convolve_st(M["snare"], reverb_ir(0.5, 7000, 5))
    gate = np.zeros(n)
    for bar in range(BARS):
        for b in (1, 3):
            i = int((bar * BAR + b * BEAT) * SR)
            a = int(0.32 * SR); r = int(0.05 * SR)
            gate[i:i + a] = 1
            gate[i + a:i + a + r] = np.linspace(1, 0, r)[: max(0, min(r, n - i - a))]
    snare = stereo(M["snare"]) * 0.7 + snare_room * gate[:, None] * 0.9
    taiko = highpass(convolve_st(M["taiko"], reverb_ir(1.2, 2500, 7)) * 0.35 + stereo(M["taiko"]) * 0.8, 55)

    dry = (strings * 1.4 + choir * 1.3 + brass * 1.6 + osti * 1.5 + lead * 3.0 + lead_fx * 0.8
           + stereo(bass) * 0.30 + stereo(M["kick"]) * 0.30 + taiko * 0.45 + snare * 0.9
           + stereo(M["hats"], 0.2) * 1.8 + stereo(M["crash"], -0.2) * 1.1 + stereo(M["fx"]) * 0.8)
    send = strings * 0.25 + choir * 0.5 + lead * 0.45 + brass * 0.3 + stereo(M["crash"]) * 0.2
    wet = convolve_st(send, reverb_ir(3.2, 5000, 11))
    mix = dry + wet * 0.45

    mix = highpass(mix, 50)
    mix = compressor(mix / np.max(np.abs(mix)), thresh=0.3, ratio=2.5)
    mix = tape(mix, wow_depth=0.0009, flutter_depth=0.0002)
    mix = lowpass(mix, 15000)

    L = int(total * SR)                      # Hall-Ausklang auf den Anfang legen -> nahtlose Schleife
    tail = mix[L:]
    mix = mix[:L].copy()
    mix[: len(tail)] += tail
    mix /= np.max(np.abs(mix)) / 0.89
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return path


def load(comp: str = "vice_anthem") -> np.ndarray:
    path = COMPOSITIONS[comp]["out"]
    if not os.path.exists(path):
        render(path, comp)
    with wave.open(path, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2)
    return data.astype(np.float64) / 32767


if __name__ == "__main__":
    import sys
    print(render(comp=sys.argv[1] if len(sys.argv) > 1 else "chase"))
