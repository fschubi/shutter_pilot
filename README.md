# Shutter Pilot

> **Automatic shutter/blind control for Home Assistant**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/fschubi/shutter_pilot)](https://github.com/fschubi/shutter_pilot/releases)

[Deutsche Version / German version](README.de.md)

---

Shutter Pilot is a Home Assistant custom integration that automates your shutters, blinds, and roller shutters based on **time schedules**, **brightness sensors**, or **sun position**. It adds a dedicated **sidebar panel** for easy management directly within Home Assistant.

## Features

- **Three control modes** per area: Time-based, brightness-based (lux sensor), or sun position (sunrise/sunset)
- **Sidebar panel** with Dashboard, Areas, and Shutters tabs for full management
- **Window/door sensors** – automatically opens shutters when windows are opened
- **Lock protection** – prevents full closing when a door is open
- **Sun protection** – drives shutters to a configurable position when sun elevation drops
- **Drive-after-close** – catches up scheduled movements when a window was still open
- **Per-shutter positions** – configurable open, closed, and sun-protection positions
- **Light actions** – turn on a light/switch when shutters close
- **Auto-mode switches** – enable/disable automation per area via HA switches
- **Multi-language panel** – automatically adapts to your HA language (DE, EN, FR, ES, IT)
- **Weekday/weekend schedules** – separate time windows for weekdays and weekends (brightness mode)

## Screenshots

| Dashboard | Areas | Shutters |
|-----------|-------|----------|
| Area cards with live status, auto-toggle, and quick actions (Up/Stop/Down/Sun) | Area list with mode badges, add/edit/delete | Shutter list with area assignments, add/edit/delete |

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

## Configuration

All configuration is done through the **Shutter Pilot sidebar panel**:

### Areas (Tab "Areas")

Click **"Add area"** to create a new area. Choose a control mode:

| Mode | Description |
|------|-------------|
| **Time** | Shutters go up/down at fixed times (e.g. 07:00 up, 19:00 down) |
| **Brightness** | Driven by a lux sensor with configurable thresholds and allowed time windows |
| **Sun position** | Uses Home Assistant's sunrise/sunset tracking with configurable offsets |

Each area can also have:
- **Sun protection** – drives shutters to a mid-position when sun elevation drops below threshold
- **Light action** – turns on a light/switch entity when shutters close
- **Drive delay** – seconds between individual shutters (prevents circuit overload)

### Shutters (Tab "Shutters")

Click **"Add shutter"** to assign a cover entity to an area:

- **Cover entity** – your `cover.*` entity
- **Window sensor** – optional `binary_sensor.*` for window open/tilt detection
- **Area Up / Area Down** – which area controls this shutter for up/down movements
- **Position sliders** – open, closed, and sun protection positions (0-100%)
- **Lock protection** – minimum position when a door is open (prevents lockout)
- **Drive after close** – catches up a missed close command when the window was still open

### Dashboard

The Dashboard tab shows all areas as cards with:
- Current shutter positions (live)
- Auto-mode toggle per area
- Quick action buttons: **Up**, **Stop**, **Down**, **Sun protection**

## Services

| Service | Description |
|---------|-------------|
| `shutter_pilot.open_group` | Open all shutters in an area |
| `shutter_pilot.close_group` | Close all shutters in an area |
| `shutter_pilot.sun_protect_group` | Move all shutters in an area to sun protection position |

All services accept an `area_id` parameter (e.g. `living`, `bedroom`).

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

## Minimum Requirements

- Home Assistant **2024.6.0** or newer

## License

This project is open source. See the [LICENSE](LICENSE) file for details.
