// Die Verzoegerung des Bereichs gilt auch fuer die Knoepfe (DerTomm, #18).
import { Panel } from "./harness.mjs";

const waits = [];
globalThis.setTimeout = (fn, ms) => { waits.push(ms); fn(); return 0; };

const calls = [];
const p = Object.create(Panel.prototype);
p.hass = { states:{}, user:{is_admin:true}, language:"de",
           callService:(d, s, data) => { calls.push([s, data.entity_id]); return Promise.resolve(); } };
p.t = k => k; p.requestUpdate = () => {};

const sh = (id, up, down, extra={}) =>
  ({ cover_entity_id:id, area_up_id:up, area_down_id:down, position_closed:0, ...extra });

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };
const run = async (list, action, gap=0, areas) => {
  waits.length = 0; calls.length = 0;
  p._data = { settings:{ min_drive_gap:gap }, shutters:list, areas };
  await p._coverAction(list, action, true);
  return [...waits];
};

const areas = [{ id:"a", drive_delay:10 }, { id:"b", drive_delay:3 }, { id:"c", drive_delay:0 },
               { id:"d" /* kein gespeicherter Wert: Vorgabe 10 */ }];

let w = await run([sh("cover.1","a","a"), sh("cover.2","a","a"), sh("cover.3","a","a")], "close", 0, areas);
ok("drei Rollladen, Bereich 10 s: zweimal 10 s gewartet", JSON.stringify(w) === "[10000,10000]", JSON.stringify(w));
ok("alle drei gefahren, in Reihenfolge",
   JSON.stringify(calls.map(c => c[1])) === '["cover.1","cover.2","cover.3"]');

w = await run([sh("cover.1","c","c"), sh("cover.2","c","c")], "close", 0, areas);
ok("Verzoegerung 0: ohne Warten, gleichzeitig (wie bisher)", w.length === 0, JSON.stringify(w));

w = await run([sh("cover.1","c","c"), sh("cover.2","c","c")], "close", 2, areas);
ok("Mindestabstand allein wirkt weiter (wie bisher)", JSON.stringify(w) === "[2000]", JSON.stringify(w));

w = await run([sh("cover.1","b","b"), sh("cover.2","b","b")], "close", 5, areas);
ok("das Groessere gewinnt: Abstand 5 s gegen Bereich 3 s", JSON.stringify(w) === "[5000]", JSON.stringify(w));

w = await run([sh("cover.1","d","d"), sh("cover.2","d","d")], "close", 0, areas);
ok("Bereich ohne gespeicherten Wert: Vorgabe 10 s wie im Backend", JSON.stringify(w) === "[10000]", JSON.stringify(w));

w = await run([sh("cover.1","a","a"), sh("cover.2","a","a")], "stop", 0, areas);
ok("Stop wartet nicht auf die Bereichsverzoegerung", w.length === 0, JSON.stringify(w));

// Hoch richtet sich nach dem Hoch-Bereich, Runter nach dem Runter-Bereich.
w = await run([sh("cover.1","a","c"), sh("cover.2","b","c")], "open", 0, areas);
ok("Hoch: Hoch-Bereich des zweiten (3 s)", JSON.stringify(w) === "[3000]", JSON.stringify(w));
w = await run([sh("cover.1","a","c"), sh("cover.2","b","c")], "close", 0, areas);
ok("Runter: Runter-Bereich des zweiten (0 s)", w.length === 0, JSON.stringify(w));

process.exit(fails ? 1 : 0);
