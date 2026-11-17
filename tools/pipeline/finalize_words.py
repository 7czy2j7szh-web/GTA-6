"""Wortzeiten verfeinern (align je Phrase), optional Kunstpause einfügen, words.json + final.wav schreiben, prüfen."""
import sys, json, wave, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Arbeitsordner für Zwischendateien (<id>_sent.json, <id>_phrase.json, ...); Standard: <repo>/work
S = os.environ.get("LEONIDA_WORK", os.path.join(os.path.dirname(os.path.dirname(HERE)), "work"))
import phrase_align as pa
from align_lib import align
R = os.path.dirname(os.path.dirname(HERE)) + "/"

def finalize(name, pause_before_word=None, pause=0.0, fixes=None):
    SRC = R + f"content/02-kanal/voice/{name}/voice.wav"
    SENT = json.load(open(S + f"/{name}_sent.json"))
    words = [tuple(wd) for snt in SENT for ch in snt for wd in ch]
    rep = json.load(open(S + f"/{name}_phrase.json"))["rep"]
    times, assign, um = pa.assign_from(SRC, words, rep["phrases"])
    x, sr = pa.load(SRC)
    os.makedirs(S + f"/{name}_phw", exist_ok=True)
    fine = list(times)
    for k, (a, b, _) in enumerate(rep["phrases"]):
        idx = [i for i in range(len(words)) if assign[i] == k]
        if not idx: continue
        p = f"{S}/{name}_phw/p{k}.wav"
        o = wave.open(p, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
        o.writeframes((x[int(a * sr):int(b * sr)] * 32767).astype(np.int16).tobytes()); o.close()
        al = align(os.path.relpath(p, R), [[words[i] for i in idx]])[0]
        for i, (_, t) in zip(idx, al): fine[i] = round(a + t, 3)
    for (i, t) in (fixes or {}).items(): fine[i] = t
    cut = None
    if pause_before_word is not None:
        i0 = pause_before_word
        cut = max(p[0] for p in rep["phrases"] if p[0] <= fine[i0] + 0.05)
        y = np.concatenate([x[:int(cut * sr)], np.zeros(int(pause * sr), np.float32), x[int(cut * sr):]])
        fine = [t + (pause if t >= cut - 0.01 else 0) for t in fine]
    else:
        y = x
    o = wave.open(R + f"content/02-kanal/voice/{name}/final.wav", "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((y * 32767).astype(np.int16).tobytes()); o.close()
    out, k = [], 0
    for snt in SENT:
        so = []
        for ch in snt:
            so.append([[w, round(fine[k + m], 3)] for m, (w, _) in enumerate(ch)]); k += len(ch)
        out.append(so)
    json.dump({"sent": out, "dur": round(len(y) / sr, 3), "pause_at": cut, "pause": pause},
              open(R + f"content/02-kanal/voice/{name}/words.json", "w"), ensure_ascii=False)
    # Prüfung auf der Endfassung
    win = int(0.01 * sr); n = len(y) // win
    e = np.sqrt((y[:n * win].reshape(n, win) ** 2).mean(1)); es = np.convolve(e, np.ones(3) / 3, "same")
    flat = [(w, t) for (w, _), t in zip(words, fine)]
    for i, (wd, t) in enumerate(flat):
        j = int(t / 0.01); flag = []
        if (es[j:j + 6].max() if j < n else 0) < 0.02: flag.append("Start in Stille")
        if i + 1 < len(flat):
            seg = es[int(t / 0.01):int(flat[i + 1][1] / 0.01)] < 0.012
            run = best = 0
            for v in seg:
                run = run + 1 if v else 0; best = max(best, run)
            if best >= 18 and not wd.rstrip("“\"").endswith((".", ",", ":", "?", "!")): flag.append(f"Stille {best * 0.01:.2f}s danach")
            if flat[i + 1][1] - t < 0.05: flag.append("zu dicht")
        if flag: print("  !", i, wd, t, flag)
    print(" ".join(f"{i}:{w}@{t:.2f}" for i, (w, t) in enumerate(flat)))
    print("dur", round(len(y) / sr, 2), "pause at", cut)

if __name__ == "__main__":
    name = sys.argv[1]
    pw = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    pz = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    fx = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    finalize(name, pw, pz, {int(k): v for k, v in fx.items()})
