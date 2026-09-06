# Graph Report - shutter_pilot  (2026-09-06)

## Corpus Check
- 103 files · ~208,773 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2815 nodes · 6298 edges · 125 communities (112 shown, 12 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9288c9f8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- export.py
- evaluate_guard
- helpers.py
- HomeAssistant
- brightness.py
- Brightness Mode Time/Sun Window
- switch.py
- _ForecastSensorBase
- window_helper.py
- _entry
- test_forum_2_18.py
- get_position_store
- test_ventilation.py
- TestExportReadsTheWayTheReportWasMeant
- is_cover_sun_protected
- get_weather_data
- cover_tracker.py
- Window Contact Debounce (Xerenas)
- Any
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
- async_enforce_guard
- test_init.py
- set_cover_sun_protected
- sun_protect_conditions_met
- async_build_export
- manifest.json
- test_area_mode_none.py
- test_min_drive_gap.py
- ShutterPositionStore
- const.py
- _ws_delete_shutter
- test_lock_protection_tilt.py
- Bereichs-Karte (Area Card)
- test_frost_protection.py
- config_flow.py
- i18n_parity.mjs
- set_cover_position
- test_sensor_names.py
- CLAUDE.md Project Doc
- Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)
- test_minute_tick_order_independence.py
- TestAwningReport
- _ws_delete_area
- test_duplicate_cover.py
- test_panel.py
- _silent_setting_notes
- test_shutter_automation.py
- get_effective_close_position
- README.md
- Catch-up Drive Bookkeeping (heinzie)
- _condition_note
- test_services.py
- TestHelperEntities
- _drive_group
- .make_guard_entry
- test_forum_2_17.py
- _Connection
- TestNoScheduleIsExplained
- sun_condition_keys
- _shutter
- test_window_trigger_stale_restore.py
- ._setup
- get_window_state
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- TestReloadIsNotAFinding
- __init__.py
- test_elevation_log_disabled.py
- TestRolePositions
- _apply_shutter_automation_state
- test_sun_bounds.py
- CHANGELOG.md
- window_trigger.py
- TestClamp
- TestAlternativeClosePosition
- TestDriveCommandNote
- resolve_shade_position
- TestTheExportExplainsAQuietWindow
- shade_release_opens
- conftest.py
- test_forum_2_15.py
- .test_neighbour_in_the_same_area_is_not
- TestPerShutterOverride
- test_sun_conditions.py
- Sondertage-Sensor (Workday-Sensor)
- TestNextActionWithoutASchedule
- _ticks
- TestHelperConditionInTheReport
- TestRainProtection
- TestAzimuthRowIsItsOwnCheck
- TestSwitchEntity
- get_position_for_role
- TestHysteresis
- services.yaml Service Definitions
- TestWebSocketToggle
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- test_forum_window_contact.py
- TestParseTime
- Shutter Pilot Integration (Brand/Concept)
- callback
- TestHysteresisTheWrongWayRound
- Tests GitHub Workflow

## God Nodes (most connected - your core abstractions)
1. `ShutterPilotPanel` - 111 edges
2. `async_build_export()` - 100 edges
3. `sun_condition_keys()` - 83 edges
4. `is_cover_sun_protected()` - 46 edges
5. `get_window_state()` - 45 edges
6. `evaluate_guard()` - 42 edges
7. `get_position_store()` - 40 edges
8. `get_position_for_role()` - 40 edges
9. `sun_extra_conditions_met()` - 40 edges
10. `set_cover_position()` - 38 edges

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

## Communities (125 total, 12 thin omitted)

### Community 0 - "export.py"
Cohesion: 0.06
Nodes (46): _drive_command_note(), _drive_verdict(), _kind_word(), datetime, Settings export – a forum-ready report of what is actually configured. Every…, Wie die Geraeteart im Bericht heisst., Which cover service this drive actually receives. "It goes the wrong way" is a…, Why an automated opening would not run for this shutter right now. "It never… (+38 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.12
Nodes (26): evaluate_guard(), Decide whether this awning may be out, and say why not. Writes the lockout…, _awning(), _data(), make_entry(), fixture, Einfahren ab `on_above`, Freigabe erst unter `off_below`., 22 km/h liegt unter der Einfahr- und ueber der Freigabeschwelle. Ohne Hysterese… (+18 more)

### Community 2 - "helpers.py"
Cohesion: 0.05
Nodes (80): Binary sensor entities exposing the sun protection state per area., awning_dusk_condition_met(), awning_track_step(), awning_tracks_sun(), close_condition_met(), commanded_position(), condition_memory(), _condition_slot_met() (+72 more)

### Community 3 - "HomeAssistant"
Cohesion: 0.15
Nodes (34): ActiveConnection, async_response, callback, _async_register_websocket(), async_setup(), _find_entry_data(), HomeAssistant, Set up the Shutter Pilot component. (+26 more)

### Community 4 - "brightness.py"
Cohesion: 0.11
Nodes (30): ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener(), ConfigEntry, HomeAssistant, Helper functions for area-based follow-up actions (e.g. lights)., Execute configured light/switch action for an area and direction. direction:… (+22 more)

### Community 5 - "Brightness Mode Time/Sun Window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "switch.py"
Cohesion: 0.07
Nodes (28): async_setup_entry(), _kind_label(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Auto-Mode and master switches for Shutter Pilot., The German word this switch is named after. (+20 more)

### Community 7 - "_ForecastSensorBase"
Cohesion: 0.07
Nodes (23): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+15 more)

### Community 8 - "window_helper.py"
Cohesion: 0.12
Nodes (25): _canonical_state(), _first_entity_id(), get_deferred_close_position(), get_tilt_entity_id(), get_ventilation_position(), has_separate_tilt_entity(), has_tilt_state(), _normalize_state() (+17 more)

### Community 9 - "_entry"
Cohesion: 0.08
Nodes (34): cancel_all(), cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant (+26 more)

### Community 10 - "test_forum_2_18.py"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "get_position_store"
Cohesion: 0.08
Nodes (30): forget_drive_after_close(), Note a drive that waits for the window, in memory and on disk. The shutter…, Take a pending drive out of memory and off disk., Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), get_position_store(), Persistent cover position storage across Home Assistant restarts. (+22 more)

### Community 12 - "test_ventilation.py"
Cohesion: 0.11
Nodes (27): True when every configured ventilation condition holds. All conditions are…, vent_conditions_met(), _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore() (+19 more)

### Community 13 - "TestExportReadsTheWayTheReportWasMeant"
Cohesion: 0.12
Nodes (9): deepcopy_options(), Eine Frage zu stellen darf die Antwort nicht verändern., Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus., Was MartyBrs Export offenliess, obwohl alles darin stand., Fünfstellige Lux-Schwellen an einem Sensor in W/m². Nebeneinander sehen 559,7…, Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung., „Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen., TestExport (+1 more)

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

### Community 18 - "Any"
Cohesion: 0.11
Nodes (32): _condition_rows(), _deferred_close_note(), _dusk_row(), _fmt(), _guard_rows(), _has_window_contact(), _is_set(), _memory_copy() (+24 more)

### Community 20 - "Panel: Build/Resolver Internals"
Cohesion: 0.06
Nodes (22): p, src, target, win, winSrc, code, DEFAULT_PANEL, flat() (+14 more)

### Community 21 - "test_awning_dusk.py"
Cohesion: 0.08
Nodes (33): is_dusk_retracted(), Any, True while dusk retract alone is holding this awning in. Read by elevation.py…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions() (+25 more)

### Community 22 - "_latest_deadline"
Cohesion: 0.13
Nodes (22): _latest_deadline(), time, The clock time this direction runs at regardless of the lux value. None means…, _area(), _as_local(), _berlin(), _monday(), datetime (+14 more)

### Community 23 - "test_shade_hours.py"
Cohesion: 0.10
Nodes (22): True if the clock allows shading right now. Elevation, azimuth, conditions and…, shading_time_window_ok(), _at(), cover_calls(), _fast_startup_restore(), datetime, fixture, Beschattung nur innerhalb bestimmter Uhrzeiten. Aus GitHub-Diskussion #5… (+14 more)

### Community 24 - "get_sun_mode_triggers"
Cohesion: 0.15
Nodes (18): get_sun_mode_triggers(), Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), parametrize, Midsummer: the sun is up at 05:10, the shutters wait until 07:30., Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it., Existing setups must not shift at all. (+10 more)

### Community 25 - "test_awning_shading.py"
Cohesion: 0.15
Nodes (21): awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+13 more)

### Community 26 - "test_sun_protect_areas.py"
Cohesion: 0.13
Nodes (25): _area(), cover_calls(), _fast_startup_restore(), _positions(), fixture, Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-… (+17 more)

### Community 27 - "ShutterPilotAwningGuardSensor"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "test_resume_automation.py"
Cohesion: 0.10
Nodes (24): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+16 more)

### Community 29 - "schedule_times.py"
Cohesion: 0.12
Nodes (28): Diagnostics support for Shutter Pilot., _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times() (+20 more)

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
Cohesion: 0.11
Nodes (12): bjoerg: „nur die Abfrage des Fenstergriffs scheint zu haengen." Sein Kontakt…, Ohne Kipp-Zustand ist alles in Ordnung – dafuer gibt es 2.8.2., Ein `sensor` darf melden, was er will – kein Hinweis., „auf" faltet auf on – erreichbar, also kein Hinweis., c.radis Fall: „wenn das Fenster auf gekippt steht, wird der Rolladen gar nicht…, Steht das Fenster gerade gekippt, ist das die halbe Antwort., Mit dem Haken faehrt er – dann gibt es nichts zu erklaeren., Ohne Kontakt tritt „Fenster offen" nie ein – der Haken tut nichts. (+4 more)

### Community 37 - "test_forum_findings.py"
Cohesion: 0.13
Nodes (14): drives(), fixture, Die fünf Funde aus der Forum-Runde vom 08.08.2026 – und der Export. Zwei…, Aufgezeichnete Fahrbefehle – ohne echte Cover-Integration., Ein Bereich mit Sonnenschutz, Haltezeit 30 min und einer Lux-Bedingung., Eine Runde der Sonnenschutz-Auswertung., F1: der Merker wurde gesetzt, bevor gefahren wurde., F5: die Haltezeit hielt auch das berechtigte Ende auf. (+6 more)

### Community 39 - "is_weekend_schedule"
Cohesion: 0.13
Nodes (15): get_random_offset(), get_time_mode_triggers(), is_weekend_schedule(), date, Return (up, down) times for a time-mode area, jitter included., True if the weekend schedule applies. When a workday sensor is configured it…, Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area() (+7 more)

### Community 40 - "async_enforce_guard"
Cohesion: 0.11
Nodes (17): async_enforce_guard(), async_retract_awning(), describe_reasons(), ConfigEntry, HomeAssistant, One short line for the log and the export., Pull one awning in, bypassing the drive gap and the area stagger., Evaluate every awning and pull in the ones that must not be out. (+9 more)

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "set_cover_sun_protected"
Cohesion: 0.20
Nodes (10): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist…, Ohne Aussperrschutz bleibt es beim eingestellten Wert., Die Rueckfahrhoehe ist die Beschattungsposition, nicht die gekappte., _setup() (+2 more)

### Community 43 - "sun_protect_conditions_met"
Cohesion: 0.05
Nodes (39): azimuth_in_sun_protect_range(), elevation_in_sun_protect_range(), get_azimuth_bounds(), get_elevation_bounds(), Return (min, max) elevation for sun protection range., True when sun elevation is within the configured protection window. Switched…, Return (min, max) azimuth for the windows of this area, in degrees., True when the sun stands in front of this area's windows. Ranges may wrap… (+31 more)

### Community 44 - "async_build_export"
Cohesion: 0.11
Nodes (11): async_build_export(), ConfigEntry, Build the export as markdown plus the raw options behind it., Der Daemmerungs-Verdikt einer Markise - bjoergs Wunsch aus dem Forum (abends…, bjoerg hatte `switch.shutter_pilot_auto_balkon` als Windsensor. Der steht…, TestDuskRow, TestOwnEntityAsGuardSensor, „Warum faehrt er morgens nicht hoch" stand bisher nirgends im Bericht. Jede… (+3 more)

### Community 45 - "manifest.json"
Cohesion: 0.10
Nodes (20): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+12 more)

### Community 46 - "test_area_mode_none.py"
Cohesion: 0.16
Nodes (14): cover_calls(), _fast_startup_restore(), fixture, malleYay: Shutter Pilot nur fuer den Sonnenschutz. „Gibt es eine Moeglichkeit,…, Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein Reload…, Gegenprobe: dieselben Zeiten, nur mit Modus., Der Punkt der ganzen Uebung., Ohne Zeitplan holt niemand den Rollladen von der halben Hoehe. Im Zeitmodus… (+6 more)

### Community 47 - "test_min_drive_gap.py"
Cohesion: 0.15
Nodes (14): _drive_all(), drive_log(), _entry(), fixture, MockConfigEntry, parametrize, Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos). Bei Funk (433…, Nach einer Pause muss die nächste Fahrt sofort raus. (+6 more)

### Community 48 - "ShutterPositionStore"
Cohesion: 0.08
Nodes (25): manual_override_still_blocks(), True if a manual position should keep blocking automated opening. The behaviour…, Any, callback, HomeAssistant, Update one cover and persist., Return stored record if loaded., Return stored position without async load (after async_load was called). (+17 more)

### Community 49 - "const.py"
Cohesion: 0.13
Nodes (19): Dusk retract for awnings: drive in once, never back out on its own. Asked for…, _grace_seconds(), guard_status(), is_barred(), _lockout_seconds(), Any, Wind, rain and ice protection for awnings and roof windows. The one part of…, Read the last decision without touching it. Deliberately does not evaluate:… (+11 more)

### Community 50 - "_ws_delete_shutter"
Cohesion: 0.16
Nodes (17): _area_registry_uids(), Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns., Delete a shutter by index., _shutter_registry_uids(), _ws_delete_shutter(), entry(), fixture (+9 more)

### Community 51 - "test_lock_protection_tilt.py"
Cohesion: 0.13
Nodes (14): get_position_for_window_state(), Target position for one window state, or None while the window is shut. A two-…, Der Aussperrschutz und das gekippte Fenster. bjoerg im Forum, nachdem er seinen…, Wolfs Fall aus 2.10.2 darf sich nicht aendern. Ein zweiwertiger Kontakt meldet…, bjoergs Aufbau: ein Griff mit open / tilted / closed., Wolfs Aufbau aus 2.10.2: zweiwertiger Kontakt, kein Kipp-Zustand., bjoergs Fall: 30 % muessen 30 % bleiben., Die Gegenrichtung – dafuer ist der Aussperrschutz da. (+6 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "test_frost_protection.py"
Cohesion: 0.08
Nodes (27): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), _frost_area(), parametrize, Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Fail closed: wer nichts einstellt, merkt nichts., Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt… (+19 more)

### Community 54 - "config_flow.py"
Cohesion: 0.13
Nodes (13): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+5 more)

### Community 55 - "i18n_parity.mjs"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "set_cover_position"
Cohesion: 0.10
Nodes (18): find_shutter_by_cover(), mark_automation_pending(), Mark cover so the next state change is recorded as automation, not manual., Hold back a drive command until the configured global gap has passed. Radio…, Set cover position (and optionally slat angle) and persist the result. Returns…, The configured entry for one cover entity, or None. Looked up rather than…, _respect_min_drive_gap(), set_cover_position() (+10 more)

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

### Community 61 - "TestAwningReport"
Cohesion: 0.13
Nodes (7): _awning_silent_notes(), Shutter settings left on an awning, where they mean nothing. Same class as…, Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen". Die…, 559,7 neben 30000 erklaert nichts, 559,7 W/m² neben 30000 alles., Faktor 3,6 daneben heisst: die Markise faehrt nie ein., Wie beim Hysterese-Speicher: der Bericht darf nichts verschieben., TestAwningReport

### Community 62 - "_ws_delete_area"
Cohesion: 0.25
Nodes (8): _drop_registry_entries(), Persist new options (deep-copied) to the config entry., Reload the config entry after a short delay to let persistence settle., Remove our own entities from the registry after a delete. Home Assistant keeps…, Delete an area by id., _reload_entry_delayed(), _update_entry_options(), _ws_delete_area()

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

### Community 67 - "get_effective_close_position"
Cohesion: 0.14
Nodes (10): get_effective_close_position(), Apply lock protection (Aussperrschutz): - If lock_protection and window…, Der Deckel klemmt nach unten – an einer Markise die falsche Richtung., Sonst bliebe eine umgestellte Markise bei 20 % im Sturm stehen., TestLockProtection, Tests for per-shutter positions, slats and lock protection., _shutter(), TestLockProtection (+2 more)

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 70 - "Catch-up Drive Bookkeeping (heinzie)"
Cohesion: 0.23
Nodes (11): cover_calls(), _driven(), entry(), datetime, fixture, heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten. Sein…, Genau heinzies Ablauf, vier Schritte., Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden. (+3 more)

### Community 71 - "_condition_note"
Cohesion: 0.13
Nodes (14): _condition_note(), Warn about the two ways a condition passes without meaning anything., _area(), data(), fixture, Forum 2.19.0 – der Aufhebepunkt, der aus einem leeren Feld entstand. bjoerg im…, Frost fragt "kaelter als" – dort ist 0 als Aufhebepunkt normal., Ein leeres Feld faellt auf den Einschaltpunkt zurueck. (+6 more)

### Community 72 - "test_services.py"
Cohesion: 0.19
Nodes (12): cover_calls(), _positions(), fixture, Tests for the group services. Regression guard: open_group/close_group used to…, Each shutter gets its own shading angle, not the first one's., Ventilation reuses the position configured for a tilted window., Users can hook their own automations onto the movement event., test_close_group_uses_per_shutter_positions() (+4 more)

### Community 73 - "TestHelperEntities"
Cohesion: 0.14
Nodes (7): parametrize, Helpers as a condition (DocSpider). A house mode, a cinema flag or a cleaning-…, No on_above/off_below configured, and none needed., The panel stores the option verbatim, HA reports it verbatim., Nothing to compare against – it must not block, but it warns., Mirrors the order the panel renders – list first, domain second., TestHelperEntities

### Community 74 - "_drive_group"
Cohesion: 0.32
Nodes (7): async_setup_services(), _drive_group(), ConfigEntry, HomeAssistant, Shutter Pilot services - open_group, close_group, sun_protect_group (area-…, Register Shutter Pilot services., Drive every shutter of a group to its own configured position for `role`.

### Community 75 - ".make_guard_entry"
Cohesion: 0.24
Nodes (4): `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, TestGuardTableRespectsInversion, TestRainAndIceUnitPlausibility

### Community 76 - "test_forum_2_17.py"
Cohesion: 0.06
Nodes (34): manual_position_is_a_close(), note_manual_position(), True if this shutter takes part in the shading of its area. A separate answer…, True if a hand-driven position is simply "closed", not an override. The manual…, Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, shading_enabled(), cover_calls(), entry() (+26 more)

### Community 77 - "_Connection"
Cohesion: 0.29
Nodes (3): _Connection, Nimmt entgegen, was der Befehl zurueckmeldet. `user` braucht es, weil beide…, _User

### Community 78 - "TestNoScheduleIsExplained"
Cohesion: 0.47
Nodes (3): _entry_with_area(), malleYays Modus im Bericht. Ein Bereich, der nichts faehrt, sieht Einstellung…, TestNoScheduleIsExplained

### Community 79 - "sun_condition_keys"
Cohesion: 0.08
Nodes (22): Merge the global protection settings with this awning's overrides. Most…, resolve_guard_config(), Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), Ein Balkon hinterm Haus sieht anderen Wind als die Terrasse., Ein kleiner Gelenkarm muss frueher rein als eine Kassette daneben., TestConfigResolution, _area() (+14 more)

### Community 80 - "_shutter"
Cohesion: 0.24
Nodes (6): parametrize, Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist., „tilted" ist kein Synonym von on/off und darf keins werden., heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`., _shutter(), TestBinarySensorOpenSynonyms

### Community 81 - "test_window_trigger_stale_restore.py"
Cohesion: 0.25
Nodes (9): cover_calls(), _fast_startup(), _positions(), fixture, Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine veraltete…, Fahrten mitschreiben und die Position tatsaechlich im State nachziehen., _setup(), _shutter() (+1 more)

### Community 82 - "._setup"
Cohesion: 0.30
Nodes (5): hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es leider…, Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py, nur an der…, Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal zu. Die…, TestGuardBeatsShadingForAWindow, TestOpeningAndClosingByConditions

### Community 83 - "get_window_state"
Cohesion: 0.12
Nodes (12): get_window_state(), Return: "closed" | "tilted" | "open" Supports both binary_sensor and sensor…, Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact, The existing single-contact behaviour must not shift at all., While tilted, many contacts also read 'open' – tilt must win. (+4 more)

### Community 84 - "Shutter Pilot Sidebar Panel"
Cohesion: 0.20
Nodes (11): Admin-Rechteprüfung (require_admin), Entitätsauswahl (Suchfeld statt lange Liste), HACS Default Store PR hacs/default#9592, i18n: 11 Sprachen im Panel, Mac Catalyst native Picker Absturz, Shutter Pilot Sidebar Panel, Shutter Pilot info.md (HACS store text), FUNDING.yml Sponsor Button (+3 more)

### Community 85 - "Sonnenschutz / Beschattung"
Cohesion: 0.20
Nodes (11): Fahrtkontrolle (cover_verify), Mindestabstand zwischen Fahrbefehlen, An der Beschattung teilnehmen (shading_enabled), Beschattungs-Zeitfenster (shade_from/shade_to), Beschattungszeitraum (Monate), Sonnenschutz / Beschattung, Wetter & Vorhersage (weather_data.py Konzept), FORUM_POST.md Draft Posts (+3 more)

### Community 87 - "TestReloadIsNotAFinding"
Cohesion: 0.33
Nodes (3): Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., TestReloadIsNotAFinding

### Community 88 - "__init__.py"
Cohesion: 0.10
Nodes (28): ConfigEntry, HomeAssistant, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), ConfigEntry, HomeAssistant, Set up periodic sun evaluation for sun protection., setup_elevation_listener() (+20 more)

### Community 89 - "test_elevation_log_disabled.py"
Cohesion: 0.31
Nodes (7): cover_calls(), _fast_startup(), fixture, Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich, wenn…, _setup(), TestElevationLogReflectsWhetherItDecided, _tick_elevation()

### Community 90 - "TestRolePositions"
Cohesion: 0.33
Nodes (3): parametrize, The group services used to hard-code 100/0 and ignore these values., TestRolePositions

### Community 91 - "_apply_shutter_automation_state"
Cohesion: 0.40
Nodes (4): _apply_shutter_automation_state(), Keep the per-shutter automation switch in step with the saved value. The…, Der Wert liegt im Config-Entry und geht beim Speichern nicht verloren., TestOptionsRoundTrip

### Community 92 - "test_sun_bounds.py"
Cohesion: 0.19
Nodes (11): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, _local_timezone(), datetime, fixture, Tests for the earliest/latest clock bounds in sun mode. MartyBr's case from the…, The exact setup described in the forum., Run these tests in Berlin. The default test timezone is US/Pacific, but… (+3 more)

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "window_trigger.py"
Cohesion: 0.22
Nodes (8): cancel_window_close(), _debounce_seconds(), _is_cover_effectively_closed(), Any, Window trigger logic - React to window open/close for shutters., True if cover is close enough to its configured closed position., How long "closed" has to hold before we act on it., Drop a pending close reaction, e.g. because the window opened again.

### Community 97 - "TestDriveCommandNote"
Cohesion: 0.39
Nodes (3): Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote

### Community 98 - "resolve_shade_position"
Cohesion: 0.29
Nodes (5): The shading position for this shutter right now, plus how it was picked. Three…, resolve_shade_position(), parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition

### Community 100 - "shade_release_opens"
Cohesion: 0.38
Nodes (4): True if the end of the shading day should drive the cover open. Without a…, shade_release_opens(), Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest., TestShadeReleaseIsImplied

### Community 101 - "conftest.py"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "test_forum_2_15.py"
Cohesion: 0.09
Nodes (22): automated_up_blocked(), no_up_condition_blocks(), datetime, True while a configured condition forbids the automated opening. "Whatever my…, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading() (+14 more)

### Community 103 - ".test_neighbour_in_the_same_area_is_not"
Cohesion: 0.36
Nodes (5): Update runtime sun protection state for dashboard and skip logic., set_sun_protect_active(), Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 104 - "TestPerShutterOverride"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 105 - "test_sun_conditions.py"
Cohesion: 0.29
Nodes (5): data(), fixture, Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, Extra conditions gate shading; they never widen the sun window., TestGeometryStillApplies

### Community 106 - "Sondertage-Sensor (Workday-Sensor)"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 107 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 108 - "_ticks"
Cohesion: 0.22
Nodes (8): Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, Die Sperre wirkt im Scheduler – und nur nach oben., Sonst stuende das Haus unter der Ferien-Kennung den Abend offen., hollizone: bei offenem Dachfenster soll die Beschattung warten. Kein neuer Code…, _rearm_scheduler(), TestShadingWaitsForTheWindow, TestUpIsBlocked, _ticks()

### Community 109 - "TestHelperConditionInTheReport"
Cohesion: 0.33
Nodes (3): Ein an/aus-Helfer hat keine Schwellen – und das muss dastehen. Sonst zeigt die…, Slots a-d haben keine Vorgabe-Invertierung, sind aber seit 2.21.5 per Checkbox…, TestHelperConditionInTheReport

### Community 110 - "TestRainProtection"
Cohesion: 0.33
Nodes (3): Kein Wert = Gefahr. Am Fenster ist das die richtige Richtung., Ecowitt liefert mm/h – Zahl mit Hysterese statt an/aus., TestRainProtection

### Community 112 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 113 - "get_position_for_role"
Cohesion: 0.07
Nodes (29): clamp_to_rest(), extends_upward(), The safe position for this kind – retracted, or shut., True when a higher cover position means "further out" for this device. Almost…, Cap a target so it never sits further out than the rest position. Deliberately…, rest_position(), filter_shutters_by_area(), get_position_for_role() (+21 more)

### Community 114 - "TestHysteresis"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "test_forum_window_contact.py"
Cohesion: 0.29
Nodes (5): cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, `cover.buro`: beschattet auf 80 %, Kontakt „open" an einem binary_sensor. Beide…, TestHeinziesSetup

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **93 isolated node(s):** `domain`, `name`, `weather`, `@fschubi`, `config_flow` (+88 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 954 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `sun_condition_keys()` connect `sun_condition_keys` to `export.py`, `evaluate_guard`, `helpers.py`, `test_ventilation.py`, `Any`, `test_awning_shading.py`, `test_sun_protect_areas.py`, `test_resume_automation.py`, `test_forum_2_21_3.py`, `resolve_shading_config`, `async_enforce_guard`, `sun_protect_conditions_met`, `async_build_export`, `const.py`, `test_frost_protection.py`, `_condition_note`, `.make_guard_entry`, `test_forum_2_17.py`, `._setup`, `__init__.py`, `TestAlternativeClosePosition`, `TestTheExportExplainsAQuietWindow`, `test_forum_2_15.py`, `test_sun_conditions.py`, `TestRainProtection`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **What connects `domain`, `name`, `weather` to the rest of the system?**
  _93 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `export.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06103896103896104 - nodes in this community are weakly interconnected._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._