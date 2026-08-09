# CLAUDE.md – Arbeitsgrundlage & Fortschritts-Doku

Diese Datei führt Claude (Entwickler-KI) als eigene Projektdokumentation:
Funktionsumfang, Konventionen und ein fortlaufendes Fortschritts-Log. Sie wird
bei jedem größeren Arbeitsschritt aktualisiert und mit gepusht.

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
  frontend/shutter-pilot-panel.js  Das komplette Panel (~2560 Z., ein File)
tests/               pytest-Suite (374 Tests)
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

Wochenendwerte fallen immer auf die Wochentagswerte zurück, wenn sie leer
bleiben. Statt Samstag/Sonntag kann ein **Workday-Sensor** entscheiden
(Feiertage, Schichtdienst). Eine **Präsenzsimulation** streut die Zeiten um bis
zu N Minuten; der Wert ist pro Tag stabil, nicht pro Fahrt.

### Rollläden

Je Rollladen: Positionen für offen, geschlossen und Sonnenschutz, optional eine
**abweichende Schließposition** für laue Abende und eine **Frostposition**,
optional **Lamellenwinkel** (Raffstore). Fenstersensor mit Aussperrschutz, dazu
optional ein zweiter Kontakt, wenn „gekippt" als eigene Entität gemeldet wird,
und eine **Entprellung** (0–30 s), bevor auf „geschlossen" reagiert wird.

### Beschattung

Aktiv, wenn **alle** Bedingungen zugleich gelten:

1. Sonnenhöhe im konfigurierten Bereich (min/max)
2. Sonne steht vor den Fenstern (Azimut, Kompass-Schnellwahl)
3. bis zu **vier Zusatzbedingungen** – Binärsensor, Zahlenwert mit Ein-/
   Ausschaltschwelle oder Textzustand (Wetterlage). Dieselbe Mechanik trägt die
   eigenen Slots `close`, `frost` und `vent_a`/`vent_b` – die sind aber **fail
   closed**, ein toter Sensor löst dort nichts aus.
4. Datum liegt im konfigurierten **Beschattungszeitraum** (Jahreswechsel möglich)

Geometrie und Bedingungen lassen sich **pro Rollladen** überschreiben. Der
Rückfall wirkt je Bedingungs-Slot: gesetzt am Rollladen ersetzt den Slot,
leer erbt den Bereichswert. Die Hysterese liegt deshalb pro Cover, nicht pro
Bereich – sonst hebt eine Wolke vor einem Fenster die Beschattung des anderen
auf. Ein fehlender oder toter Sensor blockiert nie (fail open).

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
| Schalter | `switch.shutter_pilot_system` (Hauptschalter), je Bereich und je Rollladen ein Auto-Schalter |
| Sensor | je Bereich „nächste Fahrt"; Vorhersage Höchst-/Tiefsttemperatur und Wetterlage nur, wenn eine Wetter-Entität hinterlegt ist |
| Binärsensor | je Bereich „Sonnenschutz aktiv" |

Dienste: `open_group`, `close_group`, `sun_protect_group`, `ventilate_group`.
Events: `shutter_pilot_cover_moved`, `shutter_pilot_cover_failed`.

### Panel

Ein einzelnes JS-File, kein Build-Schritt. Tabs: Dashboard · Bereiche ·
Rollläden · Einstellungen. Besonderheiten, die man kennen muss:

- **LitElement kommt aus der Prototypenkette** eines geladenen HA-Elements –
  Home Assistant stellt kein Modul dafür bereit. Der Resolver probiert zehn
  Kandidaten und läuft an Mixins vorbei; findet er nichts, zeigt das Panel eine
  Meldung statt einer weißen Seite. `render()` liegt in einem try/catch.
- **macOS-App (Mac Catalyst)**: native `<input type="time">` und `<select>`
  sind dort kaputt (Absturz bzw. öffnet nicht). `NATIVE_PICKERS_BROKEN`
  erkennt die Plattform, dann werden eigene Bedienelemente gerendert.
- **Rechte**: Ohne Administrator zeigt das Panel nur das Dashboard mit den
  Bedienknöpfen. Das ist Bequemlichkeit – die Grenze liegt auf dem Server.
- **i18n**: 11 Sprachen (de, en, fr, es, it, nl, da, sv, pl, pt, nb) im Objekt
  `I18N`. Jeder neue sichtbare Text braucht einen Schlüssel in **allen** elf;
  `t()` fällt sonst auf Englisch zurück. Seit 2.7.1 sind alle elf **vollständig**
  (je 258 Schlüssel) – das gilt es zu halten.

### WebSocket-API

| Befehl | Rechte |
| --- | --- |
| `shutter_pilot/get_status` | alle (lesend) |
| `save_area`, `delete_area`, `save_shutter`, `delete_shutter` | **Admin** |
| `save_settings`, `set_master_enabled`, `set_auto_mode`, `set_shutter_automation` | **Admin** |

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
.venv/bin/pytest            # 374 Tests, ~6 s
```

`.venv/` ist in `.gitignore`. In `pytest.ini` steht `-q` schon in `addopts` –
ein zusätzliches `-q` ergibt `-qq` und verschluckt die Zusammenfassung, also
ohne Argument aufrufen. Die CI ([tests.yaml](.github/workflows/tests.yaml))
fährt dieselbe Suite bei jedem Push auf `master` mit Python 3.13.

**Panel testen ohne Home Assistant:** Das JS lässt sich in Node mit einem
Stub für `customElements`/LitElement auswerten und rendern – so fallen
Renderfehler und Rechte-Logik auf, ohne HA zu starten. Hat sich bewährt, ist
aber wegwerf-Werkzeug im Scratchpad, nicht im Repo.

## Release

1. `manifest.json` Version hochziehen, `CHANGELOG.md` ergänzen
2. committen, `git push origin master`, CI grün abwarten
3. `git tag -a vX.Y.Z -m "…"` + `git push origin vX.Y.Z`
4. `gh release create vX.Y.Z --title "…" --notes-file …`

**Ohne GitHub-Release zieht HACS die Version nicht.** Die Release-Notes sind
für Endnutzer geschrieben (Emoji-Überschriften, Tabellen, „was ändert sich für
mich"), nicht als Commit-Log.

## Projektstand

Version **2.10.0**, im Forum aktiv genutzt. Einreichung für den
HACS-Default-Store läuft: PR [hacs/default#9592](https://github.com/hacs/default/pull/9592).

## Fortschritts-Log

### 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf

Aus einem Forumsbeitrag von MartyBr (weiße Seite nach dem Update auf 2.4.0):

- Ursache war ein fehlender Browser-Reload, kein Fehler im Code. Trotzdem
  gehärtet: Der Basisklassen-Resolver des Panels prüft jetzt zehn statt zwei
  Elemente, und weder ein fehlendes LitElement noch ein Renderfehler führen
  noch zu einer weißen Seite.
- **Hauptschalter startete nach einer Neuinstallation ausgeschaltet.**
  `RestoreEntity` merkt sich Zustände über die entity_id, nicht über die
  unique_id – eine neu hinzugefügte Integration erbte das „aus" der alten.
  Der Schalter schreibt jetzt seine `config_entry_id` als Attribut mit und
  verwirft fremde Zustände. Ein fehlendes Attribut gilt als eigener Zustand,
  damit Bestandsnutzer beim Update nicht plötzlich wieder „an" stehen.
  Ebenso: `unavailable`/`unknown` galten als „aus", jetzt als „an".
- Menü-Knopf im Panel für schmale Bildschirme (`ha-menu-button`, sonst eigener
  Knopf mit `hass-toggle-menu`) – vorher kam man auf dem Handy aus dem Panel
  nur über den Zurück-Knopf des Browsers heraus.

### 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck)

Review zur Aufnahme in den HACS-Default-Store durch **frenck**: Die
schreibenden WebSocket-Befehle waren authentifiziert, prüften aber keine
Rechte – jeder Nicht-Admin konnte konfigurieren.

- Alle sieben ändernden Befehle mit `@websocket_api.require_admin` versehen.
  `save_settings` stand nicht in frencks Liste, schreibt aber genauso in die
  Options – mit abgesichert.
- **Bewusste Abweichung von frencks Vorschlag:** `require_admin` bleibt am
  Panel `False`. Das Panel ist zugleich Bedienoberfläche (hoch/runter/…, über
  `cover`-Dienste, die HA selbst autorisiert). Es aus der Seitenleiste zu
  nehmen hätte Mitbewohnern die Bedienung genommen – ausdrücklicher Wunsch des
  Entwicklers, dass es sichtbar bleibt. Stattdessen richtet sich das Panel nach
  `hass.user.is_admin`. Am PR ist das offen begründet, mit dem Angebot
  umzustellen, falls frenck darauf besteht.
- PR-Status: hacs-bot stellte den PR nach jedem „ready for review" binnen
  Sekunden auf Draft zurück – Grund war **nicht** das offene Review, sondern ein
  veralteter Branch („Your branch seems out of date"). Der Fork-Branch
  `add-shutter-pilot-v2` muss vor jedem „ready for review" mit `hacs:master`
  aktuell sein. Frenck hat das am 2026-08-02 selbst erledigt (Merge `6380e7f`)
  und den PR wieder freigegeben; seither ist er in der Queue, alle Checks grün.
- **Nicht am PR herumdrehen.** Der Bot bittet Einreicher ausdrücklich, nicht zu
  kommentieren, keinen zweiten PR zu öffnen und den Base-Branch nur auf
  Aufforderung zu mergen. Der Kommentar zur `require_admin`-Abweichung war die
  Ausnahme, weil frenck um Release und Re-Request gebeten hatte.

**Nächste Schritte:** Antwort von frenck abwarten. Falls er auf
`require_admin=True` besteht, umstellen und im Forum ankündigen, dass das Panel
für Nicht-Admins verschwindet.

### 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos)

Ausführliches Feld-Feedback von **Linos** im Forum, zehn Punkte. Alle gegen den
Code geprüft, einer umgesetzt, der Rest bewusst zurückgestellt.

**Umgesetzt:** Dritte Ebene unter Hauptschalter und Bereich. `automation_enabled`
je Rollladen, Schalter `switch.shutter_pilot_auto_<name>`, Prüfung über
`is_shutter_automation_enabled()` an den vier automatisierten Fahrpfaden
(Scheduler, Helligkeit, Beschattung, Fenstertrigger). Anlass: defekter Antrieb,
der nicht fahren darf, ohne seine Konfiguration zu verlieren.

Zwei Dinge, die man dabei wissen muss:

- **Nicht in `set_cover_position()` prüfen.** Dort laufen auch die Dienste und
  die Dashboard-Knöpfe durch. Manuell muss ein abgeschalteter Rollladen fahren –
  sonst kann man ihn nach der Reparatur nicht prüfen.
- **Rangfolge:** Laufzeitwert (`data["shutter_automation"]`) → Schalter-Entität →
  gespeicherter Wert. Der Config-Wert ist nur der Startwert; sobald der Schalter
  existiert, entscheidet er, sonst würde ein Umlegen in HA beim nächsten Reload
  verlorengehen. `_apply_shutter_automation_state()` hält beide beim Speichern
  im Panel gleich. Anders als bei Bereich und Hauptschalter gilt hier
  **fail open**: ein toter Schalter legt keinen Rollladen still.

**Geprüft und zurückgestellt** (Analyse nicht neu erarbeiten):

| Punkt | Ist-Zustand |
| --- | --- |
| Sonnengrenze im Helligkeitsmodus | nur Uhrzeitfenster (`_area_window`); sonnenrelativ gibt es nur im Sonnenmodus (`clamp_to_bounds`) |
| Flattern bei Wolken | Hysterese über Werte und Phasensperren, aber **keine** Zeitbedingung; `_release_sun_protect()` fährt sofort auf |
| Fahrverzögerung global | wirkt nur je Bereich, jeder Bereich ist ein eigener Task → gleichzeitige Bursts. Choke-Point wäre `set_cover_position()` |
| Nachhol-Pending | `drive_after_close_pending` nur im RAM, `position_store.py` wäre der Ablageort |
| Profile/Label | bräuchte dritte Stufe in `resolve_shading_config()` + Migration. Zwischenschritt: Kopierknopf im Formular |
| Lüften mit Bedingungen | rein manuell, kein Automatikpfad; Bedingungs-Slots wären wiederverwendbar |
| Zweiter Azimutbereich | ein Bereich je Rollladen, Wrap-around unterstützt. Nötig nur bei getrennten Richtungen an einem Aktor |

**Nachtrag 2.5.1:** Schalten geht jetzt auch im Panel – Dashboard-Zeile und
Rollläden-Tab – über den neuen Befehl `set_shutter_automation` (Muster von
`set_auto_mode`: Laufzeitwert setzen und die Schalter-Entität nachziehen).
Ausserdem heissen die Rollladen-Schalter **Shutter Pilot Rollladen <Name>**
statt „Auto <Name>": Bereich und Rollladen tragen oft denselben Namen, und
zwei gleich benannte Schalter liefern in HA ein `_2` an einem davon.

**Fallstrick, einmal reingefallen:** In `__init__.py` stehen die
WebSocket-Dekoratoren direkt über der Funktion. Eine neue Hilfsfunktion
dazwischen zu setzen hängt die Dekoratoren an die falsche Funktion – das
Setup bricht dann mit `'function' object has no attribute '_ws_command'` ab.
Die Testsuite fängt das ab, aber nur, weil sie den echten Setup fährt.

### 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas)

Zwei Meldungen aus dem Forum, beide bestätigt und reproduziert.

**Der Bug:** `schedule_times.py` parste die `sun.sun`-Attribute (HA schreibt sie
mit `+00:00`), konvertierte aber nie nach lokal. `clamp_to_bounds()` verglich
danach `moment.time()` – die **UTC**-Wanduhr – gegen die lokal gemeinte Schranke
und schrieb sie per `moment.replace(hour=…)` in der UTC-Zone zurück. Aus
„Runter frühestens 21:00" wurde 21:00 UTC = 23:00 Berlin. Genau die gemeldete
Fahrt. Im Winter 1 h, im Sommer 2 h; nur Bereiche mit Zeitklammer betroffen.

Behoben mit **einer** Stelle: `_local_sun_time()` legt `dt_util.as_local()` um
das Parsen. `clamp_to_bounds`, `infer_today_sun_time` und die beiden
Datumsvergleiche in `scheduler.py` (281, 324) werden dadurch von selbst richtig
– bewusst kein zweites Sicherheitsnetz, der Vertrag steht stattdessen im
Docstring von `get_sun_mode_triggers` („returns local time") und als Kommentar
an scheduler.py:322.

**Warum die 246 Tests grün blieben:** `tests/test_sun_bounds.py` injizierte die
Sonnenzeiten mit `+02:00` statt `+00:00`, und die Assertions lasen `up.hour`
roh – eine UTC-Zeit mit den richtigen Ziffern besteht so einen Test. Dazu ist
die Test-Zeitzone `US/Pacific` (aus pytest-homeassistant-custom-component),
nicht UTC. Jetzt: Autouse-Fixture auf `Europe/Berlin`, `_set_sun` rechnet nach
UTC um wie das echte HA, und `_hm()` vergleicht in Ortszeit. Gegenprobe
gemacht: ohne den Fix fallen 14 der 22 Tests um.

**Anzeigefehler (Bug A), separater Ursprung:** `_renderSunInfo` rendert die rohe
`next_rising` plus Offset. Zeitklammern und Jitter fehlten – und das Panel
*kann* sie nicht rechnen: `get_random_offset` seedet Pythons Mersenne Twister,
in JS nicht nachbaubar, dazu Workday-Sensor und Wochenend-Rückfall. Deshalb
Backend als einzige Wahrheitsquelle: neue `get_sun_mode_trigger_details()`
liefert Zeit **plus Begründung**, `_ws_get_status` schickt sie als
`area_triggers`, das Panel fällt bei fehlendem Wert wörtlich aufs alte
Verhalten zurück (altes Backend, kein `sun.sun`). `clamp_to_bounds` und
`get_sun_mode_triggers` bleiben als unveränderte Hüllen stehen, damit kein
Aufrufer und kein Test bricht.

Zwei Dinge fürs nächste Mal:

- **Kein freezegun in WebSocket-Tests.** `freezer.move_to()` in die
  Vergangenheit lässt das Auth-Token als abgelaufen gelten, der Client bekommt
  `auth_invalid`. In `tests/test_ws_status.py` werden die Sonnenzeiten
  stattdessen relativ zum heutigen Tag gebaut.
- Die neun kleineren Sprachen im Panel haben **52 fehlende i18n-Schlüssel**
  (Rückfall auf Englisch). Bestand, nicht aus dieser Änderung – aber einmal
  aufräumen wäre fällig.

### 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum

Alles in einem Release; ein separates 2.5.2 wurde bewusst nicht getaggt.

**Entprellung des Fensterkontakts (Xerenas).** Beim Drehen des Griffs von
gekippt auf offen läuft der Kontakt kurz durch „geschlossen". Darin steckten
**zwei** Fehler, und nur einer war der gemeldete:

1. Timing – der `closed`-Zweig fuhr sofort zurück. Jetzt Wartezeit je Rollladen
   (0–30 s, Default 5), Muster `cover_verify`: ein Task je Cover, Abbruch beim
   nächsten Fensterereignis. **Bei 0 s bleibt der Pfad synchron** (kein Task,
   kein await) – sonst änderte sich die Reihenfolge für Bestandsnutzer.
2. Der Offen-Zweig prüfte nur „ist der Rollladen zu?" und übersah einen
   laufenden Zyklus. Nach zu → gekippt (50 %) → offen scheiterte die Prüfung,
   der Zweig brach ab und warf die Rückfahrhöhe weg. **Ohne diesen zweiten Fix
   wäre das Symptom auch mit perfekter Entprellung geblieben.**

Beim Abbrechen **nicht** von `cover_verify` abschreiben: dessen `finally` popt
ohne Identitätsprüfung und entfernt den Eintrag eines schon nachgerückten
Tasks. Hier vergleicht das `finally` mit `asyncio.current_task()`.
`cover_verify.py:186-188` hat den Fehler weiterhin – offen.

**Frostschutz (Linos).** Rolle `closed_frost` analog `closed_alt`. Die
Bedingungen kannten nur „über Schwelle"; die neue Invert-Kennung spiegelt
Vergleich *und* Hysterese. Der Frost-Slot steht in `INVERTED_BY_DEFAULT_SLOTS`,
niemand soll ankreuzen müssen, dass Frost mit „kälter" zu tun hat. Die Kennung
liegt in `sun_condition_invert_key()`, **nicht** als fünftes Tupelelement in
`sun_condition_keys()` – das wird an drei Stellen entpackt.

Dabei zwei Altlasten mitgenommen: `resolve_close_role()` wird jetzt von
Scheduler **und** Helligkeit benutzt (die abweichende Schließposition wirkte im
Helligkeitsmodus nie), und die eigenen Bedingungs-Slots sind **fail closed** bei
totem Sensor. Beschattung bleibt fail open – dort ist die sichere Antwort die
umgekehrte.

**Lüften mit Bedingungen (Linos).** Neues `ventilation.py` am gemeinsamen
Minutentakt. Zurück geht es auf die **vorherige** Position (`vent_heights`, wie
`trigger_heights`), nicht auf „offen" – sonst stünde der Rollladen nach einer
Nachtlüftung oben. Rangfolge festgeschrieben: Fensterkontakt > Beschattung >
Lüften.

**Aus dem Plan verworfen:** der Lüften-Knopf im Dashboard sollte auf den Dienst
umgestellt werden. Die Karte listet `area_up_id` **oder** `area_down_id`, der
Dienst filtert nur `area_down_id` – bei getrennten Bereichen hätte der Knopf
danach stillschweigend Rollläden ausgelassen.

**Testfallen, die Zeit gekostet haben:**

- `patch("...modul.asyncio.sleep")` patcht das **globale** Modul. Ein Mock, der
  sofort zurückkehrt (wie in `test_cover_verify`), geht gut; ein *blockierender*
  legt ganz HA lahm. In `test_window_debounce` wird nur die passende Wartezeit
  gegated, der Rest geht an den echten `sleep`.
- `hass.async_block_till_done()` wartet auch auf einen gerade erzeugten,
  gegateten Task – dafür gibt es dort `_window_bounce()` mit `sleep(0)`-Runden.
- Denselben Zustand nochmal setzen feuert **kein** Event.
- Ein reiner `async_mock_service` lässt die Cover-Position stehen; der
  Startup-Restore hält die Fahrt für verschluckt und wiederholt sie viermal.
  Dessen `STARTUP_RESTORE_DELAY_SEC = 5` hat die Suite von 4 auf 25 Sekunden
  gebracht, bis er in `test_ventilation` abgekürzt wurde.
- **Kein freezegun in WebSocket-Tests**: Zeit zurückdrehen macht das Auth-Token
  ungültig, der Client bekommt `auth_invalid`.

**Offen:** die neun kleineren Panel-Sprachen haben 52 fehlende i18n-Schlüssel
(Rückfall auf Englisch). Bestand, einmal aufräumen wäre fällig.

### 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues

**Beschattung pendelte im Minutentakt (#4).** Mit *einem* Bereich war alles
stabil – der Fehler brauchte einen Rollladen, dessen Hoch- und Runter-Bereich
verschieden sind. `elevation.py` setzte die Beschattung im `in_down`-Zweig und
gab sie im `in_up`-Zweig frei, jeweils mit der Konfiguration *dieses* Bereichs.
Widersprachen sich Bedingungen, Saison oder Geometrie, beschattete der eine und
der andere gab sofort frei: 50, 100, 50, 100.

Umbau: `_evaluate()` läuft jetzt über die **Rollläden** statt über die Bereiche,
und der Runter-Bereich entscheidet allein; Fahrten werden danach je Bereich
gebündelt. Dabei mitgenommen: ein Rollladen, dessen Runter-Bereich keine
Beschattung (mehr) hat, bekommt sein Flag gelöscht – sonst blockierte der
Aggregatwert `sun_protect_active` dauerhaft das automatische Hochfahren. Im
Repro stand er auf `True`, während `sun_protect_covers` leer war.

**Namensanzeige (#3):** `friendly_name||s.name` im Dashboard – umgedreht. Der
Rollläden-Tab machte es schon richtig.

**`cover_verify` finally** hat jetzt die Identitätsprüfung, die `window_trigger`
seit 2.6.0 hat. Der Nebenbefund von damals ist damit erledigt.

**Wieder in dieselbe Testfalle getappt:** `patch("...cover_verify.asyncio.sleep")`
patcht das globale Modul – ein *blockierender* Mock legt auch das `sleep(0)` im
Test selbst lahm. Es muss immer nur die eine passende Wartezeit gegated werden.

### 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet

Alles, was aus Forum und GitHub noch offen war, in einem Zug. Ein separates
2.6.1 wurde nicht getaggt – die Fixes stecken in 2.7.0.

**Globaler Mindestabstand (Linos' Schlüsselfunktion).** `drive_delay` staffelt
nur *innerhalb* eines Bereichs, und jeder Bereich ist ein eigener Task. Der
Choke-Point ist `set_cover_position()` – die eine Stelle, durch die jede Fahrt
läuft. Ein `asyncio.Lock` im Runtime-Dict serialisiert gleichzeitige Aufrufer zu
einer Warteschlange; der Lock wird **über den Schlaf gehalten**, sonst wären
alle gleichzeitig durch. Gedeckelt auf 10 s, damit ein Tippfehler die
Integration nicht anhält.

**Beschattung halten.** Nur die *Freigabe* wird verzögert. Das Beschatten sofort
zu lassen ist wichtig (sonst steht man eine Stunde in der Sonne), und das Ende
des Tages – `elev < e_min` – ebenfalls, sonst hängt die Beschattung in den
Abendplan hinein. Während der Haltezeit gilt der Rollladen **weiter als
beschattet**, sonst fährt der Scheduler in die Lücke.

**Sonnengrenzen im Helligkeitsmodus.** `_area_window` prüft zusätzlich eine
Sonnenschranke. Gerechnet wird mit `_local_sun_time`/`infer_today_sun_time` aus
`schedule_times` – genau die Umrechnung, deren Fehlen in 2.6.0 zwei Stunden
Versatz erzeugt hat. Im Panel brauchen die beiden Felder einen eigenen Helfer:
`Number("")` wäre `0`, und `0` ist hier eine gültige Schranke, kein „aus".

**Kopierknopf** statt Profile/Label – der vereinbarte Zwischenschritt, ohne
Eingriff ins Datenmodell. **Ausschlussliste statt Erlaubnisliste**, damit ein
künftiges Feld nicht stillschweigend vom Kopieren ausgenommen bleibt. Listen
werden kopiert, nicht geteilt.

**Blind fahren (Viktor).** Sein Vorschlag war, die Positionsprüfung abzuschalten
– das wäre schlechter: dann fährt die Lüftung auch bei richtig stehendem
Rollladen, und der Fenstertrigger verliert die Rückfahrhöhe. `get_tracked_position()`
fällt stattdessen auf die eigene Buchführung zurück. Die übrige Logik bleibt in
Kraft.

**Nachhol-Fahrt persistent.** Nur Position, Winkel, Grund und Zeitstempel gehen
auf die Platte; das Shutter-Dict wird beim Start frisch aus den Optionen
zugeordnet – eine veraltete Kopie wäre die gefährlichere der beiden. Nach 24 h
verworfen.

**Bugs:** Das Pendeln (#4) brauchte *getrennte* Hoch-/Runter-Bereiche; mit einem
Bereich war nichts nachzustellen. Merke: bei Berichten über Sonnenschutz immer
zuerst fragen, ob die beiden Bereiche verschieden sind.

**Testfalle, zum zweiten Mal:** `patch("...modul.asyncio.sleep")` trifft das
globale Modul. Ein *blockierender* Mock legt auch das `sleep(0)` im Test selbst
lahm. Immer nur die eine passende Wartezeit gaten.

**Offen geblieben, bewusst:** Profile/Label (der Kopierknopf ist der
Zwischenschritt) und ein zweiter Azimutbereich je Rollladen (nur nötig, wenn ein
Aktor zwei Richtungen bedient). Sowie die 52 fehlenden i18n-Schlüssel in den
neun kleineren Panel-Sprachen – Bestand, Rückfall auf Englisch.

### 2026-08-07 – 2.7.1: die drei Restpunkte

**Der Mindestabstand galt nicht für die Dashboard-Knöpfe.** Beim Durchsehen der
offenen Punkte aufgefallen – ein Mangel an einem Feature, das Stunden vorher
rausging. `_coverAction` schickte **einen** Dienstaufruf mit allen entity_ids;
Home Assistant fächert das gleichzeitig auf. Der Knopf, den Linos drückt, war
also genau der Burst, gegen den die Einstellung gebaut ist.

Bewusst **nicht** übers Backend gelöst: Die Knöpfe rufen `cover`-Dienste direkt
auf, und dabei prüft HA die Rechte je Entität. Ein eigener WebSocket-Befehl
hätte diese Prüfung verloren – das Panel ist absichtlich auch für Nicht-Admins
sichtbar. Also wird im Frontend ein zweites Mal gestaffelt. Zwei Stellen für
dieselbe Regel, aber die Alternative wäre ein Loch in der Rechteprüfung.
Gestaffelt wird auch „Stop": ein verschluckter Stopp lässt den Rollladen bis
zum Anschlag laufen, ein um Sekunden späterer nicht.

**52 i18n-Schlüssel × 9 Sprachen.** Alle elf Sprachen stehen jetzt bei 258
Schlüsseln. Ein Prüfskript dafür ist trivial und lohnt sich vor jedem Release:
Schlüsselmengen aller Sprachen gegen `de` vergleichen.

**Sensornamen übersetzbar.** Fallstrick: `Entity._name_internal` nimmt
`_attr_name`, **sobald es gesetzt ist** – der Übersetzungsschlüssel wird dann nie
nachgeschlagen. Es braucht also beides: `_attr_name` weg *und*
`_attr_has_entity_name = True`. Bestehende Entitäts-IDs bleiben, weil die
Registry sie über die `unique_id` hält; ein Test hält das fest, damit ein
künftiges Umbenennen nicht unbemerkt Automationen bricht.

`ShutterPilotNextActionSensor` bleibt absichtlich bei `_attr_name`: Der Name
enthält den vom Nutzer vergebenen Bereichsnamen, den keine Übersetzungsdatei
kennen kann.

### 2026-08-07 – 2.7.2 und der Stand beim HACS-Store

**Textbedingung (#6).** Der Melder hatte selbst geschlossen, die Sackgasse war
aber echt: Ohne bekannte Zustandsliste bot das Formular nur den gerade
gemeldeten Zustand an. Freitextfeld jetzt genau dort – `weather.*` behält seine
15 Standardlagen ohne Zusatzfeld, Zahlensensoren bleiben numerisch. Eingaben
werden getrimmt und kleingeschrieben, passend zu `_condition_slot_met()`.

**HACS-PR [hacs/default#9592]: der Blocker ist formal.** Alle Checks grün,
Branch aktuell, alle acht schreibenden WS-Befehle admin-geschützt, Icons liegen
korrekt in `custom_components/shutter_pilot/brand/` (icon.png 256², icon@2x.png
512²). Blockiert wird allein durch frencks `CHANGES_REQUESTED` vom 2026-08-01.

Der entscheidende Fund: **`reviewRequests` ist leer.** frenck bat um
„re-request review" – das ist eine eigene GitHub-Aktion, kein Kommentar, und sie
wurde nie ausgelöst. Ohne sie liegt der PR in keiner Warteschlange.

**Das geht nicht per API:** `POST /pulls/9592/requested_reviewers` liefert 404,
weil das Push-Rechte am Repo verlangt – als PR-Autor aus einem Fork hat man die
nicht. Nur im Browser über das ↻ neben dem Reviewer. Kein Kommentar, also auch
kein Verstoss gegen die Bot-Regel.

**Brands ist erledigt, nicht offen:** Die beiden PRs (home-assistant/brands
#10878, #10007) wurden automatisch geschlossen, weil HA seit 2026.3.0 keine
Icons für Custom Integrations mehr dort annimmt. Der Ersatzweg – Ordner `brand/`
in der Integration – ist längst gegangen. Nicht erneut einreichen.

### 2026-08-08 – 2.8.0: zwei Forum-Meldungen, die niemand beantworten konnte

MartyBr und heinzie haben je einen Fall gemeldet, beide mit Screenshots. Der
erste Schritt war, MartyBrs Konfiguration exakt gegen die echten Helfer
nachzurechnen (`resolve_shading_config`, `sun_protect_conditions_met`,
`sun_extra_conditions_met`, `season_allows_shading`) mit den Werten aus seinem
zweiten Screenshot: Elevation 25,54° in [2°, 70°] ✓, Richtungsprüfung aus ✓,
Bedingung 1 32.898 ≥ 30.000 ✓, Bedingung 2 96,8 ≥ 40 ✓, ganzjährig ✓.

**Die Konfiguration hätte beschatten müssen.** Der Grund lag also in einer
Einstellung, die auf keinem Bild war. Genau das ist der Anlass für den Export –
und der Anlass, ihn nicht als Datei-Dump zu bauen, sondern mit der
Entscheidung: `export.py` rechnet je Rollladen die reale Beschattungsprüfung
durch und schreibt jede Teilprüfung mit ihrem Ergebnis hin. Eine Zeile
beantwortet damit, was vorher drei Screenshots offen liessen.

**Zwei Eigenheiten, die den Aufbau bestimmt haben:**

1. **Der Export darf nichts anfassen.** `_condition_slot_met()` schreibt beim
   Auswerten die Hysterese mit, und `condition_memory()` legt den Eintrag beim
   ersten Zugriff überhaupt erst an. Ein Bericht, der das täte, würde den
   Zustand verschieben, den er dokumentieren soll – gemessen würde dann etwas,
   das der Messvorgang selbst erzeugt hat. Deshalb `_memory_copy()`: liest ohne
   `setdefault`, gibt eine Kopie zurück. Ein Test hält das fest.
2. **Alle gespeicherten Schlüssel, nicht eine Auswahl.** Der Wert, auf den es
   ankommt, ist immer der, den niemand fotografiert hat. `False` zählt dabei als
   gesetzt – eine ausgeschaltete Option ist eine Entscheidung.

**Die fünf Funde beim Nachprüfen** (alle mit Test, siehe
`tests/test_forum_findings.py`):

1. **Merker vor der Fahrt.** `set_cover_sun_protected(..., True)` lief, während
   die Fahrt erst eingereiht war – und `set_cover_position()` schluckt
   Ausnahmen. Eine gescheiterte Fahrt galt ab der nächsten Minute als erledigt
   und wurde **nie** wiederholt. `set_cover_position()` gibt jetzt zurück, ob es
   geklappt hat; `_drive_sun_protect()` liefert die Cover, die wirklich unter
   Beschattung stehen. Wartende Nachhol-Fahrten zählen ausdrücklich dazu, sonst
   würde die Merkdatei jede Minute neu geschrieben.
2. **`should_skip_full_open_preserving_sun_protect` fragte den Bereich.** Seit
   2.7.0 (GitHub #4) wird die Beschattung je Cover geführt; diese eine Stelle
   nicht. Sie ist zugleich die **einzige** im ganzen Code, deren Verhalten von
   der Position abhängt (`abs(cur - pos_sp) <= 10`) – und damit die einzige
   Erklärung für heinzies vierten Punkt: von Hand verfahren, dann fährt er
   hoch. Der Bereichs-Vorabcheck in `brightness.py` fiel mit weg; er hielt den
   ganzen Raum an, sobald ein Fenster beschattet war.
3. **Haltezeit auch für den Sonnenuntergang.** Die Reihenfolge im Code
   entschied: erst warten, dann den Grund bestimmen. Jetzt umgekehrt – die
   Haltezeit gilt nur noch, wenn eine *Bedingung* weggefallen ist. Sonne über
   den Bereich gestiegen, aus dem Fenster gewandert oder Saisonende sind keine
   Wolke, sie kommen innerhalb der Haltezeit nicht zurück. Zusammen mit Fund 2
   war das ein doppelter Riegel: nicht freigeben *und* das Hochfahren sperren.
4. **`off_below > on_above` wurde geklammert.** MartyBrs 40 / 130 beim Azimut
   ist als Spanne gemeint; das Paar ist aber Einschaltpunkt plus Aufhebepunkt
   darunter. Übrig blieb „Azimut ≥ 40". Warnung jetzt im Formular und einmal je
   Bedingung im Log, mit dem Verweis auf „Nur bei passender Fensterrichtung".
5. **`resolve_sun_geometry` warf die alte Einzelschwelle weg**, sobald der Haken
   „Eigene Ausrichtung" gesetzt war – auch ohne eigene Werte. Aus „ab 25°" wurde
   der eingebaute Vorgabewert, also [1°, 4°]. Verworfen wird sie jetzt nur, wenn
   der Rollladen wirklich eigene Elevationswerte trägt.

Dazu die Anordnung im Formular: die Felder, die der Haken freischaltet, standen
**hinter** dem Bedingungsblock. In MartyBrs Screenshot ist genau das zu sehen –
Haken gesetzt, darunter sofort Bedingungen. Jetzt stehen sie direkt unter dem
Haken.

**Lehre:** Wenn ein Merker sagt „erledigt", muss er von der Handlung gesetzt
werden, nicht von der Absicht. Die Funde 1 und 3 sind beide diese Klasse: ein
Zustand, der vorauseilt (Fund 1) oder nachhängt (Fund 3), und in beiden Fällen
gibt es danach keinen Weg zurück, weil derselbe Zustand die Wiederholung sperrt.

**Verifiziert:** `pytest` 387 Tests grün (13 neue), `node --check` fürs Panel,
i18n 269/269 Schlüssel in allen elf Sprachen. **Nicht** im Browser geprüft: die
Panel-Änderungen (Export-Abschnitt, Warnhinweis, neue Feldreihenfolge) – dafür
bräuchte es eine laufende HA-Instanz mit angelegtem Benutzer.

### 2026-08-08 – 2.8.1: was der Export sofort eingebracht hat

Der Bericht aus 2.8.0 hat gehalten, wofür er gebaut wurde: MartyBrs Export
beantwortet seine Meldung ohne eine einzige Rückfrage.

**MartyBr ist eine Einstellungssache, keine Codefrage.** Acht seiner zehn
Rollläden hängen mit Schwellen von 20.000–50.000 an
`sensor.gw3000a_wifi4133_solarstrahlung`, der 559,7 meldet – Solarstrahlung in
W/m², nicht Lux. Die Bedingung kann dort nie erfüllt werden. Die beiden
Rollläden an `sensor.solarstrahlung_lux` (70.914) rechnen dagegen sauber, und
„Rollo Küche" steht im eigenen Bericht auf „Ergebnis: beschatten". Dazu vier
Azimut-Bedingungen als Spanne gedacht (40/130, 130/220, 205/320, 355/359) –
alle vier werden auf „≥ unterer Wert" geklammert, das ist Fund 4 aus 2.8.0.
Nachgerechnet mit `_condition_slot_met` gegen seine Werte, nicht geschätzt.

**heinzie war zweimal kaputt, jedes Mal ausreichend allein:**

1. **`window_open_state` = `open` an einem `binary_sensor`.** Der bietet nur
   `on` und `off`. `get_window_state` verglich exakt, also galt der Kontakt
   dauerhaft als geschlossen – kein Lüften, keine Rückfahrt, kein
   Aussperrschutz, und **keine einzige Logzeile**. Das Formular bot die vier
   Wörter an, ohne je nachzusehen, was die gewählte Entität überhaupt melden
   kann. Jetzt faltet `_canonical_state()` beide Seiten auf `on`/`off`; exakte
   Treffer bleiben exakt, `tilted`/`2` sind ausdrücklich **keine** Synonyme.
   Im Formular steht `off` mit zur Wahl (Kontakte, die andersherum melden) und
   darunter der gerade gemeldete Zustand.
2. **Der Kontakt erreichte den beschatteten Rollladen nicht.**
   `_is_cover_effectively_closed` liess nur (nahezu) geschlossene durch – die
   Beschattung parkt auf halber Höhe, also fiel er durch. Die in dieser Datei
   festgeschriebene Rangfolge *Fensterkontakt > Beschattung > Lüften* galt
   damit für `ventilation.py`, aber nicht für den Kontakt selbst.

**Der Nebenbefund, ohne den Fix 2 gefährlich wäre:** `_release_sun_protect()`
räumte die Rückfahrhöhe des Fensterkontakts nicht weg. Endet die Beschattung
bei offenem Fenster, fährt der Rollladen sonst beim Schliessen auf die
Beschattungsposition zurück – Stunden später. Scheduler und Helligkeitsmodus
rufen dafür längst `clear_stale_window_cycle_after_automated_up()`; die
Freigabe tat es nicht. Dazu `forget_drive_after_close()`, weil ersteres den
Merker nur aus dem RAM nimmt und die Platte stehen lässt.

**Am Export nachgezogen**, alles drei aus MartyBrs Bericht heraus gelesen: die
**Einheit** neben dem Wert (559,7 W/m² neben Schwelle 30000 erklärt sich von
selbst, 559,7 neben 30000 nicht), ein Hinweis, wenn Haupt-, Bereichs- oder
Rollladenschalter **aus** steht (dort stand „Ergebnis: beschatten", während
nichts fahren konnte), und die Erklärung der beiden stillen Haken – `unknown`
mit ✅ heisst „blockiert nicht", nicht „erfüllt".

**Testfalle, neu:** `tests/test_forum_findings.py` braucht ~14 s Fixture-Setup
je Test (Startup-Restore plus Fahrtkontrolle). Sechs neue Tests dort kosten
anderthalb Minuten Suite-Laufzeit – wer dort etwas ergänzt, sollte prüfen, ob
es nicht in eine Datei mit leichterem Aufbau gehört.

### 2026-08-08 – 2.8.2: heinzies Diagnose-Datei gegengerechnet

Er hat nicht den Einstellungs-Export geschickt, sondern die HA-Diagnose. Reicht
auch: **beide** Rollläden mit Fensterkontakt (`cover.gardrobe`, `cover.buro`)
tragen `window_open_state: "open"` an demselben `binary_sensor`, und beide
stehen in `sun_protect_covers` bei 47 % bzw. 80 %. Damit greifen die zwei Fixes
aus 2.8.1 an genau seinem Fall, jeder für sich schon ausreichend.

Nachgerechnet mit `resolve_shading_config` gegen seine Werte: „Buero" beschattet
korrekt (Elevation 54,1° in [0–90], Azimut 177,3° in [5–335], 620 W/m² ≥ 300).
„Wohnz. 5" hat `elevation_max: -5` und Azimut 135–135, „Wohnz. 6" Schwellen von
20.000 an einem W/m²-Sensor – beide können nie beschatten. Nicht sein
gemeldetes Problem, aber er wird danach fragen.

**Der Fund, den 2.8.1 nicht abdeckt:** Ein Kontakt ohne Kipp-Zustand ist
zweiwertig, `_get_target_position_for_window_state()` fährt dann bewusst die
**Kipp-Position** – auch für „offen". Im Formular standen trotzdem zwei
Schieber, und heinzie hatte 97 % bei „offen" und 98 % bei „gekippt" gesetzt;
gefahren wird 98. Ohne Kipp-Zustand steht jetzt nur noch ein Schieber da, auf
`position_when_window_tilted`. Der alte Hinweis dazu behauptete, die Position
gelte „wenn der Rollladen geschlossen ist" – seit 2.8.1 doppelt falsch.

**Merke:** Die Diagnose-Datei (`diagnostics.py`) trägt `options` und `runtime`
vollständig, inklusive `sun_protect_covers` und `sun_cond_state`. Für die Frage
„warum fährt er nicht" ist sie so gut wie der Export – nur ohne die
Sensorwerte, die man sich dann selbst dazu holen muss.

### 2026-08-08 – 2.9.0: Linos' Durchgang durch die Oberflaeche

Zehn Punkte, davon zwei echte Fehler, zwei Fragen mit einer Luecke dahinter
und der Rest Beschriftung und Aufbau.

**Der Anzeigefehler:** `_renderSunProtectInfo` setzte „Warte auf passende
Sonnenhöhe", sobald `in_range` (= Geometrie erfüllt) galt und der Schutz
trotzdem nicht aktiv war. Der Text erschien also genau dann, wenn die Höhe
**passte**. Linos stellte 0°–90° ein und bekam ihn den ganzen Tag. Das Backend
liefert `elevation_in_range` und `azimuth_in_range` längst mit – jetzt werden
sie auch benutzt, mit einem eigenen Text für „Geometrie passt, Bedingungen
fehlen noch".

**Die Luecke hinter seiner Wetter-Frage:** `weather_data.py` nahm
`forecast[0]["temperature"]` und schrieb ihn alle 30 Minuten neu. Eine
Tagesvorhersage wird aber fortgeschrieben und faellt, sobald die Spitze vorbei
ist. Wer abends „war es ueber 26 °C?" fragt, fragt gegen einen Wert, der
inzwischen 25 sagt. `_peak_today()` haelt daher das Tagesmaximum, an das Datum
gebunden, plus eigener Sensor `forecast_temp_max_peak`.

**Seine zweite Frage war eine Verstaendnisfrage:** nachts teilweise oeffnen zum
Luftwechsel ist *Abweichendes Schliessen* (`position_closed_alt` +
`sun_cond_close_*`), nicht *Automatisches Lueften* – letzteres faehrt
zwischendurch und wieder zurueck, ersteres bestimmt die Schliessposition.

**Bewusst nicht gemacht: Kompass-Mehrfachauswahl.** Sein Vorschlag war, N+NO+O
gleichzeitig anzuklicken. Daraus muss aber wieder **ein** Min/Max-Bereich
werden, und N+O ergaebe stillschweigend 0°–90° samt NO. Das ist genau die
Verwechslung von Spanne und Punktepaar, die MartyBrs Fehler war.

**Nachgereicht in 2.9.1: die aufklappbaren Abschnitte.** Zurueckgestellt war
sie, weil `_section()` nur die Ueberschrift ausgab und die Felder als
Geschwister folgten – 18 Aufrufstellen in drei Formularen. Gegangen ist der
Weg dann doch, weil sich das ganze Panel in Node auswerten laesst und der
Umbau damit pruefbar wird.

Zwei Dinge, die dabei zaehlen:

* **Der Harnisch braucht zwei Ebenen.** Der LitElement-Resolver laeuft die
  Prototypenkette hoch und nimmt die *hoechste* Klasse, die `html` und `css`
  noch kennt. Gibt `customElements.get()` genau eine Stub-Klasse zurueck,
  landet er bei `Function.prototype`. Es braucht `class Host extends Stub`.
  Und `get("shutter-pilot-panel")` muss **leer** bleiben, sonst ueberspringt
  das File sein eigenes `define()` und die Klasse ist nicht einzusammeln.
* **Die Grenze eines Abschnitts ist nicht die naechste Ueberschrift.** Der
  Export sitzt in `${this._isAdmin()?html\`…\`:""}`; ein Rumpf, der bis zur
  naechsten Ueberschrift laeuft, verschluckt den oeffnenden Ausdruck und das
  File laesst sich nicht mehr parsen. Beim automatisierten Umbau gehoeren die
  umschliessenden Ausdruecke in die Abbruchliste.

Geprueft wurde nicht die Optik, sondern der Bestand: beide Fassungen voll
aufgeklappt gerendert und die `<label>`- und `hint`-Texte verglichen – 71
Bedienelemente, keines verloren.

### 2026-08-09 – 2.10.0: der nachgeholte Rollladen und Linos' Bedingungen

**heinzies Ablauf, vier Schritte:** abends alle runter, einer bleibt wegen
offenem Fenster oben (vorgemerkt), Fenster zu → holt nach, naechster Morgen →
alle hoch **ausser ihm**.

Der Nachhol-Zweig in `scheduler.py` und `brightness.py` verliess die Schleife
mit `continue`, **bevor** `covers_driven_down.add()` / `covers_driven_up.
discard()` liefen. Der Rollladen blieb damit als „heute hochgefahren"
vermerkt, und `_run_up_async` filtert genau danach. Dass die Fahrt beim
Fensterschliessen stattfand, sieht der Scheduler nicht – `window_trigger.py`
pflegt diese Merker nicht. **Merke:** ein `continue` in einer Fahrschleife
ueberspringt nicht nur die Fahrt, sondern auch deren Buchfuehrung.

**Der Fund darunter:** `clear_covers_driven_for_direction()` setzte
`data["covers_driven_up"] = set()` – ein **neues** Set. Scheduler und
Helligkeitsmodus binden ihre Referenz aber einmalig beim Setup per
`setdefault`. Ab dem ersten Aufruf schrieben sie also in ein Set, das nicht
mehr in `data` haengt: der Aufruf war wirkungslos, und Diagnose wie Export
zeigten dauerhaft „–", waehrend intern etwas anderes entschied. Genau das
stand in allen bisherigen Exporten, und ich habe es geglaubt.

Repariert wurde nicht die Funktion, sondern ihre Notwendigkeit: die vier
Aufrufe sind weg, die Funktion auch. Die Sets pflegen sich ueber `add`/
`discard` gegenseitig. **Wirksam machen waere die falsche Reparatur gewesen** –
in `brightness.py` lief der Aufruf jede Minute, ein wirksames Leeren haette
jede Minute neu gefahren; im Scheduler stand er direkt vor dem Filter, der
gegen dasselbe Set prueft, und haette ihn ausgehebelt.

**Linos, zwei Punkte:** „Abweichendes Schliessen" hat jetzt zwei Bedingungen
(`CLOSE_CONDITION_SLOTS`, Muster von `VENT_CONDITION_SLOTS`, beide muessen
zutreffen, fail closed wie bisher). Und die Zahlenfelder trugen ueberall die
Beschriftung des Sonnenschutzes – „Beschatten ab" samt Hinweis auf
durchziehende Wolken, auch bei Frost und Lueften. `_condLabels()` entscheidet
das jetzt am Slot; die Schluessel bleiben dieselben.

**Offen:** `drive_after_close` und Aussperrschutz schliessen sich heute aus.
Der Nachhol-Zweig faehrt gar nicht, obwohl der Aussperrschutz sagt, wie weit
gefahren werden duerfte. Wer bei offenem Fenster die Lueftungsposition und
beim Schliessen die volle Fahrt will, kann das nicht einstellen.

**Slots heissen `a`–`d`, nicht `sun_cond_a`.** `sun_condition_keys("a")` baut
`sun_cond_a_entity` daraus. Mit dem vollen Namen aufgerufen entsteht
`sun_cond_sun_cond_a_entity`, der Slot gilt als unkonfiguriert und
`_condition_slot_met` gibt **True** zurück – ein fail-open, das wie ein
bestandener Test aussieht.
