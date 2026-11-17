"""K7 „GTA 6 Xbox One“ – Kanal-Format ohne Moderatorin: Trailer-Szenen, Plum-Karten, Wort-Untertitel."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k7/words.json"))
SENT = D["sent"]
VOICE_END = D["dur"]
LEAD = 0.04
r = lambda v: round(v, 3)
pages = [pg for snt in SENT for pg in snt]
WS = [t for pg in pages for _, t in pg]              # Wortzeiten nach Index
def w(i): return WS[i]
def s(i): return r(w(i) - 0.1)                        # Satzanfang (Schnitt/Kartenwechsel)
def rel(t, base): return r(t - base - LEAD)

t_hook, t_geht = 0.0, s(6)
t_ms, t_haken, t_h2, t_kom = s(9), s(22), s(33), s(42)
t_pc, t_sol, t_step, t_folg = s(50), s(58), s(64), s(74)
T_Q = r(w(75) + 0.3)                                   # Abschlussfrage nach „Folg mir!“
END = r(VOICE_END + 1.9)

subs = []
for i, pg in enumerate(pages):
    s0 = pg[0][1] - LEAD
    nxt = pages[i + 1][0][1] - LEAD if i + 1 < len(pages) else 1e9
    s1 = min(nxt, pg[-1][1] + 0.85)
    if i + 1 == len(pages):
        s1 = min(s1, T_Q)                              # keine Überlappung mit der Abschlussfrage
    subs.append({"t": r(max(s0, 0)), "end": r(s1), "words": [[wd, r(max(t - LEAD, 0))] for wd, t in pg]})

CY = 550
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
el(0.0, t_ms, card=False, gap=18, y=560, motion="none", rows=[      # schon im ersten Bild sichtbar
    {"type": "title", "text": "GTA 6 auf der", "size": 96, "color": "accent", "at": -0.5},
    {"type": "big", "text": "XBOX ONE?", "size": 190, "at": -0.3, "motion": "punch"},
    {"type": "big", "text": "GEHT!", "size": 150, "at": rel(w(6), 0), "motion": "punch"}])
# Oben: FOMO-Pille, dann Kommentar-Aufforderung
E.append({"t": 2.5, "end": t_kom, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "ES GIBT EINEN HAKEN · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_kom, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "WELCHE KONSOLE? · SCHREIB'S MIR", "size": 30}]})
# 2 Cloud Gaming
el(t_ms, t_haken, rows=[
    {"type": "title", "text": "Xbox Cloud Gaming", "size": 96, "color": "accent", "at": 0.05},
    {"type": "big", "text": "AB 7 UHR", "size": 170, "at": rel(w(12), t_ms), "motion": "punch"},
    {"type": "text", "text": "19.11. · Series-S-Grafik · 30 FPS · laut Xbox", "size": 36, "color": "second",
     "at": rel(w(20), t_ms)}])
# 3 Haken 1
el(t_haken, t_h2, rows=[
    {"type": "pills", "items": ["HAKEN 1"], "psize": 40, "ph": 90, "at": 0.05, "motion": "punch"},
    {"type": "big", "text": "SPIEL KAUFEN", "size": 140, "at": rel(w(26), t_haken), "motion": "punch"},
    {"type": "text", "text": "Game Pass schaltet GTA 6 nicht frei", "size": 40, "color": "cream",
     "at": rel(w(31), t_haken)}])
# 4 Haken 2
el(t_h2, t_kom, y=560, gap=18, pad=50, rows=[
    {"type": "pills", "items": ["HAKEN 2"], "psize": 38, "ph": 84, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Cloud-Stunden je Abo", "size": 80, "color": "accent", "at": rel(w(35), t_h2)},
    {"type": "pills", "items": ["Essential 5", "Premium 10", "Ultimate 15"], "psize": 34, "ph": 80, "gap": 14,
     "at": rel(w(39), t_h2), "motion": "punch"},
    {"type": "text", "text": "Stunden Cloud-Zeit · laut Eurogamer", "size": 34, "color": "second",
     "at": rel(w(41), t_h2)}])
# 5 Kommentar-Teil
el(t_kom, t_pc, rows=[
    {"type": "title", "text": "Welche Konsole hast du?", "size": 76, "color": "accent", "at": 0.05},
    {"type": "pills", "items": ["PS5", "SERIES X|S"], "psize": 40, "ph": 90, "at": rel(w(43), t_kom), "motion": "punch"},
    {"type": "pills", "items": ["XBOX ONE", "PS4"], "psize": 40, "ph": 90, "at": rel(w(43), t_kom) + 0.25,
     "motion": "punch"}])
# 6 PS4 & PC
el(t_pc, t_sol, rows=[
    {"type": "strike", "text": "PS4 & PC", "size": 180, "at": rel(w(51), t_pc), "strike_at": r(w(56) - w(51))},
    {"type": "text", "text": "bisher nichts angekündigt", "size": 44, "color": "cream", "at": rel(w(55), t_pc)}])
# 7 Lösung
el(t_sol, t_folg, y=525, gap=14, pad=48, rows=[
    {"type": "title", "text": "Die Lösung", "size": 84, "color": "accent", "at": 0.05},
    {"type": "pills", "items": ["1 Spiel kaufen"], "psize": 44, "ph": 90, "at": rel(w(64), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["2 Game Pass aktiv"], "psize": 44, "ph": 90, "at": rel(w(66), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["3 Do. ab 7 Uhr streamen"], "psize": 44, "ph": 90, "at": rel(w(69), t_sol),
     "motion": "punch"}])
# 8 Ende: + Folgen, Abschlussfrage, Pfeil
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": rel(w(74), t_folg), "motion": "punch"}])
el(T_Q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Zockst du\nin der Cloud?", "size": 116, "at": 0.0, "motion": "punch"}])
E.append({"t": r(T_Q + 0.3), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_ms, t_haken, t_h2, t_kom, t_pc, t_sol, t_step, t_folg, END]
SH = [(L, 55.22, 57.03, 0.45),      # Strand mit Flugzeug
      (T2, 38.42, 41.56, 0.55),     # Strand-Fitness
      (L, 40.48, 42.29, 0.47),      # Jason & Lucia am Auto
      (T2, 83.15, 85.06, 0.5),      # Steg/Meer Sonnenuntergang
      (T1, 21.79, 23.23, 0.5),      # voller Strand
      (T2, 141.88, 143.69, 0.5),    # Motorrad
      (T2, 6.85, 8.09, 0.5),        # Insel von oben
      (T1, 37.49, 39.76, 0.42),     # Dachterrasse
      (T2, 96.18, 97.62, 0.45)]     # Party auf Yacht (dunkler: Abschlussfrage gut lesbar)
scenes = []
for k_, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k_], cuts[k_ + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k_, src.split("/")[-1][6:], ss, r(a), r(b), sp)

spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835,
        "voice": {"wav": "content/02-kanal/voice/k7/final.wav", "t": 0.0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.3, "type": "riser", "len": r(w(6) - LEAD - 0.3)},
                {"t": rel(w(6), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(12), 0), "type": "pop"},
                {"t": r(t_haken + 0.05), "type": "pop"}, {"t": rel(w(26), 0), "type": "hit", "gain": 0.5},
                {"t": r(t_h2 + 0.05), "type": "pop"}, {"t": rel(w(39), 0), "type": "pop"},
                {"t": rel(w(43), 0), "type": "pop"},
                {"t": rel(w(56), 0), "type": "hit", "gain": 0.5},
                {"t": rel(w(59), 0), "type": "chime"},
                {"t": rel(w(64), 0), "type": "pop"}, {"t": rel(w(66), 0), "type": "pop"},
                {"t": rel(w(69), 0), "type": "hit", "gain": 0.4},
                {"t": rel(w(74), 0), "type": "pop"}, {"t": r(T_Q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_ms, t_haken, t_pc, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k7.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Seiten", len(subs), "Elemente", len(E), "Kommentar ab", t_kom, "Lösung ab", t_sol, "Frage", T_Q)
