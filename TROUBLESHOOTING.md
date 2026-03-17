# Fehlerbehebung: 500 Internal Server Error

Falls der Konfigurations-Dialog weiterhin einen 500-Fehler anzeigt:

## 1. Logs prüfen

Die genaue Fehlerursache steht in den Home Assistant Logs:

1. **Einstellungen** → **System** → **Logs**
2. Oder **Entwicklerwerkzeuge** → **Logs**
3. Vor dem Öffnen des Konfigurations-Dialogs auf „Logs leeren“ klicken
4. Dann Konfiguration öffnen (Fehler auslösen)
5. In den Logs nach `Shutter Pilot` oder `Traceback`/`Error` suchen

Die Python-Fehlermeldung zeigt die genaue Ursache.

### Wenn keine Logs erscheinen – Debug-Logging aktivieren

Um sicherzugehen, dass Shutter Pilot-Meldungen sichtbar sind:

**Variante A – Über die Oberfläche:**
1. **Einstellungen** → **System** → **Logging**
2. Unter „Integrierte Logger“: `custom_components.shutter_pilot` hinzufügen
3. Log-Level auf **Debug** stellen
4. Home Assistant neu starten

**Variante B – Über configuration.yaml:**
```yaml
logger:
  default: info
  logs:
    custom_components.shutter_pilot: debug
```
Dann Home Assistant neu starten.

Beim Klick auf „Konfigurieren“ sollten nun Meldungen erscheinen:
- `Shutter Pilot: Options-Flow wird erstellt` → Flow wurde gestartet
- `Shutter Pilot: async_step_init aufgerufen` → Erster Schritt läuft
- Fehlt die zweite Meldung, tritt der Fehler vor dem ersten Schritt auf.

## 2. Integration entfernen und neu hinzufügen

Manchmal hilft ein kompletter Neustart der Konfiguration:

1. **Einstellungen** → **Geräte & Dienste** → **Integrationen**
2. Shutter Pilot suchen → Menü (⋮) → **Integration löschen**
3. **+ Integration hinzufügen** → „Shutter Pilot“ suchen → hinzufügen
4. Anschließend erneut **Konfigurieren** testen

## 3. Home Assistant neu starten

Nach einem Update der Integration sollte Home Assistant neu gestartet werden, damit die Migration alter Konfigurationseinträge durchläuft.

## 4. Logs teilen

Wenn das Problem weiter besteht, bitte den vollständigen Traceback aus den Logs teilen (z.B. per GitHub-Issue).

## Testplan (manuell) – neue Bereichs-UI

- **Bereiche anlegen/bearbeiten**
  - Bereich hinzufügen: Modus `time` → Speichern → Bereich erscheint in Liste.
  - Bereich hinzufügen: Modus `brightness` → Sensor auswählen + Lux-Schwellen + Zeitfenster setzen → Speichern.
  - Bereich hinzufügen: Modus `sun` → Offsets setzen → Speichern.
  - Bereich löschen: Rollläden, die darauf zeigen, fallen auf den ersten Bereich zurück.

- **Rollladen hinzufügen**
  - Cover + Fenster optional + `area_up_id`/`area_down_id` auswählen → Speichern.
  - Fenster öffnen/kippen/schließen → Positionen & Restore funktionieren weiterhin.

- **Modus Zeit**
  - Bereich `time_up`/`time_down` setzen → prüfen, ob Scheduler 1×/Tag up/down auslöst.

- **Modus Sonnenstand**
  - Bereich `sunrise_offset`/`sunset_offset` setzen → prüfen, ob Sunrise/Sunset Trigger greifen.

- **Modus Helligkeit**
  - Lux unter `lux_down` innerhalb `down`-Zeitfenster → fährt runter.
  - Lux über `lux_up` innerhalb `up`-Zeitfenster → fährt hoch.
  - Lux über `lux_up` außerhalb `up`-Zeitfenster → fährt **nicht** hoch.
  - **Pending-Up**: Lux bleibt im Up-Zeitfenster zu niedrig → später (nach Ende Up-Fenster) Lux über Schwelle → 1× hoch.

- **Sonnenschutz pro Bereich**
  - `sun_protect_enabled` aktivieren + Threshold setzen → wenn `sun.sun` Elevation unter Schwelle fällt → fährt auf `position_sun_protect`.

- **Drive-after-close**
  - Bei geplanter Fahrt runter + Fenster offen + `drive_after_close` aktiv → Fahrt wird gemerkt und beim Fensterschließen ausgeführt.

- **Services**
  - `shutter_pilot.open_group`/`close_group`/`sun_protect_group` mit `area_id` ausführen → nur Rollläden dieses Bereichs reagieren.
