# Gesamtplan Raffstores

Stand 2026-10-21. Quelle: Forum simon42 #172 (Claus/Sancezz), #191/#193 (Florian/Fuchse), #196 (Claus).
Nichts davon ist umgesetzt. Erst nach Rückmeldung im Forum bauen.

## Leitplanken (gelten für jede Stufe)

1. **Bestandsschutz vor allem.** Jeder neue Schlüssel hat Vorgabe "wie bisher" und wird mit `shutter.get(KEY, Default)` gelesen. Keine Migration, keine Pflichtfelder.
2. **Raffstore bleibt ein Rollladen** (`device_kind` fehlt). Kein neuer Gerätetyp, kein eigener Tab: ein neuer `device_kind` würde von `only_shutters()` aus Zeitplan, Helligkeit und Fenstertrigger gefiltert (Falle aus `is_shutter()`). Die Raffstore-Einstellungen kommen als Abschnitt in das Rollladen-Formular, sichtbar bei `tilt_enabled`.
3. **`has_guard()` / `GUARDED_KINDS` nicht anfassen** (rund 15 Stellen, u. a. Aussperrschutz-Aufhebung in `window_helper.py:205`, Dienste, Export). Der Raffstore-Wind bekommt ein eigenes Prädikat.
4. **Die 858 vorhandenen Tests laufen unverändert grün.** Wird ein bestehender Test geändert, ist das ein Alarmsignal. Je Stufe neue Tests: ohne Schlüssel = altes Verhalten, mit Schlüssel = neues. Dazu eine Gegenprobe (Fix entschärfen, genau die neuen Tests fallen).
5. Je Feld: Key in `const.py`, Panel, i18n x11, Test, README (beide Sprachen), Export, Changelog. Neue Schlüssel in `AWNING_UNUSED_KEYS` / `WINDOW_UNUSED_KEYS` (const.py **und** Panel-JS) eintragen.
6. Release erst nach Freigabe. Stufen dürfen gebündelt werden.

## Stufe 1 – Tür als reiner Aussperrschutz (Florian)  — umgesetzt in 2.24.0 (lokal, noch nicht released)

| Schlüssel | Vorgabe | Wirkung |
| --- | --- | --- |
| `window_react` | an | Aus: Fenstertrigger fährt bei "offen/gekippt" nicht. Der Zweig "geschlossen" (Nachholfahrt, Wiederherstellen) bleibt. |
| `drive_after_close_up` | aus | Auf-Fahrten (Zeit, Helligkeit) bei offener Tür werden wie das Runterfahren vorgemerkt, samt Lamellenwinkel. |

Stolpersteine:
- **Nicht** unter dem bestehenden `drive_after_close` mitlaufen lassen: Nutzer mit diesem Haken würden morgens plötzlich nicht mehr hochfahren.
- Zurückhalten in `scheduler.py` (Aufruf mit `apply_lock_protection=False`) und `brightness._run_up` **nach** `should_skip_automated_up`, sonst wird ein ohnehin übersprungener Rollladen vorgemerkt.
- `covers_driven_up/down` spiegelbildlich zum Runter-Zweig pflegen (Fehlerklasse aus 2.22.4 und 2.23.0).
- Prüfen: Handfahrt löscht die Vormerkung weiterhin (`cover_tracker`).

## Stufe 2 – Windschutz für Raffstores (Florian, Claus)

| Schlüssel | Vorgabe | Wirkung |
| --- | --- | --- |
| `storm_guard` | aus | Opt-in je Raffstore |
| `storm_position` | 100 | Sturmposition |
| `storm_tilt` | 100 | Lamellen bei Sturm |
| Wind-Schwelle | wie global | je Raffstore überschreibbar (über `resolve_guard_config`), Sperrzeit 20 min |

Entschieden laut Forum: Sturm fährt hoch und **sperrt alle automatischen Fahrten** (Morgen, Abend, Beschattung) solange er anhält. Nachholen danach: keine Präferenz, Vorschlag: Sperre nur aufheben, kein Nachholen.

Stolpersteine:
- Nur der **Wind-Slot** (kein Regen/Frost, die hängen am Haus).
- Eigene zweite Schleife in `async_enforce_guard`, die Markisenschleife bleibt unverändert. Ruheposition = `storm_position`, **nicht** `position_open` (bei Raffstores unten).
- Sperre in Scheduler, Helligkeit und Beschattung abfragen, nur bei gesetztem Haken.
- **KNX-Windalarm am Aktor (Claus):** Ist der Aktor selbst verriegelt, soll Shutter Pilot nicht senden bzw. die Fahrtkontrolle das nicht als Fehler werten, und danach die zuletzt gewollte Stellung nachholen. Offen: wie erkennt man den Alarm (eigener Sensor?). Im Forum nachfragen.

## Stufe 3 – Position und Lamellen getrennt (Claus #172, #196, Kern seines Wunsches)  — umgesetzt in 2.26.0 (lokal)

- Je Rolle (offen, zu, Sonnenschutz): Position **oder** Lamellen auf "unverändert" setzbar. Heute sendet `set_cover_position` immer eine Position, `get_tilt_for_role` kennt nur Zahlen oder `None` (= aus).
- Neue Werte "unverändert" dürfen bestehende Zahlen nicht umdeuten (leer = bisheriges Verhalten).
- Betroffen: `_send_position`, Fenster-/Vormerk-Pfad (Vormerkung muss "unverändert" speichern können), Fahrtkontrolle, "gilt als oben/unten"-Buchführung.
- **Reihenfolge Position -> Lamellen** (viele KNX-Aktoren setzen den Winkel nach einer Höhenfahrt zurück): heute werden beide nacheinander gesendet, ohne auf das Erreichen der Position zu warten. Optional: Winkel erst nach erreichter Position senden (Haken, Vorgabe aus).
- Die Entscheidung "Beschattung ist nicht eine Zahl, sondern drei Quellen" (CLAUDE.md) muss sauber weiterlaufen.

## Stufe 4 – Handbedienung nur an den Lamellen

- Heute vergleichen `cover_tracker` und `cover_verify` nur die Höhe. Eine reine Winkeländerung wird nicht als Handfahrt erkannt und nicht verifiziert.
- Erweiterung: Winkeländerung ohne Höhenänderung gegen das zuletzt befohlene Lamellenziel (mit Toleranz) als Handfahrt buchen, mit eigener Sperrzeit. Bestehende Fremdfahrt-Logik und das 3-%-Fenster (2.23.2) dürfen sich nicht ändern.
- Claus erkennt Tasten heute über `knx_event` und sperrt 1 h: Alternative wäre ein Dienst/Haken "Automatik pausieren für N min".

## Stufe 5 – Mehrstufiger Sonnenschutz (Claus)

- Mehrere Stufen mit Bedingungen, Rangfolge, Hysterese bzw. Haltezeit je Stufe (Wolken bei 2.000 lx), je Stufe Position/Lamellen fest oder "unverändert".
- Größter Brocken. Baut auf Stufe 3 auf. Bestehende Slot-Mechanik (`_condition_slot_met`, Hysterese pro Cover) wiederverwenden, nicht neu erfinden. Zusätzlich zur vorhandenen "zweiten Beschattungsposition" (`sp_alt`), die unverändert bleibt.

## Stufe 6 – Sichtschutz (Bad)

- Eigene Position/Lamellen, ausgelöst durch eine Entität (Badbelegung, Licht), **Vorrang vor Morgenfahrt und Beschattung**.
- Dazu "Hochfahren nur wenn Räume leer": passt auf den vorhandenen Slot `no_up` (nicht neu bauen, prüfen ob er reicht).

## Stufe 7 – Referenzfahrt

- Optional je Raffstore: einmal im Monat ganz hoch, dann runter, damit Position und Winkel stimmen. Eigener Haken, Vorgabe aus, im Minutentakt-Timer (kein eigener Timer).

## Außerhalb der Raffstores (Claus #172)

- **Notfall-Eingang** (Rauchmelder): alle Rollläden und Jalousien hoch, Automatik gesperrt solange aktiv. Eigene Funktion, hängt nicht an Raffstores. Als eigenen Funktionswunsch führen.

## Reihenfolge

1 -> 2 (kleine Pakete, lösen Floriansfall) -> 3 -> 4 (Grundlage für 5) -> 5 -> 6 -> 7. Notfall-Eingang separat einplanen.
Vorher im Forum klären: KNX-Windalarm (Stufe 2), Haltezeit/Stufen-Rangfolge (Stufe 5), Handbedienung (Stufe 4).

## Entwurf Stufe 2 — umgesetzt in 2.25.0 (lokal) (2026-10-24, nach Antworten #200 Florian und #202 Claus)

Entschieden laut Forum: nach dem Sturm wird die Sperre nur aufgehoben, kein Nachholen. Sturmposition 100 %, Lamellen 100 %. Eigene Schwelle für Raffstores, Sperrzeit 20 min. Claus will zusätzlich einen Alarm-Binärsensor als Auslöser und eine allgemeine Sperr-Entität.

### 2a – Raffstore-Sturm

| Schlüssel | Vorgabe | Wirkung |
| --- | --- | --- |
| `storm_guard` | aus | Opt-in je Raffstore |
| `storm_position` | 100 | Sturmposition (nicht `position_open`, das ist bei Raffstores unten) |
| `storm_tilt` | 100 | Lamellen bei Sturm |

**Auslöser: beide Möglichkeiten aus derselben Mechanik.** Der Wind-Slot kennt schon Binärsensor (on = Gefahr), Zahl mit Ein-/Ausschwelle und Textzustand (`guard_slot_danger`). Wind-Geschwindigkeit (Florian) und Alarm-Binärsensor (Claus) brauchen also keinen neuen Auswertungscode, nur einen eigenen Slot.

- Neuer Slot `rwind` (Raffstore-Wind), global unter Einstellungen mit Sperrzeit 20 min, je Raffstore überschreibbar. **Nicht** `AWNING_GUARD_SLOTS` erweitern: die Markisenschleife würde den Slot sonst mitlaufen lassen.
- `evaluate_guard` bekommt einen optionalen Parameter für die Slotliste (Vorgabe = bisherige Liste, Markisen unverändert).
- Schleife in `async_enforce_guard` für die Opt-in-Raffstores; `has_guard()` bleibt unangetastet.
- Wirkung bei Sturm: einmal je Gefahr auf `storm_position`/`storm_tilt` fahren (dringend, ohne Mindestabstand), `set_cover_sun_protected(..., False)`.
- Sperre automatischer Fahrten, solange `barred`: Scheduler (auf/ab), Helligkeit (auf/ab), Beschattung, Nachholfahrt und Lüften über eine gemeinsame Abfrage `storm_barred(data, cover)`; Dienste und Dashboard-Knöpfe bleiben frei (Hand schlägt Automatik).
- Toter Sensor: wie bei Markisen sofort gesperrt, Zwangsfahrt erst nach der Schonfrist.

### 2b – Sperr-Entität (Claus)

- Schlüssel `lock_entity` je Rollladen (`binary_sensor`, `switch`, `input_boolean`). `on` = Shutter Pilot sendet nichts Automatisches. Deckt den KNX-Aktor-Windalarm, Sperrobjekte und "Fensterputzen" ab.
- Neue Funktion `automation_allowed()` = Automatik an **und** nicht gesperrt, in den Fahrt-Auslösern (Scheduler, Helligkeit, Beschattung, Lüften, Fenstertrigger-Reaktion). Nicht in `is_shutter_automation_enabled` selbst einbauen: der Fenstertrigger verwirft dort die Vormerkung (`window_trigger.py:240/275`).
- Nach Aufhebung: nichts nachholen (ausreichend laut Claus), die nächste planmäßige Fahrt gilt.
- Fahrtkontrolle: es wird nichts gesendet, also nichts zu prüfen.

### Offene Entscheidungen

1. Sturm sperrt nur die Automatik, Handfahrten bleiben frei (Empfehlung: ja).
2. Sturm ignoriert Hauptschalter und Automatikschalter wie bei Markisen (Empfehlung: ja, ist Opt-in).
3. Sturm fährt auch bei gesetzter Sperr-Entität hoch, und die Fahrtkontrolle zählt das nicht als Fehler (Empfehlung: ja; Claus' Aktor verriegelt sich selbst).
4. Lamellen-Rückmeldung (2 % statt 0 %, kurz Lamellen 0 nach der Höhenfahrt): gehört zu Stufe 4, nicht hierher.

### Bestandsschutz

Neue Schlüssel mit Vorgabe aus, `AWNING_GUARD_SLOTS` und `has_guard()` unverändert, Markisenschleife unverändert, Tests wie bei Stufe 1 (Kontrollfälle ohne Haken, Gegenproben).

## Entwurf Stufe 4 – Handbedienung nur an den Lamellen (2026-11-01, noch nichts gebaut)

### Befund im Code

* `cover_tracker._on_cover_state_change` liest nur `current_position`. Bei unveränderter Höhe kehrt er früh zurück ("Funkpegel, Batteriewert …") – eine reine Winkeländerung wird weder als Handfahrt gebucht noch schreibt sie `_hand_moved_at`, hebt Vormerkungen oder den Fensterzyklus auf.
* Gemerkt wird nur das letzte **Höhen**ziel (`commanded_positions`); ein gesendeter Winkel wird nirgends festgehalten. Ohne ihn lässt sich eine Handverstellung nicht von der Nachmeldung unserer eigenen Fahrt unterscheiden.
* `cover_verify` prüft nur die Höhe (`_current_position`); `current_tilt_position` wird nur in `diagnostics.py` gelesen. Der Winkel einer automatischen Fahrt ist also unkontrolliert.

### Vorschlag

1. **Winkelziel merken**: `commanded_tilts[cover]` neben `commanded_positions`, geschrieben in `_set_cover_tilt`, verworfen bei Handfahrt wie die Höhe.
2. **Erkennung (Opt-in, `tilt_hand_detect`, Vorgabe aus)**: ändert sich `current_tilt_position` bei unveränderter Höhe, ist es eine Handverstellung, wenn
   * kein Pending/Karenz (`is_recent_automation`) läuft,
   * der neue Winkel mehr als die Toleranz (Vorschlag 8 %) vom gemerkten Ziel abweicht,
   * der Antrieb nicht fährt (`opening`/`closing`) und die Höhe seit N s stillsteht – KNX-Aktoren melden nach einer Höhenfahrt kurz Lamellen 0 oder 2 % statt 0 % (Claus #196); ohne diese Entprellung wäre jede Fahrt eine "Handfahrt".
3. **Folge einer erkannten Handverstellung**: `_hand_moved_at` setzen, `forget_window_cycle`, `forget_drive_after_close`, Quelle im Positionsspeicher `manual` – also dasselbe wie bei einer Höhen-Handfahrt, **ohne** `note_manual_position` (Winkel sagt nichts über "oben/unten").
4. **Sperrzeit**: bewusst nicht neu erfunden. Die vorhandenen drei Übersteuerungsmodi (`never`/`daily`/`next_action`) gelten. Claus' Wunsch "1 h nach Tastendruck" lässt sich heute über die Sperr-Entität (2.25.0) abbilden; ein Dienst "Automatik pausieren für N min" wäre ein eigener, kleiner Wunsch.
5. **Fahrtkontrolle für Lamellen** (später, getrennt): `cover_verify` zusätzlich gegen `current_tilt_position` mit eigener Toleranz.

### Bestandsschutz

Haken fehlt = Tracker wie heute (früher Rücksprung bleibt). Die 3-%-Regel und das 90-s-Fenster (2.23.2) bleiben unberührt, die neue Erkennung läuft nur *nach* ihnen.

### Vorher klären

* Soll eine Hand-Lamellenverstellung die **Beschattung/Abendfahrt blockieren** (wie eine Höhen-Handfahrt) oder nur nicht überschrieben werden, bis die nächste Fahrt kommt? (Vorschlag: gleiche Modi wie Höhe.)
* Meldet Claus' Aktor `current_tilt_position` überhaupt zuverlässig und wie hoch ist das Rauschen nach einer Fahrt? Ein Export mit Zustandsverlauf einer Fahrt entscheidet über Toleranz und Wartezeit.
* Umfang: Erkennung allein (klein, ~1 Tag) oder mit Fahrtkontrolle der Lamellen (größer).
