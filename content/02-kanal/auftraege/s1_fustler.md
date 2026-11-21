# S1 „Fustler – nur noch ein Lebkuchen“ → exports/kanal/S1_fustler-lebkuchen.mp4
Erlaubnis: fustler hat dem Kanal erlaubt, seine Clips zu verwenden (Screenshot liegt beim Nutzer). Credit ist Pflicht.
Quelle: assets/streamer/fustler/lebkuchen_raw.mp4 (Bildschirmaufnahme, 1260x2240 = 9:16, 60 fps, 42,3 s; nicht ins Git).
Inhalt laut Transkript:
- 0:00–0:08 GTA-6-Szene (oben Webcam, unten Spiel, Chat-Overlay). Fustler: „Scheiße. Aber das sieht echt nicht gesund aus, wenn das so dünn ist, ne?“ Spielansage „Weitere Straßenrennen …“.
- ab ca. 0:13 Webcam-Szene: eine Frau beschwert sich: „Das … zurück ins Regal. Das war im Regal gestanden, ich habe die Packung erst gekauft. Einfach nur noch ein … fucking Ding drin. Wollt ihr mich komplett verarschen? Wegen einem Teil schmeißt ihr das ganze Ding wieder zurück?“ Laut Clip-Titel: Fustler hat nur noch einen Lebkuchen übrig gelassen und die Packung zurückgestellt. (Ob die Frau seine Freundin ist, ist nicht belegt – nicht behaupten.)
- ab ca. 0:20 ist oben ein Sponsor-Banner im Stream („yfood Werbung“, am Ende „SNOCKS“). Dieses Banner mit einer eigenen Karte ÜBERDECKEN (keine fremde Werbung im Kanal).
Ziel: TikTok 22–30 s, Hochformat 1080x1920, 30 fps. Das Original bleibt erkennbar (nicht spiegeln, nicht verzerren, kein Tempo-/Tonhöhen-Trick) – es ist erlaubt, wir brauchen keine Tarnung.
Aufbau:
1. Hook 0–3 s (Gemini-TTS, Kore, über den ersten Bildern, Originalton leise darunter): „Fustler zockt GTA sechs, und dann das!“ (Text darf leicht angepasst werden, kurz und neugierig).
2. Clip mit ORIGINALTON: Ausschnitt nach eigenem Ermessen (Vorschlag ca. 0:00–0:32), langweilige Stellen kürzen; Pointe muss drin sein. Schnitte nur an Satzgrenzen.
3. Untertitel für den Originalton (Wortzeiten per phrase_align mit dem Transkript; Schimpfwörter dürfen stehen bleiben, „fucking“ als „f*cking“ schreiben).
4. Karte über dem Sponsor-Banner ab ca. 0:20: z. B. title „Nur noch EIN Lebkuchen?!“ (Plum-Karte, deckt das Banner komplett ab).
5. Dauerhaft oben klein: glowpill „Clip: twitch.tv/fustler“.
6. Kommentar-Frage gegen Ende als Karte: „Hättest du die Packung zurückgestellt? 👇“ (ohne Emoji, wenn die Schrift es nicht kann).
7. Outro 2–3 s (Gemini-TTS): „Mehr GTA-sechs-Momente? Folg mir!“ + „+ Folgen“ + Credit bleibt sichtbar.
Musik: keine oder sehr leise (Originalton hat Vorrang). "lufs": -14.
Technik-Hinweise: Den 9:16-Clip vorab mit ffmpeg zuschneiden/auf 1080x1920@30 skalieren und als Szene im Renderer nutzen (Szene füllt das Bild bei 9:16 ohne Beschnitt; darken 0, bg_blur 0). Prüfen, ob sfx.render_track mehrere voice-Einträge annimmt (Hook-WAV, Clip-Ton, Outro-WAV); sonst die Tonspuren vorher zu einer WAV mischen. Gesichter nicht mit Untertiteln/Karten verdecken.
Abgabe: downloads/S1_fustler-lebkuchen.mp4 (+ _ohne-musik nur falls Musik genutzt). Bauskript nach tools/pipeline/beispiele/build_s1.py.
Beschreibung (Entwurf): Fustler lässt nur noch EINEN Lebkuchen übrig 😭 Clip mit Erlaubnis von twitch.tv/fustler – schaut bei ihm vorbei! Speicher dir das 📌 #fustler #gta6 #twitch #streamer #lustig
Kommentar zum Anpinnen: Hättest du die Packung zurückgestellt? 👇 Clip mit Erlaubnis von twitch.tv/fustler
