import { makePanel, render } from "./fixture.mjs";

const { p, areas, shutters } = makePanel();

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const R = (label, fn, minLen=200) => {
  try {
    const t = fn();
    const s = render(t);
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
  ok("  … zeigt die Frostsperre mit Nachholen",
     out.includes("sec_cold") && out.includes("f_cold_catch_up"), "Frostsperre fehlt in den Einstellungen");
  ok("  … zeigt die Invertier-Checkbox am Schutz",
     out.includes("f_cond_invert_label"), "Checkbox fehlt im Schutz-Formular");
}
{
  /* Reihenfolge-Modus eines Bereichs: Pfeile an jedem Rollladen. */
  p._orderArea = "living";
  const out = R("Dashboard mit Reihenfolge-Modus", () => p._renderDashboard(p._data));
  ok("  … zeigt die Pfeile", out.includes("btn_move_up") && out.includes("btn_move_down"),
     "Pfeile fehlen im Reihenfolge-Modus");
  p._orderArea = "";
  const plain = R("Dashboard ohne Reihenfolge-Modus", () => p._renderDashboard(p._data));
  ok("  … zeigt keine Pfeile", !plain.includes("btn_move_up"), "Pfeile ohne Modus");
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
  /* Frostsperre: nur an echten Rollläden, mit Position und Lamellen. */
  const frost = out.includes("sec_frostlock");
  ok("  … Frostsperre-Abschnitt nur am Rollladen",
     frost === !s.device_kind, "sec_frostlock " + (frost ? "an" : "fehlt") + " bei " + s.name);
  if (s.frost_lock) ok("  … Frostposition und Lamellen sichtbar",
     out.includes("f_frost_lock_position") && out.includes("f_frost_lock_tilt"), "Felder fehlen");
  if (s.device_kind === "awning") {
    ok("  … zeigt den Daemmerungs-Abschnitt (nur Markisen)",
       out.includes("sec_awning_dusk"), "Daemmerungs-Abschnitt fehlt an einer Markise");
  }
  if (s.device_kind === "window") {
    ok("  … zeigt den Daemmerungs-Abschnitt NICHT (Dachfenster)",
       !out.includes("sec_awning_dusk"), "Daemmerungs-Abschnitt taucht faelschlich an einem Dachfenster auf");
  }
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
