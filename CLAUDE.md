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
tests/               pytest-Suite (232 Tests)
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
**abweichende Schließposition** für laue Abende, optional **Lamellenwinkel**
(Raffstore). Fenstersensor mit Aussperrschutz, dazu optional ein zweiter
Kontakt, wenn „gekippt" als eigene Entität gemeldet wird.

### Beschattung

Aktiv, wenn **alle** Bedingungen zugleich gelten:

1. Sonnenhöhe im konfigurierten Bereich (min/max)
2. Sonne steht vor den Fenstern (Azimut, Kompass-Schnellwahl)
3. bis zu **vier Zusatzbedingungen** – Binärsensor, Zahlenwert mit Ein-/
   Ausschaltschwelle oder Textzustand (Wetterlage)
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
  als zwei Sensoren (Höchsttemperatur, Wetterlage) – direkt als Bedingung nutzbar.
- **Licht-Folgeaktion** je Bereich beim Runterfahren.
- **Minutentakt**: ein einziger `async_track_time_change` versorgt Scheduler,
  Wetter und Beschattung – nicht pro Modul einen eigenen Timer anlegen.

### Entitäten, Dienste, Events

| Art | Entität |
| --- | --- |
| Schalter | `switch.shutter_pilot_system` (Hauptschalter), je Bereich ein Auto-Schalter |
| Sensor | je Bereich „nächste Fahrt"; Vorhersage-Temperatur und -Wetterlage nur, wenn eine Wetter-Entität hinterlegt ist |
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
  `t()` fällt sonst auf Englisch zurück.

### WebSocket-API

| Befehl | Rechte |
| --- | --- |
| `shutter_pilot/get_status` | alle (lesend) |
| `save_area`, `delete_area`, `save_shutter`, `delete_shutter` | **Admin** |
| `save_settings`, `set_master_enabled`, `set_auto_mode` | **Admin** |

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
.venv/bin/pytest            # 232 Tests, ~2 s
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

Version **2.4.2**, im Forum aktiv genutzt. Einreichung für den
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
- PR-Status: hacs-bot stellt den PR nach jedem „ready for review" innerhalb von
  Sekunden auf Draft zurück, solange frencks „Changes requested" offen steht.
  Das kann nur er auflösen. **Nicht weiter am Draft-Status drehen** – der Bot
  bittet Einreicher ohnehin, nicht auf dem PR zu kommentieren.

**Nächste Schritte:** Antwort von frenck abwarten. Falls er auf
`require_admin=True` besteht, umstellen und im Forum ankündigen, dass das Panel
für Nicht-Admins verschwindet.
