# Graph Report - shutter_pilot  (2026-11-03)

## Corpus Check
- 133 files · ~264,847 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3484 nodes · 8030 edges · 150 communities (135 shown, 12 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `94ed6a5a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_brightness_lux_hold.py
- evaluate_guard
- cover_tracker.py
- frost_condition_met
- helpers.py
- _area_window
- switch.py
- sensor.py
- test_raffstore_storm_and_lock.py
- cover_verify.py
- test_forum_2_18.py
- ShutterPilotNextActionSensor
- test_ventilation.py
- TestExportReadsTheWayTheReportWasMeant
- _setup
- get_weather_data
- note_manual_position
- Window Contact Debounce (Xerenas)
- elevation.py
- ShutterPilotPanel
- harness.mjs
- test_awning_dusk.py
- _latest_deadline
- test_shade_hours.py
- get_sun_mode_triggers
- test_awning_shading.py
- is_cover_sun_protected
- ShutterPilotAwningGuardSensor
- test_resume_automation.py
- TestSecondWindowContact
- test_forum_2_21_3.py
- _status
- shutter-pilot-panel.js
- resolve_shading_config
- sun_extra_conditions_met
- ._note
- test_forum_findings.py
- ._renderShutterForm
- is_weekend_schedule
- ConfigEntry
- test_init.py
- test_tilt_hand_detect.py
- sun_protect_conditions_met
- .test_scheduler_skips_disabled_shutter
- manifest.json
- test_area_mode_none.py
- test_min_drive_gap.py
- .async_load
- test_reorder_shutters.py
- ._coverAction
- Bereichs-Karte (Area Card)
- test_keep_position_and_tilt.py
- ShutterPilotOptionsFlow
- i18n_parity.mjs
- set_cover_position
- test_sensor_names.py
- CLAUDE.md Project Doc
- Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)
- test_minute_tick_order_independence.py
- TestAwningReport
- CLAUDE.md – Fortschritts-Log (Archiv)
- test_duplicate_cover.py
- test_panel.py
- test_export_notes.py
- _shutter
- test_window_trigger_stale_restore.py
- README.md
- test_privacy.py
- Catch-up Drive Bookkeeping (heinzie)
- sun_condition_invert_key
- test_services.py
- TestHelperEntities
- const.py
- ._area
- _setup_drive
- export.py
- resolve_sun_geometry
- season_allows_shading
- set_cover_sun_protected
- test_door_lock_raffstore.py
- ._setup
- _condition_slot_met
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- test_lock_replay_restore.py
- test_shared_automation_switch.py
- test_elevation_log_disabled.py
- test_services_forget_window_cycle.py
- async_build_export
- brightness.py
- CHANGELOG.md
- test_manual_move_clears_pending_drive.py
- has_frost_close_position
- test_geometry_and_season.py
- sun_condition_keys
- Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)
- set_sun_protect_active
- TestDriveCommandNote
- conftest.py
- Gesamtplan Raffstores
- manual_override_still_blocks
- TestPerShutterOverride
- test_sun_conditions.py
- Sondertage-Sensor (Workday-Sensor)
- _rearm_scheduler
- _ws_delete_shutter
- test_reference_run.py
- TestHelperConditionInTheReport
- _slot_reading
- TestShadingWaitsForTheWindow
- .test_south_and_west_trigger_at_different_times
- test_my_position_blind_drive.py
- services.yaml Service Definitions
- clamp_to_bounds
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- test_window_trigger_shaded_manual_reopen.py
- __init__.py
- Shutter Pilot Integration (Brand/Concept)
- _shutter
- test_frost_protection.py
- TestAzimuthRowIsItsOwnCheck
- _read_manifest_version
- get_elevation_bounds
- Tests GitHub Workflow
- TestNextActionWithoutASchedule
- TestHysteresis
- TestTheExportExplainsAQuietWindow
- test_forum_2_15.py
- shade_release_opens
- get_position_for_role
- TestSwitchEntity
- schedule_times.py
- get_window_state
- render_all.mjs
- drive_delay.mjs
- copy_from.mjs
- sorting.mjs
- guard_slot.mjs
- Stub
- reorder.mjs
- resolve_shade_position
- cover_calls
- no_up_condition_blocks
- TestWebSocketToggle
- _local_timezone

## God Nodes (most connected - your core abstractions)
1. `async_build_export()` - 118 edges
2. `ShutterPilotPanel` - 116 edges
3. `sun_condition_keys()` - 96 edges
4. `CLAUDE.md – Fortschritts-Log (Archiv)` - 63 edges
5. `set_cover_position()` - 61 edges
6. `is_cover_sun_protected()` - 56 edges
7. `get_position_store()` - 52 edges
8. `setup_elevation_listener()` - 50 edges
9. `get_window_state()` - 47 edges
10. `evaluate_guard()` - 45 edges

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

## Communities (150 total, 12 thin omitted)

### Community 0 - "test_brightness_lux_hold.py"
Cohesion: 0.21
Nodes (15): _area(), clock(), drive(), _lux(), _positions(), fixture, Mindestdauer an der Lux-Schwelle im Helligkeitsmodus. bjoerg (community-…, Monotone Uhr von Hand: die Frist rechnet in Sekunden seit der ersten… (+7 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.05
Nodes (55): async_enforce_guard(), evaluate_guard(), _grace_seconds(), guard_status(), is_barred(), _lockout_seconds(), Any, Decide whether this awning may be out, and say why not. Writes the lockout… (+47 more)

### Community 2 - "cover_tracker.py"
Cohesion: 0.05
Nodes (54): async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant, Track cover positions and restore after Home Assistant restart., After HA start, restore persisted positions if cover integration restored wrong…, Listen to cover state changes and persist positions., setup_cover_position_tracker() (+46 more)

### Community 3 - "frost_condition_met"
Cohesion: 0.15
Nodes (12): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), Fail closed: wer nichts einstellt, merkt nichts., Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, Vor der Trennung der drei Polaritaeten (siehe _slot_reading() in helpers.py)…, Ein binary_sensor, dessen 'aus' Frost bedeutet - ohne die Invertierung liest…, Kein Default-Umdrehen fuer Booleans, auch nicht bei Frost: ein gewoehnlicher… (+4 more)

### Community 4 - "helpers.py"
Cohesion: 0.04
Nodes (108): Binary sensor entities exposing the sun protection state per area., automation_allowed(), condition_memory(), _cover_is_travelling(), device_kind(), find_shutter_by_cover(), get_cover_current_position(), get_sun_angles() (+100 more)

### Community 5 - "_area_window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "switch.py"
Cohesion: 0.07
Nodes (28): async_setup_entry(), _kind_label(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Auto-Mode and master switches for Shutter Pilot., The German word this switch is named after. (+20 more)

### Community 7 - "sensor.py"
Cohesion: 0.09
Nodes (20): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Sensor entities exposing the next scheduled movement per area., Today's forecast high, ready to use as a shading condition. (+12 more)

### Community 8 - "test_raffstore_storm_and_lock.py"
Cohesion: 0.14
Nodes (17): _blind(), calls(), _morning_tick(), _positions(), fixture, Wind protection for venetian blinds and a lock entity (simon42 #193, #196,…, Die Markisen-Windeinstellung gehoert den Markisen., Fail open wie der Rollladenschalter. (+9 more)

### Community 9 - "cover_verify.py"
Cohesion: 0.08
Nodes (34): cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant, Check that a cover actually reached the requested position. Radio-driven… (+26 more)

### Community 10 - "test_forum_2_18.py"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "ShutterPilotNextActionSensor"
Cohesion: 0.21
Nodes (4): callback, datetime, Timestamp of the next scheduled up/down movement for one area., ShutterPilotNextActionSensor

### Community 12 - "test_ventilation.py"
Cohesion: 0.11
Nodes (27): True when every configured ventilation condition holds. All conditions are…, vent_conditions_met(), _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore() (+19 more)

### Community 13 - "TestExportReadsTheWayTheReportWasMeant"
Cohesion: 0.12
Nodes (9): deepcopy_options(), Eine Frage zu stellen darf die Antwort nicht verändern., Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus., Was MartyBrs Export offenliess, obwohl alles darin stand., Fünfstellige Lux-Schwellen an einem Sensor in W/m². Nebeneinander sehen 559,7…, Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung., „Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen., TestExport (+1 more)

### Community 14 - "_setup"
Cohesion: 0.15
Nodes (12): charly166 und Linos: nicht beschatten, was noch gar nicht offen ist., Das bisherige Verhalten – und genau das, was gemeldet wurde., bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest., Das alte Verhalten: Merker faellt, gefahren wird nicht., MartyBr: die Beschattung je Bereich abschalten, ohne die Automatik., Der Punkt der ganzen Uebung: die Rollladen kommen wieder hoch. Stehenlassen…, Die zwei Schalter sind getrennt – das war der ganze Wunsch., _setup() (+4 more)

### Community 15 - "get_weather_data"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "note_manual_position"
Cohesion: 0.06
Nodes (49): manual_position_is_a_close(), note_manual_position(), True if a hand-driven position is simply "closed", not an override. The manual…, Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, _area(), clock(), drive(), _drives() (+41 more)

### Community 17 - "Window Contact Debounce (Xerenas)"
Cohesion: 0.11
Nodes (28): cover_calls(), _gated_sleep(), _positions(), fixture, parametrize, Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum. Beim…, Fensterzustand melden und alles zu Ende laufen lassen., Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.… (+20 more)

### Community 18 - "elevation.py"
Cohesion: 0.05
Nodes (59): async_retract_awning(), async_retract_storm(), clamp_to_rest(), describe_reasons(), extends_upward(), ConfigEntry, HomeAssistant, Wind, rain and ice protection for awnings and roof windows. The one part of… (+51 more)

### Community 21 - "test_awning_dusk.py"
Cohesion: 0.08
Nodes (35): is_dusk_retracted(), Any, True while dusk retract alone is holding this awning in. Read by elevation.py…, awning_dusk_condition_met(), True when this awning's own "get dark, retract" condition holds. Lives on the…, _area(), _awning(), cover_calls() (+27 more)

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

### Community 26 - "is_cover_sun_protected"
Cohesion: 0.14
Nodes (24): is_cover_sun_protected(), True if shading currently holds this specific cover., _area(), _positions(), Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-…, Fällt die Bedingung des *Runter*-Bereichs weg, wird freigegeben. (+16 more)

### Community 27 - "ShutterPilotAwningGuardSensor"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "test_resume_automation.py"
Cohesion: 0.08
Nodes (29): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+21 more)

### Community 29 - "TestSecondWindowContact"
Cohesion: 0.27
Nodes (4): Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact

### Community 30 - "test_forum_2_21_3.py"
Cohesion: 0.14
Nodes (23): cover_calls(), _gated_sleep(), _moving(), _positions(), fixture, c.radis Fall: der Rollladen parkt auf 74 %, einer Zahl, die nirgends steht.…, Der Rollladen ist unterwegs – die gemeldete Position ist eine Momentaufnahme., Fenster wird angefasst, waehrend der Abendlauf noch faehrt. (+15 more)

### Community 32 - "_status"
Cohesion: 0.14
Nodes (16): _berlin_offset(), _options(), date, Tests for the area_triggers block in the get_status WebSocket payload. Xerenas…, The reported case: 07:30 must be sent, not the 06:07 sunrise., The panel falls back to its own display – but must get everything else., bjoerg und charly166: die Markisen-Einstellungen standen wieder leer da.…, GitHub #9: Entität im Formular gewählt, Speichern gedrückt, Feld wieder leer.… (+8 more)

### Community 33 - "shutter-pilot-panel.js"
Cohesion: 0.08
Nodes (21): AWNING_GUARD_SLOTS, AWNING_UNUSED_KEYS, BOOL_COND_DOMAINS, COMPASS_PRESETS, COND_DOMAINS, COND_SLOTS, HINTS, I18N (+13 more)

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

### Community 38 - "._renderShutterForm"
Cohesion: 0.16
Nodes (3): isAwning(), isWindow(), kindOf()

### Community 39 - "is_weekend_schedule"
Cohesion: 0.13
Nodes (15): get_random_offset(), get_time_mode_triggers(), is_weekend_schedule(), date, Return (up, down) times for a time-mode area, jitter included., True if the weekend schedule applies. When a workday sensor is configured it…, Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area() (+7 more)

### Community 40 - "ConfigEntry"
Cohesion: 0.14
Nodes (13): cancel_all(), Drop every pending check, used when unloading the entry., _apply_shutter_automation_state(), async_migrate_entry(), async_unload_entry(), _drop_registry_entries(), ConfigEntry, Migrate an old config entry. Only version 1 exists so far. (+5 more)

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "test_tilt_hand_detect.py"
Cohesion: 0.23
Nodes (22): _blind(), fixture, Handverstellung nur der Lamellen (Raffstore, Stufe 4, simon42 #172 Claus). Der…, Die Hoehe steht seit Ewigkeit still - nur der Winkel aendert sich., Bestandsschutz: ohne Haken bleibt der Tracker fuer Winkel blind., Nach einer Hoehenfahrt melden manche Aktoren kurz falsche Winkel., Die Hoehe hat niemand angefasst - ihr Ziel bleibt gueltig., Claus #225: MDT JAL-0810M "Lamellen nach Fahrtende 0 %". Nach jeder… (+14 more)

### Community 43 - "sun_protect_conditions_met"
Cohesion: 0.17
Nodes (12): azimuth_in_sun_protect_range(), True when the sun stands in front of this area's windows. Ranges may wrap…, True when both elevation and compass direction call for shading., sun_protect_conditions_met(), _area(), parametrize, Tests for elevation + azimuth based sun protection., The bug azimuth support fixes: 0–15° elevation is hit twice a day. (+4 more)

### Community 44 - ".test_scheduler_skips_disabled_shutter"
Cohesion: 0.40
Nodes (4): _positions(), Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt., TestDrivePaths

### Community 45 - "manifest.json"
Cohesion: 0.10
Nodes (20): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+12 more)

### Community 46 - "test_area_mode_none.py"
Cohesion: 0.15
Nodes (15): cover_calls(), _fast_startup_restore(), fixture, malleYay: Shutter Pilot nur fuer den Sonnenschutz. „Gibt es eine Moeglichkeit,…, Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein Reload…, Gegenprobe: dieselben Zeiten, nur mit Modus., Der Punkt der ganzen Uebung., Ohne Zeitplan holt niemand den Rollladen von der halben Hoehe. Im Zeitmodus… (+7 more)

### Community 47 - "test_min_drive_gap.py"
Cohesion: 0.15
Nodes (14): _drive_all(), drive_log(), _entry(), fixture, MockConfigEntry, parametrize, Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos). Bei Funk (433…, Nach einer Pause muss die nächste Fahrt sofort raus. (+6 more)

### Community 48 - ".async_load"
Cohesion: 0.11
Nodes (12): Any, callback, Update one cover and persist., Records as they were on disk when the store was first loaded., Return stored record if loaded., Return stored position without async load (after async_load was called)., Load all cover records from disk., Persist current in-memory covers to disk. (+4 more)

### Community 50 - "test_reorder_shutters.py"
Cohesion: 0.14
Nodes (14): The stored list in the requested order. Covers named in `order` come first, in…, _reordered_shutters(), _Connection, _covers(), entry(), fixture, Die Reihenfolge der Rollllaeden im Bereich festlegen (DerTomm, GitHub #17). Die…, Ein Neuladen setzt die Merker zurueck - ohne Grund nicht. (+6 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "test_keep_position_and_tilt.py"
Cohesion: 0.17
Nodes (14): _blind(), calls(), _positions(), fixture, Hoehe und Lamellen getrennt (simon42 #172, #196, Claus). Ein Raffstore, der den…, _setup(), TestGroupServiceAndWaitingDrive, TestScheduleHonoursIt (+6 more)

### Community 54 - "ShutterPilotOptionsFlow"
Cohesion: 0.10
Nodes (19): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+11 more)

### Community 55 - "i18n_parity.mjs"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "set_cover_position"
Cohesion: 0.09
Nodes (25): Set cover position (and optionally slat angle) and persist the result. Returns…, set_cover_position(), _current_tilt(), _end_positions(), _interval_days(), _monthday(), Any, ConfigEntry (+17 more)

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

### Community 62 - "CLAUDE.md – Fortschritts-Log (Archiv)"
Cohesion: 0.03
Nodes (63): 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf, 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck), 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos), 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas), 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum, 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues, 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet, 2026-08-07 – 2.7.1: die drei Restpunkte (+55 more)

### Community 63 - "test_duplicate_cover.py"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "test_panel.py"
Cohesion: 0.08
Nodes (29): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, Eine 0 bei den Sonnengrenzen ist eine Grenze, nur leer ist keine (Linos). Ohne…, Windschutz fuer Raffstores und Sperr-Entitaet (2.25.0)., `window_react` und `drive_after_close_up` (Raffstore, Florian/Claus). Das…, Hoehe/Lamellen "unveraendert" und der Winkel nach der Hoehe (2.26.0). (+21 more)

### Community 65 - "test_export_notes.py"
Cohesion: 0.13
Nodes (10): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos., malleYays Modus im Bericht. Ein Bereich, der nichts faehrt, sieht Einstellung…, Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie. (+2 more)

### Community 66 - "_shutter"
Cohesion: 0.18
Nodes (9): Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen…, Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.…, Bestandsanlagen kennen den Schlüssel nicht – die müssen weiterlaufen., Der Schalter ist die lebende Wahrheit, der gespeicherte Wert der Start., Der eigene Schalter des Rollladens hat den Laufzeitwert schon gesetzt., Fail open: Ein toter Schalter darf keinen Rollladen stilllegen., Umgelegter Schalter wirkt sofort, ohne Reload des Config-Entry., _shutter() (+1 more)

### Community 67 - "test_window_trigger_stale_restore.py"
Cohesion: 0.25
Nodes (9): cover_calls(), _fast_startup(), _positions(), fixture, Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine veraltete…, Fahrten mitschreiben und die Position tatsaechlich im State nachziehen., _setup(), _shutter() (+1 more)

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 69 - "test_privacy.py"
Cohesion: 0.19
Nodes (13): _area(), calls(), _fast(), _morning(), _positions(), fixture, Sichtschutz (Raffstore, Stufe 6, simon42 #172 Claus). Eine Entitaet…, Die Abendfahrt hat ihn waehrenddessen zugefahren. (+5 more)

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

### Community 74 - "const.py"
Cohesion: 0.04
Nodes (64): Constants for Shutter Pilot integration., Diagnostics support for Shutter Pilot., Note a drive that waits for the window, in memory and on disk. The shutter…, Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), get_position_store(), HomeAssistant (+56 more)

### Community 75 - "._area"
Cohesion: 0.16
Nodes (10): elevation_in_sun_protect_range(), True when sun elevation is within the configured protection window. Switched…, Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch. (+2 more)

### Community 76 - "_setup_drive"
Cohesion: 0.16
Nodes (13): _positions(), Gegenprobe: derselbe Aufbau, nur der Haken fehlt., Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand diesen…, Binaer geschaltet heisst sofort, nicht bei der naechsten Freigabe., Der Aussperrschutz galt an jedem Fahrweg – nur hier nicht., Die Verdrahtung, nicht nur die Funktion. Der Merker ist nur dann etwas wert,…, Genau c.radis Fall: von Hand hochgezogen, abends faehrt wieder was., _setup_drive() (+5 more)

### Community 77 - "export.py"
Cohesion: 0.08
Nodes (48): _ages(), _condition_rows(), _deferred_close_note(), _drive_command_note(), _drive_verdict(), _dusk_row(), _fmt(), _fmt_labelled() (+40 more)

### Community 78 - "resolve_sun_geometry"
Cohesion: 0.33
Nodes (5): get_azimuth_bounds(), Merge area and shutter shading geometry into one config dict. A room can have…, Return (min, max) azimuth for the windows of this area, in degrees., resolve_sun_geometry(), TestResolveSunGeometry

### Community 79 - "season_allows_shading"
Cohesion: 0.33
Nodes (5): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, October to March must wrap, like the azimuth range does., TestSeason

### Community 80 - "set_cover_sun_protected"
Cohesion: 0.16
Nodes (13): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist… (+5 more)

### Community 81 - "test_door_lock_raffstore.py"
Cohesion: 0.17
Nodes (15): calls(), _morning_tick(), _positions(), fixture, _raffstore(), Tuer als reiner Aussperrschutz (Raffstore, simon42 #191 Florian, #196 Claus).…, Der Scheduler um 07:00 des naechsten Tages (vermeidet das Vormarkieren beim…, Bestandsschutz: ohne den neuen Haken faehrt die Hochfahrt wie bisher. (+7 more)

### Community 82 - "._setup"
Cohesion: 0.30
Nodes (5): hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es leider…, Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py, nur an der…, Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal zu. Die…, TestGuardBeatsShadingForAWindow, TestOpeningAndClosingByConditions

### Community 83 - "_condition_slot_met"
Cohesion: 0.25
Nodes (6): _condition_slot_met(), Evaluate one extra shading condition. Unreadable never blocks shading., MartyBr trug beim Azimut 40 / 130 ein und meinte den Bereich 40°–130°., TestHysteresisTheWrongWayRound, Die bestehenden Bedingungen dürfen sich nicht verändert haben., TestNormalDirectionUnchanged

### Community 84 - "Shutter Pilot Sidebar Panel"
Cohesion: 0.20
Nodes (11): Admin-Rechteprüfung (require_admin), Entitätsauswahl (Suchfeld statt lange Liste), HACS Default Store PR hacs/default#9592, i18n: 11 Sprachen im Panel, Mac Catalyst native Picker Absturz, Shutter Pilot Sidebar Panel, Shutter Pilot info.md (HACS store text), FUNDING.yml Sponsor Button (+3 more)

### Community 85 - "Sonnenschutz / Beschattung"
Cohesion: 0.20
Nodes (11): Fahrtkontrolle (cover_verify), Mindestabstand zwischen Fahrbefehlen, An der Beschattung teilnehmen (shading_enabled), Beschattungs-Zeitfenster (shade_from/shade_to), Beschattungszeitraum (Monate), Sonnenschutz / Beschattung, Wetter & Vorhersage (weather_data.py Konzept), FORUM_POST.md Draft Posts (+3 more)

### Community 87 - "test_lock_replay_restore.py"
Cohesion: 0.28
Nodes (16): _blind(), calls(), _door_cycle_under_lock(), fixture, Rueckfahrt nach der Tuer, wenn die Sperre sie zurueckgehalten hat. Claus…, Tuer auf (faehrt hoch), Aktor sperrt sich, Tuer zu - die Sperre steht noch., Wer die Sperre als Handsperre nutzt, schaltet das Nachholen ab., Bestandsschutz: eine Sperre allein fuehrt zu keiner Fahrt. (+8 more)

### Community 88 - "test_shared_automation_switch.py"
Cohesion: 0.20
Nodes (10): _own_automation_switch(), The automation switch that belongs to this cover, or "". Looked up in the…, _Connection, _keys(), Rollladen und Dachfenster teilten sich einen Automatik-Schalter (Fatmax,…, _run(), _setup(), TestTheStoredKeyHeals (+2 more)

### Community 89 - "test_elevation_log_disabled.py"
Cohesion: 0.31
Nodes (7): cover_calls(), _fast_startup(), fixture, Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich, wenn…, _setup(), TestElevationLogReflectsWhetherItDecided, _tick_elevation()

### Community 90 - "test_services_forget_window_cycle.py"
Cohesion: 0.23
Nodes (13): cover_calls(), _night_cycle(), fixture, parametrize, Die Dienste verwerfen die Rueckfahrhoehe des Fenstertriggers (StephanD77,…, Kontrolle: stop_group faehrt keine Position, es ist keine neue Entscheidung…, Rollladen zu, Fenster geht auf: der Trigger merkt sich die Hoehe., _service() (+5 more)

### Community 91 - "async_build_export"
Cohesion: 0.08
Nodes (17): async_build_export(), Build the export as markdown plus the raw options behind it., Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, Der Daemmerungs-Verdikt einer Markise - bjoergs Wunsch aus dem Forum (abends…, bjoerg hatte `switch.shutter_pilot_auto_balkon` als Windsensor. Der steht… (+9 more)

### Community 92 - "brightness.py"
Cohesion: 0.10
Nodes (27): ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener(), ConfigEntry, HomeAssistant, Helper functions for area-based follow-up actions (e.g. lights)., Execute configured light/switch action for an area and direction. direction:… (+19 more)

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "test_manual_move_clears_pending_drive.py"
Cohesion: 0.29
Nodes (8): cover_calls(), _fast_startup(), _positions(), fixture, Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine spaetere…, _setup(), _shutter(), TestStalePendingDriveAfterManualMove

### Community 95 - "has_frost_close_position"
Cohesion: 0.25
Nodes (5): has_frost_close_position(), True if this shutter defines a frost-protection closing position., parametrize, 0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert., TestPosition

### Community 96 - "test_geometry_and_season.py"
Cohesion: 0.13
Nodes (9): close_condition_met(), True when the area's conditions for a partial evening close apply. Same…, Tests for per-shutter shading geometry, season window and partial close. Forum…, Unlike shading conditions, an unset close condition means "no"., Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Bestandsanlagen haben nur die erste – die muss unverändert wirken., Fail closed: ein toter Sensor darf nicht alles halb offen lassen., TestAlternativeClosePosition (+1 more)

### Community 97 - "sun_condition_keys"
Cohesion: 0.10
Nodes (15): Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), entry(), fixture, bjoerg: „Mein Regensensor liefert nur nass und trocken". In…, Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., TestGuardSensorWithoutNumbers, Der Vertrag aus 2.8.0, jetzt eine Ebene hoeher. `_memory_copy()` schuetzt die… (+7 more)

### Community 98 - "Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)"
Cohesion: 0.17
Nodes (11): #11 (offen lassen, Zwischenstand), #13 (schließen), #14 (offen lassen), #15 (offen lassen, Rückfragen), #16 (offen lassen), #17 (schließen), #18 (schließen), #19 (schließen, Englisch) (+3 more)

### Community 99 - "set_sun_protect_active"
Cohesion: 0.36
Nodes (5): Update runtime sun protection state for dashboard and skip logic., set_sun_protect_active(), Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 100 - "TestDriveCommandNote"
Cohesion: 0.39
Nodes (3): Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote

### Community 101 - "conftest.py"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "Gesamtplan Raffstores"
Cohesion: 0.09
Nodes (21): 2a – Raffstore-Sturm, 2b – Sperr-Entität (Claus), Außerhalb der Raffstores (Claus #172), Befund im Code, Bestandsschutz, Bestandsschutz, Entwurf Stufe 2 — umgesetzt in 2.25.0 (lokal) (2026-10-24, nach Antworten #200 Florian und #202 Claus), Entwurf Stufe 4 – Handbedienung nur an den Lamellen (2026-11-01, noch nichts gebaut) (+13 more)

### Community 103 - "manual_override_still_blocks"
Cohesion: 0.20
Nodes (10): manual_override_still_blocks(), True if a manual position should keep blocking automated opening. The behaviour…, _FakeStore, _iso(), Tests for the configurable manual-override expiry., Minimal stand-in exposing only get_record()., Fail safe: without a timestamp we do not silently override the user., TestDaily (+2 more)

### Community 104 - "TestPerShutterOverride"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 105 - "test_sun_conditions.py"
Cohesion: 0.29
Nodes (5): data(), fixture, Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, Extra conditions gate shading; they never widen the sun window., TestGeometryStillApplies

### Community 106 - "Sondertage-Sensor (Workday-Sensor)"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 107 - "_rearm_scheduler"
Cohesion: 0.32
Nodes (5): Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, Die Sperre wirkt im Scheduler – und nur nach oben., Sonst stuende das Haus unter der Ferien-Kennung den Abend offen., _rearm_scheduler(), TestUpIsBlocked

### Community 108 - "_ws_delete_shutter"
Cohesion: 0.11
Nodes (22): _area_registry_uids(), Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns., Delete an area by id., Delete a shutter by index., _shutter_registry_uids(), _ws_delete_area(), _ws_delete_shutter() (+14 more)

### Community 109 - "test_reference_run.py"
Cohesion: 0.16
Nodes (29): calls(), _fast(), _old(), _positions(), fixture, Referenzfahrt (Raffstore, Stufe 7, simon42 #172 Claus). In festem Abstand…, Hintergrund-Aufgaben werden von async_block_till_done nicht abgewartet., Kein Lauf in der ersten Nacht nach dem Einschalten. (+21 more)

### Community 110 - "TestHelperConditionInTheReport"
Cohesion: 0.33
Nodes (3): Ein an/aus-Helfer hat keine Schwellen – und das muss dastehen. Sonst zeigt die…, Slots a-d haben keine Vorgabe-Invertierung, sind aber seit 2.21.5 per Checkbox…, TestHelperConditionInTheReport

### Community 111 - "_slot_reading"
Cohesion: 0.24
Nodes (8): Read one condition slot's raw comparison, or None if it cannot be judged. None…, _slot_reading(), _area(), Die drei Polaritäten der Bedingungs-Slots, an einer Stelle geprüft.…, Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False., Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None mehr, das…, TestJudgeableReturnsBool, TestUnjudgeableReturnsNone

### Community 114 - "test_my_position_blind_drive.py"
Cohesion: 0.27
Nodes (10): calls(), _drive(), fixture, My-Position bei einem Antrieb ohne Rueckmeldung, der trotzdem Positionen kann…, Bestandsschutz: ein Antrieb mit Rueckmeldung bleibt bei der Zahl., test_a_target_far_from_my_is_driven_by_position(), test_a_target_within_the_tolerance_still_presses_it(), test_the_shade_button_is_pressed_for_a_blind_drive() (+2 more)

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "clamp_to_bounds"
Cohesion: 0.42
Nodes (4): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, datetime, TestClampHelper

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "test_window_trigger_shaded_manual_reopen.py"
Cohesion: 0.23
Nodes (10): cover_calls(), _fast_startup(), _positions(), fixture, Ein Beschattungs-Merker (shaded=True) ueberlebt eine manuelle Fahrt.…, Rollladen ist von Hand voll offen (100%), der Beschattungs-Merker aus der…, Gegenprobe zum Fix: steht der Rollladen tatsaechlich noch an seiner…, _setup() (+2 more)

### Community 120 - "__init__.py"
Cohesion: 0.13
Nodes (43): ActiveConnection, async_response, _async_register_panel(), _async_register_websocket(), async_setup(), _find_entry_data(), callback, HomeAssistant (+35 more)

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "_shutter"
Cohesion: 0.17
Nodes (8): parametrize, Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist., „tilted" ist kein Synonym von on/off und darf keins werden., `cover.buro`: beschattet auf 80 %, Kontakt „open" an einem binary_sensor. Beide…, heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`., _shutter(), TestBinarySensorOpenSynonyms, TestHeinziesSetup

### Community 123 - "test_frost_protection.py"
Cohesion: 0.20
Nodes (12): Pick how far this shutter closes: fully, partially, or frost-safe. Shared by…, resolve_close_role(), _frost_area(), Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten., Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet., Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen., Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten. (+4 more)

### Community 126 - "get_elevation_bounds"
Cohesion: 0.27
Nodes (5): get_elevation_bounds(), Return (min, max) elevation for sun protection range., Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, TestElevationBounds

### Community 128 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 129 - "TestHysteresis"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

### Community 131 - "test_forum_2_15.py"
Cohesion: 0.17
Nodes (12): automated_up_blocked(), datetime, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, weekend_blocks_up(), cover_calls(), _fast_startup_restore(), fixture (+4 more)

### Community 132 - "shade_release_opens"
Cohesion: 0.38
Nodes (4): True if the end of the shading day should drive the cover open. Without a…, shade_release_opens(), Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest., TestShadeReleaseIsImplied

### Community 134 - "get_position_for_role"
Cohesion: 0.05
Nodes (45): ConfigEntry, HomeAssistant, Dusk retract for awnings: drive in once, never back out on its own. Asked for…, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), filter_shutters_by_area(), get_position_for_role(), is_auto_enabled() (+37 more)

### Community 135 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 136 - "schedule_times.py"
Cohesion: 0.11
Nodes (29): _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times(), parse_time() (+21 more)

### Community 138 - "get_window_state"
Cohesion: 0.04
Nodes (58): get_tilt_for_role(), Return the slat angle for a role, or None when tilt is not used. None also…, _canonical_state(), _first_entity_id(), get_deferred_close_position(), get_effective_close_position(), get_position_for_window_state(), get_tilt_entity_id() (+50 more)

### Community 142 - "render_all.mjs"
Cohesion: 0.25
Nodes (7): areas, ok(), p, R(), settings, shutters, states

### Community 143 - "drive_delay.mjs"
Cohesion: 0.25
Nodes (4): areas, calls, p, waits

### Community 144 - "copy_from.mjs"
Cohesion: 0.29
Nodes (5): p, src, target, win, winSrc

### Community 145 - "sorting.mjs"
Cohesion: 0.29
Nodes (5): aw, d, names, p, rows

### Community 146 - "guard_slot.mjs"
Cohesion: 0.40
Nodes (4): h, p, render(), flat()

### Community 150 - "resolve_shade_position"
Cohesion: 0.11
Nodes (23): The shading position for this shutter right now, plus how it was picked. Three…, resolve_shade_position(), parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition, _area(), calls(), _fast() (+15 more)

### Community 151 - "cover_calls"
Cohesion: 0.67
Nodes (3): cover_calls(), _fast_startup_restore(), fixture

### Community 154 - "no_up_condition_blocks"
Cohesion: 0.36
Nodes (5): no_up_condition_blocks(), True while a configured condition forbids the automated opening. "Whatever my…, Linos: eine Bedingung, die das morgendliche Oeffnen blockiert., Die eine Richtung, in der ein Fehler nicht wehtun darf. Andersherum bliebe…, TestNoUpCondition

### Community 160 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 161 - "_local_timezone"
Cohesion: 0.67
Nodes (3): _local_timezone(), fixture, Run these tests in Berlin. The default test timezone is US/Pacific, but…

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **191 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+186 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1203 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `ShutterPilotPanel` to `shutter-pilot-panel.js`, `._entityField`, `._renderShutterForm`, `.t`, `._coverAction`, `._renderCondDetail`, `._load`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _191 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.05292929292929293 - nodes in this community are weakly interconnected._
- **Should `cover_tracker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05388471177944862 - nodes in this community are weakly interconnected._