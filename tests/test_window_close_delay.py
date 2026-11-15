"""Rueckfahrt nach dem Schliessen verzoegern (heinzel, #252).

Im Winter abends kurz aus der Terrassentuer: der Rollladen faehrt beim Oeffnen
hoch, die Tuer wird gegen die Kaelte zugezogen - und nach spaetestens 30 s
(Obergrenze der Entprellung) faehrt der Rollladen wieder zu. Ausgesperrt.
`window_close_delay_minutes` haengt eine Wartezeit in Minuten an die
Entprellung an; oeffnet die Tuer wieder, beginnt sie von vorn.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot import window_trigger
from custom_components.shutter_pilot.const import (
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_CLOSE_DELAY_MINUTES,
)
from tests.test_window_debounce import (  # noqa: F401 - cover_calls ist ein Fixture
    COVER,
    _gated_sleep,
    _positions,
    _setup,
    _shutter,
    _window,
    _window_bounce,
    cover_calls,
)

# 5 s Entprellung (Vorgabe) + 10 min
DELAY = 5 + 10 * 60


def _door(**overrides) -> dict:
    return _shutter(**{CONF_WINDOW_CLOSE_DELAY_MINUTES: 10, **overrides})


async def _step_out(hass) -> None:
    """Tuer auf (hier: gekippt), der Rollladen steht danach auf 50 %."""
    await _window(hass, "tilted")
    hass.states.async_set(
        COVER, "open", {"current_position": 50, "supported_features": 15}
    )


async def test_shutter_waits_the_configured_minutes(hass, cover_calls):
    _, data = await _setup(hass, _door())
    await _step_out(hass)
    assert _positions(cover_calls) == [50]

    with _gated_sleep(DELAY) as gate:
        await _window_bounce(hass, "closed")  # Tuer hinter sich zugezogen
        assert _positions(cover_calls) == [50], "bleibt oben, solange die Zeit laeuft"
        assert COVER in data["_window_close_tasks"]
        gate.set()
        await hass.async_block_till_done()

    assert _positions(cover_calls) == [50, 0], "danach genau eine Rueckfahrt"


async def test_coming_back_in_restarts_the_wait(hass, cover_calls):
    _, data = await _setup(hass, _door())
    await _step_out(hass)

    with _gated_sleep(DELAY) as gate:
        await _window_bounce(hass, "closed")  # raus
        first = data["_window_close_tasks"][COVER]
        await _window_bounce(hass, "tilted")  # wieder rein
        assert COVER not in data.get("_window_close_tasks", {}), "Wartezeit abgebrochen"
        await _window_bounce(hass, "closed")  # Tuer zu, von drinnen
        assert data["_window_close_tasks"][COVER] is not first
        # Das erneute Oeffnen sendet die Lueftungsposition noch einmal, wie
        # schon immer - eine Rueckfahrt gab es bis hierhin nicht.
        assert _positions(cover_calls) == [50, 50]
        gate.set()
        await hass.async_block_till_done()

    assert _positions(cover_calls) == [50, 50, 0]


async def test_off_by_default(hass, cover_calls):
    """Ohne den Wert bleibt es bei der Entprellung von 5 s."""
    await _setup(hass, _shutter())
    await _step_out(hass)
    with _gated_sleep(5) as gate:
        await _window_bounce(hass, "closed")
        gate.set()
        await hass.async_block_till_done()
    assert _positions(cover_calls) == [50, 0]


@pytest.mark.parametrize(
    ("minutes", "debounce", "expected"),
    [
        (0, 5, 5),
        (10, 5, 605),
        (10, 0, 600),
        (999, 0, 120 * 60),
        (-3, 5, 5),
        ("abc", 5, 5),
        (None, 5, 5),
        ("", 0, 0),
    ],
)
def test_seconds(minutes, debounce, expected):
    assert window_trigger._close_delay_seconds(
        {CONF_WINDOW_CLOSE_DELAY_MINUTES: minutes, CONF_WINDOW_CLOSE_DEBOUNCE: debounce}
    ) == expected
