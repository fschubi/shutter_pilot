// Reihenfolge im Dashboard verschieben (DerTomm, GitHub #17).
import { Panel } from "./harness.mjs";

const p = Object.create(Panel.prototype);
p.hass = { states:{}, user:{is_admin:true}, language:"de", callWS: async () => ({}) };
p.t = k => k; p.requestUpdate = () => {};

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const names = d => d.shutters.map(s => s.cover_entity_id.replace("cover.","")).join(",");

// a und c stehen in "wohn"; b und d in "bad". Die Liste mischt beide.
const mk = () => ({ shutters:[
  { cover_entity_id:"cover.a", area_up_id:"wohn", area_down_id:"wohn" },
  { cover_entity_id:"cover.b", area_up_id:"bad",  area_down_id:"bad"  },
  { cover_entity_id:"cover.c", area_up_id:"wohn", area_down_id:"wohn" },
  { cover_entity_id:"cover.d", area_up_id:"bad",  area_down_id:"bad"  },
]});

globalThis.setTimeout = (fn) => { p._timerFn = fn; return 7; };
globalThis.clearTimeout = () => {};

p._data = mk(); p._pendingOrder = null;
p._moveShutter("wohn", "cover.c", -1);
ok("c rutscht im Bereich vor a", names(p._data) === "c,b,a,d", names(p._data));
ok("andere Bereiche bleiben, wo sie waren (b vor d)",
   names(p._data).indexOf("b") < names(p._data).indexOf("d"));
ok("die Reihenfolge der ganzen Liste wird zum Speichern vorgemerkt",
   JSON.stringify(p._pendingOrder) === '["cover.c","cover.b","cover.a","cover.d"]',
   JSON.stringify(p._pendingOrder));

p._data = mk(); p._pendingOrder = null;
p._moveShutter("wohn", "cover.a", -1);
ok("der erste kann nicht weiter nach oben", names(p._data) === "a,b,c,d" && !p._pendingOrder);
p._moveShutter("wohn", "cover.c", 1);
ok("der letzte kann nicht weiter nach unten", names(p._data) === "a,b,c,d" && !p._pendingOrder);

// Geklickt wird mehrfach, gespeichert einmal (ein Speichern laedt neu).
let saves = 0;
p.hass.callWS = async (msg) => { if (msg.type === "shutter_pilot/reorder_shutters") saves++; return {}; };
p._load = async () => {};
p._data = mk(); p._pendingOrder = null;
p._moveShutter("wohn", "cover.c", -1);
p._moveShutter("bad", "cover.d", -1);
ok("zwei Klicks, noch kein Speichern", saves === 0);
await p._timerFn();
ok("danach genau ein Speichern", saves === 1, String(saves));
ok("die vorgemerkte Reihenfolge ist danach leer", p._pendingOrder === null);

// Ein Nachladen darf eine ungespeicherte Reihenfolge nicht zurueckdrehen.
p._pendingOrder = ["cover.d", "cover.c"];
p.hass.callWS = async () => mk();
Object.defineProperty(p, "_load", { value: Panel.prototype._load, configurable: true, writable: true });
await p._load();
ok("Nachladen behaelt die ungespeicherte Reihenfolge: d,c vorn",
   names(p._data) === "d,c,a,b", names(p._data));

const re = p._applyOrder(mk().shutters, ["cover.zzz", "cover.b"]);
ok("unbekannte Namen werden uebergangen, nichts geht verloren",
   re.map(s => s.cover_entity_id).join() === "cover.b,cover.a,cover.c,cover.d");

process.exit(fails ? 1 : 0);
