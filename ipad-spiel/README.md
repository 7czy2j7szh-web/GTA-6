# Neonküste – iPad-Spiel (3D)

Eigenes 3D-Fahrspiel im Open-World-Stil: Küstenstadt mit Downtown-Hochhäusern, Strandmeile, Palmenviertel und Hafen.
Läuft komplett im Browser (three.js r128 von cdnjs), kein Mac und kein App Store nötig.

| Datei | Zweck |
|---|---|
| `neonkueste.html` | Quelle (wird als Claude-Artifact veröffentlicht) |
| `index.html` | Eigenständige Version für jedes Webhosting (z. B. GitHub Pages) |
| `build.sh` | Erzeugt `index.html` aus `neonkueste.html` |

## Inhalt
- 6 Missionen (werden nacheinander freigeschaltet) + Freie Fahrt mit Tag-und-Nacht-Wechsel
  1. Erste Runde – Checkpoints in Downtown (Sonnenuntergang)
  2. Zerbrechlich – 3 Pakete liefern, Unfälle beschädigen die Ware (Tag)
  3. Heiße Ware – Tasche zum Hafen bringen, Polizei jagt dich (Dämmerung)
  4. Strandrennen – gegen 3 Gegner (Sonnenuntergang)
  5. Die Verfolgung – roten Sportwagen rammen (Nacht)
  6. Großer Abgang – 4 Sterne abschütteln (Nacht, Regen)
- Verkehr, Fußgänger, Polizei mit Fahndungssternen, Werkstätten, Drift, Nitro, Minikarte mit Route

## Steuerung
- **iPad:** linker Daumen lenkt (nach oben ziehen = Gas). Rechts: Gas, Bremse, Drift, Nitro. Kamera-Knopf oben rechts.
- **Tastatur:** Pfeile/WASD, Leertaste = Drift, Shift = Nitro, C = Kamera, P = Pause.

## Aufs iPad
Link in Safari öffnen → Teilen → „Zum Home-Bildschirm“.
