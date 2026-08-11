"""Was eine Markise nicht mitmacht.

Sie steht in derselben Liste wie die Rollläden, damit Fahrtkontrolle,
Positionsspeicher, Mindestabstand und der Doppel-Riegel ohne Zutun weiter
gelten. Genau deshalb muss festgeschrieben sein, welche Fahrwege sie *nicht*
anfassen dürfen – sonst führe sie um 07:00 aus und um 19:00 ein.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    DOMAIN,
    KIND_AWNING,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from custom_components.shutter_pilot.helpers import (
    filter_shutters_by_area,
    is_awning,
    only_awnings,
    only_shutters,
)
from custom_components.shutter_pilot.window_helper import get_effective_close_position

AWNING = "cover.markise_terrasse"
SHUTTER = "cover.wohnzimmer"
WINDOW = "binary_sensor.terrassentuer"


@pytest.fixture(autouse=True)
def _fast_startup_restore(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


def _awning(**extra):
    return {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise Terrasse",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_AREA_DOWN_ID: "terrasse",
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
        **extra,
    }


def _shutter(**extra):
    return {
        CONF_COVER_ENTITY_ID: SHUTTER,
        CONF_NAME: "Wohnzimmer",
        CONF_AREA_UP_ID: "terrasse",
        CONF_AREA_DOWN_ID: "terrasse",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: 50,
        **extra,
    }


# --- Die Unterscheidung selbst ----------------------------------------------


class TestKind:
    def test_a_missing_key_is_a_shutter(self):
        """Kein Bestand muss migriert werden."""
        assert is_awning({CONF_COVER_ENTITY_ID: SHUTTER}) is False

    def test_the_awning_key_is_recognised(self):
        assert is_awning(_awning()) is True

    def test_the_two_lists_are_complementary(self):
        both = [_shutter(), _awning()]
        assert only_shutters(both) == [_shutter()]
        assert only_awnings(both) == [_awning()]


# --- Der Zeitplan ------------------------------------------------------------


class TestSchedule:
    def test_the_schedule_filter_leaves_awnings_out(self):
        both = [_shutter(), _awning(**{CONF_AREA_UP_ID: "terrasse"})]

        picked = filter_shutters_by_area(
            both, "terrasse", use_up=False, include_awnings=False
        )

        assert [s[CONF_COVER_ENTITY_ID] for s in picked] == [SHUTTER]

    def test_but_the_group_services_keep_them(self):
        """`close_group` an einer Markise heisst „einfahren" – ein Knopfdruck."""
        both = [_shutter(), _awning()]

        picked = filter_shutters_by_area(both, "terrasse", use_up=False)

        assert len(picked) == 2

    async def test_the_schedule_does_not_touch_the_awning(self, hass, cover_calls):
        """Gegenprobe zum Filter durch den echten Scheduler.

        Beide Uhrzeiten liegen in der Vergangenheit und werden beim Setup als
        erledigt vorgemerkt – genau dieser Merker wird geleert, dann faehrt der
        naechste Takt Hoch *und* Runter.
        """
        _entry, data = await _setup(
            hass,
            [_shutter(), _awning(**{CONF_AREA_UP_ID: "terrasse"})],
        )
        data["_scheduler_fired"].clear()

        await _tick(hass, data)

        driven = {c.data["entity_id"] for c in cover_calls}
        assert SHUTTER in driven, "der Rollladen faehrt wie bisher"
        assert AWNING not in driven


# --- Aussperrschutz ----------------------------------------------------------


class TestLockProtection:
    """Der Deckel klemmt nach unten – an einer Markise die falsche Richtung."""

    def test_a_shutter_is_capped_as_before(self, hass):
        hass.states.async_set(WINDOW, "on")
        shutter = _shutter(
            **{
                CONF_WINDOW_ENTITY_ID: WINDOW,
                CONF_WINDOW_OPEN_STATE: "on",
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 20,
            }
        )

        assert get_effective_close_position(hass, shutter, 0) == 20

    def test_an_awning_is_never_capped(self, hass):
        """Sonst bliebe eine umgestellte Markise bei 20 % im Sturm stehen."""
        hass.states.async_set(WINDOW, "on")
        awning = _awning(
            **{
                CONF_WINDOW_ENTITY_ID: WINDOW,
                CONF_WINDOW_OPEN_STATE: "on",
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 20,
            }
        )

        assert get_effective_close_position(hass, awning, 0) == 0


# --- Rollen ------------------------------------------------------------------


class TestRoles:
    def test_the_rest_position_defaults_to_retracted(self):
        """Ein Rollladen faellt auf 100 zurueck, eine Markise auf 0."""
        from custom_components.shutter_pilot.helpers import get_position_for_role

        assert get_position_for_role({CONF_COVER_ENTITY_ID: SHUTTER}, ROLE_OPEN) == 100
        assert (
            get_position_for_role(
                {CONF_COVER_ENTITY_ID: AWNING, CONF_DEVICE_KIND: KIND_AWNING},
                ROLE_OPEN,
            )
            == 0
        )

    def test_a_stored_value_still_wins(self):
        from custom_components.shutter_pilot.helpers import get_position_for_role

        assert get_position_for_role(_awning(**{CONF_POSITION_OPEN: 5}), ROLE_OPEN) == 5

    def test_closing_an_awning_means_retracting_it(self):
        from custom_components.shutter_pilot.helpers import get_position_for_role

        assert get_position_for_role(_awning(), ROLE_CLOSED) == 0


# --- Hilfen ------------------------------------------------------------------


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        hass.states.async_set(
            call.data["entity_id"],
            "closed" if position <= 0 else "open",
            {"current_position": position, "supported_features": 15},
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


async def _setup(hass, shutters):
    for cover in (AWNING, SHUTTER):
        hass.states.async_set(
            cover, "open", {"current_position": 100, "supported_features": 15}
        )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 20.0, "azimuth": 200.0},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [
                {
                    CONF_AREA_ID: "terrasse",
                    CONF_AREA_NAME: "Terrasse",
                    CONF_AREA_MODE: AREA_MODE_TIME,
                    # Beide in der Vergangenheit, damit ein geleerter Merker
                    # im selben Takt Hoch und Runter ausloest.
                    CONF_AREA_TIME_UP: "00:01",
                    CONF_AREA_TIME_DOWN: "00:02",
                    CONF_AREA_DRIVE_DELAY: 0,
                }
            ],
            CONF_SHUTTERS: shutters,
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _tick(hass, data, count: int = 2) -> None:
    """Den gemeinsamen Minutentakt ausloesen, wie Home Assistant es tut."""
    from homeassistant.util import dt as dt_util

    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()
