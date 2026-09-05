# Changelog

Alle wichtigen Änderungen an Shutter Pilot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [2.21.6]

Direkte Folge von 2.21.5: die neue Invertier-Checkbox macht eine bestehende
Beschriftungslücke im Einstellungs-Export erreichbar, die vorher nur den
Frost-/Eis-Slot betraf und dort niemandem auffiel.

### Behoben
- **Der Einstellungs-Export beschriftete Schwellen immer als „nicht
  invertiert", unabhängig vom tatsächlichen Wert.** Beim Markisen-/
  Dachfensterschutz stand am Eis-Slot „einfahren ab -2 / frei unter 2" –
  tatsächlich gilt das Gegenteil: Gefahr **unter** -2, frei **ab** 2. Bisher
  betraf das nur Eis (Vorgabe: invertiert, niemand hat es angeschaut). Seit
  eine Invertierung jetzt für Wind, Regen und jede Beschattungsbedingung per
  Checkbox einstellbar ist, hätte dieselbe Beschriftungslücke jeden
  invertierten Slot betroffen. Beide Berichtstabellen (Markisen-/
  Dachfensterschutz und Beschattungsbedingungen eines Bereichs) lesen die
  Invertierung jetzt genauso wie die Auswertung selbst.
- **Ein Schalter oder Binärsensor am Wetterschutz zeigte „einfahren ab – /
  frei unter –"** – eine leere Schwelle, die wie eine vergessene Einstellung
  aussieht. Zeigt jetzt „an = Gefahr" bzw. „aus = Gefahr" (invertiert), genau
  wie die Beschattungsbedingungen das seit 2.14.0 schon für „an = erfüllt" tun.

### Was ändert sich für mich?
Nur die Anzeige im Einstellungs-Export. Ein nicht invertierter Wind-, Regen-
oder Frostsensor sieht unverändert aus.

## [2.21.5]

Keine Forum-Meldung diesmal, sondern ein gezielter Blick auf die drei
unterschiedlichen Antworten, die ein toter oder falscher Sensor je nach
Zusammenhang bekommen muss – Beschattung lässt durch, Schließen/Frost/Lüften
sperrt, Markisen- und Dachfensterschutz nimmt Gefahr an. Beim Nachrechnen
gegen den echten Code kam heraus: zwei dieser drei Antworten waren an
mehreren Stellen leiser vertauscht, als der Code selbst behauptet.

### Behoben
- **Eine halb ausgefüllte Regen- oder Frostschwelle am Markisen-/
  Dachfensterschutz galt als „keine Gefahr" statt als „nicht auswertbar".**
  Eine Entität, die lebt und etwas meldet, aber deren Zahlenschwelle nie
  eingetragen wurde (oder deren Text zu keiner konfigurierten Zustandsliste
  passt), lief bisher durch dieselbe Weiche wie eine tote Sensor-Entität –
  nur dass diese Weiche innen die Beschattungs-Antwort trug: „blockiert
  nicht". Für den Wetterschutz heißt „blockiert nicht" aber „keine Gefahr",
  und eine vergessene Schwelle wurde damit zur dauerhaften, dauerhaft
  unauffälligen Freigabe. Ein vergessener numerischer Schwellenwert am
  Frost-/Eis-Slot lief sogar in die andere, ungefährlichere Richtung –
  dauerhaft „Gefahr", unabhängig von der tatsächlichen Temperatur, mit dem
  bloßen Slotnamen als Grund statt eines erkennbaren Hinweises. Beide
  Richtungen sind jetzt dieselbe, klar benannte: wie ein toter Sensor, mit
  Karenzzeit statt Sofortsperre, und einem Grund, den Panel und Export als
  „Sensor tot" statt als Wetterereignis anzeigen.
- **Eine Invertierung war nur für Zahlen möglich, nie für Schalter oder
  Zustandslisten.** Ein Regenkontakt, dessen „aus" eigentlich „nass"
  bedeutet, oder ein Frostmelder, dessen „an" eigentlich „warm" heißt,
  konnte das nirgendwo eintragen – die Invertierung griff ausschließlich im
  Zahlenzweig. Am gefährlichsten beim Wetterschutz: ein so verdrahteter
  Regenkontakt hätte eine Markise oder ein Dachfenster bei echtem Regen
  lautlos für „trocken" gehalten.
- **Der Invertier-Schlüssel des Markisen-/Dachfensterschutzes wurde beim
  Speichern verworfen**, unabhängig vom Punkt darüber – `resolve_guard_config()`
  kannte ihn nicht in seiner eigenen Schlüsselliste. Gespeichert, im Formular
  sichtbar (nach diesem Update), wirkungslos gewesen wäre er trotzdem.

### Neu
- **Eine Checkbox „Bedeutung umkehren"** an jeder Bedingung mit Schalter oder
  Binärsensor – bei den Beschattungs- und Schließbedingungen eines Bereichs
  ebenso wie am Markisen-/Dachfensterschutz. Frost und Eis behalten ihre
  bisherige Vorgabe (umgekehrt vergleichen), alle anderen Bedingungen starten
  weiterhin unverändert.
- **Der Export warnt jetzt auch bei Regen und Frost vor einer unplausiblen
  Einheit**, genau wie bisher schon beim Wind (m/s neben einer Schwelle, die
  nach km/h aussieht). Eine Regenrate (mm/h) mit einer Schwelle aus dem
  Bereich einer Tagessumme lässt den Schutz kaum greifen; eine Tagessumme mit
  einer Raten-Schwelle verwechselt sperrt dagegen ab dem ersten Tropfen bis
  zum Reset des Sensors. Eine Frostschwelle in °F, aber nach °C gedacht (oder
  umgekehrt), wird so gut wie nie erreicht.

### Was ändert sich für mich?
Ein gewöhnlicher Wind-, Regen- oder Frostsensor mit der natürlichen
Bedeutung (an/hoher Wert = Gefahr) verhält sich unverändert. Wer einen Regen-
oder Frostslot am Schutz konfiguriert, aber die Schwelle nie eingetragen hat,
sieht ab jetzt „Sensor tot" statt einer stillen Dauersperre oder einer
stillen Dauerfreigabe – die Einstellung selbst gehört trotzdem nachgetragen.
Wer einen Sensor hat, dessen „aus" die eigentliche Gefahr bedeutet, kann das
jetzt über die neue Checkbox eintragen; vorher gab es dafür keinen Weg.

## [2.21.4]

Eine Rückmeldung zu 2.21.3, und diesmal war nichts kaputt: **die Beschriftung
sagte „offen", der Fahrweg meint „offen oder gekippt"** – und wer ein gekipptes
Fenster hat, ordnet die beiden Haken seinem Fall gar nicht zu.

### Geändert
- **„Nachholen wenn Fenster offen" heißt jetzt „Nachholen wenn Fenster offen oder gekippt"** (c.radi). Gemeldet als „wenn das Fenster auf gekippt steht, wird der Rollladen gar nicht geschlossen". Genau so ist es gedacht: mit der Nachholfunktion wird die Abendfahrt vorgemerkt und erst beim Schließen des Fensters ausgeführt – bis dahin bleibt der Rollladen stehen. Wer stattdessen die Kipp-Position angefahren haben will, setzt den Haken darunter. Nur hieß der „Bei **offenem** Fenster schon auf die Lüftungsposition fahren", und beide Hinweistexte sprachen ebenfalls nur von „offen". Beschriftungen und Hinweise nennen jetzt beides und sagen, welche Position gefahren wird; in allen elf Sprachen.
- **Der Export erklärt die vorgemerkte Fahrt selbst.** Steht die Nachholfunktion an und der Haken darunter aus, sagt der Bericht am betroffenen Rollladen, dass zur Schließzeit **gar nichts** fährt, solange ein Fenster offen oder gekippt ist – samt der beiden Positionen, die mit dem Haken gefahren würden, und dem Zustand, den der Kontakt gerade meldet. Zweite Meldung dieser Art nach 2.18.0 („im Schlafzimmer hat sich gar nichts bewegt"), und beide Male stand die Antwort in keiner Zeile des Berichts.

### Was ändert sich für mich?
Am Verhalten **nichts** – es ändern sich nur Beschriftungen und der Export.
Wer bisher dachte, ein gekipptes Fenster sei von der Nachholfunktion nicht
betroffen, findet die Einstellung jetzt dort, wo er sie sucht.

## [2.21.3]

Eine Meldung, ein Fehler – und die Zahl im Bericht war der ganze Hinweis:
**der Rollladen parkte auf 74 %, einem Wert, der in keiner Einstellung steht.**

### Behoben
- **Beim Schließen des Fensters blieb der Rollladen auf einer Zwischenstellung stehen** (c.radi). Sein Fenstergriff meldet offen, gekippt und geschlossen; offen und gekippt wurden korrekt angefahren, beim Schließen landete er auf 74 % – weder seine Schließposition (0 %) noch eine der Fensterpositionen (100 % / 15 %). Ursache: beim Schließen fährt der Rollladen auf die Höhe zurück, auf der er **vor** dem Öffnen des Fensters stand, und diese Höhe wurde als Momentaufnahme der gemeldeten Position gemerkt. Wer abends das Fenster öffnet, während die Automatik den Rollladen noch herunterfährt, merkt sich damit eine Zahl mitten aus dem Fahrweg – und fährt später genau dorthin zurück. Gemerkt wird jetzt, wo der Rollladen **steht**: solange er fährt, gilt das Ziel, das die Automatik ihm zuletzt geschickt hat.
- **Dasselbe beim automatischen Lüften.** Der Minutentakt konnte die Abendfahrt mitten im Weg treffen und sich ebenfalls eine Durchgangszahl als Rückfahrhöhe merken.

### Was ändert sich für mich?
Nichts, solange Fenster nur bei stehendem Rollladen bewegt werden. Wer das
Fenster öffnet, während der Rollladen gerade fährt, bekommt beim Schließen
jetzt die Position, auf die die Automatik unterwegs war – bisher blieb er auf
einer zufälligen Zwischenhöhe stehen und rührte sich bis zur nächsten
geplanten Fahrt nicht mehr.

Ein Antrieb, der Home Assistant **nicht** meldet, dass er gerade fährt (kein
`opening` / `closing`), verhält sich unverändert – dort ist von außen nicht zu
erkennen, dass die gemeldete Position nur eine Durchgangszahl ist.

## [2.21.2]

Zwei Rückmeldungen zu 2.21.1, beide berechtigt – und die erste war ein Fehler,
den man nicht sehen konnte: **eine Kipp-Position unterhalb der Mindesthöhe des
Aussperrschutzes wurde nie gefahren.**

### Behoben
- **Der Aussperrschutz klemmte auch bei gekipptem Fenster** (bjoerg). Sein Fenstergriff meldet `open` / `tilted` / `closed`, die Kipp-Position steht auf 30 %, die Mindesthöhe auf 95 % – gefahren wurden immer 95 %. Nachgerechnet: der Zustand wird richtig erkannt und die Kipp-Position richtig bestimmt, und dann klemmt der Schutz sie hoch. Eine Kipp-Position unterhalb der Mindesthöhe war damit **grundsätzlich unerreichbar**: gespeichert, im Formular sichtbar und wirkungslos. Der Aussperrschutz gilt jetzt nur noch bei **ganz geöffnetem** Fenster – durch einen Kippspalt steigt niemand, dort gibt es den Fall nicht, gegen den er schützt. Für zweiwertige Kontakte ändert sich nichts: die melden „offen", nie „gekippt".

### Geändert
- **Der Kopierknopf überträgt jetzt auch die Bereiche** (TanjaHH). Bisher blieben sie außen vor, mit der Begründung, genau die Bereichszuordnung unterscheide zwei sonst gleiche Rollläden. In der Praxis ist es umgekehrt: wer „Einstellungen übernehmen von …" drückt, will einen zweiten Rollladen wie den ersten – und der hängt fast immer an denselben Bereichen. Entität, Name und Fenstersensoren bleiben weiterhin unangetastet, die Geräteart ebenso.

### Was ändert sich für mich?
Wer einen Aussperrschutz **und** eine Kipp-Position unterhalb der Mindesthöhe
eingestellt hat, bekommt ab jetzt die Kipp-Position, die dort steht. Genau das
war die Absicht beim Eintragen – vorher wurde sie stillschweigend überschrieben.

## [2.21.1]

Vier Meldungen an einem Tag, und die erste war ein Fehler von mir aus 2.20.0:
**das Bearbeiten-Formular ließ sich nicht mehr öffnen.**

### Behoben
- **„awning is not defined" beim Bearbeiten oder Anlegen** (Wolf, charly166, TanjaHH, hollizone). Beim Einbau der Dachfenster habe ich eine Variable umbenannt und zwei Verwendungen übersehen. Betroffen war der Block „Einstellungen übernehmen von …" – und den gibt es erst **ab dem zweiten Eintrag derselben Geräteart**. Deshalb ging der erste Rollladen und der zweite nicht, deshalb ging es auf dem einen Gerät und auf dem anderen nicht. Gültige Syntax, also fand `node --check` nichts davon. Das Panel wird jetzt bei jedem Push vollständig durchgerendert – alle Ansichten, alle Formulare, alle Bereichsmodi, ausdrücklich mit mehreren Einträgen je Art.
- **Ein Dachfenster wurde aufgerissen statt geschlossen, wenn die Bedingung wegfiel** (gefunden beim Nachstellen von hollizones Fall). Die Freigabe fuhr auf `position_open` – bei einer Markise heißt das „eingefahren", bei einem Fenster „weit auf". Sobald der Raum abkühlte, stand das Fenster offen. Die Ruhestellung kommt jetzt aus der Geräteart, genau wie beim Schutz.
- **`resume_automation` ließ einen ganz geschlossenen Rollladen stehen** (pcsv17). Der Dienst las „gilt als unten" – ein Merker, der sagt, wohin zuletzt *gefahren* wurde, nicht, wo die Automatik ihn *haben will*. Wer von Hand zufährt, landet darin, und resume zementierte damit genau die Übersteuerung, die es aufheben soll. Jetzt wird die Tageshälfte aus dem Zeitplan abgeleitet: steht als Nächstes eine Abwärtsfahrt an, gehört der Rollladen bis dahin nach oben. In einem Bereich **ohne** Zeitplan wird bewusst keine Endlage erfunden.

### Neu
- **Die Listen sind nach Namen sortiert** (charly166) – Rollläden, Markisen und Dachfenster, mit Umlauten und Zahlen in der richtigen Reihenfolge.
- **Der Export erklärt ein Dachfenster, das nichts tut** (hollizone): kein Bereich, Sonnenschutz im Bereich aus, oder keine Bedingung hinterlegt. Ohne die öffnet ein Dachfenster nie – es fährt in keinem Zeitplan mit.
- **Der Export erkennt einen Kipp-Zustand, den der Kontakt nicht melden kann** (bjoerg). Ein `binary_sensor` kennt nur „an" und „aus". Steht dort trotzdem ein Kipp-Zustand, wird die Kipp-Position nie gefahren – und der Wechsel von offen auf gekippt ist für den Sensor **keine Änderung**, es kommt also kein Ereignis an. Von aussen sieht das aus, als hänge die Abfrage des Fenstergriffs.

## [2.21.0]

pcsv17 im Forum: „Ich möchte tagsüber mein Baby hinlegen. Dafür habe ich mir
einen Schalter gebaut, damit das Rollo auf circa 20 % runterfährt. Wenn ich den
Schalter deaktiviere, fährt das Rollo wieder hoch. Danach macht die Automatik
aber leider nicht mehr weiter."

Erst nachgerechnet, und dabei kam ein Fehler heraus, der nicht in seiner Frage
stand: **die Beschattung merkt nicht, wenn jemand den Rollladen von aussen
wegfährt.**

### Behoben
- **Die Beschattung holte einen von aussen verstellten Rollladen nie zurück.** Solange der Merker „ist beschattet" steht, folgt sie nur einer geänderten *Zielposition* – dass der Rollladen längst woanders steht, weil ihn ein eigener Schalter oder eine eigene Automation gefahren hat, sieht sie nicht. Der Rollladen stand danach offen in der Sonne, und der Merker sagte weiterhin „beschattet". Behoben nicht dadurch, dass die Beschattung ihn eigenmächtig zurückholt – das wäre das Gegenteil dessen, was jemand will, der gerade bewusst abgedunkelt hat –, sondern über den neuen Dienst unten.

### Neu
- **`shutter_pilot.resume_automation` – „Automatik wieder übernehmen".** Genau der Trigger, nach dem pcsv17 gefragt hat: der Dienst löscht die manuelle Übersteuerung, vergisst den Beschattungs-Merker und fährt **sofort** auf die Position, die gerade gilt – die Beschattungshöhe, wenn beschattet werden soll, sonst offen oder geschlossen je nach Tageshälfte. Beide Angaben sind optional: `entity_id` für einzelne Rollläden, `area_id` für einen Bereich, ohne beides gilt er fürs ganze Haus.

  ```yaml
  action: shutter_pilot.resume_automation
  data:
    entity_id: cover.kinderzimmer
  ```

  Bewusst ein Dienst und nichts, was von allein geschieht: nur wer im Raum steht, weiß, wann das Nickerchen vorbei ist. Automatisch ausgelöst würde er den Rollladen eine Minute nach dem Abdunkeln wieder hochziehen.

### Was ändert sich für mich?
Nichts, solange der Dienst nicht aufgerufen wird. Wer eigene Schalter oder
Automationen für einzelne Rollläden gebaut hat, hängt den Dienst ans Ende –
danach macht die Automatik nahtlos weiter, ohne dass „Automatik hat Vorrang"
in den Bereichseinstellungen umgestellt werden muss.

## [2.20.0]

Ein Wunsch aus dem Forum (hollizone): **eine Regensteuerung für Dachfenster,
gerne über eine externe Wetterstation.** Gebaut nicht als zweites Datenmodell,
sondern als dritte Geräteart neben Rollladen und Markise – denn der Schutz, der
eine Markise bei Sturm hereinholt, ist derselbe, der ein Dachfenster bei Regen
zuzieht. Nur die sichere Stellung liegt am anderen Ende.

### Neu
- **Dachfenster als eigene Geräteart**, mit eigenem Tab neben den Markisen. Ein Dachfenster fährt in keinem Zeitplan mit: geöffnet wird es über die Bedingungen seines Bereichs – üblich ist die Innentemperatur, „über 24 °C kippen, unter 22 °C wieder zu" –, geschlossen über den Schutz. Drei Stellungen: **geschlossen** (die sichere, dorthin fährt der Schutz), **Lüftungsstellung** (so weit öffnet es, solange die Bedingungen gelten) und **ganz offen** (nur für den Knopf von Hand). Fensterkontakt, Aussperrschutz, Lamellen und Nachholfahrt gibt es dort nicht – der Cover *ist* das Fenster.
- **Regen-, Wind- und Frostschutz für Dachfenster.** Dieselben drei Sensoren wie bei den Markisen und dieselbe Mechanik: Binärsensor, Zahlenwert mit Ein- und Ausschaltschwelle oder Zustandsliste, dazu eine Sperrzeit je Sensor. Nach dem letzten Tropfen bleibt das Fenster die eingestellte Zeit zu und öffnet erst danach wieder – sofern die Bedingung noch gilt. Ein Sensor, der nichts mehr meldet, sperrt sofort und schließt nach einer Karenz: an einem Fenster heißt „ich weiß es nicht" zu.
- **Ein bestehender Rollladen lässt sich übernehmen.** Trägt schon ein Eintrag dieselbe Cover-Entität, bietet das Formular an, ihn als Dachfenster zu übernehmen – und räumt dabei die Schlüssel weg, die dort nichts bedeuten.
- **`sensor.shutter_pilot_status` zählt Dachfenster getrennt** (`windows_open`, `windows_closed`, `windows_unknown`). Ein gekipptes Dachfenster macht das Haus nicht „offen", genauso wenig wie eine eingefahrene Markise es „zu" macht.

### Geändert
- **Die Geräteart wird jetzt positiv gefragt.** Der Zeitplan-Filter hieß „alles außer Markisen" – und hätte ein Dachfenster stillschweigend mitgenommen, abends zugefahren und vom Fensterkontakt behandelt. Was aufgezählt gehört, sind die Teilnehmer, nicht die Ausnahmen. Für bestehende Anlagen ändert sich dadurch nichts: ein fehlender Schlüssel ist weiterhin ein Rollladen, es gibt keine Migration.

> ⚠️ **Ein Hinweis, der zur Sache gehört:** Zwischen dem ersten Tropfen und dem
> geschlossenen Fenster liegen die Wetterstation, Home Assistant und die
> Laufzeit des Motors. Bei einem plötzlichen Schauer ist Wasser im Raum, bevor
> das Fenster zu ist. Ein Regensensor **am Fenster selbst** – Velux und Roto
> haben so etwas – schließt ohne diese Kette. Shutter Pilot ist der Komfort
> obendrauf, nicht der Ersatz dafür. Derselbe Hinweis steht im Formular.

## [2.19.0]

Ein Beitrag, zwei Funde – und der eine erklärt eine Beobachtung, für die es
bisher keine Erklärung gab: **ein leer gelassenes Schwellenfeld wurde als 0
gespeichert.** „Leer" heißt laut dem Hinweis darunter „gleicher Wert wie
Beschatten ab"; 0 heißt an einem Helligkeits-, Strahlungs- oder Windsensor
etwas völlig anderes, nämlich „nie wieder aufheben".

### Behoben
- **Ein geleertes Zahlenfeld wurde zu 0** (bjoerg). „Während eines Gewitters fiel die Helligkeit auf rund 6000 lx, die Beschattung blieb trotzdem unten. Beim zweiten Wert habe ich nichts eingetragen." Beides stimmte: der Feld-Helfer des Panels machte aus einer leeren Eingabe `Number("")` – und das ist 0, nicht „leer". Damit stand als Aufhebepunkt eine echte Schwelle, die ein Lux-Sensor nie unterschreitet: einmal ausgelöst, blieb die Bedingung bis zum nächsten Neustart erfüllt. Betroffen waren **alle** Schwellenpaare, die auch leer bleiben dürfen – die vier Beschattungsbedingungen, abweichendes Schließen, Frost, Lüften, „nicht hochfahren" und der Markisenschutz. Beim Wind war es am schärfsten: „Einfahren ab 0" heißt, dass die Markise gar nicht mehr ausfährt. Leere Felder bleiben jetzt leer.
- **Der Export benennt einen bereits gespeicherten Aufhebepunkt bei 0.** Die Reparatur oben verhindert nur neue Fälle; wer den Wert schon in der Konfiguration stehen hat, merkt sonst nichts davon. In der Bedingungstabelle steht dafür jetzt ein Hinweis samt der Zahl, die stattdessen gemeint war.
- **Gelöschte Bereiche und Rollläden ließen ihre Entitäten stehen** (bjoerg, gemeldet über Spook: „Nicht existierende Entität registriert von: Shutter Pilot"). `delete_shutter` räumte im Entitätsregister gar nichts auf, `delete_area` nur den Automatik-Schalter – der Sonnenschutz-Schalter, der Sensor „nächste Fahrt" und der Binärsensor „Sonnenschutz aktiv" blieben zurück. Das ist nicht nur unordentlich: die entity_id bleibt belegt, ein wieder angelegter Rollladen bekommt deshalb `..._2`, und die Konfiguration zeigt weiter auf die alte. Beide Befehle räumen jetzt vollständig auf.

### Unverändert, aber der Vollständigkeit halber
- **Ein Regensensor, der „nass"/„trocken" anzeigt, braucht kein Textfeld.** Das ist ein `binary_sensor` mit `device_class: moisture`; sein Zustand *ist* `on`/`off`, „Nass"/„Trocken" ist nur die Anzeige von Home Assistant. Das Formular zeigt dort zu Recht den Hinweis „‚on' gilt als Gefahr" statt einer Zustandsliste. Die Zustandsliste aus 2.18.0 ist für Sensoren gedacht, deren Zustand wirklich ein Wort ist.
- **„Manuelle Position" steht im Bereichsformular unter „Kalender & manuelle Bedienung"**, nicht unter „Grunddaten". Die Angabe im Forum war falsch, das Feld ist da.

## [2.18.0]

Vier Beiträge, und drei davon beschreiben dieselbe Stelle: **der Fensterkontakt
erreichte nur den (nahezu) geschlossenen Rollladen.** Die Prüfung dahinter war
richtungsblind – sie soll verhindern, dass ein offenes Fenster mittags einen
offenen Rollladen herunterzieht, sperrte damit aber auch den Aussperrschutz
aus. Und der ist auf diesem Weg das Einzige, was überhaupt nach *oben* fährt.

### Behoben
- **Der Aussperrschutz griff nicht, wenn der Rollladen halb offen stand** (pcsv17, in Wolfs Export ebenso). „Das Rollo fährt nur in diese Position, wenn es vorher ganz geschlossen war. Wurde es manuell auf z. B. 45 % gefahren und ich öffne dann die Tür, passiert nichts." Genau so war es. Die Prüfung fragt jetzt zusätzlich, in welche **Richtung** die Fahrt ginge: würde sie den Rollladen öffnen – und mehr macht der Aussperrschutz nicht –, wird gefahren, egal wo er steht. Ihr eigentlicher Zweck bleibt: ohne Aussperrschutz zieht ein offenes Fenster einen offenen Rollladen weiterhin nicht herunter.
- **Die Kontrollkästchen im Formular sahen aus wie Eingabefelder** (bjoerg). „Bei einigen Anhaak-Kästchen ist es ein wenig schwierig die Zugehörigkeit zu erkennen." Das war kein Geschmacksurteil, sondern eine Regel zu viel: `width:100%` galt samt Rahmen und Polsterung auch für Kontrollkästchen, aus dem Haken wurde ein formularbreiter Kasten, das Häkchen stand mittig darin und die Beschriftung rutschte in die Zeile darunter. Haken und Text stehen jetzt nebeneinander, und zwischen den Einstellungen liegt eine feine Trennlinie – genau das Gewünschte.
- **Ein Schutzsensor mit Textzuständen sperrte die Markise dauerhaft** (bjoerg). „Mein Regensensor liefert nur ‚nass' und ‚trocken'." Das Formular bot dafür nur Zahlenfelder an, und im Markisenschutz gilt ein Wert, der sich nicht mit der Schwelle vergleichen lässt, als **Gefahr** – die Markise fährt ein und nie wieder aus, während daneben eine Schwelle steht, die so aussieht, als würde sie geprüft. Die Zustandsliste, die es bei den Beschattungsbedingungen längst gibt, steht jetzt auch hier; der Export benennt den Fall zusätzlich.
- **Die festgestellten Reiter blieben auf manchen Android-Tablets nicht stehen** (Wolf). Der Rückfall `overflow-x:hidden` macht das Panel selbst zum Scrollbereich, und ein „sticky" Element darin klebt an nichts. Auf Browsern, die `overflow:clip` kennen, fiel das nicht auf – auf älteren WebViews schon, und deshalb funktionierte dasselbe Panel auf dem Telefon und auf dem Tablet nicht. Der Rückfall ist weg; breite Inhalte scrollen ohnehin in ihrem eigenen Rahmen.
- **Das Lux-Zahlenfeld ließ sich auf dem Tablet nicht ändern** (Wolf). Das Feld zeichnete sich bei jedem Tastendruck neu; auf manchen Android-WebViews springt dabei der Cursor oder das Zeichen geht verloren. Der Wert wird weiterhin bei jedem Tastendruck übernommen, neu gezeichnet wird erst beim Verlassen des Feldes.

### Neu
- **Ein Block für alle Bereiche oben im Dashboard** (Smons, Linos). Alle Rollläden hoch, Stop, runter, Sonnenschutz und Lüften mit einem Klick; Automatik und Beschattung für alle Bereiche an oder aus; und die Werte, die man sonst je Bereich nachschlägt: Sonnenauf- und -untergang, aktuelle Elevation und Azimut, Höchsttemperatur und Wetterlage von heute.
- **`area_id` ist bei allen Gruppen-Diensten optional** (Smons, Linos – „für das HA-Dashboard"). Ohne Bereich gilt der Dienst für alle Bereiche, „alle Rollläden hoch" ist damit **ein** Aufruf statt einer je Bereich. Dazu neu: `shutter_pilot.stop_group`.
- **`sensor.shutter_pilot_status`** (Linos). Der Primärstatus als Zustand – `open`, `closed` oder `partial` –, alles Weitere als Attribute: die Zahlen je Gruppe und, als Sekundärstatus, `shading_active` und `shading_areas` mit den Namen der gerade beschatteten Bereiche. Markisen zählen getrennt: eine eingefahrene Markise ist in Ruhe, nicht „das Haus ist zu".
- **„Bei offenem Fenster schon auf die Lüftungsposition fahren"** (bjoerg). „Müsste dann aber nicht die Jalousie auf die Position für ‚gekippt' fahren? Im Schlafzimmer hat sich gar nichts bewegt." Richtig – bisher blieb der Rollladen mit vorgemerkter Nachholfahrt einfach stehen. Der neue Haken je Rollladen fährt ihn so weit, wie es der Aussperrschutz zulässt; die volle Fahrt bleibt vorgemerkt und läuft, sobald das Fenster zugeht. **Vorgabe aus.**
- **„My"-Position für Antriebe ohne Positionierung** (Wolf). Somfy RTS und Verwandte kennen eine dritte, am Motor angelernte Stellung; Overkiz bietet sie als `button.<markise>_my_position` an. Entität eintragen und angeben, welchem Prozentwert sie entspricht – jede Fahrt, die höchstens 15 % daneben liegt, drückt dann diesen Knopf. Erst damit bedeutet „Ausfahrlänge nach Sonnenhöhe" an so einem Antrieb überhaupt etwas: ohne sie wird aus jedem Wert ab 50 % „ganz ausfahren".
- **Der Export nennt das Fahrkommando** (bjoerg). „An der Fahrtrichtung ändert es nichts." Aus den Positionen allein ist das nicht zu beantworten: an einem Antrieb ohne Positionierung sendet Shutter Pilot keine Zahl, sondern `open_cover` oder `close_cover` – und welches der beiden „ausfahren" heißt, entscheidet die Verdrahtung. Der Bericht schreibt beide Kommandos samt Position hin, und warnt, wenn die Sonnennachführung an einem Antrieb läuft, der keine Zwischenstellung anfahren kann.

## [2.17.0]

Vier Forumsbeiträge an einem Tag. Drei davon waren Fehler – und zwei davon
hängen zusammen: **die Knöpfe im Dashboard fahren an der halben Automatik
vorbei**, weil sie die `cover`-Dienste direkt aufrufen.

### Behoben
- **Der Aussperrschutz galt bei den Dashboard-Knöpfen nicht** (Linos). „Ich habe den Button „Sonnenschutz" betätigt und es sind alle Rollläden gefahren, auch der mit Aussperrschutz." Genau so war es: `close_group` und `sun_protect_group` klemmen die Zielposition seit jeher, die Knöpfe im Panel aber rufen die `cover`-Dienste direkt auf – damit Home Assistant die Rechte je Entität prüft und das Panel auch für Nicht-Admins bedienbar bleibt (2.7.1). Der Aussperrschutz war damit an genau der Stelle wirkungslos, an der man ihn am ehesten auslöst: mit offener Terrassentür daneben. Jetzt klemmen **Runter, Sonnenschutz und Lüften** auch dort auf die Mindesthöhe. Zweite Stelle für dieselbe Regel, aus demselben Grund wie beim Markisenschutz – die Alternative wäre ein Loch in der Rechteprüfung.
- **Die Gruppenknöpfe eines Bereichs fuhren abgeschaltete Rollläden mit** (Linos, c.radi). „Betätige ich den ‚hoch'-Button werden beide Rolläden bedient, obwohl der linke deaktiviert ist. Der ist aktuell defekt." Ein Gruppenknopf ist der Bereich, der handelt – der Schalter am Rollladen gilt also, und er steht zwei Zeilen über dem Knopf. **Die Knöpfe in der Rollladenzeile fahren ihn weiterhin**: genau damit prüft man ihn nach der Reparatur. Die Dienste `open_group`/`close_group` bleiben ebenfalls unverändert, sie sind der Weg „von Hand".
- **Von Hand zufahren sperrte das automatische Hochfahren – dauerhaft** (Smons). Wer abends selbst schließt (Wandschalter, eigene Automation, der Runter-Knopf im Dashboard), erzeugt eine Position mit der Quelle „manuell". Bei der Übersteuerungs-Einstellung „nie" blockiert die das Öffnen bis zum nächsten Schließen – und gelöscht wurde der Merker nur von einer *automatischen* Fahrt. Wer immer von Hand schloss, bekam also nie wieder ein automatisches Auf. Jetzt gilt: eine Handposition, die **eine der Schließpositionen dieses Rollladens** ist, ist keine Übersteuerung, sondern das, was die Automatik selbst gefahren wäre. Eine Position dazwischen bleibt eine Übersteuerung wie bisher.
- **Eine blockierte Fahrtrichtung fror die andere ein** (c.radi). „Der Bereich fährt weder hoch noch runter." Die Merker „gilt als oben/unten" hielten einen Rollladen von der nächsten Fahrt in dieselbe Richtung ab und wurden bisher nur von eigenen Fahrten gepflegt. Blieb das morgendliche Hochfahren einmal aus, galt der Rollladen für immer als „unten" – und die Abendfahrt fiel ab da ebenfalls aus, auch wenn man ihn zwischendurch von Hand hochzog. Fahrten von Hand werden jetzt mitgeschrieben, aber nur an den beiden Enden: eine Position dazwischen sagt nichts darüber, in welcher Tageshälfte der Rollladen steht.
- **Lüften kannte den Aussperrschutz nicht.** `ventilate_group` fährt nach unten wie jedes Schließen, klemmte die Position aber als einziger Fahrweg nicht.
- **Der Dateiname des Exports stand in UTC**, der Kopf des Berichts in Ortszeit. Zwei Stunden Unterschied – beim Vergleich zweier Exporte sah der neuere nach dem älteren aus.

### Neu
- **Zweite Beschattungsposition** (pcsv17). „Wäre es möglich, eine 2. Beschattungsposition anzulegen, die binär aktiviert wird, oder die eine Beschattungsposition variabel per Entität zu verändern?" Beides. Die **Bedingung** steht am Bereich, die **Position** am Rollladen – dasselbe Paar wie beim abweichenden Schließen, und dieselbe Bedingungsmechanik: Schalter, Helfer, Zeitplan, Zahlenwert mit Hysterese oder Zustandsliste. Sie greift **sofort**, auch mitten in einer laufenden Beschattung. Stufenlos geht über eine **Entität** (`input_number`, Template-Sensor, alles was 0–100 liefert); die gewinnt über beide festen Positionen. Ein unlesbarer Wert lässt die eingestellte Position gelten – eine Beschattung, die wegen eines Templates aussetzt, wäre der schlechtere Ausfall.
- **Einen Rollladen von der Beschattung ausnehmen** (Linos). „Wie schließe ich den Rollladen generell aus dem Beschatten aus?" Bisher nur über den Automatik-Schalter – und der hält auch das Öffnen am Morgen an. Der neue Haken **„An der Beschattung teilnehmen"** nimmt nur die Beschattung heraus; Zeitplan, Lüften und Fensterkontakt laufen weiter. Wer ihn abwählt, während der Rollladen gerade beschattet ist, bekommt ihn freigegeben statt eingefroren.
- **Der Export beantwortet „warum fährt er morgens nicht hoch"**. Bisher stand dort nichts dazu: jede Sperre auf diesem Weg ist lautlos und hinterlässt keinen Merker – zu sehen war nur, dass nichts gefahren ist, und das ist das Symptom. Der Bericht nennt jetzt je Rollladen den Hauptschalter, die Bereichs- und Rollladenautomatik, die Wochenend- und „nicht hochfahren"-Sperre und eine blockierende Handposition **samt ihrem Wert**.
- Der Export nennt außerdem die **gerade geltende Beschattungsposition** und woher sie kommt (feste Position, zweite Position, Entität) – und warnt, wenn eine zweite Position hinterlegt ist, für die es im Bereich keine Bedingung gibt.

### Geändert
- Die Merker im Export heißen jetzt **„gilt als oben"** und **„gilt als unten"**. Sie hießen „heute schon hoch-/runtergefahren", und das stimmte schon vorher nicht ganz – sie überleben den Tageswechsel und werden seit dieser Version auch von Fahrten von Hand gesetzt.

## [2.16.0]

Zwei Forumsbeiträge, vier Wünsche – und ein Fund in Wolfs Export, nach dem
niemand gefragt hatte.

### Neu
- **Vierter Betriebsmodus: „Kein Zeitplan"** (malleYay). „Ich würde Shutter Pilot gerne nur für den Sonnenschutz verwenden – gibt es eine Möglichkeit, keinen der 3 Steuerungsmodi zu verwenden?" Bisher nicht: die Bereichsautomatik auszuschalten nimmt die Beschattung mit, und ein Bereich ohne gewählten Modus fällt auf „Zeit" zurück und fährt um 07:00 und 19:00. Der neue Modus fährt weder nach Uhr noch nach Lux oder Sonnenstand – **Sonnenschutz und Lüften laufen weiter**. Wichtig dabei: **am Ende des Beschattungstags wird immer geöffnet**, ohne dass man den Haken aus 2.15.0 setzen müsste. Ohne Zeitplan gibt es keine Abendfahrt, die den Rollladen von der Beschattungshöhe holt – er stünde sonst für immer dort. Derselbe Modus ist auch die richtige Wahl für Bereiche, in denen nur Markisen hängen: Scheduler und Helligkeitsmodus filtern Markisen ohnehin aus, die Lux-Schwellen dort waren immer schon wirkungslos.
- **Die Tab-Leiste bleibt beim Scrollen oben stehen** (Wolf). Für jeden Wechsel zwischen Dashboard, Bereichen und Einstellungen musste man vorher erst wieder ganz nach oben.
- **Lux-Schwellen ohne Deckel** (Wolf). „Mir sind die 1000 Lux als Schwelle zum Hochfahren zu niedrig." Der Schieber endete bei 1000 – für einen Außensensor, der im Sommer Zehntausende Lux meldet, um zwei Zehnerpotenzen zu wenig. Neben dem Schieber steht jetzt ein Zahlenfeld, das jeden Wert nimmt; der Schieber deckt weiterhin den Feinbereich ab.

### Behoben
- **Shutter-Pilot-eigene Schalter und Sensoren standen in *jedem* Auswahlfeld ganz oben** – auch dort, wo sie nie hingehören. Das Vorziehen war für die Bedingungsfelder gebaut (dort ist es richtig und gewollt), galt aber für Wind-, Regen-, Frost-, Helligkeits-, Temperatur- und Sondertage-Sensor genauso. Zwei Anlagen sind dadurch schon in eine Rückkopplung gelaufen: ein Auto-Schalter als Windsensor (meldet dauerhaft „an", also dauerhaft Sturm, also fährt die Markise nie wieder aus) und der eigene Sonnenschutz-Sensor als Sondertage-Sensor (kippt mitten am Tag zwischen Wochentags- und Wochenendzeiten). In Messfeldern stehen sie jetzt nicht mehr vorne, und wer dort einen einträgt, bekommt eine Warnung unter dem Feld. Vorhersage-Sensoren sind ausgenommen: die kommen von der Wetter-Entität, nicht aus einer Entscheidung dieser Integration.

### Geändert
- **Das Bereichsformular zeigt ohne Zeitplan nur noch, was wirkt.** Zeitplan- und Kalenderabschnitt sind dann weg, die Abschnitte für abweichendes Schließen, Frost, „nicht hochfahren" und die Licht-Folgeaktion tragen einen Hinweis: sie hängen alle an einer Fahrt nach oben oder unten, die es dort nicht gibt. Gespeicherte Werte bleiben unangetastet und gelten wieder, sobald ein Modus gewählt ist.
- **Der Export benennt Bereiche ohne Zeitplan** – und warnt, wenn dort auch der Sonnenschutz aus ist: dann fährt der Bereich gar nichts, und jede einzelne Einstellung sieht für sich plausibel aus.

## [2.15.0]

Zwei Wochen Forum in einem Zug: vier Fehler und vier Wünsche, dazu drei
Antworten, für die es keinen Code brauchte.

### Neu
- **Sonnenschutz je Bereich abschaltbar** (MartyBr). Ein eigener Schalter `switch.shutter_pilot_sonnenschutz_<Bereich>`, dazu ein Schalter auf der Dashboard-Karte. Bewusst getrennt vom Automatik-Schalter: 35 °C heute und 20 °C morgen ist ein Grund, die Beschattung zu lassen – kein Grund, die Rollläden morgens unten zu lassen. Bisher blieb dafür nur der Beschattungszeitraum in Monaten, und ein Monat ist für einen Wetterumschwung viel zu grob. **Abschalten gibt frei, was gerade beschattet ist** – wer wegen kühlerem Wetter ausschaltet, will nicht bis zum Abend auf halber Höhe sitzen.
- **Am Wochenende gar nicht hochfahren** (c.radi, Linos, hollsten). Ein Haken je Bereich. Er hängt am selben Wochenendbegriff wie alles andere: **ist ein Sondertage-Sensor eingetragen, entscheidet der** – damit gilt der Haken auch für Feiertage, Ferien und Schichtdienst. Wer samstags arbeitet und nur sonntags ausschlafen will, trägt einen Workday-Sensor mit `excludes: [sun]` ein; dann ist Sonnabend ein Arbeitstag. Nur das Hochfahren ist betroffen, Runterfahren und Beschattung laufen weiter.
- **Bedingung „nicht hochfahren"** (Vorschlag von Linos). Ein Bedingungs-Slot je Bereich, gebaut wie alle anderen: an/aus-Helfer, Zeitplan-Helfer, Auswahlliste oder Zahl mit Hysterese. Solange sie zutrifft, bleiben die Rollläden morgens unten – Ferien, Urlaub, Feiertag, Homeoffice, was immer der eigene Helfer weiß. **Ein nicht lesbarer Sensor blockiert nicht**: andersherum bliebe jeder Rollladen unten, bis es jemand merkt.
- **Nur beschatten, was schon offen ist** (charly166, Linos). Beschatten und Öffnen ist derselbe Fahrbefehl mit einer anderen Zahl – ein nachts geschlossener Rollladen wurde von der Beschattung deshalb **hochgefahren**, auf die Beschattungshöhe. Angehakt bleibt er unten, bis er regulär geöffnet hat. Vorgabe aus, damit sich für niemanden ungefragt etwas ändert.
- **Am Ende des Beschattungstags wieder öffnen** (bjoerg). Sinkt die Sonne unter den eingestellten Bereich, blieb der Rollladen bisher auf Beschattungshöhe stehen, bis der Abendplan ihn schließt. Im Sonnenmodus sind das Minuten – im Helligkeits- und Zeitmodus können es Stunden sein, und genau das wurde als „der Sonnenschutz wird nie zurückgesetzt" gemeldet. Angehakt fährt er stattdessen sofort auf. Vorgabe aus.
- **Zweiter Fensterkontakt je Rollladen** (Thsu). Für Doppelflügelfenster mit einem Kontakt pro Flügel. Beide werden zusammen gelesen: das Fenster gilt als offen, sobald einer der beiden es meldet – damit greifen Aussperrschutz, Lüftungsposition und das Nachholen der Fahrt auch dann, wenn nur der zweite Flügel offen steht.

### Behoben
- **Die Markisenschutz-Einstellungen standen nach dem Speichern wieder leer im Formular** (bjoerg, charly166). Gespeichert und angewendet waren sie – der Export zeigte sie ja –, zurückgeschickt wurden sie nie: das Panel bekam nur sechs fest verdrahtete Schlüssel. Wer eine Windschwelle korrigieren wollte, musste raten, was drinsteht. Jetzt kommt alles zurück, was gespeichert ist. **Das ist auch die Ursache hinter einem zweiten Bericht**: eine Markise, die „nie ausfährt", weil beim Neueintragen versehentlich ein Shutter-Pilot-eigener Schalter als Windsensor stand – der meldet dauerhaft „on", also gilt dauerhaft Sturm. Der Export benennt das jetzt ausdrücklich.
- **Der Hinweis zur Sperrzeit stand bei Wind, Regen und Frost derselbe da** (bjoerg). Bei Frost beschrieb der Satz über die Bö sogar das Gegenteil dessen, was die Sperrzeit dort tut. Jetzt drei eigene Texte, in allen elf Sprachen.
- **Der Export widersprach sich in der Zeile „Fensterrichtung"** (in bjoergs Bericht aufgefallen). Sie las die Geometrieprüfung *insgesamt* – also Höhe **und** Richtung. Bei tiefstehender Sonne stand deshalb ein ❌ an einer Richtung, die passte, und der Wert in derselben Klammer sagte das Gegenteil. Die Zeile prüft jetzt nur noch, was sie behauptet.
- **Das Anlegen des neuen Bereichsschalters hätte einen zusätzlichen Neuladen des Config-Entrys während des Starts ausgelöst.** Beim Testen fiel auf, dass der mitten in die erste Beschattungsauswertung fallen kann. Der Schalter schreibt sich deshalb als einziger nicht in die Optionen zurück – gebraucht wird die ID nur im laufenden Prozess.

### Geändert
- **Der Export nennt, warum heute nicht hochgefahren wird** – Wochenende, Sondertag oder Bedingung. Beide Sperren wirken sonst lautlos und hinterlassen keine Spur in den Merkern; da stünde nur, dass nichts gefahren ist.
- **Der Export zeigt den Zustand des Sonnenschutz-Schalters** in der Bereichszeile, getrennt von „nicht eingerichtet".

### Ohne Codeänderung beantwortet
- **Beschattung erst, wenn die Dachfenster zu sind** (hollizone): Das kann die Integration seit 2.6.0. Am Rollladen einen Fensterkontakt eintragen und **„Fahrt nach dem Schließen nachholen"** anhaken – die Beschattung ist einer der Fahrwege, die das benutzen. Steht dann ein Fenster offen, wird die Beschattungsfahrt vorgemerkt und läuft, sobald geschlossen wird. Drei Tests halten das jetzt fest, damit es nicht bei einer Behauptung bleibt.
- **Sonnabend und Sonntag getrennt** (hollsten): Der Sondertage-Sensor kann das. Ein Workday-Sensor mit `excludes: [sun]` macht Sonnabend zum Arbeitstag – dann gelten samstags die Wochentagszeiten und nur sonntags die Wochenendzeiten. Der neue Wochenend-Haken oben richtet sich nach demselben Sensor.
- **Rollläden, die überhaupt nicht automatisch fahren sollen** (DocSpiders Hausmodus, wieder aufgetaucht): dafür gibt es seit 2.5.0 den Auto-Schalter je Rollladen.

## [2.14.0]

Aus dem Forum (DocSpider): „Hausmodus", „Kino Modus" und „Reinigungsdienst"
liegen bei ihm als Helfer vor – und ließen sich als Bedingung nicht auswählen.

### Behoben
- **Helfer waren als Bedingung nicht auswählbar – und wurden, wenn doch eingetragen, stillschweigend ignoriert.** Die Auswahl bot nur `binary_sensor`, `sensor` und `weather` an. Ein `input_boolean` fiel im Hintergrund zusätzlich in den Zahlen-Zweig, ließ sich nicht als Zahl lesen und galt damit als **erfüllt** – die schlechtestmögliche Antwort: beschattet wurde ausgerechnet durch den Zustand hindurch, der es verhindern sollte. Ein an/aus-Helfer wird jetzt wie ein Binärsensor gelesen (`input_boolean`, `switch`, `schedule`), und das gilt für alle Bedingungsfelder – Beschattung, Abweichendes Schließen, Frost, Lüften und den Markisenschutz.

### Neu
- **Helfer stehen in jedem Bedingungsfeld zur Auswahl**: Schalter (`input_boolean`), Auswahl (`input_select`), Zahl (`input_number`), dazu `switch`, `number` und `schedule`. Damit lassen sich Haus-, Anwesenheits- oder Kinomodus ohne einen einzigen Template-Sensor als Bedingung nutzen.
- **Ein Auswahl-Helfer bietet seine eigenen Möglichkeiten als Knöpfe an.** Bisher zeigte das Formular nur den gerade gemeldeten Zustand, alles andere musste man abtippen – und „Urlaub" gegen „urlaub" ging dabei daneben. Jetzt stehen alle hinterlegten Optionen da; ausgewählt werden dürfen mehrere („Urlaub **oder** Abwesend").
- **Der Export zeigt bei einem an/aus-Helfer „an = erfüllt"** statt „ab – / auf unter –". Der Strich las sich wie eine vergessene Schwelle.

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
