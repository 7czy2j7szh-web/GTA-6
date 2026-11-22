"""M2 „Cardio abgebrochen“: Meme-TikTok aus eigener GTA-6-Aufnahme (assets/eigen/clip1.mov, Wurf 2 auf den Jogger).

Ablauf: Jogger normal (Text „Er wollte nur joggen …“) -> Wurf in Zeitlupe (60-fps-Quelle, Bildüberblendung)
-> Treffer: Punch-Zoom + Standbild + Wackler + Blitz + „hit“ -> Sturz in Zeitlupe -> Kriechen mit
„Cardio: abgebrochen.“ (Gemini-TTS Fenrir) -> „Folg für mehr GTA-6-Chaos“, harter Loop-Schnitt.
ORIGINALTON WIRD NIE GELESEN (ffmpeg -an); Ton = eigene Musik (leonida_nights -> Bandstopp -> chase) + sfx.py + TTS.
Layout 1080x1920@30: oben Meme-Text, Mitte Video 1080x900 (gezoomt, Minikarte/HUD außerhalb), Rest unscharf/abgedunkelt.
Aufruf: python3 tools/pipeline/beispiele/build_m2.py   -> downloads/M2_gta6-jogger.mp4
"""
import math, os, re, subprocess, sys, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw

R = "/home/user/GTA-6/"
sys.path.insert(0, R + "tools")
from leonida import design as D, sfx as SFX, voice as V   # noqa: E402

WK = os.environ.get("LEONIDA_WORK", R + "work") + "/m2/"
os.makedirs(WK, exist_ok=True)
SRC = R + "assets/eigen/clip1.mov"
OUT = R + "downloads/M2_gta6-jogger.mp4"
TTS_TEXT, TTS_VOICE = "Cardio … abgebrochen.", "Fenrir"
FPS, SFPS, SR = 30, 60000 / 1001, 48000
WIN_Y, WIN_H = 590, 900                      # Videofenster (volle Breite)
CW0, CH0 = 1080 / WIN_H * 1080, 1080         # Ausschnitt bei Zoom 1 (Seitenverhältnis 1,2)
HUD_TOP = 80                                 # obere HUD-Leiste der Quelle (Leiste + Marker, y < 80) nie im Bild

# ---- Zeitachse: (Quelle von, bis, Tempo) bzw. Standbild ----
SEG = [(12.50, 15.85, 1.0),     # Jogger läuft, sie trägt den Leguan
       (15.85, 16.28, 0.35),    # Ausholen + Wurf in Zeitlupe
       ("freeze", 16.28, 0.5),  # Treffer: Leguan klebt am Rücken -> Standbild
       (16.28, 17.00, 0.5),     # er stolpert, Leguan fällt
       (17.00, 17.90, 0.75),    # Kameraschwenk, er stürzt
       (17.90, 22.50, 1.0)]     # Kriechen, Aufsitzen, Aufstehen (Loop-Schnitt zurück zum Joggen)
TL, t = [], 0.0
for sg in SEG:
    if sg[0] == "freeze":
        TL.append((t, t + sg[2], sg[1], 0.0)); t += sg[2]
    else:
        d = (sg[1] - sg[0]) / sg[2]; TL.append((t, t + d, sg[0], sg[2])); t += d
NF = int(round(t * FPS)); DUR = NF / FPS
T_HIT = TL[2][0]; T_FREEZE_END = TL[2][1]; T_CRAWL = TL[5][0]


def src_at(tt):
    for a, b, s0, sp in TL:
        if tt < b or (a, b) == TL[-1][:2]:
            return s0 + (tt - a) * sp, sp
    raise ValueError(tt)


def out_of(s):
    for a, b, s0, sp in TL:
        if sp and s0 <= s <= s0 + (b - a) * sp:
            return a + (s - s0) / sp
    raise ValueError(s)


# ---- Kamera (Quellzeit -> Mitte x/y, Zoom), Jogger-Positionen aus Einzelbildern bestimmt ----
CAM = [(12.50, 790, 540, 1.30), (15.85, 900, 500, 1.45), (16.28, 975, 450, 1.75), (17.00, 1090, 470, 1.90),
       (17.05, 1090, 440, 1.90), (17.12, 1065, 290, 1.90), (17.60, 1075, 250, 1.95), (18.00, 1035, 230, 1.95),
       (19.00, 995, 235, 1.95), (20.00, 1035, 360, 1.85), (21.00, 1060, 510, 1.75), (21.60, 955, 470, 1.70),
       (22.50, 915, 400, 1.60)]
HIT_P = (1000, 445)                          # Jogger beim Treffer (Quelle 16,28 s)
TTS_T = T_CRAWL + 0.25
TTS_WORD2 = 1.04                             # Beginn „abgebrochen“ in der TTS-Aufnahme (10-ms-Energie)
T_TXT2A, T_TXT2B, T_FOLLOW = TTS_T - 0.02, TTS_T + TTS_WORD2 - 0.04, DUR - 1.9


def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def cam_track():
    ks = np.array([c[0] for c in CAM])
    cx, cy, z = [np.array([c[i] for c in CAM], float) for i in (1, 2, 3)]
    tt = np.arange(NF) / FPS
    s = np.array([src_at(x)[0] for x in tt])
    arr = np.stack([np.interp(s, ks, cx), np.interp(s, ks, cy), np.interp(s, ks, z)], 1)
    k = 7; pad = np.pad(arr, ((k // 2, k // 2), (0, 0)), mode="edge")          # gleitender Mittelwert
    arr = np.stack([np.convolve(pad[:, i], np.ones(k) / k, mode="valid") for i in range(3)], 1)
    out = []
    for i, x in enumerate(tt):
        bx, by, bz = arr[i]
        if x < T_HIT:
            w = 0.0
        elif x < T_HIT + 0.1:
            w = 1 - (1 - (x - T_HIT) / 0.1) ** 3                                   # Punch: schnell rein
        elif x < T_FREEZE_END:
            w = 1.0
        else:
            w = 1 - ease((x - T_FREEZE_END) / 1.1)                                  # weich wieder raus
        zz = bz * (1 + 0.55 * w)
        px, py = bx * (1 - w) + HIT_P[0] * w, by * (1 - w) + HIT_P[1] * w
        dt = x - T_HIT
        if 0 <= dt < 0.45:                                                           # Wackler beim Treffer
            a = math.exp(-7 * dt)
            px += 9 * a * math.sin(2 * math.pi * 13 * dt); py += 7 * a * math.cos(2 * math.pi * 11 * dt)
        out.append((px, py, zz))
    return out


# ---- Texte ----
INK = (12, 13, 27)


def label(lines, size, fills, stroke=9):
    f = D.barlow(size)
    lh = int(size * 1.0)
    w = int(max(f.getlength(l) for l in lines)) + 2 * stroke
    h = lh * len(lines) + int(size * 0.25) + 2 * stroke
    img = Image.new("RGBA", (w + 2 * D.PAD, h + 2 * D.PAD), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (l, fc) in enumerate(zip(lines, fills)):
        d.text((D.PAD + (w - f.getlength(l)) / 2, D.PAD + stroke + i * lh), l, font=f, fill=fc,
               stroke_width=stroke, stroke_fill=INK)
    return D.shadowed(img, blur=16, alpha=0.8, dy=8, glow=0.55)


def bgra(im):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    return a[..., [2, 1, 0, 3]]


WHITE, RED = (253, 251, 255), (255, 84, 72)
TXT1 = bgra(label(["ER WOLLTE NUR", "JOGGEN …"], 132, [WHITE, WHITE]))
TXT2A = bgra(label(["CARDIO:"], 150, [WHITE]))
TXT2B = bgra(label(["ABGEBROCHEN."], 150, [RED]))
TXT3 = bgra(D.glow_pill("Folg für mehr GTA-6-Chaos", size=56, h=112))
# (Bild, Start, Ende, Mitte y, animiert)
OVL = [(TXT1, -1, T_TXT2A, 420, False), (TXT2A, T_TXT2A, 99, 345, True), (TXT2B, T_TXT2B, 99, 488, True),
       (TXT3, T_FOLLOW, 99, 1585, True)]


def spring(x, zeta=0.5, om=18.0):
    if x <= 0:
        return 0.0
    wd = om * math.sqrt(1 - zeta ** 2)
    return 1 - math.exp(-zeta * om * x) * (math.cos(wd * x) + zeta * om / wd * math.sin(wd * x))


def paste(c, im, cx, cy, op=1.0, sc=1.0):
    if sc != 1.0:
        im = cv2.resize(im, (max(int(im.shape[1] * sc), 2), max(int(im.shape[0] * sc), 2)), interpolation=cv2.INTER_LINEAR)
    h, w = im.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, c.shape[1]), min(y0 + h, c.shape[0])
    if xa >= xb or ya >= yb:
        return
    sub = im[ya - y0:yb - y0, xa - x0:xb - x0]
    a = sub[..., 3:4] / 255 * op
    reg = c[ya:yb, xa:xb].astype(np.float32)
    c[ya:yb, xa:xb] = (reg * (1 - a) + sub[..., :3] * a).astype(np.uint8)


# ---- Bild ----
EDGE = np.ones((1920, 1, 1), np.float32)                     # Schatten über/unter dem Videofenster
for k in range(60):
    f = 1 - 0.55 * (1 - k / 60) ** 2
    EDGE[WIN_Y - 1 - k] = f; EDGE[WIN_Y + WIN_H + k] = f


def compose(fr, cx, cy, z, tt):
    # Hintergrund: 9:16-Ausschnitt um die Bildmitte, stark unscharf + abgedunkelt
    bx = int(np.clip(cx - 304, 0, 1920 - 608))
    bg = cv2.resize(fr[:, bx:bx + 608], (135, 240), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(bg, (0, 0), 4)
    bg = cv2.resize(bg, (1080, 1920), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.42 * EDGE
    c = bg.astype(np.uint8)
    cw, ch = CW0 / z, CH0 / z
    cx = float(np.clip(cx, cw / 2, 1920 - cw / 2)); cy = float(np.clip(cy, HUD_TOP + ch / 2, 1080 - ch / 2))
    s = 1080 / cw
    M = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    win = cv2.warpAffine(fr, M, (1080, WIN_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    dt = tt - T_HIT
    if 0 <= dt < 0.12:                                                              # Blitz beim Treffer
        a = 0.6 * (1 - dt / 0.12)
        win = (win.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
    c[WIN_Y:WIN_Y + WIN_H] = win
    for im, a0, a1, y, anim in OVL:
        if not (a0 <= tt < a1):
            continue
        life = tt - a0
        op, sc = (min(1.0, life / 0.08), 0.72 + 0.28 * spring(life)) if anim else (1.0, 1.0)
        paste(c, im, 540, y, op, sc)
    return c


def render_video(path):
    n0 = int(math.floor(12.45 * SFPS))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-an", "-vf", f"select=gte(n\\,{n0})",
                            "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1920",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", path], stdin=subprocess.PIPE)
    buf, nxt, fsz = {}, n0, 1920 * 1080 * 3

    def frame(n):
        nonlocal nxt
        while nxt <= n:
            raw = dec.stdout.read(fsz)
            if len(raw) < fsz:
                return buf[max(buf)]
            buf[nxt] = np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3); nxt += 1
        for k in [k for k in buf if k < n - 2]:
            del buf[k]
        return buf[n]

    track = cam_track()
    for i in range(NF):
        tt = i / FPS
        s, sp = src_at(tt)
        fidx = s * SFPS
        f0 = int(math.floor(fidx)); a = fidx - f0
        if sp and sp < 1 and 0.2 < a < 0.8:                                          # Zeitlupe: Zwischenbild
            fr = cv2.addWeighted(frame(f0), 1 - a, frame(f0 + 1), a, 0)
        else:
            fr = frame(int(round(fidx)))
        enc.stdin.write(compose(fr, *track[i], tt).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()


# ---- Ton (nur eigene Musik, sfx.py, TTS) ----
def wav_stereo(p):
    w = wave.open(p)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    x = x.reshape(-1, w.getnchannels())
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    assert w.getframerate() == SR
    return x


def render_audio(path):
    from scipy.signal import butter, sosfilt
    n = int(round(DUR * SR))
    mix = np.zeros((n, 2))
    # 1) ruhige Musik bis zum Treffer; ab Zeitlupe dumpf (Tiefpass-Überblendung); Bandstopp in den letzten 0,35 s
    calm = wav_stereo(R + "assets/music/leonida_nights.wav")[: int(T_HIT * SR)] * 0.55
    sl = int(TL[1][0] * SR)
    lp = sosfilt(butter(2, 650 / (SR / 2), output="sos"), calm, axis=0)
    wgt = np.clip((np.arange(len(calm)) - sl) / (0.5 * SR), 0, 1)[:, None]
    calm = calm * (1 - wgt) + lp * 1.25 * wgt
    L = int(0.35 * SR); st = len(calm) - L
    tau = np.arange(L)
    pos = st + tau - tau ** 2 / (2 * L)                                               # Tempo 1 -> 0
    tape = np.stack([np.interp(pos, np.arange(len(calm)), calm[:, ch]) for ch in (0, 1)], 1)
    tape *= np.linspace(1, 0, L)[:, None] ** 0.7
    calm[st:] = tape
    calm[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    mix[: len(calm)] += calm
    # 2) epische Musik ab Ende des Standbilds (Schlag auf Sekunde 0 des Tracks), unter der TTS abgesenkt
    j = int(T_FREEZE_END * SR)
    epic = wav_stereo(R + "assets/music/chase.wav")[: n - j] * 0.62
    env = np.ones(len(epic))
    v0, v1 = int((TTS_T - 0.15) * SR) - j, int((TTS_T + 1.85) * SR) - j
    env[v0:v1] = 10 ** (-9 / 20)
    env = np.convolve(env, np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    fo = int(0.45 * SR); env[-fo:] *= np.linspace(1, 0, fo)
    mix[j:] += epic * env[:, None]
    # 3) TTS (Fenrir, trocken)
    tts = V.load(V.generate(TTS_TEXT, voice=TTS_VOICE), SR)   # gecacht (assets/voice_cache)
    tts = tts / np.max(np.abs(tts)) * 0.95
    k = int(TTS_T * SR); mix[k:k + len(tts)] += tts[: n - k, None]
    # 4) Soundeffekte (eigene Synthese, tools/leonida/sfx.py)
    ev = [("riser", T_HIT - 1.5, 0.9), ("whoosh", out_of(15.93) - 0.1, 0.45), ("hit", T_HIT, 1.0),
          ("pop", T_HIT, 0.8), ("whoosh", T_FREEZE_END - 0.12, 0.35), ("hit", out_of(17.62), 0.55),
          ("pop", T_TXT2A, 0.6), ("hit", T_TXT2B, 0.45), ("pop", T_FOLLOW, 0.7), ("chime", T_FOLLOW + 0.05, 0.4)]
    for kind, tt, g in ev:
        x = SFX.GEN[kind](); x = x / np.max(np.abs(x)) * g
        i = int(tt * SR); mix[i:i + len(x)] += x[: n - i, None]
    raw = WK + "mix_raw.wav"
    pcm = (np.clip(mix / max(1.0, np.max(np.abs(mix)) / 0.9), -1, 1) * 32767).astype(np.int16)
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    # Lautheit -14 LUFS (linear) + True-Peak-Begrenzer
    o = subprocess.run(["ffmpeg", "-i", raw, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    i_lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    f"volume={-14 - i_lufs + 0.5:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=false",
                    "-ar", str(SR), path], check=True)


if __name__ == "__main__":
    vid, aud = WK + "video.mp4", WK + "mix.wav"
    print(f"Dauer {DUR:.2f}s  Treffer {T_HIT:.2f}  Standbild bis {T_FREEZE_END:.2f}  Kriechen {T_CRAWL:.2f}  "
          f"TTS {TTS_T:.2f}  Folgen {T_FOLLOW:.2f}")
    render_audio(aud)
    render_video(vid)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("fertig:", OUT)
