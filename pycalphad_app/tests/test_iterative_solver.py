"""
test_iterative_solver.py - Unit tests for IterativeSolver state machine
"""

import pytest
from pycalphad_app.core.iterative_solver import IterativeSolver


def test_iterative_solver_initial_state():
    solver = IterativeSolver(
        database_name="High Entropy Alloys",
        composition={"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0},
        basis="at%",
        t_start=300.0,
        t_stop=1500.0,
        t_step=50.0
    )
    assert solver.current_step == 0
    assert solver.current_temp == 300.0
    assert not solver.is_completed


def test_iterative_solver_step_forward():
    solver = IterativeSolver(
        database_name="High Entropy Alloys",
        composition={"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0},
        basis="at%",
        t_start=300.0,
        t_stop=500.0,
        t_step=100.0
    )
    
    # Step 1: T = 300 K
    res1 = solver.step_forward()
    assert res1["step_index"] == 1
    assert res1["temperature"] == 300.0
    assert "phases" in res1
    assert solver.current_temp == 400.0
    assert not solver.is_completed

    # Step 2: T = 400 K
    res2 = solver.step_forward()
    assert res2["step_index"] == 2
    assert res2["temperature"] == 400.0
    assert solver.current_temp == 500.0

    # Step 3: T = 500 K (final step)
    res3 = solver.step_forward()
    assert res3["step_index"] == 3
    assert res3["temperature"] == 500.0
    assert solver.is_completed

    # Reset
    solver.reset()
    assert solver.current_step == 0
    assert solver.current_temp == 300.0
    assert not solver.is_completed


def test_iterative_solver_run_to_completion():
    solver = IterativeSolver(
        database_name="High Entropy Alloys",
        composition={"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0},
        basis="at%",
        t_start=300.0,
        t_stop=400.0,
        t_step=50.0
    )
    results = solver.run_to_completion()
    assert results is not None
    assert "thermo" in results
    assert "mechanical" in results
    assert "oxidation" in results
    assert solver.is_completed
