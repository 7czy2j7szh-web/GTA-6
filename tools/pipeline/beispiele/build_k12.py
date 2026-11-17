"""K12 „GTA 6 PC“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k12/words.json"))
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
END = r(END_VOICE + 1.9)                             # Nachlauf nach „mir!“

t_rock, t_xbox, t_vgl, t_rdr, t_kon, t_schreib, t_sol, t_folg = s(2), s(3), s(4), s(6), s(7), s(8), s(9), s(11)
t_aus = r(w(3, 2, 0) - 0.08)                          # Schnitt bei „lässt PC-Spieler außen vor“
t_remote = r(w(10, 2, 0) - 0.08)                      # Schnitt bei „Remote Play“
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_rock, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 PC?", "size": 170, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Nicht am Donnerstag!", "size": 84, "at": rel(w(1, 0, 0), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_kon, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "PC-SPIELER AUFGEPASST · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kon, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "PC ODER KONSOLE? · SCHREIB'S MIR", "size": 30}]})
# 2 Nicht angekündigt
el(t_rock, t_xbox, gap=16, rows=[
    {"type": "big", "text": "NICHT ANGEKÜNDIGT", "size": 108, "at": 0.05, "motion": "punch"},
    {"type": "text", "text": "laut Rockstar bisher keine PC-Version", "size": 40, "color": "cream",
     "at": rel(w(2, 1, 0), t_rock)}])
# 3 Xbox Cloud Gaming ohne PC
el(t_xbox, t_vgl, gap=16, rows=[
    {"type": "title", "text": "Xbox Cloud Gaming", "size": 88, "color": "accent", "at": 0.05},
    {"type": "strike", "text": "PC", "size": 170, "at": rel(w(3, 2, 0), t_xbox),
     "strike_at": r(w(3, 3, 0) - w(3, 2, 0))},
    {"type": "text", "text": "nur Xbox-Konsolen", "size": 42, "color": "cream", "at": rel(w(3, 3, 0), t_xbox)}])
# 4 Zum Vergleich
el(t_vgl, t_kon, gap=22, rows=[
    {"type": "title", "text": "Zum Vergleich", "size": 92, "color": "accent", "at": 0.05},
    {"type": "pills", "items": ["GTA 5: +19 Monate"], "psize": 50, "ph": 104, "at": rel(w(5, 1, 0), t_vgl), "motion": "punch"},
    {"type": "pills", "items": ["RDR 2: +1 Jahr"], "psize": 50, "ph": 104, "bg": "second",
     "at": rel(w(6, 0, 0), t_vgl), "motion": "punch"}])
# 5 Kommentar-Frage
el(t_kon, t_sol, rows=[
    {"type": "pills", "items": ["PC", "KONSOLE"], "psize": 56, "ph": 116, "gap": 34, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Wie zockst du?", "size": 100, "at": rel(w(7, 1, 0), t_kon)}])
# 6 Lösung
el(t_sol, t_folg, y=540, gap=16, pad=46, rows=[
    {"type": "title", "text": "Die Lösung", "size": 84, "color": "accent", "at": 0.05},
    {"type": "big", "text": "REMOTE PLAY", "size": 130, "at": rel(w(10, 0, 0), t_sol), "motion": "punch"},
    {"type": "text", "text": "mit PS5 auf dem PC spielen", "size": 42, "color": "cream", "at": rel(w(10, 1, 0), t_sol)}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Wartest du auf\ndie PC-Version?", "size": 96, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_rock, t_xbox, t_aus, t_vgl, t_rdr, t_kon, t_schreib, t_sol, t_remote, t_folg, END]
SH = [(T1, 2.72, 4.96, 0.5),       # Hook: Highway Sonnenuntergang
      (T2, 66.25, 69.15, 0.6),     # Nicht angekündigt: Parkplatz (nicht über 69.15)
      (T2, 6.85, 8.09, 0.5),       # Xbox Cloud Gaming: Insel von oben
      (T1, 76.60, 78.38, 0.5),     # PC-Spieler außen vor: Türeingang (danach Logo)
      (T2, 38.42, 41.56, 0.55),    # Zum Vergleich GTA 5: Strand-Fitness
      (T2, 141.88, 143.69, 0.5),   # Red Dead 2: Motorrad
      (L, 40.48, 42.29, 0.5),      # PC oder Konsole: Jason & Lucia am Auto
      (T2, 96.18, 97.62, 0.5),     # Schreib's in die Kommentare: Party auf Yacht
      (L, 55.22, 57.03, 0.45),     # Die Lösung: Strand mit Doppeldecker
      (T1, 21.79, 23.23, 0.5),     # Remote Play: voller Strand
      (T2, 83.15, 85.06, 0.5)]     # Folg mir + Abschluss: Steg/Meer
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835, "lufs": -14,
        "voice": {"wav": "content/02-kanal/voice/k12/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 0, 0) - 0.4 - LEAD)},
                {"t": rel(w(1, 0, 0), 0), "type": "hit", "gain": 0.6},
                {"t": r(t_rock + 0.05), "type": "pop"}, {"t": rel(w(2, 1, 0), 0), "type": "pop"},
                {"t": r(t_xbox + 0.05), "type": "pop"}, {"t": rel(w(3, 3, 0), 0), "type": "hit", "gain": 0.5},
                {"t": r(t_vgl + 0.05), "type": "pop"},
                {"t": rel(w(5, 1, 0), 0), "type": "pop"}, {"t": rel(w(6, 0, 0), 0), "type": "pop"},
                {"t": r(t_kon + 0.05), "type": "pop"},
                {"t": rel(w(10, 0, 0), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(10, 0, 0), 0), "type": "chime"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_rock, t_vgl, t_kon, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k12.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
