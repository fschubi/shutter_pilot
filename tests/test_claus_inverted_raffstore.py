"""Von Hand ganz hochgefahren gilt nicht als "zu" (Claus, simon42 #217).

Seine Essen-Schiebetuer: auf = 0 % (Lamellen 100), zu = 15 % (Lamellen 60) -
auf und zu unterscheiden sich fast nur durch die Lamellen. `manual_position_is_
a_close()` kennt ein "jenseits von zu": bei open < closed gilt jede Position
ab closed - 8 als zu, also 7 bis 100 %. Das von Hand ganz hochgefahrene 96 %
war damit "zu", der Unten-Merker blieb stehen (der Zweig, der bei einer
Zwischenposition den Merker loescht, kam nie dran), und die Daemmerung um 17:21
fuhr nicht zu."""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
)
from custom_components.shutter_pilot.helpers import (
    manual_position_is_a_close,
    note_manual_position,
)

COVER = "cover.essen_schiebetuer"


def _shutter(open_pos: float, closed: float) -> dict:
    return {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_POSITION_OPEN: open_pos,
        CONF_POSITION_CLOSED: closed,
    }


class TestAnAlmostSamePositionHasNoClosingDirection:
    def test_fully_raised_is_not_a_close_with_open_0_closed_15(self):
        assert manual_position_is_a_close(_shutter(0, 15), 96) is False

    def test_the_closed_position_itself_still_is(self):
        assert manual_position_is_a_close(_shutter(0, 15), 15) is True
        assert manual_position_is_a_close(_shutter(0, 15), 10) is True

    def test_the_hand_lift_clears_the_down_marker(self):
        data = {"covers_driven_up": set(), "covers_driven_down": {COVER}}
        note_manual_position(data, _shutter(0, 15), 96)
        assert COVER not in data["covers_driven_down"]
        assert COVER not in data["covers_driven_up"]

    def test_identical_positions_have_no_beyond_either(self):
        """Florian: auf und zu sind dieselbe Position, nur die Lamellen."""
        assert manual_position_is_a_close(_shutter(0, 0), 60) is False


class TestOrdinaryShuttersKeepTheirBeyond:
    """Bestandsschutz: wo auf und zu weit auseinander liegen, bleibt es."""

    def test_closing_all_the_way_past_a_36_percent_close_is_a_close(self):
        assert manual_position_is_a_close(_shutter(100, 36), 0) is True

    def test_a_normal_shutter_closed_at_zero(self):
        assert manual_position_is_a_close(_shutter(100, 0), 5) is True
        assert manual_position_is_a_close(_shutter(100, 0), 60) is False

    def test_the_inverted_numbering_with_a_far_apart_close(self):
        """0 = oben, 70 = zu: weiter nach unten (100) ist weiter zu."""
        assert manual_position_is_a_close(_shutter(0, 70), 100) is True
        assert manual_position_is_a_close(_shutter(0, 70), 30) is False

    def test_diele_100_open_70_closed_is_unchanged(self):
        """Dreissig Prozent Abstand: die Regel greift weiter."""
        assert manual_position_is_a_close(_shutter(100, 70), 50) is True
        assert manual_position_is_a_close(_shutter(100, 70), 98) is False


async def test_the_export_shows_phase_and_hand_ages(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.shutter_pilot.const import CONF_AREAS, CONF_SHUTTERS, DOMAIN
    from custom_components.shutter_pilot.export import async_build_export
    import time

    entry = MockConfigEntry(
        domain=DOMAIN,
        options={CONF_AREAS: [], CONF_SHUTTERS: [_shutter(0, 15)]},
    )
    entry.add_to_hass(hass)
    data = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id, {"master_enabled": True}
    )
    now = time.monotonic()
    data["_b_cond_since"] = {"down_essen": now - 600}
    data["_hand_moved_at"] = {COVER: now - 120}

    md = (await async_build_export(hass, entry))["markdown"]

    assert "| Helligkeits-Phase seit | down_essen: vor 10 min |" in md
    assert f"| zuletzt von Hand bewegt | {COVER}: vor 2 min |" in md
