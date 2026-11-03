"""Beschattungspause nach einer Handfahrt (simon42 #229 Claus).

Die Sonne blendet trotz Beschattung, er dreht die Lamellen selbst - das soll
bis zum Ende der Sonnenphase so bleiben und nicht bei der naechsten
Neuberechnung ueberschrieben werden. Opt-in je Bereich."""

from __future__ import annotations

import time

import pytest

from custom_components.shutter_pilot.const import (
    CONF_AREA_SHADE_PAUSE_MAX,
    CONF_AREA_SHADE_PAUSE_ON_HAND,
)

from test_shade_levels import (  # noqa: F401  (Fixtures und Helfer)
    COVER,
    L1,
    SHUTTER,
    _area,
    _fast,
    _flags,
    _positions,
    _setup,
    _ticks,
    calls,
)


def _sun(hass, elevation: float) -> None:
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": elevation,
            "azimuth": 198.0,
            "next_rising": "2026-08-29T04:00:00+00:00",
            "next_setting": "2026-08-28T19:00:00+00:00",
        },
    )


def _hand_move(data) -> None:
    data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic() + 1.0


async def _shaded_then_hand_moved(hass, calls, **area_extra):
    entry, data = await _setup(hass, area=_area(**area_extra))
    await _ticks(hass, data)
    assert _positions(calls)[-1] == 50
    calls["pos"].clear()
    _hand_move(data)
    return data


class TestPauseAfterHandMove:
    async def test_without_the_setting_nothing_changes(self, hass, calls):
        data = await _shaded_then_hand_moved(hass, calls)
        _flags(hass, l1="on")
        await _ticks(hass, data)
        assert _positions(calls) == [40]

    async def test_a_hand_move_pauses_the_shading(self, hass, calls):
        data = await _shaded_then_hand_moved(
            hass, calls, **{CONF_AREA_SHADE_PAUSE_ON_HAND: True}
        )
        _flags(hass, l1="on")
        await _ticks(hass, data)
        assert _positions(calls) == []
        assert COVER in data["_shade_paused"]

    async def test_a_move_before_the_phase_does_not_pause(self, hass, calls):
        """Eine alte Handfahrt von heute frueh darf die Beschattung nicht sperren."""
        entry, data = await _setup(
            hass, area=_area(**{CONF_AREA_SHADE_PAUSE_ON_HAND: True})
        )
        data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic() - 3600
        await _ticks(hass, data)
        _flags(hass, l1="on")
        await _ticks(hass, data)
        assert _positions(calls)[-1] == 40

    async def test_the_pause_ends_when_the_sun_leaves(self, hass, calls):
        data = await _shaded_then_hand_moved(
            hass, calls, **{CONF_AREA_SHADE_PAUSE_ON_HAND: True}
        )
        await _ticks(hass, data)
        assert COVER in data["_shade_paused"]
        _sun(hass, -5.0)
        await _ticks(hass, data)
        assert COVER not in data["_shade_paused"]
        # naechster Tag: die Beschattung greift wieder
        calls["pos"].clear()
        _sun(hass, 41.0)
        await _ticks(hass, data)
        assert _positions(calls) == [50]

    @pytest.mark.parametrize("minutes,expired", [(60, False), (5, True)])
    async def test_the_longest_pause_is_honoured(
        self, hass, calls, minutes, expired
    ):
        data = await _shaded_then_hand_moved(
            hass,
            calls,
            **{
                CONF_AREA_SHADE_PAUSE_ON_HAND: True,
                CONF_AREA_SHADE_PAUSE_MAX: minutes,
            },
        )
        await _ticks(hass, data)
        assert COVER in data["_shade_paused"]
        data["_shade_paused"][COVER] = time.monotonic() - 10 * 60
        _flags(hass, l1="on")
        await _ticks(hass, data)
        assert (_positions(calls) == [40]) is expired

    async def test_a_second_hand_move_restarts_the_clock(self, hass, calls):
        data = await _shaded_then_hand_moved(
            hass,
            calls,
            **{CONF_AREA_SHADE_PAUSE_ON_HAND: True, CONF_AREA_SHADE_PAUSE_MAX: 5},
        )
        await _ticks(hass, data)
        data["_shade_paused"][COVER] = time.monotonic() - 10 * 60
        data["_hand_moved_at"][COVER] = time.monotonic() + 2.0
        _flags(hass, l1="on")
        await _ticks(hass, data)
        assert _positions(calls) == []
