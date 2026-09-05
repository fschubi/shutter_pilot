"""Tests for the area_triggers block in the get_status WebSocket payload.

Xerenas reported the dashboard showing "up at 06:07" while "up no earlier than
07:30" was configured. The panel cannot compute the real time itself, so the
backend hands it over – these tests pin that contract down.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from unittest.mock import patch

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from zoneinfo import ZoneInfo

from custom_components.shutter_pilot.const import (
    AREA_MODE_SUN,
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_EARLIEST_UP,
    CONF_AREA_SUN_LATEST_DOWN,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)


def _berlin_offset():
    """Berlin's UTC offset today – 1 h in winter, 2 h in summer."""
    return datetime.now(tz=ZoneInfo("Europe/Berlin")).utcoffset()


def _sun_attrs(today: date) -> dict:
    """Sunrise 06:07 and sunset 21:10 Berlin – the times from the forum post.

    Anchored to the current day rather than a fixed date: the triggers are
    always computed for "today", and freezing the clock would invalidate the
    WebSocket auth token.
    """
    berlin = ZoneInfo("Europe/Berlin")
    rising = datetime.combine(today, time(6, 7), tzinfo=berlin)
    setting = datetime.combine(today, time(21, 10), tzinfo=berlin)
    return {
        "elevation": 30.0,
        "azimuth": 180.0,
        "next_rising": rising.astimezone(UTC).isoformat(),
        "next_setting": setting.astimezone(UTC).isoformat(),
    }


def _options(*areas) -> dict:
    return {
        CONF_AREAS: list(areas),
        CONF_SHUTTERS: [
            {
                CONF_COVER_ENTITY_ID: "cover.living_room",
                CONF_NAME: "Wohnzimmer",
                CONF_AREA_UP_ID: "sunny",
                CONF_AREA_DOWN_ID: "sunny",
            }
        ],
    }


SUN_AREA = {
    CONF_AREA_ID: "sunny",
    CONF_AREA_NAME: "Schlafbereich",
    CONF_AREA_MODE: AREA_MODE_SUN,
    CONF_AREA_DRIVE_DELAY: 0,
    CONF_AREA_SUN_EARLIEST_UP: "07:30",
}

TIME_AREA = {
    CONF_AREA_ID: "clocked",
    CONF_AREA_NAME: "Flur",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


async def _status(hass, hass_ws_client, options, with_sun=True) -> dict:
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.states.async_set(
        "cover.living_room", "open", {"current_position": 100, "supported_features": 15}
    )
    if with_sun:
        hass.states.async_set("sun.sun", "above_horizon", _sun_attrs(dt_util.now().date()))
    config_entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=options)
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "shutter_pilot/get_status"})
    response = await client.receive_json()
    assert response["success"]
    return response["result"]


class TestAreaTriggers:
    async def test_bound_time_wins_over_raw_sunrise(self, hass, hass_ws_client):
        """The reported case: 07:30 must be sent, not the 06:07 sunrise."""
        result = await _status(hass, hass_ws_client, _options(SUN_AREA))
        trigger = result["area_triggers"]["sunny"]
        assert trigger["up"].startswith(f"{dt_util.now().date().isoformat()}T07:30:00")
        # Local offset, not UTC – that mix-up was the whole bug.
        assert datetime.fromisoformat(trigger["up"]).utcoffset() == _berlin_offset()
        assert trigger["up_bound"] == "earliest"
        assert trigger["up_bound_time"] == "07:30"

    async def test_unclamped_direction_reports_no_bound(self, hass, hass_ws_client):
        result = await _status(hass, hass_ws_client, _options(SUN_AREA))
        trigger = result["area_triggers"]["sunny"]
        assert trigger["down"].startswith(f"{dt_util.now().date().isoformat()}T21:10:00")
        assert trigger["down_bound"] is None
        assert trigger["down_bound_time"] is None

    async def test_latest_bound_is_reported(self, hass, hass_ws_client):
        area = {**SUN_AREA, CONF_AREA_SUN_LATEST_DOWN: "20:00"}
        result = await _status(hass, hass_ws_client, _options(area))
        trigger = result["area_triggers"]["sunny"]
        assert trigger["down"].startswith(f"{dt_util.now().date().isoformat()}T20:00:00")
        assert trigger["down_bound"] == "latest"
        assert trigger["down_bound_time"] == "20:00"

    async def test_non_sun_areas_are_left_out(self, hass, hass_ws_client):
        result = await _status(hass, hass_ws_client, _options(SUN_AREA, TIME_AREA))
        assert "sunny" in result["area_triggers"]
        assert "clocked" not in result["area_triggers"]

    async def test_without_sun_entity_the_rest_still_arrives(
        self, hass, hass_ws_client
    ):
        """The panel falls back to its own display – but must get everything else."""
        result = await _status(
            hass, hass_ws_client, _options(SUN_AREA), with_sun=False
        )
        assert result["area_triggers"] == {}
        assert len(result["areas"]) == 1
        assert len(result["shutters"]) == 1
        assert result["master_enabled"] is True
        assert "version" in result


class TestSettingsSurviveTheRoundTrip:
    """bjoerg und charly166: die Markisen-Einstellungen standen wieder leer da.

    `save_settings` schreibt alles, was das Panel schickt – aber `get_status`
    schickte nur sechs fest verdrahtete Schluessel zurueck. Gespeichert und
    angewendet waren die Werte also, sichtbar nie; wer eine Windschwelle
    korrigieren wollte, musste raten, was drinstand.

    Deshalb jetzt eine Ausschlussliste. Eine Erlaubnisliste gilt immer nur
    fuer die Felder, an die jemand gedacht hat – derselbe Vertrag, an dem der
    Elevations-Haken zwei Versionen lang wirkungslos hing.
    """

    GUARD = {
        "sun_cond_wind_entity": "sensor.wind",
        "sun_cond_wind_on_above": 25,
        "sun_cond_wind_off_below": 15,
        "guard_wind_lockout": 20,
        "sun_cond_rain_entity": "binary_sensor.regen",
        "guard_rain_lockout": 30,
        "sun_cond_ice_entity": "sensor.aussen",
        "sun_cond_ice_on_above": -2,
        "awning_sensor_grace": 10,
    }

    async def test_the_awning_protection_comes_back(self, hass, hass_ws_client):
        result = await _status(
            hass, hass_ws_client, {**_options(TIME_AREA), **self.GUARD}
        )

        for key, value in self.GUARD.items():
            assert result["settings"].get(key) == value, key

    async def test_saving_from_the_panel_survives_the_round_trip(
        self, hass, hass_ws_client
    ):
        """GitHub #9: Entität im Formular gewählt, Speichern gedrückt, Feld
        wieder leer. Gemeldet gegen 2.14.0, vor der Ausschlussliste oben -
        dieser Test fährt den tatsaechlichen Weg des Panels (save_settings,
        dann neu laden per get_status), nicht nur eine vorher gesetzte
        Option, um den gemeldeten Ablauf woertlich nachzustellen."""
        result = await _status(hass, hass_ws_client, _options(TIME_AREA))

        client = await hass_ws_client(hass)
        await client.send_json({
            "id": 2,
            "type": "shutter_pilot/save_settings",
            "settings": self.GUARD,
        })
        save_response = await client.receive_json()
        assert save_response["success"]
        await hass.async_block_till_done()

        await client.send_json({"id": 3, "type": "shutter_pilot/get_status"})
        reload_response = await client.receive_json()
        assert reload_response["success"]

        settings = reload_response["result"]["settings"]
        for key, value in self.GUARD.items():
            assert settings.get(key) == value, (
                f"{key} kam nach dem Speichern nicht zurueck - "
                "genau das gemeldete Symptom"
            )

    async def test_the_known_defaults_are_still_filled_in(self, hass, hass_ws_client):
        """Ein frisch eingerichtetes System hat nichts davon gespeichert."""
        result = await _status(hass, hass_ws_client, _options(TIME_AREA))

        assert result["settings"]["verify_enabled"] is False
        assert result["settings"]["min_drive_gap"] == 0.0

    async def test_areas_and_shutters_stay_out_of_settings(self, hass, hass_ws_client):
        """Sie haben eigene Felder – doppelt waere nur mehr zu uebertragen."""
        result = await _status(hass, hass_ws_client, _options(TIME_AREA))

        assert CONF_AREAS not in result["settings"]
        assert CONF_SHUTTERS not in result["settings"]
