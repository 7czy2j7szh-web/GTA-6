"""K8 „GTA 6 Test“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k8/words.json"))
T0 = 0.1                                             # Stimme setzt fast sofort ein, Suchbegriff ab Bild 1
SENT = D["sent"]
END_VOICE = T0 + D["dur"]
LEAD = 0.04
r = lambda v: round(v, 3)
def w(si, pi=0, wi=0): return r(SENT[si][pi][wi][1] + T0)
def s(si): return r(w(si) - 0.08)
def rel(t, base): return r(t - base - LEAD)

# Untertitel-Seiten: Ende = min(nächste Seite, letztes Wort + 0.85)
pages = [[(wd, t + T0) for wd, t in pg] for snt in SENT for pg in snt]
subs = []
for i, pg in enumerate(pages):
    s0 = pg[0][1] - LEAD
    nxt = pages[i + 1][0][1] - LEAD if i + 1 < len(pages) else 1e9
    s1 = min(nxt, pg[-1][1] + 0.85)
    subs.append({"t": r(max(s0, 0)), "end": r(s1), "words": [[wd, r(max(t - LEAD, 0))] for wd, t in pg]})
LAST_SUB = subs[-1]["end"]
END = r(END_VOICE + 1.8)                             # Nachlauf nach „Zahlen!“

t_mor, t_ins, t_rock, t_meta, t_kom, t_schreib, t_sol, t_nicht, t_folg = s(1), s(2), s(3), s(4), s(5), s(6), s(7), s(9), s(10)
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_ins, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 TEST", "size": 160, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Morgen fallen die Wertungen", "size": 64, "at": rel(w(1, 0, 0), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_kom, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "WAS TAUGT GTA 6? · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kom, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "DEIN TIPP? · SCHREIB'S MIR", "size": 30}]})
# 2 Test-Sperre
el(t_ins, t_rock, rows=[
    {"type": "title", "text": "Test-Sperre endet", "size": 84, "color": "accent", "at": 0.05},
    {"type": "big", "text": "MI 18.11.", "size": 160, "at": rel(w(2, 2, 1), t_ins), "motion": "punch"},
    {"type": "text", "text": "laut Insider · nicht bestätigt", "size": 40, "color": "cream",
     "at": rel(w(2, 3, 0), t_ins)}])
# 3 Vorbilder GTA 5 / RDR 2
el(t_rock, t_meta, rows=[
    {"type": "pills", "items": ["GTA 5", "RDR 2"], "psize": 56, "ph": 116, "gap": 34, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Tests am Tag vor Release", "size": 64, "at": 0.3}])
# 4 Metacritic
el(t_meta, t_kom, rows=[
    {"type": "title", "text": "Metacritic", "size": 92, "color": "accent", "at": 0.05},
    {"type": "big", "text": "6,5?", "size": 190, "at": rel(w(4, 3, 1), t_meta), "motion": "punch"},
    {"type": "text", "text": "nur 5 Nutzerstimmen · wieder weg", "size": 40, "color": "cream",
     "at": rel(w(4, 3, 1), t_meta) + 0.35}])
# 5 Kommentar-Frage
el(t_kom, t_sol, rows=[
    {"type": "title", "text": "Dein Tipp?", "size": 100, "at": 0.05},
    {"type": "pills", "items": ["90+", "95+", "100"], "psize": 56, "ph": 116, "gap": 34,
     "at": rel(w(5, 1, 0), t_kom), "motion": "punch"}])
# 6 Lösung
el(t_sol, t_folg, y=540, gap=22, pad=46, rows=[
    {"type": "title", "text": "Die Lösung", "size": 80, "color": "accent", "at": 0.05},
    {"type": "big", "text": "PRESSE-WERTUNG", "size": 104, "at": rel(w(8, 1, 2), t_sol), "motion": "punch"},
    {"type": "strike", "text": "ein paar Nutzer", "size": 64, "at": rel(w(9, 0, 0), t_sol),
     "strike_at": r(w(9, 1, 2) - w(9, 0, 0))}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Welche Wertung\ntippst du?", "size": 100, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_mor, t_ins, t_rock, t_meta, t_kom, t_schreib, t_sol, t_nicht, t_folg, END]
SH = [(T1, 68.72, 70.23, 0.5),     # Hook: Ladenüberfall
      (T1, 2.72, 4.96, 0.5),       # Morgen fallen …: Highway Sonnenuntergang
      (T2, 66.25, 69.15, 0.6),     # Test-Sperre: Parkplatz (nicht über 69.15)
      (T1, 76.60, 78.38, 0.5),     # Rockstar bestätigt nicht: Türeingang
      (T2, 34.66, 38.33, 0.5),     # Metacritic: Fahrt Fahrerperspektive
      (T1, 37.49, 39.76, 0.5),     # Was tippst du: Dachterrasse/Pool
      (L, 55.22, 57.03, 0.5),      # Schreib's in die Kommentare: Strand mit Doppeldecker
      (T2, 60.62, 62.85, 0.5),     # Lösung: Jason am Zaun (vor Schnitt ~62.9)
      (L, 40.48, 42.29, 0.5),      # nicht auf ein paar Nutzer: Jason & Lucia am Auto
      (T2, 38.42, 41.56, 0.5)]     # Folg mir + Abschluss: Strand-Fitness
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835, "lufs": -14,
        "voice": {"wav": "content/02-kanal/voice/k8/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 1, 2) - 0.4 - LEAD)},
                {"t": rel(w(1, 1, 2), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 2, 1), 0), "type": "pop"},
                {"t": r(t_rock + 0.05), "type": "pop"},
                {"t": rel(w(4, 3, 1), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(5, 1, 0), 0), "type": "pop"},
                {"t": rel(w(8, 1, 2), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(8, 1, 2), 0), "type": "chime"},
                {"t": rel(w(9, 1, 2), 0), "type": "pop"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_ins, t_meta, t_kom, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k8.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
