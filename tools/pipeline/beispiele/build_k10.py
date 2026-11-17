"""K10 „GTA 6 Online“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k10/words.json"))
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
END = r(END_VOICE + 1.8)                             # Nachlauf nach „Folg mir!“

# Sätze: 0 GTA 6 Online … 1 Vergiss es 2 GTA 6 startet … 3 Ein Datum … 4 Laut Twitch-Chef … 5 Ob Anfang …
#        6 Mit wem … 7 Schreib's … 8 Die Lösung 9 Das alte GTA Online … 10 und bis dahin … 11 Folg mir
t_story, t_datum, t_twitch, t_ob, t_kom, t_schreib, t_sol, t_und, t_folg = s(2), s(3), s(4), s(5), s(6), s(7), s(8), s(10), s(11)
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_story, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 ONLINE?", "size": 136, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Nicht am Donnerstag!", "size": 72, "at": rel(w(1, 0, 0), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_kom, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "KEIN ONLINE? · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kom, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "MIT WEM ZOCKST DU? · SCHREIB'S MIR", "size": 30}]})
# 2 Nur Story
el(t_story, t_datum, rows=[
    {"type": "title", "text": "Zum Start", "size": 84, "color": "accent", "at": 0.05},
    {"type": "big", "text": "NUR STORY", "size": 160, "at": rel(w(2, 1, 3), t_story), "motion": "punch"}])
# 3 Kein Datum
el(t_datum, t_twitch, rows=[
    {"type": "big", "text": "KEIN DATUM", "size": 150, "at": rel(w(3, 0, 1), t_datum), "motion": "punch"},
    {"type": "text", "text": "von Rockstar", "size": 48, "color": "cream", "at": rel(w(3, 2, 1), t_datum)}])
# 4 2027 laut Twitch-Chef
el(t_twitch, t_kom, rows=[
    {"type": "title", "text": "Laut Twitch-Chef", "size": 84, "color": "accent", "at": 0.05},
    {"type": "big", "text": "2027", "size": 200, "at": rel(w(4, 2, 0), t_twitch), "motion": "punch"},
    {"type": "text", "text": "Anfang oder Ende?\nGerüchte widersprechen sich", "size": 42, "color": "cream",
     "at": rel(w(5, 0, 0), t_twitch)}])
# 5 Kommentar-Frage
el(t_kom, t_sol, rows=[
    {"type": "title", "text": "Mit wem zockst du?", "size": 100, "at": 0.05, "motion": "punch"}])
# 6 Lösung
el(t_sol, t_folg, y=540, gap=22, pad=46, rows=[
    {"type": "title", "text": "Die Lösung", "size": 80, "color": "accent", "at": 0.05},
    {"type": "pills", "items": ["GTA Online (alt) läuft weiter"], "psize": 46, "ph": 100,
     "at": rel(w(9, 0, 0), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["Zeit für die Story"], "psize": 46, "ph": 100,
     "at": rel(w(10, 1, 2), t_sol), "motion": "punch"}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Story oder\nOnline?", "size": 110, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_story, t_datum, t_twitch, t_ob, t_kom, t_schreib, t_sol, t_und, t_folg, END]
SH = [(T2, 34.66, 38.33, 0.5),     # Hook + Vergiss es: Fahrt Fahrerperspektive
      (T2, 66.25, 69.15, 0.6),     # Nur Story: Parkplatz (nicht über 69.15)
      (T1, 76.60, 78.38, 0.5),     # Kein Datum von Rockstar: Türeingang
      (T1, 2.72, 4.96, 0.5),       # 2027: Highway Sonnenuntergang
      (T2, 83.15, 85.06, 0.5),     # Anfang oder Ende: Steg/Meer Sonnenuntergang
      (T2, 96.18, 97.62, 0.5),     # Mit wem zocken: Party auf Yacht
      (T1, 21.79, 23.23, 0.5),     # Schreib's in die Kommentare: voller Strand
      (T2, 141.88, 143.69, 0.5),   # Lösung / altes GTA Online: Motorrad
      (L, 40.48, 42.29, 0.5),      # Zeit für die Story: Jason & Lucia am Auto
      (T2, 38.42, 41.56, 0.5)]     # Folg mir + Abschluss: Strand-Fitness
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835, "lufs": -14,
        "voice": {"wav": "content/02-kanal/voice/k10/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 0, 0) - 0.4 - LEAD)},
                {"t": rel(w(1, 0, 0), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 1, 3), 0), "type": "pop"},
                {"t": rel(w(3, 0, 1), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(3, 2, 1), 0), "type": "pop"},
                {"t": rel(w(4, 2, 0), 0), "type": "hit", "gain": 0.6}, {"t": rel(w(5, 0, 0), 0), "type": "pop"},
                {"t": r(t_kom + 0.05), "type": "pop"},
                {"t": rel(w(9, 0, 0), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(9, 0, 0), 0), "type": "chime"},
                {"t": rel(w(10, 1, 2), 0), "type": "pop"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_story, t_twitch, t_kom, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k10.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
