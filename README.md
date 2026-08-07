# Shutter Pilot

> **Automatic shutter/blind control for Home Assistant**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/fschubi/shutter_pilot)](https://github.com/fschubi/shutter_pilot/releases)
[![License](https://img.shields.io/github/license/fschubi/shutter_pilot)](LICENSE)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?logo=paypal&logoColor=white)](https://paypal.me/fschubi)

[Deutsche Version / German version](README.de.md)

---

Shutter Pilot is a Home Assistant custom integration that automates your shutters, blinds, and roller shutters based on **time schedules**, **brightness sensors**, or **sun position**. It adds a dedicated **sidebar panel** for easy management directly within Home Assistant.

## Features

- **Three control modes** per area: Time-based, brightness-based (lux sensor), or sun position (sunrise/sunset)
- **Sidebar panel** with Dashboard, Areas, and Shutters tabs for full management
- **Window/door sensors** – automatically opens shutters when windows are opened
- **Lock protection** – prevents full closing when a door is open
- **Sun protection with compass direction** – shades only when the sun is within the elevation range **and** actually facing the windows
- **Drive-after-close** – catches up scheduled movements when a window was still open
- **Per-shutter positions** – configurable open, closed, and sun-protection positions
- **Slat control** – optional tilt angle for venetian blinds
- **Workday sensor** – handles public holidays, vacation and shift work instead of a fixed Saturday/Sunday rule
- **Presence simulation** – random ±X minute offset on scheduled times
- **Light actions** – turn on a light/switch when shutters close
- **Auto-mode switches** – enable/disable automation per area via HA switches
- **Own entities** – next scheduled action and sun protection state as sensors for dashboards and automations
- **Multi-language panel** – automatically adapts to your HA language (11 languages)
- **Weekday/weekend schedules** – separate time windows for weekdays and weekends (time mode and brightness mode)
- **Sun info on dashboard** – shows next sunrise/sunset, configured offsets, and calculated trigger times for sun-mode areas

## Screenshots

Click an image to open it **full size** on GitHub (thumbnails are scaled down in this page).

<p align="center">
  <a href="docs/screenshots/dashboard.png" title="Dashboard – full size">
    <img src="docs/screenshots/dashboard.png" alt="Shutter Pilot – Dashboard tab" width="280" />
  </a>
  &nbsp;&nbsp;
  <a href="docs/screenshots/areas.png" title="Areas – full size">
    <img src="docs/screenshots/areas.png" alt="Shutter Pilot – Areas tab" width="280" />
  </a>
  &nbsp;&nbsp;
  <a href="docs/screenshots/shutters.png" title="Shutters – full size">
    <img src="docs/screenshots/shutters.png" alt="Shutter Pilot – Shutters tab" width="280" />
  </a>
</p>

<p align="center">
  <b>Dashboard</b> · <b>Areas</b> · <b>Shutters</b>
</p>

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/fschubi/shutter_pilot` as **Integration**
4. Search for "Shutter Pilot" and install
5. Restart Home Assistant

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/fschubi/shutter_pilot/releases)
2. Copy the `custom_components/shutter_pilot` folder to your HA `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Shutter Pilot** and click to add
3. After setup, "Shutter Pilot" appears in the sidebar

> **Note:** The panel is available to every user in the sidebar, but **only an administrator can configure it**. Without administrator rights the panel shows the dashboard with the control buttons (up, down, stop, sun protection, ventilate); the tabs for areas, shutters and settings as well as the master and auto switches are hidden. Every write command is checked server-side on top of that.

## Configuration

All configuration is done through the **Shutter Pilot sidebar panel**:

### Areas (Tab "Areas")

Click **"Add area"** to create a new area. Choose a control mode:

| Mode | Description |
|------|-------------|
| **Time** | Shutters go up/down at fixed times with separate weekday/weekend schedules |
| **Brightness** | Driven by a lux sensor with configurable thresholds and allowed time windows |
| **Sun position** | Uses Home Assistant's sunrise/sunset tracking with configurable offsets |

Each area can also have:
- **Sun protection** – drives shutters to a mid-position when the sun is within the elevation range **and** facing the windows
- **Extra shading conditions** – up to two sensors that must also be satisfied (see below)
- **Light action** – turns on a light/switch entity when shutters close
- **Drive delay** – seconds between individual shutters (prevents circuit overload)

### Shutters (Tab "Shutters")

Click **"Add shutter"** to assign a cover entity to an area:

- **Cover entity** – your `cover.*` entity
- **Window sensor** – optional `binary_sensor.*` for window open/tilt detection
- **Extra sensor for "tilted"** – only needed if your window exposes two separate entities, one for open and one for tilted. Leave empty for a single 3-state contact
- **Area Up / Area Down** – which area controls this shutter for up/down movements
- **Position sliders** – open, closed, and sun protection positions (0-100%)
- **Lock protection** – minimum position when a door is open (prevents lockout)
- **Drive after close** – catches up a missed close command when the window was still open
- **Close delay** – how long "closed" has to hold before the shutter drives back (0–30 s, default 5 s). Turning the handle from tilted to open drags the contact through "closed"; without a wait the shutter drives back immediately and never reaches the open position. `0` disables the wait

### Dashboard

The Dashboard tab shows all areas as cards with:
- Current shutter positions (live)
- Auto-mode toggle per area
- **Sun info panel** for sun-mode areas: next sunrise/sunset, offset, calculated trigger time, current elevation
- Quick action buttons: **Up**, **Stop**, **Down**, **Sun protection**

## Services

| Service | Description |
|---------|-------------|
| `shutter_pilot.open_group` | Open all shutters in an area |
| `shutter_pilot.close_group` | Close all shutters in an area |
| `shutter_pilot.sun_protect_group` | Move all shutters in an area to sun protection position |
| `shutter_pilot.ventilate_group` | Move all shutters in an area to the ventilation position |

All services accept an `area_id` parameter (e.g. `living`, `bedroom`). Every shutter moves to its own configured position.

## Entities

Besides the panel, Shutter Pilot creates entities you can use on regular dashboards and in your own automations:

| Entity | Description |
|--------|-------------|
| `switch.shutter_pilot_system` | Master switch for all automation |
| `switch.shutter_pilot_auto_<area>` | Automation per area |
| `switch.shutter_pilot_rollladen_<name>` | Automation per shutter (named after the **Name** field) |
| `sensor.shutter_pilot_<area>_next_action` | Timestamp of the next scheduled movement, attribute `direction` = `up`/`down` |
| `binary_sensor.shutter_pilot_<area>_sun_protection` | `on` while shading is active |

## Switching automation off

Automation can be paused on three levels, independently of each other:

| Level | Effect |
|-------|--------|
| **Master switch** | the whole integration stops driving |
| **Area** | only this area pauses |
| **Shutter** | exactly this shutter stays put, the rest of its area keeps going |

The shutter level is meant for a shutter that must not move for a while – a broken drive waiting for a spare part.

It can be toggled in three equivalent places:

- on the **dashboard**, right in the shutter row of its area
- in the **Shutters** tab list
- through the `switch.shutter_pilot_rollladen_<name>` entity, from your own automations too

The **Automation active** checkbox in the shutter form sets the initial value. A disabled shutter also gets an icon on the dashboard, so nobody has to guess why it stays put.

Note that only **automation** is switched off. Manual control keeps working – the dashboard buttons, the `open_group`/`close_group` services and the cover entity itself. Otherwise you could not even test the shutter after repairing it.

## Event

Every automated movement fires `shutter_pilot_cover_moved` on the event bus:

```yaml
automation:
  - alias: Notify when shutters close
    trigger:
      - platform: event
        event_type: shutter_pilot_cover_moved
    condition: "{{ trigger.event.data.position < 20 }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            {{ trigger.event.data.entity_id }} to
            {{ trigger.event.data.position }}% ({{ trigger.event.data.reason }})
```

Fields: `entity_id`, `position`, `tilt_position`, `reason`, `area_id`, `source`.

## Troubleshooting

For bug reports, download diagnostics: **Settings → Devices & Services → Shutter Pilot → ⋮ → Download diagnostics**. The file contains configuration, runtime state and sun data; home coordinates are redacted.

## Supported Languages

The Shutter Pilot panel automatically adapts to your Home Assistant language setting:

| Language | Code | |
|----------|:----:|---|
| Deutsch (German) | `de` | :de: |
| English | `en` | :gb: |
| Français (French) | `fr` | :fr: |
| Español (Spanish) | `es` | :es: |
| Italiano (Italian) | `it` | :it: |
| Nederlands (Dutch) | `nl` | :netherlands: |
| Dansk (Danish) | `da` | :denmark: |
| Svenska (Swedish) | `sv` | :sweden: |
| Polski (Polish) | `pl` | :poland: |
| Português (Portuguese) | `pt` | :portugal: |
| Norsk Bokmål (Norwegian) | `nb` | :norway: |

If your language is not listed, the panel falls back to English. Want to contribute a translation? PRs are welcome!

## Planned: Awning / Marquise Support

> **We're considering adding awning/marquise control** with wind, rain, and temperature sensors as a dedicated tab. Awnings have different requirements than shutters – they need to retract during bad weather to prevent damage.
>
> Planned features: wind speed sensor, rain sensor, temperature threshold, weather warning integration (DWD, OpenWeatherMap), and automatic retraction on dangerous conditions.

**Would you use this feature? [Vote here!](https://github.com/fschubi/shutter_pilot/discussions/1)**

[![Feature Poll](https://img.shields.io/badge/Vote-Awning%20Support%20Poll-blue?style=for-the-badge&logo=github)](https://github.com/fschubi/shutter_pilot/discussions/1)

## Shade only on real sun and real warmth

Elevation and compass direction only tell you **where** the sun is – not whether it is actually shining, or whether it is warm enough to matter. In spring and autumn the solar warmth is usually welcome.

That is why each area can carry up to **two extra conditions**. Shading only runs while all of them hold:

| Sensor type | Behaviour |
|-------------|-----------|
| **Binary sensor** (e.g. "high solar radiation") | Shades while it is `on`. The hysteresis lives in your sensor |
| **Numeric sensor** (lux, W/m², °C) | Shades from "Shade above", releases only below "Release below" |

The gap between the two thresholds stops the shutters from bouncing when clouds pass. Leave "Release below" empty to use the same value.

An empty field means no condition. An unavailable or broken sensor never blocks shading.

### Weather and forecast

Set your `weather.*` entity in the **Settings** tab. Shutter Pilot then fetches the daily forecast itself and provides two sensors:

| Sensor | Content |
|--------|---------|
| Forecast high temperature | expected daily high |
| Forecast condition | expected condition, e.g. `sunny` |

Pick either as an ordinary condition. A typical setup is **forecast high, shade above 24 °C** — so nothing is shaded on cool days and the sun warms the house.

An unreachable weather backend never blocks shading; the last known value is kept.

### Sensors with a text state

Conditions can compare **states** instead of numbers. That lets you use a `weather.*` entity or your own scrape sensor directly: simply pick the conditions that should trigger shading. For weather entities the standard conditions are offered as buttons.

### Shading season

Each area can be limited to certain months, e.g. April to September. Ranges may wrap across the new year, such as October to March.

A temperature condition usually makes this unnecessary: if the winter forecast stays below the threshold, no shading happens anyway.

### Sensors per window instead of per area

Conditions can live on the **area** and on the **individual shutter**. The rule is simple:

> The area provides the default. Whatever is set on the shutter wins for that window.

The fallback works **per condition**, not all or nothing. A typical setup:

- **Area:** condition 1 = forecast high above 24 °C, applies to every window
- **South window:** condition 2 = brightness sensor at the south window
- **West window:** condition 2 = brightness sensor at the west window

Both windows inherit the temperature condition while keeping their own brightness sensor. A room temperature can be set per shutter the same way.

Each window keeps its own hysteresis, so a cloud in front of one window does not release the shading of another.

## Drive by sun position, but not too early

In sun mode the computed moment can be clamped into a clock window:

| Setting | Effect |
|---|---|
| Up earliest 07:30 | In summer the sun rises at 5 a.m. – the shutters still wait until 07:30 |
| Up latest 09:00 | In winter daylight comes late – the shutter opens at 09:00 at the latest |

Weekends have their own values. Left empty, the weekday values apply. Empty fields generally mean no limit.

All times are local time — the timezone from your Home Assistant settings. The dashboard shows next to each drive time why it differs from the sun time: "· no earlier than 07:30" when a bound applies, or "· Presence: +4 min" with presence simulation enabled.

## Minimum gap between drive commands

Radio receivers — 433 MHz, HmIP and relatives — swallow commands that arrive at the same moment. The **per-area delay** only helps so far: it staggers the shutters *within* one area, but every area drives in its own task. When two areas start at the same time in the evening, their commands still collide.

The **Settings** tab therefore offers a **minimum gap between drive commands** (0–10 s). It applies at the single place every drive passes through — automated or manual — and spaces them out across all areas. Throttling here means waiting, not dropping: every shutter still gets its command, just one after another.

`0` disables the throttle; that is the behaviour before version 2.7.0.

## Verifying drives

Radio-driven shutters occasionally drop a command. Without a check nobody notices, and the integration keeps working with a position the shutter never reached.

The **Settings** tab therefore offers verification. After each automated drive, the position is checked after a configurable delay and the command repeated if needed.

On final failure the stored value is corrected and `shutter_pilot_cover_failed` is fired — with `entity_id`, `requested`, `actual` and `reason`:

```yaml
automation:
  - alias: Shutter not responding
    trigger:
      - platform: event
        event_type: shutter_pilot_cover_failed
    action:
      - service: notify.mobile_app
        data:
          message: >
            {{ trigger.event.data.entity_id }} is at
            {{ trigger.event.data.actual }}% instead of
            {{ trigger.event.data.requested }}%
```

Shutters that only report open/closed without a position are skipped automatically.

## Rooms with windows facing several directions

Elevation and compass direction normally apply to the whole area. If one window faces a different way than the others in the same room, enable **Own orientation** on that shutter and set its elevation and azimuth there.

South and west windows of the same room are then shaded at different times of day, without maintaining two areas with duplicated schedules.

## Closing only part way in the evening

To keep certain shutters from closing fully on hot evenings so the room can keep ventilating:

1. In the **area**, under *Partial closing*, set a condition — e.g. a sensor for heat and presence
2. On the relevant **shutters**, set a partial position, e.g. 50 %

Only shutters with a partial position deviate; all others close normally.

## Brightness mode with a sun bound

A thunderstorm in the afternoon pushes the lux below the threshold — and the shutters close in broad daylight. Clock windows only help so far, because sunset moves by hours through the year.

Brightness mode therefore offers two extra bounds:

| Setting | Effect |
|---|---|
| Down no earlier than X min. before sunset | Nothing closes before then, however dark it gets |
| Up no earlier than X min. before sunrise | Nothing opens before then |

Example: sunset at 21:10 with "60" means closing starts at 20:10 at the earliest. Both bounds apply **on top of** the clock windows — the tighter one wins.

Empty means no bound. The value `0` is not the same as empty — it means "exactly at sunset".

## Chasing clouds up and down

Sensor noise is already handled: separate on and off thresholds, hysteresis per condition, and only one movement per direction and phase. A drifting cloud is not noise though — it genuinely ends the condition, and the shutter opened right away.

The area therefore offers **Hold shading** (0–120 minutes). The shading stays up for that long even once the condition no longer holds. If the sun returns before then, the clock starts over next time.

Two things stay immediate on purpose:

- **Shading itself.** When the sun hits the window, the shutter should not wait an hour first.
- **The end of the day.** Once the sun drops below the configured elevation, shading is over and the normal evening schedule takes it from there, without delay.

`0` keeps the previous behaviour.

## Shading from brightness sensors alone

With brightness sensors around the house, elevation and compass direction are not needed — the sensor already knows whether the sun hits the window. No separate mode required:

1. Enable sun protection in the **area**
2. **Turn the compass direction off** — the azimuth is then not checked
3. Set the **elevation range to 0–90**, so it holds whenever the sun is up at all
4. Add the brightness sensor as an **extra condition**, with a switch-on and a switch-off threshold

Brightness alone then decides. The two thresholds matter more here than elsewhere: they keep a passing cloud from releasing the shading right away.

Because conditions can be overridden **per shutter**, each window gets its own sensor while the rest of the settings stay in the area.

## Automatic ventilation

Ventilating used to be manual only — the dashboard button or the service. In the **area**, under *Automatic ventilation*, you can now say when it should happen by itself:

1. Enable **Ventilate automatically**
2. Name up to two conditions that **both** have to hold — e.g. a presence sensor "on" and a room temperature above 24 °C

While all conditions hold, the area's shutters move to their **ventilation position** (the same one used for a tilted window). When one drops out they move back to where they stood before — not to "open", which would be wrong at night.

Ranking when several things apply at once:

| Priority | Reason |
|---|---|
| 1. Window contact | reacts to what somebody physically did at the window |
| 2. Shading | heat comes first |
| 3. Automatic ventilation | only touches shutters that are otherwise sitting still |

With no condition configured nothing happens. Master, area and per-shutter switches apply as everywhere; switching the area off mid-ventilation still drives the shutter back rather than leaving it part way open.

## Frost protection

In frost a fully closed shutter can freeze to the frame. Leaving a gap prevents that:

1. In the **area**, under *Frost protection*, set a condition — the obvious choice is the **Forecast low** sensor Shutter Pilot provides itself once a weather entity is configured
2. On the relevant **shutters**, set a frost position, e.g. 10 %

Unlike every other condition this one compares **downwards**: frost protection kicks in *below* the first value and stays on until the second is exceeded. The hysteresis keeps it from toggling around freezing point.

Frost protection wins over partial closing — protection beats comfort. Both apply in time, sun and brightness mode. A shutter without a frost position still closes fully, even when the area's condition is met.

## Support me

Shutter Pilot is built in my spare time and is — and stays — free and open source. If it makes your day a little easier and you'd like to say thanks, I'd appreciate a coffee:

<a href="https://paypal.me/fschubi">
  <img src="https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate via PayPal" />
</a>

Just as helpful and completely free: leave a ⭐, [report a bug](https://github.com/fschubi/shutter_pilot/issues), or contribute a translation.

## Minimum Requirements

- Home Assistant **2024.6.0** or newer

## License

MIT – see the [LICENSE](LICENSE) file for details.
