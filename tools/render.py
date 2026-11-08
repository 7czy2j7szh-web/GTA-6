#!/usr/bin/env python3
"""Rendert ein oder mehrere Video-Specs zu fertigen TikTok-MP4s.

Beispiele:
  python3 tools/render.py content/01-countdown/specs/c11.json
  python3 tools/render.py content/01-countdown/specs/*.json --preview 1.5
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leonida.engine import Renderer, load_spec  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--preview", type=float, nargs="*", help="nur Standbilder zu diesen Sekunden rendern")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--audio-only", action="store_true", help="nur Soundeffekte im fertigen MP4 erneuern")
    args = ap.parse_args()
    for p in args.specs:
        spec = load_spec(p)
        r = Renderer(spec)
        base = spec["out"].rsplit(".", 1)[0]
        if args.audio_only:
            print("Ton erneuert:", r.remux_audio(spec["out"]))
            continue
        if args.preview is not None:
            for t in args.preview or [0.5]:
                print(r.still(t, f"{base}_preview_{t:.1f}s.jpg"))
            continue
        print(f"Rendere {p} …", file=sys.stderr)
        r.render(spec["out"], audio=not args.no_audio)
        if "cover_at" in spec:
            print(r.still(spec["cover_at"], f"{base}_cover.jpg"))


if __name__ == "__main__":
    main()
