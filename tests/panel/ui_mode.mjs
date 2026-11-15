/* Einfache Ansicht / Experten-Ansicht und der gefuehrte Einstieg.

   Die drei Zusagen des Modus, jede mit einem eigenen Block:
   1. Jeder Abschnitt ist eingestuft – ein neuer ohne Einstufung faellt hier.
   2. Ein leeres Formular zeigt in der einfachen Ansicht nur das Noetige.
   3. Was benutzt ist, bleibt sichtbar, und kein Wert wird angefasst. */
import { makePanel, render, Panel } from "./fixture.mjs";

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const mode = (p, m) => { p._data = { ...p._data, settings: { ...p._data.settings, ui_mode: m } }; };
const has = (out, keys) => keys.filter(k => out.includes(k));

const BASIC = Panel.BASIC_SECS, EXPERT = Panel.EXPERT_SECS, FREE = Panel.UNFILTERED_SECS;

console.log("— Einstufung —");
{
  const { p, areas, shutters } = makePanel();
  const seen = new Set();
  const orig = Panel.prototype._sec;
  p._sec = function (icon, key, ...rest) { seen.add(key); return orig.call(this, icon, key, ...rest); };
  p._renderSettings(p._data);
  for (const a of areas) { p._editArea = a; p._renderAreaForm(a); }
  for (const s of shutters) { p._editShutter = { ...s, _index: shutters.indexOf(s) }; p._renderShutterForm(p._data); }
  const all = [...BASIC, ...EXPERT, ...FREE];
  const unknown = [...seen].filter(k => !all.includes(k));
  ok("jeder gerenderte Abschnitt steht in einer Liste", unknown.length === 0, "ohne Einstufung: " + unknown.join(", "));
  const twice = all.filter((k, i) => all.indexOf(k) !== i);
  ok("kein Abschnitt steht in zwei Listen", twice.length === 0, twice.join(", "));
  const stale = all.filter(k => !seen.has(k));
  ok("keine Liste nennt einen Abschnitt, den es nicht gibt", stale.length === 0, stale.join(", "));
}

console.log("— Neues, leeres Formular in der einfachen Ansicht —");
{
  const { p } = makePanel();
  mode(p, "simple");
  for (const m of ["time", "brightness", "sun"]) {
    p._editArea = { ...p._newArea(), mode: m };
    const out = render(p._renderAreaForm());
    ok(`Bereich (${m}): Grunddaten und Zeitplan da`, out.includes("sec_basics") && out.includes("sec_schedule"));
    ok(`Bereich (${m}): kein Experten-Abschnitt`, has(out, EXPERT).length === 0, has(out, EXPERT).join(", "));
    ok(`Bereich (${m}): Experten-Felder weg`,
       has(out, ["f_drive_delay", "f_temp_sensor", "f_bounds_title", "f_lux_hold", "f_sunbound_title", "f_blatest_title", "mode_none"]).length === 0,
       has(out, ["f_drive_delay", "f_temp_sensor", "f_bounds_title", "f_lux_hold", "f_sunbound_title", "f_blatest_title", "mode_none"]).join(", "));
    ok(`Bereich (${m}): Hinweis auf die Experten-Ansicht`, out.includes("mode_hidden") && out.includes("mode_show_all"));
  }
  p._editArea = { ...p._newArea(), mode: "time" };
  ok("Zeit: die vier Uhrzeiten bleiben", has(render(p._renderAreaForm()), ["f_time_up", "f_time_down", "f_time_we_up", "f_time_we_down"]).length === 4);
  p._editArea = { ...p._newArea(), mode: "brightness" };
  ok("Helligkeit: Sensor, Schwellen und Fenster bleiben",
     has(render(p._renderAreaForm()), ["f_brightness_sensor", "f_lux_up", "f_lux_down", "f_w_up_from", "f_we_down_to"]).length === 5);
  p._editArea = { ...p._newArea(), mode: "sun" };
  ok("Sonnenstand: die Versaetze bleiben", has(render(p._renderAreaForm()), ["f_sunrise_off", "f_sunset_off"]).length === 2);
  p._editArea = null;

  p.hass.states["cover.rolllo_neu"] = { state: "open", attributes: { current_position: 100, supported_features: 15 } };
  p._editShutter = { ...p._newShutter(p._data), cover_entity_id: "cover.rolllo_neu" };
  const out = render(p._renderShutterForm(p._data));
  ok("Rollladen: die vier Basis-Abschnitte da",
     has(out, ["sec_shutter", "sec_areas", "sec_positions", "sec_window"]).length === 4);
  ok("Rollladen: kein Experten-Abschnitt", has(out, EXPERT).length === 0, has(out, EXPERT).join(", "));
  const gone = ["f_pos_sun_alt", "f_pos_lvl", "f_privacy_entity", "f_open2", "f_refrun", "f_pos_sun_entity",
    "f_pos_closed_alt", "f_pos_closed_frost", "f_window_react", "f_drive_after_up", "f_win_debounce",
    "f_win_close_delay", "f_win_keep_open", "f_blind_drive", "f_lock_entity"];
  ok("Rollladen: Experten-Felder weg", has(out, gone).length === 0, has(out, gone).join(", "));
  const kept = ["f_cover", "f_area_up", "f_pos_open", "f_pos_closed", "f_pos_sun", "f_window_sensor", "f_lock", "f_drive_after"];
  ok("Rollladen: das Noetige bleibt", has(out, kept).length === kept.length,
     "fehlt: " + kept.filter(k => !out.includes(k)).join(", "));

  /* Ein Raffstore, der Lamellen meldet (Bit 128): der Abschnitt gehoert zur
     Hardware, nicht zu den Extras. */
  p.hass.states["cover.raffstore"] = { state: "open", attributes: { current_position: 100, supported_features: 255 } };
  p._editShutter = { ...p._newShutter(p._data), cover_entity_id: "cover.raffstore" };
  ok("Raffstore: Lamellen auch in der einfachen Ansicht", render(p._renderShutterForm(p._data)).includes("sec_slats"));
  p._editShutter = null;

  p._data = { ...p._data, shutters: p._data.shutters.filter(s => !s.device_kind) };
  p._settings = {};
  const set = render(p._renderSettings(p._data));
  ok("Einstellungen: nur Schalter und Export", set.includes("mode_label") && set.includes("sec_export")
     && has(set, EXPERT).length === 0, has(set, EXPERT).join(", "));
}

console.log("— Benutztes bleibt sichtbar, nichts wird angefasst —");
{
  const { p, areas, shutters, settings } = makePanel();
  mode(p, "simple");
  const living = areas.find(a => a.id === "living");
  const before = JSON.stringify(living);
  p._editArea = living;
  const out = render(p._renderAreaForm());
  const want = ["sec_calendar", "sec_sunprotect", "sec_altclose", "sec_frost", "sec_vent", "sec_noup"];
  ok("Bereich mit allem: benutzte Abschnitte stehen da", has(out, want).length === want.length,
     "fehlt: " + want.filter(k => !out.includes(k)).join(", "));
  ok("… und sind als Experte markiert", out.includes("mode_badge"));
  ok("… der unbenutzte (Licht) fehlt", !out.includes("sec_light"));
  ok("das Rendern aendert den Bereich nicht", JSON.stringify(living) === before);
  p._editArea = null;

  const full = shutters[0];
  const snap = JSON.stringify(full);
  p._editShutter = { ...full, _index: 0, privacy_entity: "switch.sicht", open_stage2: true, reference_run: true,
    position_closed_alt: 40, window_keep_open_minutes: 20, window_close_debounce: 12 };
  const sh = render(p._renderShutterForm(p._data));
  const shWant = ["sec_shutter_sun", "sec_slats", "sec_storm", "sec_frostlock", "f_privacy_entity", "f_open2_time",
    "f_refrun_days", "f_pos_closed_alt_val", "f_window_react", "f_drive_after_up", "f_win_debounce",
    "f_win_keep_open", "f_blind_drive", "f_lock_entity"];
  ok("Rollladen mit allem: Benutztes steht da", has(sh, shWant).length === shWant.length,
     "fehlt: " + shWant.filter(k => !sh.includes(k)).join(", "));
  ok("… Unbenutztes (Rückfahrt verzögern) fehlt", !sh.includes("f_win_close_delay"));
  ok("das Rendern aendert den Rollladen nicht", JSON.stringify(full) === snap);
  p._editShutter = null;

  const setOut = render(p._renderSettings(p._data));
  const setWant = ["sec_weather", "sec_guard", "sec_cold", "sec_drive", "sec_verify", "sec_export"];
  ok("Einstellungen mit allem: Benutztes steht da", has(setOut, setWant).length === setWant.length,
     "fehlt: " + setWant.filter(k => !setOut.includes(k)).join(", "));
  ok("das Rendern aendert die Einstellungen nicht", !("ui_mode" in settings));

  /* Dieselben Formulare in der Experten-Ansicht: alles, ohne Markierung. */
  mode(p, "expert");
  p._editArea = living;
  const xp = render(p._renderAreaForm());
  ok("Experte: alle Abschnitte, kein Hinweis, keine Markierung",
     xp.includes("sec_light") && !xp.includes("mode_hidden") && !xp.includes("mode_badge"));
  p._editArea = null;
}

console.log("— Reiter und Schalter —");
{
  const { p } = makePanel();
  p._integrationVersion = () => "0";
  p._tab = "dashboard";
  mode(p, "simple");
  let out = render(p._renderPanel());
  ok("einfach, Markisen vorhanden: Reiter bleiben", out.includes("tab_awnings") && out.includes("tab_windows"));
  p._data = { ...p._data, shutters: p._data.shutters.filter(s => !s.device_kind) };
  out = render(p._renderPanel());
  ok("einfach, ohne Markisen/Dachfenster: Reiter weg", !out.includes("tab_awnings") && !out.includes("tab_windows"));
  ok("… Bereiche, Rollläden, Einstellungen bleiben",
     has(out, ["tab_areas", "tab_shutters", "tab_settings"]).length === 3);
  ok("Dashboard zeigt den Schalter", out.includes("mode_simple") && out.includes("mode_expert"));
  mode(p, "expert");
  out = render(p._renderPanel());
  ok("Experte: alle Reiter", out.includes("tab_awnings") && out.includes("tab_windows"));

  p._isAdmin = () => false;
  ok("ohne Adminrechte: kein Schalter", !render(p._renderDashboard(p._data)).includes("mode_label"));
  p._isAdmin = () => true;

  const calls = [];
  p.hass.callWS = async m => { calls.push(m); return {}; };
  await p._setUiMode("simple");
  ok("Umschalten ruft set_ui_mode", calls.length === 1 && calls[0].type === "shutter_pilot/set_ui_mode" && calls[0].mode === "simple");
  ok("… und gilt sofort", p._expert() === false);
  await p._setUiMode("simple");
  ok("derselbe Modus noch einmal: kein Aufruf", calls.length === 1);
  p.hass.callWS = async () => { throw new Error("nein"); };
  globalThis.alert = () => {};
  await p._setUiMode("expert");
  ok("abgelehnt: die Anzeige springt zurueck", p._expert() === false);

  calls.length = 0;
  p.hass.callWS = async m => { calls.push(m); return p._data; };
  p._settings = { ...p._data.settings, weather_entity: "weather.home" };
  await p._saveSettings();
  const saved = calls.find(c => c.type === "shutter_pilot/save_settings");
  ok("Einstellungen speichern schickt den Modus nicht mit", saved && !("ui_mode" in saved.settings) && saved.settings.weather_entity === "weather.home");
}

console.log("— Geführter Einstieg —");
{
  const { p, areas } = makePanel();
  const empty = { ...p._data, shutters: [] };
  p._data = empty;
  p.hass.states["cover.neu_1"] = { state: "open", attributes: { friendly_name: "Küche", current_position: 100 } };
  let out = render(p._renderDashboard(p._data));
  ok("ohne Rollladen: der Einstieg statt des Dashboards", out.includes("wiz_title") && out.includes("wiz_area_title"));
  ok("… bietet die vorhandenen Bereiche an", out.includes("Wohnbereich") && out.includes("wiz_area_new"));

  ok("waehrend des Neuladens: kein Einstieg", !p._wizardActive({ ...empty, loading: true }));
  p._isAdmin = () => false;
  ok("ohne Adminrechte: kein Einstieg", !p._wizardActive(empty));
  p._isAdmin = () => true;
  const { p: full } = makePanel();
  ok("mit Rollläden: kein Einstieg", !full._wizardActive(full._data));

  const w = p._wizState(p._data);
  ok("startet mit dem ersten Bereich", w.area._isNew === false && !!w.area.id);

  w.area.name = "  ";
  p._wizNext(p._data);
  ok("ohne Namen geht es nicht weiter", w.step === 1 && w.err === "wiz_need_name");

  /* Neuer Bereich im Helligkeitsmodus. */
  w.area = p._wizArea(null); w.area.name = "Wohnbereich"; w.area.mode = "brightness";
  p._wizNext(p._data);
  ok("Schritt 2", w.step === 2 && !w.err);
  out = render(p._renderWizard(p._data));
  ok("… zeigt Sensor und Schwellen", has(out, ["f_brightness_sensor", "f_lux_up", "f_lux_down"]).length === 3);
  p._wizNext(p._data);
  ok("Helligkeit ohne Sensor geht nicht weiter", w.step === 2 && w.err === "wiz_need_sensor");
  w.area.brightness_sensor = "sensor.lux";
  p._wizNext(p._data);
  ok("Schritt 3", w.step === 3);
  out = render(p._renderWizard(p._data));
  ok("… listet die Rollläden aus Home Assistant", out.includes("cover.neu_1") && out.includes("cover.rollladen_a"));

  const calls = [];
  p.hass.callWS = async m => { calls.push(m); return { ...empty, shutters: [{ cover_entity_id: "cover.neu_1" }] }; };
  p._wizNext(p._data);
  ok("ohne Rollladen wird nichts gespeichert", calls.length === 0 && w.err === "wiz_need_cover");
  w.covers = ["cover.neu_1", "cover.rollladen_b"];
  await p._wizFinish(p._data);
  const q = calls.find(c => c.type === "shutter_pilot/quick_setup");
  ok("Einrichten ruft quick_setup genau einmal", calls.filter(c => c.type === "shutter_pilot/quick_setup").length === 1);
  ok("… kein save_area / save_shutter daneben", !calls.some(c => /save_area|save_shutter/.test(c.type)));
  /* "Wohnbereich" ergibt die ID wohnbereich – die gibt es in der Vorlage nicht,
     also kein Zusatz. Der zweite Lauf unten prueft den Zusatz. */
  ok("… neuer Bereich mit eigener ID und allen Vorgaben", q.area.id === "wohnbereich" && q.area.mode === "brightness"
     && q.area.brightness_sensor === "sensor.lux" && "manual_override" in q.area && !("_isNew" in q.area));
  ok("… Rollläden haengen am Bereich", q.shutters.length === 2 && q.shutters.every(s => s.area_up_id === "wohnbereich" && s.area_down_id === "wohnbereich"));
  ok("… mit Namen aus Home Assistant und Vorgaben", q.shutters[0].name === "Küche" && q.shutters[0].position_open === 100
     && !("_isNew" in q.shutters[0]) && !("_index" in q.shutters[0]));
  ok("danach ist der Einstieg weg", p._wiz === null && !p._wizardActive(p._data));

  /* Bestehender Bereich: nur Name, Modus und die Zeiten des Modus. */
  p._data = empty; p._wiz = null;
  const w2 = p._wizState(p._data);
  w2.area = p._wizArea(areas.find(a => a.id === "living"));
  w2.area.mode = "time"; w2.area.time_up = "06:15";
  const pay = p._wizAreaPayload(p._data);
  ok("bestehender Bereich: nur das Gezeigte geht raus",
     pay.id === "living" && pay.mode === "time" && pay.time_up === "06:15"
     && !("sun_protect_enabled" in pay) && !("sun_cond_a_entity" in pay) && !("drive_delay" in pay),
     JSON.stringify(Object.keys(pay)));

  /* Namensgleicher neuer Bereich: die ID darf keinen bestehenden treffen. */
  w2.area = p._wizArea(null); w2.area.name = "Living";
  ok("neuer Bereich mit vergebener ID bekommt einen Zusatz", p._wizAreaPayload(p._data).id === "living_2");

  /* Ueberspringen und wieder aufrufen. */
  p._wizSetSkipped(true);
  ok("übersprungen: normales Dashboard", !p._wizardActive(p._data));
  out = render(p._renderDashboard(p._data));
  ok("… mit Knopf fuer die geführte Einrichtung", out.includes("wiz_start") && !out.includes("wiz_title"));
  p._wizSetSkipped(false);
  ok("wieder aufgerufen", p._wizardActive(p._data));
}

process.exit(fails ? 1 : 0);
