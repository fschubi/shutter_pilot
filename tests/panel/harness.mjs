// Wegwerf-Harnisch: das Panel in Node auswerten, ohne Home Assistant.
// Zwei Ebenen (Host extends Stub), weil der Resolver die Prototypenkette
// hochlaeuft und die *hoechste* Klasse nimmt, die html/css noch kennt.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
// Ohne PANEL-Variable das File aus dem Repo nehmen.
const DEFAULT_PANEL = path.resolve(path.dirname(fileURLToPath(import.meta.url)),
  "../../custom_components/shutter_pilot/frontend/shutter-pilot-panel.js");

const flat = (s, v) => {
  let out = "";
  for (let i = 0; i < s.length; i++) {
    out += s[i];
    if (i < v.length) {
      const x = v[i];
      const one = y => (y && y._s) ? flat(y._s, y._v)
                     : typeof y === "function" ? ""
                     : String(y ?? "");
      out += Array.isArray(x) ? x.map(one).join("") : one(x);
    }
  }
  return out;
};
const html = (s, ...v) => ({ _s: s, _v: v, toString(){ return flat(s, v); } });
const css  = (s, ...v) => ({ toString(){ return flat(s, v); } });

class Stub {
  static get properties(){ return {}; }
  requestUpdate(){}
  addEventListener(){}
  attachShadow(){ return {}; }
}
// Der Resolver prueft prototype.html UND prototype.css.
Stub.prototype.html = html;
Stub.prototype.css  = css;
class Host extends Stub {}

let Panel = null;
globalThis.customElements = {
  get(name){ return name === "shutter-pilot-panel" ? undefined : Host; },
  define(name, cls){ if (name === "shutter-pilot-panel") Panel = cls; },
};
globalThis.window = globalThis;
globalThis.document = { createElement: () => ({ style:{}, setAttribute(){}, appendChild(){} }),
                        querySelector: () => null, addEventListener(){} };
Object.defineProperty(globalThis, "navigator", { value: { userAgent: "node", platform: "MacIntel", maxTouchPoints: 0 }, configurable: true });
globalThis.HTMLElement = Stub;
globalThis.console = console;

const code = fs.readFileSync(process.env.PANEL || DEFAULT_PANEL, "utf8");
new Function(code)();

if (!Panel) { console.error("Panel-Klasse nicht eingesammelt"); process.exit(1); }
export { Panel, html, css, flat };
