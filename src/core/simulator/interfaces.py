"""Simulator interface — any embodied interaction environment implements this.

Extensibility: Add new simulators (circuit builder, chemistry lab, geography
explorer) by implementing SimulatorInterface and registering in SimulatorRegistry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SensorReading:
    sensor_id: str
    value: float | str | bool
    unit: str = ""


@dataclass
class SimulatorState:
    simulator_id: str
    tick: int
    entity_states: dict[str, Any]  # flexible per-simulator
    sensor_readings: list[SensorReading]
    event_log: list[str]            # last N significant events
    is_complete: bool = False
    score: float | None = None

    def to_llm_description(self) -> str:
        """Human-readable summary for the LLM system prompt."""
        lines = [f"[{self.simulator_id} | tick={self.tick}]"]
        for k, v in self.entity_states.items():
            lines.append(f"  {k}: {v}")
        if self.sensor_readings:
            lines.append("Sensors:")
            for s in self.sensor_readings:
                lines.append(f"  {s.sensor_id}={s.value}{s.unit}")
        if self.event_log:
            lines.append(f"Recent events: {'; '.join(self.event_log[-3:])}")
        return "\n".join(lines)


@dataclass
class SimulatorCommand:
    command: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    success: bool
    message: str
    new_state: SimulatorState


class SimulatorInterface(ABC):
    """Base class for all BrainEcosystem simulators."""

    @property
    @abstractmethod
    def simulator_id(self) -> str: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    @abstractmethod
    def reset(self, config: dict[str, Any] | None = None) -> SimulatorState: ...

    @abstractmethod
    def execute_command(self, cmd: SimulatorCommand) -> CommandResult: ...

    @abstractmethod
    def get_state(self) -> SimulatorState: ...

    @abstractmethod
    def list_commands(self) -> list[str]: ...
