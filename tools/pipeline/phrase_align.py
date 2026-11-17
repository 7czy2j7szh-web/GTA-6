"""Robuste Wortzeiten: Aufnahme an Pausen in Phrasen schneiden, jede Phrase transkribieren,
Skriptwörter per Textabgleich den Phrasen zuordnen, innerhalb der Phrase nach Silben verteilen."""
import base64, difflib, json, os, re, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np

def load(path):
    w = wave.open(path); sr = w.getframerate()
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768, sr

def phrases(x, sr, min_pause=0.06, min_len=0.35):
    win = int(0.01 * sr); n = len(x) // win
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1)); es = np.convolve(e, np.ones(3) / 3, "same")
    q = es < 0.012; cuts = []; i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            if (j - i) * 0.01 >= min_pause and i > 0 and j < n: cuts.append(((i + j) / 2) * 0.01)
            i = j
        else: i += 1
    b = [0.0] + cuts + [len(x) / sr]
    out = []
    for k in range(len(b) - 1):
        if out and (b[k + 1] - b[k] < min_len):
            out[-1][1] = b[k + 1]
        else:
            out.append([b[k], b[k + 1]])
    return out, es

def stt(wav_bytes, tmp):
    b = base64.b64encode(wav_bytes).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": b}},
            {"text": "Transcribe this short German audio verbatim. Output only the words."}]}]}
    open(tmp, "w").write(json.dumps(body))
    import time
    for model in ["gemini-3.5-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
        r = subprocess.run(["curl", "-sS", "-m", "120", "-H", "Content-Type: application/json", "-d", "@" + tmp,
                            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"],
                           capture_output=True, text=True)
        try:
            return json.loads(r.stdout)["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            time.sleep(6)
            continue
    return ""

NUM = {"212": "zweihundertzwölf", "19.": "neunzehnten", "6": "sechs", "gb": "gigabyte"}
def norm(w):
    w = w.lower().strip()
    w = NUM.get(w, w)
    w = re.sub(r"[^a-zäöüß0-9]", "", w)
    return w

def wav_bytes(seg, sr):
    import io
    bio = io.BytesIO(); o = wave.open(bio, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((seg * 32767).astype(np.int16).tobytes()); o.close(); return bio.getvalue()

def run(path, script_words, tmpdir):
    """script_words: [(wort, silben)] in Reihenfolge -> [(wort, startzeit)]"""
    x, sr = load(path)
    ph, es = phrases(x, sr)
    os.makedirs(tmpdir, exist_ok=True)
    def job(k):
        a, b = ph[k]
        return stt(wav_bytes(x[int(a * sr):int(b * sr)], sr), f"{tmpdir}/p{k}.json")
    with ThreadPoolExecutor(3) as ex:
        texts = list(ex.map(job, range(len(ph))))
    hyp, hyp_ph = [], []
    for k, t in enumerate(texts):
        for w in t.replace("-", " ").split():
            nw = norm(w)
            if nw: hyp.append(nw); hyp_ph.append(k)
    ref = [norm(w.replace("-", "")) for w, _ in script_words]
    # GTA-6-Box -> "gta6box"; Hypothese kann "gta 6 box" sein -> Ersatz-Zuordnung über SequenceMatcher-Blöcke
    sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    assign = [None] * len(ref)
    for a, b, size in sm.get_matching_blocks():
        for i in range(size): assign[a + i] = hyp_ph[b + i]
    # Lücken: zwischen Nachbarn interpolieren (monoton)
    for i in range(len(ref)):
        if assign[i] is None:
            prev = next((assign[j] for j in range(i - 1, -1, -1) if assign[j] is not None), 0)
            nxt = next((assign[j] for j in range(i + 1, len(ref)) if assign[j] is not None), prev)
            assign[i] = prev if prev == nxt else prev  # bleibt in der vorherigen Phrase
    for i in range(1, len(assign)):                     # Monotonie erzwingen
        assign[i] = max(assign[i], assign[i - 1])
    # Wörter je Phrase nach Silben über die stimmhafte Zeit verteilen
    voiced = es > 0.02
    times = [0.0] * len(ref)
    for k in range(len(ph)):
        idx = [i for i in range(len(ref)) if assign[i] == k]
        if not idx: continue
        a, b = int(ph[k][0] / 0.01), int(ph[k][1] / 0.01)
        v = voiced[a:b]
        if v.sum() == 0: v = np.ones(b - a, bool)
        cum = np.cumsum(v) / v.sum()
        syl = [script_words[i][1] for i in idx]; tot = sum(syl); acc = 0
        first = a + int(np.argmax(v))
        for i, s in zip(idx, syl):
            j = first if acc == 0 else a + int(np.searchsorted(cum, acc / tot))
            while j < b - 1 and not voiced[j] and acc > 0: j += 1
            times[i] = round(j * 0.01, 3); acc += s
    unmatched = sum(1 for i, (a_, b_, s) in enumerate([]) )
    report = {"phrases": [[round(a, 2), round(b, 2), t] for (a, b), t in zip(ph, texts)],
              "match_ratio": round(sm.ratio(), 3)}
    return [(w, t) for (w, _), t in zip(script_words, times)], report


def assign_from(path, script_words, phr):
    """Zuordnung aus gespeicherten Phrasen-Transkripten neu berechnen (ohne neue API-Aufrufe).
    Nicht erkannte Wörter gehören zur Phrase des nächsten erkannten Worts (Satzanfänge werden oft verschluckt)."""
    x, sr = load(path)
    win = int(0.01 * sr); n = len(x) // win
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1)); es = np.convolve(e, np.ones(3) / 3, "same")
    ph = [(a, b) for a, b, _ in phr]
    hyp, hyp_ph = [], []
    for k, (_, _, t) in enumerate(phr):
        for w in t.replace("z.B.", "zum Beispiel").replace("-", " ").split():
            nw = norm(w)
            if nw: hyp.append(nw); hyp_ph.append(k)
    ref = [norm(w.replace("-", "")) for w, _ in script_words]
    sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    assign = [None] * len(ref)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for i in range(i1, i2): assign[i] = hyp_ph[j1 + i - i1]
        elif op == "replace":                       # falsch erkannte Wörter: anteilig zuordnen
            for i in range(i1, i2):
                j = j1 + int((i - i1) * (j2 - j1) / (i2 - i1))
                assign[i] = hyp_ph[min(j, j2 - 1)]
    for i in range(len(ref)):
        if assign[i] is None:                       # nicht gehört: Satzende -> vorige Phrase, sonst nächste
            nxt = next((assign[j] for j in range(i + 1, len(ref)) if assign[j] is not None), None)
            prev = next((assign[j] for j in range(i - 1, -1, -1) if assign[j] is not None), 0)
            endp = script_words[i][0].rstrip("“\"").endswith((".", "!", "?"))
            assign[i] = prev if (endp or nxt is None) else nxt
    for i in range(1, len(assign)):
        assign[i] = max(assign[i], assign[i - 1])
    voiced = es > 0.02
    times = [0.0] * len(ref)
    for k in range(len(ph)):
        idx = [i for i in range(len(ref)) if assign[i] == k]
        if not idx: continue
        a, b = int(ph[k][0] / 0.01), int(ph[k][1] / 0.01)
        v = voiced[a:b]
        if v.sum() == 0: v = np.ones(b - a, bool)
        cum = np.cumsum(v) / v.sum()
        syl = [script_words[i][1] for i in idx]; tot = sum(syl); acc = 0
        first = a + int(np.argmax(v))
        for i, s in zip(idx, syl):
            j = first if acc == 0 else a + int(np.searchsorted(cum, acc / tot))
            while j < b - 1 and not voiced[j] and acc > 0: j += 1
            times[i] = round(j * 0.01, 3); acc += s
    unmatched = [script_words[i][0] for i in range(len(ref)) if all(not (a <= i < a + s) for a, _, s in sm.get_matching_blocks())]
    return times, assign, unmatched
