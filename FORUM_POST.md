# Shutter Pilot – Rollladensteuerung für Home Assistant (HACS, komplett per Klick konfigurierbar)

Hallo zusammen,

ich möchte euch meine Home-Assistant-Integration **Shutter Pilot** vorstellen. Sie steuert Rollläden und Jalousien vollautomatisch – **ohne eine einzige Zeile YAML, ohne Automation, ohne Skript**. Die komplette Konfiguration läuft über ein eigenes Panel in der Seitenleiste.

👉 GitHub:
https://github.com/fschubi/shutter_pilot

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
- Es funktionieren **einfache Kontakte** (nur offen/zu), **3-Zustands-Kontakte** mit Kipperkennung und auch Hardware, die **offen und gekippt als zwei getrennte Entitäten** meldet.
- Die Lüftungsposition lässt sich auch **direkt anfahren**, per Knopf auf der Bereichskarte oder per Service – ganz ohne Fensterkontakt.
- Steht der Rollladen tagsüber ohnehin schon oben, passiert beim Fensteröffnen nichts – kein sinnloses Gefahre.

**Aussperrschutz:**
Steht die Terrassentür offen, wird der Rollladen **nicht komplett zugefahren**, sondern nur bis zu einer einstellbaren Mindestposition. Man steht also nicht mehr im Garten vor einem geschlossenen Rollladen.

**Nachholfunktion (Drive-after-close):**
War das Fenster zum eigentlichen Schließzeitpunkt offen, merkt sich Shutter Pilot die Fahrt und führt sie aus, **sobald das Fenster geschlossen wird**. Die abendliche Fahrt fällt also nicht einfach aus.

**Sonnenschutz nach Sonnenstand, Himmelsrichtung und echten Messwerten:**
Man definiert pro Bereich einen Höhenwinkel-Bereich (z. B. 0° bis 15°) und optional die Himmelsrichtung der Fenster. Sobald die Sonne flach genug steht **und** tatsächlich vor den Fenstern steht, fahren die Rollläden auf eine einstellbare Beschattungsposition. Ohne die Richtungsangabe würde ein Westzimmer auch morgens beschattet, weil der Höhenwinkel-Bereich zweimal täglich durchlaufen wird. Für Nord, Ost, Süd und West gibt es eine Schnellwahl.

Sonnenstand sagt aber nur, **wo** die Sonne steht – nicht, ob sie scheint. Deshalb lassen sich bis zu **zwei Zusatzbedingungen** hinterlegen, die zusätzlich erfüllt sein müssen. Das kann ein Binärsensor „hohe Sonneneinstrahlung" sein oder ein Zahlensensor mit Schwellwert – Lux, W/m² oder Temperatur. Bei Zahlensensoren gibt es zwei Schwellen (beschatten ab / aufheben unter), damit die Rollläden bei durchziehenden Wolken nicht ständig hin- und herfahren.

Damit wird nur beschattet, wenn die Sonne wirklich knallt und es warm genug ist. Im Frühjahr und Herbst bleibt die Sonnenwärme drin, wo sie erwünscht ist. Wer nach der **Wettervorhersage** beschatten will, legt einen Template-Sensor mit der Tageshöchsttemperatur an und trägt den als Bedingung ein – ein Rezept dafür steht in der README.

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
3. Diese Adresse als Kategorie **Integration** hinzufügen:
   https://github.com/fschubi/shutter_pilot
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
- Fenster-/Türkontakte: Rollladen fährt beim Öffnen auf Lüftungsposition und danach zurück (auch mit Kipperkennung, auch mit zwei getrennten Sensoren)
- **Aussperrschutz** – fährt bei offener Terrassentür nicht komplett zu
- **Nachholfunktion** – verpasste Fahrten werden ausgeführt, sobald das Fenster zu ist
- **Sonnenschutz** nach Höhenwinkel **und** Himmelsrichtung der Fenster – kein Beschatten am falschen Tagesende
- **Zusatzbedingungen** für die Beschattung: nur bei echter Einstrahlung und ausreichender Wärme
- **Lamellen-Steuerung** für Jalousien und Raffstores
- **Workday-Sensor** für Feiertage, Urlaub und Schichtarbeit
- **Anwesenheitssimulation** über zufälligen Zeit-Offset
- Positionen pro Rollladen (offen / zu / Sonnenschutz), Fahrverzögerung gegen Sicherungsüberlastung
- Licht schaltet beim Zufahren automatisch ein
- Schalter, Sensoren und ein Event als normale HA-Entitäten für eigene Automationen
- Positionen bleiben nach Neustart erhalten, manuelle Bedienung wird respektiert
- Panel in 11 Sprachen, läuft komplett lokal

**Installation:** HACS → Benutzerdefinierte Repositories → die Adresse unten als *Integration* hinzufügen → installieren → neu starten → unter Geräte & Dienste hinzufügen.
https://github.com/fschubi/shutter_pilot

Benötigt Home Assistant 2024.6.0+. Feedback und Ideen sehr willkommen!
👉 https://github.com/fschubi/shutter_pilot

---
---

# ANTWORTBEITRAG (Version 2.2.1)

*Zum Posten als Antwort im Thread. Fasst 2.2.0 und 2.2.1 zusammen.*

Danke euch für das ausführliche Feedback – das war extrem hilfreich. **Version 2.2.1 ist raus und setzt alles davon um.**

## @Bjoerg und @JayJayX – die Entitätsauswahl

Ihr habt völlig recht, das war unbenutzbar. Es war eine simple Auswahlliste mit *allen* Entitäten einer Domain – beim Helligkeitssensor also mehrere hundert Einträge – und sortiert war sie auch noch nach der internen Entity-ID statt nach dem Namen. Ein Sensor „Flur Sensor" mit der ID `sensor.0x00158d0001abcdef` stand damit unter „0". Kein Wunder, dass da niemand durchscrollen will.

Jetzt ist es ein Feld mit **einer Zeile**. Klick drauf, tippen, fertig:

- **Suche** über Anzeigename und Entity-ID, Cursor springt beim Aufklappen direkt ins Suchfeld
- Sortiert nach **Anzeigename**, nicht nach Entity-ID
- **Vorgefiltert je Feld** – beim Fenstersensor stehen Fenster- und Türkontakte oben, beim Helligkeitssensor die Lux-Sensoren, beim Cover die Rollläden
- Erkannt wird über `device_class` **und** über den Namen, damit auch Sensoren ohne gesetzte `device_class` oben landen
- Der Rest bleibt trotzdem erreichbar – nichts wird versteckt, damit niemand seinen exotischen Sensor vergeblich sucht

## Formulare sind jetzt gegliedert

Beim Testen fiel auf, dass die Einstellungen als eine lange Feldliste durchliefen – man sah nicht, wo ein neues Thema anfängt. Beide Formulare haben jetzt Überschriften mit Symbol und Trennlinie:

- **Bereich:** Grunddaten · Zeitplan · Kalender & manuelle Bedienung · Sonnenschutz · Licht
- **Rollladen:** Rollladen · Bereiche · Positionen · Fenster & Lüftung · Lamellen

Die Zeitfelder standen außerdem ganz am Ende des Bereichsformulars, weit weg von der Modusauswahl, zu der sie gehören. Die stehen jetzt direkt dahinter.

## @JayJayX – zweiter Sensor für die Fenstererkennung

Eingebaut. Es gibt ein optionales zweites Feld für einen separaten „gekippt"-Sensor. Der Kipp-Kontakt hat dabei Vorrang, weil viele Fenster im Kippzustand zusätzlich „offen" melden. Wer einen Kontakt mit drei Zuständen hat, lässt das Feld einfach leer.

## @Nicknol – Lüftungsposition

Die gab es tatsächlich schon, sie war nur nicht direkt erreichbar, sondern hing ausschließlich am Fensterkontakt. Jetzt gibt es einen **Knopf „Lüften"** auf jeder Bereichskarte und den Service `shutter_pilot.ventilate_group`. Bewusst dieselbe Position wie bei gekipptem Fenster – ein weiteres Feld zum Ausfüllen wollte ich euch ersparen.

## @Nicknol – Einstrahlung und Temperatur

Der wichtigste inhaltliche Punkt, und du hast völlig recht: Der Sonnenstand sagt nur, *wo* die Sonne steht, nicht ob sie scheint. Es gibt jetzt pro Bereich **bis zu zwei Zusatzbedingungen**, die zusätzlich zu Höhenwinkel und Himmelsrichtung erfüllt sein müssen:

- **Binärsensor** wie dein Einstrahlungssensor → beschattet wird, solange er `on` ist. Deine Hysterese steckt ja schon im Sensor
- **Zahlensensor** (Lux, W/m², °C) → mit „Beschatten ab" und optional „Aufheben unter". Der Abstand zwischen beiden Schwellen ist genau die Hysterese, damit nichts flattert, wenn eine Wolke vorbeizieht

Damit lässt sich dein Fall direkt abbilden: Einstrahlungssensor als Bedingung 1, Außentemperatur als Bedingung 2. An einem sonnigen, aber kühlen Apriltag wird dann nicht beschattet – die Sonnenwärme bleibt drin, wo sie erwünscht ist.

Eine **eigene Vorhersage-Auswertung** habe ich bewusst weggelassen, das wäre eine starre Speziallösung geworden. Stattdessen: Template-Sensor mit der Tageshöchsttemperatur aus `weather.get_forecasts` anlegen und als Bedingung eintragen. Ein fertiges Rezept steht in der README. So lässt sich jede beliebige Größe einhängen, nicht nur die Temperatur.

## Zum Punkt „eine Automation lässt sich leichter tracen"

Berechtigt. Deshalb gibt es einen **Diagnose-Download** mit dem kompletten Laufzeitzustand und ein Event `shutter_pilot_cover_moved` bei jeder automatischen Fahrt, inklusive Grund, Position und Bereich. Damit lässt sich im Logbuch nachvollziehen, warum ein Rollladen gefahren ist.

---

Update kommt wie gewohnt über HACS – danach einmal hart neu laden (Strg/Cmd+Shift+R), damit das Panel neu geladen wird.

Danke nochmal, das hat die Integration deutlich besser gemacht. Weiteres Feedback gerne! 🙂
