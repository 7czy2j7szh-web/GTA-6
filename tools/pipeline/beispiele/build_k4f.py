"""K4 final: zwei Gemini-Clips (Einstieg mit Masken, Auflösung vor Grün), Karten an ihr Sprechtempo angepasst."""
import json, os, subprocess, wave
import numpy as np
S = "/tmp/claude-0/-home-user-GTA-6/4314e1e5-1e22-5471-9026-26079bdb67ff/scratchpad"
R = "/home/user/GTA-6/"
SR = 48000
r = lambda v: round(v, 3)
C1, C2 = "assets/host/gen/k4_c2.mp4", "assets/host/gen/k4_c1.mp4"          # C1 = Einstieg, C2 = Auflösung
A_END = 9.5                                                                 # Einstieg bis hier
B_END = 10.02
TAIL = 2.0
segs = [{"src": C1, "a": 0.0, "b": A_END, "t": 0.0, "mask_dir": "assets/host/gen/k4_c2_masks"},
        {"src": C2, "a": 0.0, "b": B_END, "t": A_END}]
CLIP_END = r(A_END + B_END)
DUR = r(CLIP_END + TAIL)
def aud(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", R + p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
a1, a2 = aud(C1)[:int(A_END * SR)], aud(C2)[:int(B_END * SR)]
a1 = a1 / (np.abs(a1).max() or 1); a2 = a2 / (np.abs(a2).max() or 1)
f = int(0.02 * SR); a1[-f:] *= np.linspace(1, 0, f); a2[:f] *= np.linspace(0, 1, f)
g = int(0.6 * SR); a2[-g:] *= np.linspace(1, 0, g) ** 1.5                  # Schritte am Ende ausblenden
y = np.concatenate([a1, a2, np.zeros(int(TAIL * SR), np.float32)]) * 0.9
os.makedirs(R + "content/02-kanal/voice/k4f", exist_ok=True)
VO = "content/02-kanal/voice/k4f/voice.wav"
w = wave.open(R + VO, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
WD = json.load(open(S + "/gen/k4_words.json"))
words = [(wd, t) for wd, t in WD["2"]] + [(wd, r(t + A_END)) for wd, t in WD["1"]]
T = {wd + str(i): t for i, (wd, t) in enumerate(words)}
def wt(name, k=0):
    hits = [t for wd, t in words if wd.rstrip("!?.,:") == name]
    return hits[k]
PAGES = [["Halt", "dich", "fest:"], ["GTA", "6", "hat"], ["angeblich", "rund"], ["fünfzig", "Stunden", "Story."],
         ["Und", "für", "Platin?"], ["Über", "zweihundert"], ["Stunden!"],
         ["Zwei", "Stunden", "am"], ["Tag?"], ["Dann", "bist", "du"], ["Mitte", "Dezember"], ["durch."],
         ["Platin?"], ["Erst", "Ende", "Februar."], ["Folg", "mir!"]]
pages, k = [], 0
for pg in PAGES:
    pages.append([[words[k + i][0], words[k + i][1]] for i in range(len(pg))]); k += len(pg)
assert k == len(words), (k, len(words))
seg_end = {0: 1.35, 1: 5.6, 2: 9.35}
LEAD = 0.04
subs = []
for i, pg in enumerate(pages):
    s0 = pg[0][1] - LEAD
    nxt = pages[i + 1][0][1] - LEAD if i + 1 < len(pages) else 1e9
    s1 = min(nxt, pg[-1][1] + 0.85)
    subs.append({"t": r(max(s0, 0)), "end": r(s1), "words": [[wd, r(max(t - LEAD, 0))] for wd, t in pg]})
t_gta, t_und, t_zwei, t_platin2, t_folg = wt("GTA") - 0.1, wt("Und") - 0.1, A_END, wt("Platin", 1) - 0.1, wt("Folg") - 0.1
T_WALK = r(A_END + 7.75)
print("GTA", t_gta, "Und", t_und, "Platin2", t_platin2, "Folg", t_folg, "Walk", T_WALK, "Dauer", DUR)
CY = 550
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)
rel = lambda t, base: r(t - base - LEAD)
el(0.0, t_gta, card=False, gap=10, y=560, rows=[
    {"type": "title", "text": "Wie lange dauert", "size": 96, "at": 0.12},
    {"type": "big", "text": "GTA 6?", "size": 250, "at": 0.45, "motion": "punch"}])
el(t_gta, t_und, rows=[
    {"type": "title", "text": "Story", "size": 100, "color": "accent", "at": 0.05},
    {"type": "count", "to": 50, "suffix": " STUNDEN", "size": 170, "at": 0.3, "dur": r(wt("fünfzig") - t_gta - 0.2)},
    {"type": "text", "text": "laut Insider Tom Henderson", "size": 34, "color": "second", "at": rel(wt("Story"), t_gta)}])
E.append({"t": 2.6, "end": r(A_END + 0.2), "y": 300, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "WANN BIST DU FERTIG? · GLEICH", "size": 30}]})
el(t_und, A_END, rows=[
    {"type": "title", "text": "Für Platin", "size": 100, "color": "accent", "at": 0.05},
    {"type": "count", "to": 200, "prefix": "über ", "suffix": " STD.", "size": 170, "at": 0.3, "dur": r(wt("zweihundert") - t_und - 0.1)},
    {"type": "text", "text": "mit allen Nebenaufgaben", "size": 36, "color": "second", "at": rel(wt("Stunden", 1), t_und)}])
el(A_END, t_platin2, rows=[
    {"type": "pills", "items": ["2 Stunden am Tag"], "psize": 44, "ph": 100, "at": 0.15, "motion": "punch"},
    {"type": "text", "text": "Story durch am", "size": 44, "color": "cream", "at": 0.45},
    {"type": "big", "text": "13. DEZ.", "size": 200, "at": rel(wt("Mitte"), A_END), "motion": "punch"}])
el(t_platin2, t_folg, rows=[
    {"type": "title", "text": "Platin am", "size": 100, "color": "accent", "at": 0.05},
    {"type": "big", "text": "26. FEB.", "size": 200, "at": rel(wt("Ende"), t_platin2), "motion": "punch"},
    {"type": "text", "text": "2027 – ab Release gerechnet", "size": 34, "color": "second", "at": rel(wt("Februar"), t_platin2)}])
el(t_folg, DUR, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(r(CLIP_END - 0.3), DUR, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Wie lange zockst du\nam ersten Tag?", "size": 96, "at": 0.05, "motion": "punch"}])
E.append({"t": r(CLIP_END), "end": DUR, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})
V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, r(t_gta), 4.0, r(t_und), A_END, r(A_END + 2.1), r(t_platin2), r(t_folg), DUR]
SH = [(L, 26.42, 27.79, 0.42), (T1, 2.72, 4.96, 0.5), (L, 55.22, 57.03, 0.45), (T2, 38.42, 41.56, 0.55),
      (T1, 37.49, 39.76, 0.42), (T2, 141.88, 143.69, 0.5), (T2, 66.25, 69.15, 0.6), (T2, 34.66, 38.33, 0.5)]
scenes = []
for k_, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k_], cuts[k_ + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k_, src.split("/")[-1][6:], ss, r(a), r(b), sp)
spec = {"duration": DUR, "fps": 24, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 2.5,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835,
        "voice": {"wav": VO, "t": 0.0}, "subs": subs, "elements": E, "scenes": scenes,
        "greenclip": {"segments": segs, "scale": 1.35, "top": 770,
                      "moves": [{"t0": r(T_WALK - 0.2), "t1": r(T_WALK + 1.1), "top": 230, "scale": 1.35}],
                      "fade_out": [r(CLIP_END - 0.35), r(CLIP_END + 0.2)]},
        "music": "chase", "duck": 21,
        "sfx": [{"t": 0.45, "type": "hit", "gain": 0.5}, {"t": r(t_gta + 0.3), "type": "riser", "len": r(wt("fünfzig") - t_gta - 0.2)},
                {"t": r(wt("zweihundert") - LEAD), "type": "hit", "gain": 0.6},
                {"t": r(wt("Mitte") - LEAD), "type": "pop"}, {"t": r(wt("Ende") - LEAD), "type": "hit", "gain": 0.5},
                {"t": r(wt("Ende") - LEAD), "type": "chime"}, {"t": r(t_folg + 0.3), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_und, A_END]]}
json.dump(spec, open(R + "content/02-kanal/specs/k4f.json", "w"), ensure_ascii=False, indent=1)
print("Seiten", len(subs), "Elemente", len(E))
