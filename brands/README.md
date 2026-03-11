# Shutter Pilot Brand Icon

Home Assistant zeigt Integrations-Icons **nur** von der zentralen Brands-CDNs:  
`https://brands.home-assistant.io/custom_integrations/<domain>/icon.png`  
Solange dort kein Eintrag für **shutter_pilot** existiert, erscheint ein **weißes/graues Platzhalter-Quadrat**.

## So wird das Logo in Home Assistant sichtbar

1. **Fork** des offiziellen Brands-Repos:  
   https://github.com/home-assistant/brands → „Fork“ klicken.

2. **Ordner anlegen** in deinem Fork:  
   `custom_integrations/shutter_pilot/`

3. **Icon einfügen**:  
   Die Datei `icon.png` aus diesem Repo  
   (`brands/custom_integrations/shutter_pilot/icon.png`)  
   in deinen Fork nach  
   `custom_integrations/shutter_pilot/icon.png`  
   kopieren (per Git oder Upload).

4. **Pull Request** erstellen:  
   Im geforkten Repo „Compare & pull request“ zu `home-assistant:master`  
   (Titel z. B. „Add Shutter Pilot icon“).

5. **Nach dem Merge**:  
   Home Assistant lädt das Icon von der CDN; es erscheint bei  
   Einstellungen → Geräte & Dienste → Integrationen.  
   Ggf. **HA-Cache leeren** oder **Seite neu laden** (Strg+F5).

## Wenn weiterhin ein weißes Quadrat erscheint

- **Noch kein PR / PR nicht gemerged?**  
  Dann ist das Icon auf der CDN noch nicht vorhanden → nur PR einreichen und mergen lassen.

- **Icon ist selbst hell/weiß auf transparent?**  
  Dann wirkt es auf hellem Hintergrund wie ein weißes Quadrat.  
  **Tipp:** Zusätzlich `dark_icon.png` (dunkel optimiert) einreichen oder das Icon mit sichtbarem (z. B. farbigem) Hintergrund nutzen.

- **Empfohlene Icon-Daten:**  
  PNG, quadratisch (z. B. 256×256 px). Optional: `icon@2x.png` mit doppelter Auflösung für Retina.
