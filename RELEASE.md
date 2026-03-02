# Release-Anleitung: Shutter Pilot

Diese Anleitung erklärt, wie du eine neue Version von Shutter Pilot erstellst und auf GitHub veröffentlichst. HACS nutzt **GitHub Releases** für die Versionsanzeige – Tags allein reichen nicht, es muss ein **Release** erstellt werden.

---

## Vor dem Release: Version überall anpassen

1. **manifest.json**  
   `custom_components/shutter_pilot/manifest.json`  
   → `"version": "1.4.04"` (neue Version eintragen)

2. **README.md** (Root und custom_components)  
   → Abschnitt „Version“ auf die neue Versionsnummer setzen

3. **CHANGELOG.md**  
   → Neuen Eintrag für die Version mit Änderungen ergänzen

---

## Schritt 1: Alles committen und pushen

### Mit GitHub Desktop

1. **Repository öffnen**  
   In GitHub Desktop: Repository `shutter_pilot` auswählen

2. **Änderungen prüfen**  
   Links unter „Changes“ alle geänderten Dateien sehen  
   - grün = neu  
   - gelb = geändert  

3. **Commit erstellen**  
   - Unten links: Commit-Nachricht, z.B.:  
     `Release v1.4.04: services.yaml, 500-Fix, Konfigurationsanleitung`
   - Auf **„Commit to master“** klicken

4. **Zu GitHub pushen**  
   Oben: **„Push origin“** klicken

---

## Schritt 2: GitHub Release erstellen

**Wichtig:** HACS erkennt die Version über den **Release-Tag**, nicht nur über Tags.

### Im Browser (GitHub.com)

1. Repo öffnen: `https://github.com/fschubi/shutter_pilot`

2. **Releases** öffnen  
   Rechts: **„Releases“** → **„Draft a new release“** (oder **„Create a new release“**)

3. **Tag erstellen**  
   - **Choose a tag:** `v1.4.04` eingeben  
   - Wenn der Tag noch nicht existiert: **„+ Create new tag: v1.4.04 on publish“** wählen  
   - **Target:** `master` (oder dein Standard-Branch)

4. **Release-Titel**  
   z.B.: `Shutter Pilot v1.4.04`

5. **Beschreibung**  
   Aus `CHANGELOG.md` die Änderungen für diese Version kopieren, z.B.:

   ```markdown
   ## Geändert
   - Latitude/Longitude werden automatisch aus Home Assistant übernommen
   - Bessere Anleitung nach der Einrichtung
   - HACS: README-Anzeige im Repository
   ```

6. **Release veröffentlichen**  
   Auf **„Publish release“** klicken

---

## Schritt 3: Kontrolle

- **HACS:** Nach einigen Minuten erscheint die neue Version bei Nutzern als Update
- **Version:** Die Tag-Bezeichnung (z.B. `v1.4.04`) ist die Versionsnummer in HACS
- **manifest.json:** Die Version dort sollte mit dem Tag übereinstimmen (ohne `v`)

---

## Kurz-Checkliste

- [ ] Version in `manifest.json` angepasst
- [ ] Version in README-Dateien angepasst
- [ ] CHANGELOG.md aktualisiert
- [ ] Alle Änderungen in GitHub Desktop committed
- [ ] Zu GitHub gepusht
- [ ] GitHub Release mit Tag `vX.Y.Z` erstellt
- [ ] Release-Beschreibung aus CHANGELOG übernommen
