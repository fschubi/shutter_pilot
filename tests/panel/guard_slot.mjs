// Sensor-Formular der Markise: Rahmen mit Titel, Warnung ohne Schwelle und
// bei verkehrt herum eingetragenen Werten (Frankchief, simon42 #212).
import { Panel, flat } from "./harness.mjs";

const p = Object.create(Panel.prototype);
p.hass = { states:{
  "sensor.wind":{ state:"12.5", attributes:{} },
  "sensor.temp":{ state:"8.0", attributes:{} },
  "binary_sensor.regen":{ state:"off", attributes:{} },
}, user:{is_admin:true}, language:"de" };
p.t = k => k; p.requestUpdate = () => {};

const render = (obj, slot, perAwning=false) => {
  const ep = (k,lbl) => `<ENT ${k}>`;
  const rng = (k,lbl) => `<RNG ${k}>`;
  const out = p._renderGuardSlot(obj, slot, ep, rng, perAwning);
  return flat(out._s, out._v);
};

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };

let h = render({ sun_cond_wind_entity:"sensor.wind" }, "wind");
ok("jeder Schutz hat einen Titel", h.includes("guard-slot-title") && h.includes("guard_reason_wind"));
ok("Zahlensensor ohne Schwelle: Warnung", h.includes("f_guard_no_threshold"));

h = render({ sun_cond_wind_entity:"sensor.wind", sun_cond_wind_on_above:40, sun_cond_wind_off_below:29 }, "wind");
ok("mit Schwellen: keine Warnung", !h.includes("f_guard_no_threshold") && !h.includes("f_guard_wrong_way"));

h = render({ sun_cond_wind_entity:"sensor.wind" }, "wind", true);
ok("je Markise erbt ein leeres Feld den globalen Wert: keine Warnung",
   !h.includes("f_guard_no_threshold"));

// Frankchiefs Frostsensor: 15/20 bei ausdruecklich NICHT umgekehrt.
h = render({ sun_cond_ice_entity:"sensor.temp", sun_cond_ice_on_above:15,
             sun_cond_ice_off_below:20, sun_cond_ice_invert:false }, "ice");
ok("Frost 15/20 ohne Umkehrung: Warnung 'passt nicht zusammen'", h.includes("f_guard_wrong_way"));
h = render({ sun_cond_ice_entity:"sensor.temp", sun_cond_ice_on_above:15,
             sun_cond_ice_off_below:20 }, "ice");
ok("dieselben Werte, Frost wie voreingestellt (umgekehrt): in Ordnung",
   !h.includes("f_guard_wrong_way"));
h = render({ sun_cond_wind_entity:"sensor.wind", sun_cond_wind_on_above:40,
             sun_cond_wind_off_below:50 }, "wind");
ok("Wind 40/50: Aufhebepunkt ueber dem Einschaltpunkt, Warnung", h.includes("f_guard_wrong_way"));

h = render({ sun_cond_rain_entity:"binary_sensor.regen" }, "rain");
ok("Binaersensor: nichts auszuwaehlen, keine Schwellenwarnung",
   h.includes("f_guard_bin_hint") && !h.includes("f_guard_no_threshold"));

h = render({ sun_cond_rwind_entity:"sensor.wind" }, "rwind");
ok("Raffstore-Wind hat seinen eigenen Titel", h.includes("f_guard_rwind"));

// Frostsperre (eurofinder, simon42 #244): immer "kaelter als", kein Umkehr-Haken
// bei Zahlen, eigene Texte statt Markisen-Wortlaut.
h = render({ sun_cond_cold_entity:"sensor.temp", sun_cond_cold_on_above:2,
             sun_cond_cold_off_below:4, sun_cond_cold_invert:false }, "cold");
ok("Frostsperre, Zahlensensor: kein Umkehr-Haken", !h.includes("f_cond_invert_label"));
ok("Frostsperre: immer 'Sperren unter' / 'Wieder freigeben ueber'",
   h.includes("f_guard_on_below") && h.includes("f_guard_off_above") && !h.includes("f_guard_on_above"));
ok("Frostsperre 2/4: keine Warnung trotz altem abgewaehlten Haken", !h.includes("f_guard_wrong_way"));
h = render({ sun_cond_cold_entity:"sensor.temp", sun_cond_cold_on_above:4,
             sun_cond_cold_off_below:2 }, "cold");
ok("Frostsperre 4/2: eigene Warnung", h.includes("f_guard_wrong_way_cold"));
h = render({ sun_cond_cold_entity:"sensor.temp" }, "cold");
ok("Frostsperre ohne Schwelle: eigener Text", h.includes("f_guard_no_threshold_cold"));
h = render({ sun_cond_cold_entity:"sensor.temp", sun_cond_cold_on_above:15,
             sun_cond_cold_off_below:17 }, "cold");
ok("Frostsperre 15: Warnung 'ungewoehnlich hoch'", h.includes("f_cold_high_warn"));
h = render({ sun_cond_cold_entity:"binary_sensor.regen" }, "cold");
ok("Frostsperre, Binaersensor: eigener Hinweis, Umkehr bleibt moeglich",
   h.includes("f_guard_bin_hint_cold") && h.includes("f_cond_invert_label"));
h = render({ sun_cond_wind_entity:"sensor.wind", sun_cond_wind_on_above:40,
             sun_cond_wind_off_below:29 }, "wind");
ok("Wind unveraendert: Umkehr-Haken da", h.includes("f_cond_invert_label"));

process.exit(fails ? 1 : 0);
