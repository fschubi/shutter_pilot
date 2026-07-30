# Changelog

Alle wichtigen Änderungen an Shutter Pilot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

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
