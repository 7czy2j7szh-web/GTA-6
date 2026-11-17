import os
import wave
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"
import numpy as np
def align(path, chunks):
    """Silben proportional auf die stimmhafte Zeit verteilen; Wortanfang auf den Einsatz nach einer
    Pause bzw. das nächste Energietal einrasten, immer mit Mindestabstand (keine Wort-Klumpen)."""
    w = wave.open(ROOT + path); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16) / 32768.0
    win = int(0.01 * sr); n = len(x) // win
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1))
    es = np.convolve(e, np.ones(3) / 3, mode="same")
    voiced = es > 0.02
    cum = np.cumsum(voiced) / max(voiced.sum(), 1)
    flat = [wd for ch in chunks for wd in ch]
    tot = sum(s_ for _, s_ in flat); acc = 0; out = []
    for i, (wd, syl) in enumerate(flat):
        j0 = int(np.searchsorted(cum, acc / tot)) if i else int(np.argmax(voiced))
        j = j0
        if i:
            lo, hi = max(j0 - 3, 0), min(j0 + 4, n)
            j = lo + int(np.argmin(es[lo:hi]))
            while j < n - 1 and not voiced[j]:            # in einer Pause: auf den Einsatz danach
                j += 1
            prev_t, prev_syl = out[-1], flat[i - 1][1]
            if j * 0.01 < prev_t + 0.08 * prev_syl:       # Mindestabstand je Silbe
                j = max(j0, int(round((prev_t + 0.08 * prev_syl) / 0.01)))
        out.append(round(j * 0.01, 3)); acc += syl
    res, k = [], 0
    for ch in chunks:
        res.append([[wd, out[k + m]] for m, (wd, _) in enumerate(ch)]); k += len(ch)
    return res
