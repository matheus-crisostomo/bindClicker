"""
Data models for BindClicker.

Defines the core data structures used across the application:
  - Action:          A single recorded mouse click or key press.
  - Script:          A named collection of actions with playback settings.
  - ExecutionRecord: A log entry for one script execution.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from utils.constants import (
    RANDOM_DELAY_DEFAULT,
    REPEAT_DEFAULT,
    SCRIPT_FORMAT_VERSION,
    SPEED_DEFAULT,
)


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------
@dataclass
class Action:
    """A single recorded event (mouse click or key press/release)."""

    action_type: str                # "click", "key_press", "key_release"
    button: Optional[str] = None    # "left", "right", "middle" or key name
    x: Optional[int] = None        # Mouse X position (None for keyboard)
    y: Optional[int] = None        # Mouse Y position (None for keyboard)
    delay_before: float = 0.0      # Milliseconds to wait BEFORE this action
    delay_after: float = 0.0       # Milliseconds to wait AFTER this action
    pressed: bool = True           # True = pressed, False = released

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Action":
        return cls(
            action_type=data["action_type"],
            button=data.get("button"),
            x=data.get("x"),
            y=data.get("y"),
            delay_before=float(data.get("delay_before", 0)),
            delay_after=float(data.get("delay_after", 0)),
            pressed=data.get("pressed", True),
        )

    @property
    def display_type(self) -> str:
        """Human-readable action type for the UI."""
        type_map = {
            "click": "Mouse Click",
            "key_press": "Key Press",
            "key_release": "Key Release",
        }
        return type_map.get(self.action_type, self.action_type)

    @property
    def display_target(self) -> str:
        """Human-readable target (button/key name)."""
        if self.action_type == "click":
            btn_map = {"left": "Left", "right": "Right", "middle": "Middle"}
            return btn_map.get(self.button or "", self.button or "?")
        return self.button or "?"

    @property
    def display_position(self) -> str:
        """Formatted position string."""
        if self.x is not None and self.y is not None:
            return f"({self.x}, {self.y})"
        return "—"


# ---------------------------------------------------------------------------
# Script
# ---------------------------------------------------------------------------
@dataclass
class Script:
    """A named macro: a sequence of Actions with playback settings."""

    name: str
    actions: List[Action] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    repeat_count: int = REPEAT_DEFAULT         # 0 = infinite
    speed_multiplier: float = SPEED_DEFAULT
    random_delay_ms: int = RANDOM_DELAY_DEFAULT

    # -- Serialisation -------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "version": SCRIPT_FORMAT_VERSION,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "repeat_count": self.repeat_count,
            "speed_multiplier": self.speed_multiplier,
            "random_delay_ms": self.random_delay_ms,
            "actions": [a.to_dict() for a in self.actions],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Script":
        actions = [Action.from_dict(a) for a in data.get("actions", [])]
        return cls(
            name=data["name"],
            actions=actions,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            repeat_count=int(data.get("repeat_count", REPEAT_DEFAULT)),
            speed_multiplier=float(data.get("speed_multiplier", SPEED_DEFAULT)),
            random_delay_ms=int(data.get("random_delay_ms", RANDOM_DELAY_DEFAULT)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Script":
        return cls.from_dict(json.loads(json_str))

    def touch(self) -> None:
        """Update the `updated_at` timestamp."""
        self.updated_at = datetime.now().isoformat()

    @property
    def action_count(self) -> int:
        return len(self.actions)


# ---------------------------------------------------------------------------
# ExecutionRecord
# ---------------------------------------------------------------------------
@dataclass
class ExecutionRecord:
    """Log entry for one script execution."""

    script_name: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: str = ""
    duration_ms: float = 0.0
    actions_executed: int = 0
    status: str = "running"     # "completed", "stopped", "error"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecord":
        return cls(
            script_name=data["script_name"],
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
            duration_ms=float(data.get("duration_ms", 0)),
            actions_executed=int(data.get("actions_executed", 0)),
            status=data.get("status", "unknown"),
        )


# ---------------------------------------------------------------------------
# History  (wrapper around a list of ExecutionRecords for a script)
# ---------------------------------------------------------------------------
@dataclass
class ScriptHistory:
    """Execution history for a single script."""

    script_name: str
    records: List[ExecutionRecord] = field(default_factory=list)

    @property
    def total_runs(self) -> int:
        return len(self.records)

    def add(self, record: ExecutionRecord) -> None:
        self.records.append(record)

    def to_dict(self) -> dict:
        return {
            "script_name": self.script_name,
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptHistory":
        records = [ExecutionRecord.from_dict(r) for r in data.get("records", [])]
        return cls(script_name=data["script_name"], records=records)
