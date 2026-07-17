from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class WorkState(StrEnum):
    ACTIVE = "active"
    HEALTHY = "healthy"
    BLOCKED = "blocked"
    STOPPED = "stopped"


class CallState(StrEnum):
    NOT_DUE = "not_due"
    DUE = "due"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Clock(Protocol):
    def now(self) -> dt.datetime:
        pass


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> dt.datetime:
        return dt.datetime.now(dt.UTC)


@dataclass(frozen=True)
class FrozenClock:
    value: dt.datetime

    def now(self) -> dt.datetime:
        return normalized_utc(self.value)


def normalized_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value.astimezone(dt.UTC)


def parse_timestamp(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return normalized_utc(parsed)


def timestamp_after(clock: Clock, seconds: float) -> str:
    due = normalized_utc(clock.now()) + dt.timedelta(seconds=seconds)
    return due.replace(microsecond=0).isoformat()
