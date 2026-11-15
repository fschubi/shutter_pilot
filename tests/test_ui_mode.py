"""Einfache Ansicht / Experten-Ansicht und der gefuehrte Einstieg – der Serverteil.

Der Modus ist reine Anzeige. Geprueft wird deshalb nicht, dass er etwas tut,
sondern dass er nichts kaputt macht: wer schon Rolllaeden hat, bleibt nach dem
Update in der Experten-Ansicht; der Modus kippt nicht von selbst, sobald der
erste Rollladen angelegt wird; und das Umschalten laedt die Integration nicht
neu (ein Neuladen bricht laufende Wartezeiten ab).

Der Sammelbefehl `quick_setup` gehoert zum gefuehrten Einstieg: Bereich und
Rolllaeden in einem Zug, weil save_area und save_shutter nacheinander an dem
Neuladen dazwischen scheitern.
"""

from __future__ import annotations

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.config_flow import DEFAULT_OPTIONS
from custom_components.shutter_pilot.const import (
    AREA_MODE_SUN,
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    CONF_UI_MODE,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    UI_MODE_EXPERT,
    UI_MODE_SIMPLE,
)
from custom_components.shutter_pilot.export import async_build_export
from custom_components.shutter_pilot.helpers import effective_ui_mode

AREA = {
    CONF_AREA_ID: "wohnen",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_DRIVE_DELAY: 0,
    CONF_AREA_TIME_UP: "07:00",
    "sun_protect_enabled": True,
}


def _shutter(cover: str, area_id: str = "wohnen") -> dict:
    return {
        CONF_COVER_ENTITY_ID: cover,
        CONF_NAME: cover,
        CONF_AREA_UP_ID: area_id,
        CONF_AREA_DOWN_ID: area_id,
    }


async def _setup(hass, options: dict) -> MockConfigEntry:
    for cover in ("cover.a", "cover.b", "cover.c"):
        hass.states.async_set(
            cover, "open", {"current_position": 100, "supported_features": 15}
        )
    entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=options)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


_ids = iter(range(1, 10_000))


async def _call(client, msg: dict) -> dict:
    # Die Verbindung verlangt aufsteigende Nummern, auch ueber Tests hinweg.
    await client.send_json({"id": next(_ids), **msg})
    return await client.receive_json()


async def _status_mode(client) -> str:
    response = await _call(client, {"type": "shutter_pilot/get_status"})
    return response["result"]["settings"][CONF_UI_MODE]


class TestEffectiveMode:
    def test_an_install_with_shutters_and_no_key_is_expert(self):
        """Nach dem Update darf bei niemandem das halbe Panel verschwinden."""
        opts = {CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter("cover.a")]}
        assert effective_ui_mode(opts) == UI_MODE_EXPERT

    def test_an_install_without_shutters_and_no_key_is_simple(self):
        assert effective_ui_mode({CONF_AREAS: [AREA], CONF_SHUTTERS: []}) == UI_MODE_SIMPLE
        assert effective_ui_mode({}) == UI_MODE_SIMPLE
        assert effective_ui_mode(None) == UI_MODE_SIMPLE

    def test_a_stored_choice_wins_either_way(self):
        with_shutters = {CONF_SHUTTERS: [_shutter("cover.a")], CONF_UI_MODE: UI_MODE_SIMPLE}
        assert effective_ui_mode(with_shutters) == UI_MODE_SIMPLE
        assert effective_ui_mode({CONF_UI_MODE: UI_MODE_EXPERT}) == UI_MODE_EXPERT

    def test_garbage_in_the_key_is_treated_as_missing(self):
        assert effective_ui_mode({CONF_UI_MODE: "profi"}) == UI_MODE_SIMPLE

    def test_a_fresh_install_starts_simple(self):
        assert DEFAULT_OPTIONS[CONF_UI_MODE] == UI_MODE_SIMPLE


class TestStatusAndSwitch:
    async def test_status_reports_the_effective_mode(self, hass, hass_ws_client):
        await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter("cover.a")]})
        client = await hass_ws_client(hass)
        assert await _status_mode(client) == UI_MODE_EXPERT

    async def test_switching_stores_the_mode_without_a_reload(self, hass, hass_ws_client):
        entry = await _setup(
            hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter("cover.a")]}
        )
        client = await hass_ws_client(hass)
        with patch.object(hass.config_entries, "async_reload") as reload:
            response = await _call(
                client, {"type": "shutter_pilot/set_ui_mode", "mode": UI_MODE_SIMPLE}
            )
            await hass.async_block_till_done()
        assert response["success"] is True
        assert entry.options[CONF_UI_MODE] == UI_MODE_SIMPLE
        reload.assert_not_called()
        assert await _status_mode(client) == UI_MODE_SIMPLE

    async def test_switching_leaves_every_other_option_alone(self, hass, hass_ws_client):
        """Der Modus blendet aus. Er loescht nichts."""
        options = {
            CONF_AREAS: [AREA],
            CONF_SHUTTERS: [{**_shutter("cover.a"), "frost_lock": True}],
            CONF_WEATHER_ENTITY: "weather.home",
        }
        entry = await _setup(hass, options)
        client = await hass_ws_client(hass)
        for mode in (UI_MODE_SIMPLE, UI_MODE_EXPERT):
            await _call(client, {"type": "shutter_pilot/set_ui_mode", "mode": mode})
        rest = {k: v for k, v in entry.options.items() if k != CONF_UI_MODE}
        # Der Bereich traegt nach dem Setup zusaetzlich seine Schalter-Entitaet.
        assert {k: rest[CONF_AREAS][0][k] for k in AREA} == AREA
        assert rest[CONF_SHUTTERS][0]["frost_lock"] is True
        assert rest[CONF_WEATHER_ENTITY] == "weather.home"

    async def test_an_unknown_mode_is_refused(self, hass, hass_ws_client):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        response = await _call(
            client, {"type": "shutter_pilot/set_ui_mode", "mode": "profi"}
        )
        assert response["success"] is False
        assert CONF_UI_MODE not in entry.options

    async def test_switching_needs_admin_rights(self, hass, hass_ws_client, hass_admin_user):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        hass_admin_user.groups = []
        client = await hass_ws_client(hass)
        response = await _call(
            client, {"type": "shutter_pilot/set_ui_mode", "mode": UI_MODE_EXPERT}
        )
        assert response["success"] is False
        assert CONF_UI_MODE not in entry.options

    async def test_the_settings_form_cannot_turn_the_switch_back(
        self, hass, hass_ws_client
    ):
        """Das Formular haelt eine Kopie von vor dem Umschalten."""
        entry = await _setup(
            hass,
            {CONF_AREAS: [AREA], CONF_SHUTTERS: [], CONF_UI_MODE: UI_MODE_EXPERT},
        )
        client = await hass_ws_client(hass)
        with patch("custom_components.shutter_pilot._reload_entry_delayed"):
            response = await _call(
                client,
                {
                    "type": "shutter_pilot/save_settings",
                    "settings": {CONF_UI_MODE: UI_MODE_SIMPLE, CONF_WEATHER_ENTITY: "weather.x"},
                },
            )
        assert response["success"] is True
        assert entry.options[CONF_UI_MODE] == UI_MODE_EXPERT
        assert entry.options[CONF_WEATHER_ENTITY] == "weather.x"

    async def test_the_first_shutter_does_not_flip_the_mode(self, hass, hass_ws_client):
        """Ohne Schluessel haengt der Modus an „gibt es Rolllaeden" – und
        waere mit dem ersten gespeicherten Rollladen auf Experte gesprungen."""
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        assert await _status_mode(client) == UI_MODE_SIMPLE
        with patch("custom_components.shutter_pilot._reload_entry_delayed"):
            response = await _call(
                client,
                {"type": "shutter_pilot/save_shutter", "shutter": _shutter("cover.a")},
            )
        assert response["success"] is True
        assert entry.options[CONF_UI_MODE] == UI_MODE_SIMPLE
        assert await _status_mode(client) == UI_MODE_SIMPLE

    async def test_saving_a_shutter_keeps_an_existing_choice(self, hass, hass_ws_client):
        entry = await _setup(
            hass,
            {CONF_AREAS: [AREA], CONF_SHUTTERS: [], CONF_UI_MODE: UI_MODE_EXPERT},
        )
        client = await hass_ws_client(hass)
        with patch("custom_components.shutter_pilot._reload_entry_delayed"):
            await _call(
                client,
                {"type": "shutter_pilot/save_shutter", "shutter": _shutter("cover.a")},
            )
        assert entry.options[CONF_UI_MODE] == UI_MODE_EXPERT

    async def test_the_export_names_the_mode(self, hass):
        entry = await _setup(
            hass,
            {CONF_AREAS: [AREA], CONF_SHUTTERS: [], CONF_UI_MODE: UI_MODE_SIMPLE},
        )
        assert "Panel-Modus: einfach" in (await async_build_export(hass, entry))["markdown"]
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_UI_MODE: UI_MODE_EXPERT}
        )
        assert "Panel-Modus: Experte" in (await async_build_export(hass, entry))["markdown"]


class TestQuickSetup:
    async def _run(self, client, area: dict, shutters: list) -> dict:
        with patch("custom_components.shutter_pilot._reload_entry_delayed") as reload:
            response = await _call(
                client,
                {"type": "shutter_pilot/quick_setup", "area": area, "shutters": shutters},
            )
        response["_reloads"] = reload.call_count
        return response

    async def test_a_new_area_and_its_shutters_land_in_one_write(
        self, hass, hass_ws_client
    ):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        new_area = {CONF_AREA_ID: "oben", CONF_AREA_NAME: "Oben", CONF_AREA_MODE: AREA_MODE_SUN}
        response = await self._run(
            client, new_area, [_shutter("cover.a", "oben"), _shutter("cover.b", "oben")]
        )
        assert response["success"] is True
        assert response["result"]["added"] == 2
        assert response["_reloads"] == 1
        assert [a[CONF_AREA_ID] for a in entry.options[CONF_AREAS]] == ["wohnen", "oben"]
        assert [s[CONF_COVER_ENTITY_ID] for s in entry.options[CONF_SHUTTERS]] == [
            "cover.a",
            "cover.b",
        ]

    async def test_an_existing_area_only_gets_what_was_sent(self, hass, hass_ws_client):
        """Der Einstieg zeigt Name, Modus und Zeiten – der Rest bleibt stehen."""
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        response = await self._run(
            client,
            {CONF_AREA_ID: "wohnen", CONF_AREA_NAME: "Unten", CONF_AREA_TIME_UP: "06:30"},
            [_shutter("cover.a")],
        )
        assert response["success"] is True
        area = entry.options[CONF_AREAS][0]
        assert len(entry.options[CONF_AREAS]) == 1
        assert area[CONF_AREA_NAME] == "Unten"
        assert area[CONF_AREA_TIME_UP] == "06:30"
        assert area["sun_protect_enabled"] is True
        assert area[CONF_AREA_DRIVE_DELAY] == 0

    async def test_a_cover_that_is_already_set_up_is_skipped(self, hass, hass_ws_client):
        entry = await _setup(
            hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter("cover.a")]}
        )
        client = await hass_ws_client(hass)
        response = await self._run(
            client, dict(AREA), [_shutter("cover.a"), _shutter("cover.b"), _shutter("cover.b")]
        )
        assert response["result"]["added"] == 1
        assert response["result"]["skipped"] == ["cover.a", "cover.b"]
        assert [s[CONF_COVER_ENTITY_ID] for s in entry.options[CONF_SHUTTERS]] == [
            "cover.a",
            "cover.b",
        ]

    async def test_an_area_without_an_id_is_refused(self, hass, hass_ws_client):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        response = await self._run(client, {CONF_AREA_NAME: "Ohne"}, [_shutter("cover.a")])
        assert response["success"] is False
        assert entry.options[CONF_SHUTTERS] == []

    async def test_the_mode_is_written_down_and_stays_simple(self, hass, hass_ws_client):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        client = await hass_ws_client(hass)
        await self._run(client, dict(AREA), [_shutter("cover.a")])
        assert entry.options[CONF_UI_MODE] == UI_MODE_SIMPLE

    async def test_it_needs_admin_rights(self, hass, hass_ws_client, hass_admin_user):
        entry = await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: []})
        hass_admin_user.groups = []
        client = await hass_ws_client(hass)
        response = await self._run(client, dict(AREA), [_shutter("cover.a")])
        assert response["success"] is False
        assert entry.options[CONF_SHUTTERS] == []

    async def test_the_reload_gap_is_marked_as_loading(self, hass, hass_ws_client):
        """Waehrend des Neuladens gibt es keine Daten. Das Panel muss das von
        „kein Rollladen angelegt" unterscheiden, sonst blitzt der Einstieg auf."""
        await _setup(hass, {CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter("cover.a")]})
        client = await hass_ws_client(hass)
        ready = await _call(client, {"type": "shutter_pilot/get_status"})
        assert "loading" not in ready["result"]
        with patch(
            "custom_components.shutter_pilot._find_entry_data", return_value=(None, None)
        ):
            gap = await _call(client, {"type": "shutter_pilot/get_status"})
        assert gap["result"]["loading"] is True
        assert gap["result"]["shutters"] == []
