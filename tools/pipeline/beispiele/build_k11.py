"""K11 „GTA 6 Code fehlt“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k11/words.json"))
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

# Sätze: 0 GTA 6 Box gekauft? | 1 Prüf sofort den Code! | 2 Manche Käufer melden … benutzt. | 3 Und eine Disc …
# 4 Wie oft … Einzelfälle. | 5 Box oder digital … | 6 Schreib's … | 7 Die Lösung: | 8 Box und Kassenbon … | 9 zuerst …
# 10 dann zum Rockstar Support. | 11 Und deinen Code nie online zeigen! | 12 Folg mir!
t_pruef, t_kaeuf, t_disc, t_oft, t_kom, t_schreib, t_sol = s(1), s(2), s(3), s(4), s(5), s(6), s(7)
t_haendler, t_nie, t_folg = s(9), s(11), s(12)
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_kaeuf, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 CODE", "size": 150, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Fehlt er bei dir?", "size": 80, "at": rel(w(0, 0, 2), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_kom, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "PRÜF DEINEN CODE · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kom, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "BOX ODER DIGITAL? · SCHREIB'S MIR", "size": 30}]})
# 2 Berichte: fehlt / schon benutzt
el(t_kaeuf, t_disc, rows=[
    {"type": "text", "text": "Berichte von Käufern:", "size": 46, "color": "cream", "at": 0.05},
    {"type": "pills", "items": ["FEHLT"], "psize": 60, "ph": 120, "at": rel(w(2, 1, 2), t_kaeuf), "motion": "punch"},
    {"type": "pills", "items": ["SCHON BENUTZT"], "psize": 60, "ph": 120, "bg": "second",
     "at": rel(w(2, 3, 0), t_kaeuf), "motion": "punch"}])
# 3 Keine Disc
el(t_disc, t_oft, rows=[
    {"type": "big", "text": "KEINE DISC", "size": 140, "at": rel(w(3, 0, 2), t_disc), "motion": "punch"},
    {"type": "text", "text": "nur Download-Code in der Box", "size": 42, "color": "cream",
     "at": rel(w(3, 1, 0), t_disc)}])
# 4 Wie oft? Unklar
el(t_oft, t_kom, rows=[
    {"type": "title", "text": "Wie oft?", "size": 96, "color": "accent", "at": 0.05},
    {"type": "big", "text": "UNKLAR", "size": 170, "at": rel(w(4, 2, 1), t_oft), "motion": "punch"},
    {"type": "text", "text": "bisher Einzelfälle · laut Berichten", "size": 40, "color": "cream",
     "at": rel(w(4, 3, 0), t_oft)}])
# 5 Kommentar-Frage
el(t_kom, t_sol, rows=[
    {"type": "pills", "items": ["BOX", "DIGITAL"], "psize": 56, "ph": 116, "gap": 34, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Was hast du?", "size": 100, "at": rel(w(5, 1, 0), t_kom)}])
# 6 Lösung
el(t_sol, t_folg, y=515, gap=14, pad=42, rows=[
    {"type": "title", "text": "Die Lösung", "size": 80, "color": "accent", "at": 0.05},
    {"type": "pills", "items": ["1  Box + Bon fotografieren"], "psize": 42, "ph": 78,
     "at": rel(w(8, 0, 0), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["2  Händler"], "psize": 42, "ph": 78, "bg": "second",
     "at": rel(w(9, 0, 0), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["3  Rockstar Support"], "psize": 42, "ph": 78,
     "at": rel(w(10, 0, 0), t_sol), "motion": "punch"},
    {"type": "text", "text": "Code nie online zeigen!", "size": 46, "color": "cream",
     "at": rel(w(11, 0, 0), t_sol)}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Hat dein Code\ngeklappt?", "size": 100, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_pruef, t_kaeuf, t_disc, t_oft, t_kom, t_schreib, t_sol, t_haendler, t_nie, t_folg, END]
SH = [(T1, 68.72, 70.23, 0.5),     # Hook Box gekauft: Ladenüberfall
      (T1, 47.58, 48.56, 0.5),     # Prüf den Code: Überwachungskamera
      (T2, 34.66, 38.33, 0.5),     # Käufer melden: Fahrt Fahrerperspektive
      (T1, 2.72, 4.96, 0.5),       # Keine Disc: Highway Sonnenuntergang
      (T2, 66.25, 69.15, 0.6),     # Wie oft: Parkplatz (nicht über 69.15)
      (L, 40.48, 42.29, 0.5),      # Box oder digital: Jason & Lucia am Auto
      (T2, 96.18, 97.62, 0.5),     # Schreib's in die Kommentare: Party auf Yacht
      (T1, 37.49, 39.76, 0.5),     # Die Lösung + Fotografieren: Dachterrasse/Pool
      (T2, 38.42, 41.56, 0.5),     # Händler + Rockstar Support: Strand-Fitness
      (T2, 141.88, 143.69, 0.5),   # Code nie online zeigen: Motorrad
      (L, 55.22, 57.03, 0.5)]      # Folg mir + Abschluss: Strand mit Doppeldecker
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835, "lufs": -14,
        "voice": {"wav": "content/02-kanal/voice/k11/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 1, 1) - 0.4 - LEAD)},
                {"t": rel(w(1, 1, 1), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 1, 2), 0), "type": "pop"}, {"t": rel(w(2, 3, 0), 0), "type": "pop"},
                {"t": rel(w(3, 0, 2), 0), "type": "hit", "gain": 0.5},
                {"t": rel(w(4, 2, 1), 0), "type": "pop"},
                {"t": r(t_kom + 0.05), "type": "pop"},
                {"t": r(t_sol + 0.05), "type": "hit", "gain": 0.5}, {"t": r(t_sol + 0.05), "type": "chime"},
                {"t": rel(w(8, 0, 0), 0), "type": "pop"}, {"t": rel(w(9, 0, 0), 0), "type": "pop"},
                {"t": rel(w(10, 0, 0), 0), "type": "pop"}, {"t": rel(w(11, 0, 0), 0), "type": "pop"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_kaeuf, t_kom, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k11.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
