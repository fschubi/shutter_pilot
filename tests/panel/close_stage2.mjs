/* Zweite Schliessstufe im Rollladenformular (Claus, simon42 #267).

   Haken an: Helligkeitssensor, Uhrzeit, Bedingung und die zweite Stellung
   erscheinen; Schwelle und Dauer nur mit Sensor. Ohne einen der drei Ausloeser
   faehrt die Stufe nie - dann steht eine Warnung da. Einstufung: Experte,
   in der einfachen Ansicht nur, wenn der Haken schon gesetzt ist. */
import { makePanel, render } from "./fixture.mjs";

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const val = (out, label) => {
  const i = out.indexOf(label);
  if (i < 0) return null;
  const m = /slider-val">(-?\d+(?:\.\d+)?)(?:%| min)/.exec(out.slice(i));
  return m ? Number(m[1]) : null;
};

const { p } = makePanel();
p.hass.states["cover.diele"] = { state: "closed", attributes: { current_position: 0, supported_features: 255 } };
const base = { cover_entity_id: "cover.diele", name: "Diele", area_up_id: "living", area_down_id: "living",
  tilt_enabled: true, _index: null };
const form = (s, mode = "expert") => {
  p._data = { ...p._data, settings: { ...p._data.settings, ui_mode: mode } };
  p._editShutter = s;
  return render(p._renderShutterForm(p._data));
};

let out = form({ ...base });
ok("Experte: Haken sichtbar", out.includes("f_close2"));
ok("Haken aus: keine Felder", !out.includes("f_close2_lux_entity"));

out = form({ ...base }, "simple");
ok("einfach, nicht gesetzt: ausgeblendet", !out.includes("f_close2_hint"));
out = form({ ...base, close_stage2: true, close_stage2_time: "23:00" }, "simple");
ok("einfach, gesetzt: bleibt sichtbar", out.includes("f_close2_hint"));

out = form({ ...base, close_stage2: true });
ok("ohne Ausloeser: Warnung", out.includes("f_close2_no_trigger"));
ok("ohne Sensor: keine Schwelle", !out.includes("f_close2_lux\""), "");
ok("ohne Sensor: keine Dauer", !out.includes("f_close2_minutes"));
ok("Position leer: zeigt 0 wie das Backend", val(out, "f_close2_pos") === 0, String(val(out, "f_close2_pos")));
ok("Lamellen leer: zeigt 0 wie das Backend", val(out, "f_close2_tilt") === 0, String(val(out, "f_close2_tilt")));

out = form({ ...base, close_stage2: true, close_stage2_lux_entity: "sensor.lux", close_stage2_lux: 1,
  close_stage2_minutes: 5, tilt_closed_stage2: 60 });
ok("mit Sensor: keine Warnung", !out.includes("f_close2_no_trigger"));
ok("mit Sensor: Dauer 5 min", val(out, "f_close2_minutes") === 5, String(val(out, "f_close2_minutes")));
ok("Lamellen 60", val(out, "f_close2_tilt") === 60, String(val(out, "f_close2_tilt")));

out = form({ ...base, close_stage2: true, close_stage2_entity: "input_boolean.nacht" });
ok("nur Bedingung: keine Warnung", !out.includes("f_close2_no_trigger"));

out = form({ ...base, tilt_enabled: false, close_stage2: true, close_stage2_time: "23:00" });
ok("ohne Lamellen: kein Lamellen-Schieber", !out.includes("f_close2_tilt"));

/* Ohne gespeicherte Dauer zeigt der Schieber die 5, die das Backend nimmt -
   nicht 0 (dieselbe Falle wie 2.40.2). */
out = form({ ...base, close_stage2: true, close_stage2_lux_entity: "sensor.lux" });
ok("Dauer leer: zeigt 5 wie das Backend", val(out, "f_close2_minutes") === 5, String(val(out, "f_close2_minutes")));

if (fails) { console.log(fails + " FAIL"); process.exit(1); }
console.log("alle ok");
