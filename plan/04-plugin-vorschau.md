# Vorschau Phase 2: Das Content-Plugin

> Wird **erst gebaut, wenn du den Plan freigegeben hast.** Hier steht, was es können soll, damit du weißt, wozu du Ja sagst.

## Ziel

Du schickst mir Rohclips von der Konsole und ein Stichwort. Zurück kommt ein **fertiges TikTok-Video (MP4)** mit Hook, Untertiteln, Zooms, Effekten, Sound und Cover, das du nur noch hochladen musst.

Technische Grundlage: ein Claude-Code-Plugin in diesem Repo. ffmpeg, Python und Pillow sind in der Umgebung bereits vorhanden (geprüft am 08.11.).

## Befehle

| Befehl | Was er macht |
|---|---|
| `/pack [Thema]` | Komplettes Content-Pack nach Vorlage (Hook, Skript, Aufnahmeliste, Caption …) |
| `/countdown [Tag]` | Rendert ein Countdown-Video komplett automatisch aus Fakt + offiziellem Bild + Text + Sound, **ohne Gameplay**. Steht als Erstes, damit es noch vor dem Release hilft. |
| `/render [Clip] [Format]` | Rohclip → fertiges Video im gewünschten Format (F08–F17) |
| `/vergleich [Clip GTA 5] [Clip GTA 6]` | GTA 5 vs. GTA 6 mit geteiltem Bildschirm, synchron geschnitten, beschriftet |
| `/floridaman [Schlagzeile] [Clips]` | Nachrichten-Look: Schlagzeilen-Grafik, Bauchbinde, Nachrichten-Schnitt |
| `/cover [Text]` | Titelbild im Look des Accounts |
| `/report` | Wochenbericht aus deinen Analytics-Screenshots |
| `/ideen` | Neue Ideen aus News, deinen Zahlen und den Kommentaren |

## Was `/render` mit einem Clip macht

1. **Hochformat:** 16:9 → 9:16, wahlweise mit intelligentem Ausschnitt, unscharfem Hintergrund oder geteiltem Bildschirm
2. **Schnitt:** langweilige Stellen raus, Tempo-Rampen auf die Action
3. **Hook-Titel** in den ersten 2 Sekunden, groß und im Account-Look
4. **Untertitel** Wort für Wort, groß, mittig, im sicheren Bereich
5. **Zoom-Punches und Wackeln** an markierten Stellen bzw. auf dem Beat
6. **Soundeffekte** (Whoosh, Bass-Schlag, Nachrichten-Jingle), selbst erzeugt bzw. lizenzfrei, damit es keine Rechteprobleme gibt
7. **Serien-Logo** („FLORIDA MAN #7", „NOCH 3 TAGE") und auf Wunsch ein Fortschrittsbalken
8. **Endlosschleife:** Ende und Anfang werden aneinander angepasst
9. **Export:** 1080×1920, H.264/AAC, Lautstärke für Handys angepasst, plus Cover-Bild
10. **Check vor der Ausgabe:** Ich schaue mir Einzelbilder an und prüfe Spoiler, Gewalt-Nahaufnahmen, Texte im sicheren Bereich und die Länge

## Helfer im Hintergrund (Agents)

- **Hook-Doktor:** bewertet jeden Hook streng und macht 3 bessere Vorschläge
- **Regel-Wächter:** prüft jedes Pack gegen die Spielregeln (Spoiler, Leaks, Musik, Gewalt, Clickbait)
- **Trend-Scout:** sucht täglich nach GTA-6-News, Entdeckungen und Patches und macht daraus Ideen

## Noch offen (klären wir beim Bau)

| Frage | Optionen |
|---|---|
| Wie kommen deine Clips zu mir? | GitHub-Upload (kurze Clips), Cloud-Link (eventuell Netzwerk-Freigabe nötig) |
| Stimme | deine eigene Aufnahme (Empfehlung) oder eine Computerstimme. Ob eine gute deutsche Stimme offline läuft, teste ich beim Bau. |
| Automatische Untertitel aus deiner Stimme | Spracherkennung, falls sie sich hier installieren lässt; sonst Untertitel aus dem Skript |

## Reihenfolge beim Bau

1. **Tag 1:** `/countdown` + `/cover` + Account-Look, sofort für die restlichen Countdown-Tage nutzbar
2. **Tag 2–3:** `/render`, `/vergleich`, `/floridaman` mit Test-Clips, **fertig vor dem 19.11.**
3. **Danach:** `/report`, Agents, Feinschliff anhand der echten Zahlen

**Je früher du den Plan freigibst, desto mehr Countdown-Tage kann das Plugin schon übernehmen.**
