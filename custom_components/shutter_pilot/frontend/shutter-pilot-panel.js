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
const WIN_OPEN_OPTS = ["on","off","open","true","offen"];
const WIN_TILT_OPTS = ["none","tilted","gekippt","kipp","2"];
// Mirrors _STATE_SYNONYMS in window_helper.py. Used only to tell the user
// whether the picked word can ever match what the contact reports.
const WIN_STATE_SYNONYMS = {on:"on",true:"on",1:"on",open:"on",offen:"on","geöffnet":"on",geoeffnet:"on",auf:"on",
  off:"off",false:"off",0:"off",closed:"off",geschlossen:"off",zu:"off"};
const winCanon = v => { const t=String(v??"").toLowerCase().trim(); return WIN_STATE_SYNONYMS[t]||t; };
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
  sec_basics:"Grunddaten",sec_basics_sub:"Name, Modus, Abstand zwischen den Fahrten",sec_calendar_sub:"Feiertage, Zufallsversatz, manuelle Übersteuerung",sec_sunprotect_sub:"Sonnenhöhe, Richtung, Bedingungen",sec_shutter_sub:"Entität, Name, Automatik",sec_positions_sub:"offen, geschlossen, Sonnenschutz, Frost",
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
  f_cond_on:"Trifft zu ab",
  f_cond_off:"Aufheben unter",
  f_cond_num_hint:"„Aufheben unter“ darf niedriger sein als „Trifft zu ab“ – der Abstand verhindert Flattern, wenn der Wert um die Schwelle pendelt. Leer = gleicher Wert.",
  f_close_cond_both_hint:"Sind beide Bedingungen eingetragen, muss abends auch beides zutreffen.",
  f_sun_cond_num_hint:"„Aufheben unter“ darf niedriger sein als „Beschatten ab“ – der Abstand verhindert Flattern bei durchziehenden Wolken. Leer = gleicher Wert.",
  f_sun_cond_wrong_way:"Die beiden Werte stehen verkehrt herum. Das ist ein Einschaltpunkt mit einem Aufhebepunkt DARUNTER, kein Bereich von–bis. So wie es dasteht, wird der zweite Wert verworfen und die Bedingung ist praktisch immer erfüllt. Für einen Bereich von Himmelsrichtungen gibt es „Nur bei passender Fensterrichtung“.",
  f_geo_override_values_hint:"Diese beiden Werte gelten jetzt statt derer des Bereichs – auch wenn du sie nicht anfasst.",
  sec_export:"Einstellungen exportieren",
  sec_export_sub:"für Fehlerberichte im Forum",
  f_export_hint:"Erzeugt einen Bericht mit allen Einstellungen, den aktuellen Sensorwerten und der Beschattungs-Entscheidung von genau jetzt – je Rollladen mit Begründung. Den Text ins Forum stellen, dann muss niemand raten, was eingestellt ist. Enthalten sind nur Shutter Pilots eigene Einstellungen und die Namen der von dir gewählten Entitäten, keine Zugangsdaten und kein Standort.",
  btn_export:"Bericht erzeugen",
  btn_export_copy:"Kopieren",
  btn_export_copied:"Kopiert ✓",
  btn_export_download:"Herunterladen",
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
  f_elev_min:"Sonnenschutz ab Elevation (°)",
  f_elev_enabled:"Sonnenhöhe prüfen",
  f_elev_enabled_hint:"Aus: die Sonnenhöhe spielt keine Rolle, es entscheiden allein die Bedingungen. Sinnvoll, wenn ein Helligkeitssensor am Fenster hängt – der misst die Sonne bereits.",
  f_temp_sensor:"Raumtemperatur (nur Anzeige, optional)",
  f_temp_sensor_hint:"Wird auf der Karte im Dashboard angezeigt und entscheidet nichts. Als Bedingung gehört ein Temperatursensor unter „Sonnenschutz“ oder „Abweichendes Schliessen“.",
  dash_room_temp:"Raumtemperatur",f_elev_max:"Sonnenschutz bis Elevation (°)",
  master_switch:"System aktiv",
  sun_prot_active:"Sonnenschutz aktiv",sun_prot_inactive:"Sonnenschutz inaktiv",
  sun_prot_range:"Elevation-Bereich",
  sun_prot_cond_pending:"Sonnenhöhe passt – Bedingungen noch nicht erfüllt",f_sun_off_hint:"Plus verschiebt nach hinten, Minus nach vorn: −15 fährt eine Viertelstunde vor Sonnenaufgang bzw. Sonnenuntergang, +15 eine Viertelstunde danach.",btn_duplicate:"Duplizieren",copy_suffix:"(Kopie)",sun_prot_waiting:"Warte auf passende Sonnenhöhe",
  f_light_entity:"Lampe/Schalter bei Runter (optional)",f_light_brightness:"Lampe Helligkeit (%)",
  f_time_up:"Woche Hoch",f_time_down:"Woche Runter",
  f_time_we_up:"Wochenende Hoch",f_time_we_down:"Wochenende Runter",
  f_sunrise_off:"Offset Sonnenaufgang (Min.)",f_sunset_off:"Offset Sonnenuntergang (Min.)",
  sun_next_rise:"Nächster Sonnenaufgang",sun_next_set:"Nächster Sonnenuntergang",
  sun_trigger_up:"Hoch-Fahrt um",sun_trigger_down:"Runter-Fahrt um",
  f_sun_cond_add:"Zustand eintragen und Enter",f_sun_cond_add_hint:"Ein Textsensor meldet immer nur seinen aktuellen Zustand – die übrigen lassen sich hier von Hand ergänzen. Gross- und Kleinschreibung ist egal.",
  f_blind_drive:"Antrieb meldet keine Position (blind fahren)",f_blind_drive_hint:"Für einseitigen Funk wie Somfy RTS. Shutter Pilot rechnet dann mit der zuletzt gesendeten Position, statt aufzugeben – nur so funktionieren Fenstertrigger und automatisches Lüften auch bei solchen Antrieben.",
  f_copy_from:"Einstellungen übernehmen von",f_copy_pick:"– Rollladen wählen –",f_copy_btn:"Übernehmen",f_copy_hint:"Kopiert Positionen, Lamellen, Beschattung, Bedingungen und Fenster-Einstellungen. Cover-Entität, Name, Bereiche und Fenstersensoren bleiben unverändert.",
  f_sunbound_title:"Zusätzliche Sonnengrenzen",f_sunbound_hint:"Verhindert Fahrten am helllichten Tag, etwa wenn ein Gewitter die Helligkeit einbrechen lässt. Leer = keine Grenze.",f_b_down_sunset:"Runter frühestens X Min. vor Sonnenuntergang",f_b_up_sunrise:"Hoch frühestens X Min. vor Sonnenaufgang",
  f_shade_hold:"Beschattung halten (Min.)",f_shade_hold_hint:"Zieht eine Wolke durch, endet die Bedingung sofort und der Rollladen fährt auf. So lange bleibt die Beschattung trotzdem stehen. 0 = sofort auffahren.",
  sec_drive:"Fahrbefehle",sec_drive_sub:"Abstand zwischen zwei Befehlen",f_min_gap:"Mindestabstand zwischen Fahrbefehlen",f_min_gap_hint:"Funk-Empfänger (433 MHz, HmIP) verschlucken Befehle, die gleichzeitig ankommen. Die Verzögerung im Bereich hilft dort nicht: jeder Bereich fährt für sich. Hier wird jeder Fahrbefehl gedrosselt – automatisch wie von Hand. 0 = aus.",f_min_gap_off:"aus",
  f_frost_cond_sensor:"Tipp: Bei hinterlegter Wetter-Entität stellt Shutter Pilot dafür den Sensor „Shutter Pilot Vorhersage Tiefsttemperatur\" bereit.",
  sec_vent:"Automatisches Lüften",sec_vent_sub:"Auf die Lüftungsposition fahren, wenn Bedingungen erfüllt sind",f_vent_enabled:"Automatisch lüften",f_vent_hint:"Sind alle Bedingungen erfüllt, fahren die Rollläden des Bereichs auf ihre Lüftungsposition und danach wieder zurück. Ein offenes Fenster und der Sonnenschutz haben Vorrang.",f_vent_cond:"Bedingung",
  sec_frost:"Frostschutz",sec_frost_sub:"Nicht ganz schliessen, wenn Frost droht",f_frost_cond:"Bedingung (optional)",f_frost_cond_hint:"Ist diese Bedingung erfüllt, schliessen Rollläden mit hinterlegter Frostposition nur so weit. So frieren die Lamellen nicht am Rahmen fest. Gewinnt gegen das abweichende Schliessen.",f_pos_closed_frost:"Frostschutz-Position hinterlegen",f_pos_closed_frost_hint:"Ein Spalt bleibt offen, damit der Rollladen nicht festfriert.",f_pos_closed_frost_val:"Position bei Frost",f_sun_cond_on_below:"Einschalten unter",f_sun_cond_off_above:"Ausschalten über",f_sun_cond_num_inv_hint:"Der Frostschutz greift unterhalb des ersten Werts und bleibt aktiv, bis der zweite überschritten wird.",
  sun_bound_earliest:"frühestens",sun_bound_latest:"spätestens",sun_jitter:"Präsenz",
  sun_elevation:"Aktuelle Elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Nur Hochfahren über diesen Bereich",
  dash_shutter_role_down:"Nur Runterfahren über diesen Bereich",
  dash_shutter_role_both:"Hoch- und Runterfahren über diesen Bereich",
  dash_current_lux:"Aktuell",
  f_brightness_sensor:"Helligkeitssensor",f_lux_up:"Lux Hoch-Schwelle",f_lux_down:"Lux Runter-Schwelle",
  f_lux_wrong_way:"Die Hoch-Schwelle sollte über der Runter-Schwelle liegen: hoch geht es oberhalb, runter unterhalb. Liegt sie darunter, gilt zwischen den beiden Werten beides gleichzeitig – überschneiden sich dann noch die Zeitfenster, pendelt der Rollladen.",
  f_w_up_from:"Woche Hoch ab",f_w_up_to:"Woche Hoch bis",f_w_down_from:"Woche Runter ab",f_w_down_to:"Woche Runter bis",
  f_we_up_from:"WE Hoch ab",f_we_up_to:"WE Hoch bis",f_we_down_from:"WE Runter ab",f_we_down_to:"WE Runter bis",
  f_cover:"Rollladen / Cover",f_window_sensor:"Fenster-/Türsensor (optional)",
  f_win_open:"Fenster-Status 'offen'",f_win_tilt:"Fenster-Status 'gekippt'",
  f_win_tilt_none:"Deaktiviert (kein Kipp-Status)",
  f_win_state_now:"Der Kontakt meldet gerade:",f_win_state_mismatch:"Dieser Zustand kann bei einem binary_sensor nie auftreten – der Kontakt gilt dann dauerhaft als geschlossen. Wähle „on“ oder „off“.",
  f_pos_win_open:"Position bei Fenster offen",f_pos_win_tilt:"Position bei Fenster gekippt",f_pos_win_2state:"Position bei offenem Fenster",
  f_pos_win_tilt_2state_hint:"Dein Kontakt meldet nur offen und zu – „gekippt“ kann er nicht unterscheiden. Deshalb gilt dieser eine Wert für beides. Trägst du oben einen Kipp-Zustand ein, bekommst du zwei getrennte Positionen.",
  f_lock:"Aussperrschutz (verhindert vollständiges Schließen bei offener Tür)",
  f_min_pos:"Mindest-Position wenn Tür offen",
  f_area_up:"Bereich (Hoch)",f_area_down:"Bereich (Runter)",
  f_pos_open:"Position Offen",f_pos_closed:"Position Geschlossen",f_pos_sun:"Sonnenschutz-Position",
  f_drive_after:"Nachholen wenn Fenster offen",
  f_drive_after_hint:"Wenn die Schließzeit erreicht wird aber das Fenster noch offen ist, wird die Fahrt nachgeholt sobald das Fenster geschlossen wird.",
  f_win_debounce:"Verzögerung beim Schließen (Sek.)",f_win_debounce_hint:"Beim Drehen des Griffs von „gekippt“ auf „offen“ meldet der Kontakt kurz „geschlossen“. So lange muss „geschlossen“ anhalten, bevor der Rollladen zurückfährt. 0 = sofort reagieren.",
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
  sec_basics:"Basics",sec_basics_sub:"name, mode, gap between drives",sec_calendar_sub:"holidays, random jitter, manual override",sec_sunprotect_sub:"sun height, direction, conditions",sec_shutter_sub:"entity, name, automation",sec_positions_sub:"open, closed, sun protection, frost",
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
  f_cond_on:"Applies from",
  f_cond_off:"Release below",
  f_cond_num_hint:"«Release below» may sit lower than «Applies from» – the gap stops flapping when the value hovers around the threshold. Empty = same value.",
  f_close_cond_both_hint:"With both conditions filled in, both have to hold in the evening.",
  f_sun_cond_num_hint:"Release below may be lower than Shade above – the gap prevents flapping when clouds pass. Empty = same value.",
  f_sun_cond_wrong_way:"These two are the wrong way round. This is a switch-on point with a release point BELOW it, not a from–to range. As entered, the second value is discarded and the condition is met practically all the time. For a range of compass directions use “Only when the sun faces this window”.",
  f_geo_override_values_hint:"These two now apply instead of the area's – whether you touch them or not.",
  sec_export:"Export settings",
  sec_export_sub:"for bug reports in the forum",
  f_export_hint:"Builds a report with every setting, the current sensor readings and the shading decision of this very moment – per shutter, with its reasoning. Paste it into the forum and nobody has to guess what is configured. It contains only Shutter Pilot's own settings and the names of the entities you picked: no credentials, no location.",
  btn_export:"Build report",
  btn_export_copy:"Copy",
  btn_export_copied:"Copied ✓",
  btn_export_download:"Download",
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
  f_elev_min:"Sun protect from elevation (°)",
  f_elev_enabled:"Check the sun's height",
  f_elev_enabled_hint:"Off: the sun's height plays no part, the conditions alone decide. Useful when a brightness sensor sits at the window – it already measures the sun.",
  f_temp_sensor:"Room temperature (display only, optional)",
  f_temp_sensor_hint:"Shown on the dashboard card and decides nothing. As a condition, a temperature sensor belongs under “Sun protection” or “Partial closing”.",
  dash_room_temp:"Room temperature",f_elev_max:"Sun protect until elevation (°)",
  master_switch:"System active",
  sun_prot_active:"Sun protection active",sun_prot_inactive:"Sun protection inactive",
  sun_prot_range:"Elevation range",
  sun_prot_cond_pending:"Sun height fits – conditions not met yet",f_sun_off_hint:"Plus shifts later, minus earlier: −15 drives a quarter of an hour before sunrise or sunset, +15 a quarter of an hour after.",btn_duplicate:"Duplicate",copy_suffix:"(copy)",sun_prot_waiting:"Waiting for matching sun elevation",
  f_light_entity:"Light/switch on close (optional)",f_light_brightness:"Light brightness (%)",
  f_time_up:"Weekday Up",f_time_down:"Weekday Down",
  f_time_we_up:"Weekend Up",f_time_we_down:"Weekend Down",
  f_sunrise_off:"Sunrise offset (min.)",f_sunset_off:"Sunset offset (min.)",
  sun_next_rise:"Next sunrise",sun_next_set:"Next sunset",
  sun_trigger_up:"Up trigger at",sun_trigger_down:"Down trigger at",
  f_sun_cond_add:"Type a state and press Enter",f_sun_cond_add_hint:"A text sensor only ever reports its current state – add the others by hand here. Case does not matter.",
  f_blind_drive:"Drive reports no position (blind)",f_blind_drive_hint:"For one-way radio such as Somfy RTS. Shutter Pilot then reasons with the position it last sent instead of giving up – that is what makes window triggers and automatic ventilation work with such drives.",
  f_copy_from:"Copy settings from",f_copy_pick:"– choose a shutter –",f_copy_btn:"Apply",f_copy_hint:"Copies positions, slats, shading, conditions and window settings. Cover entity, name, areas and window sensors are left alone.",
  f_sunbound_title:"Extra sun bounds",f_sunbound_hint:"Prevents movements in broad daylight, e.g. when a thunderstorm drops the brightness. Empty = no bound.",f_b_down_sunset:"Down no earlier than X min. before sunset",f_b_up_sunrise:"Up no earlier than X min. before sunrise",
  f_shade_hold:"Hold shading (min.)",f_shade_hold_hint:"A passing cloud ends the condition at once and the shutter opens. This keeps the shading up for that long anyway. 0 = open immediately.",
  sec_drive:"Drive commands",sec_drive_sub:"Spacing between two commands",f_min_gap:"Minimum gap between drive commands",f_min_gap_hint:"Radio receivers (433 MHz, HmIP) swallow commands that arrive together. The per-area delay does not help: each area drives on its own. This throttles every drive command, automated or manual. 0 = off.",f_min_gap_off:"off",
  f_frost_cond_sensor:"Tip: with a weather entity configured, Shutter Pilot provides the sensor \"Shutter Pilot Vorhersage Tiefsttemperatur\" for exactly this.",
  sec_vent:"Automatic ventilation",sec_vent_sub:"Drive to the ventilation position when conditions hold",f_vent_enabled:"Ventilate automatically",f_vent_hint:"While every condition holds, the shutters of this area move to their ventilation position and back afterwards. An open window and sun protection take precedence.",f_vent_cond:"Condition",
  sec_frost:"Frost protection",sec_frost_sub:"Do not close fully when frost is likely",f_frost_cond:"Condition (optional)",f_frost_cond_hint:"When this condition holds, shutters with a frost position only close that far, so the slats cannot freeze to the frame. Wins over partial closing.",f_pos_closed_frost:"Set a frost-protection position",f_pos_closed_frost_hint:"Leaves a gap so the shutter cannot freeze shut.",f_pos_closed_frost_val:"Position during frost",f_sun_cond_on_below:"Switch on below",f_sun_cond_off_above:"Switch off above",f_sun_cond_num_inv_hint:"Frost protection kicks in below the first value and stays on until the second is exceeded.",
  sun_bound_earliest:"no earlier than",sun_bound_latest:"no later than",sun_jitter:"Presence",
  sun_elevation:"Current elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Up drives only via this area",
  dash_shutter_role_down:"Down drives only via this area",
  dash_shutter_role_both:"Up and down drives via this area",
  dash_current_lux:"Current",
  f_brightness_sensor:"Brightness sensor",f_lux_up:"Lux up threshold",f_lux_down:"Lux down threshold",
  f_lux_wrong_way:"The up threshold belongs above the down threshold: up happens above it, down below. Put it lower and both rules hold between the two values at once – once the time windows overlap as well, the shutter starts oscillating.",
  f_w_up_from:"Weekday up from",f_w_up_to:"Weekday up to",f_w_down_from:"Weekday down from",f_w_down_to:"Weekday down to",
  f_we_up_from:"Weekend up from",f_we_up_to:"Weekend up to",f_we_down_from:"Weekend down from",f_we_down_to:"Weekend down to",
  f_cover:"Shutter / Cover",f_window_sensor:"Window/door sensor (optional)",
  f_win_open:"Window state 'open'",f_win_tilt:"Window state 'tilted'",
  f_win_tilt_none:"Disabled (no tilt state)",
  f_win_state_now:"The contact currently reports:",f_win_state_mismatch:"A binary_sensor can never report this state – the contact would always count as closed. Pick \"on\" or \"off\".",
  f_pos_win_open:"Position when window open",f_pos_win_tilt:"Position when window tilted",f_pos_win_2state:"Position when the window is open",
  f_pos_win_tilt_2state_hint:"Your contact only reports open and closed – it cannot tell \"tilted\" apart. So this single value covers both. Set a tilted state above and you get two separate positions.",
  f_lock:"Lock protection (prevents full close when door is open)",
  f_min_pos:"Minimum position when door open",
  f_area_up:"Area (Up)",f_area_down:"Area (Down)",
  f_pos_open:"Position Open",f_pos_closed:"Position Closed",f_pos_sun:"Sun protection position",
  f_drive_after:"Catch up when window open",
  f_drive_after_hint:"When close time is reached but the window is still open, the drive will be executed as soon as the window is closed.",
  f_win_debounce:"Close delay (sec.)",f_win_debounce_hint:"Turning the handle from tilted to open makes the contact report \"closed\" for a moment. This is how long \"closed\" has to hold before the shutter drives back. 0 = react immediately.",
  pick_entity:"Select entity…",
  confirm_del_area:"Really delete area \"{id}\"?",confirm_del_shutter:"Really delete shutter?",
},
fr:{
  f_sun_cond_wrong_way:"Ces deux valeurs sont inversées. Il s’agit d’un seuil de déclenchement avec un seuil de levée EN DESSOUS, pas d’une plage de–à. Telle quelle, la seconde valeur est ignorée et la condition est remplie pratiquement en permanence. Pour une plage d’orientations, utilisez « Seulement si la fenêtre est bien orientée ».",
  f_geo_override_values_hint:"Ces deux valeurs remplacent désormais celles de la zone – même si vous n’y touchez pas.",
  sec_export:"Exporter les réglages",
  sec_export_sub:"pour les rapports d’erreur du forum",
  f_export_hint:"Génère un rapport avec tous les réglages, les valeurs actuelles des capteurs et la décision d’ombrage de cet instant précis – volet par volet, avec sa justification. Collez-le sur le forum et personne n’aura à deviner ce qui est configuré. Il ne contient que les réglages propres à Shutter Pilot et les noms des entités que vous avez choisies : aucun identifiant, aucune localisation.",
  btn_export:"Générer le rapport",
  btn_export_copy:"Copier",
  btn_export_copied:"Copié ✓",
  btn_export_download:"Télécharger",
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
  sec_basics:"Général",sec_basics_sub:"nom, mode, intervalle entre les mouvements",sec_calendar_sub:"jours fériés, décalage aléatoire, priorité manuelle",sec_sunprotect_sub:"hauteur du soleil, direction, conditions",sec_shutter_sub:"entité, nom, automatisation",sec_positions_sub:"ouvert, fermé, protection solaire, gel",
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
  f_cond_on:"S'applique à partir de",
  f_cond_off:"Annuler en dessous de",
  f_cond_num_hint:"« Annuler en dessous de » peut être inférieur à « S'applique à partir de » – l'écart évite les oscillations autour du seuil. Vide = même valeur.",
  f_close_cond_both_hint:"Si les deux conditions sont renseignées, les deux doivent être remplies le soir.",
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
  f_sun_cond_add:"Saisir un état puis Entrée",f_sun_cond_add_hint:"Un capteur texte n’indique que son état actuel – ajoutez les autres à la main ici. La casse n’a pas d’importance.",
  f_bound_none:"aucune limite – toucher pour définir",f_bounds_title:"Au plus tôt / au plus tard",f_bounds_hint:"Ramène l’instant calculé d’après le soleil dans une plage horaire. Par exemple : suivre le soleil, mais jamais avant 07:30 ni après 09:00. Vide = aucune limite.",f_bounds_we_hint:"Week-end – vide signifie que la valeur de semaine s’applique.",f_earliest_up:"Montée au plus tôt",f_latest_up:"Montée au plus tard",f_earliest_down:"Descente au plus tôt",f_latest_down:"Descente au plus tard",f_we_earliest_up:"WE montée au plus tôt",f_we_latest_up:"WE montée au plus tard",f_we_earliest_down:"WE descente au plus tôt",f_we_latest_down:"WE descente au plus tard",f_shutter_cond_hint:"Conditions propres à cette fenêtre, par ex. un capteur de luminosité juste à la fenêtre ou la température de la pièce. Laisser vide pour utiliser la condition de la zone.",sec_verify:"Vérifier les commandes",sec_verify_sub:"pour les volets qui perdent des ordres",f_verify_hint:"Vérifie après chaque commande automatique si la position a réellement été atteinte, et répète sinon. Utile pour les volets radio qui perdent parfois un ordre.",f_verify_enabled:"Vérifier les commandes",f_verify_after:"Vérifier après",f_verify_tolerance:"Écart toléré",f_verify_retries:"Nouvelles tentatives",f_verify_event_hint:"En cas d’échec définitif, la valeur enregistrée est corrigée et l’événement shutter_pilot_cover_failed est émis.",sec_weather:"Météo",sec_weather_sub:"base des conditions d’ombrage",f_weather_entity:"Entité météo",f_weather_hint:"Facultatif. Si renseignée, Shutter Pilot récupère lui-même les prévisions du jour et fournit des capteurs utilisables dans les conditions ci-dessous.",f_weather_sensors_hint:"Disponible comme : température maximale, température minimale et condition prévues.",w_temp_max:"Maximale du jour",w_condition:"Temps du jour",w_updated:"Dernière récupération",f_sun_cond_n:"Condition {n} (facultatif)",f_sun_cond_states:"États autorisés",f_sun_cond_states_hint:"L’ombrage ne fonctionne que tant que le capteur indique l’un des états sélectionnés.",f_season:"Saison d’ombrage",f_season_hint:"N’ombrager que pendant ces mois. La plage peut passer le nouvel an, par ex. octobre à mars.",sec_altclose:"Fermeture partielle",sec_altclose_sub:"par ex. partiellement les soirs chauds",f_close_cond:"Condition (facultatif)",f_close_cond_hint:"Si cette condition est remplie le soir, les volets avec une position partielle ne se ferment que jusque-là.",f_pos_closed_alt:"Utiliser une position de fermeture partielle",f_pos_closed_alt_val:"Partiellement fermé",f_pos_closed_alt_hint:"Ne s’applique que si la zone a une condition de fermeture et qu’elle est remplie.",sec_shutter_sun:"Protection solaire",sec_shutter_sun_sub:"utile seulement pour une autre orientation",f_geo_override:"Orientation propre à ce volet",f_geo_override_hint:"Normalement les valeurs de la zone s’appliquent. À activer uniquement si cette fenêtre est orientée autrement que les autres de la zone.",f_elev_min:"Protection solaire à partir de (°)",
  f_elev_enabled:"Vérifier la hauteur du soleil",
  f_elev_enabled_hint:"Désactivé : la hauteur du soleil n'intervient pas, seules les conditions décident. Utile si un capteur de luminosité est posé à la fenêtre – il mesure déjà le soleil.",
  f_temp_sensor:"Température de la pièce (affichage seul, facultatif)",
  f_temp_sensor_hint:"Affichée sur la carte du tableau de bord, sans aucun effet. Comme condition, un capteur de température se règle sous « Protection solaire » ou « Fermeture partielle ».",
  dash_room_temp:"Température",f_elev_max:"Protection solaire jusqu’à (°)",master_switch:"Système actif",sun_prot_active:"Protection solaire active",sun_prot_inactive:"Protection solaire inactive",sun_prot_range:"Plage de hauteur",
  sun_prot_cond_pending:"Hauteur du soleil correcte – conditions pas encore remplies",f_sun_off_hint:"Plus décale plus tard, moins plus tôt : −15 agit un quart d'heure avant le lever ou le coucher, +15 un quart d'heure après.",btn_duplicate:"Dupliquer",copy_suffix:"(copie)",sun_prot_waiting:"En attente de la hauteur du soleil",
  f_blind_drive:"Le moteur ne renvoie pas de position (à l’aveugle)",f_blind_drive_hint:"Pour la radio unidirectionnelle comme Somfy RTS. Shutter Pilot utilise alors la dernière position envoyée.",
  f_copy_from:"Reprendre les réglages de",f_copy_pick:"– choisir un volet –",f_copy_btn:"Appliquer",f_copy_hint:"Copie positions, lamelles, ombrage, conditions et réglages de fenêtre. Entité, nom, zones et capteurs restent inchangés.",
  f_sunbound_title:"Limites solaires supplémentaires",f_sunbound_hint:"Empêche les mouvements en plein jour, par ex. lors d’un orage. Vide = aucune limite.",f_b_down_sunset:"Descente au plus tôt X min. avant le coucher",f_b_up_sunrise:"Montée au plus tôt X min. avant le lever",
  f_shade_hold:"Maintenir l’ombrage (min.)",f_shade_hold_hint:"Un nuage met fin à la condition immédiatement. L’ombrage est malgré tout maintenu pendant cette durée. 0 = ouvrir tout de suite.",
  sec_drive:"Commandes",sec_drive_sub:"Espacement entre deux commandes",f_min_gap:"Écart minimal entre commandes",f_min_gap_hint:"Les récepteurs radio ignorent les commandes simultanées. Le délai par zone n’y suffit pas. Ici chaque commande est espacée. 0 = désactivé.",f_min_gap_off:"désactivé",
  f_frost_cond_sensor:"Astuce : avec une entité météo configurée, Shutter Pilot fournit le capteur « Shutter Pilot Vorhersage Tiefsttemperatur ».",
  sec_vent:"Aération automatique",sec_vent_sub:"Aller en position d’aération si les conditions sont remplies",f_vent_enabled:"Aérer automatiquement",f_vent_hint:"Tant que toutes les conditions sont remplies, les volets vont en position d’aération puis reviennent. Une fenêtre ouverte et la protection solaire sont prioritaires.",f_vent_cond:"Condition",
  sec_frost:"Protection antigel",sec_frost_sub:"Ne pas fermer complètement en cas de gel",f_frost_cond:"Condition (optionnel)",f_frost_cond_hint:"Si cette condition est remplie, les volets avec une position antigel ne se ferment que jusque-là. Prioritaire sur la fermeture partielle.",f_pos_closed_frost:"Définir une position antigel",f_pos_closed_frost_hint:"Laisse un jeu pour éviter le gel.",f_pos_closed_frost_val:"Position en cas de gel",f_sun_cond_on_below:"Activer en dessous de",f_sun_cond_off_above:"Désactiver au-dessus de",f_sun_cond_num_inv_hint:"La protection s’active sous la première valeur et reste active jusqu’au dépassement de la seconde.",
  sun_bound_earliest:"au plus tôt",sun_bound_latest:"au plus tard",sun_jitter:"Présence",
  sun_elevation:"Élévation actuelle",sun_offset:"Décalage",
  dash_shutter_role_up:"Montée seulement via cette zone",
  dash_shutter_role_down:"Descente seulement via cette zone",
  dash_shutter_role_both:"Montée et descente via cette zone",
  dash_current_lux:"Actuel",
  f_brightness_sensor:"Capteur luminosité",f_lux_up:"Seuil lux montée",f_lux_down:"Seuil lux descente",
  f_lux_wrong_way:"Le seuil de montée doit être au-dessus du seuil de descente : on monte au-dessus, on descend en dessous. S'il est plus bas, les deux règles s'appliquent en même temps entre les deux valeurs – et si les plages horaires se recoupent, le volet oscille.",
  f_w_up_from:"Sem. montée de",f_w_up_to:"Sem. montée à",f_w_down_from:"Sem. descente de",f_w_down_to:"Sem. descente à",
  f_we_up_from:"WE montée de",f_we_up_to:"WE montée à",f_we_down_from:"WE descente de",f_we_down_to:"WE descente à",
  f_cover:"Volet / Cover",f_window_sensor:"Capteur fenêtre (optionnel)",
  f_win_open:"État fenêtre 'ouverte'",f_win_tilt:"État fenêtre 'basculée'",f_win_tilt_none:"Désactivé",
  f_win_state_now:"Le contact indique actuellement :",f_win_state_mismatch:"Un binary_sensor ne peut jamais avoir cet état – le contact serait toujours considéré comme fermé. Choisissez « on » ou « off ».",
  f_pos_win_open:"Position fenêtre ouverte",f_pos_win_tilt:"Position fenêtre basculée",f_pos_win_2state:"Position quand la fenêtre est ouverte",
  f_pos_win_tilt_2state_hint:"Votre contact ne signale qu'ouvert et fermé – il ne distingue pas « basculé ». Cette valeur unique couvre donc les deux cas. Renseignez un état basculé ci-dessus pour obtenir deux positions distinctes.",
  f_lock:"Protection anti-enfermement",f_min_pos:"Position min. porte ouverte",
  f_area_up:"Zone (Montée)",f_area_down:"Zone (Descente)",
  f_pos_open:"Position Ouvert",f_pos_closed:"Position Fermé",f_pos_sun:"Position protection solaire",
  f_drive_after:"Rattraper si fenêtre ouverte",f_drive_after_hint:"La commande sera exécutée dès que la fenêtre sera fermée.",
  f_win_debounce:"Délai à la fermeture (sec.)",f_win_debounce_hint:"Durée pendant laquelle « fermé » doit se maintenir avant le retour du volet. 0 = immédiat.",
  pick_entity:"Sélectionner…",confirm_del_area:"Supprimer la zone \"{id}\" ?",confirm_del_shutter:"Supprimer le volet ?",
},
es:{
  f_sun_cond_wrong_way:"Estos dos valores están al revés. Es un punto de activación con un punto de liberación POR DEBAJO, no un rango de–a. Tal como está, el segundo valor se descarta y la condición se cumple prácticamente siempre. Para un rango de orientaciones usa «Solo con la orientación adecuada de la ventana».",
  f_geo_override_values_hint:"Estos dos valores sustituyen ahora a los de la zona, los toques o no.",
  sec_export:"Exportar ajustes",
  sec_export_sub:"para informes de fallos en el foro",
  f_export_hint:"Genera un informe con todos los ajustes, los valores actuales de los sensores y la decisión de sombreado de este mismo momento – por persiana y con su motivo. Pégalo en el foro y nadie tendrá que adivinar qué hay configurado. Solo contiene los ajustes propios de Shutter Pilot y los nombres de las entidades que has elegido: ni credenciales ni ubicación.",
  btn_export:"Generar informe",
  btn_export_copy:"Copiar",
  btn_export_copied:"Copiado ✓",
  btn_export_download:"Descargar",
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
  sec_basics:"Datos básicos",sec_basics_sub:"nombre, modo, intervalo entre movimientos",sec_calendar_sub:"festivos, desfase aleatorio, anulación manual",sec_sunprotect_sub:"altura solar, dirección, condiciones",sec_shutter_sub:"entidad, nombre, automatización",sec_positions_sub:"abierto, cerrado, protección solar, helada",
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
  f_cond_on:"Se aplica a partir de",
  f_cond_off:"Anular por debajo de",
  f_cond_num_hint:"«Anular por debajo de» puede ser menor que «Se aplica a partir de»: la diferencia evita oscilaciones alrededor del umbral. Vacío = mismo valor.",
  f_close_cond_both_hint:"Si se rellenan ambas condiciones, por la tarde deben cumplirse las dos.",
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
  f_sun_cond_add:"Escribe un estado y pulsa Intro",f_sun_cond_add_hint:"Un sensor de texto solo informa su estado actual – añade los demás a mano aquí. Mayúsculas y minúsculas dan igual.",
  f_bound_none:"sin límite – toca para definir",f_bounds_title:"Como pronto / como tarde",f_bounds_hint:"Ajusta el momento calculado por el sol a una franja horaria. Por ejemplo: seguir el sol, pero nunca antes de las 07:30 ni después de las 09:00. Vacío = sin límite.",f_bounds_we_hint:"Fin de semana – vacío significa que se aplica el valor entre semana.",f_earliest_up:"Subir como pronto",f_latest_up:"Subir como tarde",f_earliest_down:"Bajar como pronto",f_latest_down:"Bajar como tarde",f_we_earliest_up:"FS subir como pronto",f_we_latest_up:"FS subir como tarde",f_we_earliest_down:"FS bajar como pronto",f_we_latest_down:"FS bajar como tarde",f_shutter_cond_hint:"Condiciones solo para esta ventana, p. ej. un sensor de luz junto a la ventana o la temperatura de la habitación. Déjalo vacío para usar la condición de la zona.",sec_verify:"Verificar movimientos",sec_verify_sub:"para persianas que pierden órdenes",f_verify_hint:"Comprueba tras cada movimiento automático si se alcanzó la posición y repite la orden si no. Útil para persianas por radio que pierden alguna orden.",f_verify_enabled:"Verificar movimientos",f_verify_after:"Comprobar después de",f_verify_tolerance:"Desviación permitida",f_verify_retries:"Reintentos",f_verify_event_hint:"Si falla definitivamente se corrige el valor guardado y se lanza el evento shutter_pilot_cover_failed.",sec_weather:"Meteorología",sec_weather_sub:"base de las condiciones de sombreado",f_weather_entity:"Entidad meteorológica",f_weather_hint:"Opcional. Si se indica, Shutter Pilot obtiene la previsión diaria y ofrece sensores que puedes elegir en las condiciones de abajo.",f_weather_sensors_hint:"Disponible como: temperatura máxima, mínima y condición previstas.",w_temp_max:"Máxima de hoy",w_condition:"Tiempo de hoy",w_updated:"Última consulta",f_sun_cond_n:"Condición {n} (opcional)",f_sun_cond_states:"Estados permitidos",f_sun_cond_states_hint:"El sombreado solo actúa mientras el sensor informe uno de los estados seleccionados.",f_season:"Temporada de sombreado",f_season_hint:"Sombrear solo durante estos meses. El rango puede cruzar el año nuevo, p. ej. de octubre a marzo.",sec_altclose:"Cierre parcial",sec_altclose_sub:"p. ej. solo a medias en noches cálidas",f_close_cond:"Condición (opcional)",f_close_cond_hint:"Si esta condición se cumple por la noche, las persianas con posición parcial solo cierran hasta ahí.",f_pos_closed_alt:"Usar una posición de cierre parcial",f_pos_closed_alt_val:"Parcialmente cerrada",f_pos_closed_alt_hint:"Solo se aplica si la zona tiene una condición de cierre y se cumple.",sec_shutter_sun:"Protección solar",sec_shutter_sun_sub:"solo necesario con otra orientación",f_geo_override:"Orientación propia de esta persiana",f_geo_override_hint:"Normalmente valen los valores de la zona. Actívalo solo si esta ventana mira en otra dirección que las demás de la zona.",f_elev_min:"Protección solar desde elevación (°)",
  f_elev_enabled:"Comprobar la altura del sol",
  f_elev_enabled_hint:"Desactivado: la altura solar no interviene, deciden solo las condiciones. Útil si hay un sensor de luminosidad en la ventana: ya mide el sol.",
  f_temp_sensor:"Temperatura de la sala (solo visualización, opcional)",
  f_temp_sensor_hint:"Se muestra en la tarjeta del panel y no decide nada. Como condición, un sensor de temperatura va en «Protección solar» o «Cierre parcial».",
  dash_room_temp:"Temperatura",f_elev_max:"Protección solar hasta elevación (°)",master_switch:"Sistema activo",sun_prot_active:"Protección solar activa",sun_prot_inactive:"Protección solar inactiva",sun_prot_range:"Rango de elevación",
  sun_prot_cond_pending:"La altura solar encaja: aún no se cumplen las condiciones",f_sun_off_hint:"Más desplaza hacia después, menos hacia antes: −15 actúa un cuarto de hora antes del amanecer o del atardecer, +15 un cuarto de hora después.",btn_duplicate:"Duplicar",copy_suffix:"(copia)",sun_prot_waiting:"Esperando la elevación solar adecuada",
  f_blind_drive:"El motor no informa posición (a ciegas)",f_blind_drive_hint:"Para radio unidireccional como Somfy RTS. Shutter Pilot usa entonces la última posición enviada.",
  f_copy_from:"Copiar ajustes de",f_copy_pick:"– elegir persiana –",f_copy_btn:"Aplicar",f_copy_hint:"Copia posiciones, lamas, sombreado, condiciones y ajustes de ventana. Entidad, nombre, áreas y sensores no cambian.",
  f_sunbound_title:"Límites solares adicionales",f_sunbound_hint:"Evita movimientos a plena luz del día, p. ej. con una tormenta. Vacío = sin límite.",f_b_down_sunset:"Bajar como pronto X min. antes del ocaso",f_b_up_sunrise:"Subir como pronto X min. antes del amanecer",
  f_shade_hold:"Mantener sombreado (min.)",f_shade_hold_hint:"Una nube termina la condición al instante. El sombreado se mantiene igualmente ese tiempo. 0 = abrir enseguida.",
  sec_drive:"Órdenes de marcha",sec_drive_sub:"Separación entre dos órdenes",f_min_gap:"Separación mínima entre órdenes",f_min_gap_hint:"Los receptores de radio pierden órdenes que llegan a la vez. El retardo por área no basta. Aquí se espacia cada orden. 0 = desactivado.",f_min_gap_off:"desactivado",
  f_frost_cond_sensor:"Consejo: con una entidad meteorológica configurada, Shutter Pilot ofrece el sensor «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Ventilación automática",sec_vent_sub:"Ir a la posición de ventilación si se cumplen las condiciones",f_vent_enabled:"Ventilar automáticamente",f_vent_hint:"Mientras se cumplan todas las condiciones, las persianas van a su posición de ventilación y luego vuelven. Una ventana abierta y la protección solar tienen prioridad.",f_vent_cond:"Condición",
  sec_frost:"Protección antihielo",sec_frost_sub:"No cerrar del todo si hay riesgo de helada",f_frost_cond:"Condición (opcional)",f_frost_cond_hint:"Si se cumple, las persianas con posición antihielo solo cierran hasta ahí. Tiene prioridad sobre el cierre parcial.",f_pos_closed_frost:"Definir posición antihielo",f_pos_closed_frost_hint:"Deja una holgura para que no se congele.",f_pos_closed_frost_val:"Posición con helada",f_sun_cond_on_below:"Activar por debajo de",f_sun_cond_off_above:"Desactivar por encima de",f_sun_cond_num_inv_hint:"La protección se activa por debajo del primer valor y sigue activa hasta superar el segundo.",
  sun_bound_earliest:"no antes de",sun_bound_latest:"no después de",sun_jitter:"Presencia",
  sun_elevation:"Elevación actual",sun_offset:"Desfase",
  dash_shutter_role_up:"Solo subida por esta zona",
  dash_shutter_role_down:"Solo bajada por esta zona",
  dash_shutter_role_both:"Subida y bajada por esta zona",
  dash_current_lux:"Actual",
  f_brightness_sensor:"Sensor brillo",f_lux_up:"Umbral lux subida",f_lux_down:"Umbral lux bajada",
  f_lux_wrong_way:"El umbral de subida debe estar por encima del de bajada: se sube por encima y se baja por debajo. Si queda más bajo, entre ambos valores se cumplen las dos reglas a la vez, y si además se solapan las franjas horarias la persiana oscila.",
  f_w_up_from:"L-V subida desde",f_w_up_to:"L-V subida hasta",f_w_down_from:"L-V bajada desde",f_w_down_to:"L-V bajada hasta",
  f_we_up_from:"Fin sem. subida desde",f_we_up_to:"Fin sem. subida hasta",f_we_down_from:"Fin sem. bajada desde",f_we_down_to:"Fin sem. bajada hasta",
  f_cover:"Persiana / Cover",f_window_sensor:"Sensor ventana (opcional)",
  f_win_open:"Estado ventana 'abierta'",f_win_tilt:"Estado ventana 'inclinada'",f_win_tilt_none:"Desactivado",
  f_win_state_now:"El contacto informa ahora mismo:",f_win_state_mismatch:"Un binary_sensor nunca puede tener este estado: el contacto contaría siempre como cerrado. Elige «on» u «off».",
  f_pos_win_open:"Posición ventana abierta",f_pos_win_tilt:"Posición ventana inclinada",f_pos_win_2state:"Posición con la ventana abierta",
  f_pos_win_tilt_2state_hint:"Tu contacto solo informa abierto y cerrado: no distingue «inclinado». Por eso este único valor cubre ambos casos. Define arriba un estado inclinado y tendrás dos posiciones separadas.",
  f_lock:"Protección anti-bloqueo",f_min_pos:"Posición mín. puerta abierta",
  f_area_up:"Zona (Subida)",f_area_down:"Zona (Bajada)",
  f_pos_open:"Posición Abierta",f_pos_closed:"Posición Cerrada",f_pos_sun:"Posición protección solar",
  f_drive_after:"Recuperar si ventana abierta",f_drive_after_hint:"Se ejecutará cuando la ventana se cierre.",
  f_win_debounce:"Retardo al cerrar (seg.)",f_win_debounce_hint:"Tiempo que debe mantenerse «cerrado» antes de que la persiana vuelva. 0 = inmediato.",
  pick_entity:"Seleccionar…",confirm_del_area:"¿Eliminar zona \"{id}\"?",confirm_del_shutter:"¿Eliminar persiana?",
},
it:{
  f_sun_cond_wrong_way:"I due valori sono invertiti. È un punto di attivazione con un punto di rilascio SOTTO di esso, non un intervallo da–a. Così com’è, il secondo valore viene scartato e la condizione risulta soddisfatta praticamente sempre. Per un intervallo di orientamenti usa «Solo con l’orientamento giusto della finestra».",
  f_geo_override_values_hint:"Questi due valori valgono ora al posto di quelli della zona, che li tocchi o no.",
  sec_export:"Esporta impostazioni",
  sec_export_sub:"per le segnalazioni sul forum",
  f_export_hint:"Crea un rapporto con tutte le impostazioni, i valori attuali dei sensori e la decisione di ombreggiatura di questo preciso momento – per ogni tapparella, con la sua motivazione. Incollalo nel forum e nessuno dovrà indovinare che cosa è configurato. Contiene solo le impostazioni di Shutter Pilot e i nomi delle entità che hai scelto: nessuna credenziale, nessuna posizione.",
  btn_export:"Crea rapporto",
  btn_export_copy:"Copia",
  btn_export_copied:"Copiato ✓",
  btn_export_download:"Scarica",
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
  sec_basics:"Dati di base",sec_basics_sub:"nome, modalità, intervallo tra le corse",sec_calendar_sub:"festivi, scarto casuale, comando manuale",sec_sunprotect_sub:"altezza del sole, direzione, condizioni",sec_shutter_sub:"entità, nome, automazione",sec_positions_sub:"aperto, chiuso, protezione solare, gelo",
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
  f_cond_on:"Vale a partire da",
  f_cond_off:"Annulla sotto",
  f_cond_num_hint:"«Annulla sotto» può essere inferiore a «Vale a partire da»: la distanza evita oscillazioni attorno alla soglia. Vuoto = stesso valore.",
  f_close_cond_both_hint:"Se sono indicate entrambe le condizioni, la sera devono valere tutte e due.",
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
  f_sun_cond_add:"Digita uno stato e premi Invio",f_sun_cond_add_hint:"Un sensore testuale riporta solo lo stato attuale – aggiungi qui gli altri a mano. Maiuscole e minuscole non contano.",
  f_bound_none:"nessun limite – tocca per impostare",f_bounds_title:"Non prima / non oltre",f_bounds_hint:"Riporta l’orario calcolato dal sole dentro una finestra oraria. Ad esempio: segui il sole, ma mai prima delle 07:30 né dopo le 09:00. Vuoto = nessun limite.",f_bounds_we_hint:"Fine settimana – vuoto significa che vale il valore feriale.",f_earliest_up:"Su non prima di",f_latest_up:"Su non oltre",f_earliest_down:"Giù non prima di",f_latest_down:"Giù non oltre",f_we_earliest_up:"FS su non prima di",f_we_latest_up:"FS su non oltre",f_we_earliest_down:"FS giù non prima di",f_we_latest_down:"FS giù non oltre",f_shutter_cond_hint:"Condizioni solo per questa finestra, ad es. un sensore di luminosità sulla finestra o la temperatura della stanza. Lascia vuoto per usare la condizione della zona.",sec_verify:"Verifica delle corse",sec_verify_sub:"per tapparelle che perdono comandi",f_verify_hint:"Dopo ogni corsa automatica verifica se la posizione è stata davvero raggiunta e altrimenti ripete il comando. Utile per tapparelle radio che perdono qualche comando.",f_verify_enabled:"Verifica le corse",f_verify_after:"Verifica dopo",f_verify_tolerance:"Scostamento ammesso",f_verify_retries:"Tentativi",f_verify_event_hint:"In caso di esito negativo definitivo il valore memorizzato viene corretto e viene emesso l’evento shutter_pilot_cover_failed.",sec_weather:"Meteo",sec_weather_sub:"base delle condizioni di ombreggiatura",f_weather_entity:"Entità meteo",f_weather_hint:"Facoltativo. Se impostata, Shutter Pilot recupera da sé le previsioni del giorno e fornisce sensori selezionabili nelle condizioni qui sotto.",f_weather_sensors_hint:"Disponibile come: temperatura massima, minima e condizione previste.",w_temp_max:"Massima di oggi",w_condition:"Tempo di oggi",w_updated:"Ultimo aggiornamento",f_sun_cond_n:"Condizione {n} (facoltativa)",f_sun_cond_states:"Stati ammessi",f_sun_cond_states_hint:"L’ombreggiatura funziona solo finché il sensore riporta uno degli stati selezionati.",f_season:"Stagione di ombreggiatura",f_season_hint:"Ombreggia solo in questi mesi. L’intervallo può attraversare il capodanno, ad es. da ottobre a marzo.",sec_altclose:"Chiusura parziale",sec_altclose_sub:"ad es. solo a metà nelle sere calde",f_close_cond:"Condizione (facoltativa)",f_close_cond_hint:"Se la sera questa condizione è soddisfatta, le tapparelle con posizione parziale si chiudono solo fin lì.",f_pos_closed_alt:"Usa una posizione di chiusura parziale",f_pos_closed_alt_val:"Parzialmente chiusa",f_pos_closed_alt_hint:"Vale solo se la zona ha una condizione di chiusura ed è soddisfatta.",sec_shutter_sun:"Protezione solare",sec_shutter_sun_sub:"serve solo con un altro orientamento",f_geo_override:"Orientamento proprio di questa tapparella",f_geo_override_hint:"Normalmente valgono i valori della zona. Attiva solo se questa finestra è esposta diversamente dalle altre della zona.",f_elev_min:"Protezione solare da elevazione (°)",
  f_elev_enabled:"Verificare l'altezza del sole",
  f_elev_enabled_hint:"Disattivato: l'altezza del sole non conta, decidono solo le condizioni. Utile con un sensore di luminosità alla finestra: misura già il sole.",
  f_temp_sensor:"Temperatura del locale (solo visualizzazione, opzionale)",
  f_temp_sensor_hint:"Mostrata sulla scheda della dashboard, non decide nulla. Come condizione, un sensore di temperatura va sotto «Protezione solare» o «Chiusura parziale».",
  dash_room_temp:"Temperatura",f_elev_max:"Protezione solare fino a elevazione (°)",master_switch:"Sistema attivo",sun_prot_active:"Protezione solare attiva",sun_prot_inactive:"Protezione solare non attiva",sun_prot_range:"Intervallo di elevazione",
  sun_prot_cond_pending:"Altezza del sole corretta – condizioni non ancora soddisfatte",f_sun_off_hint:"Più sposta più tardi, meno più presto: −15 agisce un quarto d'ora prima dell'alba o del tramonto, +15 un quarto d'ora dopo.",btn_duplicate:"Duplica",copy_suffix:"(copia)",sun_prot_waiting:"In attesa dell’elevazione solare adatta",
  f_blind_drive:"Il motore non riporta la posizione (alla cieca)",f_blind_drive_hint:"Per radio unidirezionale come Somfy RTS. Shutter Pilot usa allora l’ultima posizione inviata.",
  f_copy_from:"Copia impostazioni da",f_copy_pick:"– scegli tapparella –",f_copy_btn:"Applica",f_copy_hint:"Copia posizioni, lamelle, ombreggiatura, condizioni e impostazioni finestra. Entità, nome, aree e sensori restano invariati.",
  f_sunbound_title:"Limiti solari aggiuntivi",f_sunbound_hint:"Evita movimenti in pieno giorno, ad es. durante un temporale. Vuoto = nessun limite.",f_b_down_sunset:"Giù non prima di X min. dal tramonto",f_b_up_sunrise:"Su non prima di X min. dall’alba",
  f_shade_hold:"Mantieni ombreggiatura (min.)",f_shade_hold_hint:"Una nuvola interrompe subito la condizione. L’ombreggiatura resta comunque per questo tempo. 0 = apri subito.",
  sec_drive:"Comandi di marcia",sec_drive_sub:"Distanza tra due comandi",f_min_gap:"Distanza minima tra i comandi",f_min_gap_hint:"I ricevitori radio perdono i comandi che arrivano insieme. Il ritardo per area non basta. Qui ogni comando viene distanziato. 0 = disattivato.",f_min_gap_off:"disattivato",
  f_frost_cond_sensor:"Suggerimento: con un\u2019entità meteo configurata, Shutter Pilot fornisce il sensore «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Ventilazione automatica",sec_vent_sub:"Vai in posizione di ventilazione se le condizioni sono soddisfatte",f_vent_enabled:"Ventila automaticamente",f_vent_hint:"Finché tutte le condizioni sono soddisfatte, le tapparelle vanno in posizione di ventilazione e poi tornano. Una finestra aperta e la protezione solare hanno la precedenza.",f_vent_cond:"Condizione",
  sec_frost:"Protezione antigelo",sec_frost_sub:"Non chiudere del tutto in caso di gelo",f_frost_cond:"Condizione (opzionale)",f_frost_cond_hint:"Se la condizione è soddisfatta, le tapparelle con posizione antigelo si chiudono solo fin lì. Prevale sulla chiusura parziale.",f_pos_closed_frost:"Imposta una posizione antigelo",f_pos_closed_frost_hint:"Lascia una fessura per evitare il congelamento.",f_pos_closed_frost_val:"Posizione con gelo",f_sun_cond_on_below:"Attiva sotto",f_sun_cond_off_above:"Disattiva sopra",f_sun_cond_num_inv_hint:"La protezione si attiva sotto il primo valore e resta attiva finché non si supera il secondo.",
  sun_bound_earliest:"non prima delle",sun_bound_latest:"non oltre le",sun_jitter:"Presenza",
  sun_elevation:"Elevazione attuale",sun_offset:"Offset",
  dash_shutter_role_up:"Solo apertura da questa zona",
  dash_shutter_role_down:"Solo chiusura da questa zona",
  dash_shutter_role_both:"Apertura e chiusura da questa zona",
  dash_current_lux:"Attuale",
  f_brightness_sensor:"Sensore luminosità",f_lux_up:"Soglia lux apertura",f_lux_down:"Soglia lux chiusura",
  f_lux_wrong_way:"La soglia di apertura va sopra quella di chiusura: si apre al di sopra, si chiude al di sotto. Se sta più in basso, fra i due valori valgono entrambe le regole insieme e, se si sovrappongono anche le fasce orarie, la tapparella oscilla.",
  f_w_up_from:"Feriale su da",f_w_up_to:"Feriale su a",f_w_down_from:"Feriale giù da",f_w_down_to:"Feriale giù a",
  f_we_up_from:"Weekend su da",f_we_up_to:"Weekend su a",f_we_down_from:"Weekend giù da",f_we_down_to:"Weekend giù a",
  f_cover:"Tapparella / Cover",f_window_sensor:"Sensore finestra (opzionale)",
  f_win_open:"Stato finestra 'aperta'",f_win_tilt:"Stato finestra 'ribaltata'",f_win_tilt_none:"Disattivato",
  f_win_state_now:"Il contatto segnala ora:",f_win_state_mismatch:"Un binary_sensor non può mai avere questo stato: il contatto risulterebbe sempre chiuso. Scegli «on» oppure «off».",
  f_pos_win_open:"Posizione finestra aperta",f_pos_win_tilt:"Posizione finestra ribaltata",f_pos_win_2state:"Posizione a finestra aperta",
  f_pos_win_tilt_2state_hint:"Il contatto segnala solo aperto e chiuso: non distingue «ribaltato». Questo singolo valore vale quindi per entrambi. Imposta sopra uno stato ribaltato per avere due posizioni separate.",
  f_lock:"Protezione anti-blocco",f_min_pos:"Posizione min. porta aperta",
  f_area_up:"Zona (Su)",f_area_down:"Zona (Giù)",
  f_pos_open:"Posizione Aperta",f_pos_closed:"Posizione Chiusa",f_pos_sun:"Posizione protezione solare",
  f_drive_after:"Recupera se finestra aperta",f_drive_after_hint:"Verrà eseguito alla chiusura della finestra.",
  f_win_debounce:"Ritardo alla chiusura (sec.)",f_win_debounce_hint:"Per quanto tempo deve permanere «chiuso» prima che la tapparella torni indietro. 0 = subito.",
  pick_entity:"Seleziona…",confirm_del_area:"Eliminare zona \"{id}\"?",confirm_del_shutter:"Eliminare tapparella?",
},
nl:{
  f_sun_cond_wrong_way:"Deze twee waarden staan omgekeerd. Dit is een inschakelpunt met een opheffingspunt ERONDER, geen bereik van–tot. Zoals het er nu staat wordt de tweede waarde weggegooid en is de voorwaarde vrijwel altijd vervuld. Voor een bereik van windrichtingen is er «Alleen bij passende raamrichting».",
  f_geo_override_values_hint:"Deze twee waarden gelden nu in plaats van die van de zone – of je ze nu aanraakt of niet.",
  sec_export:"Instellingen exporteren",
  sec_export_sub:"voor foutmeldingen op het forum",
  f_export_hint:"Maakt een rapport met alle instellingen, de huidige sensorwaarden en de zonweringsbeslissing van precies dit moment – per rolluik, met de reden erbij. Plak het op het forum en niemand hoeft te raden wat er ingesteld is. Het bevat alleen de eigen instellingen van Shutter Pilot en de namen van de entiteiten die je gekozen hebt: geen inloggegevens en geen locatie.",
  btn_export:"Rapport maken",
  btn_export_copy:"Kopiëren",
  btn_export_copied:"Gekopieerd ✓",
  btn_export_download:"Downloaden",
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
  sec_basics:"Basisgegevens",sec_basics_sub:"naam, modus, interval tussen bewegingen",sec_calendar_sub:"feestdagen, willekeurige spreiding, handmatige voorrang",sec_sunprotect_sub:"zonnehoogte, richting, voorwaarden",sec_shutter_sub:"entiteit, naam, automatisering",sec_positions_sub:"open, dicht, zonwering, vorst",
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
  f_cond_on:"Geldt vanaf",
  f_cond_off:"Opheffen onder",
  f_cond_num_hint:"«Opheffen onder» mag lager liggen dan «Geldt vanaf» – het verschil voorkomt pendelen rond de drempel. Leeg = zelfde waarde.",
  f_close_cond_both_hint:"Zijn beide voorwaarden ingevuld, dan moeten 's avonds ook beide gelden.",
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
  f_sun_cond_add:"Toestand invoeren en Enter",f_sun_cond_add_hint:"Een tekstsensor meldt alleen zijn huidige toestand – vul de andere hier met de hand aan. Hoofdletters maken niet uit.",
  f_bound_none:"geen grens – tik om in te stellen",f_bounds_title:"Niet eerder / niet later",f_bounds_hint:"Trekt het uit de zonnestand berekende moment in een tijdvenster. Bijvoorbeeld: op zonnestand rijden, maar nooit vóór 07:30 en nooit na 09:00. Leeg = geen grens.",f_bounds_we_hint:"Weekend – leeg betekent dat de doordeweekse waarde geldt.",f_earliest_up:"Omhoog niet eerder dan",f_latest_up:"Omhoog niet later dan",f_earliest_down:"Omlaag niet eerder dan",f_latest_down:"Omlaag niet later dan",f_we_earliest_up:"WE omhoog niet eerder",f_we_latest_up:"WE omhoog niet later",f_we_earliest_down:"WE omlaag niet eerder",f_we_latest_down:"WE omlaag niet later",f_shutter_cond_hint:"Voorwaarden alleen voor dit raam, bijv. een lichtsensor bij het raam of de kamertemperatuur. Leeg laten om de voorwaarde van de zone te gebruiken.",sec_verify:"Bewegingen controleren",sec_verify_sub:"voor rolluiken die commando’s verliezen",f_verify_hint:"Controleert na elke automatische beweging of de positie echt bereikt is en herhaalt het commando anders. Handig voor rolluiken op radio die af en toe een commando missen.",f_verify_enabled:"Bewegingen controleren",f_verify_after:"Controleren na",f_verify_tolerance:"Toegestane afwijking",f_verify_retries:"Nieuwe pogingen",f_verify_event_hint:"Bij definitief mislukken wordt de opgeslagen waarde gecorrigeerd en de gebeurtenis shutter_pilot_cover_failed verstuurd.",sec_weather:"Weer",sec_weather_sub:"basis voor de zonweringsvoorwaarden",f_weather_entity:"Weer-entiteit",f_weather_hint:"Optioneel. Als deze is ingesteld haalt Shutter Pilot zelf de dagverwachting op en levert sensoren die je hieronder in de voorwaarden kunt kiezen.",f_weather_sensors_hint:"Beschikbaar als: verwachte maximum- en minimumtemperatuur en weertype.",w_temp_max:"Maximum vandaag",w_condition:"Weer vandaag",w_updated:"Laatst opgehaald",f_sun_cond_n:"Voorwaarde {n} (optioneel)",f_sun_cond_states:"Toegestane toestanden",f_sun_cond_states_hint:"De zonwering werkt alleen zolang de sensor een van de gekozen toestanden meldt.",f_season:"Zonweringsseizoen",f_season_hint:"Alleen in deze maanden zonweren. Het bereik mag over de jaarwisseling lopen, bijv. oktober tot maart.",sec_altclose:"Gedeeltelijk sluiten",sec_altclose_sub:"bijv. maar half op warme avonden",f_close_cond:"Voorwaarde (optioneel)",f_close_cond_hint:"Als deze voorwaarde ’s avonds geldt, sluiten rolluiken met een gedeeltelijke positie slechts tot daar.",f_pos_closed_alt:"Gedeeltelijke sluitpositie gebruiken",f_pos_closed_alt_val:"Gedeeltelijk gesloten",f_pos_closed_alt_hint:"Geldt alleen als de zone een sluitvoorwaarde heeft en die vervuld is.",sec_shutter_sun:"Zonwering",sec_shutter_sun_sub:"alleen nodig bij een andere raamrichting",f_geo_override:"Eigen oriëntatie voor dit rolluik",f_geo_override_hint:"Normaal gelden de waarden van de zone. Schakel dit alleen in als dit raam een andere kant op ligt dan de rest van de zone.",f_elev_min:"Zonwering vanaf hoogte (°)",
  f_elev_enabled:"Zonnehoogte controleren",
  f_elev_enabled_hint:"Uit: de zonnehoogte speelt geen rol, alleen de voorwaarden beslissen. Handig als er een lichtsensor bij het raam hangt – die meet de zon al.",
  f_temp_sensor:"Kamertemperatuur (alleen weergave, optioneel)",
  f_temp_sensor_hint:"Wordt op de dashboardkaart getoond en beslist niets. Als voorwaarde hoort een temperatuursensor onder «Zonwering» of «Gedeeltelijk sluiten».",
  dash_room_temp:"Kamertemperatuur",f_elev_max:"Zonwering tot hoogte (°)",master_switch:"Systeem actief",sun_prot_active:"Zonwering actief",sun_prot_inactive:"Zonwering niet actief",sun_prot_range:"Hoogtebereik",
  sun_prot_cond_pending:"Zonnehoogte klopt – voorwaarden nog niet vervuld",f_sun_off_hint:"Plus verschuift naar later, min naar eerder: −15 rijdt een kwartier voor zonsopkomst of zonsondergang, +15 een kwartier erna.",btn_duplicate:"Dupliceren",copy_suffix:"(kopie)",sun_prot_waiting:"Wacht op passende zonnestand",
  f_blind_drive:"Motor meldt geen positie (blind)",f_blind_drive_hint:"Voor eenrichtingsradio zoals Somfy RTS. Shutter Pilot rekent dan met de laatst verzonden positie.",
  f_copy_from:"Instellingen overnemen van",f_copy_pick:"– rolluik kiezen –",f_copy_btn:"Toepassen",f_copy_hint:"Kopieert posities, lamellen, zonwering, voorwaarden en raaminstellingen. Entiteit, naam, gebieden en sensoren blijven ongewijzigd.",
  f_sunbound_title:"Extra zonnegrenzen",f_sunbound_hint:"Voorkomt bewegingen op klaarlichte dag, bijv. bij onweer. Leeg = geen grens.",f_b_down_sunset:"Omlaag niet eerder dan X min. voor zonsondergang",f_b_up_sunrise:"Omhoog niet eerder dan X min. voor zonsopgang",
  f_shade_hold:"Zonwering vasthouden (min.)",f_shade_hold_hint:"Een wolk beëindigt de voorwaarde meteen. De zonwering blijft toch zo lang staan. 0 = direct openen.",
  sec_drive:"Rijcommando’s",sec_drive_sub:"Afstand tussen twee commando’s",f_min_gap:"Minimale afstand tussen commando’s",f_min_gap_hint:"Radio-ontvangers missen commando’s die tegelijk aankomen. De vertraging per gebied helpt daar niet. Hier wordt elk commando gespreid. 0 = uit.",f_min_gap_off:"uit",
  f_frost_cond_sensor:"Tip: met een weer-entiteit ingesteld levert Shutter Pilot de sensor «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Automatisch ventileren",sec_vent_sub:"Naar de ventilatiestand als de voorwaarden gelden",f_vent_enabled:"Automatisch ventileren",f_vent_hint:"Zolang alle voorwaarden gelden gaan de rolluiken naar hun ventilatiestand en daarna terug. Een open raam en zonwering gaan voor.",f_vent_cond:"Voorwaarde",
  sec_frost:"Vorstbeveiliging",sec_frost_sub:"Niet volledig sluiten bij kans op vorst",f_frost_cond:"Voorwaarde (optioneel)",f_frost_cond_hint:"Als deze voorwaarde geldt, sluiten rolluiken met een vorstpositie slechts tot daar. Gaat voor op gedeeltelijk sluiten.",f_pos_closed_frost:"Vorstpositie instellen",f_pos_closed_frost_hint:"Laat een kier zodat het rolluik niet vastvriest.",f_pos_closed_frost_val:"Positie bij vorst",f_sun_cond_on_below:"Inschakelen onder",f_sun_cond_off_above:"Uitschakelen boven",f_sun_cond_num_inv_hint:"De beveiliging treedt in werking onder de eerste waarde en blijft actief tot de tweede wordt overschreden.",
  sun_bound_earliest:"niet vóór",sun_bound_latest:"niet later dan",sun_jitter:"Aanwezigheid",
  sun_elevation:"Huidige elevatie",sun_offset:"Offset",
  dash_shutter_role_up:"Alleen omhoog via deze zone",
  dash_shutter_role_down:"Alleen omlaag via deze zone",
  dash_shutter_role_both:"Omhoog en omlaag via deze zone",
  dash_current_lux:"Huidig",
  f_brightness_sensor:"Helderheidssensor",f_lux_up:"Lux omhoog drempel",f_lux_down:"Lux omlaag drempel",
  f_lux_wrong_way:"De omhoog-drempel hoort boven de omlaag-drempel: omhoog gebeurt erboven, omlaag eronder. Ligt hij lager, dan gelden tussen beide waarden allebei de regels tegelijk – overlappen ook de tijdvensters, dan gaat het rolluik heen en weer.",
  f_w_up_from:"Doordeweeks omhoog van",f_w_up_to:"Doordeweeks omhoog tot",f_w_down_from:"Doordeweeks omlaag van",f_w_down_to:"Doordeweeks omlaag tot",
  f_we_up_from:"Weekend omhoog van",f_we_up_to:"Weekend omhoog tot",f_we_down_from:"Weekend omlaag van",f_we_down_to:"Weekend omlaag tot",
  f_cover:"Rolluik / Cover",f_window_sensor:"Raam-/deursensor (optioneel)",
  f_win_open:"Raamstatus 'open'",f_win_tilt:"Raamstatus 'gekanteld'",f_win_tilt_none:"Uitgeschakeld (geen kantelstatus)",
  f_win_state_now:"Het contact meldt nu:",f_win_state_mismatch:"Een binary_sensor kan deze status nooit hebben – het contact geldt dan altijd als gesloten. Kies \"on\" of \"off\".",
  f_pos_win_open:"Positie bij raam open",f_pos_win_tilt:"Positie bij raam gekanteld",f_pos_win_2state:"Positie bij een open raam",
  f_pos_win_tilt_2state_hint:"Je contact meldt alleen open en dicht – «gekanteld» kan het niet onderscheiden. Daarom geldt deze ene waarde voor beide. Vul hierboven een kantelstatus in voor twee aparte posities.",
  f_lock:"Buitensluitbeveiliging (voorkomt volledig sluiten bij open deur)",f_min_pos:"Minimumpositie bij open deur",
  f_area_up:"Zone (Omhoog)",f_area_down:"Zone (Omlaag)",
  f_pos_open:"Positie Open",f_pos_closed:"Positie Gesloten",f_pos_sun:"Zonweringpositie",
  f_drive_after:"Inhalen als raam open",f_drive_after_hint:"Als de sluitingstijd bereikt wordt maar het raam nog open is, wordt de actie uitgevoerd zodra het raam gesloten wordt.",
  f_win_debounce:"Vertraging bij sluiten (sec.)",f_win_debounce_hint:"Hoe lang «gesloten» moet aanhouden voordat het rolluik terugkeert. 0 = direct.",
  pick_entity:"Entiteit selecteren…",confirm_del_area:"Zone \"{id}\" echt verwijderen?",confirm_del_shutter:"Rolluik echt verwijderen?",
},
da:{
  f_sun_cond_wrong_way:"De to værdier står omvendt. Det er et tændpunkt med et ophævelsespunkt UNDER, ikke et interval fra–til. Som det står nu, kasseres den anden værdi, og betingelsen er stort set altid opfyldt. Til et interval af verdenshjørner findes «Kun ved passende vinduesretning».",
  f_geo_override_values_hint:"Disse to værdier gælder nu i stedet for områdets – uanset om du rører dem.",
  sec_export:"Eksportér indstillinger",
  sec_export_sub:"til fejlrapporter i forummet",
  f_export_hint:"Laver en rapport med alle indstillinger, de aktuelle sensorværdier og afskærmningsbeslutningen fra netop nu – pr. persienne og med begrundelse. Sæt teksten ind i forummet, så behøver ingen at gætte, hvad der er indstillet. Den indeholder kun Shutter Pilots egne indstillinger og navnene på de entiteter, du har valgt: ingen adgangsoplysninger og ingen placering.",
  btn_export:"Lav rapport",
  btn_export_copy:"Kopiér",
  btn_export_copied:"Kopieret ✓",
  btn_export_download:"Hent",
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
  sec_basics:"Grunddata",sec_basics_sub:"navn, tilstand, interval mellem kørsler",sec_calendar_sub:"helligdage, tilfældig forskydning, manuel tilsidesættelse",sec_sunprotect_sub:"solhøjde, retning, betingelser",sec_shutter_sub:"entitet, navn, automatik",sec_positions_sub:"åben, lukket, solafskærmning, frost",
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
  f_cond_on:"Gælder fra",
  f_cond_off:"Ophæv under",
  f_cond_num_hint:"«Ophæv under» må ligge lavere end «Gælder fra» – afstanden forhindrer flakken omkring tærsklen. Tom = samme værdi.",
  f_close_cond_both_hint:"Er begge betingelser udfyldt, skal begge også være opfyldt om aftenen.",
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
  f_sun_cond_add:"Skriv en tilstand og tryk Enter",f_sun_cond_add_hint:"En tekstsensor melder kun sin aktuelle tilstand – tilføj de øvrige manuelt her. Store og små bogstaver er lige meget.",
  f_bound_none:"ingen grænse – tryk for at angive",f_bounds_title:"Tidligst / senest",f_bounds_hint:"Trækker det tidspunkt, der er beregnet ud fra solen, ind i et tidsvindue. For eksempel: kør efter solen, men aldrig før 07:30 og aldrig efter 09:00. Tom = ingen grænse.",f_bounds_we_hint:"Weekend – tom betyder, at hverdagsværdien gælder.",f_earliest_up:"Op tidligst",f_latest_up:"Op senest",f_earliest_down:"Ned tidligst",f_latest_down:"Ned senest",f_we_earliest_up:"WE op tidligst",f_we_latest_up:"WE op senest",f_we_earliest_down:"WE ned tidligst",f_we_latest_down:"WE ned senest",f_shutter_cond_hint:"Betingelser kun for dette vindue, f.eks. en lyssensor lige ved vinduet eller rumtemperaturen. Lad stå tomt for at bruge områdets betingelse.",sec_verify:"Kontrollér kørsler",sec_verify_sub:"til persienner der taber kommandoer",f_verify_hint:"Kontrollerer efter hver automatisk kørsel, om positionen faktisk blev nået, og gentager ellers kommandoen. Nyttigt ved radiostyrede persienner, der af og til taber en kommando.",f_verify_enabled:"Kontrollér kørsler",f_verify_after:"Kontrollér efter",f_verify_tolerance:"Tilladt afvigelse",f_verify_retries:"Gentagelser",f_verify_event_hint:"Ved endelig fejl korrigeres den gemte værdi, og hændelsen shutter_pilot_cover_failed udsendes.",sec_weather:"Vejr",sec_weather_sub:"grundlag for afskærmningsbetingelser",f_weather_entity:"Vejr-entitet",f_weather_hint:"Valgfrit. Er den angivet, henter Shutter Pilot selv dagens prognose og stiller sensorer til rådighed, som du kan vælge i betingelserne nedenfor.",f_weather_sensors_hint:"Findes som: forventet højeste og laveste temperatur samt vejrtype.",w_temp_max:"Dagens højeste",w_condition:"Dagens vejr",w_updated:"Sidst hentet",f_sun_cond_n:"Betingelse {n} (valgfri)",f_sun_cond_states:"Tilladte tilstande",f_sun_cond_states_hint:"Afskærmningen kører kun, så længe sensoren melder en af de valgte tilstande.",f_season:"Afskærmningssæson",f_season_hint:"Afskærm kun i disse måneder. Intervallet må gå hen over nytår, f.eks. oktober til marts.",sec_altclose:"Delvis lukning",sec_altclose_sub:"f.eks. kun halvt på varme aftener",f_close_cond:"Betingelse (valgfri)",f_close_cond_hint:"Er betingelsen opfyldt om aftenen, lukker persienner med en delvis position kun så langt.",f_pos_closed_alt:"Brug en delvis lukkeposition",f_pos_closed_alt_val:"Delvist lukket",f_pos_closed_alt_hint:"Gælder kun, hvis området har en lukkebetingelse, og den er opfyldt.",sec_shutter_sun:"Solbeskyttelse",sec_shutter_sun_sub:"kun nødvendigt ved en anden vinduesretning",f_geo_override:"Egen orientering for denne persienne",f_geo_override_hint:"Normalt gælder områdets værdier. Slå kun til, hvis dette vindue vender anderledes end de øvrige i området.",f_elev_min:"Solbeskyttelse fra højde (°)",
  f_elev_enabled:"Kontrollér solhøjden",
  f_elev_enabled_hint:"Fra: solhøjden spiller ingen rolle, betingelserne alene afgør. Nyttigt når en lyssensor sidder ved vinduet – den måler allerede solen.",
  f_temp_sensor:"Rumtemperatur (kun visning, valgfri)",
  f_temp_sensor_hint:"Vises på dashboard-kortet og afgør intet. Som betingelse hører en temperatursensor under «Solafskærmning» eller «Delvis lukning».",
  dash_room_temp:"Rumtemperatur",f_elev_max:"Solbeskyttelse til højde (°)",master_switch:"System aktivt",sun_prot_active:"Solbeskyttelse aktiv",sun_prot_inactive:"Solbeskyttelse inaktiv",sun_prot_range:"Højdeinterval",
  sun_prot_cond_pending:"Solhøjden passer – betingelserne er endnu ikke opfyldt",f_sun_off_hint:"Plus rykker senere, minus tidligere: −15 kører et kvarter før solopgang eller solnedgang, +15 et kvarter efter.",btn_duplicate:"Dublér",copy_suffix:"(kopi)",sun_prot_waiting:"Venter på passende solhøjde",
  f_blind_drive:"Motoren melder ingen position (blind)",f_blind_drive_hint:"Til envejsradio som Somfy RTS. Shutter Pilot regner så med den sidst sendte position.",
  f_copy_from:"Kopiér indstillinger fra",f_copy_pick:"– vælg rullegardin –",f_copy_btn:"Anvend",f_copy_hint:"Kopierer positioner, lameller, afskærmning, betingelser og vinduesindstillinger. Entitet, navn, områder og sensorer ændres ikke.",
  f_sunbound_title:"Ekstra solgrænser",f_sunbound_hint:"Forhindrer kørsel ved højlys dag, f.eks. ved tordenvejr. Tom = ingen grænse.",f_b_down_sunset:"Ned tidligst X min. før solnedgang",f_b_up_sunrise:"Op tidligst X min. før solopgang",
  f_shade_hold:"Fasthold afskærmning (min.)",f_shade_hold_hint:"En sky afslutter betingelsen med det samme. Afskærmningen bliver alligevel stående så længe. 0 = åbn straks.",
  sec_drive:"Kørselskommandoer",sec_drive_sub:"Afstand mellem to kommandoer",f_min_gap:"Mindste afstand mellem kommandoer",f_min_gap_hint:"Radiomodtagere taber kommandoer, der ankommer samtidig. Forsinkelsen pr. område hjælper ikke. Her spredes hver kommando. 0 = fra.",f_min_gap_off:"fra",
  f_frost_cond_sensor:"Tip: med en vejr-entitet angivet leverer Shutter Pilot sensoren «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Automatisk udluftning",sec_vent_sub:"Kør til udluftningsposition når betingelserne er opfyldt",f_vent_enabled:"Udluft automatisk",f_vent_hint:"Så længe alle betingelser er opfyldt, kører rullegardinerne til udluftningsposition og tilbage igen. Et åbent vindue og solafskærmning har forrang.",f_vent_cond:"Betingelse",
  sec_frost:"Frostbeskyttelse",sec_frost_sub:"Luk ikke helt, når der er risiko for frost",f_frost_cond:"Betingelse (valgfri)",f_frost_cond_hint:"Når betingelsen er opfyldt, lukker rullegardiner med en frostposition kun så langt. Vinder over delvis lukning.",f_pos_closed_frost:"Angiv frostposition",f_pos_closed_frost_hint:"Efterlader en sprække, så rullegardinet ikke fryser fast.",f_pos_closed_frost_val:"Position ved frost",f_sun_cond_on_below:"Tænd under",f_sun_cond_off_above:"Sluk over",f_sun_cond_num_inv_hint:"Beskyttelsen aktiveres under den første værdi og forbliver aktiv, indtil den anden overskrides.",
  sun_bound_earliest:"tidligst",sun_bound_latest:"senest",sun_jitter:"Tilstedeværelse",
  sun_elevation:"Aktuel elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Kun op via dette område",
  dash_shutter_role_down:"Kun ned via dette område",
  dash_shutter_role_both:"Op og ned via dette område",
  dash_current_lux:"Aktuel",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux op-tærskel",f_lux_down:"Lux ned-tærskel",
  f_lux_wrong_way:"Op-tærsklen hører over ned-tærsklen: op sker over den, ned under den. Ligger den lavere, gælder begge regler samtidig mellem de to værdier – og overlapper tidsrummene også, kører persiennen frem og tilbage.",
  f_w_up_from:"Hverdag op fra",f_w_up_to:"Hverdag op til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Weekend op fra",f_we_up_to:"Weekend op til",f_we_down_from:"Weekend ned fra",f_we_down_to:"Weekend ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vinduessensor (valgfrit)",
  f_win_open:"Vinduestilstand 'åben'",f_win_tilt:"Vinduestilstand 'vippet'",f_win_tilt_none:"Deaktiveret",
  f_win_state_now:"Kontakten melder lige nu:",f_win_state_mismatch:"En binary_sensor kan aldrig have denne tilstand – kontakten vil altid tælle som lukket. Vælg \"on\" eller \"off\".",
  f_pos_win_open:"Position ved åbent vindue",f_pos_win_tilt:"Position ved vippet vindue",f_pos_win_2state:"Position når vinduet er åbent",
  f_pos_win_tilt_2state_hint:"Din kontakt melder kun åben og lukket – den kan ikke skelne «vippet». Derfor gælder denne ene værdi for begge. Angiv en vippet tilstand ovenfor for at få to separate positioner.",
  f_lock:"Låsebeskyttelse",f_min_pos:"Minimumposition ved åben dør",
  f_area_up:"Område (Op)",f_area_down:"Område (Ned)",
  f_pos_open:"Position Åben",f_pos_closed:"Position Lukket",f_pos_sun:"Solbeskyttelsesposition",
  f_drive_after:"Indhent hvis vindue åbent",f_drive_after_hint:"Handlingen udføres, så snart vinduet lukkes.",
  f_win_debounce:"Forsinkelse ved lukning (sek.)",f_win_debounce_hint:"Hvor længe «lukket» skal holde, før rullegardinet kører tilbage. 0 = med det samme.",
  pick_entity:"Vælg entitet…",confirm_del_area:"Slet område \"{id}\"?",confirm_del_shutter:"Slet persienne?",
},
sv:{
  f_sun_cond_wrong_way:"De två värdena står omvänt. Det här är en påslagspunkt med en frigöringspunkt UNDER, inte ett intervall från–till. Som det står nu kastas det andra värdet och villkoret är uppfyllt praktiskt taget hela tiden. För ett intervall av väderstreck finns «Endast vid passande fönsterriktning».",
  f_geo_override_values_hint:"De här två värdena gäller nu i stället för områdets – vare sig du rör dem eller inte.",
  sec_export:"Exportera inställningar",
  sec_export_sub:"för felrapporter i forumet",
  f_export_hint:"Skapar en rapport med alla inställningar, sensorernas nuvarande värden och solskyddsbeslutet från just nu – per persienn och med motivering. Klistra in texten i forumet, så behöver ingen gissa vad som är inställt. Den innehåller bara Shutter Pilots egna inställningar och namnen på de entiteter du valt: inga inloggningsuppgifter och ingen plats.",
  btn_export:"Skapa rapport",
  btn_export_copy:"Kopiera",
  btn_export_copied:"Kopierat ✓",
  btn_export_download:"Ladda ner",
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
  sec_basics:"Grunduppgifter",sec_basics_sub:"namn, läge, intervall mellan körningar",sec_calendar_sub:"helgdagar, slumpmässig spridning, manuell åsidosättning",sec_sunprotect_sub:"solhöjd, riktning, villkor",sec_shutter_sub:"entitet, namn, automatik",sec_positions_sub:"öppet, stängt, solskydd, frost",
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
  f_cond_on:"Gäller från",
  f_cond_off:"Upphäv under",
  f_cond_num_hint:"«Upphäv under» får ligga lägre än «Gäller från» – avståndet hindrar fladder kring tröskeln. Tomt = samma värde.",
  f_close_cond_both_hint:"Är båda villkoren ifyllda måste båda gälla på kvällen.",
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
  f_sun_cond_add:"Skriv ett tillstånd och tryck Enter",f_sun_cond_add_hint:"En textsensor rapporterar bara sitt nuvarande tillstånd – lägg till de övriga för hand här. Versaler spelar ingen roll.",
  f_bound_none:"ingen gräns – tryck för att ange",f_bounds_title:"Tidigast / senast",f_bounds_hint:"Drar tidpunkten som räknats fram ur solens läge in i ett tidsfönster. Till exempel: kör efter solen, men aldrig före 07:30 och aldrig efter 09:00. Tomt = ingen gräns.",f_bounds_we_hint:"Helg – tomt betyder att vardagsvärdet gäller.",f_earliest_up:"Upp tidigast",f_latest_up:"Upp senast",f_earliest_down:"Ner tidigast",f_latest_down:"Ner senast",f_we_earliest_up:"Helg upp tidigast",f_we_latest_up:"Helg upp senast",f_we_earliest_down:"Helg ner tidigast",f_we_latest_down:"Helg ner senast",f_shutter_cond_hint:"Villkor bara för det här fönstret, t.ex. en ljussensor vid fönstret eller rumstemperaturen. Lämna tomt för att använda områdets villkor.",sec_verify:"Kontrollera körningar",sec_verify_sub:"för persienner som tappar kommandon",f_verify_hint:"Kontrollerar efter varje automatisk körning om positionen verkligen nåddes och upprepar annars kommandot. Bra för radiostyrda persienner som ibland tappar ett kommando.",f_verify_enabled:"Kontrollera körningar",f_verify_after:"Kontrollera efter",f_verify_tolerance:"Tillåten avvikelse",f_verify_retries:"Nya försök",f_verify_event_hint:"Vid slutgiltigt fel korrigeras det sparade värdet och händelsen shutter_pilot_cover_failed skickas.",sec_weather:"Väder",sec_weather_sub:"underlag för solskyddsvillkoren",f_weather_entity:"Väderentitet",f_weather_hint:"Valfritt. Om den anges hämtar Shutter Pilot dagens prognos själv och tillhandahåller sensorer som du kan välja i villkoren nedan.",f_weather_sensors_hint:"Finns som: prognostiserad högsta och lägsta temperatur samt vädertyp.",w_temp_max:"Dagens högsta",w_condition:"Dagens väder",w_updated:"Senast hämtad",f_sun_cond_n:"Villkor {n} (valfritt)",f_sun_cond_states:"Tillåtna tillstånd",f_sun_cond_states_hint:"Solskyddet fungerar bara så länge sensorn rapporterar något av de valda tillstånden.",f_season:"Solskyddssäsong",f_season_hint:"Solskydda bara under dessa månader. Intervallet får gå över nyår, t.ex. oktober till mars.",sec_altclose:"Delvis stängning",sec_altclose_sub:"t.ex. bara halvvägs varma kvällar",f_close_cond:"Villkor (valfritt)",f_close_cond_hint:"Om villkoret gäller på kvällen stänger persienner med en delposition bara så långt.",f_pos_closed_alt:"Använd en delvis stängd position",f_pos_closed_alt_val:"Delvis stängd",f_pos_closed_alt_hint:"Gäller bara om området har ett stängningsvillkor och det är uppfyllt.",sec_shutter_sun:"Solskydd",sec_shutter_sun_sub:"behövs bara vid annan fönsterriktning",f_geo_override:"Egen orientering för den här persiennen",f_geo_override_hint:"Normalt gäller områdets värden. Slå på detta bara om fönstret vetter åt ett annat håll än de övriga i området.",f_elev_min:"Solskydd från höjd (°)",
  f_elev_enabled:"Kontrollera solhöjden",
  f_elev_enabled_hint:"Av: solhöjden spelar ingen roll, villkoren avgör ensamma. Bra när en ljussensor sitter vid fönstret – den mäter redan solen.",
  f_temp_sensor:"Rumstemperatur (endast visning, valfritt)",
  f_temp_sensor_hint:"Visas på dashboard-kortet och avgör ingenting. Som villkor hör en temperatursensor under «Solskydd» eller «Delvis stängning».",
  dash_room_temp:"Rumstemperatur",f_elev_max:"Solskydd till höjd (°)",master_switch:"Systemet aktivt",sun_prot_active:"Solskydd aktivt",sun_prot_inactive:"Solskydd inaktivt",sun_prot_range:"Höjdintervall",
  sun_prot_cond_pending:"Solhöjden stämmer – villkoren är inte uppfyllda än",f_sun_off_hint:"Plus flyttar senare, minus tidigare: −15 kör en kvart före soluppgång eller solnedgång, +15 en kvart efter.",btn_duplicate:"Duplicera",copy_suffix:"(kopia)",sun_prot_waiting:"Väntar på rätt solhöjd",
  f_blind_drive:"Motorn rapporterar ingen position (blint)",f_blind_drive_hint:"För envägsradio som Somfy RTS. Shutter Pilot räknar då med den senast skickade positionen.",
  f_copy_from:"Kopiera inställningar från",f_copy_pick:"– välj jalusi –",f_copy_btn:"Använd",f_copy_hint:"Kopierar positioner, lameller, solskydd, villkor och fönsterinställningar. Entitet, namn, områden och sensorer lämnas orörda.",
  f_sunbound_title:"Extra solgränser",f_sunbound_hint:"Förhindrar körningar mitt på dagen, t.ex. vid åska. Tomt = ingen gräns.",f_b_down_sunset:"Ner tidigast X min. före solnedgång",f_b_up_sunrise:"Upp tidigast X min. före soluppgång",
  f_shade_hold:"Behåll solskydd (min.)",f_shade_hold_hint:"Ett moln avslutar villkoret direkt. Solskyddet står kvar så länge ändå. 0 = öppna genast.",
  sec_drive:"Körkommandon",sec_drive_sub:"Avstånd mellan två kommandon",f_min_gap:"Minsta avstånd mellan kommandon",f_min_gap_hint:"Radiomottagare tappar kommandon som kommer samtidigt. Fördröjningen per område räcker inte. Här sprids varje kommando ut. 0 = av.",f_min_gap_off:"av",
  f_frost_cond_sensor:"Tips: med en väderentitet angiven ger Shutter Pilot sensorn «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Automatisk vädring",sec_vent_sub:"Kör till vädringsläget när villkoren gäller",f_vent_enabled:"Vädra automatiskt",f_vent_hint:"Så länge alla villkor gäller går jalusierna till vädringsläget och tillbaka igen. Ett öppet fönster och solskyddet går före.",f_vent_cond:"Villkor",
  sec_frost:"Frostskydd",sec_frost_sub:"Stäng inte helt när frost hotar",f_frost_cond:"Villkor (valfritt)",f_frost_cond_hint:"När villkoret gäller stänger jalusier med frostposition bara så långt. Går före delvis stängning.",f_pos_closed_frost:"Ange frostposition",f_pos_closed_frost_hint:"Lämnar en springa så att jalusin inte fryser fast.",f_pos_closed_frost_val:"Position vid frost",f_sun_cond_on_below:"Slå på under",f_sun_cond_off_above:"Slå av över",f_sun_cond_num_inv_hint:"Skyddet aktiveras under det första värdet och är kvar tills det andra överskrids.",
  sun_bound_earliest:"tidigast",sun_bound_latest:"senast",sun_jitter:"Närvaro",
  sun_elevation:"Aktuell elevation",sun_offset:"Offset",
  dash_shutter_role_up:"Endast upp via detta område",
  dash_shutter_role_down:"Endast ner via detta område",
  dash_shutter_role_both:"Upp och ner via detta område",
  dash_current_lux:"Aktuell",
  f_brightness_sensor:"Ljussensor",f_lux_up:"Lux upp-tröskel",f_lux_down:"Lux ner-tröskel",
  f_lux_wrong_way:"Upp-tröskeln hör hemma över ner-tröskeln: upp sker ovanför, ner nedanför. Ligger den lägre gäller båda reglerna samtidigt mellan värdena – överlappar dessutom tidsfönstren pendlar persiennen.",
  f_w_up_from:"Vardag upp från",f_w_up_to:"Vardag upp till",f_w_down_from:"Vardag ner från",f_w_down_to:"Vardag ner till",
  f_we_up_from:"Helg upp från",f_we_up_to:"Helg upp till",f_we_down_from:"Helg ner från",f_we_down_to:"Helg ner till",
  f_cover:"Persienn / Cover",f_window_sensor:"Fönstersensor (valfritt)",
  f_win_open:"Fönsterstatus 'öppet'",f_win_tilt:"Fönsterstatus 'vippat'",f_win_tilt_none:"Inaktiverad",
  f_win_state_now:"Kontakten rapporterar just nu:",f_win_state_mismatch:"En binary_sensor kan aldrig ha detta tillstånd – kontakten räknas då alltid som stängd. Välj \"on\" eller \"off\".",
  f_pos_win_open:"Position vid öppet fönster",f_pos_win_tilt:"Position vid vippat fönster",f_pos_win_2state:"Position när fönstret är öppet",
  f_pos_win_tilt_2state_hint:"Din kontakt rapporterar bara öppet och stängt – den kan inte skilja ut «vippat». Därför gäller detta enda värde för båda. Ange ett vippat tillstånd ovan för två separata positioner.",
  f_lock:"Utelåsningsskydd",f_min_pos:"Minimiposition vid öppen dörr",
  f_area_up:"Område (Upp)",f_area_down:"Område (Ner)",
  f_pos_open:"Position Öppen",f_pos_closed:"Position Stängd",f_pos_sun:"Solskyddsposition",
  f_drive_after:"Hämta om fönster öppet",f_drive_after_hint:"Åtgärden utförs så snart fönstret stängs.",
  f_win_debounce:"Fördröjning vid stängning (sek.)",f_win_debounce_hint:"Hur länge «stängt» måste hålla innan jalusin åker tillbaka. 0 = direkt.",
  pick_entity:"Välj entitet…",confirm_del_area:"Ta bort område \"{id}\"?",confirm_del_shutter:"Ta bort persienn?",
},
pl:{
  f_sun_cond_wrong_way:"Te dwie wartości są odwrócone. To punkt włączenia z punktem wyłączenia PONIŻEJ niego, a nie zakres od–do. W tej postaci druga wartość jest odrzucana, a warunek jest spełniony praktycznie zawsze. Dla zakresu kierunków świata służy «Tylko przy odpowiednim kierunku okna».",
  f_geo_override_values_hint:"Te dwie wartości obowiązują teraz zamiast wartości strefy – niezależnie od tego, czy ich dotkniesz.",
  sec_export:"Eksport ustawień",
  sec_export_sub:"do zgłoszeń błędów na forum",
  f_export_hint:"Tworzy raport ze wszystkimi ustawieniami, bieżącymi odczytami czujników i decyzją o zacienieniu z tej właśnie chwili – dla każdej rolety, wraz z uzasadnieniem. Wklej go na forum, a nikt nie będzie musiał zgadywać, co jest ustawione. Zawiera tylko własne ustawienia Shutter Pilota i nazwy wybranych przez Ciebie encji: żadnych danych logowania ani lokalizacji.",
  btn_export:"Utwórz raport",
  btn_export_copy:"Kopiuj",
  btn_export_copied:"Skopiowano ✓",
  btn_export_download:"Pobierz",
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
  sec_basics:"Dane podstawowe",sec_basics_sub:"nazwa, tryb, odstęp między przejazdami",sec_calendar_sub:"święta, losowe przesunięcie, sterowanie ręczne",sec_sunprotect_sub:"wysokość słońca, kierunek, warunki",sec_shutter_sub:"encja, nazwa, automatyka",sec_positions_sub:"otwarte, zamknięte, ochrona przed słońcem, mróz",
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
  f_cond_on:"Obowiązuje od",
  f_cond_off:"Anuluj poniżej",
  f_cond_num_hint:"„Anuluj poniżej” może być niższe niż „Obowiązuje od” – odstęp zapobiega migotaniu wokół progu. Puste = ta sama wartość.",
  f_close_cond_both_hint:"Gdy wpisane są oba warunki, wieczorem muszą być spełnione oba.",
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
  f_sun_cond_add:"Wpisz stan i naciśnij Enter",f_sun_cond_add_hint:"Czujnik tekstowy zgłasza tylko swój bieżący stan – pozostałe dodaj tutaj ręcznie. Wielkość liter nie ma znaczenia.",
  f_bound_none:"bez granicy – dotknij, aby ustawić",f_bounds_title:"Najwcześniej / najpóźniej",f_bounds_hint:"Wciąga moment wyliczony z położenia słońca w okno czasowe. Na przykład: jedź według słońca, ale nigdy przed 07:30 i nigdy po 09:00. Puste = bez granicy.",f_bounds_we_hint:"Weekend – puste oznacza, że obowiązuje wartość z dni roboczych.",f_earliest_up:"W górę najwcześniej",f_latest_up:"W górę najpóźniej",f_earliest_down:"W dół najwcześniej",f_latest_down:"W dół najpóźniej",f_we_earliest_up:"WK w górę najwcześniej",f_we_latest_up:"WK w górę najpóźniej",f_we_earliest_down:"WK w dół najwcześniej",f_we_latest_down:"WK w dół najpóźniej",f_shutter_cond_hint:"Warunki tylko dla tego okna, np. czujnik jasności przy oknie albo temperatura pomieszczenia. Zostaw puste, aby użyć warunku strefy.",sec_verify:"Sprawdzanie jazd",sec_verify_sub:"dla rolet gubiących polecenia",f_verify_hint:"Po każdej automatycznej jeździe sprawdza, czy pozycja została faktycznie osiągnięta, i w razie potrzeby powtarza polecenie. Przydatne przy roletach radiowych, które czasem gubią polecenie.",f_verify_enabled:"Sprawdzaj jazdy",f_verify_after:"Sprawdź po",f_verify_tolerance:"Dopuszczalne odchylenie",f_verify_retries:"Ponowne próby",f_verify_event_hint:"Przy ostatecznym niepowodzeniu zapisana wartość zostaje poprawiona i wysłane jest zdarzenie shutter_pilot_cover_failed.",sec_weather:"Pogoda",sec_weather_sub:"podstawa warunków zacienienia",f_weather_entity:"Encja pogodowa",f_weather_hint:"Opcjonalnie. Po wskazaniu Shutter Pilot sam pobiera prognozę na dzień i udostępnia czujniki, które można wybrać w warunkach poniżej.",f_weather_sensors_hint:"Dostępne jako: prognozowana temperatura maksymalna, minimalna i stan pogody.",w_temp_max:"Dzisiejsze maksimum",w_condition:"Dzisiejsza pogoda",w_updated:"Ostatnio pobrano",f_sun_cond_n:"Warunek {n} (opcjonalnie)",f_sun_cond_states:"Dozwolone stany",f_sun_cond_states_hint:"Zacienienie działa tylko wtedy, gdy czujnik zgłasza jeden z wybranych stanów.",f_season:"Sezon zacieniania",f_season_hint:"Zacieniaj tylko w tych miesiącach. Zakres może przechodzić przez nowy rok, np. od października do marca.",sec_altclose:"Zamykanie częściowe",sec_altclose_sub:"np. tylko do połowy w ciepłe wieczory",f_close_cond:"Warunek (opcjonalnie)",f_close_cond_hint:"Gdy warunek jest wieczorem spełniony, rolety z pozycją częściową zamykają się tylko do niej.",f_pos_closed_alt:"Użyj częściowej pozycji zamknięcia",f_pos_closed_alt_val:"Częściowo zamknięta",f_pos_closed_alt_hint:"Obowiązuje tylko, gdy strefa ma warunek zamknięcia i jest on spełniony.",sec_shutter_sun:"Osłona słoneczna",sec_shutter_sun_sub:"potrzebne tylko przy innym kierunku okna",f_geo_override:"Własna orientacja tej rolety",f_geo_override_hint:"Normalnie obowiązują wartości strefy. Włącz tylko wtedy, gdy to okno jest skierowane inaczej niż pozostałe w strefie.",f_elev_min:"Osłona słoneczna od wysokości (°)",
  f_elev_enabled:"Sprawdzaj wysokość słońca",
  f_elev_enabled_hint:"Wyłączone: wysokość słońca nie ma znaczenia, decydują same warunki. Przydatne, gdy przy oknie wisi czujnik jasności – on już mierzy słońce.",
  f_temp_sensor:"Temperatura pomieszczenia (tylko podgląd, opcjonalnie)",
  f_temp_sensor_hint:"Pokazywana na karcie pulpitu i o niczym nie decyduje. Jako warunek czujnik temperatury należy do „Ochrony przed słońcem” lub „Częściowego zamykania”.",
  dash_room_temp:"Temperatura",f_elev_max:"Osłona słoneczna do wysokości (°)",master_switch:"System aktywny",sun_prot_active:"Osłona słoneczna aktywna",sun_prot_inactive:"Osłona słoneczna nieaktywna",sun_prot_range:"Zakres wysokości",
  sun_prot_cond_pending:"Wysokość słońca pasuje – warunki jeszcze niespełnione",f_sun_off_hint:"Plus przesuwa na później, minus na wcześniej: −15 zadziała kwadrans przed wschodem lub zachodem, +15 kwadrans po.",btn_duplicate:"Duplikuj",copy_suffix:"(kopia)",sun_prot_waiting:"Oczekiwanie na odpowiednią wysokość słońca",
  f_blind_drive:"Napęd nie zgłasza pozycji (na ślepo)",f_blind_drive_hint:"Dla radia jednokierunkowego jak Somfy RTS. Shutter Pilot używa wtedy ostatnio wysłanej pozycji.",
  f_copy_from:"Skopiuj ustawienia z",f_copy_pick:"– wybierz roletę –",f_copy_btn:"Zastosuj",f_copy_hint:"Kopiuje pozycje, lamele, zacienienie, warunki i ustawienia okna. Encja, nazwa, obszary i czujniki pozostają bez zmian.",
  f_sunbound_title:"Dodatkowe granice słoneczne",f_sunbound_hint:"Zapobiega jazdom w biały dzień, np. podczas burzy. Puste = bez granicy.",f_b_down_sunset:"W dół nie wcześniej niż X min. przed zachodem",f_b_up_sunrise:"W górę nie wcześniej niż X min. przed wschodem",
  f_shade_hold:"Utrzymuj zacienienie (min.)",f_shade_hold_hint:"Chmura natychmiast kończy warunek. Zacienienie mimo to pozostaje przez ten czas. 0 = otwórz od razu.",
  sec_drive:"Polecenia jazdy",sec_drive_sub:"Odstęp między dwoma poleceniami",f_min_gap:"Minimalny odstęp między poleceniami",f_min_gap_hint:"Odbiorniki radiowe gubią polecenia docierające jednocześnie. Opóźnienie w obszarze nie wystarcza. Tutaj każde polecenie jest rozdzielane. 0 = wyłączone.",f_min_gap_off:"wyłączone",
  f_frost_cond_sensor:"Wskazówka: po wskazaniu encji pogodowej Shutter Pilot udostępnia czujnik „Shutter Pilot Vorhersage Tiefsttemperatur\".",
  sec_vent:"Automatyczne wietrzenie",sec_vent_sub:"Jazda do pozycji wietrzenia, gdy warunki są spełnione",f_vent_enabled:"Wietrz automatycznie",f_vent_hint:"Dopóki wszystkie warunki są spełnione, rolety jadą do pozycji wietrzenia, a potem wracają. Otwarte okno i ochrona przeciwsłoneczna mają pierwszeństwo.",f_vent_cond:"Warunek",
  sec_frost:"Ochrona przed mrozem",sec_frost_sub:"Nie zamykaj całkowicie przy mrozie",f_frost_cond:"Warunek (opcjonalnie)",f_frost_cond_hint:"Gdy warunek jest spełniony, rolety z pozycją mrozową zamykają się tylko do niej. Ma pierwszeństwo przed zamknięciem częściowym.",f_pos_closed_frost:"Ustaw pozycję mrozową",f_pos_closed_frost_hint:"Zostawia szczelinę, aby roleta nie przymarzła.",f_pos_closed_frost_val:"Pozycja przy mrozie",f_sun_cond_on_below:"Włącz poniżej",f_sun_cond_off_above:"Wyłącz powyżej",f_sun_cond_num_inv_hint:"Ochrona włącza się poniżej pierwszej wartości i działa, dopóki nie zostanie przekroczona druga.",
  sun_bound_earliest:"nie wcześniej niż",sun_bound_latest:"nie później niż",sun_jitter:"Obecność",
  sun_elevation:"Aktualna elewacja",sun_offset:"Offset",
  dash_shutter_role_up:"Tylko w górę przez tę strefę",
  dash_shutter_role_down:"Tylko w dół przez tę strefę",
  dash_shutter_role_both:"W górę i w dół przez tę strefę",
  dash_current_lux:"Aktualnie",
  f_brightness_sensor:"Czujnik jasności",f_lux_up:"Próg lux w górę",f_lux_down:"Próg lux w dół",
  f_lux_wrong_way:"Próg podnoszenia powinien być powyżej progu opuszczania: w górę powyżej, w dół poniżej. Jeśli jest niżej, między obiema wartościami obowiązują obie reguły naraz – a gdy nakładają się jeszcze okna czasowe, roleta zaczyna się wahać.",
  f_w_up_from:"Dzień roboczy góra od",f_w_up_to:"Dzień roboczy góra do",f_w_down_from:"Dzień roboczy dół od",f_w_down_to:"Dzień roboczy dół do",
  f_we_up_from:"Weekend góra od",f_we_up_to:"Weekend góra do",f_we_down_from:"Weekend dół od",f_we_down_to:"Weekend dół do",
  f_cover:"Roleta / Cover",f_window_sensor:"Czujnik okna (opcjonalnie)",
  f_win_open:"Stan okna 'otwarte'",f_win_tilt:"Stan okna 'uchylone'",f_win_tilt_none:"Wyłączone",
  f_win_state_now:"Kontaktron zgłasza teraz:",f_win_state_mismatch:"binary_sensor nigdy nie przyjmuje tego stanu – kontaktron byłby zawsze uznawany za zamknięty. Wybierz „on” lub „off”.",
  f_pos_win_open:"Pozycja przy otwartym oknie",f_pos_win_tilt:"Pozycja przy uchylonym oknie",f_pos_win_2state:"Pozycja przy otwartym oknie",
  f_pos_win_tilt_2state_hint:"Twój kontaktron zgłasza tylko otwarte i zamknięte – nie rozróżnia stanu „uchylone”. Dlatego ta jedna wartość obowiązuje w obu przypadkach. Ustaw powyżej stan uchylenia, aby uzyskać dwie osobne pozycje.",
  f_lock:"Blokada bezpieczeństwa",f_min_pos:"Minimalna pozycja przy otwartych drzwiach",
  f_area_up:"Strefa (W górę)",f_area_down:"Strefa (W dół)",
  f_pos_open:"Pozycja Otwarta",f_pos_closed:"Pozycja Zamknięta",f_pos_sun:"Pozycja osłony słonecznej",
  f_drive_after:"Nadrobić gdy okno otwarte",f_drive_after_hint:"Akcja zostanie wykonana po zamknięciu okna.",
  f_win_debounce:"Opóźnienie przy zamykaniu (sek.)",f_win_debounce_hint:"Jak długo musi utrzymać się stan „zamknięte”, zanim roleta wróci. 0 = natychmiast.",
  pick_entity:"Wybierz encję…",confirm_del_area:"Usunąć strefę \"{id}\"?",confirm_del_shutter:"Usunąć roletę?",
},
pt:{
  f_sun_cond_wrong_way:"Estes dois valores estão trocados. Trata-se de um ponto de activação com um ponto de libertação ABAIXO dele, não de um intervalo de–a. Assim, o segundo valor é descartado e a condição fica praticamente sempre cumprida. Para um intervalo de orientações existe «Apenas com a orientação certa da janela».",
  f_geo_override_values_hint:"Estes dois valores passam a valer em vez dos da zona – quer lhes toque ou não.",
  sec_export:"Exportar definições",
  sec_export_sub:"para relatos de erro no fórum",
  f_export_hint:"Cria um relatório com todas as definições, os valores actuais dos sensores e a decisão de sombreamento deste preciso momento – por estore e com a respectiva justificação. Cole o texto no fórum e ninguém terá de adivinhar o que está configurado. Contém apenas as definições do próprio Shutter Pilot e os nomes das entidades que escolheu: sem credenciais e sem localização.",
  btn_export:"Criar relatório",
  btn_export_copy:"Copiar",
  btn_export_copied:"Copiado ✓",
  btn_export_download:"Transferir",
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
  sec_basics:"Dados básicos",sec_basics_sub:"nome, modo, intervalo entre movimentos",sec_calendar_sub:"feriados, desfasamento aleatório, comando manual",sec_sunprotect_sub:"altura do sol, direção, condições",sec_shutter_sub:"entidade, nome, automatismo",sec_positions_sub:"aberto, fechado, proteção solar, gelo",
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
  f_cond_on:"Aplica-se a partir de",
  f_cond_off:"Anular abaixo de",
  f_cond_num_hint:"«Anular abaixo de» pode ser inferior a «Aplica-se a partir de» – a diferença evita oscilações em torno do limiar. Vazio = mesmo valor.",
  f_close_cond_both_hint:"Se ambas as condições estiverem preenchidas, à noite têm de se verificar as duas.",
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
  f_sun_cond_add:"Escreva um estado e prima Enter",f_sun_cond_add_hint:"Um sensor de texto só reporta o estado atual – acrescente os restantes à mão aqui. Maiúsculas não importam.",
  f_bound_none:"sem limite – toque para definir",f_bounds_title:"No mínimo / no máximo",f_bounds_hint:"Puxa o momento calculado a partir do sol para dentro de uma janela horária. Por exemplo: seguir o sol, mas nunca antes das 07:30 nem depois das 09:00. Vazio = sem limite.",f_bounds_we_hint:"Fim de semana – vazio significa que vale o valor dos dias úteis.",f_earliest_up:"Subir no mínimo às",f_latest_up:"Subir no máximo às",f_earliest_down:"Descer no mínimo às",f_latest_down:"Descer no máximo às",f_we_earliest_up:"FDS subir no mínimo",f_we_latest_up:"FDS subir no máximo",f_we_earliest_down:"FDS descer no mínimo",f_we_latest_down:"FDS descer no máximo",f_shutter_cond_hint:"Condições apenas para esta janela, p. ex. um sensor de luminosidade junto à janela ou a temperatura da divisão. Deixe vazio para usar a condição da zona.",sec_verify:"Verificar movimentos",sec_verify_sub:"para estores que perdem comandos",f_verify_hint:"Verifica após cada movimento automático se a posição foi realmente atingida e repete o comando caso contrário. Útil para estores por rádio que perdem comandos ocasionalmente.",f_verify_enabled:"Verificar movimentos",f_verify_after:"Verificar após",f_verify_tolerance:"Desvio permitido",f_verify_retries:"Novas tentativas",f_verify_event_hint:"Em caso de falha definitiva o valor guardado é corrigido e o evento shutter_pilot_cover_failed é emitido.",sec_weather:"Meteorologia",sec_weather_sub:"base das condições de sombreamento",f_weather_entity:"Entidade meteorológica",f_weather_hint:"Opcional. Se definida, o Shutter Pilot obtém a previsão do dia e disponibiliza sensores que pode escolher nas condições abaixo.",f_weather_sensors_hint:"Disponível como: temperatura máxima, mínima e condição previstas.",w_temp_max:"Máxima de hoje",w_condition:"Tempo de hoje",w_updated:"Última consulta",f_sun_cond_n:"Condição {n} (opcional)",f_sun_cond_states:"Estados permitidos",f_sun_cond_states_hint:"O sombreamento só funciona enquanto o sensor indicar um dos estados selecionados.",f_season:"Época de sombreamento",f_season_hint:"Sombrear apenas durante estes meses. O intervalo pode atravessar o ano novo, p. ex. de outubro a março.",sec_altclose:"Fecho parcial",sec_altclose_sub:"p. ex. só a meio em noites quentes",f_close_cond:"Condição (opcional)",f_close_cond_hint:"Se esta condição se verificar à noite, os estores com posição parcial fecham apenas até aí.",f_pos_closed_alt:"Usar uma posição de fecho parcial",f_pos_closed_alt_val:"Parcialmente fechado",f_pos_closed_alt_hint:"Só se aplica se a zona tiver uma condição de fecho e esta estiver satisfeita.",sec_shutter_sun:"Proteção solar",sec_shutter_sun_sub:"só necessário com outra orientação",f_geo_override:"Orientação própria deste estore",f_geo_override_hint:"Normalmente valem os valores da zona. Ative apenas se esta janela estiver virada para outro lado que as restantes da zona.",f_elev_min:"Proteção solar a partir da elevação (°)",
  f_elev_enabled:"Verificar a altura do sol",
  f_elev_enabled_hint:"Desligado: a altura do sol não conta, decidem apenas as condições. Útil quando há um sensor de luminosidade na janela – já mede o sol.",
  f_temp_sensor:"Temperatura da divisão (apenas visualização, opcional)",
  f_temp_sensor_hint:"Mostrada no cartão do painel e não decide nada. Como condição, um sensor de temperatura pertence a «Proteção solar» ou «Fecho parcial».",
  dash_room_temp:"Temperatura",f_elev_max:"Proteção solar até à elevação (°)",master_switch:"Sistema ativo",sun_prot_active:"Proteção solar ativa",sun_prot_inactive:"Proteção solar inativa",sun_prot_range:"Intervalo de elevação",
  sun_prot_cond_pending:"A altura do sol encaixa – condições ainda não cumpridas",f_sun_off_hint:"Mais desloca para mais tarde, menos para mais cedo: −15 atua um quarto de hora antes do nascer ou do pôr do sol, +15 um quarto de hora depois.",btn_duplicate:"Duplicar",copy_suffix:"(cópia)",sun_prot_waiting:"À espera da elevação solar adequada",
  f_blind_drive:"O motor não reporta posição (às cegas)",f_blind_drive_hint:"Para rádio unidirecional como Somfy RTS. O Shutter Pilot usa então a última posição enviada.",
  f_copy_from:"Copiar definições de",f_copy_pick:"– escolher estore –",f_copy_btn:"Aplicar",f_copy_hint:"Copia posições, lâminas, sombreamento, condições e definições de janela. Entidade, nome, áreas e sensores ficam iguais.",
  f_sunbound_title:"Limites solares adicionais",f_sunbound_hint:"Evita movimentos em pleno dia, p. ex. durante uma trovoada. Vazio = sem limite.",f_b_down_sunset:"Descer no mínimo X min. antes do pôr do sol",f_b_up_sunrise:"Subir no mínimo X min. antes do nascer do sol",
  f_shade_hold:"Manter sombreamento (min.)",f_shade_hold_hint:"Uma nuvem termina a condição de imediato. O sombreamento fica na mesma durante esse tempo. 0 = abrir logo.",
  sec_drive:"Comandos de marcha",sec_drive_sub:"Espaçamento entre dois comandos",f_min_gap:"Intervalo mínimo entre comandos",f_min_gap_hint:"Os recetores de rádio perdem comandos que chegam ao mesmo tempo. O atraso por área não chega. Aqui cada comando é espaçado. 0 = desligado.",f_min_gap_off:"desligado",
  f_frost_cond_sensor:"Dica: com uma entidade meteorológica definida, o Shutter Pilot fornece o sensor «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Ventilação automática",sec_vent_sub:"Ir para a posição de ventilação quando as condições se verificam",f_vent_enabled:"Ventilar automaticamente",f_vent_hint:"Enquanto todas as condições se verificarem, os estores vão para a posição de ventilação e depois voltam. Uma janela aberta e a proteção solar têm prioridade.",f_vent_cond:"Condição",
  sec_frost:"Proteção contra gelo",sec_frost_sub:"Não fechar totalmente com risco de gelo",f_frost_cond:"Condição (opcional)",f_frost_cond_hint:"Se a condição se verificar, os estores com posição de gelo fecham apenas até aí. Tem prioridade sobre o fecho parcial.",f_pos_closed_frost:"Definir posição de gelo",f_pos_closed_frost_hint:"Deixa uma folga para o estore não congelar.",f_pos_closed_frost_val:"Posição com gelo",f_sun_cond_on_below:"Ligar abaixo de",f_sun_cond_off_above:"Desligar acima de",f_sun_cond_num_inv_hint:"A proteção actua abaixo do primeiro valor e mantém-se até o segundo ser ultrapassado.",
  sun_bound_earliest:"não antes das",sun_bound_latest:"não depois das",sun_jitter:"Presença",
  sun_elevation:"Elevação atual",sun_offset:"Offset",
  dash_shutter_role_up:"Só subir por esta zona",
  dash_shutter_role_down:"Só descer por esta zona",
  dash_shutter_role_both:"Subir e descer por esta zona",
  dash_current_lux:"Atual",
  f_brightness_sensor:"Sensor de luminosidade",f_lux_up:"Limiar lux subir",f_lux_down:"Limiar lux descer",
  f_lux_wrong_way:"O limiar de subida fica acima do de descida: sobe-se acima dele e desce-se abaixo. Se ficar mais baixo, entre os dois valores valem as duas regras ao mesmo tempo – e se as janelas horárias também se sobrepuserem, a persiana oscila.",
  f_w_up_from:"Semana subir de",f_w_up_to:"Semana subir até",f_w_down_from:"Semana descer de",f_w_down_to:"Semana descer até",
  f_we_up_from:"Fim-de-semana subir de",f_we_up_to:"Fim-de-semana subir até",f_we_down_from:"Fim-de-semana descer de",f_we_down_to:"Fim-de-semana descer até",
  f_cover:"Estore / Cover",f_window_sensor:"Sensor de janela (opcional)",
  f_win_open:"Estado janela 'aberta'",f_win_tilt:"Estado janela 'basculante'",f_win_tilt_none:"Desativado",
  f_win_state_now:"O contacto indica agora:",f_win_state_mismatch:"Um binary_sensor nunca pode ter este estado – o contacto contaria sempre como fechado. Escolhe «on» ou «off».",
  f_pos_win_open:"Posição janela aberta",f_pos_win_tilt:"Posição janela basculante",f_pos_win_2state:"Posição com a janela aberta",
  f_pos_win_tilt_2state_hint:"O teu contacto só indica aberto e fechado – não distingue «basculante». Por isso este único valor vale para ambos. Define acima um estado basculante para teres duas posições separadas.",
  f_lock:"Proteção anti-bloqueio",f_min_pos:"Posição mín. porta aberta",
  f_area_up:"Zona (Subir)",f_area_down:"Zona (Descer)",
  f_pos_open:"Posição Aberta",f_pos_closed:"Posição Fechada",f_pos_sun:"Posição proteção solar",
  f_drive_after:"Recuperar se janela aberta",f_drive_after_hint:"A ação será executada assim que a janela for fechada.",
  f_win_debounce:"Atraso ao fechar (seg.)",f_win_debounce_hint:"Quanto tempo «fechado» tem de se manter antes de o estore recuar. 0 = imediato.",
  pick_entity:"Selecionar entidade…",confirm_del_area:"Eliminar zona \"{id}\"?",confirm_del_shutter:"Eliminar estore?",
},
nb:{
  f_sun_cond_wrong_way:"De to verdiene står omvendt. Dette er et påslagspunkt med et opphevingspunkt UNDER, ikke et intervall fra–til. Slik det står nå forkastes den andre verdien, og vilkåret er oppfylt så godt som hele tiden. For et intervall av himmelretninger finnes «Bare ved passende vindusretning».",
  f_geo_override_values_hint:"Disse to verdiene gjelder nå i stedet for områdets – enten du rører dem eller ikke.",
  sec_export:"Eksporter innstillinger",
  sec_export_sub:"til feilrapporter i forumet",
  f_export_hint:"Lager en rapport med alle innstillinger, sensorenes nåværende verdier og solskjermingsavgjørelsen fra akkurat nå – per rullegardin og med begrunnelse. Lim teksten inn i forumet, så slipper alle å gjette hva som er stilt inn. Den inneholder bare Shutter Pilots egne innstillinger og navnene på entitetene du har valgt: ingen påloggingsdetaljer og ingen posisjon.",
  btn_export:"Lag rapport",
  btn_export_copy:"Kopier",
  btn_export_copied:"Kopiert ✓",
  btn_export_download:"Last ned",
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
  sec_basics:"Grunndata",sec_basics_sub:"navn, modus, intervall mellom kjøringer",sec_calendar_sub:"helligdager, tilfeldig forskyvning, manuell overstyring",sec_sunprotect_sub:"solhøyde, retning, vilkår",sec_shutter_sub:"entitet, navn, automatikk",sec_positions_sub:"åpen, lukket, solskjerming, frost",
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
  f_cond_on:"Gjelder fra",
  f_cond_off:"Opphev under",
  f_cond_num_hint:"«Opphev under» kan ligge lavere enn «Gjelder fra» – avstanden hindrer flakking rundt terskelen. Tom = samme verdi.",
  f_close_cond_both_hint:"Er begge vilkårene fylt ut, må begge også gjelde om kvelden.",
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
  f_sun_cond_add:"Skriv en tilstand og trykk Enter",f_sun_cond_add_hint:"En tekstsensor melder bare sin nåværende tilstand – legg til de andre for hånd her. Store og små bokstaver spiller ingen rolle.",
  f_bound_none:"ingen grense – trykk for å angi",f_bounds_title:"Tidligst / senest",f_bounds_hint:"Trekker tidspunktet som er regnet ut fra sola inn i et tidsvindu. For eksempel: kjør etter sola, men aldri før 07:30 og aldri etter 09:00. Tom = ingen grense.",f_bounds_we_hint:"Helg – tom betyr at hverdagsverdien gjelder.",f_earliest_up:"Opp tidligst",f_latest_up:"Opp senest",f_earliest_down:"Ned tidligst",f_latest_down:"Ned senest",f_we_earliest_up:"Helg opp tidligst",f_we_latest_up:"Helg opp senest",f_we_earliest_down:"Helg ned tidligst",f_we_latest_down:"Helg ned senest",f_shutter_cond_hint:"Betingelser bare for dette vinduet, f.eks. en lyssensor ved vinduet eller romtemperaturen. La stå tom for å bruke betingelsen til området.",sec_verify:"Kontroller kjøringer",sec_verify_sub:"for persienner som mister kommandoer",f_verify_hint:"Kontrollerer etter hver automatiske kjøring om posisjonen faktisk ble nådd, og gjentar ellers kommandoen. Nyttig for radiostyrte persienner som av og til mister en kommando.",f_verify_enabled:"Kontroller kjøringer",f_verify_after:"Kontroller etter",f_verify_tolerance:"Tillatt avvik",f_verify_retries:"Nye forsøk",f_verify_event_hint:"Ved endelig feil rettes den lagrede verdien, og hendelsen shutter_pilot_cover_failed sendes.",sec_weather:"Vær",sec_weather_sub:"grunnlag for solskjermingsbetingelsene",f_weather_entity:"Vær-entitet",f_weather_hint:"Valgfritt. Er den satt, henter Shutter Pilot selv dagens varsel og gir sensorer du kan velge i betingelsene nedenfor.",f_weather_sensors_hint:"Finnes som: varslet høyeste og laveste temperatur samt værtype.",w_temp_max:"Dagens høyeste",w_condition:"Dagens vær",w_updated:"Sist hentet",f_sun_cond_n:"Betingelse {n} (valgfri)",f_sun_cond_states:"Tillatte tilstander",f_sun_cond_states_hint:"Solskjermingen virker bare så lenge sensoren melder en av de valgte tilstandene.",f_season:"Solskjermingssesong",f_season_hint:"Solskjerm bare i disse månedene. Intervallet kan gå over nyttår, f.eks. oktober til mars.",sec_altclose:"Delvis lukking",sec_altclose_sub:"f.eks. bare halvveis på varme kvelder",f_close_cond:"Betingelse (valgfri)",f_close_cond_hint:"Er betingelsen oppfylt om kvelden, lukker persienner med en delvis posisjon bare så langt.",f_pos_closed_alt:"Bruk en delvis lukkeposisjon",f_pos_closed_alt_val:"Delvis lukket",f_pos_closed_alt_hint:"Gjelder bare hvis området har en lukkebetingelse og den er oppfylt.",sec_shutter_sun:"Solbeskyttelse",sec_shutter_sun_sub:"bare nødvendig ved en annen vindusretning",f_geo_override:"Egen orientering for denne persiennen",f_geo_override_hint:"Normalt gjelder verdiene til området. Slå på bare hvis dette vinduet vender en annen vei enn de andre i området.",f_elev_min:"Solbeskyttelse fra høyde (°)",
  f_elev_enabled:"Kontroller solhøyden",
  f_elev_enabled_hint:"Av: solhøyden spiller ingen rolle, vilkårene alene avgjør. Nyttig når en lyssensor sitter ved vinduet – den måler allerede solen.",
  f_temp_sensor:"Romtemperatur (kun visning, valgfritt)",
  f_temp_sensor_hint:"Vises på dashbordkortet og avgjør ingenting. Som vilkår hører en temperatursensor under «Solskjerming» eller «Delvis lukking».",
  dash_room_temp:"Romtemperatur",f_elev_max:"Solbeskyttelse til høyde (°)",master_switch:"Systemet aktivt",sun_prot_active:"Solbeskyttelse aktiv",sun_prot_inactive:"Solbeskyttelse inaktiv",sun_prot_range:"Høydeintervall",
  sun_prot_cond_pending:"Solhøyden passer – vilkårene er ikke oppfylt ennå",f_sun_off_hint:"Pluss flytter senere, minus tidligere: −15 kjører et kvarter før soloppgang eller solnedgang, +15 et kvarter etter.",btn_duplicate:"Dupliser",copy_suffix:"(kopi)",sun_prot_waiting:"Venter på passende solhøyde",
  f_blind_drive:"Motoren melder ingen posisjon (blindt)",f_blind_drive_hint:"For enveisradio som Somfy RTS. Shutter Pilot regner da med sist sendte posisjon.",
  f_copy_from:"Kopier innstillinger fra",f_copy_pick:"– velg rullegardin –",f_copy_btn:"Bruk",f_copy_hint:"Kopierer posisjoner, lameller, solskjerming, betingelser og vindusinnstillinger. Entitet, navn, områder og sensorer endres ikke.",
  f_sunbound_title:"Ekstra solgrenser",f_sunbound_hint:"Hindrer kjøring midt på dagen, f.eks. ved tordenvær. Tom = ingen grense.",f_b_down_sunset:"Ned tidligst X min. før solnedgang",f_b_up_sunrise:"Opp tidligst X min. før soloppgang",
  f_shade_hold:"Behold solskjerming (min.)",f_shade_hold_hint:"En sky avslutter betingelsen med en gang. Solskjermingen blir likevel stående så lenge. 0 = åpne straks.",
  sec_drive:"Kjørekommandoer",sec_drive_sub:"Avstand mellom to kommandoer",f_min_gap:"Minste avstand mellom kommandoer",f_min_gap_hint:"Radiomottakere mister kommandoer som kommer samtidig. Forsinkelsen per område hjelper ikke. Her spres hver kommando. 0 = av.",f_min_gap_off:"av",
  f_frost_cond_sensor:"Tips: med en vær-entitet angitt leverer Shutter Pilot sensoren «Shutter Pilot Vorhersage Tiefsttemperatur».",
  sec_vent:"Automatisk lufting",sec_vent_sub:"Kjør til luftestilling når betingelsene er oppfylt",f_vent_enabled:"Luft automatisk",f_vent_hint:"Så lenge alle betingelser er oppfylt, kjører rullegardinene til luftestillingen og tilbake igjen. Et åpent vindu og solskjermingen går foran.",f_vent_cond:"Betingelse",
  sec_frost:"Frostbeskyttelse",sec_frost_sub:"Ikke lukk helt når det er fare for frost",f_frost_cond:"Betingelse (valgfri)",f_frost_cond_hint:"Når betingelsen gjelder, lukker rullegardiner med frostposisjon bare så langt. Går foran delvis lukking.",f_pos_closed_frost:"Angi frostposisjon",f_pos_closed_frost_hint:"Lar det stå en glipe så rullegardinen ikke fryser fast.",f_pos_closed_frost_val:"Posisjon ved frost",f_sun_cond_on_below:"Slå på under",f_sun_cond_off_above:"Slå av over",f_sun_cond_num_inv_hint:"Beskyttelsen aktiveres under den første verdien og er aktiv til den andre overskrides.",
  sun_bound_earliest:"tidligst",sun_bound_latest:"senest",sun_jitter:"Tilstedeværelse",
  sun_elevation:"Gjeldende elevasjon",sun_offset:"Offset",
  dash_shutter_role_up:"Bare opp via dette området",
  dash_shutter_role_down:"Bare ned via dette området",
  dash_shutter_role_both:"Opp og ned via dette området",
  dash_current_lux:"Nå",
  f_brightness_sensor:"Lyssensor",f_lux_up:"Lux opp-terskel",f_lux_down:"Lux ned-terskel",
  f_lux_wrong_way:"Opp-terskelen hører over ned-terskelen: opp skjer over den, ned under den. Ligger den lavere, gjelder begge reglene samtidig mellom verdiene – overlapper tidsvinduene i tillegg, pendler rullegardinen.",
  f_w_up_from:"Hverdag opp fra",f_w_up_to:"Hverdag opp til",f_w_down_from:"Hverdag ned fra",f_w_down_to:"Hverdag ned til",
  f_we_up_from:"Helg opp fra",f_we_up_to:"Helg opp til",f_we_down_from:"Helg ned fra",f_we_down_to:"Helg ned til",
  f_cover:"Persienne / Cover",f_window_sensor:"Vindussensor (valgfritt)",
  f_win_open:"Vindustilstand 'åpent'",f_win_tilt:"Vindustilstand 'vippet'",f_win_tilt_none:"Deaktivert",
  f_win_state_now:"Kontakten melder akkurat nå:",f_win_state_mismatch:"En binary_sensor kan aldri ha denne tilstanden – kontakten regnes da alltid som lukket. Velg \"on\" eller \"off\".",
  f_pos_win_open:"Posisjon ved åpent vindu",f_pos_win_tilt:"Posisjon ved vippet vindu",f_pos_win_2state:"Posisjon når vinduet er åpent",
  f_pos_win_tilt_2state_hint:"Kontakten din melder bare åpent og lukket – den kan ikke skille ut «vippet». Derfor gjelder denne ene verdien for begge. Angi en vippet tilstand over for å få to separate posisjoner.",
  f_lock:"Utestengingsbeskyttelse",f_min_pos:"Minimumsposisjon ved åpen dør",
  f_area_up:"Område (Opp)",f_area_down:"Område (Ned)",
  f_pos_open:"Posisjon Åpen",f_pos_closed:"Posisjon Lukket",f_pos_sun:"Solbeskyttelsesposisjon",
  f_drive_after:"Ta igjen hvis vindu åpent",f_drive_after_hint:"Handlingen utføres så snart vinduet lukkes.",
  f_win_debounce:"Forsinkelse ved lukking (sek.)",f_win_debounce_hint:"Hvor lenge «lukket» må holde før rullegardinen kjører tilbake. 0 = umiddelbart.",
  pick_entity:"Velg entitet…",confirm_del_area:"Slette område \"{id}\"?",confirm_del_shutter:"Slette persienne?",
},
};

class ShutterPilotPanel extends PanelBase {
  static get properties(){return{hass:{type:Object,hasChanged:()=>true},narrow:{type:Boolean},panel:{type:Object},_tab:{attribute:false},_data:{attribute:false},_editArea:{attribute:false},_editShutter:{attribute:false},_isMobile:{attribute:false},_export:{attribute:false},_exportCopied:{attribute:false}};}
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
      display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none}
    .sec:first-of-type{margin-top:6px;padding-top:0;border-top:none}
    .sec:hover h4{color:var(--sp)}
    .sec:focus-visible{outline:2px solid var(--sp);outline-offset:3px;border-radius:6px}
    .sec ha-icon{--mdc-icon-size:19px;color:var(--sp)}
    .sec h4{margin:0;font-size:14px;font-weight:600;letter-spacing:.02em;color:var(--txt)}
    .sec .sec-sub{font-size:12px;color:var(--txt2);font-weight:400}
    /* Pfeil ganz rechts, damit die Kopfzeile als aufklappbar zu lesen ist. */
    .sec .sec-chev{margin-left:auto;color:var(--txt2);transition:transform .15s ease}
    .sec.open .sec-chev{transform:rotate(180deg)}
    .sec-body{margin-bottom:4px}
    .room-temp{margin-top:8px;font-size:13px;color:var(--txt2)}
    .room-temp b{color:var(--txt)}
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
    .srow-btns{display:inline-flex;gap:4px;flex-shrink:0}
    .copy-row{display:flex;gap:8px;align-items:center}
    .cond-add{width:100%;margin-top:6px;padding:7px 9px;border:1px solid var(--divider);border-radius:8px;background:var(--card2,transparent);color:var(--txt);font-size:13px}
    .copy-row select{flex:1;min-width:0}
    .rbtn{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;padding:0;border:1px solid var(--divider);border-radius:8px;background:var(--card2,transparent);color:var(--txt2);cursor:pointer}
    .rbtn ha-icon{--mdc-icon-size:17px}
    .rbtn:hover{background:var(--sp);border-color:var(--sp);color:#fff}
    .rbtn.up:hover{background:var(--ok,#2e7d32);border-color:var(--ok,#2e7d32)}
    .rbtn.down:hover{background:var(--err,#c62828);border-color:var(--err,#c62828)}
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
    .hint.warn{color:var(--err,#c62828);font-weight:600}
    .export-box{width:100%;min-height:220px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
      font-size:11px;line-height:1.45;margin-top:10px;padding:8px;box-sizing:border-box;
      border:1px solid var(--bd,#3336);border-radius:8px;background:var(--card,#0000000d);
      color:var(--txt,inherit);resize:vertical;white-space:pre}
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
  /* Shutter Pilot legt selbst Entitäten an – Vorhersage, Schalter. Genau die
     gehören in die Bedingungsfelder, und genau die fand niemand: sie standen
     irgendwo zwischen tausend fremden. Sie kommen jetzt zuoberst, noch vor
     den Treffern des Domänen-Hinweises. */
  _isOwnEntity(id){
    if(this.hass?.entities?.[id]?.platform==="shutter_pilot")return true;
    return /^[a-z_]+\.shutter_pilot_/.test(id);
  }
  _rankEntities(ids,hint){
    const own=[],rest=[];
    for(const e of ids)(this._isOwnEntity(e)?own:rest).push(e);
    if(!hint)return{matching:own,others:rest};
    const matching=[...own],others=[];
    for(const e of rest)(this._matchesHint(e,hint)?matching:others).push(e);
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
  /* Ausserhalb des Sonnenschutzes heisst "Beschatten ab" schlicht falsch –
     dieselben Felder tragen die Bedingung fuer Schliessen, Frost und Lueften.
     Nur die Beschriftung dreht sich, die Schluessel bleiben dieselben. */
  static get SUN_SLOTS(){return ["a","b","c","d"];}
  _condLabels(slot,inverted){
    const shading=this.constructor.SUN_SLOTS.includes(slot);
    if(inverted)return{on:"f_sun_cond_on_below",off:"f_sun_cond_off_above",hint:"f_sun_cond_num_inv_hint"};
    return shading
      ? {on:"f_sun_cond_on", off:"f_sun_cond_off", hint:"f_sun_cond_num_hint"}
      : {on:"f_cond_on",     off:"f_cond_off",     hint:"f_cond_num_hint"};
  }
  _renderCondDetail(a,slot,eid,f,inverted){
    const T=k=>this.t(k);
    const L=this._condLabels(slot,inverted);
    if(eid.startsWith("binary_sensor."))
      return html`<div class="hint">${T("f_sun_cond_bin_hint")}</div>`;

    const sk=`sun_cond_${slot}_states`;
    const useStates=this._condStates(a,sk).length>0||this._isStateEntity(eid);
    if(!useStates){
      /* Frost fragt "kälter als", alles andere "wärmer/heller als" – nur die
         Beschriftung dreht sich, die Schlüssel bleiben dieselben. */
      /* Die beiden Werte sind ein Einschaltpunkt mit einem Aufhebepunkt
         darunter, kein Bereich. Wer "40 bis 130" meint, trägt sie verkehrt
         herum ein – das Backend verwirft den zweiten Wert dann stillschweigend
         und die Bedingung ist von morgens bis abends erfüllt. */
      const on=Number(a[`sun_cond_${slot}_on_above`]);
      const off=Number(a[`sun_cond_${slot}_off_below`]);
      const wrongWay=Number.isFinite(on)&&Number.isFinite(off)&&
        a[`sun_cond_${slot}_off_below`]!==""&&a[`sun_cond_${slot}_off_below`]!=null&&
        (inverted?off<on:off>on);
      return html`
        ${f(`sun_cond_${slot}_on_above`,T(L.on),"number")}
        ${f(`sun_cond_${slot}_off_below`,T(L.off),"number")}
        ${wrongWay?html`<div class="hint warn">⚠️ ${T("f_sun_cond_wrong_way")}</div>`:""}
        <div class="hint">${T(L.hint)}</div>`;
    }

    const chosen=new Set(this._condStates(a,sk));
    const toggle=v=>{
      chosen.has(v)?chosen.delete(v):chosen.add(v);
      a[sk]=[...chosen];
      this.requestUpdate();
    };
    // Bei Wetter-Entitäten die Standardlagen anbieten, sonst nur den aktuell
    // gemeldeten Zustand – abtippen ist fehleranfällig, und die übrigen kennt
    // niemand im Voraus.
    const isWeather=eid.startsWith("weather.")||eid.includes("wetterlage");
    const known=isWeather
      ? WEATHER_CONDITIONS
      : [...new Set([...chosen,String(this.hass?.states?.[eid]?.state||"")].filter(Boolean))];
    /* Bei einem Textsensor sieht man immer nur den Zustand, den er gerade
       meldet – auf "rainy" müsste man bis zum nächsten Regen warten. Deshalb
       lässt sich hier zusätzlich einer von Hand eintragen. */
    const addManual=(e)=>{
      const v=String(e.target.value||"").trim().toLowerCase();
      e.target.value="";
      if(!v||chosen.has(v))return;
      chosen.add(v);
      a[sk]=[...chosen];
      this.requestUpdate();
    };
    return html`
      <div class="field"><label>${T("f_sun_cond_states")}</label>
        <div class="preset-row">${known.map(v=>html`
          <button class="btn preset ${chosen.has(v)?"active":""}"
            @click=${()=>toggle(v)}>${v}</button>`)}</div>
        ${isWeather?"":html`
          <input class="cond-add" type="text" placeholder="${T("f_sun_cond_add")}"
            @change=${addManual} @keydown=${e=>{if(e.key==="Enter"){e.preventDefault();addManual(e);}}}>
          <div class="hint">${T("f_sun_cond_add_hint")}</div>`}
        <div class="hint">${T("f_sun_cond_states_hint")}</div></div>`;
  }
  /* Aufklappbare Abschnitte. Zugeklappt bleibt die Kopfzeile mit ihrer kurzen
     Erklaerung stehen – so ist der Aufbau eines langen Formulars auf einen
     Blick zu lesen, statt ihn zu erscrollen. Der Zustand haengt am Abschnitt,
     nicht am bearbeiteten Objekt, und ueberlebt im localStorage: wer seine
     Bedingungen staendig braucht, klappt sie einmal auf und nie wieder zu.
     Ein zugeklappter Abschnitt wird nicht gerendert – gespeichert wird aber
     das ganze Objekt, es geht also nichts verloren. */
  static get SEC_DEFAULT_OPEN(){return ["sec_weather","sec_basics","sec_shutter"];}
  static get SEC_STORE(){return "shutter_pilot_sections";}
  _secState(){
    if(!this.__secs){
      let saved=null;
      try{saved=JSON.parse(localStorage.getItem(this.constructor.SEC_STORE)||"{}");}catch(e){}
      this.__secs=(saved&&typeof saved==="object")?saved:{};
    }
    return this.__secs;
  }
  _secIsOpen(key){
    const st=this._secState();
    return key in st?!!st[key]:this.constructor.SEC_DEFAULT_OPEN.includes(key);
  }
  _secToggle(key){
    const st=this._secState();
    st[key]=!this._secIsOpen(key);
    try{localStorage.setItem(this.constructor.SEC_STORE,JSON.stringify(st));}catch(e){}
    this.requestUpdate();
  }
  _sec(icon,titleKey,subKey,body){
    const open=this._secIsOpen(titleKey);
    return html`<div class="sec ${open?"open":""}" role="button" tabindex="0"
        aria-expanded=${open?"true":"false"}
        @click=${()=>this._secToggle(titleKey)}
        @keydown=${e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();this._secToggle(titleKey);}}}>
        <ha-icon icon="${icon}"></ha-icon>
        <h4>${this.t(titleKey)}</h4>
        ${subKey?html`<span class="sec-sub">${this.t(subKey)}</span>`:""}
        <ha-icon class="sec-chev" icon="mdi:chevron-down"></ha-icon></div>
      ${open?html`<div class="sec-body">${body}</div>`:""}`;
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
      ${this._sec("mdi:weather-partly-cloudy","sec_weather","sec_weather_sub",html`
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

      `)}${this._sec("mdi:transit-connection-horizontal","sec_drive","sec_drive_sub",html`
      <div class="hint">${T("f_min_gap_hint")}</div>
      <div class="field"><label>${T("f_min_gap")}</label><div class="slider-row">
        <input type="range" min="0" max="10" step="0.5" .value=${s.min_drive_gap??0}
          @input=${e=>{s.min_drive_gap=Number(e.target.value);this.requestUpdate();}}>
        <span class="slider-val">${(s.min_drive_gap??0)==0?T("f_min_gap_off"):(s.min_drive_gap+" s")}</span></div></div>

      `)}${this._sec("mdi:check-circle-outline","sec_verify","sec_verify_sub",html`
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
        <div class="hint">${T("f_verify_event_hint")}</div>`:""}`)}

      ${/* Der WS-Befehl ist admin-pflichtig wie jeder andere hier – ein Knopf,
           der nur eine Fehlermeldung liefern kann, gehört nicht ins Formular. */""}
      ${this._isAdmin()?html`
      ${this._sec("mdi:clipboard-text-outline","sec_export","sec_export_sub",html`
      <div class="hint">${T("f_export_hint")}</div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn" @click=${()=>this._buildExport()}>
          <ha-icon icon="mdi:file-document-outline"></ha-icon>${T("btn_export")}</button>
        ${this._export?html`
          <button class="btn" @click=${()=>this._copyExport()}>
            <ha-icon icon="mdi:content-copy"></ha-icon>${this._exportCopied?T("btn_export_copied"):T("btn_export_copy")}</button>
          <button class="btn" @click=${()=>this._downloadExport()}>
            <ha-icon icon="mdi:download"></ha-icon>${T("btn_export_download")}</button>`:""}
      </div>
      ${this._export?html`
        <textarea class="export-box" readonly .value=${this._export}
          @focus=${e=>e.target.select()}></textarea>`:""}`)}`:""}

      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveSettings()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
      </div></div>`;
  }

  /* ─── Einstellungs-Export ─── */
  async _buildExport(){
    try{
      const res=await this.hass.callWS({type:"shutter_pilot/export_config"});
      this._export=res.markdown;
      this._exportCopied=false;
      this.requestUpdate();
    }catch(e){console.warn(e);alert("Error: "+e.message);}
  }
  async _copyExport(){
    if(!this._export)return;
    /* navigator.clipboard gibt es nur unter https bzw. auf localhost – im
       Heimnetz läuft Home Assistant oft schlicht auf http. Ohne den Rückfall
       auf ein Hilfs-Textfeld hätte der Knopf ausgerechnet dort nichts getan,
       wo die meisten ihn drücken. */
    try{
      await navigator.clipboard.writeText(this._export);
    }catch(e){
      const ta=document.createElement("textarea");
      ta.value=this._export;
      ta.style.position="fixed";ta.style.opacity="0";
      this.renderRoot.appendChild(ta);ta.select();
      try{document.execCommand("copy");}catch(err){console.warn(err);}
      ta.remove();
    }
    this._exportCopied=true;
    this.requestUpdate();
    setTimeout(()=>{this._exportCopied=false;this.requestUpdate();},2500);
  }
  _downloadExport(){
    if(!this._export)return;
    /* Auf einem Android-Tablet reagierte der Knopf, lud aber nichts. Zwei
       Gruende, beide auf dem Desktop unsichtbar: der WebView der
       Companion-App verwirft den Klick auf ein <a>, das nicht im Dokument
       haengt, und das sofortige revokeObjectURL() zieht die Blob-URL wieder
       weg, bevor der Download anlaeuft. Chrome am Rechner verzeiht beides. */
    const stamp=new Date().toISOString().slice(0,16).replace(/[:T]/g,"-");
    const url=URL.createObjectURL(new Blob([this._export],{type:"text/markdown"}));
    const a=document.createElement("a");
    a.href=url;a.download=`shutter-pilot-${stamp}.md`;
    a.rel="noopener";a.style.display="none";
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{a.remove();URL.revokeObjectURL(url);},4000);
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
    return html`<div class="grid">${this._sortedAreas(d).map(a=>this._dashCard(a,d))}</div>`;
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
      ${this._renderRoomTemp(area)}
      ${mode==="sun"?this._renderSunInfo(area,d):""}
      ${mode==="time"?this._renderTimeInfo(area):""}
      ${mode==="brightness"?this._renderBrightnessInfo(area):""}
      ${area.sun_protect_enabled?this._renderSunProtectInfo(area,d):""}
      <div style="margin-top:8px">${sh.length===0?html`<div style="padding:8px 0;color:var(--txt2);font-size:13px">${this.t("no_shutters")}</div>`:
        sh.map(s=>{const st=this.hass?.states?.[s.cover_entity_id];const p=st?.attributes?.current_position;
          const autoOff=this._shutterAutoOff(s);
          return html`<div class="srow ${autoOff?"auto-off":""}"><span class="nm-wrap">${this._dashShutterRole(s,id)}<span class="nm">${s.name||st?.attributes?.friendly_name||s.cover_entity_id}</span>${autoOff?html`<ha-icon class="auto-off-ic" icon="mdi:robot-off-outline" title="${this.t("dash_shutter_auto_off")}"></ha-icon>`:""}</span><span class="srow-right">${this._shutterAutoSwitch(s)}<span class="pos">${p!=null?Math.round(p)+"%":"–"}</span>${this._rowButtons(s)}</span></div>`;})}</div>
      <div class="actions">
        <button class="btn open" @click=${()=>this._coverAction(sh,"open")}><ha-icon icon="mdi:arrow-up-bold"></ha-icon>${this.t("btn_up")}</button>
        <button class="btn stop" @click=${()=>this._coverAction(sh,"stop")}><ha-icon icon="mdi:stop"></ha-icon>${this.t("btn_stop")}</button>
        <button class="btn close" @click=${()=>this._coverAction(sh,"close")}><ha-icon icon="mdi:arrow-down-bold"></ha-icon>${this.t("btn_down")}</button>
        <button class="btn sun" @click=${()=>this._coverAction(sh,"sun")}><ha-icon icon="mdi:sun-wireless-outline"></ha-icon>${this.t("btn_sun")}</button>
        <button class="btn vent" @click=${()=>this._coverAction(sh,"vent")}><ha-icon icon="mdi:air-filter"></ha-icon>${this.t("btn_vent")}</button>
      </div></div>`;
  }
  /* Reine Anzeige. Der Wert kommt direkt aus Home Assistant und entscheidet
     nichts – wer ihn als Bedingung will, traegt ihn beim Sonnenschutz ein. */
  _renderRoomTemp(area){
    const id=String(area.temp_sensor||"").trim();
    if(!id)return "";
    const st=this.hass?.states?.[id];
    if(!st)return "";
    const raw=st.state;
    if(raw==null||["unknown","unavailable",""].includes(String(raw)))return "";
    const unit=st.attributes?.unit_of_measurement||"";
    const num=Number(raw);
    const val=Number.isFinite(num)?num.toFixed(1):String(raw);
    return html`<div class="sun-row room-temp">
      <ha-icon icon="mdi:thermometer"></ha-icon>
      <span>${this.t("dash_room_temp")}: <b>${val}${unit?" "+unit:""}</b></span></div>`;
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
    const azEnabled=st.azimuth_enabled??!!area.azimuth_enabled;
    /* "Warte auf passende Sonnenhöhe" stand vorher genau dann da, wenn die
       Höhe bereits passte – wer 0°–90° einstellte, bekam die Meldung den
       ganzen Tag und suchte den Fehler bei der Elevation. Gesagt wird jetzt,
       woran es wirklich hängt. */
    let statusText=this.t("sun_prot_inactive");
    if(active)statusText=this.t("sun_prot_active");
    else if(st.elevation_in_range===false)statusText=this.t("sun_prot_waiting");
    else if(azEnabled&&st.azimuth_in_range===false)statusText=this.t("sun_prot_wrong_dir");
    else if(inRange)statusText=this.t("sun_prot_cond_pending");
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
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editArea={id:"",name:"",mode:"time",drive_delay:10,workday_sensor:"",random_offset:0,manual_override:"never",sun_protect_enabled:false,elevation_min:0,elevation_max:90,shade_hold:0,azimuth_enabled:false,azimuth_min:90,azimuth_max:270,season_from:"",season_to:"",sun_cond_close_entity:"",sun_cond_frost_entity:"",vent_enabled:false,sun_cond_vent_a_entity:"",sun_cond_vent_b_entity:"",sun_cond_a_entity:"",sun_cond_a_on_above:"",sun_cond_a_off_below:"",sun_cond_b_entity:"",sun_cond_b_on_above:"",sun_cond_b_off_below:"",sun_cond_c_entity:"",sun_cond_d_entity:"",down_light_entity:"",down_light_brightness:40,time_up:"07:00",time_down:"19:00",time_we_up:"08:00",time_we_down:"20:00",sunrise_offset:0,sunset_offset:0,brightness_sensor:"",lux_down:400,lux_up:500,w_up_from:"05:00",w_up_to:"09:00",w_down_from:"16:00",w_down_to:"23:59",we_up_from:"07:00",we_up_to:"10:00",we_down_from:"16:00",we_down_to:"23:59",_isNew:true};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${this.t("add_area")}</button></div>
      ${!d.areas?.length?html`<div class="empty">${this.t("empty_areas_list")}</div>`:
        this._isMobile?html`
          <div class="grid">
            ${this._sortedAreas(d).map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
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
                  <button class="btn" title="${this.t("btn_duplicate")}" @click=${()=>this._duplicateArea(a)}><ha-icon icon="mdi:content-duplicate"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteArea(id)}><ha-icon icon="mdi:delete"></ha-icon></button>
                </div>
              </div>`;})}
          </div>
        `:html`
          <div class="card"><div class="table-wrap"><table>
            <tr><th>${this.t("col_name")}</th><th>${this.t("col_id")}</th><th>${this.t("col_mode")}</th><th>${this.t("col_shutters")}</th><th></th></tr>
            ${this._sortedAreas(d).map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
              return html`<tr>
                <td><strong>${a.name||id}</strong></td><td style="color:var(--txt2)">${id}</td>
                <td><span class="chip ${a.mode||"time"}">${this._modeName(a.mode)}</span></td>
                <td>${cnt}</td>
                <td style="text-align:right">
                  <button class="btn edit" @click=${()=>{this._editArea={...a,_isNew:false};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn" title="${this.t("btn_duplicate")}" @click=${()=>this._duplicateArea(a)}><ha-icon icon="mdi:content-duplicate"></ha-icon></button>
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
    /* Zahl, die auch leer bleiben darf: Number("") wäre 0 – und 0 ist hier
       eine gültige Schranke ("ab Sonnenuntergang"), nicht "aus". */
    const numOpt=(k,lbl)=>html`<div class="field"><label>${lbl}</label><input type="number" .value=${a[k]??""}
      @input=${e=>{const v=e.target.value.trim();a[k]=v===""?"":Number(v);}}></div>`;
    const tm=(k,lbl)=>this._timeField(a,k,lbl);
    // Klammern dürfen leer bleiben, deshalb allowEmpty.
    const bd=(k,lbl,dflt)=>this._timeField(a,k,lbl,dflt,true);
    const rng=(k,lbl,min,max,step=1,suffix="")=>html`<div class="field"><label>${lbl}</label><div class="slider-row">
      <input type="range" min="${min}" max="${max}" step="${step}" .value=${a[k]??min} @input=${e=>{a[k]=Number(e.target.value);this.requestUpdate();}}>
      <span class="slider-val">${a[k]??min}${suffix}</span></div></div>`;
    const ep=(k,lbl,domains,hint=null)=>this._entityField(a,k,lbl,domains,hint);
    return html`<div class="form"><h3>${a._isNew?T("add_area"):T("edit_area")}</h3>

      ${this._sec("mdi:tag-outline","sec_basics","sec_basics_sub",html`
      ${f("name",T("f_name"))}
      ${a._isNew?"":html`<div class="field"><label>${T("col_id")}</label><input disabled .value=${a.id}></div>`}
      <div class="field"><label>${T("f_mode")}</label>
        <select .value=${m} @change=${e=>{a.mode=e.target.value;this.requestUpdate();}}>
          <option value="time" ?selected=${m==="time"}>${T("mode_time")}</option>
          <option value="brightness" ?selected=${m==="brightness"}>${T("mode_brightness")}</option>
          <option value="sun" ?selected=${m==="sun"}>${T("mode_sun")}</option></select></div>
      ${rng("drive_delay",T("f_drive_delay"),0,120,1,"s")}
      ${ep("temp_sensor",T("f_temp_sensor"),["sensor"],HINTS.temperature)}
      <div class="hint">${T("f_temp_sensor_hint")}</div>

      `)}${this._sec(MODE_ICONS[m]||"mdi:clock-outline","sec_schedule","sec_schedule_"+m,html`
      ${m==="time"?html`${tm("time_up",T("f_time_up"))}${tm("time_down",T("f_time_down"))}${tm("time_we_up",T("f_time_we_up"))}${tm("time_we_down",T("f_time_we_down"))}`:
        m==="sun"?html`${rng("sunrise_offset",T("f_sunrise_off"),-60,60,1," min")}${rng("sunset_offset",T("f_sunset_off"),-60,60,1," min")}
          <div class="hint">${T("f_sun_off_hint")}</div>
          <div class="hint" style="margin-top:10px"><b>${T("f_bounds_title")}</b><br>${T("f_bounds_hint")}</div>
          ${bd("sun_earliest_up",T("f_earliest_up"),"07:30")}${bd("sun_latest_up",T("f_latest_up"),"09:00")}
          ${bd("sun_earliest_down",T("f_earliest_down"),"17:00")}${bd("sun_latest_down",T("f_latest_down"),"22:30")}
          <div class="hint">${T("f_bounds_we_hint")}</div>
          ${bd("sun_we_earliest_up",T("f_we_earliest_up"),"08:00")}${bd("sun_we_latest_up",T("f_we_latest_up"),"09:00")}
          ${bd("sun_we_earliest_down",T("f_we_earliest_down"),"17:00")}${bd("sun_we_latest_down",T("f_we_latest_down"),"22:30")}`:
        html`${ep("brightness_sensor",T("f_brightness_sensor"),["sensor"],HINTS.illuminance)}${rng("lux_up",T("f_lux_up"),0,1000,1," lx")}${rng("lux_down",T("f_lux_down"),0,1000,1," lx")}
          ${/* Hoch gilt oberhalb, Runter unterhalb. Liegt die Hoch-Schwelle
               darunter, ist dazwischen beides zugleich wahr – solange sich die
               Zeitfenster nicht überschneiden fällt das niemandem auf, danach
               pendelt der Rollladen. */""}
          ${Number(a.lux_up??500)<=Number(a.lux_down??400)?html`<div class="hint warn">⚠️ ${T("f_lux_wrong_way")}</div>`:""}
          ${tm("w_up_from",T("f_w_up_from"))}${tm("w_up_to",T("f_w_up_to"))}${tm("w_down_from",T("f_w_down_from"))}${tm("w_down_to",T("f_w_down_to"))}
          ${tm("we_up_from",T("f_we_up_from"))}${tm("we_up_to",T("f_we_up_to"))}${tm("we_down_from",T("f_we_down_from"))}${tm("we_down_to",T("f_we_down_to"))}
          <div class="hint" style="margin-top:10px"><b>${T("f_sunbound_title")}</b><br>${T("f_sunbound_hint")}</div>
          ${numOpt("b_down_after_sunset",T("f_b_down_sunset"))}
          ${numOpt("b_up_before_sunrise",T("f_b_up_sunrise"))}`}

      `)}${this._sec("mdi:calendar-check","sec_calendar","sec_calendar_sub",html`
      ${ep("workday_sensor",T("f_workday_sensor"),["binary_sensor"],HINTS.workday)}
      <div class="hint">${T("f_workday_hint")}</div>
      ${rng("random_offset",T("f_random_offset"),0,60,1," min")}
      <div class="hint">${T("f_random_offset_hint")}</div>
      <div class="field"><label>${T("f_manual_override")}</label>
        <select .value=${a.manual_override||"never"} @change=${e=>{a.manual_override=e.target.value;this.requestUpdate();}}>
          ${OVERRIDE_OPTS.map(o=>html`<option value="${o}" ?selected=${(a.manual_override||"never")===o}>${T("f_override_"+o)}</option>`)}
        </select><div class="hint">${T("f_manual_override_hint")}</div></div>

      `)}${this._sec("mdi:sun-wireless-outline","sec_sunprotect","sec_sunprotect_sub",html`
      <div class="field"><label><input type="checkbox" .checked=${!!a.sun_protect_enabled} @change=${e=>{a.sun_protect_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_sun_protect")}</label></div>
      ${a.sun_protect_enabled?html`
        <div class="field"><label><input type="checkbox" .checked=${a.elevation_enabled!==false}
          @change=${e=>{a.elevation_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_elev_enabled")}</label>
          <div class="hint">${T("f_elev_enabled_hint")}</div></div>
        ${a.elevation_enabled!==false?html`
          ${rng("elevation_min",T("f_elev_min"),-5,45,0.5,"°")}${rng("elevation_max",T("f_elev_max"),-5,90,0.5,"°")}`:""}
        ${rng("shade_hold",T("f_shade_hold"),0,120,5," min")}
        <div class="hint">${T("f_shade_hold_hint")}</div>
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

      `)}${this._sec("mdi:arrow-collapse-down","sec_altclose","sec_altclose_sub",html`
      <div class="hint">${T("f_close_cond_hint")}</div>
      ${ep("sun_cond_close_entity",T("f_close_cond")+" 1",["binary_sensor","sensor","weather"],HINTS.condition)}
      ${a.sun_cond_close_entity?this._renderCondDetail(a,"close",a.sun_cond_close_entity,f):""}
      ${/* Die zweite erst anbieten, wenn die erste steht – zwei leere Felder
           uebereinander sehen nach Pflicht aus. Beide muessen zutreffen. */""}
      ${a.sun_cond_close_entity?html`
        ${ep("sun_cond_close_b_entity",T("f_close_cond")+" 2",["binary_sensor","sensor","weather"],HINTS.condition)}
        ${a.sun_cond_close_b_entity?this._renderCondDetail(a,"close_b",a.sun_cond_close_b_entity,f):""}
        <div class="hint">${T("f_close_cond_both_hint")}</div>`:""}

      `)}${this._sec("mdi:snowflake-alert","sec_frost","sec_frost_sub",html`
      <div class="hint">${T("f_frost_cond_hint")}</div>
      <div class="hint">${T("f_frost_cond_sensor")}</div>
      ${ep("sun_cond_frost_entity",T("f_frost_cond"),["binary_sensor","sensor","weather"],HINTS.condition)}
      ${a.sun_cond_frost_entity?this._renderCondDetail(a,"frost",a.sun_cond_frost_entity,f,true):""}

      `)}${this._sec("mdi:air-filter","sec_vent","sec_vent_sub",html`
      <div class="field"><label><input type="checkbox" .checked=${!!a.vent_enabled}
        @change=${e=>{a.vent_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_vent_enabled")}</label>
        <div class="hint">${T("f_vent_hint")}</div></div>
      ${a.vent_enabled?html`
        ${ep("sun_cond_vent_a_entity",T("f_vent_cond")+" 1",["binary_sensor","sensor","weather"],HINTS.condition)}
        ${a.sun_cond_vent_a_entity?this._renderCondDetail(a,"vent_a",a.sun_cond_vent_a_entity,f):""}
        ${a.sun_cond_vent_a_entity?html`
          ${ep("sun_cond_vent_b_entity",T("f_vent_cond")+" 2",["binary_sensor","sensor","weather"],HINTS.condition)}
          ${a.sun_cond_vent_b_entity?this._renderCondDetail(a,"vent_b",a.sun_cond_vent_b_entity,f):""}`:""}`:""}

      `)}${this._sec("mdi:lightbulb-outline","sec_light","sec_light_sub",html`
      ${ep("down_light_entity",T("f_light_entity"),["light","switch"])}
      ${rng("down_light_brightness",T("f_light_brightness"),0,100,1,"%")}`)}

      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveArea()}><ha-icon icon="mdi:content-save"></ha-icon>${T("btn_save")}</button>
        <button class="btn cancel" @click=${()=>{this._editArea=null;this.requestUpdate();}}>${T("btn_cancel")}</button></div></div>`;
  }

  /* ─── Shutters Tab ─── */
  _renderShutters(d){
    if(this._editShutter)return this._renderShutterForm(d);
    const areaName=id=>{const a=d.areas.find(x=>x.id===id);return a?a.name:id;};const T=k=>this.t(k);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editShutter={cover_entity_id:"",name:"",window_entity_id:"",window_open_state:"on",window_tilted_state:"none",position_when_window_open:100,position_when_window_tilted:50,lock_protection:false,window_tilted_entity_id:"",min_position_when_open:20,area_up_id:d.areas[0]?.id||"",area_down_id:d.areas[0]?.id||"",position_open:100,position_closed:0,position_sun_protect:50,position_closed_alt:"",position_closed_frost:"",sun_geometry_override:false,tilt_enabled:false,tilt_open:100,tilt_closed:0,tilt_sun_protect:30,drive_after_close:false,window_close_debounce:5,blind_drive:false,_isNew:true,_index:null};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>${T("add_shutter")}</button></div>
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
                  <button class="btn edit" @click=${()=>{this._copyFrom="";this._editShutter={window_close_debounce:5,...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
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
                  <button class="btn edit" @click=${()=>{this._copyFrom="";this._editShutter={window_close_debounce:5,...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
                  <button class="btn del" @click=${()=>this._deleteShutter(i)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
          </table></div></div>
        `}`;
  }
  /* „Einstellungen übernehmen von …" – der kleine Bruder von Profilen.
     Nimmt die Tipparbeit ab, ohne das Datenmodell umzubauen: kopiert wird
     alles ausser Identität und Bereichszuordnung, denn genau die unterscheidet
     zwei sonst gleiche Rollläden. */
  _renderCopyFrom(d,s){
    const T=k=>this.t(k);
    const others=(d.shutters||[]).filter(o=>o.cover_entity_id&&o.cover_entity_id!==s.cover_entity_id);
    if(!others.length)return "";
    const pick=this._copyFrom||"";
    return html`<div class="field"><label>${T("f_copy_from")}</label>
      <div class="copy-row">
        <select .value=${pick} @change=${e=>{this._copyFrom=e.target.value;this.requestUpdate();}}>
          <option value="">${T("f_copy_pick")}</option>
          ${others.map(o=>html`<option value="${o.cover_entity_id}" ?selected=${pick===o.cover_entity_id}>${o.name||o.cover_entity_id}</option>`)}
        </select>
        <button class="btn" ?disabled=${!pick} @click=${()=>this._applyCopyFrom(others)}>
          <ha-icon icon="mdi:content-copy"></ha-icon>${T("f_copy_btn")}</button>
      </div>
      <div class="hint">${T("f_copy_hint")}</div></div>`;
  }
  _winEntityId(s){
    const v=s.window_entity_id;
    return String((Array.isArray(v)?v[0]:v)||"").trim();
  }
  /* Der gemeldete Zustand gehoert immer in die Liste. Ein binary_sensor kennt
     nur on und off; wer daneben "open" waehlt, hat einen Kontakt konfiguriert,
     der nie als offen gilt - und genau das war nirgends zu sehen. */
  _winOpenOpts(s){
    const cur=String(this.hass?.states?.[this._winEntityId(s)]?.state||"").toLowerCase().trim();
    const opts=[...WIN_OPEN_OPTS];
    if(cur&&!["unknown","unavailable"].includes(cur)&&!opts.includes(cur))opts.push(cur);
    return opts;
  }
  _renderWinStateHint(s){
    const T=k=>this.t(k);
    const id=this._winEntityId(s);
    if(!id)return "";
    const st=this.hass?.states?.[id];
    if(!st)return "";
    const cur=String(st.state||"");
    const line=html`<div class="hint">${T("f_win_state_now")} <code>${cur}</code></div>`;
    // Ein binary_sensor kann nur on oder off melden. Alles andere trifft nie
    // zu, der Kontakt gilt dauerhaft als geschlossen und keine einzige
    // Reaktion laeuft - ohne dass irgendwo etwas davon steht.
    if(!id.startsWith("binary_sensor."))return line;
    if(["on","off"].includes(winCanon(s.window_open_state||"on")))return line;
    return html`${line}<div class="hint warn">⚠️ ${T("f_win_state_mismatch")}</div>`;
  }
  /* Identität und Zuordnung bleiben stehen; alles andere kommt von der Vorlage.
     Eine Ausschlussliste statt einer Erlaubnisliste, damit ein künftiges Feld
     nicht stillschweigend vom Kopieren ausgenommen bleibt. */
  static get COPY_KEEP(){return ["cover_entity_id","name","area_up_id","area_down_id",
    "window_entity_id","window_tilted_entity_id","shutter_auto_entity_id",
    "_isNew","_index"];}
  _applyCopyFrom(others){
    const src=others.find(o=>o.cover_entity_id===this._copyFrom);
    if(!src||!this._editShutter)return;
    const keep=this.constructor.COPY_KEEP;
    const target=this._editShutter;
    for(const [k,v] of Object.entries(src)){
      if(keep.includes(k))continue;
      target[k]=Array.isArray(v)?[...v]:v;
    }
    this._copyFrom="";
    this.requestUpdate();
  }
  _renderShutterForm(d){
    const s=this._editShutter;const areas=this._sortedAreas(d);const T=k=>this.t(k);
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

      ${this._sec("mdi:window-shutter","sec_shutter","sec_shutter_sub",html`
      ${ep("cover_entity_id",T("f_cover"),["cover"],null)}
      ${f("name",T("f_name"))}
      <div class="field"><label><input type="checkbox" .checked=${s.automation_enabled!==false}
        @change=${e=>{s.automation_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_shutter_auto")}</label>
        <div class="hint">${T("f_shutter_auto_hint")}</div></div>
      ${this._renderCopyFrom(d,s)}

      `)}${this._sec("mdi:map-marker","sec_areas","sec_areas_sub",html`
      ${areaSel("area_up_id",T("f_area_up"))}
      ${areaSel("area_down_id",T("f_area_down"))}

      `)}${this._sec("mdi:arrow-up-down","sec_positions","sec_positions_sub",html`
      ${pct("position_open",T("f_pos_open"))}
      ${pct("position_closed",T("f_pos_closed"))}
      ${pct("position_sun_protect",T("f_pos_sun"))}
      <div class="field"><label><input type="checkbox" .checked=${s.position_closed_alt!==""&&s.position_closed_alt!=null}
        @change=${e=>{s.position_closed_alt=e.target.checked?50:"";this.requestUpdate();}}> ${T("f_pos_closed_alt")}</label>
        <div class="hint">${T("f_pos_closed_alt_hint")}</div></div>
      ${s.position_closed_alt!==""&&s.position_closed_alt!=null?pct("position_closed_alt",T("f_pos_closed_alt_val")):""}
      <div class="field"><label><input type="checkbox" .checked=${s.position_closed_frost!==""&&s.position_closed_frost!=null}
        @change=${e=>{s.position_closed_frost=e.target.checked?10:"";this.requestUpdate();}}> ${T("f_pos_closed_frost")}</label>
        <div class="hint">${T("f_pos_closed_frost_hint")}</div></div>
      ${s.position_closed_frost!==""&&s.position_closed_frost!=null?pct("position_closed_frost",T("f_pos_closed_frost_val")):""}

      `)}${this._sec("mdi:sun-compass","sec_shutter_sun","sec_shutter_sun_sub",html`
      <div class="field"><label><input type="checkbox" .checked=${!!s.sun_geometry_override}
        @change=${e=>{s.sun_geometry_override=e.target.checked;this.requestUpdate();}}> ${T("f_geo_override")}</label>
        <div class="hint">${T("f_geo_override_hint")}</div></div>
      ${/* Direkt unter den Haken, nicht hinter den Bedingungsblock: sonst hakt
           man an, sieht darunter die Bedingungen erscheinen – und findet die
           Felder nie, die der Haken tatsächlich freischaltet. Genau so ist im
           Forum eine Beschattung eingerichtet worden, die nie lief. */""}
      ${s.sun_geometry_override?html`
        <div class="field"><label><input type="checkbox" .checked=${s.elevation_enabled!==false}
          @change=${e=>{s.elevation_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_elev_enabled")}</label>
          <div class="hint">${T("f_elev_enabled_hint")}</div></div>
        ${s.elevation_enabled!==false?html`
          ${pctRange("elevation_min",T("f_elev_min"),-5,45,0.5,"°")}
          ${pctRange("elevation_max",T("f_elev_max"),-5,90,0.5,"°")}`:""}
        <div class="hint">${T("f_geo_override_values_hint")}</div>
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
      <div class="hint">${T("f_shutter_cond_hint")}</div>
      ${this._renderConditionSlots(s,ep,f)}

      `)}${this._sec("mdi:window-open-variant","sec_window","sec_window_sub",html`
      ${ep("window_entity_id",T("f_window_sensor"),["binary_sensor","sensor"],HINTS.window)}
      ${s.window_entity_id||s.window_tilted_entity_id?html`
        ${ep("window_tilted_entity_id",T("f_window_tilt_sensor"),["binary_sensor","sensor"],HINTS.window)}
        <div class="hint">${T("f_window_tilt_sensor_hint")}</div>`:""}
      ${sel("window_open_state",T("f_win_open"),this._winOpenOpts(s))}
      ${this._renderWinStateHint(s)}
      ${sel("window_tilted_state",T("f_win_tilt"),
        [{v:"none",l:T("f_win_tilt_none")},...WIN_TILT_OPTS.filter(x=>x!=="none").map(x=>({v:x,l:x}))])}
      ${(s.window_tilted_state&&s.window_tilted_state!=="none")||s.window_tilted_entity_id
        ? html`${pct("position_when_window_open",T("f_pos_win_open"))}
               ${pct("position_when_window_tilted",T("f_pos_win_tilt"))}`
        /* Zweiwertiger Kontakt: gefahren wird die Kipp-Position, auch bei
           "offen" - offen und gekippt sind nicht zu unterscheiden. Zwei
           Schieber nebeneinander liessen den oberen wie den wirksamen
           aussehen, und der eingestellte Wert kam nie zum Zug. */
        : html`${pct("position_when_window_tilted",T("f_pos_win_2state"))}
               <div class="hint">${T("f_pos_win_tilt_2state_hint")}</div>`}
      <div class="field"><label><input type="checkbox" .checked=${!!s.lock_protection} @change=${e=>{s.lock_protection=e.target.checked;this.requestUpdate();}}> ${T("f_lock")}</label></div>
      ${s.lock_protection?pct("min_position_when_open",T("f_min_pos")):""}
      <div class="field"><label><input type="checkbox" .checked=${!!s.drive_after_close} @change=${e=>{s.drive_after_close=e.target.checked;this.requestUpdate();}}> ${T("f_drive_after")}</label>
        <div class="hint">${T("f_drive_after_hint")}</div></div>
      ${pctRange("window_close_debounce",T("f_win_debounce"),0,30,1," s")}
      <div class="hint">${T("f_win_debounce_hint")}</div>
      <div class="field"><label><input type="checkbox" .checked=${!!s.blind_drive}
        @change=${e=>{s.blind_drive=e.target.checked;this.requestUpdate();}}> ${T("f_blind_drive")}</label>
        <div class="hint">${T("f_blind_drive_hint")}</div></div>

      `)}${this._sec("mdi:blinds-horizontal","sec_slats","sec_slats_sub",html`
      <div class="field"><label><input type="checkbox" .checked=${!!s.tilt_enabled} @change=${e=>{s.tilt_enabled=e.target.checked;this.requestUpdate();}}> ${T("f_tilt")}</label>
        <div class="hint">${this._supportsTilt(s.cover_entity_id)?T("f_tilt_hint"):T("f_tilt_unsupported")}</div></div>
      ${s.tilt_enabled?html`${pct("tilt_open",T("f_tilt_open"))}${pct("tilt_closed",T("f_tilt_closed"))}${pct("tilt_sun_protect",T("f_tilt_sun"))}`:""}`)}

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
  /* Einzelbedienung je Rollladen. Bewusst dieselben Dienste wie die
     Bereichsknöpfe – nur die Auswahl ist eine andere. */
  _rowButtons(shutter){
    if(!shutter?.cover_entity_id)return "";
    const act=a=>this._coverAction([shutter],a);
    return html`<span class="srow-btns">
      <button class="rbtn up" title="${this.t("btn_up")}" @click=${()=>act("open")}><ha-icon icon="mdi:arrow-up-bold"></ha-icon></button>
      <button class="rbtn stop" title="${this.t("btn_stop")}" @click=${()=>act("stop")}><ha-icon icon="mdi:stop"></ha-icon></button>
      <button class="rbtn down" title="${this.t("btn_down")}" @click=${()=>act("close")}><ha-icon icon="mdi:arrow-down-bold"></ha-icon></button>
    </span>`;
  }
  /* Der Mindestabstand aus den Einstellungen sitzt im Backend, in
     set_cover_position(). Diese Knöpfe rufen die cover-Dienste aber direkt
     auf – damit Home Assistant die Rechte je Entität selbst prüft, so wie es
     das für Dienstaufrufe aus dem Frontend tut. Deshalb wird hier ein zweites
     Mal gestaffelt, statt den Weg übers Backend zu nehmen und diese Prüfung
     zu verlieren.

     Gestaffelt wird auch "Stop": ein verschluckter Stopp-Befehl lässt den
     Rollladen bis zum Anschlag weiterfahren, ein um Sekunden späterer nicht. */
  async _coverAction(shutters,action){
    const list=(shutters||[]).filter(s=>s?.cover_entity_id);
    if(!list.length)return;
    const gap=Math.max(0,Number(this._data?.settings?.min_drive_gap)||0);
    const call=(s)=>{
      const eid=s.cover_entity_id;
      if(action==="open")return this.hass.callService("cover","open_cover",{entity_id:eid});
      if(action==="close")return this.hass.callService("cover","close_cover",{entity_id:eid});
      if(action==="stop")return this.hass.callService("cover","stop_cover",{entity_id:eid});
      // Lüften nutzt dieselbe Position wie ein gekipptes Fenster.
      const pos=action==="sun"?(s.position_sun_protect??50):(s.position_when_window_tilted??50);
      return this.hass.callService("cover","set_cover_position",{entity_id:eid,position:pos});
    };
    if(!gap){await Promise.all(list.map(call));return;}
    for(let i=0;i<list.length;i++){
      if(i)await new Promise(r=>setTimeout(r,gap*1000));
      await call(list[i]);
    }
  }
  /* Gespeichert wird in Anlagereihenfolge; angezeigt alphabetisch. Sonst
     steht derselbe Bereich im Dashboard woanders als im Bereiche-Tab, je
     nachdem wann er angelegt wurde. Sortiert wird auf einer Kopie – die
     Reihenfolge in den Optionen bleibt unangetastet. */
  _sortedAreas(d){
    const areas=(d&&d.areas)||[];
    return [...areas].sort((x,y)=>String(x.name||x.id||"").localeCompare(
      String(y.name||y.id||""),undefined,{sensitivity:"base",numeric:true}));
  }
  /* Kopie zum Bearbeiten, nicht zum Speichern: id und Schalter-Entität fallen
     weg, damit _saveArea() eine neue id aus dem Namen baut und die Kopie nicht
     den Automatik-Schalter des Originals mitbenutzt. */
  _duplicateArea(a){
    const copy={...a};
    delete copy.id;delete copy.auto_entity_id;
    copy.name=`${a.name||a.id||""} ${this.t("copy_suffix")}`.trim();
    copy._isNew=true;
    this._editArea=copy;this.requestUpdate();
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
