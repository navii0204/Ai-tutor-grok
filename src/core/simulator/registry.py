"""SimulatorRegistry — plugin registry for all simulator backends."""

from __future__ import annotations

from src.core.logging_config import get_logger
from .interfaces import SimulatorInterface

log = get_logger(__name__)


class SimulatorRegistry:
    def __init__(self) -> None:
        self._simulators: dict[str, SimulatorInterface] = {}

    def register(self, sim: SimulatorInterface) -> None:
        self._simulators[sim.simulator_id] = sim
        log.info("simulator_registered", id=sim.simulator_id, name=sim.display_name)

    def get(self, simulator_id: str) -> SimulatorInterface:
        if simulator_id not in self._simulators:
            raise KeyError(f"No simulator registered: '{simulator_id}'")
        return self._simulators[simulator_id]

    def list_simulators(self) -> list[dict[str, str]]:
        return [{"id": s.simulator_id, "name": s.display_name} for s in self._simulators.values()]
