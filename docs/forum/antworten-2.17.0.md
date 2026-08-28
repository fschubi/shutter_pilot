# Forum-Antworten zu 2.17.0

Vier Beiträge, drei echte Fehler. Zwei davon hängen zusammen: die Knöpfe im
Dashboard rufen die `cover`-Dienste direkt auf und kommen damit an einem Teil
der Automatik vorbei.

---

## @Linos – Aussperrschutz und Beschattung ausschließen

Hallo Linos,

du hast nichts falsch gemacht – **beides waren Fehler bei mir**, und beide sind
in 2.17.0 behoben.

**1. Der Aussperrschutz galt bei den Dashboard-Knöpfen nicht.** Die
Bereichsknöpfe rufen die `cover`-Dienste direkt auf, damit Home Assistant die
Rechte je Entität prüft (so bleibt das Panel auch für Mitbewohner ohne
Adminrechte bedienbar). Der Aussperrschutz sitzt aber im Backend – und war
damit ausgerechnet an der Stelle wirkungslos, an der man ihn am ehesten
braucht. „Esszimmer rechts" hat `lock_protection` mit Mindesthöhe 100 %; über
den Dienst `shutter_pilot.sun_protect_group` wäre er bei offener Tür gar nicht
gefahren, über den Knopf fuhr er auf 40. Ab 2.17.0 klemmen **Runter,
Sonnenschutz und Lüften** auch im Panel auf die Mindesthöhe.

**2. „Esszimmer rechts" soll gar nicht beschattet werden.** Dafür gibt es jetzt
im Rollladenformular den Haken **„An der Beschattung teilnehmen"** – abwählen,
fertig. Zeitplan, Lüften und Fensterkontakt laufen weiter, er fährt morgens
hoch wie alle anderen. Deine beiden Ideen hätten das nicht sauber gelöst:
Beschattungsposition auf 100 % heißt „beschatte ihn, indem du ihn öffnest"
(und er zählt dann als beschattet, was das automatische Hochfahren blockiert),
und den Bereich ohne Beschattung anzulegen nimmt sie den anderen zwei
Esszimmer-Rollläden mit weg.

Zwei Sachen aus deinem Export nebenbei, die du wahrscheinlich nicht so wolltest:

* Bei **„Esszimmer rechts"** und **„Gäste beide"** sind eigene Werte für
  Sonnenhöhe/Fensterrichtung hinterlegt, aber **„Eigene Ausrichtung" ist aus** –
  es gelten die Bereichswerte (90°–300°). Nach dem Abwählen der Beschattung ist
  das bei „Esszimmer rechts" egal, bei „Gäste beide" nicht.
* Der Bedingungs-Slot **c** (Lichtsensor ≥ 2800 lx) steht in allen fünf
  Bereichen und ist die einzige Bedingung, die gerade nicht erfüllt ist. Das ist
  vermutlich Absicht (abends 53 lx), nur zur Sicherheit erwähnt.

Danke fürs Melden – der erste Punkt war ein echtes Loch.

---

## @Smons – Rollläden fahren morgens nicht hoch

Moin Smons,

**gefunden, und es ist ein Fehler bei mir.** In 2.17.0 behoben.

Alle deine Süd-Rollläden stehen im Export auf `0 %` mit **Quelle: manual**, und
dein Bereich steht auf **Manuelle Übersteuerung: „nie"**. Das bedeutet: eine
von Hand gefahrene Position blockiert das automatische Öffnen bis zum nächsten
Schließen. Gelöscht wurde diese Markierung bisher aber **nur von einer
automatischen Fahrt**. Wer abends selbst zufährt – Wandschalter, eigene
Automation oder der Runter-Knopf im Shutter-Pilot-Dashboard –, bekam damit nie
wieder ein automatisches Auf. Genau das ist bei dir passiert, und es ist der
Grund, warum um 6:38 nichts kam.

Ab 2.17.0 gilt: eine Handposition, die **eine der Schließpositionen dieses
Rollladens** ist (bei dir 0 %), ist keine Übersteuerung, sondern das, was die
Automatik selbst gefahren wäre. Eine Position **dazwischen** – etwa 50 % zum
Abdunkeln – bleibt eine Übersteuerung wie bisher.

Die Uhrzeit selbst stimmte: Sonnenaufgang 06:38 liegt sauber in deinem Fenster
`sun_earliest_up 06:30` / `sun_latest_up 07:00`. Die Rechnung war also richtig,
gefahren ist nur keiner.

Eine Sache, die du trotzdem prüfen solltest, weil sie am selben Morgen
mitgespielt haben kann: Im Bereich **„Süd"** steht `sun_we_earliest_up` auf
**09:00**, und an einem Tag, den `binary_sensor.arbeitstag` als *keinen*
Arbeitstag meldet, gilt genau dieser Wert – dann wäre 06:38 auf 09:00
geschoben worden. Aus dem Export lässt sich der Sensorzustand nicht ablesen;
schau bei Gelegenheit nach, ob er an dem Morgen `on` war. (Am Ergebnis hätte es
nichts geändert – der Merker „manuell" hätte auch um 09:00 blockiert.)

Zwei weitere Kleinigkeiten aus dem Export:

* Ebenfalls in **„Süd"**: eine Wochenend-Obergrenze fehlt und fällt auf
  `sun_latest_up` (07:00) zurück. Die untere Wochenendgrenze 09:00 liegt damit
  **hinter** der oberen; es gewinnt die untere, also 09:00. Falls du am
  Wochenende 09:00 willst, passt das – sonst trag `sun_we_latest_up` mit ein.
* An **„Tina"**, **„Schlafzimmer Tür"**, **„Wohnzimmer Ost"**, **„Gästebad"**,
  **„Gästezimmer"** und **„Küche"** hat der Fensterkontakt keinen Kipp-Zustand.
  Der Kontakt ist damit zweiwertig, und gefahren wird immer
  `position_when_window_tilted` (50 %) – auch bei „offen".
  `position_when_window_open` (100 %) wird nie benutzt. Der Export sagt das
  inzwischen an jedem betroffenen Rollladen.

---

## @c.radi – Bereich Schlafzimmer fährt weder hoch noch runter

Guten Morgen c.radi,

**zwei Fehler bei mir, einer bei dir.** Die beiden Fehler sind in 2.17.0
behoben.

**1. Der „hoch"-Knopf fuhr den deaktivierten Rollladen mit.** Richtig gesehen,
das war falsch. Ein Gruppenknopf im Dashboard ist der Bereich, der handelt –
der Schalter am Rollladen gilt also, und er steht zwei Zeilen über dem Knopf.
Ab 2.17.0 überspringen die Bereichsknöpfe abgeschaltete Rollläden. Die kleinen
Knöpfe **in der Rollladenzeile** fahren ihn weiterhin – genau damit prüfst du
ihn, wenn er repariert ist.

**2. Eine blockierte Richtung fror die andere ein.** Shutter Pilot merkt sich je
Rollladen, ob er „oben" oder „unten" gilt, damit er nicht zweimal am Tag in
dieselbe Richtung fährt. Gepflegt wurde das bisher nur von eigenen Fahrten. In
deinem Export steht „Schlafzimmer rechts" unter *heute schon runtergefahren* –
seit dem letzten Neuladen vor gut zwei Tagen. Blieb das Hochfahren einmal aus,
galt er ab da für immer als unten, und **die Abendfahrt fiel ebenfalls aus**.
Ihn von Hand hochzuziehen half nicht, weil das niemand mitgeschrieben hat. Ab
2.17.0 zählen Fahrten von Hand mit.

**3. Und jetzt der Teil, den ich nicht patchen kann.** Dein Helligkeitssensor
ist `sensor.0_0_aussen_nord_bewegungsmelder_beleuchtungsstarke` – die
Beleuchtungsstärke eines **Bewegungsmelders**. Solche Sensoren melden meist nur
bei Bewegung einen neuen Wert, und der Helligkeitsmodus reagiert auf genau
diese Meldungen. In deinem Hoch-Fenster **06:30–07:00** bewegt sich morgens
draußen an der Nordseite oft niemand, also kommt kein Wert und es fährt nichts.

Zwei Wege:

* **Sauber:** einen Helligkeitssensor nehmen, der zyklisch meldet (ein reiner
  Lux-Sensor, oder ein Template-Sensor, der den Wert regelmäßig fortschreibt).
* **Sofort:** deine Frist „spätestens hoch" nutzen – die hängt am Minutentakt
  und braucht keinen Sensorwert. Sie steht bei dir auf **07:15**, dein
  Hoch-Fenster endet aber um **07:00**. Das ist erlaubt und funktioniert, sieht
  aber verkehrt aus. Wenn du „zwischen 6:30 und 7:00 hoch" willst, setz
  `w_up_to` auf 07:15 oder die Frist auf 07:00.

Für dein zweites Ziel – „abends mit Dämmerung runter" – passt der
Helligkeitsmodus grundsätzlich, aber mit demselben Sensorproblem. Die Frist
„spätestens runter 22:00" hast du ja schon gesetzt, die greift auf jeden Fall.

Und noch ein Haken, den du gesetzt hast und der leicht in Vergessenheit gerät:
im Bereich „Schlafen" steht **„Am Wochenende nicht hochfahren"** auf an. An
jedem Tag, den `binary_sensor.workday_sensor` als freien Tag meldet – also auch
an Feiertagen –, fährt dort morgens **gar nichts** hoch, unabhängig von allem
oben. Runterfahren und Beschattung laufen weiter.

Noch ein Hinweis: die Bereiche **„Arbeiten"** und **„Wohnen"** stehen beide auf
Automatik **aus**. In „Arbeiten" berechnet der Export bei „Arbeitszimmer links"
sogar *„Ergebnis: beschatten"* – gefahren wird trotzdem nichts, weil die
Bereichsautomatik aus ist. Falls das Absicht ist: alles gut.

---

## @pcsv17 – zweite Beschattungsposition

Hi pcsv17,

**beides gibt es ab 2.17.0.**

**Binär geschaltet:** Die **Bedingung** stellst du am Bereich ein (Abschnitt
Sonnenschutz, ganz unten: „Zweite Beschattungsposition"), die **Position** am
Rollladen. Dasselbe Paar wie beim abweichenden Schließen. Als Bedingung geht
alles, was Shutter Pilot sonst auch nimmt: ein `input_boolean`, ein Schalter,
ein Zeitplan, ein Zahlenwert mit Hysterese (z. B. „ab 28 °C, wieder aus unter
25") oder eine Liste von Zuständen. Trifft sie zu, fahren alle Rollläden mit
hinterlegter zweiter Position dorthin – **auch mitten in einer laufenden
Beschattung**, nicht erst beim nächsten Mal.

**Variabel per Entität:** Im Rollladenformular gibt es das Feld
**„Beschattungsposition aus Entität"**. Trag dort ein `input_number`, einen
Template-Sensor oder irgendetwas ein, das eine Zahl von 0 bis 100 liefert. Die
gewinnt über beide festen Positionen und wirkt sofort. Ist der Wert unlesbar
oder außerhalb 0–100, gilt weiter die eingestellte Position – eine Beschattung,
die aussetzt, weil ein Template gerade nichts liefert, wäre der schlechtere
Ausfall.

Beides ist optional; wer nichts einträgt, merkt keinen Unterschied.
