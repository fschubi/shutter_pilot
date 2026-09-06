"""Punkt 5 der Analyse: kein bestaetigter Fehler, aber eine offene Frage.

Beschattung (`elevation.py`), Daemmerungs-Einfahrt (`awning_dusk.py`) und der
Wetterschutz (`awning_guard.py`) haengen alle am selben gemeinsamen
Minutentakt (`__init__.py::_setup_minute_ticker`), aber jeder Callback stoesst
seine eigentliche Auswertung nur als eigenen `hass.async_create_task(...)`
an. Es gibt also keine Garantie, in welcher Reihenfolge die drei Module
*fertig* werden - nur eine Reihenfolge, in der ihre Tasks *gestartet* werden.

Diese Tests pruefen die Sicherheitseigenschaft, die davon nicht abhaengen
darf: eine durch Wind/Regen/Frost gesperrte Markise darf in keiner
Reihenfolge der drei Auswertungen ausgefahren werden, und eine freigegebene
Markise darf in jeder Reihenfolge korrekt ausfahren. Jedes Modul prueft seine
sicherheitsrelevanten Voraussetzungen selbst und lebt (`evaluate_guard()`
liest Sensor- und Laufzeitzustand direkt, nicht einen von einem anderen
Modul vorbereiteten Cache) - deshalb wird hier *nicht* serialisiert oder
sonst irgendetwas an der Nebenlaeufigkeit geaendert, nur die Eigenschaft
selbst nachgewiesen.
"""

from __future__ import annotations

import itertools
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AWNING_GUARD_WIND,
    AWNING_DUSK_SLOT,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_ENABLED,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    sun_condition_keys,
)

AWNING = "cover.markise_order_test"
WIND = "sensor.wind_order_test"
TEMP = "sensor.temp_order_test"
LUX = "sensor.lux_order_test"

COND_A_ENTITY, COND_A_ON, COND_A_OFF, _ = sun_condition_keys("a")
DUSK_ENTITY, DUSK_ON, DUSK_OFF, _ = sun_condition_keys(AWNING_DUSK_SLOT)
WIND_ENTITY, WIND_ON, WIND_OFF, _ = sun_condition_keys(AWNING_GUARD_WIND)

TICK_NAMES = ("elevation", "awning_guard", "awning_dusk")
ALL_ORDERS = list(itertools.permutations(TICK_NAMES))


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    """Jede Fahrt, ueber den gesamten Testlauf hinweg mitgeschrieben."""
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        entity_id = call.data["entity_id"]
        for eid in [entity_id] if isinstance(entity_id, str) else entity_id:
            hass.states.async_set(
                eid,
                "closed" if position <= 0 else "open",
                {"current_position": position, "supported_features": 15},
            )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


def _positions(calls) -> list[int]:
    return [c.data["position"] for c in calls]


async def _setup(hass, *, danger: bool, dark: bool) -> tuple:
    """Eine Markise, elevationsfrei beschattet, mit Wind-Guard und Dusk.

    `elevation_enabled=False`, bewusst der schaerfere Fall aus Punkt 3: ohne
    Elevationspruefung gibt es keinen Elevations-Zweig, der von sich aus
    aufraeumt - jede Sicherheit muss aus Guard/Dusk selbst kommen.
    """
    hass.states.async_set(
        AWNING, "closed", {"current_position": 100, "supported_features": 15}
    )
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 5.0, "azimuth": 180.0})
    hass.states.async_set(TEMP, "30")  # Beschattungsbedingung bleibt immer erfuellt
    hass.states.async_set(WIND, "25" if danger else "2")
    hass.states.async_set(LUX, "20" if dark else "500")

    area = {
        CONF_AREA_ID: "order_area",
        CONF_AREA_NAME: "Order Test",
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_ENABLED: False,
        CONF_AREA_AZIMUTH_ENABLED: False,
        COND_A_ENTITY: TEMP,
        COND_A_ON: 25,
        COND_A_OFF: 20,
    }
    shutter = {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise Order Test",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_AREA_DOWN_ID: "order_area",
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
        DUSK_ENTITY: LUX,
        DUSK_ON: 50,
        DUSK_OFF: 100,
        WIND_ENTITY: WIND,
        WIND_ON: 15,
        WIND_OFF: 10,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _tick(hass, data, name: str) -> None:
    data["_minute_callbacks"][name](None)
    await hass.async_block_till_done()


class TestABarredAwningNeverExtendsRegardlessOfOrder:
    """Wind-Gefahr + Dunkelheit + erfuellte Beschattungsbedingung, alle drei
    gleichzeitig. In *keiner* der sechs moeglichen Reihenfolgen der drei
    Minutentakte darf die Markise auf 100 % (ausgefahren) fahren."""

    @pytest.mark.parametrize("order", ALL_ORDERS, ids=lambda o: "->".join(o))
    async def test_no_order_extends_a_barred_awning(self, hass, cover_calls, order):
        entry, data = await _setup(hass, danger=True, dark=True)

        # Der natuerliche Setup-Lauf (Registrierungsreihenfolge) ist bereits
        # im Mitschnitt enthalten - danach noch einmal explizit in der
        # parametrisierten Reihenfolge, mehrfach, um eine zufaellig sichere
        # Registrierungsreihenfolge nicht mit echter Ordnungsunabhaengigkeit
        # zu verwechseln.
        for _ in range(2):
            for name in order:
                await _tick(hass, data, name)

        assert 100 not in _positions(cover_calls), (
            f"Reihenfolge {order}: eine durch Wind gesperrte Markise wurde "
            "trotzdem ausgefahren"
        )
        assert hass.states.get(AWNING).attributes.get("current_position") == 0


class TestAFreeAwningExtendsRegardlessOfOrder:
    """Gegenprobe zur vorigen Klasse: ohne Gefahr und ohne Dunkelheit muss
    die Beschattung in jeder Reihenfolge trotzdem ausfahren - die
    Ordnungsunabhaengigkeit darf keine pauschale Blockade sein."""

    @pytest.mark.parametrize("order", ALL_ORDERS, ids=lambda o: "->".join(o))
    async def test_every_order_still_lets_shading_extend_it(
        self, hass, cover_calls, order
    ):
        entry, data = await _setup(hass, danger=False, dark=False)

        for name in order:
            await _tick(hass, data, name)

        assert 100 in _positions(cover_calls), (
            f"Reihenfolge {order}: die Beschattung haette ausfahren muessen"
        )
