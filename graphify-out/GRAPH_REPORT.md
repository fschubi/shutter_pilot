# Graph Report - shutter_pilot  (2026-11-22)

## Corpus Check
- 145 files · ~291,092 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3770 nodes · 8934 edges · 156 communities (143 shown, 10 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `af9fb0b8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_brightness_lux_hold.py
- evaluate_guard
- elevation.py
- TestRolePositions
- window_trigger.py
- _area_window
- switch.py
- sensor.py
- test_raffstore_storm_and_lock.py
- cover_verify.py
- test_forum_2_18.py
- manifest.json
- test_ventilation.py
- awning_guard.py
- is_cover_sun_protected
- get_weather_data
- test_hand_lift_new_episode.py
- _positions
- test_awning_excluded.py
- ShutterPilotPanel
- harness.mjs
- test_awning_dusk.py
- _latest_deadline
- test_shade_hours.py
- get_sun_mode_triggers
- test_awning_shading.py
- test_sun_protect_areas.py
- ShutterPilotAwningGuardSensor
- test_resume_automation.py
- helpers.py
- test_forum_2_21_3.py
- TestWithoutFeedback
- _status
- shutter-pilot-panel.js
- resolve_shading_config
- sun_extra_conditions_met
- ._note
- test_forum_findings.py
- ._renderShutterForm
- is_weekend_schedule
- .make_guard_entry
- test_init.py
- test_tilt_hand_detect.py
- sun_protect_conditions_met
- test_export_notes.py
- test_area_mode_none.py
- test_min_drive_gap.py
- test_reorder_shutters.py
- remember_drive_after_close
- Bereichs-Karte (Area Card)
- test_keep_position_and_tilt.py
- _setup
- i18n_parity.mjs
- set_cover_position
- test_sensor_names.py
- CLAUDE.md Project Doc
- Shutter List Table (Name, Cover-Entity, Bereich Hoch/Runter, Fenster)
- test_minute_tick_order_independence.py
- test_forum_2_17.py
- CLAUDE.md – Fortschritts-Log (Archiv)
- test_duplicate_cover.py
- test_panel.py
- _silent_setting_notes
- _shutter
- test_window_trigger_stale_restore.py
- README.md
- _setup
- Catch-up Drive Bookkeeping (heinzie)
- _area
- test_services.py
- TestHelperEntities
- test_forum_2_15.py
- resolve_sun_geometry
- manual_position_is_a_close
- Any
- test_frost_lock.py
- async_build_export
- set_cover_sun_protected
- _raffstore
- ._setup
- __init__.py
- Shutter Pilot Sidebar Panel
- Sonnenschutz / Beschattung
- ._renderCondDetail
- test_lock_replay_restore.py
- test_shared_automation_switch.py
- test_elevation_log_disabled.py
- test_services_forget_window_cycle.py
- _setup
- ShutterPilotNextActionSensor
- CHANGELOG.md
- test_geometry_and_season.py
- schedule_times.py
- sun_condition_keys
- test_brightness_pending_evening.py
- Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)
- TestDriveVerdictInExport
- test_open_stage2.py
- conftest.py
- Gesamtplan Raffstores
- ShutterPositionStore
- TestPerShutterOverride
- data
- Sondertage-Sensor (Workday-Sensor)
- .test_a_real_move_still_counts
- is_cover_ventilating
- test_reference_run.py
- _three_state
- test_window_parked_and_late_report.py
- TestSecondWindowContact
- TestSwitchEntity
- test_my_position_blind_drive.py
- services.yaml Service Definitions
- get_elevation_bounds
- Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)
- Bug Report Issue Template
- test_window_trigger_shaded_manual_reopen.py
- HomeAssistant
- Shutter Pilot Integration (Brand/Concept)
- TestShadingOptOut
- clamp_to_bounds
- test_manual_move_clears_pending_drive.py
- TestElevationCanBeSwitchedOff
- TestExportReadsTheWayTheReportWasMeant
- Tests GitHub Workflow
- _shutter
- _canonical_state
- TestTheExportExplainsAQuietWindow
- TestDriveCommandNote
- _shutter
- get_window_state
- _awning
- const.py
- _frost_area
- TestWebSocketToggle
- .test_neighbour_in_the_same_area_is_not
- TestNextActionWithoutASchedule
- note_manual_position
- TestSecondCloseCondition
- fixture.mjs
- drive_delay.mjs
- copy_from.mjs
- sorting.mjs
- guard_slot.mjs
- Stub
- reorder.mjs
- .test_scheduler_skips_disabled_shutter
- resolve_shade_position
- ._coverAction
- _local_timezone
- tilt_buttons.mjs
- TestNoUpCondition
- _ws_delete_shutter

## God Nodes (most connected - your core abstractions)
1. `ShutterPilotPanel` - 141 edges
2. `async_build_export()` - 124 edges
3. `sun_condition_keys()` - 101 edges
4. `CLAUDE.md – Fortschritts-Log (Archiv)` - 74 edges
5. `set_cover_position()` - 65 edges
6. `is_cover_sun_protected()` - 58 edges
7. `get_position_store()` - 56 edges
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

## Communities (156 total, 10 thin omitted)

### Community 0 - "test_brightness_lux_hold.py"
Cohesion: 0.21
Nodes (15): _area(), clock(), drive(), _lux(), _positions(), fixture, Mindestdauer an der Lux-Schwelle im Helligkeitsmodus. bjoerg (community-…, Monotone Uhr von Hand: die Frist rechnet in Sekunden seit der ersten… (+7 more)

### Community 1 - "evaluate_guard"
Cohesion: 0.06
Nodes (48): async_enforce_guard(), evaluate_guard(), Merge the global protection settings with this awning's overrides. Most…, Decide whether this awning may be out, and say why not. `fail_open` is for the…, Evaluate every awning and pull in the ones that must not be out., resolve_guard_config(), _awning(), _data() (+40 more)

### Community 2 - "elevation.py"
Cohesion: 0.05
Nodes (66): ConfigEntry, HomeAssistant, Dusk retract for awnings: drive in once, never back out on its own. Asked for…, Watch every awning's own dusk condition, if it has one configured., setup_awning_dusk(), guard_status(), is_barred(), Read the last decision without touching it. Deliberately does not evaluate:… (+58 more)

### Community 3 - "TestRolePositions"
Cohesion: 0.33
Nodes (3): parametrize, The group services used to hard-code 100/0 and ignore these values., TestRolePositions

### Community 4 - "window_trigger.py"
Cohesion: 0.09
Nodes (25): _cover_is_travelling(), True while the cover reports that it is on its way somewhere. Bewusst nur der…, Where this cover *stands* – not the number it happens to pass through. Ein…, resting_position(), _first_entity_id(), get_tilt_entity_id(), Accept both a plain entity id and a single-element list., Entity id of the optional separate tilt contact, or empty string. (+17 more)

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
Nodes (32): cancel_verification(), _current_position(), is_enabled(), _opt_int(), Any, ConfigEntry, HomeAssistant, Check that a cover actually reached the requested position. Radio-driven… (+24 more)

### Community 10 - "test_forum_2_18.py"
Cohesion: 0.07
Nodes (24): _awning(), cover_calls(), fixture, Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg. Vier…, „Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts., Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren., 100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch., Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich. (+16 more)

### Community 11 - "manifest.json"
Cohesion: 0.10
Nodes (20): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+12 more)

### Community 12 - "test_ventilation.py"
Cohesion: 0.12
Nodes (25): _area(), _blocked_setup(), _conditions(), cover_calls(), _evaluate(), _fast_startup_restore(), _positions(), fixture (+17 more)

### Community 13 - "awning_guard.py"
Cohesion: 0.04
Nodes (73): async_frost_hold(), async_frost_release(), async_retract_awning(), async_retract_storm(), clamp_to_rest(), describe_reasons(), _drop_frost_marker(), extends_upward() (+65 more)

### Community 14 - "is_cover_sun_protected"
Cohesion: 0.10
Nodes (21): is_cover_sun_protected(), True if shading currently holds this specific cover., Die Tagesmerker des Schedulers loeschen. Beim Aufbau gilt jede heute schon…, charly166 und Linos: nicht beschatten, was noch gar nicht offen ist., Das bisherige Verhalten – und genau das, was gemeldet wurde., bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest., Das alte Verhalten: Merker faellt, gefahren wird nicht., MartyBr: die Beschattung je Bereich abschalten, ohne die Automatik. (+13 more)

### Community 15 - "get_weather_data"
Cohesion: 0.10
Nodes (26): async_fetch_forecast(), _configured_entity(), get_weather_data(), _peak_today(), Any, ConfigEntry, HomeAssistant, Fetch today's weather forecast for use as a shading condition. Since Home… (+18 more)

### Community 16 - "test_hand_lift_new_episode.py"
Cohesion: 0.13
Nodes (29): _area(), clock(), drive(), _drives(), _hand_open(), _lux(), fixture, Ein von Hand geoeffneter Rollladen bleibt im Helligkeitsmodus abends offen.… (+21 more)

### Community 17 - "_positions"
Cohesion: 0.07
Nodes (60): _close_delay_seconds(), _debounce_seconds(), Debounce plus the configured "I'll be right back" wait, in seconds., How long "closed" has to hold before we act on it., _door(), parametrize, Rueckfahrt nach dem Schliessen verzoegern (heinzel, #252). Im Winter abends…, Tuer auf (hier: gekippt), der Rollladen steht danach auf 50 %. (+52 more)

### Community 18 - "test_awning_excluded.py"
Cohesion: 0.22
Nodes (7): filter_shutters_by_area(), Filter shutters by area_up_id or area_down_id. Every kind is in by default…, cover_calls(), _fast_startup_restore(), fixture, Was eine Markise nicht mitmacht. Sie steht in derselben Liste wie die…, „Zu" an einem Dachfenster heisst schliessen – ein Knopfdruck.

### Community 21 - "test_awning_dusk.py"
Cohesion: 0.08
Nodes (35): is_dusk_retracted(), Any, True while dusk retract alone is holding this awning in. Read by elevation.py…, awning_dusk_condition_met(), True when this awning's own "get dark, retract" condition holds. Lives on the…, _area(), _awning(), cover_calls() (+27 more)

### Community 22 - "_latest_deadline"
Cohesion: 0.13
Nodes (22): _latest_deadline(), time, The clock time this direction runs at regardless of the lux value. None means…, _area(), _as_local(), _berlin(), _monday(), datetime (+14 more)

### Community 23 - "test_shade_hours.py"
Cohesion: 0.16
Nodes (14): True if the clock allows shading right now. Elevation, azimuth, conditions and…, shading_time_window_ok(), _at(), cover_calls(), _fast_startup_restore(), datetime, fixture, Beschattung nur innerhalb bestimmter Uhrzeiten. Aus GitHub-Diskussion #5… (+6 more)

### Community 24 - "get_sun_mode_triggers"
Cohesion: 0.13
Nodes (22): get_sun_mode_triggers(), Return (up, down) datetimes for a sun-mode area, jitter and bounds included.…, _area(), _hm(), parametrize, Tests for the earliest/latest clock bounds in sun mode. MartyBr's case from the…, Midsummer: the sun is up at 05:10, the shutters wait until 07:30., Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it. (+14 more)

### Community 25 - "test_awning_shading.py"
Cohesion: 0.14
Nodes (23): awning_lockout_key(), Return the lockout option key for a guard slot., awning_shade_position(), Extension for the current sun height. A high sun is shaded by a short…, _area(), _awning(), cover_calls(), _fast_startup_restore() (+15 more)

### Community 26 - "test_sun_protect_areas.py"
Cohesion: 0.13
Nodes (25): _area(), cover_calls(), _fast_startup_restore(), _positions(), fixture, Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4). Gemeldet als…, Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut., Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich. Der Hoch-… (+17 more)

### Community 27 - "ShutterPilotAwningGuardSensor"
Cohesion: 0.11
Nodes (13): BinarySensorEntity, async_setup_entry(), AddEntitiesCallback, Any, callback, ConfigEntry, datetime, HomeAssistant (+5 more)

### Community 28 - "test_resume_automation.py"
Cohesion: 0.08
Nodes (29): cover_calls(), _drive_from_outside(), _fast_startup(), _in(), fixture, Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen. pcsv17…, Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen., Genau sein Ablauf, gegen die echte Beschattung gefahren. (+21 more)

### Community 29 - "helpers.py"
Cohesion: 0.04
Nodes (82): Binary sensor entities exposing the sun protection state per area., async_restore_positions_on_startup(), _collect_cover_entity_ids(), ConfigEntry, HomeAssistant, Track cover positions and restore after Home Assistant restart., After HA start, restore persisted positions if cover integration restored wrong…, Listen to cover state changes and persist positions. (+74 more)

### Community 30 - "test_forum_2_21_3.py"
Cohesion: 0.14
Nodes (23): cover_calls(), _gated_sleep(), _moving(), _positions(), fixture, c.radis Fall: der Rollladen parkt auf 74 %, einer Zahl, die nirgends steht.…, Der Rollladen ist unterwegs – die gemeldete Position ist eine Momentaufnahme., Fenster wird angefasst, waehrend der Abendlauf noch faehrt. (+15 more)

### Community 31 - "TestWithoutFeedback"
Cohesion: 0.18
Nodes (8): _blind(), _normal(), Der Antrieb meldet keine Position – nur `state`, kein current_position., Bisheriges Verhalten für alle anderen Rollläden., Vor der ersten Fahrt weiss auch die Buchführung nichts., Meldet der Antrieb eine Position, gilt sie – auch im Blind-Modus., TestWithFeedback, TestWithoutFeedback

### Community 32 - "_status"
Cohesion: 0.14
Nodes (16): _berlin_offset(), _options(), date, Tests for the area_triggers block in the get_status WebSocket payload. Xerenas…, The reported case: 07:30 must be sent, not the 06:07 sunrise., The panel falls back to its own display – but must get everything else., bjoerg und charly166: die Markisen-Einstellungen standen wieder leer da.…, GitHub #9: Entität im Formular gewählt, Speichern gedrückt, Feld wieder leer.… (+8 more)

### Community 33 - "shutter-pilot-panel.js"
Cohesion: 0.08
Nodes (24): AWNING_GUARD_SLOTS, AWNING_UNUSED_KEYS, BOOL_COND_DOMAINS, COMPASS_PRESETS, COND_DOMAINS, COND_SLOTS, FORCED_BELOW_SLOTS, HINTS (+16 more)

### Community 34 - "resolve_shading_config"
Cohesion: 0.16
Nodes (14): Merge area and shutter shading settings into one config dict. Geometry follows…, resolve_shading_config(), _area(), data(), fixture, Tests for per-shutter conditions falling back to the area. Forum discussion:…, South is in its dead band and holds; west never engaged., The point of the whole design: brightness per window, weather once. (+6 more)

### Community 35 - "sun_extra_conditions_met"
Cohesion: 0.11
Nodes (17): True when every configured extra condition for shading is satisfied. Pass the…, sun_extra_conditions_met(), _area(), Tests for the extra shading conditions. Forum feedback (Nicknol): shading…, A passing cloud must not make the shutters bounce., A nonsensical configuration must not create a trap., Nicknol's case: real sunshine AND a warm day., Extra conditions gate shading; they never widen the sun window. (+9 more)

### Community 36 - "._note"
Cohesion: 0.12
Nodes (12): bjoerg: „nur die Abfrage des Fenstergriffs scheint zu haengen." Sein Kontakt…, Ohne Kipp-Zustand ist alles in Ordnung – dafuer gibt es 2.8.2., Ein `sensor` darf melden, was er will – kein Hinweis., „auf" faltet auf on – erreichbar, also kein Hinweis., c.radis Fall: „wenn das Fenster auf gekippt steht, wird der Rolladen gar nicht…, Steht das Fenster gerade gekippt, ist das die halbe Antwort., Mit dem Haken faehrt er – dann gibt es nichts zu erklaeren., Ohne Kontakt tritt „Fenster offen" nie ein – der Haken tut nichts. (+4 more)

### Community 37 - "test_forum_findings.py"
Cohesion: 0.11
Nodes (16): drives(), fixture, Die fünf Funde aus der Forum-Runde vom 08.08.2026 – und der Export. Zwei…, Aufgezeichnete Fahrbefehle – ohne echte Cover-Integration., Ein Bereich mit Sonnenschutz, Haltezeit 30 min und einer Lux-Bedingung., Eine Runde der Sonnenschutz-Auswertung., F1: der Merker wurde gesetzt, bevor gefahren wurde., F5: die Haltezeit hielt auch das berechtigte Ende auf. (+8 more)

### Community 39 - "is_weekend_schedule"
Cohesion: 0.13
Nodes (15): get_random_offset(), get_time_mode_triggers(), is_weekend_schedule(), date, Return (up, down) times for a time-mode area, jitter included., True if the weekend schedule applies. When a workday sensor is configured it…, Return the presence-simulation jitter in minutes for one day. Deterministic per…, _area() (+7 more)

### Community 40 - ".make_guard_entry"
Cohesion: 0.18
Nodes (5): fixture, `_guard_rows()` beschriftete die Schwellen bisher immer als "nicht invertiert"…, Derselbe Fehler wie beim Wind (Faktor 3,6 daneben), nur an zwei weiteren…, TestGuardTableRespectsInversion, TestRainAndIceUnitPlausibility

### Community 41 - "test_init.py"
Cohesion: 0.10
Nodes (19): async_get_config_entry_diagnostics(), Any, ConfigEntry, HomeAssistant, Return diagnostics for a config entry., End-to-end setup tests: the integration must load with all platforms., Master switch plus one auto switch per area., The next-action sensor exists and reports a direction. (+11 more)

### Community 42 - "test_tilt_hand_detect.py"
Cohesion: 0.23
Nodes (22): _blind(), fixture, Handverstellung nur der Lamellen (Raffstore, Stufe 4, simon42 #172 Claus). Der…, Die Hoehe steht seit Ewigkeit still - nur der Winkel aendert sich., Bestandsschutz: ohne Haken bleibt der Tracker fuer Winkel blind., Nach einer Hoehenfahrt melden manche Aktoren kurz falsche Winkel., Die Hoehe hat niemand angefasst - ihr Ziel bleibt gueltig., Claus #225: MDT JAL-0810M "Lamellen nach Fahrtende 0 %". Nach jeder… (+14 more)

### Community 43 - "sun_protect_conditions_met"
Cohesion: 0.17
Nodes (12): azimuth_in_sun_protect_range(), True when the sun stands in front of this area's windows. Ranges may wrap…, True when both elevation and compass direction call for shading., sun_protect_conditions_met(), _area(), parametrize, Tests for elevation + azimuth based sun protection., The bug azimuth support fixes: 0–15° elevation is hit twice a day. (+4 more)

### Community 44 - "test_export_notes.py"
Cohesion: 0.11
Nodes (12): Ein Kipp-Zustand, den der Kontakt gar nicht melden kann. Ein `binary_sensor`…, _window_contact_note(), entry(), _entry_with_area(), Hinweise im Export, die ohne laufende Automatik pruefbar sind. Bewusst nicht in…, bjoerg: „Mein Regensensor liefert nur nass und trocken". In…, Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup., bjoergs Export: „Fensterrichtung: ❌ (295,4° in [225° – 315°])". Die Zeile las… (+4 more)

### Community 46 - "test_area_mode_none.py"
Cohesion: 0.11
Nodes (17): cover_calls(), _fast_startup_restore(), fixture, malleYay: Shutter Pilot nur fuer den Sonnenschutz. „Gibt es eine Moeglichkeit,…, Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest., Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein Reload…, Gegenprobe: dieselben Zeiten, nur mit Modus., Der Punkt der ganzen Uebung. (+9 more)

### Community 47 - "test_min_drive_gap.py"
Cohesion: 0.15
Nodes (14): _drive_all(), drive_log(), _entry(), fixture, MockConfigEntry, parametrize, Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos). Bei Funk (433…, Nach einer Pause muss die nächste Fahrt sofort raus. (+6 more)

### Community 50 - "test_reorder_shutters.py"
Cohesion: 0.14
Nodes (14): The stored list in the requested order. Covers named in `order` come first, in…, _reordered_shutters(), _Connection, _covers(), entry(), fixture, Die Reihenfolge der Rollllaeden im Bereich festlegen (DerTomm, GitHub #17). Die…, Ein Neuladen setzt die Merker zurueck - ohne Grund nicht. (+6 more)

### Community 51 - "remember_drive_after_close"
Cohesion: 0.20
Nodes (12): Note a drive that waits for the window, in memory and on disk. The shutter…, Bring remembered catch-up drives back after a restart. Only covers that still…, remember_drive_after_close(), restore_drive_after_close(), _data(), entry(), fixture, Nachhol-Fahrten überstehen den Neustart. Stand die Schließzeit an, während das… (+4 more)

### Community 52 - "Bereichs-Karte (Area Card)"
Cohesion: 0.18
Nodes (18): Bereichs-Karte (Area Card), Area Add/Edit/Delete Actions, Area Mode: Brightness (Helligkeit), Area Mode: Sun (Sonnenstand), Area Mode: Time (Zeit), Area-to-Shutter Association (Rollläden count per area), Automatik-Schalter je Bereich, Dashboard Tab (+10 more)

### Community 53 - "test_keep_position_and_tilt.py"
Cohesion: 0.17
Nodes (14): _blind(), calls(), _positions(), fixture, Hoehe und Lamellen getrennt (simon42 #172, #196, Claus). Ein Raffstore, der den…, _setup(), TestGroupServiceAndWaitingDrive, TestScheduleHonoursIt (+6 more)

### Community 54 - "_setup"
Cohesion: 0.06
Nodes (36): default_area(), callback, ConfigEntry, Config flow for Shutter Pilot integration. All real configuration happens in…, Handle a config flow for Shutter Pilot., Handle the initial step. Location is taken from Home Assistant., Return the options flow handler., Minimal options flow – configuration lives in the sidebar panel. (+28 more)

### Community 55 - "i18n_parity.mjs"
Cohesion: 0.12
Nodes (7): code, codes, de, DEFAULT_PANEL, Host, I18N, Stub

### Community 56 - "set_cover_position"
Cohesion: 0.09
Nodes (22): my_position_target(), _press_my_position(), Set cover position (and optionally slat angle) and persist the result. Returns…, Supported-features bitmask of a cover, 0 when it cannot be read., The taught "My" stop, when this target is close enough to it. Returns…, Trigger the My entity, whichever domain it lives in., Drive a cover to a position, falling back to open/close where needed. Many…, Set the slat angle. Covers without tilt support are skipped quietly. (+14 more)

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

### Community 61 - "test_forum_2_17.py"
Cohesion: 0.13
Nodes (19): cover_calls(), entry(), _fast_startup_restore(), _positions(), fixture, Die vier Forumsmeldungen zu 2.16.0, jede mit ihrem eigenen Beweis. Leichter…, Gegenprobe: derselbe Aufbau, nur der Haken fehlt., Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand diesen… (+11 more)

### Community 62 - "CLAUDE.md – Fortschritts-Log (Archiv)"
Cohesion: 0.03
Nodes (74): 2026-08-02 – 2.4.1: Hauptschalter und Menü-Knopf, 2026-08-02 – 2.4.2: Rechteprüfung (Review von frenck), 2026-08-02 – 2.5.0: Automatik pro Rollladen (Feedback von Linos), 2026-08-06 – 2.6.0, Teil 1: Zeitzone im Sonnenmodus (Meldung von Xerenas), 2026-08-06 – 2.6.0, Teil 2: drei Features aus dem Forum, 2026-08-07 – 2.7.0, Teil 1: zwei GitHub-Issues, 2026-08-07 – 2.7.0, Teil 2: die Restliste abgearbeitet, 2026-08-07 – 2.7.1: die drei Restpunkte (+66 more)

### Community 63 - "test_duplicate_cover.py"
Cohesion: 0.25
Nodes (9): MockConfigEntry, Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis. Forum,…, Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen., Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular., _save(), _setup(), _shutter(), TestExportNamesExistingDuplicates (+1 more)

### Community 64 - "test_panel.py"
Cohesion: 0.07
Nodes (33): CompletedProcess, Das Panel rendern, ohne Home Assistant zu starten. Warum das hier steht und…, Bereiche kommen mit, Identitaet und Fenstersensoren nicht., Sortiert angezeigt, aber der Index zeigt auf die volle Liste – sonst loescht…, Eine 0 bei den Sonnengrenzen ist eine Grenze, nur leer ist keine (Linos). Ohne…, Windschutz fuer Raffstores und Sperr-Entitaet (2.25.0)., `window_react` und `drive_after_close_up` (Raffstore, Florian/Claus). Das…, Hoehe/Lamellen "unveraendert" und der Winkel nach der Hoehe (2.26.0). (+25 more)

### Community 65 - "_silent_setting_notes"
Cohesion: 0.21
Nodes (6): Settings that are stored, look like they work, and do nothing. Both come from…, _silent_setting_notes(), Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen., Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos., Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie., TestSilentSettings

### Community 66 - "_shutter"
Cohesion: 0.18
Nodes (9): Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen…, Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.…, Bestandsanlagen kennen den Schlüssel nicht – die müssen weiterlaufen., Der Schalter ist die lebende Wahrheit, der gespeicherte Wert der Start., Der eigene Schalter des Rollladens hat den Laufzeitwert schon gesetzt., Fail open: Ein toter Schalter darf keinen Rollladen stilllegen., Umgelegter Schalter wirkt sofort, ohne Reload des Config-Entry., _shutter() (+1 more)

### Community 67 - "test_window_trigger_stale_restore.py"
Cohesion: 0.25
Nodes (9): cover_calls(), _fast_startup(), _positions(), fixture, Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine veraltete…, Fahrten mitschreiben und die Position tatsaechlich im State nachziehen., _setup(), _shutter() (+1 more)

### Community 68 - "README.md"
Cohesion: 0.22
Nodes (12): Markise (device_kind awning), Bei Dämmerung einfahren (awning_dusk), Wind-/Regen-/Frostschutz (awning_guard), Frostschutz, My-Position (Somfy RTS dritte Stellung), Dienst retract_awnings, Dachfenster (device_kind roof_window), Lamellensteuerung (Raffstore/Jalousie) (+4 more)

### Community 69 - "_setup"
Cohesion: 0.16
Nodes (18): _area(), calls(), _fast(), _morning(), _positions(), fixture, Sichtschutz (Raffstore, Stufe 6, simon42 #172 Claus). Eine Entitaet…, Die Abendfahrt hat ihn waehrenddessen zugefahren. (+10 more)

### Community 70 - "Catch-up Drive Bookkeeping (heinzie)"
Cohesion: 0.23
Nodes (11): cover_calls(), _driven(), entry(), datetime, fixture, heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten. Sein…, Genau heinzies Ablauf, vier Schritte., Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden. (+3 more)

### Community 71 - "_area"
Cohesion: 0.15
Nodes (9): _area(), Frost fragt "kaelter als" – dort ist 0 als Aufhebepunkt normal., Ein leeres Feld faellt auf den Einschaltpunkt zurueck., bjoergs Fall: 0 ist eine echte Schranke, kein "leer"., Nach einem Neustart ist der Merker leer – dann gilt on_above., Der Export benennt den Fall, denn Bestandsdaten tragen die 0 weiter., TestEmptyReleasePoint, TestExportNote (+1 more)

### Community 72 - "test_services.py"
Cohesion: 0.19
Nodes (12): cover_calls(), _positions(), fixture, Tests for the group services. Regression guard: open_group/close_group used to…, Each shutter gets its own shading angle, not the first one's., Ventilation reuses the position configured for a tilted window., Users can hook their own automations onto the movement event., test_close_group_uses_per_shutter_positions() (+4 more)

### Community 73 - "TestHelperEntities"
Cohesion: 0.14
Nodes (7): parametrize, Helpers as a condition (DocSpider). A house mode, a cinema flag or a cleaning-…, No on_above/off_below configured, and none needed., The panel stores the option verbatim, HA reports it verbatim., Nothing to compare against – it must not block, but it warns., Mirrors the order the panel renders – list first, domain second., TestHelperEntities

### Community 74 - "test_forum_2_15.py"
Cohesion: 0.17
Nodes (12): automated_up_blocked(), datetime, True if this area must not open automatically today because it is a weekend.…, Reason the automated opening of this whole area is off today, or None. One call…, weekend_blocks_up(), cover_calls(), _fast_startup_restore(), fixture (+4 more)

### Community 75 - "resolve_sun_geometry"
Cohesion: 0.19
Nodes (10): elevation_in_sun_protect_range(), get_azimuth_bounds(), Merge area and shutter shading geometry into one config dict. A room can have…, True when sun elevation is within the configured protection window. Switched…, Return (min, max) azimuth for the windows of this area, in degrees., resolve_sun_geometry(), Der Haken „Sonnenhöhe prüfen" sitzt seit 2.10.1 auch am Rollladen. Gespeichert…, Wolfs Fall: Haken am Rollladen aus, „Eigene Ausrichtung" auch. (+2 more)

### Community 76 - "manual_position_is_a_close"
Cohesion: 0.12
Nodes (14): manual_position_is_a_close(), True if a hand-driven position is simply "closed", not an override. The manual…, Von Hand ganz hochgefahren gilt nicht als "zu" (Claus, simon42 #217). Seine…, Florian: auf und zu sind dieselbe Position, nur die Lamellen., Bestandsschutz: wo auf und zu weit auseinander liegen, bleibt es., 0 = oben, 70 = zu: weiter nach unten (100) ist weiter zu., Dreissig Prozent Abstand: die Regel greift weiter., _shutter() (+6 more)

### Community 77 - "Any"
Cohesion: 0.10
Nodes (35): _ages(), _condition_note(), _condition_rows(), _deferred_close_note(), _dusk_row(), _fmt(), _fmt_labelled(), _guard_rows() (+27 more)

### Community 78 - "test_frost_lock.py"
Cohesion: 0.20
Nodes (36): _cover(), cover_calls(), _held(), _no_schedule(), _positions(), fixture, Frostsperre für Rollläden (eurofinder, simon42 #237). Der bestehende…, Ein leerer Akku darf das Haus nicht den ganzen Winter stilllegen. (+28 more)

### Community 79 - "async_build_export"
Cohesion: 0.07
Nodes (20): async_build_export(), _awning_silent_notes(), ConfigEntry, Build the export as markdown plus the raw options behind it., Shutter settings left on an awning, where they mean nothing. Same class as…, Jedes Speichern im Panel laedt neu und leert die Merker. Wer danach exportiert…, Bestandsinstallation, die den Schluessel noch nicht kennt., Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen". Die… (+12 more)

### Community 80 - "set_cover_sun_protected"
Cohesion: 0.16
Nodes (13): Track shading per cover, so windows facing different ways act apart., set_cover_sun_protected(), cover_calls(), fixture, Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt. Zwei getrennte…, Der Rollladen steht auf Beschattung, das Fenster geht auf., Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen., Aussperrschutz an, Kipp-Position darunter – wer gewinnt? Der Fenstertrigger ist… (+5 more)

### Community 81 - "_raffstore"
Cohesion: 0.19
Nodes (12): _morning_tick(), _positions(), _raffstore(), Der Scheduler um 07:00 des naechsten Tages (vermeidet das Vormarkieren beim…, Bestandsschutz: ohne den neuen Haken faehrt die Hochfahrt wie bisher., Bestandsschutz: wer nur `drive_after_close` gesetzt hat, faehrt morgens bei…, Bestandsschutz: ohne den Schluessel bewegt der Kontakt wie bisher., Auf und zu sind dieselbe Position, nur die Lamellen unterscheiden sich. (+4 more)

### Community 82 - "._setup"
Cohesion: 0.30
Nodes (5): hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es leider…, Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py, nur an der…, Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal zu. Die…, TestGuardBeatsShadingForAWindow, TestOpeningAndClosingByConditions

### Community 83 - "__init__.py"
Cohesion: 0.10
Nodes (22): cancel_all(), Drop every pending check, used when unloading the entry., _apply_shutter_automation_state(), async_migrate_entry(), async_setup(), async_unload_entry(), _drop_registry_entries(), ConfigEntry (+14 more)

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

### Community 91 - "_setup"
Cohesion: 0.22
Nodes (8): Alles andere spricht fuer Beschattung – nur die Uhr nicht., Eine Uhrzeitgrenze kommt nicht zurueck – anders als eine Wolke. Wuerde die…, Was entscheidet, muss im Bericht stehen – sonst sucht wieder jemand., Sonst stuende an jedem Rollladen eine Zeile, die nichts beschreibt., _setup(), TestAgainstTheRealShading, TestExport, _ticks()

### Community 92 - "ShutterPilotNextActionSensor"
Cohesion: 0.21
Nodes (4): callback, datetime, Timestamp of the next scheduled up/down movement for one area., ShutterPilotNextActionSensor

### Community 93 - "CHANGELOG.md"
Cohesion: 0.31
Nodes (8): Manuelle Übersteuerung (manual_override), Dienst shutter_pilot.resume_automation, Zweite Beschattungsposition (sp_alt), Forum Answers 2.17.0, Forum Answers 2.18.0, c.radi (Forumsnutzer), pcsv17 (Forumsnutzer), Smons (Forumsnutzer)

### Community 94 - "test_geometry_and_season.py"
Cohesion: 0.18
Nodes (8): True if today lies inside the configured shading season. Months are inclusive…, season_allows_shading(), parametrize, Tests for per-shutter shading geometry, season window and partial close. Forum…, October to March must wrap, like the azimuth range does., The case Linos described: one room, south and west windows., TestSeason, TestWindowsFacingDifferentWays

### Community 95 - "schedule_times.py"
Cohesion: 0.11
Nodes (29): _bound(), _clamp_with_reason(), get_next_action(), get_sun_mode_trigger_details(), infer_today_sun_time(), _local_sun_time(), _next_from_times(), parse_time() (+21 more)

### Community 96 - "sun_condition_keys"
Cohesion: 0.04
Nodes (80): Return (entity, on_above, off_below, states) option keys for a slot., Return the "compare downwards" option key for a slot., sun_condition_invert_key(), sun_condition_keys(), close_condition_met(), condition_memory(), _condition_slot_met(), frost_condition_met() (+72 more)

### Community 97 - "test_brightness_pending_evening.py"
Cohesion: 0.23
Nodes (19): drive(), _drives(), _lux(), fixture, Die Vormerkung "heute noch hochfahren" endet mit der Abendfahrt (Claus, #249).…, Der gemeldete Tag, Meldung fuer Meldung., Vorgemerkt und nie eingeloest (Automatik des Rollladens war morgens aus)., Gilt der Rollladen schon als unten, faehrt abends nichts - trotzdem Schluss. (+11 more)

### Community 98 - "Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)"
Cohesion: 0.17
Nodes (11): #11 (offen lassen, Zwischenstand), #13 (schließen), #14 (offen lassen), #15 (offen lassen, Rückfragen), #16 (offen lassen), #17 (schließen), #18 (schließen), #19 (schließen, Englisch) (+3 more)

### Community 99 - "TestDriveVerdictInExport"
Cohesion: 0.18
Nodes (4): „Warum faehrt er morgens nicht hoch" stand bisher nirgends im Bericht. Jede…, Gespeichert, sichtbar, wirkungslos – die bekannte Klasse., _remember(), TestDriveVerdictInExport

### Community 100 - "test_open_stage2.py"
Cohesion: 0.22
Nodes (22): calls(), _fast(), _positions(), fixture, Zweite Oeffnungsstufe (simon42 #225 Claus). Morgens nur die Lamellen (normale…, Wochenend-Sperre, Sichtschutz, "nicht hochfahren": keine Hochfahrt, keine Stufe…, _setup(), test_a_dead_condition_entity_holds_it_back() (+14 more)

### Community 101 - "conftest.py"
Cohesion: 0.33
Nodes (6): auto_enable_custom_integrations(), entry(), fixture, Shared fixtures for the Shutter Pilot test suite., Let Home Assistant load custom_components/ during tests., Set up a Shutter Pilot config entry. The sidebar panel needs the real…

### Community 102 - "Gesamtplan Raffstores"
Cohesion: 0.09
Nodes (21): 2a – Raffstore-Sturm, 2b – Sperr-Entität (Claus), Außerhalb der Raffstores (Claus #172), Befund im Code, Bestandsschutz, Bestandsschutz, Entwurf Stufe 2 — umgesetzt in 2.25.0 (lokal) (2026-10-24, nach Antworten #200 Florian und #202 Claus), Entwurf Stufe 4 – Handbedienung nur an den Lamellen (2026-11-01, noch nichts gebaut) (+13 more)

### Community 103 - "ShutterPositionStore"
Cohesion: 0.07
Nodes (27): manual_override_still_blocks(), True if a manual position should keep blocking automated opening. The behaviour…, Any, callback, HomeAssistant, Drop a remembered drive, because it ran or is no longer wanted., Remember that the frost lock holds this cover, and where it stood., Return remembered drives that are still worth running. A catch-up from days ago… (+19 more)

### Community 104 - "TestPerShutterOverride"
Cohesion: 0.29
Nodes (3): Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich., Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung., TestPerShutterOverride

### Community 106 - "Sondertage-Sensor (Workday-Sensor)"
Cohesion: 0.40
Nodes (6): Bedingung 'Hochfahren unterbinden' (no_up), Am Wochenende gar nicht hochfahren, Sondertage-Sensor (Workday-Sensor), Forum Answers 2.15.0, hollsten / Roland (Forumsnutzer), MartyBr (Forumsnutzer)

### Community 107 - ".test_a_real_move_still_counts"
Cohesion: 0.24
Nodes (9): _hours_pass(), _positions(), Die Karenz der eigenen Fahrt (90 s) ist am Morgen laengst vorbei., Tag 1 aus c.radis Bericht - war schon richtig, bleibt es., Gegenprobe: dieselbe Meldung mit neuer Position ist eine Handfahrt., _report(), _setup(), TestAStateUpdateWithoutAMoveIsNotAManualMove (+1 more)

### Community 108 - "is_cover_ventilating"
Cohesion: 0.67
Nodes (3): is_cover_ventilating(), Any, True while automatic ventilation holds this cover.

### Community 109 - "test_reference_run.py"
Cohesion: 0.16
Nodes (29): calls(), _fast(), _old(), _positions(), fixture, Referenzfahrt (Raffstore, Stufe 7, simon42 #172 Claus). In festem Abstand…, Hintergrund-Aufgaben werden von async_block_till_done nicht abgewartet., Kein Lauf in der ersten Nacht nach dem Einschalten. (+21 more)

### Community 110 - "_three_state"
Cohesion: 0.21
Nodes (7): bjoergs Aufbau: ein Griff mit open / tilted / closed., bjoergs Fall: 30 % muessen 30 % bleiben., Die Gegenrichtung – dafuer ist der Aussperrschutz da., Wer die Kipp-Position hoeher legt, merkt von der Aenderung nichts., TestTiltedWindow, TestWithoutLockProtection, _three_state()

### Community 111 - "test_window_parked_and_late_report.py"
Cohesion: 0.27
Nodes (11): calls(), _park(), fixture, bjoerg (community-smarthome.com/11378/166): zwei Fehler an der Abendfahrt bei…, Tagsueber offen, nichts vorgemerkt: das Fenster zieht ihn nicht herunter., _setup(), test_late_report_near_target_stays_automation(), test_open_cover_without_pending_drive_is_not_pulled_down() (+3 more)

### Community 112 - "TestSecondWindowContact"
Cohesion: 0.27
Nodes (4): Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf., Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen., Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel., TestSecondWindowContact

### Community 113 - "TestSwitchEntity"
Cohesion: 0.33
Nodes (3): Bereich "Wohnbereich" und Rollladen dürfen sich nicht ins Gehege kommen. Beide…, Je Rollladen ein eigener Schalter, benannt nach dem Namensfeld., TestSwitchEntity

### Community 114 - "test_my_position_blind_drive.py"
Cohesion: 0.27
Nodes (10): calls(), _drive(), fixture, My-Position bei einem Antrieb ohne Rueckmeldung, der trotzdem Positionen kann…, Bestandsschutz: ein Antrieb mit Rueckmeldung bleibt bei der Zahl., test_a_target_far_from_my_is_driven_by_position(), test_a_target_within_the_tolerance_still_presses_it(), test_the_shade_button_is_pressed_for_a_blind_drive() (+2 more)

### Community 115 - "services.yaml Service Definitions"
Cohesion: 0.40
Nodes (5): Dienste open_group / close_group, Dienst stop_group, Dienst sun_protect_group, Dienst ventilate_group, services.yaml Service Definitions

### Community 116 - "get_elevation_bounds"
Cohesion: 0.27
Nodes (5): get_elevation_bounds(), Return (min, max) elevation for sun protection range., Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)., TestGeometryOverrideKeepsAreaBounds, TestElevationBounds

### Community 117 - "Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig)"
Cohesion: 0.67
Nodes (4): Nachholfunktion (drive_after_close), Zweiter Fensterkontakt (Doppelflügel, ODER-Verknüpfung), Fensterkontakt-Zustände (offen/gekippt/zu, 2- vs 3-wertig), heinzie (Forumsnutzer)

### Community 118 - "Bug Report Issue Template"
Cohesion: 0.50
Nodes (3): Bug Report Issue Template, Issue Template Config, Feature Request Issue Template

### Community 119 - "test_window_trigger_shaded_manual_reopen.py"
Cohesion: 0.23
Nodes (10): cover_calls(), _fast_startup(), _positions(), fixture, Ein Beschattungs-Merker (shaded=True) ueberlebt eine manuelle Fahrt.…, Rollladen ist von Hand voll offen (100%), der Beschattungs-Merker aus der…, Gegenprobe zum Fix: steht der Rollladen tatsaechlich noch an seiner…, _setup() (+2 more)

### Community 120 - "HomeAssistant"
Cohesion: 0.14
Nodes (42): ActiveConnection, async_response, _async_register_panel(), _async_register_websocket(), _find_entry_data(), callback, HomeAssistant, Switch the panel between simple and expert mode. Deliberately not routed… (+34 more)

### Community 121 - "Shutter Pilot Integration (Brand/Concept)"
Cohesion: 0.67
Nodes (3): Shutter Pilot Brand Icon (2x), Shutter Pilot Brand Icon (256x256 PNG), Shutter Pilot Integration (Brand/Concept)

### Community 122 - "TestShadingOptOut"
Cohesion: 0.27
Nodes (3): Der Vertrag aus 2.8.0, jetzt eine Ebene hoeher. `_memory_copy()` schuetzt die…, TestShadingOptOut, TestTheReportDoesNotMoveWhatItMeasures

### Community 123 - "clamp_to_bounds"
Cohesion: 0.42
Nodes (4): clamp_to_bounds(), Pull a computed moment into the configured clock window. Lets an area drive by…, datetime, TestClampHelper

### Community 124 - "test_manual_move_clears_pending_drive.py"
Cohesion: 0.29
Nodes (8): cover_calls(), _fast_startup(), _positions(), fixture, Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine spaetere…, _setup(), _shutter(), TestStalePendingDriveAfterManualMove

### Community 125 - "TestElevationCanBeSwitchedOff"
Cohesion: 0.22
Nodes (5): Beschattung allein nach Helligkeitssensor (Forum, charly166). Wer an jedem…, Ohne Sonnenhöhe gibt es nichts zu prüfen – also auch nichts zu sperren., Bestandsanlagen kennen den Schlüssel nicht – die prüfen weiter., Nur die Höhe faellt weg, die Fensterrichtung bleibt in Kraft., TestElevationCanBeSwitchedOff

### Community 126 - "TestExportReadsTheWayTheReportWasMeant"
Cohesion: 0.12
Nodes (9): deepcopy_options(), Eine Frage zu stellen darf die Antwort nicht verändern., Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus., Was MartyBrs Export offenliess, obwohl alles darin stand., Fünfstellige Lux-Schwellen an einem Sensor in W/m². Nebeneinander sehen 559,7…, Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung., „Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen., TestExport (+1 more)

### Community 128 - "_shutter"
Cohesion: 0.17
Nodes (8): parametrize, Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist., „tilted" ist kein Synonym von on/off und darf keins werden., `cover.buro`: beschattet auf 80 %, Kontakt „open" an einem binary_sensor. Beide…, heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`., _shutter(), TestBinarySensorOpenSynonyms, TestHeinziesSetup

### Community 129 - "_canonical_state"
Cohesion: 0.36
Nodes (8): _canonical_state(), _normalize_state(), Any, State of one window contact, using this shutter's configured vocabulary. Both…, Fold on/off vocabulary onto one token; leave anything else untouched. Words…, True if the dedicated tilt contact currently reports 'tilted'., _separate_tilt_active(), _single_window_state()

### Community 131 - "TestDriveCommandNote"
Cohesion: 0.39
Nodes (3): Wolfs Fall: Nachführung 50–100 % an einem Antrieb ohne Zwischenstopp., bjoerg: „an der Fahrtrichtung ändert es nichts". Aus den Positionen allein…, TestDriveCommandNote

### Community 132 - "_shutter"
Cohesion: 0.21
Nodes (4): _shutter(), TestLockProtection, TestTilt, TestWindowState

### Community 133 - "get_window_state"
Cohesion: 0.18
Nodes (8): get_window_state(), Return: "closed" | "tilted" | "open" Supports both binary_sensor and sensor…, The existing single-contact behaviour must not shift at all., While tilted, many contacts also read 'open' – tilt must win., A configured but absent tilt entity must not break detection., _shutter(), TestSeparateTiltEntity, TestSingleContactUnchanged

### Community 134 - "_awning"
Cohesion: 0.10
Nodes (15): _awning(), `close_group` an einer Markise heisst „einfahren" – ein Knopfdruck., Gegenprobe zum Filter durch den echten Scheduler. Beide Uhrzeiten liegen in der…, Der Deckel klemmt nach unten – an einer Markise die falsche Richtung., Sonst bliebe eine umgestellte Markise bei 20 % im Sturm stehen., Ein Rollladen faellt auf 100 zurueck, eine Markise auf 0., Den gemeinsamen Minutentakt ausloesen, wie Home Assistant es tut., Kein Bestand muss migriert werden. (+7 more)

### Community 135 - "const.py"
Cohesion: 0.04
Nodes (96): ConfigEntry, Brightness sensor logic - per area (brightness mode)., Set up brightness sensor listener., setup_brightness_listener(), Constants for Shutter Pilot integration., ConfigEntry, HomeAssistant, Helper functions for area-based follow-up actions (e.g. lights). (+88 more)

### Community 136 - "_frost_area"
Cohesion: 0.10
Nodes (17): _frost_area(), parametrize, Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht einen Spalt…, Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten., Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet., 0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert., Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen., Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten. (+9 more)

### Community 137 - "TestWebSocketToggle"
Cohesion: 0.40
Nodes (3): Der Schalter im Panel geht über einen eigenen Befehl, wie bei Bereichen., Ohne Administratorrechte wird der Befehl abgewiesen., TestWebSocketToggle

### Community 138 - ".test_neighbour_in_the_same_area_is_not"
Cohesion: 0.48
Nodes (3): Ein beschattetes Fenster sperrte den ganzen Bereich., cover.b steht auf seiner Beschattungsposition, ist aber frei., TestOpenBlockerIsPerCover

### Community 139 - "TestNextActionWithoutASchedule"
Cohesion: 0.47
Nodes (3): Der Sensor „naechste Fahrt" darf nichts versprechen. Das ist die eine Stelle,…, Gegenprobe: dieselben Zeiten, nur mit Modus., TestNextActionWithoutASchedule

### Community 140 - "note_manual_position"
Cohesion: 0.25
Nodes (6): note_manual_position(), Book a hand-driven end position into the up/down bookkeeping. covers_driven_up…, Eine blockierte Richtung fror bisher die andere ein. `covers_driven_down` haelt…, Dazwischen ist weder "oben" noch "unten": der Oben-Merker bleibt wie er war,…, Neu zuweisen haenge den Scheduler an ein totes Set (2.10.0)., TestManualDriveIsBooked

### Community 141 - "TestSecondCloseCondition"
Cohesion: 0.33
Nodes (3): Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos). „Der Tag war warm"…, Fail closed: ein toter Sensor darf nicht alles halb offen lassen., TestSecondCloseCondition

### Community 142 - "fixture.mjs"
Cohesion: 0.29
Nodes (5): makePanel(), render(), ok(), { p, areas, shutters }, R()

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

### Community 149 - ".test_scheduler_skips_disabled_shutter"
Cohesion: 0.40
Nodes (4): _positions(), Der wichtigste Fall: Von Hand muss er weiter fahren., Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt., TestDrivePaths

### Community 150 - "resolve_shade_position"
Cohesion: 0.09
Nodes (30): The shading position for this shutter right now, plus how it was picked. Three…, resolve_shade_position(), parametrize, Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer., TestSecondShadingPosition, _area(), calls(), _fast() (+22 more)

### Community 152 - "_local_timezone"
Cohesion: 0.67
Nodes (3): _local_timezone(), fixture, Run these tests in Berlin. The default test timezone is US/Pacific, but…

### Community 153 - "tilt_buttons.mjs"
Cohesion: 0.29
Nodes (4): calls, p, without, withTilt

### Community 154 - "TestNoUpCondition"
Cohesion: 0.39
Nodes (3): Linos: eine Bedingung, die das morgendliche Oeffnen blockiert., Die eine Richtung, in der ein Fehler nicht wehtun darf. Andersherum bliebe…, TestNoUpCondition

### Community 159 - "_ws_delete_shutter"
Cohesion: 0.11
Nodes (22): _area_registry_uids(), Delete a shutter by index., Every entity one area owns. Keep in step with switch/sensor/binary_sensor., Every entity one shutter or awning owns., Delete an area by id., _shutter_registry_uids(), _ws_delete_area(), _ws_delete_shutter() (+14 more)

## Ambiguous Edges - Review These
- `Bereich / Area` → `Panel: Rollläden (Shutters) Tab`  [AMBIGUOUS]
  docs/screenshots/shutters.png · relation: conceptually_related_to

## Knowledge Gaps
- **203 isolated node(s):** `LIT_HOSTS`, `LitElement`, `MODE_ICONS`, `WIN_OPEN_OPTS`, `WIN_TILT_OPTS` (+198 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1287 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Bereich / Area` and `Panel: Rollläden (Shutters) Tab`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Bereiche Tab Screenshot` connect `Bereichs-Karte (Area Card)` to `shutter-pilot-panel.js`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `ShutterPilotPanel` connect `ShutterPilotPanel` to `shutter-pilot-panel.js`, `._renderShutterForm`, `._entityField`, `._renderSettings`, `.t`, `._renderCondDetail`, `._coverAction`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `Area-to-Shutter Association (Rollläden count per area)` connect `Bereichs-Karte (Area Card)` to `helpers.py`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **What connects `LIT_HOSTS`, `LitElement`, `MODE_ICONS` to the rest of the system?**
  _203 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `evaluate_guard` be split into smaller, more focused modules?**
  _Cohesion score 0.056334735857877516 - nodes in this community are weakly interconnected._
- **Should `elevation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050721954831543875 - nodes in this community are weakly interconnected._