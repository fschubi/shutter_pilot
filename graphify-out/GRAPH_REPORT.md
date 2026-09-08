# Graph Report - shutter_pilot  (2026-09-08)

## Corpus Check
- 106 files · ~213,776 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2883 nodes · 6576 edges · 132 communities (122 shown, 9 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5967ceb0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- const.py
- evaluate_guard
- helpers.py
- __init__.py
- brightness.py
- _area_window
- ShutterPilotShutterAutomationSwitch
- _ForecastSensorBase
- window_helper.py
- _entry
- test_forum_2_18.py
- get_position_store
- test_ventilation.py
- manual_override_still_blocks
- test_forum_2_15.py
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
- _area
- TestAwningReport
- test_init.py
- set_cover_sun_protected
- sun_protect_conditions_met
- test_window_trigger_shaded_manual_reopen.py
- manifest.json
- test_area_mode_none.py
- test_min_drive_gap.py
- ShutterPositionStore
- is_weekend_schedule
- _ws_delete_shutter
- test_lock_protection_tilt.py
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
- test_export_notes.py
- _shutter
- _shutter
- README.md
- Catch-up Drive Bookkeeping (heinzie)
- test_forum_2_19.py
- test_services.py
- TestHelperEntities
- clamp_to_bounds
- .make_guard_entry
- test_forum_2_17.py
- get_tilt_entity_id
- elevation_in_sun_protect_range
- sun_condition_keys
- _shutter
- test_window_trigger_stale_restore.py
- ._setup
- get_window_state
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- test_frost_protection.py
- async_unload_entry
- test_elevation_log_disabled.py
- test_shutter_positions.py
- _apply_shutter_automation_state
- test_blind_drive.py
- CHANGELOG.md
- test_manual_move_clears_pending_drive.py
- test_shutter_automation.py
- close_condition_met
- fixture
- resolve_shade_position
- TestTheExportExplainsAQuietWindow
- setup_elevation_listener
- conftest.py
- automated_up_blocked
- no_up_condition_blocks
- TestPerShutterOverride
- test_sun_conditions.py
- Sondertage-Sensor (Workday-Sensor)
- test_forum_window_contact.py
- is_cover_sun_protected
- .test_neighbour_in_the_same_area_is_not
- TestSingleContactUnchanged
- TestSecondWindowContact
- TestSwitchEntity
- get_effective_close_position
- TestHysteresis
- services.yaml Service Definitions
- test_geometry_and_season.py
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- get_elevation_bounds
- TestParseTime
- Shutter Pilot Integration (Brand/Concept)
- TestNextActionWithoutASchedule
- TestAzimuthRowIsItsOwnCheck
- season_allows_shading
- .test_dead_sensor_does_not_trigger
- TestWebSocketToggle
- Tests GitHub Workflow
- _condition_slot_met
- TestGuardGateAppliesByHasGuardNotByAwning
- _local_timezone
- cover_calls

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
10. `CLAUDE.md – Fortschritts-Log (Archiv)` - 43 edges

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

## Communities (132 total, 9 thin omitted)

### Community 0 - "const.py"
Cohesion: 0.06
Nodes (65): Dusk retract for awnings: drive in once, never back out on its own. Asked for…, async_retract_awning(), clamp_to_rest(), describe_reasons(), extends_upward(), _grace_seconds(), guard_status(), is_barred() (+57 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.06
Nodes (50): async_enforce_guard(), evaluate_guard(), ConfigEntry, HomeAssistant, Decide whether this awning may be out, and say why not. Writes the lockout…, Evaluate every awning and pull in the ones that must not be out., Watch the guard sensors and hold the minute tick as a safety net., Merge the global protection settings with this awning's overrides. Most… (+42 more)

### Community 2 - "helpers.py"
Cohesion: 0.05
Nodes (85): commanded_position(), condition_memory(), _cover_is_travelling(), find_shutter_by_cover(), forget_drive_after_close(), get_cover_current_position(), get_sun_condition_status(), get_sun_protect_status_for_areas() (+77 more)

### Community 3 - "__init__.py"
Cohesion: 0.13
Nodes (40): ActiveConnection, async_migrate_entry(), _async_register_websocket(), async_setup(), _find_entry_data(), callback, HomeAssistant, Shutter Pilot - Rollladensteuerung für Home Assistant. (+32 more)

### Community 4 - "brightness.py"
Cohesion: 0.08
Nodes (40): ConfigEntry, HomeAssistant, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener() (+32 more)

### Community 5 - "_area_window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "ShutterPilotShutterAutomationSwitch"
Cohesion: 0.07
Nodes (25): async_setup_entry(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Global switch to enable/disable all Shutter Pilot automation., Switch to enable/disable automation for an area., Switch to enable/disable the sun protection of one area. Separate from the… (+17 more)

### Community 7 - "_ForecastSensorBase"
Cohesion: 0.07
Nodes (23): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+15 more)

### Community 8 - "window_helper.py"
Cohesion: 0.16
Nodes (20): _canonical_state(), _first_entity_id(), get_deferred_close_position(), get_position_for_window_state(), get_ventilation_position(), has_tilt_state(), _normalize_state(), Any (+12 more)

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

### Community 14 - "test_forum_2_15.py"
Cohesion: 0.10
Nodes (20): cover_calls(), _fast_startup_restore(), fixture, Die Meldungen aus dem Forum vom August, gegen den echten Code gehalten. Vier…, Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, charly166 und Linos: nicht beschatten, was noch gar nicht offen ist., Das bisherige Verhalten – und genau das, was gemeldet wurde., MartyBr: die Beschattung je Bereich abschalten, ohne die Automatik. (+12 more)

### Community 15 - "get_weather_data"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "cover_tracker.py"
Cohesion: 0.13
Nodes (22): async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant, Track cover positions and restore after Home Assistant restart., After HA start, restore persisted positions if cover integration restored wrong…, Listen to cover state changes and persist positions., setup_cover_position_tracker() (+14 more)

### Community 17 - "Window Contact Debounce (Xerenas)"
Cohesion: 0.11
Nodes (28): cover_calls(), _gated_sleep(), _positions(), fixture, parametrize, Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum. Beim…, Fensterzustand melden und alles zu Ende laufen lassen., Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.… (+20 more)

### Community 18 - "export.py"
Cohesion: 0.09
Nodes (45): Return the "compare downwards" option key for a slot., sun_condition_invert_key(), _condition_note(), _condition_rows(), _deferred_close_note(), _drive_command_note(), _drive_verdict(), _dusk_row() (+37 more)

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
Cohesion: 0.13
Nodes (22): get_sun_mode_triggers(), Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), parametrize, Tests for the earliest/latest clock bounds in sun mode. MartyBr's case from the…, Midsummer: the sun is up at 05:10, the shutters wait until 07:30., Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it. (+14 more)

### Community 25 - "test_awning_shading.py"
Cohesion: 0.15
Nodes (21): awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+13 more)

### Community 26 - "test_sun_protect_areas.py"
Cohesion: 0.14
Nodes (22): _area(), _positions(), Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-…, Fällt die Bedingung des *Runter*-Bereichs weg, wird freigegeben., Der Bereichswert lief aus dem Tritt und blockierte Hochfahrten., Der einfache Fall muss sich unverändert verhalten. (+14 more)

### Community 27 - "ShutterPilotAwningGuardSensor"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "test_resume_automation.py"
Cohesion: 0.10
Nodes (24): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+16 more)

### Community 29 - "schedule_times.py"
Cohesion: 0.13
Nodes (27): _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times(), parse_time() (+19 more)

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

### Community 39 - "_area"
Cohesion: 0.19
Nodes (10): get_random_offset(), get_time_mode_triggers(), date, Return (up, down) times for a time-mode area, jitter included., Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area(), Tests for the schedule maths: weekday detection, jitter, trigger times., Scheduler and sensor must agree, so repeated calls must match. (+2 more)

### Community 40 - "TestAwningReport"
Cohesion: 0.13
Nodes (7): _awning_silent_notes(), Shutter settings left on an awning, where they mean nothing. Same class as…, Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen". Die…, 559,7 neben 30000 erklaert nichts, 559,7 W/m² neben 30000 alles., Faktor 3,6 daneben heisst: die Markise faehrt nie ein., Wie beim Hysterese-Speicher: der Bericht darf nichts verschieben., TestAwningReport

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "set_cover_sun_protected"
Cohesion: 0.20
Nodes (10): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist…, Ohne Aussperrschutz bleibt es beim eingestellten Wert., Die Rueckfahrhoehe ist die Beschattungsposition, nicht die gekappte., _setup() (+2 more)

### Community 43 - "sun_protect_conditions_met"
Cohesion: 0.17
Nodes (12): azimuth_in_sun_protect_range(), True when the sun stands in front of this area's windows. Ranges may wrap…, True when both elevation and compass direction call for shading., sun_protect_conditions_met(), _area(), parametrize, Tests for elevation + azimuth based sun protection., The bug azimuth support fixes: 0–15° elevation is hit twice a day. (+4 more)

### Community 44 - "test_window_trigger_shaded_manual_reopen.py"
Cohesion: 0.23
Nodes (10): cover_calls(), _fast_startup(), _positions(), fixture, Ein Beschattungs-Merker (shaded=True) ueberlebt eine manuelle Fahrt.…, Rollladen ist von Hand voll offen (100%), der Beschattungs-Merker aus der…, Gegenprobe zum Fix: steht der Rollladen tatsaechlich noch an seiner…, _setup() (+2 more)

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
Cohesion: 0.11
Nodes (16): Any, callback, HomeAssistant, Persistent cover position storage across Home Assistant restarts., Update one cover and persist., Return stored record if loaded., Return stored position without async load (after async_load was called)., JSON store for last known cover positions (per config entry). (+8 more)

### Community 49 - "is_weekend_schedule"
Cohesion: 0.27
Nodes (5): is_weekend_schedule(), True if the weekend schedule applies. When a workday sensor is configured it…, A public holiday on a Monday must use the weekend schedule., Shift work: a Saturday that is a working day uses the weekday plan., TestWeekendDetection

### Community 50 - "_ws_delete_shutter"
Cohesion: 0.09
Nodes (28): async_response, _area_registry_uids(), _drop_registry_entries(), ConfigEntry, Persist new options (deep-copied) to the config entry., Remove our own entities from the registry after a delete. Home Assistant keeps…, Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns. (+20 more)

### Community 51 - "test_lock_protection_tilt.py"
Cohesion: 0.14
Nodes (12): Der Aussperrschutz und das gekippte Fenster. bjoerg im Forum, nachdem er seinen…, Wolfs Fall aus 2.10.2 darf sich nicht aendern. Ein zweiwertiger Kontakt meldet…, bjoergs Aufbau: ein Griff mit open / tilted / closed., Wolfs Aufbau aus 2.10.2: zweiwertiger Kontakt, kein Kipp-Zustand., bjoergs Fall: 30 % muessen 30 % bleiben., Die Gegenrichtung – dafuer ist der Aussperrschutz da., Wer die Kipp-Position hoeher legt, merkt von der Aenderung nichts., TestTheTwoStateContactKeepsItsCap (+4 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "frost_condition_met"
Cohesion: 0.17
Nodes (11): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), Fail closed: wer nichts einstellt, merkt nichts., Vor der Trennung der drei Polaritaeten (siehe _slot_reading() in helpers.py)…, Ein binary_sensor, dessen 'aus' Frost bedeutet - ohne die Invertierung liest…, Kein Default-Umdrehen fuer Booleans, auch nicht bei Frost: ein gewoehnlicher…, Ohne Invertierung liesse sich "unter X" nicht ausdrücken. (+3 more)

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
Cohesion: 0.05
Nodes (25): async_build_export(), Build the export as markdown plus the raw options behind it., Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., Der Daemmerungs-Verdikt einer Markise - bjoergs Wunsch aus dem Forum (abends…, Ein an/aus-Helfer hat keine Schwellen – und das muss dastehen. Sonst zeigt die…, Slots a-d haben keine Vorgabe-Invertierung, sind aber seit 2.21.5 per Checkbox…, bjoerg hatte `switch.shutter_pilot_auto_balkon` als Windsensor. Der steht… (+17 more)

### Community 62 - "CLAUDE.md – Fortschritts-Log (Archiv)"
Cohesion: 0.05
Nodes (43): 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf, 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck), 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos), 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas), 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum, 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues, 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet, 2026-08-07 – 2.7.1: die drei Restpunkte (+35 more)

### Community 63 - "test_duplicate_cover.py"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "test_panel.py"
Cohesion: 0.17
Nodes (13): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, bjoerg (Forum): eine leere Stelle statt eines Icons vor „Hochfahren…, bjoerg (Forum): am Lux-Feld war der Schieber winzig, das Zahlenfeld riesig.…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., _run(), test_all_eleven_languages_carry_the_same_keys() (+5 more)

### Community 65 - "test_export_notes.py"
Cohesion: 0.13
Nodes (10): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos., malleYays Modus im Bericht. Ein Bereich, der nichts faehrt, sieht Einstellung…, Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie. (+2 more)

### Community 66 - "_shutter"
Cohesion: 0.18
Nodes (9): Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen…, Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.…, Bestandsanlagen kennen den Schlüssel nicht – die müssen weiterlaufen., Der Schalter ist die lebende Wahrheit, der gespeicherte Wert der Start., Der eigene Schalter des Rollladens hat den Laufzeitwert schon gesetzt., Fail open: Ein toter Schalter darf keinen Rollladen stilllegen., Umgelegter Schalter wirkt sofort, ohne Reload des Config-Entry., _shutter() (+1 more)

### Community 67 - "_shutter"
Cohesion: 0.31
Nodes (3): _shutter(), TestLockProtection, TestTilt

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 70 - "Catch-up Drive Bookkeeping (heinzie)"
Cohesion: 0.23
Nodes (11): cover_calls(), _driven(), entry(), datetime, fixture, heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten. Sein…, Genau heinzies Ablauf, vier Schritte., Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden. (+3 more)

### Community 71 - "test_forum_2_19.py"
Cohesion: 0.13
Nodes (12): _area(), data(), fixture, Forum 2.19.0 – der Aufhebepunkt, der aus einem leeren Feld entstand. bjoerg im…, Frost fragt "kaelter als" – dort ist 0 als Aufhebepunkt normal., Ein leeres Feld faellt auf den Einschaltpunkt zurueck., bjoergs Fall: 0 ist eine echte Schranke, kein "leer"., Nach einem Neustart ist der Merker leer – dann gilt on_above. (+4 more)

### Community 72 - "test_services.py"
Cohesion: 0.19
Nodes (12): cover_calls(), _positions(), fixture, Tests for the group services. Regression guard: open_group/close_group used to…, Each shutter gets its own shading angle, not the first one's., Ventilation reuses the position configured for a tilted window., Users can hook their own automations onto the movement event., test_close_group_uses_per_shutter_positions() (+4 more)

### Community 73 - "TestHelperEntities"
Cohesion: 0.14
Nodes (7): parametrize, Helpers as a condition (DocSpider). A house mode, a cinema flag or a cleaning-…, No on_above/off_below configured, and none needed., The panel stores the option verbatim, HA reports it verbatim., Nothing to compare against – it must not block, but it warns., Mirrors the order the panel renders – list first, domain second., TestHelperEntities

### Community 74 - "clamp_to_bounds"
Cohesion: 0.42
Nodes (4): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, datetime, TestClampHelper

### Community 75 - ".make_guard_entry"
Cohesion: 0.24
Nodes (4): `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, TestGuardTableRespectsInversion, TestRainAndIceUnitPlausibility

### Community 76 - "test_forum_2_17.py"
Cohesion: 0.06
Nodes (32): manual_position_is_a_close(), note_manual_position(), True if a hand-driven position is simply "closed", not an override. The manual…, Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, cover_calls(), entry(), _fast_startup_restore(), _positions() (+24 more)

### Community 77 - "get_tilt_entity_id"
Cohesion: 0.27
Nodes (7): get_tilt_entity_id(), has_separate_tilt_entity(), Entity id of the optional separate tilt contact, or empty string., True if this shutter uses a dedicated entity for the tilted state., parametrize, Tests for window state detection, including a separate tilt contact. Forum…, TestHelpers

### Community 78 - "elevation_in_sun_protect_range"
Cohesion: 0.18
Nodes (7): elevation_in_sun_protect_range(), True when sun elevation is within the configured protection window. Switched…, Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., TestElevationCanBeSwitchedOff

### Community 79 - "sun_condition_keys"
Cohesion: 0.16
Nodes (14): Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), Read one condition slot's raw comparison, or None if it cannot be judged. None…, _slot_reading(), _area(), Die drei Polaritäten der Bedingungs-Slots, an einer Stelle geprüft.…, Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False., Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None mehr, das… (+6 more)

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
Cohesion: 0.19
Nodes (6): get_window_state(), Return: "closed" | "tilted" | "open" Supports both binary_sensor and sensor…, TestWindowState, While tilted, many contacts also read 'open' – tilt must win., A configured but absent tilt entity must not break detection., TestSeparateTiltEntity

### Community 84 - "Shutter Pilot Sidebar Panel"
Cohesion: 0.20
Nodes (11): Admin-Rechteprüfung (require_admin), Entitätsauswahl (Suchfeld statt lange Liste), HACS Default Store PR hacs/default#9592, i18n: 11 Sprachen im Panel, Mac Catalyst native Picker Absturz, Shutter Pilot Sidebar Panel, Shutter Pilot info.md (HACS store text), FUNDING.yml Sponsor Button (+3 more)

### Community 85 - "Sonnenschutz / Beschattung"
Cohesion: 0.20
Nodes (11): Fahrtkontrolle (cover_verify), Mindestabstand zwischen Fahrbefehlen, An der Beschattung teilnehmen (shading_enabled), Beschattungs-Zeitfenster (shade_from/shade_to), Beschattungszeitraum (Monate), Sonnenschutz / Beschattung, Wetter & Vorhersage (weather_data.py Konzept), FORUM_POST.md Draft Posts (+3 more)

### Community 87 - "test_frost_protection.py"
Cohesion: 0.20
Nodes (12): Pick how far this shutter closes: fully, partially, or frost-safe. Shared by…, resolve_close_role(), _frost_area(), Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten., Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet., Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen., Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten. (+4 more)

### Community 88 - "async_unload_entry"
Cohesion: 0.29
Nodes (7): async_unload_entry(), Unload a config entry., cancel_all_window_close(), cancel_window_close(), Any, Drop a pending close reaction, e.g. because the window opened again., Drop every pending close reaction, for unload and reload.

### Community 89 - "test_elevation_log_disabled.py"
Cohesion: 0.31
Nodes (7): cover_calls(), _fast_startup(), fixture, Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich, wenn…, _setup(), TestElevationLogReflectsWhetherItDecided, _tick_elevation()

### Community 90 - "test_shutter_positions.py"
Cohesion: 0.25
Nodes (4): parametrize, Tests for per-shutter positions, slats and lock protection., The group services used to hard-code 100/0 and ignore these values., TestRolePositions

### Community 91 - "_apply_shutter_automation_state"
Cohesion: 0.40
Nodes (4): _apply_shutter_automation_state(), Keep the per-shutter automation switch in step with the saved value. The…, Der Wert liegt im Config-Entry und geht beim Speichern nicht verloren., TestOptionsRoundTrip

### Community 92 - "test_blind_drive.py"
Cohesion: 0.15
Nodes (11): _blind(), entry(), _normal(), fixture, Rollläden ohne Positionsrückmeldung (Wunsch von Viktor, ESP Somfy RTS).…, Der Antrieb meldet keine Position – nur `state`, kein current_position., Bisheriges Verhalten für alle anderen Rollläden., Vor der ersten Fahrt weiss auch die Buchführung nichts. (+3 more)

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "test_manual_move_clears_pending_drive.py"
Cohesion: 0.29
Nodes (8): cover_calls(), _fast_startup(), _positions(), fixture, Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine spaetere…, _setup(), _shutter(), TestStalePendingDriveAfterManualMove

### Community 95 - "test_shutter_automation.py"
Cohesion: 0.24
Nodes (7): cover_calls(), _positions(), fixture, Automatik pro Rollladen – dritte Ebene unter Hauptschalter und Bereich. Der…, Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt., TestDrivePaths

### Community 96 - "close_condition_met"
Cohesion: 0.15
Nodes (8): close_condition_met(), True when the area's conditions for a partial evening close apply. Same…, Unlike shading conditions, an unset close condition means "no"., Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Bestandsanlagen haben nur die erste – die muss unverändert wirken., Fail closed: ein toter Sensor darf nicht alles halb offen lassen., TestAlternativeClosePosition, TestSecondCloseCondition

### Community 97 - "fixture"
Cohesion: 0.13
Nodes (8): entry(), fixture, Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „Mein Regensensor liefert nur nass und trocken". In…, Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote, TestGuardSensorWithoutNumbers

### Community 98 - "resolve_shade_position"
Cohesion: 0.29
Nodes (5): The shading position for this shutter right now, plus how it was picked. Three…, resolve_shade_position(), parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition

### Community 100 - "setup_elevation_listener"
Cohesion: 0.09
Nodes (20): is_dusk_retracted(), Any, True while dusk retract alone is holding this awning in. Read by elevation.py…, Diagnostics support for Shutter Pilot., ConfigEntry, HomeAssistant, Set up periodic sun evaluation for sun protection., setup_elevation_listener() (+12 more)

### Community 101 - "conftest.py"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "automated_up_blocked"
Cohesion: 0.23
Nodes (8): automated_up_blocked(), datetime, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, weekend_blocks_up(), c.radi, Linos, hollsten: am Wochenende gar nicht hochfahren., hollstens Fall: samstags arbeiten, sonntags ausschlafen. Der Sondertage-Sensor…, TestWeekendBlocksUp

### Community 103 - "no_up_condition_blocks"
Cohesion: 0.36
Nodes (5): no_up_condition_blocks(), True while a configured condition forbids the automated opening. "Whatever my…, Linos: eine Bedingung, die das morgendliche Oeffnen blockiert., Die eine Richtung, in der ein Fehler nicht wehtun darf. Andersherum bliebe…, TestNoUpCondition

### Community 104 - "TestPerShutterOverride"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 105 - "test_sun_conditions.py"
Cohesion: 0.29
Nodes (5): data(), fixture, Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, Extra conditions gate shading; they never widen the sun window., TestGeometryStillApplies

### Community 106 - "Sondertage-Sensor (Workday-Sensor)"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 107 - "test_forum_window_contact.py"
Cohesion: 0.29
Nodes (5): cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, `cover.buro`: beschattet auf 80 %, Kontakt „open" an einem binary_sensor. Beide…, TestHeinziesSetup

### Community 108 - "is_cover_sun_protected"
Cohesion: 0.33
Nodes (5): is_cover_sun_protected(), True if shading currently holds this specific cover., bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest., Das alte Verhalten: Merker faellt, gefahren wird nicht., TestShadeReleaseOpens

### Community 109 - ".test_neighbour_in_the_same_area_is_not"
Cohesion: 0.48
Nodes (3): Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 110 - "TestSingleContactUnchanged"
Cohesion: 0.38
Nodes (3): The existing single-contact behaviour must not shift at all., _shutter(), TestSingleContactUnchanged

### Community 111 - "TestSecondWindowContact"
Cohesion: 0.27
Nodes (4): Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact

### Community 112 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 113 - "get_effective_close_position"
Cohesion: 0.07
Nodes (28): filter_shutters_by_area(), only_shutters(), Filter shutters by area_up_id or area_down_id. Every kind is in by default…, Keep just the shutters from a list of covers about to be driven. Filtering here…, get_effective_close_position(), Apply lock protection (Aussperrschutz): - If lock_protection and window…, _awning(), cover_calls() (+20 more)

### Community 114 - "TestHysteresis"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "test_geometry_and_season.py"
Cohesion: 0.17
Nodes (11): get_azimuth_bounds(), Return (min, max) azimuth for the windows of this area, in degrees., Merge area and shutter shading geometry into one config dict. A room can have…, resolve_sun_geometry(), Tests for per-shutter shading geometry, season window and partial close. Forum…, Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch., The case Linos described: one room, south and west windows. (+3 more)

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "get_elevation_bounds"
Cohesion: 0.27
Nodes (5): get_elevation_bounds(), Return (min, max) elevation for sun protection range., Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, TestElevationBounds

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 124 - "season_allows_shading"
Cohesion: 0.33
Nodes (5): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, October to March must wrap, like the azimuth range does., TestSeason

### Community 125 - ".test_dead_sensor_does_not_trigger"
Cohesion: 0.22
Nodes (4): parametrize, Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, 0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert., TestPosition

### Community 126 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 128 - "_condition_slot_met"
Cohesion: 0.25
Nodes (6): _condition_slot_met(), Evaluate one extra shading condition. Unreadable never blocks shading., MartyBr trug beim Azimut 40 / 130 ein und meinte den Bereich 40°–130°., TestHysteresisTheWrongWayRound, Die bestehenden Bedingungen dürfen sich nicht verändert haben., TestNormalDirectionUnchanged

### Community 130 - "_local_timezone"
Cohesion: 0.67
Nodes (3): _local_timezone(), fixture, Run these tests in Berlin. The default test timezone is US/Pacific, but…

### Community 131 - "cover_calls"
Cohesion: 0.67
Nodes (3): cover_calls(), _fast_startup_restore(), fixture

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **135 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+130 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1001 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `ShutterPilotPanel` to `shutter-pilot-panel.js`, `Panel: Main Render & Lists`, `.t`, `._renderCondDetail`, `._dashCard`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _135 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `const.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055379746835443035 - nodes in this community are weakly interconnected._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.05726975222066386 - nodes in this community are weakly interconnected._