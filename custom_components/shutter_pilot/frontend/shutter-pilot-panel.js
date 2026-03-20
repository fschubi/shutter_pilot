/**
 * Shutter Pilot – Home Assistant Sidebar Panel v3
 * Tabs: Dashboard | Bereiche | Rollläden
 */
const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace") ?? customElements.get("hui-view")
);
const html = LitElement?.prototype?.html ?? ((s,...v)=>s.reduce((a,b,i)=>a+v[i-1]+b));
const css  = LitElement?.prototype?.css  ?? ((s)=>s);

const MODES = {time:"Zeit",brightness:"Helligkeit",sun:"Sonnenstand"};
const MODE_ICONS = {time:"mdi:clock-outline",brightness:"mdi:white-balance-sunny",sun:"mdi:weather-sunset"};
const WIN_OPEN_OPTS = ["on","open","true","offen"];
const WIN_TILT_OPTS = ["none","tilted","gekippt","kipp","2"];

class ShutterPilotPanel extends LitElement {
  static get properties(){return{hass:{type:Object},narrow:{type:Boolean},panel:{type:Object},_tab:{attribute:false},_data:{attribute:false},_editArea:{attribute:false},_editShutter:{attribute:false}};}
  static get styles(){return css`
    :host{display:block;padding:16px;font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);--sp:var(--primary-color,#03a9f4);--card-bg:var(--card-background-color,#1c1c1c);--txt:var(--primary-text-color);--txt2:var(--secondary-text-color);--divider:var(--divider-color,#333)}
    .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px}
    .topbar h1{margin:0;font-size:24px;font-weight:500;color:var(--txt)}
    .topbar .sub{font-size:14px;color:var(--txt2)}
    .tabs{display:flex;gap:0;border-bottom:2px solid var(--divider);margin-bottom:20px}
    .tab{padding:10px 20px;cursor:pointer;font-size:14px;font-weight:500;color:var(--txt2);border-bottom:3px solid transparent;transition:all .2s}
    .tab:hover{color:var(--txt)}
    .tab.active{color:var(--sp);border-bottom-color:var(--sp)}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
    .card{background:var(--card-bg);border-radius:12px;padding:20px;box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.15))}
    .card-hdr{display:flex;align-items:center;gap:12px;margin-bottom:16px}
    .card-hdr .ic{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--sp);color:#fff;--mdc-icon-size:22px}
    .card-hdr .info h2{margin:0;font-size:18px;font-weight:500;color:var(--txt)}
    .card-hdr .info span{font-size:13px;color:var(--txt2)}
    .auto-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .auto-row .lbl{font-size:14px;color:var(--txt)}
    .srow{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--divider)}
    .srow:last-child{border-bottom:none}
    .srow .nm{font-size:14px;color:var(--txt);flex:1}
    .srow .pos{font-size:13px;color:var(--txt2);min-width:50px;text-align:right}
    .actions{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
    .btn{border:none;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:500;transition:opacity .2s;display:inline-flex;align-items:center;gap:6px}
    .btn:hover{opacity:.85}
    .btn.open{background:#4caf50;color:#fff} .btn.stop{background:#757575;color:#fff}
    .btn.close{background:#f44336;color:#fff}
    .btn.sun{background:#ff9800;color:#fff} .btn.add{background:var(--sp);color:#fff}
    .btn.edit{background:#607d8b;color:#fff} .btn.del{background:#e53935;color:#fff}
    .btn.cancel{background:var(--divider);color:var(--txt)} .btn.save{background:#4caf50;color:#fff}
    .empty{text-align:center;padding:48px 16px;color:var(--txt2)}
    table{width:100%;border-collapse:collapse;font-size:14px}
    th{text-align:left;padding:10px 8px;color:var(--txt2);font-weight:500;border-bottom:2px solid var(--divider)}
    td{padding:10px 8px;border-bottom:1px solid var(--divider);color:var(--txt)}
    tr:hover td{background:rgba(255,255,255,.03)}
    .form{background:var(--card-bg);border-radius:12px;padding:24px;margin-bottom:20px;max-width:600px}
    .form h3{margin:0 0 16px;font-size:18px;color:var(--txt)}
    .field{margin-bottom:14px}
    .field label{display:block;font-size:13px;color:var(--txt2);margin-bottom:4px}
    .field input,.field select{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--divider);background:var(--primary-background-color,#111);color:var(--txt);font-size:14px;box-sizing:border-box}
    .field input[type=time]{cursor:pointer}
    .field select{appearance:auto}
    .field input:focus,.field select:focus{outline:none;border-color:var(--sp)}
    .field .hint{font-size:11px;color:var(--txt2);margin-top:2px}
    .form-actions{display:flex;gap:8px;margin-top:16px}
    .chip{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:500}
    .chip.time{background:#1565c0;color:#fff} .chip.brightness{background:#f57f17;color:#fff} .chip.sun{background:#e65100;color:#fff}
  `;}

  constructor(){super();this._tab="dashboard";this._data=null;this._editArea=null;this._editShutter=null;}
  connectedCallback(){super.connectedCallback?.();this._load();}
  updated(c){if(c.has("hass")&&this.hass&&!this._data)this._load();}

  async _load(){
    if(!this.hass)return;
    try{this._data=await this.hass.callWS({type:"shutter_pilot/get_status"});}catch(e){console.warn("SP load error",e);}
  }

  _entities(domains){
    if(!this.hass?.states)return[];
    return Object.keys(this.hass.states).filter(e=>domains.some(d=>e.startsWith(d+"."))).sort();}

  render(){
    const d=this._data;
    return html`
      <div class="topbar"><div><h1>Shutter Pilot</h1>
        ${d?html`<div class="sub">${d.areas?.length||0} Bereiche, ${d.shutters?.length||0} Rollläden</div>`:""}</div></div>
      <div class="tabs">
        ${["dashboard","areas","shutters"].map(t=>html`
          <div class="tab ${this._tab===t?"active":""}" @click=${()=>{this._tab=t;this._editArea=null;this._editShutter=null;this.requestUpdate();}}>
            ${t==="dashboard"?"Dashboard":t==="areas"?"Bereiche":"Rollläden"}</div>`)}
      </div>
      ${!d?html`<div class="empty">Laden…</div>`:
        this._tab==="dashboard"?this._renderDashboard(d):
        this._tab==="areas"?this._renderAreas(d):
        this._renderShutters(d)}`;
  }

  /* ─── Dashboard Tab ─── */
  _renderDashboard(d){
    if(!d.areas?.length)return html`<div class="empty"><ha-icon icon="mdi:window-shutter-settings"></ha-icon><p>Keine Bereiche konfiguriert. Wechsle zum Tab "Bereiche".</p></div>`;
    return html`<div class="grid">${d.areas.map(a=>this._dashCard(a,d))}</div>`;
  }
  _dashCard(area,d){
    const id=area.id||"";
    const name=area.name||id;
    const mode=area.mode||"time";
    const sh=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id);
    const autoOn=d.auto_modes?.[id]!==false;
    return html`<div class="card">
      <div class="card-hdr"><div class="ic"><ha-icon icon="${MODE_ICONS[mode]||"mdi:blinds"}"></ha-icon></div>
        <div class="info"><h2>${name}</h2><span>${MODES[mode]||mode} · ${sh.length} Rollladen</span></div></div>
      <div class="auto-row"><span class="lbl">Automatik</span>
        <ha-switch .checked=${autoOn} @change=${e=>this._toggleAuto(id,e.target.checked)}></ha-switch></div>
      <div style="margin-top:8px">${sh.length===0?html`<div style="padding:8px 0;color:var(--txt2);font-size:13px">Keine Rollläden</div>`:
        sh.map(s=>{const st=this.hass?.states?.[s.cover_entity_id];const p=st?.attributes?.current_position;
          return html`<div class="srow"><span class="nm">${st?.attributes?.friendly_name||s.name||s.cover_entity_id}</span><span class="pos">${p!=null?Math.round(p)+"%":"–"}</span></div>`;})}</div>
      <div class="actions">
        <button class="btn open" @click=${()=>this._svc("open_group",id)}><ha-icon icon="mdi:arrow-up-bold"></ha-icon>Hoch</button>
        <button class="btn stop" @click=${()=>this._stopArea(sh)}><ha-icon icon="mdi:stop"></ha-icon>Stop</button>
        <button class="btn close" @click=${()=>this._svc("close_group",id)}><ha-icon icon="mdi:arrow-down-bold"></ha-icon>Runter</button>
        <button class="btn sun" @click=${()=>this._svc("sun_protect_group",id)}><ha-icon icon="mdi:sun-wireless-outline"></ha-icon>Sonnenschutz</button>
      </div></div>`;
  }

  /* ─── Areas Tab ─── */
  _renderAreas(d){
    if(this._editArea)return this._renderAreaForm(d);
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editArea={id:"",name:"",mode:"time",drive_delay:10,sun_protect_enabled:false,elevation_threshold:4,down_light_entity:"",down_light_brightness:40,time_up:"07:00",time_down:"19:00",sunrise_offset:0,sunset_offset:0,brightness_sensor:"",lux_down:400,lux_up:500,w_up_from:"05:00",w_up_to:"09:00",w_down_from:"16:00",w_down_to:"23:59",we_up_from:"07:00",we_up_to:"10:00",we_down_from:"16:00",we_down_to:"23:59",_isNew:true};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>Bereich hinzufügen</button></div>
      ${!d.areas?.length?html`<div class="empty">Noch keine Bereiche angelegt.</div>`:html`
      <div class="card"><table>
        <tr><th>Name</th><th>ID</th><th>Modus</th><th>Rollläden</th><th></th></tr>
        ${d.areas.map(a=>{const id=a.id||"";const cnt=d.shutters.filter(s=>s.area_up_id===id||s.area_down_id===id).length;
          return html`<tr>
            <td><strong>${a.name||id}</strong></td><td style="color:var(--txt2)">${id}</td>
            <td><span class="chip ${a.mode||"time"}">${MODES[a.mode]||a.mode}</span></td>
            <td>${cnt}</td>
            <td style="text-align:right">
              <button class="btn edit" @click=${()=>{this._editArea={...a,_isNew:false};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="btn del" @click=${()=>this._deleteArea(id)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
      </table></div>`}`;
  }
  _renderAreaForm(d){
    const a=this._editArea;const m=a.mode||"time";
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${a[k]??""}  @input=${e=>{a[k]=type==="number"?Number(e.target.value):e.target.value;this.requestUpdate();}}></div>`;
    const tm=(k,lbl)=>html`<div class="field"><label>${lbl}</label><input type="time" .value=${a[k]||"07:00"} @input=${e=>{a[k]=e.target.value;this.requestUpdate();}}></div>`;
    const ep=(k,lbl,domains)=>{const lid=`dl_${k}`;const ents=this._entities(domains);return html`<div class="field"><label>${lbl}</label>
      <input list="${lid}" .value=${a[k]||""} @input=${e=>{a[k]=e.target.value;this.requestUpdate();}} placeholder="Entität auswählen…">
      <datalist id="${lid}">${ents.map(e=>html`<option value="${e}">${this.hass.states[e]?.attributes?.friendly_name||e}</option>`)}</datalist></div>`;};
    return html`<div class="form"><h3>${a._isNew?"Bereich hinzufügen":"Bereich bearbeiten"}</h3>
      ${f("name","Name")}
      ${a._isNew?"":html`<div class="field"><label>ID</label><input disabled .value=${a.id}></div>`}
      <div class="field"><label>Steuerungsmodus</label>
        <select .value=${m} @change=${e=>{a.mode=e.target.value;this.requestUpdate();}}>
          <option value="time" ?selected=${m==="time"}>Zeit</option>
          <option value="brightness" ?selected=${m==="brightness"}>Helligkeit</option>
          <option value="sun" ?selected=${m==="sun"}>Sonnenstand</option></select></div>
      ${f("drive_delay","Verzögerung zwischen Rollläden (Sek.)","number")}
      <div class="field"><label><input type="checkbox" .checked=${!!a.sun_protect_enabled} @change=${e=>{a.sun_protect_enabled=e.target.checked;this.requestUpdate();}}> Sonnenschutz aktivieren</label></div>
      ${a.sun_protect_enabled?f("elevation_threshold","Elevation-Schwellwert (°)","number"):""}
      ${ep("down_light_entity","Lampe/Schalter bei Runter (optional)",["light","switch"])}
      ${f("down_light_brightness","Lampe Helligkeit (%)","number")}
      ${m==="time"?html`${tm("time_up","Zeit Hoch")}${tm("time_down","Zeit Runter")}`:
        m==="sun"?html`${f("sunrise_offset","Offset Sonnenaufgang (Min.)","number")}${f("sunset_offset","Offset Sonnenuntergang (Min.)","number")}`:
        html`${ep("brightness_sensor","Helligkeitssensor",["sensor"])}${f("lux_up","Lux Hoch-Schwelle","number")}${f("lux_down","Lux Runter-Schwelle","number")}
          ${tm("w_up_from","Woche Hoch ab")}${tm("w_up_to","Woche Hoch bis")}${tm("w_down_from","Woche Runter ab")}${tm("w_down_to","Woche Runter bis")}
          ${tm("we_up_from","WE Hoch ab")}${tm("we_up_to","WE Hoch bis")}${tm("we_down_from","WE Runter ab")}${tm("we_down_to","WE Runter bis")}`}
      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveArea()}><ha-icon icon="mdi:content-save"></ha-icon>Speichern</button>
        <button class="btn cancel" @click=${()=>{this._editArea=null;this.requestUpdate();}}>Abbrechen</button></div></div>`;
  }

  /* ─── Shutters Tab ─── */
  _renderShutters(d){
    if(this._editShutter)return this._renderShutterForm(d);
    const areaName=id=>{const a=d.areas.find(x=>x.id===id);return a?a.name:id;};
    return html`
      <div style="margin-bottom:16px"><button class="btn add" @click=${()=>{this._editShutter={cover_entity_id:"",name:"",window_entity_id:"",window_open_state:"on",window_tilted_state:"none",position_when_window_open:100,position_when_window_tilted:50,lock_protection:false,min_position_when_open:20,area_up_id:d.areas[0]?.id||"",area_down_id:d.areas[0]?.id||"",position_open:100,position_closed:0,position_sun_protect:50,drive_after_close:false,_isNew:true,_index:null};this.requestUpdate();}}><ha-icon icon="mdi:plus"></ha-icon>Rollladen hinzufügen</button></div>
      ${!d.shutters?.length?html`<div class="empty">Noch keine Rollläden angelegt.</div>`:html`
      <div class="card"><table>
        <tr><th>Name</th><th>Cover-Entity</th><th>Bereich Hoch</th><th>Bereich Runter</th><th>Fenster</th><th></th></tr>
        ${d.shutters.map((s,i)=>{const st=this.hass?.states?.[s.cover_entity_id];
          return html`<tr>
            <td><strong>${s.name||"–"}</strong></td>
            <td style="color:var(--txt2)">${st?.attributes?.friendly_name||s.cover_entity_id}</td>
            <td>${areaName(s.area_up_id)}</td><td>${areaName(s.area_down_id)}</td>
            <td>${s.window_entity_id||"–"}</td>
            <td style="text-align:right">
              <button class="btn edit" @click=${()=>{this._editShutter={...s,_isNew:false,_index:i};this.requestUpdate();}}><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="btn del" @click=${()=>this._deleteShutter(i)}><ha-icon icon="mdi:delete"></ha-icon></button></td></tr>`;})}
      </table></div>`}`;
  }
  _renderShutterForm(d){
    const s=this._editShutter;const areas=d.areas||[];
    const f=(k,lbl,type="text")=>html`<div class="field"><label>${lbl}</label><input type="${type}" .value=${s[k]??""}  @input=${e=>{s[k]=type==="number"?Number(e.target.value):e.target.value;this.requestUpdate();}}></div>`;
    const ep=(k,lbl,domains)=>{const lid=`dl_s_${k}`;const ents=this._entities(domains);return html`<div class="field"><label>${lbl}</label>
      <input list="${lid}" .value=${s[k]||""} @input=${e=>{s[k]=e.target.value;this.requestUpdate();}} placeholder="Entität auswählen…">
      <datalist id="${lid}">${ents.map(e=>html`<option value="${e}">${this.hass.states[e]?.attributes?.friendly_name||e}</option>`)}</datalist></div>`;};
    const sel=(k,lbl,opts)=>html`<div class="field"><label>${lbl}</label><select .value=${s[k]||""} @change=${e=>{s[k]=e.target.value;this.requestUpdate();}}>
      ${opts.map(o=>typeof o==="string"?html`<option value="${o}" ?selected=${s[k]===o}>${o}</option>`:html`<option value="${o.v}" ?selected=${s[k]===o.v}>${o.l}</option>`)}</select></div>`;
    const areaSel=(k,lbl)=>sel(k,lbl,areas.map(a=>({v:a.id,l:a.name||a.id})));
    return html`<div class="form"><h3>${s._isNew?"Rollladen hinzufügen":"Rollladen bearbeiten"}</h3>
      ${ep("cover_entity_id","Rollladen / Cover",["cover"])}
      ${f("name","Name")}
      ${ep("window_entity_id","Fenster-/Türsensor (optional)",["binary_sensor","sensor"])}
      ${sel("window_open_state","Fenster-Status 'offen'",WIN_OPEN_OPTS)}
      ${sel("window_tilted_state","Fenster-Status 'gekippt'",
        [{v:"none",l:"Deaktiviert (kein Kipp-Status)"},...WIN_TILT_OPTS.filter(x=>x!=="none").map(x=>({v:x,l:x}))])}
      ${f("position_when_window_open","Position bei Fenster offen (%)","number")}
      ${f("position_when_window_tilted","Position bei Fenster gekippt (%)","number")}
      <div class="field"><label><input type="checkbox" .checked=${!!s.lock_protection} @change=${e=>{s.lock_protection=e.target.checked;this.requestUpdate();}}> Aussperrschutz (verhindert vollständiges Schließen bei offener Tür)</label></div>
      ${s.lock_protection?f("min_position_when_open","Mindest-Position wenn Tür offen (%)","number"):""}
      ${areaSel("area_up_id","Bereich (Hoch)")}
      ${areaSel("area_down_id","Bereich (Runter)")}
      ${f("position_open","Position Offen (%)","number")}
      ${f("position_closed","Position Geschlossen (%)","number")}
      ${f("position_sun_protect","Sonnenschutz-Position (%)","number")}
      <div class="field"><label><input type="checkbox" .checked=${!!s.drive_after_close} @change=${e=>{s.drive_after_close=e.target.checked;this.requestUpdate();}}> Nachholen wenn Fenster offen</label>
        <div class="hint">Wenn die Schließzeit erreicht wird aber das Fenster noch offen ist, wird die Fahrt nachgeholt sobald das Fenster geschlossen wird.</div></div>
      <div class="form-actions">
        <button class="btn save" @click=${()=>this._saveShutter()}><ha-icon icon="mdi:content-save"></ha-icon>Speichern</button>
        <button class="btn cancel" @click=${()=>{this._editShutter=null;this.requestUpdate();}}>Abbrechen</button></div></div>`;
  }

  /* ─── Actions ─── */
  async _toggleAuto(id,on){try{await this.hass.callWS({type:"shutter_pilot/set_auto_mode",area_id:id,enabled:on});await this._load();}catch(e){console.warn(e);}}
  _svc(svc,id){this.hass.callService("shutter_pilot",svc,{area_id:id});}
  _stopArea(shutters){
    for(const s of shutters){
      const eid=s.cover_entity_id;
      if(eid)this.hass.callService("cover","stop_cover",{entity_id:eid});
    }
  }

  async _saveArea(){
    const a={...this._editArea};delete a._isNew;delete a._index;
    if(!a.id){a.id=a.name.toLowerCase().replace(/[äÄ]/g,"ae").replace(/[öÖ]/g,"oe").replace(/[üÜ]/g,"ue").replace(/[ß]/g,"ss").replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")||"bereich";}
    try{await this.hass.callWS({type:"shutter_pilot/save_area",area:a});this._editArea=null;await this._load();}catch(e){console.warn(e);alert("Fehler: "+e.message);}
  }
  async _deleteArea(id){
    if(!confirm(`Bereich "${id}" wirklich löschen?`))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_area",area_id:id});await this._load();}catch(e){console.warn(e);}
  }
  async _saveShutter(){
    const s={...this._editShutter};const idx=s._index;delete s._isNew;delete s._index;
    try{await this.hass.callWS({type:"shutter_pilot/save_shutter",shutter:s,index:idx});this._editShutter=null;await this._load();}catch(e){console.warn(e);alert("Fehler: "+e.message);}
  }
  async _deleteShutter(idx){
    if(!confirm("Rollladen wirklich löschen?"))return;
    try{await this.hass.callWS({type:"shutter_pilot/delete_shutter",index:idx});await this._load();}catch(e){console.warn(e);}
  }
}
customElements.define("shutter-pilot-panel",ShutterPilotPanel);
