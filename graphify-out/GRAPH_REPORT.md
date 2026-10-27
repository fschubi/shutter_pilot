# Graph Report - shutter_pilot  (2026-10-27)

## Corpus Check
- 124 files · ~247,934 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3271 nodes · 7458 edges · 153 communities (139 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b3ff8438`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_brightness_lux_hold.py
- evaluate_guard
- cover_tracker.py
- HomeAssistant
- brightness.py
- _area_window
- switch.py
- _ForecastSensorBase
- test_raffstore_storm_and_lock.py
- _entry
- test_forum_2_18.py
- test_window_parked_and_late_report.py
- test_ventilation.py
- get_effective_close_position
- is_cover_sun_protected
- get_weather_data
- test_hand_lift_new_episode.py
- Window Contact Debounce (Xerenas)
- Any
- ShutterPilotPanel
- harness.mjs
- test_awning_dusk.py
- _latest_deadline
- test_shade_hours.py
- get_sun_mode_triggers
- test_awning_shading.py
- test_sun_protect_areas.py
- binary_sensor.py
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
- test_manual_move_clears_window_cycle.py
- test_init.py
- clamp_to_rest
- get_elevation_bounds
- test_blind_drive.py
- manifest.json
- test_area_mode_none.py
- test_min_drive_gap.py
- ShutterPositionStore
- test_reorder_shutters.py
- ._coverAction
- Bereichs-Karte (Area Card)
- test_keep_position_and_tilt.py
- ShutterPilotOptionsFlow
- i18n_parity.mjs
- test_cover_no_position.py
- test_sensor_names.py
- CLAUDE.md Project Doc
- Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)
- test_minute_tick_order_independence.py
- get_position_store
- CLAUDE.md – Fortschritts-Log (Archiv)
- test_duplicate_cover.py
- test_panel.py
- test_export_notes.py
- is_shutter_automation_enabled
- frost_condition_met
- README.md
- make_entry
- Catch-up Drive Bookkeeping (heinzie)
- _condition_note
- test_services.py
- TestHelperEntities
- remember_drive_after_close
- sun_protect_conditions_met
- test_forum_2_17.py
- export.py
- resolve_sun_geometry
- test_geometry_and_season.py
- set_cover_sun_protected
- test_door_lock_raffstore.py
- ._setup
- get_window_state
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- test_frost_protection.py
- TestExportReadsTheWayTheReportWasMeant
- test_elevation_log_disabled.py
- test_services_forget_window_cycle.py
- .make_guard_entry
- test_window_trigger_stale_restore.py
- CHANGELOG.md
- test_manual_move_clears_pending_drive.py
- TestDriveCommandNote
- close_condition_met
- sun_condition_keys
- Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)
- window_helper.py
- test_lock_protection_tilt.py
- const.py
- Gesamtplan Raffstores
- manual_override_still_blocks
- TestPerShutterOverride
- test_sun_conditions.py
- Sondertage-Sensor (Workday-Sensor)
- async_build_export
- _Connection
- awning_guard.py
- helpers.py
- TestAzimuthRowIsItsOwnCheck
- note_manual_position
- guard_status
- test_my_position_blind_drive.py
- services.yaml Service Definitions
- manual_position_is_a_close
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- _hand_open
- no_up_condition_blocks
- Shutter Pilot Integration (Brand/Concept)
- TestNextActionWithoutASchedule
- resolve_shade_position
- TestTheExportExplainsAQuietWindow
- __init__.py
- TestSingleContactUnchanged
- Tests GitHub Workflow
- _condition_slot_met
- .test_dead_sensor_does_not_trigger
- _ws_delete_shutter
- automated_up_blocked
- shade_release_opens
- test_awning_excluded.py
- TestSwitchEntity
- schedule_times.py
- test_sun_bounds.py
- TestWebSocketToggle
- get_deferred_close_position
- TestParseTime
- cover_calls
- render_all.mjs
- drive_delay.mjs
- copy_from.mjs
- sorting.mjs
- guard_slot.mjs
- Stub
- reorder.mjs
- is_cover_ventilating
- TestRainProtection
- TestHysteresis
- _warn_useless_hysteresis

## God Nodes (most connected - your core abstractions)
1. `ShutterPilotPanel` - 116 edges
2. `async_build_export()` - 113 edges
3. `sun_condition_keys()` - 89 edges
4. `is_cover_sun_protected()` - 56 edges
5. `CLAUDE.md – Fortschritts-Log (Archiv)` - 56 edges
6. `set_cover_position()` - 53 edges
7. `get_position_store()` - 50 edges
8. `setup_elevation_listener()` - 49 edges
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

## Communities (153 total, 11 thin omitted)

### Community 0 - "test_brightness_lux_hold.py"
Cohesion: 0.21
Nodes (15): _area(), clock(), drive(), _lux(), _positions(), fixture, Mindestdauer an der Lux-Schwelle im Helligkeitsmodus. bjoerg (community-…, Monotone Uhr von Hand: die Frist rechnet in Sekunden seit der ersten… (+7 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.12
Nodes (23): evaluate_guard(), Decide whether this awning may be out, and say why not. Writes the lockout…, _awning(), _data(), Einfahren ab `on_above`, Freigabe erst unter `off_below`., 22 km/h liegt unter der Einfahr- und ueber der Freigabeschwelle. Ohne Hysterese…, Eine Boe ist nach zwanzig Sekunden vorbei. Die Markise trotzdem nicht., Eine Boenfront ist eine Reihe von Boen, keine einzelne. (+15 more)

### Community 2 - "cover_tracker.py"
Cohesion: 0.08
Nodes (35): async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant, Track cover positions and restore after Home Assistant restart., After HA start, restore persisted positions if cover integration restored wrong…, Listen to cover state changes and persist positions., setup_cover_position_tracker() (+27 more)

### Community 3 - "HomeAssistant"
Cohesion: 0.14
Nodes (38): ActiveConnection, async_response, _async_register_panel(), _async_register_websocket(), _find_entry_data(), callback, HomeAssistant, Register one shared per-minute timer for scheduler and sun protection. (+30 more)

### Community 4 - "brightness.py"
Cohesion: 0.10
Nodes (27): ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener(), ConfigEntry, HomeAssistant, Helper functions for area-based follow-up actions (e.g. lights)., Execute configured light/switch action for an area and direction. direction:… (+19 more)

### Community 5 - "_area_window"
Cohesion: 0.08
Nodes (36): _area_window(), datetime, HomeAssistant, True if `now` lies inside the allowed window. direction: 'up' or 'down'., True unless a sun-relative bound still blocks this direction. The clock windows…, _sun_bound_ok(), _area(), _at() (+28 more)

### Community 6 - "switch.py"
Cohesion: 0.07
Nodes (28): async_setup_entry(), _kind_label(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Auto-Mode and master switches for Shutter Pilot., The German word this switch is named after. (+20 more)

### Community 7 - "_ForecastSensorBase"
Cohesion: 0.07
Nodes (23): async_setup_entry(), _ForecastSensorBase, AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+15 more)

### Community 8 - "test_raffstore_storm_and_lock.py"
Cohesion: 0.14
Nodes (17): _blind(), calls(), _morning_tick(), _positions(), fixture, Wind protection for venetian blinds and a lock entity (simon42 #193, #196,…, Die Markisen-Windeinstellung gehoert den Markisen., Fail open wie der Rollladenschalter. (+9 more)

### Community 9 - "_entry"
Cohesion: 0.08
Nodes (32): cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant, Check that a cover actually reached the requested position. Radio-driven… (+24 more)

### Community 10 - "test_forum_2_18.py"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "test_window_parked_and_late_report.py"
Cohesion: 0.27
Nodes (11): calls(), _park(), fixture, bjoerg (community-smarthome.com/11378/166): zwei Fehler an der Abendfahrt bei…, Tagsueber offen, nichts vorgemerkt: das Fenster zieht ihn nicht herunter., _setup(), test_late_report_near_target_stays_automation(), test_open_cover_without_pending_drive_is_not_pulled_down() (+3 more)

### Community 12 - "test_ventilation.py"
Cohesion: 0.11
Nodes (27): True when every configured ventilation condition holds. All conditions are…, vent_conditions_met(), _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore() (+19 more)

### Community 13 - "get_effective_close_position"
Cohesion: 0.16
Nodes (9): get_effective_close_position(), Apply lock protection (Aussperrschutz): - If lock_protection and window…, parametrize, Tests for per-shutter positions, slats and lock protection., The group services used to hard-code 100/0 and ignore these values., _shutter(), TestLockProtection, TestRolePositions (+1 more)

### Community 14 - "is_cover_sun_protected"
Cohesion: 0.09
Nodes (25): is_cover_sun_protected(), True if shading currently holds this specific cover., cover_calls(), _fast_startup_restore(), fixture, Die Meldungen aus dem Forum vom August, gegen den echten Code gehalten. Vier…, Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, charly166 und Linos: nicht beschatten, was noch gar nicht offen ist. (+17 more)

### Community 15 - "get_weather_data"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "test_hand_lift_new_episode.py"
Cohesion: 0.16
Nodes (23): _area(), clock(), drive(), _drives(), _lux(), fixture, Ein von Hand geoeffneter Rollladen bleibt im Helligkeitsmodus abends offen.…, Spiegelbild: eine Handfahrt auf 0 % gilt laut manual_position_is_a_close()… (+15 more)

### Community 17 - "Window Contact Debounce (Xerenas)"
Cohesion: 0.11
Nodes (28): cover_calls(), _gated_sleep(), _positions(), fixture, parametrize, Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum. Beim…, Fensterzustand melden und alles zu Ende laufen lassen., Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.… (+20 more)

### Community 18 - "Any"
Cohesion: 0.05
Nodes (71): ConfigEntry, HomeAssistant, Dusk retract for awnings: drive in once, never back out on its own. Asked for…, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), describe_reasons(), One short line for the log and the export., ConfigEntry (+63 more)

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
Cohesion: 0.15
Nodes (18): get_sun_mode_triggers(), Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), parametrize, Midsummer: the sun is up at 05:10, the shutters wait until 07:30., Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it., Existing setups must not shift at all. (+10 more)

### Community 25 - "test_awning_shading.py"
Cohesion: 0.15
Nodes (21): awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore(), _positions(), fixture (+13 more)

### Community 26 - "test_sun_protect_areas.py"
Cohesion: 0.14
Nodes (22): _area(), _positions(), Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-…, Fällt die Bedingung des *Runter*-Bereichs weg, wird freigegeben., Der Bereichswert lief aus dem Tritt und blockierte Hochfahrten., Der einfache Fall muss sich unverändert verhalten. (+14 more)

### Community 27 - "binary_sensor.py"
Cohesion: 0.09
Nodes (20): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+12 more)

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
Cohesion: 0.11
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

### Community 40 - "test_manual_move_clears_window_cycle.py"
Cohesion: 0.20
Nodes (13): cover_calls(), _fast_startup(), _hours_pass(), _positions(), fixture, Der Rueckfahr-Merker des Fenstertriggers darf keine manuelle Fahrt ueberleben -…, Die Karenz der eigenen Fahrt (90 s) ist am Morgen laengst vorbei., Tag 1 aus c.radis Bericht - war schon richtig, bleibt es. (+5 more)

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "clamp_to_rest"
Cohesion: 0.15
Nodes (10): clamp_to_rest(), extends_upward(), The safe position for this kind – retracted, or shut., True when a higher cover position means "further out" for this device. Almost…, Cap a target so it never sits further out than the rest position. Deliberately…, rest_position(), Sonst verweigerte der Schutz genau die Fahrt, fuer die er da ist., TestClamp (+2 more)

### Community 43 - "get_elevation_bounds"
Cohesion: 0.14
Nodes (13): azimuth_in_sun_protect_range(), get_elevation_bounds(), Return (min, max) elevation for sun protection range., True when the sun stands in front of this area's windows. Ranges may wrap…, Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, _area(), parametrize (+5 more)

### Community 44 - "test_blind_drive.py"
Cohesion: 0.15
Nodes (11): _blind(), entry(), _normal(), fixture, Rollläden ohne Positionsrückmeldung (Wunsch von Viktor, ESP Somfy RTS).…, Der Antrieb meldet keine Position – nur `state`, kein current_position., Bisheriges Verhalten für alle anderen Rollläden., Vor der ersten Fahrt weiss auch die Buchführung nichts. (+3 more)

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
Cohesion: 0.13
Nodes (14): Any, callback, Update one cover and persist., Records as they were on disk when the store was first loaded., Return stored record if loaded., Return stored position without async load (after async_load was called)., JSON store for last known cover positions (per config entry)., Load all cover records from disk. (+6 more)

### Community 50 - "test_reorder_shutters.py"
Cohesion: 0.14
Nodes (14): The stored list in the requested order. Covers named in `order` come first, in…, _reordered_shutters(), _Connection, _covers(), entry(), fixture, Die Reihenfolge der Rollllaeden im Bereich festlegen (DerTomm, GitHub #17). Die…, Ein Neuladen setzt die Merker zurueck - ohne Grund nicht. (+6 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "test_keep_position_and_tilt.py"
Cohesion: 0.19
Nodes (13): _blind(), calls(), _positions(), fixture, Hoehe und Lamellen getrennt (simon42 #172, #196, Claus). Ein Raffstore, der den…, _setup(), TestGroupServiceAndWaitingDrive, TestScheduleHonoursIt (+5 more)

### Community 54 - "ShutterPilotOptionsFlow"
Cohesion: 0.10
Nodes (19): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+11 more)

### Community 55 - "i18n_parity.mjs"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "test_cover_no_position.py"
Cohesion: 0.12
Nodes (10): calls(), entry(), fixture, Antriebe, die keine Position kennen. Viele Markisenmotoren – und etliche…, Vier Markisen mal zehn Sekunden waeren eine halbe Minute im Sturm., Alle drei Dienste mitschreiben, damit sichtbar wird, welcher lief., Halb ausfahren kann der Antrieb nicht – stehenbleiben ist schlechter., Ohne lesbares Feature-Bit bleibt es beim bisherigen Verhalten. (+2 more)

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

### Community 61 - "get_position_store"
Cohesion: 0.12
Nodes (19): get_position_store(), HomeAssistant, Persistent cover position storage across Home Assistant restarts., Return or create the position store for a config entry., _storage_key(), parametrize, TestFlagParsing, entry() (+11 more)

### Community 62 - "CLAUDE.md – Fortschritts-Log (Archiv)"
Cohesion: 0.04
Nodes (56): 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf, 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck), 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos), 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas), 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum, 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues, 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet, 2026-08-07 – 2.7.1: die drei Restpunkte (+48 more)

### Community 63 - "test_duplicate_cover.py"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "test_panel.py"
Cohesion: 0.08
Nodes (29): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, Eine 0 bei den Sonnengrenzen ist eine Grenze, nur leer ist keine (Linos). Ohne…, Windschutz fuer Raffstores und Sperr-Entitaet (2.25.0)., `window_react` und `drive_after_close_up` (Raffstore, Florian/Claus). Das…, Hoehe/Lamellen "unveraendert" und der Winkel nach der Hoehe (2.26.0). (+21 more)

### Community 65 - "test_export_notes.py"
Cohesion: 0.12
Nodes (12): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), entry(), _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos. (+4 more)

### Community 66 - "is_shutter_automation_enabled"
Cohesion: 0.11
Nodes (18): is_shutter_automation_enabled(), True if automated driving is allowed for this single shutter. Third level below…, cover_calls(), _positions(), fixture, Automatik pro Rollladen – dritte Ebene unter Hauptschalter und Bereich. Der…, Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt. (+10 more)

### Community 67 - "frost_condition_met"
Cohesion: 0.16
Nodes (11): frost_condition_met(), True when the area's frost condition applies. Same evaluation as the shading…, _area(), Fail closed: wer nichts einstellt, merkt nichts., Vor der Trennung der drei Polaritaeten (siehe _slot_reading() in helpers.py)…, Ein binary_sensor, dessen 'aus' Frost bedeutet - ohne die Invertierung liest…, Kein Default-Umdrehen fuer Booleans, auch nicht bei Frost: ein gewoehnlicher…, Ohne Invertierung liesse sich "unter X" nicht ausdrücken. (+3 more)

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 69 - "make_entry"
Cohesion: 0.15
Nodes (12): async_enforce_guard(), Evaluate every awning and pull in the ones that must not be out., make_entry(), fixture, Der Merker gehoert an die Fahrt, nicht an die Absicht. Genau diese Verwechslung…, Sonst gilt die Markise weiter als beschattet und faehrt nie wieder., Bewusste Abweichung von der Rangfolge Haupt- > Bereichs- > Rollladenschalter.…, Entry plus Laufzeit-Dict, ohne die Integration zu starten. (+4 more)

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

### Community 74 - "remember_drive_after_close"
Cohesion: 0.24
Nodes (10): Note a drive that waits for the window, in memory and on disk. The shutter…, Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), _data(), Nachhol-Fahrten überstehen den Neustart. Stand die Schließzeit an, während das…, Eine Fahrt von vorgestern sagt nichts mehr darüber, was jetzt gilt., Nicht die Kopie von der Platte – die wäre inzwischen veraltet. (+2 more)

### Community 75 - "sun_protect_conditions_met"
Cohesion: 0.15
Nodes (9): True when both elevation and compass direction call for shading., sun_protect_conditions_met(), Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., TestElevationCanBeSwitchedOff, The bug azimuth support fixes: 0–15° elevation is hit twice a day. (+1 more)

### Community 76 - "test_forum_2_17.py"
Cohesion: 0.11
Nodes (21): cover_calls(), entry(), _fast_startup_restore(), _positions(), fixture, Die vier Forumsmeldungen zu 2.16.0, jede mit ihrem eigenen Beweis. Leichter…, Gegenprobe: derselbe Aufbau, nur der Haken fehlt., Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand diesen… (+13 more)

### Community 77 - "export.py"
Cohesion: 0.09
Nodes (46): Return the "compare downwards" option key for a slot., sun_condition_invert_key(), _condition_rows(), _deferred_close_note(), _drive_verdict(), _dusk_row(), _fmt(), _fmt_labelled() (+38 more)

### Community 78 - "resolve_sun_geometry"
Cohesion: 0.18
Nodes (10): elevation_in_sun_protect_range(), get_azimuth_bounds(), Merge area and shutter shading geometry into one config dict. A room can have…, True when sun elevation is within the configured protection window. Switched…, Return (min, max) azimuth for the windows of this area, in degrees., resolve_sun_geometry(), Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch. (+2 more)

### Community 79 - "test_geometry_and_season.py"
Cohesion: 0.20
Nodes (8): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, Tests for per-shutter shading geometry, season window and partial close. Forum…, October to March must wrap, like the azimuth range does., The case Linos described: one room, south and west windows., TestSeason, TestWindowsFacingDifferentWays

### Community 80 - "set_cover_sun_protected"
Cohesion: 0.06
Nodes (34): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover, cover_calls(), fixture, parametrize (+26 more)

### Community 81 - "test_door_lock_raffstore.py"
Cohesion: 0.17
Nodes (15): calls(), _morning_tick(), _positions(), fixture, _raffstore(), Tuer als reiner Aussperrschutz (Raffstore, simon42 #191 Florian, #196 Claus).…, Der Scheduler um 07:00 des naechsten Tages (vermeidet das Vormarkieren beim…, Bestandsschutz: ohne den neuen Haken faehrt die Hochfahrt wie bisher. (+7 more)

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
Cohesion: 0.22
Nodes (10): _frost_area(), Frostschutz – Anregung von Linos aus dem Forum. Bei erfüllter Bedingung soll…, Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten., Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet., Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen., Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten., _shutter(), _temp() (+2 more)

### Community 88 - "TestExportReadsTheWayTheReportWasMeant"
Cohesion: 0.12
Nodes (9): deepcopy_options(), Eine Frage zu stellen darf die Antwort nicht verändern., Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus., Was MartyBrs Export offenliess, obwohl alles darin stand., Fünfstellige Lux-Schwellen an einem Sensor in W/m². Nebeneinander sehen 559,7…, Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung., „Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen., TestExport (+1 more)

### Community 89 - "test_elevation_log_disabled.py"
Cohesion: 0.31
Nodes (7): cover_calls(), _fast_startup(), fixture, Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich, wenn…, _setup(), TestElevationLogReflectsWhetherItDecided, _tick_elevation()

### Community 90 - "test_services_forget_window_cycle.py"
Cohesion: 0.23
Nodes (13): cover_calls(), _night_cycle(), fixture, parametrize, Die Dienste verwerfen die Rueckfahrhoehe des Fenstertriggers (StephanD77,…, Kontrolle: stop_group faehrt keine Position, es ist keine neue Entscheidung…, Rollladen zu, Fenster geht auf: der Trigger merkt sich die Hoehe., _service() (+5 more)

### Community 91 - ".make_guard_entry"
Cohesion: 0.24
Nodes (4): `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, TestGuardTableRespectsInversion, TestRainAndIceUnitPlausibility

### Community 92 - "test_window_trigger_stale_restore.py"
Cohesion: 0.25
Nodes (9): cover_calls(), _fast_startup(), _positions(), fixture, Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine veraltete…, Fahrten mitschreiben und die Position tatsaechlich im State nachziehen., _setup(), _shutter() (+1 more)

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "test_manual_move_clears_pending_drive.py"
Cohesion: 0.29
Nodes (8): cover_calls(), _fast_startup(), _positions(), fixture, Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine spaetere…, _setup(), _shutter(), TestStalePendingDriveAfterManualMove

### Community 95 - "TestDriveCommandNote"
Cohesion: 0.39
Nodes (3): Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote

### Community 96 - "close_condition_met"
Cohesion: 0.15
Nodes (8): close_condition_met(), True when the area's conditions for a partial evening close apply. Same…, Unlike shading conditions, an unset close condition means "no"., Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Bestandsanlagen haben nur die erste – die muss unverändert wirken., Fail closed: ein toter Sensor darf nicht alles halb offen lassen., TestAlternativeClosePosition, TestSecondCloseCondition

### Community 97 - "sun_condition_keys"
Cohesion: 0.11
Nodes (17): Return (entity, on_above, off_below, states) option keys for a slot., sun_condition_keys(), Read one condition slot's raw comparison, or None if it cannot be judged. None…, _slot_reading(), _area(), Die drei Polaritäten der Bedingungs-Slots, an einer Stelle geprüft.…, Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False., Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None mehr, das… (+9 more)

### Community 98 - "Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)"
Cohesion: 0.17
Nodes (11): #11 (offen lassen, Zwischenstand), #13 (schließen), #14 (offen lassen), #15 (offen lassen, Rückfragen), #16 (offen lassen), #17 (schließen), #18 (schließen), #19 (schließen, Englisch) (+3 more)

### Community 99 - "window_helper.py"
Cohesion: 0.14
Nodes (20): _canonical_state(), _first_entity_id(), get_tilt_entity_id(), has_separate_tilt_entity(), has_tilt_state(), _normalize_state(), Any, Helper to check window state and apply lock protection (Aussperrschutz). (+12 more)

### Community 100 - "test_lock_protection_tilt.py"
Cohesion: 0.13
Nodes (14): get_position_for_window_state(), Target position for one window state, or None while the window is shut. A two-…, Der Aussperrschutz und das gekippte Fenster. bjoerg im Forum, nachdem er seinen…, Wolfs Fall aus 2.10.2 darf sich nicht aendern. Ein zweiwertiger Kontakt meldet…, bjoergs Aufbau: ein Griff mit open / tilted / closed., Wolfs Aufbau aus 2.10.2: zweiwertiger Kontakt, kein Kipp-Zustand., bjoergs Fall: 30 % muessen 30 % bleiben., Die Gegenrichtung – dafuer ist der Aussperrschutz da. (+6 more)

### Community 101 - "const.py"
Cohesion: 0.25
Nodes (7): Constants for Shutter Pilot integration., auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "Gesamtplan Raffstores"
Cohesion: 0.12
Nodes (16): 2a – Raffstore-Sturm, 2b – Sperr-Entität (Claus), Außerhalb der Raffstores (Claus #172), Bestandsschutz, Entwurf Stufe 2 — umgesetzt in 2.25.0 (lokal) (2026-10-24, nach Antworten #200 Florian und #202 Claus), Gesamtplan Raffstores, Leitplanken (gelten für jede Stufe), Offene Entscheidungen (+8 more)

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

### Community 107 - "async_build_export"
Cohesion: 0.05
Nodes (25): async_build_export(), _awning_silent_notes(), Build the export as markdown plus the raw options behind it., Shutter settings left on an awning, where they mean nothing. Same class as…, has_storm_guard(), True for a venetian blind that opted in to the wind protection. Not…, Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt. (+17 more)

### Community 108 - "_Connection"
Cohesion: 0.29
Nodes (3): _Connection, Nimmt entgegen, was der Befehl zurueckmeldet. `user` braucht es, weil beide…, _User

### Community 109 - "awning_guard.py"
Cohesion: 0.11
Nodes (24): async_retract_awning(), async_retract_storm(), _grace_seconds(), _lockout_seconds(), Any, ConfigEntry, HomeAssistant, Wind, rain and ice protection for awnings and roof windows. The one part of… (+16 more)

### Community 110 - "helpers.py"
Cohesion: 0.06
Nodes (68): apply_covers_driven_from_persisted(), automation_allowed(), clear_manual_override_for_covers(), _cover_is_travelling(), find_shutter_by_cover(), get_cover_current_position(), get_sun_condition_status(), get_tracked_position() (+60 more)

### Community 112 - "note_manual_position"
Cohesion: 0.25
Nodes (6): note_manual_position(), Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, Eine blockierte Richtung fror bisher die andere ein. `covers_driven_down` haelt…, Dazwischen ist weder "oben" noch "unten": der Oben-Merker bleibt wie er war,…, Neu zuweisen haenge den Scheduler an ein totes Set (2.10.0)., TestManualDriveIsBooked

### Community 113 - "guard_status"
Cohesion: 0.27
Nodes (6): guard_status(), is_barred(), Read the last decision without touching it. Deliberately does not evaluate:…, True while this awning must not extend., Wie `_memory_copy()` im Export: der Bericht darf nichts verschieben., TestReadOnlyStatus

### Community 114 - "test_my_position_blind_drive.py"
Cohesion: 0.27
Nodes (10): calls(), _drive(), fixture, My-Position bei einem Antrieb ohne Rueckmeldung, der trotzdem Positionen kann…, Bestandsschutz: ein Antrieb mit Rueckmeldung bleibt bei der Zahl., test_a_target_far_from_my_is_driven_by_position(), test_a_target_within_the_tolerance_still_presses_it(), test_the_shade_button_is_pressed_for_a_blind_drive() (+2 more)

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "manual_position_is_a_close"
Cohesion: 0.29
Nodes (5): manual_position_is_a_close(), True if a hand-driven position is simply "closed", not an override. The manual…, Wer abends von Hand schliesst, bekam nie wieder ein automatisches Auf. Der…, Bei einer Markise ist „zu" die groessere Zahl., TestManualCloseIsNoOverride

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "_hand_open"
Cohesion: 0.28
Nodes (6): _hand_open(), Was cover_tracker bei einer erkannten Fremdfahrt auf 100 % verbucht., Linos: Wandschalter nach der Abendfahrt, naechste Lux-Meldung., bjoerg: Ausreisser am Nachmittag, von Hand geoeffnet, echte Daemmerung spaeter…, Mit lux_hold: die Frist und die Episode sind derselbe Zaehler., TestHandOpenAfterTheEveningClose

### Community 120 - "no_up_condition_blocks"
Cohesion: 0.36
Nodes (5): no_up_condition_blocks(), True while a configured condition forbids the automated opening. "Whatever my…, Linos: eine Bedingung, die das morgendliche Oeffnen blockiert., Die eine Richtung, in der ein Fehler nicht wehtun darf. Andersherum bliebe…, TestNoUpCondition

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 123 - "resolve_shade_position"
Cohesion: 0.10
Nodes (19): condition_memory(), guard_slot_danger(), has_alt_shade_position(), _own_slot_met(), Hysteresis memory for one area, or for one cover inside it. Two windows of the…, True if this shutter defines a second shading position., True when the area's condition for the second shading position holds. Fail…, Pick which of the two shading positions this shutter uses. (+11 more)

### Community 125 - "__init__.py"
Cohesion: 0.11
Nodes (20): cancel_all(), Drop every pending check, used when unloading the entry., _apply_shutter_automation_state(), async_migrate_entry(), async_setup(), async_unload_entry(), _drop_registry_entries(), ConfigEntry (+12 more)

### Community 126 - "TestSingleContactUnchanged"
Cohesion: 0.38
Nodes (3): The existing single-contact behaviour must not shift at all., _shutter(), TestSingleContactUnchanged

### Community 128 - "_condition_slot_met"
Cohesion: 0.25
Nodes (6): _condition_slot_met(), Evaluate one extra shading condition. Unreadable never blocks shading., MartyBr trug beim Azimut 40 / 130 ein und meinte den Bereich 40°–130°., TestHysteresisTheWrongWayRound, Die bestehenden Bedingungen dürfen sich nicht verändert haben., TestNormalDirectionUnchanged

### Community 129 - ".test_dead_sensor_does_not_trigger"
Cohesion: 0.22
Nodes (4): parametrize, Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, 0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert., TestPosition

### Community 130 - "_ws_delete_shutter"
Cohesion: 0.15
Nodes (19): _area_registry_uids(), Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns., Delete an area by id., Delete a shutter by index., _shutter_registry_uids(), _ws_delete_area(), _ws_delete_shutter() (+11 more)

### Community 131 - "automated_up_blocked"
Cohesion: 0.23
Nodes (8): automated_up_blocked(), datetime, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, weekend_blocks_up(), c.radi, Linos, hollsten: am Wochenende gar nicht hochfahren., hollstens Fall: samstags arbeiten, sonntags ausschlafen. Der Sondertage-Sensor…, TestWeekendBlocksUp

### Community 132 - "shade_release_opens"
Cohesion: 0.38
Nodes (4): True if the end of the shading day should drive the cover open. Without a…, shade_release_opens(), Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest., TestShadeReleaseIsImplied

### Community 134 - "test_awning_excluded.py"
Cohesion: 0.08
Nodes (24): filter_shutters_by_area(), only_shutters(), Filter shutters by area_up_id or area_down_id. Every kind is in by default…, Keep just the shutters from a list of covers about to be driven. Filtering here…, _awning(), cover_calls(), _fast_startup_restore(), fixture (+16 more)

### Community 135 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 136 - "schedule_times.py"
Cohesion: 0.12
Nodes (28): Diagnostics support for Shutter Pilot., _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times() (+20 more)

### Community 137 - "test_sun_bounds.py"
Cohesion: 0.19
Nodes (11): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, _local_timezone(), datetime, fixture, Tests for the earliest/latest clock bounds in sun mode. MartyBr's case from the…, The exact setup described in the forum., Run these tests in Berlin. The default test timezone is US/Pacific, but… (+3 more)

### Community 138 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 139 - "get_deferred_close_position"
Cohesion: 0.50
Nodes (5): get_deferred_close_position(), get_ventilation_position(), HomeAssistant, Where this shutter belongs while its window stands open, lock cap applied.…, How far a deferred close may already go, or None to keep waiting. "Fahrt nach…

### Community 141 - "cover_calls"
Cohesion: 0.67
Nodes (3): cover_calls(), _fast_startup_restore(), fixture

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

### Community 149 - "is_cover_ventilating"
Cohesion: 0.67
Nodes (3): is_cover_ventilating(), Any, True while automatic ventilation holds this cover.

### Community 150 - "TestRainProtection"
Cohesion: 0.33
Nodes (3): Kein Wert = Gefahr. Am Fenster ist das die richtige Richtung., Ecowitt liefert mm/h – Zahl mit Hysterese statt an/aus., TestRainProtection

### Community 151 - "TestHysteresis"
Cohesion: 0.33
Nodes (3): A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., TestHysteresis

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **180 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1144 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `ShutterPilotPanel` to `shutter-pilot-panel.js`, `._entityField`, `._renderShutterForm`, `.t`, `._coverAction`, `._renderCondDetail`, `._load`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _180 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.11818181818181818 - nodes in this community are weakly interconnected._
- **Should `cover_tracker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07777777777777778 - nodes in this community are weakly interconnected._