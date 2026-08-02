# Changelog

Alle wichtigen Änderungen an Shutter Pilot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [2.5.1]

### Geändert
- **Automatik pro Rollladen direkt im Panel schaltbar.** Bisher ging das nur über die Entität. Jetzt sitzt der Schalter dort, wo man ihn sucht: im **Dashboard** in der Rollladenzeile des Bereichs und im Tab **Rollläden** in der Liste – genau wie der Automatik-Schalter am Bereich. Der Haken im Rollladenformular bleibt als Startwert erhalten.
- **Eindeutigere Namen für die Rollladen-Schalter.** Sie hiessen `switch.shutter_pilot_auto_<name>` – dasselbe Muster wie die Bereichsschalter. Trugen ein Bereich und ein Rollladen denselben Namen (Wohnzimmer ist beides), standen zwei gleich benannte Schalter in der Liste und Home Assistant hängte an einen davon ein `_2`. Die Rollladen-Schalter heissen jetzt **Shutter Pilot Rollladen &lt;Name&gt;** und nutzen das Namensfeld aus dem Rollladenformular. Bei Installationen, die bereits 2.5.0 hatten, ändert sich nur der Anzeigename; die Entitäts-ID bleibt, wie Home Assistant sie angelegt hat.

## [2.5.0]

Aus dem Feld-Feedback von Linos aus dem Forum.

### Neu
- **Automatik pro Rollladen abschaltbar.** Bisher ließ sich die Automatik nur global oder für einen ganzen Bereich anhalten. Jetzt gibt es eine dritte Ebene: Der Haken **Automatik aktiv** im Rollladenformular nimmt genau einen Rollladen aus allen automatischen Fahrten – Zeit, Helligkeit, Sonnenstand und Fensterkontakt. Gedacht für einen defekten Antrieb, der auf ein Ersatzteil wartet: Der Rollladen bleibt stehen, seine Einstellungen bleiben erhalten, und der Rest des Bereichs fährt weiter. Von Hand fährt er unverändert – über die Knöpfe im Dashboard, die Dienste und die Cover-Entität. Je Rollladen entsteht dafür ein Schalter `switch.shutter_pilot_auto_<rollladen>`, der sich auch in eigenen Automationen verwenden lässt. Im Dashboard kennzeichnet ein Symbol die abgeschalteten Rollläden.

## [2.4.2]

### Geändert
- **Konfiguration nur noch für Administratoren.** Aus dem Review zur Aufnahme in HACS (danke, @frenck): Die schreibenden WebSocket-Befehle prüften keine Rechte. Jeder angemeldete Benutzer ohne Administratorrechte konnte damit Bereiche und Rollläden umkonfigurieren sowie den Hauptschalter und die Automatik pro Bereich umlegen. Alle ändernden Befehle – Bereiche und Rollläden speichern und löschen, Einstellungen speichern, Hauptschalter, Automatik pro Bereich – verlangen jetzt Administratorrechte. Der lesende Statusbefehl bleibt unverändert.
- **Panel passt sich den Rechten an.** Es bleibt für alle Benutzer in der Seitenleiste, denn es ist zugleich die Bedienoberfläche für die Rollläden. Ohne Administratorrechte erscheint nur das Dashboard mit den Bedienknöpfen; die Tabs für Bereiche, Rollläden und Einstellungen sowie Hauptschalter und Automatik-Schalter sind ausgeblendet. Die Bedienung selbst läuft über die normalen `cover`-Dienste, für die Home Assistant die Rechte ohnehin selbst prüft.

## [2.4.1]

### Neu
- **Menü-Knopf auf dem Handy.** Auf schmalen Bildschirmen blendet Home Assistant die Seitenleiste aus – aus dem Panel kam man dann nur noch über den Zurück-Knopf des Browsers heraus. Links neben dem Titel steht jetzt das gewohnte Menü-Symbol, das die Seitenleiste aufklappt.

### Behoben
- **Hauptschalter startete nach einer Neuinstallation ausgeschaltet.** Home Assistant merkt sich den Zustand eines Schalters über die Entitäts-ID, nicht über die Integration. Wer Shutter Pilot entfernt und neu hinzufügt, bekam wieder dieselbe Entitäts-ID – und erbte damit ein „aus" aus der alten Installation. Der Schalter merkt sich jetzt, zu welcher Installation ein Zustand gehört, und startet bei einer neuen eingeschaltet. Ein bewusst ausgeschalteter Schalter aus einer älteren Version bleibt beim Update unverändert.
- **Hauptschalter startete ausgeschaltet, wenn die Entität beim letzten Beenden nicht bereit war.** `unavailable` und `unknown` wurden als „aus" gewertet. Beides gilt jetzt als „an", denn es ist keine Entscheidung des Nutzers.
- **Panel konnte weiß bleiben.** Das Panel holt sich seine Basisklasse aus einem bereits geladenen Element des Home-Assistant-Frontends. War keins der beiden bisher geprüften Elemente vorhanden, brach das Panel wortlos ab. Jetzt werden zehn Elemente geprüft, Mixins in der Vererbungskette übersprungen, und wenn wirklich nichts passt, erscheint eine Meldung mit Hinweis statt einer weißen Seite. Fehler beim Aufbau der Ansicht werden ebenfalls angezeigt, statt sie leer zu lassen.

## [2.4.0]

Umsetzung der Architekturdiskussion aus dem Forum.

### Neu
- **Bedingungen pro Rollladen, mit Rückfall auf den Bereich.** Jeder Rollladen kann eigene Bedingungen bekommen – etwa einen Helligkeitssensor direkt am Fenster oder die Temperatur des jeweiligen Raums. Bleibt ein Feld leer, gilt weiterhin der Wert des Bereichs. Der Rückfall wirkt **je Bedingung**: Man kann den Sensor pro Fenster setzen und die Wetterbedingung trotzdem einmal zentral im Bereich pflegen. Damit steht der Standard im Bereich und nur die Ausnahme am Fenster.
- **Früheste und späteste Uhrzeit im Sonnenmodus.** Der aus dem Sonnenstand berechnete Zeitpunkt lässt sich in ein Uhrzeitfenster klemmen: „nach Sonnenstand fahren, aber frühestens 7:30 und spätestens 9:00". Mit eigenen Wochenendwerten, die wie gewohnt auf die Wochentagswerte zurückfallen, wenn sie leer bleiben. Wirkt auch auf den Sensor „nächste Fahrt".
- **Fahrten werden überprüft.** Optional prüft Shutter Pilot nach jeder automatischen Fahrt, ob die Position tatsächlich erreicht wurde, und wiederholt den Befehl sonst. Einzustellen im Tab **Einstellungen** mit Wartezeit, erlaubter Abweichung und Anzahl der Wiederholungen. Rollläden, die keine Position melden, werden übersprungen.

### Behoben
- **Gescheiterte Fahrten wurden als erfolgreich gespeichert.** Nach dem Befehl wurde die Zielposition als Tatsache abgelegt. Bei Funk-Rollläden geht gelegentlich ein Befehl verloren, und die Integration rechnete danach dauerhaft mit einer nie erreichten Position weiter – etwa beim Überspringen eines automatischen Hochfahrens. Bei aktiver Überprüfung wird der gespeicherte Wert jetzt korrigiert und das Ereignis `shutter_pilot_cover_failed` gefeuert.
- **Hysterese wurde zwischen Rollläden geteilt.** Der Hysterese-Zustand hing am Bereich. Mit Bedingungen pro Fenster hätte eine Wolke vor dem einen Fenster die Beschattung des anderen aufgehoben. Der Zustand wird jetzt pro Rollladen geführt.
- `get_sun_condition_status` entpackte drei Werte aus einem Vierer-Tupel und wäre beim ersten Aufruf abgestürzt.

## [2.3.0]

Umsetzung der Rückmeldungen aus dem zweiten Forum.

### Neu
- **Wetter und Vorhersage direkt in der Integration.** Im neuen Tab **Einstellungen** lässt sich eine `weather.*`-Entität hinterlegen. Shutter Pilot ruft dann selbst die Tagesvorhersage ab und stellt zwei Sensoren bereit: **Vorhersage Höchsttemperatur** und **Vorhersage Wetterlage**. Beide sind ganz normal als Bedingung auswählbar – der Template-Sensor aus der README ist damit nicht mehr nötig. Seit Home Assistant 2024.4 liegen Vorhersagen nicht mehr in Attributen, sondern nur noch hinter dem Dienst `weather.get_forecasts`.
- **Bedingungen können Zustände vergleichen.** Bisher wurden nur Zahlen und Binärsensoren ausgewertet. Jetzt lässt sich auch auf Textzustände prüfen – etwa `sunny` oder `bewölkt`. Damit funktionieren Wetter-Entitäten und selbstgebaute Scrape-Sensoren direkt als Bedingung. Bei Wetter-Entitäten werden die Standardlagen als Schaltflächen angeboten statt sie abtippen zu müssen.
- **Vier Bedingungen statt zwei.** Bedingung 3 und 4 erscheinen erst, wenn die vorherige gefüllt ist.
- **Beschattungszeitraum pro Bereich.** „Nur von April bis September" – Zeiträume über den Jahreswechsel sind möglich, z. B. Oktober bis März. Damit bleibt die Wintersonne draußen aus der Beschattung und drinnen als Wärme.
- **Eigene Ausrichtung pro Rollladen.** Für Räume mit Fenstern in mehreren Himmelsrichtungen lassen sich Höhenwinkel und Azimut jetzt am einzelnen Rollladen überschreiben. Süd- und Westfenster desselben Raums werden dadurch zu unterschiedlichen Tageszeiten beschattet. Ohne diesen Schalter gelten unverändert die Werte des Bereichs.
- **Abweichende Schließposition.** Der Bereich legt über eine Bedingung fest *wann*, der einzelne Rollladen über eine Teilposition *wie weit*. So schließen an heißen Abenden nur ausgewählte Rollläden teilweise, um weiter zu lüften.

### Behoben
- **Sensoren mit Textzustand wurden stillschweigend ignoriert.** `float()` schlug fehl, die Bedingung galt als erfüllt, und es gab keinerlei Hinweis – der Sensor sah konfiguriert aus und tat nichts. Ohne hinterlegte Zustandsliste erscheint jetzt eine Warnung im Log.

### Hinweis
Ein fehlendes, nicht erreichbares oder fehlerhaft antwortendes Wetter-Backend blockiert die Beschattung nie. Der letzte bekannte Wert bleibt erhalten, gewarnt wird nur einmal.

## [2.2.1]

### Geändert
- **Entitätsauswahl klappt jetzt zu.** In 2.2.0 stand die Trefferliste dauerhaft offen und belegte pro Feld rund sieben Zeilen – bei mehreren Auswahlfeldern in einem Formular wurde das schnell unübersichtlich. Jetzt ist nur eine Zeile sichtbar. Ein Klick darauf klappt die Suche auf, der Cursor springt direkt ins Suchfeld, und nach der Auswahl klappt alles wieder zu. Schliessen geht auch mit `Esc` oder über den Pfeil. Es ist immer höchstens eine Auswahl gleichzeitig offen.
- **Formulare in Abschnitte gegliedert.** Bereichs- und Rollladen-Formular liefen bisher als eine lange Feldliste durch, ohne erkennbare Grenzen zwischen den Themen. Beide haben jetzt Überschriften mit Symbol und Trennlinie:
  - Bereich: Grunddaten · Zeitplan · Kalender & manuelle Bedienung · Sonnenschutz · Licht
  - Rollladen: Rollladen · Bereiche · Positionen · Fenster & Lüftung · Lamellen
- **Zeitplan steht jetzt direkt hinter der Modusauswahl.** Vorher standen die Zeitfelder ganz am Ende des Formulars, weit weg von der Einstellung, zu der sie gehören.

## [2.2.0]

Dieses Release setzt die Rückmeldungen aus dem Forum um.

### Neu
- **Entitätsauswahl komplett überarbeitet.** Statt einer Auswahlliste mit sämtlichen Entitäten einer Domain gibt es jetzt ein Suchfeld mit Trefferliste. Sortiert wird nach **Anzeigename** statt nach Entity-ID – ein Sensor namens „Flur Sensor" mit der ID `sensor.0x00158d0001abcdef` steht jetzt unter F und nicht mehr unter 0. Passende Entitäten stehen oben unter „Passende", alle übrigen bleiben darunter erreichbar. Die Vorauswahl nutzt `device_class` **und** den Namen, damit auch Sensoren ohne gesetzte `device_class` gefunden werden.
- **Zweiter Fenstersensor pro Rollladen** für Hardware, die „offen" und „gekippt" als zwei getrennte Entitäten meldet. Der Kipp-Kontakt hat Vorrang, weil viele Fenster im Kippzustand zusätzlich „offen" melden. Ohne zweiten Sensor bleibt alles wie bisher.
- **Lüftungsposition ist jetzt direkt ansteuerbar** – bisher war sie nur über einen Fensterkontakt erreichbar. Neu: Service `shutter_pilot.ventilate_group` und ein Knopf **Lüften** auf jeder Bereichskarte. Es wird dieselbe Position genutzt wie bei gekipptem Fenster, es gibt also kein zusätzliches Feld zum Ausfüllen.
- **Zusatzbedingungen für den Sonnenschutz.** Pro Bereich lassen sich bis zu zwei Bedingungen hinterlegen, die zusätzlich zu Höhenwinkel und Himmelsrichtung erfüllt sein müssen:
  - Ein **Binärsensor** (z. B. „hohe Sonneneinstrahlung") wirkt direkt – die Hysterese steckt dann im Sensor selbst.
  - Ein **Zahlensensor** bekommt eine Schwelle „Beschatten ab" und optional „Aufheben unter". Der Abstand zwischen beiden verhindert, dass die Rollläden bei durchziehenden Wolken hin- und herfahren.

  Damit lässt sich beides abbilden: nur beschatten, wenn wirklich die Sonne knallt, und nur, wenn es warm genug ist. Im Frühjahr und Herbst bleibt die Sonnenwärme so erwünschterweise drin. Ein fehlender, unbekannter oder nicht verfügbarer Sensor blockiert die Beschattung nie.

### Geändert
- Die Sonnenschutz-Freigabe berücksichtigt die neuen Bedingungen: Fällt eine Bedingung weg, während Sonnenstand und Richtung noch passen, fahren die Rollläden wieder hoch.
- Das Panel nutzt jetzt auf allen Plattformen dieselbe Entitätsauswahl. Der Sonderfall für die macOS-App entfällt damit an dieser Stelle.

### Hinweis zur Wettervorhersage
Eine eigene Vorhersage-Auswertung ist bewusst nicht eingebaut. Wer nach der Tageshöchsttemperatur beschatten will, legt einen Template-Sensor mit dem Vorhersagewert an und trägt diesen als Bedingung ein – siehe README.

### Tests
143 statt 107 Tests. Neu abgedeckt: Fensterzustand mit zwei Sensoren, Bedingungen mit Hysterese, `ventilate_group`. Die Sortier- und Vorfilterlogik des Panels ist zusätzlich mit einem eigenständigen Node-Skript geprüft.

## [2.1.4]

### Behoben
- **In der Home-Assistant-App für macOS liessen sich Auswahlfelder nicht bedienen.** Die Pfeile waren sichtbar, aber ein Klick öffnete nichts. In Mac Catalyst sind native Formular-Popups im WebView defekt – das betraf sowohl die in 2.1.3 eingeführten Stunden-/Minuten-Felder als auch die Entitätsauswahl (Workday-Sensor, Helligkeitssensor, Lampe, Cover).
- **Zeitfelder in der macOS-App**: eigenes Steuerelement mit `−`/`+`-Schaltflächen für Stunde und Minute, mit Überlauf (23 → 00) und weiterhin direkter Eingabemöglichkeit.
- **Entitätsauswahl in der macOS-App**: Suchfeld mit anklickbarer Ergebnisliste statt Dropdown.
- Beides nutzt ausschliesslich `<button>` und `<input type="text">`, also Elemente, die in dieser Umgebung nachweislich funktionieren. Auf iPhone, iPad, Android und in allen Browsern bleiben die nativen Elemente unverändert erhalten.

## [2.1.3]

### Geändert
- **Zeit-Picker auf Handy und im Browser zurück.** In 2.1.2 wurden alle Zeitfelder zu Textfeldern, um den Absturz der macOS-App zu vermeiden – das verschlechterte aber die Bedienung überall sonst, wo man vorher bequem scrollend auswählen konnte. Der native Picker kommt jetzt überall zurück; nur die Home-Assistant-App für macOS bekommt eine Alternative, weil ausschliesslich dort der Absturz auftritt.
- **In der macOS-App: zwei Auswahlfelder für Stunde und Minute** statt Tippen. `<select>` nutzt dort ein natives Menü und löst den `UIPickerView`-Absturz nicht aus.
- Erkannt wird die betroffene Umgebung über Companion-App + macOS + keine Touch-Punkte. iPhone, iPad, Android und alle Browser behalten den nativen Picker.

## [2.1.2]

### Behoben
- **Home-Assistant-App für macOS stürzte beim Klick auf ein Zeitfeld komplett ab.** Ursache war nicht das Panel, sondern eine Einschränkung von Mac Catalyst: Für `<input type="time">` öffnet WebKit einen `UIDatePicker` mit `UIPickerView`, und `UIPickerView` ist im Mac-Idiom nicht unterstützt. UIKit wirft dann eine ungefangene Exception (`_throwForUnsupportedMacIdiomBehaviorWithReason:`), die die gesamte App beendet. Alle Zeitfelder sind jetzt normale Textfelder im Format `HH:MM` und lösen keinen nativen Picker mehr aus. Die Eingabe akzeptiert `7:00`, `0700`, `07.00` und `07:00` und normalisiert automatisch; ungültige Eingaben werden auf den letzten gültigen Wert zurückgesetzt.

  Die in 2.1.1 vermutete Ursache (Re-Render-Sturm) war falsch – sie erklärte das Schließen des Dialogs, nicht den Absturz der App. Die Änderungen aus 2.1.1 bleiben trotzdem sinnvoll und aktiv.

## [2.1.1]

### Behoben
- **Formular schloss sich beim Klick auf ein Zeitfeld (Desktop)**: Das Panel rendert bei jeder Zustandsänderung in Home Assistant neu – also viele Male pro Sekunde. Dabei wurde der Wert aller Eingabefelder neu gesetzt, was den nativen Zeit-Dialog des Browsers sofort wieder schloss. Auf dem iPhone fiel das nicht auf, weil der Picker dort ein eigenes Overlay ist. Solange ein Formular geöffnet ist, lösen reine `hass`-Updates jetzt kein Re-Render mehr aus.
- **Entitäten liessen sich nicht auswählen (z. B. Workday-Sensor)**: Die Auswahlfelder waren Textfelder mit `<datalist>`. Safari zeigt Datalists praktisch nicht an, dort war schlicht nichts anklickbar. Ersetzt durch ein natives `<select>`, das in jedem Browser funktioniert und Freundlichnamen samt Entity-ID anzeigt.
- **Cursor sprang beim Tippen**: Text- und Zeitfelder lösten bei jedem Tastendruck ein Re-Render aus. Entfernt.
- Ein bereits gespeicherter, aktuell nicht verfügbarer Entitätswert bleibt jetzt erhalten und wird mit Hinweis angezeigt, statt beim Speichern unbemerkt verloren zu gehen.

### Neu
- `brand/icon@2x.png` (512×512). Seit Home Assistant 2026.3 liefern Custom Integrations ihre Brand-Bilder selbst aus dem Ordner `brand/` aus; das Brands-Repository nimmt dafür keine Beiträge mehr an.

## [2.1.0]

### Neu
- **Sonnenschutz nach Himmelsrichtung (Azimut)**: Pro Bereich kann jetzt die Fensterrichtung angegeben werden. Die Beschattung greift nur noch, wenn die Sonne tatsächlich vor den Fenstern steht. Bisher wurde der Höhenwinkel-Bereich (z. B. 0–15°) **zweimal täglich** durchlaufen – ein Westzimmer wurde damit auch morgens beschattet. Schnellwahl für Nord/Ost/Süd/West, Bereiche über 0° hinweg (z. B. 315°–45°) werden korrekt behandelt.
- **Workday-Sensor pro Bereich**: Optional ersetzt ein `binary_sensor` (z. B. der Workday-Helper) die harte Samstag/Sonntag-Logik. Deckt Feiertage, Urlaub und Schichtarbeit ab. Ohne Sensor bleibt das Verhalten unverändert.
- **Lamellen-Steuerung**: Pro Rollladen optional Lamellenwinkel für Offen, Geschlossen und Sonnenschutz (`set_cover_tilt_position`). Entitäten ohne Lamellen-Unterstützung werden übersprungen.
- **Anwesenheitssimulation**: Zufälliger Offset von ±X Minuten auf die geplanten Fahrzeiten, pro Tag stabil, damit Panel und Scheduler dieselbe Zeit anzeigen.
- **Manuelle Übersteuerung mit Ablauf**: Pro Bereich wählbar, ob eine von Hand gesetzte Position bis zur nächsten Schließfahrt (bisheriges Verhalten), nur am selben Tag oder gar nicht die Automatik blockiert.
- **Neue Entitäten**: `sensor.<bereich>_nächste_fahrt` (Zeitstempel + Richtung) und `binary_sensor.<bereich>_sonnenschutz` – nutzbar auf normalen Dashboards und in eigenen Automationen.
- **Bus-Event `shutter_pilot_cover_moved`** bei jeder automatischen Fahrt, mit `entity_id`, `position`, `tilt_position`, `reason`, `area_id` und `source`.
- **Diagnose-Download** (Einstellungen → Geräte & Dienste → Shutter Pilot → ⋮ → Diagnoseinformationen) mit Konfiguration, Laufzeitstatus und Sonnendaten.

### Behoben
- **Services ignorierten die Positionen pro Rollladen**: `open_group` fuhr fest auf 100 %, `close_group` fest auf 0 %. Jetzt gelten die konfigurierten Offen-/Geschlossen-Positionen, wie beim Scheduler.
- **`sun_protect_group` nutzte die Sonnenschutz-Position des ersten Rollladens für alle** Rollläden des Bereichs. Jetzt bekommt jeder Rollladen seinen eigenen Wert.
- **Panel zeigte veraltete Daten**: Sonnenstand, Sonnenschutz-Status und die berechneten Fahrzeiten wurden nur beim Öffnen geladen. Das Panel aktualisiert sich jetzt alle 30 Sekunden (pausiert, solange ein Formular offen ist).
- **Fehlende Manifest-Abhängigkeiten**: `http`, `frontend` und `websocket_api` waren nicht deklariert, obwohl die Integration sie nutzt.
- **`async_migrate_entry` lag als Methode in der ConfigFlow-Klasse** und wurde deshalb nie aufgerufen. Jetzt korrekt auf Modulebene.
- **Fehlende Übersetzungen zeigten den Rohschlüssel** im Panel. Es wird jetzt auf Englisch zurückgefallen.
- **Unnötige Wartezeit**: Nach dem letzten Rollladen einer Gruppe wurde weiterhin die Fahrverzögerung abgewartet (bei 8 Rollläden × 10 s eine ganze Minute).

### Geändert
- **Nur noch ein Minuten-Timer** statt zwei: Scheduler und Sonnenschutz teilen sich einen gemeinsamen Ticker.
- **`single_config_entry`** im Manifest – Panel und WebSocket-API waren immer auf eine Instanz ausgelegt.
- **Options-Flow von 858 auf ~200 Zeilen eingedampft**: Er verwies auf Dialoge, die das Panel längst vollständig ersetzt hat, enthielt tote Schritte und hart kodierte deutsche Menütexte. Er zeigt jetzt nur noch den Hinweis auf das Panel.
- **Sonnenschutz-Freigabe**: Fällt die Sonne unter den Bereich, wird nicht mehr aufgefahren – dort übernimmt der Abend-/Nachtzeitplan.

### Projekt
- MIT-Lizenz ergänzt (die READMEs verwiesen bereits auf eine LICENSE-Datei, die es nicht gab).
- `.gitignore` ergänzt und versehentlich eingecheckte `__pycache__`-Dateien entfernt.
- GitHub Actions für **hassfest** und **HACS**-Validierung sowie Issue-Vorlagen.
- **Testsuite** mit 107 Tests (`pytest-homeassistant-custom-component`) für Zeitfenster, Wochenend-/Workday-Logik, Elevation und Azimut, Aussperrschutz, Positionen pro Rollladen und den kompletten Setup-Pfad.

## [2.0.40]

### Behoben
- **Abends Rollladen öffnet voll statt zu**: Bei überlappenden Lux-Schwellen (z. B. Hoch 10 / Runter 25) konnte ab der Runter-Zeit (16:00) trotzdem die **Hoch**-Logik laufen (lux > 10). Dadurch konnte ein Rollladen erst zu- und danach wieder aufgefahren werden. Die Helligkeits-**Hoch**-Logik läuft jetzt **nur noch vor** der globalen Runter-Zeit (morgens/tagsüber); ab Runter-Zeit wird nur noch **Runter** ausgeführt.
- **2-Zustands-Fensterkontakte öffnen abends voll statt Lüftung**: Wenn ein Fensterkontakt nur offen/geschlossen unterscheidet (`window_tilted_state = none`) und der Rollladen geschlossen ist, fährt der Rollladen jetzt auf `position_when_window_tilted` (Lüftung, z. B. 50 %) statt auf 100 %. Tagsüber bleibt das Verhalten unverändert: Ist der Rollladen bereits offen, greift der Fenster-Trigger nicht.

## [1.4.42]

### Behoben
- **Helligkeit Oszillation (hoch → runter → hoch)**: Bei überlappenden Lux-Schwellen (z. B. Hoch 10 / Runter 25) hat die Runter-Logik morgens mit `lux <= 25` immer gewonnen. Mit aktivem „Zeitfenster ignorieren“ wird **Runter per Helligkeit nur noch ab der eingestellten Runter-Zeit** (z. B. 16:00) ausgeführt – morgens kein Schließen mehr durch Lux.
- **Schlafbereich zu früh hoch**: Hochfahren per Helligkeit erfolgt pro Bereich nur noch **innerhalb des Zeitplan-Hochfensters** (Hoch ab … Hoch bis). Schlafzimmer-Rollläden mit `group_up = sleep` öffnen per Lux erst, wenn z. B. WE 07:00–09:00 erreicht ist; davor übernimmt der Scheduler oder spätere Lux-Updates.
- **Wohnbereich bleibt zu (nach zu dunklem Zeitfenster)**: Wenn der Scheduler im Hoch-Fenster (z. B. 05:00–06:00) wegen zu wenig Lux blockiert wurde, wird das Hochfahren nun als **„pending“** markiert und bei `lux > Hoch-Schwelle` **einmalig nachgeholt**, auch wenn das Zeitfenster inzwischen vorbei ist (z. B. 06:33).
### Geändert
- `scheduler.is_within_group_up_schedule_window()` für die Abfrage des Hoch-Zeitfensters pro Gruppe.
- Pending/Catch-up zwischen Scheduler und Helligkeitslistener für „Hoch“ bei zu dunklem Zeitfenster.

## [1.4.05] - 2025-03-02

### Behoben
- **500 Internal Server Error**: Menu-Optionen auf Dict-Format umgestellt (kein Translation-Lookup mehr), zusätzliche Info-Logs zur Fehlersuche
- services.yaml vereinfacht (example/required entfernt)
- Unbenutzten Import entity_registry entfernt

### Geändert
- TROUBLESHOOTING.md: Anleitung für Debug-Logging ergänzt, falls keine Logs sichtbar sind

## [1.4.04] - 2025-03-02

### Behoben
- services.yaml hinzugefügt – behebt Fehler "Failed to load services.yaml for integration: shutter_pilot"

## [1.4.03] - 2025-03-02

### Behoben
- **500 Internal Server Error** (Fortsetzung): Migration alter Konfigurationseinträge, DEFAULT_OPTIONS-Merge für inkonsistente Optionen, robustere Verarbeitung von `shutters`
- TROUBLESHOOTING.md für Fehleranalyse ergänzt

## [1.4.02] - 2025-03-02

### Behoben
- **500 Internal Server Error** beim Konfigurieren: Options-Flow absicherung für `options=None`, Fehler „settings“ → „settings_menu“ korrigiert
- Icon (Rollladen + Sonne) hinzugefügt – Bereitstellung für Home Assistant Brands Repository

## [1.4.01] - 2025-03-02

### Geändert
- **Einrichtung vereinfacht**: Latitude/Longitude werden automatisch aus dem Home Assistant Heimatstandort übernommen – keine manuelle Eingabe mehr nötig
- **integration_type**: Von `helper` auf `service` geändert – erscheint nun vollwertig unter Integrationen
- **Konfigurationsanleitung**: Klare Anleitung: Tab Integrationen → Shutter Pilot → Menü (⋮) → Konfigurieren
- HACS: README.md und hacs.json im Repository-Root für die Anzeige in Home Assistant ergänzt

### Behoben
- Nutzer sehen nach der Einrichtung nun klar, wo sie die Integration konfigurieren können

## [1.3.0]

- Rollladensteuerung mit Fenster-Trigger, Sunrise/Sunset, Auto-Modi
- Zeiten pro Gruppe (Living, Sleep, Children)
- Drive-After-Close, Helligkeitssensor, Elevation-Sonnenschutz
