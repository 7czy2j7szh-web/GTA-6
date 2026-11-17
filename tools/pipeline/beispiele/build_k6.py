"""K6 „GTA 6 Update“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k6/words.json"))
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

t_rock, t_auf, t_was, t_kom, t_sol, t_dann, t_folg = s(2), s(3), s(4), s(5), s(7), s(10), s(11)
t_schreib = s(6)
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_rock, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 UPDATE", "size": 150, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Vorgeladen reicht nicht!", "size": 74, "at": rel(w(0, 0, 2), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_kom, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "IST DEINE KONSOLE BEREIT? · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kom, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "PS5 ODER XBOX? · SCHREIB'S MIR", "size": 30}]})
# 2 Zweites Update
el(t_rock, t_auf, rows=[
    {"type": "title", "text": "Update Nr. 2", "size": 92, "color": "accent", "at": 0.05},
    {"type": "big", "text": "01.002.001", "size": 150, "at": rel(w(2, 1, 1), t_rock), "motion": "punch"},
    {"type": "text", "text": "seit 16.11. · noch vor dem Release", "size": 40, "color": "cream",
     "at": rel(w(2, 2, 1), t_rock)}])
# 3 Größen
el(t_auf, t_was, rows=[
    {"type": "big", "text": "PS5 · 602 MB", "size": 124, "at": rel(w(3, 0, 1), t_auf), "motion": "punch"},
    {"type": "big", "text": "XBOX · 1,6 GB", "size": 124, "at": rel(w(3, 2, 1), t_auf), "motion": "punch"},
    {"type": "text", "text": "Update 1 kam schon am 13.11.", "size": 40, "color": "cream",
     "at": rel(w(3, 3, 1), t_auf)}])
# 4 Keine Patchnotes
el(t_was, t_kom, rows=[
    {"type": "big", "text": "???", "size": 190, "at": 0.05, "motion": "punch"},
    {"type": "text", "text": "keine Patchnotes von Rockstar", "size": 44, "color": "cream",
     "at": rel(w(4, 1, 0), t_was)}])
# 5 Kommentar-Frage
el(t_kom, t_sol, rows=[
    {"type": "pills", "items": ["PS5", "XBOX"], "psize": 56, "ph": 116, "gap": 34, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Was zockst du?", "size": 100, "at": rel(w(5, 1, 0), t_kom)}])
# 6 Lösung
el(t_sol, t_folg, y=520, gap=16, pad=46, rows=[
    {"type": "title", "text": "Die Lösung", "size": 80, "color": "accent", "at": 0.05},
    {"type": "big", "text": "JETZT PRÜFEN", "size": 120, "at": rel(w(8, 0, 0), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["PS5: Options › Nach Update suchen"], "psize": 38, "ph": 80,
     "at": rel(w(9, 0, 0), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["Xbox: Menü › Spiel verwalten › Updates"], "psize": 38, "ph": 80, "bg": "second",
     "at": rel(w(9, 2, 0), t_sol), "motion": "punch"}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Hast du das\nUpdate schon?", "size": 100, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_rock, t_auf, t_was, t_kom, t_schreib, t_sol, t_folg, END]
SH = [(T1, 68.72, 70.23, 0.5),     # Hook: Überfall im Laden
      (T1, 2.72, 4.96, 0.5),       # Rockstar hat schon …: Highway Sonnenuntergang
      (T2, 66.25, 69.15, 0.6),     # Größen: Parkplatz (nicht über 69.15)
      (T1, 39.85, 41.29, 0.5),     # Was drin ist …: VICE-Schriftzug
      (T2, 81.45, 83.06, 0.55),    # PS5 oder Xbox: Steg
      (T2, 98.52, 99.62, 0.5),     # Schreib's in die Kommentare
      (T2, 34.66, 38.33, 0.5),     # Lösung + Donnerstag: Fahrt Fahrerperspektive
      (L, 26.42, 27.79, 0.42)]     # Folg mir + Abschluss: Cabrio
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835,
        "voice": {"wav": "content/02-kanal/voice/k6/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 0, 2) - 0.4 - LEAD)},
                {"t": rel(w(1, 0, 2), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 1, 1), 0), "type": "pop"},
                {"t": rel(w(3, 0, 1), 0), "type": "pop"}, {"t": rel(w(3, 2, 1), 0), "type": "pop"},
                {"t": r(t_was + 0.05), "type": "hit", "gain": 0.5},
                {"t": r(t_kom + 0.05), "type": "pop"},
                {"t": rel(w(8, 0, 0), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(8, 0, 0), 0), "type": "chime"},
                {"t": rel(w(9, 0, 0), 0), "type": "pop"}, {"t": rel(w(9, 2, 0), 0), "type": "pop"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_rock, t_kom, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k6.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
