"""Persistent cover position storage across Home Assistant restarts."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Literal

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
SOURCE_MANUAL = "manual"
SOURCE_AUTOMATION = "automation"
PositionSource = Literal["manual", "automation"]


def _storage_key(entry_id: str) -> str:
    return f"{DOMAIN}.positions.{entry_id}"


class ShutterPositionStore:
    """JSON store for last known cover positions (per config entry)."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._store = Store(hass, STORAGE_VERSION, _storage_key(entry_id))
        self._covers: dict[str, dict[str, Any]] | None = None
        self._pending: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> dict[str, dict[str, Any]]:
        """Load all cover records from disk."""
        if self._covers is not None:
            return self._covers
        raw = await self._store.async_load()
        if not isinstance(raw, dict):
            self._covers = {}
            self._pending = {}
        else:
            covers = raw.get("covers")
            self._covers = covers if isinstance(covers, dict) else {}
            pending = raw.get("pending")
            self._pending = pending if isinstance(pending, dict) else {}
        return self._covers

    async def async_save(self) -> None:
        """Persist current in-memory covers to disk."""
        if self._covers is None:
            return
        await self._store.async_save(
            {"covers": self._covers, "pending": self._pending}
        )

    async def async_set_pending(
        self, cover_entity_id: str, position: float, tilt: float | None, reason: str
    ) -> None:
        """Remember a drive that waits for the window to close.

        Only the plain values are persisted, never the shutter configuration
        that came with it – that is reloaded from the options anyway, and a
        stale copy on disk would be the more dangerous of the two.
        """
        await self.async_load()
        self._pending[cover_entity_id] = {
            "position": float(position),
            "tilt": None if tilt is None else float(tilt),
            "reason": str(reason),
            "saved": datetime.now().astimezone().isoformat(),
        }
        await self.async_save()

    async def async_clear_pending(self, cover_entity_id: str) -> None:
        """Drop a remembered drive, because it ran or is no longer wanted."""
        await self.async_load()
        if self._pending.pop(cover_entity_id, None) is not None:
            await self.async_save()

    async def async_get_pending(self, max_age_hours: float) -> dict[str, dict[str, Any]]:
        """Return remembered drives that are still worth running.

        A catch-up from days ago says nothing about what the shutters should do
        now, so anything older is dropped instead of surprising someone with a
        movement after a long absence.
        """
        await self.async_load()
        cutoff = datetime.now().astimezone() - timedelta(hours=max_age_hours)
        fresh: dict[str, dict[str, Any]] = {}
        dropped = False
        for cover, rec in list(self._pending.items()):
            if not isinstance(rec, dict):
                dropped = True
                continue
            try:
                saved = datetime.fromisoformat(str(rec.get("saved")))
            except (TypeError, ValueError):
                dropped = True
                continue
            if saved < cutoff:
                _LOGGER.info(
                    "Discarding stale catch-up drive for %s (saved %s)", cover, saved
                )
                dropped = True
                continue
            fresh[cover] = rec
        if dropped:
            self._pending = fresh
            await self.async_save()
        return dict(fresh)

    async def async_set_position(
        self,
        cover_entity_id: str,
        position: float,
        source: PositionSource,
    ) -> None:
        """Update one cover and persist."""
        covers = await self.async_load()
        covers[cover_entity_id] = {
            "position": float(position),
            "source": source,
            "updated": datetime.now().astimezone().isoformat(),
        }
        await self.async_save()

    def get_record(self, cover_entity_id: str) -> dict[str, Any] | None:
        """Return stored record if loaded."""
        if self._covers is None:
            return None
        rec = self._covers.get(cover_entity_id)
        return rec if isinstance(rec, dict) else None

    @callback
    def get_position_sync(self, cover_entity_id: str) -> float | None:
        """Return stored position without async load (after async_load was called)."""
        rec = self.get_record(cover_entity_id)
        if not rec:
            return None
        try:
            return float(rec["position"])
        except (TypeError, ValueError, KeyError):
            return None

    @callback
    def get_source_sync(self, cover_entity_id: str) -> str | None:
        rec = self.get_record(cover_entity_id)
        if not rec:
            return None
        return str(rec.get("source") or "")


def get_position_store(hass: HomeAssistant, entry_id: str) -> ShutterPositionStore:
    """Return or create the position store for a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_data = domain_data.setdefault(entry_id, {})
    store = entry_data.get("position_store")
    if store is None:
        store = ShutterPositionStore(hass, entry_id)
        entry_data["position_store"] = store
    return store
