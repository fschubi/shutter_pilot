"""Nachhol-Fahrten überstehen den Neustart.

Stand die Schließzeit an, während das Fenster noch offen war, merkt sich
Shutter Pilot die Fahrt und holt sie nach, sobald das Fenster zugeht. Dieser
Merker lag nur im Arbeitsspeicher – ein Neustart dazwischen liess die Fahrt
lautlos verschwinden.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import (
    PENDING_MAX_AGE_HOURS,
    forget_drive_after_close,
    remember_drive_after_close,
    restore_drive_after_close,
)
from custom_components.shutter_pilot.position_store import get_position_store

COVER = "cover.living_room"
SHUTTER = {CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Wohnzimmer"}


@pytest.fixture
async def entry(hass):
    config_entry = MockConfigEntry(
        domain=DOMAIN, title="SP", options={CONF_SHUTTERS: [SHUTTER]}
    )
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "shutters": [SHUTTER],
        "drive_after_close_pending": {},
    }
    store = get_position_store(hass, config_entry.entry_id)
    await store.async_load()
    return config_entry


def _data(hass, entry) -> dict:
    return hass.data[DOMAIN][entry.entry_id]


class TestPersistence:
    async def test_a_pending_drive_survives_a_restart(self, hass, entry):
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()

        # Neustart: der Arbeitsspeicher ist leer, die Platte nicht.
        data["drive_after_close_pending"] = {}
        await restore_drive_after_close(hass, entry, data)

        pending = data["drive_after_close_pending"][COVER]
        assert pending["position"] == 0
        assert pending["reason"] == "Schedule down"

    async def test_the_shutter_config_comes_from_the_options(self, hass, entry):
        """Nicht die Kopie von der Platte – die wäre inzwischen veraltet."""
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter={"alt": True},
        )
        await hass.async_block_till_done()
        data["drive_after_close_pending"] = {}

        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"][COVER]["shutter"] is SHUTTER

    async def test_executing_it_clears_the_disk_copy(self, hass, entry):
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()

        forget_drive_after_close(hass, entry, data, COVER)
        await hass.async_block_till_done()

        data["drive_after_close_pending"] = {}
        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"] == {}, "nicht wieder auferstanden"

    async def test_a_removed_shutter_is_dropped(self, hass, entry):
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, "cover.weg",
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()
        data["drive_after_close_pending"] = {}

        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"] == {}


class TestStaleEntries:
    async def test_an_old_entry_is_discarded(self, hass, entry):
        """Eine Fahrt von vorgestern sagt nichts mehr darüber, was jetzt gilt."""
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()

        store = get_position_store(hass, entry.entry_id)
        old = datetime.now().astimezone() - timedelta(hours=PENDING_MAX_AGE_HOURS + 1)
        store._pending[COVER]["saved"] = old.isoformat()

        data["drive_after_close_pending"] = {}
        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"] == {}

    async def test_a_fresh_entry_is_kept(self, hass, entry):
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()

        store = get_position_store(hass, entry.entry_id)
        recent = datetime.now().astimezone() - timedelta(hours=1)
        store._pending[COVER]["saved"] = recent.isoformat()

        data["drive_after_close_pending"] = {}
        await restore_drive_after_close(hass, entry, data)
        assert COVER in data["drive_after_close_pending"]

    async def test_a_broken_timestamp_is_discarded(self, hass, entry):
        data = _data(hass, entry)
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down", shutter=SHUTTER,
        )
        await hass.async_block_till_done()

        store = get_position_store(hass, entry.entry_id)
        store._pending[COVER]["saved"] = "kaputt"

        data["drive_after_close_pending"] = {}
        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"] == {}

    async def test_nothing_stored_is_not_an_error(self, hass, entry):
        data = _data(hass, entry)
        await restore_drive_after_close(hass, entry, data)
        assert data["drive_after_close_pending"] == {}
