# Forum-Antworten zu 2.15.0

Ein Block je Person, zum einzelnen Einstellen. Reihenfolge wie im Thread.

---

## An bjoerg

Hallo bjoerg,

danke für den ausführlichen Bericht **und** den Export – ohne den hätte ich zwei
der Punkte nicht gefunden. Der Reihe nach, und einen davon hast du mir
tatsächlich ausgegraben, ohne es zu merken.

### 🔴 Der wichtigste Punkt zuerst: dein Windsensor

In deinem Export steht:

```
| wind | switch.shutter_pilot_auto_balkon | on | einfahren ab 4 / frei unter 3 | ⛔ wind |
Ergebnis: gesperrt · Grund: wind
```

Da steht **ein Schalter von Shutter Pilot selbst** als Windsensor. Der meldet
dauerhaft `on` – für den Schutz heißt das: **dauerhaft Sturm**. Deine Markise
ist damit permanent gesperrt und wird permanent eingefahren. Sie kann gar nicht
funktionieren, egal wie du die Schieberegler stellst.

Und ich weiß jetzt auch, wie das passiert ist – siehe den nächsten Punkt.

**Zu tun:** Einstellungen → Wind- und Regenschutz → als Windsensor deinen
echten Sensor eintragen (bei dir vermutlich etwas wie
`sensor.wetterstation_windspeed`). Achte dabei auf die **Einheit**: misst er in
m/s, sind 25 km/h ungefähr **7 m/s**, nicht 25.

Bei Regen würde ich die Einfahrschwelle von `1` auf **`0.2`** setzen – 1 mm/h
erreicht Nieselregen nie, die Markise bliebe dann im Regen draußen.

### 🐞 „Die eingetragenen Entitäten verschwinden beim Speichern"

**Das war ein echter Fehler, und er ist behoben.** Gespeichert und angewendet
waren deine Werte – der Export hat sie ja gezeigt –, aber das Panel hat sie nie
zurückbekommen: es holte sich nur sechs fest verdrahtete Einstellungen vom
Server, der Markisenschutz war nicht dabei.

Wer in ein leeres Formular tippt, tippt irgendwas hinein – genau so ist der
Auto-Schalter als Windsensor dort gelandet. Ab 2.15.0 steht wieder da, was
gespeichert ist.

### 🐞 Der Sperrzeit-Hinweis stand überall gleich

Auch das war ein Fehler, kein bloßer Textdreher: Bei **Frost** beschreibt der
Satz über die Bö sogar das Gegenteil dessen, was die Sperrzeit dort tut (die
steht standardmäßig auf 0, weil Frost nicht böig kommt). Jetzt hat jeder der
drei Schutztypen seinen eigenen Text, in allen elf Sprachen.

### 🐞 „Der Sonnenschutz wird nicht zurückgesetzt"

Du hast recht, und die Ursache ist erklärbar: Sinkt die Sonne unter deine
Untergrenze (bei dir 4°), hat Shutter Pilot bisher nur den Merker gelöscht und
**nicht gefahren** – in der Annahme, dass gleich der Abendplan kommt.

Im Sonnenmodus stimmt das. Du bist im **Helligkeitsmodus** mit `lux_down 199` –
da wartet er auf einen Lux-Wert, und das können Stunden sein. Genau das hast du
beobachtet: *„Erst wie sie dann ganz zu gefahren sind."*

**Neu in 2.15.0:** Haken *„Am Ende des Beschattungstags wieder öffnen"* im
Sonnenschutz-Block des Bereichs. Vorgabe aus, damit sich für niemanden
ungefragt etwas ändert – bei dir bitte anhaken.

### ❓ „Was ist der Unterschied bei den beiden Positionen?"

Die obere gilt bei **offenem** Fenster, die untere bei **gekipptem**. Der Haken
dabei: das kann dein Kontakt nur unterscheiden, wenn er einen eigenen
Kipp-Zustand meldet.

* **Schlafzimmer** (`sensor.balkontur_opening_state`, Kipp-Zustand `tilted`):
  hier wirken beide, 90 % bei offen und 30 % bei gekippt.
* **Alle anderen** (`window_tilted_state: none`): zweiwertiger Kontakt, es wird
  **immer** die Kipp-Position gefahren, auch bei „offen". Dein Export sagt das
  auch:

  > ⚠️ Ohne Kipp-Zustand ist der Kontakt zweiwertig, gefahren wird immer
  > `position_when_window_tilted` (20 %) – auch bei „offen".

  Deine 100 % bei „offen" kommen dort nie zum Zug. Seit 2.8.2 zeigt das
  Formular für solche Kontakte deshalb auch nur noch **einen** Schieber.

### ❓ Die Markise läuft umgedreht

Deine `cover.markise` meldet **keine Position** (im Export: „Position jetzt: –").
Solche Antriebe kennen nur *auf* und *zu*; Shutter Pilot schickt dann statt
einer Prozentzahl ein `open_cover` (ab 50 %) oder `close_cover` (unter 50 %).

Deshalb bewirkt ein Schieber von 0 auf 20 nichts – erst der Sprung über die
Mitte zählt. **Dreh die beiden Werte einfach um:**

| Feld | statt | auf |
| --- | --- | --- |
| Ruhestellung (eingefahren) | 0 % | **100 %** |
| Beschattung (ausgefahren) | 100 % | **0 %** |

Dann fährt „Ruhe" ein `open_cover` und „Beschattung" ein `close_cover`, und die
Richtung stimmt. Der Wind- und Regenschutz rechnet das automatisch mit – der
liest die eingestellten Rollen, nicht feste Zahlen.

Sauberer wäre natürlich, den Aktor selbst richtig herum zu konfigurieren; das
geht aber nicht bei jedem Modell.

### ❓ Der Nachtrag: Schlafzimmer nicht runter, morgens nicht hoch

**Nicht runtergefahren, weil das Fenster auf Kipp war** – das ist gewollt und
korrekt: Du hast an allen Rollläden *„Fahrt nach dem Schließen nachholen"*
aktiviert. Die Fahrt wird vorgemerkt und läuft, sobald das Fenster zugeht. (Ohne
diesen Haken würde er bei offenem Fenster einfach zufahren.)

**Morgens nicht hochgefahren** – hier ist mein Verdacht ein anderer, und er
steht in deinem eigenen letzten Satz:

> *„Ich habe das ganze erstmal ausgeschaltet und meine Automationen wieder
> eingeschaltet."*

Liefen die **parallel** zu Shutter Pilot? Dann ist das die Erklärung. Deine
Bereiche stehen alle auf `manual_override: never`. Das heißt: *Eine Position,
die nicht von Shutter Pilot kommt, gilt als von Hand gesetzt und blockiert das
automatische Hochfahren bis zum nächsten Schließen.* Für Shutter Pilot ist eine
fremde Automation nicht von einem Handgriff zu unterscheiden.

Dazu passt auch das Wohnzimmer mit **90 % und 5 %** – das sind keine von deinen
konfigurierten Positionen (du hast 0 / 50 / 100 / 20). Da hat etwas anderes
gefahren.

**Zu tun:** Entweder die alten Automationen wirklich abschalten, oder
`manual_override` auf **`next_action`** stellen – dann gewinnt der Zeitplan
immer.

### Und zum Anfang: 2.7.1 → 2.14 „hat alles zerschossen"

Von 2.7.1 auf 2.14 sind sieben Versionen. Dass du neu angefangen hast, war
vermutlich der schnellste Weg. Ein Punkt für die Zukunft, weil er oft
missverstanden wird: **nach jedem Update den Browser einmal hart neu laden**
(Strg+F5 bzw. Cmd+Shift+R). Ein Panel aus dem Cache mit neuem Backend sieht
genau so aus wie „alles kaputt".

Wenn nach dem Update auf 2.15.0 noch etwas quer steht: **schick bitte noch
einmal den Export.** Der beantwortet inzwischen ziemlich viel von allein.

Danke fürs Melden – zwei der Fehler oben hätte ohne deinen Bericht niemand
gefunden. 👍

---

## An Thsu

Hallo Thsu,

danke fürs freundliche Wort – und du hast nichts übersehen, das gab es
tatsächlich noch nicht.

**Neu in 2.15.0:** Beim Rollladen gibt es unter „Fenster & Lüftung" jetzt ein
Feld **„Zweiter Fensterkontakt"**. Es erscheint, sobald der erste gesetzt ist.

Beide Kontakte werden **zusammen** gelesen: Das Fenster gilt als offen, sobald
**einer** von beiden es meldet. Damit greifen Aussperrschutz, Lüftungsposition
und die Nachholfunktion auch dann, wenn nur der zweite Flügel offen steht.

Ein eigenes Feld für „welcher Zustand heißt offen" gibt es beim zweiten Kontakt
bewusst nicht – zwei Flügel eines Fensters sind dieselbe Hardware zweimal, es
gelten die Einstellungen des ersten.

> ℹ️ Nicht zu verwechseln mit dem Feld darunter, **„Zusätzlicher Sensor für
> gekippt"**. Das ist für Fenster, die *offen* und *gekippt* als zwei getrennte
> Entitäten melden – also derselbe Flügel, zweimal beschrieben. Bei dir ist es
> das neue Feld.

Und danke für die Urlaubswünsche – hat gut getan. 🙂

---

## An hollizone

Hallo,

**das kann Shutter Pilot bereits**, und zwar seit 2.6.0. Du hast keinen Fehler
gemacht, die Einstellung heißt nur nicht so, wie man sie suchen würde.

**Rezept:** Beim betroffenen Rollladen unter „Fenster & Lüftung":

1. **Fenstersensor** eintragen (den hast du ja schon)
2. Haken bei **„Fahrt nach dem Schließen nachholen"** setzen

Damit gilt: Steht bei fälliger Beschattung das Fenster offen, wird die Fahrt
**vorgemerkt statt ausgeführt** – und läuft, sobald das Fenster geschlossen
wird. Genau das Verhalten, das du von der Abendschließung kennst. Es ist
derselbe Mechanismus; die Beschattung ist einer der Fahrwege, die ihn benutzen.

Ich habe das in 2.15.0 mit drei Tests festgenagelt (offen → wird vorgemerkt,
schließen → fährt, geschlossen → fährt sofort), damit es nicht bei einer
Behauptung von mir bleibt und bei einer künftigen Änderung nicht unbemerkt
kaputtgeht.

> ⚠️ Der Merker wird nach **24 Stunden** verworfen. Bleibt ein Dachfenster einen
> ganzen Tag offen, wird die Beschattung von gestern nicht mehr nachgeholt –
> was auch richtig so ist, sie sagt nichts mehr über die jetzige Sonne aus.

Dein Argument mit den großen Dachfenstern ist gut. Falls dir das Nachholen zu
spät kommt, gibt es als Alternative den **Aussperrschutz** (Mindestposition bei
offenem Fenster) – dann fährt er zwar, aber nur bis zu einer Höhe, bei der
nichts zuschlagen kann.

---

## An Pampelmuse

Hallo Pampelmuse,

danke für die Urlaubswünsche 🙂 – und für den Log. Der ist allerdings nur der
**Bereichs**-Teil des Exports, und darin steht tatsächlich nichts Verdächtiges:

* Sonnenhöhe: nicht geprüft (Haken aus) → blockiert nicht ✅
* Fensterrichtung: nicht geprüft (Haken aus) → blockiert nicht ✅
* Beschattungszeitraum Mai–September ✅ (im August)
* Uhrzeit 09:00–19:00 ✅
* Bedingung a: 20,2 °C ≥ 18 ✅
* Bedingung b: 23,9 °C ≥ 23 ✅

**Der Bereich sagt also: beschatten.** Die Ursache muss folglich bei den
Rollläden liegen – und genau dieser Teil fehlt in dem, was du geschickt hast.
Die drei häufigsten Ursachen, bitte der Reihe nach prüfen:

**1. Der Runter-Bereich, nicht der Hoch-Bereich** ⭐ *(mit Abstand am häufigsten)*

Über die Beschattung entscheidet allein der **Bereich Runter** eines Rollladens.
Steht „1.OG Sonnenseite" bei deinen Rollläden nur als *Bereich Hoch* drin,
passiert nichts – auch wenn im Bereich alles richtig eingestellt ist. Im Export
steht das je Rollladen so:

```
Bereich hoch: `…` · Bereich runter: `…` (der Runter-Bereich entscheidet über die Beschattung)
```

**2. Beschattungsposition = Offen-Position**

Steht bei einem Rollladen die Sonnenschutz-Position auf demselben Wert wie die
Offen-Position (meist 100), *fährt* Shutter Pilot – nur bewegt sich nichts.
Typisch sind 40–60 %.

**3. Automatik am Rollladen aus**

Der Schalter `switch.shutter_pilot_rollladen_<Name>`. Steht der auf aus, wird
der Rollladen weder beschattet noch freigegeben.

**Schick mir bitte den vollständigen Export** – Einstellungen → ganz unten
„Einstellungs-Export erstellen" → Kopieren oder Herunterladen. Der rechnet je
Rollladen die echte Beschattungsprüfung durch und schreibt jede Teilprüfung mit
Ergebnis hin. Damit sehen wir es in einer Zeile.

> 💡 Noch ein Hinweis am Rande: Du hast `drive_delay: 10`. Bei mehreren
> Rollläden im Bereich vergehen zwischen dem ersten und dem letzten also
> Sekunden bis Minuten. Falls du nach dem Einschalten sofort hinsiehst: warte
> einmal eine Minute ab.

---

## An charly166

Guten Morgen charly166,

danke – und zwei Volltreffer. Beide sind in **2.15.0** erledigt.

### 🐞 „Die globalen Markisen-Einstellungen sind beim nächsten Aufruf leer"

**Bestätigter Fehler, behoben.** Deine Beobachtung war genau richtig:
gespeichert **waren** sie (deshalb im Export sichtbar), zurückgeschickt hat der
Server sie nie – das Panel bekam nur sechs fest verdrahtete Einstellungen, der
Markisenschutz war nicht dabei.

Ärgerlich war das nicht nur optisch: Wer eine Windschwelle korrigieren wollte,
musste raten, was drinsteht. bjoerg hat sich dabei einen Shutter-Pilot-eigenen
Schalter als Windsensor eingetragen – seine Markise war danach dauerhaft
gesperrt.

Ab 2.15.0 kommt zurück, was gespeichert ist. **Bitte nach dem Update einmal
nachsehen, ob dort noch das steht, was du erwartest.**

### 💡 „Rollläden fahren in die Beschattungsposition, obwohl sie noch nicht hochgefahren sind"

Du hast den Kern genau getroffen, und dahinter steckt etwas Handfestes:
**Beschatten und Öffnen ist derselbe Fahrbefehl mit einer anderen Zahl.**
„Position 50" von 100 herunter und „Position 50" von 0 herauf sind für Home
Assistant identisch – dem Code fehlt schlicht die Information, aus welcher
Richtung er kommt. Die steht aber in der aktuellen Position, und genau die wird
jetzt gelesen.

**Neu:** Haken *„Nur beschatten, was schon offen ist"* im Sonnenschutz-Block
des Bereichs. Angehakt bleibt ein noch geschlossener Rollladen unten, bis er
regulär geöffnet hat. Vorgabe aus, weil es das Fahrverhalten ändert – wer es
will, hakt es an.

Deinen Wunsch nach dem Wochenende habe ich mit aufgenommen, siehe die Antwort an
c.radi und Linos.

---

## An Linos

Hallo Linos,

drei Punkte, und alle drei sind in **2.15.0** drin – deiner mit der
Bedingungs-Entity war der beste Vorschlag im ganzen Thread, weil er die drei
anderen Fälle gleich miterledigt.

### ✅ „Eine Bedingung-Entity, die das automatische Öffnen in der Früh blockiert"

Genau so gebaut. Im Bereich gibt es einen neuen Abschnitt **„Hochfahren
unterbinden"** mit dem Feld **Bedingung „nicht hochfahren"**.

Es nimmt alles, was die anderen Bedingungsfelder auch nehmen:

| Was du hast | Geht |
| --- | --- |
| Urlaubs-/Ferienschalter (`input_boolean`) | ✅ an = nicht hochfahren |
| Zeitplan-Helfer (`schedule`) | ✅ |
| Auswahlliste (`input_select`, z. B. Hausmodus) | ✅ mehrere Zustände wählbar |
| Zahlensensor | ✅ mit Ein-/Ausschaltschwelle |

Zwei Dinge, die ich bewusst so entschieden habe:

* **Nur das Hochfahren ist gesperrt.** Runterfahren und Beschattung laufen
  weiter – sonst stünde das Haus unter der Ferien-Kennung den ganzen Abend
  offen zur Straße.
* **Ein nicht lesbarer Sensor blockiert nicht.** Andersherum bliebe jeder
  Rollladen unten, bis es jemand merkt – und aus dem Zimmer heraus kommt man
  daran nicht vorbei.

### ✅ Wochenende

Zusätzlich ein einfacher Haken: **„Am Wochenende gar nicht hochfahren"**, im
selben Abschnitt. Er hängt am selben Wochenendbegriff wie alles andere: **ist
ein Sondertage-Sensor eingetragen, entscheidet der** – damit deckt der Haken
automatisch auch Feiertage, Ferien und Schichtdienst ab.

Dein Tipp an c.radi mit der Automation auf den Auto-Schalter war völlig richtig
und funktioniert weiter. Jetzt braucht es ihn nicht mehr.

### ✅ „Automatisches Mitfahren erst, wenn der Behang komplett geöffnet wurde"

Auch drin – Haken **„Nur beschatten, was schon offen ist"**. Die Ursache dahinter
ist, dass Beschatten und Öffnen derselbe Fahrbefehl mit einer anderen Zahl ist;
die Richtung steht nur in der aktuellen Position, und die wird jetzt gelesen.

> ℹ️ Beim **Lüften** greift das nicht, und das ist Absicht: Lüften merkt sich
> die vorherige Position und fährt dorthin zurück. Es hebt einen geschlossenen
> Rollladen nur an, wenn du die Lüftungsbedingung ausdrücklich eingeschaltet
> hast – da ist genau das der Zweck.

Danke fürs Mitdenken – wie üblich. 👍

---

## An hollsten (Roland)

Hallo Roland,

völlig berechtigter Einwand, und das ist einer der Fälle, in denen ich zuerst
nachgesehen habe, ob es nicht doch schon geht. **Es geht** – nur heißt die
Einstellung nicht „Sonnabend".

Der **Sondertage-Sensor** je Bereich (früher „Workday-Sensor") entscheidet
*vor* dem Kalender darüber, ob der Wochenend- oder der Wochentagsplan gilt. Für
deinen Fall:

1. In der `configuration.yaml` einen Workday-Sensor mit **`excludes: [sun]`**
   anlegen:

```yaml
binary_sensor:
  - platform: workday
    country: DE
    province: NI          # dein Bundesland
    name: Arbeitstag Handel
    excludes: [sun]       # nur der Sonntag ist frei, der Sonnabend nicht
```

2. Ihn im Bereich als **Sondertage-Sensor** eintragen.

Ergebnis: **Sonnabend gilt als Arbeitstag** → es greifen die Wochentagszeiten.
Nur am **Sonntag** (und an Feiertagen, die der Sensor kennt) greifen die
Wochenendzeiten. Genau die Trennung, die du beschreibst.

Der Sensor wirkt in **allen drei Modi** – Zeit, Helligkeit und Sonnenstand.

> 💡 Und der neue Haken **„Am Wochenende gar nicht hochfahren"** aus 2.15.0
> richtet sich nach demselben Sensor. Wer sonntags gar nicht geöffnet haben
> will, bekommt das damit ohne eine einzige Automation.

Ein drittes Zeitschema (Woche / Sonnabend / Sonntag) habe ich deshalb bewusst
**nicht** gebaut: Es wäre ein dritter Satz von acht Feldern in jedem Bereich –
und es könnte immer noch nicht, was der Sensor kann (Feiertage, Ferien,
Schichtpläne).

Falls du keinen Workday-Sensor einrichten magst, geht es zur Not auch mit einem
Template-Sensor:

```yaml
template:
  - binary_sensor:
      - name: Kein Sonntag
        state: "{{ now().weekday() != 6 }}"
```

---

## An MartyBr

Hallo Martin,

**genau das gibt es jetzt** – in 2.15.0.

Jeder Bereich mit eingeschaltetem Sonnenschutz bekommt einen eigenen Schalter:

```
switch.shutter_pilot_sonnenschutz_<Bereich>
```

Dazu einen Schalter direkt auf der **Dashboard-Karte**, neben der Statuszeile
des Sonnenschutzes – für den Griff zwischendurch, ohne in die Einstellungen zu
gehen.

Er ist bewusst **getrennt** vom Automatik-Schalter des Bereichs, genau aus dem
Grund, den du nennst: 35 °C heute und 20 °C morgen ist ein Grund, die
Beschattung sein zu lassen. Es ist kein Grund, die Rollläden morgens unten zu
lassen.

Zwei Dinge, die du wissen solltest:

* **Ausschalten gibt frei, was gerade beschattet ist** – die betroffenen
  Rollläden fahren auf. Sie stehenzulassen wäre die schlechtere Hälfte: Wer bei
  Wetterumschwung abschaltet, will nicht bis zum Abend auf halber Höhe sitzen.
* Der Schalter ist eine **normale Schalter-Entität**. Du kannst ihn also aus
  einer Automation heraus stellen – zum Beispiel abhängig von der
  Tageshöchsttemperatur:

```yaml
automation:
  - alias: Beschattung nach Vorhersage
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: >
          {% if states('sensor.shutter_pilot_vorhersage_hochsttemperatur')|float(0) >= 24 %}
            switch.turn_on
          {% else %}
            switch.turn_off
          {% endif %}
        target:
          entity_id: switch.shutter_pilot_sonnenschutz_wohnbereich
```

Der Sensor `sensor.shutter_pilot_vorhersage_hochsttemperatur` kommt von Shutter
Pilot selbst, sobald du unter Einstellungen eine Wetter-Entität hinterlegt hast.
Er hält seit 2.9.0 das **Tagesmaximum** fest, fällt also nachmittags nicht
wieder ab.

Deinen bisherigen Behelf mit den Beschattungsmonaten kannst du damit
zurückstellen – der bleibt natürlich, wo er ist, falls du ihn zusätzlich
brauchst.

Danke für den Vorschlag. 👍
