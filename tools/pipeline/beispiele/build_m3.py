"""M3 „13 Jahre gewartet“: Meme-TikTok aus eigener GTA-6-Aufnahme (assets/eigen/clip1.mov), ORIGINALTON KOMPLETT RAUS.

Layout: oben großer weißer Barlow-Text, Mitte Spielszene (volle Breite, gezoomt -> Minikarte/Kompass/Sterne
abgeschnitten), Rest unscharfer, abgedunkelter Video-Hintergrund. Schnitte im Takt von „chase“ (118 BPM).
Ablauf: Hook „13 Jahre auf GTA 6 gewartet.“ -> „Ich nach 10 Minuten:“ -> Wurf 1 (Zeitlupe, Punch-Zoom, Standbild, hit)
-> Wurf 2 (schneller, hit) -> Standbild „Bestes Spiel ever.“ + TTS (Kore) „Hat sich gelohnt!“.
Ton: nur Musik + Soundeffekte (tools/leonida/sfx.py) + TTS, Lautheit -14 LUFS. Die Tonspur der Quelle wird nie gelesen.
Aufruf: python3 tools/pipeline/beispiele/build_m3.py   -> downloads/M3_gta6-13-jahre.mp4
"""
import json, math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageFilter

R = "/home/user/GTA-6/"
sys.path.insert(0, R + "tools")
from leonida import design as D, sfx as S, voice as V  # noqa: E402

W = os.environ.get("LEONIDA_WORK", R + "work") + "/m3/"
os.makedirs(W, exist_ok=True)
SRC = R + "assets/eigen/clip1.mov"
TTS = R + "content/02-kanal/voice/m3/take.wav"         # Gemini-TTS Kore „Hat sich gelohnt!!“ (1,05 s)
OUT = R + "downloads/M3_gta6-13-jahre.mp4"
FPS, SFPS, SR = 30, 60000 / 1001, 48000
B = 60 / 118                                           # ein Schlag „chase“; Takt-Eins bei 0 s im Track
SW, SH = 1920, 1080
# Spielbild ohne HUD: Kompass/Lebensleiste bis y=78, Minikarte ab y=884 -> nur y 79..879 verwenden
Y0, Y1 = 79, 879
PW, PH, PY = 1080, 700, 660                            # Video-Panel (volle Breite), Oberkante y
BASE_H = Y1 - Y0
BASE_W = BASE_H * PW / PH

# ---- Schnittliste: ("play", Quelle von, bis, Tempo) | ("freeze", Quelle, Dauer); Tempo None = bis Zielzeit füllen
HIT1_SRC, HIT2_SRC = 8.01, 16.22                       # Einschlag Leguan: Mann (weiße Haare) / Jogger
GROUND1, GROUND2 = 9.45, 17.70                         # liegt am Boden
FREEZE1, FREEZE2 = 0.35, 0.20
SLOW1, SLOW2 = 0.35, 0.45
t_hit1, t_hit2 = 7 * B, 12 * B
s_b1 = HIT1_SRC - 0.24 - (t_hit1 - 0.24 / SLOW1 - 4 * B)          # Anlauf Wurf 1 in Echtzeit
s_c1 = HIT2_SRC - 0.12 - (t_hit2 - 0.12 / SLOW2 - 10 * B) * 1.25  # Anlauf Wurf 2 mit 1,25x
END_FRZ = 20.85                                        # Jogger am Boden, sie läuft hin
PIECES = [  # (Art, ..., Ende im Video)
    ("play", 0.40, None, 1.0, 4 * B, "intro"),
    ("play", s_b1, HIT1_SRC - 0.24, 1.0, None, "w1"),
    ("play", HIT1_SRC - 0.24, HIT1_SRC, SLOW1, None, "w1"),
    ("freeze", HIT1_SRC, FREEZE1, None, None, "w1"),
    ("play", HIT1_SRC, 9.70, None, 10 * B, "w1"),         # Mann taumelt und fällt (~9,45 am Boden)
    ("play", s_c1, HIT2_SRC - 0.12, 1.25, None, "w2"),
    ("play", HIT2_SRC - 0.12, HIT2_SRC, SLOW2, None, "w2"),
    ("freeze", HIT2_SRC, FREEZE2, None, None, "w2"),
    ("play", HIT2_SRC, 18.30, None, 15 * B, "w2"),        # Jogger stolpert, fällt (~17,7)
    ("play", END_FRZ - B, END_FRZ, 1.0, 16 * B, "end"),
    ("freeze", END_FRZ, None, None, 22 * B, "end"),
]
DUR = 22 * B
r3 = lambda v: round(v, 3)

timeline, t = [], 0.0
for kind, a, b, sp, tend, tag in PIECES:
    if kind == "play":
        if b is None:
            b = a + (tend - t) * sp
        if sp is None:
            sp = (b - a) / (tend - t)
        d = (b - a) / sp
    else:
        d = b if b is not None else tend - t
        sp = 0.0
    timeline.append(dict(kind=kind, a=a, t0=t, t1=t + d, sp=sp, tag=tag))
    t += d
assert abs(t - DUR) < 1e-6, (t, DUR)
for p in timeline:
    print(f"{p['kind']:6s} {p['tag']:5s} out {p['t0']:6.3f}-{p['t1']:6.3f}  src {p['a']:6.3f}"
          f"-{p['a'] + (p['t1'] - p['t0']) * p['sp']:6.3f}  x{p['sp']:.2f}")


def src_time(t):
    for p in timeline:
        if p["t0"] <= t < p["t1"] + 1e-9:
            return p["a"] + (t - p["t0"]) * p["sp"], p
    return timeline[-1]["a"], timeline[-1]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ---- Kamera: Basis-Mitte je Abschnitt, Punch-Zoom auf den Treffer (Ziel in Quellpixeln)
BASE_CX = {"intro": 0.40 * SW, "w1": 0.45 * SW, "w2": 0.48 * SW, "end": 0.50 * SW}
T1 = (0.47 * SW, 0.40 * SH)      # Mann beim Einschlag
T2 = (0.51 * SW, 0.44 * SH)      # Jogger beim Einschlag
TE = (0.50 * SW, 0.58 * SH)      # Standbild: Jogger + Spielerin
s1_start = t_hit1 - 0.24 / SLOW1
s2_start = t_hit2 - 0.12 / SLOW2
HITS = [t_hit1, t_hit2]


def zoom_curve(t, t_in, t_hit, frz, z_in, z_punch, out_dur):
    if t < t_in or t > t_hit + frz + out_dur:
        return 1.0
    if t < t_hit:
        return 1 + (z_in - 1) * ease((t - t_in) / (t_hit - t_in))
    if t < t_hit + frz:
        return z_in + (z_punch - z_in) * ease_out((t - t_hit) / 0.09)
    return 1 + (z_punch - 1) * (1 - ease((t - t_hit - frz) / out_dur))


def camera(t, tag):
    z1 = zoom_curve(t, s1_start, t_hit1, FREEZE1, 1.45, 1.75, 0.35)
    z2 = zoom_curve(t, s2_start, t_hit2, FREEZE2, 1.60, 1.95, 0.30)
    if z1 > 1.0001:
        z, tgt, zm = z1, T1, 1.75
    elif z2 > 1.0001:
        z, tgt, zm = z2, T2, 1.95
    elif tag == "end" and t >= 16 * B:
        z = 1 + 0.16 * ease_out((t - 16 * B) / (DUR - 16 * B)); tgt, zm = TE, 1.16
    else:
        z, tgt, zm = 1.0, None, 1.0
    bx, by = BASE_CX[tag], (Y0 + Y1) / 2
    if tgt:
        k = min(1.0, (z - 1) / (zm - 1))
        bx, by = bx + (tgt[0] - bx) * k, by + (tgt[1] - by) * k
    # Wackler beim Einschlag
    for th in HITS:
        if 0 <= t - th < 0.3:
            a = 10 * math.exp(-(t - th) * 14)
            bx += a * math.sin((t - th) * 95) / z * 1.6
            by += a * math.cos((t - th) * 77) / z * 1.6
    w, h = BASE_W / z, BASE_H / z
    x0 = min(max(bx - w / 2, 0), SW - w)
    y0 = min(max(by - h / 2, Y0), Y1 - h)
    return x0, y0, w, h


# ---- Texte (oben, weiß mit dunklem Schatten)
def stack(rows, gap=6):
    ims = [D.text(s, D.barlow(sz), fill="white", glow=0.55) for s, sz in rows]
    inner = [im.height - 2 * D.PAD for im in ims]
    wmax = max(im.width for im in ims)
    hh = sum(inner) + gap * (len(ims) - 1) + 2 * D.PAD
    out = Image.new("RGBA", (wmax, hh), (0, 0, 0, 0))
    y = 0
    for im, ih in zip(ims, inner):
        out.alpha_composite(im, ((wmax - im.width) // 2, y))
        y += ih + gap
    return out


TEXTS = [  # (von, bis, Bild)
    (0.0, 4 * B, stack([("13 JAHRE", 240), ("AUF GTA 6 GEWARTET.", 116)])),
    (4 * B, 16 * B, stack([("ICH NACH", 130), ("10 MINUTEN:", 200)])),
    (16 * B, DUR + 1, stack([("BESTES SPIEL", 170), ("EVER.", 230)])),
]
TEXT_CY = 478
for _, _, im in TEXTS:
    assert im.width - 2 * D.PAD <= 980, im.width
T_TTS = 9.20
SUB_WORDS = [("Hat", 0.04), ("sich", 0.20), ("gelohnt.", 0.42)]
SUB_Y = PY + PH + 110


def spring(t, zeta=0.5, omega=18.0):
    if t <= 0:
        return 0.0
    wd = omega * math.sqrt(1 - zeta ** 2)
    return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + zeta * omega / wd * math.sin(wd * t))


def paste_center(canvas, im, cx, cy, scale=1.0, op=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if op < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * op))
        im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


PANEL_SHADOW = Image.new("RGBA", (D.W, D.H), (0, 0, 0, 0))
PANEL_SHADOW.paste((7, 8, 16, 170), (0, PY - 14, D.W, PY + PH + 14))
PANEL_SHADOW = PANEL_SHADOW.filter(ImageFilter.GaussianBlur(16))


def out_time(src, tag):
    for p in timeline:
        if p["tag"] == tag and p["kind"] == "play" and p["a"] <= src <= p["a"] + (p["t1"] - p["t0"]) * p["sp"]:
            return p["t0"] + (src - p["a"]) / p["sp"]
    raise ValueError(src)


def compose(frame, t, tag):
    src = Image.fromarray(frame)
    # Hintergrund: Vollbild-Ausschnitt 9:16, stark unscharf, abgedunkelt
    cw = SH * 9 / 16
    cx = min(max(BASE_CX[tag] - cw / 2, 0), SW - cw)
    bg = src.crop((int(cx), 0, int(cx + cw), SH)).resize((54, 96), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(2.2)).resize((D.W, D.H), Image.BILINEAR)
    bg = Image.eval(bg, lambda v: int(v * 0.42)).convert("RGBA")
    x0, y0, w, h = camera(t, tag)
    panel = src.crop((x0, y0, x0 + w, y0 + h)).resize((PW, PH), Image.LANCZOS)
    for th in HITS:                                    # weißer Blitz beim Einschlag
        if 0 <= t - th < 0.14:
            panel = Image.blend(panel, Image.new("RGB", panel.size, (255, 255, 255)), 0.55 * (1 - (t - th) / 0.14))
    bg.alpha_composite(PANEL_SHADOW)
    bg.paste(panel, (0, PY))
    for a, b, im in TEXTS:
        if a <= t < b:
            life = t - a
            sc = 1.0 if life > 0.6 else 0.8 + 0.2 * spring(life)
            paste_center(bg, im, D.W / 2, TEXT_CY, sc, min(1.0, life / 0.07))
    if t >= T_TTS - 0.05:
        act = max(i for i, (_, wt) in enumerate(SUB_WORDS) if t >= T_TTS + wt - 0.04 or i == 0)
        life = t - (T_TTS + SUB_WORDS[act][1] - 0.04)
        sub = D.subtitle([w for w, _ in SUB_WORDS], act, pop=min(1.0, max(life, 0) / 0.1))
        paste_center(bg, sub, D.W / 2, SUB_Y)
    return np.asarray(bg.convert("RGB"))


def render_video(path):
    n_out = int(round(DUR * FPS))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-an", "-vf", "fps=60000/1001",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{D.W}x{D.H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    fsize = SW * SH * 3
    cur_i, cur = -1, None
    for k in range(n_out):
        t = k / FPS
        ts, p = src_time(t)
        want = int(round(ts * SFPS))
        assert want >= cur_i, (t, ts)
        while cur_i < want:
            buf = dec.stdout.read(fsize)
            if len(buf) < fsize:
                break
            cur, cur_i = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3), cur_i + 1
        enc.stdin.write(compose(cur, t, p["tag"]).tobytes())
    enc.stdin.close(); enc.wait()
    dec.stdout.close(); dec.kill()


# ---- Ton: Musik + Effekte + TTS (keine Spur aus der Quelle!)
def to_stereo(x):
    return np.stack([x, x], 1)


def render_audio(path):
    n = int(DUR * SR)
    music = S.music_bed(DUR, "chase", 0.0)[:n]
    # Musik kurz zurücknehmen in den Standbildern (Treffer wirkt) und unter der Stimme
    g = np.ones(n)
    tt = np.arange(n) / SR
    for th, fz in [(t_hit1, FREEZE1), (t_hit2, FREEZE2)]:
        g = np.minimum(g, np.where((tt >= th) & (tt < th + fz + 0.1), 0.5, 1.0))
    vox = V.load(TTS, SR)
    vi = int(T_TTS * SR)
    g = np.minimum(g, np.where((tt >= T_TTS - 0.1) & (tt < T_TTS + len(vox) / SR + 0.15), 0.4, 1.0))
    k = int(0.03 * SR)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    music = music * g[:, None]
    ev = [("whoosh", 4 * B - 0.18, 0.8), ("pop", 4 * B, 0.7), ("riser", t_hit1 - 1.5, 0.7), ("hit", t_hit1, 1.0),
          ("hit", out_time(GROUND1, "w1"), 0.35),           # Mann schlägt auf
          ("whoosh", 10 * B - 0.18, 0.8), ("hit", t_hit2, 1.0), ("pop", out_time(GROUND2, "w2"), 0.6),
          ("whoosh", 15 * B - 0.18, 0.6), ("chime", 16 * B, 0.8), ("pop", 16 * B, 0.6)]
    fx = np.zeros(n)
    for kind, t0, gain in ev:
        s = S.GEN[kind]() * S.MIX_GAIN[kind] * gain
        i = int(t0 * SR); j = min(n, i + len(s))
        fx[i:j] += s[: j - i]
    fx = fx / np.max(np.abs(fx)) * 0.55
    v = np.zeros(n); j = min(n, vi + len(vox)); v[vi:j] = vox[: j - vi]
    v = v / np.max(np.abs(v)) * 0.85
    mix = music + to_stereo(fx) + to_stereo(v)
    mix *= 0.8 / np.max(np.abs(mix))
    raw = W + "mix_raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    # Lautheit -14 LUFS (2 Durchgänge, linear wenn möglich)
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(o[o.rindex("{"):o.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), path], check=True)


if __name__ == "__main__":
    vid, aud = W + "m3_video.mp4", W + "m3_audio.wav"
    if not os.path.exists(vid) or os.environ.get("VIDEO"):
        render_video(vid)
    render_audio(aud)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                   check=True)
    print("fertig:", OUT, "Dauer", r3(DUR), "Treffer", r3(t_hit1), r3(t_hit2), "TTS", T_TTS)
