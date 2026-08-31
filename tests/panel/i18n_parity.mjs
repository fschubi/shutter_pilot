// Kein Regex-Parsen: das File auswerten und I18N herausreichen.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
// Ohne PANEL-Variable das File aus dem Repo nehmen.
const DEFAULT_PANEL = path.resolve(path.dirname(fileURLToPath(import.meta.url)),
  "../../custom_components/shutter_pilot/frontend/shutter-pilot-panel.js");
class Stub { static get properties(){return {};} requestUpdate(){} addEventListener(){} }
const html=(s,...v)=>({_s:s,_v:v}); const css=(s,...v)=>({});
Stub.prototype.html=html; Stub.prototype.css=css;
class Host extends Stub {}
globalThis.customElements={ get:n=>n==="shutter-pilot-panel"?undefined:Host, define(){} };
globalThis.window=globalThis;
globalThis.document={createElement:()=>({style:{},setAttribute(){},appendChild(){}}),querySelector:()=>null,addEventListener(){}};
Object.defineProperty(globalThis,"navigator",{value:{userAgent:"node",platform:"MacIntel",maxTouchPoints:0},configurable:true});
globalThis.HTMLElement=Stub;

const code = fs.readFileSync(process.env.PANEL || DEFAULT_PANEL, "utf8");
const I18N = new Function(code + "\n;return I18N;")();

const codes = Object.keys(I18N);
const de = new Set(Object.keys(I18N.de));
console.log("Sprachen:", codes.join(" "), `(${codes.length})`);
console.log("Schluessel in de:", de.size);
let bad = 0;
for (const c of codes) {
  const keys = new Set(Object.keys(I18N[c]));
  const missing = [...de].filter(k => !keys.has(k));
  const extra   = [...keys].filter(k => !de.has(k));
  const empty   = [...keys].filter(k => typeof I18N[c][k] === "string" && !I18N[c][k].trim());
  console.log(`  ${c}: ${keys.size}`
    + (missing.length ? "  FEHLEN: " + missing.slice(0,8).join(",") : "")
    + (extra.length   ? "  ZUSAETZLICH: " + extra.slice(0,8).join(",") : "")
    + (empty.length   ? "  LEER: " + empty.slice(0,5).join(",") : ""));
  if (missing.length || extra.length || empty.length) bad++;
}
console.log(bad ? `=> ${bad} Sprache(n) weichen ab` : "=> alle elf vollstaendig");
process.exit(bad ? 1 : 0);
