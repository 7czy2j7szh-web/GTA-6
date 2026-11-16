# Regeln für Gemini-Prompts (damit Clips nicht abgelehnt werden)

**Was bisher funktioniert hat:**
- K3 (Vorladen) und K4 (Spielzeit): Sie sagt nur harmlose Sätze, Startbild ist das Greenscreen-Bild, die Szenenbeschreibung ist immer gleich.

**Was abgelehnt wurde** („I can't make videos of real people in situations like that“):
- K5, Version 1: Sie sollte über Sterben, Beute und einen Hehler reden.
- K5, Version 2: harmloser Text, aber im selben Chat direkt nach der ersten Ablehnung.

**Regeln für jeden neuen Prompt:**
1. **Sie sagt nur harmlose Sätze.** Keine Wörter zu Tod/Sterben, Waffen, Schießen, Polizei, Überfall, Diebstahl, Beute, Hehler, Drogen, Gewalt oder Verbrechen. Solche Spiel-Inhalte kommen als Sprecherstimme über Trailer-Szenen oder auf die Karten, nie in ihren Mund.
2. **Keine echten Personen**, keine Namen von echten Menschen in ihrem Text.
3. **Pro Video ein neuer Gemini-Chat.** Nach einer Ablehnung nicht im selben Chat weitermachen, sondern neu starten.
4. **Startbild:** `greenscreen_gross_blickdicht.png` für beide Clips.
5. **Szenenbeschreibung bleibt wortgleich** zu K3/K4 (SCENE AND STYLE, CHARACTER CONSISTENCY, AUDIO, AVOID). Keine anzüglichen Beschreibungen von Körper oder Posen.
6. **Höchstens 17 Wörter pro 10-Sekunden-Clip**, Zahlen ausgeschrieben, kein Text während sie läuft.

**Vor dem Abschicken prüfen:** Jeden Satz, den sie sagt, gegen Regel 1 und 2 lesen. Im Zweifel den Inhalt auf Sprecherstimme und Karten verschieben.

**Grenze:** Google veröffentlicht die genauen Filterregeln nicht und die Video-KI kann ich von hier aus nicht testen. Die Regeln machen eine Ablehnung deshalb sehr unwahrscheinlich, garantieren kann sie aber niemand.
