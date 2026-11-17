"""Tonspur von K7 neu mischen und um festen Wert absenken (Ziel ≈ -14 LUFS), Video unverändert übernehmen."""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, "tools")
from leonida import sfx as sfxmod
R = "/home/user/GTA-6/"
spec = json.load(open(R + "content/02-kanal/specs/k7.json"))
v = spec["voice"]
for path, music, db in [("exports/kanal/K7_gta6-xbox-one.mp4", spec["music"], float(sys.argv[1])),
                        ("exports/kanal/K7_gta6-xbox-one_ohne-musik.mp4", False, float(sys.argv[2]))]:
    wav = R + path[:-4] + "_relevel.wav"
    sfxmod.render_track(spec.get("sfx", []), spec["duration"], wav, music=music,
                        voice=[{"t": v["t"], "wav": v["wav"]}], duck=spec.get("duck"))
    w = wave.open(wav); p = w.getparams(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32); w.close()
    x = np.clip(x * 10 ** (db / 20), -32768, 32767).astype(np.int16)
    o = wave.open(wav, "wb"); o.setparams(p); o.writeframes(x.tobytes()); o.close()
    tmp = R + path[:-4] + "_tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", R + path, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, R + path); os.remove(wav)
    print("ok", path, db)
