# PROJEKT-KONTEXT: GTA-6-TikTok-Kanal (Übergabe, Stand 17.11.2026)

> Diese Datei enthält alles, was eine neue Claude-Session oder ein Claude-Projekt braucht, um nahtlos weiterzuarbeiten.
> Zuerst diese Datei lesen. Danach je nach Aufgabe: `tools/pipeline/ANLEITUNG.md` (Video bauen), `content/02-kanal/posting.md` (Posting-Texte), `content/02-kanal/prompts/gemini_regeln.md` (Gemini-App-Prompts).

---

## 1. Worum es geht

- **Ziel:** Deutschsprachiger TikTok-Kanal rund um **GTA 6** aufbauen (Ziel 10.000 Follower). Release: **Donnerstag, 19.11.2026, 0:00 Uhr Ortszeit** (PS5 und Xbox Series X|S).
- **Rollen:**
  - **Claude:** recherchiert News, schreibt Skripte, erzeugt die Stimme, schneidet und rendert **fertige MP4s** und liefert Beschreibung, Hashtags und angepinnten Kommentar.
  - **Nutzer:** lädt die Videos hoch und gibt Feedback.
- **Sprache mit dem Nutzer:** Deutsch, einfach und kurz. Der Nutzer schreibt oft per Spracheingabe mit Tippfehlern und gibt kurze Kommandos („Mach weiter“, „Hier sind die beiden“).
  - Erwartet wird immer: fertiges Video, Beschreibung, Hashtags, angepinnter Kommentar und der Hinweis „KI-generierte Inhalte einschalten“.
- **Repo:** GitHub `7czy2j7szh-web/gta-6`, Arbeits-Branch **`claude/fervent-wright-3nsdjj`**.
  - Nur dorthin pushen.
  - Keinen Pull Request ohne ausdrücklichen Auftrag.
  - Keine Modellnamen in Commits.
  - Commit-Trailer gemäß den Vorgaben der jeweiligen Session.

---

## 2. Aktuelle Entscheidungen (WICHTIG, Stand 17.11.)

1. **Keine Moderatorin mehr im Bild.** Der Nutzer hat am 17.11. entschieden: Videos wie die Kanal-Videos K4/K5 (Trailer-Szenen, lila Karten, Untertitel, Musik), aber **ohne die sprechende Frau**.
2. **Stimme nur über Gemini-TTS:** Modell `gemini-3.8-flash-tts`, weibliche Stimme **Kore** über `tools/leonida/voice.py`.
3. **Arbeitsweise mit Agents:**
   - Die Haupt-Session recherchiert, wählt Themen, schreibt Sprechtexte und Karten-Pläne und verteilt dann je Video einen Agent (`general-purpose`).
   - Jeder Agent produziert sein Video nach `tools/pipeline/ANLEITUNG.md`.
   - Die Haupt-Session prüft, committet und liefert aus.
   - **Grenze:** Der Container hat 4 CPU-Kerne, ein Render braucht etwa 2. Also höchstens **2 Renders parallel**. Recherche-Agents können zusätzlich laufen.
   - **Ehrlich zum Nutzer:** Agents halten die Haupt-Session schlank und machen es schneller, sparen aber nicht unbedingt Tokens insgesamt.
4. **Regeln aus dem TikTok-Boost** (V11 wurde von TikTok als „hilfreich“ geboostet, +520 Aufrufe, über Suche gefunden und geteilt):
   - **Ein Suchbegriff pro Video** („GTA 6 Geld“, „GTA 6 Update“ …), und zwar an drei Stellen: groß im **ersten Bild**, im **ersten gesprochenen Satz** und am **Anfang der Beschreibung**.
   - Video **länger als 20 s** (Ziel 21–28 s), **erste echte Info innerhalb von 3 s**.
   - Beschreibung **über 50 Zeichen mit echten Details**, dazu „Speicher dir das 📌“ und 5 passende Hashtags.
   - Zum Speichern und Teilen auffordern.
   - V11 hatte nur 6,8 s durchschnittliche Wiedergabezeit bei 16,5 s Länge (14,5 % schauten bis zum Ende), 1.130 Aufrufe, 66 Likes, 11 Speicherungen. Die Speicherungen waren das stärkste Signal.

---

## 3. Inhaltsregeln für jedes Video

- **Thema:** News aus den **letzten 24 Stunden**, die die Leute wirklich betreffen. Alternativ ein Suchthema mit Nutzwert.
- **Aufbau:**
  1. FOMO-Hook (in den ersten 1–3 s, mit Suchbegriff)
  2. Fakten
  3. **Kommentar-Aufforderung in der Mitte** („… Schreib's in die Kommentare!“)
  4. **Lösung am Ende** („Die Lösung: …“, mit kurzer Kunstpause davor)
  5. „Folg mir!“ mit Abschlussfrage
- **Oben eine Pille:**
  - zuerst „… · LÖSUNG AM ENDE“
  - in der Mitte „… · SCHREIB'S MIR“
- **Unbestätigtes klar kennzeichnen** („laut Insider“, „laut Previews“, „laut Eurogamer“), auch auf den Karten.
- **Keine Rockstar-Imitation:** kein Rockstar-Branding als eigenes ausgeben. Trailer-Szenen stammen von Rockstars offizieller Medienseite.
- **Quellen** gehören in den angepinnten Kommentar und, wenn nötig, kurz auf die Karte.
- **Posting-Format** (Beispiele in `content/02-kanal/posting.md`):
  - **Beschreibung:** beginnt mit dem Suchbegriff, z. B. „GTA 6 Geld: …“, dann Details, „Speicher dir das 📌“ und 5 Hashtags (#gta6 #gta6deutsch + Themen-Tags).
  - **Kommentar zum Anpinnen:** Frage mit 👇, darunter eine Zeile Quellen bzw. „nicht offiziell bestätigt“.
  - **Hinweis an den Nutzer:** „KI-generierte Inhalte“ einschalten.

---

## 4. Bereits behandelte Themen (Wiederholungen vermeiden)

| Video | Thema |
|---|---|
| C8–C11 | Countdown „Noch X Tage“, 212 GB, Preload |
| V2 | Alles in 10 Sekunden |
| V3 | Release-Uhrzeit 0:00 Ortszeit |
| V4 | Prank „GTA 6 schon heute spielen“ |
| V5 | Milliarde Umsatz |
| V6 | VPN-Trick (Prank mit Wendung) |
| V7 | 30 FPS |
| V8 | PS5 oder Xbox |
| V9 | Standard oder Ultimate |
| V10 | Bekommt GTA 6 eine 100? |
| V11 | Polizei merkt sich alles (Fahndungssystem) |
| V12 | Antwort an Robin (Wertung) |
| V13/V14 | Firmen geben frei (Logitech) |
| V15 | Ist GTA 6 spielen Fremdgehen? |
| V16 | Orte in echt |
| V17 | GTA oder Token |
| S8 | Umfrage „Was machst du zuerst?“ |
| S9 | POV Preload |
| S10 | Läuft GTA 6 auf meinem …? |
| K1 | GTA-6-Box: keine Disc, nur Code; Taschenlampen-Code-Warnung |
| K2 | Spoiler-Gefahr ab Mittwoch: TikTok-Wörterfilter |
| K3 | Größter Fehler am Release-Tag: nicht vorgeladen |
| K4 | Spielzeit: 50 h Story / 200+ h Platin laut Insider Tom Henderson; mit 2 h/Tag Story am 13.12. durch, Platin am 26.02.2027 |
| K5 | GTA 6 Geld: Bargeld weg beim Tod, Beute erst beim Hehler, Story braucht Geld (laut Previews); Lösung: einzahlen |
| K6 | GTA 6 Update (in Arbeit, siehe 9.) |
| K7 | GTA 6 auf Xbox One per Cloud (in Arbeit, siehe 9.) |

---

## 5. Technik: Pipeline und Dateien

### Ordner im Repo
| Pfad | Inhalt |
|---|---|
| `tools/leonida/channel.py` | **Renderer für das Kanal-Format.** Nimmt eine JSON-Spec, rendert das Video und erzeugt automatisch eine zweite Datei `_ohne-musik`. CRF 18, preset slow. |
| `tools/leonida/design.py` | Plum-Design: Karten, Pillen, Glow-Pille, Verlaufstext, Untertitel, Safe-Zone, Pfeil |
| `tools/leonida/voice.py` | Gemini-TTS (`generate(text, voice='Kore')`), gecacht in `assets/voice_cache/` |
| `tools/leonida/sfx.py`, `music.py` | Soundeffekte (hit/pop/riser/whoosh/chime) und selbst komponierte Musik |
| `tools/leonida/greenclip.py`, `presenter.py`, `host.py`, `mascot.py` | Figuren (Greenscreen-Clips, 2D-Moderatorin, Porträtkarte, Bigfoot). **Derzeit nicht im Einsatz.** |
| `tools/pipeline/` | **Hilfsskripte:** `tighten.py` (Pausen kürzen), `stt.py`/`stt_full.py` (Spracherkennung zur Prüfung), `phrase_align.py` + `align_lib.py` + `finalize_words.py` (Wortzeiten), `seg_clip.py` (KI-Masken pro Bild) |
| `tools/pipeline/ANLEITUNG.md` | **Schritt-für-Schritt-Anleitung für ein Video ohne Moderatorin** (auch der Auftrag an die Agents) |
| `tools/pipeline/beispiele/` | Bau-Skripte als Vorlage: `build_k5.py` (Vorlage mit Karten/Szenen), `build_k5f.py`/`build_k4f.py` (finale Versionen) |
| `content/02-kanal/specs/*.json` | Baupläne aller Kanal-Videos |
| `content/02-kanal/voice/<id>/` | `take.wav`, `voice.wav` (Pausen gekürzt), `final.wav`, `words.json` |
| `content/02-kanal/posting.md` | Posting-Texte K1–K5 |
| `content/02-kanal/prompts/` | Gemini-App-Prompts (K5) und `gemini_regeln.md` |
| `downloads/` | **Fertige Videos für den Nutzer** (im Git). `exports/` ist gitignored. |
| `plan/` | Strategie, Formate, Workflow (Stand der Anfangszeit) |
| `work/` | Zwischendateien der Pipeline (gitignored, per `LEONIDA_WORK` änderbar) |

### Nicht im Git (muss in einer neuen Umgebung neu beschafft werden)
- **Trailer** (`assets/official/video/`) laden mit:
  ```
  cd assets/official/video && for n in GTAVI_Trailer_1 GTAVI_Trailer_2 GTAVI_Launch_Trailer; do curl -sSL --http1.1 --retry 5 -o $n.mp4 https://media-rockstargames-com.akamaized.net/VI/downloads/videos/$n/$n.mp4; done
  ```
  Weitere Videos dort: `GTAVI_An_Extended_Look`, `GTAVI_Pre-Load_Now`, `GTAVI_Official_Cover_Art_Landscape`. Bilder kommen über `tools/fetch_assets.py`.
- **Musik als WAV** (`assets/music/*.wav`): Die `.m4a` sind im Git, die WAV-Dateien bei Bedarf mit `ffmpeg -i chase.m4a chase.wav` erzeugen.
- **`assets/host/`:** Die Bilder der Moderatorin (vom Nutzer, privat, gitignored). Derzeit nicht nötig.
- **Python-Pakete:** numpy, pillow, scipy, opencv-python-headless, onnxruntime, praat-parselmouth, rembg. Dazu ffmpeg.

### Ablauf eines Videos (Details in `tools/pipeline/ANLEITUNG.md`)
1. Sprechtext schreiben (Zahlen ausgeschrieben, etwa 60–75 Wörter für 21–28 s).
2. TTS mit Kore, dann `tighten.py`, dann Prüfung mit `stt_full.py`. Bei Versprechern neu erzeugen; dafür den Text minimal ändern, sonst greift der Cache.
3. SENT-Struktur (Sätze → Untertitel-Seiten → (Wort, Silben)), dann `phrase_align.py`, dann `finalize_words.py <id> [wortindex pause]`.
4. Bau-Skript nach Vorlage schreiben, Spec-JSON erzeugen, mit `Channel(spec).render(...)` rendern (etwa 5–10 min).
5. Prüfen:
   - keine dunklen Bilder (Graustufen-Mittel < 40)
   - Kontaktbogen ansehen
   - Lautheit (≈ −14 LUFS)
   - End-STT über die Version ohne Musik
6. Beide MP4 nach `downloads/` kopieren, Posting-Text in `posting.md` eintragen, committen und pushen, Datei an den Nutzer senden.

### Design „Plum“ (Kurzfassung)
- **Schrift:** Barlow Condensed für Titel und große Zahlen, Albert Sans für Text.
- **Effekte:** keine Text-Outlines, nur weicher Schatten und dunkles Glühen.
- **Karten:** lila, Breite 936 px, oben bei y≈520–550.
- **Untertitel:** Wort für Wort mit hervorgehobener Pille, sub_y 835.
- **Zeilentypen:** big (Verlaufstext), title, text, pills, glowpill, strike (wird durchgestrichen), count (zählt hoch), arrow, image. Bewegungen: glide, punch, card.
- **Ende:** „+ Folgen“-Glow-Pille (y 330), große Abschlussfrage (y≈820) und Pfeil (x 805, y 1200).

### Trailer-Szenen: geprüfte Quellfenster (Sekunden, ohne Schnitt oder Schrift)
| Quelle | Fenster | Inhalt / Hinweis |
|---|---|---|
| Launch | 26.42–27.79 | Cabrio |
| Launch | 40.48–42.29 | Jason & Lucia am Auto |
| Launch | 55.22–57.03 | Strand mit Doppeldecker |
| T1 | 2.72–4.96 | Highway bei Sonnenuntergang |
| T1 | 21.79–23.23 | voller Strand |
| T1 | 37.49–39.76 | Dachterrasse/Pool |
| T1 | 39.85–41.29 | VICE-Schriftzug |
| T1 | 42.47–43.86 | Pool-Alligator (Social-Clip) |
| T1 | 46.58–47.49 | Livestream |
| T1 | 47.58–48.56 | Überwachungskamera |
| T1 | 68.72–70.23 | Ladenüberfall |
| T1 | 76.60–78.38 | Türeingang (danach Logo, nicht weiter) |
| T2 | 6.85–8.09 | Insel von oben |
| T2 | 34.66–38.33 | Fahrt aus Fahrerperspektive |
| T2 | 38.42–41.56 | Strand-Fitness |
| T2 | 60.62–63.06 | Jason am Zaun (evtl. Schnitt bei ~62.9) |
| T2 | 63.15–66.16 | Lucia am Zaun, **wird am Ende dunkel**, besser meiden |
| T2 | 66.25–69.15 | Parkplatz (ab 69.3 „ROCKSTAR GAMES PRESENTS“) |
| T2 | 81.45–83.06 | Steg bei Sonnenuntergang |
| T2 | 83.15–85.06 | Steg/Meer bei Sonnenuntergang |
| T2 | 88.28–89.46 | – |
| T2 | 96.18–97.62 | Party auf Yacht |
| T2 | 98.52–99.62 | – |
| T2 | 141.88–143.69 | Motorrad |

Tempo (speed) = Fenster ÷ Szenenlänge, möglichst ≥ 0,55. Ohne Figur: bg_blur 0, darken 0.25.

---

## 6. Gemini, KI-Modelle, Abrechnung

- **API-Schlüssel:** wird vom Netzwerk-Proxy der Umgebung eingesetzt. **Nie im Chat nach Schlüsseln fragen**, sondern bei Bedarf das Credential-Formular benutzen.
- **Abrechnung (seit 16./17.11. aktiv):**
  - Stufe „Kostenpflichtig 1“, Prepaid, rund 8,99 € Gratis-Guthaben (Google-AI-Abo).
  - Dem Nutzer wurde empfohlen, Auto-Reload **aus** zu lassen oder ein Monatslimit zu setzen.
  - Die Meldung „100 $ ausgegeben → Hochstufung“ betrifft nur die Rate-Limits und ist keine Abbuchung.
  - **Vor teuren Aktionen (Video-KI) immer Preis nennen und fragen.**
- **Modelle:**
  - **TTS:** `gemini-3.8-flash-tts`. Stimmen: **Kore** (Standard, weiblich), Leda (weiblich, höher), Fenrir/Puck (männlich, alte V-Videos).
  - **STT/Prüfung:** `gemini-3.5-flash` (genau), `gemini-3.5-flash-lite` (schnell, verhört sich bei Wörtern wie „Hehler“).
  - **Bild:** `gemini-3.1-flash-image` funktioniert (wenige Cent pro Bild).
  - **Video:** `gemini-omni-1.2-flash`, nur über die **Interactions API** erreichbar.
    - Aufruf: `POST /v1beta/interactions` mit `{"model", "input":[{"type":"text"}, {"type":"image","data","mime_type"}], "response_format":{"type":"video","aspect_ratio":"9:16","resolution":"360p|720p|1080p|4k","delivery":"inline|uri"}}`
    - Kosten: etwa 0,07 $/s in 720p, etwa 0,10 $/s in 1080p, Clips bis 15 s.
    - **Blockiert das Bild der Moderatorin mit „prohibited_content“** (feste Sperre, nicht umgehen). Für Szenen ohne Personen nutzbar.
  - **Musik:** `lyria-3-pro-preview` vorhanden, aber ungetestet (Preis vorher prüfen).
- **Gemini-App (beim Nutzer):** Mit der Moderatorin gingen 2 × 10-s-Clips durch, wenn die Regeln in `content/02-kanal/prompts/gemini_regeln.md` eingehalten wurden:
  - harmloser Sprechtext ohne Tod, Waffen oder Verbrechen
  - neuer Chat pro Video
  - Startbild `greenscreen_gross_blickdicht.png`
  - keine anzüglichen Beschreibungen
  - höchstens 17 Wörter pro Clip
  
  Derzeit pausiert, weil die Moderatorin nicht mehr eingesetzt wird.

---

## 7. Umgebung und Grenzen

- **Container:** Cloud, 4 CPU, 15 GB RAM, **keine GPU**. Rendern ist CPU-gebunden.
- **Netzwerk:**
  - Erreichbar: Rockstar-Medien-CDN und die Gemini-API.
  - **Nicht abrufbar** (DNS gesperrt): ai.google.dev, aistudio.google.com, gtabase.com, pcgames.de, gtaintel.com. Stattdessen Websuche und andere Quellen nutzen.
- **Freigestellte Figuren** (falls je wieder nötig):
  - Greenscreen-Key in `greenclip.py` (Key auf dem hochskalierten Bild, Glas-Rettung).
  - Clips ohne Grün: Masken pro Bild mit `tools/pipeline/seg_clip.py` (rembg birefnet-general-lite, etwa 11 s pro Bild).

---

## 8. Feste Regeln (immer)

- Nie nach Geheimnissen oder Schlüsseln im Chat fragen.
- Keine persönlichen Daten des Nutzers nach außen geben.
- Nur auf `claude/fervent-wright-3nsdjj` pushen, keinen PR ohne Auftrag.
- Keine Bot-Checks oder Inhaltsfilter umgehen. Wenn Gemini etwas ablehnt, den Inhalt regelkonform ändern und nie tricksen.
- Kein Rockstar-Branding als eigenes ausgeben, keine erfundenen Fakten. Unbestätigtes immer kennzeichnen.
- Die Bilder der Moderatorin bleiben lokal (gitignored).
- Ehrlich berichten: Was nicht geht oder nicht geprüft ist, klar sagen.

---

## 9. Offene Aufgaben (Stand 17.11.2026, nachmittags)

**K6 und K7 sind fertig** (17.11.): von zwei Agents parallel produziert, geprüft, in `downloads/`, Posting-Texte in `content/02-kanal/posting.md`, Bau-Skripte in `tools/pipeline/beispiele/` (`build_k6.py`, `build_k7.py`; danach jeweils `k6_loud.py` bzw. `k7_relevel.py`, weil der Renderer etwa 2–3 dB zu laut mischt). Die folgenden Pläne dienen nur noch als Referenz.

**Danach in der Haupt-Session:**
1. Ergebnisse prüfen.
2. Posting-Texte in `posting.md` eintragen.
3. `content/02-kanal/voice/k6|k7`, `specs/k6|k7.json` und `downloads/K6*|K7*` committen und pushen.
4. Videos mit Beschreibung und Kommentar an den Nutzer senden.

Falls die Dateien fehlen, die Videos nach diesem Plan neu bauen.

### K6 „GTA 6 Update“ → `K6_gta6-update.mp4`
- **Fakten:**
  - Zweites Update vor Release: 01.002.001 seit 16.11., gestaffelt ausgerollt (33 % → nach 12 h 66 % → nach 24 h alle).
  - Größe: PS5 ≈ 602 MB, Xbox ≈ 1,6 GB. Update 1 (01.002.000) kam am 13.11. mit etwa 1 GB auf PS5.
  - Keine Patchnotes.
  - Prüfen: PS5: Spiel markieren → Options → „Nach Update suchen“. Xbox: Menü → „Spiel verwalten“ → Updates.
  - Quellen: play3.de, Sportskeeda, timesaver.gg.
- **Sprechtext:** „GTA 6 vorgeladen? Das reicht nicht! Rockstar hat schon das zweite Update verteilt, noch vor dem Release. Auf PS5 rund sechshundert Megabyte, auf Xbox eins Komma sechs Gigabyte. Was drin ist, verrät Rockstar nicht. PS5 oder Xbox, was zockst du? Schreib's in die Kommentare! Die Lösung: Prüf es jetzt. Spiel markieren, Options-Taste, Nach Update suchen. Dann geht's am Donnerstag sofort los. Folg mir!“
- **Karten:**
  1. GTA 6 UPDATE / Vorgeladen reicht nicht!
  2. Update Nr. 2 · seit 16.11.
  3. PS5 · 602 MB / XBOX · 1,6 GB
  4. ??? · keine Patchnotes
  5. Was zockst du? PS5 / XBOX
  6. Die Lösung: JETZT PRÜFEN + Wege für PS5/Xbox
  7. + Folgen und „Hast du das Update schon?“
- **Pillen:** „IST DEINE KONSOLE BEREIT? · LÖSUNG AM ENDE“, danach „PS5 ODER XBOX? · SCHREIB'S MIR“.

### K7 „GTA 6 Xbox One“ → `K7_gta6-xbox-one.mp4`
- **Fakten:**
  - Laut Xbox Wire ab 19.11. per Xbox Cloud Gaming auch auf Xbox One (und Series X|S).
  - Start 1 Uhr US-Ostküste = 7 Uhr deutsche Zeit. Series-S-Grafik, 30 FPS.
  - Das Spiel muss trotzdem gekauft werden, Game Pass schaltet es nicht frei.
  - Cloud-Zeit je Abo begrenzt, laut Eurogamer Essential 5 / Premium 10 / Ultimate 15 Stunden. Extra-Zeit kaufen bisher nur für Xbox Insider.
  - PC und PS4: nichts angekündigt.
  - Quellen: Xbox Wire, Eurogamer, GameStar, Notebookcheck, gigamaus.de.
- **Sprechtext:** „GTA 6 auf der Xbox One? Geht, ab Donnerstag! Microsoft streamt es über Xbox Cloud Gaming, ab sieben Uhr morgens, in Series-S-Grafik. Aber es gibt einen Haken: Das Spiel musst du trotzdem kaufen. Und mit Game Pass hast du nur ein Stunden-Limit. Welche Konsole hast du? Schreib's in die Kommentare! Für PS4 und PC ist bisher nichts angekündigt. Die Lösung für die Xbox One: Spiel kaufen, Game Pass aktiv, Donnerstag ab sieben Uhr streamen. Folg mir!“
- **Karten:**
  1. GTA 6 auf der XBOX ONE? / GEHT!
  2. Xbox Cloud Gaming · AB 7 UHR
  3. HAKEN 1: SPIEL KAUFEN
  4. HAKEN 2: Cloud-Stunden je Abo (5/10/15)
  5. Welche Konsole hast du?
  6. PS4 & PC (durchgestrichen) · bisher nichts angekündigt
  7. Die Lösung: 3 Schritte
  8. + Folgen und „Zockst du in der Cloud?“
- **Pillen:** „ES GIBT EINEN HAKEN · LÖSUNG AM ENDE“, danach „WELCHE KONSOLE? · SCHREIB'S MIR“.

### Nächste Ideen (ab Release 19.11.)
- „Das Erste, was du in GTA 6 machen solltest“ / „GTA 6 erste Schritte“ (Suchwelle ab Release)
- Launch-Probleme: Server, Download-Code in der Box (laut Berichten fehlt er bei manchen Exemplaren oder funktioniert nicht)
- „GTA 6 PC – kommt es?“ (Rockstar hat nichts angekündigt; Vergleich: GTA 5 kam rund 19 Monate später auf PC, RDR2 rund 13 Monate)
- Launch-Festival in Miami am 21.11.
- Ursprünglicher GTA-6-Leaker bekennt sich schuldig (laut Berichten)
- Nach Release Tipp-Videos mit Suchbegriff: „GTA 6 Geld verdienen“, „GTA 6 Polizei abhängen“, „GTA 6 bestes Auto“, „GTA 6 Cheats“
- Recherche kann ein eigener Agent machen, während gerendert wird.
