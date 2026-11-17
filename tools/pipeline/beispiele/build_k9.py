"""K9 „GTA 6 Deutsch“ – Kanal-Format ohne Moderatorin: Gemini-Stimme über Trailer-Szenen."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k9/words.json"))
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

t_stim, t_deu, t_off, t_daf, t_eng, t_schreib, t_sol, t_folg = s(2), s(3), s(4), s(5), s(6), s(7), s(8), s(11)
t_unc = r(w(5, 4, 0) - 0.08)                          # Schnitt bei „und nach allem …“ (ungeschnitten)
t_q = r(LAST_SUB)                                     # Abschlussfrage erst nach dem letzten Untertitel
CY = 560
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)

# 1 Suchbegriff ab dem ersten Bild
HOOK = -0.22                                         # Element startet vor Bild 1: Suchbegriff ab t=0 voll sichtbar
el(HOOK, t_stim, card=False, gap=14, y=560, motion="none", rows=[
    {"type": "big", "text": "GTA 6 DEUTSCH?", "size": 128, "at": 0.0, "motion": "punch"},
    {"type": "title", "text": "Nicht ganz!", "size": 84, "at": rel(w(1, 0, 0), HOOK)}])
# Oben: FOMO-Pille, dann Kommentar-Pille
E.append({"t": 2.5, "end": t_eng, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "VERSTEHST DU ALLES? · LÖSUNG AM ENDE", "size": 30}]})
E.append({"t": t_eng, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "ENGLISCH ODER SYNCHRO? · SCHREIB'S MIR", "size": 30}]})
# 2 Sprachausgabe
el(t_stim, t_deu, rows=[
    {"type": "title", "text": "Sprachausgabe", "size": 92, "color": "accent", "at": 0.05},
    {"type": "big", "text": "ENGLISCH", "size": 170, "at": rel(w(2, 1, 0), t_stim), "motion": "punch"}])
# 3 Deutsch nur Menüs + Untertitel (unbestätigt)
el(t_deu, t_daf, rows=[
    {"type": "pills", "items": ["Menüs: Deutsch"], "psize": 50, "ph": 104, "at": rel(w(3, 1, 1), t_deu), "motion": "punch"},
    {"type": "pills", "items": ["Untertitel: Deutsch"], "psize": 50, "ph": 104, "bg": "second",
     "at": rel(w(3, 2, 1), t_deu), "motion": "punch"},
    {"type": "text", "text": "laut Release-Infos · nicht offiziell bestätigt", "size": 34, "color": "cream",
     "at": rel(w(4, 0, 0), t_deu)}])
# 4 USK 18 + ungeschnitten?
el(t_daf, t_eng, gap=16, rows=[
    {"type": "big", "text": "USK 18", "size": 160, "at": 0.05, "motion": "punch"},
    {"type": "text", "text": "PS5 & Xbox Series · laut USK", "size": 40, "color": "cream", "at": rel(w(5, 3, 1), t_daf)},
    {"type": "pills", "items": ["UNGESCHNITTEN?"], "psize": 50, "ph": 100, "at": rel(w(5, 4, 0), t_daf), "motion": "punch"},
    {"type": "text", "text": "sehr wahrscheinlich, nicht bestätigt", "size": 36, "color": "cream",
     "at": rel(w(5, 5, 0), t_daf)}])
# 5 Kommentar-Frage
el(t_eng, t_sol, rows=[
    {"type": "pills", "items": ["ENGLISCH", "SYNCHRO"], "psize": 56, "ph": 116, "gap": 34, "at": 0.05, "motion": "punch"},
    {"type": "title", "text": "Was willst du?", "size": 100, "at": rel(w(6, 2, 0), t_eng)}])
# 6 Lösung
el(t_sol, t_folg, y=540, gap=16, pad=46, rows=[
    {"type": "title", "text": "Die Lösung", "size": 84, "color": "accent", "at": 0.05},
    {"type": "big", "text": "UNTERTITEL AN", "size": 118, "at": rel(w(9, 0, 0), t_sol), "motion": "punch"}])
# 7 Ende
el(t_folg, END, card=False, y=330, exit=False, rows=[
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.05, "motion": "punch"}])
el(t_q, END, card=False, y=820, exit=False, rows=[
    {"type": "title", "text": "Englisch oder\nSynchro?", "size": 100, "at": 0.0, "motion": "punch"}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, t_stim, t_deu, t_off, t_daf, t_unc, t_eng, t_schreib, t_sol, t_folg, END]
SH = [(T1, 2.72, 4.96, 0.5),       # Hook: Highway Sonnenuntergang
      (L, 40.48, 42.29, 0.47),     # Stimmen englisch: Jason & Lucia am Auto
      (T1, 37.49, 39.76, 0.42),    # Menüs/Untertitel: Dachterrasse
      (T1, 39.85, 41.29, 0.5),     # nicht offiziell bestätigt: VICE-Schriftzug
      (T2, 66.25, 69.15, 0.6),     # USK 18: Parkplatz (nicht über 69.15)
      (T1, 68.72, 70.23, 0.5),     # ungeschnitten: Ladenüberfall
      (T2, 60.62, 62.85, 0.5),     # Englisch oder Synchro: Jason am Zaun (vor Schnitt ~62.9)
      (T2, 96.18, 97.62, 0.45),    # Schreib's in die Kommentare: Yacht
      (T2, 34.66, 38.33, 0.5),     # Lösung: Fahrt Fahrerperspektive
      (T2, 83.15, 85.06, 0.5)]     # Folg mir + Abschluss: Steg/Meer
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), "speed", sp, "Quelle bis", r(ss + sp * (b - a)))
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.25, "bg_blur": 0,
        "grade": {"contrast": 1.06, "sat": 1.08}, "sub_y": 835, "lufs": -14,
        "voice": {"wav": "content/02-kanal/voice/k9/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": "chase", "duck": 21,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5},
                {"t": 0.4, "type": "riser", "len": r(w(1, 0, 0) - 0.4 - LEAD)},
                {"t": rel(w(1, 0, 0), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 1, 0), 0), "type": "pop"},
                {"t": rel(w(3, 1, 1), 0), "type": "pop"}, {"t": rel(w(3, 2, 1), 0), "type": "pop"},
                {"t": r(t_daf + 0.05), "type": "hit", "gain": 0.5},
                {"t": rel(w(5, 4, 0), 0), "type": "pop"},
                {"t": r(t_eng + 0.05), "type": "pop"},
                {"t": rel(w(9, 0, 0), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(9, 0, 0), 0), "type": "chime"},
                {"t": r(t_folg + 0.05), "type": "pop"}, {"t": r(t_q), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_stim, t_daf, t_eng, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k9.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Stimme bis", r(END_VOICE), "letzter UT bis", LAST_SUB, "Seiten", len(subs), "Elemente", len(E))
print("Schnitte", cuts)
