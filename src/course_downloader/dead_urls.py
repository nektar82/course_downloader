"""Persistent record of URLs that returned 404 (permanently dead)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class DeadUrlStore:
    """Tracks URLs that 404'd so future passes skip them without fetching.

    A 404 means the resource is gone; retrying it every pass wastes time
    and log space. The store persists to disk so restarts (e.g. after a VM
    reboot) remember which URLs are dead.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._dead: set[str] = set()
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._dead = set(data) if isinstance(data, list) else set()
        except (OSError, ValueError):
            self._dead = set()

    def is_dead(self, url: str) -> bool:
        """Return True if the URL is known to be dead (404)."""
        return url in self._dead

    def mark_dead(self, url: str) -> None:
        """Record a URL as dead and persist immediately."""
        if url in self._dead:
            return
        self._dead.add(url)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(sorted(self._dead), indent=2), encoding="utf-8"
            )
        except OSError:
            LOGGER.warning("Could not persist dead URL list to %s", self.path)

    def __len__(self) -> int:
        return len(self._dead)
