"""Der Hauptschalter muss nach einer Neuinstallation eingeschaltet starten."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.shutter_pilot.switch import ATTR_ENTRY_ID, _restored_is_on


def _state(value: str, entry_id: str | None = None) -> SimpleNamespace:
    attrs = {} if entry_id is None else {ATTR_ENTRY_ID: entry_id}
    return SimpleNamespace(state=value, attributes=attrs)


@pytest.mark.parametrize(
    ("last_state", "expected", "case"),
    [
        (None, True, "frische Installation ohne gespeicherten Zustand"),
        (_state("off", "old_entry"), True, "Zustand stammt aus einer früheren Installation"),
        (_state("unavailable", "entry1"), True, "Entität war beim Beenden nicht bereit"),
        (_state("unknown", "entry1"), True, "Zustand beim Beenden unbekannt"),
        (_state("on", "entry1"), True, "eigener Zustand: an"),
        (_state("off", "entry1"), False, "eigener Zustand: aus bleibt aus"),
        (_state("off"), False, "Update aus einer Version vor 2.4.1: aus bleibt aus"),
        (_state("on"), True, "Update aus einer Version vor 2.4.1: an bleibt an"),
    ],
)
def test_restored_is_on(last_state, expected: bool, case: str) -> None:
    assert _restored_is_on(last_state, "entry1") is expected, case
