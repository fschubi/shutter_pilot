# Shutter Pilot

Rollladensteuerung für Home Assistant – inspiriert vom ioBroker Shuttercontrol-Adapter.

[![GitHub](https://img.shields.io/badge/GitHub-fschubi%2Fshutter__pilot-blue?logo=github)](https://github.com/fschubi/shutter_pilot)

---

## Funktionen

| Funktion | Beschreibung |
|----------|--------------|
| **Fenster-Trigger** | Rollladen fährt hoch wenn Fenster geöffnet, wiederherstellen wenn geschlossen |
| **Fenster-Sensoren** | `binary_sensor` und `sensor` (Zustände: open/tilted/closed) |
| **Kippfunktion** | Bei gekipptem Fenster eigene Position (z.B. 50%) |
| **Aussperrschutz** | Bei offener Tür wird Rollladen nicht komplett geschlossen |
| **Drive-After-Close** | Bei Schließzeit noch offenes Fenster → Fahrt beim Schließen |
| **Zeiten pro Gruppe** | Living, Sleep, Children jeweils eigene Zeiten |
| **Sunrise/Sunset** | Fix, Sonnenaufgang oder Sonnenuntergang – mit Offset (Minuten) |
| **Auto-Modus** | Pro Gruppe optional `input_boolean`/`switch` |
| **Helligkeitssensor** | Lux-basierte Steuerung |
| **Sonnenschutz** | Elevation-basiert (einmal pro Tag) |
| **Gruppensteuerung** | Dienste: open_group, close_group, sun_protect_group |

---

## Installation

### Über HACS (empfohlen)

1. HACS → Integrationen → „+ Repository hinzufügen“
2. URL: `https://github.com/fschubi/shutter_pilot`
3. Kategorie: Integration
4. Installation bestätigen
5. Home Assistant neu starten

### Manuell

1. [Release](https://github.com/fschubi/shutter_pilot/releases) herunterladen
2. Ordner `shutter_pilot` nach `config/custom_components/` entpacken
3. Home Assistant neu starten
4. **Einstellungen** → **Geräte & Dienste** → **+ Integration hinzufügen** → „Shutter Pilot“

---

## Konfiguration

### Einrichtung

1. Integration hinzufügen
2. **Shutter Pilot** anklicken → **Konfigurieren**
3. **Einstellungen** → Untermenü wählen:
   - **Allgemeine Einstellungen**: Helligkeitssensor, Lux-Schwellwerte, Verzögerung, Auto-Modi, Sonnenschutz
   - **Zeitplan Wohnbereich / Schlafbereich / Kinderbereich**: jeweils Fix- oder Sonnenzeiten, Offset
4. **Rollladen hinzufügen**: Cover, Fenster-Sensor, Aussperrschutz, Drive-After-Close, Gruppe

### Sunrise/Sunset Offset

- **Offset in Minuten**: negativ = vor dem Ereignis, positiv = danach
- Beispiel: `-30` bei Sonnenaufgang → 30 Minuten vor Sonnenaufgang
- Beispiel: `15` bei Sonnenuntergang → 15 Minuten nach Sonnenuntergang

### Shutter Pilot Control Card (Dashboard)

Zum **Bedienen** der Rollläden steht eine fertige Lovelace-Karte bereit:

1. **Dashboard** öffnen → **Bearbeiten** (oben rechts) → **Karte hinzufügen**
2. **Manuelle Konfiguration** wählen
3. Inhalt aus `lovelace_card_only.yaml` einfügen
4. Unter „Einzelne Rollläden“ die Entity-IDs durch deine Cover-Entities ersetzen (z.B. `cover.wohnzimmer`)

Die Karte enthält:
- **Gruppen**: Wohnbereich, Schlaf, Kinder, Alle – jeweils Hoch / Runter / Sonnenschutz
- **Einzelne Rollläden**: Direktsteuerung mit Positionsanzeige

Alternativ: Vollständige Ansicht aus `lovelace_shutter_pilot_control.yaml` als neue Dashboard-View einfügen.

### Dienste

```yaml
service: shutter_pilot.open_group
data:
  group: living   # living | sleep | children | all

service: shutter_pilot.close_group
data:
  group: all

service: shutter_pilot.sun_protect_group
data:
  group: living
```

---

## GitHub / Upload

Repository: **https://github.com/fschubi/shutter_pilot**

```bash
# Bestehendes Projekt hochladen
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/fschubi/shutter_pilot.git
git push -u origin main
```

---

## Version

1.3.0

## Kompatibilität

Home Assistant 2024.x und neuer.

## Lizenz

MIT
