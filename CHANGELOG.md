# Changelog

Alle wichtigen Änderungen an Shutter Pilot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [2.13.0]

Aus GitHub-Diskussion #5 (Fireblade900rr): das Kinderzimmer soll in den
Schulferien morgens dunkel bleiben.

### Neu
- **Beschattung nur zu bestimmten Uhrzeiten.** Elevation, Fensterrichtung, Bedingungen und Beschattungszeitraum beschreiben alle *die Sonne* – für „erst ab neun" gab es bisher nichts. Zwei neue Felder, **beide einzeln optional**: „Beschattung frühestens ab" reicht für sich, eine obere Grenze braucht es nicht. Einstellbar je Bereich und **je Rollladen** – der gefragte Fall ist immer ein einzelnes Zimmer, nicht das ganze Geschoss. Leer am Rollladen heißt: der Bereichswert gilt. Ein Fenster über Mitternacht gibt es bewusst nicht; steht die zweite Zeit vor der ersten, wird die Einstellung verworfen und im Log genannt, statt sie stillschweigend als Umschlag zu lesen.
- Endet die Beschattung an dieser Grenze, wird **sofort freigegeben** – die Haltezeit gilt dafür nicht. Sie ist für durchziehende Wolken da; eine Uhrzeit kommt innerhalb der Haltezeit nicht zurück, und der Rollladen zählte solange weiter als beschattet, was das planmäßige Öffnen zusätzlich blockiert hätte.

### Geändert
- **Der „Workday-Sensor" heißt jetzt „Sondertage-Sensor".** Der alte Name verschwieg seinen wichtigsten Einsatz: Damit lassen sich Feiertage, Urlaub, Schichtdienst **und Schulferien** abbilden. Der Hinweistext nennt jetzt das vollständige Rezept – Ferien-Sensor eintragen, „Hoch Wochenende" auf 09:00, „Runter Wochenende" leer lassen –, mit dem genau die gefragte Ferienregelung ohne eine Zeile Code entsteht. Gespeicherter Schlüssel und Verhalten bleiben unverändert.
- **Der Export nennt die Uhrzeit-Grenze**, wenn eine gesetzt ist: aktuelle Uhrzeit, Fenster und Ergebnis in derselben Zeile wie Elevation und Azimut.

### Behoben
- **Ein Tippfehler in einem Zeitfeld erfand eine Grenze.** Der gemeinsame Zeit-Parser fällt bei unlesbaren Werten auf 06:00 zurück. Für die neuen Felder wäre daraus eine Beschattungssperre jeden Morgen geworden, die niemand eingetragen hat. Sie prüfen jetzt streng auf `HH:MM` und ignorieren alles andere – mit einer Zeile im Log.

## [2.12.0]

Markisen. Nicht als umgedrehter Rollladen, sondern mit dem Teil, der eine
Markise erst betriebssicher macht: Wind- und Regenschutz.

### Neu
- **Eigener Tab „Markisen".** Eine Markise wird dort angelegt statt bei den Rollläden. Sie hat nur zwei Positionen – Ruhestellung (eingefahren) und Beschattung (ausgefahren) –, dazu einen Beschattungsbereich statt Hoch- und Runter-Bereich. **Eine Markise fährt in keinem Zeitplan mit**: weder Uhrzeit noch Helligkeit noch Sonnenauf- und -untergang bewegen sie. Ausgefahren wird sie allein von der Beschattung, und die rechnet mit denselben Regeln wie bei den Rollläden – Sonnenhöhe, Fensterrichtung, Zusatzbedingungen, Saison, Haltezeit.
- **Wind-, Regen- und Frostschutz.** Wind-, Regen- und Temperatursensor stehen global unter Einstellungen und gelten für jede Markise. Beim **Wind** darf eine einzelne Markise abweichen – eigener Sensor oder nur eigene Schwellen –, weil Wind örtlich verschieden ist; Regen und Frost fallen übers ganze Haus gleich und bleiben global. Über der Einfahrschwelle fährt die Markise sofort ein und darf nicht mehr ausfahren; freigegeben wird sie erst wieder unter der zweiten Schwelle **und** nach einer Sperrzeit (Vorgabe 20 min bei Wind, 30 min bei Regen). Eine Bö ist nach zwanzig Sekunden vorbei – die Markise soll trotzdem nicht sofort wieder heraus, und jede neue Überschreitung startet die Zeit von vorn. Dasselbe für Regen und, nach unten vergleichend, für Frost.
- **Der Schutz gilt auch bei ausgeschalteten Schaltern.** Hauptschalter aus, Bereichsautomatik aus, Markisen-Automatik aus: eingefahren wird trotzdem. Das ist eine bewusste Abweichung von der sonstigen Rangfolge. Ein Schutz, der sich versehentlich abschalten lässt, ist keiner; abschalten geht absichtlich, indem der Sensor entfernt wird.
- **Toter Sensor: ausfahren sofort gesperrt, einfahren nach Karenz.** Meldet der Sensor `unavailable` oder `unknown`, weiß niemand, was der Wind tut – ausgefahren wird ab der ersten Sekunde nicht mehr. Eine bereits ausgefahrene Markise wird erst nach einer Karenzzeit (Vorgabe 10 min) hereingeholt, damit ein Sensor, der beim Neustart kurz aussetzt, nicht das ganze Haus einfährt.
- **Ausfahrlänge nach Sonnenhöhe** (optional, Vorgabe aus). Steht die Sonne hoch, reicht wenig Ausfall; sinkt sie, braucht dieselbe Fläche mehr. Zwei Stützpunkte, gerade Linie dazwischen, dazu eine Mindeständerung – ohne die liefe der Antrieb jede Minute ein paar Prozent.
- **Sperr-Sensor je Markise** (`binary_sensor.…_sperre`) mit Grund und Restzeit als Attribute, **Dienst `shutter_pilot.retract_awnings`** für eine angekündigte Sturmwarnung (fährt alle Markisen sofort ein, ohne Staffelung), und das Ereignis `shutter_pilot_awning_retracted` für eigene Benachrichtigungen.
- **Bestehenden Rollladen als Markise übernehmen.** Wer eine Markise erst als Rollladen angelegt hat, wählt sie im Markisen-Tab aus und bekommt einen Knopf dafür. Fenster-, Lamellen- und Schließ-Einstellungen werden dabei gelöscht statt stehengelassen – gespeichert, sichtbar und wirkungslos ist genau die Sorte Einstellung, die der Export seit 2.10.2 anprangert.

### Behoben
- **Antriebe ohne Positionsmeldung ließen sich gar nicht fahren.** Viele Markisenmotoren und etliche ältere Rollladenantriebe kennen nur auf, stop und zu; `cover.set_cover_position` scheitert dort. Seit 2.8.0 wird eine gescheiterte Fahrt jede Minute wiederholt – aus einem stummen Fehler wurde also eine Endlosschleife. Jetzt wird auf „ganz auf" bzw. „ganz zu" ausgewichen, und eine Teilposition an so einem Antrieb steht einmal als Warnung im Log. Betrifft Rollläden genauso.

### Geändert
- **Der Export beantwortet „warum ist die Markise nicht draußen".** Je Markise eine Tabelle mit Wert, Einheit, Schwellen und Ergebnis je Schutz, dazu die Freigabezeit. Warnt außerdem, wenn ein Windsensor in m/s misst und die Schwelle nach km/h aussieht: Faktor 3,6 daneben heißt, die Markise fährt nie ein.
- **Der Auto-Schalter einer Markise heißt „Markise <Name>"** statt „Rollladen <Name>". Bestehende Entitäts-IDs bleiben.

## [2.11.1]

Aus dem Forum, Viktor: ein Rollladen liess sich zweimal anlegen.

### Behoben
- **Derselbe Rollladen konnte mehrfach hinzugefügt werden.** Ein Fehlklick reichte – und mit verschiedenen Bereichen an den beiden Einträgen fuhr der Rollladen im Minutentakt hin und her, weil jeder Eintrag für sich entscheidet und die beiden sich widersprechen. In der Liste sieht man den Doppeleintrag kaum. Das Panel warnt jetzt direkt unter der Auswahl, und der Server nimmt einen zweiten Eintrag für dieselbe Cover-Entität gar nicht mehr an. Den bestehenden Eintrag zu bearbeiten geht unverändert. (Forum, Viktor)

### Geändert
- **Der Export benennt bestehende Doppeleinträge.** Wer den Fehler schon in seiner Konfiguration hat, findet ihn im Bericht statt beim Suchen: die Zeile steht bei beiden Einträgen, mit dem Hinweis, einen davon zu löschen.

## [2.11.0]

Aus dem Forum, hollizone: im Helligkeitsmodus fehlte eine Uhrzeit, zu der
gefahren wird, wenn der Lux-Wert nie hoch genug steigt.

### Neu
- **„Spätestens hochfahren um" und „Spätestens runterfahren um" im Helligkeitsmodus.** In der dunklen Jahreszeit bleibt es tagelang trüb und die Hoch-Schwelle wird nie überschritten – die Zeitfenster helfen dagegen nicht, sie *erlauben* eine Fahrt nur und lösen keine aus. Die neuen Fristen fahren einmal am Tag unabhängig vom Helligkeitswert. **Beide sind standardmäßig aus**, damit sich in bestehenden Anlagen nichts von selbst bewegt. Für das Wochenende gibt es je einen eigenen Wert; bleibt er leer, gilt der Wert der Woche. Ein Rollladen, der bereits in diese Richtung gefahren ist, bleibt stehen – Beschattung und eine manuelle Position haben weiterhin Vorrang, und eine bereits vergangene Frist wird nach einem Neustart nicht nachgeholt. (Forum, hollizone)

## [2.10.3]

Wieder aus Wolfs Export – diesmal aus einer Zeile, über die niemand gestolpert
war, weil sie sauber aussah.

### Behoben
- **„Sonnenhöhe prüfen" wirkte am einzelnen Rollladen nicht.** Der Haken kam in 2.10.1 für Bereich *und* Rollladen. Gespeichert wurde er auch am Rollladen, gelesen nie: die Beschattung fragte dort weiter den Bereich. Wer die Höhenprüfung an einem Fenster abschalten wollte – dem mit dem eigenen Helligkeitssensor –, bekam sie trotzdem. Ab jetzt zählt der Haken am Rollladen, sobald „Eigene Ausrichtung" eingeschaltet ist; ohne diesen Schalter gelten wie bei allen anderen Geometriewerten die Werte des Bereichs. (Forum, Wolf)

### Geändert
- **Der Bericht wird als `.txt` heruntergeladen.** Inhalt und Aufbau bleiben gleich, nur die Endung ändert sich: das Forum nimmt `.md` nicht an, `.txt` schon. Wer den Bericht stattdessen einfügt, merkt keinen Unterschied. (Forum, Wolf)
- **Der Export nennt auch eine abgeschaltete Höhenprüfung, die niemand liest.** Steht sie am Rollladen auf „aus", während „Eigene Ausrichtung" aus ist, dann entscheidet der Bereich – der Haken steht in der Tabelle wie jeder wirksame Wert. Eingeschaltet bleibt er unerwähnt: das ist die Vorgabe und sagt nichts aus.

## [2.10.2]

Aus Wolfs Einstellungs-Export im Forum. Der Bericht hat einen Fehler
aufgedeckt, der noch keinem aufgefallen war – und dabei gleich gezeigt, wo er
selbst in die Irre führt.

### Behoben
- **Der Aussperrschutz galt beim Fensterkontakt nicht.** Er greift an jedem automatischen Fahrweg – nur nicht an dem einzigen, der ausschließlich *bei offenem Fenster* fährt. Wer die Position bei offenem Fenster niedriger eingestellt hatte als die Mindesthöhe des Aussperrschutzes, bekam genau das, was die Einstellung verhindern soll: Terrassentür auf, Rollladen davor zu. Aufgefallen bei einem Rollladen, der beschattet auf halber Höhe stand – seit 2.8.1 erreicht der Fensterkontakt auch den beschatteten Rollladen, und ab da war der Weg offen. Die Zielposition wird jetzt genauso gedeckelt wie bei jeder anderen Fahrt. (Forum, Wolf)
- **„Bericht herunterladen" tat auf Android nichts.** Der Knopf reagierte, die Datei kam nie an. Zwei Ursachen, auf dem Rechner beide unsichtbar: die App verwirft den Klick auf einen Download-Verweis, der nicht in der Seite hängt, und die erzeugte Datei wurde sofort wieder freigegeben, bevor der Download anlief. (Forum, Wolf)

### Geändert
- **Der Export sagt jetzt, wenn die Merker gerade erst geleert wurden.** Jedes Speichern im Panel lädt die Integration neu, und dabei fangen „beschattete Rollläden", „heute schon hochgefahren" und die wartenden Nachhol-Fahrten wieder bei null an. Wer direkt nach einer Änderung exportierte – also fast jeder – bekam eine Tabelle voller Striche und obendrein den Hinweis, dass das in einen Fehlerbericht gehört. Der Bericht nennt jetzt den Zeitpunkt des letzten Ladens und erklärt die leeren Zeilen, statt sie anzuschwärzen.
- **Der Export benennt zwei Einstellungen, die dastehen und nichts tun.** Eigene Werte für Sonnenhöhe und Fensterrichtung am Rollladen, während „Eigene Ausrichtung" aus ist – dann gelten die Werte des Bereichs. Und eine Position für „Fenster offen" an einem Kontakt ohne Kipp-Zustand: der ist zweiwertig, gefahren wird immer die Kipp-Position. Beide Werte stehen in der Tabelle wie jeder andere, und nichts unterschied sie bisher von denen, die wirken.
- **Warnung im Formular, wenn die Lux-Schwellen verkehrt herum stehen.** Hochgefahren wird oberhalb der Hoch-Schwelle, runter unterhalb der Runter-Schwelle. Liegt die Hoch-Schwelle darunter, gilt zwischen beiden Werten beides gleichzeitig – überschneiden sich dann noch die Zeitfenster, pendelt der Rollladen. Dieselbe Art Hinweis wie bei den Bedingungsschwellen seit 2.8.0.

## [2.10.1]

Drei Wünsche aus dem Forum, und einer davon deckte eine Falle auf, die neue
Nutzer seit jeher trifft.

### Neu
- **„Sonnenhöhe prüfen" lässt sich abschalten** – je Bereich und je Rollladen. Wer an jedem Fenster einen Helligkeitssensor hängen hat, will den entscheiden lassen: der misst die Sonne bereits. Die Höhenspanne ist dann eine Zahl, die man raten müsste. Aus heißt: allein die Bedingungen zählen; die Fensterrichtung bleibt davon unberührt. Bestehende Bereiche prüfen unverändert weiter. (Forum, charly166)
- **Raumtemperatur auf der Dashboard-Karte.** Optionaler Sensor je Bereich, rein zur Anzeige – er entscheidet nichts. Ein toter oder fehlender Sensor lässt die Zeile einfach weg. (Forum, hollizone)

### Behoben
- **Ein neu angelegter Bereich beschattete tagsüber nie.** Die Vorgabe für die Sonnenhöhe stand auf **0°–15°** – im Sommer steht die Mittagssonne bei 60°. Wer einen Bereich anlegte, den Sonnenschutz einschaltete, seine Bedingung eintrug und sonst nichts änderte, bekam Beschattung nur kurz nach Sonnenaufgang und vor Sonnenuntergang. Neue Bereiche starten jetzt mit **0°–90°**. Bestehende Bereiche behalten ihre Werte.

## [2.10.0]

### Neu
- **Zwei Bedingungen für „Abweichendes Schliessen".** Bisher gab es nur eine, und „der Tag war warm" allein ist selten die ganze Regel – „und jemand ist zu Hause" ist die andere Hälfte. Die zweite erscheint, sobald die erste steht; sind beide eingetragen, muss abends auch beides zutreffen. Wie beim automatischen Lüften. Bestehende Einstellungen bleiben unverändert, die erste Bedingung behält ihren Schlüssel. (Forum, Linos)

### Behoben
- **Ein wegen offenem Fenster nachgeholter Rollladen blieb am nächsten Morgen unten.** Abends fahren alle runter, einer bleibt wegen offenem Fenster oben und wird vorgemerkt, nach dem Schließen holt er die Fahrt nach – und am nächsten Morgen fährt alles hoch außer ihm. Der Nachhol-Zweig verließ die Schleife, **bevor** die Merker „heute schon hoch-/runtergefahren" gesetzt wurden. Der Rollladen galt damit weiter als „heute hochgefahren", und genau danach filtert der nächste Morgen. (Forum, heinzie)
- **Diagnose und Export zeigten „heute schon hochgefahren" dauerhaft leer.** Beim Beginn eines Fahrzyklus wurde die Merkliste durch eine **neue** ersetzt, während Zeitplan und Helligkeitsmodus weiter auf die alte schrieben. Ab der ersten Fahrt zeigten Diagnose und Export deshalb etwas anderes an als das, wonach tatsächlich entschieden wurde – und der Aufruf selbst blieb wirkungslos. Beide Listen sind jetzt dieselbe.

### Geändert
- **„Beschatten ab" stand auch dort, wo nichts beschattet wird.** Dieselben Felder tragen die Bedingung für Abweichendes Schliessen, Frostschutz und Lüften – beschriftet waren sie überall mit den Wörtern des Sonnenschutzes, samt Hinweis auf „durchziehende Wolken". Außerhalb des Sonnenschutzes heißt es jetzt „Trifft zu ab", und der Hinweis spricht von der Schwelle statt vom Wetter. An der Funktion ändert sich nichts – die Bedingungen hingen nie am Sonnenschutz. (Forum, Linos)

## [2.9.1]

### Geändert
- **Die Abschnitte in den Formularen lassen sich auf- und zuklappen.** Bereich, Rollladen und Einstellungen waren eine einzige lange Bahn – im Bereichsformular über 20 Felder am Stück. Jede Überschrift ist jetzt ein Schalter, und **zugeklappt bleibt sie mit einer kurzen Erklärung stehen**: „Sonnenschutz – Sonnenhöhe, Richtung, Bedingungen", „Kalender & manuelle Bedienung – Feiertage, Zufallsversatz, manuelle Übersteuerung". So ist der Aufbau eines Formulars auf einen Blick zu lesen, statt ihn zu erscrollen. Fünf Überschriften hatten noch gar keine Erklärung – die haben jetzt eine. Was du auf- oder zuklappst, merkt sich der Browser; beim ersten Mal steht der erste Abschnitt offen. Ein zugeklappter Abschnitt ändert nichts an den Werten: gespeichert wird immer der ganze Datensatz. (Forum, Linos)

## [2.9.0]

Ausführliches Feedback von **Linos** im Forum – Aufbau, Beschriftungen und zwei
Fragen, hinter denen echte Lücken steckten.

### Neu
- **Sensor „Vorhersage Tageshöchstwert".** Eine Tagesvorhersage wird im Lauf des Tages fortgeschrieben, und die meisten Quellen setzen sie herunter, sobald die Spitze vorbei ist: um 21 Uhr steht bei „Höchsttemperatur heute" womöglich 25 °C, obwohl es um 15 Uhr 28 °C hatte. Eine Bedingung wie „nur halb schließen, wenn es über 26 °C hatte" wird genau dann geprüft – gegen eine Zahl, die sich klammheimlich davongestohlen hat. Der neue Sensor hält den höchsten Wert des Tages fest und steigt bis Mitternacht nur noch. Für Entscheidungen am Tag nimmt man weiter den laufenden Wert, für Entscheidungen am Abend diesen.
- **Bereich duplizieren.** Knopf in der Bereichsliste: öffnet eine Kopie mit allen Einstellungen zum Umbenennen. ID und Automatik-Schalter bleiben leer, damit die Kopie nicht am Schalter des Originals hängt.

### Behoben
- **„Warte auf passende Sonnenhöhe" stand da, wenn die Sonnenhöhe passte.** Der Text erschien immer dann, wenn die Geometrie stimmte und der Sonnenschutz trotzdem nicht aktiv war – wer 0°–90° einstellte, bekam ihn den ganzen Tag und suchte den Fehler bei der Elevation. Das Dashboard sagt jetzt, woran es wirklich liegt: Sonnenhöhe daneben, falsche Himmelsrichtung, oder Geometrie passt und die Bedingungen fehlen noch.

### Geändert
- **Die beiden Offsets erklären ihr Vorzeichen.** Die Schieber gehen von −60 bis +60, nur stand nirgends, in welche Richtung. Es gilt: Plus verschiebt nach hinten, Minus nach vorn – −15 fährt eine Viertelstunde vor Sonnenaufgang. An der Rechnung ändert sich nichts, es steht jetzt nur dabei.
- **Bereiche stehen überall alphabetisch.** Gespeichert wird weiter in Anlagereihenfolge, angezeigt sortiert – vorher stand derselbe Bereich im Dashboard an anderer Stelle als im Bereiche-Tab.
- **Shutter Pilots eigene Entitäten stehen in der Auswahlliste ganz oben.** Die Vorhersage-Sensoren sind für die Bedingungsfelder gedacht, standen aber irgendwo zwischen tausend fremden Entitäten.

## [2.8.2]

Nacharbeit zu 2.8.1, aus heinzies Diagnose-Datei gelesen.

### Behoben
- **Die Position für „Fenster offen" tat bei den meisten Kontakten nichts.** Ein Kontakt ohne eigenen Kipp-Zustand meldet nur offen und zu; offen und gekippt sind für ihn dasselbe, gefahren wird deshalb die **Kipp-Position** – auch bei „offen". Im Formular standen trotzdem zwei Schieber untereinander, und der obere sah aus wie der zuständige. Wer dort 97 % einstellte, bekam die 98 % vom Feld darunter. Ohne Kipp-Zustand steht jetzt **ein** Schieber da, mit dem Hinweis daneben, warum. Sobald ein Kipp-Zustand eingetragen ist, erscheinen wieder beide.
- **Der Hinweis dazu war schlicht falsch.** Er sagte, die Position gelte, „wenn der Rollladen geschlossen ist" – seit 2.8.1 stimmt das doppelt nicht mehr. Jetzt steht dort, was tatsächlich der Fall ist.

## [2.8.1]

Der Export aus 2.8.0 hat sofort geliefert: MartyBrs Bericht beantwortete seine
Meldung in einer Zeile, und heinzies Fensterkontakt liess sich damit auf zwei
Ursachen zurückführen, von denen jede für sich gereicht hätte.

### Behoben
- **„open" als Fenster-Status traf bei einem `binary_sensor` nie zu.** Das Formular bietet „on", „open", „true" und „offen" zur Auswahl an – ein `binary_sensor` meldet aber ausschliesslich `on` oder `off`. Wer „open" wählte, hatte einen Kontakt konfiguriert, der dauerhaft als geschlossen galt: keine Lüftungsposition, keine Rückfahrt, kein Aussperrschutz, und nirgends ein Hinweis darauf. Die gebräuchlichen Wörter für „offen" und „zu" gelten jetzt als gleichbedeutend, bestehende Einstellungen ändern sich dadurch nicht. Zusätzlich steht **„off"** zur Wahl – für Kontakte, die andersherum melden – und unter dem Feld steht, was die gewählte Entität gerade meldet. (Forum, heinzie)
- **Der Fensterkontakt erreichte einen beschatteten Rollladen nicht.** Reagiert wurde nur, wenn der Rollladen (nahezu) geschlossen war. Die Beschattung parkt ihn aber auf halber Höhe – weder zu noch offen –, und damit fiel er durch die Prüfung. Wer nachmittags die Terrassentür öffnete, stand vor dem heruntergefahrenen Rollladen. Die Rangfolge lautet Fensterkontakt > Beschattung > Lüften; jetzt gilt sie auch hier. Ein tagsüber offener Rollladen bleibt unverändert in Ruhe. (Forum, heinzie)
- **Endete die Beschattung bei offenem Fenster, fuhr der Rollladen später wieder herunter.** Die Rückfahrhöhe des Fensterkontakts blieb stehen und wurde beim Schliessen angefahren – auf die Beschattungsposition, Stunden nachdem die Beschattung vorbei war. Die Freigabe räumt sie jetzt mit weg, so wie Zeitplan und Helligkeitsmodus es beim Hochfahren schon tun.

### Geändert
- **Der Export nennt die Einheit des Sensors.** „559,7" neben der Schwelle „30000" sieht nach „noch nicht hell genug" aus; „559,7 W/m²" neben „30000" zeigt, dass dieser Sensor die Schwelle nie erreichen wird, weil dort Lux-Werte eingetragen sind. Genau dieser Fall steckte in MartyBrs Bericht.
- **Der Export sagt, wenn eine Entscheidung gar nicht gefahren wird.** Bei ausgeschaltetem Haupt-, Bereichs- oder Rollladenschalter stand dort bisher „Ergebnis: beschatten", ohne dass irgendetwas passieren konnte.
- **Der Export erklärt die beiden stillen Haken.** Ein ✅ hinter einem Sensor, der `unknown` meldet, heisst nicht „Bedingung erfüllt", sondern „blockiert nicht" – das steht jetzt daneben. Ebenso wird die verkehrt herum gesetzte Schwelle aus 2.8.0 im Bericht benannt, nicht nur im Formular und im Log.

## [2.8.0]

Zwei Meldungen aus dem Forum (MartyBr, heinzie) liessen sich aus ihren
Screenshots **nicht** beantworten – die Einstellung, auf die es ankam, war nie
im Bild. Deshalb steht am Anfang dieser Version ein Export, und dahinter fünf
Fehler, die beim Nachprüfen des Codes zutage kamen.

### Neu
- **Einstellungen exportieren** (Einstellungen → „Einstellungen exportieren"). Erzeugt einen Bericht mit allen gespeicherten Einstellungen jedes Bereichs und jedes Rollladens, den **aktuellen Sensorwerten** und – das eigentlich Nützliche – der **Beschattungs-Entscheidung von genau jetzt**, je Rollladen mit Begründung Zeile für Zeile: Elevation im Bereich? Richtung? Zeitraum? Welche Bedingung erfüllt, welche nicht? Kopieren oder als `.md` herunterladen und ins Forum stellen. Enthalten sind nur Shutter Pilots eigene Einstellungen und die Namen der gewählten Entitäten – keine Zugangsdaten, kein Standort. Gerechnet wird ausdrücklich gegen eine **Kopie** des Hysterese-Gedächtnisses: eine Frage zu stellen darf die Antwort nicht verändern.

### Behoben
- **Eine Beschattung, die beim Fahren scheiterte, wurde nie wiederholt.** Der Merker „dieser Rollladen ist beschattet" wurde gesetzt, *bevor* gefahren wurde. Blieb der Fahrbefehl stecken, galt die Beschattung ab der nächsten Minute als erledigt – der Rollladen stand offen in der Sonne, dauerhaft und ohne Fehlermeldung. Der Merker folgt jetzt der Fahrt, statt ihr vorauszugehen.
- **Ein beschattetes Fenster sperrte das Hochfahren im ganzen Bereich.** Die Beschattung wird seit 2.7.0 je Rollladen geführt, die Sperre fürs automatische Öffnen fragte aber weiter die Bereichs-Summe. Betroffen war jeder andere Rollladen desselben Bereichs, der zufällig nahe seiner Beschattungsposition stand – und nur der, weil genau die Position verglichen wird. Deshalb half es, ihn von Hand ein Stück zu verfahren. (Forum, heinzie)
- **Die Haltezeit hielt auch das berechtigte Ende der Beschattung auf.** „Beschattung halten" ist für durchziehende Wolken gedacht. Sie lief aber auch, wenn die Sonne aus dem Fenster gewandert, über den Höhenbereich gestiegen oder der Beschattungszeitraum vorbei war – bis zu zwei Stunden dunkel, obwohl nichts davon zurückkommt. Für den Wolkenfall gilt sie unverändert, und sie schreibt ihre Restzeit jetzt sichtbar ins Log.
- **„Aufheben unter" über „Beschatten ab" wurde stillschweigend verworfen.** Die beiden Werte sind ein Einschaltpunkt mit einem Aufhebepunkt darunter, keine Spanne von–bis. Wer beim Azimut 40 und 130 einträgt und den Bereich 40°–130° meint, bekam die Bedingung „Azimut ≥ 40" – von morgens bis abends erfüllt, aus der falschen Himmelsrichtung inklusive. Das Formular warnt jetzt an Ort und Stelle, und einmal je Bedingung steht es auch im Log. Für eine Spanne von Himmelsrichtungen gibt es „Nur bei passender Fensterrichtung". (Forum, MartyBr)
- **„Eigene Ausrichtung für diesen Rollladen" verschob die Höhengrenzen, ohne dass man etwas eingab.** Bei einem Bereich, der noch die alte Einzelschwelle trug, warf der Haken sie weg und fiel auf die eingebaute Vorgabe zurück: aus „ab 25°" wurde „zwischen 1° und 4°", also praktisch nie. Die Grenzen des Bereichs bleiben jetzt stehen, bis wirklich eigene Werte gesetzt sind.
- **Die Felder hinter „Eigene Ausrichtung" standen an der falschen Stelle.** Auf den Haken folgte zuerst der Bedingungsblock und erst dahinter die Höhen- und Richtungsfelder, die der Haken freischaltet. Man hakte an, sah darunter Bedingungen erscheinen, füllte sie aus – und bekam die eigentlichen Felder nie zu Gesicht. Sie stehen jetzt direkt darunter, mit dem Hinweis, dass ab dann sie statt der Bereichswerte gelten.

## [2.7.2]

### Behoben
- **Bei einer Textbedingung liess sich praktisch nur ein Zustand auswählen.** Das Formular bot die Zustände als Knöpfe an – bei einer `weather.*`-Entität die 15 Standardlagen von Home Assistant, bei jedem anderen Sensor aber nur den **gerade gemeldeten** Zustand. Wer einen Template- oder Scrape-Sensor für die Wetterlage benutzt, hätte bis zum nächsten Regen warten müssen, um „rainy" anklicken zu können. Dort lässt sich jetzt zusätzlich ein Zustand von Hand eintragen. Bei Wetter-Entitäten ändert sich nichts – dort ist die Liste vollständig bekannt. (GitHub #6)

## [2.7.1]

Nacharbeit zu 2.7.0.

### Behoben
- **Der Mindestabstand galt nicht für die Knöpfe im Dashboard.** Die Drosselung sitzt im Backend, die Knöpfe riefen die Cover-Dienste aber direkt auf – und zwar mit **einem** Aufruf für alle Rollläden eines Bereichs, den Home Assistant dann gleichzeitig ausführt. Ausgerechnet der Knopf, den man drückt, erzeugte also genau den Funk-Burst, gegen den die Einstellung gebaut ist. Die Knöpfe staffeln jetzt ebenfalls. Sie rufen weiterhin direkt die Cover-Dienste auf, damit Home Assistant die Rechte je Entität selbst prüft.

### Geändert
- **Das Panel ist in allen elf Sprachen vollständig.** In den neun kleineren Sprachen fehlten 52 Texte und erschienen auf Englisch – darunter ganze Abschnitte: Zeitklammern im Sonnenstand-Modus, Fahrtkontrolle, Wetter, Beschattungszeitraum, abweichendes Schließen, eigene Ausrichtung je Rollladen sowie die Sonnenschutz-Anzeige auf dem Dashboard.
- **Die Vorhersagesensoren heißen jetzt in der Sprache der Oberfläche.** Sie waren hart deutsch, auch für englische Nutzer – daran war im Forum jemand gescheitert, der nach „forecast" gesucht hatte. **Bestehende Entitäts-IDs ändern sich nicht**, Automationen laufen unverändert weiter; auf Deutsch bleibt auch der angezeigte Name derselbe.

## [2.7.0]

Zwei Fehlerberichte von GitHub und der gesammelte Rest aus dem Forum – die Liste ist damit abgearbeitet. Danke an vitals5, Vorhand, Viktor, MartyBr, charly166, Smons und Linos.

### Behoben
- **Rollladen fuhr im Minutentakt zwischen offen und Sonnenschutz hin und her.** Betroffen waren Rollläden, die zum Hochfahren einen **anderen Bereich** benutzen als zum Runterfahren – also genau das Muster „morgens raumweise, abends alle zusammen". Die Beschattung wurde vom Runter-Bereich gesetzt, aber vom Hoch-Bereich wieder aufgehoben; unterschieden sich deren Bedingungen, Beschattungszeiträume oder Ausrichtungen, hoben sich beide jede Minute gegenseitig auf. Der Bereich, mit dem ein Rollladen schließt, entscheidet jetzt allein über seine Beschattung. (GitHub #4)
- **Eigener Rollladenname wurde im Dashboard nicht angezeigt.** Dort stand der Name der Cover-Entität, auch wenn im Formular ein eigener eingetragen war. Der eigene Name gewinnt jetzt – so wie im Tab Rollläden schon immer. (GitHub #3)
- **Nachhol-Fahrten gingen bei einem Neustart verloren.** Stand die Schließzeit an, während das Fenster noch offen war, verschwand der Merker beim nächsten Neustart lautlos und der Rollladen blieb die Nacht über oben. Er wird jetzt gespeichert – und nach 24 Stunden verworfen, weil eine Fahrt von vorgestern nichts mehr darüber sagt, was jetzt gelten soll.
- **Fahrtkontrolle konnte eine laufende Prüfung aus den Augen verlieren.** Wurde eine Fahrt durch eine neue ersetzt, räumte die abgebrochene Prüfung anschließend den Eintrag der neuen weg.

### Neu
- **Mindestabstand zwischen Fahrbefehlen** (Einstellungen, 0–10 s). Funk-Empfänger verschlucken Befehle, die gleichzeitig ankommen. Die Verzögerung im Bereich hilft dagegen nicht, weil jeder Bereich für sich fährt. Der neue Abstand wirkt an der einen Stelle, durch die **jede** Fahrt läuft – automatisch wie von Hand – und staffelt sie über alle Bereiche hinweg. Gedrosselt heißt gewartet, nicht weggelassen.
- **Beschattung halten** (Bereich, 0–120 Min.). Eine durchziehende Wolke beendet die Bedingung wirklich, und der Rollladen fuhr sofort auf. So lange bleibt die Beschattung jetzt stehen. Das Beschatten selbst und das Ende des Tages bleiben bewusst sofort.
- **Sonnengrenzen im Helligkeitsmodus.** „Runter frühestens X Minuten vor Sonnenuntergang" – damit ein Gewitter am Nachmittag die Rollläden nicht am helllichten Tag schließt. Uhrzeitfenster können das nicht, weil der Sonnenuntergang übers Jahr um Stunden wandert.
- **Einstellungen von einem anderen Rollladen übernehmen.** Vorlage wählen, übernehmen, fertig. Cover-Entität, Name, Bereiche und Fenstersensoren bleiben unverändert – genau die unterscheiden zwei sonst gleiche Rollläden.
- **Antrieb ohne Positionsrückmeldung (blind fahren).** Für einseitigen Funk wie Somfy RTS. Solche Antriebe antworten nicht, und jede Prüfung, die eine Position braucht, gab bisher auf – womit Fenstertrigger und automatisches Lüften für sie stillschweigend abgeschaltet waren. Mit dem Haken rechnet Shutter Pilot mit der zuletzt gesendeten Position.
- **Rollläden lassen sich im Dashboard einzeln bedienen.** Jede Rollladenzeile in der Bereichskarte hat eigene Knöpfe für hoch, stop und runter.

### Geändert
- **Hinweis beim Frostschutz**, welcher Sensor sich als Bedingung anbietet – der Name „Vorhersage Tiefsttemperatur" war schwer zu finden, wenn man nach „forecast" gesucht hat.
- **README**: neue Abschnitte zur Beschattung allein über Helligkeitssensoren (das ging schon immer, stand aber nirgends), zum Mindestabstand, zu den Sonnengrenzen, zur Haltezeit und zum Kopierknopf.

> **Nach dem Update den Browser hart neu laden** (Strg+F5 bzw. Cmd+Shift+R), sonst zeigt die Seitenleiste weiter das alte Panel.

## [2.6.0]

Aus dem Forum: zwei bestätigte Fehlermeldungen von Xerenas und drei Anregungen von Xerenas und Linos.

### Neu
- **Verzögerung beim Schließen des Fensterkontakts.** Beim Drehen des Griffs von „gekippt" auf „offen" läuft der Kontakt kurz durch „geschlossen". Shutter Pilot beendete daraufhin sofort die Lüftung und fuhr zurück; die Offen-Position wurde danach teils gar nicht mehr angefahren. Je Rollladen lässt sich jetzt einstellen, wie lange „geschlossen" anhalten muss, bevor darauf reagiert wird – **0 bis 30 Sekunden, Standard 5**. Kommt in dieser Zeit wieder „offen" oder „gekippt", wird die Rückfahrt verworfen und stattdessen die passende Fensterposition angefahren. **Das gilt auch für bestehende Rollläden:** die Rückfahrt nach dem Schließen setzt künftig fünf Sekunden später ein. Wer das nicht möchte, stellt den Regler auf 0.
- **Automatisches Lüften.** Bisher ging Lüften nur von Hand. Im Bereich lässt sich jetzt festlegen, unter welchen Bedingungen die Rollläden von selbst auf ihre Lüftungsposition fahren – bis zu zwei Entitäten, die beide erfüllt sein müssen, etwa Anwesenheit *und* Raumtemperatur über 24 °C. Fällt eine Bedingung weg, fährt der Rollladen dorthin zurück, wo er vorher stand, nicht auf „offen". Fensterkontakt und Beschattung haben Vorrang.
- **Frostschutz.** Bei erfüllter Bedingung schließen Rollläden mit hinterlegter Frostposition nur so weit, damit die Lamellen nicht am Rahmen festfrieren. Anders als bei allen übrigen Bedingungen wird hier **nach unten** verglichen: unter dem ersten Wert greift der Schutz, über dem zweiten fällt er wieder weg. Dazu kommt ein dritter Vorhersagesensor, die **Tiefsttemperatur** – der naheliegende Auslöser.

### Behoben
- **Fahrten im Sonnenstand-Modus kamen ein bis zwei Stunden zu spät.** Wer „Runter frühestens 21:00" eingestellt hatte, bei dem fuhr der Rollladen im Sommer erst um 23:00. Home Assistant liefert die Sonnenzeiten in Weltzeit (UTC); Shutter Pilot rechnete sie nicht in die Ortszeit um und legte die eingestellte Uhrzeit deshalb auf die falsche Zeitleiste – aus 21:00 Ortszeit wurde 21:00 UTC. Im Winter war der Versatz eine Stunde, im Sommer zwei. Betroffen war jeder Bereich im Sonnenstand-Modus mit einer Zeitklammer („frühestens" oder „spätestens"); ohne Klammer war alles korrekt. Das galt auch für den Sensor „nächste Fahrt". **Nach dem Update fahren betroffene Bereiche wieder zur eingestellten Zeit** – ohne Zutun.
- **Ein später Sonnenuntergang konnte die Abendfahrt ganz ausfallen lassen.** Derselbe Ursprung: Lag die berechnete Zeit in Weltzeit schon hinter Mitternacht, ordnete Shutter Pilot sie dem falschen Kalendertag zu und fuhr an diesem Tag gar nicht. Betraf vor allem Zeitzonen westlich von Greenwich.
- **Abweichendes Schließen wirkte im Helligkeitsmodus nicht.** Die Teilposition für laue Abende galt bisher nur für Zeit- und Sonnenstand-Bereiche. Jetzt entscheiden beide Pfade gleich.
- **Eine unlesbare Bedingung löste das abweichende Schließen aus.** War der Sensor der Schließbedingung `unavailable` oder `unknown`, galt die Bedingung als erfüllt und die Rollläden schlossen nur teilweise. Ein toter Sensor bedeutet jetzt „Bedingung gilt nicht". Bei den Beschattungsbedingungen bleibt es bewusst umgekehrt: dort darf ein toter Sensor die Rollläden nie oben halten.

### Geändert
- **Das Dashboard zeigt die tatsächliche Fahrzeit.** Bisher stand dort die rohe Sonnenzeit: bei Sonnenaufgang 06:07 und „Hoch frühestens 07:30" hieß es weiterhin „Hoch-Fahrt um 06:07". Zeitklammern und die Streuung der Präsenzsimulation flossen nicht ein – das Panel konnte beides gar nicht berechnen. Die Zeit kommt jetzt aus der Integration selbst und stimmt mit dem überein, was wirklich passiert. Daneben steht, **warum** sie abweicht: „· frühestens 07:30" oder „· Präsenz: +4 min". Die reinen Sonnenauf- und -untergangszeiten bleiben sichtbar, damit der Unterschied erkennbar ist.

> **Nach dem Update den Browser hart neu laden** (Strg+F5 bzw. Cmd+Shift+R), sonst zeigt die Seitenleiste weiter das alte Panel.

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
