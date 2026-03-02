# Changelog

Alle wichtigen Änderungen an Shutter Pilot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

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
