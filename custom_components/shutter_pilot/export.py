"""Settings export – a forum-ready report of what is actually configured.

Every bug report so far arrived as a handful of screenshots: one of the area
form, one of the shutter form, one of a dashboard with the sensor values. Half
the settings that decide the outcome were never in the picture, and the values
had been read at a different moment than the shutters misbehaved. Two reports
could not be answered from their screenshots at all.

So this does three things that screenshots cannot:

* it dumps **every** stored key of every area and shutter, not a curated
  selection – the field that turns out to matter is always the one nobody
  thought to photograph,
* it reads the condition sensors **now**, in the same pass, so values and
  settings belong to the same moment,
* it runs the real shading decision per shutter and prints why it came out the
  way it did. That single line answers most reports outright.

The evaluation runs against a **copy** of the hysteresis memory. Asking a
question must not change the answer – evaluating a condition normally records
whether it was met, and an export doing that would nudge the very state it is
meant to document.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_SUN_GEOMETRY_OVERRIDE,
    CONF_WINDOW_ENTITY_ID,
    DOMAIN,
    INVERTED_BY_DEFAULT_SLOTS,
    SUN_CONDITION_SLOTS,
    sun_condition_invert_key,
    sun_condition_keys,
)
from .helpers import (
    elevation_used,
    get_azimuth_bounds,
    get_cover_current_position,
    get_elevation_bounds,
    get_sun_angles,
    is_auto_enabled,
    is_cover_sun_protected,
    is_shutter_automation_enabled,
    is_system_enabled,
    resolve_shading_config,
    season_allows_shading,
    sun_protect_conditions_met,
)
from .position_store import get_position_store
from .window_helper import has_tilt_state

# Geometriewerte, die ohne "Eigene Ausrichtung" stumm liegen bleiben.
_GEOMETRY_KEYS = (
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_ENABLED,
)

# Keys that only ever repeat what the heading already says.
_SKIP_KEYS = frozenset({CONF_AREA_ID, CONF_AREA_NAME, CONF_COVER_ENTITY_ID})


def _fmt(value: Any) -> str:
    """One config value as a single readable line."""
    if value is None:
        return "–"
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) if value else "–"
    text = str(value)
    return text if text.strip() else "–"


def _is_set(value: Any) -> bool:
    """True if the user actually put something there.

    `False` counts as set – a switched-off option is a decision, and in a bug
    report it is often *the* decision.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _settings_table(obj: dict[str, Any]) -> list[str]:
    """All stored keys of one area or shutter, as a markdown table."""
    rows = [
        f"| `{key}` | {_fmt(value)} |"
        for key, value in sorted(obj.items())
        if key not in _SKIP_KEYS and not key.startswith("_") and _is_set(value)
    ]
    if not rows:
        return ["_keine abweichenden Einstellungen_", ""]
    return ["| Einstellung | Wert |", "| --- | --- |", *rows, ""]


def _memory_copy(
    data: dict[str, Any], area_id: str, cover_entity_id: str | None = None
) -> dict[str, Any]:
    """A copy of the hysteresis memory, without creating it.

    `condition_memory()` sets the entry up on first access, which for an export
    would mean writing runtime state just by looking at it – and the copy would
    then be of something this call itself brought into existence.
    """
    key = f"{area_id}|{cover_entity_id}" if cover_entity_id else area_id
    stored = data.get("sun_cond_state", {})
    return dict(stored.get(key, {})) if isinstance(stored, dict) else {}


def _state_of(hass: HomeAssistant, entity_id: str) -> str:
    """The sensor value as it reads right now, with its unit.

    The unit is the point. Two reports in a row set five-digit lux thresholds
    on a sensor that measures W/m² and tops out near 1000 – the numbers look
    fine side by side until the unit is next to them.
    """
    state = hass.states.get(entity_id)
    if state is None:
        return "**Entität gibt es nicht**"
    if state.state in ("unknown", "unavailable"):
        return f"**{state.state}**"
    unit = str(state.attributes.get("unit_of_measurement") or "").strip()
    return f"{state.state} {unit}".strip()


def _condition_note(
    hass: HomeAssistant, cfg: dict[str, Any], slot: str, entity_id: str
) -> str:
    """Warn about the two ways a condition passes without meaning anything."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        # Shading conditions fail open by design, so this reads as a tick in
        # the table – which looks like the condition was checked and held.
        return "Sensor liefert nichts – blockiert nicht (fail open)"

    _, on_key, off_key, states_key = sun_condition_keys(slot)
    if _is_set(cfg.get(states_key)):
        return ""
    try:
        on_above = float(cfg.get(on_key))
        off_below = float(cfg.get(off_key))
    except (TypeError, ValueError):
        return ""
    inverted = bool(
        cfg.get(sun_condition_invert_key(slot), slot in INVERTED_BY_DEFAULT_SLOTS)
    )
    if (off_below > on_above) if not inverted else (off_below < on_above):
        # Same clamp helpers.py applies, spelled out where it is visible.
        return (
            f"⚠️ „auf unter\" liegt auf der falschen Seite und wird verworfen – "
            f"die Bedingung heißt nur noch „{'≤' if inverted else '≥'} "
            f"{on_above:.10g}\""
        )
    return ""


def _condition_rows(
    hass: HomeAssistant, cfg: dict[str, Any], memory: dict[str, Any]
) -> tuple[list[str], bool]:
    """The extra shading conditions of one config, with their live values.

    Returns the markdown rows and whether every condition holds. `memory` must
    be a copy – see the module docstring.
    """
    # Imported here so the private evaluator stays private to helpers.
    from .helpers import _condition_slot_met

    rows: list[str] = []
    all_met = True
    for slot in SUN_CONDITION_SLOTS:
        entity_key, on_key, off_key, states_key = sun_condition_keys(slot)
        entity_id = str(cfg.get(entity_key) or "").strip()
        if not entity_id:
            continue
        met = _condition_slot_met(hass, cfg, slot, memory)
        all_met = all_met and met
        allowed = cfg.get(states_key)
        limits = (
            f"Zustände: {_fmt(allowed)}"
            if _is_set(allowed)
            else f"ab {_fmt(cfg.get(on_key))} / auf unter {_fmt(cfg.get(off_key))}"
        )
        rows.append(
            f"| {slot} | `{entity_id}` | {_state_of(hass, entity_id)} | "
            f"{limits} | {'✅' if met else '❌'} | "
            f"{_condition_note(hass, cfg, slot, entity_id) or '–'} |"
        )
    if not rows:
        return [], True
    return (
        [
            "| Bed. | Sensor | Wert jetzt | Schwellen | erfüllt | Hinweis |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ],
        all_met,
    )


def _silent_setting_notes(shutter: dict[str, Any]) -> list[str]:
    """Settings that are stored, look like they work, and do nothing.

    Both come from the same trap: a value the form still shows – or showed in
    an older version – while a switch next to it decides that something else
    is read instead. In the table below they sit next to the values that do
    apply, and nothing tells them apart.
    """
    notes: list[str] = []

    if not shutter.get(CONF_SUN_GEOMETRY_OVERRIDE):
        own = [key for key in _GEOMETRY_KEYS if _is_set(shutter.get(key))]
        if own:
            notes.append(
                "> ⚠️ Eigene Werte für Sonnenhöhe/Fensterrichtung sind "
                f"hinterlegt ({', '.join(f'`{k}`' for k in own)}), aber "
                "**„Eigene Ausrichtung\" ist aus** – es gelten die Werte des "
                "Bereichs."
            )

    window_id = shutter.get(CONF_WINDOW_ENTITY_ID)
    if _is_set(window_id) and not has_tilt_state(shutter):
        open_pos = shutter.get(CONF_POSITION_WHEN_WINDOW_OPEN)
        tilt_pos = shutter.get(CONF_POSITION_WHEN_WINDOW_TILTED)
        if _is_set(open_pos) and _is_set(tilt_pos) and open_pos != tilt_pos:
            notes.append(
                "> ⚠️ Ohne Kipp-Zustand ist der Kontakt zweiwertig, gefahren "
                f"wird immer `position_when_window_tilted` ({_fmt(tilt_pos)} %) "
                f"– auch bei „offen\". `position_when_window_open` "
                f"({_fmt(open_pos)} %) wird nie benutzt."
            )

    return [*notes, ""] if notes else []


def _shading_verdict(
    hass: HomeAssistant,
    area: dict[str, Any],
    shutter: dict[str, Any],
    data: dict[str, Any],
    elev: float | None,
    azim: float | None,
    blocked: str = "",
    fresh_runtime: bool = False,
) -> list[str]:
    """Run the real shading decision for one shutter and explain the outcome.

    `blocked` names the switch that stops this shutter from being driven at
    all. The decision is still worth printing – it is what the configuration
    says – but on its own it reads like a promise the integration will not keep.

    `fresh_runtime` says the markers were wiped moments ago by a reload, which
    makes a divergence the expected reading rather than a finding.
    """
    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "")
    geo = resolve_shading_config(area, shutter)

    # A copy, so documenting the state does not change it.
    memory = _memory_copy(data, str(area.get(CONF_AREA_ID) or ""), cover)

    geometry_ok = sun_protect_conditions_met(elev, azim, geo)
    season_ok = season_allows_shading(area)
    cond_rows, conditions_ok = _condition_rows(hass, geo, memory)

    e_min, e_max = get_elevation_bounds(geo)
    a_min, a_max = get_azimuth_bounds(geo)
    az_used = bool(geo.get("azimuth_enabled", False))

    elev_txt = "–" if elev is None else f"{elev:.1f}°"
    lines = [
        "- Sonnenhöhe: nicht geprüft (Option aus), gemessen " + elev_txt
        if not elevation_used(geo)
        else (
            f"- Elevation {elev_txt} in [{e_min:.1f}° – {e_max:.1f}°]: "
            f"{'✅' if elev is not None and e_min <= elev <= e_max else '❌'}"
        ),
        "- Fensterrichtung: "
        + (
            f"{'✅' if geometry_ok else '❌'} "
            f"({'–' if azim is None else f'{azim:.1f}°'} in "
            f"[{a_min:.0f}° – {a_max:.0f}°])"
            if az_used
            else "nicht geprüft (Option aus)"
        ),
        f"- Beschattungszeitraum: {'✅' if season_ok else '❌'}",
        f"- Zusätzliche Bedingungen: {'✅' if conditions_ok else '❌'}",
    ]
    should = geometry_ok and season_ok and conditions_ok
    lines.append("")
    lines.append(
        f"**Ergebnis: {'beschatten' if should else 'nicht beschatten'}** · "
        f"gemerkter Zustand: "
        f"{'beschattet' if is_cover_sun_protected(data, cover) else 'nicht beschattet'}"
    )
    if blocked:
        lines.append("")
        lines.append(
            f"> ⚠️ {blocked} steht auf **aus**. Diese Entscheidung wird berechnet, "
            "aber nicht gefahren – die Beschattung bleibt aus, egal was hier steht."
        )
    elif should != is_cover_sun_protected(data, cover) and fresh_runtime:
        lines.append("")
        lines.append(
            "> ℹ️ Entscheidung und gemerkter Zustand gehen auseinander, weil die "
            "Integration gerade neu geladen wurde – der Merker ist dabei leer "
            "geworden und steht nach der nächsten Minute wieder. Kein Fehler."
        )
    elif should != is_cover_sun_protected(data, cover):
        lines.append("")
        lines.append(
            "> ⚠️ Entscheidung und gemerkter Zustand gehen auseinander. Das ist "
            "normal, solange eine Haltezeit läuft oder die Minute noch nicht "
            "vorbei ist – bleibt es so, gehört es in den Fehlerbericht."
        )
    lines.append("")
    return lines + cond_rows


async def async_build_export(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Build the export as markdown plus the raw options behind it."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    if not isinstance(data, dict):
        data = {}

    areas = entry.options.get(CONF_AREAS, [])
    areas = [a for a in areas if isinstance(a, dict)] if isinstance(areas, list) else []
    shutters = entry.options.get(CONF_SHUTTERS, [])
    shutters = (
        [s for s in shutters if isinstance(s, dict)] if isinstance(shutters, list) else []
    )
    areas_by_id = {str(a.get(CONF_AREA_ID) or ""): a for a in areas}

    elev, azim = get_sun_angles(hass)
    store = get_position_store(hass, entry.entry_id)
    now = dt_util.as_local(dt_util.now())

    # Jedes Speichern im Panel laedt den Entry neu, und dabei gehen alle
    # Laufzeit-Merker verloren. Wer danach exportiert – also fast jeder, der
    # gerade etwas umgestellt hat – bekam eine Tabelle voller Striche und die
    # Aufforderung, das zu melden.
    started = data.get("_runtime_started")
    age_minutes: float | None = None
    if isinstance(started, datetime):
        age_minutes = max(0.0, (dt_util.utcnow() - started).total_seconds() / 60.0)
    fresh_runtime = age_minutes is not None and age_minutes < 5

    # Which build produced this report matters more than anything else in it –
    # half the answers in the forum are "that is fixed in the newer version".
    version = "?"
    try:
        integration = await async_get_integration(hass, DOMAIN)
        version = str(integration.version or "?")
    except Exception:  # pragma: no cover - version is nice to have, not vital
        pass

    out: list[str] = [
        f"## Shutter Pilot {version} – Einstellungs-Export",
        "",
        f"Erstellt: {now.strftime('%Y-%m-%d %H:%M %Z')} · "
        f"Home Assistant {HA_VERSION} · "
        f"Sonne: Elevation {'–' if elev is None else f'{elev:.1f}°'}, "
        f"Azimut {'–' if azim is None else f'{azim:.1f}°'}",
        "",
        f"System aktiv: {'ja' if is_system_enabled(hass, entry) else '**nein**'}",
        "",
    ]

    globals_ = {
        key: value
        for key, value in (entry.options or {}).items()
        if key not in (CONF_AREAS, CONF_SHUTTERS)
    }
    if globals_:
        out += ["### Allgemeine Einstellungen", "", *_settings_table(globals_)]

    for area in areas:
        area_id = str(area.get(CONF_AREA_ID) or "")
        name = str(area.get(CONF_AREA_NAME) or area_id)
        out += [
            f"### Bereich „{name}\" (`{area_id}`)",
            "",
            f"Modus: `{_fmt(area.get(CONF_AREA_MODE))}` · "
            f"Automatik: {'an' if is_auto_enabled(hass, entry, area) else '**aus**'} · "
            f"Sonnenschutz: "
            f"{'an' if area.get(CONF_AREA_SUN_PROTECT_ENABLED) else 'aus'}",
            "",
            *_settings_table(area),
        ]
        rows, _ = _condition_rows(hass, area, _memory_copy(data, area_id))
        if rows:
            out += ["Bedingungen des Bereichs, Werte von jetzt:", "", *rows]

    for shutter in shutters:
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "")
        name = str(shutter.get(CONF_NAME) or "")
        up_id = str(shutter.get(CONF_AREA_UP_ID) or "")
        down_id = str(shutter.get(CONF_AREA_DOWN_ID) or "")
        pos = get_cover_current_position(hass, cover)
        record = store.get_record(cover) or {}

        heading = f"### Rollladen `{cover}`"
        if name:
            heading += f" – „{name}\""
        out += [
            heading,
            "",
            f"Position jetzt: {'–' if pos is None else f'{pos:.0f} %'} · "
            f"zuletzt gespeichert: {_fmt(record.get('position'))} "
            f"(Quelle: {_fmt(record.get('source'))}) · "
            f"Automatik: "
            f"{'an' if is_shutter_automation_enabled(hass, entry, shutter) else '**aus**'}",
            "",
            f"Bereich hoch: `{up_id or '–'}` · Bereich runter: `{down_id or '–'}` "
            "(der Runter-Bereich entscheidet über die Beschattung)",
            "",
        ]

        down_area = areas_by_id.get(down_id)
        if down_area is None and down_id:
            out += [
                f"> ⚠️ Bereich `{down_id}` gibt es nicht mehr – dieser Rollladen "
                "wird nie beschattet.",
                "",
            ]
        elif down_area is not None and not down_area.get(
            CONF_AREA_SUN_PROTECT_ENABLED
        ):
            has_own = any(
                str(shutter.get(sun_condition_keys(slot)[0]) or "").strip()
                for slot in SUN_CONDITION_SLOTS
            )
            if has_own or shutter.get(CONF_SUN_GEOMETRY_OVERRIDE):
                out += [
                    "> ⚠️ Hier sind eigene Beschattungs-Einstellungen hinterlegt, "
                    f"aber im Bereich „{down_area.get(CONF_AREA_NAME) or down_id}\" "
                    "ist der Sonnenschutz **aus**. Damit greift keine davon.",
                    "",
                ]

        out += _settings_table(shutter)
        out += _silent_setting_notes(shutter)

        if down_area is not None and down_area.get(CONF_AREA_SUN_PROTECT_ENABLED):
            if not is_system_enabled(hass, entry):
                blocked = "Der Hauptschalter"
            elif not is_auto_enabled(hass, entry, down_area):
                blocked = (
                    f"Die Automatik des Bereichs "
                    f"„{down_area.get(CONF_AREA_NAME) or down_id}\""
                )
            elif not is_shutter_automation_enabled(hass, entry, shutter):
                blocked = "Die Automatik dieses Rollladens"
            else:
                blocked = ""
            out += [
                "Beschattungs-Prüfung mit den Werten von jetzt:",
                "",
                *_shading_verdict(
                    hass, down_area, shutter, data, elev, azim, blocked,
                    fresh_runtime,
                ),
            ]

    out += [
        "### Laufender Zustand",
        "",
        "| Merker | Wert |",
        "| --- | --- |",
        f"| beschattete Rollläden | {_fmt(sorted(data.get('sun_protect_covers', set())))} |",
        f"| heute schon hochgefahren | {_fmt(sorted(data.get('covers_driven_up', set())))} |",
        f"| heute schon runtergefahren | {_fmt(sorted(data.get('covers_driven_down', set())))} |",
        f"| wartende Nachhol-Fahrten | {_fmt(sorted(data.get('drive_after_close_pending', {})))} |",
        f"| Minuten-Ticker läuft | {_fmt(bool(data.get('_minute_ticker_unsub')))} |",
        "| zuletzt geladen | "
        + ("–" if age_minutes is None else f"vor {age_minutes:.0f} min")
        + " |",
        "",
    ]
    if fresh_runtime:
        out += [
            "> ℹ️ Die Integration wurde gerade neu geladen – jedes Speichern im "
            "Panel tut das. Die Merker oben fangen danach wieder bei null an "
            "und füllen sich im Lauf des Tages. Leere Zeilen sind hier also "
            "kein Befund.",
            "",
        ]

    return {
        "markdown": "\n".join(out),
        "options": {"areas": areas, "shutters": shutters, "settings": globals_},
    }
