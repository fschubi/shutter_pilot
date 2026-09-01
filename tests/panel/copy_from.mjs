import { Panel } from "./harness.mjs";
const p = Object.create(Panel.prototype);
p.hass = { states:{}, user:{is_admin:true}, language:"de" };
p.t = k => k; p.requestUpdate = () => {};

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };

// TanjaHHs Fall: Vorlage mit eigenen Bereichen, neuer Rollladen daneben.
const src = { cover_entity_id:"cover.sitzecke", name:"Rollladen Sitzecke",
  area_up_id:"manuel_hoch", area_down_id:"living",
  position_open:100, position_closed:0, position_sun_protect:50,
  lock_protection:true, min_position_when_open:100, drive_after_close:true,
  window_entity_id:"binary_sensor.sitzecke", shutter_auto_entity_id:"switch.sp_sitzecke",
  window_close_debounce:5 };
const target = { cover_entity_id:"cover.essen", name:"Rollladen Essen",
  area_up_id:"living", area_down_id:"living", shutter_auto_entity_id:"switch.sp_essen",
  _isNew:true, _index:null };

p._editShutter = target;
p._copyFrom = "cover.sitzecke";
p._applyCopyFrom([src]);

ok("Bereich hoch wird übernommen", target.area_up_id === "manuel_hoch", target.area_up_id);
ok("Bereich runter wird übernommen", target.area_down_id === "living", target.area_down_id);
ok("Entität bleibt die eigene", target.cover_entity_id === "cover.essen");
ok("Name bleibt der eigene", target.name === "Rollladen Essen");
ok("Schalter-Entität bleibt die eigene", target.shutter_auto_entity_id === "switch.sp_essen");
ok("Fensterkontakt der Vorlage kommt NICHT mit", target.window_entity_id === undefined,
   String(target.window_entity_id));
ok("Positionen kommen mit", target.position_sun_protect === 50 && target.min_position_when_open === 100);
ok("Aussperrschutz kommt mit", target.lock_protection === true);

// Die Geraeteart darf eine Vorlage nie mitbringen.
const win = { cover_entity_id:"cover.fenster_neu", name:"Neu", device_kind:"window",
  position_closed:0, position_open:100, position_sun_protect:30, _isNew:true, _index:null };
const winSrc = { cover_entity_id:"cover.fenster_alt", name:"Alt", device_kind:"window",
  area_down_id:"bad", position_sun_protect:40 };
p._editShutter = win; p._copyFrom = "cover.fenster_alt";
p._applyCopyFrom([winSrc]);
ok("Geräteart bleibt unangetastet", win.device_kind === "window");
ok("Dachfenster übernimmt seinen Bereich", win.area_down_id === "bad", String(win.area_down_id));
process.exit(fails ? 1 : 0);
