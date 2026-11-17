"""K5 „GTA 6 Geld“ – Vorlage (2D-Moderatorin + Platzhalter-Stimme), Such-Video."""
import json
R = "/home/user/GTA-6/"
D = json.load(open(R + "content/02-kanal/voice/k5/words.json"))
T0 = 0.7                                             # erst nach vorne beugen, dann „Achtung!“
SENT = D["sent"]
END_VOICE = T0 + D["dur"]
LEAD = 0.04
r = lambda v: round(v, 3)
def w(si, pi=0, wi=0): return r(SENT[si][pi][wi][1] + T0)
def s(si): return r(w(si) - 0.08)
def rel(t, base): return r(t - base - LEAD)
T_TURN = r(w(6, 0, 1) + 0.45)
END = r(T_TURN + 2.6)
pages = [[(wd, t + T0) for wd, t in pg] for snt in SENT for pg in snt]
subs = []
for i, pg in enumerate(pages):
    t0 = pg[0][1] - LEAD
    t1 = pages[i + 1][0][1] - LEAD if i + 1 < len(pages) else END_VOICE + 0.3
    subs.append({"t": r(t0), "end": r(t1), "words": [[wd, r(t - LEAD)] for wd, t in pg]})
t_loot, t_story, t_sol, t_cta = s(2), s(3), s(4), s(6)
CY = 515
E = []
def el(t, end, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": CY, "rows": rows}; e.update(kw); E.append(e)
# Suchbegriff steht ab dem ersten Bild im Bild
el(0.0, t_loot, rows=[
    {"type": "title", "text": "GTA 6 Geld", "size": 100, "color": "accent", "at": 0.1},
    {"type": "strike", "text": "BARGELD", "size": 170, "at": 0.3, "strike_at": rel(w(1, 1, 3), 0) - 0.3},
    {"type": "text", "text": "weg, wenn du stirbst · laut Previews", "size": 36, "color": "second", "at": rel(w(1, 2), 0)}])
E.append({"t": 2.4, "end": t_story, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "WIE SCHÜTZT DU DEIN GELD? · LÖSUNG AM ENDE", "size": 30}]})
el(t_loot, t_story, rows=[
    {"type": "title", "text": "Deine Beute", "size": 100, "color": "accent", "at": 0.05},
    {"type": "big", "text": "0 $", "size": 170, "at": rel(w(2, 0, 1), t_loot), "motion": "punch"},
    {"type": "text", "text": "bis der Hehler sie kauft", "size": 44, "color": "cream", "at": rel(w(2, 1, 2), t_loot)}])
E.append({"t": t_story, "end": t_sol, "y": 282, "card": False, "motion": "punch",
          "rows": [{"type": "glowpill", "text": "SCHON MAL ALLES VERLOREN? · SCHREIB'S MIR", "size": 30}]})
el(t_story, t_sol, rows=[
    {"type": "title", "text": "Story-Missionen", "size": 100, "color": "accent", "at": 0.05},
    {"type": "big", "text": "GESPERRT", "size": 170, "at": rel(w(3, 2), t_story), "motion": "punch"},
    {"type": "text", "text": "bis du genug Geld hast · laut Preview-Bericht", "size": 32, "color": "second",
     "at": rel(w(3, 2), t_story) + 0.35}])
el(t_sol, t_cta, rows=[
    {"type": "title", "text": "Die Lösung", "size": 100, "color": "accent", "at": 0.05},
    {"type": "big", "text": "EINZAHLEN!", "size": 150, "at": rel(w(5, 0, 1), t_sol), "motion": "punch"},
    {"type": "pills", "items": ["Bank = sicher"], "psize": 44, "ph": 100, "at": rel(w(5, 0, 1), t_sol) + 0.35,
     "motion": "punch"}])
el(t_cta, END, card=False, gap=28, y=520, exit=False, rows=[
    {"type": "title", "text": "Was kaufst du dir\nals Erstes?", "size": 88, "at": 0.05},
    {"type": "glowpill", "text": "+ Folgen", "size": 56, "at": 0.3, "motion": "punch"}])
E.append({"t": r(t_cta + 0.4), "end": END, "y": 1200, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 180, "nudge": 14}]})

V = "assets/official/video/"
L, T1, T2 = V + "GTAVI_Launch_Trailer.mp4", V + "GTAVI_Trailer_1.mp4", V + "GTAVI_Trailer_2.mp4"
cuts = [0.0, 2.0, t_loot, t_story, t_sol, t_cta, END]
SH = [(T1, 68.72, 70.23, 0.5), (T1, 76.60, 78.38, 0.5), (T2, 66.25, 69.15, 0.6), (T2, 141.88, 143.69, 0.5),
      (T2, 38.42, 41.56, 0.5), (T1, 2.72, 4.96, 0.5)]
scenes = []
for k, (src, ss, se, x) in enumerate(SH):
    a, b = cuts[k], cuts[k + 1]
    sp = min(1.0, round((se - ss - 0.03) / (b - a), 3))
    scenes.append({"clip": src, "ss": ss, "start": r(a), "end": r(b), "cam": {"x": x, "zoom": [1.0, 1.05], "speed": sp}})
    print(k, src.split("/")[-1][6:], ss, r(a), r(b), sp)
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.2, "grade": {"contrast": 1.08, "sat": 1.1},
        "sub_y": 840, "voice": {"wav": "content/02-kanal/voice/k5/final.wav", "t": T0}, "subs": subs, "elements": E,
        "scenes": scenes,
        "presenter": {"views": {"front": "assets/host/host_cut.png", "side": "assets/host/side_cut.png",
                                "back": "assets/host/back_cut.png"}, "x0": 600, "head_y": 925,
                      "actions": [
                          {"t": 0.0, "gesture": "lean", "dur": 1.6, "amount": 1.0},
                          {"t": r(w(1, 1, 3) - 0.1), "gesture": "nod", "dur": 0.6},
                          {"t": r(w(2, 1, 2) - 0.2), "gesture": "present", "dur": 1.4},
                          {"t": r(w(3, 2) - 0.1), "look": [0, -1], "dur": 0.8},
                          {"t": r(w(4, 0, 1) - 0.2), "gesture": "point", "dur": 1.3},
                          {"t": r(w(6) - 0.15), "gesture": "glass", "dur": 0.9},
                          {"t": T_TURN, "turn": "back", "dur": 0.35},
                          {"t": r(T_TURN + 0.8), "walk": -320, "speed": 520}]},
        "music": "chase",
        "sfx": [{"t": 0.3, "type": "riser", "len": r(w(1, 1, 3) - T0 - 0.3 + T0)},
                {"t": rel(w(1, 1, 3), 0), "type": "hit", "gain": 0.6},
                {"t": rel(w(2, 0, 1), 0), "type": "pop"},
                {"t": rel(w(3, 2), 0), "type": "hit", "gain": 0.5},
                {"t": rel(w(5, 0, 1), 0), "type": "hit", "gain": 0.5}, {"t": rel(w(5, 0, 1), 0), "type": "chime"},
                {"t": r(t_cta + 0.3), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.6} for c in [t_loot, t_sol]]}
json.dump(spec, open(R + "content/02-kanal/specs/k5.json", "w"), ensure_ascii=False, indent=1)
print("Dauer", END, "Seiten", len(subs), "Elemente", len(E), "Hälfte 2 ab", t_story)
