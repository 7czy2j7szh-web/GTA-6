# Gemeinsame Regeln: Meme-TikToks aus eigener Aufnahme (Stand 22.11.2026)
Quelle: /home/user/GTA-6/assets/eigen/clip1.mov (eigene PS5-Aufnahme des Nutzers aus GTA 6, 1920x1080, 59,94 fps, 22,6 s; NICHT ins Git).
Inhalt: Die Spielfigur (Frau, Tanktop, Shorts) trägt einen grünen Leguan/„Chamäleon“ und wirft ihn auf Passanten; ihr Partner (Glatze, Oberkörper frei, Umhängetasche) läuft mit.
- Wurf 1 ca. 7,5–10 s: Wurf auf einen älteren Mann (weiße Haare) am Bordstein, er fällt um; danach hebt sie das Tier wieder auf, ein silbernes Auto kommt (~11–12 s).
- Wurf 2 ca. 15,3–18 s: Wurf auf einen Jogger (weißes Shirt) auf dem Gehweg, er fällt und kriecht am Boden (bis ~22 s); sie hebt das Tier auf (~21 s).
Genaue Zeiten selbst anhand von Einzelbildern bestimmen.

PFLICHT:
- Den Originalton KOMPLETT entfernen (die Stimme des Nutzers ist im Hintergrund). Neuer Ton: eigene Musik (assets/music/chase.m4a, vice_anthem.m4a oder leonida_nights.m4a; WAV per ffmpeg erzeugen falls nötig), Soundeffekte aus tools/leonida/sfx.py (hit, pop, whoosh, riser, chime) und optional kurze Gemini-TTS-Sätze (tools/leonida/voice.py, Stimme Kore oder Fenrir für trockenen Erzähler-Ton). Lautheit -14 LUFS.
- Hochformat 1080x1920, 30 fps. Layout: klassisches Meme – oben großer Text (Barlow, weiß mit dunklem Schatten oder Plum-Karte), in der Mitte das Video (volle Breite, ggf. leicht gezoomt, damit Minikarte/HUD-Ränder weniger stören), Rest mit unscharfem, abgedunkeltem Video-Hintergrund füllen. Beim Treffer: Punch-Zoom auf die Aktion + Zeitlupe (60-fps-Quelle nutzen) + kurzes Standbild + Soundeffekt.
- Kurz und loopbar: 8–18 s. Text muss in 1–2 s lesbar sein. Keine Untertitel nötig außer für TTS-Sätze.
- Keine fremde Musik, keine Rockstar-Logos einblenden. Es ist eigenes Gameplay – kein Credit nötig.
- Werkzeuge: ffmpeg + PIL (tools/leonida/design.py für Schrift/Karten) oder der Renderer tools/leonida/channel.py (Szenen mit "cam": {"x","zoom":[a,b],"speed"} – speed < 1 = Zeitlupe). Ein vorgerendertes Basis-Video als Szene ist erlaubt.
- Prüfen: Kontaktbogen ansehen (Text lesbar, Treffer gut sichtbar), keine dunklen Bilder (<40), Lautheit, und sicherstellen, dass vom Originalton nichts übrig ist.
- Abgabe: downloads/<Datei>.mp4. Bauskript nach tools/pipeline/beispiele/build_<id>.py. KEIN git. Bericht knapp: Pfad, Dauer, verwendete Stellen, Prüfergebnisse, Beschreibung + Kommentar.
