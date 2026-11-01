"""Sichtschutz (Raffstore, Stufe 6, simon42 #172 Claus).

Eine Entitaet (Badbelegung, Licht) stellt den Rollladen auf eigene Position und
Lamellen, solange sie "an" ist. Vorrang vor Morgenfahrt, Beschattung und
Lueften; das Zufahren laeuft weiter. Danach zurueck - ausser eine neuere
Entscheidung (Hand, Abendfahrt) hat den Rollladen schon bewegt. Ohne Entitaet am
Rollladen aendert sich nichts."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_KEEP_POSITION_PRIVACY,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_PRIVACY,
    CONF_POSITION_SUN_PROTECT,
    CONF_PRIVACY_ENTITY,
    CONF_PRIVACY_INVERT,
    CONF_SHUTTERS,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_TILT_PRIVACY,
    DOMAIN,
)

COVER = "cover.bad"
OCC = "binary_sensor.bad_belegt"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Bad",
    CONF_AREA_UP_ID: "bad",
    CONF_AREA_DOWN_ID: "bad",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_POSITION_SUN_PROTECT: 50,
    CONF_PRIVACY_ENTITY: OCC,
    CONF_POSITION_PRIVACY: 30,
}


def _area(**extra) -> dict:
    area = {
        CONF_AREA_ID: "bad",
        CONF_AREA_NAME: "Bad",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
    }
    area.update(extra)
    return area


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def calls(hass):
    pos: list = []
    tilt = async_mock_service(hass, "cover", "set_cover_tilt_position")

    async def _handler(call):
        pos.append(call)
        hass.states.async_set(
            call.data["entity_id"],
            "open",
            {
                "current_position": call.data["position"],
                "current_tilt_position": 50,
                "supported_features": 255,
            },
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return {"pos": pos, "tilt": tilt}


async def _setup(hass, shutter=None, area=None, position=100, occupied="off", sun=41.0):
    hass.states.async_set(OCC, occupied)
    hass.states.async_set(
        COVER,
        "open",
        {
            "current_position": position,
            "current_tilt_position": 50,
            "supported_features": 255,
        },
    )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": sun, "azimuth": 198.0},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [area or _area()],
            CONF_SHUTTERS: [shutter or dict(SHUTTER)],
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _set(hass, state: str) -> None:
    hass.states.async_set(OCC, state)
    await hass.async_block_till_done()


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


async def _morning(hass, data) -> None:
    when = (dt_util.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0
    )
    data["_minute_callbacks"]["scheduler"](when)
    await hass.async_block_till_done()


class TestPrivacyDrive:
    async def test_the_shutter_goes_to_the_privacy_position_and_back(
        self, hass, calls
    ):
        _, data = await _setup(hass)
        await _set(hass, "on")
        assert _positions(calls) == [30]

        await _set(hass, "off")
        assert _positions(calls) == [30, 100]

    async def test_inverted_means_free_is_the_trigger(self, hass, calls):
        shutter = {**SHUTTER, CONF_PRIVACY_INVERT: True}
        _, _ = await _setup(hass, shutter=shutter, occupied="on")
        await _set(hass, "off")
        assert _positions(calls) == [30]

    async def test_without_an_entity_nothing_happens(self, hass, calls):
        """Bestandsschutz."""
        plain = {k: v for k, v in SHUTTER.items() if k != CONF_PRIVACY_ENTITY}
        await _setup(hass, shutter=plain)
        await _set(hass, "on")
        assert calls["pos"] == []

    async def test_an_unavailable_entity_does_not_hold(self, hass, calls):
        await _setup(hass)
        await _set(hass, "unavailable")
        assert calls["pos"] == []

    async def test_slats_follow_and_the_height_can_stay(self, hass, calls):
        shutter = {
            **SHUTTER,
            CONF_TILT_ENABLED: True,
            CONF_TILT_OPEN: 100,
            CONF_TILT_CLOSED: 0,
            CONF_TILT_PRIVACY: 70,
            CONF_KEEP_POSITION_PRIVACY: True,
        }
        await _setup(hass, shutter=shutter)
        await _set(hass, "on")
        assert calls["pos"] == []
        assert [c.data["tilt_position"] for c in calls["tilt"]] == [70]


class TestPrivacyOutranks:
    async def test_the_morning_opening_waits_and_is_caught_up(self, hass, calls):
        _, data = await _setup(hass, position=0)
        await _set(hass, "on")
        calls["pos"].clear()

        await _morning(hass, data)
        assert 100 not in _positions(calls)

        await _set(hass, "off")
        assert _positions(calls)[-1] == 100

    async def test_without_privacy_the_morning_opens_as_always(self, hass, calls):
        _, data = await _setup(hass, position=0)
        await _morning(hass, data)
        assert 100 in _positions(calls)

    async def test_shading_does_not_move_it_during_privacy(self, hass, calls):
        area = _area(
            **{
                CONF_AREA_SUN_PROTECT_ENABLED: True,
                CONF_AREA_ELEVATION_MIN: 0,
                CONF_AREA_ELEVATION_MAX: 90,
                CONF_AREA_AZIMUTH_ENABLED: False,
            }
        )
        _, data = await _setup(hass, area=area, sun=-5.0)
        await _set(hass, "on")
        calls["pos"].clear()
        hass.states.async_set("sun.sun", "above_horizon", {"elevation": 41.0, "azimuth": 198.0})

        for _ in range(2):
            for cb in list(data["_minute_callbacks"].values()):
                cb(dt_util.now())
            await hass.async_block_till_done()

        assert 50 not in _positions(calls)


class TestPrivacyEnd:
    async def test_a_hand_move_in_between_is_not_overridden(self, hass, calls):
        _, data = await _setup(hass)
        await _set(hass, "on")
        calls["pos"].clear()
        data["_hand_moved_at"] = {COVER: 10**12}

        await _set(hass, "off")

        assert calls["pos"] == []

    async def test_a_shutter_that_left_the_privacy_position_stays(self, hass, calls):
        """Die Abendfahrt hat ihn waehrenddessen zugefahren."""
        _, data = await _setup(hass)
        await _set(hass, "on")
        calls["pos"].clear()
        hass.states.async_set(
            COVER,
            "closed",
            {"current_position": 0, "current_tilt_position": 50, "supported_features": 255},
        )
        await hass.async_block_till_done()
        data["_hand_moved_at"] = {}

        await _set(hass, "off")

        assert calls["pos"] == []
