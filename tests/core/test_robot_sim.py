"""Tests for the robot simulator."""

from __future__ import annotations

import pytest

from src.core.simulator.interfaces import SimulatorCommand
from src.core.simulator.robot_sim import RobotSimulator


def test_robot_reset():
    sim = RobotSimulator(grid_size=10)
    state = sim.reset({"start_x": 0, "start_y": 0, "target": [9, 9]})
    assert state.entity_states["robot_position"] == "(0,0)"
    assert not state.is_complete


def test_robot_move_forward():
    sim = RobotSimulator()
    sim.reset()
    result = sim.execute_command(SimulatorCommand("move_forward", {"steps": 3}))
    assert result.success
    assert "(3,0)" in result.new_state.entity_states["robot_position"]


def test_robot_turn_and_move():
    sim = RobotSimulator()
    sim.reset({"start_x": 5, "start_y": 5})
    sim.execute_command(SimulatorCommand("turn_left"))  # now facing north
    result = sim.execute_command(SimulatorCommand("move_forward", {"steps": 2}))
    assert "(5,3)" in result.new_state.entity_states["robot_position"]


def test_robot_boundary():
    sim = RobotSimulator(grid_size=5)
    sim.reset({"start_x": 0, "start_y": 0})
    # Already at west edge, turn to face west then try to move
    sim.execute_command(SimulatorCommand("turn_left"))   # north
    sim.execute_command(SimulatorCommand("turn_left"))   # west
    result = sim.execute_command(SimulatorCommand("move_forward", {"steps": 3}))
    # Should not move (already at boundary)
    assert "(0,0)" in result.new_state.entity_states["robot_position"]
    assert result.new_state.entity_states["obstacles_hit"] > 0


def test_robot_target_completion():
    sim = RobotSimulator(grid_size=3)
    sim.reset({"start_x": 0, "start_y": 0, "target": [2, 0]})
    sim.execute_command(SimulatorCommand("move_forward", {"steps": 2}))
    state = sim.get_state()
    assert state.is_complete
    assert state.score is not None and state.score > 0


def test_robot_sense_distance():
    sim = RobotSimulator(grid_size=10)
    sim.reset({"start_x": 0, "start_y": 0})
    result = sim.execute_command(SimulatorCommand("sense_distance"))
    assert result.success
    assert "Distance forward: 9" in result.message
