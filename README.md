# GTA 6 TikTok: 0 → 10.000 Follower

Die Projekt-Zentrale. **Claude macht die Videos fertig, du lädst hoch.**
Faceless-Kanal: ohne Konsole, ohne Stimme, ohne Gesicht.

| | |
|---|---|
| Release GTA 6 | **Do, 19.11.2026** (PS5 & Xbox Series X\|S) |
| Preload | ab **10.11.2026**, bis zu 212 GB |
| Ziel | 10.000 Follower (realistisch: Januar–März 2027) |
| Status | 🟢 Countdown läuft: Videos bis 10.11. fertig |

## Dateien

| Datei | Inhalt |
|---|---|
| [`plan/00-update-faceless.md`](plan/00-update-faceless.md) | **Zuerst lesen:** neuer Rahmen, Bildquellen & Lizenzen, neue Hauptformate |
| [`plan/01-strategie.md`](plan/01-strategie.md) | Positionierung, Phasen, Rechnung, Spielregeln, Kennzahlen |
| [`plan/02-formate.md`](plan/02-formate.md) | Format-Bibliothek, Hook-Bank, Schnitt-Gesetze |
| [`plan/03-workflow.md`](plan/03-workflow.md) | Zusammenarbeit, Wochen-Report |
| [`plan/04-plugin-vorschau.md`](plan/04-plugin-vorschau.md) | Ausbaustufen des Video-Werkzeugs |
| [`content/01-countdown/posting.md`](content/01-countdown/posting.md) | **Was du wann postest** (Caption, Hashtags, Kommentar) |
| [`content/01-countdown/pakete.md`](content/01-countdown/pakete.md) | Drehbücher Countdown-Phase |
| `content/01-countdown/specs/` | Video-Baupläne (JSON) für den Renderer |
| `tools/` | Renderer (`render.py`), Musik (`leonida/music.py`), Asset-Download (`fetch_assets.py`) |
| `assets/music/leonida_nights.m4a` | Unser eigener Erkennungs-Track „Leonida Nights" (selbst komponiert) |

## Videos neu rendern

```bash
pip install -r requirements.txt                        # numpy, pillow, scipy
python3 tools/fetch_assets.py                          # Bilder & Clips laden (nicht im Git)
python3 tools/render.py content/01-countdown/specs/c11.json
python3 tools/render.py content/01-countdown/specs/c11.json --preview 0.5 5 15   # nur Standbilder
```
