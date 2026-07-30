"""Tests for the configurable manual-override expiry."""

from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.shutter_pilot.const import (
    CONF_AREA_MANUAL_OVERRIDE,
    OVERRIDE_DAILY,
    OVERRIDE_NEVER,
    OVERRIDE_NEXT_ACTION,
)
from custom_components.shutter_pilot.helpers import manual_override_still_blocks


class _FakeStore:
    """Minimal stand-in exposing only get_record()."""

    def __init__(self, updated: str | None) -> None:
        self._updated = updated

    def get_record(self, cover_entity_id: str):
        if self._updated is None:
            return None
        return {"position": 40.0, "source": "manual", "updated": self._updated}


def _iso(days_ago: int) -> str:
    return (datetime.now().astimezone() - timedelta(days=days_ago)).isoformat()


class TestNever:
    def test_blocks_regardless_of_age(self):
        store = _FakeStore(_iso(30))
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_NEVER}
        assert manual_override_still_blocks(store, "cover.x", area) is True

    def test_is_the_default(self):
        store = _FakeStore(_iso(30))
        assert manual_override_still_blocks(store, "cover.x", {}) is True
        assert manual_override_still_blocks(store, "cover.x", None) is True


class TestNextAction:
    def test_never_blocks(self):
        store = _FakeStore(_iso(0))
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_NEXT_ACTION}
        assert manual_override_still_blocks(store, "cover.x", area) is False


class TestDaily:
    def test_same_day_blocks(self):
        store = _FakeStore(_iso(0))
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_DAILY}
        assert manual_override_still_blocks(store, "cover.x", area) is True

    def test_previous_day_expires(self):
        store = _FakeStore(_iso(1))
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_DAILY}
        assert manual_override_still_blocks(store, "cover.x", area) is False

    def test_missing_record_keeps_blocking(self):
        """Fail safe: without a timestamp we do not silently override the user."""
        store = _FakeStore(None)
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_DAILY}
        assert manual_override_still_blocks(store, "cover.x", area) is True

    def test_broken_timestamp_keeps_blocking(self):
        store = _FakeStore("not-a-date")
        area = {CONF_AREA_MANUAL_OVERRIDE: OVERRIDE_DAILY}
        assert manual_override_still_blocks(store, "cover.x", area) is True
