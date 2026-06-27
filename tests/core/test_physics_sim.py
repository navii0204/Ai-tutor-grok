"""Tests for physics (projectile) simulator."""

from __future__ import annotations

import pytest

from src.core.simulator.interfaces import SimulatorCommand
from src.core.simulator.physics_sim import PhysicsSimulator


def test_physics_reset():
    sim = PhysicsSimulator()
    state = sim.reset()
    assert not state.is_complete
    assert state.entity_states["launched"] is False


def test_launch_and_land():
    sim = PhysicsSimulator(dt=0.05)
    sim.reset()
    sim.execute_command(SimulatorCommand("launch", {"angle": 45, "speed": 20}))
    result = sim.execute_command(SimulatorCommand("run_to_land"))
    assert result.success
    assert result.new_state.is_complete
    # Range should be non-trivial
    state = result.new_state
    assert float(state.entity_states["range"].replace(" m", "")) > 5


def test_45_degree_max_range():
    """45° should give maximum range compared to 30° and 60°."""
    def get_range(angle: float) -> float:
        sim = PhysicsSimulator(dt=0.05)
        sim.reset()
        sim.execute_command(SimulatorCommand("launch", {"angle": angle, "speed": 20}))
        sim.execute_command(SimulatorCommand("run_to_land"))
        state = sim.get_state()
        return float(state.entity_states["range"].replace(" m", ""))

    r30 = get_range(30)
    r45 = get_range(45)
    r60 = get_range(60)

    assert r45 > r30
    assert r45 > r60
    assert abs(r30 - r60) < 1.0  # symmetric property


def test_no_double_launch():
    sim = PhysicsSimulator()
    sim.reset()
    sim.execute_command(SimulatorCommand("launch", {"angle": 45, "speed": 10}))
    result = sim.execute_command(SimulatorCommand("launch", {"angle": 30, "speed": 10}))
    assert not result.success
