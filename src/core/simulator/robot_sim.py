"""RobotSimulator — a 2D grid robot for school project-based learning.

Students command a robot on a grid to solve challenges (reach target,
avoid obstacles, draw shapes). The LLM uses simulator state to guide
Socratic questions about loops, conditionals, and problem decomposition.

This is the backend state machine; the frontend renders via Canvas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .interfaces import (
    CommandResult,
    SensorReading,
    SimulatorCommand,
    SimulatorInterface,
    SimulatorState,
)

DIRECTIONS = ["north", "east", "south", "west"]
DELTA: dict[str, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


@dataclass
class RobotState:
    x: int = 0
    y: int = 0
    facing: str = "east"
    path: list[tuple[int, int]] = field(default_factory=list)
    steps_taken: int = 0
    obstacles_hit: int = 0
    pen_down: bool = False
    drawn_cells: list[tuple[int, int]] = field(default_factory=list)


class RobotSimulator(SimulatorInterface):
    """2D grid robot simulator for Grade 6–8 computational thinking projects."""

    def __init__(self, grid_size: int = 10) -> None:
        self._grid_size = grid_size
        self._obstacles: set[tuple[int, int]] = set()
        self._target: tuple[int, int] | None = None
        self._robot = RobotState()
        self._tick = 0
        self._event_log: list[str] = []

    @property
    def simulator_id(self) -> str:
        return "robot_sim"

    @property
    def display_name(self) -> str:
        return "Robot Grid Simulator"

    def reset(self, config: dict[str, Any] | None = None) -> SimulatorState:
        cfg = config or {}
        self._grid_size = cfg.get("grid_size", 10)
        self._robot = RobotState(
            x=cfg.get("start_x", 0),
            y=cfg.get("start_y", 0),
            facing=cfg.get("facing", "east"),
        )
        self._obstacles = {tuple(o) for o in cfg.get("obstacles", [])}  # type: ignore[misc]
        target = cfg.get("target")
        self._target = tuple(target) if target else (self._grid_size - 1, self._grid_size - 1)  # type: ignore[assignment]
        self._tick = 0
        self._event_log = ["Robot initialised"]
        return self.get_state()

    def execute_command(self, cmd: SimulatorCommand) -> CommandResult:
        self._tick += 1
        action = cmd.command.lower()
        steps = int(cmd.params.get("steps", 1))

        if action == "move_forward":
            return self._move(steps)
        if action == "turn_left":
            return self._turn(-1)
        if action == "turn_right":
            return self._turn(1)
        if action == "pen_down":
            self._robot.pen_down = True
            return CommandResult(True, "Pen lowered — robot will draw its path.", self.get_state())
        if action == "pen_up":
            self._robot.pen_down = False
            return CommandResult(True, "Pen lifted.", self.get_state())
        if action == "sense_distance":
            return self._sense_distance()

        return CommandResult(False, f"Unknown command: {action}", self.get_state())

    def get_state(self) -> SimulatorState:
        r = self._robot
        at_target = self._target and (r.x, r.y) == self._target
        return SimulatorState(
            simulator_id=self.simulator_id,
            tick=self._tick,
            entity_states={
                "robot_position": f"({r.x},{r.y})",
                "facing": r.facing,
                "steps_taken": r.steps_taken,
                "obstacles_hit": r.obstacles_hit,
                "pen_down": r.pen_down,
                "grid_size": self._grid_size,
                "target": str(self._target),
            },
            sensor_readings=[
                SensorReading("distance_forward", self._distance_forward(), "cells"),
                SensorReading("at_target", at_target or False),
            ],
            event_log=self._event_log[-5:],
            is_complete=bool(at_target),
            score=self._compute_score() if at_target else None,
        )

    def list_commands(self) -> list[str]:
        return ["move_forward", "turn_left", "turn_right", "pen_down", "pen_up", "sense_distance"]

    # ── Private ────────────────────────────────────────────────────────────────

    def _move(self, steps: int) -> CommandResult:
        dx, dy = DELTA[self._robot.facing]
        moved = 0
        for _ in range(steps):
            nx, ny = self._robot.x + dx, self._robot.y + dy
            if not (0 <= nx < self._grid_size and 0 <= ny < self._grid_size):
                self._event_log.append(f"Hit boundary at ({self._robot.x},{self._robot.y})")
                self._robot.obstacles_hit += 1
                break
            if (nx, ny) in self._obstacles:
                self._event_log.append(f"Obstacle at ({nx},{ny})!")
                self._robot.obstacles_hit += 1
                break
            self._robot.x, self._robot.y = nx, ny
            self._robot.path.append((nx, ny))
            if self._robot.pen_down:
                self._robot.drawn_cells.append((nx, ny))
            moved += 1
            self._robot.steps_taken += 1
        msg = f"Moved {moved} step(s) {self._robot.facing} to ({self._robot.x},{self._robot.y})"
        self._event_log.append(msg)
        return CommandResult(True, msg, self.get_state())

    def _turn(self, direction: int) -> CommandResult:
        idx = DIRECTIONS.index(self._robot.facing)
        self._robot.facing = DIRECTIONS[(idx + direction) % 4]
        msg = f"Now facing {self._robot.facing}"
        self._event_log.append(msg)
        return CommandResult(True, msg, self.get_state())

    def _sense_distance(self) -> CommandResult:
        d = self._distance_forward()
        msg = f"Distance forward: {d} cells"
        return CommandResult(True, msg, self.get_state())

    def _distance_forward(self) -> int:
        dx, dy = DELTA[self._robot.facing]
        d = 0
        x, y = self._robot.x, self._robot.y
        while True:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < self._grid_size and 0 <= ny < self._grid_size):
                break
            if (nx, ny) in self._obstacles:
                break
            d += 1
            x, y = nx, ny
        return d

    def _compute_score(self) -> float:
        path_len = self._robot.steps_taken
        optimal = abs(self._target[0]) + abs(self._target[1]) if self._target else 1  # type: ignore[index]
        efficiency = max(0.0, 1.0 - (path_len - optimal) / max(optimal, 1))
        penalty = self._robot.obstacles_hit * 0.1
        return round(max(0.0, efficiency - penalty), 3)
