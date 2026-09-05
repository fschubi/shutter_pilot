"""Die drei Polaritäten der Bedingungs-Slots, an einer Stelle geprüft.

`_slot_reading()` liest einen Bedingungs-Slot roh aus und antwortet mit
`True`/`False`/`None` – `None` heißt „nicht beurteilbar" und trägt selbst
keine Sicherheitsbedeutung. Was `None` für die eigene Richtung heißt,
entscheidet ausschließlich der Aufrufer:

  sun_extra_conditions_met() / _condition_slot_met() -> fail open
  _own_slot_met()  (close/frost/vent)                -> fail closed
  guard_slot_danger()  (Markisen + Dachfenster)       -> fail danger

Vor dieser Trennung steckten alle "nicht auswertbar"-Fälle als hartes
`return True` *in* der gemeinsamen Funktion – der Beschattungs-Antwort. Die
beiden anderen Aufrufer fingen nur die äußeren Fälle (Entität fehlt, Sensor
tot) selbst ab und erbten die innere Beschattungs-Antwort ungefragt für alle
Fälle, die tiefer in der Funktion lagen (Text ohne Zustandsliste, fehlende
Schwelle). Am gefährlichsten bei `guard_slot_danger()`: die Beschattungs-
Antwort "blockiert nicht" heißt dort "keine Gefahr" – eine Markise oder ein
Dachfenster hätte bei einer halb ausgefüllten Regen-/Frostkonfiguration
lautlos keinen Schutz gehabt. `test_awning_guard.py::TestUnusableButAlive`
und `test_frost_protection.py` decken das je Fassade konkret ab; dieser Test
prüft die Rohfunktion selbst, damit ein künftiger vierter Aufrufer nicht
versehentlich eine der drei Antworten erbt, ohne es zu entscheiden.
"""

from __future__ import annotations

from custom_components.shutter_pilot.const import CONF_AREA_ID, sun_condition_keys
from custom_components.shutter_pilot.helpers import _slot_reading

SLOT = "a"
ENTITY = "sensor.helligkeit"


def _area(**overrides) -> dict:
    area = {CONF_AREA_ID: "living"}
    area.update(overrides)
    return area


class TestUnjudgeableReturnsNone:
    """Jeder "nicht auswertbar"-Fall gibt None zurück, nicht True oder False."""

    async def test_no_entity_configured(self, hass):
        assert _slot_reading(hass, _area(), SLOT, {}) is None

    async def test_entity_unavailable(self, hass):
        entity_key, *_ = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "unavailable")
        area = _area(**{entity_key: ENTITY})
        assert _slot_reading(hass, area, SLOT, {}) is None

    async def test_entity_unknown(self, hass):
        entity_key, *_ = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "unknown")
        area = _area(**{entity_key: ENTITY})
        assert _slot_reading(hass, area, SLOT, {}) is None

    async def test_text_without_a_state_list(self, hass):
        entity_key, *_ = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "bewölkt")
        area = _area(**{entity_key: ENTITY})
        assert _slot_reading(hass, area, SLOT, {}) is None

    async def test_threshold_never_configured(self, hass):
        entity_key, _on, _off, _states = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "500")
        area = _area(**{entity_key: ENTITY})  # on_above fehlt
        assert _slot_reading(hass, area, SLOT, {}) is None


class TestJudgeableReturnsBool:
    """Sobald etwas auszuwerten ist, kommt ein echtes True/False - kein None
    mehr, das ein Aufrufer versehentlich als "nicht auswertbar" behandeln
    könnte."""

    async def test_above_threshold(self, hass):
        entity_key, on_key, off_key, _states = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "500")
        area = _area(**{entity_key: ENTITY, on_key: 300, off_key: 200})
        assert _slot_reading(hass, area, SLOT, {}) is True

    async def test_below_threshold(self, hass):
        entity_key, on_key, off_key, _states = sun_condition_keys(SLOT)
        hass.states.async_set(ENTITY, "100")
        area = _area(**{entity_key: ENTITY, on_key: 300, off_key: 200})
        assert _slot_reading(hass, area, SLOT, {}) is False
