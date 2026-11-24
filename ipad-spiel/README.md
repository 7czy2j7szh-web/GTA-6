# Neonküste – iPad-Spiel (3D)

Eigenes 3D-Fahrspiel im Open-World-Stil: Küstenstadt mit Downtown-Hochhäusern, Strandmeile, Palmenviertel und Hafen.
Läuft komplett im Browser (three.js r128 von cdnjs), kein Mac und kein App Store nötig.

| Datei | Zweck |
|---|---|
| `neonkueste.html` | Quelle (wird als Claude-Artifact veröffentlicht) |
| `index.html` | Eigenständige Version für jedes Webhosting (z. B. GitHub Pages) |
| `build.sh` | Erzeugt `index.html` aus `neonkueste.html` |

## Spielprinzip
Münzen verdienen → im **Autohaus** bessere Autos kaufen und tunen → schwerere Missionen schaffen.

- **Münzen** gibt es für Missionen (Bronze ×1, Silber ×1,5, Gold ×2; Wiederholung ohne bessere Medaille 35 %), Aufträge in der Freien Fahrt, Drifts, eingesammelte Münzen und knappe Überholmanöver. In der Freien Fahrt kostet Erwischtwerden 15 % Kaution, Totalschaden 10 %.
- **8 Autos** von Klasse D bis S: Rostlaube (gratis), Stadtflitzer 600, Brummer 1.500, Muscle 77 3.000, Coupé GT 6.000, Strandrakete 10.000, Neon Venom 18.000, Phantom X 32.000.
- **Tuning** pro Auto: Motor, Reifen, Panzerung, Nitro (je 3 Stufen) und Lackierung (gratis).
- **8 Missionen** mit empfohlener Klasse, werden nacheinander freigeschaltet:
  1. Erste Runde (D) · 2. Zerbrechlich (D) · 3. Heiße Ware (C) · 4. Strandrennen (B) · 5. Die Verfolgung (C) · 6. Großer Abgang (B) · 7. Nachtrennen (A) · 8. König der Küste (S)
- Spielstand wird im Browser gespeichert (localStorage).

## Steuerung
- **iPad:** linker Daumen lenkt (nach oben ziehen = Gas). Rechts: Gas, Bremse, Drift, Nitro. Kamera-Knopf oben rechts.
- **Tastatur:** Pfeile/WASD, Leertaste = Drift, Shift = Nitro, C = Kamera, P = Pause.

## Aufs iPad
Link in Safari öffnen → Teilen → „Zum Home-Bildschirm“.
