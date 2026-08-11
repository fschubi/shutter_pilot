"""Die Markise an der vorhandenen Beschattung.

Der Kern des Umbaus ist, dass es keinen zweiten Fahrmotor gibt: `elevation.py`
faehrt auf `position_sun_protect` und gibt auf `position_open` frei, und welche
Zahl das ist, entscheidet die Konfiguration. Diese Datei haelt fest, dass das
auch dann gilt, wenn die beiden Zahlen vertauscht sind – und dass der Schutz
davor liegt.

Setup-Muster von `test_sun_protect_areas.py`: echtes `async_setup`, Fahrten
ueber einen abgefangenen `cover.set_cover_position`, Minutentakt von Hand.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    AWNING_GUARD_WIND,
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
    CONF_AREAS,
    CONF_AWNING_TRACK_ENABLED,
    CONF_AWNING_TRACK_HIGH_ELEV,
    CONF_AWNING_TRACK_HIGH_POS,
    CONF_AWNING_TRACK_LOW_ELEV,
    CONF_AWNING_TRACK_LOW_POS,
    CONF_AWNING_TRACK_STEP,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    awning_lockout_key,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    awning_shade_position,
    is_cover_sun_protected,
)

AWNING = "cover.markise_terrasse"
WIND = "sensor.wind"
RADIATION = "sensor.strahlung"


@pytest.fixture(autouse=True)
def _fast_startup_restore(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "terrasse",
        CONF_AREA_NAME: "Terrasse",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: False,
    }
    area.update(overrides)
    return area


def _awning(**overrides) -> dict:
    """Ruhestellung eingefahren, Beschattung ausgefahren – umgekehrt."""
    awning = {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise Terrasse",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_AREA_DOWN_ID: "terrasse",
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
    }
    awning.update(overrides)
    return awning


def _wind(entity=WIND, on_above=30, off_below=15, lockout=0) -> dict:
    keys = sun_condition_keys(AWNING_GUARD_WIND)
    return {
        keys[0]: entity,
        keys[1]: on_above,
        keys[2]: off_below,
        awning_lockout_key(AWNING_GUARD_WIND): lockout,
    }


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        for eid in [call.data["entity_id"]]:
            hass.states.async_set(
                eid,
                "closed" if position <= 0 else "open",
                {"current_position": position, "supported_features": 15},
            )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


def _positions(calls) -> list[int]:
    return [c.data["position"] for c in calls]


async def _setup(hass, options: dict, elevation=41.0):
    hass.states.async_set(
        AWNING, "closed", {"current_position": 0, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": elevation,
            "azimuth": 198.0,
            "next_rising": "2026-08-12T04:00:00+00:00",
            "next_setting": "2026-08-11T19:00:00+00:00",
        },
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=options)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _ticks(hass, data, count: int = 2) -> None:
    from homeassistant.util import dt as dt_util

    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


# --- Ausfahren und Einfahren -------------------------------------------------


class TestShading:
    async def test_the_awning_extends_when_shading_applies(
        self, hass, cover_calls
    ):
        """Dieselbe Maschine, nur andere Zahlen: 0 ist Ruhe, 100 Beschattung."""
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [_awning()],
                **_wind(entity=""),
            },
        )
        await _ticks(hass, data)

        assert 100 in _positions(cover_calls)
        assert is_cover_sun_protected(data, AWNING)

    async def test_it_comes_back_in_when_the_sun_leaves(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [_awning()],
                **_wind(entity=""),
            },
        )
        await _ticks(hass, data)
        cover_calls.clear()

        # Sonne unter den Bereich gesunken: Tag vorbei.
        hass.states.async_set(
            "sun.sun",
            "above_horizon",
            {"elevation": -3.0, "azimuth": 290.0},
        )
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, AWNING)


# --- Der Schutz schlaegt die Beschattung -------------------------------------


class TestGuardBeatsShading:
    async def test_a_barred_awning_does_not_extend(self, hass, cover_calls):
        """Und zwar bevor sie faehrt, nicht durch Einfahren eine Sekunde spaeter."""
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [_awning()],
                **_wind(),
            },
        )
        hass.states.async_set(WIND, "48")
        await _ticks(hass, data)

        assert 100 not in _positions(cover_calls)
        assert not is_cover_sun_protected(data, AWNING)

    async def test_once_the_wind_drops_it_goes_out(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [_awning()],
                **_wind(),
            },
        )
        hass.states.async_set(WIND, "48")
        await _ticks(hass, data)
        cover_calls.clear()

        hass.states.async_set(WIND, "5")
        await _ticks(hass, data)

        assert 100 in _positions(cover_calls)

    async def test_an_extended_awning_is_pulled_in_by_the_guard(
        self, hass, cover_calls
    ):
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [_awning()],
                **_wind(),
            },
        )
        hass.states.async_set(WIND, "6")
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, AWNING)
        cover_calls.clear()

        hass.states.async_set(WIND, "52")
        await hass.async_block_till_done()

        assert 0 in _positions(cover_calls)
        assert not is_cover_sun_protected(data, AWNING)


# --- Ausfahrlaenge nach Sonnenstand ------------------------------------------


class TestSunTracking:
    """Zwei Stuetzpunkte, gerade Linie dazwischen."""

    def test_a_high_sun_needs_the_short_projection(self):
        awning = _awning(
            **{
                CONF_AWNING_TRACK_ENABLED: True,
                CONF_AWNING_TRACK_HIGH_ELEV: 60,
                CONF_AWNING_TRACK_HIGH_POS: 60,
                CONF_AWNING_TRACK_LOW_ELEV: 20,
                CONF_AWNING_TRACK_LOW_POS: 100,
            }
        )
        assert awning_shade_position(awning, 70) == 60

    def test_a_low_sun_needs_the_full_one(self):
        awning = _awning(
            **{
                CONF_AWNING_TRACK_ENABLED: True,
                CONF_AWNING_TRACK_HIGH_ELEV: 60,
                CONF_AWNING_TRACK_HIGH_POS: 60,
                CONF_AWNING_TRACK_LOW_ELEV: 20,
                CONF_AWNING_TRACK_LOW_POS: 100,
            }
        )
        assert awning_shade_position(awning, 12) == 100

    def test_it_interpolates_in_between(self):
        awning = _awning(
            **{
                CONF_AWNING_TRACK_ENABLED: True,
                CONF_AWNING_TRACK_HIGH_ELEV: 60,
                CONF_AWNING_TRACK_HIGH_POS: 60,
                CONF_AWNING_TRACK_LOW_ELEV: 20,
                CONF_AWNING_TRACK_LOW_POS: 100,
            }
        )
        assert awning_shade_position(awning, 40) == 80

    def test_switched_off_it_uses_the_plain_position(self):
        assert awning_shade_position(_awning(), 40) == 100

    def test_without_sun_data_it_uses_the_plain_position(self):
        awning = _awning(**{CONF_AWNING_TRACK_ENABLED: True})
        assert awning_shade_position(awning, None) == 100

    def test_anchors_the_wrong_way_round_fall_back(self):
        """Durch zwei gleiche Punkte laesst sich keine Gerade legen."""
        awning = _awning(
            **{
                CONF_AWNING_TRACK_ENABLED: True,
                CONF_AWNING_TRACK_HIGH_ELEV: 20,
                CONF_AWNING_TRACK_LOW_ELEV: 60,
            }
        )
        assert awning_shade_position(awning, 40) == 100

    async def test_the_awning_follows_the_sinking_sun(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [
                    _awning(
                        **{
                            CONF_AWNING_TRACK_ENABLED: True,
                            CONF_AWNING_TRACK_HIGH_ELEV: 60,
                            CONF_AWNING_TRACK_HIGH_POS: 60,
                            CONF_AWNING_TRACK_LOW_ELEV: 20,
                            CONF_AWNING_TRACK_LOW_POS: 100,
                            CONF_AWNING_TRACK_STEP: 10,
                        }
                    )
                ],
                **_wind(entity=""),
            },
            elevation=60.0,
        )
        await _ticks(hass, data)
        assert 60 in _positions(cover_calls)
        cover_calls.clear()

        # 30° liegt ein Viertel des Weges von 20° nach 60°, also 90 %.
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 30.0, "azimuth": 240.0}
        )
        await _ticks(hass, data)

        assert 90 in _positions(cover_calls)

    async def test_a_small_change_does_not_move_the_motor(
        self, hass, cover_calls
    ):
        """Ohne die Mindestaenderung liefe der Antrieb jede Minute ein paar Prozent."""
        _entry, data = await _setup(
            hass,
            {
                CONF_AREAS: [_area()],
                CONF_SHUTTERS: [
                    _awning(
                        **{
                            CONF_AWNING_TRACK_ENABLED: True,
                            CONF_AWNING_TRACK_HIGH_ELEV: 60,
                            CONF_AWNING_TRACK_HIGH_POS: 60,
                            CONF_AWNING_TRACK_LOW_ELEV: 20,
                            CONF_AWNING_TRACK_LOW_POS: 100,
                            CONF_AWNING_TRACK_STEP: 10,
                        }
                    )
                ],
                **_wind(entity=""),
            },
            elevation=60.0,
        )
        await _ticks(hass, data)
        cover_calls.clear()

        # Zwei Grad tiefer sind zwei Prozent mehr Ausfall.
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 58.0, "azimuth": 200.0}
        )
        await _ticks(hass, data)

        assert cover_calls == []
