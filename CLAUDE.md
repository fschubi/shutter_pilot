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
tests/               pytest-Suite (939 Tests)
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
Zwei weitere Haken (2.24.0, beide ohne Migration): `window_react` (Vorgabe an;
aus = der Kontakt bewegt nichts, hält nur automatische Fahrten zurück) und
`drive_after_close_up` (Vorgabe aus; hält auch die **Hochfahrt** zurück –
bewusst nicht unter `drive_after_close`, das würde bestehenden Nutzern die
Morgenfahrt nehmen).
Windschutz für Raffstores (2.25.0, `storm_guard`, eigener Slot `rwind`) und
Sperr-Entität (`automation_lock_entity`): beide Opt-in; die Abfrage steht in
`shutter_held()` neben `is_shutter_automation_enabled()`.
Höhe/Lamellen je Zustand "unverändert" (2.26.0, `keep_*`, `role_position()`)
und `tilt_after_position`: ebenfalls Opt-in, `set_cover_position(position=None)`.

An einem Antrieb ohne Positionierung gibt es eine dritte Stellung: die am Motor
angelernte **„My"-Position** (`my_position_entity` + `my_position_pct`, RTS über
Overkiz als `button.*`). `my_position_target()` greift im Rückfallzweig
von `_send_position()` und, seit 2.27.1, auch bei `blind_drive` an einem
Antrieb, der Positionen kann; sonst ist die Zahl die genauere Anweisung.

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
  Viermal doppelt gebaut: Mindestabstand, Markisensperre, Aussperrschutz, Bereichs-Verzögerung (2.27.0). Bei
  einem neuen Riegel ist die erste Frage, ob das Panel ihn kennt. Trennung:
  **Gruppenknopf = Bereich handelt** (Rollladenschalter gilt), **Zeilenknopf und
  Dienste = von Hand** (gilt nicht – sonst ist ein reparierter Antrieb nicht
  prüfbar).
- **i18n**: 11 Sprachen (de, en, fr, es, it, nl, da, sv, pl, pt, nb) im Objekt
  `I18N`. Jeder neue sichtbare Text braucht einen Schlüssel in **allen** elf;
  `t()` fällt sonst auf Englisch zurück. Seit 2.7.1 sind alle elf **vollständig**
  (Stand 2.23.0: je 446 Schlüssel) – das gilt es zu halten. Prüfskript: alle
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
.venv/bin/pytest            # 939 Tests, ~21 s
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

Version **2.27.1**, im Forum aktiv genutzt. Seit 18.10.2026 im
**HACS-Default-Store** (PR [hacs/default#9592](https://github.com/hacs/default/pull/9592), von frenck gemergt).

## Fortschritts-Log

Vollständige Historie (ältere Einträge) steht in `docs/CHANGELOG_DEV.md` – hier nur die letzten fünf, damit diese Datei nicht wieder über das Kontextlimit wächst. Neuer Eintrag kommt hier dazu; wird die Liste hier zu lang, wandert der älteste nach `docs/CHANGELOG_DEV.md`.

### 2026-10-27 – 2.27.1: zwei Fehler aus der Issue-Durchsicht (#20, #21)

Beim Durchgehen aller offenen GitHub-Issues blieben zwei echte Fehler übrig;
die anderen waren erledigt (#13, #17, #18, #19 geschlossen) oder Wünsche
(#14, #16, #11) bzw. ungeklärt (#15, wartet auf Rückmeldung).

**#20 (StephanD77):** `services.py` verwarf die Merker des Fenstertriggers
nie. Handfahrt (2.23.0) und interne Hochfahrt tun es
(`forget_window_cycle`, `clear_stale_window_cycle_after_automated_up`), die
Dienste liefen daran vorbei – im Modus „Kein Zeitplan" mit externem Scheduler
der einzige Fahrweg. Nachgestellt mit seiner Sequenz (Nachtfahrt, Fenster auf,
`open_group` bei offenem Fenster, Fenster zu). Jetzt verwirft `_drive_group()`
und `resume_automation()` `trigger_actions`/`trigger_heights` und die
wartende Nachholfahrt, **wenn tatsächlich etwas gesendet wurde** (Höhe oder
Winkel); `stop_group` fährt nichts und lässt die Merker stehen. Dieselbe
Fehlerklasse wie 2.22.3/2.23.0 – siebtes Mal: eine neue Handlung, die einen
Merker nicht kennt.

**#21 (Reinhard-M):** `_send_position()` drückte die My-Position nur im
Zweig „Antrieb kann kein `set_cover_position`". Ein Jarolift-Controller kann
beides und meldet nichts zurück. Mit `blind_drive` und My-Position gewinnt
jetzt der Knopf, wenn das Ziel in die Toleranz fällt (`my_position_target`);
ohne den Haken bleibt die Zahl die genauere Anweisung.

**Ein bestehender Test musste sich ändern:** `test_forum_2_18.py::
test_a_drive_that_can_position_is_left_alone`. Die Hilfsfunktion `_awning()`
setzt `blind_drive` standardmäßig an, der Test meinte aber den gewöhnlichen
Antrieb *mit* Rückmeldung. Jetzt ausdrücklich `blind_drive: False`; die Absicht
(Zahl gewinnt beim Antrieb mit Rückmeldung) bleibt geprüft.

**Verifiziert:** `pytest` 939 grün (11 neue: `tests/test_services_forget_
window_cycle.py` und `tests/test_my_position_blind_drive.py`). Gegenproben:
ohne das Verwerfen fallen 4, ohne den Vorrang des Knopfes 2. Nicht im echten
Home Assistant geprüft.

### 2026-10-27 – 2.27.0: Reihenfolge, Knopf-Verzögerung, Sensor-Formular

Aus den letzten beiden Forumsbeiträgen: DerTomm (#213, GitHub #17/#18) und
Frankchief (#212 samt Export).

**A – Verzögerung gilt nicht für die Dashboard-Knöpfe (Bug #18).**
`_coverAction()` im Panel kannte nur `min_drive_gap`; die Bereichs-
Verzögerung (`drive_delay`) wirkt serverseitig in jedem Fahrweg, die Knöpfe
rufen aber direkt `cover.*` auf und sind damit an ihr vorbeigelaufen – ein
weiterer Riegel, der im Panel doppelt gebaut werden muss (Liste in „Panel":
Mindestabstand, Markisensperre, Aussperrschutz, **jetzt auch Bereichs-
Verzögerung**). `_driveDelaySec()`: das Größere aus Bereich und Mindestabstand,
Hoch nach `area_up_id`, sonst `area_down_id`, Bereich ohne gespeicherten Wert =
Vorgabe 10 (`DEFAULT_AREA_DRIVE_DELAY` im Panel gespiegelt). *Stop* wartet nie.
**Bekannte Grenze:** die Abfolge läuft im Browser-Tab; schließt jemand das
Panel mitten drin, fahren die restlichen nicht. Der Weg über die Dienste
(`close_group` …) wäre robuster, ändert aber die Rechte-/Schalter-Semantik
der Knöpfe (siehe Panel-Abschnitt) und blieb deshalb außen vor.

**B – Reihenfolge (Wunsch #17).** Gespeichert wird die Reihenfolge der
`shutters`-Liste; jeder Fahrweg läuft sie ab, das Dashboard zeigt sie unsortiert
(der Rollläden-Tab ist alphabetisch). Neuer Admin-Befehl
`shutter_pilot/reorder_shutters` (`_reordered_shutters()`: Genannte zuerst,
Rest dahinter, unbekannte Namen übergangen, Duplikate behalten – ein
unvollständiger Aufruf kann nie einen Rollladen verlieren). Kein Neuladen bei
unveränderter Reihenfolge, weil ein Neuladen die Laufzeit-Merker nullt. Im
Panel: Sortier-Knopf je Bereichskarte, Pfeile, Tausch in der *globalen* Liste
mit dem Nachbarn der Bereichsansicht, **eine** Speicherung 2,5 s nach dem
letzten Klick, `_pendingOrder` überlebt ein `_load()` dazwischen. Bereiche
untereinander bleiben gleichzeitig (jeder Bereich ein eigener Task); der
globale Mindestabstand staffelt sie in Bereichsreihenfolge. Eine echte
Reihenfolge *zwischen* Bereichen wäre eine eigene Änderung.

**C – Sensor-Formular.** Frankchiefs Export: Wind-Sensor ohne Schwellen
(„Zahlenschwelle nie eingetragen" = Gefahr, die Markise bleibt drin) und
`sun_cond_ice_invert: nein` ausdrücklich gespeichert – Frost ist voreingestellt
umgekehrt, das Panel schreibt den Schlüssel erst beim *Klick* auf die Checkbox,
er hat also eine von drei gleich aussehenden angeklickt. Rahmen mit Titel je
Schutz, Warnung „keine Schwelle" (nicht je Markise: dort erbt ein leeres Feld
den globalen Wert) und „Werte verkehrt herum" (wie bei den Bedingungen).
**Meine Antwort im Forum war falsch:** bei einem Binärsensor (Regen State
Piezo) gibt es nichts auszuwählen, „an" ist Gefahr; die Zustandsliste gibt es
nur bei Text-Sensoren. In der Antwort richtiggestellt.

**Verifiziert:** `pytest` 928 grün (8 + 4 neue; Node-Tests `drive_delay.mjs`,
`reorder.mjs`, `guard_slot.mjs`). Gegenproben: ohne Bereichs-Verzögerung fällt
der Knopf-Test, ohne Tausch der Reorder-Test, ohne Befehl-Sortierung sechs,
ohne die beiden Warnungen der Formular-Test. **Nicht im Browser und nicht im
echten Home Assistant geprüft** – besonders die Pfeile und der Rahmen.

### 2026-10-26 – 2.26.1: der Unten-Merker, der die Hand nicht kannte

Claus (simon42 #207, Export der Diele): Abendfahrt durch Sichtschutz
(Template-Sensor 0 lx bei Licht an), Raffstore von Hand auf 98 % gehoben
(`position_open` 50 – also **Zwischenposition**), Dämmerung 17:19 fuhr nicht
zu. Nachgestellt, bevor irgendetwas geändert wurde. Ursache:
`note_manual_position()` buchte nur die zwei Endlagen, eine Zwischenposition
ließ den Unten-Merker stehen – und `brightness._run_down` springt über jeden
Rollladen in `covers_driven_down` (die Zeile steht *vor* der Episoden-Prüfung
aus 2.23.1).

**Fix in zwei Teilen, weil Teil 1 allein ein Loch aufgemacht hätte:**
1. Zwischenposition löscht den Unten-Merker (der Oben-Merker bleibt).
2. Jede Handfahrt schreibt `data["_hand_moved_at"][cover]` (monotone Zeit wie
   die Episoden); `_run_down` fasst einen Rollladen nicht an, wenn nach dem
   Beginn der laufenden Dunkel-Episode von Hand gefahren wurde (strikt `>`).
   Ohne Teil 2 fuhr „von Hand zu, im Dunkeln ein Stück auf" bei der nächsten
   Lux-Meldung wieder zu: der Rollladen hatte keinen `down_fired`-Eintrag,
   weil nicht die Helligkeit ihn zugefahren hatte (das gilt für Endlagen-Auf
   schon seit 2.23.1 – dort jetzt ebenfalls abgedeckt).

**Ein bestehender Test musste sich ändern:** `test_forum_2_17.py::
test_a_position_in_between_says_nothing` hielt genau die alte Entscheidung
fest („dazwischen sagt nichts", 2.17.0). Umgeschrieben auf „löscht den
Unten-Merker, lässt den Oben-Merker" mit Begründung im Docstring; alle
anderen Tests blieben unverändert grün.

**Kleinigkeit aus derselben Meldung:** der Export schreibt `manual_override`
mit der Panel-Beschriftung dazu (`never` las Claus als „nie").

**Bewusste Verhaltensänderung:** ein von Hand auf eine Zwischenposition
gefahrener Rollladen wird im Helligkeitsmodus in der nächsten Dunkel-Episode
wieder zugefahren (vorher: nie, bis zum nächsten Tag), und eine „spätestens
runter"-Frist (`episode=None`) fährt ihn einmal zu. Zeit- und Sonnenmodus
unberührt.

**Verifiziert:** `pytest` 916 grün (5 neue, `tests/test_hand_lift_new_episode.py`).
Gegenproben: ohne Löschen des Merkers fallen der Claus-Test und der
umgeschriebene 2.17-Test, ohne Zeitpunkt der Test „von Hand zu, im Dunkeln
gehoben". Nicht in echtem Home Assistant geprüft.

### 2026-10-24 – 2.26.0: Höhe und Lamellen getrennt (Raffstore, Stufe 3)

Claus (#172, #196), sein erklärter Kern: je Zustand „Position oder Lamellen
unverändert". Eine leere Zahl heißt im Panel „Vorgabe nehmen", nicht „nicht
fahren" – deshalb **eigene Haken** statt eines Leerwerts:
`keep_position_{open,closed,sun_protect}` und `keep_tilt_{open,closed,
sun_protect}` (ein Tilt-Haken gilt für alle Rollen, die diesen Winkel lesen,
also auch `closed_alt`/`closed_frost`; `keep_position_*` nur für die drei
Grundrollen). Alle aus, wenn der Schlüssel fehlt.

**Umsetzung:** `get_position_for_role()` bleibt die Zahl, die Entscheidungen
lesen (`manual_position_is_a_close`, "gilt als oben"...). Neu
`role_position()` gibt `None` für "Höhe lassen" und wird nur dort gefragt, wo
der Befehl tatsächlich gesendet wird: Scheduler, Helligkeit (auf/ab),
Beschattung (Anwenden und Freigabe), Gruppendienste, `resume_automation`.
`get_tilt_for_role()` liefert bei "Lamellen lassen" `None`, das jeder
Aufrufer schon als "keinen Winkel senden" las. `set_cover_position()` nimmt
`position=None`: nur Winkel senden, nichts speichern, nichts prüfen;
beides `None` = nichts tun. Der Aussperrschutz-Deckel
(`get_effective_close_position`) und die Nachholfahrt (`position=None` auch
auf der Platte) kennen `None`. Flag ohne `tilt_enabled` wird ignoriert
(`position_kept` prüft es), damit ein Rest keine Rolle zum No-op macht.

**Lamellen nach der Höhe:** `tilt_after_position` (Vorgabe aus). Hintergrundtask
(`hass.async_create_background_task`, **nicht** `async_create_task`: ein
getrackter Task hielt `async_block_till_done` und den HA-Shutdown bis zu
drei Minuten auf – so hing der erste Testlauf), pollt alle 2 s, spätestens
nach 180 s wird der Winkel trotzdem gesendet; eine neue Fahrt ersetzt ihn.

**Bewusst offen:** `shade_only_when_open` (`shading_would_open_cover`) liest
weiter die Zahl von `position_sun_protect`, auch bei "Höhe lassen" – sie
beschreibt dann nichts mehr. Wer beides nutzt, merkt es als "beschattet nie".
Nicht angefasst: Lüftungs- und Fensterpositionen (eigene Zahlen).

**Panel/Export:** `keepRow` blendet den Schieber bei gesetztem Haken aus;
Export nennt die betroffenen Zustände. i18n 6 neue Schlüssel ×11.

**Verifiziert:** `pytest` 910 grün (18 neue in
`tests/test_keep_position_and_tilt.py`, 1 in `test_panel.py`). Gegenproben:
ohne `role_position`-Keep fallen 4, ohne Tilt-Keep 3, ohne Winkel-nach-Höhe 1,
ohne Lamellen-Prüfung 2. **Nicht im Browser und nicht im echten Home
Assistant geprüft.** Lamellen-Rückmeldung des KNX-Aktors (2 % statt 0 %) ist
Stufe 4.

### 2026-10-24 – 2.25.0: Sturm für Raffstores und die Sperr-Entität (Stufe 2)

Florian (#193) und Claus (#196, #202). Entwurf in `docs/PLAN_RAFFSTORE.md`,
Entscheidungen bestätigt: Sturm sperrt nur die **Automatik** (Hand frei),
ignoriert Haupt- und Automatikschalter wie bei Markisen, fährt auch durch
eine Sperr-Entität hindurch.

**2a Wind.** Opt-in `storm_guard` (Vorgabe aus), eigene Zielwerte
`storm_position`/`storm_tilt` (100/100, **nicht** `position_open` – bei
Raffstores unten). Eigener Slot `rwind` in `STORM_GUARD_SLOTS`, bewusst
**nicht** in `AWNING_GUARD_SLOTS`: die Markisenschleife läuft über dieses
Tupel. Dieselbe Slot-Mechanik, deshalb gehen Windgeschwindigkeit mit
Hysterese (Florian) und Alarm-Binärsensor (Claus) ohne neuen
Auswertungscode. `evaluate_guard`/`resolve_guard_config` bekamen einen
`slots`-Parameter mit der alten Liste als Vorgabe; zweite Schleife in
`async_enforce_guard`. `has_guard()` blieb unangetastet (rund 15 Stellen).
Sturm sperrt über `shutter_held()` in Scheduler, Helligkeit, Beschattung,
Lüften und Fenstertrigger; die Abfrage steht *neben*
`is_shutter_automation_enabled`, nicht an ihrer Stelle – ein bestehender Test
patcht den Namen in `brightness` (ein erster Versuch, ihn zu ersetzen, ließ
genau diesen fallen).

**2b Sperr-Entität.** `automation_lock_entity` je Rollladen, `on` = nichts
Automatisches. Fail open (fehlende Entität sperrt nicht), keine Nachholung.
`cover_verify._verify` wiederholt und meldet bei gesperrtem Cover nichts
(Claus' Aktor verriegelt sich selbst). Der Fenstertrigger *behält* eine
Vormerkung bei Sperre (anders als bei ausgeschalteter Automatik).

**Panel/Export:** Abschnitt „Windschutz Raffstore" im Formular (sichtbar mit
Lamellen), globaler Wind-Sensor für Raffstores unter Einstellungen,
Sperr-Entität im Formular, i18n 13 neue Schlüssel ×11. Der Haken trägt die
Vorgaben 100/100 selbst ein, sonst zeigte der Schieber 0 % und das Backend
führe mit 100 %. Export: Windschutz-Tabelle und Sperr-Zeile.

**Verifiziert:** `pytest` 891 grün (19 neue in
`tests/test_raffstore_storm_and_lock.py`, 1 in `test_panel.py`). Gegenproben:
ohne Sturmschleife fallen 5, ohne Sperr-Entität 1, ohne Sturmhalt 1, ohne
Verify-Sperre 1; die Kontrollfälle (Haken aus, Markisen) bleiben grün.
**Offen:** nicht im Browser und nicht im echten Home Assistant geprüft;
Lamellen-Rückmeldung des KNX-Aktors (2 % statt 0 %, kurz Lamellen 0) ist
Stufe 4.

## graphify

This project has a knowledge graph at `graphify-out/` with god nodes,
community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when
  `graphify-out/graph.json` exists. Use `graphify path "<A>" "<B>"` for
  relationships and `graphify explain "<concept>"` for focused concepts.
  These return a scoped subgraph, usually much smaller than
  `GRAPH_REPORT.md` or raw grep output.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation instead
  of raw source browsing.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or
  when `query`/`path`/`explain` do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current
  (AST-only, no API cost).
