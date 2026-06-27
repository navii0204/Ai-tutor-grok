"""PhysicsSimulator — projectile motion / forces for deeper STEM reasoning.

Students set initial conditions and observe outcomes; the Socratic engine
asks questions about what will happen BEFORE each simulation tick runs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .interfaces import (
    CommandResult,
    SensorReading,
    SimulatorCommand,
    SimulatorInterface,
    SimulatorState,
)

G = 9.8  # m/s²


@dataclass
class Projectile:
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 1.0
    launched: bool = False
    landed: bool = False
    time_elapsed: float = 0.0
    trajectory: list[tuple[float, float]] = field(default_factory=list)


class PhysicsSimulator(SimulatorInterface):
    """Projectile motion simulator for conceptual physics understanding."""

    def __init__(self, dt: float = 0.1) -> None:
        self._dt = dt
        self._projectile = Projectile()
        self._tick = 0
        self._event_log: list[str] = []
        self._air_resistance: float = 0.0

    @property
    def simulator_id(self) -> str:
        return "physics_sim"

    @property
    def display_name(self) -> str:
        return "Projectile Motion Lab"

    def reset(self, config: dict[str, Any] | None = None) -> SimulatorState:
        cfg = config or {}
        self._projectile = Projectile(
            x=float(cfg.get("x0", 0)),
            y=float(cfg.get("y0", 0)),
            mass=float(cfg.get("mass", 1.0)),
        )
        self._air_resistance = float(cfg.get("air_resistance", 0.0))
        self._tick = 0
        self._event_log = ["Projectile reset"]
        return self.get_state()

    def execute_command(self, cmd: SimulatorCommand) -> CommandResult:
        self._tick += 1
        action = cmd.command.lower()

        if action == "launch":
            return self._launch(
                angle_deg=float(cmd.params.get("angle", 45)),
                speed=float(cmd.params.get("speed", 20)),
            )
        if action == "step":
            n = int(cmd.params.get("n", 1))
            for _ in range(n):
                self._step()
            return CommandResult(True, f"Stepped {n} tick(s)", self.get_state())
        if action == "run_to_land":
            steps = 0
            while not self._projectile.landed and steps < 10000:
                self._step()
                steps += 1
            return CommandResult(True, f"Ran {steps} steps until landing", self.get_state())
        if action == "set_air_resistance":
            self._air_resistance = float(cmd.params.get("value", 0))
            return CommandResult(True, f"Air resistance set to {self._air_resistance}", self.get_state())

        return CommandResult(False, f"Unknown command: {action}", self.get_state())

    def get_state(self) -> SimulatorState:
        p = self._projectile
        range_x = p.x if p.landed else None
        max_height = max((pt[1] for pt in p.trajectory), default=0) if p.trajectory else 0

        return SimulatorState(
            simulator_id=self.simulator_id,
            tick=self._tick,
            entity_states={
                "position": f"({p.x:.2f}, {p.y:.2f}) m",
                "velocity": f"({p.vx:.2f}, {p.vy:.2f}) m/s",
                "speed": f"{math.hypot(p.vx, p.vy):.2f} m/s",
                "time_elapsed": f"{p.time_elapsed:.2f} s",
                "launched": p.launched,
                "landed": p.landed,
                "range": f"{range_x:.2f} m" if range_x is not None else "—",
                "max_height_so_far": f"{max_height:.2f} m",
                "air_resistance": self._air_resistance,
            },
            sensor_readings=[
                SensorReading("height", round(p.y, 3), "m"),
                SensorReading("speed", round(math.hypot(p.vx, p.vy), 3), "m/s"),
            ],
            event_log=self._event_log[-5:],
            is_complete=p.landed,
            score=None,
        )

    def list_commands(self) -> list[str]:
        return ["launch", "step", "run_to_land", "set_air_resistance"]

    # ── Private ────────────────────────────────────────────────────────────────

    def _launch(self, angle_deg: float, speed: float) -> CommandResult:
        if self._projectile.launched:
            return CommandResult(False, "Already launched. Reset first.", self.get_state())
        rad = math.radians(angle_deg)
        self._projectile.vx = speed * math.cos(rad)
        self._projectile.vy = speed * math.sin(rad)
        self._projectile.launched = True
        msg = f"Launched at {angle_deg}° with speed {speed} m/s"
        self._event_log.append(msg)
        return CommandResult(True, msg, self.get_state())

    def _step(self) -> None:
        p = self._projectile
        if not p.launched or p.landed:
            return
        drag_x = -self._air_resistance * p.vx
        drag_y = -self._air_resistance * p.vy
        p.vx += drag_x * self._dt
        p.vy += (-G + drag_y) * self._dt
        p.x += p.vx * self._dt
        p.y += p.vy * self._dt
        p.time_elapsed += self._dt
        p.trajectory.append((round(p.x, 3), round(p.y, 3)))
        if p.y <= 0 and p.time_elapsed > 0.01:
            p.y = 0.0
            p.landed = True
            self._event_log.append(f"Landed at x={p.x:.2f} m after {p.time_elapsed:.2f} s")
