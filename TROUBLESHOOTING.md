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
