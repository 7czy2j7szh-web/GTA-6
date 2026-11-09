# Analytics-Log

## C11 „Noch 11 Tage" (gepostet 08.11., 15:06, 20 s)
| Views | Likes | Kommentare | Shares | Saves | Ø Wiedergabe | Ganz angesehen | Neue Follower |
|---|---|---|---|---|---|---|---|
| 1.906 | 22 | 3 | 2 | 0 | 4,3 s (21 %) | 2 % | 0 |

- Meiste Absprünge bei **0:01**, Ausspielung nach ca. 6–7 h beendet.
- Wer bleibt, interagiert gut (Likes/Kommentare/Shares im Verhältnis zur Wiedergabezeit ok).

## S10 „Läuft GTA 6 auf …?" (gepostet 08.11.)
- ~2.000 Views, ~20 Likes (Details/Screenshot fehlen noch)

## C10v2 „212 GB · Noch 10 Tage" (gepostet 09.11., 18:09, 12 s) – Stand nach ~50 min
| Views | Likes | Kommentare | Shares | Saves | Ø Wiedergabe | Ganz angesehen | Neue Follower |
|---|---|---|---|---|---|---|---|
| 241 | 5 | 1 | 0 | 0 | 3,4 s (28 %) | 5 % | 0 |

- Meiste Absprünge bei **0:02** (vorher 0:01) = genau beim ersten Textwechsel nach dem Hook.
- Vergleich zu C11: Wiedergabe 21 % → 28 %, ganz angesehen 2 % → 5 %. Besser, aber noch weit unter Ziel (≥ 50 % / ≥ 20 %).
- Views steigen nach 1 h noch gleichmäßig → Ausspielung läuft noch, Endbewertung nach 24 h.
- **Diagnose:** Der Hook „212 GB braucht GTA 6." liefert die komplette Info sofort → kein Grund zu bleiben.

## S8v3 Umfrage „Was machst du ZUERST?" (gepostet 09.11., 19:02, 8 s) – Stand nach ~14 min
| Views | Likes | Kommentare | Shares | Saves | Ø Wiedergabe | Ganz angesehen | Neue Follower |
|---|---|---|---|---|---|---|---|
| 91 | 3 | 1 | 0 | 0 | 3,3 s (41 %) | 9,9 % | 0 |

- Beste Bindung bisher (21 % → 28 % → 41 %), aber Stichprobe noch klein.
- Absprung-Spitze wieder bei 0:02 = erster Bildwechsel nach dem Hook.

---

## Erkenntnisse → neue Regeln (ab 09.11.)
1. **Pointe ins erste Bild**, max. 2–4 Wörter, riesig. Kein Satz, der erst nach 1 s aufgelöst wird.
2. **Helles Bild mit Bewegung ab Frame 0** (schneller Zoom), keine dunklen Standbilder zum Start.
3. **Badge/Fortschrittsbalken erst nach dem Hook** (`chrome_from`), sonst Präsentations-Look.
4. **Länge 8–12 s** statt 20 s → mehr Komplett-Views und Loops.
5. Am Ende **Like-Satz** + Frage im angepinnten Kommentar.

## Technik-Regel (09.11.)
6. **Keine weißen Blitze bei schnellen Bildwechseln** (S8v2 flackerte). Blitz jetzt standardmäßig sanft (`flash_strength` 110, 0 = aus); bei Wechseln < 2 s ganz aus.
7. **Keine dunklen Hintergründe** (Garage, Nacht-Hafen, Auto-Innenraum) – wirken nach einem Wechsel wie ein schwarzer Bildschirm.
8. **Hook = offene Frage, nicht die Antwort.** Neugier aufbauen (z. B. „Deine Konsole ist NICHT bereit …"), Auflösung erst am Ende.
