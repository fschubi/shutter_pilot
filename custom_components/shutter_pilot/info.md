# Shutter Pilot

Rollladensteuerung für Home Assistant mit Fenster-Trigger, Sunrise/Sunset, Auto-Modi und Drive-After-Close.

## Installation

1. HACS → Integrationen → Repository hinzufügen: `https://github.com/fschubi/shutter_pilot`
2. Integration installieren
3. Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → + Integration hinzufügen → „Shutter Pilot“

## Konfiguration (Rollläden hinzufügen)

**Tab „Integrationen“** (nicht Geräte!) → Shutter Pilot → Menü (⋮) → Konfigurieren

## Features

- Fenster-Trigger (binary_sensor + sensor)
- Zeiten pro Gruppe (Living, Sleep, Children)
- Sunrise/Sunset mit Offset
- Auto-Modus pro Gruppe
- Drive-After-Close
- Helligkeitssensor, Elevation-Sonnenschutz
