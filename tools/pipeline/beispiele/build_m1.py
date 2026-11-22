"""M1 „Rentner vs. Chamäleon“: Meme-TikTok aus eigener GTA-6-Aufnahme (assets/eigen/clip1.mov, Wurf 1).

Layout: oben POV-Text, Mitte Video (4:3-Ausschnitt ohne Minikarte/HUD, volle Breite), Rest unscharfer,
abgedunkelter Video-Hintergrund. Ablauf: Anlauf (1x) -> Wurf in Zeitlupe -> Treffer: Punch-Zoom + Blitz +
Wackler + Standbild + „hit“ + Scoreboard „RENTNER 0 : 1 CHAMÄLEON“ -> er torkelt und fällt (Zeitlupe am Boden)
+ TTS „Rente durch.“ (Fenrir) -> Standbild „Was hättest du geworfen?“ -> harter Schnitt zurück zum Anfang (Loop).
Ton: Originalton wird NICHT verwendet (nur Bilder aus der Quelle), neu: Musik „chase“, sfx.py-Effekte, TTS.
Aufruf: python3 tools/pipeline/beispiele/build_m1.py   (Quellbilder werden einmal nach work/m1/src extrahiert)
"""
import glob, math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

R = "/home/user/GTA-6/"
sys.path.insert(0, R)
from tools.leonida import design as D, sfx as SFX, voice as VOICE

W = os.environ.get("LEONIDA_WORK", R + "work") + "/m1/"
SRC = R + "assets/eigen/clip1.mov"
OUT = R + "downloads/M1_gta6-rentner.mp4"
FPS, SR, SFPS = 30, 48000, 60000 / 1001
VW, VH, VY = 1080, 810, 595                  # Videofenster (4:3) im 1080x1920-Bild
N0, N1 = 345, 600                            # benötigte Quellbilder (Index n, Zeit n/59.94)
S_HIT = 484 / SFPS                           # 8,0747 s: Leguan trifft den Rentner an der Brust
S_END = 587 / SFPS                           # 9,793 s: Rentner liegt rechts am Boden

# ---------- 1) Quellbilder (nur Video, kein Ton) ----------
os.makedirs(W + "src", exist_ok=True)
if len(glob.glob(W + "src/*.jpg")) < N1 - N0 + 1:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-an", "-vf", f"select='between(n,{N0},{N1})'",
                    "-vsync", "0", "-start_number", str(N0), "-q:v", "2", W + "src/%04d.jpg"], check=True)

# ---------- 2) Zeitachse: Quelle S(T) mit Zeitlupe/Standbildern ----------
SEGS = [("play", 7.60, 1.0, 1.0, 0.0),       # A Anlauf, Echtzeit (ab 5,85 s)
        ("play", S_HIT, 1.0, 0.35, 0.25),    # B Wurf: Rampe auf 0,35x
        ("freeze", 1.5),                     # C Treffer-Standbild
        ("play", 9.30, 0.35, 1.0, 0.30),     # D1 er torkelt (Rampe zurück auf 1x)
        ("play", S_END, 1.0, 0.33, 0.20),    # D2 Sturz + am Boden in Zeitlupe
        ("freeze", 1.75)]                    # E Endkarte
smooth = lambda x: x * x * (3 - 2 * x)
S_T, MARK = [], {}
s, t, dt = 5.85, 0.0, 1 / FPS / 40
nxt = 0.0
for k, sg in enumerate(SEGS):
    MARK[k] = t
    if sg[0] == "freeze":
        t_end = t + sg[1]
        while nxt < t_end - 1e-9:
            S_T.append(s); nxt += 1 / FPS
        t = t_end
        continue
    _, until, v0, v1, ramp = sg
    t0 = t
    while s < until - 1e-9:
        while nxt <= t + 1e-9:
            S_T.append(s); nxt += 1 / FPS
        tau = t - t0
        v = v0 + (v1 - v0) * smooth(min(1, tau / ramp)) if ramp else v1
        s = min(until, s + v * dt); t += dt
    s = until
NF = len(S_T)
DUR = NF / FPS
T_A, T_HIT, T_RES, T_D2, T_E = MARK[1], MARK[2], MARK[3], MARK[4], MARK[5]
SPEED = np.gradient(np.array(S_T)) * FPS


def spring(x, zeta=0.45, omega=18.0):
    if x <= 0:
        return 0.0
    wd = omega * math.sqrt(1 - zeta ** 2)
    return 1 - math.exp(-zeta * omega * x) * (math.cos(wd * x) + zeta * omega / wd * math.sin(wd * x))


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


# ---------- 3) Kamera (Ausschnitt cx, cy, Breite w in Quell-Pixeln, 4:3) ----------
CAM_A0, CAM_A1 = (930, 505, 1160), (930, 505, 1110)
CAM_B1 = (870, 445, 860)
CAM_P = (830, 400, 600)                      # Punch: Leguan + Gesicht des Rentners


def follow(S):
    cx = np.interp(S, [S_HIT, 8.30, 8.60, 8.90, 9.20, 9.30, S_END], [930, 985, 1110, 1250, 1340, 1340, 1440])
    cy = np.interp(S, [S_HIT, 9.30, S_END], [505, 505, 600])
    w = np.interp(S, [S_HIT, 9.30, S_END], [1160, 1160, 960])
    return (cx, cy, w)


def cam_c(life):
    k = spring(life)
    cx, cy, w = lerp(CAM_B1, CAM_P, k)
    return (cx, cy, w - 30 * min(1, life / 1.5))


def camera(n):
    T, S = n / FPS, S_T[n]
    if T < T_A:
        c = lerp(CAM_A0, CAM_A1, T / T_A)
    elif T < T_HIT:
        c = lerp(CAM_A1, CAM_B1, smooth((T - T_A) / (T_HIT - T_A)))
    elif T < T_RES:
        c = cam_c(T - T_HIT)
    elif T < T_E:
        k = smooth(min(1, (T - T_RES) / 0.35))
        c = lerp(cam_c(T_RES - T_HIT), follow(S), k)
    else:
        cx, cy, w = follow(S_END)
        c = (cx, cy, w - 40 * (T - T_E) / (DUR - T_E))
    cx, cy, w = c
    if T_HIT <= T < T_HIT + 0.45:            # Wackler beim Treffer
        l = T - T_HIT
        a = math.exp(-l / 0.12)
        cx += 16 * a * math.sin(2 * math.pi * 19 * l) * w / VW
        cy += 11 * a * math.cos(2 * math.pi * 23 * l) * w / VW
    h = w * 0.75
    cx = min(max(cx, w / 2), 1920 - w / 2)
    cy = min(max(cy, h / 2), 1080 - h / 2)
    return cx, cy, w, h


# ---------- 4) Grafiken ----------
def fit_text(s, maxw, size, fill="white"):
    while True:
        im = D.text(s, D.barlow(size), fill=fill, glow=0.0)
        if im.width - 2 * D.PAD <= maxw or size < 40:
            return im
        size -= 2


TOP = fit_text("POV: Du bist Rentner\nin Vice City", 960, 132)


def scoreboard():
    cw, ch = 820, 266
    img = D.card(cw, ch)
    names = [D.text("RENTNER", D.barlow(66), fill="cream", glow=0.0),
             D.text("CHAMÄLEON", D.barlow(66), fill="cream", glow=0.0)]
    green = [D.hexc("#eaff9a"), D.hexc("#7be35a"), D.hexc("#1f9a4b")]
    grey = [D.hexc("#ffffff"), D.hexc("#d9cfe0"), D.hexc("#9c8aa8")]
    digits = [D.gradient_text("0", D.barlow(176), stops=grey, glow=0.1),
              D.gradient_text("1", D.barlow(176), stops=green, glow=0.5)]
    colon = D.text(":", D.barlow(150), fill="cream", glow=0.0)
    ox, oy = D.PAD, D.PAD
    dtop, dh = 98, digits[0].height - 2 * D.PAD
    for i, cxx in enumerate([cw * 0.25, cw * 0.75]):
        nm, dg = names[i], digits[i]
        nh = max(x.height for x in names)          # gemeinsame Grundlinie (Ä macht die Tinte höher)
        img.alpha_composite(nm, (int(ox + cxx - nm.width / 2), int(oy + 30 + nh - nm.height - D.PAD)))
        img.alpha_composite(dg, (int(ox + cxx - dg.width / 2), int(oy + dtop - D.PAD)))
    cy_d = dtop + dh / 2
    img.alpha_composite(colon, (int(ox + cw / 2 - colon.width / 2), int(oy + cy_d - colon.height / 2)))
    return img


SCORE = scoreboard()


def question():
    cw, ch = 760, 250
    img = D.card(cw, ch)
    q = D.text("Was hättest du\ngeworfen?", D.barlow(98), fill="cream", glow=0.0)
    img.alpha_composite(q, (int(D.PAD + cw / 2 - q.width / 2), int(D.PAD + ch / 2 - q.height / 2)))
    return img


QUEST = question()
ARROW = D.arrow(150)

# TTS „Rente durch.“: Wortgrenze aus der Lautstärke
TTS = VOICE.generate("Rente durch.", voice="Fenrir")
tts = VOICE.load(TTS, SR)
h10 = int(0.01 * SR)
en = np.sqrt((tts[: len(tts) // h10 * h10].reshape(-1, h10) ** 2).mean(1))
lo, hi = int(0.25 / 0.01), int(0.65 / 0.01)
GAP = (lo + int(np.argmin(en[lo:hi]))) * 0.01
T_TTS = round(T_D2 + 0.22, 3)
TTS_END = T_TTS + len(tts) / SR
SUBS = [(T_TTS - 0.04, T_TTS + GAP - 0.03, 0), (T_TTS + GAP - 0.03, TTS_END + 0.05, 1)]
SUB_IM = {k: D.subtitle(["Rente", "durch."], k) for k in (0, 1)}
T_Q = T_E + 0.08
T_ARROW = max(T_E + 0.35, TTS_END + 0.3)


def scaled(im, k):
    if abs(k - 1) < 0.004:
        return im
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BICUBIC)


def put_center(canvas, im, cx, cy, op=1.0):
    D.paste(canvas, im, cx - im.width / 2, cy - im.height / 2, op)


def pop_in(life, dur=None):
    s = spring(life, 0.5, 16)
    return min(1, life / 0.08), 0.6 + 0.4 * s


# ---------- 5) Bilder rendern ----------
_cache = {}


def src(n):
    if n not in _cache:
        if len(_cache) > 6:
            _cache.pop(next(iter(_cache)))
        _cache[n] = Image.open(W + f"src/{n:04d}.jpg").convert("RGB")
    return _cache[n]


def source_frame(n):
    f = S_T[n] * SFPS
    i = int(math.floor(f + 1e-6)); a = f - i
    if SPEED[n] < 0.05 or a < 0.12:
        return src(i)
    if a > 0.88:
        return src(i + 1)
    return Image.blend(src(i), src(i + 1), a)


def frame(n):
    T = n / FPS
    im = source_frame(n)
    cx, cy, w, h = camera(n)
    vid = im.resize((VW, VH), Image.LANCZOS, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    # Hintergrund: kleines Bild -> 9:16 -> weichzeichnen -> hochskalieren -> abdunkeln
    sm = im.resize((240, 135), Image.BILINEAR)
    bx = min(max(cx / 8 - 38, 0), 240 - 76)
    bg = sm.crop((int(bx), 0, int(bx) + 76, 135)).filter(ImageFilter.GaussianBlur(3.2))
    bg = bg.resize((1080, 1920), Image.BICUBIC)
    bg = Image.eval(bg, lambda v: int(v * 0.42))
    c = bg.convert("RGBA")
    # Endkarte: Video leicht abdunkeln
    if T >= T_E:
        k = min(1, (T - T_E) / 0.2) * 0.38
        vid = Image.eval(vid, lambda v, k=k: int(v * (1 - k)))
    if T_HIT <= T < T_HIT + 0.13:            # Blitz beim Treffer
        vid = Image.blend(vid, Image.new("RGB", vid.size, (255, 255, 255)), 0.65 * (1 - (T - T_HIT) / 0.13))
    sh = Image.new("RGBA", (VW, VH + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, 20, VW, VH + 20], fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (0, VY - 20))
    c.paste(vid, (0, VY))
    put_center(c, TOP, 540, 425)
    if T >= T_HIT + 0.1:                      # Scoreboard
        op, k = pop_in(T - T_HIT - 0.1)
        put_center(c, scaled(SCORE, k), 490, 1503, op)
    for a, b, k in SUBS:
        if a <= T < b:
            put_center(c, SUB_IM[k], 540, 1300)
    if T >= T_Q:
        op, k = pop_in(T - T_Q)
        put_center(c, scaled(QUEST, k), 500, 1000, op)
    if T >= T_ARROW:
        l = T - T_ARROW
        put_center(c, ARROW, 820 + 12 * math.sin(l * 9), 1222, min(1, l / 0.12))
    return c.convert("RGB")


# ---------- 6) Ton (komplett neu, ohne Originalton) ----------
def mix_audio(path):
    N = int(round(DUR * SR))
    tt = np.arange(N) / SR
    music = SFX.music_bed(DUR + 1.5, "chase")[:N]           # Schluss-Fade abgeschnitten (eigener Fade)
    from scipy.signal import butter, sosfiltfilt
    lp = sosfiltfilt(butter(2, 480 / (SR / 2), output="sos"), music, axis=0)
    xf = np.clip((tt - T_A) / 0.3, 0, 1)                     # Zeitlupe: dumpfer + leiser
    g = np.ones(N)
    g = np.where(tt >= T_A, 1 - 0.45 * xf, g)
    g = np.where(tt >= T_HIT, np.clip(1 - (tt - T_HIT) / 0.025, 0, 1) * 0.55, g)   # Stille im Standbild
    g = np.where(tt >= T_RES, 0.8 * np.clip((tt - T_RES) / 0.12, 0, 1), g)
    duck = np.clip(np.minimum((tt - (T_TTS - 0.1)) / 0.08, (TTS_END + 0.1 - tt) / 0.15), 0, 1)
    g = g * (1 - 0.6 * duck)
    g = g * np.clip((DUR - tt) / 0.25, 0, 1)
    wet = np.where((tt >= T_A) & (tt < T_RES), xf, 0.0)
    m = (music * (1 - wet)[:, None] + lp * wet[:, None]) * g[:, None]
    ev = [("whoosh", T_A - 0.12, 0.9, None), ("riser", T_A, 0.9, round(T_HIT - T_A, 2)),
          ("hit", T_HIT, 1.0, None), ("hit", T_HIT + 0.012, 0.6, 0.6), ("pop", T_HIT + 0.1, 0.9, None),
          ("whoosh", T_RES - 0.08, 0.6, None), ("pop", T_Q, 0.8, None), ("chime", T_Q + 0.05, 0.35, None)]
    fx = np.zeros(N)
    for kind, t0, gain, ln in ev:
        x = (SFX.GEN[kind](ln) if ln else SFX.GEN[kind]()) * gain * SFX.MIX_GAIN[kind]
        i = int(t0 * SR); j = min(N, i + len(x)); fx[i:j] += x[: j - i]
    fx = fx / np.max(np.abs(fx)) * 0.55
    v = np.zeros(N)
    i = int(T_TTS * SR); j = min(N, i + len(tts)); v[i:j] = tts[: j - i] / np.max(np.abs(tts)) * 0.75
    out = m + (fx + v)[:, None]
    # Pegel: -14 LUFS (linear), Spitzen mit Vorausschau-Limiter auf -1,5 dBFS
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    for _ in range(3):
        tmp = W + "mix_tmp.wav"; save_wav(tmp, out)
        o = subprocess.run(["ffmpeg", "-nostats", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
        out = out * 10 ** ((-14 - lufs) / 20)
        ceil = 10 ** (-1.5 / 20)
        pk = maximum_filter1d(np.abs(out).max(1), size=int(0.004 * SR))
        gl = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
        gl = np.minimum(gl, lfilter([0.01], [1, -0.99], gl))
        out = out * gl[:, None]
        if abs(lufs + 14) < 0.15:
            break
    save_wav(path, out)
    return lufs


def save_wav(p, x):
    with wave.open(p, "wb") as o:
        o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
        o.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    print(f"Dauer {DUR:.2f} s, {NF} Bilder | A..{T_A:.2f} Treffer {T_HIT:.2f} weiter {T_RES:.2f} "
          f"Sturz {T_D2:.2f} Ende {T_E:.2f} | TTS {T_TTS:.2f}-{TTS_END:.2f} (Wortgrenze {GAP:.2f})")
    wav = W + "m1_mix.wav"
    print("LUFS vor letzter Korrektur", mix_audio(wav))
    if os.environ.get("STILLS"):
        for n in [int(x) for x in os.environ["STILLS"].split(",")]:
            frame(n).save(W + f"still_{n:03d}.jpg", quality=88)
        sys.exit()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait()
    print("fertig:", OUT)
