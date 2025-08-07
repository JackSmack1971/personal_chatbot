"""Memory manager placeholder.

Defines interfaces and a simple in-memory adapter to unblock tests.
A Supabase-backed adapter will be added later per integration-architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


class MemoryError(Exception):
    """Base error for memory operations."""


@dataclass
class MemoryRecord:
    id: str
    user_id: str
    content: str
    metadata: Dict[str, Any]


class MemoryStore(Protocol):  # pragma: no cover - interface
    def create(self, record: MemoryRecord) -> None: ...
    def get(self, record_id: str) -> Optional[MemoryRecord]: ...
    def list_by_user(self, user_id: str, limit: int = 50) -> List[MemoryRecord]: ...
    def delete(self, record_id: str) -> bool: ...


class InMemoryStore(MemoryStore):
    """Minimal in-memory implementation for testing."""

    def __init__(self) -> None:
        self._store: Dict[str, MemoryRecord] = {}

    def create(self, record: MemoryRecord) -> None:
        if record.id in self._store:
            raise MemoryError("Record already exists")
        self._store[record.id] = record

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self._store.get(record_id)

    def list_by_user(self, user_id: str, limit: int = 50) -> List[MemoryRecord]:
        results = [r for r in self._store.values() if r.user_id == user_id]
        return results[:limit]

    def delete(self, record_id: str) -> bool:
        return self._store.pop(record_id, None) is not None


class SupabaseStore(MemoryStore):  # pragma: no cover - stub for future implementation
    """Placeholder for Supabase adapter wired during integration."""
    def __init__(self) -> None:
        raise NotImplementedError("SupabaseStore not implemented in scaffolding")