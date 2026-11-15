/* Die gemeinsame Vorlage fuer die Render-Tests: ein Panel mit je zwei
   Eintraegen pro Geraeteart und Bereichen in allen vier Modi. Als Funktion,
   damit jeder Test seine eigene Kopie bekommt und nichts umstellt, was der
   naechste erwartet. */
import { Panel, flat } from "./harness.mjs";

export function makePanel() {
  /* Die Falle, die 2.20.0 durchgelassen hat: `_renderCopyFrom` steigt bei
     `others.length === 0` frueh aus. Mit je *einem* Eintrag pro Geraeteart wird
     der Block nie gerendert – und ein ReferenceError darin faellt nie auf.
     Deshalb hier von jeder Art ZWEI. */
  const states = {};
  const mk = (id, pos) => { states[id] = { state: pos > 0 ? "open" : "closed",
    attributes: { current_position: pos, supported_features: 15, friendly_name: id } }; };
  mk("cover.rollladen_a", 100); mk("cover.rollladen_b", 0);
  mk("cover.markise_a", 0);     mk("cover.markise_b", 100);
  mk("cover.fenster_a", 0);     mk("cover.fenster_b", 30);
  states["sensor.lux"]  = { state: "25000", attributes: { unit_of_measurement: "lx" } };
  states["sensor.temp"] = { state: "24.0",  attributes: { unit_of_measurement: "°C" } };
  states["sensor.wind"] = { state: "3.0",   attributes: { unit_of_measurement: "m/s" } };
  states["binary_sensor.rain"] = { state: "off", attributes: { device_class: "moisture" } };
  states["binary_sensor.fenster"] = { state: "off", attributes: {} };
  states["button.my_pos"] = { state: "unknown", attributes: {} };
  states["weather.home"] = { state: "sunny", attributes: {} };

  const p = Object.create(Panel.prototype);
  p.hass = { states, user: { is_admin: true }, language: "de", callWS: async () => ({}) };
  p.t = k => k;
  p.requestUpdate = () => {};
  p._secIsOpen = () => true;
  p._isAdmin = () => true;
  p._isMobile = false;

  const areas = [
    { id:"living", name:"Wohnbereich", mode:"brightness", sun_protect_enabled:true,
      elevation_min:0, elevation_max:90, azimuth_enabled:true, azimuth_min:135, azimuth_max:225,
      shade_hold:10, brightness_sensor:"sensor.lux", lux_up:500, lux_down:400,
      sun_cond_a_entity:"sensor.lux", sun_cond_a_on_above:30000, sun_cond_a_off_below:20000,
      sun_cond_b_entity:"binary_sensor.rain", sun_cond_close_entity:"sensor.temp",
      sun_cond_frost_entity:"sensor.temp", vent_enabled:true, sun_cond_vent_a_entity:"sensor.temp",
      sun_cond_no_up_entity:"binary_sensor.rain", sun_cond_sp_alt_entity:"sensor.temp",
      manual_override:"never", workday_sensor:"binary_sensor.fenster" },
    { id:"sleep", name:"Schlafbereich", mode:"sun", sun_protect_enabled:false, sunrise_offset:0, sunset_offset:0 },
    { id:"none",  name:"Ohne Zeitplan", mode:"none", sun_protect_enabled:true, elevation_enabled:false, azimuth_enabled:false },
    { id:"time",  name:"Nach Uhr", mode:"time", time_up:"07:00", time_down:"19:00", sun_protect_enabled:false },
  ];
  const shutters = [
    { cover_entity_id:"cover.rollladen_a", name:"Rollladen A", area_up_id:"living", area_down_id:"living",
      position_open:100, position_closed:0, position_sun_protect:50, tilt_enabled:true,
      window_entity_id:"binary_sensor.fenster", window_open_state:"on", window_tilted_state:"none",
      lock_protection:true, min_position_when_open:20, drive_after_close:true,
      sun_geometry_override:true, elevation_enabled:true, blind_drive:true, my_position_entity:"button.my_pos",
      keep_position_sun_protect:true, keep_tilt_open:true, tilt_after_position:true,
      storm_guard:true, storm_position:100, storm_tilt:100, sun_cond_rwind_entity:"binary_sensor.windalarm",
      automation_lock_entity:"input_boolean.fenster_putzen", frost_lock:true, frost_lock_position:0, frost_lock_tilt:100, window_react:false, drive_after_close_up:true },
    { cover_entity_id:"cover.rollladen_b", name:"Rollladen B", area_up_id:"living", area_down_id:"living",
      position_open:100, position_closed:0, position_sun_protect:50 },
    { cover_entity_id:"cover.markise_a", name:"Markise A", device_kind:"awning", area_down_id:"living",
      position_open:0, position_sun_protect:100, awning_track_enabled:true, blind_drive:true,
      my_position_entity:"button.my_pos", sun_cond_wind_entity:"sensor.wind", sun_cond_rwind_entity:"binary_sensor.windalarm",
      sun_cond_dusk_entity:"sensor.lux" },
    { cover_entity_id:"cover.markise_b", name:"Markise B", device_kind:"awning", area_down_id:"living",
      position_open:0, position_sun_protect:100 },
    { cover_entity_id:"cover.fenster_a", name:"Dachfenster A", device_kind:"window", area_down_id:"none",
      position_closed:0, position_open:100, position_sun_protect:30, sun_geometry_override:true },
    { cover_entity_id:"cover.fenster_b", name:"Dachfenster B", device_kind:"window", area_down_id:"none",
      position_closed:0, position_open:100, position_sun_protect:30 },
  ];
  const settings = { weather_entity:"weather.home", sun_cond_wind_entity:"sensor.wind",
    sun_cond_wind_on_above:40, sun_cond_wind_off_below:25, guard_wind_lockout:20,
    sun_cond_rain_entity:"binary_sensor.rain", guard_rain_lockout:10,
    sun_cond_cold_entity:"sensor.aussen", sun_cond_cold_on_above:2, sun_cond_cold_off_below:4, frost_lock_catch_up:true,
    sun_cond_ice_entity:"sensor.temp", sun_cond_ice_on_above:-2, sun_cond_ice_off_below:2,
    min_drive_gap:1, verify_enabled:true };

  p._data = { areas, shutters, settings, auto_modes:{living:true,sleep:true,none:true,time:true},
    sun_protect_modes:{living:true,none:true}, master_enabled:true, sun_protect_status:{},
    sun:{elevation:38, azimuth:180, next_rising:null, next_setting:null},
    weather:{}, area_triggers:{} };
  p._settings = settings;
  return { p, areas, shutters, settings, states };
}

export const render = t => (t && t._s) ? flat(t._s, t._v) : String(t ?? "");
export { Panel };
