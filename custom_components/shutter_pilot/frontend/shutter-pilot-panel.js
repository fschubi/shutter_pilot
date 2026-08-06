/**
 * Shutter Pilot – Home Assistant Sidebar Panel v5
 * 11 languages · Tabs: Dashboard | Areas | Shutters
 */
/* Home Assistant liefert kein Modul, aus dem sich LitElement importieren
   liesse. Die Klasse ist nur über die Prototypenkette eines bereits
   registrierten HA-Elements erreichbar. Welche Elemente geladen sind, hängt
   davon ab, welche Seite der Browser vorher offen hatte, und wie tief
   LitElement in der Kette steckt, hängt von der Frontend-Version ab (manche
   Elemente sitzen hinter Mixins). Deshalb mehrere Kandidaten durchgehen und
   die Kette hochlaufen, bis die Klasse gefunden ist, die html und css selbst
   mitbringt. Wird nichts gefunden, darf das Panel NICHT einfach weiterlaufen:
   ohne echtes css() ist static styles ungültig, Lit wirft beim ersten Rendern
   und der Nutzer sieht nur eine weisse Seite. In dem Fall wird unten eine
   lesbare Meldung angezeigt. */
const LIT_HOSTS = ["ha-panel-lovelace","hui-masonry-view","hui-view","ha-panel-config",
  "home-assistant-main","ha-sidebar","ha-card","ha-icon","ha-textfield","ha-switch"];
const LitElement = (() => {
  const usable = c => typeof c?.prototype?.html === "function" && typeof c?.prototype?.css === "function";
  for (const name of LIT_HOSTS) {
    let cur = customElements.get(name);
    if (!usable(cur)) continue;
    // Höchste Klasse der Kette nehmen, die html und css noch kennt – das ist
    // LitElement selbst und nicht das konkrete Element oder ein Mixin.
    let best = null;
    while (usable(cur)) { best = cur; cur = Object.getPrototypeOf(cur); }
    if (best && best !== customElements.get(name)) return best;
    if (best) return Object.getPrototypeOf(best);
  }
  return null;
})();
const LIT_MISSING = !LitElement;
if (LIT_MISSING) {
  console.error("[shutter_pilot] LitElement nicht gefunden – Home-Assistant-Frontend inkompatibel oder Panel zu früh geladen.");
}
const html = LitElement?.prototype?.html ?? ((s,...v)=>s.reduce((a,b,i)=>a+v[i-1]+b));
const css  = LitElement?.prototype?.css  ?? ((s)=>s);

/* Notfall-Basisklasse: kein Lit, aber auch keine weisse Seite. */
const PanelBase = LitElement ?? class extends HTMLElement {
  connectedCallback(){
    this.innerHTML =
      '<div style="padding:24px;font-family:sans-serif;color:var(--primary-text-color,#212121);'
      + 'background:var(--card-background-color,#fff);border-radius:12px;line-height:1.5">'
      + '<h2 style="margin:0 0 8px">Shutter Pilot</h2>'
      + '<p>Das Panel konnte die Frontend-Basis von Home Assistant nicht laden.</p>'
      + '<p>Bitte zuerst ein Dashboard öffnen und dann erneut hierher wechseln, '
      + 'oder die Seite mit Strg+F5 (Mac: Cmd+Shift+R) neu laden.</p>'
      + '<p style="color:var(--secondary-text-color,#727272);font-size:13px">'
      + 'Bleibt es dabei, hilft die Fehlermeldung aus der Browser-Konsole (F12) im Issue weiter.</p>'
      + '</div>';
  }
};

const MODE_ICONS = {time:"mdi:clock-outline",brightness:"mdi:white-balance-sunny",sun:"mdi:weather-sunset"};
const WIN_OPEN_OPTS = ["on","open","true","offen"];
const WIN_TILT_OPTS = ["none","tilted","gekippt","kipp","2"];
const OVERRIDE_OPTS = ["never","daily","next_action"];
/* Kompassrichtungen als Schnellwahl für den Azimut-Bereich (Fensterrichtung) */
const COMPASS_PRESETS = [
  {key:"north", min:315, max:45},
  {key:"east",  min:45,  max:135},
  {key:"south", min:135, max:225},
  {key:"west",  min:225, max:315},
];
const REFRESH_MS = 30000;
const COND_SLOTS = ["a","b","c","d"];
const WEATHER_CONDITIONS = ["sunny","partlycloudy","cloudy","rainy","pouring",
  "snowy","snowy-rainy","fog","hail","lightning","lightning-rainy","windy",
  "windy-variant","clear-night","exceptional"];
const MONTHS = [1,2,3,4,5,6,7,8,9,10,11,12];

/* Vorfilterung je Feld. `classes` prüft device_class, `pattern` den
   Anzeigenamen samt Entity-ID. Beides nur zum Vorsortieren – nichts wird
   ausgeblendet, denn längst nicht jeder setzt eine device_class. */
const HINTS = {
  window:      {classes:["window","door","opening","garage_door"], pattern:/fenster|window|t[uü]r|door|kontakt|contact|kipp|tilt/i},
  illuminance: {classes:["illuminance"], pattern:/illumin|lux|helligkeit|brightness|einstrahl|radiation|solar|\blx\b/i},
  temperature: {classes:["temperature"], pattern:/temp|grad|celsius/i},
  workday:     {classes:[], pattern:/workday|arbeitstag|werktag|feiertag|holiday/i},
  condition:   {classes:["illuminance","temperature","irradiance","power"],
                pattern:/illumin|lux|helligkeit|brightness|einstrahl|radiation|solar|temp|\blx\b/i},
};

/* In der Home-Assistant-App für macOS (Mac Catalyst) sind native Formular-
   Popups defekt: <input type="time"> beendet die App (UIPickerView ist im
   Mac-Idiom nicht unterstützt), und <select>-Dropdowns öffnen sich gar nicht
   erst – man sieht nur die Pfeile. Auf dieser Plattform werden deshalb
   eigene Bedienelemente aus reinem HTML gerendert. iPhone, iPad, Android und
   normale Browser sind nicht betroffen und behalten die nativen Elemente.
   Erkennung: Companion-App + macOS + keine Touch-Punkte. Ein iPad meldet
   maxTouchPoints > 0 und bleibt damit bei den nativen Elementen. */
const NATIVE_PICKERS_BROKEN = (() => {
  try {
    const inApp = !!(window.webkit?.messageHandlers?.externalBus || window.externalApp);
    if (!inApp) return false;
    const plat = navigator.platform || navigator.userAgent || "";
    return /Mac/i.test(plat) && (navigator.maxTouchPoints || 0) === 0;
  } catch (_) {
    return false;
  }
})();

/* ─── i18n ─── */
const I18N = {
de:{
  f_bound_none:"keine Grenze – zum Festlegen tippen",
  f_bounds_title:"Frühestens / spätestens",
  f_bounds_hint:"Klemmt den aus dem Sonnenstand berechneten Zeitpunkt in ein Uhrzeitfenster. Beispiel: nach Sonnenstand fahren, aber nie vor 7:30 und nie nach 9:00. Leer heisst keine Grenze.",
  f_bounds_we_hint:"Wochenende – leer bedeutet, dass der Wochentagswert gilt.",
  f_earliest_up:"Hoch frühestens",
  f_latest_up:"Hoch spätestens",
  f_earliest_down:"Runter frühestens",
  f_latest_down:"Runter spätestens",
  f_we_earliest_up:"WE Hoch frühestens",
  f_we_latest_up:"WE Hoch spätestens",
  f_we_earliest_down:"WE Runter frühestens",
  f_we_latest_down:"WE Runter spätestens",
  f_shutter_cond_hint:"Eigene Bedingungen nur für dieses Fenster, etwa ein Helligkeitssensor direkt am Fenster oder die Raumtemperatur. Leer lassen heisst: die Bedingung des Bereichs gilt.",
  sec_verify:"Fahrten überprüfen",
  sec_verify_sub:"für Rollläden, die Befehle verlieren",
  f_verify_hint:"Prüft nach jeder automatischen Fahrt, ob die Position tatsächlich erreicht wurde, und wiederholt den Befehl sonst. Sinnvoll bei Funk-Rollläden, bei denen gelegentlich ein Befehl verlorengeht.",
  f_verify_enabled:"Fahrten überprüfen",
  f_verify_after:"Prüfen nach",
  f_verify_tolerance:"Erlaubte Abweichung",
  f_verify_retries:"Wiederholungen",
  f_verify_event_hint:"Schlägt es endgültig fehl, wird der gespeicherte Wert korrigiert und das Ereignis shutter_pilot_cover_failed gefeuert.",
  tab_settings:"Einstellungen",
  sec_weather:"Wetter",
  sec_weather_sub:"Grundlage für Beschattungsbedingungen",
  f_weather_entity:"Wetter-Entität",
  f_weather_hint:"Optional. Ist sie gesetzt, holt Shutter Pilot die Tagesvorhersage selbst ab und stellt daraus zwei Sensoren bereit, die du unten bei den Bedingungen auswählen kannst.",
  f_weather_sensors_hint:"Verfügbar als: Vorhersage Höchsttemperatur und Vorhersage Wetterlage.",
  w_temp_max:"Höchsttemperatur heute",
  w_condition:"Wetterlage heute",
  w_updated:"Zuletzt abgerufen",
  f_sun_cond_n:"Bedingung {n} (optional)",
  f_sun_cond_states:"Erlaubte Zustände",
  f_sun_cond_states_hint:"Beschattet wird nur, wenn der Sensor einen der ausgewählten Zustände meldet.",
  f_season:"Beschattungszeitraum",
  f_season_all:"ganzjährig",
  f_season_hint:"Nur in diesen Monaten beschatten. Zeiträume über den Jahreswechsel sind möglich, z. B. Oktober bis März.",
  sec_altclose:"Abweichendes Schliessen",
  sec_altclose_sub:"z. B. abends bei Hitze nur teilweise",
  f_close_cond:"Bedingung (optional)",
  f_close_cond_hint:"Ist diese Bedingung abends erfüllt, schliessen Rollläden mit hinterlegter Teilposition nur so weit statt ganz.",
  f_pos_closed_alt:"Abweichende Schliessposition nutzen",
  f_pos_closed_alt_val:"Teilweise geschlossen",
  f_pos_closed_alt_hint:"Greift nur, wenn im Bereich eine Schliessbedingung hinterlegt ist und diese zutrifft.",
  sec_shutter_sun:"Sonnenschutz",
  sec_shutter_sun_sub:"nur nötig bei abweichender Fensterrichtung",
  f_geo_override:"Eigene Ausrichtung für diesen Rollladen",
  f_geo_override_hint:"Normalerweise gelten die Werte des Bereichs. Aktiviere das nur, wenn dieses Fenster in eine andere Richtung zeigt als die übrigen im Bereich.",
  month_1:"Januar",
  month_2:"Februar",
  month_3:"März",
  month_4:"April",
  month_5:"Mai",
  month_6:"Juni",
  month_7:"Juli",
  month_8:"August",
  month_9:"September",
  month_10:"Oktober",
  month_11:"November",
  month_12:"Dezember",
  sec_basics:"Grunddaten",
  sec_schedule:"Zeitplan",
  sec_schedule_time:"nach Uhrzeit",
  sec_schedule_brightness:"nach Helligkeit",
  sec_schedule_sun:"nach Sonnenstand",
  sec_calendar:"Kalender & manuelle Bedienung",
  sec_sunprotect:"Sonnenschutz",
  sec_light:"Licht",
  sec_light_sub:"beim Schliessen einschalten",
  sec_shutter:"Rollladen",
  sec_areas:"Bereiche",
  sec_areas_sub:"welcher Bereich steuert hoch bzw. runter",
  sec_positions:"Positionen",
  sec_window:"Fenster & Lüftung",
  sec_window_sub:"Kontakte, Lüftungsposition, Aussperrschutz",
  sec_slats:"Lamellen",
  sec_slats_sub:"nur für Jalousien und Raffstores",
  ent_matching:"Passende",
  ent_others:"Alle weiteren",
  ent_more:"… und {n} weitere – bitte Suche verfeinern",
  clear:"Auswahl löschen",
  menu:"Menü",
  admin_only:"Konfiguration ist Administratoren vorbehalten.",
  f_shutter_auto:"Automatik aktiv",
  f_shutter_auto_hint:"Aus: Dieser Rollladen wird von keiner Automatik mehr gefahren – weder nach Zeit noch nach Helligkeit, Sonnenstand oder Fensterkontakt. Von Hand und über die Knöpfe im Dashboard fährt er weiterhin. Gedacht für einen defekten Rollladen, ohne seine Einstellungen zu verlieren.",
  dash_shutter_auto_off:"Automatik aus",
  btn_vent:"Lüften",
  f_window_tilt_sensor:"Zusätzlicher Sensor für „gekippt“ (optional)",
  f_window_tilt_sensor_hint:"Nur nötig, wenn dein Fenster zwei getrennte Entitäten hat: eine für „offen“ und eine für „gekippt“. Bei einem Kontakt mit drei Zuständen bleibt dieses Feld leer.",
  f_sun_cond_title:"Zusätzliche Bedingungen",
  f_sun_cond_hint:"Beschattet nur, wenn diese Bedingungen erfüllt sind – z. B. wirklich Sonne oder wirklich warm. Leer lassen heisst: keine Bedingung.",
  f_sun_cond_a:"Bedingung 1 (optional)",
  f_sun_cond_b:"Bedingung 2 (optional)",
  f_sun_cond_on:"Beschatten ab",
  f_sun_cond_off:"Aufheben unter",
  f_sun_cond_num_hint:"„Aufheben unter“ darf niedriger sein als „Beschatten ab“ – der Abstand verhindert Flattern bei durchziehenden Wolken. Leer = gleicher Wert.",
  f_sun_cond_bin_hint:"Binärsensor: beschattet wird, solange er „an“ ist.",
  filter_entity:"Suchen…",no_match:"Kein Treffer",
  entity_missing:"Entität nicht gefunden – sie wurde umbenannt oder ist nicht verfügbar.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Workday-Sensor (optional)",
  f_workday_hint:"Wenn gesetzt, gilt bei \"aus\" der Wochenend-Zeitplan – berücksichtigt Feiertage, Urlaub und Schichtarbeit. Ohne Sensor zählen Samstag und Sonntag.",
  f_random_offset:"Zufalls-Offset (Anwesenheitssimulation)",
  f_random_offset_hint:"Verschiebt die Fahrzeiten täglich zufällig um bis zu ± diesen Wert. 0 = aus.",
  f_manual_override:"Manuelle Position",
  f_manual_override_hint:"Wie lange eine von Hand gesetzte Position die Automatik blockiert.",
  f_override_never:"Bis zur nächsten Schließfahrt",
  f_override_daily:"Nur am selben Tag",
  f_override_next_action:"Automatik hat Vorrang",
  f_azimuth:"Nur bei passender Fensterrichtung",
  f_azimuth_hint:"Beschattet nur, wenn die Sonne wirklich vor den Fenstern steht. Ohne diese Option wird auch morgens beschattet, wenn die Sonne hinter dem Haus steht.",
  f_azimuth_preset:"Himmelsrichtung",
  f_azimuth_min:"Azimut von",
  f_azimuth_max:"Azimut bis",
  compass_north:"Nord",
  compass_east:"Ost",
  compass_south:"Süd",
  compass_west:"West",
  f_tilt:"Lamellen steuern (Jalousie/Raffstore)",
  f_tilt_hint:"Zusätzlich zur Höhe wird der Lamellenwinkel gesetzt.",
  f_tilt_unsupported:"Diese Entität meldet keine Lamellen-Unterstützung – die Einstellung wird ignoriert.",
  f_tilt_open:"Lamellen Offen",
  f_tilt_closed:"Lamellen Geschlossen",
  f_tilt_sun:"Lamellen Sonnenschutz",
  sun_prot_direction:"Fensterrichtung",
  sun_azimuth:"Sonnen-Azimut",
  sun_prot_wrong_dir:"Sonne steht nicht vor den Fenstern",
  tab_dashboard:"Dashboard",tab_areas:"Bereiche",tab_shutters:"Rollläden",
  subtitle:"{a} Bereiche, {s} Rollläden",
  loading:"Laden…",
  mode_time:"Zeit",mode_brightness:"Helligkeit",mode_sun:"Sonnenstand",
  shutter_s:"Rollladen",no_shutters:"Keine Rollläden",
  auto:"Automatik",
  btn_up:"Hoch",btn_stop:"Stop",btn_down:"Runter",btn_sun:"Sonnenschutz",
  btn_add:"hinzufügen",btn_save:"Speichern",btn_cancel:"Abbrechen",
  empty_areas:"Keine Bereiche konfiguriert. Wechsle zum Tab \"Bereiche\".",
  empty_areas_list:"Noch keine Bereiche angelegt.",
  empty_shutters_list:"Noch keine Rollläden angelegt.",
  add_area:"Bereich hinzufügen",edit_area:"Bereich bearbeiten",
  add_shutter:"Rollladen hinzufügen",edit_shutter:"Rollladen bearbeiten",
  col_name:"Name",col_id:"ID",col_mode:"Modus",col_shutters:"Rollläden",
  col_cover:"Cover-Entity",col_area_up:"Bereich Hoch",col_area_down:"Bereich Runter",col_window:"Fenster",
  f_name:"Name",f_mode:"Steuerungsmodus",
  f_drive_delay:"Verzögerung zwischen Rollläden (Sek.)",
  f_sun_protect:"Sonnenschutz aktivieren",f_elev_thresh:"Elevation-Schwellwert (°)",
  f_elev_min:"Sonnenschutz ab Elevation (°)",f_elev_max:"Sonnenschutz bis Elevation (°)",
  master_switch:"System aktiv",
  sun_prot_active:"Sonnenschutz aktiv",sun_prot_inactive:"Sonnenschutz inaktiv",
  sun_prot_range:"Elevation-Bereich",sun_prot_waiting:"Warte auf passende Sonnenhöhe",
  f_light_entity:"Lampe/Schalter bei Runter (optional)",f_light_brightness:"Lampe Helligkeit (%)",
  f_time_up:"Woche Hoch",f_time_down:"Woche Runter",
  f_time_we_up:"Wochenende Hoch",f_time_we_down:"Wochenende Runter",
  f_sunrise_off:"Offset Sonnenaufgang (Min.)",f_sunset_off:"Offset Sonnenuntergang (Min.)",
  sun_next_rise:"Nächster Sonnenaufgang",sun_next_set:"Nächster Sonnenuntergang",
  sun_trigger_up:"Hoch-Fahrt um",sun_trigger_down:"Runter-Fahrt um",
  sun_bound_earliest:"frühestens",sun_bound_latest:"spätestens",sun_jitter:"Präsenz",
  sun_elevation:"Aktuelle Elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Nur Hochfahren über diesen Bereich",
  dash_shutter_role_down:"Nur Runterfahren über diesen Bereich",
  dash_shutter_role_both:"Hoch- und Runterfahren über diesen Bereich",
  dash_current_lux:"Aktuell",
  f_brightness_sensor:"Helligkeitssensor",f_lux_up:"Lux Hoch-Schwelle",f_lux_down:"Lux Runter-Schwelle",
  f_w_up_from:"Woche Hoch ab",f_w_up_to:"Woche Hoch bis",f_w_down_from:"Woche Runter ab",f_w_down_to:"Woche Runter bis",
  f_we_up_from:"WE Hoch ab",f_we_up_to:"WE Hoch bis",f_we_down_from:"WE Runter ab",f_we_down_to:"WE Runter bis",
  f_cover:"Rollladen / Cover",f_window_sensor:"Fenster-/Türsensor (optional)",
  f_win_open:"Fenster-Status 'offen'",f_win_tilt:"Fenster-Status 'gekippt'",
  f_win_tilt_none:"Deaktiviert (kein Kipp-Status)",
  f_pos_win_open:"Position bei Fenster offen",f_pos_win_tilt:"Position bei Fenster gekippt",
  f_pos_win_tilt_2state_hint:"Bei 2-Zustands-Kontakten wird diese Position verwendet, wenn der Rollladen geschlossen ist.",
  f_lock:"Aussperrschutz (verhindert vollständiges Schließen bei offener Tür)",
  f_min_pos:"Mindest-Position wenn Tür offen",
  f_area_up:"Bereich (Hoch)",f_area_down:"Bereich (Runter)",
  f_pos_open:"Position Offen",f_pos_closed:"Position Geschlossen",f_pos_sun:"Sonnenschutz-Position",
  f_drive_after:"Nachholen wenn Fenster offen",
  f_drive_after_hint:"Wenn die Schließzeit erreicht wird aber das Fenster noch offen ist, wird die Fahrt nachgeholt sobald das Fenster geschlossen wird.",
  pick_entity:"Entität auswählen…",
  confirm_del_area:"Bereich \"{id}\" wirklich löschen?",confirm_del_shutter:"Rollladen wirklich löschen?",
},
en:{
  f_bound_none:"no limit – tap to set",
  f_bounds_title:"Earliest / latest",
  f_bounds_hint:"Clamps the moment computed from the sun position into a clock window. For example: drive by sun position, but never before 07:30 and never after 09:00. Empty means no limit.",
  f_bounds_we_hint:"Weekend – empty means the weekday value applies.",
  f_earliest_up:"Up earliest",
  f_latest_up:"Up latest",
  f_earliest_down:"Down earliest",
  f_latest_down:"Down latest",
  f_we_earliest_up:"WE up earliest",
  f_we_latest_up:"WE up latest",
  f_we_earliest_down:"WE down earliest",
  f_we_latest_down:"WE down latest",
  f_shutter_cond_hint:"Conditions just for this window, e.g. a brightness sensor right at the window or the room temperature. Leave empty to use the area's condition.",
  sec_verify:"Verify drives",
  sec_verify_sub:"for shutters that lose commands",
  f_verify_hint:"Checks after each automated drive whether the position was actually reached, and repeats the command otherwise. Useful for radio-driven shutters that occasionally drop a command.",
  f_verify_enabled:"Verify drives",
  f_verify_after:"Check after",
  f_verify_tolerance:"Allowed deviation",
  f_verify_retries:"Retries",
  f_verify_event_hint:"On final failure the stored value is corrected and the event shutter_pilot_cover_failed is fired.",
  tab_settings:"Settings",
  sec_weather:"Weather",
  sec_weather_sub:"basis for shading conditions",
  f_weather_entity:"Weather entity",
  f_weather_hint:"Optional. When set, Shutter Pilot fetches the daily forecast itself and provides two sensors you can pick in the conditions below.",
  f_weather_sensors_hint:"Available as: forecast high temperature and forecast condition.",
  w_temp_max:"High today",
  w_condition:"Condition today",
  w_updated:"Last fetched",
  f_sun_cond_n:"Condition {n} (optional)",
  f_sun_cond_states:"Allowed states",
  f_sun_cond_states_hint:"Shading only runs while the sensor reports one of the selected states.",
  f_season:"Shading season",
  f_season_all:"all year",
  f_season_hint:"Shade only during these months. Ranges may wrap across the new year, e.g. October to March.",
  sec_altclose:"Partial closing",
  sec_altclose_sub:"e.g. only part way on hot evenings",
  f_close_cond:"Condition (optional)",
  f_close_cond_hint:"When this condition holds in the evening, shutters with a partial position only close that far instead of fully.",
  f_pos_closed_alt:"Use a partial closing position",
  f_pos_closed_alt_val:"Partially closed",
  f_pos_closed_alt_hint:"Only applies when the area has a closing condition and it is met.",
  sec_shutter_sun:"Sun protection",
  sec_shutter_sun_sub:"only needed for a different window direction",
  f_geo_override:"Own orientation for this shutter",
  f_geo_override_hint:"Normally the area values apply. Enable this only if this window faces a different direction than the others in the area.",
  month_1:"January",
  month_2:"February",
  month_3:"March",
  month_4:"April",
  month_5:"May",
  month_6:"June",
  month_7:"July",
  month_8:"August",
  month_9:"September",
  month_10:"October",
  month_11:"November",
  month_12:"December",
  sec_basics:"Basics",
  sec_schedule:"Schedule",
  sec_schedule_time:"by time",
  sec_schedule_brightness:"by brightness",
  sec_schedule_sun:"by sun position",
  sec_calendar:"Calendar & manual control",
  sec_sunprotect:"Sun protection",
  sec_light:"Light",
  sec_light_sub:"turn on when closing",
  sec_shutter:"Shutter",
  sec_areas:"Areas",
  sec_areas_sub:"which area drives up and down",
  sec_positions:"Positions",
  sec_window:"Window & ventilation",
  sec_window_sub:"contacts, ventilation position, lock protection",
  sec_slats:"Slats",
  sec_slats_sub:"venetian blinds only",
  ent_matching:"Matching",
  ent_others:"All others",
  ent_more:"… and {n} more – please refine your search",
  clear:"Clear selection",
  menu:"Menu",
  admin_only:"Configuration is reserved for administrators.",
  f_shutter_auto:"Automation active",
  f_shutter_auto_hint:"Off: this shutter is no longer driven by any automation – not by time, brightness, sun position or window contact. Manual control and the dashboard buttons keep working. Meant for a defective shutter, without losing its settings.",
  dash_shutter_auto_off:"automation off",
  btn_vent:"Ventilate",
  f_window_tilt_sensor:"Extra sensor for tilted (optional)",
  f_window_tilt_sensor_hint:"Only needed if your window exposes two separate entities: one for open and one for tilted. Leave empty for a single 3-state contact.",
  f_sun_cond_title:"Extra conditions",
  f_sun_cond_hint:"Shade only while these conditions hold – e.g. real sunshine or real warmth. Leave empty for no condition.",
  f_sun_cond_a:"Condition 1 (optional)",
  f_sun_cond_b:"Condition 2 (optional)",
  f_sun_cond_on:"Shade above",
  f_sun_cond_off:"Release below",
  f_sun_cond_num_hint:"Release below may be lower than Shade above – the gap prevents flapping when clouds pass. Empty = same value.",
  f_sun_cond_bin_hint:"Binary sensor: shading runs while it is on.",
  filter_entity:"Search…",no_match:"No match",
  entity_missing:"Entity not found – it was renamed or is unavailable.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Workday sensor (optional)",
  f_workday_hint:"When set, \"off\" means the weekend schedule applies – covers public holidays, vacation and shift work. Without a sensor, Saturday and Sunday count.",
  f_random_offset:"Random offset (presence simulation)",
  f_random_offset_hint:"Shifts the scheduled times by up to ± this value, chosen once per day. 0 = off.",
  f_manual_override:"Manual position",
  f_manual_override_hint:"How long a manually set position blocks the automation.",
  f_override_never:"Until the next closing run",
  f_override_daily:"Only on the same day",
  f_override_next_action:"Automation always wins",
  f_azimuth:"Only when the sun faces the windows",
  f_azimuth_hint:"Shades only while the sun actually stands in front of the windows. Without this, shading also triggers in the morning when the sun is behind the house.",
  f_azimuth_preset:"Compass direction",
  f_azimuth_min:"Azimuth from",
  f_azimuth_max:"Azimuth to",
  compass_north:"North",
  compass_east:"East",
  compass_south:"South",
  compass_west:"West",
  f_tilt:"Control slats (venetian blind)",
  f_tilt_hint:"Sets the slat angle in addition to the height.",
  f_tilt_unsupported:"This entity reports no tilt support – the setting will be ignored.",
  f_tilt_open:"Slats Open",
  f_tilt_closed:"Slats Closed",
  f_tilt_sun:"Slats sun protection",
  sun_prot_direction:"Window direction",
  sun_azimuth:"Sun azimuth",
  sun_prot_wrong_dir:"sun is not facing the windows",
  tab_dashboard:"Dashboard",tab_areas:"Areas",tab_shutters:"Shutters",
  subtitle:"{a} areas, {s} shutters",
  loading:"Loading…",
  mode_time:"Time",mode_brightness:"Brightness",mode_sun:"Sun position",
  shutter_s:"shutter",no_shutters:"No shutters",
  auto:"Automation",
  btn_up:"Up",btn_stop:"Stop",btn_down:"Down",btn_sun:"Sun protect",
  btn_add:"Add",btn_save:"Save",btn_cancel:"Cancel",
  empty_areas:"No areas configured. Switch to the \"Areas\" tab.",
  empty_areas_list:"No areas created yet.",
  empty_shutters_list:"No shutters created yet.",
  add_area:"Add area",edit_area:"Edit area",
  add_shutter:"Add shutter",edit_shutter:"Edit shutter",
  col_name:"Name",col_id:"ID",col_mode:"Mode",col_shutters:"Shutters",
  col_cover:"Cover entity",col_area_up:"Area Up",col_area_down:"Area Down",col_window:"Window",
  f_name:"Name",f_mode:"Control mode",
  f_drive_delay:"Delay between shutters (sec.)",
  f_sun_protect:"Enable sun protection",f_elev_thresh:"Elevation threshold (°)",
  f_elev_min:"Sun protect from elevation (°)",f_elev_max:"Sun protect until elevation (°)",
  master_switch:"System active",
  sun_prot_active:"Sun protection active",sun_prot_inactive:"Sun protection inactive",
  sun_prot_range:"Elevation range",sun_prot_waiting:"Waiting for matching sun elevation",
  f_light_entity:"Light/switch on close (optional)",f_light_brightness:"Light brightness (%)",
  f_time_up:"Weekday Up",f_time_down:"Weekday Down",
  f_time_we_up:"Weekend Up",f_time_we_down:"Weekend Down",
  f_sunrise_off:"Sunrise offset (min.)",f_sunset_off:"Sunset offset (min.)",
  sun_next_rise:"Next sunrise",sun_next_set:"Next sunset",
  sun_trigger_up:"Up trigger at",sun_trigger_down:"Down trigger at",
  sun_bound_earliest:"no earlier than",sun_bound_latest:"no later than",sun_jitter:"Presence",
  sun_elevation:"Current elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Up drives only via this area",
  dash_shutter_role_down:"Down drives only via this area",
  dash_shutter_role_both:"Up and down drives via this area",
  dash_current_lux:"Current",
  f_brightness_sensor:"Brightness sensor",f_lux_up:"Lux up threshold",f_lux_down:"Lux down threshold",
  f_w_up_from:"Weekday up from",f_w_up_to:"Weekday up to",f_w_down_from:"Weekday down from",f_w_down_to:"Weekday down to",
  f_we_up_from:"Weekend up from",f_we_up_to:"Weekend up to",f_we_down_from:"Weekend down from",f_we_down_to:"Weekend down to",
  f_cover:"Shutter / Cover",f_window_sensor:"Window/door sensor (optional)",
  f_win_open:"Window state 'open'",f_win_tilt:"Window state 'tilted'",
  f_win_tilt_none:"Disabled (no tilt state)",
  f_pos_win_open:"Position when window open",f_pos_win_tilt:"Position when window tilted",
  f_pos_win_tilt_2state_hint:"For 2-state contacts, this position is used when the shutter is closed.",
  f_lock:"Lock protection (prevents full close when door is open)",
  f_min_pos:"Minimum position when door open",
  f_area_up:"Area (Up)",f_area_down:"Area (Down)",
  f_pos_open:"Position Open",f_pos_closed:"Position Closed",f_pos_sun:"Sun protection position",
  f_drive_after:"Catch up when window open",
  f_drive_after_hint:"When close time is reached but the window is still open, the drive will be executed as soon as the window is closed.",
  pick_entity:"Select entity…",
  confirm_del_area:"Really delete area \"{id}\"?",confirm_del_shutter:"Really delete shutter?",
},
fr:{
  tab_settings:"Réglages",
  f_season_all:"toute l'année",
  month_1:"Janvier",
  month_2:"Février",
  month_3:"Mars",
  month_4:"Avril",
  month_5:"Mai",
  month_6:"Juin",
  month_7:"Juillet",
  month_8:"Août",
  month_9:"Septembre",
  month_10:"Octobre",
  month_11:"Novembre",
  month_12:"Décembre",
  sec_basics:"Général",
  sec_schedule:"Horaire",
  sec_schedule_time:"par heure",
  sec_schedule_brightness:"par luminosité",
  sec_schedule_sun:"par position solaire",
  sec_calendar:"Calendrier & commande manuelle",
  sec_sunprotect:"Protection solaire",
  sec_light:"Lumière",
  sec_light_sub:"allumer à la fermeture",
  sec_shutter:"Volet",
  sec_areas:"Zones",
  sec_areas_sub:"quelle zone commande la montée et la descente",
  sec_positions:"Positions",
  sec_window:"Fenêtre & aération",
  sec_window_sub:"contacts, position d'aération, anti-enfermement",
  sec_slats:"Lames",
  sec_slats_sub:"stores vénitiens uniquement",
  ent_matching:"Correspondants",
  ent_others:"Tous les autres",
  ent_more:"… et {n} de plus – affinez la recherche",
  clear:"Effacer",
  menu:"Menu",
  admin_only:"La configuration est réservée aux administrateurs.",
  f_shutter_auto:"Automatisme actif",
  f_shutter_auto_hint:"Désactivé : ce volet n'est plus commandé par aucun automatisme – ni par l'heure, la luminosité, la position du soleil ou le contact de fenêtre. La commande manuelle et les boutons du tableau de bord restent actifs. Prévu pour un volet défectueux, sans perdre ses réglages.",
  dash_shutter_auto_off:"automatisme désactivé",
  btn_vent:"Aérer",
  f_window_tilt_sensor:"Capteur supplémentaire basculé (optionnel)",
  f_window_tilt_sensor_hint:"Nécessaire uniquement si votre fenêtre expose deux entités distinctes.",
  f_sun_cond_title:"Conditions supplémentaires",
  f_sun_cond_hint:"N'ombrage que si ces conditions sont remplies. Vide = aucune condition.",
  f_sun_cond_a:"Condition 1 (optionnel)",
  f_sun_cond_b:"Condition 2 (optionnel)",
  f_sun_cond_on:"Ombrager au-dessus de",
  f_sun_cond_off:"Lever en dessous de",
  f_sun_cond_num_hint:"L'écart entre les deux seuils évite les oscillations. Vide = même valeur.",
  f_sun_cond_bin_hint:"Capteur binaire : ombrage tant qu'il est actif.",
  filter_entity:"Rechercher…",no_match:"Aucun résultat",
  entity_missing:"Entité introuvable – renommée ou indisponible.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Capteur jour ouvré (optionnel)",
  f_workday_hint:"Si défini, \"off\" applique l'horaire du week-end – prend en compte jours fériés, congés et travail posté.",
  f_random_offset:"Décalage aléatoire (simulation de présence)",
  f_random_offset_hint:"Décale les horaires de ± cette valeur, tiré une fois par jour. 0 = désactivé.",
  f_manual_override:"Position manuelle",
  f_manual_override_hint:"Durée pendant laquelle une position manuelle bloque l'automatisme.",
  f_override_never:"Jusqu'à la prochaine fermeture",
  f_override_daily:"Seulement le même jour",
  f_override_next_action:"L'automatisme est prioritaire",
  f_azimuth:"Uniquement si le soleil fait face aux fenêtres",
  f_azimuth_hint:"N'ombrage que lorsque le soleil est réellement devant les fenêtres.",
  f_azimuth_preset:"Point cardinal",
  f_azimuth_min:"Azimut de",
  f_azimuth_max:"Azimut à",
  compass_north:"Nord",
  compass_east:"Est",
  compass_south:"Sud",
  compass_west:"Ouest",
  f_tilt:"Piloter les lames (store vénitien)",
  f_tilt_hint:"Règle l'angle des lames en plus de la hauteur.",
  f_tilt_unsupported:"Cette entité n'indique aucune prise en charge des lames – le réglage sera ignoré.",
  f_tilt_open:"Lames Ouvertes",
  f_tilt_closed:"Lames Fermées",
  f_tilt_sun:"Lames protection solaire",
  sun_prot_direction:"Orientation des fenêtres",
  sun_azimuth:"Azimut solaire",
  sun_prot_wrong_dir:"le soleil ne fait pas face aux fenêtres",
  tab_dashboard:"Tableau de bord",tab_areas:"Zones",tab_shutters:"Volets",
  subtitle:"{a} zones, {s} volets",loading:"Chargement…",
  mode_time:"Horaire",mode_brightness:"Luminosité",mode_sun:"Position solaire",
  shutter_s:"volet",no_shutters:"Aucun volet",auto:"Automatique",
  btn_up:"Monter",btn_stop:"Stop",btn_down:"Descendre",btn_sun:"Protection solaire",
  btn_add:"Ajouter",btn_save:"Enregistrer",btn_cancel:"Annuler",
  empty_areas:"Aucune zone configurée.",empty_areas_list:"Aucune zone créée.",empty_shutters_list:"Aucun volet créé.",
  add_area:"Ajouter zone",edit_area:"Modifier zone",add_shutter:"Ajouter volet",edit_shutter:"Modifier volet",
  col_name:"Nom",col_id:"ID",col_mode:"Mode",col_shutters:"Volets",
  col_cover:"Entité cover",col_area_up:"Zone Montée",col_area_down:"Zone Descente",col_window:"Fenêtre",
  f_name:"Nom",f_mode:"Mode de contrôle",f_drive_delay:"Délai entre volets (sec.)",
  f_sun_protect:"Protection solaire",f_elev_thresh:"Seuil élévation (°)",
  f_light_entity:"Lampe/interrupteur descente",f_light_brightness:"Luminosité lampe (%)",
  f_time_up:"Semaine montée",f_time_down:"Semaine descente",
  f_time_we_up:"Week-end montée",f_time_we_down:"Week-end descente",
  f_sunrise_off:"Décalage lever (min.)",f_sunset_off:"Décalage coucher (min.)",
  sun_next_rise:"Prochain lever",sun_next_set:"Prochain coucher",
  sun_trigger_up:"Montée à",sun_trigger_down:"Descente à",
  sun_bound_earliest:"au plus tôt",sun_bound_latest:"au plus tard",sun_jitter:"Présence",
  sun_elevation:"Élévation actuelle",sun_offset:"Décalage",
  dash_shutter_role_up:"Montée seulement via cette zone",
  dash_shutter_role_down:"Descente seulement via cette zone",
  dash_shutter_role_both:"Montée et descente via cette zone",
  dash_current_lux:"Actuel",
  f_brightness_sensor:"Capteur luminosité",f_lux_up:"Seuil lux montée",f_lux_down:"Seuil lux descente",
  f_w_up_from:"Sem. montée de",f_w_up_to:"Sem. montée à",f_w_down_from:"Sem. descente de",f_w_down_to:"Sem. descente à",
  f_we_up_from:"WE montée de",f_we_up_to:"WE montée à",f_we_down_from:"WE descente de",f_we_down_to:"WE descente à",
  f_cover:"Volet / Cover",f_window_sensor:"Capteur fenêtre (optionnel)",
  f_win_open:"État fenêtre 'ouverte'",f_win_tilt:"État fenêtre 'basculée'",f_win_tilt_none:"Désactivé",
  f_pos_win_open:"Position fenêtre ouverte",f_pos_win_tilt:"Position fenêtre basculée",
  f_pos_win_tilt_2state_hint:"Pour les contacts à 2 états, cette position est utilisée lorsque le volet est fermé.",
  f_lock:"Protection anti-enfermement",f_min_pos:"Position min. porte ouverte",
  f_area_up:"Zone (Montée)",f_area_down:"Zone (Descente)",
  f_pos_open:"Position Ouvert",f_pos_closed:"Position Fermé",f_pos_sun:"Position protection solaire",
  f_drive_after:"Rattraper si fenêtre ouverte",f_drive_after_hint:"La commande sera exécutée dès que la fenêtre sera fermée.",
  pick_entity:"Sélectionner…",confirm_del_area:"Supprimer la zone \"{id}\" ?",confirm_del_shutter:"Supprimer le volet ?",
},
es:{
  tab_settings:"Ajustes",
  f_season_all:"todo el año",
  month_1:"Enero",
  month_2:"Febrero",
  month_3:"Marzo",
  month_4:"Abril",
  month_5:"Mayo",
  month_6:"Junio",
  month_7:"Julio",
  month_8:"Agosto",
  month_9:"Septiembre",
  month_10:"Octubre",
  month_11:"Noviembre",
  month_12:"Diciembre",
  sec_basics:"Datos básicos",
  sec_schedule:"Horario",
  sec_schedule_time:"por hora",
  sec_schedule_brightness:"por luminosidad",
  sec_schedule_sun:"por posición solar",
  sec_calendar:"Calendario y control manual",
  sec_sunprotect:"Protección solar",
  sec_light:"Luz",
  sec_light_sub:"encender al cerrar",
  sec_shutter:"Persiana",
  sec_areas:"Zonas",
  sec_areas_sub:"qué zona controla subida y bajada",
  sec_positions:"Posiciones",
  sec_window:"Ventana y ventilación",
  sec_window_sub:"contactos, posición de ventilación, antibloqueo",
  sec_slats:"Lamas",
  sec_slats_sub:"solo persianas venecianas",
  ent_matching:"Coincidencias",
  ent_others:"Todos los demás",
  ent_more:"… y {n} más – refina la búsqueda",
  clear:"Borrar",
  menu:"Menú",
  admin_only:"La configuración está reservada a los administradores.",
  f_shutter_auto:"Automatización activa",
  f_shutter_auto_hint:"Desactivado: esta persiana ya no se mueve por ninguna automatización – ni por hora, luminosidad, posición del sol o contacto de ventana. El manejo manual y los botones del panel siguen funcionando. Pensado para una persiana averiada, sin perder su configuración.",
  dash_shutter_auto_off:"automatización desactivada",
  btn_vent:"Ventilar",
  f_window_tilt_sensor:"Sensor adicional inclinada (opcional)",
  f_window_tilt_sensor_hint:"Solo necesario si tu ventana expone dos entidades separadas.",
  f_sun_cond_title:"Condiciones adicionales",
  f_sun_cond_hint:"Sombrea solo si se cumplen estas condiciones. Vacío = sin condición.",
  f_sun_cond_a:"Condición 1 (opcional)",
  f_sun_cond_b:"Condición 2 (opcional)",
  f_sun_cond_on:"Sombrear por encima de",
  f_sun_cond_off:"Liberar por debajo de",
  f_sun_cond_num_hint:"La diferencia entre umbrales evita oscilaciones. Vacío = mismo valor.",
  f_sun_cond_bin_hint:"Sensor binario: sombrea mientras esté activo.",
  filter_entity:"Buscar…",no_match:"Sin resultados",
  entity_missing:"Entidad no encontrada: fue renombrada o no está disponible.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Sensor de día laborable (opcional)",
  f_workday_hint:"Si se define, \"off\" aplica el horario de fin de semana – cubre festivos, vacaciones y turnos.",
  f_random_offset:"Desfase aleatorio (simulación de presencia)",
  f_random_offset_hint:"Desplaza los horarios ± este valor, elegido una vez al día. 0 = desactivado.",
  f_manual_override:"Posición manual",
  f_manual_override_hint:"Cuánto tiempo una posición manual bloquea la automatización.",
  f_override_never:"Hasta el próximo cierre",
  f_override_daily:"Solo el mismo día",
  f_override_next_action:"La automatización tiene prioridad",
  f_azimuth:"Solo cuando el sol da a las ventanas",
  f_azimuth_hint:"Sombrea solo cuando el sol está realmente frente a las ventanas.",
  f_azimuth_preset:"Punto cardinal",
  f_azimuth_min:"Azimut desde",
  f_azimuth_max:"Azimut hasta",
  compass_north:"Norte",
  compass_east:"Este",
  compass_south:"Sur",
  compass_west:"Oeste",
  f_tilt:"Controlar lamas (persiana veneciana)",
  f_tilt_hint:"Ajusta el ángulo de las lamas además de la altura.",
  f_tilt_unsupported:"Esta entidad no indica compatibilidad con lamas – el ajuste se ignorará.",
  f_tilt_open:"Lamas Abiertas",
  f_tilt_closed:"Lamas Cerradas",
  f_tilt_sun:"Lamas protección solar",
  sun_prot_direction:"Orientación de ventanas",
  sun_azimuth:"Azimut solar",
  sun_prot_wrong_dir:"el sol no da a las ventanas",
  tab_dashboard:"Panel",tab_areas:"Zonas",tab_shutters:"Persianas",
  subtitle:"{a} zonas, {s} persianas",loading:"Cargando…",
  mode_time:"Horario",mode_brightness:"Brillo",mode_sun:"Posición solar",
  shutter_s:"persiana",no_shutters:"Sin persianas",auto:"Automático",
  btn_up:"Subir",btn_stop:"Parar",btn_down:"Bajar",btn_sun:"Protección solar",
  btn_add:"Añadir",btn_save:"Guardar",btn_cancel:"Cancelar",
  empty_areas:"No hay zonas configuradas.",empty_areas_list:"No hay zonas.",empty_shutters_list:"No hay persianas.",
  add_area:"Añadir zona",edit_area:"Editar zona",add_shutter:"Añadir persiana",edit_shutter:"Editar persiana",
  col_name:"Nombre",col_id:"ID",col_mode:"Modo",col_shutters:"Persianas",
  col_cover:"Entidad cover",col_area_up:"Zona Subida",col_area_down:"Zona Bajada",col_window:"Ventana",
  f_name:"Nombre",f_mode:"Modo de control",f_drive_delay:"Retraso entre persianas (seg.)",
  f_sun_protect:"Protección solar",f_elev_thresh:"Umbral elevación (°)",
  f_light_entity:"Luz/interruptor al bajar",f_light_brightness:"Brillo luz (%)",
  f_time_up:"L-V subida",f_time_down:"L-V bajada",
  f_time_we_up:"Fin de semana subida",f_time_we_down:"Fin de semana bajada",
  f_sunrise_off:"Desfase amanecer (min.)",f_sunset_off:"Desfase atardecer (min.)",
  sun_next_rise:"Próximo amanecer",sun_next_set:"Próximo atardecer",
  sun_trigger_up:"Subida a las",sun_trigger_down:"Bajada a las",
  sun_bound_earliest:"no antes de",sun_bound_latest:"no después de",sun_jitter:"Presencia",
  sun_elevation:"Elevación actual",sun_offset:"Desfase",
  dash_shutter_role_up:"Solo subida por esta zona",
  dash_shutter_role_down:"Solo bajada por esta zona",
  dash_shutter_role_both:"Subida y bajada por esta zona",
  dash_current_lux:"Actual",
  f_brightness_sensor:"Sensor brillo",f_lux_up:"Umbral lux subida",f_lux_down:"Umbral lux bajada",
  f_w_up_from:"L-V subida desde",f_w_up_to:"L-V subida hasta",f_w_down_from:"L-V bajada desde",f_w_down_to:"L-V bajada hasta",
  f_we_up_from:"Fin sem. subida desde",f_we_up_to:"Fin sem. subida hasta",f_we_down_from:"Fin sem. bajada desde",f_we_down_to:"Fin sem. bajada hasta",
  f_cover:"Persiana / Cover",f_window_sensor:"Sensor ventana (opcional)",
  f_win_open:"Estado ventana 'abierta'",f_win_tilt:"Estado ventana 'inclinada'",f_win_tilt_none:"Desactivado",
  f_pos_win_open:"Posición ventana abierta",f_pos_win_tilt:"Posición ventana inclinada",
  f_pos_win_tilt_2state_hint:"Para contactos de 2 estados, esta posición se usa cuando la persiana está cerrada.",
  f_lock:"Protección anti-bloqueo",f_min_pos:"Posición mín. puerta abierta",
  f_area_up:"Zona (Subida)",f_area_down:"Zona (Bajada)",
  f_pos_open:"Posición Abierta",f_pos_closed:"Posición Cerrada",f_pos_sun:"Posición protección solar",
  f_drive_after:"Recuperar si ventana abierta",f_drive_after_hint:"Se ejecutará cuando la ventana se cierre.",
  pick_entity:"Seleccionar…",confirm_del_area:"¿Eliminar zona \"{id}\"?",confirm_del_shutter:"¿Eliminar persiana?",
},
it:{
  tab_settings:"Impostazioni",
  f_season_all:"tutto l'anno",
  month_1:"Gennaio",
  month_2:"Febbraio",
  month_3:"Marzo",
  month_4:"Aprile",
  month_5:"Maggio",
  month_6:"Giugno",
  month_7:"Luglio",
  month_8:"Agosto",
  month_9:"Settembre",
  month_10:"Ottobre",
  month_11:"Novembre",
  month_12:"Dicembre",
  sec_basics:"Dati di base",
  sec_schedule:"Orario",
  sec_schedule_time:"per orario",
  sec_schedule_brightness:"per luminosità",
  sec_schedule_sun:"per posizione solare",
  sec_calendar:"Calendario e comando manuale",
  sec_sunprotect:"Protezione solare",
  sec_light:"Luce",
  sec_light_sub:"accendi alla chiusura",
  sec_shutter:"Tapparella",
  sec_areas:"Zone",
  sec_areas_sub:"quale zona comanda salita e discesa",
  sec_positions:"Posizioni",
  sec_window:"Finestra e aerazione",
  sec_window_sub:"contatti, posizione di aerazione, antichiusura",
  sec_slats:"Lamelle",
  sec_slats_sub:"solo veneziane",
  ent_matching:"Corrispondenti",
  ent_others:"Tutti gli altri",
  ent_more:"… e altri {n} – affina la ricerca",
  clear:"Cancella",
  menu:"Menu",
  admin_only:"La configurazione è riservata agli amministratori.",
  f_shutter_auto:"Automazione attiva",
  f_shutter_auto_hint:"Disattivata: questa tapparella non viene più mossa da alcuna automazione – né per orario, luminosità, posizione del sole o contatto finestra. Il comando manuale e i pulsanti della dashboard restano attivi. Pensato per una tapparella guasta, senza perderne le impostazioni.",
  dash_shutter_auto_off:"automazione disattivata",
  btn_vent:"Aerare",
  f_window_tilt_sensor:"Sensore aggiuntivo ribaltata (opzionale)",
  f_window_tilt_sensor_hint:"Serve solo se la finestra espone due entità separate.",
  f_sun_cond_title:"Condizioni aggiuntive",
  f_sun_cond_hint:"Ombreggia solo se queste condizioni sono soddisfatte. Vuoto = nessuna condizione.",
  f_sun_cond_a:"Condizione 1 (opzionale)",
  f_sun_cond_b:"Condizione 2 (opzionale)",
  f_sun_cond_on:"Ombreggia sopra",
  f_sun_cond_off:"Rilascia sotto",
  f_sun_cond_num_hint:"Il divario tra le soglie evita oscillazioni. Vuoto = stesso valore.",
  f_sun_cond_bin_hint:"Sensore binario: ombreggia finché è attivo.",
  filter_entity:"Cerca…",no_match:"Nessun risultato",
  entity_missing:"Entità non trovata: rinominata o non disponibile.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Sensore giorno feriale (opzionale)",
  f_workday_hint:"Se impostato, \"off\" applica l'orario del fine settimana – copre festivi, ferie e turni.",
  f_random_offset:"Scarto casuale (simulazione di presenza)",
  f_random_offset_hint:"Sposta gli orari di ± questo valore, scelto una volta al giorno. 0 = disattivato.",
  f_manual_override:"Posizione manuale",
  f_manual_override_hint:"Per quanto tempo una posizione manuale blocca l'automazione.",
  f_override_never:"Fino alla prossima chiusura",
  f_override_daily:"Solo lo stesso giorno",
  f_override_next_action:"L'automazione ha la priorità",
  f_azimuth:"Solo quando il sole è di fronte alle finestre",
  f_azimuth_hint:"Ombreggia solo quando il sole è realmente davanti alle finestre.",
  f_azimuth_preset:"Punto cardinale",
  f_azimuth_min:"Azimut da",
  f_azimuth_max:"Azimut a",
  compass_north:"Nord",
  compass_east:"Est",
  compass_south:"Sud",
  compass_west:"Ovest",
  f_tilt:"Controllo lamelle (veneziana)",
  f_tilt_hint:"Imposta l'angolo delle lamelle oltre all'altezza.",
  f_tilt_unsupported:"Questa entità non segnala supporto per le lamelle – l'impostazione sarà ignorata.",
  f_tilt_open:"Lamelle Aperte",
  f_tilt_closed:"Lamelle Chiuse",
  f_tilt_sun:"Lamelle protezione solare",
  sun_prot_direction:"Orientamento finestre",
  sun_azimuth:"Azimut solare",
  sun_prot_wrong_dir:"il sole non è di fronte alle finestre",
  tab_dashboard:"Pannello",tab_areas:"Zone",tab_shutters:"Tapparelle",
  subtitle:"{a} zone, {s} tapparelle",loading:"Caricamento…",
  mode_time:"Orario",mode_brightness:"Luminosità",mode_sun:"Posizione solare",
  shutter_s:"tapparella",no_shutters:"Nessuna tapparella",auto:"Automatico",
  btn_up:"Su",btn_stop:"Stop",btn_down:"Giù",btn_sun:"Protezione solare",
  btn_add:"Aggiungi",btn_save:"Salva",btn_cancel:"Annulla",
  empty_areas:"Nessuna zona configurata.",empty_areas_list:"Nessuna zona creata.",empty_shutters_list:"Nessuna tapparella.",
  add_area:"Aggiungi zona",edit_area:"Modifica zona",add_shutter:"Aggiungi tapparella",edit_shutter:"Modifica tapparella",
  col_name:"Nome",col_id:"ID",col_mode:"Modalità",col_shutters:"Tapparelle",
  col_cover:"Entità cover",col_area_up:"Zona Su",col_area_down:"Zona Giù",col_window:"Finestra",
  f_name:"Nome",f_mode:"Modalità",f_drive_delay:"Ritardo tra tapparelle (sec.)",
  f_sun_protect:"Protezione solare",f_elev_thresh:"Soglia elevazione (°)",
  f_light_entity:"Luce/interruttore alla chiusura",f_light_brightness:"Luminosità luce (%)",
  f_time_up:"Feriale apertura",f_time_down:"Feriale chiusura",
  f_time_we_up:"Weekend apertura",f_time_we_down:"Weekend chiusura",
  f_sunrise_off:"Offset alba (min.)",f_sunset_off:"Offset tramonto (min.)",
  sun_next_rise:"Prossima alba",sun_next_set:"Prossimo tramonto",
  sun_trigger_up:"Apertura alle",sun_trigger_down:"Chiusura alle",
  sun_bound_earliest:"non prima delle",sun_bound_latest:"non oltre le",sun_jitter:"Presenza",
  sun_elevation:"Elevazione attuale",sun_offset:"Offset",
  dash_shutter_role_up:"Solo apertura da questa zona",
  dash_shutter_role_down:"Solo chiusura da questa zona",
  dash_shutter_role_both:"Apertura e chiusura da questa zona",
  dash_current_lux:"Attuale",
  f_brightness_sensor:"Sensore luminosità",f_lux_up:"Soglia lux apertura",f_lux_down:"Soglia lux chiusura",
  f_w_up_from:"Feriale su da",f_w_up_to:"Feriale su a",f_w_down_from:"Feriale giù da",f_w_down_to:"Feriale giù a",
  f_we_up_from:"Weekend su da",f_we_up_to:"Weekend su a",f_we_down_from:"Weekend giù da",f_we_down_to:"Weekend giù a",
  f_cover:"Tapparella / Cover",f_window_sensor:"Sensore finestra (opzionale)",
  f_win_open:"Stato finestra 'aperta'",f_win_tilt:"Stato finestra 'ribaltata'",f_win_tilt_none:"Disattivato",
  f_pos_win_open:"Posizione finestra aperta",f_pos_win_tilt:"Posizione finestra ribaltata",
  f_pos_win_tilt_2state_hint:"Per contatti a 2 stati, questa posizione viene usata quando la tapparella è chiusa.",
  f_lock:"Protezione anti-blocco",f_min_pos:"Posizione min. porta aperta",
  f_area_up:"Zona (Su)",f_area_down:"Zona (Giù)",
  f_pos_open:"Posizione Aperta",f_pos_closed:"Posizione Chiusa",f_pos_sun:"Posizione protezione solare",
  f_drive_after:"Recupera se finestra aperta",f_drive_after_hint:"Verrà eseguito alla chiusura della finestra.",
  pick_entity:"Seleziona…",confirm_del_area:"Eliminare zona \"{id}\"?",confirm_del_shutter:"Eliminare tapparella?",
},
nl:{
  tab_settings:"Instellingen",
  f_season_all:"hele jaar",
  month_1:"Januari",
  month_2:"Februari",
  month_3:"Maart",
  month_4:"April",
  month_5:"Mei",
  month_6:"Juni",
  month_7:"Juli",
  month_8:"Augustus",
  month_9:"September",
  month_10:"Oktober",
  month_11:"November",
  month_12:"December",
  sec_basics:"Basisgegevens",
  sec_schedule:"Schema",
  sec_schedule_time:"op tijd",
  sec_schedule_brightness:"op helderheid",
  sec_schedule_sun:"op zonnestand",
  sec_calendar:"Kalender & handbediening",
  sec_sunprotect:"Zonwering",
  sec_light:"Licht",
  sec_light_sub:"inschakelen bij sluiten",
  sec_shutter:"Rolluik",
  sec_areas:"Zones",
  sec_areas_sub:"welke zone stuurt omhoog en omlaag",
  sec_positions:"Posities",
  sec_window:"Raam & ventilatie",
  sec_window_sub:"contacten, ventilatiestand, uitsluitbeveiliging",
  sec_slats:"Lamellen",
  sec_slats_sub:"alleen jaloezieën",
  ent_matching:"Passend",
  ent_others:"Alle overige",
  ent_more:"… en nog {n} – verfijn de zoekopdracht",
  clear:"Wissen",
  menu:"Menu",
  admin_only:"Configuratie is voorbehouden aan beheerders.",
  f_shutter_auto:"Automatisering actief",
  f_shutter_auto_hint:"Uit: dit rolluik wordt door geen enkele automatisering meer bediend – niet op tijd, lichtsterkte, zonnestand of raamcontact. Handmatig en via de knoppen op het dashboard blijft het werken. Bedoeld voor een defect rolluik, zonder de instellingen te verliezen.",
  dash_shutter_auto_off:"automatisering uit",
  btn_vent:"Ventileren",
  f_window_tilt_sensor:"Extra sensor voor gekanteld (optioneel)",
  f_window_tilt_sensor_hint:"Alleen nodig als je raam twee aparte entiteiten heeft.",
  f_sun_cond_title:"Extra voorwaarden",
  f_sun_cond_hint:"Beschaduwt alleen als aan deze voorwaarden is voldaan. Leeg = geen voorwaarde.",
  f_sun_cond_a:"Voorwaarde 1 (optioneel)",
  f_sun_cond_b:"Voorwaarde 2 (optioneel)",
  f_sun_cond_on:"Beschaduwen boven",
  f_sun_cond_off:"Opheffen onder",
  f_sun_cond_num_hint:"Het verschil tussen de drempels voorkomt pendelen. Leeg = zelfde waarde.",
  f_sun_cond_bin_hint:"Binaire sensor: beschaduwt zolang deze aan is.",
  filter_entity:"Zoeken…",no_match:"Geen resultaat",
  entity_missing:"Entiteit niet gevonden – hernoemd of niet beschikbaar.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Werkdag-sensor (optioneel)",
  f_workday_hint:"Indien ingesteld geldt bij \"uit\" het weekendschema – houdt rekening met feestdagen, vakantie en ploegendienst.",
  f_random_offset:"Willekeurige afwijking (aanwezigheidssimulatie)",
  f_random_offset_hint:"Verschuift de tijden met ± deze waarde, één keer per dag gekozen. 0 = uit.",
  f_manual_override:"Handmatige positie",
  f_manual_override_hint:"Hoe lang een handmatig ingestelde positie de automatisering blokkeert.",
  f_override_never:"Tot de volgende sluitbeweging",
  f_override_daily:"Alleen op dezelfde dag",
  f_override_next_action:"Automatisering gaat voor",
  f_azimuth:"Alleen als de zon op de ramen staat",
  f_azimuth_hint:"Beschaduwt alleen wanneer de zon daadwerkelijk voor de ramen staat.",
  f_azimuth_preset:"Windrichting",
  f_azimuth_min:"Azimut van",
  f_azimuth_max:"Azimut tot",
  compass_north:"Noord",
  compass_east:"Oost",
  compass_south:"Zuid",
  compass_west:"West",
  f_tilt:"Lamellen aansturen (jaloezie)",
  f_tilt_hint:"Stelt naast de hoogte ook de lamelhoek in.",
  f_tilt_unsupported:"Deze entiteit meldt geen lamelondersteuning – de instelling wordt genegeerd.",
  f_tilt_open:"Lamellen Open",
  f_tilt_closed:"Lamellen Dicht",
  f_tilt_sun:"Lamellen zonwering",
  sun_prot_direction:"Raamrichting",
  sun_azimuth:"Zon-azimut",
  sun_prot_wrong_dir:"zon staat niet op de ramen",
  tab_dashboard:"Dashboard",tab_areas:"Zones",tab_shutters:"Rolluiken",
  subtitle:"{a} zones, {s} rolluiken",loading:"Laden…",
  mode_time:"Tijd",mode_brightness:"Helderheid",mode_sun:"Zonnestand",
  shutter_s:"rolluik",no_shutters:"Geen rolluiken",auto:"Automatisch",
  btn_up:"Omhoog",btn_stop:"Stop",btn_down:"Omlaag",btn_sun:"Zonwering",
  btn_add:"Toevoegen",btn_save:"Opslaan",btn_cancel:"Annuleren",
  empty_areas:"Geen zones geconfigureerd. Ga naar het tabblad \"Zones\".",
  empty_areas_list:"Nog geen zones aangemaakt.",empty_shutters_list:"Nog geen rolluiken aangemaakt.",
  add_area:"Zone toevoegen",edit_area:"Zone bewerken",add_shutter:"Rolluik toevoegen",edit_shutter:"Rolluik bewerken",
  col_name:"Naam",col_id:"ID",col_mode:"Modus",col_shutters:"Rolluiken",
  col_cover:"Cover-entiteit",col_area_up:"Zone Omhoog",col_area_down:"Zone Omlaag",col_window:"Raam",
  f_name:"Naam",f_mode:"Besturingsmodus",f_drive_delay:"Vertraging tussen rolluiken (sec.)",
  f_sun_protect:"Zonwering inschakelen",f_elev_thresh:"Elevatiedrempel (°)",
  f_light_entity:"Lamp/schakelaar bij sluiten (optioneel)",f_light_brightness:"Lamp helderheid (%)",
  f_time_up:"Doordeweeks omhoog",f_time_down:"Doordeweeks omlaag",
  f_time_we_up:"Weekend omhoog",f_time_we_down:"Weekend omlaag",
  f_sunrise_off:"Offset zonsopgang (min.)",f_sunset_off:"Offset zonsondergang (min.)",
  sun_next_rise:"Volgende zonsopgang",sun_next_set:"Volgende zonsondergang",
  sun_trigger_up:"Omhoog om",sun_trigger_down:"Omlaag om",
  sun_bound_earliest:"niet vóór",sun_bound_latest:"niet later dan",sun_jitter:"Aanwezigheid",
  sun_elevation:"Huidige elevatie",sun_offset:"Offset",
  dash_shutter_role_up:"Alleen omhoog via deze zone",
  dash_shutter_role_down:"Alleen omlaag via deze zone",
  dash_shutter_role_both:"Omhoog en omlaag via deze zone",
  dash_current_lux:"Huidig",
  f_brightness_sensor:"Helderheidssensor",f_lux_up:"Lux omhoog drempel",f_lux_down:"Lux omlaag drempel",
  f_w_up_from:"Doordeweeks omhoog van",f_w_up_to:"Doordeweeks omhoog tot",f_w_down_from:"Doordeweeks omlaag van",f_w_down_to:"Doordeweeks omlaag tot",
  f_we_up_from:"Weekend omhoog van",f_we_up_to:"Weekend omhoog tot",f_we_down_from:"Weekend omlaag van",f_we_down_to:"Weekend omlaag tot",
  f_cover:"Rolluik / Cover",f_window_sensor:"Raam-/deursensor (optioneel)",
  f_win_open:"Raamstatus 'open'",f_win_tilt:"Raamstatus 'gekanteld'",f_win_tilt_none:"Uitgeschakeld (geen kantelstatus)",
  f_pos_win_open:"Positie bij raam open",f_pos_win_tilt:"Positie bij raam gekanteld",
  f_pos_win_tilt_2state_hint:"Bij 2-stands contacten wordt deze positie gebruikt wanneer het rolluik gesloten is.",
  f_lock:"Buitensluitbeveiliging (voorkomt volledig sluiten bij open deur)",f_min_pos:"Minimumpositie bij open deur",
  f_area_up:"Zone (Omhoog)",f_area_down:"Zone (Omlaag)",
  f_pos_open:"Positie Open",f_pos_closed:"Positie Gesloten",f_pos_sun:"Zonweringpositie",
  f_drive_after:"Inhalen als raam open",f_drive_after_hint:"Als de sluitingstijd bereikt wordt maar het raam nog open is, wordt de actie uitgevoerd zodra het raam gesloten wordt.",
  pick_entity:"Entiteit selecteren…",confirm_del_area:"Zone \"{id}\" echt verwijderen?",confirm_del_shutter:"Rolluik echt verwijderen?",
},
da:{
  tab_settings:"Indstillinger",
  f_season_all:"hele året",
  month_1:"Januar",
  month_2:"Februar",
  month_3:"Marts",
  month_4:"April",
  month_5:"Maj",
  month_6:"Juni",
  month_7:"Juli",
  month_8:"August",
  month_9:"September",
  month_10:"Oktober",
  month_11:"November",
  month_12:"December",
  sec_basics:"Grunddata",
  sec_schedule:"Tidsplan",
  sec_schedule_time:"efter tid",
  sec_schedule_brightness:"efter lysstyrke",
  sec_schedule_sun:"efter solposition",
  sec_calendar:"Kalender & manuel betjening",
  sec_sunprotect:"Solafskærmning",
  sec_light:"Lys",
  sec_light_sub:"tænd ved lukning",
  sec_shutter:"Persienne",
  sec_areas:"Områder",
  sec_areas_sub:"hvilket område styrer op og ned",
  sec_positions:"Positioner",
  sec_window:"Vindue & udluftning",
  sec_window_sub:"kontakter, udluftningsposition, låsesikring",
  sec_slats:"Lameller",
  sec_slats_sub:"kun persienner",
  ent_matching:"Matchende",
  ent_others:"Alle øvrige",
  ent_more:"… og {n} mere – forfin søgningen",
  clear:"Ryd",
  menu:"Menu",
  admin_only:"Konfiguration er forbeholdt administratorer.",
  f_shutter_auto:"Automatik aktiv",
  f_shutter_auto_hint:"Fra: denne rullejalousi køres ikke længere af nogen automatik – hverken efter tid, lysstyrke, solens position eller vindueskontakt. Manuelt og via knapperne på dashboardet kører den fortsat. Beregnet til en defekt rullejalousi, uden at miste indstillingerne.",
  dash_shutter_auto_off:"automatik fra",
  btn_vent:"Udluft",
  f_window_tilt_sensor:"Ekstra sensor for vippet (valgfri)",
  f_window_tilt_sensor_hint:"Kun nødvendigt hvis dit vindue har to separate enheder.",
  f_sun_cond_title:"Ekstra betingelser",
  f_sun_cond_hint:"Skygger kun når disse betingelser er opfyldt. Tom = ingen betingelse.",
  f_sun_cond_a:"Betingelse 1 (valgfri)",
  f_sun_cond_b:"Betingelse 2 (valgfri)",
  f_sun_cond_on:"Skyg over",
  f_sun_cond_off:"Ophæv under",
  f_sun_cond_num_hint:"Afstanden mellem tærsklerne forhindrer svingninger. Tom = samme værdi.",
  f_sun_cond_bin_hint:"Binær sensor: skygger så længe den er aktiv.",
  filter_entity:"Søg…",no_match:"Ingen træffer",
  entity_missing:"Enhed ikke fundet – omdøbt eller utilgængelig.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Arbejdsdag-sensor (valgfri)",
  f_workday_hint:"Når den er sat, betyder \"fra\" at weekendplanen gælder – dækker helligdage, ferie og skifteholdsarbejde.",
  f_random_offset:"Tilfældig forskydning (tilstedeværelsessimulering)",
  f_random_offset_hint:"Forskyder tiderne med ± denne værdi, valgt én gang om dagen. 0 = fra.",
  f_manual_override:"Manuel position",
  f_manual_override_hint:"Hvor længe en manuelt sat position blokerer automatikken.",
  f_override_never:"Indtil næste lukning",
  f_override_daily:"Kun samme dag",
  f_override_next_action:"Automatikken har forrang",
  f_azimuth:"Kun når solen står mod vinduerne",
  f_azimuth_hint:"Skygger kun, når solen faktisk står foran vinduerne.",
  f_azimuth_preset:"Verdenshjørne",
  f_azimuth_min:"Azimut fra",
  f_azimuth_max:"Azimut til",
  compass_north:"Nord",
  compass_east:"Øst",
  compass_south:"Syd",
  compass_west:"Vest",
  f_tilt:"Styr lameller (persienne)",
  f_tilt_hint:"Indstiller lamelvinklen ud over højden.",
  f_tilt_unsupported:"Denne enhed melder ingen lamelunderstøttelse – indstillingen ignoreres.",
  f_tilt_open:"Lameller Åbne",
  f_tilt_closed:"Lameller Lukkede",
  f_tilt_sun:"Lameller solafskærmning",
  sun_prot_direction:"Vinduesretning",
  sun_azimuth:"Sol-azimut",
  sun_prot_wrong_dir:"solen står ikke mod vinduerne",
  tab_dashboard:"Dashboard",tab_areas:"Områder",tab_shutters:"Persienner",
  subtitle:"{a} områder, {s} persienner",loading:"Indlæser…",
  mode_time:"Tid",mode_brightness:"Lysstyrke",mode_sun:"Solposition",
  shutter_s:"persienne",no_shutters:"Ingen persienner",auto:"Automatik",
  btn_up:"Op",btn_stop:"Stop",btn_down:"Ned",btn_sun:"Solbeskyttelse",
  btn_add:"Tilføj",btn_save:"Gem",btn_cancel:"Annuller",
  empty_areas:"Ingen områder konfigureret. Skift til fanen \"Områder\".",
  empty_areas_list:"Ingen områder oprettet endnu.",empty_shutters_list:"Ingen persienner oprettet endnu.",
  add_area:"Tilføj område",edit_area:"Rediger område",add_shutter:"Tilføj persienne",edit_shutter:"Rediger persienne",
  col_name:"Navn",col_id:"ID",col_mode:"Tilstand",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Op",col_area_down:"Område Ned",col_window:"Vindue",
  f_name:"Navn",f_mode:"Styringstilstand",f_drive_delay:"Forsinkelse mellem persienner (sek.)",
  f_sun_protect:"Aktivér solbeskyttelse",f_elev_thresh:"Elevationstærskel (°)",
  f_light_entity:"Lampe/kontakt ved lukning (valgfrit)",f_light_brightness:"Lampe lysstyrke (%)",
  f_time_up:"Hverdag op",f_time_down:"Hverdag ned",
  f_time_we_up:"Weekend op",f_time_we_down:"Weekend ned",
  f_sunrise_off:"Solopgang offset (min.)",f_sunset_off:"Solnedgang offset (min.)",
  sun_next_rise:"Næste solopgang",sun_next_set:"Næste solnedgang",
  sun_trigger_up:"Op kl.",sun_trigger_down:"Ned kl.",
  sun_bound_earliest:"tidligst",sun_bound_latest:"senest",sun_jitter:"Tilstedeværelse",
  sun_elevation:"Aktuel elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Kun op via dette område",
  dash_shutter_role_down:"Kun ned via dette område",
  dash_shutter_role_both:"Op og ned via dette område",
  dash_current_lux:"Aktuel",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux op-tærskel",f_lux_down:"Lux ned-tærskel",
  f_w_up_from:"Hverdag op fra",f_w_up_to:"Hverdag op til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Weekend op fra",f_we_up_to:"Weekend op til",f_we_down_from:"Weekend ned fra",f_we_down_to:"Weekend ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vinduessensor (valgfrit)",
  f_win_open:"Vinduestilstand 'åben'",f_win_tilt:"Vinduestilstand 'vippet'",f_win_tilt_none:"Deaktiveret",
  f_pos_win_open:"Position ved åbent vindue",f_pos_win_tilt:"Position ved vippet vindue",
  f_pos_win_tilt_2state_hint:"For 2-tilstands kontakter bruges denne position, når rullegardinet er lukket.",
  f_lock:"Låsebeskyttelse",f_min_pos:"Minimumposition ved åben dør",
  f_area_up:"Område (Op)",f_area_down:"Område (Ned)",
  f_pos_open:"Position Åben",f_pos_closed:"Position Lukket",f_pos_sun:"Solbeskyttelsesposition",
  f_drive_after:"Indhent hvis vindue åbent",f_drive_after_hint:"Handlingen udføres, så snart vinduet lukkes.",
  pick_entity:"Vælg entitet…",confirm_del_area:"Slet område \"{id}\"?",confirm_del_shutter:"Slet persienne?",
},
sv:{
  tab_settings:"Inställningar",
  f_season_all:"hela året",
  month_1:"Januari",
  month_2:"Februari",
  month_3:"Mars",
  month_4:"April",
  month_5:"Maj",
  month_6:"Juni",
  month_7:"Juli",
  month_8:"Augusti",
  month_9:"September",
  month_10:"Oktober",
  month_11:"November",
  month_12:"December",
  sec_basics:"Grunduppgifter",
  sec_schedule:"Schema",
  sec_schedule_time:"efter tid",
  sec_schedule_brightness:"efter ljusstyrka",
  sec_schedule_sun:"efter solposition",
  sec_calendar:"Kalender & manuell styrning",
  sec_sunprotect:"Solskydd",
  sec_light:"Ljus",
  sec_light_sub:"tänd vid stängning",
  sec_shutter:"Persienn",
  sec_areas:"Områden",
  sec_areas_sub:"vilket område styr upp och ner",
  sec_positions:"Positioner",
  sec_window:"Fönster & vädring",
  sec_window_sub:"kontakter, vädringsläge, utelåsningsskydd",
  sec_slats:"Lameller",
  sec_slats_sub:"endast persienner",
  ent_matching:"Matchande",
  ent_others:"Alla övriga",
  ent_more:"… och {n} till – förfina sökningen",
  clear:"Rensa",
  menu:"Meny",
  admin_only:"Konfiguration är förbehållen administratörer.",
  f_shutter_auto:"Automatik aktiv",
  f_shutter_auto_hint:"Av: denna persienn styrs inte längre av någon automatik – varken efter tid, ljusstyrka, solens läge eller fönsterkontakt. Manuellt och via knapparna på instrumentpanelen fungerar den fortfarande. Avsedd för en trasig persienn, utan att förlora inställningarna.",
  dash_shutter_auto_off:"automatik av",
  btn_vent:"Vädra",
  f_window_tilt_sensor:"Extra sensor för vädringsläge (valfri)",
  f_window_tilt_sensor_hint:"Behövs bara om fönstret har två separata entiteter.",
  f_sun_cond_title:"Ytterligare villkor",
  f_sun_cond_hint:"Skuggar bara när dessa villkor är uppfyllda. Tomt = inget villkor.",
  f_sun_cond_a:"Villkor 1 (valfritt)",
  f_sun_cond_b:"Villkor 2 (valfritt)",
  f_sun_cond_on:"Skugga över",
  f_sun_cond_off:"Släpp under",
  f_sun_cond_num_hint:"Avståndet mellan trösklarna förhindrar pendling. Tomt = samma värde.",
  f_sun_cond_bin_hint:"Binär sensor: skuggar så länge den är aktiv.",
  filter_entity:"Sök…",no_match:"Ingen träff",
  entity_missing:"Entiteten hittades inte – omdöpt eller otillgänglig.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Arbetsdagssensor (valfri)",
  f_workday_hint:"När den är satt betyder \"av\" att helgschemat gäller – täcker helgdagar, semester och skiftarbete.",
  f_random_offset:"Slumpmässig förskjutning (närvarosimulering)",
  f_random_offset_hint:"Förskjuter tiderna med ± detta värde, valt en gång per dag. 0 = av.",
  f_manual_override:"Manuellt läge",
  f_manual_override_hint:"Hur länge ett manuellt satt läge blockerar automatiken.",
  f_override_never:"Till nästa stängning",
  f_override_daily:"Endast samma dag",
  f_override_next_action:"Automatiken har företräde",
  f_azimuth:"Endast när solen står mot fönstren",
  f_azimuth_hint:"Skuggar bara när solen faktiskt står framför fönstren.",
  f_azimuth_preset:"Väderstreck",
  f_azimuth_min:"Azimut från",
  f_azimuth_max:"Azimut till",
  compass_north:"Norr",
  compass_east:"Öst",
  compass_south:"Syd",
  compass_west:"Väst",
  f_tilt:"Styr lameller (persienn)",
  f_tilt_hint:"Ställer in lamellvinkeln utöver höjden.",
  f_tilt_unsupported:"Den här entiteten rapporterar inget lamellstöd – inställningen ignoreras.",
  f_tilt_open:"Lameller Öppna",
  f_tilt_closed:"Lameller Stängda",
  f_tilt_sun:"Lameller solskydd",
  sun_prot_direction:"Fönsterriktning",
  sun_azimuth:"Sol-azimut",
  sun_prot_wrong_dir:"solen står inte mot fönstren",
  tab_dashboard:"Dashboard",tab_areas:"Områden",tab_shutters:"Persienner",
  subtitle:"{a} områden, {s} persienner",loading:"Laddar…",
  mode_time:"Tid",mode_brightness:"Ljusstyrka",mode_sun:"Solposition",
  shutter_s:"persienn",no_shutters:"Inga persienner",auto:"Automatik",
  btn_up:"Upp",btn_stop:"Stopp",btn_down:"Ner",btn_sun:"Solskydd",
  btn_add:"Lägg till",btn_save:"Spara",btn_cancel:"Avbryt",
  empty_areas:"Inga områden konfigurerade. Byt till fliken \"Områden\".",
  empty_areas_list:"Inga områden skapade ännu.",empty_shutters_list:"Inga persienner skapade ännu.",
  add_area:"Lägg till område",edit_area:"Redigera område",add_shutter:"Lägg till persienn",edit_shutter:"Redigera persienn",
  col_name:"Namn",col_id:"ID",col_mode:"Läge",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Upp",col_area_down:"Område Ner",col_window:"Fönster",
  f_name:"Namn",f_mode:"Styrläge",f_drive_delay:"Fördröjning mellan persienner (sek.)",
  f_sun_protect:"Aktivera solskydd",f_elev_thresh:"Elevationströskel (°)",
  f_light_entity:"Lampa/kontakt vid stängning (valfritt)",f_light_brightness:"Lampa ljusstyrka (%)",
  f_time_up:"Vardag upp",f_time_down:"Vardag ner",
  f_time_we_up:"Helg upp",f_time_we_down:"Helg ner",
  f_sunrise_off:"Soluppgång offset (min.)",f_sunset_off:"Solnedgång offset (min.)",
  sun_next_rise:"Nästa soluppgång",sun_next_set:"Nästa solnedgång",
  sun_trigger_up:"Upp kl.",sun_trigger_down:"Ner kl.",
  sun_bound_earliest:"tidigast",sun_bound_latest:"senast",sun_jitter:"Närvaro",
  sun_elevation:"Aktuell elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Endast upp via detta område",
  dash_shutter_role_down:"Endast ner via detta område",
  dash_shutter_role_both:"Upp och ner via detta område",
  dash_current_lux:"Aktuell",
  f_brightness_sensor:"Ljussensor",f_lux_up:"Lux upp-tröskel",f_lux_down:"Lux ner-tröskel",
  f_w_up_from:"Vardag upp från",f_w_up_to:"Vardag upp till",f_w_down_from:"Vardag ner från",f_w_down_to:"Vardag ner till",
  f_we_up_from:"Helg upp från",f_we_up_to:"Helg upp till",f_we_down_from:"Helg ner från",f_we_down_to:"Helg ner till",
  f_cover:"Persienn / Cover",f_window_sensor:"Fönstersensor (valfritt)",
  f_win_open:"Fönsterstatus 'öppet'",f_win_tilt:"Fönsterstatus 'vippat'",f_win_tilt_none:"Inaktiverad",
  f_pos_win_open:"Position vid öppet fönster",f_pos_win_tilt:"Position vid vippat fönster",
  f_pos_win_tilt_2state_hint:"För 2-lägeskontakter används denna position när rullgardinen är stängd.",
  f_lock:"Utelåsningsskydd",f_min_pos:"Minimiposition vid öppen dörr",
  f_area_up:"Område (Upp)",f_area_down:"Område (Ner)",
  f_pos_open:"Position Öppen",f_pos_closed:"Position Stängd",f_pos_sun:"Solskyddsposition",
  f_drive_after:"Hämta om fönster öppet",f_drive_after_hint:"Åtgärden utförs så snart fönstret stängs.",
  pick_entity:"Välj entitet…",confirm_del_area:"Ta bort område \"{id}\"?",confirm_del_shutter:"Ta bort persienn?",
},
pl:{
  tab_settings:"Ustawienia",
  f_season_all:"cały rok",
  month_1:"Styczeń",
  month_2:"Luty",
  month_3:"Marzec",
  month_4:"Kwiecień",
  month_5:"Maj",
  month_6:"Czerwiec",
  month_7:"Lipiec",
  month_8:"Sierpień",
  month_9:"Wrzesień",
  month_10:"Październik",
  month_11:"Listopad",
  month_12:"Grudzień",
  sec_basics:"Dane podstawowe",
  sec_schedule:"Harmonogram",
  sec_schedule_time:"według godziny",
  sec_schedule_brightness:"według jasności",
  sec_schedule_sun:"według położenia słońca",
  sec_calendar:"Kalendarz i obsługa ręczna",
  sec_sunprotect:"Ochrona przeciwsłoneczna",
  sec_light:"Światło",
  sec_light_sub:"włącz przy zamykaniu",
  sec_shutter:"Roleta",
  sec_areas:"Strefy",
  sec_areas_sub:"która strefa steruje w górę i w dół",
  sec_positions:"Pozycje",
  sec_window:"Okno i wietrzenie",
  sec_window_sub:"kontaktrony, pozycja wietrzenia, zabezpieczenie",
  sec_slats:"Lamele",
  sec_slats_sub:"tylko żaluzje",
  ent_matching:"Pasujące",
  ent_others:"Wszystkie pozostałe",
  ent_more:"… i {n} więcej – uściślij wyszukiwanie",
  clear:"Wyczyść",
  menu:"Menu",
  admin_only:"Konfiguracja jest zastrzeżona dla administratorów.",
  f_shutter_auto:"Automatyka aktywna",
  f_shutter_auto_hint:"Wyłączone: ta roleta nie jest już sterowana przez żadną automatykę – ani według czasu, jasności, położenia słońca, ani kontaktronu okiennego. Ręcznie i przyciskami na pulpicie nadal działa. Przeznaczone dla uszkodzonej rolety, bez utraty jej ustawień.",
  dash_shutter_auto_off:"automatyka wyłączona",
  btn_vent:"Wietrzenie",
  f_window_tilt_sensor:"Dodatkowy czujnik uchylenia (opcjonalnie)",
  f_window_tilt_sensor_hint:"Potrzebne tylko, gdy okno udostępnia dwie osobne encje.",
  f_sun_cond_title:"Dodatkowe warunki",
  f_sun_cond_hint:"Zacienia tylko, gdy warunki są spełnione. Puste = brak warunku.",
  f_sun_cond_a:"Warunek 1 (opcjonalnie)",
  f_sun_cond_b:"Warunek 2 (opcjonalnie)",
  f_sun_cond_on:"Zacieniaj powyżej",
  f_sun_cond_off:"Zwolnij poniżej",
  f_sun_cond_num_hint:"Odstęp między progami zapobiega oscylacjom. Puste = ta sama wartość.",
  f_sun_cond_bin_hint:"Czujnik binarny: zacienia, gdy jest włączony.",
  filter_entity:"Szukaj…",no_match:"Brak wyników",
  entity_missing:"Nie znaleziono encji – zmieniono nazwę lub jest niedostępna.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Czujnik dnia roboczego (opcjonalnie)",
  f_workday_hint:"Gdy ustawiony, \"off\" oznacza harmonogram weekendowy – obejmuje święta, urlopy i pracę zmianową.",
  f_random_offset:"Losowe przesunięcie (symulacja obecności)",
  f_random_offset_hint:"Przesuwa godziny o ± tę wartość, losowaną raz dziennie. 0 = wyłączone.",
  f_manual_override:"Pozycja ręczna",
  f_manual_override_hint:"Jak długo ręcznie ustawiona pozycja blokuje automatykę.",
  f_override_never:"Do następnego zamknięcia",
  f_override_daily:"Tylko tego samego dnia",
  f_override_next_action:"Automatyka ma pierwszeństwo",
  f_azimuth:"Tylko gdy słońce pada na okna",
  f_azimuth_hint:"Zacienia tylko wtedy, gdy słońce rzeczywiście stoi przed oknami.",
  f_azimuth_preset:"Kierunek świata",
  f_azimuth_min:"Azymut od",
  f_azimuth_max:"Azymut do",
  compass_north:"Północ",
  compass_east:"Wschód",
  compass_south:"Południe",
  compass_west:"Zachód",
  f_tilt:"Sterowanie lamelami (żaluzja)",
  f_tilt_hint:"Ustawia kąt lameli oprócz wysokości.",
  f_tilt_unsupported:"Ta encja nie zgłasza obsługi lameli – ustawienie zostanie zignorowane.",
  f_tilt_open:"Lamele Otwarte",
  f_tilt_closed:"Lamele Zamknięte",
  f_tilt_sun:"Lamele ochrona słoneczna",
  sun_prot_direction:"Kierunek okien",
  sun_azimuth:"Azymut słońca",
  sun_prot_wrong_dir:"słońce nie pada na okna",
  tab_dashboard:"Panel",tab_areas:"Strefy",tab_shutters:"Rolety",
  subtitle:"{a} stref, {s} rolet",loading:"Ładowanie…",
  mode_time:"Czas",mode_brightness:"Jasność",mode_sun:"Pozycja słońca",
  shutter_s:"roleta",no_shutters:"Brak rolet",auto:"Automatyka",
  btn_up:"W górę",btn_stop:"Stop",btn_down:"W dół",btn_sun:"Osłona słoneczna",
  btn_add:"Dodaj",btn_save:"Zapisz",btn_cancel:"Anuluj",
  empty_areas:"Brak skonfigurowanych stref. Przejdź do zakładki \"Strefy\".",
  empty_areas_list:"Nie utworzono jeszcze żadnych stref.",empty_shutters_list:"Nie utworzono jeszcze żadnych rolet.",
  add_area:"Dodaj strefę",edit_area:"Edytuj strefę",add_shutter:"Dodaj roletę",edit_shutter:"Edytuj roletę",
  col_name:"Nazwa",col_id:"ID",col_mode:"Tryb",col_shutters:"Rolety",
  col_cover:"Encja cover",col_area_up:"Strefa W górę",col_area_down:"Strefa W dół",col_window:"Okno",
  f_name:"Nazwa",f_mode:"Tryb sterowania",f_drive_delay:"Opóźnienie między roletami (sek.)",
  f_sun_protect:"Włącz osłonę słoneczną",f_elev_thresh:"Próg elewacji (°)",
  f_light_entity:"Lampa/przełącznik przy zamykaniu (opcjonalnie)",f_light_brightness:"Jasność lampy (%)",
  f_time_up:"Dzień roboczy w górę",f_time_down:"Dzień roboczy w dół",
  f_time_we_up:"Weekend w górę",f_time_we_down:"Weekend w dół",
  f_sunrise_off:"Offset wschodu (min.)",f_sunset_off:"Offset zachodu (min.)",
  sun_next_rise:"Następny wschód",sun_next_set:"Następny zachód",
  sun_trigger_up:"W górę o",sun_trigger_down:"W dół o",
  sun_bound_earliest:"nie wcześniej niż",sun_bound_latest:"nie później niż",sun_jitter:"Obecność",
  sun_elevation:"Aktualna elewacja",sun_offset:"Offset",
  dash_shutter_role_up:"Tylko w górę przez tę strefę",
  dash_shutter_role_down:"Tylko w dół przez tę strefę",
  dash_shutter_role_both:"W górę i w dół przez tę strefę",
  dash_current_lux:"Aktualnie",
  f_brightness_sensor:"Czujnik jasności",f_lux_up:"Próg lux w górę",f_lux_down:"Próg lux w dół",
  f_w_up_from:"Dzień roboczy góra od",f_w_up_to:"Dzień roboczy góra do",f_w_down_from:"Dzień roboczy dół od",f_w_down_to:"Dzień roboczy dół do",
  f_we_up_from:"Weekend góra od",f_we_up_to:"Weekend góra do",f_we_down_from:"Weekend dół od",f_we_down_to:"Weekend dół do",
  f_cover:"Roleta / Cover",f_window_sensor:"Czujnik okna (opcjonalnie)",
  f_win_open:"Stan okna 'otwarte'",f_win_tilt:"Stan okna 'uchylone'",f_win_tilt_none:"Wyłączone",
  f_pos_win_open:"Pozycja przy otwartym oknie",f_pos_win_tilt:"Pozycja przy uchylonym oknie",
  f_pos_win_tilt_2state_hint:"Dla kontaktów 2-stanowych ta pozycja jest używana, gdy roleta jest zamknięta.",
  f_lock:"Blokada bezpieczeństwa",f_min_pos:"Minimalna pozycja przy otwartych drzwiach",
  f_area_up:"Strefa (W górę)",f_area_down:"Strefa (W dół)",
  f_pos_open:"Pozycja Otwarta",f_pos_closed:"Pozycja Zamknięta",f_pos_sun:"Pozycja osłony słonecznej",
  f_drive_after:"Nadrobić gdy okno otwarte",f_drive_after_hint:"Akcja zostanie wykonana po zamknięciu okna.",
  pick_entity:"Wybierz encję…",confirm_del_area:"Usunąć strefę \"{id}\"?",confirm_del_shutter:"Usunąć roletę?",
},
pt:{
  tab_settings:"Definições",
  f_season_all:"todo o ano",
  month_1:"Janeiro",
  month_2:"Fevereiro",
  month_3:"Março",
  month_4:"Abril",
  month_5:"Maio",
  month_6:"Junho",
  month_7:"Julho",
  month_8:"Agosto",
  month_9:"Setembro",
  month_10:"Outubro",
  month_11:"Novembro",
  month_12:"Dezembro",
  sec_basics:"Dados básicos",
  sec_schedule:"Horário",
  sec_schedule_time:"por hora",
  sec_schedule_brightness:"por luminosidade",
  sec_schedule_sun:"por posição solar",
  sec_calendar:"Calendário e controlo manual",
  sec_sunprotect:"Proteção solar",
  sec_light:"Luz",
  sec_light_sub:"ligar ao fechar",
  sec_shutter:"Estore",
  sec_areas:"Zonas",
  sec_areas_sub:"que zona comanda subida e descida",
  sec_positions:"Posições",
  sec_window:"Janela e ventilação",
  sec_window_sub:"contactos, posição de ventilação, proteção",
  sec_slats:"Lâminas",
  sec_slats_sub:"apenas estores venezianos",
  ent_matching:"Correspondentes",
  ent_others:"Todos os outros",
  ent_more:"… e mais {n} – refine a pesquisa",
  clear:"Limpar",
  menu:"Menu",
  admin_only:"A configuração é reservada aos administradores.",
  f_shutter_auto:"Automação ativa",
  f_shutter_auto_hint:"Desligado: esta persiana já não é movida por nenhuma automação – nem por hora, luminosidade, posição do sol ou contacto de janela. O comando manual e os botões do painel continuam a funcionar. Pensado para uma persiana avariada, sem perder as suas definições.",
  dash_shutter_auto_off:"automação desligada",
  btn_vent:"Ventilar",
  f_window_tilt_sensor:"Sensor adicional basculante (opcional)",
  f_window_tilt_sensor_hint:"Só é necessário se a janela tiver duas entidades separadas.",
  f_sun_cond_title:"Condições adicionais",
  f_sun_cond_hint:"Sombreia apenas se estas condições se verificarem. Vazio = sem condição.",
  f_sun_cond_a:"Condição 1 (opcional)",
  f_sun_cond_b:"Condição 2 (opcional)",
  f_sun_cond_on:"Sombrear acima de",
  f_sun_cond_off:"Libertar abaixo de",
  f_sun_cond_num_hint:"A diferença entre limiares evita oscilações. Vazio = mesmo valor.",
  f_sun_cond_bin_hint:"Sensor binário: sombreia enquanto estiver ativo.",
  filter_entity:"Pesquisar…",no_match:"Sem resultados",
  entity_missing:"Entidade não encontrada – foi renomeada ou está indisponível.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Sensor de dia útil (opcional)",
  f_workday_hint:"Quando definido, \"off\" aplica o horário de fim de semana – cobre feriados, férias e turnos.",
  f_random_offset:"Desvio aleatório (simulação de presença)",
  f_random_offset_hint:"Desloca os horários em ± este valor, escolhido uma vez por dia. 0 = desligado.",
  f_manual_override:"Posição manual",
  f_manual_override_hint:"Durante quanto tempo uma posição manual bloqueia a automação.",
  f_override_never:"Até ao próximo fecho",
  f_override_daily:"Apenas no mesmo dia",
  f_override_next_action:"A automação tem prioridade",
  f_azimuth:"Apenas quando o sol incide nas janelas",
  f_azimuth_hint:"Sombreia apenas quando o sol está realmente em frente às janelas.",
  f_azimuth_preset:"Ponto cardeal",
  f_azimuth_min:"Azimute de",
  f_azimuth_max:"Azimute até",
  compass_north:"Norte",
  compass_east:"Este",
  compass_south:"Sul",
  compass_west:"Oeste",
  f_tilt:"Controlar lâminas (estore veneziano)",
  f_tilt_hint:"Define o ângulo das lâminas além da altura.",
  f_tilt_unsupported:"Esta entidade não indica suporte a lâminas – a definição será ignorada.",
  f_tilt_open:"Lâminas Abertas",
  f_tilt_closed:"Lâminas Fechadas",
  f_tilt_sun:"Lâminas proteção solar",
  sun_prot_direction:"Orientação das janelas",
  sun_azimuth:"Azimute solar",
  sun_prot_wrong_dir:"o sol não incide nas janelas",
  tab_dashboard:"Painel",tab_areas:"Zonas",tab_shutters:"Estores",
  subtitle:"{a} zonas, {s} estores",loading:"A carregar…",
  mode_time:"Horário",mode_brightness:"Luminosidade",mode_sun:"Posição solar",
  shutter_s:"estore",no_shutters:"Sem estores",auto:"Automático",
  btn_up:"Subir",btn_stop:"Parar",btn_down:"Descer",btn_sun:"Proteção solar",
  btn_add:"Adicionar",btn_save:"Guardar",btn_cancel:"Cancelar",
  empty_areas:"Nenhuma zona configurada. Mude para o separador \"Zonas\".",
  empty_areas_list:"Nenhuma zona criada.",empty_shutters_list:"Nenhum estore criado.",
  add_area:"Adicionar zona",edit_area:"Editar zona",add_shutter:"Adicionar estore",edit_shutter:"Editar estore",
  col_name:"Nome",col_id:"ID",col_mode:"Modo",col_shutters:"Estores",
  col_cover:"Entidade cover",col_area_up:"Zona Subir",col_area_down:"Zona Descer",col_window:"Janela",
  f_name:"Nome",f_mode:"Modo de controlo",f_drive_delay:"Atraso entre estores (seg.)",
  f_sun_protect:"Ativar proteção solar",f_elev_thresh:"Limiar de elevação (°)",
  f_light_entity:"Luz/interruptor ao fechar (opcional)",f_light_brightness:"Luminosidade da luz (%)",
  f_time_up:"Semana subir",f_time_down:"Semana descer",
  f_time_we_up:"Fim-de-semana subir",f_time_we_down:"Fim-de-semana descer",
  f_sunrise_off:"Offset nascer do sol (min.)",f_sunset_off:"Offset pôr do sol (min.)",
  sun_next_rise:"Próximo nascer do sol",sun_next_set:"Próximo pôr do sol",
  sun_trigger_up:"Subir às",sun_trigger_down:"Descer às",
  sun_bound_earliest:"não antes das",sun_bound_latest:"não depois das",sun_jitter:"Presença",
  sun_elevation:"Elevação atual",sun_offset:"Offset",
  dash_shutter_role_up:"Só subir por esta zona",
  dash_shutter_role_down:"Só descer por esta zona",
  dash_shutter_role_both:"Subir e descer por esta zona",
  dash_current_lux:"Atual",
  f_brightness_sensor:"Sensor de luminosidade",f_lux_up:"Limiar lux subir",f_lux_down:"Limiar lux descer",
  f_w_up_from:"Semana subir de",f_w_up_to:"Semana subir até",f_w_down_from:"Semana descer de",f_w_down_to:"Semana descer até",
  f_we_up_from:"Fim-de-semana subir de",f_we_up_to:"Fim-de-semana subir até",f_we_down_from:"Fim-de-semana descer de",f_we_down_to:"Fim-de-semana descer até",
  f_cover:"Estore / Cover",f_window_sensor:"Sensor de janela (opcional)",
  f_win_open:"Estado janela 'aberta'",f_win_tilt:"Estado janela 'basculante'",f_win_tilt_none:"Desativado",
  f_pos_win_open:"Posição janela aberta",f_pos_win_tilt:"Posição janela basculante",
  f_pos_win_tilt_2state_hint:"Para contactos de 2 estados, esta posição é usada quando a persiana está fechada.",
  f_lock:"Proteção anti-bloqueio",f_min_pos:"Posição mín. porta aberta",
  f_area_up:"Zona (Subir)",f_area_down:"Zona (Descer)",
  f_pos_open:"Posição Aberta",f_pos_closed:"Posição Fechada",f_pos_sun:"Posição proteção solar",
  f_drive_after:"Recuperar se janela aberta",f_drive_after_hint:"A ação será executada assim que a janela for fechada.",
  pick_entity:"Selecionar entidade…",confirm_del_area:"Eliminar zona \"{id}\"?",confirm_del_shutter:"Eliminar estore?",
},
nb:{
  tab_settings:"Innstillinger",
  f_season_all:"hele året",
  month_1:"Januar",
  month_2:"Februar",
  month_3:"Mars",
  month_4:"April",
  month_5:"Mai",
  month_6:"Juni",
  month_7:"Juli",
  month_8:"August",
  month_9:"September",
  month_10:"Oktober",
  month_11:"November",
  month_12:"Desember",
  sec_basics:"Grunndata",
  sec_schedule:"Tidsplan",
  sec_schedule_time:"etter tid",
  sec_schedule_brightness:"etter lysstyrke",
  sec_schedule_sun:"etter solposisjon",
  sec_calendar:"Kalender og manuell betjening",
  sec_sunprotect:"Solskjerming",
  sec_light:"Lys",
  sec_light_sub:"slå på ved lukking",
  sec_shutter:"Persienne",
  sec_areas:"Områder",
  sec_areas_sub:"hvilket område styrer opp og ned",
  sec_positions:"Posisjoner",
  sec_window:"Vindu og lufting",
  sec_window_sub:"kontakter, luftestilling, utelåsingsvern",
  sec_slats:"Lameller",
  sec_slats_sub:"kun persienner",
  ent_matching:"Treff",
  ent_others:"Alle andre",
  ent_more:"… og {n} til – avgrens søket",
  clear:"Tøm",
  menu:"Meny",
  admin_only:"Konfigurasjon er forbeholdt administratorer.",
  f_shutter_auto:"Automatikk aktiv",
  f_shutter_auto_hint:"Av: denne persiennen kjøres ikke lenger av noen automatikk – verken etter tid, lysstyrke, solposisjon eller vinduskontakt. Manuelt og via knappene på dashbordet virker den fortsatt. Ment for en defekt persienn, uten å miste innstillingene.",
  dash_shutter_auto_off:"automatikk av",
  btn_vent:"Lufte",
  f_window_tilt_sensor:"Ekstra sensor for vippet (valgfri)",
  f_window_tilt_sensor_hint:"Bare nødvendig hvis vinduet har to separate enheter.",
  f_sun_cond_title:"Flere betingelser",
  f_sun_cond_hint:"Skjermer bare når disse betingelsene er oppfylt. Tom = ingen betingelse.",
  f_sun_cond_a:"Betingelse 1 (valgfri)",
  f_sun_cond_b:"Betingelse 2 (valgfri)",
  f_sun_cond_on:"Skjerm over",
  f_sun_cond_off:"Frigi under",
  f_sun_cond_num_hint:"Avstanden mellom tersklene hindrer pendling. Tom = samme verdi.",
  f_sun_cond_bin_hint:"Binær sensor: skjermer så lenge den er aktiv.",
  filter_entity:"Søk…",no_match:"Ingen treff",
  entity_missing:"Enheten ble ikke funnet – omdøpt eller utilgjengelig.",
  /* v2.1 – Azimut, Workday, Zufalls-Offset, Lamellen, Override */
  f_workday_sensor:"Arbeidsdag-sensor (valgfri)",
  f_workday_hint:"Når den er satt, betyr \"av\" at helgeplanen gjelder – dekker helligdager, ferie og skiftarbeid.",
  f_random_offset:"Tilfeldig forskyvning (tilstedeværelsessimulering)",
  f_random_offset_hint:"Forskyver tidene med ± denne verdien, valgt én gang per dag. 0 = av.",
  f_manual_override:"Manuell posisjon",
  f_manual_override_hint:"Hvor lenge en manuelt satt posisjon blokkerer automatikken.",
  f_override_never:"Til neste lukking",
  f_override_daily:"Bare samme dag",
  f_override_next_action:"Automatikken har forrang",
  f_azimuth:"Bare når sola står mot vinduene",
  f_azimuth_hint:"Skjermer bare når sola faktisk står foran vinduene.",
  f_azimuth_preset:"Himmelretning",
  f_azimuth_min:"Asimut fra",
  f_azimuth_max:"Asimut til",
  compass_north:"Nord",
  compass_east:"Øst",
  compass_south:"Sør",
  compass_west:"Vest",
  f_tilt:"Styr lameller (persienne)",
  f_tilt_hint:"Setter lamellvinkelen i tillegg til høyden.",
  f_tilt_unsupported:"Denne enheten melder ingen lamellstøtte – innstillingen ignoreres.",
  f_tilt_open:"Lameller Åpne",
  f_tilt_closed:"Lameller Lukket",
  f_tilt_sun:"Lameller solskjerming",
  sun_prot_direction:"Vindusretning",
  sun_azimuth:"Sol-asimut",
  sun_prot_wrong_dir:"sola står ikke mot vinduene",
  tab_dashboard:"Dashboard",tab_areas:"Områder",tab_shutters:"Persienner",
  subtitle:"{a} områder, {s} persienner",loading:"Laster…",
  mode_time:"Tid",mode_brightness:"Lysstyrke",mode_sun:"Solposisjon",
  shutter_s:"persienne",no_shutters:"Ingen persienner",auto:"Automatikk",
  btn_up:"Opp",btn_stop:"Stopp",btn_down:"Ned",btn_sun:"Solbeskyttelse",
  btn_add:"Legg til",btn_save:"Lagre",btn_cancel:"Avbryt",
  empty_areas:"Ingen områder konfigurert. Bytt til fanen \"Områder\".",
  empty_areas_list:"Ingen områder opprettet ennå.",empty_shutters_list:"Ingen persienner opprettet ennå.",
  add_area:"Legg til område",edit_area:"Rediger område",add_shutter:"Legg til persienne",edit_shutter:"Rediger persienne",
  col_name:"Navn",col_id:"ID",col_mode:"Modus",col_shutters:"Persienner",
  col_cover:"Cover-entitet",col_area_up:"Område Opp",col_area_down:"Område Ned",col_window:"Vindu",
  f_name:"Navn",f_mode:"Styringsmodus",f_drive_delay:"Forsinkelse mellom persienner (sek.)",
  f_sun_protect:"Aktiver solbeskyttelse",f_elev_thresh:"Elevasjonsterskel (°)",
  f_light_entity:"Lampe/bryter ved lukking (valgfritt)",f_light_brightness:"Lampe lysstyrke (%)",
  f_time_up:"Hverdag opp",f_time_down:"Hverdag ned",
  f_time_we_up:"Helg opp",f_time_we_down:"Helg ned",
  f_sunrise_off:"Soloppgang offset (min.)",f_sunset_off:"Solnedgang offset (min.)",
  sun_next_rise:"Neste soloppgang",sun_next_set:"Neste solnedgang",
  sun_trigger_up:"Opp kl.",sun_trigger_down:"Ned kl.",
  sun_bound_earliest:"tidligst",sun_bound_latest:"senest",sun_jitter:"Tilstedeværelse",
  sun_elevation:"Gjeldende elevasjon",sun_offset:"Offset",
  dash_shutter_role_up:"Bare opp via dette området",
  dash_shutter_role_down:"Bare ned via dette området",
  dash_shutter_role_both:"Opp og ned via dette området",
  dash_current_lux:"Nå",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux opp-terskel",f_lux_down:"Lux ned-terskel",
  f_w_up_from:"Hverdag opp fra",f_w_up_to:"Hverdag opp til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Helg opp fra",f_we_up_to:"Helg opp til",f_we_down_from:"Helg ned fra",f_we_down_to:"Helg ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vindussensor (valgfritt)",
  f_win_open:"Vindustilstand 'åpent'",f_win_tilt:"Vindustilstand 'vippet'",f_win_tilt_none:"Deaktivert",
  f_pos_win_open:"Posisjon ved åpent vindu",f_pos_win_tilt:"Posisjon ved vippet vindu",
  f_pos_win_tilt_2state_hint:"For 2-tilstandskontakter brukes denne posisjonen når persiennen er lukket.",
  f_lock:"Utestengingsbeskyttelse",f_min_pos:"Minimumsposisjon ved åpen dør",
  f_area_up:"Område (Opp)",f_area_down:"Område (Ned)",
  f_pos_open:"Posisjon Åpen",f_pos_closed:"Posisjon Lukket",f_pos_sun:"Solbeskyttelsesposisjon",
  f_drive_after:"Ta igjen hvis vindu åpent",f_drive_after_hint:"Handlingen utføres så snart vinduet lukkes.",
  pick_entity:"Velg entitet…",confirm_del_area:"Slette område \"{id}\"?",confirm_del_shutter:"Slette persienne?",
},
};

class ShutterPilotPanel extends PanelBase {
  static get properties(){return{hass:{type:Object,hasChanged:()=>true},narrow:{type:Boolean},panel:{type:Object},_tab:{attribute:false},_data:{attribute:false},_editArea:{attribute:false},_editShutter:{attribute:false},_isMobile:{attribute:false}};}
  static get styles(){return css`
    :host{display:block;padding:16px;font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);--sp:var(--primary-color,#03a9f4);--card-bg:var(--card-background-color,#1c1c1c);--txt:var(--primary-text-color);--txt2:var(--secondary-text-color);--divider:var(--divider-color,#333);overflow-x:hidden;touch-action:pan-y}
    .topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:12px}
    .title-row{display:flex;align-items:center;flex-wrap:wrap;gap:10px;row-gap:4px;width:100%}
    .menu-btn{flex-shrink:0;margin-left:-8px;color:var(--txt);--mdc-icon-button-size:40px}
    .menu-fallback{flex-shrink:0;margin-left:-4px;display:inline-flex;align-items:center;justify-content:center;
      width:40px;height:40px;padding:0;border:none;border-radius:50%;background:transparent;color:var(--txt);cursor:pointer}
    .menu-fallback:hover{background:rgba(127,127,127,.15)}
    .master-row{display:flex;align-items:center;gap:8px;margin-left:auto;font-size:14px;color:var(--txt2)}
    .master-row ha-switch{--mdc-theme-secondary:var(--primary-color,#03a9f4)}
    .sun-protect-info{margin-top:8px;padding:10px 12px;border-radius:8px;background:rgba(255,152,0,.12);border:1px solid rgba(255,152,0,.35);font-size:13px}
    .sun-protect-info.active{border-color:rgba(76,175,80,.45);background:rgba(76,175,80,.12)}
    .sun-protect-info .sun-row{margin:4px 0;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
    .topbar h1{margin:0;font-size:24px;font-weight:500;color:var(--txt)}
    .topbar .sub{font-size:14px;color:var(--txt2)}
    .sp-ver-badge{font-size:13px;font-weight:600;color:#4caf50;flex-shrink:0;padding:3px 10px;border-radius:10px;border:2px solid #4caf50;background:rgba(76,175,80,.12);line-height:1.2}
    /* Ohne Konfigurationstabs bleibt nur eine Trennlinie über dem Dashboard. */
    .tabs-spacer{border-bottom:2px solid var(--divider);margin-bottom:20px}
    .tabs{display:flex;gap:0;border-bottom:2px solid var(--divider);margin-bottom:20px;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;scroll-snap-type:x mandatory}
    .tabs::-webkit-scrollbar{height:6px}
    .tab{padding:10px 20px;cursor:pointer;font-size:14px;font-weight:500;color:var(--txt2);border-bottom:3px solid transparent;transition:all .2s;flex:0 0 auto;scroll-snap-align:start}
    .tab:hover{color:var(--txt)}
    .time-row{display:flex;align-items:center;gap:8px}
    .time-row select{flex:1 1 0;min-width:0}
    .time-sep{font-weight:600;color:var(--txt2)}
    .spin{display:flex;align-items:center;gap:4px;flex:1 1 0}
    .spin-btn{flex:0 0 auto;min-width:38px;height:38px;font-size:18px;line-height:1;
      cursor:pointer;border:none;border-radius:8px;background:var(--card2, rgba(127,127,127,.18));color:var(--txt)}
    .spin-btn:hover{background:var(--sp);color:#fff}
    .spin-val{flex:1 1 0;min-width:0;text-align:center}
    .picked{padding:10px;border-radius:8px;background:var(--card2, rgba(127,127,127,.12));
      display:flex;align-items:center;gap:8px;font-size:14px;color:var(--txt2)}
    .picked.trigger{cursor:pointer;border:1px solid var(--divider)}
    .picked.trigger:hover{border-color:var(--sp)}
    .picked.has{color:var(--txt);font-weight:500}
    .picked-val{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .chev{flex:0 0 auto;color:var(--txt2);font-size:12px}
    .search-row{display:flex;align-items:center;gap:6px}
    .search-row input{flex:1;min-width:0}
    .ent-list{max-height:190px;overflow-y:auto;border-radius:8px;
      border:1px solid var(--divider);margin-top:6px}
    /* Abschnitte im Formular sichtbar trennen: vorher lief alles als eine
       lange Feldliste durch und man sah nicht, wo ein neues Thema anfängt. */
    .sec{margin:22px 0 12px;padding-top:14px;border-top:2px solid var(--divider);
      display:flex;align-items:center;gap:8px}
    .sec:first-of-type{margin-top:6px;padding-top:0;border-top:none}
    .sec ha-icon{--mdc-icon-size:19px;color:var(--sp)}
    .sec h4{margin:0;font-size:14px;font-weight:600;letter-spacing:.02em;color:var(--txt)}
    .sec .sec-sub{font-size:12px;color:var(--txt2);font-weight:400}
    .field.open{background:var(--card2, rgba(127,127,127,.07));padding:10px;
      border-radius:8px;border:1px solid var(--sp)}
    .ent-group{padding:6px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;
      color:var(--txt2);background:var(--card2, rgba(127,127,127,.10));position:sticky;top:0}
    .ent-row{padding:8px 10px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--divider)}
    .ent-row:last-child{border-bottom:none}
    .ent-row:hover{background:var(--card2, rgba(127,127,127,.15))}
    .ent-row.sel{background:var(--sp);color:#fff}
    .ent-row.empty{cursor:default;color:var(--txt2)}
    .preset-row{display:flex;flex-wrap:wrap;gap:6px}
    .btn.preset{padding:6px 12px;font-size:13px;background:var(--card2, rgba(127,127,127,.12));color:var(--txt)}
    .btn.preset.active{background:var(--sp);color:#fff}
    .tab.active{color:var(--sp);border-bottom-color:var(--sp)}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(340px,100%),1fr));gap:16px}
    .card{background:var(--card-bg);border-radius:12px;padding:20px;box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.15));min-width:0}
    .card-hdr{display:flex;align-items:center;gap:12px;margin-bottom:16px}
    .card-hdr .ic{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--sp);color:#fff;--mdc-icon-size:22px}
    .card-hdr .info h2{margin:0;font-size:18px;font-weight:500;color:var(--txt)}
    .card-hdr .info span{font-size:13px;color:var(--txt2)}
    .auto-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .auto-row .lbl{font-size:14px;color:var(--txt)}
    .srow{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .srow.auto-off .nm{opacity:.55}
    .srow-right{display:flex;align-items:center;gap:10px;flex-shrink:0}
    .sh-auto{--mdc-theme-secondary:var(--primary-color,#03a9f4);transform:scale(.8);transform-origin:right center}
    .auto-off-ic{--mdc-icon-size:17px;margin-left:6px;color:var(--txt2);flex-shrink:0}
    .srow:last-child{border-bottom:none}
    .srow .nm-wrap{display:flex;align-items:center;min-width:0;flex:1;gap:0}
    .srow .role-icons{display:inline-flex;align-items:center;justify-content:center;margin-right:6px;flex-shrink:0}
    .srow .role-icons ha-icon{--mdc-icon-size:18px;color:var(--sp)}
    .srow .nm{font-size:14px;color:var(--txt);flex:1;min-width:0}
    .srow .pos{font-size:13px;color:var(--txt2);min-width:50px;text-align:right}
    .actions{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
    .btn{border:none;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:500;transition:opacity .2s;display:inline-flex;align-items:center;gap:6px}
    .btn:hover{opacity:.85}
    .btn.open{background:#4caf50;color:#fff} .btn.stop{background:#757575;color:#fff}
    .btn.close{background:#f44336;color:#fff}
    .btn.sun{background:#ff9800;color:#fff} .btn.add{background:var(--sp);color:#fff}
    .btn.edit{background:#607d8b;color:#fff} .btn.del{background:#e53935;color:#fff}
    .btn.cancel{background:var(--divider);color:var(--txt)} .btn.save{background:#4caf50;color:#fff}
    .empty{text-align:center;padding:48px 16px;color:var(--txt2)}
    .table-wrap{max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}
    table{width:100%;border-collapse:collapse;font-size:14px}
    th{text-align:left;padding:10px 8px;color:var(--txt2);font-weight:500;border-bottom:2px solid var(--divider)}
    td{padding:10px 8px;border-bottom:1px solid var(--divider);color:var(--txt)}
    tr:hover td{background:rgba(255,255,255,.03)}
    .kv{display:grid;grid-template-columns:minmax(120px,auto) 1fr;gap:6px 10px;font-size:13px;color:var(--txt)}
    .kv .k{color:var(--txt2)}
    .kv .v{min-width:0;word-break:break-word}
    .row-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:12px}
    .form{background:var(--card-bg);border-radius:12px;padding:24px;margin-bottom:20px;max-width:600px}
    .form h3{margin:0 0 16px;font-size:18px;color:var(--txt)}
    .field{margin-bottom:14px}
    .field label{display:block;font-size:13px;color:var(--txt2);margin-bottom:4px}
    .field input,.field select{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--divider);background:var(--primary-background-color,#111);color:var(--txt);font-size:14px;box-sizing:border-box}
    .field input[type=time]{cursor:pointer}
    .field select{appearance:auto}
    .field input:focus,.field select:focus{outline:none;border-color:var(--sp)}
    .field .hint{font-size:11px;color:var(--txt2);margin-top:2px}
    .slider-row{display:flex;align-items:center;gap:12px}
    .slider-row input[type=range]{flex:1;accent-color:var(--sp);height:6px;cursor:pointer}
    .slider-row .slider-val{min-width:44px;text-align:center;font-size:14px;font-weight:500;color:var(--sp)}
    .form-actions{display:flex;gap:8px;margin-top:16px}
    .chip{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:500}
    .chip.time{background:#1565c0;color:#fff} .chip.brightness{background:#f57f17;color:#fff} .chip.sun{background:#e65100;color:#fff}
    .sun-info{margin:12px 0 4px;padding:10px 12px;background:rgba(255,152,0,.08);border-radius:8px;border-left:3px solid #ff9800}
    .time-info{margin:12px 0 4px;padding:10px 12px;background:rgba(33,150,243,.08);border-radius:8px;border-left:3px solid #2196f3}
    .time-info.weekend{border-left-color:#8bc34a;background:rgba(139,195,74,.08)}
    .brightness-info{margin:12px 0 4px;padding:10px 12px;background:rgba(255,193,7,.08);border-radius:8px;border-left:3px solid #ffc107}
    .sun-row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:13px;color:var(--txt);flex-wrap:wrap}
    .sun-row ha-icon{--mdc-icon-size:18px;color:#ff9800;flex-shrink:0}
    .sun-off{font-size:12px;color:var(--txt2)}

    @media (max-width:420px){
      :host{padding:12px}
      .grid{grid-template-columns:1fr}
      .card{padding:16px}
      .tab{padding:10px 14px}
    }
  `;}

  constructor(){
    super();
    this._tab="dashboard";
    this._data=null;
    this._editArea=null;
    this._editShutter=null;
    this._isMobile=false;
    this._mql=null;
    this._mqlHandler=null;
    this._refreshTimer=null;
  }
  connectedCallback(){
    super.connectedCallback?.();
    // Ohne Lit zeigt die Notfall-Basisklasse nur ihre Meldung. Alles Weitere
    // würde hier ins Leere laufen.
    if(LIT_MISSING)return;
    this._load();
    // Sonnenstand, Sonnenschutz-Status und die berechneten Fahrzeiten ändern
    // sich laufend. Ohne diesen Timer bliebe das Panel auf dem Stand vom
    // Öffnen stehen. Nicht neu laden, während ein Formular offen ist.
    this._refreshTimer=window.setInterval(()=>{
      if(!this._editArea&&!this._editShutter)this._load();
    },REFRESH_MS);
    try{
      this._mql=window.matchMedia("(max-width: 600px)");
      this._mqlHandler=()=>this._syncMobile();
      if(this._mql?.addEventListener)this._mql.addEventListener("change",this._mqlHandler);
      else if(this._mql?.addListener)this._mql.addListener(this._mqlHandler);
    }catch(_){/* ignore */}
    this._syncMobile();
  }
  disconnectedCallback(){
    if(this._refreshTimer){window.clearInterval(this._refreshTimer);this._refreshTimer=null;}
    try{
      if(this._mql&&this._mqlHandler){
        if(this._mql.removeEventListener)this._mql.removeEventListener("change",this._mqlHandler);
        else if(this._mql.removeListener)this._mql.removeListener(this._mqlHandler);
      }
    }catch(_){/* ignore */}
    this._mql=null;
    this._mqlHandler=null;
    super.disconnectedCallback?.();
  }
  shouldUpdate(changed){
    // hass wird bei JEDER Zustandsänderung in Home Assistant neu gesetzt
    // (hasChanged:()=>true), also viele Male pro Sekunde. Ein Re-Render setzt
    // dabei .value auf allen Eingabefeldern neu. Steht der Cursor gerade in
    // einem Feld – etwa im nativen Zeit-Dialog des Browsers – wird dieser
    // dadurch geschlossen. Solange ein Formular offen ist, ignorieren wir
    // deshalb reine hass-Updates; die Formulare brauchen hass nur für die
    // Entitätslisten, und die ändern sich währenddessen praktisch nie.
    if((this._editArea||this._editShutter)&&changed.size===1&&changed.has("hass"))return false;
    return true;
  }
  updated(c){
    if(c.has("hass")&&this.hass&&!this._data)this._load();
    if(c.has("narrow"))this._syncMobile();
  }

  _syncMobile(){
    const byNarrow=!!this.narrow;
    const byWidth=!!(this._mql&&this._mql.matches);
    const next=byNarrow||byWidth;
    if(next!==this._isMobile){this._isMobile=next;this.requestUpdate();}
  }

  get _lang(){const l=(this.hass?.language||"en").substring(0,2);return I18N[l]?l:"en";}
  // Fällt auf Englisch zurück, damit neue Schlüssel in noch nicht
  // übersetzten Sprachen lesbar bleiben statt als Rohschlüssel zu erscheinen.
  t(k){return (I18N[this._lang]||{})[k]||I18N.en[k]||k;}
  /* Konfigurieren darf nur, wer in Home Assistant Administrator ist – die
     schreibenden WebSocket-Befehle weisen alle anderen ohnehin ab. Das Panel
     blendet deshalb aus, was für sie nicht bedienbar wäre; die Rollladen-
     Bedienung bleibt für alle da, die läuft über die cover-Dienste. Fehlt
     hass.user (kurz nach dem Laden), gilt Administrator: Verstecken wäre für
     den Admin nur störend, und geschützt wird ohnehin auf der Serverseite. */
  _isAdmin(){return this.hass?.user?.is_admin!==false;}
  _modeName(m){return this.t("mode_"+m)||m;}

  /** Versionsnummer aus ?v= der geladenen Panel-URL (funktioniert auch wenn get_status noch keine version liefert). */
  _panelAssetVersionFromScript(){
    try{
      for(const s of document.querySelectorAll("script[src]")){
        const src=s.getAttribute("src")||"";
        if(!src.includes("shutter_pilot"))continue;
        const u=new URL(src,window.location.href);
        const v=u.searchParams.get("v");
        if(v)return String(v).trim();
      }
    }catch(e){/* ignore */}
    return "";
  }

  _integrationVersion(){
    const d=this._data;
    if(d?.version!=null&&String(d.version).trim()!=="")return String(d.version).trim();
    const pc=this.panel?.config?.shutter_pilot_version;
    if(pc!=null&&String(pc).trim()!=="")return String(pc).trim();
    return this._panelAssetVersionFromScript();
  }

  /** Sensorentität: zuerst entity_id, sonst Suche nach friendly_name (z. B. „Lichtstärke Garten“). */
  _resolveBrightnessSensorEntity(hass,ref){
    const r=String(ref||"").trim();
    if(!r||!hass?.states)return"";
    if(hass.states[r])return r;
    const norm=(s)=>{try{return String(s).toLowerCase().normalize("NFKC");}catch(_){return String(s).toLowerCase();}};
    const lower=norm(r);
    for(const eid of Object.keys(hass.states)){
      if(!eid.startsWith("sensor.")&&!eid.startsWith("number."))continue;
      const fn=norm(hass.states[eid].attributes?.friendly_name||"");
      if(fn&&fn===lower)return eid;
    }
    return r;
  }

  _numFromLuxString(s){
    const m=String(s).replace(",",".").trim().match(/-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if(!m)return NaN;
    return parseFloat(m[0]);
  }

  /** Lux aus State (inkl. Einheiten im String) oder typischen Attributen. */
  _readLux(hass,entityId){
    if(!entityId||!hass?.states?.[entityId])return null;
    const st=hass.states[entityId];
    const raw=String(st.state??"").trim();
    const stateUnset=raw==="unavailable"||raw==="unknown"||raw==="none";
    if(!stateUnset){
      const n=this._numFromLuxString(raw);
      if(Number.isFinite(n))return n;
    }
    const a=st.attributes||{};
    const direct=[a.illuminance,a.light_level,a.lux,a.brightness,a.value,a.current];
    for(const c of direct){
      if(c!=null&&Number.isFinite(Number(c)))return Number(c);
      if(c!=null){const x=this._numFromLuxString(String(c));if(Number.isFinite(x))return x;}
    }
    for(const k of Object.keys(a)){
      if(!/illumin|lux|light|helligkeit|brightness|lx\b/i.test(k))continue;
      if(k==="unit_of_measurement"||k==="friendly_name"||k==="device_class")continue;
      const v=a[k];
      if(v!=null&&Number.isFinite(Number(v)))return Number(v);
      if(v!=null){const x=this._numFromLuxString(String(v));if(Number.isFinite(x))return x;}
    }
    return null;
  }

  /** Pfeil(e) je nach Zuordnung Hoch/Runter für diesen Bereich. */
  /* Automatik am einzelnen Rollladen: Der Schalter ist die lebende Wahrheit,
     der gespeicherte Wert gilt, solange es ihn noch nicht gibt. Sonst sucht
     man im Dashboard vergeblich, warum ein Rollladen stehen bleibt. */
  _shutterAutoOff(s){
    const eid=(s.shutter_auto_entity_id||"").trim();
    const st=eid?this.hass?.states?.[eid]:null;
    if(st&&(st.state==="on"||st.state==="off"))return st.state==="off";
    return s.automation_enabled===false;
  }
  /* Schalter für die Automatik eines einzelnen Rollladens – dasselbe Muster
     wie der Automatik-Schalter am Bereich. Ohne Administratorrechte nur
     Anzeige; der Server weist die Änderung ohnehin ab. */
  _shutterAutoSwitch(s){
    const cover=(s.cover_entity_id||"").trim();
    if(!cover)return "";
    const on=!this._shutterAutoOff(s);
    return html`<ha-switch class="sh-auto" .checked=${on} ?disabled=${!this._isAdmin()}
      title="${this.t("auto")}"
      @change=${e=>this._toggleShutterAuto(cover,e.target.checked)}></ha-switch>`;
  }
  async _toggleShutterAuto(cover,on){
    try{
      await this.hass.callWS({type:"shutter_pilot/set_shutter_automation",cover_entity_id:cover,enabled:on});
      await this._load();
    }catch(e){console.warn(e);}
  }
  _dashShutterRole(s,areaId){
    const up=(s.area_up_id||"")===areaId;
    const down=(s.area_down_id||"")===areaId;
    if(up&&down)return html`<span class="role-icons" title="${this.t("dash_shutter_role_both")}"><ha-icon icon="mdi:arrow-up-down-bold"></ha-icon></span>`;
    if(up)return html`<span class="role-icons" title="${this.t("dash_shutter_role_up")}"><ha-icon icon="mdi:arrow-up-bold"></ha-icon></span>`;
    if(down)return html`<span class="role-icons" title="${this.t("dash_shutter_role_down")}"><ha-icon icon="mdi:arrow-down-bold"></ha-icon></span>`;
    return html``;
  }

  async _load(){if(!this.hass)return;try{this._data=await this.hass.callWS({type:"shutter_pilot/get_status"});}catch(e){console.warn("SP load",e);}}
  /* Nach Anzeigename sortiert, nicht nach Entity-ID. Nutzer suchen nach
     "Küche", nicht nach "sensor.0x00158d000...". */
  _entities(domains){
    if(!this.hass?.states)return[];
    return Object.keys(this.hass.states)
      .filter(e=>domains.some(d=>e.startsWith(d+".")))
      .sort((a,b)=>this._entityLabel(a).localeCompare(this._entityLabel(b),undefined,{sensitivity:"base",numeric:true}));
  }
  _entityLabel(eid){const n=this.hass?.states?.[eid]?.attributes?.friendly_name;return n?`${n} (${eid})`:eid;}
  _deviceClass(eid){return String(this.hass?.states?.[eid]?.attributes?.device_class||"").toLowerCase();}
  /* Weiche Vorfilterung: passende Entitäten nach oben, der Rest bleibt
     erreichbar. Hart filtern wäre riskant – längst nicht jeder setzt bei
     seinen Sensoren eine device_class, und dann fände man seinen Sensor
     überhaupt nicht mehr. */
  _matchesHint(eid,hint){
    if(!hint)return false;
    const dc=this._deviceClass(eid);
    const label=this._entityLabel(eid).toLowerCase();
    if(hint.classes?.includes(dc))return true;
    if(hint.pattern&&hint.pattern.test(label))return true;
    return false;
  }
  _rankEntities(ids,hint){
    if(!hint)return{matching:[],others:ids};
    const matching=[],others=[];
    for(const e of ids)(this._matchesHint(e,hint)?matching:others).push(e);
    return{matching,others};
  }
  /* Zeiteingabe bewusst als Textfeld, nicht als <input type="time">.
     Die Home-Assistant-App für macOS ist eine Mac-Catalyst-App. Dort öffnet
     WebKit für type="time" einen UIDatePicker mit UIPickerView – und
     UIPickerView ist im Mac-Idiom nicht unterstützt. UIKit wirft dann eine
     ungefangene Exception und die gesamte App stürzt ab, nicht nur das Panel.
     Ein Textfeld löst keinen nativen Picker aus und funktioniert überall
     gleich. Akzeptiert 7:00, 0700, 07.00 und 07:00. */
  _normalizeTime(raw){
    const m=String(raw??"").trim().match(/^(\d{1,2})[:.\s]?(\d{2})$/);
    if(!m)return null;
    const h=Number(m[1]),mi=Number(m[2]);
    if(!Number.isFinite(h)||!Number.isFinite(mi)||h>23||mi>59)return null;
    return String(h).padStart(2,"0")+":"+String(mi).padStart(2,"0");
  }
  _timeField(obj,key,label,fallback="07:00",allowEmpty=false){
    // Zeitklammern dürfen leer bleiben – leer heisst "keine Grenze".
    if(allowEmpty&&!this._normalizeTime(obj[key])){
      return html`<div class="field"><label>${label}</label>
        <div class="picked trigger" @click=${()=>{obj[key]=fallback;this.requestUpdate();}}>
          <span class="picked-val">${this.t("f_bound_none")}</span>
          <span class="chev">+</span></div></div>`;
    }
    const cur=this._normalizeTime(obj[key])||fallback;
    const clear=allowEmpty?html`<button class="spin-btn" title="${this.t("clear")}"
      @click=${()=>{obj[key]="";this.requestUpdate();}}>×</button>`:"";
    // Überall ausser in der macOS-App: nativer Zeit-Picker, auf dem Handy
    // also weiterhin das gewohnte Scrollrad.
    if(!NATIVE_PICKERS_BROKEN){
      return html`<div class="field"><label>${label}</label>
        <div class="time-row">
          <input type="time" .value=${cur}
            @change=${e=>{const v=this._normalizeTime(e.target.value);if(v)obj[key]=v;}}>
          ${clear}</div></div>`;
    }
    // macOS-App: eigenes Steuerelement. Nur <button> und <input type="text">,
    // beides funktioniert dort zuverlässig. Tippen bleibt möglich, ist aber
    // nicht nötig – die Werte lassen sich komplett per Klick einstellen.
    const [h,mi]=cur.split(":").map(Number);
    const two=n=>String(n).padStart(2,"0");
    const set=(hh,mm)=>{
      const H=((hh%24)+24)%24, M=((mm%60)+60)%60;
      obj[key]=`${two(H)}:${two(M)}`;
      this.requestUpdate();
    };
    const spin=(val,onMinus,onPlus,onType,max)=>html`
      <div class="spin">
        <button class="spin-btn" @click=${onMinus}>−</button>
        <input class="spin-val" type="text" inputmode="numeric" maxlength="2" .value=${two(val)}
          @change=${e=>{const n=parseInt(e.target.value,10);
            if(Number.isFinite(n)&&n>=0&&n<=max)onType(n);else this.requestUpdate();}}>
        <button class="spin-btn" @click=${onPlus}>+</button>
      </div>`;
    return html`<div class="field"><label>${label}</label>
      <div class="time-row">
        ${spin(h,()=>set(h-1,mi),()=>set(h+1,mi),n=>set(n,mi),23)}
        <span class="time-sep">:</span>
        ${spin(mi,()=>set(h,mi-1),()=>set(h,mi+1),n=>set(h,n),59)}
        ${clear}
      </div></div>`;
  }
  /* Entitätsauswahl: Suchfeld mit Trefferliste, auf allen Plattformen gleich.
     Vorher ein natives <select> mit sämtlichen Entitäten der Domain – beim
     Helligkeitssensor also die komplette sensor.-Domain, in einer normalen
     Installation mehrere hundert Einträge, sortiert nach Entity-ID und ohne
     Suche. Genau daran sind Nutzer im Forum gescheitert. Ausserdem öffnete
     sich <select> in der macOS-App gar nicht.
     Der gespeicherte Wert wird immer angeboten, auch wenn die Entität gerade
     fehlt – sonst ginge sie beim Speichern unbemerkt verloren. */
  _openEntityPicker(key){
    this._openPicker=key;
    this[`_flt_${key}`]="";
    this.requestUpdate();
    // Direkt ins Suchfeld springen, damit man nach dem Aufklappen sofort
    // lostippen kann und nicht noch einmal klicken muss.
    this.updateComplete?.then(()=>{
      const el=this.renderRoot?.querySelector(`#sp_search_${key}`);
      if(el)el.focus();
    });
  }
  _closeEntityPicker(){this._openPicker=null;this.requestUpdate();}
  /* Zustandsvergleich statt Zahlenvergleich: Wetter-Entitäten und
     Scrape-Sensoren melden Text wie "sunny". Vorbelegt wird anhand des
     aktuellen Zustands, damit man es meist gar nicht anfassen muss. */
  _isStateEntity(eid){
    if(!eid)return false;
    if(eid.startsWith("weather."))return true;
    const st=this.hass?.states?.[eid];
    if(!st)return false;
    return Number.isNaN(Number(st.state));
  }
  _condStates(obj,key){
    const raw=obj[key];
    if(Array.isArray(raw))return raw;
    if(typeof raw==="string"&&raw.trim())return raw.split(",").map(x=>x.trim());
    return [];
  }
  _renderConditionSlots(a,ep,f){
    const T=k=>this.t(k);
    const out=[];
    for(let i=0;i<COND_SLOTS.length;i++){
      const slot=COND_SLOTS[i];
      const ek=`sun_cond_${slot}_entity`;
      const eid=a[ek]||"";
      // Nächsten Slot erst zeigen, wenn der vorherige gefüllt ist – sonst
      // stehen vier leere Auswahlfelder im Formular herum.
      if(i>0&&!a[`sun_cond_${COND_SLOTS[i-1]}_entity`]&&!eid)break;
      out.push(html`
        ${ep(ek,T("f_sun_cond_n").replace("{n}",i+1),["binary_sensor","sensor","weather"],HINTS.condition)}
        ${eid?this._renderCondDetail(a,slot,eid,f):""}`);
      if(!eid)break;
    }
    return out;
  }
  _renderCondDetail(a,slot,eid,f){
    const T=k=>this.t(k);
    if(eid.startsWith("binary_sensor."))
      return html`<div class="hint">${T("f_sun_cond_bin_hint")}</div>`;

    const sk=`sun_cond_${slot}_states`;
    const useStates=this._condStates(a,sk).length>0||this._isStateEntity(eid);
    if(!useStates){
      return html`
        ${f(`sun_cond_${slot}_on_above`,T("f_sun_cond_on"),"number")}
        ${f(`sun_cond_${slot}_off_below`,T("f_sun_cond_off"),"number")}
        <div class="hint">${T("f_sun_cond_num_hint")}</div>`;
    }

    const chosen=new Set(this._condStates(a,sk));
    const toggle=v=>{
      chosen.has(v)?chosen.delete(v):chosen.add(v);
      a[sk]=[...chosen];
      this.requestUpdate();
    };
    // Bei Wetter-Entitäten die Standardlagen anbieten, sonst nur den aktuell
    // gemeldeten Zustand – Abtippen ist zu fehleranfällig.
    const known=eid.startsWith("weather.")||eid.includes("wetterlage")
      ? WEATHER_CONDITIONS
      : [...new Set([...chosen,String(this.hass?.states?.[eid]?.state||"")].filter(Boolean))];
    return html`
      <div class="field"><label>${T("f_sun_cond_states")}</label>
        <div class="preset-row">${known.map(v=>html`
          <button class="btn preset ${chosen.has(v)?"active":""}"
            @click=${()=>toggle(v)}>${v}</button>`)}</div>
        <div class="hint">${T("f_sun_cond_states_hint")}</div></div>`;
  }
  _section(icon,titleKey,subKey=null){
    return html`<div class="sec"><ha-icon icon="${icon}"></ha-icon>
      <h4>${this.t(titleKey)}</h4>
      ${subKey?html`<span class="sec-sub">${this.t(subKey)}</span>`:""}</div>`;
  }

  _entityField(obj,key,label,domains,hint=null){
    const cur=obj[key]||"";
    const open=this._openPicker===key;

    // Zugeklappt nur eine Zeile. Vorher stand die Liste dauerhaft offen und
    // hat sieben Zeilen belegt – bei mehreren Feldern im Formular wurde das
    // unübersichtlich.
    if(!open){
      return html`<div class="field"><label>${label}</label>
        <div class="picked trigger ${cur?"has":""}" @click=${()=>this._openEntityPicker(key)}>
          <span class="picked-val">${cur?this._entityLabel(cur):this.t("pick_entity")}</span>
          ${cur?html`<button class="spin-btn" title="${this.t("clear")}"
            @click=${e=>{e.stopPropagation();obj[key]="";this.requestUpdate();}}>×</button>`:""}
          <span class="chev">▾</span></div>
        ${cur&&!this.hass?.states?.[cur]?html`<div class="hint">${this.t("entity_missing")}</div>`:""}</div>`;
    }

    const all=this._entities(domains);
    if(cur&&!all.includes(cur))all.unshift(cur);

    const fk=`_flt_${key}`;
    const flt=(this[fk]||"").trim().toLowerCase();
    const filtered=flt
      ? all.filter(e=>this._entityLabel(e).toLowerCase().includes(flt))
      : all;
    const {matching,others}=this._rankEntities(filtered,hint);

    const LIMIT=40;
    let budget=LIMIT;
    const take=list=>{const part=list.slice(0,Math.max(0,budget));budget-=part.length;return part;};
    const shownMatching=take(matching);
    const shownOthers=take(others);
    const hidden=(matching.length+others.length)-(shownMatching.length+shownOthers.length);

    const row=e=>html`<div class="ent-row ${cur===e?"sel":""}"
      @click=${()=>{obj[key]=e;this[fk]="";this._closeEntityPicker();}}>
      ${this._entityLabel(e)}</div>`;

    return html`<div class="field open"><label>${label}</label>
      <div class="search-row">
        <input id="sp_search_${key}" type="text" placeholder="${this.t("filter_entity")}"
          .value=${this[fk]||""}
          @input=${e=>{this[fk]=e.target.value;this.requestUpdate();}}
          @keydown=${e=>{if(e.key==="Escape")this._closeEntityPicker();}}>
        <button class="spin-btn" title="${this.t("btn_cancel")}"
          @click=${()=>this._closeEntityPicker()}>▴</button>
      </div>
      <div class="ent-list">
        ${shownMatching.length?html`<div class="ent-group">${this.t("ent_matching")}</div>`:""}
        ${shownMatching.map(row)}
        ${shownOthers.length&&shownMatching.length?html`<div class="ent-group">${this.t("ent_others")}</div>`:""}
        ${shownOthers.map(row)}
        ${!filtered.length?html`<div class="ent-row empty">${this.t("no_match")}</div>`:""}
        ${hidden>0?html`<div class="ent-row empty">${this.t("ent_more").replace("{n}",hidden)}</div>`:""}
      </div></div>`;
  }

  render(){
    // Wirft das Rendern, hängt Lit sich auf und der Nutzer sieht eine leere,
    // weisse Seite ohne jeden Hinweis. Lieber die Meldung anzeigen – damit
    // ist im Forum sofort klar, woran es liegt.
    try{
      return this._renderPanel();
    }catch(err){
      console.error("[shutter_pilot] Fehler beim Rendern des Panels:",err);
      return html`<div class="form">
        <h3>Shutter Pilot</h3>
        <div class="hint">Beim Aufbau der Ansicht ist ein Fehler aufgetreten:
          <code>${String(err?.message||err)}</code></div>
        <div class="hint">Bitte die Seite neu laden (Strg+F5). Bleibt es dabei,
          hilft diese Meldung samt Browser-Konsole (F12) im Issue weiter.</div>
        <div class="form-actions">
          <button class="btn save" @click=${()=>{this._editArea=null;this._editShutter=null;this._settings=null;this._tab="dashboard";this.requestUpdate();}}>Zurück zum Dashboard</button>
        </div></div>`;
    }
  }
  /* Auf schmalen Bildschirmen blendet Home Assistant die Seitenleiste aus.
     Ohne diesen Knopf kommt man aus dem Panel nur noch über den Zurück-Knopf
     des Browsers heraus – in der App gibt es den nicht immer. ha-menu-button
     ist das Original aus dem Frontend (klappt die Seitenleiste auf und zeigt
     auch den Benachrichtigungspunkt). Ist es nicht geladen, tut es ein
     eigener Knopf, der dasselbe Ereignis feuert. */
  _renderMenuButton(){
    if(!(this.narrow||this._isMobile))return "";
    if(customElements.get("ha-menu-button"))
      return html`<ha-menu-button class="menu-btn" .hass=${this.hass} .narrow=${true}></ha-menu-button>`;
    return html`<button class="menu-fallback" title="${this.t("menu")}" aria-label="${this.t("menu")}"
      @click=${()=>this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:true,composed:true}))}>
      <ha-icon icon="mdi:menu"></ha-icon></button>`;
  }
  _renderPanel(){
    const d=this._data;const T=k=>this.t(k);
    const verRaw=this._integrationVersion();
    const ver=verRaw?verRaw:"";
    const admin=this._isAdmin();
    // Ohne Administratorrechte bleibt nur das Dashboard. Der Tab-Zustand wird
    // hier abgefangen, damit auch ein alter Wert aus der Sitzung nicht in ein
    // Formular führt, das sich gar nicht speichern liesse.
    const tabs=admin?["dashboard","areas","shutters","settings"]:["dashboard"];
    const tab=tabs.includes(this._tab)?this._tab:"dashboard";
    return html`
      <div class="topbar"><div style="flex:1">
        <div class="title-row">
          ${this._renderMenuButton()}
          <h1>Shutter Pilot</h1>
          ${ver?html`<span class="sp-ver-badge" title="Shutter Pilot v${ver}" aria-label="Shutter Pilot Version ${ver}">v${ver}</span>`:""}
          ${d&&admin?html`<div class="master-row"><span>${T("master_switch")}</span>
            <ha-switch .checked=${d.master_enabled!==false} @change=${e=>this._toggleMaster(e.target.checked)}></ha-switch></div>`:""}
        </div>
        ${d?html`<div class="sub">${T("subtitle").replace("{a}",d.areas?.length||0).replace("{s}",d.shutters?.length||0)}</div>`:""}
        ${admin?"":html`<div class="sub">${T("admin_only")}</div>`}
      </div></div>
      ${tabs.length>1?html`<div class="tabs">
        ${tabs.map(t=>html`
          <div class="tab ${tab===t?"active":""}" @click=${()=>{this._tab=t;this._editArea=null;this._editShutter=null;this.requestUpdate();}}>
            ${T("tab_"+t)}</div>`)}
      </div>`:html`<div class="tabs-spacer"></div>`}
      ${!d?html`<div class="empty">${T("loading")}</div>`:
        tab==="dashboard"?this._renderDashboard(d):
        tab==="areas"?this._renderAreas(d):
        tab==="settings"?this._renderSettings(d):
        this._renderShutters(d)}`;
  }

  /* ─── Einstellungen ─── */
  _renderSettings(d){
    const T=k=>this.t(k);
    const s=this._settings??(this._settings={...(d.settings||{})});
    const w=d.weather||{};
    const fmt=v=>v==null?"–":v;
    return html`<div class="form">
      ${this._section("mdi:weather-partly-cloudy","sec_weather","sec_weather_sub")}
      <div class="hint">${T("f_weather_hint")}</div>
      ${this._entityField(s,"weather_entity",T("f_weather_entity"),["weather"],null)}
      ${s.weather_entity?html`
        <div class="kv" style="margin-top:10px">
          <div class="k">${T("w_temp_max")}</div><div class="v">${fmt(w.temp_max)}</div>
          <div class="k">${T("w_condition")}</div><div class="v">${fmt(w.condition)}</div>
          <div class="k">${T("w_updated")}</div>
          <div class="v">${w.updated?new Date(w.updated).toLocaleString():"–"}</div>
        </div>
        <div class="hint">${T("f_weather_sensors_hint")}</div>`:""}

      ${this._section("mdi:check-circle-outline","sec_verify","sec_verify_sub")}
      <div class="hint">${T("f_verify_hint")}</div>
      <div class="field"><label><input type="checkbox" .checked=${!!s.verify_enabled}
        @change=${e=>{s.verify_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_verify_enabled")}</label></div>
      ${s.verify_enabled?html`
        <div class="field"><label>${T("f_verify_after")}</label><div class="slider-row">
          <input type="range" min="5" max="180" step="5" .value=${s.verify_after??45}
            @input=${e=>{s.verify_after=Number(e.target.value);this.requestUpdate();}}>
          <span class="slider-val">${s.verify_after??45}s</span></div></div>
        <div class="field"><label>${T("f_verify_tolerance")}</label><div class="slider-row">
          <input type="range" min="1" max="30" .value=${s.verify_tolerance??8}
            @input=${e=>{s.verify_tolerance=Number(e.target.value);this.requestUpdate();}}>
          <span class="slider-val">${s.verify_tolerance??8}%</span></div></div>
        <div class="field"><label>${T("f_verify_retries")}</label><div class="slider-row">
          <input type="range" min="0" max="5" .value=${s.verify_retries??1}
            @input=${e=>{s.verify_retries=Number(e.target.value);this.requestUpdate();}}>
          <span class="slider-val">${s.verify_retries??1}</span></div></div>
        <div class="hint">${T("f_verify_event_hint")}</div>`:""}

      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveSettings()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
      </div></div>`;
  }
  async _saveSettings(){
    try{
      await this.hass.callWS({type:"shutter_pilot/save_settings",settings:{...this._settings}});
      this._settings=null;
      await this._load();
    }catch(e){console.warn(e);alert("Error: "+e.message);}
  }

  /* ─── Dashboard ─── */
  _renderDashboard(d){
    if(!d.areas?.length)return html`<div class="empty"><ha-icon icon="mdi:window-shutter-settings"></ha-icon><p>${this.t("empty_areas")}</p></div>`;
    return html`<div class="grid">${d.areas.map(a=>this._dashCard(a,d))}</div>`;
  }
  _dashCard(area,d){
    const id=area.id||"",name=area.name||id,mode=area.mode||"time";
    const sh=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id);
    const autoOn=d.auto_modes?.[id]!==false;
    return html`<div class="card">
      <div class="card-hdr"><div class="ic"><ha-icon icon="${MODE_ICONS[mode]||"mdi:blinds"}"></ha-icon></div>
        <div class="info"><h2>${name}</h2><span>${this._modeName(mode)} · ${sh.length} ${this.t("shutter_s")}</span></div></div>
      <div class="auto-row"><span class="lbl">${this.t("auto")}</span>
        <ha-switch .checked=${autoOn} ?disabled=${!this._isAdmin()}
          @change=${e=>this._toggleAuto(id,e.target.checked)}></ha-switch></div>
      ${mode==="sun"?this._renderSunInfo(area,d):""}
      ${mode==="time"?this._renderTimeInfo(area):""}
      ${mode==="brightness"?this._renderBrightnessInfo(area):""}
      ${area.sun_protect_enabled?this._renderSunProtectInfo(area,d):""}
      <div style="margin-top:8px">${sh.length===0?html`<div style="padding:8px 0;color:var(--txt2);font-size:13px">${this.t("no_shutters")}</div>`:
        sh.map(s=>{const st=this.hass?.states?.[s.cover_entity_id];const p=st?.attributes?.current_position;
          const autoOff=this._shutterAutoOff(s);
          return html`<div class="srow ${autoOff?"auto-off":""}"><span class="nm-wrap">${this._dashShutterRole(s,id)}<span class="nm">${st?.attributes?.friendly_name||s.name||s.cover_entity_id}</span>${autoOff?html`<ha-icon class="auto-off-ic" icon="mdi:robot-off-outline" title="${this.t("dash_shutter_auto_off")}"></ha-icon>`:""}</span><span class="srow-right">${this._shutterAutoSwitch(s)}<span class="pos">${p!=null?Math.round(p)+"%":"–"}</span></span></div>`;})}</div>
      <div class="actions">
        <button class="btn open" @click=${()=>this._coverAction(sh,"open")}><ha-icon icon="mdi:arrow-up-bold"></ha-icon>${this.t("btn_up")}</button>
        <button class="btn stop" @click=${()=>this._coverAction(sh,"stop")}><ha-icon icon="mdi:stop"></ha-icon>${this.t("btn_stop")}</button>
        <button class="btn close" @click=${()=>this._coverAction(sh,"close")}><ha-icon icon="mdi:arrow-down-bold"></ha-icon>${this.t("btn_down")}</button>
        <button class="btn sun" @click=${()=>this._coverAction(sh,"sun")}><ha-icon icon="mdi:sun-wireless-outline"></ha-icon>${this.t("btn_sun")}</button>
        <button class="btn vent" @click=${()=>this._coverAction(sh,"vent")}><ha-icon icon="mdi:air-filter"></ha-icon>${this.t("btn_vent")}</button>
      </div></div>`;
  }
  _renderSunProtectInfo(area,d){
    const id=area.id||"";
    const st=d.sun_protect_status?.[id]||{};
    const elev=d.sun?.elevation;
    const eMin=st.elevation_min??area.elevation_min??0;
    const eMax=st.elevation_max??area.elevation_max??area.elevation_threshold??15;
    const cur=elev!=null?Number(elev).toFixed(1)+"°":"–";
    const active=!!st.active;
    const inRange=!!st.in_range;
    let statusText=this.t("sun_prot_inactive");
    if(active)statusText=this.t("sun_prot_active");
    else if(inRange)statusText=this.t("sun_prot_waiting");
    const azEnabled=st.azimuth_enabled??!!area.azimuth_enabled;
    const azMin=st.azimuth_min??area.azimuth_min??90;
    const azMax=st.azimuth_max??area.azimuth_max??270;
    const azCur=st.current_azimuth!=null?Number(st.current_azimuth).toFixed(0)+"°":"–";
    return html`<div class="sun-protect-info ${active?"active":""}">
      <div class="sun-row"><ha-icon icon="mdi:sun-wireless-outline"></ha-icon>
        <span><b>${statusText}</b></span></div>
      <div class="sun-row"><ha-icon icon="mdi:angle-acute"></ha-icon>
        <span>${this.t("sun_prot_range")}: <b>${eMin}° – ${eMax}°</b> · ${this.t("sun_elevation")}: <b>${cur}</b></span></div>
      ${azEnabled?html`<div class="sun-row"><ha-icon icon="mdi:compass-outline"></ha-icon>
        <span>${this.t("sun_prot_direction")}: <b>${Math.round(azMin)}° – ${Math.round(azMax)}°</b> · ${this.t("sun_azimuth")}: <b>${azCur}</b>
        ${st.azimuth_in_range===false?html`<span class="sun-off"> · ${this.t("sun_prot_wrong_dir")}</span>`:""}</span></div>`:""}
    </div>`;
  }
  _renderSunInfo(area,d){
    const sun=d.sun||{};
    const offUp=parseInt(area.sunrise_offset)||0;
    const offDown=parseInt(area.sunset_offset)||0;
    const fmtTime=(iso,offsetMin)=>{
      if(!iso)return "–";
      try{const dt=new Date(iso);dt.setMinutes(dt.getMinutes()+offsetMin);return dt.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}catch(e){return "–";}
    };
    const fmtRaw=(iso)=>{
      if(!iso)return "–";
      try{return new Date(iso).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}catch(e){return "–";}
    };
    const elev=sun.elevation!=null?sun.elevation.toFixed(1)+"°":"–";
    /* Die tatsächliche Fahrzeit rechnet das Backend: Zeitklammern und der
       Präsenz-Jitter sind hier nicht nachbaubar. Fehlt sie (altes Backend,
       keine sun.sun), bleibt es beim bisherigen Verhalten. */
    const tr=(d.area_triggers||{})[area.id||""]||null;
    const bound=(kind,at)=>{
      if(!kind)return "";
      const lbl=kind==="earliest"?this.t("sun_bound_earliest"):this.t("sun_bound_latest");
      return html`<span class="sun-off">· ${lbl} ${at}</span>`;
    };
    const jitter=(min)=>min?html`<span class="sun-off">· ${this.t("sun_jitter")}: ${min>0?"+":""}${min} min</span>`:"";
    const triggerUp=tr&&tr.up?fmtRaw(tr.up):(offUp?fmtTime(sun.next_rising,offUp):fmtRaw(sun.next_rising));
    const triggerDown=tr&&tr.down?fmtRaw(tr.down):(offDown?fmtTime(sun.next_setting,offDown):fmtRaw(sun.next_setting));
    return html`<div class="sun-info">
      <div class="sun-row"><ha-icon icon="mdi:weather-sunset-up"></ha-icon>
        <span>${this.t("sun_next_rise")}: <b>${fmtRaw(sun.next_rising)}</b></span>
        ${offUp?html`<span class="sun-off">(${this.t("sun_offset")}: ${offUp>0?"+":""}${offUp} min → ${this.t("sun_trigger_up")} <b>${triggerUp}</b>)</span>`:
          html`<span class="sun-off">(${this.t("sun_trigger_up")} <b>${triggerUp}</b>)</span>`}
        ${tr?bound(tr.up_bound,tr.up_bound_time):""} ${tr?jitter(tr.up_jitter):""}</div>
      <div class="sun-row"><ha-icon icon="mdi:weather-sunset-down"></ha-icon>
        <span>${this.t("sun_next_set")}: <b>${fmtRaw(sun.next_setting)}</b></span>
        ${offDown?html`<span class="sun-off">(${this.t("sun_offset")}: ${offDown>0?"+":""}${offDown} min → ${this.t("sun_trigger_down")} <b>${triggerDown}</b>)</span>`:
          html`<span class="sun-off">(${this.t("sun_trigger_down")} <b>${triggerDown}</b>)</span>`}
        ${tr?bound(tr.down_bound,tr.down_bound_time):""} ${tr?jitter(tr.down_jitter):""}</div>
      <div class="sun-row"><ha-icon icon="mdi:angle-acute"></ha-icon>
        <span>${this.t("sun_elevation")}: <b>${elev}</b></span></div>
    </div>`;
  }
  _renderTimeInfo(area){
    const isWeekend=(()=>{const day=(new Date()).getDay();return day===0||day===6;})();
    const wUp=area.time_up||"07:00";
    const wDown=area.time_down||"19:00";
    const weUp=area.time_we_up||wUp;
    const weDown=area.time_we_down||wDown;
    const isGerman=this._lang==="de";
    const activePrefix=isGerman?"Heute aktiv":"Active today";
    const activeProfile=isWeekend
      ? (isGerman?"Wochenendprofil":"Weekend profile")
      : (isGerman?"Wochenprofil":"Weekday profile");
    return html`<div class="time-info ${isWeekend?"weekend":""}">
      <div class="sun-row"><ha-icon icon="mdi:calendar-today"></ha-icon>
        <span>${activePrefix}: <b>${activeProfile}</b></span></div>
      <div class="sun-row"><ha-icon icon="mdi:calendar-week"></ha-icon>
        <span>${this.t("f_time_up")}: <b>${wUp}</b> · ${this.t("f_time_down")}: <b>${wDown}</b></span></div>
      <div class="sun-row"><ha-icon icon="mdi:calendar-weekend"></ha-icon>
        <span>${this.t("f_time_we_up")}: <b>${weUp}</b> · ${this.t("f_time_we_down")}: <b>${weDown}</b></span></div>
    </div>`;
  }
  _renderBrightnessInfo(area){
    const luxDown=Number.isFinite(Number(area.lux_down))?Number(area.lux_down):400;
    const luxUp=Number.isFinite(Number(area.lux_up))?Number(area.lux_up):500;
    const rawRef=(area.brightness_sensor||"").trim();
    const sensorId=this._resolveBrightnessSensorEntity(this.hass,rawRef);
    const luxNow=this._readLux(this.hass,sensorId);
    const st=sensorId&&this.hass?.states?.[sensorId];
    const sensorLabel=rawRef?(st?.attributes?.friendly_name||sensorId||rawRef):"";
    const wUpFrom=area.w_up_from||"05:00";
    const wUpTo=area.w_up_to||"09:00";
    const wDownFrom=area.w_down_from||"16:00";
    const wDownTo=area.w_down_to||"23:59";
    const weUpFrom=area.we_up_from||"07:00";
    const weUpTo=area.we_up_to||"10:00";
    const weDownFrom=area.we_down_from||"16:00";
    const weDownTo=area.we_down_to||"23:59";
    const luxDisp=luxNow!=null&&!Number.isNaN(luxNow)?`${Number(luxNow).toFixed(1)} lx`:"–";
    return html`<div class="brightness-info">
      <div class="sun-row"><ha-icon icon="mdi:brightness-6"></ha-icon>
        <span>${this.t("dash_current_lux")}: <b>${luxDisp}</b>${rawRef?html`<span class="sun-off"> · ${sensorLabel}</span>`:""}</span></div>
      <div class="sun-row"><ha-icon icon="mdi:weather-sunny-alert"></ha-icon>
        <span>${this.t("f_lux_down")}: <b>${luxDown} lx</b> · ${this.t("f_lux_up")}: <b>${luxUp} lx</b></span></div>
      <div class="sun-row"><ha-icon icon="mdi:calendar-week"></ha-icon>
        <span>${this.t("f_w_up_from")}: <b>${wUpFrom}</b> – <b>${wUpTo}</b> · ${this.t("f_w_down_from")}: <b>${wDownFrom}</b> – <b>${wDownTo}</b></span></div>
      <div class="sun-row"><ha-icon icon="mdi:calendar-weekend"></ha-icon>
        <span>${this.t("f_we_up_from")}: <b>${weUpFrom}</b> – <b>${weUpTo}</b> · ${this.t("f_we_down_from")}: <b>${weDownFrom}</b> – <b>${weDownTo}</b></span></div>
    </div>`;
  }

  /* ─── Areas Tab ─── */
  _renderAreas(d){
    if(this._editArea)return this._renderAreaForm(d);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editArea={id:"",name:"",mode:"time",drive_delay:10,workday_sensor:"",random_offset:0,manual_override:"never",sun_protect_enabled:false,elevation_min:0,elevation_max:15,azimuth_enabled:false,azimuth_min:90,azimuth_max:270,season_from:"",season_to:"",sun_cond_close_entity:"",sun_cond_a_entity:"",sun_cond_a_on_above:"",sun_cond_a_off_below:"",sun_cond_b_entity:"",sun_cond_b_on_above:"",sun_cond_b_off_below:"",sun_cond_c_entity:"",sun_cond_d_entity:"",down_light_entity:"",down_light_brightness:40,time_up:"07:00",time_down:"19:00",time_we_up:"08:00",time_we_down:"20:00",sunrise_offset:0,sunset_offset:0,brightness_sensor:"",lux_down:400,lux_up:500,w_up_from:"05:00",w_up_to:"09:00",w_down_from:"16:00",w_down_to:"23:59",we_up_from:"07:00",we_up_to:"10:00",we_down_from:"16:00",we_down_to:"23:59",_isNew:true};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${this.t("add_area")}</button></div>
      ${!d.areas?.length?html`<div class="empty">${this.t("empty_areas_list")}</div>`:
        this._isMobile?html`
          <div class="grid">
            ${d.areas.map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
              const name=a.name||id||"–";
              const mode=a.mode||"time";
              return html`<div class="card">
                <div class="card-hdr">
                  <div class="ic"><ha-icon icon="mdi:map-marker"></ha-icon></div>
                  <div class="info">
                    <h2 style="margin:0;font-size:16px">${name}</h2>
                    <span style="font-size:12px">${this._modeName(mode)} · ${cnt} ${this.t("shutter_s")}${cnt===1?"":"n"}</span>
                  </div>
                </div>
                <div class="row-actions">
                  <button class="btn edit" @click=${()=>{this._editArea={...a,_isNew:false};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteArea(id)}><ha-icon icon="mdi:delete"></ha-icon></button>
                </div>
              </div>`;})}
          </div>
        `:html`
          <div class="card"><div class="table-wrap"><table>
            <tr><th>${this.t("col_name")}</th><th>${this.t("col_id")}</th><th>${this.t("col_mode")}</th><th>${this.t("col_shutters")}</th><th></th></tr>
            ${d.areas.map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
              return html`<tr>
                <td><strong>${a.name||id}</strong></td><td style="color:var(--txt2)">${id}</td>
                <td><span class="chip ${a.mode||"time"}">${this._modeName(a.mode)}</span></td>
                <td>${cnt}</td>
                <td style="text-align:right">
                  <button class="btn edit" @click=${()=>{this._editArea={...a,_isNew:false};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteArea(id)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
          </table></div></div>
        `}`;
  }
  _renderAreaForm(){
    const a=this._editArea;const m=a.mode||"time";const T=k=>this.t(k);
    /* Kein requestUpdate() beim Tippen: Jedes Re-Render setzt .value neu und
       reißt damit die Cursorposition bzw. den nativen Zeit-Dialog weg. Der
       Wert steht im Objekt, gerendert werden muss dafür nichts. */
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${a[k]??""} @input=${e=>{a[k]=type==="number"?Number(e.target.value):e.target.value;}}></div>`;
    const tm=(k,lbl)=>this._timeField(a,k,lbl);
    // Klammern dürfen leer bleiben, deshalb allowEmpty.
    const bd=(k,lbl,dflt)=>this._timeField(a,k,lbl,dflt,true);
    const rng=(k,lbl,min,max,step=1,suffix="")=>html`<div class="field"><label>${lbl}</label><div class="slider-row">
      <input type="range" min="${min}" max="${max}" step="${step}" .value=${a[k]??min} @input=${e=>{a[k]=Number(e.target.value);this.requestUpdate();}}>
      <span class="slider-val">${a[k]??min}${suffix}</span></div></div>`;
    const ep=(k,lbl,domains,hint=null)=>this._entityField(a,k,lbl,domains,hint);
    return html`<div class="form"><h3>${a._isNew?T("add_area"):T("edit_area")}</h3>

      ${this._section("mdi:tag-outline","sec_basics")}
      ${f("name",T("f_name"))}
      ${a._isNew?"":html`<div class="field"><label>${T("col_id")}</label><input disabled .value=${a.id}></div>`}
      <div class="field"><label>${T("f_mode")}</label>
        <select .value=${m} @change=${e=>{a.mode=e.target.value;this.requestUpdate();}}>
          <option value="time" ?selected=${m==="time"}>${T("mode_time")}</option>
          <option value="brightness" ?selected=${m==="brightness"}>${T("mode_brightness")}</option>
          <option value="sun" ?selected=${m==="sun"}>${T("mode_sun")}</option></select></div>
      ${rng("drive_delay",T("f_drive_delay"),0,120,1,"s")}

      ${this._section(MODE_ICONS[m]||"mdi:clock-outline","sec_schedule","sec_schedule_"+m)}
      ${m==="time"?html`${tm("time_up",T("f_time_up"))}${tm("time_down",T("f_time_down"))}${tm("time_we_up",T("f_time_we_up"))}${tm("time_we_down",T("f_time_we_down"))}`:
        m==="sun"?html`${rng("sunrise_offset",T("f_sunrise_off"),-60,60,1," min")}${rng("sunset_offset",T("f_sunset_off"),-60,60,1," min")}
          <div class="hint" style="margin-top:10px"><b>${T("f_bounds_title")}</b><br>${T("f_bounds_hint")}</div>
          ${bd("sun_earliest_up",T("f_earliest_up"),"07:30")}${bd("sun_latest_up",T("f_latest_up"),"09:00")}
          ${bd("sun_earliest_down",T("f_earliest_down"),"17:00")}${bd("sun_latest_down",T("f_latest_down"),"22:30")}
          <div class="hint">${T("f_bounds_we_hint")}</div>
          ${bd("sun_we_earliest_up",T("f_we_earliest_up"),"08:00")}${bd("sun_we_latest_up",T("f_we_latest_up"),"09:00")}
          ${bd("sun_we_earliest_down",T("f_we_earliest_down"),"17:00")}${bd("sun_we_latest_down",T("f_we_latest_down"),"22:30")}`:
        html`${ep("brightness_sensor",T("f_brightness_sensor"),["sensor"],HINTS.illuminance)}${rng("lux_up",T("f_lux_up"),0,1000,1," lx")}${rng("lux_down",T("f_lux_down"),0,1000,1," lx")}
          ${tm("w_up_from",T("f_w_up_from"))}${tm("w_up_to",T("f_w_up_to"))}${tm("w_down_from",T("f_w_down_from"))}${tm("w_down_to",T("f_w_down_to"))}
          ${tm("we_up_from",T("f_we_up_from"))}${tm("we_up_to",T("f_we_up_to"))}${tm("we_down_from",T("f_we_down_from"))}${tm("we_down_to",T("f_we_down_to"))}`}

      ${this._section("mdi:calendar-check","sec_calendar")}
      ${ep("workday_sensor",T("f_workday_sensor"),["binary_sensor"],HINTS.workday)}
      <div class="hint">${T("f_workday_hint")}</div>
      ${rng("random_offset",T("f_random_offset"),0,60,1," min")}
      <div class="hint">${T("f_random_offset_hint")}</div>
      <div class="field"><label>${T("f_manual_override")}</label>
        <select .value=${a.manual_override||"never"} @change=${e=>{a.manual_override=e.target.value;this.requestUpdate();}}>
          ${OVERRIDE_OPTS.map(o=>html`<option value="${o}" ?selected=${(a.manual_override||"never")===o}>${T("f_override_"+o)}</option>`)}
        </select><div class="hint">${T("f_manual_override_hint")}</div></div>

      ${this._section("mdi:sun-wireless-outline","sec_sunprotect")}
      <div class="field"><label><input type="checkbox" .checked=${!!a.sun_protect_enabled} @change=${e=>{a.sun_protect_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_sun_protect")}</label></div>
      ${a.sun_protect_enabled?html`
        ${rng("elevation_min",T("f_elev_min"),-5,45,0.5,"°")}${rng("elevation_max",T("f_elev_max"),-5,90,0.5,"°")}
        <div class="field"><label><input type="checkbox" .checked=${!!a.azimuth_enabled} @change=${e=>{a.azimuth_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_azimuth")}</label>
          <div class="hint">${T("f_azimuth_hint")}</div></div>
        ${a.azimuth_enabled?html`
          <div class="field"><label>${T("f_azimuth_preset")}</label>
            <div class="preset-row">${COMPASS_PRESETS.map(p=>html`
              <button class="btn preset ${(Number(a.azimuth_min)===p.min&&Number(a.azimuth_max)===p.max)?"active":""}"
                @click=${()=>{a.azimuth_min=p.min;a.azimuth_max=p.max;this.requestUpdate();}}>${T("compass_"+p.key)}</button>`)}
            </div></div>
          ${rng("azimuth_min",T("f_azimuth_min"),0,360,5,"°")}${rng("azimuth_max",T("f_azimuth_max"),0,360,5,"°")}`:""}
        <div class="field"><label>${T("f_season")}</label>
          <div class="time-row">
            <select .value=${String(a.season_from||"")} @change=${e=>{a.season_from=e.target.value;this.requestUpdate();}}>
              <option value="">${T("f_season_all")}</option>
              ${MONTHS.map(m=>html`<option value="${m}" ?selected=${String(a.season_from)===String(m)}>${T("month_"+m)}</option>`)}
            </select><span class="time-sep">–</span>
            <select .value=${String(a.season_to||"")} @change=${e=>{a.season_to=e.target.value;this.requestUpdate();}}>
              <option value="">${T("f_season_all")}</option>
              ${MONTHS.map(m=>html`<option value="${m}" ?selected=${String(a.season_to)===String(m)}>${T("month_"+m)}</option>`)}
            </select></div>
          <div class="hint">${T("f_season_hint")}</div></div>
        <div class="hint" style="margin-top:10px"><b>${T("f_sun_cond_title")}</b><br>${T("f_sun_cond_hint")}</div>
        ${this._renderConditionSlots(a,ep,f)}`:""}

      ${this._section("mdi:arrow-collapse-down","sec_altclose","sec_altclose_sub")}
      <div class="hint">${T("f_close_cond_hint")}</div>
      ${ep("sun_cond_close_entity",T("f_close_cond"),["binary_sensor","sensor","weather"],HINTS.condition)}
      ${a.sun_cond_close_entity?this._renderCondDetail(a,"close",a.sun_cond_close_entity,f):""}
      ${this._section("mdi:lightbulb-outline","sec_light","sec_light_sub")}
      ${ep("down_light_entity",T("f_light_entity"),["light","switch"])}
      ${rng("down_light_brightness",T("f_light_brightness"),0,100,1,"%")}

      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveArea()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
        <button class="btn cancel" @click=${()=>{this._editArea=null;this.requestUpdate();}}>${T("btn_cancel")}</button></div></div>`;
  }

  /* ─── Shutters Tab ─── */
  _renderShutters(d){
    if(this._editShutter)return this._renderShutterForm(d);
    const areaName=id=>{const a=d.areas.find(x=>x.id===id);return a?a.name:id;};const T=k=>this.t(k);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editShutter={cover_entity_id:"",name:"",window_entity_id:"",window_open_state:"on",window_tilted_state:"none",position_when_window_open:100,position_when_window_tilted:50,lock_protection:false,window_tilted_entity_id:"",min_position_when_open:20,area_up_id:d.areas[0]?.id||"",area_down_id:d.areas[0]?.id||"",position_open:100,position_closed:0,position_sun_protect:50,position_closed_alt:"",sun_geometry_override:false,tilt_enabled:false,tilt_open:100,tilt_closed:0,tilt_sun_protect:30,drive_after_close:false,_isNew:true,_index:null};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${T("add_shutter")}</button></div>
      ${!d.shutters?.length?html`<div class="empty">${T("empty_shutters_list")}</div>`:
        this._isMobile?html`
          <div class="grid">
            ${d.shutters.map((s,i)=>{const st=this.hass?.states?.[s.cover_entity_id];
              const friendly=st?.attributes?.friendly_name||"";
              const entityId=s.cover_entity_id||"";
              const title=s.name||friendly||entityId||"–";
              const coverLine=friendly||entityId||"–";
              return html`<div class="card">
                <div class="card-hdr">
                  <div class="ic"><ha-icon icon="mdi:window-shutter"></ha-icon></div>
                  <div class="info">
                    <h2 style="margin:0;font-size:16px">${title}</h2>
                    <span style="font-size:12px">${coverLine}${entityId&&friendly?html`<span class="sun-off"> · ${entityId}</span>`:""}</span>
                  </div>
                </div>
                <div class="auto-row"><span class="lbl">${T("auto")}</span>${this._shutterAutoSwitch(s)}</div>
                <div class="kv">
                  <div class="k">${T("col_area_up")}</div><div class="v">${areaName(s.area_up_id)||"–"}</div>
                  <div class="k">${T("col_area_down")}</div><div class="v">${areaName(s.area_down_id)||"–"}</div>
                  <div class="k">${T("col_window")}</div><div class="v">${s.window_entity_id||"–"}</div>
                </div>
                <div class="row-actions">
                  <button class="btn edit" @click=${()=>{this._editShutter={...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteShutter(i)}><ha-icon icon="mdi:delete"></ha-icon></button>
                </div>
              </div>`;})}
          </div>
        `:html`
          <div class="card"><div class="table-wrap"><table>
            <tr><th>${T("col_name")}</th><th>${T("col_cover")}</th><th>${T("col_area_up")}</th><th>${T("col_area_down")}</th><th>${T("col_window")}</th><th>${T("auto")}</th><th></th></tr>
            ${d.shutters.map((s,i)=>{const st=this.hass?.states?.[s.cover_entity_id];
              return html`<tr>
                <td><strong>${s.name||"–"}</strong></td>
                <td style="color:var(--txt2)">${st?.attributes?.friendly_name||s.cover_entity_id}</td>
                <td>${areaName(s.area_up_id)}</td><td>${areaName(s.area_down_id)}</td>
                <td>${s.window_entity_id||"–"}</td>
                <td>${this._shutterAutoSwitch(s)}</td>
                <td style="text-align:right">
                  <button class="btn edit" @click=${()=>{this._editShutter={...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteShutter(i)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
          </table></div></div>
        `}`;
  }
  _renderShutterForm(d){
    const s=this._editShutter;const areas=d.areas||[];const T=k=>this.t(k);
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${s[k]??""} @input=${e=>{s[k]=type==="number"?Number(e.target.value):e.target.value;}}></div>`;
    const pct=(k,lbl)=>html`<div class="field"><label>${lbl}</label><div class="slider-row">
      <input type="range" min="0" max="100" .value=${s[k]??0} @input=${e=>{s[k]=Number(e.target.value);this.requestUpdate();}}>
      <span class="slider-val">${s[k]??0}%</span></div></div>`;
    const ep=(k,lbl,domains,hint=null)=>this._entityField(s,k,lbl,domains,hint);
    const pctRange=(k,lbl,min,max,step=1,suffix="")=>html`<div class="field"><label>${lbl}</label><div class="slider-row">
      <input type="range" min="${min}" max="${max}" step="${step}" .value=${s[k]??min} @input=${e=>{s[k]=Number(e.target.value);this.requestUpdate();}}>
      <span class="slider-val">${s[k]??min}${suffix}</span></div></div>`;
    const sel=(k,lbl,opts)=>html`<div class="field"><label>${lbl}</label><select .value=${s[k]||""} @change=${e=>{s[k]=e.target.value;this.requestUpdate();}}>
      ${opts.map(o=>typeof o==="string"?html`<option value="${o}" ?selected=${s[k]===o}>${o}</option>`:html`<option value="${o.v}" ?selected=${s[k]===o.v}>${o.l}</option>`)}</select></div>`;
    const areaSel=(k,lbl)=>sel(k,lbl,areas.map(a=>({v:a.id,l:a.name||a.id})));
    return html`<div class="form"><h3>${s._isNew?T("add_shutter"):T("edit_shutter")}</h3>

      ${this._section("mdi:window-shutter","sec_shutter")}
      ${ep("cover_entity_id",T("f_cover"),["cover"],null)}
      ${f("name",T("f_name"))}
      <div class="field"><label><input type="checkbox" .checked=${s.automation_enabled!==false}
        @change=${e=>{s.automation_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_shutter_auto")}</label>
        <div class="hint">${T("f_shutter_auto_hint")}</div></div>

      ${this._section("mdi:map-marker","sec_areas","sec_areas_sub")}
      ${areaSel("area_up_id",T("f_area_up"))}
      ${areaSel("area_down_id",T("f_area_down"))}

      ${this._section("mdi:arrow-up-down","sec_positions")}
      ${pct("position_open",T("f_pos_open"))}
      ${pct("position_closed",T("f_pos_closed"))}
      ${pct("position_sun_protect",T("f_pos_sun"))}
      <div class="field"><label><input type="checkbox" .checked=${s.position_closed_alt!==""&&s.position_closed_alt!=null}
        @change=${e=>{s.position_closed_alt=e.target.checked?50:"";this.requestUpdate();}}> ${T("f_pos_closed_alt")}</label>
        <div class="hint">${T("f_pos_closed_alt_hint")}</div></div>
      ${s.position_closed_alt!==""&&s.position_closed_alt!=null?pct("position_closed_alt",T("f_pos_closed_alt_val")):""}

      ${this._section("mdi:sun-compass","sec_shutter_sun","sec_shutter_sun_sub")}
      <div class="field"><label><input type="checkbox" .checked=${!!s.sun_geometry_override}
        @change=${e=>{s.sun_geometry_override=e.target.checked;this.requestUpdate();}}> ${T("f_geo_override")}</label>
        <div class="hint">${T("f_geo_override_hint")}</div></div>
      <div class="hint">${T("f_shutter_cond_hint")}</div>
      ${this._renderConditionSlots(s,ep,f)}
      ${s.sun_geometry_override?html`
        ${pctRange("elevation_min",T("f_elev_min"),-5,45,0.5,"°")}
        ${pctRange("elevation_max",T("f_elev_max"),-5,90,0.5,"°")}
        <div class="field"><label><input type="checkbox" .checked=${!!s.azimuth_enabled}
          @change=${e=>{s.azimuth_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_azimuth")}</label></div>
        ${s.azimuth_enabled?html`
          <div class="field"><label>${T("f_azimuth_preset")}</label>
            <div class="preset-row">${COMPASS_PRESETS.map(p=>html`
              <button class="btn preset ${(Number(s.azimuth_min)===p.min&&Number(s.azimuth_max)===p.max)?"active":""}"
                @click=${()=>{s.azimuth_min=p.min;s.azimuth_max=p.max;this.requestUpdate();}}>${T("compass_"+p.key)}</button>`)}
            </div></div>
          ${pctRange("azimuth_min",T("f_azimuth_min"),0,360,5,"°")}
          ${pctRange("azimuth_max",T("f_azimuth_max"),0,360,5,"°")}`:""}`:""}

      ${this._section("mdi:window-open-variant","sec_window","sec_window_sub")}
      ${ep("window_entity_id",T("f_window_sensor"),["binary_sensor","sensor"],HINTS.window)}
      ${s.window_entity_id||s.window_tilted_entity_id?html`
        ${ep("window_tilted_entity_id",T("f_window_tilt_sensor"),["binary_sensor","sensor"],HINTS.window)}
        <div class="hint">${T("f_window_tilt_sensor_hint")}</div>`:""}
      ${sel("window_open_state",T("f_win_open"),WIN_OPEN_OPTS)}
      ${sel("window_tilted_state",T("f_win_tilt"),
        [{v:"none",l:T("f_win_tilt_none")},...WIN_TILT_OPTS.filter(x=>x!=="none").map(x=>({v:x,l:x}))])}
      ${pct("position_when_window_open",T("f_pos_win_open"))}
      ${pct("position_when_window_tilted",T("f_pos_win_tilt"))}
      ${(!s.window_tilted_state||s.window_tilted_state==="none")?html`<div class="hint">${T("f_pos_win_tilt_2state_hint")}</div>`:""}
      <div class="field"><label><input type="checkbox" .checked=${!!s.lock_protection} @change=${e=>{s.lock_protection=e.target.checked;this.requestUpdate();}}> ${T("f_lock")}</label></div>
      ${s.lock_protection?pct("min_position_when_open",T("f_min_pos")):""}
      <div class="field"><label><input type="checkbox" .checked=${!!s.drive_after_close} @change=${e=>{s.drive_after_close=e.target.checked;this.requestUpdate();}}> ${T("f_drive_after")}</label>
        <div class="hint">${T("f_drive_after_hint")}</div></div>

      ${this._section("mdi:blinds-horizontal","sec_slats","sec_slats_sub")}
      <div class="field"><label><input type="checkbox" .checked=${!!s.tilt_enabled} @change=${e=>{s.tilt_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_tilt")}</label>
        <div class="hint">${this._supportsTilt(s.cover_entity_id)?T("f_tilt_hint"):T("f_tilt_unsupported")}</div></div>
      ${s.tilt_enabled?html`${pct("tilt_open",T("f_tilt_open"))}${pct("tilt_closed",T("f_tilt_closed"))}${pct("tilt_sun_protect",T("f_tilt_sun"))}`:""}

      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveShutter()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
        <button class="btn cancel" @click=${()=>{this._editShutter=null;this.requestUpdate();}}>${T("btn_cancel")}</button></div></div>`;
  }

  /* ─── Actions ─── */
  _supportsTilt(entityId){
    // CoverEntityFeature.SET_TILT_POSITION === 128
    const st=entityId&&this.hass?.states?.[entityId];
    if(!st)return true;
    const f=Number(st.attributes?.supported_features||0);
    return !f||!!(f&128);
  }
  async _toggleAuto(id,on){try{await this.hass.callWS({type:"shutter_pilot/set_auto_mode",area_id:id,enabled:on});await this._load();}catch(e){console.warn(e);}}
  async _toggleMaster(on){try{await this.hass.callWS({type:"shutter_pilot/set_master_enabled",enabled:on});await this._load();}catch(e){console.warn(e);}}
  _coverAction(shutters,action){
    const eids=shutters.map(s=>s.cover_entity_id).filter(Boolean);
    if(!eids.length)return;
    if(action==="open")this.hass.callService("cover","open_cover",{entity_id:eids});
    else if(action==="close")this.hass.callService("cover","close_cover",{entity_id:eids});
    else if(action==="stop")this.hass.callService("cover","stop_cover",{entity_id:eids});
    else if(action==="sun"){for(const s of shutters){const eid=s.cover_entity_id;const pos=s.position_sun_protect??50;if(eid)this.hass.callService("cover","set_cover_position",{entity_id:eid,position:pos});}}
    // Lüften nutzt dieselbe Position wie ein gekipptes Fenster.
    else if(action==="vent"){for(const s of shutters){const eid=s.cover_entity_id;const pos=s.position_when_window_tilted??50;if(eid)this.hass.callService("cover","set_cover_position",{entity_id:eid,position:pos});}}
  }
  async _saveArea(){
    const a={...this._editArea};delete a._isNew;delete a._index;
    if(!a.id){a.id=a.name.toLowerCase().replace(/[äÄ]/g,"ae").replace(/[öÖ]/g,"oe").replace(/[üÜ]/g,"ue").replace(/[ß]/g,"ss").replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")||"area";}
    try{await this.hass.callWS({type:"shutter_pilot/save_area",area:a});this._editArea=null;await this._load();}catch(e){console.warn(e);alert("Error: "+e.message);}
  }
  async _deleteArea(id){
    if(!confirm(this.t("confirm_del_area").replace("{id}",id)))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_area",area_id:id});await this._load();}catch(e){console.warn(e);}
  }
  async _saveShutter(){
    const s={...this._editShutter};const idx=s._index;delete s._isNew;delete s._index;
    try{await this.hass.callWS({type:"shutter_pilot/save_shutter",shutter:s,index:idx});this._editShutter=null;await this._load();}catch(e){console.warn(e);alert("Error: "+e.message);}
  }
  async _deleteShutter(idx){
    if(!confirm(this.t("confirm_del_shutter")))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_shutter",index:idx});await this._load();}catch(e){console.warn(e);}
  }
}
if(!customElements.get("shutter-pilot-panel")){
  customElements.define("shutter-pilot-panel",ShutterPilotPanel);
}
