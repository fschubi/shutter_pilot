import { Panel, flat } from "./harness.mjs";

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
    sun_geometry_override:true, elevation_enabled:true, blind_drive:true, my_position_entity:"button.my_pos" },
  { cover_entity_id:"cover.rollladen_b", name:"Rollladen B", area_up_id:"living", area_down_id:"living",
    position_open:100, position_closed:0, position_sun_protect:50 },
  { cover_entity_id:"cover.markise_a", name:"Markise A", device_kind:"awning", area_down_id:"living",
    position_open:0, position_sun_protect:100, awning_track_enabled:true, blind_drive:true,
    my_position_entity:"button.my_pos", sun_cond_wind_entity:"sensor.wind" },
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
  sun_cond_ice_entity:"sensor.temp", sun_cond_ice_on_above:-2, sun_cond_ice_off_below:2,
  min_drive_gap:1, verify_enabled:true };

p._data = { areas, shutters, settings, auto_modes:{living:true,sleep:true,none:true,time:true},
  sun_protect_modes:{living:true,none:true}, master_enabled:true, sun_protect_status:{},
  sun:{elevation:38, azimuth:180, next_rising:null, next_setting:null},
  weather:{}, area_triggers:{} };
p._settings = settings;

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const R = (label, fn, minLen=200) => {
  try {
    const t = fn();
    const s = t && t._s ? flat(t._s, t._v) : String(t ?? "");
    ok(label, s.length >= minLen, "nur " + s.length + " Zeichen");
    return s;
  } catch (e) { ok(label, false, e.constructor.name + ": " + e.message); return ""; }
};

console.log("— Listen und Tabs —");
R("Dashboard",        () => p._renderDashboard(p._data));
R("Bereiche-Tab",     () => p._renderAreas(p._data));
R("Rollläden-Tab",    () => p._renderShutters(p._data));
R("Markisen-Tab",     () => p._renderAwnings(p._data));
R("Dachfenster-Tab",  () => p._renderWindows(p._data));
{
  const out = R("Einstellungen", () => p._renderSettings(p._data));
  /* Wind ist numerisch, Regen boolesch (binary_sensor.rain) - beide
     Zweige von _renderGuardSlot() muessen die Checkbox zeigen. */
  ok("  … zeigt die Invertier-Checkbox am Schutz",
     out.includes("f_cond_invert_label"), "Checkbox fehlt im Schutz-Formular");
}
p._isMobile = true;
R("Dashboard (mobil)",       () => p._renderDashboard(p._data));
R("Rollläden-Tab (mobil)",   () => p._renderShutters(p._data));
R("Markisen-Tab (mobil)",    () => p._renderAwnings(p._data));
R("Dachfenster-Tab (mobil)", () => p._renderWindows(p._data));
p._isMobile = false;

console.log("— Formulare, jedes mit einer Vorlage in der Liste —");
for (const s of shutters) {
  p._editShutter = { ...s, _isNew: false, _index: shutters.indexOf(s) };
  const out = R("Formular: " + s.name, () => p._renderShutterForm(p._data));
  ok("  … zeigt den Kopierknopf (zweiter Eintrag derselben Art)",
     out.includes("f_copy_from"), "Kopierblock fehlt – Test deckt ihn nicht ab");
}
p._editShutter = null;

console.log("— Formulare für einen NEUEN Eintrag (ohne Vorlage) —");
p._editShutter = p._newAwning(p._data);   R("Neue Markise",     () => p._renderShutterForm(p._data));
p._editShutter = p._newWindow(p._data);   R("Neues Dachfenster",() => p._renderShutterForm(p._data));
p._editShutter = null;

console.log("— Bereichsformulare, alle vier Modi —");
for (const a of areas) {
  p._editArea = a;
  const out = R("Bereich: " + a.name + " (" + a.mode + ")", () => p._renderAreaForm(a));
  if (a.id === "living") {
    /* Der Invertier-Haken muss an einer numerischen Bedingung (frost/a)
       ebenso auftauchen wie an einer booleschen (b) - sonst haette die
       Checkbox nur den einen Zweig erreicht, den man gerade im Kopf hatte. */
    ok("  … zeigt die Invertier-Checkbox",
       out.includes("f_cond_invert_label"), "Checkbox fehlt im Bereichsformular");
  }
}
p._editArea = null;

console.log("— Nicht-Admin —");
p._isAdmin = () => false;
p.hass.user = { is_admin: false };
R("Dashboard ohne Adminrechte", () => p._renderDashboard(p._data), 50);

process.exit(fails ? 1 : 0);
