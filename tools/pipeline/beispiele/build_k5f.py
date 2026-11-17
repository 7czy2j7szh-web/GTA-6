"""K5 final „GTA 6 Geld“: Gemini-Clip 1 (Einstieg) → Sprecherstimme über Trailer-Szenen (3 Regeln) → Gemini-Clip 2 (Lösung, Weglaufen)."""
import json, os, subprocess, wave
import numpy as np
R = "/home/user/GTA-6/"
SR = 48000
r = lambda v: round(v, 3)
C1, C2 = "assets/host/gen/k5_b.mp4", "assets/host/gen/k5_a.mp4"
A_END = 7.85                      # Einstieg bis hier (nach „musst!“ + kurzes Nicken)
VO_T = r(A_END + 0.1)             # Sprecherstimme startet
VO_LEN = 7.65
C2_A, C2_B = 0.35, 10.02          # Clip 2 ohne die stumme erste Drittelsekunde
C2_T = r(VO_T + VO_LEN + 0.15)
CLIP_END = r(C2_T + C2_B - C2_A)
TAIL = 2.0
DUR = r(CLIP_END + TAIL)
T_WALK = r(C2_T + 7.3 - C2_A)
segs = [{"src": C1, "a": 0.0, "b": A_END, "t": 0.0}, {"src": C2, "a": C2_A, "b": C2_B, "t": C2_T}]

def aud(p, sr_in=None):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", R + p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
def norm(x, target=0.16):
    v = x[np.abs(x) > 0.02]
    return x / (np.sqrt(np.mean(v ** 2)) or 1) * target
a1 = norm(aud(C1)[:int(A_END * SR)])
vo = norm(aud("content/02-kanal/voice/k5vo/voice.wav"))
a2 = norm(aud(C2)[int(C2_A * SR):int(C2_B * SR)])
f = int(0.02 * SR); a1[-f:] *= np.linspace(1, 0, f); a2[:f] *= np.linspace(0, 1, f)
g = int(0.6 * SR); a2[-g:] *= np.linspace(1, 0, g) ** 1.5                  # Schritte am Ende ausblenden
y = np.zeros(int(DUR * SR) + SR, np.float32)
def put(sig, t):
    i = int(round(t * SR)); y[i:i + len(sig)] += sig
put(a1, 0.0); put(vo, VO_T); put(a2, C2_T)
y = y[:int(DUR * SR)]
y = y / max(np.abs(y).max(), 1e-6) * 0.9
os.makedirs(R + "content/02-kanal/voice/k5final", exist_ok=True)
VOICE = "content/02-kanal/voice/k5final/voice.wav"
w = wave.open(R + VOICE, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()

def words_of(name, off, shift=0.0):
    d = json.load(open(R + f"content/02-kanal/voice/{name}/words.json"))
    return [[[[wd, r(t - shift + off)] for wd, t in pg] for pg in snt] for snt in d["sent"]]
SENT = words_of("k5c1", 0.0) + words_of("k5vo", VO_T) + words_of("k5c2", C2_T, C2_A)
pages = [pg for snt in SENT for pg in snt]
words = [w_ for pg in pages for w_ in pg]
def wt(name, k=0):
    return [t for wd, t in words if wd.rstrip("!?.,:") == name][k]
LEAD = 0.04
subs = []
for i, pg in enumerate(pages):
    s0 = pg[0][1] - LEAD
    nxt = pages[i + 1][0][1] - LEAD if i + 1 < len(pages) else 1e9
    s1 = min(nxt, pg[-1][1] + 0.85)
    subs.append({"t": r(max(s0, 0)), "end": r(s1), "words": [[wd, r(max(t - LEAD, 0))] for wd, t in pg]})
rel = lambda t, base: r(t - base - LEAD)
t_drei, t_r1, t_r2, t_r3 = r(wt("Drei") - 0.1), r(wt("Erstens") - 0.1), r(wt("Zweitens") - 0.1), r(wt("Drittens") - 0.1)
t_sol, t_und, t_folg = r(wt("Die") - 0.1), r(wt("Und") - 0.1), r(wt("Folg") - 0.1)
print("Drei", t_drei, "R1", t_r1, "R2", t_r2, "R3", t_r3, "Lösung", t_sol, "Und", t_und, "Folg", t_folg,
      "Walk", T_WALK, "Clip-Ende", CLIP_END, "Dauer", DUR)
CY = 550
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)
# Suchbegriff ab dem ersten Bild
el(0.0, t_drei, card=False, gap=12, y=560, rows=[
    {"type": "big", "text": "GTA 6 GELD", "size": 180, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Das musst du wissen", "size": 80, "at": 0.35}])
el(t_drei, A_END, rows=[
    {"type": "big", "text": "3 REGELN", "size": 190, "at": 0.05, "motion": "punch"},
    {"type": "text", "text": "die du vor dem Start kennen musst", "size": 40, "color": "cream", "at": rel(wt("Start"), t_drei)}])
E.append({"t": 2.6, "end": t_r2, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "WIE SCHÜTZT DU DEIN GELD? · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_r2, "end": C2_T, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "SCHON MAL ALLES VERLOREN? · SCHREIB'S MIR", "size": 30}]})
el(t_r1, t_r2, rows=[
    {"type": "pills", "items": ["REGEL 1"], "psize": 40, "ph": 90, "at": 0.05, "motion": "punch"},
    {"type": "strike", "text": "BARGELD", "size": 170, "at": rel(wt("Bargeld"), t_r1), "strike_at": r(wt("weg") - wt("Bargeld"))},
    {"type": "text", "text": "weg, wenn du stirbst · laut Previews", "size": 36, "color": "second", "at": rel(wt("wenn"), t_r1)}])
el(t_r2, t_r3, rows=[
    {"type": "pills", "items": ["REGEL 2 · BEUTE"], "psize": 40, "ph": 90, "at": 0.05, "motion": "punch"},
    {"type": "big", "text": "0 $", "size": 170, "at": rel(wt("Beute"), t_r2), "motion": "punch"},
    {"type": "text", "text": "bis der Hehler sie kauft", "size": 44, "color": "cream", "at": rel(wt("Hehler"), t_r2)}])
el(t_r3, C2_T, rows=[
    {"type": "pills", "items": ["REGEL 3 · STORY"], "psize": 40, "ph": 90, "at": 0.05, "motion": "punch"},
    {"type": "big", "text": "GESPERRT", "size": 170, "at": rel(wt("nicht"), t_r3), "motion": "punch"},
    {"type": "text", "text": "bis du genug Geld hast · laut Preview-Bericht", "size": 32, "color": "second",
     "at": rel(wt("weiter"), t_r3)}])
el(t_sol, t_und, rows=[
    {"type": "title", "text": "Die Lösung", "size": 100, "color": "accent", "at": 0.05},
    {"type": "big", "text": "EINZAHLEN!", "size": 150, "at": rel(wt("einzahlen"), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["Bank = sicher"], "psize": 44, "ph": 100, "at": rel(wt("einzahlen"), t_sol) + 0.4,
     "motion": "punch"}])
el(t_und, r(T_WALK - 0.1), rows=[
    {"type": "title", "text": "Was kaufst du dir\nals Erstes?", "size": 92, "at": 0.05},
    {"type": "glowpill", "text": "Schreib's in die Kommentare", "size": 40, "at": 0.45, "motion": "punch"}])
el(t_folg, DUR, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(r(CLIP_END - 0.3), DUR, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Was kaufst du dir\nals Erstes?", "size": 96, "at": 0.05, "motion": "punch"}])
E.append({"t": r(CLIP_END), "end": DUR, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})
V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, 2.2, t_drei, A_END, t_r2, t_r3, C2_T, t_und, r(T_WALK - 0.1), DUR]
SH = [(T1, 68.72, 70.23, 0.5), (T1, 76.60, 78.38, 0.5), (T2, 66.25, 69.15, 0.6), (T2, 141.88, 143.69, 0.5),
      (T1, 37.49, 39.76, 0.42), (L, 40.48, 42.29, 0.47), (T2, 38.42, 41.56, 0.55), (T1, 2.72, 4.96, 0.5),
      (T2, 34.66, 38.33, 0.5)]
scenes = []
for k_, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k_], cuts[k_ + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k_, src.split("/")[-1][6:], ss, r(a), r(b), sp)
spec = {"duration": DUR, "fps": 24, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 2.5,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835,
        "voice": {"wav": VOICE, "t": 0.0}, "subs": subs, "elements": E, "scenes": scenes,
        "greenclip": {"segments": segs, "scale": 1.35, "top": 770,
                      "moves": [{"t0": r(T_WALK - 0.2), "t1": r(T_WALK + 1.1), "top": 230, "scale": 1.35}],
                      "fade_out": [r(CLIP_END - 0.35), r(CLIP_END + 0.2)]},
        "music": "chase", "duck": 21,
        "sfx": [{"t": r(wt("Achtung") - LEAD), "type": "hit", "gain": 0.5},
                {"t": r(wt("Dein")), "type": "riser", "len": r(wt("Drei") - wt("Dein"))},
                {"t": r(wt("Drei") - LEAD), "type": "hit", "gain": 0.6},
                {"t": r(t_r1 + 0.1), "type": "pop"}, {"t": r(wt("weg") - LEAD), "type": "hit", "gain": 0.5},
                {"t": r(t_r2 + 0.1), "type": "pop"}, {"t": r(wt("Beute") - LEAD), "type": "pop"},
                {"t": r(t_r3 + 0.1), "type": "pop"}, {"t": r(wt("nicht") - LEAD), "type": "hit", "gain": 0.5},
                {"t": r(wt("einzahlen") - LEAD), "type": "hit", "gain": 0.5}, {"t": r(wt("einzahlen") - LEAD), "type": "chime"},
                {"t": r(t_und + 0.3), "type": "pop"}, {"t": r(t_folg + 0.3), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [A_END, C2_T]]}
json.dump(spec, open(R + "content/02-kanal/specs/k5f.json", "w"), ensure_ascii=False, indent=1)
print("Seiten", len(subs), "Elemente", len(E))
