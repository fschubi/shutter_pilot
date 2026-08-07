"""Globaler Mindestabstand zwischen Fahrbefehlen (Wunsch von Linos).

Bei Funk (433 MHz, HmIP) verschlucken die Empfänger Befehle, die gleichzeitig
ankommen. Die Verzögerung je Bereich hilft dort nicht: jeder Bereich fährt in
einem eigenen Task, zwei Bereiche feuern also weiterhin im selben Moment.

Gedrosselt wird deshalb in `set_cover_position()` – der einen Stelle, durch die
jede Fahrt läuft, automatisch wie manuell.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import helpers
from custom_components.shutter_pilot.const import (
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_MIN_DRIVE_GAP,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
    MAX_MIN_DRIVE_GAP,
)

COVERS = ["cover.a", "cover.b", "cover.c"]


@pytest.fixture
def drive_log(hass):
    """Zeitstempel und Reihenfolge jeder Fahrt."""
    log: list[tuple[str, float]] = []

    async def _handler(call):
        log.append((call.data["entity_id"], time.monotonic()))

    hass.services.async_register("cover", "set_cover_position", _handler)
    return log


async def _entry(hass, **options) -> MockConfigEntry:
    for cover in COVERS:
        hass.states.async_set(
            cover, "open", {"current_position": 100, "supported_features": 15}
        )
    opts = {
        CONF_AREAS: [],
        CONF_SHUTTERS: [
            {CONF_COVER_ENTITY_ID: c, CONF_NAME: c} for c in COVERS
        ],
    }
    opts.update(options)
    config_entry = MockConfigEntry(domain=DOMAIN, title="SP", options=opts)
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "shutters": opts[CONF_SHUTTERS],
        "last_positions": {},
        "pending_automation_covers": set(),
        "recent_automation_covers": {},
    }
    return config_entry


async def _drive_all(hass, entry) -> None:
    """Drei Fahrbefehle gleichzeitig absetzen, wie zwei Bereiche es täten."""
    await asyncio.gather(
        *(
            helpers.set_cover_position(hass, entry, cover, 50, "test")
            for cover in COVERS
        )
    )


class TestThrottle:
    async def test_off_by_default_nothing_is_delayed(self, hass, drive_log):
        entry = await _entry(hass)
        started = time.monotonic()
        await _drive_all(hass, entry)
        assert len(drive_log) == 3
        assert time.monotonic() - started < 0.2, "kein Warten ohne Einstellung"

    async def test_commands_are_spaced_out(self, hass, drive_log):
        entry = await _entry(hass, **{CONF_MIN_DRIVE_GAP: 0.15})
        await _drive_all(hass, entry)

        assert len(drive_log) == 3, "keiner verschluckt"
        stamps = [t for _cover, t in drive_log]
        gaps = [b - a for a, b in zip(stamps, stamps[1:])]
        assert all(g >= 0.13 for g in gaps), f"zu dicht: {gaps}"

    async def test_every_shutter_still_gets_its_command(self, hass, drive_log):
        """Drosseln heisst warten, nicht weglassen."""
        entry = await _entry(hass, **{CONF_MIN_DRIVE_GAP: 0.05})
        await _drive_all(hass, entry)
        assert sorted(c for c, _t in drive_log) == sorted(COVERS)

    async def test_a_later_drive_is_not_held_back(self, hass, drive_log):
        """Nach einer Pause muss die nächste Fahrt sofort raus."""
        entry = await _entry(hass, **{CONF_MIN_DRIVE_GAP: 0.1})
        await helpers.set_cover_position(hass, entry, COVERS[0], 50, "erste")
        await asyncio.sleep(0.15)

        started = time.monotonic()
        await helpers.set_cover_position(hass, entry, COVERS[1], 50, "zweite")
        assert time.monotonic() - started < 0.05


class TestConfiguration:
    @pytest.mark.parametrize("value", [0, "0", None, "", "abc", -5])
    async def test_values_that_mean_off(self, hass, drive_log, value):
        entry = await _entry(hass, **{CONF_MIN_DRIVE_GAP: value})
        started = time.monotonic()
        await _drive_all(hass, entry)
        assert time.monotonic() - started < 0.2
        assert len(drive_log) == 3

    async def test_absurd_value_is_capped(self, hass, drive_log):
        """Ein Tippfehler darf die Integration nicht zum Stehen bringen."""
        entry = await _entry(hass, **{CONF_MIN_DRIVE_GAP: 9999})
        gap_seen = []

        real_sleep = asyncio.sleep

        async def _record(seconds, *args, **kwargs):
            gap_seen.append(seconds)
            return await real_sleep(0)

        with patch.object(asyncio, "sleep", _record):
            await _drive_all(hass, entry)

        assert gap_seen, "es wurde überhaupt gedrosselt"
        assert max(gap_seen) <= MAX_MIN_DRIVE_GAP
