# Shutter Pilot – Rollladensteuerung für Home Assistant (HACS, komplett per Klick konfigurierbar)

Hallo zusammen,

ich möchte euch meine Home-Assistant-Integration **Shutter Pilot** vorstellen. Sie steuert Rollläden und Jalousien vollautomatisch – **ohne eine einzige Zeile YAML, ohne Automation, ohne Skript**. Die komplette Konfiguration läuft über ein eigenes Panel in der Seitenleiste.

👉 **GitHub: https://github.com/fschubi/shutter_pilot**

---

## Warum noch eine Rollladensteuerung?

Wer seine Rollläden in Home Assistant automatisiert, kennt das: Man baut sich fünf Automationen, dann kommen die Sonderfälle – das Fenster ist offen, wenn zugefahren werden soll. Die Terrassentür steht auf und man sperrt sich aus. Morgens ist es noch zu dunkel, also soll der Rollladen später hoch. Im Schlafzimmer gelten andere Zeiten als im Wohnzimmer. Am Wochenende sowieso. Und nach jedem Neustart steht alles anders da als vorher.

Genau diese Fälle nimmt Shutter Pilot einem ab. Man legt **Bereiche** an (z. B. Wohnen, Schlafen, Kinderzimmer), ordnet ihnen Rollläden zu – fertig. Den Rest macht die Integration.

---

## Was kann sie? (in einfachen Worten)

**Drei Steuerungsarten – pro Bereich frei wählbar:**

- **Zeit** – feste Uhrzeiten zum Hoch- und Runterfahren, mit **getrennten Zeiten für Werktag und Wochenende**.
- **Helligkeit** – gesteuert über einen Lux-Sensor. Man gibt an, ab welcher Helligkeit hoch- bzw. runtergefahren wird, plus erlaubte Zeitfenster (z. B. „hoch frühestens ab 05:00, spätestens 09:00"). So fährt der Rollladen nicht um 3 Uhr nachts hoch, nur weil eine Straßenlaterne angeht.
- **Sonnenstand** – nutzt Sonnenauf- und -untergang von Home Assistant, mit Offset in Minuten (z. B. „30 Minuten nach Sonnenuntergang zu").

**Fenster- und Türkontakte werden berücksichtigt:**

- Wird ein Fenster geöffnet oder gekippt, während der Rollladen unten ist, fährt er automatisch auf **Lüftungsposition**. Wird das Fenster wieder geschlossen, fährt er zurück auf die Position von vorher.
- Es funktionieren sowohl **einfache Kontakte** (nur offen/zu) als auch **3-Zustands-Kontakte** mit Kipperkennung.
- Steht der Rollladen tagsüber ohnehin schon oben, passiert beim Fensteröffnen nichts – kein sinnloses Gefahre.

**Aussperrschutz:**
Steht die Terrassentür offen, wird der Rollladen **nicht komplett zugefahren**, sondern nur bis zu einer einstellbaren Mindestposition. Man steht also nicht mehr im Garten vor einem geschlossenen Rollladen.

**Nachholfunktion (Drive-after-close):**
War das Fenster zum eigentlichen Schließzeitpunkt offen, merkt sich Shutter Pilot die Fahrt und führt sie aus, **sobald das Fenster geschlossen wird**. Die abendliche Fahrt fällt also nicht einfach aus.

**Sonnenschutz nach Sonnenstand und Himmelsrichtung:**
Man definiert pro Bereich einen Höhenwinkel-Bereich (z. B. 0° bis 15°) und optional die Himmelsrichtung der Fenster. Sobald die Sonne flach genug steht **und** tatsächlich vor den Fenstern steht, fahren die Rollläden auf eine einstellbare Beschattungsposition. Ohne die Richtungsangabe würde ein Westzimmer auch morgens beschattet, weil der Höhenwinkel-Bereich zweimal täglich durchlaufen wird. Für Nord, Ost, Süd und West gibt es eine Schnellwahl.

**Lamellen für Jalousien und Raffstores:**
Neben der Höhe lässt sich pro Rollladen der Lamellenwinkel für Offen, Geschlossen und Sonnenschutz einstellen. Entitäten ohne Lamellen-Unterstützung werden automatisch übersprungen.

**Feiertage, Urlaub und Schichtarbeit:**
Statt starr auf Samstag und Sonntag zu schauen, kann pro Bereich ein Workday-Sensor hinterlegt werden. Damit gilt an Feiertagen automatisch der Wochenendplan.

**Anwesenheitssimulation:**
Optional werden die Fahrzeiten täglich zufällig um bis zu ±X Minuten verschoben, damit von außen kein starres Muster erkennbar ist.

**Manuelle Bedienung wird respektiert:**
Hat man einen Rollladen von Hand auf eine bestimmte Höhe gestellt, überschreibt die Automatik das nicht beim nächsten Durchlauf. Positionen werden dauerhaft gespeichert und **nach einem Home-Assistant-Neustart wiederhergestellt**.

**Weitere Kleinigkeiten, die im Alltag viel ausmachen:**

- **Fahrverzögerung** pro Bereich: die Rollläden fahren nacheinander statt alle gleichzeitig – schont Motoren und Sicherung.
- **Positionen pro Rollladen** einstellbar: „offen", „geschlossen" und „Sonnenschutz" (jeweils 0–100 %). Nicht jeder Rollladen muss ganz zufahren.
- **Getrennte Bereiche für Hoch und Runter**: ein Rollladen kann morgens zum Bereich „Schlafen" gehören und abends zum Bereich „Wohnen".
- **Lichtaktion**: beim Zufahren kann automatisch ein Licht oder Schalter eingeschaltet werden (bei Lampen inklusive Helligkeit in %), beim Auffahren wieder aus.
- **Schalter in Home Assistant**: es gibt einen Master-Schalter für die gesamte Automatik und je einen Auto-Schalter pro Bereich. Die sind ganz normale `switch`-Entitäten und lassen sich in eigenen Automationen, Szenen oder auf dem Dashboard verwenden (z. B. „Urlaubsmodus" oder „Automatik heute aus").
- **Sensoren**: pro Bereich ein Sensor mit der nächsten geplanten Fahrt (Zeit und Richtung) und ein Binary-Sensor für den Sonnenschutz-Status – damit lässt sich alles auch auf einem normalen Dashboard darstellen.
- **Event `shutter_pilot_cover_moved`** bei jeder automatischen Fahrt, inklusive Position, Grund und Bereich. Damit kann man sich eigene Benachrichtigungen bauen.
- **Services** für eigene Automationen: `shutter_pilot.open_group`, `shutter_pilot.close_group` und `shutter_pilot.sun_protect_group`, jeweils mit `area_id`.
- **Panel in 11 Sprachen** (DE, EN, FR, ES, IT, NL, DA, SV, PL, PT, NB) – es übernimmt automatisch die Spracheinstellung von Home Assistant.
- **Läuft komplett lokal.** Keine Cloud, keine externen Abhängigkeiten, keine zusätzlichen Python-Pakete.

---

## Das Panel

Nach der Einrichtung erscheint „Shutter Pilot" in der Seitenleiste, mit drei Reitern:

- **Dashboard** – jeder Bereich als Karte: aktuelle Positionen aller Rollläden live, Auto-Schalter, und Schnelltasten für **Hoch / Stop / Runter / Sonnenschutz**. Je nach Modus zeigt die Karte zusätzlich die passenden Infos an: bei Zeitmodus die heute aktiven Zeiten (Woche/Wochenende), bei Helligkeitsmodus den aktuellen Lux-Wert und die Schwellen, bei Sonnenmodus den nächsten Sonnenauf-/-untergang plus die daraus berechnete Fahrzeit inklusive Offset.
- **Bereiche** – Bereiche anlegen und einstellen (Modus, Zeiten, Schwellwerte, Sonnenschutz, Lichtaktion, Fahrverzögerung).
- **Rollläden** – Cover-Entitäten zuordnen, Fenstersensor hinterlegen, Positionen per Schieberegler festlegen.

Alles wird direkt gespeichert, ein Neustart von Home Assistant ist dafür nicht nötig.

---

## Installation

**Über HACS (empfohlen):**

1. HACS öffnen
2. Oben rechts das Drei-Punkte-Menü → **Benutzerdefinierte Repositories**
3. `https://github.com/fschubi/shutter_pilot` als Kategorie **Integration** hinzufügen
4. Nach „Shutter Pilot" suchen und installieren
5. Home Assistant neu starten

**Manuell:**

1. Aktuelles Release von GitHub herunterladen
2. Ordner `custom_components/shutter_pilot` nach `config/custom_components/` kopieren
3. Home Assistant neu starten

**Danach einrichten:**

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **Shutter Pilot** suchen und hinzufügen
3. „Shutter Pilot" erscheint in der Seitenleiste – dort im Reiter **Bereiche** den ersten Bereich anlegen und im Reiter **Rollläden** die Cover zuordnen

Standort und Sonnenzeiten werden automatisch aus den Home-Assistant-Einstellungen übernommen, da muss man nichts eintragen.

**Voraussetzung:** Home Assistant **2024.6.0** oder neuer. Es funktioniert mit jeder Rollladen-Entität, die Positionen unterstützt (`cover.*` mit `set_cover_position`) – also z. B. Shelly, Zigbee-Rollladenaktoren, KNX, Homematic, ESPHome und so weiter.

---

## Kurzes Beispiel aus der Praxis

Mein Wohnbereich läuft im Helligkeitsmodus: morgens ab 05:00 Uhr darf hochgefahren werden, aber erst wenn es draußen hell genug ist. Abends ab 16:00 Uhr wird zugefahren, sobald es dämmert – dabei geht automatisch die Stehlampe auf 40 % an. Die Terrassentür hat einen Kontakt: steht sie offen, bleibt der Rollladen auf 20 % stehen statt komplett zuzufahren. Mache ich die Tür später zu, holt Shutter Pilot die Fahrt von selbst nach.

Der Schlafbereich läuft parallel im Zeitmodus mit eigenen Wochenendzeiten – und das ganz ohne eine einzige Automation in Home Assistant.

---

## Feedback erwünscht

Das Projekt ist Open Source und wird aktiv weiterentwickelt. Über Rückmeldungen, Fehlerberichte und Ideen freue ich mich sehr:

- **Repo:** https://github.com/fschubi/shutter_pilot
- **Fehler & Wünsche:** https://github.com/fschubi/shutter_pilot/issues

Aktuell überlege ich, eine **Markisensteuerung** zu ergänzen – mit Wind-, Regen- und Temperatursensor sowie automatischem Einfahren bei Unwetter. Wer das nutzen würde, kann hier abstimmen:
https://github.com/fschubi/shutter_pilot/discussions/1

Übersetzungen sind ebenfalls willkommen – Pull Requests gerne.

Viel Spaß damit!

---
---

# KURZVERSION (für kleinere Posts / Kommentare)

**Shutter Pilot – Rollladensteuerung für Home Assistant (HACS)**

Steuert Rollläden und Jalousien vollautomatisch, komplett über ein eigenes Panel in der Seitenleiste – **kein YAML, keine Automationen nötig**.

Pro Bereich wählbar: **Zeit** (getrennt für Woche/Wochenende), **Helligkeit** (Lux-Sensor mit Zeitfenstern) oder **Sonnenstand** (Sonnenauf-/-untergang mit Offset).

Dazu:
- Fenster-/Türkontakte: Rollladen fährt beim Öffnen auf Lüftungsposition und danach zurück (auch mit Kipperkennung)
- **Aussperrschutz** – fährt bei offener Terrassentür nicht komplett zu
- **Nachholfunktion** – verpasste Fahrten werden ausgeführt, sobald das Fenster zu ist
- **Sonnenschutz** nach Höhenwinkel **und** Himmelsrichtung der Fenster – kein Beschatten am falschen Tagesende
- **Lamellen-Steuerung** für Jalousien und Raffstores
- **Workday-Sensor** für Feiertage, Urlaub und Schichtarbeit
- **Anwesenheitssimulation** über zufälligen Zeit-Offset
- Positionen pro Rollladen (offen / zu / Sonnenschutz), Fahrverzögerung gegen Sicherungsüberlastung
- Licht schaltet beim Zufahren automatisch ein
- Schalter, Sensoren und ein Event als normale HA-Entitäten für eigene Automationen
- Positionen bleiben nach Neustart erhalten, manuelle Bedienung wird respektiert
- Panel in 11 Sprachen, läuft komplett lokal

**Installation:** HACS → Benutzerdefinierte Repositories → `https://github.com/fschubi/shutter_pilot` als *Integration* → installieren → neu starten → unter Geräte & Dienste hinzufügen.

Benötigt Home Assistant 2024.6.0+. Feedback und Ideen sehr willkommen!
👉 https://github.com/fschubi/shutter_pilot
