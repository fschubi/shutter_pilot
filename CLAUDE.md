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
  privacy.py         Sichtschutz: Entität stellt den Rollladen auf eigene Position
  reference_run.py   Referenzfahrt für Raffstores (auf, zu, zurück)
  weather_data.py    Tagesvorhersage über weather.get_forecasts
  group_actions.py   Folgeaktion Licht je Bereich
  switch/sensor/binary_sensor.py   Entitäten
  services.py        Dienste (Gruppenaktionen)
  frontend/shutter-pilot-panel.js  Das komplette Panel (~4800 Z., ein File)
tests/               pytest-Suite (1043 Tests)
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
Dazu `window_keep_open_minutes` (2.37.0, Vorgabe 0): schließt das Fenster kurz vor
der Hochfahrt des Up-Bereichs, entfällt die Rückfahrt (`opening_follows_soon()`).
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
.venv/bin/pytest            # 1043 Tests, ~21 s
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

Version **2.37.0**, im Forum aktiv genutzt. Seit 18.10.2026 im
**HACS-Default-Store** (PR [hacs/default#9592](https://github.com/hacs/default/pull/9592), von frenck gemergt).

## Fortschritts-Log

Vollständige Historie (ältere Einträge) steht in `docs/CHANGELOG_DEV.md` – hier nur die letzten fünf, damit diese Datei nicht wieder über das Kontextlimit wächst. Neuer Eintrag kommt hier dazu; wird die Liste hier zu lang, wandert der älteste nach `docs/CHANGELOG_DEV.md`.

### 2026-11-04 – 2.37.0: Fenster zu kurz vor der Hochfahrt (Horst, simon42 #233)

Horst lüftet das Bad vor Sonnenaufgang: Fenster auf → Rollladen hoch, Fenster zu →
Rollladen zurück auf zu, obwohl die Hochfahrt Minuten später kommt. Neu je Rollladen
`window_keep_open_minutes` (0–240, Vorgabe 0 = aus). `window_trigger.
opening_follows_soon()` fragt `get_next_action()` des **Up-Bereichs**: nächster
Termin ist eine Hochfahrt innerhalb der Minuten **und** `automated_up_blocked()` ist
None (sonst bliebe er den ganzen Tag offen). Helligkeitsmodus zählt nie (kein fester
Zeitpunkt). Gespart wird nur eine Rückfahrt *nach unten*; der Zyklus (`trigger_actions`/
`trigger_heights`) wird trotzdem beendet. Der `drive_after_close`-Zweig bleibt
unberührt. Panel: Regler 0–240/5, i18n 2 Schlüssel ×11 (je 523). **Verifiziert:**
`pytest` 1043 grün (7 neue, `tests/test_window_keep_open.py`); Gegenprobe: ohne die
Prüfung fällt der Kernfall. Nicht im echten Home Assistant geprüft.
Außerdem Forum-Antwort an eurofinder (#234): Frostschutz ändert nur die Schließposition
und stoppt keine Fahrt – „nicht fahren bei Frost“ geht über eine Zusatzbedingung
mit Hysterese oder die Sperr-Entität (Schwellwert-Helfer).

### 2026-11-03 – 2.36.0: Beschattungspause nach Handfahrt, Dashboard-Zeilen

Claus (#229): Beschattung soll nach einer Handfahrt (Höhe oder Lamellen) pausieren,
bis die Sonne das Fenster verlässt, optional mit Höchstdauer. Bereichshaken
`shade_pause_on_hand` + `shade_pause_max` (Minuten, 0 = ohne). In
`elevation._evaluate` über `_hand_pause_holds()`: Phase = `protect_on` und
Geometrie und Jahreszeit und Zeitfenster (**ohne** Bedingungen – eine Wolke
beendet die Pause nicht). Start der Phase merkt `_shade_phase[cover]`; eine
Handfahrt (`_hand_moved_at`) *danach* setzt `_shade_paused`, `_shade_pause_seen`
verhindert, dass ein abgelaufener Stempel erneut pausiert; eine weitere Handfahrt
startet die Uhr neu. Pausiert wird ein Rollladen komplett (`continue`: weder
beschatten noch nachfahren noch freigeben); endet die Phase, läuft der normale
Freigabepfad. Handfahrten *vor* der Phase zählen nicht. **Nicht abgedeckt:** nach
einem Neustart beginnt die Phase neu, ältere Handfahrten werden ignoriert.
Dashboard: Zeile `flex-wrap`, Name mind. 130 px, Lamellen-Knöpfe mit −/+,
`_tiltReading()` hängt „· L 60 %“ an die Höhe. i18n 3 Schlüssel ×11.
Claus' Frage, ob die zweite Öffnungsstufe auch noch nach der Uhrzeit feuert, wenn
die Bedingung erst später zutrifft: ja, jede Minute ab der Uhrzeit, einmal am
Tag; steht die Beschattung gerade, wartet sie bis zur Freigabe.
**Verifiziert:** `pytest` 1036 grün (7 neue, `tests/test_shade_pause.py`);
Gegenproben: ohne Haken fallen 5, ohne Höchstdauer 1, ohne Phasenende 1. Nicht
im Browser und nicht im echten Home Assistant geprüft.

### 2026-11-03 – 2.35.0: zweite Öffnungsstufe

Claus (#225): Diele morgens nur Lamellen, ab 10 Uhr bei Anwesenheit und schönem
Wetter ganz hoch. Haken `open_stage2` mit `open_stage2_time` (10:00),
`open_stage2_entity` (leer = keine Bedingung, tot = nein) und eigener Rolle
`ROLE_OPEN_STAGE2` (Position/Lamellen/Keep in den vier Tabellen). Eigenes Modul
`open_stage2.py` im Minutentakt. **Vollendet nur, was begonnen wurde:** der
Rollladen muss in `covers_driven_up` stehen und nicht in `covers_driven_down` –
so löst eine am Morgen gesperrte Hochfahrt (Wochenende, Sichtschutz, `no_up`)
keine Stufe 2 aus, und die Abendfahrt beendet den Tag. Übersprungen bei: System
/Automatik aus, Sichtschutz, offenem Fenster, Beschattung aktiv, Handfahrt heute
(`_hand_moved_today` aus der monotonen Zeit und der Zeit seit Mitternacht). Einmal
am Tag (`_open2_done`), im Speicher, nicht über den Neustart – der leert aber
auch `covers_driven_up`, sodass nach einem Neustart nichts nachfeuert.
Panel: Haken, Uhrzeit, Entität, Position/Keep, Lamellen; i18n 6 Schlüssel ×11.
Nicht im echten Home Assistant geprüft.

### 2026-11-03 – 2.34.0: Sichtschutz mit zweiter Stellung bei Sonne

Claus (#226) löste „TV an, Lamellen 50, bei Blendung zu“ mit einer Zusatz-Automation
und musste die Lamellen-Handerkennung dafür abschalten (seine Automation bewegt
am Tracker vorbei). Jetzt Haken `privacy_sun` mit eigener Rolle `ROLE_PRIVACY_SUN`
(Position/Lamellen/Keep, alle in den vier Rollentabellen). `privacy_role()` fragt
nur die **Geometrie** (`sun_protect_conditions_met` mit `resolve_shading_config`),
nicht Bedingungen, Zeitraum oder Fenster: die beschreiben den Haushalt, nicht die
Sonne. `privacy.py` wählt die Rolle beim Start und im Minutentakt; bei Wechsel
fährt `_switch_role()` neu, behält aber den Rückkehr-Zustand (`pos`/`tilt`) und
erneuert `at` und `sent`, damit Ende und Handfahrt-Vergleich auf der neuen
Stellung rechnen. Eine Handfahrt nach der letzten Sichtschutzfahrt wird nicht
überfahren. Panel: Haken mit Position/Lamellen, i18n 4 Schlüssel ×11.
Nicht im echten Home Assistant geprüft; kein Halte-/Hysterese-Verhalten an der
Sonnenkante (Minutentakt, die Grenze ist selten scharf).

### 2026-11-03 – 2.33.0: Lamellen-Knöpfe im Dashboard

Claus (#225): Höhe fahren geht auf der Übersicht, Lamellen nicht. `_rowButtons()`
zeigt bei `tilt_enabled` zwei Knöpfe (−/+ `TILT_STEP` 10 %), `_tiltStep()` liest
`current_tilt_position` (ohne Meldung ab 50) und ruft `cover.set_cover_tilt_position`
direkt auf – Zeilenknopf wie die anderen: von Hand, ohne Rollladenschalter, ohne
Riegel. Kein Gruppenknopf. Node-Test `tests/panel/tilt_buttons.mjs`; i18n
2 Schlüssel ×11. Nicht im Browser geprüft.


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
