// Lamellen-Knoepfe in der Dashboard-Zeile (Claus #225).
import { Panel } from "./harness.mjs";

const calls = [];
const p = Object.create(Panel.prototype);
p.hass = { states:{ "cover.a":{ attributes:{ current_tilt_position:50 } },
                    "cover.b":{ attributes:{ current_tilt_position:95 } },
                    "cover.c":{ attributes:{} } },
           user:{ is_admin:true }, language:"de",
           callService:(d, s, data) => { calls.push([d, s, data.entity_id, data.tilt_position]); return Promise.resolve(); } };
p.t = k => k; p.requestUpdate = () => {};

let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };

await p._tiltStep({ cover_entity_id:"cover.a" }, 10);
ok("+10 von 50 -> 60 ueber den cover-Dienst", JSON.stringify(calls.at(-1)) === '["cover","set_cover_tilt_position","cover.a",60]', JSON.stringify(calls.at(-1)));
await p._tiltStep({ cover_entity_id:"cover.a" }, -10);
ok("-10 von 50 -> 40", calls.at(-1)[3] === 40);
await p._tiltStep({ cover_entity_id:"cover.b" }, 10);
ok("oben bei 100 begrenzt", calls.at(-1)[3] === 100, String(calls.at(-1)[3]));
await p._tiltStep({ cover_entity_id:"cover.c" }, 10);
ok("ohne gemeldeten Winkel: ab 50", calls.at(-1)[3] === 60, String(calls.at(-1)[3]));
const n = calls.length;
await p._tiltStep({}, 10);
ok("ohne Entitaet nichts", calls.length === n);

const flat = x => JSON.stringify(x);
const withTilt = flat(p._rowButtons({ cover_entity_id:"cover.a", tilt_enabled:true }));
const without = flat(p._rowButtons({ cover_entity_id:"cover.a" }));
ok("Knoepfe nur bei Lamellen", withTilt.includes("btn_tilt_more") && !without.includes("btn_tilt_more"));

ok("Winkel neben der Hoehe", p._tiltReading({ tilt_enabled:true }, p.hass.states["cover.a"]) === " · L 50%");
ok("kein Winkel ohne Lamellen oder Meldung", p._tiltReading({}, p.hass.states["cover.a"]) === "" && p._tiltReading({ tilt_enabled:true }, p.hass.states["cover.c"]) === "");

process.exit(fails ? 1 : 0);
