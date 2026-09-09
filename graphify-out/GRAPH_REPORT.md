# Graph Report - shutter_pilot  (2026-09-09)

## Corpus Check
- 106 files · ~214,943 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2890 nodes · 6591 edges · 128 communities (120 shown, 7 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `59358568`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- awning_guard.py
- evaluate_guard
- helpers.py
- __init__.py
- const.py
- _area_window
- ShutterPilotShutterAutomationSwitch
- _ForecastSensorBase
- get_tilt_entity_id
- _entry
- test_forum_2_18.py
- get_position_store
- test_ventilation.py
- manual_override_still_blocks
- is_cover_sun_protected
- get_weather_data
- cover_tracker.py
- Window Contact Debounce (Xerenas)
- export.py
- ShutterPilotPanel
- Panel: Build/Resolver Internals
- test_awning_dusk.py
- _latest_deadline
- test_shade_hours.py
- get_sun_mode_triggers
- test_awning_shading.py
- test_sun_protect_areas.py
- ShutterPilotAwningGuardSensor
- test_resume_automation.py
- schedule_times.py
- test_forum_2_21_3.py
- ._dashCard
- _status
- shutter-pilot-panel.js
- resolve_shading_config
- sun_extra_conditions_met
- ._note
- test_forum_findings.py
- .t
- is_weekend_schedule
- TestAwningReport
- test_init.py
- set_cover_sun_protected
- sun_protect_conditions_met
- test_window_trigger_shaded_manual_reopen.py
- manifest.json
- test_area_mode_none.py
- test_min_drive_gap.py
- ShutterPositionStore
- async_enforce_guard
- _ws_delete_shutter
- manual_position_is_a_close
- Bereichs-Karte (Area Card)
- frost_condition_met
- config_flow.py
- i18n_parity.mjs
- set_cover_position
- test_sensor_names.py
- CLAUDE.md Project Doc
- Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)
- test_minute_tick_order_independence.py
- async_build_export
- CLAUDE.md – Fortschritts-Log (Archiv)
- test_duplicate_cover.py
- test_panel.py
- _silent_setting_notes
- test_shutter_automation.py
- _shutter
- README.md
- Catch-up Drive Bookkeeping (heinzie)
- sun_condition_invert_key
- test_services.py
- TestHelperEntities
- only_shutters
- setup_awning_dusk
- _setup_drive
- TestExportReadsTheWayTheReportWasMeant
- elevation_in_sun_protect_range
- _slot_reading
- _shutter
- test_window_trigger_stale_restore.py
- ._setup
- TestSeparateTiltEntity
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- test_frost_protection.py
- ConfigEntry
- test_elevation_log_disabled.py
- test_forum_2_17.py
- _ticks
- test_blind_drive.py
- CHANGELOG.md
- test_manual_move_clears_pending_drive.py
- async_setup_services
- test_geometry_and_season.py
- sun_condition_keys
- resolve_shade_position
- TestTheExportExplainsAQuietWindow
- setup_elevation_listener
- conftest.py
- test_forum_2_15.py
- test_awning_guard.py
- TestPerShutterOverride
- test_sun_conditions.py
- Sondertage-Sensor (Workday-Sensor)
- TestHeinziesSetup
- resolve_guard_config
- .test_neighbour_in_the_same_area_is_not
- position_store.py
- get_window_state
- TestSwitchEntity
- get_position_for_role
- TestHysteresis
- services.yaml Service Definitions
- resolve_sun_geometry
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- get_elevation_bounds
- TestRainProtection
- Shutter Pilot Integration (Brand/Concept)
- TestNextActionWithoutASchedule
- is_cover_ventilating
- season_allows_shading
- TestWebSocketToggle
- Tests GitHub Workflow
- _condition_slot_met

## God Nodes (most connected - your core abstractions)
1. `ShutterPilotPanel` - 111 edges
2. `async_build_export()` - 101 edges
3. `sun_condition_keys()` - 87 edges
4. `is_cover_sun_protected()` - 54 edges
5. `setup_elevation_listener()` - 47 edges
6. `get_window_state()` - 47 edges
7. `get_position_for_role()` - 46 edges
8. `set_cover_position()` - 46 edges
9. `evaluate_guard()` - 45 edges
10. `CLAUDE.md – Fortschritts-Log (Archiv)` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Panel: Rollläden (Shutters) Tab` --conceptually_related_to--> `Bereich / Area`  [AMBIGUOUS]
  docs/screenshots/shutters.png → CLAUDE.md
- `Fensterkontakt (binary_sensor) je Rollladen` --implements--> `CONF_WINDOW_CONTACT / Fensterkontakt Config Key`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/const.py
- `Getrennter Bereich Hoch/Runter je Rollladen` --conceptually_related_to--> `helpers.py (Beschattungslogik, Positionen, Sperren)`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/helpers.py
- `Getrennter Bereich Hoch/Runter je Rollladen` --conceptually_related_to--> `scheduler.py (Zeit- und Sonnenmodus)`  [INFERRED]
  docs/screenshots/shutters.png → custom_components/shutter_pilot/scheduler.py
- `setup_awning_dusk()` --calls--> `_evaluate()`  [INFERRED]
  custom_components/shutter_pilot/awning_dusk.py → tests/test_ventilation.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **HACS-Release- und Zertifizierungs-Pipeline** — release_releaseguide, changelog_changelog, github_workflows_tests_testsworkflow, github_workflows_validate_validateworkflow, concept_hacs_store_pr [INFERRED 0.75]
- **Geräteart-Polymorphie: Rollladen / Markise / Dachfenster teilen sich einen Fahrweg** — concept_sun_protection, concept_awning, concept_roof_window, concept_awning_guard [INFERRED 0.85]
- **Drei Antworten eines toten/unlesbaren Sensors je Kontext (fail open / fail closed / fail danger)** — concept_sun_protection, concept_drive_after_close, concept_frost_protection, concept_awning_guard, concept_automatic_ventilation [INFERRED 0.85]

## Communities (128 total, 7 thin omitted)

### Community 0 - "awning_guard.py"
Cohesion: 0.09
Nodes (26): async_retract_awning(), clamp_to_rest(), extends_upward(), _grace_seconds(), _lockout_seconds(), Any, Wind, rain and ice protection for awnings and roof windows. The one part of…, The safe position for this kind – retracted, or shut. (+18 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.13
Nodes (24): evaluate_guard(), Decide whether this awning may be out, and say why not. Writes the lockout…, _awning(), _data(), make_entry(), fixture, Einfahren ab `on_above`, Freigabe erst unter `off_below`., 22 km/h liegt unter der Einfahr- und ueber der Freigabeschwelle. Ohne Hysterese… (+16 more)

### Community 2 - "helpers.py"
Cohesion: 0.05
Nodes (79): awning_track_step(), commanded_position(), condition_memory(), _cover_is_travelling(), find_shutter_by_cover(), forget_drive_after_close(), get_cover_current_position(), get_sun_angles() (+71 more)

### Community 3 - "__init__.py"
Cohesion: 0.12
Nodes (43): ActiveConnection, async_response, _async_register_panel(), _async_register_websocket(), async_setup(), _find_entry_data(), callback, HomeAssistant (+35 more)

### Community 4 - "const.py"
Cohesion: 0.06
Nodes (59): Dusk retract for awnings: drive in once, never back out on its own. Asked for…, ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener(), Constants for Shutter Pilot integration., Sun protection per area - elevation range plus optional compass direction., ConfigEntry (+51 more)

### Community 5 - "_area_window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "ShutterPilotShutterAutomationSwitch"
Cohesion: 0.07
Nodes (25): async_setup_entry(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Global switch to enable/disable all Shutter Pilot automation., Switch to enable/disable automation for an area., Switch to enable/disable the sun protection of one area. Separate from the… (+17 more)

### Community 7 - "_ForecastSensorBase"
Cohesion: 0.07
Nodes (23): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+15 more)

### Community 8 - "get_tilt_entity_id"
Cohesion: 0.12
Nodes (18): Ein Kipp-Zustand, den der Kontakt gar nicht melden kann. Ein `binary_sensor`…, _window_contact_note(), _canonical_state(), _first_entity_id(), get_tilt_entity_id(), has_separate_tilt_entity(), _normalize_state(), Any (+10 more)

### Community 9 - "_entry"
Cohesion: 0.08
Nodes (34): cancel_all(), cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant (+26 more)

### Community 10 - "test_forum_2_18.py"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "get_position_store"
Cohesion: 0.16
Nodes (16): Note a drive that waits for the window, in memory and on disk. The shutter…, Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), get_position_store(), Return or create the position store for a config entry., parametrize, TestFlagParsing (+8 more)

### Community 12 - "test_ventilation.py"
Cohesion: 0.11
Nodes (27): True when every configured ventilation condition holds. All conditions are…, vent_conditions_met(), _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore() (+19 more)

### Community 13 - "manual_override_still_blocks"
Cohesion: 0.20
Nodes (10): manual_override_still_blocks(), True if a manual position should keep blocking automated opening. The behaviour…, _FakeStore, _iso(), Tests for the configurable manual-override expiry., Minimal stand-in exposing only get_record()., Fail safe: without a timestamp we do not silently override the user., TestDaily (+2 more)

### Community 14 - "is_cover_sun_protected"
Cohesion: 0.13
Nodes (13): is_cover_sun_protected(), True if shading currently holds this specific cover., charly166 und Linos: nicht beschatten, was noch gar nicht offen ist., Das bisherige Verhalten – und genau das, was gemeldet wurde., bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest., Das alte Verhalten: Merker faellt, gefahren wird nicht., MartyBr: die Beschattung je Bereich abschalten, ohne die Automatik., Der Punkt der ganzen Uebung: die Rollladen kommen wieder hoch. Stehenlassen… (+5 more)

### Community 15 - "get_weather_data"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "cover_tracker.py"
Cohesion: 0.17
Nodes (16): async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant, Track cover positions and restore after Home Assistant restart., After HA start, restore persisted positions if cover integration restored wrong…, Listen to cover state changes and persist positions., setup_cover_position_tracker() (+8 more)

### Community 17 - "Window Contact Debounce (Xerenas)"
Cohesion: 0.11
Nodes (28): cover_calls(), _gated_sleep(), _positions(), fixture, parametrize, Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum. Beim…, Fensterzustand melden und alles zu Ende laufen lassen., Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.… (+20 more)

### Community 18 - "export.py"
Cohesion: 0.10
Nodes (41): _condition_rows(), _deferred_close_note(), _drive_command_note(), _drive_verdict(), _dusk_row(), _fmt(), _guard_rows(), _has_window_contact() (+33 more)

### Community 20 - "Panel: Build/Resolver Internals"
Cohesion: 0.06
Nodes (22): p, src, target, win, winSrc, code, DEFAULT_PANEL, flat() (+14 more)

### Community 21 - "test_awning_dusk.py"
Cohesion: 0.08
Nodes (32): awning_dusk_condition_met(), True when this awning's own "get dark, retract" condition holds. Lives on the…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+24 more)

### Community 22 - "_latest_deadline"
Cohesion: 0.13
Nodes (22): _latest_deadline(), time, The clock time this direction runs at regardless of the lux value. None means…, _area(), _as_local(), _berlin(), _monday(), datetime (+14 more)

### Community 23 - "test_shade_hours.py"
Cohesion: 0.10
Nodes (22): True if the clock allows shading right now. Elevation, azimuth, conditions and…, shading_time_window_ok(), _at(), cover_calls(), _fast_startup_restore(), datetime, fixture, Beschattung nur innerhalb bestimmter Uhrzeiten. Aus GitHub-Diskussion #5… (+14 more)

### Community 24 - "get_sun_mode_triggers"
Cohesion: 0.09
Nodes (29): clamp_to_bounds(), get_sun_mode_triggers(), Pull a computed moment into the configured clock window. Lets an area drive by…, Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), _local_timezone(), datetime (+21 more)

### Community 25 - "test_awning_shading.py"
Cohesion: 0.15
Nodes (21): awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+13 more)

### Community 26 - "test_sun_protect_areas.py"
Cohesion: 0.12
Nodes (27): is_sun_protect_active(), Runtime flag: sun protection currently active for an area., _area(), cover_calls(), _fast_startup_restore(), _positions(), fixture, Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als… (+19 more)

### Community 27 - "ShutterPilotAwningGuardSensor"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "test_resume_automation.py"
Cohesion: 0.09
Nodes (26): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+18 more)

### Community 29 - "schedule_times.py"
Cohesion: 0.10
Nodes (30): _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times(), parse_time() (+22 more)

### Community 30 - "test_forum_2_21_3.py"
Cohesion: 0.14
Nodes (23): cover_calls(), _gated_sleep(), _moving(), _positions(), fixture, c.radis Fall: der Rollladen parkt auf 74 %, einer Zahl, die nirgends steht.…, Der Rollladen ist unterwegs – die gemeldete Position ist eine Momentaufnahme., Fenster wird angefasst, waehrend der Abendlauf noch faehrt. (+15 more)

### Community 32 - "_status"
Cohesion: 0.14
Nodes (16): _berlin_offset(), _options(), date, Tests for the area_triggers block in the get_status WebSocket payload. Xerenas…, The reported case: 07:30 must be sent, not the 06:07 sunrise., The panel falls back to its own display – but must get everything else., bjoerg und charly166: die Markisen-Einstellungen standen wieder leer da.…, GitHub #9: Entität im Formular gewählt, Speichern gedrückt, Feld wieder leer.… (+8 more)

### Community 33 - "shutter-pilot-panel.js"
Cohesion: 0.09
Nodes (23): AWNING_GUARD_SLOTS, AWNING_UNUSED_KEYS, BOOL_COND_DOMAINS, COMPASS_PRESETS, COND_DOMAINS, COND_SLOTS, HINTS, I18N (+15 more)

### Community 34 - "resolve_shading_config"
Cohesion: 0.16
Nodes (14): Merge area and shutter shading settings into one config dict. Geometry follows…, resolve_shading_config(), _area(), data(), fixture, Tests for per-shutter conditions falling back to the area. Forum discussion:…, South is in its dead band and holds; west never engaged., The point of the whole design: brightness per window, weather once. (+6 more)

### Community 35 - "sun_extra_conditions_met"
Cohesion: 0.16
Nodes (11): True when every configured extra condition for shading is satisfied. Pass the…, sun_extra_conditions_met(), _area(), Nicknol's case: real sunshine AND a warm day., A broken sensor must not disable shading permanently., A sensor alone cannot decide anything without a threshold., Still fails open – but no longer silently., TestBinarySensor (+3 more)

### Community 36 - "._note"
Cohesion: 0.12
Nodes (12): bjoerg: „nur die Abfrage des Fenstergriffs scheint zu haengen." Sein Kontakt…, Ohne Kipp-Zustand ist alles in Ordnung – dafuer gibt es 2.8.2., Ein `sensor` darf melden, was er will – kein Hinweis., „auf" faltet auf on – erreichbar, also kein Hinweis., c.radis Fall: „wenn das Fenster auf gekippt steht, wird der Rolladen gar nicht…, Steht das Fenster gerade gekippt, ist das die halbe Antwort., Mit dem Haken faehrt er – dann gibt es nichts zu erklaeren., Ohne Kontakt tritt „Fenster offen" nie ein – der Haken tut nichts. (+4 more)

### Community 37 - "test_forum_findings.py"
Cohesion: 0.13
Nodes (14): drives(), fixture, Die fünf Funde aus der Forum-Runde vom 08.08.2026 – und der Export. Zwei…, Aufgezeichnete Fahrbefehle – ohne echte Cover-Integration., Ein Bereich mit Sonnenschutz, Haltezeit 30 min und einer Lux-Bedingung., Eine Runde der Sonnenschutz-Auswertung., F1: der Merker wurde gesetzt, bevor gefahren wurde., F5: die Haltezeit hielt auch das berechtigte Ende auf. (+6 more)

### Community 39 - "is_weekend_schedule"
Cohesion: 0.13
Nodes (15): get_random_offset(), get_time_mode_triggers(), is_weekend_schedule(), date, Return (up, down) times for a time-mode area, jitter included., True if the weekend schedule applies. When a workday sensor is configured it…, Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area() (+7 more)

### Community 40 - "TestAwningReport"
Cohesion: 0.13
Nodes (7): _awning_silent_notes(), Shutter settings left on an awning, where they mean nothing. Same class as…, Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen". Die…, 559,7 neben 30000 erklaert nichts, 559,7 W/m² neben 30000 alles., Faktor 3,6 daneben heisst: die Markise faehrt nie ein., Wie beim Hysterese-Speicher: der Bericht darf nichts verschieben., TestAwningReport

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "set_cover_sun_protected"
Cohesion: 0.16
Nodes (13): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist… (+5 more)

### Community 43 - "sun_protect_conditions_met"
Cohesion: 0.16
Nodes (13): azimuth_in_sun_protect_range(), get_azimuth_bounds(), Return (min, max) azimuth for the windows of this area, in degrees., True when the sun stands in front of this area's windows. Ranges may wrap…, True when both elevation and compass direction call for shading., sun_protect_conditions_met(), _area(), parametrize (+5 more)

### Community 44 - "test_window_trigger_shaded_manual_reopen.py"
Cohesion: 0.23
Nodes (10): cover_calls(), _fast_startup(), _positions(), fixture, Ein Beschattungs-Merker (shaded=True) ueberlebt eine manuelle Fahrt.…, Rollladen ist von Hand voll offen (100%), der Beschattungs-Merker aus der…, Gegenprobe zum Fix: steht der Rollladen tatsaechlich noch an seiner…, _setup() (+2 more)

### Community 45 - "manifest.json"
Cohesion: 0.10
Nodes (20): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+12 more)

### Community 46 - "test_area_mode_none.py"
Cohesion: 0.15
Nodes (15): cover_calls(), _fast_startup_restore(), fixture, malleYay: Shutter Pilot nur fuer den Sonnenschutz. „Gibt es eine Moeglichkeit,…, Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein Reload…, Gegenprobe: dieselben Zeiten, nur mit Modus., Der Punkt der ganzen Uebung., Ohne Zeitplan holt niemand den Rollladen von der halben Hoehe. Im Zeitmodus… (+7 more)

### Community 47 - "test_min_drive_gap.py"
Cohesion: 0.15
Nodes (14): _drive_all(), drive_log(), _entry(), fixture, MockConfigEntry, parametrize, Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos). Bei Funk (433…, Nach einer Pause muss die nächste Fahrt sofort raus. (+6 more)

### Community 48 - "ShutterPositionStore"
Cohesion: 0.15
Nodes (13): Any, callback, Update one cover and persist., Return stored record if loaded., Return stored position without async load (after async_load was called)., JSON store for last known cover positions (per config entry)., Load all cover records from disk., Persist current in-memory covers to disk. (+5 more)

### Community 49 - "async_enforce_guard"
Cohesion: 0.12
Nodes (13): async_enforce_guard(), ConfigEntry, HomeAssistant, Evaluate every awning and pull in the ones that must not be out., Watch the guard sensors and hold the minute tick as a safety net., setup_awning_guard(), Der Merker gehoert an die Fahrt, nicht an die Absicht. Genau diese Verwechslung…, Sonst gilt die Markise weiter als beschattet und faehrt nie wieder. (+5 more)

### Community 50 - "_ws_delete_shutter"
Cohesion: 0.10
Nodes (24): _area_registry_uids(), _drop_registry_entries(), Remove our own entities from the registry after a delete. Home Assistant keeps…, Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns., Delete an area by id., Delete a shutter by index., _shutter_registry_uids() (+16 more)

### Community 51 - "manual_position_is_a_close"
Cohesion: 0.11
Nodes (9): manual_position_is_a_close(), True if a hand-driven position is simply "closed", not an override. The manual…, Wer abends von Hand schliesst, bekam nie wieder ein automatisches Auf. Der…, Bei einer Markise ist „zu" die groessere Zahl., „Warum faehrt er morgens nicht hoch" stand bisher nirgends im Bericht. Jede…, Gespeichert, sichtbar, wirkungslos – die bekannte Klasse., _remember(), TestDriveVerdictInExport (+1 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "frost_condition_met"
Cohesion: 0.14
Nodes (17): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), _frost_area(), Fail closed: wer nichts einstellt, merkt nichts., Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, Vor der Trennung der drei Polaritaeten (siehe _slot_reading() in helpers.py)…, Ein binary_sensor, dessen 'aus' Frost bedeutet - ohne die Invertierung liest… (+9 more)

### Community 54 - "config_flow.py"
Cohesion: 0.13
Nodes (13): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+5 more)

### Community 55 - "i18n_parity.mjs"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "set_cover_position"
Cohesion: 0.15
Nodes (12): Set cover position (and optionally slat angle) and persist the result. Returns…, set_cover_position(), calls(), entry(), fixture, Antriebe, die keine Position kennen. Viele Markisenmotoren – und etliche…, Vier Markisen mal zehn Sekunden waeren eine halbe Minute im Sturm., Alle drei Dienste mitschreiben, damit sichtbar wird, welcher lief. (+4 more)

### Community 57 - "test_sensor_names.py"
Cohesion: 0.15
Nodes (11): MockConfigEntry, parametrize, Die Vorhersagesensoren heissen jetzt in der Sprache der Oberfläche. Vorher…, Sonst stünden sie dauerhaft auf „unbekannt"., Ein fehlender Schlüssel macht die Entität namenlos – das faellt sonst erst in…, Eine bestehende Installation behält ihre Entitäts-IDs., Kein hart kodierter Name mehr – der Schlüssel entscheidet., _setup() (+3 more)

### Community 58 - "CLAUDE.md Project Doc"
Cohesion: 0.16
Nodes (16): CLAUDE.md Project Doc, Automatisches Lüften, Event shutter_pilot_awning_retracted, Helligkeitsmodus (brightness), Event shutter_pilot_cover_failed, Event shutter_pilot_cover_moved, Dashboard-Block für das ganze Haus, Diagnose-Download (diagnostics.py) (+8 more)

### Community 59 - "Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)"
Cohesion: 0.16
Nodes (14): "Rollladen hinzufügen" Button, Bereich / Area, Getrennter Bereich Hoch/Runter je Rollladen, Cover-Entity Konzept (Rollladen-Antrieb), Panel: Bereiche (Areas) Tab, Panel: Dashboard Tab, Panel: Rollläden (Shutters) Tab, Edit/Delete Row Actions (pencil/trash icons) (+6 more)

### Community 60 - "test_minute_tick_order_independence.py"
Cohesion: 0.18
Nodes (14): cover_calls(), _fast_startup(), _positions(), fixture, parametrize, Punkt 5 der Analyse: kein bestaetigter Fehler, aber eine offene Frage.…, Wind-Gefahr + Dunkelheit + erfuellte Beschattungsbedingung, alle drei…, Gegenprobe zur vorigen Klasse: ohne Gefahr und ohne Dunkelheit muss die… (+6 more)

### Community 61 - "async_build_export"
Cohesion: 0.06
Nodes (25): async_build_export(), Build the export as markdown plus the raw options behind it., _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"… (+17 more)

### Community 62 - "CLAUDE.md – Fortschritts-Log (Archiv)"
Cohesion: 0.04
Nodes (44): 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf, 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck), 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos), 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas), 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum, 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues, 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet, 2026-08-07 – 2.7.1: die drei Restpunkte (+36 more)

### Community 63 - "test_duplicate_cover.py"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "test_panel.py"
Cohesion: 0.17
Nodes (13): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, bjoerg (Forum): eine leere Stelle statt eines Icons vor „Hochfahren…, bjoerg (Forum): am Lux-Feld war der Schieber winzig, das Zahlenfeld riesig.…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., _run(), test_all_eleven_languages_carry_the_same_keys() (+5 more)

### Community 65 - "_silent_setting_notes"
Cohesion: 0.21
Nodes (6): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos., Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie., TestSilentSettings

### Community 66 - "test_shutter_automation.py"
Cohesion: 0.11
Nodes (16): cover_calls(), _positions(), fixture, Automatik pro Rollladen – dritte Ebene unter Hauptschalter und Bereich. Der…, Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt., Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen…, Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.… (+8 more)

### Community 67 - "_shutter"
Cohesion: 0.21
Nodes (4): _shutter(), TestLockProtection, TestTilt, TestWindowState

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 70 - "Catch-up Drive Bookkeeping (heinzie)"
Cohesion: 0.23
Nodes (11): cover_calls(), _driven(), entry(), datetime, fixture, heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten. Sein…, Genau heinzies Ablauf, vier Schritte., Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden. (+3 more)

### Community 71 - "sun_condition_invert_key"
Cohesion: 0.12
Nodes (16): Return the "compare downwards" option key for a slot., sun_condition_invert_key(), _condition_note(), Warn about the two ways a condition passes without meaning anything., _area(), data(), fixture, Forum 2.19.0 – der Aufhebepunkt, der aus einem leeren Feld entstand. bjoerg im… (+8 more)

### Community 72 - "test_services.py"
Cohesion: 0.19
Nodes (12): cover_calls(), _positions(), fixture, Tests for the group services. Regression guard: open_group/close_group used to…, Each shutter gets its own shading angle, not the first one's., Ventilation reuses the position configured for a tilted window., Users can hook their own automations onto the movement event., test_close_group_uses_per_shutter_positions() (+4 more)

### Community 73 - "TestHelperEntities"
Cohesion: 0.14
Nodes (7): parametrize, Helpers as a condition (DocSpider). A house mode, a cinema flag or a cleaning-…, No on_above/off_below configured, and none needed., The panel stores the option verbatim, HA reports it verbatim., Nothing to compare against – it must not block, but it warns., Mirrors the order the panel renders – list first, domain second., TestHelperEntities

### Community 74 - "only_shutters"
Cohesion: 0.11
Nodes (15): device_kind(), filter_shutters_by_area(), is_shutter(), only_shutters(), Filter shutters by area_up_id or area_down_id. Every kind is in by default…, The configured kind, with the missing key meaning "shutter"., True only for an actual shutter. Asked positively on purpose. `not is_awning()`…, Keep just the shutters from a list of covers about to be driven. Filtering here… (+7 more)

### Community 75 - "setup_awning_dusk"
Cohesion: 0.12
Nodes (20): ConfigEntry, HomeAssistant, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), forget_shading_for_cover(), Drop every trace of "this cover is currently shaded". The flag is what…, Where this kind of device belongs when nothing is asking for it. A shutter and…, rest_role() (+12 more)

### Community 76 - "_setup_drive"
Cohesion: 0.16
Nodes (13): _positions(), Gegenprobe: derselbe Aufbau, nur der Haken fehlt., Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand diesen…, Binaer geschaltet heisst sofort, nicht bei der naechsten Freigabe., Der Aussperrschutz galt an jedem Fahrweg – nur hier nicht., Die Verdrahtung, nicht nur die Funktion. Der Merker ist nur dann etwas wert,…, Genau c.radis Fall: von Hand hochgezogen, abends faehrt wieder was., _setup_drive() (+5 more)

### Community 77 - "TestExportReadsTheWayTheReportWasMeant"
Cohesion: 0.12
Nodes (9): deepcopy_options(), Eine Frage zu stellen darf die Antwort nicht verändern., Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus., Was MartyBrs Export offenliess, obwohl alles darin stand., Fünfstellige Lux-Schwellen an einem Sensor in W/m². Nebeneinander sehen 559,7…, Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung., „Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen., TestExport (+1 more)

### Community 78 - "elevation_in_sun_protect_range"
Cohesion: 0.18
Nodes (7): elevation_in_sun_protect_range(), True when sun elevation is within the configured protection window. Switched…, Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., TestElevationCanBeSwitchedOff

### Community 79 - "_slot_reading"
Cohesion: 0.24
Nodes (8): Read one condition slot's raw comparison, or None if it cannot be judged. None…, _slot_reading(), _area(), Die drei Polaritäten der Bedingungs-Slots, an einer Stelle geprüft.…, Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False., Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None mehr, das…, TestJudgeableReturnsBool, TestUnjudgeableReturnsNone

### Community 80 - "_shutter"
Cohesion: 0.24
Nodes (6): parametrize, Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist., „tilted" ist kein Synonym von on/off und darf keins werden., heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`., _shutter(), TestBinarySensorOpenSynonyms

### Community 81 - "test_window_trigger_stale_restore.py"
Cohesion: 0.25
Nodes (9): cover_calls(), _fast_startup(), _positions(), fixture, Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine veraltete…, Fahrten mitschreiben und die Position tatsaechlich im State nachziehen., _setup(), _shutter() (+1 more)

### Community 82 - "._setup"
Cohesion: 0.30
Nodes (5): hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es leider…, Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py, nur an der…, Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal zu. Die…, TestGuardBeatsShadingForAWindow, TestOpeningAndClosingByConditions

### Community 83 - "TestSeparateTiltEntity"
Cohesion: 0.26
Nodes (3): While tilted, many contacts also read 'open' – tilt must win., A configured but absent tilt entity must not break detection., TestSeparateTiltEntity

### Community 84 - "Shutter Pilot Sidebar Panel"
Cohesion: 0.20
Nodes (11): Admin-Rechteprüfung (require_admin), Entitätsauswahl (Suchfeld statt lange Liste), HACS Default Store PR hacs/default#9592, i18n: 11 Sprachen im Panel, Mac Catalyst native Picker Absturz, Shutter Pilot Sidebar Panel, Shutter Pilot info.md (HACS store text), FUNDING.yml Sponsor Button (+3 more)

### Community 85 - "Sonnenschutz / Beschattung"
Cohesion: 0.20
Nodes (11): Fahrtkontrolle (cover_verify), Mindestabstand zwischen Fahrbefehlen, An der Beschattung teilnehmen (shading_enabled), Beschattungs-Zeitfenster (shade_from/shade_to), Beschattungszeitraum (Monate), Sonnenschutz / Beschattung, Wetter & Vorhersage (weather_data.py Konzept), FORUM_POST.md Draft Posts (+3 more)

### Community 87 - "test_frost_protection.py"
Cohesion: 0.13
Nodes (14): has_frost_close_position(), True if this shutter defines a frost-protection closing position., Pick how far this shutter closes: fully, partially, or frost-safe. Shared by…, resolve_close_role(), parametrize, Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Die bestehenden Bedingungen dürfen sich nicht verändert haben., Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten. (+6 more)

### Community 88 - "ConfigEntry"
Cohesion: 0.13
Nodes (14): _apply_shutter_automation_state(), async_migrate_entry(), async_unload_entry(), ConfigEntry, Migrate an old config entry. Only version 1 exists so far., Unload a config entry., Keep the per-shutter automation switch in step with the saved value. The…, cancel_all_window_close() (+6 more)

### Community 89 - "test_elevation_log_disabled.py"
Cohesion: 0.31
Nodes (7): cover_calls(), _fast_startup(), fixture, Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich, wenn…, _setup(), TestElevationLogReflectsWhetherItDecided, _tick_elevation()

### Community 90 - "test_forum_2_17.py"
Cohesion: 0.17
Nodes (11): note_manual_position(), Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, cover_calls(), entry(), _fast_startup_restore(), fixture, Die vier Forumsmeldungen zu 2.16.0, jede mit ihrem eigenen Beweis. Leichter…, Eine blockierte Richtung fror bisher die andere ein. `covers_driven_down` haelt… (+3 more)

### Community 91 - "_ticks"
Cohesion: 0.22
Nodes (8): Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, Die Sperre wirkt im Scheduler – und nur nach oben., Sonst stuende das Haus unter der Ferien-Kennung den Abend offen., hollizone: bei offenem Dachfenster soll die Beschattung warten. Kein neuer Code…, _rearm_scheduler(), TestShadingWaitsForTheWindow, TestUpIsBlocked, _ticks()

### Community 92 - "test_blind_drive.py"
Cohesion: 0.15
Nodes (11): _blind(), entry(), _normal(), fixture, Rollläden ohne Positionsrückmeldung (Wunsch von Viktor, ESP Somfy RTS).…, Der Antrieb meldet keine Position – nur `state`, kein current_position., Bisheriges Verhalten für alle anderen Rollläden., Vor der ersten Fahrt weiss auch die Buchführung nichts. (+3 more)

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "test_manual_move_clears_pending_drive.py"
Cohesion: 0.29
Nodes (8): cover_calls(), _fast_startup(), _positions(), fixture, Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine spaetere…, _setup(), _shutter(), TestStalePendingDriveAfterManualMove

### Community 95 - "async_setup_services"
Cohesion: 0.19
Nodes (11): describe_reasons(), One short line for the log and the export., True if this shutter takes part in the shading of its area. A separate answer…, shading_enabled(), async_setup_services(), _drive_group(), ConfigEntry, HomeAssistant (+3 more)

### Community 96 - "test_geometry_and_season.py"
Cohesion: 0.11
Nodes (13): close_condition_met(), has_alt_close_position(), True if this shutter defines a partial closing position., True when the area's conditions for a partial evening close apply. Same…, Tests for per-shutter shading geometry, season window and partial close. Forum…, Unlike shading conditions, an unset close condition means "no"., Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Bestandsanlagen haben nur die erste – die muss unverändert wirken. (+5 more)

### Community 97 - "sun_condition_keys"
Cohesion: 0.11
Nodes (13): Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), entry(), fixture, bjoerg: „Mein Regensensor liefert nur nass und trocken". In…, Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., TestGuardSensorWithoutNumbers, Der Vertrag aus 2.8.0, jetzt eine Ebene hoeher. `_memory_copy()` schuetzt die… (+5 more)

### Community 98 - "resolve_shade_position"
Cohesion: 0.29
Nodes (5): The shading position for this shutter right now, plus how it was picked. Three…, resolve_shade_position(), parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition

### Community 100 - "setup_elevation_listener"
Cohesion: 0.12
Nodes (15): is_dusk_retracted(), Any, True while dusk retract alone is holding this awning in. Read by elevation.py…, ConfigEntry, HomeAssistant, Set up periodic sun evaluation for sun protection., setup_elevation_listener(), awning_tracks_sun() (+7 more)

### Community 101 - "conftest.py"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "test_forum_2_15.py"
Cohesion: 0.12
Nodes (17): automated_up_blocked(), no_up_condition_blocks(), datetime, True while a configured condition forbids the automated opening. "Whatever my…, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, weekend_blocks_up(), cover_calls() (+9 more)

### Community 103 - "test_awning_guard.py"
Cohesion: 0.24
Nodes (9): guard_status(), is_barred(), Read the last decision without touching it. Deliberately does not evaluate:…, True while this awning must not extend., Wind-, Regen- und Frostschutz der Markise. Die Schutzebene ist der Teil der…, Der Sensor lebt und meldet etwas – nur laesst sich daraus keine Antwort…, Wie `_memory_copy()` im Export: der Bericht darf nichts verschieben., TestReadOnlyStatus (+1 more)

### Community 104 - "TestPerShutterOverride"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 105 - "test_sun_conditions.py"
Cohesion: 0.29
Nodes (5): data(), fixture, Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, Extra conditions gate shading; they never widen the sun window., TestGeometryStillApplies

### Community 106 - "Sondertage-Sensor (Workday-Sensor)"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 108 - "resolve_guard_config"
Cohesion: 0.31
Nodes (5): Merge the global protection settings with this awning's overrides. Most…, resolve_guard_config(), Ein Balkon hinterm Haus sieht anderen Wind als die Terrasse., Ein kleiner Gelenkarm muss frueher rein als eine Kassette daneben., TestConfigResolution

### Community 109 - ".test_neighbour_in_the_same_area_is_not"
Cohesion: 0.48
Nodes (3): Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 110 - "position_store.py"
Cohesion: 0.29
Nodes (4): Diagnostics support for Shutter Pilot., HomeAssistant, Persistent cover position storage across Home Assistant restarts., _storage_key()

### Community 111 - "get_window_state"
Cohesion: 0.16
Nodes (10): get_window_state(), Return: "closed" | "tilted" | "open" Supports both binary_sensor and sensor…, Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact, Tests for window state detection, including a separate tilt contact. Forum…, The existing single-contact behaviour must not shift at all. (+2 more)

### Community 112 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 113 - "get_position_for_role"
Cohesion: 0.07
Nodes (29): get_position_for_role(), is_awning(), only_awnings(), Return the configured cover position for open/closed/sun_protect., True if this entry is an awning rather than a shutter. Both live in the same…, Return just the awnings, in configuration order., _awning(), cover_calls() (+21 more)

### Community 114 - "TestHysteresis"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "resolve_sun_geometry"
Cohesion: 0.24
Nodes (6): Merge area and shutter shading geometry into one config dict. A room can have…, resolve_sun_geometry(), Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch., TestElevationSwitchPerShutter, TestResolveSunGeometry

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "get_elevation_bounds"
Cohesion: 0.23
Nodes (6): get_elevation_bounds(), Return (min, max) elevation for sun protection range., Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, Tests for elevation + azimuth based sun protection., TestElevationBounds

### Community 120 - "TestRainProtection"
Cohesion: 0.33
Nodes (3): Kein Wert = Gefahr. Am Fenster ist das die richtige Richtung., Ecowitt liefert mm/h – Zahl mit Hysterese statt an/aus., TestRainProtection

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 123 - "is_cover_ventilating"
Cohesion: 0.67
Nodes (3): is_cover_ventilating(), Any, True while automatic ventilation holds this cover.

### Community 124 - "season_allows_shading"
Cohesion: 0.33
Nodes (5): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, October to March must wrap, like the azimuth range does., TestSeason

### Community 126 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 128 - "_condition_slot_met"
Cohesion: 0.40
Nodes (4): _condition_slot_met(), Evaluate one extra shading condition. Unreadable never blocks shading., MartyBr trug beim Azimut 40 / 130 ein und meinte den Bereich 40°–130°., TestHysteresisTheWrongWayRound

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **136 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+131 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1005 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `ShutterPilotPanel` to `shutter-pilot-panel.js`, `Panel: Main Render & Lists`, `.t`, `._renderCondDetail`, `._dashCard`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _136 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `awning_guard.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09206349206349207 - nodes in this community are weakly interconnected._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.1323671497584541 - nodes in this community are weakly interconnected._