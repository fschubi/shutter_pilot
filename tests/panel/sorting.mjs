import { Panel } from "./harness.mjs";
const p = Object.create(Panel.prototype);
p.hass = { states:{}, user:{is_admin:true}, language:"de" };
p.t = k => k; p.requestUpdate = () => {};

const d = { shutters: [
  { cover_entity_id:"cover.z", name:"Zimmer hinten" },
  { cover_entity_id:"cover.a", name:"Ärger-Umlaut" },
  { cover_entity_id:"cover.m", name:"Markise", device_kind:"awning" },
  { cover_entity_id:"cover.b", name:"Bad" },
  { cover_entity_id:"cover.k10", name:"Küche 10" },
  { cover_entity_id:"cover.k2", name:"Küche 2" },
]};
let fails = 0;
const ok = (n,c,x="") => { console.log((c?"  ok   ":"  FAIL ")+n+(c?"":"  -> "+x)); if(!c) fails++; };

const rows = p._byKind(d, "shutter");
const names = rows.map(r => r.s.name);
ok("alphabetisch sortiert, Umlaut und Zahl korrekt",
   JSON.stringify(names) === JSON.stringify(["Ärger-Umlaut","Bad","Küche 2","Küche 10","Zimmer hinten"]),
   JSON.stringify(names));
ok("Markise ist nicht dabei", !names.includes("Markise"));

// Der Punkt, an dem so etwas schiefgeht: der Index muss auf die VOLLE Liste zeigen.
for (const r of rows) {
  ok("Index zeigt auf den richtigen Eintrag: " + r.s.name,
     d.shutters[r.i] === r.s, "Index " + r.i + " zeigt auf " + d.shutters[r.i]?.name);
}
const aw = p._byKind(d, "awning");
ok("Markisenliste getrennt", aw.length === 1 && d.shutters[aw[0].i] === aw[0].s);
process.exit(fails ? 1 : 0);
