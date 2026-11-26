/* Leere Schieber zeigen, was das Backend faehrt - und die Lux-Warnung kommt nur,
   wenn sich die Zeitfenster ueberschneiden (Claus, simon42 #267).

   Sichtschutz-Position nie bewegt: das Panel zeigte 0 %, das Backend fuhr 30 %
   (DEFAULT_POSITION_PRIVACY). Der KNX-Monitor sah 30, der Nutzer haette 0
   erwartet. Die Werte hier muessen zu helpers.py passen; der Python-Test
   test_panel_slider_fallbacks_match_the_backend prueft das gegen die Konstanten. */
import { makePanel, render } from "./fixture.mjs";

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const val = (out, label) => {
  const i = out.indexOf(label);
  if (i < 0) return null;
  const m = /slider-val">(-?\d+(?:\.\d+)?)%/.exec(out.slice(i));
  return m ? Number(m[1]) : null;
};

const { p } = makePanel();
p._data = { ...p._data, settings: { ...p._data.settings, ui_mode: "expert" } };
p.hass.states["cover.bad"] = { state: "closed", attributes: { current_position: 0, supported_features: 255 } };

/* Claus' Bad: Sichtschutz-Entität gesetzt, Position nie bewegt, Lamellen 38. */
p._editShutter = { cover_entity_id: "cover.bad", name: "Bad", area_up_id: "living", area_down_id: "living",
  tilt_enabled: true, privacy_entity: "binary_sensor.bad_sichtschutz", tilt_privacy: 38,
  open_stage2: true, blind_drive: true, my_position_entity: "button.my_pos", _index: null };
let out = render(p._renderShutterForm(p._data));
ok("Sichtschutz-Position leer: zeigt 30 wie das Backend", val(out, "f_privacy_pos") === 30, String(val(out, "f_privacy_pos")));
ok("gesetzte Lamellen bleiben 38", val(out, "f_privacy_tilt") === 38, String(val(out, "f_privacy_tilt")));
ok("zweite Öffnungsstufe leer: 100", val(out, "f_open2_pos") === 100, String(val(out, "f_open2_pos")));
ok("Lamellen zweite Stufe leer: 100", val(out, "f_open2_tilt") === 100, String(val(out, "f_open2_tilt")));
ok("My-Position leer: 50", val(out, "f_my_position_pct") === 50, String(val(out, "f_my_position_pct")));

p._editShutter = { ...p._editShutter, position_privacy: 0 };
out = render(p._renderShutterForm(p._data));
ok("eine gespeicherte 0 bleibt 0", val(out, "f_privacy_pos") === 0, String(val(out, "f_privacy_pos")));

p._editShutter = { cover_entity_id: "cover.markise_x", device_kind: "awning", area_down_id: "living", _index: null };
out = render(p._renderShutterForm(p._data));
ok("Markise leer: Sonnenschutz 100", val(out, "f_awning_pos_sun") === 100 || out.includes('slider-val">100%'),
   "Markisen-Rueckfall fehlt");
p._editShutter = null;

console.log("— Lux-Warnung —");
const area = (o) => ({ ...p._newArea(), mode: "brightness", brightness_sensor: "sensor.lux", ...o });
const warn = a => { p._editArea = a; return render(p._renderAreaForm()).includes("f_lux_wrong_way"); };
ok("Claus: hoch ab 50, runter bei 100, Fenster getrennt: keine Warnung",
   !warn(area({ lux_up: 50, lux_down: 100, w_up_from: "05:00", w_up_to: "12:00", w_down_from: "15:00", w_down_to: "23:59",
                we_up_from: "05:00", we_up_to: "12:00", we_down_from: "15:00", we_down_to: "23:59" })));
ok("dieselben Schwellen, Fenster ueberschneiden sich: Warnung",
   warn(area({ lux_up: 50, lux_down: 100, w_up_from: "05:00", w_up_to: "16:00", w_down_from: "15:00", w_down_to: "23:59" })));
ok("nur das Wochenende ueberschneidet sich: Warnung",
   warn(area({ lux_up: 50, lux_down: 100, w_up_from: "05:00", w_up_to: "09:00", w_down_from: "16:00", w_down_to: "23:59",
               we_up_from: "07:00", we_up_to: "17:00", we_down_from: "16:00", we_down_to: "23:59" })));
ok("Fenster ueber Mitternacht: vorsichtshalber Warnung",
   warn(area({ lux_up: 50, lux_down: 100, w_up_from: "05:00", w_up_to: "09:00", w_down_from: "22:00", w_down_to: "02:00" })));
ok("fehlendes Fenster gilt wie im Backend den ganzen Tag: Warnung",
   warn({ ...area({ lux_up: 50, lux_down: 100 }), w_up_from: "", w_up_to: "" }));
ok("hoch ueber runter: nie eine Warnung",
   !warn(area({ lux_up: 500, lux_down: 400, w_up_from: "05:00", w_up_to: "16:00", w_down_from: "15:00", w_down_to: "23:59" })));
p._editArea = null;

process.exit(fails ? 1 : 0);
