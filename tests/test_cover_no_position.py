"""Antriebe, die keine Position kennen.

Viele Markisenmotoren – und etliche aeltere Rollladenantriebe – koennen nur
auf, stop und zu. `cover.set_cover_position` wirft dort, und seit 2.8.0 wird
eine gescheiterte Fahrt jede Minute wiederholt: aus einem stummen Fehler waere
also eine Endlosschleife geworden.

Die Tilt-Fahrt prueft ihr Feature-Bit seit jeher, die Positionsfahrt nie.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import DOMAIN
from custom_components.shutter_pilot.helpers import set_cover_position

COVER = "cover.markise_ohne_position"

# CoverEntityFeature: OPEN=1, CLOSE=2, SET_POSITION=4, STOP=8
FEATURES_WITH_POSITION = 1 | 2 | 4 | 8
FEATURES_WITHOUT_POSITION = 1 | 2 | 8


@pytest.fixture
def entry(hass):
    config_entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options={})
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {}
    return config_entry


@pytest.fixture
def calls(hass):
    """Alle drei Dienste mitschreiben, damit sichtbar wird, welcher lief."""
    seen: list[tuple[str, dict]] = []

    async def _record(call):
        seen.append((call.service, dict(call.data)))

    for service in ("set_cover_position", "open_cover", "close_cover"):
        hass.services.async_register("cover", service, _record)
    return seen


class TestFallback:
    async def test_a_normal_cover_is_positioned(self, hass, entry, calls):
        hass.states.async_set(
            COVER, "open", {"supported_features": FEATURES_WITH_POSITION}
        )

        assert await set_cover_position(hass, entry, COVER, 45, "Test")

        assert calls[0][0] == "set_cover_position"
        assert calls[0][1]["position"] == 45

    async def test_full_extension_becomes_open_cover(self, hass, entry, calls):
        hass.states.async_set(
            COVER, "closed", {"supported_features": FEATURES_WITHOUT_POSITION}
        )

        assert await set_cover_position(hass, entry, COVER, 100, "Test")

        assert [c[0] for c in calls] == ["open_cover"]

    async def test_retracting_becomes_close_cover(self, hass, entry, calls):
        hass.states.async_set(
            COVER, "open", {"supported_features": FEATURES_WITHOUT_POSITION}
        )

        assert await set_cover_position(hass, entry, COVER, 0, "Test")

        assert [c[0] for c in calls] == ["close_cover"]

    async def test_a_partial_target_still_drives_and_warns(
        self, hass, entry, calls, caplog
    ):
        """Halb ausfahren kann der Antrieb nicht – stehenbleiben ist schlechter."""
        hass.states.async_set(
            COVER, "closed", {"supported_features": FEATURES_WITHOUT_POSITION}
        )

        assert await set_cover_position(hass, entry, COVER, 60, "Test")

        assert [c[0] for c in calls] == ["open_cover"]
        assert "cannot be positioned" in caplog.text

    async def test_an_unknown_cover_is_positioned_as_before(
        self, hass, entry, calls
    ):
        """Ohne lesbares Feature-Bit bleibt es beim bisherigen Verhalten."""
        hass.states.async_set(COVER, "open", {})

        assert await set_cover_position(hass, entry, COVER, 30, "Test")

        assert calls[0][0] == "set_cover_position"


class TestUrgent:
    async def test_the_drive_gap_is_skipped_when_urgent(
        self, hass, entry, calls, monkeypatch
    ):
        """Vier Markisen mal zehn Sekunden waeren eine halbe Minute im Sturm."""
        hass.states.async_set(
            COVER, "open", {"supported_features": FEATURES_WITH_POSITION}
        )
        waited = []

        async def _gap(*_a, **_kw):
            waited.append(True)

        monkeypatch.setattr(
            "custom_components.shutter_pilot.helpers._respect_min_drive_gap", _gap
        )

        await set_cover_position(hass, entry, COVER, 0, "Storm", urgent=True)
        assert waited == []

        await set_cover_position(hass, entry, COVER, 0, "Normal")
        assert waited == [True]
