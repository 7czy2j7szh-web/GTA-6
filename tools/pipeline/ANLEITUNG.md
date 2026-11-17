# Produktionsanleitung: TikTok-Video im Kanal-Format OHNE Moderatorin

Repo: /home/user/GTA-6 (immer dort arbeiten). Hilfsskripte: P=/home/user/GTA-6/tools/pipeline (Skripte), W=/home/user/GTA-6/work (Zwischendateien, gitignored; anderer Ort per Umgebungsvariable LEONIDA_WORK)
Ergebnis: 1080x1920, 30 fps, Trailer-Szenen im Hintergrund, lila Info-Karten (Plum-Design), Wort-für-Wort-Untertitel, weibliche Gemini-Stimme, Musik "chase". KEINE Figur/Moderatorin im Bild.
**Beste Vorlage: $P/beispiele/build_k6.py** (ohne Moderatorin, fertig geprüft) bzw. build_k7.py. Kopieren nach $P/beispiele/build_<id>.py und nur Text-Zeiten, Karten und Szenen anpassen. In die Spec immer `"lufs": -14` schreiben: Dann gleicht der Renderer die Lautheit selbst an, ein Nachmisch-Skript (k6_loud/k7_relevel) ist nicht mehr nötig. Für die Untertitel-Endzeiten die Logik aus $P/beispiele/build_k5f.py nehmen (s1 = min(nächste Seite, letztes Wort + 0.85)).
Renderer: tools/leonida/channel.py (Doku oben in der Datei), Design: tools/leonida/design.py.

Vorher einmal: `mkdir -p /home/user/GTA-6/work`.

## 1. Stimme (nur Gemini-TTS)
```
cd /home/user/GTA-6 && python3 - <<PY
import sys, shutil, os; sys.path.insert(0,'.')
from tools.leonida import voice
p = voice.generate(open('$W/<id>_text.txt').read().strip(), voice='Kore')
os.makedirs('content/02-kanal/voice/<id>', exist_ok=True); shutil.copy(p, 'content/02-kanal/voice/<id>/take.wav')
PY
python3 $P/tighten.py content/02-kanal/voice/<id>/take.wav content/02-kanal/voice/<id>/voice.wav
python3 $P/stt_full.py content/02-kanal/voice/<id>/voice.wav "Transkribiere wörtlich. Danach eine Zeile: Versprecher oder unklare Wörter?" $W/<id>_stt.json
```
- Bei Fehler 503/429: 20–30 s warten und wiederholen, oder $P/stt.py (leichteres Modell, versteht "Beute/Hehler" u. Ä. manchmal falsch).
- Versprecher oder falsches Wort -> neu erzeugen. voice.generate cached nach Text: für eine neue Aufnahme den Text minimal ändern (z. B. Satzzeichen). Zahlen im Sprechtext AUSGESCHRIEBEN.
- Länge: Ziel 21–28 s Gesamtvideo (TikTok bevorzugt > 20 s).

## 2. Wortzeiten
SENT-Struktur: Sätze -> Seiten (Untertitel-Seiten mit 1–4 Wörtern) -> (Wort, Silbenzahl). Speichern als $W/<id>_sent.json, dann:
```
python3 - <<'PY'
import sys, json
S = "/home/user/GTA-6/work"; sys.path.insert(0, "/home/user/GTA-6/tools/pipeline")
import phrase_align as pa
SENT = json.load(open(S + "/<id>_sent.json"))
orig = pa.phrases; pa.phrases = lambda x, sr: orig(x, sr, min_pause=0.06, min_len=0.45)
words = [tuple(wd) for snt in SENT for ch in snt for wd in ch]
res, rep = pa.run("/home/user/GTA-6/content/02-kanal/voice/<id>/voice.wav", words, S + "/<id>_ph")
json.dump({"res": res, "rep": rep}, open(S + "/<id>_phrase.json", "w"), ensure_ascii=False)
print("match", rep["match_ratio"]); [print(p) for p in rep["phrases"]]
PY
python3 $P/finalize_words.py <id>            # optional: <wortindex> <pause_s> fügt vor diesem Wort eine Kunstpause ein (z. B. vor "Die Lösung", 0.4)
```
-> schreibt content/02-kanal/voice/<id>/final.wav und words.json. Zeilen mit "!" prüfen; offensichtlich falsche Zeiten anhand der Lautstärke (10/20-ms-Energie) von Hand korrigieren.

## 3. Spec bauen ($P/beispiele/build_<id>.py, schreibt content/02-kanal/specs/<id>.json)
- Ab dem ERSTEN Bild (t=0) steht der Suchbegriff groß im Bild (Karte card=False, Zeile type "big").
- Karten oben (y≈520–550), Untertitel sub_y 835, darunter freie Trailer-Szene. bg_blur 0 (keine Figur), darken 0.25, grade wie in der Vorlage.
- Oben (y≈282) eine glowpill-Zeile als FOMO-Hinweis ("… · LÖSUNG AM ENDE"), in der Mitte eine Kommentar-Aufforderung ("… · SCHREIB'S MIR").
- Ende: "+ Folgen" (glowpill, y 330) ab "Folg mir", danach Abschlussfrage groß (y≈820) + Pfeil (type arrow, x 805, y 1200) bis zum Schluss. 1,8–2,0 s Nachlauf nach dem letzten Wort.
- Unbestätigtes klein kennzeichnen ("laut …").
- Szenenschnitte an Satzanfängen; je Szene nur das angegebene Quellfenster (start..ende) nutzen, speed = min(1, Fenster/Szenenlänge), möglichst ≥ 0.55. Quellen: assets/official/video/GTAVI_Trailer_1.mp4 (T1), GTAVI_Trailer_2.mp4 (T2), GTAVI_Launch_Trailer.mp4 (L). Nur die dir zugeteilten Fenster verwenden.
- Texte müssen in die Karte passen (Breite 936 px; Barlow condensed ≈ 0,5 × size pro Zeichen; big ≤ ~9 Zeichen bei 170, sonst kleiner).
- sfx wie in der Vorlage (hit/pop/riser/whoosh/chime), music "chase", duck 21.

## 4. Rendern (~5–10 min)
```
cd /home/user/GTA-6 && python3 -c "
import json,sys; sys.path.insert(0,'tools')
from leonida.channel import Channel
Channel(json.load(open('content/02-kanal/specs/<id>.json'))).render('exports/kanal/<Datei>.mp4')"
```
Erzeugt auch <Datei>_ohne-musik.mp4. Timeout großzügig setzen (600000 ms).

## 5. Prüfen (Pflicht)
- Dunkle Bilder: jedes Bild Graustufen-Mittel < 40 -> Szene tauschen/kürzen.
- Kontaktbogen: ffmpeg -i <mp4> -vf "fps=2,scale=216:-1,tile=11x6" -frames:v 1 <jpg> und ansehen: Texte lesbar, nichts abgeschnitten, keine Überlappung Karte/Pille/Untertitel, Szenen passen.
- Lautheit: ffmpeg -i <mp4> -af ebur128 -f null - (Integrated ≈ -14 LUFS; mit "lufs": -14 in der Spec automatisch).
- End-STT auf der Version ohne Musik (ffmpeg -ac 1 -ar 16000 → $P/stt_full.py): alle Sätze richtig.
- Bei Fehlern korrigieren und neu rendern.

## 6. Abgabe
- Beide MP4 nach /home/user/GTA-6/downloads/ kopieren.
- NICHT git commit/push (macht die Haupt-Session). Keine Dateien anderer Videos anfassen.
- Bericht (kurz): Dateipfade, Dauer, Prüfergebnisse, Abweichungen vom Auftrag, Beschreibung + Hashtags + Kommentar zum Anpinnen (Entwurf).
