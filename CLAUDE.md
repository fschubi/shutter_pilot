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
tests/               pytest-Suite (1109 Tests)
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
Windschutz für Raffstores (2.25.0, `storm_guard`, eigener Slot `rwind`), Sperr-Entität
(`automation_lock_entity`) und Frostsperre (2.38.0, `frost_lock`, globaler Slot `cold`,
fail open): alle Opt-in; die Abfrage steht in `shutter_held()` neben
`is_shutter_automation_enabled()`.
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
- **Einfache / Experten-Ansicht** (2.40.0): reine Anzeige. Jeder Abschnitt steht in
  `BASIC_SECS`, `EXPERT_SECS` oder `UNFILTERED_SECS`; Experten-Abschnitte über `_xsec(used,…)`,
  Experten-Felder über `_adv(used, tpl)`. `used` hält sichtbar, was vom Standard abweicht.
  Ein neues Feld ohne Einstufung steht in beiden Ansichten.
- **Geführter Einstieg**: ersetzt das Dashboard, solange kein Rollladen angelegt ist.
- **i18n**: 11 Sprachen (de, en, fr, es, it, nl, da, sv, pl, pt, nb) im Objekt
  `I18N`. Jeder neue sichtbare Text braucht einen Schlüssel in **allen** elf;
  `t()` fällt sonst auf Englisch zurück. Seit 2.7.1 sind alle elf **vollständig**
  (Stand 2.40.0: je 575 Schlüssel) – das gilt es zu halten. Prüfskript: alle
  Sprachmengen gegen `de` halten, ist in zwanzig Zeilen geschrieben.

### WebSocket-API

| Befehl | Rechte |
| --- | --- |
| `shutter_pilot/get_status` | alle (lesend) |
| `save_area`, `delete_area`, `save_shutter`, `delete_shutter` | **Admin** |
| `save_settings`, `set_master_enabled`, `set_auto_mode`, `set_shutter_automation`, `set_sun_protect` | **Admin** |
| `set_ui_mode` (Ansicht, ohne Neuladen), `quick_setup` (Bereich + Rollläden in einem Zug) | **Admin** |

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
.venv/bin/pytest            # 1109 Tests, ~40 s
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

Version **2.40.1**, im Forum aktiv genutzt. Seit 18.10.2026 im
**HACS-Default-Store** (PR [hacs/default#9592](https://github.com/hacs/default/pull/9592), von frenck gemergt).

## Fortschritts-Log

Vollständige Historie (ältere Einträge) steht in `docs/CHANGELOG_DEV.md` – hier nur die letzten fünf, damit diese Datei nicht wieder über das Kontextlimit wächst. Neuer Eintrag kommt hier dazu; wird die Liste hier zu lang, wandert der älteste nach `docs/CHANGELOG_DEV.md`.

### 2026-11-22 – 2.40.1: Frostschutz-Umkehr, Frostschutz vs. Frostsperre (eurofinder, simon42 #262)

Seit 2.40.0 vier Beiträge (#259–#262); nur #262 mit Arbeit. eurofinder fragte, wozu es im
Bereich noch „Frostschutz" gibt, wenn die Frostsperre schon unter Einstellungen steht, und wozu
dort „Bedeutung umkehren" dient. **Zwei getrennte Funktionen:** Frostschutz (Bereichs-Slot
`frost`, Rolle `closed_frost`) kürzt nur die Abendfahrt, Frostsperre (`cold`, `frost_lock`) hält
alles an. **Fehler:** Der Umkehr-Haken war bei Zahlensensoren an `frost` (Bereich) und `ice`
(Markise) noch abwählbar – abgewählt = Wärmeschalter, dieselbe Falle wie 2.38.2 bei `cold`.
Neu `FORCED_BELOW_SLOTS` (frost, ice, cold) und `helpers.numeric_inverted(cfg, slot)`, das
`_slot_reading` **und** der Export (3 Stellen) benutzen – der Export las bei `cold` vorher noch
den gespeicherten Haken. Panel: `FORCED_BELOW_SLOTS`-Spiegel, `_condInverted` gibt dort im
Zahlenzweig immer true, Haken ausgeblendet (Bereich und Schutz-Slot). Bei eurofinder war der
Haken gesetzt, es wirkte also richtig – nur verwirrend. **Texte** ×11: `sec_frost` „Frostschutz
beim Schließen", `sec_frost_sub`, `f_frost_cond_hint` (verweist auf die Frostsperre),
`f_pos_closed_frost_val` „Frostschutz-Position (abends)" – vorher hießen beide Positionen
„Position bei Frost". README: Gegenüberstellungstabelle. Panel-Test `guard_slot.mjs` stellte das
alte Eis-Verhalten fest und ist umgestellt. **Verifiziert:** `pytest` 1109 grün
(`tests/test_frost_invert_forced.py`, 7); Gegenprobe: mit nur der alten `cold`-Regel fallen 4.
Nicht im Browser und nicht im echten Home Assistant geprüft. Keine neuen Schlüssel (je 575).

### 2026-11-15 – 2.40.0: Einfache Ansicht, Experten-Ansicht, geführter Einstieg

Wunsch von Schubi nach dem Urlaub: neue Nutzer sehen zu viel. **Der Modus blendet nur aus** –
kein Backend-Verhalten, kein gelöschter Wert. `CONF_UI_MODE` (`simple`/`expert`) in den Optionen,
nicht im Browser (Handy = PC, steht im Export). Ohne Schlüssel entscheidet
`helpers.effective_ui_mode()`: Rollläden vorhanden → Experte, sonst einfach; `DEFAULT_OPTIONS`
setzt `simple`. `save_shutter` und `quick_setup` schreiben den Wert fest, sonst kippt er mit dem
ersten Rollladen. Eigener Befehl `set_ui_mode` **ohne Neuladen** (save_settings lädt neu und
bricht Wartezeiten ab; es überspringt den Schlüssel deshalb). Panel: `_expert()`, `_xsec(used,…)`
für Abschnitte, `_adv(used, tpl)` für Felder, `_modeHint()` am Formularende (zählt über
`__hidden`), Listen `BASIC_SECS`/`EXPERT_SECS`/`UNFILTERED_SECS`. **`used` = weicht vom Standard
ab → bleibt sichtbar** (Abschnitt mit Marke „Experte"). Lamellen-Abschnitt zusätzlich, wenn der
Antrieb Bit 128 meldet (`_hasTilt`, streng). Markisen-/Dachfensterformulare ungefiltert, ihre
Reiter in „einfach" nur bei vorhandenen Einträgen. Beschattung liegt komplett in „Experte"
(Schubis Vorgabe: einfach = Zeit, Licht, Sonnenstand). **Geführter Einstieg** (`_renderWizard`):
aktiv, solange kein Rollladen existiert (Admin, nicht übersprungen, nicht `loading`); drei
Schritte, speichert über `quick_setup` in einem Schreibvorgang – `save_area` + n×`save_shutter`
scheitern am Neuladen dazwischen (`_find_entry_data` liefert dann nichts). Bestehender Bereich
bekommt nur Name, Modus und die Zeiten des Modus. `get_status` meldet im Neulade-Loch
`loading: true`, sonst blitzt der Einstieg bei jedem Speichern auf. `_newArea()`/`_newShutter(d)`
aus den Knöpfen herausgezogen. i18n 26 Schlüssel ×11 (je 575). Tests: `tests/test_ui_mode.py`
(21), `tests/panel/ui_mode.mjs` (69 Prüfungen), Vorlage nach `tests/panel/fixture.mjs`.
**Verifiziert:** `pytest` 1102 grün; Gegenproben: sechs gezielte Brüche im Panel und ohne das
Festschreiben in `save_shutter` fällt je mindestens ein Test. Im Browser mit echtem Lit durchgeklickt (Wegwerf-Seite mit
Stub-`hass`, ohne HA-Theme): Einstieg bis `quick_setup`, einfache Formulare, Marke, Hinweis,
Umschalten. **Nicht geprüft:** im echten Home Assistant, mobil, HA-Theme (hell/dunkel).
**Neues Feld künftig:** in `_adv`/`_xsec` einstufen, sonst steht es in beiden Ansichten.

### 2026-11-15 – 2.39.0: Forum nach dem Urlaub (#249–#253)

Fünf neue Beiträge seit dem 06.11., zwei davon mit Arbeit. **Claus (#249):** Diele im
Helligkeitsmodus, Hoch-Fenster 05–12 Uhr, Sensor ist ein Template (0 lx bei Licht an). Um 15:35
Abendfahrt, um 15:40 (Licht aus, 1000 lx) wieder hoch. Ursache `_pending_up` in `brightness.py`:
die Vormerkung „im Fenster dunkel, heute noch hochfahren" entstand auch *nach* der Morgenfahrt,
eingelöst wird sie nur von einer Fahrt, die es dann nicht mehr gibt (`_run_up` liefert False,
alles ist oben) – sie blieb bis Mitternacht und galt abends als „im Fenster". Fix: vorgemerkt
wird nur, solange `_up_outstanding(area_id)` (ein Rollladen des Hoch-Bereichs nicht in
`covers_driven_up`); die Abendfahrt beendet sie (`_forget_pending_up` je gefahrenem Rollladen
über dessen **Hoch**-Bereich, dazu der Bereich selbst, sobald die Runter-Bedingung hält – auch
wenn nichts zu fahren war). Der Export war nach einem Neuladen gezogen, die Vormerkung selbst
ist darin nicht belegt; der Ablauf ist aus den Einstellungen nachgestellt. Export zeigt sie
jetzt unter „Laufender Zustand". **heinzel (#252):** will im Winter kurz aus der Tür, zieht sie
zu und ist nach 30 s (Obergrenze der Entprellung) ausgesperrt. Neu `window_close_delay_minutes`
(0–120, Vorgabe 0), in `_close_delay_seconds()` auf die Entprellung addiert – derselbe Task,
dasselbe Abbrechen beim Wiederöffnen. Bewusst ein eigenes Feld statt einer höheren Obergrenze:
die Entprellung fragt „war das wirklich zu?", das hier „ich komme gleich wieder". bjoerg (#253)
empfahl den Griffsensor, das bleibt die sauberere Lösung. **Nicht abgedeckt:** Neustart/Neuladen
bricht die Wartezeit ab, der Zyklus bleibt dann „triggered" bei geschlossenem Fenster.
Frankchief (#250): nur Frage (zwei Himmelsrichtungen → Geometrie am Rollladen überschreiben).
Panel: Regler, i18n 2 Schlüssel ×11 (je 549). **Verifiziert:** `pytest` 1080 grün (6 + 11 neue);
Gegenprobe: ohne den Fix fallen 4 der 6 Vormerkungs-Tests. Nicht im Browser, nicht im echten
Home Assistant geprüft. **Geplant, nicht gebaut:** Einfach-/Expertenmodus im Panel.

### 2026-11-06 – 2.38.2: Frostsperre nachgeprüft (eurofinder, simon42 #244)

eurofinder fragte, wozu „Bedeutung umkehren" bei der Frostsperre da ist, und sah beim Abwählen
Markisen-Text. Beides stimmte; drei Prüfagenten (Panel, Backend, Texte) fanden mehr.
**Invert:** `_slot_reading` erzwingt bei `FROST_LOCK_SLOT` im Zahlenzweig „kälter als" und liest
den gespeicherten Haken nicht mehr (alte Abwahl wirkt nicht nach); Binärsensor/Zustandsliste
behalten die Umkehr. Panel blendet den Haken bei Zahlen aus; eigene Texte mit Suffix `_cold`
(`no_threshold`, `wrong_way`, `bin_hint`, `states_hint`, `lockout`), Warnung bei „Sperren unter"
> 10 (`f_cold_high_warn`), Warnung am Rollladen ohne Sensor (`f_frost_lock_no_sensor`), Abwahl
leert Position/Lamellen; vier Texte überarbeitet (`f_frost_lock_hint` nennt jetzt auch
Sichtschutz, Stufe 2, Referenzfahrt und die Frostposition als einzige Ausnahme).
**Backend:** Die Frostfahrt prüft jetzt Fenster, Sichtschutz und Windschutz (`async_frost_hold`,
Marker gilt trotzdem); ein toter Sensor beendet eine *laufende* Sperre nicht
(`unreadable` aus `evaluate_guard`, `barred` bleibt); der Marker steht im `position_store`
(`frost_held`) und kommt in `setup_awning_guard` zurück – Neustart/Neuladen fährt nicht doppelt
und erkennt ein Frostende danach; `async_frost_release` vergisst Fensterzyklus und
Nachhol-Fahrt; Lamellen nur mit `tilt_enabled`. Export: „frei" statt „darf ausfahren", neutraler
Gefahr-Satz. README: Dachfenster-Beispiel falsch (nur Rollläden), Referenzfahrt ergänzt.
**Nicht gemacht:** Server-Validierung der Werte (`_ws_save_*`), Fahrtkontrolle gegen die Sperre,
Referenzfahrt mitten im Lauf stoppen, Nachholen im Helligkeitsmodus nach Licht statt Uhr.
**Verifiziert:** `pytest` 1063 grün (8 neue Backend-, 9 Panel-Fälle); Gegenproben: ohne
Zwangs-Invert, Fenster-, Storm-Check, Restore und Vergessen fällt je ein Test. Nicht im Browser,
nicht im echten Home Assistant geprüft.

### 2026-11-06 – 2.38.1: Textfehler Frostsperre, Schutz ausgegraut (eurofinder, simon42 #242)

Der gemeinsame Hysterese-Satz (`f_guard_hyst_hint`) sprach von der „Markise" und stand auch
unter Frostsperre und Windschutz für Raffstores – jetzt neutral („der Schutz"), ×11. Der
Abschnitt „Wind- und Regenschutz für Markisen" wird ausgegraut (`_sec(..., dim)`, Klasse
`.sec.dim`), solange weder Markise noch Dachfenster existiert (`hasGuard`); bleibt
aufklappbar. Neuer Schlüssel `sec_guard_none` ×11 (je 540). **Verifiziert:** `pytest` 1055
grün, i18n-Parität. Nicht im Browser geprüft.

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
