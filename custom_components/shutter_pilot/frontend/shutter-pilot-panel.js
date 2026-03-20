/**
 * Shutter Pilot – Home Assistant Sidebar Panel
 * A LitElement-based web component for managing shutter areas and controls.
 */

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace") ?? customElements.get("hui-view")
);
const html = LitElement?.prototype?.html ?? (s => s);
const css = LitElement?.prototype?.css ?? (s => s);

const MODE_ICONS = { time: "mdi:clock-outline", brightness: "mdi:white-balance-sunny", sun: "mdi:weather-sunset" };
const MODE_LABELS = { time: "Zeit", brightness: "Helligkeit", sun: "Sonnenstand" };

class ShutterPilotPanel extends (LitElement ?? HTMLElement) {

  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      panel: { type: Object },
      _data: { type: Object, attribute: false },
    };
  }

  static get styles() {
    return css`
      :host { display: block; padding: 16px; --sp-card-bg: var(--card-background-color, #fff);
               --sp-primary: var(--primary-color, #03a9f4); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
      .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; flex-wrap: wrap; gap: 8px; }
      .header h1 { margin: 0; font-size: 24px; font-weight: 500; color: var(--primary-text-color); }
      .header .subtitle { font-size: 14px; color: var(--secondary-text-color); }
      .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
      .card { background: var(--sp-card-bg); border-radius: 12px; padding: 20px; box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.15)); }
      .card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
      .card-header .icon { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                           background: var(--sp-primary); color: #fff; --mdc-icon-size: 22px; }
      .card-header .info h2 { margin: 0; font-size: 18px; font-weight: 500; color: var(--primary-text-color); }
      .card-header .info span { font-size: 13px; color: var(--secondary-text-color); }
      .auto-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .auto-row .label { font-size: 14px; color: var(--primary-text-color); }
      .shutters { margin-top: 12px; }
      .shutter-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .shutter-row:last-child { border-bottom: none; }
      .shutter-name { font-size: 14px; color: var(--primary-text-color); flex: 1; }
      .shutter-pos { font-size: 13px; color: var(--secondary-text-color); min-width: 50px; text-align: right; }
      .actions { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
      .btn { border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; cursor: pointer; font-weight: 500;
             transition: opacity .2s; display: flex; align-items: center; gap: 6px; }
      .btn:hover { opacity: .85; }
      .btn.open { background: var(--label-badge-green, #4caf50); color: #fff; }
      .btn.close { background: var(--label-badge-red, #f44336); color: #fff; }
      .btn.sun { background: var(--label-badge-yellow, #ff9800); color: #fff; }
      .btn.config { background: var(--secondary-background-color, #eee); color: var(--primary-text-color); }
      .empty { text-align: center; padding: 48px 16px; color: var(--secondary-text-color); }
      .empty ha-icon { --mdc-icon-size: 48px; margin-bottom: 16px; display: block; }
    `;
  }

  constructor() {
    super();
    this._data = null;
  }

  connectedCallback() {
    super.connectedCallback?.();
    this._loadData();
  }

  updated(changedProps) {
    if (changedProps.has("hass") && this.hass) {
      this._loadData();
    }
  }

  async _loadData() {
    if (!this.hass) return;
    try {
      this._data = await this.hass.callWS({ type: "shutter_pilot/get_status" });
    } catch (e) {
      console.warn("Shutter Pilot: could not load status", e);
    }
  }

  render() {
    if (!this._data) {
      return html`<div class="empty"><ha-icon icon="mdi:loading"></ha-icon>Laden…</div>`;
    }
    const { areas, shutters, auto_modes } = this._data;
    if (!areas || areas.length === 0) {
      return html`
        <div class="header"><h1>Shutter Pilot</h1></div>
        <div class="empty">
          <ha-icon icon="mdi:window-shutter-settings"></ha-icon>
          <p>Keine Bereiche konfiguriert.<br>Öffne die Integrations-Einstellungen um Bereiche anzulegen.</p>
        </div>`;
    }
    return html`
      <div class="header">
        <div>
          <h1>Shutter Pilot</h1>
          <div class="subtitle">${areas.length} Bereich${areas.length !== 1 ? "e" : ""}, ${shutters.length} Rollladen</div>
        </div>
      </div>
      <div class="grid">
        ${areas.map(area => this._renderArea(area, shutters, auto_modes))}
      </div>`;
  }

  _renderArea(area, allShutters, autoModes) {
    const areaId = area.id;
    const mode = area.mode || "time";
    const icon = MODE_ICONS[mode] || "mdi:blinds";
    const modeLabel = MODE_LABELS[mode] || mode;
    const areaShutters = allShutters.filter(
      s => s.area_up_id === areaId || s.area_down_id === areaId
    );
    const autoOn = autoModes?.[areaId] !== false;
    return html`
      <div class="card">
        <div class="card-header">
          <div class="icon"><ha-icon icon="${icon}"></ha-icon></div>
          <div class="info">
            <h2>${area.name}</h2>
            <span>${modeLabel} · ${areaShutters.length} Rollladen</span>
          </div>
        </div>
        <div class="auto-row">
          <span class="label">Automatik</span>
          <ha-switch .checked=${autoOn} @change=${(e) => this._toggleAuto(areaId, e.target.checked)}></ha-switch>
        </div>
        <div class="shutters">
          ${areaShutters.length === 0
            ? html`<div style="padding:8px 0;color:var(--secondary-text-color);font-size:13px;">Keine Rollläden zugewiesen</div>`
            : areaShutters.map(s => this._renderShutter(s))}
        </div>
        <div class="actions">
          <button class="btn open" @click=${() => this._callService("open_group", areaId)}>
            <ha-icon icon="mdi:arrow-up-bold"></ha-icon>Hoch</button>
          <button class="btn close" @click=${() => this._callService("close_group", areaId)}>
            <ha-icon icon="mdi:arrow-down-bold"></ha-icon>Runter</button>
          <button class="btn sun" @click=${() => this._callService("sun_protect_group", areaId)}>
            <ha-icon icon="mdi:sun-wireless-outline"></ha-icon>Sonnenschutz</button>
        </div>
      </div>`;
  }

  _renderShutter(shutter) {
    const entityId = shutter.cover_entity_id;
    const stateObj = this.hass?.states?.[entityId];
    const pos = stateObj?.attributes?.current_position;
    const posText = pos != null ? `${Math.round(pos)}%` : "–";
    const friendlyName = stateObj?.attributes?.friendly_name || shutter.name || entityId;
    return html`
      <div class="shutter-row">
        <span class="shutter-name">${friendlyName}</span>
        <span class="shutter-pos">${posText}</span>
      </div>`;
  }

  async _toggleAuto(areaId, on) {
    try {
      await this.hass.callWS({ type: "shutter_pilot/set_auto_mode", area_id: areaId, enabled: on });
      await this._loadData();
    } catch (e) {
      console.warn("Failed to toggle auto mode", e);
    }
  }

  _callService(service, areaId) {
    this.hass.callService("shutter_pilot", service, { area_id: areaId });
  }
}

customElements.define("shutter-pilot-panel", ShutterPilotPanel);
