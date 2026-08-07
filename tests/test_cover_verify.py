"""Tests for the drive verification.

Radio-driven shutters lose commands. Before this, the requested position was
stored as fact, so the integration kept deciding on a value the cover never
reached. Inspired by the "Cover Hardware" section of the NACC blueprint.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import SupportsResponse  # noqa: F401 - keeps import style
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    CONF_VERIFY_AFTER,
    CONF_VERIFY_ENABLED,
    CONF_VERIFY_RETRIES,
    CONF_VERIFY_TOLERANCE,
    DEFAULT_VERIFY_AFTER,
    DOMAIN,
    EVENT_COVER_FAILED,
)
from custom_components.shutter_pilot import cover_verify
from custom_components.shutter_pilot.position_store import get_position_store

COVER = "cover.test"


def _entry(hass, **options) -> MockConfigEntry:
    opts = {CONF_VERIFY_ENABLED: True, CONF_VERIFY_AFTER: 5, CONF_VERIFY_TOLERANCE: 8}
    opts.update(options)
    entry = MockConfigEntry(domain=DOMAIN, options=opts)
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    return entry


def _set_cover(hass, position: float | None) -> None:
    attrs = {} if position is None else {"current_position": position}
    hass.states.async_set(COVER, "open", attrs)


async def _run(hass, entry, target: float, reason: str = "Test"):
    """Run one verification with the waits skipped."""
    calls = []

    async def _handler(call):
        calls.append(call)

    hass.services.async_register("cover", "set_cover_position", _handler)
    try:
        with patch(
            "custom_components.shutter_pilot.cover_verify.asyncio.sleep",
            AsyncMock(return_value=None),
        ):
            await cover_verify._verify(hass, entry, COVER, target, reason)
    finally:
        hass.services.async_remove("cover", "set_cover_position")
    return calls


class TestSuccess:
    async def test_reached_on_first_try(self, hass):
        entry = _entry(hass)
        _set_cover(hass, 30)
        calls = await _run(hass, entry, 30)
        assert calls == []

    async def test_within_tolerance_counts_as_reached(self, hass):
        entry = _entry(hass, **{CONF_VERIFY_TOLERANCE: 8})
        _set_cover(hass, 34)
        assert await _run(hass, entry, 30) == []

    async def test_just_outside_tolerance_is_repeated(self, hass):
        entry = _entry(hass, **{CONF_VERIFY_TOLERANCE: 3, CONF_VERIFY_RETRIES: 1})
        _set_cover(hass, 40)
        calls = await _run(hass, entry, 30)
        assert len(calls) == 1


class TestRetry:
    async def test_repeats_then_succeeds(self, hass):
        """Second check sees the cover in place, so no failure is reported."""
        entry = _entry(hass, **{CONF_VERIFY_RETRIES: 1})
        _set_cover(hass, 100)
        events = []
        hass.bus.async_listen(EVENT_COVER_FAILED, events.append)

        async def _handler(call):
            # The repeated command works this time.
            _set_cover(hass, 30)

        hass.services.async_register("cover", "set_cover_position", _handler)
        try:
            with patch(
                "custom_components.shutter_pilot.cover_verify.asyncio.sleep",
                AsyncMock(return_value=None),
            ):
                await cover_verify._verify(hass, entry, COVER, 30, "Test")
        finally:
            hass.services.async_remove("cover", "set_cover_position")
        await hass.async_block_till_done()
        assert events == []

    async def test_respects_retry_count(self, hass):
        entry = _entry(hass, **{CONF_VERIFY_RETRIES: 2})
        _set_cover(hass, 100)
        calls = await _run(hass, entry, 30)
        assert len(calls) == 2


class TestFinalFailure:
    @pytest.fixture
    async def failed(self, hass):
        entry = _entry(hass, **{CONF_VERIFY_RETRIES: 1})
        _set_cover(hass, 100)
        events = []
        hass.bus.async_listen(EVENT_COVER_FAILED, events.append)
        await _run(hass, entry, 30, "Schedule down (living)")
        await hass.async_block_till_done()
        return entry, events

    async def test_fires_event(self, hass, failed):
        _entry_obj, events = failed
        assert len(events) == 1
        data = events[0].data
        assert data["entity_id"] == COVER
        assert data["requested"] == 30
        assert data["actual"] == 100
        assert "Schedule down" in data["reason"]

    async def test_stores_the_real_position(self, hass, failed):
        """The whole point: no more deciding on a position never reached."""
        entry, _events = failed
        store = get_position_store(hass, entry.entry_id)
        assert store.get_position_sync(COVER) == 100
        assert hass.data[DOMAIN][entry.entry_id]["last_positions"][COVER] == 100

    async def test_logs_a_warning(self, hass, caplog):
        entry = _entry(hass, **{CONF_VERIFY_RETRIES: 0})
        _set_cover(hass, 100)
        await _run(hass, entry, 30)
        assert "did not reach" in caplog.text


class TestSkipped:
    async def test_cover_without_position_is_skipped(self, hass):
        entry = _entry(hass)
        _set_cover(hass, None)
        assert cover_verify.supports_position_feedback(hass, COVER) is False
        cover_verify.schedule_verification(hass, entry, COVER, 30, "Test")
        assert hass.data[DOMAIN][entry.entry_id].get("_verify_tasks") in (None, {})

    async def test_disabled_does_nothing(self, hass):
        entry = _entry(hass, **{CONF_VERIFY_ENABLED: False})
        _set_cover(hass, 100)
        cover_verify.schedule_verification(hass, entry, COVER, 30, "Test")
        assert hass.data[DOMAIN][entry.entry_id].get("_verify_tasks") in (None, {})

    async def test_unavailable_cover_aborts_quietly(self, hass):
        entry = _entry(hass)
        _set_cover(hass, 100)
        events = []
        hass.bus.async_listen(EVENT_COVER_FAILED, events.append)
        hass.states.async_set(COVER, "unavailable", {})
        await _run(hass, entry, 30)
        await hass.async_block_till_done()
        assert events == []


class TestTaskHandling:
    async def test_new_drive_replaces_pending_check(self, hass):
        """Otherwise an old check would fight a fresh command."""
        entry = _entry(hass)
        _set_cover(hass, 100)
        cover_verify.schedule_verification(hass, entry, COVER, 30, "first")
        tasks = hass.data[DOMAIN][entry.entry_id]["_verify_tasks"]
        first = tasks[COVER]

        cover_verify.schedule_verification(hass, entry, COVER, 60, "second")
        second = tasks[COVER]
        assert first is not second

        cover_verify.cancel_all(hass.data[DOMAIN][entry.entry_id])
        await hass.async_block_till_done()
        # Cancellation is only requested synchronously, so check after the
        # event loop had a chance to process it.
        assert first.cancelled()
        assert second.cancelled()

    async def test_cancel_all_clears_everything(self, hass):
        """Used when the entry is unloaded – nothing may keep running."""
        entry = _entry(hass)
        _set_cover(hass, 100)
        cover_verify.schedule_verification(hass, entry, COVER, 30, "Test")
        data = hass.data[DOMAIN][entry.entry_id]
        task = data["_verify_tasks"][COVER]
        cover_verify.cancel_all(data)
        assert data["_verify_tasks"] == {}
        await hass.async_block_till_done()
        assert task.cancelled()


class TestTaskBookkeeping:
    """Ein abgebrochener Task darf den Eintrag seines Nachfolgers nicht löschen.

    `schedule_verification` popt vor dem Neuanlegen; die Abbruchbehandlung des
    alten Tasks läuft aber erst im nächsten Loop-Durchlauf. Ohne
    Identitätsprüfung im `finally` räumte sie danach den *neuen* Eintrag weg –
    ein späteres Cancel fand den laufenden Task dann nicht mehr.
    """

    async def test_replacing_a_check_keeps_the_new_task(self, hass):
        import asyncio

        entry = _entry(hass)
        _set_cover(hass, 30)
        data = hass.data[DOMAIN][entry.entry_id]

        # Nur die Wartezeit der Prüfung anhalten: `cover_verify.asyncio` *ist*
        # das globale Modul, ein pauschaler Patch legt auch den Test lahm.
        gate = asyncio.Event()
        real_sleep = asyncio.sleep

        async def _gated(seconds, *args, **kwargs):
            if seconds == DEFAULT_VERIFY_AFTER:
                await gate.wait()
                return None
            return await real_sleep(seconds, *args, **kwargs)

        with patch.object(asyncio, "sleep", _gated):
            cover_verify.schedule_verification(hass, entry, COVER, 30, "erste")
            first = data["_verify_tasks"][COVER]
            cover_verify.schedule_verification(hass, entry, COVER, 60, "zweite")
            second = data["_verify_tasks"][COVER]
            assert first is not second

            # Dem abgebrochenen ersten Task Gelegenheit geben, sein finally zu
            # durchlaufen.
            for _ in range(5):
                await asyncio.sleep(0)

            assert data["_verify_tasks"].get(COVER) is second, "Nachfolger überlebt"

            cover_verify.cancel_all(data)
            for _ in range(5):
                await asyncio.sleep(0)
            assert second.cancelled() or second.done()
