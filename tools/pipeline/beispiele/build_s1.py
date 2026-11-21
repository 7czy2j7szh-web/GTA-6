"""S1 „Fustler – nur noch ein Lebkuchen“: Streamer-Clip (mit Erlaubnis von twitch.tv/fustler) mit Originalton.

Ablauf: 1) Clip-Ausschnitte per ffmpeg schneiden und auf 1080x1920@30 skalieren (Sponsor-Logo/-Banner
abgedeckt, Spielszene leicht aufgehellt), 2) Tonspur mischen (Hook-TTS + Originalton angeglichen + Outro-TTS)
-> content/02-kanal/voice/s1/final.wav, 3) Wortzeiten per phrase_align (einmal, gecacht), 4) Spec schreiben.
Aufruf: python3 build_s1.py            (Schritte 1/2 nur, wenn Dateien fehlen; PREP=1 erzwingt sie)
"""
import json, os, subprocess, sys, wave
import numpy as np

R = "/home/user/GTA-6/"
W = os.environ.get("LEONIDA_WORK", R + "work") + "/s1/"
os.makedirs(W, exist_ok=True)
SRC = R + "assets/streamer/fustler/lebkuchen_raw.mp4"
VD = "content/02-kanal/voice/s1/"
CLIP = "work/s1/clip_1080.mp4"
FPS, SR = 30, 48000
r = lambda v: round(v, 3)
snap = lambda v: round(v * FPS) / FPS

# Ausschnitte (Quelle in s). Layout A = oben Webcam/unten Spiel, B = oben Sponsor-Banner/unten Webcam.
# Schnitte nur in Sprechpausen an Satzgrenzen.
SEG = [("A", 0.62, 3.60),     # Hook über der GTA-6-Szene („Aber das sieht echt nicht gesund aus …“ leise darunter)
       ("A", 12.78, 15.35),   # Frau kommt mit der Packung: „Das … zurück ins Regal.“
       ("B", 16.55, 20.10),   # „Das war im Regal gestanden. Ich hab die Packung erst gekauft.“
       ("B", 21.33, 26.08),   # „Einfach nur noch ein f*cking Ding drin. Wollt ihr mich komplett verarschen?“
       ("B", 27.00, None)]    # „Warum, wegen ein Teil schickst du das ganze Ding wieder zurück?“ + Outro
POINTE_END_SRC = 30.43        # Ende von „zurück?“
HOOK_T = 0.10
hook_wav, outro_wav = VD + "hook2.wav", VD + "outro.wav"   # hook2: „Fustler zockt GTA sechs – und dann das!“


def wav_load(p):
    w = wave.open(R + p if not p.startswith("/") else p)
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2).mean(1)
    if w.getframerate() != SR:
        from scipy.signal import resample_poly
        x = resample_poly(x, SR, w.getframerate()).astype(np.float32)
    return x


def wav_save(p, x):
    o = wave.open(p, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()


hook_dur = len(wav_load(hook_wav)) / SR
outro_dur = len(wav_load(outro_wav)) / SR
# Zeitachse: Segmentlängen auf ganze Bilder runden
cuts = [0.0]
for _, a, b in SEG[:-1]:
    cuts.append(r(cuts[-1] + snap(b - a)))
c4 = cuts[-1]
POINTE = r(c4 + POINTE_END_SRC - SEG[-1][1])
OUTRO_T = r(POINTE + 0.7)
END = r(snap(OUTRO_T + outro_dur + 2.0))
segs = [(k, a, r(snap(b - a)) if b else r(END - c4)) for k, a, b in SEG]   # (Layout, Quelle-Start, Dauer)


def prep_video():
    """Ausschnitte schneiden, Logo (Layout A) bzw. Banner (Layout B) abdecken, 1080x1920@30."""
    parts, fc = [], []
    for i, (k, a, d) in enumerate(segs):
        f = f"[0:v]trim=start={a}:duration={d},setpts=PTS-STARTPTS"
        if k == "A":   # yfood-Logo im Webcam-Rahmen entfernen (Glowpill liegt zusätzlich darüber); Nachtszene aufhellen
            f += ",delogo=x=846:y=82:w=350:h=142,eq=brightness=0.035:gamma=1.18"
        else:          # Sponsor-Banner (obere Hälfte bis y=1158 der Quelle) mit Plum-Fläche füllen, Karte liegt darüber
            f += ",drawbox=x=0:y=0:w=iw:h=1158:color=0x4b2f54@1:t=fill"
        fc.append(f + ",scale=1080:1920:flags=lanczos,fps=30,setsar=1" + f"[v{i}]")
        parts.append(f"[v{i}]")
    fc.append("".join(parts) + f"concat=n={len(segs)}:v=1:a=0,format=yuv420p[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[out]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-r", "30", R + CLIP], check=True)


def rms_active(x, rel_db=-30):
    h = int(0.02 * SR); n = len(x) // h
    e = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1))
    act = e > e.max() * 10 ** (rel_db / 20)
    return float(np.sqrt((e[act] ** 2).mean()))


def prep_audio():
    """Originalton der Ausschnitte (Frau leise -> per dynaudnorm angeglichen) + Hook/Outro-TTS -> final.wav."""
    src = W + "src48.wav"
    if not os.path.exists(src):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", str(SR), src], check=True)
    x = wav_load(src)
    n = int(round(END * SR))
    clip = np.zeros(n, np.float32)
    fade = int(0.008 * SR)
    for i, (k, a, d) in enumerate(segs):
        s = x[int(round(a * SR)):int(round((a + d) * SR))].copy()
        s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
        j = int(round(cuts[i] * SR)) if i < len(cuts) else int(round(c4 * SR))
        clip[j:j + len(s)] = s[: n - j]
    hook, outro = wav_load(hook_wav), wav_load(outro_wav)
    tts_rms = rms_active(np.concatenate([hook, outro]))
    # Sprachteil (ab Schnitt 1 bis kurz nach der Pointe): Pegel angleichen
    i0, i1 = int(cuts[1] * SR), int((POINTE + 0.25) * SR)
    sp = W + "speech_in.wav"; spo = W + "speech_norm.wav"
    wav_save(sp, clip[i0:i1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sp, "-af",
                    "highpass=f=90,dynaudnorm=f=150:g=9:p=0.9:m=12:s=0", spo], check=True)
    speech = wav_load(spo)[: i1 - i0]
    speech *= tts_rms / rms_active(speech) * 10 ** (-0.5 / 20)
    out = clip * 0
    out[i0:i0 + len(speech)] = speech
    # Hook-Unterlage: Originalton deutlich unter der TTS-Stimme, kurz vor dem Schnitt ausblenden
    j1 = int(cuts[1] * SR)
    bed = clip[:j1] * (tts_rms * 10 ** (-17 / 20) / rms_active(clip[:j1]))
    fo = int(0.15 * SR); bed[-fo:] *= np.linspace(1, 0, fo)
    out[:j1] = bed
    # Ausklang nach der Pointe: Raumton auf Höhe der Sprechpausen weiterlaufen lassen
    h = int(0.02 * SR)
    e = np.sqrt((speech[: len(speech) // h * h].reshape(-1, h) ** 2).mean(1))
    floor = np.percentile(e, 15)
    tail = clip[i1:]
    tail = tail * (floor / (np.sqrt((tail ** 2).mean()) or 1))
    xf = int(0.1 * SR); tail[:xf] *= np.linspace(0, 1, xf)
    out[i1 - xf:i1] *= np.linspace(1, 0, xf)
    out[i1:] += tail[: n - i1]
    # TTS darüber
    for t, v in [(HOOK_T, hook), (OUTRO_T, outro)]:
        j = int(t * SR); out[j:j + len(v)] += v[: n - j]
    out *= 0.9 / np.max(np.abs(out))
    wav_save(R + VD + "final.wav", out)
    wav_save(W + "speech_aligned.wav", speech / np.max(np.abs(speech)) * 0.9)   # für phrase_align (Offset cuts[1])


if os.environ.get("PREP") or not os.path.exists(R + CLIP):
    prep_video()
if os.environ.get("PREP") or not os.path.exists(R + VD + "final.wav"):
    prep_audio()

# ---- Wortzeiten (Untertitel). Seiten mit 1–4 Wörtern; Anzeige „f*cking“ ----
SENT_CLIP = [[["Das …"], ["zurück", "ins", "Regal."]],
             [["Das", "war"], ["im", "Regal", "gestanden."]],
             [["Ich", "hab", "die", "Packung"], ["erst", "gekauft."]],
             [["Einfach", "nur", "noch"], ["ein", "fucking", "Ding", "drin."]],
             [["Wollt", "ihr", "mich"], ["komplett", "verarschen?"]],
             [["Warum,", "wegen", "ein", "Teil"], ["schickst", "du", "das"], ["ganze", "Ding"], ["wieder", "zurück?"]]]
SENT_OUTRO = [[["Mehr", "GTA-6-Momente?"]], [["Folg", "mir!"]]]
SENT_HOOK = [[["Fustler", "zockt", "GTA", "sechs"], ["und", "dann", "das!"]]]


def syl(wd):
    import re
    v = re.findall(r"[aeiouäöüy]+", wd.lower().replace("gta", "geteah").replace("6", "sechs"))
    return max(1, len(v))


def align(name, wav, sent):
    cache = W + f"s1_{name}_phrase.json"
    words = [(w, syl(w)) for snt in sent for pg in snt for w in pg]
    if not os.path.exists(cache):
        sys.path.insert(0, R + "tools/pipeline")
        import phrase_align as pa
        if not hasattr(pa, "_orig_phrases"):
            pa._orig_phrases = pa.phrases
            pa.phrases = lambda x, sr: pa._orig_phrases(x, sr, min_pause=0.06, min_len=0.45)
        res, rep = pa.run(wav, words, W + f"s1_{name}_ph")
        json.dump({"res": res, "rep": rep}, open(cache, "w"), ensure_ascii=False, indent=0)
        print(name, "match", rep["match_ratio"]); [print("  ", p) for p in rep["phrases"]]
    res = json.load(open(cache))["res"]
    return [(w, t) for (w, _), (_, t) in zip(words, res)]


wc = align("clip", W + "speech_aligned.wav", SENT_CLIP)
wo = align("outro", R + outro_wav, SENT_OUTRO)
wh = align("hook", R + hook_wav, SENT_HOOK)
# Handkorrektur (Quelle in s): phrase_align ordnet beim leisen, teils undeutlichen Originalton mehrere Wörter
# falsch zu (z. B. „Wollt ihr mich …“ in die Phrase davor). Zeiten aus 10-ms-Energie + Zischlaut-Anteil
# (z/s/sch/f/ch) der angeglichenen Tonspur bestimmt.
SRC_T = [13.033, 13.833, 14.313, 14.653,                                   # Das … zurück ins Regal.
         16.816, 17.136, 17.346, 17.516, 18.016,                           # Das war im Regal gestanden.
         18.396, 18.496, 18.636, 18.786, 19.016, 19.246,                   # Ich hab die Packung erst gekauft.
         21.489, 21.649, 21.769, 22.329, 22.559, 22.879, 23.149,           # Einfach nur noch ein f*cking Ding drin.
         23.469, 23.589, 23.849, 24.159, 24.489,                           # Wollt ihr mich komplett verarschen?
         27.146, 27.396, 27.586, 27.696, 28.176, 28.676, 28.846,           # Warum, wegen ein Teil schickst du das
         29.156, 29.606, 29.836, 30.086]                                   # ganze Ding wieder zurück?


def src2out(t):
    for i, (k, a, d) in enumerate(segs):
        if a - 0.05 <= t <= a + d:
            return cuts[i] + t - a
    raise ValueError(t)


assert len(SRC_T) == len(wc)
for k, v in enumerate(SRC_T):
    print(f"  {wc[k][0]:12s} phrase_align {wc[k][1] + cuts[1]:6.2f}  korrigiert {src2out(v):6.2f}")
    wc[k] = (wc[k][0], src2out(v) - cuts[1])
wo = [(w, t) for (w, _), t in zip(wo, [0.03, 0.25, 1.66, 1.86])]   # Outro: „Folgt“ ≠ „Folg“ -> phrase_align daneben
LEAD = 0.04
pages, i = [], 0
for snt in SENT_CLIP:
    for pg in snt:
        pages.append([(("f*cking" if w == "fucking" else w), wc[i + k][1] + cuts[1]) for k, w in enumerate(pg)])
        i += len(pg)
i = 0
for snt in SENT_OUTRO:
    for pg in snt:
        pages.append([(w, wo[i + k][1] + OUTRO_T) for k, w in enumerate(pg)]); i += len(pg)
subs = []
for k, pg in enumerate(pages):
    s0 = pg[0][1] - LEAD
    nxt = pages[k + 1][0][1] - LEAD if k + 1 < len(pages) else 1e9
    s1 = min(nxt, pg[-1][1] + 0.85)
    for c in cuts[1:] + [OUTRO_T - LEAD]:               # Seite endet spätestens am nächsten Schnitt
        if s0 < c - 0.05 < s1 and k + 1 < len(pages) and pages[k + 1][0][1] > c:
            s1 = min(s1, c)
    subs.append({"t": r(max(s0, 0)), "end": r(s1), "words": [[w, r(max(t - LEAD, 0))] for w, t in pg]})
LAST_SUB = subs[-1]["end"]
t_und = r(HOOK_T + wh[4][1] - LEAD)
t_folg = r(OUTRO_T + wo[2][1] - LEAD)
t_q = r(POINTE + 0.1)
c1, c2 = cuts[1], cuts[2]

E = []
def el(t, end, y, rows, **kw):
    e = {"t": r(t), "end": r(end), "y": y, "rows": rows}; e.update(kw); E.append(e)

# Layout A (Spiel unten): Hook-Text über der Spielszene, Credit-Pille deckt das Sponsor-Logo im Webcam-Rahmen ab
HOOK = -0.22
el(HOOK, c1, 1150, card=False, gap=10, motion="none", rows=[
    {"type": "title", "text": "Fustler zockt GTA 6", "size": 82, "at": 0.0, "motion": "punch"},
    {"type": "big", "text": "UND DANN DAS!", "size": 140, "at": r(t_und - HOOK), "motion": "punch"}])
el(HOOK, c2, 130, x=818, card=False, motion="none", exit=False,
   rows=[{"type": "glowpill", "text": "Clip: twitch.tv/fustler", "size": 30}])
# Layout B: Plum-Karte deckt das Sponsor-Banner (y 0–993) komplett ab, darauf Credit, Titel, Untertitel
el(c2, END, 473, card=True, w=1160, pad=523, gap=0, motion="none", exit=False, rows=[])
el(c2, END, 262, card=False, motion="none", exit=False,
   rows=[{"type": "glowpill", "text": "Clip: twitch.tv/fustler", "size": 30}])
el(c2, t_q, 555, card=False, gap=14, motion="none", rows=[
    {"type": "title", "text": "Nur noch", "size": 96, "at": 0.05, "motion": "punch"},
    {"type": "big", "text": "EIN LEBKUCHEN?!", "size": 122, "at": 0.3, "motion": "punch"},
    {"type": "text", "text": "Fustler ließ nur einen übrig\n(laut Clip-Titel)", "size": 38, "color": "cream", "at": 1.0}])
# Ende: Kommentar-Frage, + Folgen, Pfeil zum Kommentar-Knopf
el(t_q, END, 600, card=False, exit=False, motion="punch",
   rows=[{"type": "title", "text": "Hättest du die Packung\nzurückgestellt?", "size": 82}])
el(t_folg, END, 400, card=False, exit=False, motion="punch",
   rows=[{"type": "glowpill", "text": "+ Folgen", "size": 56}])
E.append({"t": r(t_q + 0.15), "end": END, "y": 1210, "x": 805, "card": False, "exit": False,
          "rows": [{"type": "arrow", "w": 170, "nudge": 14}]})

scenes = [{"clip": CLIP, "ss": 0.0, "start": 0.0, "end": END, "cam": {"x": 0.5, "y": 0.5, "zoom": [1.0, 1.0], "speed": 1.0}}]
spec = {"duration": END, "fps": 30, "crf": 18, "preset": "slow", "darken": 0.0, "bg_blur": 0,
        "sub_y": 805, "lufs": -14, "voice": {"wav": VD + "final.wav", "t": 0.0}, "subs": subs, "elements": E,
        "scenes": scenes, "music": False,
        "sfx": [{"t": 0.05, "type": "hit", "gain": 0.5}, {"t": t_und, "type": "hit", "gain": 0.6},
                {"t": r(c2 + 0.3), "type": "pop"}, {"t": r(t_q), "type": "pop"}, {"t": r(t_folg), "type": "pop"}]
               + [{"t": r(c - 0.12), "type": "whoosh", "gain": 0.5} for c in [c1, c2]]}
json.dump(spec, open(R + "content/02-kanal/specs/s1.json", "w"), ensure_ascii=False, indent=1)
print("Schnitte", cuts, "Pointe", POINTE, "Outro", OUTRO_T, "Dauer", END, "Seiten", len(subs), "Elemente", len(E))
print("Quelle:", [(k, a, r(a + d)) for k, a, d in segs])
for s in subs:
    print(s["t"], s["end"], " ".join(w for w, _ in s["words"]), [t for _, t in s["words"]])
