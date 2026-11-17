"""Tonspur neu mischen (identisch zum Renderer) und auf ca. -14 LUFS absenken; Video wird nur kopiert."""
import json, os, re, subprocess, sys
sys.path.insert(0, "/home/user/GTA-6/tools")
os.chdir("/home/user/GTA-6")
from leonida import sfx as sfxmod
S = "/tmp/claude-0/-home-user-GTA-6/4314e1e5-1e22-5471-9026-26079bdb67ff/scratchpad"
spec = json.load(open("content/02-kanal/specs/k6.json"))
v = spec["voice"]
def lufs(p):
    o = subprocess.run(["ffmpeg", "-i", p, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
for mp4, music in [("exports/kanal/K6_gta6-update.mp4", spec["music"]), ("exports/kanal/K6_gta6-update_ohne-musik.mp4", False)]:
    wav = f"{S}/k6_mix_{'m' if music else 'o'}.wav"
    sfxmod.render_track(spec.get("sfx", []), spec["duration"], wav, music=music,
                        voice=[{"t": v["t"], "wav": v["wav"]}], duck=spec.get("duck"))
    g = round(-14.0 - lufs(wav), 2)
    tmp = mp4.replace(".mp4", ".tmp.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", f"volume={g}dB", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, mp4); os.remove(wav)
    print(mp4, "Gain", g, "dB ->", lufs(mp4), "LUFS")
