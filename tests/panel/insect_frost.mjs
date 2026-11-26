/* Insektenschutz (Claus #267) und Frostschutz beim Oeffnen (MartyBr #268)
   im Rollladenformular: Felder erscheinen hinter ihrem Haken, leere Werte
   zeigen die Backend-Vorgaben, beide sind Experten-Felder. */
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
p.hass.states["cover.terrasse"] = { state: "closed", attributes: { current_position: 0, supported_features: 255 } };
const base = { cover_entity_id: "cover.terrasse", name: "Terrasse", area_up_id: "living", area_down_id: "living",
  tilt_enabled: true, _index: null };
const form = (s, mode = "expert") => {
  p._data = { ...p._data, settings: { ...p._data.settings, ui_mode: mode } };
  p._editShutter = s;
  return render(p._renderShutterForm(p._data));
};

console.log("— Frostschutz beim Oeffnen —");
let out = form({ ...base });
ok("Experte: Haken sichtbar", out.includes("f_pos_open_frost"));
ok("Haken aus: kein Schieber", !out.includes("f_pos_open_frost_val"));
out = form({ ...base, position_open_frost: 85 });
ok("gesetzt: Schieber 85", val(out, "f_pos_open_frost_val") === 85, String(val(out, "f_pos_open_frost_val")));
out = form({ ...base }, "simple");
ok("einfach, nicht gesetzt: ausgeblendet", !out.includes("f_pos_open_frost_hint"));
out = form({ ...base, position_open_frost: 85 }, "simple");
ok("einfach, gesetzt: bleibt sichtbar", out.includes("f_pos_open_frost_hint"));

console.log("— Insektenschutz —");
out = form({ ...base });
ok("Experte: Haken sichtbar", out.includes("> f_insect</label>"));
ok("Haken aus: keine Felder", !out.includes("f_insect_from"));
out = form({ ...base, insect_guard: true, insect_guard_from: "11:00", insect_guard_to: "16:00" });
ok("Zeitfenster sichtbar", out.includes("f_insect_from") && out.includes("f_insect_to"));
ok("Bedingung sichtbar", out.includes("f_insect_entity"));
ok("ohne Sensor: keine Mindesttemperatur", !out.includes("f_insect_temp_min"));
out = form({ ...base, insect_guard: true, insect_guard_temp_entity: "sensor.temp" });
ok("mit Sensor: Mindesttemperatur", out.includes("f_insect_temp_min"));
ok("Mindesttemperatur leer: zeigt 15 wie das Backend", /f_insect_temp_min<\/label><input type="number" step="0.5" \.value=15\b/.test(out));
out = form({ ...base }, "simple");
ok("einfach, nicht gesetzt: ausgeblendet", !out.includes("f_insect_hint"));
out = form({ ...base, insect_guard: true }, "simple");
ok("einfach, gesetzt: bleibt sichtbar", out.includes("f_insect_hint"));

if (fails) { console.log(fails + " FAIL"); process.exit(1); }
console.log("alle ok");
