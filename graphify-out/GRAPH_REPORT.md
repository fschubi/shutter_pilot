# Graph Report - shutter_pilot  (2026-09-06)

## Corpus Check
- 113 files · ~203,773 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2753 nodes · 6349 edges · 128 communities (116 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.85)
- Token cost: 785,806 input · 0 output

## Community Hubs (Navigation)
- Awning Guard: Retract & Status
- Guard Evaluation & Lockout Config
- Condition Slot Core (helpers.py)
- Integration Setup & WebSocket API
- Awning Dusk & Brightness Setup
- Brightness Mode Time/Sun Window
- Switch Entities (Auto/Master)
- Weather Forecast Sensors
- Window State & Position Resolution
- Cover Verify (Fahrtkontrolle)
- Forum: Manual Drive Edge Cases
- Deferred Close & Position Store
- Ventilation Conditions
- Export Report: Dusk & Guard Rows
- Sun Protection State Tracking
- Weather Data Fetching
- Awning Guard Setup & Startup Restore
- Window Contact Debounce (Xerenas)
- Export Row Formatting (Conditions/Guard)
- Panel: Export & Settings Core
- Panel: Build/Resolver Internals
- Awning Dusk Retract Tests
- Time Mode Deadline & Timezone
- Shading Time Window Check
- Sun Mode Trigger Times
- Awning Sun Tracking Position
- Shading Pendulum Fix (GitHub #4)
- Binary Sensor Entities Setup
- Resume Automation Service
- Next Action & Sun Time Calc
- Resting Position During Drive (c.radi)
- Panel: Dashboard Rendering
- Area Triggers WS Payload Tests
- const.py Config Key Constants
- Per-Shutter Shading Config Fallback
- Extra Shading Conditions
- Window Contact State Recognition
- Forum Findings: Export Verification
- Panel: Area & Shutter Forms
- Presence Simulation Jitter
- Condition Slot Key Naming
- Integration Diagnostics & E2E Setup
- Per-Cover Sun Protect Tracking
- Azimuth Geometry Check
- Elevation Geometry Check
- manifest.json Metadata
- Mode 'none' (Shading Only)
- Global Minimum Drive Delay
- Manual Override Expiry
- Position Store Persistence
- Lock Protection Across Drive Paths
- Frost Protection Slot
- Dashboard Area Card UI
- Frost Condition Evaluation
- Config Flow Setup
- Panel i18n Test Harness
- Awning Fallback Drive Commands
- Forecast Sensor Naming (i18n)
- Project Features Overview
- Panel Shutters/Areas Tab Concepts
- Awning Sensor Unit Mismatch Notes
- Export Notes: Window & Azimuth
- Sun Geometry Resolution
- Duplicate Shutter Guard
- Panel Render Test Harness
- Silent/Ineffective Settings Notes
- Shutter Automation Switch Precedence
- Window State Test Suite
- Awning/Roof Window Device Features
- Catch-up Drive Bookkeeping (heinzie)
- Empty Field = 0 Threshold Bug
- Group Services Tests
- Helper Entity Conditions (DocSpider)
- Window State Detection
- Guard Row Inversion Labels
- Forum 2.16.0 Findings
- Window State Single Contact Tests
- Elevation Bounds Override Test
- Tri-State Slot Reading (None)
- Binary Sensor State Synonyms
- Tilt Position Preservation Tests
- Roof Window Guard Tests
- Separate Tilt Entity Tests
- Panel/HACS Feature List
- Feature List: Shading & Verification
- Panel: Condition & Guard Slot UI
- Weekend Schedule Detection
- Sun Tracking Awning Extension
- Manual Close vs Override Detection
- No-Up Condition Block
- Shading Season Check
- Clock Window Clamp Helper
- Manual Override & Resume Service
- Manual Drive Bookkeeping
- Ventilation Position Tests
- Second Close Condition (Linos)
- Awning Drive Command Direction Note
- Second Shading Position Tests
- Export: Quiet Area Notes Tests
- Shade Release Opens (No Schedule)
- Test Suite Fixtures
- Weekend Block Up Test
- Per-Cover Open Blocker Test
- Per-Shutter Time Window Override
- Extra Conditions + Geometry Tests
- Weekend/No-Up Block Feature
- Next-Action Sensor Honesty Test
- Reload Clears Runtime Memory
- Helper Condition Export Row
- Close Condition Tests
- Manual vs Scheduled Drive Paths
- Switch Entity Naming Test
- Group Service Role Positions
- Shading Hysteresis Test
- Group Services Definitions
- WebSocket Toggle Admin Check
- Catch-up Drive & Double Window Contact
- GitHub Issue Templates
- Heinzie Full Cycle Test
- parse_time() Tests
- Shutter Pilot Brand Icon
- Ventilation Active State
- Manual Drive Booking Wiring Test
- Invert Direction Regression Test
- Test Timezone Fixture (Berlin)
- Test Fixture: Cover Calls
- CI Test Workflow & Deps

## God Nodes (most connected - your core abstractions)
1. `ShutterPilotPanel` - 111 edges
2. `async_build_export()` - 101 edges
3. `sun_condition_keys()` - 84 edges
4. `is_cover_sun_protected()` - 51 edges
5. `get_window_state()` - 47 edges
6. `setup_elevation_listener()` - 46 edges
7. `get_position_for_role()` - 46 edges
8. `set_cover_position()` - 46 edges
9. `evaluate_guard()` - 42 edges
10. `sun_extra_conditions_met()` - 42 edges

## Surprising Connections (you probably didn't know these)
- `Panel: Rollläden (Shutters) Tab` --conceptually_related_to--> `Bereich / Area`  [AMBIGUOUS]
  docs/screenshots/shutters.png → CLAUDE.md
- `Getrennter Bereich Hoch/Runter je Rollladen` --conceptually_related_to--> `helpers.py (Beschattungslogik, Positionen, Sperren)`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/helpers.py
- `Getrennter Bereich Hoch/Runter je Rollladen` --conceptually_related_to--> `scheduler.py (Zeit- und Sonnenmodus)`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/scheduler.py
- `Fensterkontakt (binary_sensor) je Rollladen` --implements--> `CONF_WINDOW_CONTACT / Fensterkontakt Config Key`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/const.py
- `Fensterkontakt (binary_sensor) je Rollladen` --conceptually_related_to--> `window_trigger.py (Fenstertrigger-Logik)`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/window_trigger.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Geräteart-Polymorphie: Rollladen / Markise / Dachfenster teilen sich einen Fahrweg** — concept_sun_protection, concept_awning, concept_roof_window, concept_awning_guard [INFERRED 0.85]
- **Drei Antworten eines toten/unlesbaren Sensors je Kontext (fail open / fail closed / fail danger)** — concept_sun_protection, concept_drive_after_close, concept_frost_protection, concept_awning_guard, concept_automatic_ventilation [INFERRED 0.85]
- **HACS-Release- und Zertifizierungs-Pipeline** — release_releaseguide, changelog_changelog, github_workflows_tests_testsworkflow, github_workflows_validate_validateworkflow, concept_hacs_store_pr [INFERRED 0.75]

## Communities (128 total, 11 thin omitted)

### Community 0 - "Awning Guard: Retract & Status"
Cohesion: 0.04
Nodes (80): async_retract_awning(), clamp_to_rest(), describe_reasons(), extends_upward(), _grace_seconds(), guard_status(), is_barred(), Any (+72 more)

### Community 1 - "Guard Evaluation & Lockout Config"
Cohesion: 0.06
Nodes (49): async_enforce_guard(), evaluate_guard(), _lockout_seconds(), Decide whether this awning may be out, and say why not. Writes the lockout…, Evaluate every awning and pull in the ones that must not be out., Merge the global protection settings with this awning's overrides. Most…, resolve_guard_config(), awning_lockout_key() (+41 more)

### Community 2 - "Condition Slot Core (helpers.py)"
Cohesion: 0.04
Nodes (88): Diagnostics support for Shutter Pilot., awning_dusk_condition_met(), close_condition_met(), commanded_position(), condition_memory(), _condition_slot_met(), _cover_is_travelling(), elevation_used() (+80 more)

### Community 3 - "Integration Setup & WebSocket API"
Cohesion: 0.06
Nodes (71): ActiveConnection, async_response, _apply_shutter_automation_state(), _area_registry_uids(), async_migrate_entry(), _async_register_websocket(), async_setup(), async_unload_entry() (+63 more)

### Community 4 - "Awning Dusk & Brightness Setup"
Cohesion: 0.07
Nodes (57): ConfigEntry, HomeAssistant, Dusk retract for awnings: drive in once, never back out on its own. Asked for…, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener. (+49 more)

### Community 5 - "Brightness Mode Time/Sun Window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "Switch Entities (Auto/Master)"
Cohesion: 0.07
Nodes (28): async_setup_entry(), _kind_label(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Auto-Mode and master switches for Shutter Pilot., The German word this switch is named after. (+20 more)

### Community 7 - "Weather Forecast Sensors"
Cohesion: 0.07
Nodes (23): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+15 more)

### Community 8 - "Window State & Position Resolution"
Cohesion: 0.06
Nodes (45): _canonical_state(), _first_entity_id(), get_deferred_close_position(), get_effective_close_position(), get_position_for_window_state(), get_tilt_entity_id(), get_ventilation_position(), has_separate_tilt_entity() (+37 more)

### Community 9 - "Cover Verify (Fahrtkontrolle)"
Cohesion: 0.08
Nodes (34): cancel_all(), cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant (+26 more)

### Community 10 - "Forum: Manual Drive Edge Cases"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "Deferred Close & Position Store"
Cohesion: 0.08
Nodes (29): forget_drive_after_close(), Note a drive that waits for the window, in memory and on disk. The shutter…, Take a pending drive out of memory and off disk., Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), get_position_store(), Return or create the position store for a config entry. (+21 more)

### Community 12 - "Ventilation Conditions"
Cohesion: 0.11
Nodes (27): True when every configured ventilation condition holds. All conditions are…, vent_conditions_met(), _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore() (+19 more)

### Community 13 - "Export Report: Dusk & Guard Rows"
Cohesion: 0.07
Nodes (20): async_build_export(), ConfigEntry, Build the export as markdown plus the raw options behind it., Der Daemmerungs-Verdikt einer Markise - bjoergs Wunsch aus dem Forum (abends…, bjoerg hatte `switch.shutter_pilot_auto_balkon` als Windsensor. Der steht…, TestDuskRow, TestOwnEntityAsGuardSensor, „Warum faehrt er morgens nicht hoch" stand bisher nirgends im Bericht. Jede… (+12 more)

### Community 14 - "Sun Protection State Tracking"
Cohesion: 0.09
Nodes (25): is_cover_sun_protected(), True if shading currently holds this specific cover., cover_calls(), _fast_startup_restore(), fixture, Die Meldungen aus dem Forum vom August, gegen den echten Code gehalten. Vier…, Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, charly166 und Linos: nicht beschatten, was noch gar nicht offen ist. (+17 more)

### Community 15 - "Weather Data Fetching"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "Awning Guard Setup & Startup Restore"
Cohesion: 0.08
Nodes (38): ConfigEntry, HomeAssistant, Watch the guard sensors and hold the minute tick as a safety net., setup_awning_guard(), async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant (+30 more)

### Community 17 - "Window Contact Debounce (Xerenas)"
Cohesion: 0.11
Nodes (28): cover_calls(), _gated_sleep(), _positions(), fixture, parametrize, Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum. Beim…, Fensterzustand melden und alles zu Ende laufen lassen., Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.… (+20 more)

### Community 18 - "Export Row Formatting (Conditions/Guard)"
Cohesion: 0.09
Nodes (37): Return the "compare downwards" option key for a slot., sun_condition_invert_key(), _condition_note(), _condition_rows(), _deferred_close_note(), _dusk_row(), _fmt(), _guard_rows() (+29 more)

### Community 20 - "Panel: Build/Resolver Internals"
Cohesion: 0.06
Nodes (22): p, src, target, win, winSrc, code, DEFAULT_PANEL, flat() (+14 more)

### Community 21 - "Awning Dusk Retract Tests"
Cohesion: 0.10
Nodes (22): _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture, parametrize, Dusk retract für Markisen – Anregung von bjoerg aus dem Forum. Er wollte, dass… (+14 more)

### Community 22 - "Time Mode Deadline & Timezone"
Cohesion: 0.13
Nodes (22): _latest_deadline(), time, The clock time this direction runs at regardless of the lux value. None means…, _area(), _as_local(), _berlin(), _monday(), datetime (+14 more)

### Community 23 - "Shading Time Window Check"
Cohesion: 0.10
Nodes (22): True if the clock allows shading right now. Elevation, azimuth, conditions and…, shading_time_window_ok(), _at(), cover_calls(), _fast_startup_restore(), datetime, fixture, Beschattung nur innerhalb bestimmter Uhrzeiten. Aus GitHub-Diskussion #5… (+14 more)

### Community 24 - "Sun Mode Trigger Times"
Cohesion: 0.13
Nodes (22): get_sun_mode_triggers(), Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), parametrize, Tests for the earliest/latest clock bounds in sun mode. MartyBr's case from the…, Midsummer: the sun is up at 05:10, the shutters wait until 07:30., Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it. (+14 more)

### Community 25 - "Awning Sun Tracking Position"
Cohesion: 0.15
Nodes (21): awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+13 more)

### Community 26 - "Shading Pendulum Fix (GitHub #4)"
Cohesion: 0.14
Nodes (22): _area(), _positions(), Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-…, Fällt die Bedingung des *Runter*-Bereichs weg, wird freigegeben., Der Bereichswert lief aus dem Tritt und blockierte Hochfahrten., Der einfache Fall muss sich unverändert verhalten. (+14 more)

### Community 27 - "Binary Sensor Entities Setup"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "Resume Automation Service"
Cohesion: 0.12
Nodes (21): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+13 more)

### Community 29 - "Next Action & Sun Time Calc"
Cohesion: 0.13
Nodes (27): _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times(), parse_time() (+19 more)

### Community 30 - "Resting Position During Drive (c.radi)"
Cohesion: 0.14
Nodes (23): cover_calls(), _gated_sleep(), _moving(), _positions(), fixture, c.radis Fall: der Rollladen parkt auf 74 %, einer Zahl, die nirgends steht.…, Der Rollladen ist unterwegs – die gemeldete Position ist eine Momentaufnahme., Fenster wird angefasst, waehrend der Abendlauf noch faehrt. (+15 more)

### Community 32 - "Area Triggers WS Payload Tests"
Cohesion: 0.14
Nodes (16): _berlin_offset(), _options(), date, Tests for the area_triggers block in the get_status WebSocket payload. Xerenas…, The reported case: 07:30 must be sent, not the 06:07 sunrise., The panel falls back to its own display – but must get everything else., bjoerg und charly166: die Markisen-Einstellungen standen wieder leer da.…, GitHub #9: Entität im Formular gewählt, Speichern gedrückt, Feld wieder leer.… (+8 more)

### Community 33 - "const.py Config Key Constants"
Cohesion: 0.09
Nodes (23): AWNING_GUARD_SLOTS, AWNING_UNUSED_KEYS, BOOL_COND_DOMAINS, COMPASS_PRESETS, COND_DOMAINS, COND_SLOTS, HINTS, I18N (+15 more)

### Community 34 - "Per-Shutter Shading Config Fallback"
Cohesion: 0.16
Nodes (14): Merge area and shutter shading settings into one config dict. Geometry follows…, resolve_shading_config(), _area(), data(), fixture, Tests for per-shutter conditions falling back to the area. Forum discussion:…, South is in its dead band and holds; west never engaged., The point of the whole design: brightness per window, weather once. (+6 more)

### Community 35 - "Extra Shading Conditions"
Cohesion: 0.16
Nodes (11): True when every configured extra condition for shading is satisfied. Pass the…, sun_extra_conditions_met(), _area(), Nicknol's case: real sunshine AND a warm day., A broken sensor must not disable shading permanently., A sensor alone cannot decide anything without a threshold., Still fails open – but no longer silently., TestBinarySensor (+3 more)

### Community 36 - "Window Contact State Recognition"
Cohesion: 0.12
Nodes (12): bjoerg: „nur die Abfrage des Fenstergriffs scheint zu haengen." Sein Kontakt…, Ohne Kipp-Zustand ist alles in Ordnung – dafuer gibt es 2.8.2., Ein `sensor` darf melden, was er will – kein Hinweis., „auf" faltet auf on – erreichbar, also kein Hinweis., c.radis Fall: „wenn das Fenster auf gekippt steht, wird der Rolladen gar nicht…, Steht das Fenster gerade gekippt, ist das die halbe Antwort., Mit dem Haken faehrt er – dann gibt es nichts zu erklaeren., Ohne Kontakt tritt „Fenster offen" nie ein – der Haken tut nichts. (+4 more)

### Community 37 - "Forum Findings: Export Verification"
Cohesion: 0.11
Nodes (16): drives(), fixture, Die fünf Funde aus der Forum-Runde vom 08.08.2026 – und der Export. Zwei…, Aufgezeichnete Fahrbefehle – ohne echte Cover-Integration., Ein Bereich mit Sonnenschutz, Haltezeit 30 min und einer Lux-Bedingung., Eine Runde der Sonnenschutz-Auswertung., F1: der Merker wurde gesetzt, bevor gefahren wurde., F5: die Haltezeit hielt auch das berechtigte Ende auf. (+8 more)

### Community 39 - "Presence Simulation Jitter"
Cohesion: 0.19
Nodes (10): get_random_offset(), get_time_mode_triggers(), date, Return (up, down) times for a time-mode area, jitter included., Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area(), Tests for the schedule maths: weekday detection, jitter, trigger times., Scheduler and sensor must agree, so repeated calls must match. (+2 more)

### Community 40 - "Condition Slot Key Naming"
Cohesion: 0.11
Nodes (13): Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), entry(), fixture, bjoerg: „Mein Regensensor liefert nur nass und trocken". In…, Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., TestGuardSensorWithoutNumbers, entry() (+5 more)

### Community 41 - "Integration Diagnostics & E2E Setup"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "Per-Cover Sun Protect Tracking"
Cohesion: 0.16
Nodes (13): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist… (+5 more)

### Community 43 - "Azimuth Geometry Check"
Cohesion: 0.18
Nodes (11): azimuth_in_sun_protect_range(), True when the sun stands in front of this area's windows. Ranges may wrap…, True when both elevation and compass direction call for shading., sun_protect_conditions_met(), _area(), parametrize, The bug azimuth support fixes: 0–15° elevation is hit twice a day., Legacy behaviour: without the azimuth check nothing is blocked. (+3 more)

### Community 44 - "Elevation Geometry Check"
Cohesion: 0.16
Nodes (10): elevation_in_sun_protect_range(), True when sun elevation is within the configured protection window. Switched…, Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch. (+2 more)

### Community 45 - "manifest.json Metadata"
Cohesion: 0.10
Nodes (20): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+12 more)

### Community 46 - "Mode 'none' (Shading Only)"
Cohesion: 0.16
Nodes (14): cover_calls(), _fast_startup_restore(), fixture, malleYay: Shutter Pilot nur fuer den Sonnenschutz. „Gibt es eine Moeglichkeit,…, Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein Reload…, Gegenprobe: dieselben Zeiten, nur mit Modus., Der Punkt der ganzen Uebung., Ohne Zeitplan holt niemand den Rollladen von der halben Hoehe. Im Zeitmodus… (+6 more)

### Community 47 - "Global Minimum Drive Delay"
Cohesion: 0.15
Nodes (14): _drive_all(), drive_log(), _entry(), fixture, MockConfigEntry, parametrize, Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos). Bei Funk (433…, Nach einer Pause muss die nächste Fahrt sofort raus. (+6 more)

### Community 48 - "Manual Override Expiry"
Cohesion: 0.20
Nodes (10): manual_override_still_blocks(), True if a manual position should keep blocking automated opening. The behaviour…, _FakeStore, _iso(), Tests for the configurable manual-override expiry., Minimal stand-in exposing only get_record()., Fail safe: without a timestamp we do not silently override the user., TestDaily (+2 more)

### Community 49 - "Position Store Persistence"
Cohesion: 0.13
Nodes (11): Any, callback, Update one cover and persist., Return stored record if loaded., Return stored position without async load (after async_load was called)., Load all cover records from disk., Persist current in-memory covers to disk., Remember a drive that waits for the window to close. Only the plain values are… (+3 more)

### Community 50 - "Lock Protection Across Drive Paths"
Cohesion: 0.19
Nodes (11): _positions(), Gegenprobe: derselbe Aufbau, nur der Haken fehlt., Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand diesen…, Binaer geschaltet heisst sofort, nicht bei der naechsten Freigabe., Der Aussperrschutz galt an jedem Fahrweg – nur hier nicht., Genau c.radis Fall: von Hand hochgezogen, abends faehrt wieder was., _setup_drive(), TestGroupServices (+3 more)

### Community 51 - "Frost Protection Slot"
Cohesion: 0.20
Nodes (10): _frost_area(), Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten., Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet., Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen., Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten., _shutter(), _temp() (+2 more)

### Community 52 - "Dashboard Area Card UI"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "Frost Condition Evaluation"
Cohesion: 0.17
Nodes (11): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), Fail closed: wer nichts einstellt, merkt nichts., Vor der Trennung der drei Polaritaeten (siehe _slot_reading() in helpers.py)…, Ein binary_sensor, dessen 'aus' Frost bedeutet - ohne die Invertierung liest…, Kein Default-Umdrehen fuer Booleans, auch nicht bei Frost: ein gewoehnlicher…, Ohne Invertierung liesse sich "unter X" nicht ausdrücken. (+3 more)

### Community 54 - "Config Flow Setup"
Cohesion: 0.13
Nodes (13): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+5 more)

### Community 55 - "Panel i18n Test Harness"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "Awning Fallback Drive Commands"
Cohesion: 0.12
Nodes (10): calls(), entry(), fixture, Antriebe, die keine Position kennen. Viele Markisenmotoren – und etliche…, Vier Markisen mal zehn Sekunden waeren eine halbe Minute im Sturm., Alle drei Dienste mitschreiben, damit sichtbar wird, welcher lief., Halb ausfahren kann der Antrieb nicht – stehenbleiben ist schlechter., Ohne lesbares Feature-Bit bleibt es beim bisherigen Verhalten. (+2 more)

### Community 57 - "Forecast Sensor Naming (i18n)"
Cohesion: 0.15
Nodes (11): MockConfigEntry, parametrize, Die Vorhersagesensoren heissen jetzt in der Sprache der Oberfläche. Vorher…, Sonst stünden sie dauerhaft auf „unbekannt"., Ein fehlender Schlüssel macht die Entität namenlos – das faellt sonst erst in…, Eine bestehende Installation behält ihre Entitäts-IDs., Kein hart kodierter Name mehr – der Schlüssel entscheidet., _setup() (+3 more)

### Community 58 - "Project Features Overview"
Cohesion: 0.16
Nodes (16): CLAUDE.md Project Doc, Automatisches Lüften, Event shutter_pilot_awning_retracted, Helligkeitsmodus (brightness), Event shutter_pilot_cover_failed, Event shutter_pilot_cover_moved, Dashboard-Block für das ganze Haus, Diagnose-Download (diagnostics.py) (+8 more)

### Community 59 - "Panel Shutters/Areas Tab Concepts"
Cohesion: 0.15
Nodes (15): "Rollladen hinzufügen" Button, Bereich / Area, Getrennter Bereich Hoch/Runter je Rollladen, Cover-Entity Konzept (Rollladen-Antrieb), Panel: Bereiche (Areas) Tab, Panel: Dashboard Tab, Panel: Rollläden (Shutters) Tab, Edit/Delete Row Actions (pencil/trash icons) (+7 more)

### Community 60 - "Awning Sensor Unit Mismatch Notes"
Cohesion: 0.13
Nodes (7): _awning_silent_notes(), Shutter settings left on an awning, where they mean nothing. Same class as…, Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen". Die…, 559,7 neben 30000 erklaert nichts, 559,7 W/m² neben 30000 alles., Faktor 3,6 daneben heisst: die Markise faehrt nie ein., Wie beim Hysterese-Speicher: der Bericht darf nichts verschieben., TestAwningReport

### Community 61 - "Export Notes: Window & Azimuth"
Cohesion: 0.17
Nodes (8): Ein Kipp-Zustand, den der Kontakt gar nicht melden kann. Ein `binary_sensor`…, _window_contact_note(), _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, bjoergs Export: „Fensterrichtung: ❌ (295,4° in [225° – 315°])". Die Zeile las…, malleYays Modus im Bericht. Ein Bereich, der nichts faehrt, sieht Einstellung…, TestAzimuthRowIsItsOwnCheck, TestNoScheduleIsExplained

### Community 62 - "Sun Geometry Resolution"
Cohesion: 0.20
Nodes (8): get_azimuth_bounds(), Return (min, max) azimuth for the windows of this area, in degrees., Merge area and shutter shading geometry into one config dict. A room can have…, resolve_sun_geometry(), Tests for per-shutter shading geometry, season window and partial close. Forum…, The case Linos described: one room, south and west windows., TestResolveSunGeometry, TestWindowsFacingDifferentWays

### Community 63 - "Duplicate Shutter Guard"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "Panel Render Test Harness"
Cohesion: 0.17
Nodes (13): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, bjoerg (Forum): eine leere Stelle statt eines Icons vor „Hochfahren…, bjoerg (Forum): am Lux-Feld war der Schieber winzig, das Zahlenfeld riesig.…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., _run(), test_all_eleven_languages_carry_the_same_keys() (+5 more)

### Community 65 - "Silent/Ineffective Settings Notes"
Cohesion: 0.21
Nodes (6): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos., Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie., TestSilentSettings

### Community 66 - "Shutter Automation Switch Precedence"
Cohesion: 0.18
Nodes (9): Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen…, Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.…, Bestandsanlagen kennen den Schlüssel nicht – die müssen weiterlaufen., Der Schalter ist die lebende Wahrheit, der gespeicherte Wert der Start., Der eigene Schalter des Rollladens hat den Laufzeitwert schon gesetzt., Fail open: Ein toter Schalter darf keinen Rollladen stilllegen., Umgelegter Schalter wirkt sofort, ohne Reload des Config-Entry., _shutter() (+1 more)

### Community 67 - "Window State Test Suite"
Cohesion: 0.21
Nodes (4): _shutter(), TestLockProtection, TestTilt, TestWindowState

### Community 68 - "Awning/Roof Window Device Features"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 70 - "Catch-up Drive Bookkeeping (heinzie)"
Cohesion: 0.23
Nodes (11): cover_calls(), _driven(), entry(), datetime, fixture, heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten. Sein…, Genau heinzies Ablauf, vier Schritte., Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden. (+3 more)

### Community 71 - "Empty Field = 0 Threshold Bug"
Cohesion: 0.19
Nodes (9): _area(), data(), fixture, Forum 2.19.0 – der Aufhebepunkt, der aus einem leeren Feld entstand. bjoerg im…, Ein leeres Feld faellt auf den Einschaltpunkt zurueck., bjoergs Fall: 0 ist eine echte Schranke, kein "leer"., Nach einem Neustart ist der Merker leer – dann gilt on_above., TestEmptyReleasePoint (+1 more)

### Community 72 - "Group Services Tests"
Cohesion: 0.19
Nodes (12): cover_calls(), _positions(), fixture, Tests for the group services. Regression guard: open_group/close_group used to…, Each shutter gets its own shading angle, not the first one's., Ventilation reuses the position configured for a tilted window., Users can hook their own automations onto the movement event., test_close_group_uses_per_shutter_positions() (+4 more)

### Community 73 - "Helper Entity Conditions (DocSpider)"
Cohesion: 0.14
Nodes (7): parametrize, Helpers as a condition (DocSpider). A house mode, a cinema flag or a cleaning-…, No on_above/off_below configured, and none needed., The panel stores the option verbatim, HA reports it verbatim., Nothing to compare against – it must not block, but it warns., Mirrors the order the panel renders – list first, domain second., TestHelperEntities

### Community 74 - "Window State Detection"
Cohesion: 0.28
Nodes (6): get_window_state(), Return: "closed" | "tilted" | "open" Supports both binary_sensor and sensor…, Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact

### Community 75 - "Guard Row Inversion Labels"
Cohesion: 0.24
Nodes (4): `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, TestGuardTableRespectsInversion, TestRainAndIceUnitPlausibility

### Community 76 - "Forum 2.16.0 Findings"
Cohesion: 0.18
Nodes (9): cover_calls(), entry(), _fast_startup_restore(), fixture, Die vier Forumsmeldungen zu 2.16.0, jede mit ihrem eigenen Beweis. Leichter…, Der Vertrag aus 2.8.0, jetzt eine Ebene hoeher. `_memory_copy()` schuetzt die…, Entry mit hingestelltem Laufzeit-Dict, ohne echtes Setup., TestShadingOptOut (+1 more)

### Community 77 - "Window State Single Contact Tests"
Cohesion: 0.19
Nodes (6): parametrize, Tests for window state detection, including a separate tilt contact. Forum…, The existing single-contact behaviour must not shift at all., _shutter(), TestHelpers, TestSingleContactUnchanged

### Community 78 - "Elevation Bounds Override Test"
Cohesion: 0.23
Nodes (6): get_elevation_bounds(), Return (min, max) elevation for sun protection range., Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, Tests for elevation + azimuth based sun protection., TestElevationBounds

### Community 79 - "Tri-State Slot Reading (None)"
Cohesion: 0.24
Nodes (5): _area(), Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False., Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None mehr, das…, TestJudgeableReturnsBool, TestUnjudgeableReturnsNone

### Community 80 - "Binary Sensor State Synonyms"
Cohesion: 0.24
Nodes (6): parametrize, Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist., „tilted" ist kein Synonym von on/off und darf keins werden., heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`., _shutter(), TestBinarySensorOpenSynonyms

### Community 81 - "Tilt Position Preservation Tests"
Cohesion: 0.21
Nodes (7): bjoergs Aufbau: ein Griff mit open / tilted / closed., bjoergs Fall: 30 % muessen 30 % bleiben., Die Gegenrichtung – dafuer ist der Aussperrschutz da., Wer die Kipp-Position hoeher legt, merkt von der Aenderung nichts., TestTiltedWindow, TestWithoutLockProtection, _three_state()

### Community 82 - "Roof Window Guard Tests"
Cohesion: 0.30
Nodes (5): hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es leider…, Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py, nur an der…, Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal zu. Die…, TestGuardBeatsShadingForAWindow, TestOpeningAndClosingByConditions

### Community 83 - "Separate Tilt Entity Tests"
Cohesion: 0.26
Nodes (3): While tilted, many contacts also read 'open' – tilt must win., A configured but absent tilt entity must not break detection., TestSeparateTiltEntity

### Community 84 - "Panel/HACS Feature List"
Cohesion: 0.20
Nodes (11): Admin-Rechteprüfung (require_admin), Entitätsauswahl (Suchfeld statt lange Liste), HACS Default Store PR hacs/default#9592, i18n: 11 Sprachen im Panel, Mac Catalyst native Picker Absturz, Shutter Pilot Sidebar Panel, Shutter Pilot info.md (HACS store text), FUNDING.yml Sponsor Button (+3 more)

### Community 85 - "Feature List: Shading & Verification"
Cohesion: 0.20
Nodes (11): Fahrtkontrolle (cover_verify), Mindestabstand zwischen Fahrbefehlen, An der Beschattung teilnehmen (shading_enabled), Beschattungs-Zeitfenster (shade_from/shade_to), Beschattungszeitraum (Monate), Sonnenschutz / Beschattung, Wetter & Vorhersage (weather_data.py Konzept), FORUM_POST.md Draft Posts (+3 more)

### Community 87 - "Weekend Schedule Detection"
Cohesion: 0.27
Nodes (5): is_weekend_schedule(), True if the weekend schedule applies. When a workday sensor is configured it…, A public holiday on a Monday must use the weekend schedule., Shift work: a Saturday that is a working day uses the weekday plan., TestWeekendDetection

### Community 88 - "Sun Tracking Awning Extension"
Cohesion: 0.20
Nodes (10): ConfigEntry, HomeAssistant, Set up periodic sun evaluation for sun protection., setup_elevation_listener(), awning_track_step(), awning_tracks_sun(), Update runtime sun protection state for dashboard and skip logic., True when this awning extends further as the sun sinks. (+2 more)

### Community 89 - "Manual Close vs Override Detection"
Cohesion: 0.29
Nodes (5): manual_position_is_a_close(), True if a hand-driven position is simply "closed", not an override. The manual…, Wer abends von Hand schliesst, bekam nie wieder ein automatisches Auf. Der…, Bei einer Markise ist „zu" die groessere Zahl., TestManualCloseIsNoOverride

### Community 90 - "No-Up Condition Block"
Cohesion: 0.36
Nodes (5): no_up_condition_blocks(), True while a configured condition forbids the automated opening. "Whatever my…, Linos: eine Bedingung, die das morgendliche Oeffnen blockiert., Die eine Richtung, in der ein Fehler nicht wehtun darf. Andersherum bliebe…, TestNoUpCondition

### Community 91 - "Shading Season Check"
Cohesion: 0.33
Nodes (5): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, October to March must wrap, like the azimuth range does., TestSeason

### Community 92 - "Clock Window Clamp Helper"
Cohesion: 0.42
Nodes (4): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, datetime, TestClampHelper

### Community 93 - "Manual Override & Resume Service"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "Manual Drive Bookkeeping"
Cohesion: 0.31
Nodes (5): note_manual_position(), Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, Eine blockierte Richtung fror bisher die andere ein. `covers_driven_down` haelt…, Neu zuweisen haenge den Scheduler an ein totes Set (2.10.0)., TestManualDriveIsBooked

### Community 95 - "Ventilation Position Tests"
Cohesion: 0.22
Nodes (4): parametrize, Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, 0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert., TestPosition

### Community 96 - "Second Close Condition (Linos)"
Cohesion: 0.22
Nodes (4): Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Bestandsanlagen haben nur die erste – die muss unverändert wirken., Fail closed: ein toter Sensor darf nicht alles halb offen lassen., TestSecondCloseCondition

### Community 97 - "Awning Drive Command Direction Note"
Cohesion: 0.39
Nodes (3): Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote

### Community 98 - "Second Shading Position Tests"
Cohesion: 0.25
Nodes (3): parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition

### Community 100 - "Shade Release Opens (No Schedule)"
Cohesion: 0.38
Nodes (4): True if the end of the shading day should drive the cover open. Without a…, shade_release_opens(), Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest., TestShadeReleaseIsImplied

### Community 101 - "Test Suite Fixtures"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "Weekend Block Up Test"
Cohesion: 0.29
Nodes (3): c.radi, Linos, hollsten: am Wochenende gar nicht hochfahren., hollstens Fall: samstags arbeiten, sonntags ausschlafen. Der Sondertage-Sensor…, TestWeekendBlocksUp

### Community 103 - "Per-Cover Open Blocker Test"
Cohesion: 0.48
Nodes (3): Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 104 - "Per-Shutter Time Window Override"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 105 - "Extra Conditions + Geometry Tests"
Cohesion: 0.29
Nodes (5): data(), fixture, Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, Extra conditions gate shading; they never widen the sun window., TestGeometryStillApplies

### Community 106 - "Weekend/No-Up Block Feature"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 107 - "Next-Action Sensor Honesty Test"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 108 - "Reload Clears Runtime Memory"
Cohesion: 0.33
Nodes (3): Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., TestReloadIsNotAFinding

### Community 109 - "Helper Condition Export Row"
Cohesion: 0.33
Nodes (3): Ein an/aus-Helfer hat keine Schwellen – und das muss dastehen. Sonst zeigt die…, Slots a-d haben keine Vorgabe-Invertierung, sind aber seit 2.21.5 per Checkbox…, TestHelperConditionInTheReport

### Community 111 - "Manual vs Scheduled Drive Paths"
Cohesion: 0.40
Nodes (4): _positions(), Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt., TestDrivePaths

### Community 112 - "Switch Entity Naming Test"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 113 - "Group Service Role Positions"
Cohesion: 0.33
Nodes (3): parametrize, The group services used to hard-code 100/0 and ignore these values., TestRolePositions

### Community 114 - "Shading Hysteresis Test"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

### Community 115 - "Group Services Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "WebSocket Toggle Admin Check"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 117 - "Catch-up Drive & Double Window Contact"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "GitHub Issue Templates"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 121 - "Shutter Pilot Brand Icon"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "Ventilation Active State"
Cohesion: 0.67
Nodes (3): is_cover_ventilating(), Any, True while automatic ventilation holds this cover.

### Community 125 - "Test Timezone Fixture (Berlin)"
Cohesion: 0.67
Nodes (3): _local_timezone(), fixture, Run these tests in Berlin. The default test timezone is US/Pacific, but…

### Community 126 - "Test Fixture: Cover Calls"
Cohesion: 0.67
Nodes (3): cover_calls(), _fast_startup_restore(), fixture

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **94 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 937 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Dashboard Area Card UI` to `const.py Config Key Constants`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `Panel: Export & Settings Core` to `const.py Config Key Constants`, `Panel: Main Render & Lists`, `Panel: Area & Shutter Forms`, `Panel: Condition & Guard Slot UI`, `Panel: Dashboard Rendering`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Dashboard Area Card UI` to `Condition Slot Core (helpers.py)`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Awning Guard: Retract & Status` be split into smaller, more focused modules?**
  _Cohesion score 0.039892183288409704 - nodes in this community are weakly interconnected._
- **Should `Guard Evaluation & Lockout Config` be split into smaller, more focused modules?**
  _Cohesion score 0.057811753463927376 - nodes in this community are weakly interconnected._