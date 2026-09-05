# Shutter Pilot

> **Automatische Rollladen-/Jalousiensteuerung für Home Assistant**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/fschubi/shutter_pilot)](https://github.com/fschubi/shutter_pilot/releases)
[![Lizenz](https://img.shields.io/github/license/fschubi/shutter_pilot)](LICENSE)
[![PayPal](https://img.shields.io/badge/Spenden-PayPal-00457C?logo=paypal&logoColor=white)](https://paypal.me/fschubi)

[English version](README.md)

---

Shutter Pilot ist eine Home Assistant Custom Integration, die Rollläden, Jalousien und Markisen automatisch steuert – basierend auf **Zeitplänen**, **Helligkeitssensoren** oder **Sonnenstand**. Die Integration bietet ein eigenes **Sidebar-Panel** für die komfortable Verwaltung direkt in Home Assistant.

## Funktionen

- **Drei Steuerungsmodi** pro Bereich: Zeitbasiert, helligkeitsbasiert (Lux-Sensor) oder Sonnenstand (Sonnenauf-/untergang)
- **Sidebar-Panel** mit Dashboard, Bereiche, Rollläden, Markisen und Dachfenster-Tabs zur vollständigen Verwaltung
- **Fenster-/Türsensoren** – öffnet Rollläden automatisch bei geöffnetem Fenster
- **Aussperrschutz** – verhindert vollständiges Schließen bei offener Tür
- **Sonnenschutz mit Himmelsrichtung** – beschattet nur, wenn die Sonne im eingestellten Höhenwinkel **und** vor den Fenstern steht
- **Nachholfunktion** – holt geplante Fahrten nach, wenn das Fenster bei der Schließzeit noch offen war
- **Pro-Rollladen-Positionen** – konfigurierbare Offen-, Geschlossen- und Sonnenschutz-Positionen
- **Lamellen-Steuerung** – optionaler Lamellenwinkel für Jalousien und Raffstores
- **Workday-Sensor** – Feiertage, Urlaub und Schichtarbeit statt starrer Samstag/Sonntag-Logik
- **Anwesenheitssimulation** – zufälliger Zeit-Offset von ±X Minuten
- **Licht-Aktionen** – schaltet ein Licht/Schalter ein wenn Rollläden schließen
- **Auto-Modus-Schalter** – Automatik pro Bereich ein-/ausschalten über HA-Switches
- **Eigene Entitäten** – nächste Fahrt und Sonnenschutz-Status als Sensoren für Dashboard und Automationen
- **Mehrsprachiges Panel** – passt sich automatisch an die HA-Sprache an (11 Sprachen)
- **Wochentag-/Wochenend-Zeitpläne** – separate Zeitfenster für Wochentage und Wochenenden (Zeitmodus und Helligkeitsmodus)
- **Sonnenstand-Info im Dashboard** – zeigt nächsten Sonnenaufgang/-untergang, Offset und berechnete Trigger-Zeit für Sonnenstand-Bereiche
- **Markisen** – eigener Tab, Beschattung ohne Zeitplan, mit **Wind-, Regen- und Frostschutz** (gilt auch bei ausgeschalteter Automatik) und optionaler Ausfahrlänge nach Sonnenhöhe
- **Dachfenster** – eigener Tab, Öffnen nach Bedingungen (z. B. Innentemperatur), **Regen-, Wind- und Frostschutz** schließt sie wieder

## Screenshots

Klicke auf ein Bild, um es auf GitHub in **voller Auflösung** zu öffnen (hier werden nur verkleinerte Vorschaubilder angezeigt).

<p align="center">
  <a href="docs/screenshots/dashboard.png" title="Dashboard – Vollbild">
    <img src="docs/screenshots/dashboard.png" alt="Shutter Pilot – Dashboard" width="280" />
  </a>
  &nbsp;&nbsp;
  <a href="docs/screenshots/areas.png" title="Bereiche – Vollbild">
    <img src="docs/screenshots/areas.png" alt="Shutter Pilot – Bereiche" width="280" />
  </a>
  &nbsp;&nbsp;
  <a href="docs/screenshots/shutters.png" title="Rollläden – Vollbild">
    <img src="docs/screenshots/shutters.png" alt="Shutter Pilot – Rollläden" width="280" />
  </a>
</p>

<p align="center">
  <b>Dashboard</b> · <b>Bereiche</b> · <b>Rollläden</b>
</p>

## Installation

### HACS (Empfohlen)

1. Öffne HACS in Home Assistant
2. Klicke auf das Drei-Punkte-Menü (oben rechts) → **Benutzerdefinierte Repositories**
3. Füge `https://github.com/fschubi/shutter_pilot` als **Integration** hinzu
4. Suche nach "Shutter Pilot" und installiere
5. Starte Home Assistant neu

### Manuell

1. Lade das neueste Release von [GitHub Releases](https://github.com/fschubi/shutter_pilot/releases) herunter
2. Kopiere den Ordner `custom_components/shutter_pilot` in dein HA `config/custom_components/` Verzeichnis
3. Starte Home Assistant neu

## Einrichtung

1. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche nach **Shutter Pilot** und klicke zum Hinzufügen
3. Nach der Einrichtung erscheint "Shutter Pilot" in der Seitenleiste

> **Hinweis:** Das Panel steht allen Benutzern in der Seitenleiste zur Verfügung, **konfigurieren kann es aber nur ein Administrator**. Ohne Administratorrechte zeigt das Panel das Dashboard mit den Bedienknöpfen (hoch, runter, stopp, Sonnenschutz, lüften); die Tabs für Bereiche, Rollläden und Einstellungen sowie der Hauptschalter und die Automatik-Schalter sind ausgeblendet. Alle ändernden Befehle werden zusätzlich serverseitig geprüft.

## Konfiguration

Die gesamte Konfiguration erfolgt über das **Shutter Pilot Sidebar-Panel**:

### Bereiche (Tab "Bereiche")

Klicke auf **"Bereich hinzufügen"** um einen neuen Bereich zu erstellen. Wähle einen Steuerungsmodus:

| Modus | Beschreibung |
|-------|-------------|
| **Zeit** | Rollläden fahren zu festen Zeiten hoch/runter mit separaten Wochentag-/Wochenend-Zeiten |
| **Helligkeit** | Gesteuert durch einen Lux-Sensor mit konfigurierbaren Schwellwerten und erlaubten Zeitfenstern |
| **Sonnenstand** | Nutzt Home Assistants Sonnenauf-/untergang-Tracking mit konfigurierbarem Offset |
| **Kein Zeitplan** | Der Bereich fährt weder nach Uhr noch nach Lux oder Sonnenstand – es gelten nur Sonnenschutz und Lüften. Für alle, die Shutter Pilot ausschließlich zum Beschatten einsetzen, und für Markisen-Bereiche |

Jeder Bereich kann zusätzlich haben:
- **Sonnenschutz** – fährt Rollläden auf eine Mittelposition, wenn die Sonne im eingestellten Höhenwinkel-Bereich **und** vor den Fenstern steht
- **Zusatzbedingungen für den Sonnenschutz** – bis zu zwei Sensoren, die zusätzlich erfüllt sein müssen (siehe unten)
- **Licht-Aktion** – schaltet ein Licht/Schalter ein wenn Rollläden schließen
- **Fahrverzögerung** – Sekunden zwischen einzelnen Rollläden (verhindert Sicherungsüberlastung)

### Rollläden (Tab "Rollläden")

Klicke auf **"Rollladen hinzufügen"** um eine Cover-Entity einem Bereich zuzuweisen:

- **Cover-Entity** – deine `cover.*` Entity
- **Fenstersensor** – optionaler `binary_sensor.*` für Fenster-Offen/Kipp-Erkennung
- **Zweiter Fensterkontakt** – für Doppelflügelfenster mit einem Kontakt pro Flügel. Beide werden zusammen gelesen: das Fenster gilt als offen, sobald einer der beiden es meldet. Damit greifen Aussperrschutz, Lüftungsposition und die Nachholfunktion auch dann, wenn nur der zweite Flügel offen steht. Es gelten dieselben Zustände wie beim ersten Kontakt – zwei Flügel eines Fensters sind dieselbe Hardware zweimal
- **Zusätzlicher Sensor für „gekippt"** – nur nötig, wenn dein Fenster zwei getrennte Entitäten meldet, eine für offen und eine für gekippt. Bei einem Kontakt mit drei Zuständen bleibt das Feld leer
- **Fenster-Status „offen"** – welcher Zustand der Entität „Fenster ist offen" bedeutet. Ein `binary_sensor` kennt nur `on` und `off`; welcher davon offen heißt, hängt vom Kontakt ab, deshalb steht der gerade gemeldete Zustand unter dem Feld. Die gängigen Schreibweisen (`on`/`open`/`offen`/`true`) gelten als gleichbedeutend, ebenso `off`/`closed`/`geschlossen`. Ein `sensor` mit drei Zuständen wird direkt gelesen
- **Bereich Hoch / Bereich Runter** – welcher Bereich diesen Rollladen für Hoch-/Runter-Fahrten steuert
- **Positions-Slider** – Offen-, Geschlossen- und Sonnenschutz-Positionen (0-100%)
- **Aussperrschutz** – Mindest-Position bei offener Tür (verhindert Aussperren)
- **Nachholfunktion** – holt einen verpassten Schließbefehl nach, wenn das Fenster noch offen **oder gekippt** war. Bis dahin fährt der Rollladen ohne den Haken darunter **gar nicht** – auch nicht auf die Kipp-Position. Der Merker übersteht seit 2.7.0 auch einen Neustart von Home Assistant; nach 24 Stunden wird er verworfen, weil eine Fahrt von vorgestern nichts mehr darüber sagt, was jetzt gelten soll
- **Bei offenem oder gekipptem Fenster schon auf die Lüftungsposition fahren** – erscheint nur zusammen mit der Nachholfunktion. Ohne den Haken bleibt der Rollladen stehen, wo er steht, bis das Fenster zugeht; mit ihm fährt er auf die Position für „offen" bzw. „gekippt", so weit es der Aussperrschutz zulässt, und die volle Fahrt bleibt vorgemerkt. Vorgabe aus: er bewegt sonst in jeder zufriedenen Anlage abends Rollläden
- **Antrieb meldet keine Position (blind fahren)** – für einseitigen Funk wie Somfy RTS. Solche Antriebe antworten nicht, und jede Prüfung, die eine Position braucht, gab bisher auf – damit waren Fenstertrigger und automatisches Lüften für sie stillschweigend abgeschaltet. Mit dem Haken rechnet Shutter Pilot stattdessen mit der Position, die es zuletzt gesendet hat. Die Fahrtkontrolle überspringt solche Rollläden ohnehin, weil es nichts zu prüfen gibt
- **„My"-Position** – erscheint nur zusammen mit dem Haken darüber. Somfy RTS und Verwandte kennen eine dritte, einmal am Motor angelernte Stellung; Home Assistant bietet sie als Knopf an (Overkiz) oder man packt sie in ein Skript. Entität eintragen und angeben, welchem Prozentwert sie entspricht – jede Fahrt, die höchstens 15 % daneben liegt, drückt dann diesen Knopf, statt auf einen Endanschlag auszuweichen. Ohne sie wird an so einem Antrieb aus jeder Zwischenposition ein Endanschlag
- **Verzögerung beim Schließen** – wie lange „geschlossen" anhalten muss, bevor der Rollladen zurückfährt (0–30 s, Standard 5 s). Beim Drehen des Griffs von „gekippt" auf „offen" läuft der Kontakt kurz durch „geschlossen"; ohne Wartezeit fährt der Rollladen sofort zurück und die Offen-Position wird nie erreicht. `0` schaltet die Wartezeit ab

### Dashboard

Das Dashboard zeigt alle Bereiche als Karten mit:
- Aktuelle Rollladen-Positionen (live)
- Raumtemperatur, wenn im Bereich ein Sensor dafür hinterlegt ist (reine Anzeige)
- Auto-Modus-Schalter pro Bereich
- **Sonnenstand-Info** für Sonnenstand-Bereiche: nächster Sonnenaufgang/-untergang, Offset, berechnete Trigger-Zeit, aktuelle Elevation
- Schnellaktions-Buttons: **Hoch**, **Stop**, **Runter**, **Sonnenschutz**, **Lüften**

Über den Karten steht ein Block für alles, was für das ganze Haus gilt: dieselben
fünf Knöpfe für alle Rollläden zugleich, Automatik und Beschattung für alle
Bereiche an oder aus, und die Werte, die man sonst je Bereich nachsehen müsste –
Sonnenauf- und -untergang, aktuelle Elevation und Azimut, Höchsttemperatur und
Wetterlage von heute.

## Services

| Service | Beschreibung |
|---------|-------------|
| `shutter_pilot.open_group` | Alle Rollläden eines Bereichs öffnen |
| `shutter_pilot.close_group` | Alle Rollläden eines Bereichs schließen |
| `shutter_pilot.stop_group` | Alle fahrenden Rollläden, Markisen und Dachfenster eines Bereichs anhalten |
| `shutter_pilot.sun_protect_group` | Alle Rollläden eines Bereichs in Sonnenschutz-Position fahren |
| `shutter_pilot.ventilate_group` | Alle Rollläden eines Bereichs in die Lüftungsposition fahren |
| `shutter_pilot.retract_awnings` | Alle Markisen sofort einfahren – ohne Staffelung, für eine angekündigte Sturmwarnung |
| `shutter_pilot.resume_automation` | Rollläden an die Automatik zurückgeben, nachdem sie von aussen gefahren wurden. Löscht die manuelle Übersteuerung und fährt sofort auf die Position, die gerade gilt |

`area_id` (z. B. `living`, `schlafzimmer`) ist bei **allen** Diensten **optional**:
ohne Bereich gilt der Dienst für alle Bereiche – „alle Rollläden hoch" ist damit
ein Aufruf und nicht einer je Bereich. Jeder Rollladen fährt dabei auf seine
eigene konfigurierte Position, und keiner fährt doppelt: der Hoch-Dienst filtert
über den Hoch-Bereich, die Runter-Dienste über den Runter-Bereich.

## Entitäten

Zusätzlich zum Panel legt Shutter Pilot Entitäten an, die du auf normalen Dashboards und in eigenen Automationen verwenden kannst:

| Entität | Beschreibung |
|---------|-------------|
| `switch.shutter_pilot_system` | Master-Schalter für die gesamte Automatik |
| `switch.shutter_pilot_auto_<bereich>` | Automatik pro Bereich |
| `switch.shutter_pilot_sonnenschutz_<bereich>` | Beschattung pro Bereich – nur sie, die übrige Automatik läuft weiter |
| `switch.shutter_pilot_rollladen_<name>` | Automatik pro Rollladen (Name aus dem Feld **Name**) |
| `sensor.shutter_pilot_<bereich>_nächste_fahrt` | Zeitstempel der nächsten geplanten Fahrt, Attribut `direction` = `up`/`down` |
| `binary_sensor.shutter_pilot_<bereich>_sonnenschutz` | `on`, solange die Beschattung aktiv ist |
| `sensor.shutter_pilot_status` | Das Haus auf einen Blick: Zustand `open` / `closed` / `partial`, Attribute `open`, `closed`, `partial`, `awnings_extended`, `awnings_retracted`, `windows_open`, `windows_closed`, `shading_active`, `shading_areas`, `shading_covers`. Markisen und Dachfenster zählen getrennt – eine eingefahrene Markise ist in Ruhe, nicht „das Haus ist zu", und ein gekipptes Dachfenster macht das Haus nicht offen |
| `switch.shutter_pilot_markise_<name>` | Automatik pro Markise (der Wind- und Regenschutz gilt trotzdem) |
| `switch.shutter_pilot_dachfenster_<name>` | Automatik pro Dachfenster (der Regen-, Wind- und Frostschutz gilt trotzdem) |
| `binary_sensor.shutter_pilot_<name>_sperre` | `on`, solange die Markise nicht ausfahren bzw. das Dachfenster nicht öffnen darf. Attribute: `reasons`, `release_in_seconds` |

## Automatik abschalten

Die Automatik lässt sich auf drei Ebenen anhalten, jede für sich:

| Ebene | Wirkung |
|-------|---------|
| **Hauptschalter** | die gesamte Integration fährt nichts mehr |
| **Bereich** | nur dieser Bereich pausiert |
| **Rollladen** | genau dieser Rollladen bleibt stehen, der Rest des Bereichs fährt weiter |

Die Rollladen-Ebene ist für den Fall gedacht, dass ein Rollladen vorübergehend nicht fahren darf – ein defekter Antrieb, der auf ein Ersatzteil wartet.

Umschalten geht an drei Stellen, alle gleichwertig:

- im **Dashboard** direkt in der Rollladenzeile des Bereichs
- im Tab **Rollläden** in der Liste
- über die Entität `switch.shutter_pilot_rollladen_<name>`, auch aus eigenen Automationen

Der Haken **Automatik aktiv** im Rollladenformular legt den Startwert fest. Ein abgeschalteter Rollladen bekommt im Dashboard zusätzlich ein Symbol, damit man nicht rätselt, warum er stehen bleibt.

Wichtig: Abgeschaltet ist nur die **Automatik**. Von Hand fährt der Rollladen weiter – über die Knöpfe im Dashboard, die Dienste `open_group`/`close_group` und ganz normal über die Cover-Entität. Sonst könnte man ihn nach der Reparatur nicht einmal prüfen.

## Event

Bei jeder automatischen Fahrt wird `shutter_pilot_cover_moved` auf dem Event-Bus gefeuert – ideal für eigene Benachrichtigungen:

```yaml
automation:
  - alias: Melden wenn Rollläden schließen
    trigger:
      - platform: event
        event_type: shutter_pilot_cover_moved
    condition: "{{ trigger.event.data.position < 20 }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            {{ trigger.event.data.entity_id }} auf
            {{ trigger.event.data.position }}% ({{ trigger.event.data.reason }})
```

Enthaltene Felder: `entity_id`, `position`, `tilt_position`, `reason`, `area_id`, `source`.

## Fehlersuche

Bei Problemen hilft der Diagnose-Download: **Einstellungen → Geräte & Dienste → Shutter Pilot → ⋮ → Diagnoseinformationen herunterladen**. Die Datei enthält Konfiguration, Laufzeitstatus und Sonnendaten – Standortkoordinaten werden geschwärzt.

## Unterstützte Sprachen

Das Shutter Pilot Panel passt sich automatisch an die Spracheinstellung deines Home Assistant an:

| Sprache | Code | |
|---------|:----:|---|
| Deutsch | `de` | :de: |
| English (Englisch) | `en` | :gb: |
| Français (Französisch) | `fr` | :fr: |
| Español (Spanisch) | `es` | :es: |
| Italiano (Italienisch) | `it` | :it: |
| Nederlands (Niederländisch) | `nl` | :netherlands: |
| Dansk (Dänisch) | `da` | :denmark: |
| Svenska (Schwedisch) | `sv` | :sweden: |
| Polski (Polnisch) | `pl` | :poland: |
| Português (Portugiesisch) | `pt` | :portugal: |
| Norsk Bokmål (Norwegisch) | `nb` | :norway: |

Wenn deine Sprache nicht aufgeführt ist, wird automatisch Englisch verwendet. Du möchtest eine Übersetzung beitragen? Pull Requests sind willkommen!

## Markisen

Seit 2.12.0 gibt es einen eigenen Tab **Markisen**. Eine Markise ist kein
umgedrehter Rollladen, auch wenn der Fahrweg derselbe ist – zwei Dinge sind
grundlegend anders, und beide sind hier umgesetzt.

### Sie fährt in keinem Zeitplan mit

Uhrzeit, Helligkeit, Sonnenauf- und -untergang bewegen eine Markise nicht.
Ausgefahren wird sie allein von der Beschattung. Die rechnet mit denselben
Regeln wie bei den Rollläden – Sonnenhöhe, Fensterrichtung, bis zu vier
Zusatzbedingungen, Beschattungszeitraum, Haltezeit –, deshalb bekommt die
Markise auch nur *einen* Bereich: den, dessen Sonnenschutz gelten soll.

Sie hat entsprechend nur zwei Positionen:

| Position | Bedeutung | Vorgabe |
| --- | --- | --- |
| Ruhestellung | eingefahren, wenn keine Beschattung nötig ist | 0 % |
| Beschattung | ausgefahren zum Beschatten | 100 % |

Fensterkontakt, Aussperrschutz, Lamellen, abweichende Schließposition,
Frostposition und automatisches Lüften gibt es an einer Markise nicht – das
Formular zeigt sie gar nicht erst.

### Wind-, Regen- und Frostschutz

Der Teil, ohne den eine Markisensteuerung nicht betriebssicher ist.

Unter **Einstellungen** stehen alle drei Sensoren – Wind, Regen und Temperatur
(Frost). Sie gelten für jede Markise im Haus.

Beim **Wind** kann eine einzelne Markise davon abweichen: eigener Sensor (ein
Balkon hinterm Haus sieht anderen Wind als die Terrasse) oder nur eigene
Schwellen (ein kleiner Gelenkarm muss früher rein als eine Kassette am selben
Sensor). **Regen und Frost gibt es nur global** – die fallen über dem ganzen
Haus gleich, und ein zweites Feld dafür wäre nur eine weitere Zeile zum
Übersehen.

Wie es wirkt:

* **Über der Einfahrschwelle** fährt die Markise sofort ein und darf nicht mehr
  ausfahren.
* **Freigegeben** wird sie erst wieder unter der zweiten Schwelle **und** nach
  einer Sperrzeit (Vorgabe 20 min bei Wind, 30 min bei Regen). Eine Bö ist nach
  zwanzig Sekunden vorbei – die Markise soll trotzdem nicht sofort wieder
  heraus. Jede neue Überschreitung startet die Zeit von vorn.
* **Reagiert wird in Sekunden, nicht im Minutentakt:** der Schutz hängt direkt
  an den Sensoren, der Minutentakt ist nur das Sicherheitsnetz.

> ⚠️ **Der Schutz gilt auch bei ausgeschalteten Schaltern.** Hauptschalter aus,
> Bereichsautomatik aus, Markisen-Automatik aus: eingefahren wird trotzdem. Das
> ist eine bewusste Abweichung von der sonst geltenden Rangfolge. Ein Schutz,
> der sich versehentlich abschalten lässt, ist keiner – abschalten geht
> absichtlich, indem der Sensor entfernt wird.

**Toter Sensor:** Meldet der Sensor `unavailable` oder `unknown`, weiß niemand,
was der Wind tut. Ausgefahren wird dann ab der ersten Sekunde nicht mehr. Eine
bereits ausgefahrene Markise wird erst nach einer Karenzzeit (Vorgabe 10 min)
hereingeholt – ein Sensor, der beim Neustart kurz aussetzt, soll nicht das ganze
Haus einfahren. Dieselbe Behandlung bekommt seit 2.21.5 ein Sensor, der zwar
lebt, dessen Zahlenschwelle aber nie eingetragen wurde – auch dort lässt sich
sonst nichts entscheiden, und die Markise darf nicht stillschweigend so
behandelt werden, als wäre alles in Ordnung.

**Invertierte Sensoren.** Meldet der Regen- oder Frostsensor die Gefahr
umgekehrt – ein Kontakt, dessen „aus" eigentlich „nass" heißt, oder ein
Melder, dessen „an" eigentlich „warm" bedeutet –, lässt sich das seit 2.21.5
über die Checkbox **„Bedeutung umkehren"** direkt unter dem Sensorfeld
eintragen. Ohne sie gilt weiterhin die natürliche Lesart: „an" ist Gefahr.

### Ausfahrlänge nach Sonnenhöhe

Optional, Vorgabe aus. Steht die Sonne hoch, reicht wenig Ausfall; sinkt sie,
braucht dieselbe Fläche mehr. Zwei Stützpunkte, gerade Linie dazwischen:

```
Sonne steht hoch bei 60°  →  ausfahren auf  60 %
Sonne steht tief bei 20°  →  ausfahren auf 100 %
```

Dazu eine **Mindeständerung** (Vorgabe 10 %). Ohne die liefe der Antrieb jede
Minute ein paar Prozent – der sicherste Weg, ein Getriebe zu verschleißen.

### Bei Dämmerung einfahren, ohne automatische Wiederausfahrt

Ein eigener Sensor, unabhängig von der Beschattung – dafür seit 2.22.0 im
Formular jeder Markise unter **„Bei Dämmerung einfahren"**. Der Unterschied
ist bewusst: die Beschattung fährt bei Bedarf aus und wieder ein, je nachdem
ob die Bedingung gerade gilt. Dieser Sensor fährt **nur ein** – wird es
morgens wieder hell, bleibt die Markise drin, bis jemand sie von Hand
ausfährt oder die Beschattung (falls eingeschaltet) das übernimmt.

Für einen Helligkeitssensor gilt „dunkler als" ohne eigenes Ankreuzen, genau
wie beim Frost- und Eisschutz – ein Wert unter der ersten Schwelle löst aus,
freigegeben wird erst wieder über der zweiten. Ein Schalter oder
Binärsensor gilt als „an" bedeutet dunkel, mit derselben Checkbox
**„Bedeutung umkehren"** wie beim Wind-, Regen- und Frostschutz, falls der
eigene Sensor es andersherum meldet.

Der Sensor gehört zur einzelnen Markise, nicht zum Bereich – anders als
Regen und Frost, die im ganzen Haus gleich gelten. Er respektiert
Hauptschalter, Bereichsautomatik und die Automatik der Markise selbst
(anders als der Wetterschutz, der bewusst keinen davon fragt): eine
Komfortfunktion soll nicht greifen, wenn jemand die Automatik ausgeschaltet
hat.

### Entitäten, Dienst und Ereignis

| Art | Name |
| --- | --- |
| Binärsensor | `binary_sensor.shutter_pilot_<name>_sperre` – an, solange nicht ausgefahren werden darf. Attribute: Grund und Restzeit |
| Schalter | `switch.shutter_pilot_markise_<name>` – Automatik je Markise (der Schutz gilt trotzdem) |
| Dienst | `shutter_pilot.retract_awnings` – alle Markisen sofort einfahren, ohne Staffelung. Für eine angekündigte Sturmwarnung |
| Ereignis | `shutter_pilot_awning_retracted` mit `entity_id` und `reasons` – für eigene Benachrichtigungen |

### Einen bestehenden Rollladen übernehmen

Wer eine Markise erst als Rollladen angelegt hat: im Markisen-Tab dieselbe
Cover-Entität auswählen, dann erscheint ein Knopf **„Als Markise übernehmen"**.
Fenster-, Lamellen- und Schließ-Einstellungen werden dabei gelöscht statt
stehengelassen, und die beiden Positionen auf die Markisen-Vorgabe gesetzt.

### Antriebe ohne Positionsmeldung

Viele Markisenmotoren kennen nur auf, stop und zu. Shutter Pilot weicht dort
selbstständig auf `cover.open_cover` bzw. `cover.close_cover` aus, und der
Export nennt, welches der beiden Kommandos deine Positionen jeweils ergeben –
„sie fährt verkehrt herum" lässt sich aus den Positionen allein nicht
beantworten, denn welches Kommando „ausfahren" heißt, entscheidet die
Verdrahtung.

Teilpositionen und die Ausfahrlänge nach Sonnenhöhe funktionieren an solchen
Antrieben nur mit einer **„My"-Position** (siehe Rollladen-Einstellungen oben):
die angelernte dritte Stellung ist die einzige Zwischenposition, die so ein
Motor anfahren kann. Ohne sie wird aus jedem Wert ab 50 % „ganz ausfahren" –
das steht einmal als Warnung im Log und im Export.


## Dachfenster

Seit 2.20.0 gibt es einen eigenen Tab **Dachfenster**. Dahinter steckt dieselbe
Maschine wie bei den Markisen – nur zeigt die Gefahr in die andere Richtung:
eine Markise muss **ein**fahren, wenn es bläst, ein Dachfenster muss **zu**,
wenn es regnet.

### Es fährt in keinem Zeitplan mit

Wie die Markise. Uhrzeit, Helligkeit und Sonnenstand bewegen ein Dachfenster
nicht, und Fensterkontakt, Aussperrschutz, Lamellen und Nachholfahrt gibt es
dort nicht – der Cover *ist* das Fenster.

Geöffnet wird es allein über die **Bedingungen** seines Bereichs. Üblich ist
die Innentemperatur: „über 24 °C kippen, unter 22 °C wieder zu". Sonnenhöhe und
Fensterrichtung lassen sich dafür abschalten, dann bleibt eine reine
Bedingungssteuerung. Der Bereichsmodus **Kein Zeitplan** passt dazu.

Drei Stellungen:

| Stellung | Bedeutung | Vorgabe |
| --- | --- | --- |
| Geschlossen | die sichere Stellung – dorthin fährt der Schutz | 0 % |
| Lüftungsstellung | so weit öffnet es, solange die Bedingungen zutreffen | 30 % |
| Ganz offen | nur für den Auf-Knopf von Hand | 100 % |

### Regen-, Wind- und Frostschutz

Dieselben drei Sensoren wie bei den Markisen, unter **Einstellungen**, mit
derselben Mechanik: Binärsensor, Zahlenwert mit Ein- und Ausschaltschwelle oder
Zustandsliste, dazu eine **Sperrzeit** je Sensor. Nach dem letzten Tropfen
bleibt das Fenster also noch die eingestellte Zeit zu, und erst danach öffnet
es wieder – sofern die Bedingung noch gilt.

Ein Regensensor, der **nichts mehr meldet**, sperrt sofort und schließt nach
einer Karenzzeit. An einem Fenster ist das die richtige Richtung: „ich weiß es
nicht" heißt zu.

Für eine Ecowitt-Wetterstation ist die **Regenrate** der richtige Wert
(`sensor.*_rain_rate`, mm/h), nicht die Tagessumme – die rechnet hoch und geht
nach dem Regen nicht mehr herunter.

> ⚠️ **Verlass dich nicht allein darauf.** Zwischen dem ersten Tropfen und dem
> geschlossenen Fenster liegen die Wetterstation, Home Assistant und die
> Laufzeit des Motors. Bei einem plötzlichen Schauer ist Wasser im Raum, bevor
> das Fenster zu ist. Ein Regensensor **am Fenster selbst** – Velux und Roto
> haben so etwas – schließt ohne diese Kette. Shutter Pilot ist der Komfort
> obendrauf, nicht der Ersatz dafür.

## Sonnenschutz nur bei echter Sonne und Wärme

Höhenwinkel und Himmelsrichtung sagen nur, **wo** die Sonne steht – nicht, ob sie tatsächlich scheint oder ob es überhaupt warm genug ist. Im Frühjahr und Herbst ist die Sonnenwärme im Zimmer ja oft erwünscht.

Deshalb lassen sich pro Bereich bis zu **vier Zusatzbedingungen** hinterlegen. Beschattet wird nur, wenn alle erfüllt sind:

| Quelle | Verhalten |
|--------|-----------|
| **Binärsensor oder Schalter** (`binary_sensor`, `input_boolean`, `switch`, `schedule`) | Erfüllt, solange er `on` ist. Keine Schwellen nötig – die Hysterese steckt in deinem Sensor |
| **Zahlensensor** (Lux, Watt/m², °C – auch `input_number`) | Erfüllt ab „Beschatten ab", aufgehoben erst unter „Aufheben unter" |
| **Textzustand** (`weather.*`, `input_select`, Scrape-Sensor) | Erfüllt, wenn der gemeldete Zustand einer der ausgewählten ist. Mehrere sind erlaubt |

Der Abstand zwischen den beiden Schwellen verhindert, dass die Rollläden bei durchziehenden Wolken ständig hin- und herfahren. Lässt du „Aufheben unter" leer, gilt derselbe Wert.

**Helfer gehen genauso.** „Hausmodus" als `input_select` (Zuhause / Abwesend / Urlaub), „Reinigungsdienst" als `input_boolean` – beides steht in der Auswahl und braucht keinen Template-Sensor. Bei einem Auswahl-Helfer bietet das Formular direkt seine hinterlegten Möglichkeiten als Knöpfe an.

Ein leeres Feld bedeutet: keine Bedingung. Ein nicht verfügbarer oder defekter Sensor blockiert die Beschattung nie.

### Wetter und Vorhersage

Hinterlege im Tab **Einstellungen** deine `weather.*`-Entität. Shutter Pilot ruft dann selbst die Tagesvorhersage ab und stellt drei Sensoren bereit:

| Sensor | Inhalt |
|--------|--------|
| Vorhersage Höchsttemperatur | erwarteter Tageshöchstwert, wie die Quelle ihn gerade meldet |
| Vorhersage Tageshöchstwert | der **höchste** Wert, der heute gemeldet wurde |
| Vorhersage Wetterlage | erwartete Wetterlage, z. B. `sunny` |

Alle wählst du ganz normal als Bedingung aus. Typisch: **Vorhersage Höchsttemperatur, beschatten ab 24 °C**. Damit wird an kühlen Tagen nicht beschattet, und die Sonne wärmt das Haus.

**Wann welcher der beiden Temperaturwerte?** Eine Tagesvorhersage wird im Lauf des Tages fortgeschrieben, und die meisten Quellen setzen sie herunter, sobald die Spitze vorbei ist: Um 21 Uhr steht bei „Höchsttemperatur heute" womöglich 25 °C, obwohl es um 15 Uhr 28 °C hatte. Für Entscheidungen am Tag – beschatten – nimm den laufenden Wert. Für Entscheidungen am Abend – abweichendes Schließen, Nachtlüftung – nimm den **Tageshöchstwert**; der steigt bis Mitternacht nur noch.

Ein nicht erreichbares Wetter-Backend blockiert die Beschattung nie – der letzte bekannte Wert bleibt erhalten.

### Sensoren mit Textzustand

Bedingungen können auch **Zustände** vergleichen statt Zahlen. Damit lassen sich eine `weather.*`-Entität oder ein selbstgebauter Scrape-Sensor direkt eintragen: Du wählst einfach die Wetterlagen aus, bei denen beschattet werden soll. Bei Wetter-Entitäten stehen die Standardlagen als Schaltflächen bereit.

### Beschattungszeitraum

Pro Bereich lässt sich einstellen, in welchen Monaten überhaupt beschattet wird – etwa nur April bis September. Zeiträume über den Jahreswechsel sind möglich, z. B. Oktober bis März.

Meist erübrigt sich das durch eine Temperaturbedingung: Wenn die Vorhersage im Winter ohnehin unter der Schwelle bleibt, wird gar nicht erst beschattet.

### Beschattung nur zu bestimmten Uhrzeiten

Elevation, Fensterrichtung, Bedingungen und Beschattungszeitraum beschreiben
alle *die Sonne*. Manchmal geht es aber um den Haushalt: „in den Schulferien
soll das Kinderzimmer bis neun dunkel bleiben".

Dafür gibt es zwei Felder, **beide einzeln optional**:

| Feld | Bedeutung |
| --- | --- |
| Beschattung frühestens ab | vorher wird nicht beschattet |
| Beschattung nur bis | danach wird freigegeben |

„Erst ab 09:00" reicht also für sich, eine obere Grenze braucht es nicht.
Einstellbar **je Bereich und je Rollladen** – leer am Rollladen heißt: der
Bereichswert gilt. Gedacht ist es für das eine Zimmer, das eine andere Regel
braucht.

Zwei Dinge, die man wissen sollte:

* Endet die Beschattung an dieser Grenze, wird **sofort freigegeben**. Die
  Haltezeit gilt dafür nicht – sie ist für durchziehende Wolken da, und eine
  Uhrzeit kommt innerhalb der Haltezeit nicht zurück.
* Ein Fenster **über Mitternacht gibt es nicht**. Steht die zweite Zeit vor der
  ersten, wird die Einstellung verworfen und im Log genannt, statt sie
  stillschweigend als Umschlag zu lesen.

> 💡 Für „der Rollladen soll morgens später **hochfahren**" ist nicht dieses
> Feld zuständig, sondern der **Sondertage-Sensor** des Bereichs – siehe unten.

### Einen Rollladen von der Beschattung ausnehmen

Manchmal soll ein einzelnes Fenster in einem sonst beschatteten Raum nie
mitfahren – der Arbeitsplatz am Nordfenster, die Tür zur Terrasse, das
Aquarium. Dafür gibt es im Rollladenformular den Haken **„An der Beschattung
teilnehmen"** (Vorgabe: an).

Abwählen nimmt **nur die Beschattung** heraus. Zeitplan, Lüften und
Fensterkontakt laufen weiter, und der Rollladen fährt morgens hoch wie alle
anderen. Steht er beim Abwählen gerade auf Beschattungshöhe, wird er
freigegeben statt dort eingefroren.

> 💡 Der **Automatik-Schalter** am Rollladen ist etwas anderes: der hält *jede*
> automatische Fahrt an, auch das Öffnen am Morgen. Er ist für den defekten
> Antrieb gedacht, nicht für „dieses Fenster bitte nicht beschatten".

### Zweite Beschattungsposition

Eine Beschattungsposition ist ein Kompromiss: tief genug gegen die Mittagshitze
heißt an einem milden Tag unnötig dunkel. Deshalb lassen sich **zwei**
hinterlegen.

| Wo | Was |
| --- | --- |
| Bereich | die Bedingung, unter der die zweite gilt |
| Rollladen | die zweite Position selbst |

Dasselbe Paar wie beim abweichenden Schließen. Die Bedingung ist ein ganz
normaler Bedingungs-Slot: ein Schalter, ein Helfer, ein Zeitplan, ein Zahlenwert
mit Hysterese oder eine Zustandsliste. Trifft sie zu, fahren alle Rollläden mit
hinterlegter zweiter Position dorthin – **auch mitten in einer laufenden
Beschattung**, nicht erst beim nächsten Mal. Ohne hinterlegte Position an einem
Rollladen ändert sich für ihn nichts.

Wer es stufenlos braucht, trägt stattdessen eine **Entität** ein: ein
`input_number`, ein Template-Sensor, irgendetwas, das eine Zahl von 0 bis 100
liefert. Die gewinnt über beide festen Positionen. Ist der Wert unlesbar oder
außerhalb 0–100, gilt weiter die eingestellte Position – eine Beschattung, die
wegen eines Templates aussetzt, wäre der schlechtere Ausfall.

### Gar nicht hochfahren – Wochenende, Ferien, Urlaub

Der Sondertage-Sensor unten verschiebt die Uhrzeit. Manchmal soll aber
**überhaupt nicht** geöffnet werden. Dafür gibt es zwei Wege je Bereich, beide
im Abschnitt „Hochfahren unterbinden":

| Einstellung | Wofür |
| --- | --- |
| Am Wochenende gar nicht hochfahren | ausschlafen statt später aufstehen |
| Bedingung „nicht hochfahren" | Ferien, Urlaub, Feiertag, Homeoffice – was immer ein Helfer weiß |

**Beide betreffen nur das Hochfahren.** Runterfahren und Beschattung laufen
weiter – sonst stünde das Haus abends offen zur Straße.

Der Wochenend-Haken hängt am selben Wochenendbegriff wie alles andere in
Shutter Pilot: **ist ein Sondertage-Sensor eingetragen, entscheidet der.**
Damit gilt der Haken automatisch auch für Feiertage, Ferien und Schichtdienst.

> 💡 **Nur sonntags ausschlafen, samstags nicht?** Einen Workday-Sensor mit
> `excludes: [sun]` anlegen und als Sondertage-Sensor eintragen. Dann ist
> Sonnabend ein Arbeitstag – es gelten die Wochentagszeiten –, und nur am
> Sonntag greift die Wochenendregel.

Die Bedingung nimmt alles, was die anderen Bedingungsfelder auch nehmen: einen
`input_boolean` (Urlaubsschalter), einen `schedule`-Helfer, eine Auswahlliste
oder einen Zahlenwert mit Hysterese. Solange sie zutrifft, bleibt der Rollladen
morgens unten. **Ein nicht lesbarer Sensor blockiert nicht** – andersherum
bliebe jeder Rollladen unten, bis es jemand merkt, und aus dem Zimmer heraus
kommt man daran nicht vorbei.

### Später hochfahren an Ferien- und Feiertagen

Der **Sondertage-Sensor** je Bereich (früher „Workday-Sensor") schaltet zwischen
Wochentags- und Wochenend-Zeitplan um. Er wirkt in **allen drei Modi** – Zeit,
Helligkeit und Sonnenstand.

Damit lassen sich Feiertage, Urlaub, Schichtdienst **und Schulferien**
abbilden. Das Rezept für Ferien:

1. Einen Binärsensor bauen, der `on` meldet, solange Schule ist – und `off` an
   Ferien- **und** Wochenendtagen
2. Ihn als Sondertage-Sensor des Bereichs eintragen
3. „Hoch Wochenende" auf `09:00` stellen, **„Runter Wochenende" leer lassen**
   (leere Wochenendwerte fallen auf die Wochentagswerte zurück)

Dann bleibt der Rollladen in den Ferien bis neun unten und fährt abends
unverändert zu.

Soll das nur für **ein einzelnes Zimmer** gelten: dem Rollladen einen eigenen
**Hoch-Bereich** geben und den gemeinsamen Runter-Bereich behalten. Hoch- und
Runter-Bereich dürfen verschieden sein. Die Beschattung ändert sich dadurch
nicht – die entscheidet der Runter-Bereich.

### Beschattung ein- und ausschalten, ohne die Automatik anzufassen

Jeder Bereich mit eingeschaltetem Sonnenschutz bekommt einen eigenen Schalter
`switch.shutter_pilot_sonnenschutz_<Bereich>` – und einen Schalter auf der
Dashboard-Karte gleich neben der Statuszeile.

Er ist bewusst **getrennt** vom Automatik-Schalter des Bereichs: 35 °C heute
und 20 °C morgen ist ein Grund, die Beschattung zu lassen. Es ist kein Grund,
die Rollläden morgens unten zu lassen. Bisher blieb dafür nur der
Beschattungszeitraum in Monaten – für einen Wetterumschwung viel zu grob.

**Ausschalten gibt frei, was gerade beschattet ist**: die betroffenen Rollläden
fahren auf. Sie stehenzulassen wäre die schlechtere Hälfte – wer wegen kühlerem
Wetter abschaltet, will nicht bis zum Abend auf halber Höhe sitzen.

### Zwei Haken zum Verhalten der Beschattung

Beide stehen im Sonnenschutz-Block des Bereichs, beide sind **standardmäßig
aus**, weil sie das Fahrverhalten ändern.

**Am Ende des Beschattungstags wieder öffnen.** Sinkt die Sonne unter den
eingestellten Bereich, bleibt der Rollladen sonst auf Beschattungshöhe stehen,
bis der Abendplan ihn schließt. Im Sonnenmodus sind das Minuten – im
Helligkeits- und Zeitmodus können es Stunden sein, und dann sitzt man den
ganzen Nachmittag hinter halb geschlossenen Rollläden. Angehakt fährt er
stattdessen sofort auf.

**Nur beschatten, was schon offen ist.** Beschatten und Öffnen ist derselbe
Fahrbefehl mit einer anderen Zahl – ein nachts geschlossener Rollladen wird von
der Beschattung deshalb *hochgefahren*, auf die Beschattungshöhe. Wer das nicht
will, hakt es an: dann bleibt er unten, bis er regulär geöffnet hat.

### Sensoren pro Fenster statt pro Bereich

Bedingungen lassen sich sowohl im **Bereich** als auch am **einzelnen Rollladen** hinterlegen. Die Regel ist einfach:

> Der Bereich liefert den Standard. Was am Rollladen gesetzt ist, gilt für dieses Fenster.

Der Rückfall wirkt **je Bedingung**, nicht alles oder nichts. Typischer Aufbau:

- **Bereich:** Bedingung 1 = Vorhersage Höchsttemperatur ab 24 °C. Gilt für alle Fenster.
- **Südfenster:** Bedingung 2 = Helligkeitssensor am Südfenster.
- **Westfenster:** Bedingung 2 = Helligkeitssensor am Westfenster.

Beide Fenster erben die Temperaturbedingung und haben trotzdem ihren eigenen Helligkeitssensor. Genauso lässt sich eine Raumtemperatur pro Rollladen hinterlegen.

Bei einer **Textbedingung** – etwa der Wetterlage – bietet das Formular die Zustände als Knöpfe an. Bei einer `weather.*`-Entität sind das die 15 Standardlagen von Home Assistant. Ein gewöhnlicher Sensor meldet dagegen immer nur seinen *aktuellen* Zustand; dort lassen sich die übrigen darum von Hand eintragen, statt auf den nächsten Regen zu warten.

Jedes Fenster führt seine Hysterese getrennt – eine Wolke vor dem einen Fenster hebt die Beschattung des anderen nicht auf.

## Nach Sonnenstand fahren, aber nicht zu früh

Im Sonnenmodus lässt sich der berechnete Zeitpunkt in ein Uhrzeitfenster klemmen:

| Einstellung | Wirkung |
|---|---|
| Hoch frühestens 07:30 | Im Sommer geht die Sonne um 5 Uhr auf – gefahren wird trotzdem erst um 7:30 |
| Hoch spätestens 09:00 | Im Winter wird es erst spät hell – spätestens um 9 Uhr geht der Rollladen hoch |

Für das Wochenende gibt es eigene Werte. Bleiben die leer, gelten die Wochentagswerte. Leere Felder bedeuten generell: keine Grenze.

Alle Uhrzeiten sind Ortszeit – die Zeitzone aus den Home-Assistant-Einstellungen. Im Dashboard steht neben der Fahrzeit, warum sie von der Sonnenzeit abweicht: „· frühestens 07:30", wenn die Klammer greift, oder „· Präsenz: +4 min" bei aktiver Präsenzsimulation.

## Mindestabstand zwischen Fahrbefehlen

Funk-Empfänger – 433 MHz, HmIP und Verwandte – verschlucken Befehle, die im selben Moment ankommen. Die **Verzögerung im Bereich** hilft dagegen nur teilweise: Sie staffelt die Rollläden *eines* Bereichs, aber jeder Bereich fährt in einem eigenen Vorgang. Fahren abends zwei Bereiche gleichzeitig los, treffen die Befehle trotzdem zusammen.

Im Tab **Einstellungen** gibt es deshalb einen **Mindestabstand zwischen Fahrbefehlen** (0–10 s). Er wirkt an der einen Stelle, durch die *jede* Fahrt läuft – automatisch wie von Hand – und staffelt sie über alle Bereiche hinweg. Gedrosselt heißt dabei gewartet, nicht weggelassen: Jeder Rollladen bekommt seinen Befehl, nur eben nacheinander.

`0` schaltet die Drosselung ab; das ist das Verhalten vor Version 2.7.0.

## Fahrten überprüfen

Funk-Rollläden verlieren gelegentlich einen Befehl. Ohne Kontrolle merkt das niemand, und die Integration rechnet danach mit einer Position weiter, die der Rollladen nie erreicht hat.

Im Tab **Einstellungen** lässt sich deshalb die Überprüfung aktivieren. Nach jeder automatischen Fahrt wird nach einer einstellbaren Wartezeit geprüft, ob die Position innerhalb der Toleranz erreicht wurde, und der Befehl sonst wiederholt.

Schlägt es endgültig fehl, wird der gespeicherte Wert korrigiert und das Ereignis `shutter_pilot_cover_failed` gefeuert – mit `entity_id`, `requested`, `actual` und `reason`. Damit lässt sich eine Benachrichtigung bauen:

```yaml
automation:
  - alias: Rollladen reagiert nicht
    trigger:
      - platform: event
        event_type: shutter_pilot_cover_failed
    action:
      - service: notify.mobile_app
        data:
          message: >
            {{ trigger.event.data.entity_id }} steht auf
            {{ trigger.event.data.actual }}% statt
            {{ trigger.event.data.requested }}%
```

Rollläden, die nur auf und zu kennen und keine Position melden, werden automatisch übersprungen.

## Räume mit Fenstern in mehreren Himmelsrichtungen

Höhenwinkel und Himmelsrichtung gelten normalerweise für den ganzen Bereich. Zeigt ein Fenster in eine andere Richtung als die übrigen im selben Raum, aktivierst du beim betreffenden Rollladen **Eigene Ausrichtung** und stellst dort Höhenwinkel und Azimut ein.

So werden Süd- und Westfenster desselben Raums zu unterschiedlichen Tageszeiten beschattet, ohne dass du zwei Bereiche mit doppeltem Zeitplan pflegen musst.

## Abends nur teilweise schließen

Sollen bestimmte Rollläden an heißen Abenden nicht ganz zufahren, um weiter zu lüften:

1. Im **Bereich** unter *Abweichendes Schliessen* eine Bedingung hinterlegen – naheliegend ist der Sensor **Vorhersage Tageshöchstwert**, den Shutter Pilot selbst bereitstellt
2. Optional eine **zweite Bedingung** – beide müssen dann zutreffen. Typisch: „der Tag war warm“ **und** „jemand ist zu Hause“
3. Bei den betreffenden **Rollläden** eine Teilposition setzen, z. B. 50 %

Nur Rollläden mit gesetzter Teilposition weichen ab, alle anderen schließen normal. Ein toter Sensor gilt hier als *nicht erfüllt* – dann wird normal geschlossen, statt jeden Rollladen die Nacht über halb offen stehen zu lassen.

## Einstellungen von einem anderen Rollladen übernehmen

Wer zehn Fenster gleich konfigurieren will, muss nicht zehnmal dasselbe tippen. Im Rollladenformular steht unter dem Namen eine Auswahl **Einstellungen übernehmen von** – Vorlage wählen, **Übernehmen** klicken, fertig.

Kopiert werden Positionen, Lamellenwinkel, Beschattung mit Geometrie und Bedingungen, Frost- und Lüftungswerte sowie die Fenster-Einstellungen.

Bewusst **nicht** kopiert wird, was einen Rollladen ausmacht:

- Cover-Entität und Name
- Bereich für Hoch und Runter
- Fenster- und Kippsensor

Genau diese Felder unterscheiden zwei sonst gleiche Rollläden – würden sie mitkopiert, hätte man hinterher zweimal dasselbe Fenster.

## Helligkeitsmodus mit Sonnengrenze

Ein Gewitter am Nachmittag drückt die Helligkeit unter die Schwelle – und die Rollläden schließen am helllichten Tag. Uhrzeitfenster helfen dagegen nur begrenzt, denn der Sonnenuntergang wandert übers Jahr um Stunden.

Im Helligkeitsmodus gibt es deshalb zwei zusätzliche Grenzen:

| Einstellung | Wirkung |
|---|---|
| Runter frühestens X Min. vor Sonnenuntergang | Vor dieser Zeit wird nicht geschlossen, egal wie dunkel es wird |
| Hoch frühestens X Min. vor Sonnenaufgang | Vor dieser Zeit wird nicht geöffnet |

Beispiel: Sonnenuntergang 21:10 und „60" bedeutet, dass frühestens ab 20:10 geschlossen wird. Beide Grenzen gelten **zusätzlich** zu den Uhrzeitfenstern – die engere gewinnt.

Leer heißt: keine Grenze. Der Wert `0` ist etwas anderes als leer – er bedeutet „genau ab Sonnenuntergang".

## Feste Zeit, wenn die Lux-Schwelle nie erreicht wird

In der dunklen Jahreszeit bleibt es tagelang trüb, und die Hoch-Schwelle wird nie überschritten. Die Uhrzeitfenster helfen nicht: Sie **erlauben** eine Fahrt nur, sie lösen keine aus.

Dafür gibt es je Bereich zwei abschaltbare Fristen:

| Einstellung | Wirkung |
|---|---|
| Spätestens hochfahren um | Zu dieser Uhrzeit wird geöffnet, unabhängig vom Helligkeitswert |
| Spätestens runterfahren um | Zu dieser Uhrzeit wird geschlossen, unabhängig vom Helligkeitswert |

Beide sind **standardmäßig aus** – eingeschaltet fahren sie einmal am Tag, auch außerhalb der Zeitfenster. Für das Wochenende gibt es je einen eigenen Wert; bleibt er leer, gilt der Wert der Woche.

Was die Frist **nicht** tut: einen Rollladen bewegen, der bereits in diese Richtung gefahren ist. Wurde morgens per Lux geöffnet, passiert um 09:00 nichts mehr. Beschattung und eine manuelle Position haben weiterhin Vorrang, und nach einem Neustart wird eine bereits vergangene Frist nicht nachgeholt.

## Ständiges Hoch und Runter bei Wolken

Gegen Rauschen am Sensor ist vorgesorgt: getrennte Schwellen für Ein und Aus, eine Hysterese je Bedingung, und pro Phase wird nur einmal in dieselbe Richtung gefahren. Eine durchziehende Wolke ist aber kein Rauschen – sie beendet die Bedingung wirklich, und der Rollladen fuhr sofort auf.

Dafür gibt es im Bereich **Beschattung halten** (0–120 Minuten). So lange bleibt die Beschattung stehen, auch wenn die Bedingung nicht mehr gilt. Kommt die Sonne vorher zurück, beginnt die Zeit beim nächsten Mal von vorn.

Zwei Dinge bleiben bewusst sofort:

- **Das Beschatten selbst.** Wenn die Sonne aufs Fenster trifft, soll der Rollladen nicht erst eine Stunde warten.
- **Das Ende des Tages.** Sinkt die Sonne unter den eingestellten Höhenwinkel, ist die Beschattung vorbei – dann übernimmt der normale Abendplan ohne Verzögerung.

`0` behält das bisherige Verhalten.

## Beschattung allein über Helligkeitssensoren

Wer rund ums Haus Helligkeitssensoren verteilt hat, braucht Höhenwinkel und Himmelsrichtung nicht – der Sensor weiß bereits, ob die Sonne aufs Fenster scheint. Dafür ist keine eigene Betriebsart nötig:

1. Im **Bereich** den Sonnenschutz aktivieren
2. **Himmelsrichtung ausschalten** (Haken raus) – dann wird der Azimut nicht geprüft
3. **„Sonnenhöhe prüfen" ausschalten** (Haken raus) – dann spielt der Höhenwinkel keine Rolle mehr
4. Den Helligkeitssensor als **Zusatzbedingung** eintragen, mit Ein- und Ausschaltschwelle

Damit entscheidet allein die Helligkeit. Die zwei Schwellen sind hier wichtiger als sonst: Sie verhindern, dass eine durchziehende Wolke die Beschattung sofort wieder aufhebt.

Weil die Bedingungen **pro Rollladen** überschrieben werden können, bekommt jedes Fenster seinen eigenen Sensor, während der Rest der Einstellungen im Bereich stehen bleibt.

## Automatisch lüften

Lüften war bisher nur von Hand möglich – über den Knopf im Dashboard oder den Dienst. Im **Bereich** lässt sich unter *Automatisches Lüften* jetzt festlegen, wann es von selbst passieren soll:

1. **Automatisch lüften** aktivieren
2. Bis zu zwei Bedingungen angeben, die **beide** erfüllt sein müssen – etwa ein Anwesenheitssensor auf „an" und eine Raumtemperatur über 24 °C

Sind alle Bedingungen erfüllt, fahren die Rollläden des Bereichs auf ihre **Lüftungsposition** (dieselbe wie bei gekipptem Fenster). Fällt eine Bedingung weg, fahren sie dorthin zurück, wo sie vorher standen – nicht auf „offen", was nachts falsch wäre.

Die Rangfolge, falls mehreres zugleich zutrifft:

| Vorrang | Grund |
|---|---|
| 1. Fensterkontakt | reagiert darauf, was jemand tatsächlich am Fenster getan hat |
| 2. Beschattung | Hitze geht vor |
| 3. Automatisches Lüften | fährt nur Rollläden an, die sonst stillstehen |

Ohne eingetragene Bedingung passiert nichts. Hauptschalter, Bereichs- und Rollladenautomatik gelten wie überall; wird der Bereich abgeschaltet, während gelüftet wird, fährt der Rollladen noch zurück, statt halb offen stehen zu bleiben.

## Frostschutz

Bei Frost kann ein ganz geschlossener Rollladen am Rahmen festfrieren. Damit das nicht passiert, bleibt ein Spalt offen:

1. Im **Bereich** unter *Frostschutz* eine Bedingung hinterlegen – naheliegend ist der Sensor **Vorhersage Tiefsttemperatur**, den Shutter Pilot selbst bereitstellt, sobald eine Wetter-Entität eingetragen ist
2. Bei den betreffenden **Rollläden** eine Frostposition setzen, z. B. 10 %

Anders als bei allen übrigen Bedingungen wird hier **nach unten** verglichen: Der Frostschutz greift *unter* dem ersten Wert und bleibt aktiv, bis der zweite überschritten ist. Die Hysterese verhindert, dass er um den Gefrierpunkt herum ständig ein- und ausschaltet.

Frostschutz gewinnt gegen das abweichende Schließen – Schutz geht vor Komfort. Beides wirkt im Zeit-, Sonnen- und Helligkeitsmodus. Ein Rollladen ohne gesetzte Frostposition schließt unverändert ganz, selbst wenn die Bedingung des Bereichs erfüllt ist.

## Geplant

Wünsche, die nachvollziehbar sind, aber (noch) keinen Code haben – gebündelt
hier statt verstreut über Issues und Forum, damit sie nicht zwischen echten
Fehlermeldungen untergehen. Ein 👍 auf dem verlinkten Issue hilft bei der
Priorisierung mehr als ein neuer Kommentar.

- **Fahrzeit-Simulation für Antriebe ohne Positionsrückmeldung** (z. B.
  Jarolift-Controller): statt nur `open_cover`/`close_cover` als Rückfall
  eine Zwischenposition über die konfigurierte Fahrzeit annähern.
  [#11](https://github.com/fschubi/shutter_pilot/issues/11)

## Unterstützt mich

Shutter Pilot entsteht in meiner Freizeit und ist und bleibt kostenlos und quelloffen. Wenn dir die Integration den Alltag erleichtert und du dich erkenntlich zeigen möchtest, freue ich mich über einen Kaffee:

<a href="https://paypal.me/fschubi">
  <img src="https://img.shields.io/badge/PayPal-Spenden-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Über PayPal spenden" />
</a>

Genauso hilfreich und völlig kostenlos: einen ⭐ hierlassen, einen [Fehler melden](https://github.com/fschubi/shutter_pilot/issues) oder eine Übersetzung beisteuern.

## Mindestanforderungen

- Home Assistant **2024.6.0** oder neuer

## Lizenz

MIT – siehe die [LICENSE](LICENSE) Datei für Details.
