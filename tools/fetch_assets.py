#!/usr/bin/env python3
"""Lädt alle Bild-/Video-Quellen aus assets/manifest.json herunter.

Offizielle Rockstar-Bilder -> assets/official/img/   (nicht im Git, © Rockstar)
Freie Clips (Wikimedia)    -> assets/free/           (nicht im Git, zu groß)
Braucht Netzwerkzugriff auf www.rockstargames.com und upload.wikimedia.org.
"""
import json
import os
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def fetch(url: str, dest: str):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("  vorhanden:", os.path.relpath(dest, ROOT))
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    wait = 15
    for attempt in range(5):
        r = subprocess.run(["curl", "-sSL", "-m", "300", "-o", dest, "-w", "%{http_code}", url],
                           capture_output=True, text=True)
        code = r.stdout.strip()
        if r.returncode == 0 and code == "200":
            print("  ok:      " + os.path.relpath(dest, ROOT))
            time.sleep(3)  # Server schonen
            return
        if os.path.exists(dest):
            os.remove(dest)
        if code != "429":
            break
        print(f"  gedrosselt (429), warte {wait}s …")
        time.sleep(wait)
        wait *= 2
    print(f"  FEHLER ({code}): " + os.path.relpath(dest, ROOT))


GALLERY_PAGES = ["https://www.rockstargames.com/VI/launch-gallery", "https://www.rockstargames.com/VI/media"]
GALLERY_RE = r"/VI/_next/static/media/((?:Vice_City|Grassrivers|Leonida_Keys|Port_Gellhorn|Jason_Duval|Lucia_Caminos|Jason_and_Lucia|Jason_Lucia_Rooftop|Jason_Lucia_Lock_And_Load|hero)[A-Za-z0-9_]*)\.[A-Za-z0-9_~.-]*?\.(jpg|jpeg|webp)"
MIDAS = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"


def fetch_gallery():
    """Echte GTA-6-Screenshots (4K) aus Rockstars Launch-Gallery/Media-Seite."""
    import re
    seen = {}
    for page in GALLERY_PAGES:
        html = subprocess.run(["curl", "-sS", "-m", "60", page], capture_output=True, text=True).stdout
        for m in re.finditer(GALLERY_RE, html):
            name = m.group(1)
            if name.endswith(("_landscape", "_square", "_tablet", "_ultrawide")):
                continue
            seen.setdefault(f"{name}.{m.group(2)}", "https://www.rockstargames.com" + m.group(0))
    for fname, url in sorted(seen.items()):
        fetch(url, os.path.join(ROOT, "assets", "official", "gallery", fname))


def main():
    man = json.load(open(os.path.join(ROOT, "assets", "manifest.json"), encoding="utf-8"))
    print("Offizielle Bilder:")
    for a in man["official"]:
        fetch(a["src"], os.path.join(ROOT, "assets", "official", "img", a["name"]))
    print("Rockstar-Galerie (Screenshots):")
    fetch_gallery()
    print("Tiefen-Modell:")
    fetch(MIDAS, os.path.join(ROOT, "models", "midas_small.onnx"))
    print("Freie Clips:")
    for a in man["free"]:
        fetch(a["src"], os.path.join(ROOT, "assets", "free", a["name"]))


if __name__ == "__main__":
    main()
