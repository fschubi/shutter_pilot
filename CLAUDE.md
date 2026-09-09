# CLAUDE.md – Arbeitsgrundlage & Fortschritts-Doku

Diese Datei führt Claude (Entwickler-KI) als eigene Projektdokumentation:
Funktionsumfang, Konventionen und ein fortlaufendes Fortschritts-Log. Sie wird
bei jedem größeren Arbeitsschritt aktualisiert und mit gepusht.

**Größenlimit:** CLAUDE.md wird bei jeder Session komplett in den Kontext
geladen, deshalb bewusst klein gehalten. Das Fortschritts-Log unten enthält
nur die **letzten fünf Einträge**; die vollständige Historie steht in
`docs/CHANGELOG_DEV.md`. Beim Hinzufügen eines neuen Eintrags: den ältesten
der fünf hier herausnehmen und (unverändert) an den Anfang der Log-Einträge in
`docs/CHANGELOG_DEV.md` setzen, sonst wächst diese Datei wieder über das
Limit.

## Projekt

**Shutter Pilot** – Custom Integration für Home Assistant, die Rollläden nach
Zeit, Helligkeit oder Sonnenstand fährt. Konfiguriert wird nicht über
YAML oder Options-Flow, sondern über ein **eigenes Sidebar-Panel**.

- Repo: https://github.com/fschubi/shutter_pilot (Branch `master`)
- Verteilung über HACS · Mindestversion Home Assistant 2024.6.0
- `single_config_entry: true` – es gibt genau einen Config-Entry
- Sprache im Projekt: **Deutsch** (Commits, Changelog, Kommentare, Forumstexte).
  Code-Bezeichner und Docstrings im Python-Teil sind englisch.

## Aufbau

```
custom_components/shutter_pilot/
  __init__.py        Setup, Panel-Registrierung, WebSocket-API, Minutentakt
  const.py           Alle Config-Keys, Defaults, Events – die Referenz
  helpers.py         Herzstück: Beschattungslogik, Positionen, Sperren (~980 Z.)
  scheduler.py       Zeit- und Sonnenmodus: Fahrten planen und auslösen
  brightness.py      Helligkeitsmodus mit erlaubten Zeitfenstern
  elevation.py       Beschattung: Elevation, Azimut, Bedingungen, pro Rollladen
  ventilation.py     Automatisches Lüften nach Bedingungen
  awning_guard.py    Markisen: Wind-, Regen- und Frostschutz (Sperre + Zwangsfahrt)
  awning_dusk.py     Markisen: bei Dämmerung einfahren, nie automatisch wieder aus
  schedule_times.py  Zeitmathematik: Wochenende, Jitter, Zeitklammern
  window_trigger.py  Reaktion auf Fensterkontakte
  window_helper.py   Fensterzustand und Aussperrschutz
  cover_tracker.py   Positionen mitschreiben, nach Neustart wiederherstellen
  cover_verify.py    Fahrtkontrolle: erreicht der Rollladen die Position?
  position_store.py  JSON-Speicher der letzten Positionen
  weather_data.py    Tagesvorhersage über weather.get_forecasts
  group_actions.py   Folgeaktion Licht je Bereich
  switch/sensor/binary_sensor.py   Entitäten
  services.py        Dienste (Gruppenaktionen)
  frontend/shutter-pilot-panel.js  Das komplette Panel (~4800 Z., ein File)
tests/               pytest-Suite (799 Tests)
tests/panel/         Panel in Node rendern – laeuft in der CI mit
```

## Funktionsumfang

### Bereiche und Modi

Ein **Bereich** bündelt Rollläden und legt fest, *wann* gefahren wird. Jeder
Rollladen hat einen Bereich fürs Hochfahren und einen fürs Runterfahren – die
dürfen verschieden sein (morgens raumweise, abends alle zusammen).

| Modus | Auslöser |
| --- | --- |
| `time` | feste Uhrzeiten, getrennt für Woche und Wochenende |
| `brightness` | Helligkeitssensor mit Schwellen, nur in erlaubten Zeitfenstern |
| `sun` | Sonnenauf-/-untergang plus Offset, optional in Zeitklammern |
| `none` | gar nichts – nur Beschattung und Lüften (2.16.0) |

Zwei Sperren je Bereich unterbinden das **Hochfahren** ganz (Runterfahren und
Beschattung laufen weiter): ein Wochenendhaken, der an `is_weekend_schedule()`
hängt und damit auch Feiertage und Ferien erfasst, und der Bedingungs-Slot
`no_up` – ausgewertet über `_own_slot_met()`, also „nicht gesetzt = nein, toter
Sensor = nein". Beide fragt `automated_up_blocked()` an genau zwei Stellen ab:
`scheduler._run_up_async` und `brightness._run_up`.

Wochenendwerte fallen immer auf die Wochentagswerte zurück, wenn sie leer
bleiben. Statt Samstag/Sonntag kann ein **Workday-Sensor** entscheiden
(Feiertage, Schichtdienst). Eine **Präsenzsimulation** streut die Zeiten um bis
zu N Minuten; der Wert ist pro Tag stabil, nicht pro Fahrt.

### Rollläden

Je Rollladen: Positionen für offen, geschlossen und Sonnenschutz, optional eine
**abweichende Schließposition** für laue Abende und eine **Frostposition**,
optional **Lamellenwinkel** (Raffstore). Fenstersensor mit Aussperrschutz, dazu
optional ein **zweiter Fensterkontakt** (Doppelflügel, ODER-verknüpft, der
offenere gewinnt) und ein zweiter Kontakt, wenn „gekippt" als eigene Entität
gemeldet wird (der behält Vorrang und wird *nicht* mitgerankt – er ist ein
Modifikator, kein zweiter Flügel),
und eine **Entprellung** (0–30 s), bevor auf „geschlossen" reagiert wird.
Optional fährt eine vorgemerkte Nachholfahrt schon jetzt auf die
Lüftungsposition (`window_vent_while_open`, Vorgabe aus) – ohne den Haken
passiert bei offenem Fenster gar nichts.

An einem Antrieb ohne Positionierung gibt es eine dritte Stellung: die am Motor
angelernte **„My"-Position** (`my_position_entity` + `my_position_pct`, RTS über
Overkiz als `button.*`). `my_position_target()` greift **nur im Rückfallzweig**
von `_send_position()`; wo Positionen gehen, ist die Zahl die genauere
Anweisung.

### Beschattung

Aktiv, wenn **alle** Bedingungen zugleich gelten:

1. Sonnenhöhe im konfigurierten Bereich (min/max)
2. Sonne steht vor den Fenstern (Azimut, Kompass-Schnellwahl)
3. bis zu **vier Zusatzbedingungen** – Binärsensor, Zahlenwert mit Ein-/
   Ausschaltschwelle oder Textzustand (Wetterlage). Dieselbe Mechanik trägt die
   eigenen Slots `close`, `frost` und `vent_a`/`vent_b` – die sind aber **fail
   closed**, ein toter Sensor löst dort nichts aus.
4. Datum liegt im konfigurierten **Beschattungszeitraum** (Jahreswechsel möglich)
5. Uhrzeit liegt im **Beschattungs-Zeitfenster** (`shade_from`/`shade_to`, beide
   einzeln optional, je Bereich und je Rollladen). Die einzige der fünf
   Prüfungen, die nicht die Sonne beschreibt, sondern den Haushalt – und
   bewusst **ohne** Wrap über Mitternacht

Dazu drei Einstellungen, die nicht die Sonne beschreiben, sondern das
Verhalten – alle je Bereich, alle mit Vorgabe „wie bisher":

* **Sonnenschutz-Schalter** (`switch.shutter_pilot_sonnenschutz_<bereich>`),
  getrennt vom Automatik-Schalter. Ausschalten *gibt frei*, es friert nicht ein.
* **Am Ende des Beschattungstags öffnen** – sonst steht der Rollladen bei
  `elev < e_min` bis zum Abendplan auf Beschattungshöhe. Im Sonnenmodus sind
  das Minuten, sonst Stunden.
* **Nur beschatten, was schon offen ist** – `set_cover_position(50)` ist von
  unten derselbe Befehl wie von oben; die Richtung steht nur in der aktuellen
  Position.

Die Beschattungsposition ist nicht eine Zahl, sondern drei Quellen, spezifisch
zuerst: eine **Entität** (0–100, unlesbar = Rückfall statt Aussetzer), eine
**zweite feste Position** hinter dem Slot `sp_alt` (Bedingung am Bereich,
Position am Rollladen – das Paar von `closed_alt`), sonst die normale. Sie
greift **sofort**, auch mitten in einer laufenden Beschattung; `_shade_pos_last`
verhindert dabei, dass der Motor jede Minute ein Prozent nachfährt. Ein
Rollladen kann über `shading_enabled` ganz aussteigen – anders als der
Automatik-Schalter hält das nur die Beschattung an, nicht den Zeitplan.

Geometrie und Bedingungen lassen sich **pro Rollladen** überschreiben. Der
Rückfall wirkt je Bedingungs-Slot: gesetzt am Rollladen ersetzt den Slot,
leer erbt den Bereichswert. Die Hysterese liegt deshalb pro Cover, nicht pro
Bereich – sonst hebt eine Wolke vor einem Fenster die Beschattung des anderen
auf. Ein fehlender oder toter Sensor blockiert nie (fail open).

### Markisen

Ein Eintrag in derselben `shutters`-Liste, unterschieden durch `device_kind`
(fehlt = Rollladen, keine Migration). Der Fahrweg ist **derselbe**: die
Beschattung fährt auf `position_sun_protect` und gibt auf `position_open` frei,
und welche Zahl das ist, entscheidet die Konfiguration – bei der Markise 100
bzw. 0. Nur die *Rückfallwerte* in `get_position_for_role()` drehen sich.

Anders sind zwei Dinge:

1. **Kein Zeitplan.** Scheduler, Helligkeit, Lüften und Fenstertrigger filtern
   Markisen aus (`only_shutters()`), der Aussperrschutz steigt früh aus – er
   klemmt nach unten, und unten ist bei einer Markise die *sichere* Seite.
2. **`awning_guard.py`.** Wind, Regen, Frost global unter Einstellungen; **nur
   der Wind** ist je Markise überschreibbar (örtlich verschieden), Regen und
   Frost fallen übers ganze Haus gleich. Slots derselben Mechanik, mit
   der Bedeutung **„Gefahr liegt vor"** statt „Bedingung erfüllt" – dadurch
   passen Binärsensor, Zahlenhysterese und Textzustände ohne eine einzige
   Änderung an `_condition_slot_met()`. Dazu eine **Sperrzeit** je Slot, die
   die Wertehysterese nicht leisten kann (eine Bö ist nach 20 s vorbei).

Optional: **Ausfahrlänge nach Sonnenhöhe**, zwei Stützpunkte linear
interpoliert, mit Mindeständerung gegen den Minutentakt am Getriebe.

Optional (2.22.0): **`awning_dusk.py`**, bei Dämmerung einfahren. Eigener
Bedingungs-Slot je Markise (`AWNING_DUSK_SLOT`), unabhängig vom
Sonnenschutz-Schalter des Bereichs und unabhängig vom Wetterschutz. Anders
als `awning_guard.py` respektiert er Hauptschalter, Bereichsautomatik und die
Automatik der Markise – eine Komfortfunktion, keine Sicherheitsfunktion, und
deshalb bewusst kein vierter Guard-Slot neben Wind/Regen/Eis. Fährt nur
**einmal ein**, wenn die Bedingung eintritt; die Freigabe (Bedingung fällt
weg) löst **keine** Fahrt aus – ausfahren bleibt Sache der Beschattung
(falls eingeschaltet) oder von Hand. Der Speicher hängt am Cover
(`condition_memory(data, "dusk", cover)`), nicht an einer Bereichs-ID, sonst
würden Markisen ohne echten Bereich in denselben Hysterese-Topf fallen.

### Manuelle Übersteuerung

Drei Modi je Bereich: `never` (manuelle Position blockiert bis zum nächsten
Schließen), `daily` (gilt nur am selben Tag), `next_action` (Automatik gewinnt
immer). Dafür trennt die Integration eigene Fahrten von fremden – über
Pending-Marker und ein Zeitfenster („recent automation").

### Fahrtkontrolle

Optional: nach jeder automatischen Fahrt prüfen, ob die Position tatsächlich
erreicht wurde, sonst wiederholen. Am Ende wird der gespeicherte Wert
korrigiert und `shutter_pilot_cover_failed` gefeuert. Rollläden ohne
Positionsmeldung werden übersprungen. Einstellbar: Wartezeit, Toleranz,
Wiederholungen.

### Weiteres

- **Positionsspeicher**: letzte Positionen überleben den Neustart; beim Start
  wird korrigiert, wenn die Cover-Integration falsch wiederhergestellt hat.
- **Wetter**: eigene Tagesvorhersage über `weather.get_forecasts`, ausgegeben
  als drei Sensoren (Höchst-, Tiefsttemperatur, Wetterlage) – direkt als
  Bedingung nutzbar.
- **Frostschutz**: eigener Bedingungs-Slot, der **nach unten** vergleicht, plus
  Rolle `closed_frost`. Gewinnt gegen die abweichende Schließposition.
- **Automatisches Lüften**: eigener Bedingungs-Slot je Bereich. Rangfolge
  Fensterkontakt > Beschattung > Lüften; zurück auf die vorherige Position.
- **Licht-Folgeaktion** je Bereich beim Runterfahren.
- **Minutentakt**: ein einziger `async_track_time_change` versorgt Scheduler,
  Wetter, Beschattung und Lüften – nicht pro Modul einen eigenen Timer anlegen.

### Entitäten, Dienste, Events

| Art | Entität |
| --- | --- |
| Schalter | `switch.shutter_pilot_system` (Hauptschalter), je Bereich und je Rollladen ein Auto-Schalter, je Bereich mit Beschattung ein Sonnenschutz-Schalter |
| Sensor | je Bereich „nächste Fahrt"; **einer fürs ganze Haus** (`shutter_pilot_status`: offen/geschlossen/teilweise, dazu Zahlen je Gruppe und die beschatteten Bereiche); Vorhersage Höchst-/Tiefsttemperatur und Wetterlage nur, wenn eine Wetter-Entität hinterlegt ist |
| Binärsensor | je Bereich „Sonnenschutz aktiv"; je Markise „Sperre" mit Grund und Restzeit |

Dienste: `open_group`, `close_group`, `sun_protect_group`, `ventilate_group`,
`stop_group`, `retract_awnings`, `resume_automation`. **Bereich überall
optional** – ohne ihn gelten sie fürs ganze Haus.
Events: `shutter_pilot_cover_moved`, `shutter_pilot_cover_failed`,
`shutter_pilot_awning_retracted`.

### Panel

Ein einzelnes JS-File, kein Build-Schritt. Tabs: Dashboard · Bereiche ·
Rollläden · Markisen · Dachfenster · Einstellungen. Besonderheiten, die man kennen muss:

- **LitElement kommt aus der Prototypenkette** eines geladenen HA-Elements –
  Home Assistant stellt kein Modul dafür bereit. Der Resolver probiert zehn
  Kandidaten und läuft an Mixins vorbei; findet er nichts, zeigt das Panel eine
  Meldung statt einer weißen Seite. `render()` liegt in einem try/catch.
- **macOS-App (Mac Catalyst)**: native `<input type="time">` und `<select>`
  sind dort kaputt (Absturz bzw. öffnet nicht). `NATIVE_PICKERS_BROKEN`
  erkennt die Plattform, dann werden eigene Bedienelemente gerendert.
- **Rechte**: Ohne Administrator zeigt das Panel nur das Dashboard mit den
  Bedienknöpfen. Das ist Bequemlichkeit – die Grenze liegt auf dem Server.
- **Über den Bereichskarten steht ein Block fürs ganze Haus** (2.18.0): dieselben
  fünf Fahrknöpfe für alle Rollläden, Automatik und Beschattung für alle Bereiche,
  dazu Sonnenauf-/-untergang, Elevation, Azimut und die Tagesvorhersage. Die
  Schalter laufen über die WebSocket-Befehle und sind deshalb Admin-only, die
  Fahrknöpfe nicht – dieselbe Trennung wie auf den Karten.
- **Die Bedienknöpfe rufen die `cover`-Dienste direkt auf** (damit HA die Rechte
  je Entität prüft). Sie kommen damit an *jedem* Riegel im Backend vorbei.
  Dreimal doppelt gebaut: Mindestabstand, Markisensperre, Aussperrschutz. Bei
  einem neuen Riegel ist die erste Frage, ob das Panel ihn kennt. Trennung:
  **Gruppenknopf = Bereich handelt** (Rollladenschalter gilt), **Zeilenknopf und
  Dienste = von Hand** (gilt nicht – sonst ist ein reparierter Antrieb nicht
  prüfbar).
- **i18n**: 11 Sprachen (de, en, fr, es, it, nl, da, sv, pl, pt, nb) im Objekt
  `I18N`. Jeder neue sichtbare Text braucht einen Schlüssel in **allen** elf;
  `t()` fällt sonst auf Englisch zurück. Seit 2.7.1 sind alle elf **vollständig**
  (Stand 2.22.0: je 444 Schlüssel) – das gilt es zu halten. Prüfskript: alle
  Sprachmengen gegen `de` halten, ist in zwanzig Zeilen geschrieben.

### WebSocket-API

| Befehl | Rechte |
| --- | --- |
| `shutter_pilot/get_status` | alle (lesend) |
| `save_area`, `delete_area`, `save_shutter`, `delete_shutter` | **Admin** |
| `save_settings`, `set_master_enabled`, `set_auto_mode`, `set_shutter_automation`, `set_sun_protect` | **Admin** |

Alle ändernden Befehle tragen `@websocket_api.require_admin` (außen, darunter
`websocket_command` – Reihenfolge wie in HA Core). Kommt ein neuer schreibender
Befehl dazu: **nicht vergessen**.

## Konventionen

- Kommentare erklären **warum**, nicht was. Keine Doppelung des Codes.
- Neue Config-Keys immer in `const.py`, mit Default daneben.
- Panel und Backend gehören zusammen: neues Feld → Key, Panel-Feld, i18n×11,
  Test, README (beide Sprachen), Changelog.
- Tests für jede Logikänderung. Die Suite ist die Absicherung gegen Regressionen
  in einer Integration, die niemand hier im Wohnzimmer nachstellen kann.
- Commit-Nachrichten deutsch, Fließtext statt Stichpunktliste, mit Begründung.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest            # 799 Tests, ~19 s
```

`.venv/` ist in `.gitignore`. In `pytest.ini` steht `-q` schon in `addopts` –
ein zusätzliches `-q` ergibt `-qq` und verschluckt die Zusammenfassung, also
ohne Argument aufrufen. Die CI ([tests.yaml](.github/workflows/tests.yaml))
fährt dieselbe Suite bei jedem Push auf `master` mit Python 3.13.

**Panel testen ohne Home Assistant:** Das JS lässt sich in Node mit einem
Stub für `customElements`/LitElement auswerten und rendern. Seit 2.21.1 liegt
das **im Repo** (`tests/panel/`, angebunden über `tests/test_panel.py`) und
läuft in der CI mit – vorher war es Wegwerf-Werkzeug im Scratchpad, und genau
deshalb ging ein ReferenceError raus, den es gefunden hätte. Der Renderer
deckt alle Ansichten, alle Formulare und alle Bereichsmodi ab, **mit zwei
Einträgen je Geräteart**: der Kopierknopf wird erst ab dem zweiten gerendert.

## Release

1. `manifest.json` Version hochziehen, `CHANGELOG.md` ergänzen
2. committen, `git push origin master`, CI grün abwarten
3. `git tag -a vX.Y.Z -m "…"` + `git push origin vX.Y.Z`
4. `gh release create vX.Y.Z --title "…" --notes-file …`

**Ohne GitHub-Release zieht HACS die Version nicht.** Die Release-Notes sind
für Endnutzer geschrieben (Emoji-Überschriften, Tabellen, „was ändert sich für
mich"), nicht als Commit-Log.

## Projektstand

Version **2.22.4**, im Forum aktiv genutzt. Einreichung für den
HACS-Default-Store läuft: PR [hacs/default#9592](https://github.com/hacs/default/pull/9592).

## Fortschritts-Log

Vollständige Historie (ältere Einträge) steht in `docs/CHANGELOG_DEV.md` – hier nur die letzten fünf, damit diese Datei nicht wieder über das Kontextlimit wächst. Neuer Eintrag kommt hier dazu; wird die Liste hier zu lang, wandert der älteste nach `docs/CHANGELOG_DEV.md`.

### 2026-09-09 – 2.22.4: der Merker, der die Freigabe nicht bemerkte

Forumsmeldung c.radi (community.simon42.com/90112/144): „Mein Rolladen
Schlafzimmer links fährt abends nicht herunter." Export mitgeliefert, Wert
für Wert gegen die echten Helfer nachgerechnet statt geglaubt.

**Der auffällige Widerspruch im Export:** Position „Schlafzimmer Links"
100 % (offen), Quelle „automation" – aber unter „Laufender Zustand" stand
genau dieser Rollladen trotzdem in `covers_driven_down` („gilt als unten"),
`covers_driven_up` war für alle vier Rollläden leer. `scheduled_role_now()`
dokumentiert diesen Merker ausdrücklich als „nur wo zuletzt hingefahren
wurde" – ein Rollladen, der von der Automatik selbst nach oben gefahren
wurde, aber weiter als „unten" gilt, ist genau der Widerspruch, den
`brightness.py::_run_down()` als „heute schon unten gewesen" liest und
deshalb überspringt.

**Nachgerechnet, welcher Fahrweg das erzeugen kann.** Jeder reguläre
Fahrweg pflegt `covers_driven_up`/`covers_driven_down` mit – `_drive_group()`
(services.py, für `open_group`/`close_group`/…), `brightness.py` und
`scheduler.py` je für ihre eigene Richtung, `note_manual_position()` für
eine erkannte Fremdfahrt. Zwei Fahrwege tun das nicht:

1. **`resume_automation()`** (services.py) ruft `set_cover_position()`
   direkt auf, ohne die beiden Sets anzufassen – anders als `_drive_group()`
   in derselben Datei. Reproduziert: Rollladen künstlich in
   `covers_driven_down`, Dienst mit `scheduled_role_now() == "open"`
   aufgerufen – er fährt korrekt auf 100 %, aber der alte Merker blieb
   unverändert stehen.
2. **Die Beschattungsfreigabe** (`elevation.py::_release_sun_protect()`,
   ausgelöst durch `shade_release_opens`) fährt den Rollladen am Ende des
   Beschattungszeitraums in seine Ruhestellung (`rest_role()` – bei einem
   Rollladen `ROLE_OPEN`), räumt dabei bereits den Fenster-Zyklus und eine
   vorgemerkte Nachhol-Fahrt auf, aber nicht `covers_driven_down`.
   Reproduziert mit demselben Muster: Merker künstlich gesetzt, Freigabe
   per Elevationsabfall ausgelöst – Rollladen fährt auf 100 %, der Merker
   bleibt stehen.

**Warum das zu c.radis Bereich passt, ohne eine bestimmte Diensterei zu
unterstellen:** sein Bereich „Schlafen" hat `sun_protect_enabled: ja`,
`shade_release_opens: ja` **und** `we_no_up: ja` (Wochenend-Sperre fürs
Hochfahren). Die Sperre hält den Rollladen morgens korrekt unten – die
Beschattung kennt diese Sperre nicht und darf das auch nicht (Beschattung
und Hochfahr-Sperre sind bewusst getrennte Fragen). Fällt die Elevation am
Nachmittag unter `elevation_min`, fährt die Freigabe unabhängig von der
Sperre ganz auf. Ohne den Fix blieb der alte „unten"-Merker von der
Sperre über die Freigabe hinweg stehen, und die abendliche
Helligkeitsautomatik überspringt den nun weit offenen Rollladen.

Behoben an beiden Stellen mit derselben zweizeiligen Pflege wie in
`_drive_group()`: nach der Fahrt in `_release_sun_protect()` und in
`resume_automation()` `covers_driven_up`/`covers_driven_down` je nach
Zielrolle setzen bzw. löschen. **Dieselbe Fehlerklasse wie so oft in diesem
Log** (2.17.0, 2.21.3, 2.22.0 Fund 2, 2.22.2 Fund 2, 2.22.3 Fund 2): ein
Merker, der eine Handlung überlebt, für die er nicht gedacht war – diesmal
an zwei Stellen zugleich, weil beide denselben zentralen Vertrag
(„nach einer Endlagenfahrt stimmt die Richtung") ohne ihn beteiligt zu
haben, gebrochen haben.

**Verifiziert:** `pytest` 832 Tests grün (3 neue). Für beide Funde je eine
echte Gegenprobe – Fix testweise entschärft, genau die zugehörigen neuen
Tests fielen (`tests/test_resume_automation.py`, zwei neue Tests;
`tests/test_area_mode_none.py`, ein neuer Test), alle anderen 8xx blieben
grün, danach Fix wiederhergestellt und volle Suite erneut grün. **Nicht im
Browser geprüft** – reine Backend-Logik, keine Panel-Änderung.

### 2026-09-08 – 2.22.3: der Merker, der die Hand nicht bemerkte

Zwei Forumsmeldungen vom selben Tag (community-smarthome.com/11378), beide
zuerst gegen den Code nachgerechnet statt geglaubt – Charly ohne, bjoerg mit
Einstellungs-Export.

**Fund 1 (Charly): eine von Hand voll hochgefahrene Markise – nein, ein
Rollladen – fuhr beim Fensteröffnen wieder herunter.** Charlys Beitrag:
Rollladen morgens von Hand hochgefahren, kurz danach (nicht während der
Fahrt) das Fenster geöffnet und nach ein paar Minuten wieder geschlossen –
der Rollladen fuhr herunter, das automatische Öffnen (Sonnenstand + Zeit)
sollte laut ihm erst später greifen. Ursache in `window_trigger.py:308`:
`shaded = is_cover_sun_protected(data, cover_entity)` gilt seit d9f79b1
(2.15.0) als *unbedingter* Auslösegrund für den Fensterkontakt – „Shading
counts as a reason to react, whatever the position". `elevation.py` löscht
diesen Merker aber bewusst nicht, wenn jemand den Rollladen von Hand aus der
Beschattung herausfährt (`forget_shading_for_cover()`: „Deliberately not
called automatically when a foreign drive is noticed" – das ist Absicht,
damit `resume_automation` einen Sinn hat). Reproduziert: Rollladen manuell
auf 100 %, Beschattungs-Merker aus einer noch aktiven oder von der letzten
Beschattung übrig gebliebenen Auswertung steht auf `True`, Fenster geht auf
– der Trigger fährt trotz `opens_cover=False` (Zielposition liegt unter der
aktuellen) auf die Lüftungsposition herunter, genau das, was der
Code-Kommentar eine Zeile darüber ausdrücklich verbietet („during daytime
... must NOT force the cover into a ventilation position").

Behoben mit einer neuen `_is_cover_effectively_open()` (spiegelbildlich zu
`_is_cover_effectively_closed()`, gleiche 8-%-Toleranz): der `shaded`-Bypass
gilt nur noch, solange der Rollladen nicht bereits effektiv offen steht.
Der ursprüngliche Grund für den unbedingten Bypass (heinzies Fall aus
2.15.0: ein an der Beschattungsposition, z. B. 25 %, geparkter Rollladen
muss trotzdem reagieren, damit die Terrassentür nicht davor hängen bleibt)
bleibt unberührt – dort steht der Rollladen tatsächlich noch an seiner
Beschattungshöhe, nicht bei 100 %. Gegenprobe mit genau diesem Altfall
eigens im neuen Test mitgeführt.

**Fund 2 (bjoerg, Post 139, https://community-smarthome.com/t/11378/139):
eine vorgemerkte Nachhol-Fahrt überlebte zwei manuelle Fahrten und drohte,
später gegen einen längst anders positionierten Rollladen zu feuern.**
Sein eigentliches Problem – der Rollladen fuhr morgens nicht automatisch
hoch – ist **kein Codefehler**: er hatte das Schlafzimmerfenster abends
offen (Rollladen entsprechend auf `position_when_window_open`=95 %),
per Taster am Bett auf 35 % zugefahren, und `manual_override` steht für
den Bereich auf `never`. Nachgerechnet: `manual_position_is_a_close()`
vergleicht 35 % gegen `position_closed`=0 mit 8 % Toleranz – nicht nah
genug, also zählt die Fahrt als echter Override, der laut `never` bis zum
nächsten Schließen bestehen bleibt. Geschlossen wurde die Balkontür seitdem
nicht (nur auf Kipp gestellt) – die Automatik verhält sich also exakt wie
dokumentiert, keine Regression durch 2.22.2 (dessen Änderungen lagen in
`services.py`/`window_trigger.py`, nicht in diesem Pfad). Wer eine
nächtliche Teilfahrt nicht bis zum nächsten echten Fensterschluss als
Override gewertet haben will, nutzt `manual_override: daily` statt `never`
– dann gilt der Override nur für den Kalendertag, an dem er gesetzt wurde.

Sein Export zeigte aber einen echten, verwandten Fehler: unter „wartende
Nachhol-Fahrten" stand sein Rollladen noch, **obwohl er ihn längst von Hand
wieder auf 100 % gefahren hatte**. `drive_after_close_pending` – gesetzt
von `brightness.py::_run_down`, weil das Fenster beim abendlichen
Zufahren offen stand – wird ausschließlich durch ein tatsächliches
„Fenster geschlossen"-Ereignis konsumiert (`_apply_window_closed()` in
`window_trigger.py`). Zwei manuelle Fahrten dazwischen (nachts auf 35 %,
morgens auf 100 %) ließen die Vormerkung unberührt stehen. Reproduziert:
schließt das Fenster irgendwann später am Tag, völlig unabhängig vom
nächtlichen Geschehen, fährt der längst von Hand wieder geöffnete
Rollladen unerwartet auf die überholte Vormerkung von gestern Abend (0 %)
zu – eine Fahrt, die zu dem Zeitpunkt niemand mehr will.

Behoben in `cover_tracker.py::_on_cover_state_change`: dieselbe Stelle, die
bei einer erkannten Fremd-/Handfahrt bereits `note_manual_position()` und
`forget_commanded_position()` aufruft, ruft jetzt zusätzlich
`forget_drive_after_close()` auf. **Dieselbe Fehlerklasse wie 2.21.3, wie
Fund 2 aus 2.22.2 und wie `note_manual_position()` (2.17.0) selbst:** ein
Merker, der eine Handlung überlebt, für die er nicht gedacht war – diesmal
war es nicht der Fenstertrigger-Zyklus, sondern die davon unabhängige
Nachhol-Fahrt-Vormerkung, die dieselbe manuelle Fahrt nicht mitbekam.

**Verifiziert:** `pytest` 829 Tests grün (2 neue). Für beide Funde je eine
echte Gegenprobe – Fix testweise entschärft, genau der zugehörige neue Test
fiel, alle anderen 8xx blieben grün, danach Fix wiederhergestellt und volle
Suite erneut grün. Neue Dateien: `tests/test_window_trigger_shaded_manual_
reopen.py` (mit Gegenprobe für den heinzie-Altfall im selben Test),
`tests/test_manual_move_clears_pending_drive.py`. **Nicht im Browser
geprüft** – reine Backend-Logik, keine Panel-Änderung.

### 2026-09-06 – 2.22.2: drei Schlösser, die eine Hintertür hatten

Kein Forumsbeitrag – eine beauftragte, vollständige Analyse der gesamten
Beschattungs-, Lüftungs-, Dämmerungs- und Schutzlogik, mit ausdrücklichem
Auftrag, jeden Fund gegen den tatsächlichen Codefluss zu prüfen, bevor er
als Fehler behauptet wird. Erst mit `graphify query`/`explain` orientiert,
dann `helpers.py`, `elevation.py`, `awning_guard.py`, `awning_dusk.py`,
`ventilation.py`, `window_trigger.py`, `window_helper.py`, `scheduler.py`,
`brightness.py`, `cover_tracker.py`, `services.py` vollständig gelesen und
gegen die vorhandenen Tests abgeglichen. Drei Funde wurden nicht nur
gelesen, sondern **durch tatsächliche Testläufe** verifiziert – ein
temporärer Reproduktionstest je Fund, kurz nach `tests/` kopiert, ausgeführt
und wieder gelöscht (`git status` danach sauber), bevor überhaupt Code
geändert wurde.

**Fund 1: `resume_automation` kannte den Wetterschutz nicht.**
`services.py::resume_automation()` filterte seine Ziele über
`filter_shutters_by_area(..., use_up=False)` **ohne** `shutters_only=True` –
anders als `ventilate_group` in derselben Datei, das das bewusst tut
(„Awnings have no ventilation position"). Der Dienst ist laut README,
`services.yaml` und diesem Dokument ausdrücklich nur für „einen Rollladen"
gedacht, konnte aber Markisen und Dachfenster erreichen. Seine letzte
Fahrstufe – die Übergabe an den Zeitplan, wenn die Beschattung nichts
beanspruchte – rief `set_cover_position()` direkt auf, **ohne** je
`has_guard()`/`is_barred()` zu fragen, obwohl genau diese Prüfung in
`_drive_group()` (derselben Datei, benutzt von `open_group`/`close_group`/
`sun_protect_group`) längst existiert. Reproduziert: ein Dachfenster,
durch aktiven Regen gesperrt (bereits korrekt auf 0 % zugefahren), stand
laut Zeitplan „müsste tagsüber offen sein" – `resume_automation` fuhr es
trotz weiterhin aktivem Regen auf 100 % auf. Log bestätigt:
`Resume automation: cover.dachfenster_test -> 100%`, während der Guard
weiterhin `barred=True` meldete.

Behoben mit zwei Riegeln statt einem: `shutters_only=True` beim Filtern
(Markisen/Dachfenster erreichen den Dienst jetzt gar nicht mehr – werden
also auch nicht mehr von manueller Übersteuerung oder
Beschattungsmerkern befreit, was der Dienst für sie ohnehin nie sollte),
und zusätzlich dieselbe defensive `has_guard`/`is_barred`-Prüfung wie in
`_drive_group()` direkt vor der letzten Fahrt – unter der heutigen
Konfiguration durch den ersten Riegel bereits unerreichbar, aber
Tiefenverteidigung für den Tag, an dem eine dritte geschützte Geräteart
dazukommt. **Merke, wieder einmal:** ein Dienst, der „für einen Rollladen"
dokumentiert ist, muss das auch selbst durchsetzen – sonst ist die
Dokumentation die einzige Guard-Prüfung, die er hat.

**Fund 2: der Fenstertrigger vergaß seinen eigenen Zyklus nach einer
Nachholfahrt.** `window_trigger.py::_apply_window_closed()` hat zwei
Enden: einen `pending_entry`-Zweig (eine vorgemerkte Fahrt wird nachgeholt)
und den normalen Restore-Zweig. Nur der zweite räumte am Ende
`trigger_actions`/`trigger_heights` auf; der erste endete mit einem
`return` **davor**. Reproduziertes Szenario: ein Rollladen wird beschattet
(40 %), das Fenster geht auf – der Trigger merkt sich 40 % als
Rückfahrziel und fährt auf die Lüftungsposition. Abends will der Zeitplan
voll zufahren, das Fenster ist noch offen: die Fahrt wird vorgemerkt
(`remember_drive_after_close`, genau wie in `scheduler.py` und
`brightness.py`). Fenster schließt – die vorgemerkte Fahrt greift korrekt
auf 0 %, aber der Zyklus-Merker bleibt auf „triggered" mit der **alten**
Höhe (40 %) stehen. Wird das Fenster später in derselben Nacht noch
einmal kurz zum Lüften geöffnet und geschlossen – ohne jeden Bezug zur
Beschattung von vorhin –, restauriert der Trigger auf die veraltete 40 %
statt auf die aktuell korrekten 0 %: der Rollladen öffnet sich mitten in
der Nacht von selbst. Log bestätigt vor dem Fix:
`Window closed – restore: cover.schlafzimmer_stale -> 40%`.

Behoben mit zwei Zeilen: der `pending_entry`-Zweig räumt
`trigger_actions`/`trigger_heights` jetzt genauso auf wie der normale Zweig
– die nachgeholte Fahrt **ist** die Restaurierung dieses Fensterzyklus.
**Dieselbe Fehlerklasse wie `resting_position()` (2.21.3) und
`note_manual_position()` (2.17.0):** ein Merker, der eine Handlung
überlebt, für die er nicht gedacht war.

**Fund 3: die Dämmerungs-Einfahrt einer Markise konnte die Beschattung
dauerhaft lahmlegen.** `awning_dusk.py` fuhr eine Markise bei Dunkelheit
ein, ohne `sun_protect_covers` anzufassen. `elevation.py` verlässt sich
aber genau auf dieses Flag: solange es „aktiv" sagt und die Markise nicht
sonnennachführend ist, tut die Beschattung bei weiterhin erfüllter
Bedingung **nichts** (`elif not is_awning(shutter): …` gilt nur für
Nicht-Markisen). Normalerweise räumt `elevation.py` das Flag am Abend
selbst auf, weil die Elevationsprüfung dann selbst scheitert – das griff
aber nicht bei `elevation_enabled=False` (eine dokumentierte, unterstützte
Konfiguration seit 2.10.1: „wer einen Sensor pro Fenster hat, will, dass
der entscheidet"). Reproduziert: Markise mit abgeschalteter
Elevationsprüfung, Beschattung an einem durchgehend „heißen"
Temperatursensor. Dämmerung fährt korrekt ein – aber danach fuhr über
mehrere weitere Minutentakte **kein einziger** Befehl mehr, obwohl die
Beschattungsbedingung unverändert erfüllt blieb (Log:
`commands issued after dusk retract: []`, Position bleibt bei 0 %).

Eine alleinige Lösung „beim Einfahren `forget_shading_for_cover()`
aufrufen" wäre gefährlich unvollständig gewesen: ohne eine Sperre auf der
anderen Seite hätte dieselbe (unabhängige) Beschattungsbedingung die
Markise **sofort in derselben Minute** wieder ausgefahren, sobald der
Merker weg ist – bei `elevation_enabled=False` gibt es keinen natürlichen
Moment, der das verhindert. Deshalb eine abgestimmte Lösung an beiden
Enden: `awning_dusk.py` räumt `forget_shading_for_cover()` beim Einfahren
korrekt auf, und eine neue Funktion `is_dusk_retracted(data, cover)` wird
von `elevation.py` **vor** jeder Verlängerung/Neuausfahrt gefragt – solange
das Cover in `data["_dusk_retracted"]` steht, fasst die Beschattung es gar
nicht erst an. Erst wenn `awning_dusk.py` selbst wieder hell registriert
und den Eintrag entfernt, darf die Beschattung erneut entscheiden. Wind-,
Regen- und Frostschutz bleiben unberührt: `awning_guard.py` läuft
komplett unabhängig weiter und hat weiterhin Vorrang – eigens mit einem
Test abgesichert, der einen aktiven Wind-Guard **nach** einer
Dämmerungs-Freigabe prüft.

**Nebenbefund, geprüft statt geglaubt (kein Fehler): die
Minutentakt-Reihenfolge.** Beschattung, Wetterschutz und
Dämmerungsfunktion hängen am selben gemeinsamen Minutentakt
(`_setup_minute_ticker()`), aber jeder Callback stößt seine Auswertung
nur als eigenen `hass.async_create_task(...)` an – es gibt keine Garantie,
in welcher Reihenfolge die drei tatsächlich fertig werden, nur eine
Reihenfolge, in der ihre Tasks gestartet werden. Zwölf Regressionstests
(`tests/test_minute_tick_order_independence.py`) haben alle sechs
möglichen Reihenfolgen der drei Auswertungen durchgespielt, je einmal mit
und ohne aktive Gefahr – in keiner Reihenfolge ließ sich eine gesperrte
Markise ausfahren, in keiner blieb eine freie Markise unbeschattet. **Das
ist kein Zufall, sondern Architektur:** `evaluate_guard()` liest Sensor-
und Laufzeitzustand bei jedem Aufruf direkt, keines der drei Module
verlässt sich auf einen von einem anderen vorbereiteten Cache. Bewusst
**nicht** serialisiert – die Gegenprobe (Guard-Prüfung in
`_drive_sun_protect()` probeweise abgeschaltet) ließ alle sechs
„gesperrt"-Permutationen sofort umfallen, die Tests sind also scharf genug,
einen echten Reihenfolgefehler zu erkennen, hätte es einen gegeben. Der
Kommentar in `__init__.py`, der die Setup-Reihenfolge von
`setup_elevation_listener`/`setup_awning_guard` erklärte, war dabei selbst
irreführend („der Guard muss sein Verdikt schon kennen, wenn die erste
Beschattung fragt" – tatsächlich läuft `elevation.py` zuerst) und wurde
präzisiert: die Reihenfolge ist unerheblich, weil jeder Fahrweg den Guard
selbst prüft, nicht weil eine bestimmte Startreihenfolge das garantiert.

**Zweiter Nebenbefund, rein kosmetisch:** die Beschattungs-Logzeile
(`[sun-protect] area=…: elev=… in […]`) behauptete auch bei
`elevation_enabled=False` einen geprüften Höhenbereich – ausgerechnet für
die Konfiguration, die Fund 3 überhaupt erst brauchte. Sagt jetzt
„elevation check disabled", wenn die per-Rollladen zusammengeführte
Geometrie die Höhe für diese Fahrt gar nicht entschieden hat.

**Verifiziert:** `pytest` 826 Tests grün (23 neue). Für jeden der drei
bestätigten Fehler und für die Reihenfolgen-Frage eine **echte Gegenprobe**
gemacht – Fix jeweils testweise entschärft (`if False and …` bzw. einen
Aufruf auskommentiert), genau die zugehörigen neuen Tests fielen, alle
anderen 8xx blieben grün, danach der Fix wiederhergestellt und die volle
Suite erneut grün. Neue Dateien: `tests/test_window_trigger_stale_restore.py`,
`tests/test_minute_tick_order_independence.py`,
`tests/test_elevation_log_disabled.py`; erweitert:
`tests/test_resume_automation.py`, `tests/test_awning_dusk.py`. **Nicht im
Browser geprüft** – reine Backend-Logik, keine Panel-Änderung.

### 2026-09-06 – 2.22.1: der Schutz, der nur die Markise kannte

Kein Forumsbeitrag – ein Fund beim systematischen Durchgehen der gesamten
Beschattungs-/Schutzlogik für Rollläden, Markisen und Dachfenster, auf
eigene Anforderung hin (Bedingungslücken, Widersprüche, Zirkelbezüge).

**Der Fund:** `_drive_sun_protect()` in `elevation.py` fragte den
Wind-/Regen-/Frostschutz (`evaluate_guard`/`clamp_to_rest`) vor einer
Beschattungsfahrt nur unter `if awning:` – aus der Zeit, als die Markise
(2.12.0) die einzige geschützte Geräteart war. Seit das Dachfenster
(2.20.0) genau denselben Schutz bekam (`has_guard()` deckt beide ab), lief
diese eine Prüfstelle nicht mit: ein Dachfenster geriet in den
allgemeinen (Nicht-Markisen-)Zweig und konnte trotz aktiver Regengefahr
auf die Lüftungsspalt-Position hinausgefahren werden.

**Warum das schwerer wiegt als ein einmaliges Fehlverhalten.** Der Schutz
fährt pro Gefahrenepisode nur *einmal* zu (`state["retracted"]` in
`awning_guard.py`, damit er nicht gegen eine manuelle Korrektur ankämpft
– dieselbe Regel wie bei einer Markise). Ohne die Schutzabfrage im
Beschattungs-Fahrweg konnte die Beschattung ein einmal vom Schutz
zugefahrenes Dachfenster beliebig oft wieder öffnen, solange es
weiterregnete – der Schutz hielt sich für diese Episode für erledigt und
griff kein zweites Mal ein. Genau das Szenario, vor dem der 2.20.0-Log
warnt: „bei einem Dachfenster kostet ein verpasster Schutz Wasser im
Haus."

**Behoben mit der kleinstmöglichen Änderung:** das Schutz-Gate hängt jetzt
an `has_guard(shutter)` statt an `is_awning(shutter)` – eine reine
Umhängung, keine neue Prüfung. Die geräteartabhängige Positionsberechnung
(Markise vs. Dachfenster/Rollladen) bleibt unverändert im jeweiligen
Zweig stehen; nur die Frage „braucht dieses Gerät den Schutz" wurde von
der Frage „wie wird seine Zielposition berechnet" getrennt. Für Markisen
ist das exakt dieselbe Prüfung wie vorher, nur eine Codezeile weiter
unten. Für gewöhnliche Rollläden (`has_guard()` == False) läuft der Block
gar nicht erst an.

**Merke, wieder einmal:** dieselbe Fehlerklasse wie
`resolve_sun_geometry()` (2.10.3), `only_shutters` (2.16.0/2.20.0) und
`guard_rest_role`/`rest_role` (2.21.1) – eine neue Geräteart wird an einem
zentralen Vertrag ergänzt, aber nicht an jeder Stelle durchgezogen, die
denselben Vertrag konsultiert. Diesmal war es nicht ein Schlüssel-Tupel
oder ein Filter, sondern ein Sicherheits-Check vor einer Fahrt.

**Verifiziert:** `pytest` 803 Tests grün (4 neue), in
`tests/test_roof_windows.py`. Der Kern-Regressionstest fährt genau die
Reihenfolge nach, die den Fund ausmacht: Dachfenster öffnet bei
trockenem, warmem Zustand → Regen setzt ein, Schutz fährt einmal zu → es
regnet über mehrere weitere Minutentakte unverändert weiter → die
Beschattung darf nicht erneut öffnen. Dazu eine Gegenprobe mit allen drei
Gerätearten im selben Bereich am selben Regensensor: nur der ungeschützte
Rollladen beschattet normal, Markise und Dachfenster bleiben gesperrt.
Volle Suite `pytest` grün (803, zuvor 799). **Nicht im Browser geprüft** –
reine Backend-Logik, keine Panel-Änderung.

### 2026-09-05 – 2.22.0: die Markise, die abends von selbst geht

Direkte Umsetzung von [#12](https://github.com/fschubi/shutter_pilot/issues/12),
bjoergs Wunsch aus dem Forum: eine Markise soll abends bei Dämmerung
einfahren, aber **niemals** automatisch wieder ausfahren – schon gar nicht,
wenn niemand zuhause ist. Sein eigener Workaround (Helfer-Schalter unter
„Hochfahren unterbinden") griff nachweislich nicht: `only_shutters()`
schließt Markisen von genau diesem Fahrweg aus (`brightness.py`,
`scheduler.py`).

**Warum nicht die Beschattung.** `elevation.py` fährt eine Markise bei
Bedarf aus *und wieder ein* – dieselbe Bedingung, die abends auslöst, würde
am nächsten Tag genauso auslösen und die Markise erneut ausfahren. Genau das
war der Kern der Meldung: keine automatische Wiederausfahrt.

**Warum nicht ein vierter Guard-Slot.** `awning_guard.py` (Wind/Regen/Eis)
ignoriert Hauptschalter, Bereichsautomatik und die Automatik der Markise mit
Absicht – eine Böe darf nicht davon abhängen, ob jemand die Markise
ausgeschaltet hat. Ein Komfort-Wunsch wie „bei Dunkelheit einfahren" soll das
nicht: schaltet jemand die Automatik ab, soll auch diese Funktion still
sein. Deshalb ein eigener Bedingungs-Slot (`AWNING_DUSK_SLOT = "dusk"`),
dieselbe Mechanik wie überall (Zahl mit Hysterese, Zustandsliste, Boolean,
Invertierung), aber mit eigener, respektierender Prüfung.

**Neues Modul, kein neuer Timer.** `awning_dusk.py` haengt am gemeinsamen
Minutentakt wie `ventilation.py` und `awning_guard.py`. Fährt genau einmal
ein, wenn die Bedingung eintritt (`_dusk_retracted`-Merker gegen Motor-
Genöle), und bei Freigabe passiert **nichts** – keine Fahrt, keine
Ausnahme, einfach der fehlende Code für „wieder ausfahren". Ein zweiter
Dämmerungs-Zyklus nach einer hellen Phase darf wieder auslösen, sonst hülfe
das Feature nur einmal im Leben der Anlage.

**Der Merker-Fallstrick, diesmal im Voraus vermieden.** `_own_slot_met()`
liest `area.get(CONF_AREA_ID)` roh für den Hysterese-Speicher – bei einem
Rollladen mit echter Bereichs-ID ist das richtig, bei einer Markise ohne
eigene wäre es `""`, und **jede** Markise ohne Bereichs-ID würde sich einen
gemeinsamen Hysterese-Topf teilen. Deshalb `awning_dusk_condition_met()`
eigenständig, mit dem Cover als Speicherschlüssel
(`condition_memory(data, "dusk", cover)`) statt der Bereichs-ID – ein Test
hält das mit zwei Markisen ohne Bereich fest.

**Panel:** ein eigener, zusammenklappbarer Abschnitt „Bei Dämmerung
einfahren", nur an Markisen (nicht an Dachfenstern) – über `_renderCondDetail()`,
nicht `_renderGuardSlot()`, weil letzteres eine Sperrzeit mitbringt, die es
hier gar nicht gibt. Export: eine eigene Verdikt-Zeile mit Sensor, Schwelle
und aktuellem Zustand, nach demselben Muster wie der Wetterschutz.

**#12 ist damit erledigt**, aus „Geplant" in beiden READMEs wieder entfernt
– derselbe Platz, an dem laut 2.12.0-Log früher schon einmal ein Wunsch
(damals Markisen selbst) stand, bevor er gebaut wurde.

**Verifiziert:** `pytest` 799 Tests grün (20 neue), **fünf Gegenproben** –
ohne den Wiederholungsschutz feuert der Motor jede Minute; ohne den
`is_awning()`-Filter fährt auch ein Dachfenster mit; ohne die
Automatik-Prüfung am Rollladen fährt eine abgeschaltete Markise trotzdem;
ohne dieselbe Prüfung am Bereich ebenso; ohne die Export-Zeile fallen drei
neue Tests. i18n 444/444 in allen elf Sprachen (4 neu). Panel in Node
gerendert, mit einer eigenen Prüfung je Geräteart (Markise zeigt den
Abschnitt, Dachfenster nicht) – Gegenprobe gemacht. **Nicht im Browser
geprüft.**
