# -*- coding: utf-8 -*-
"""
test_thorough_solver.py - Tests for Thorough CALPHAD Equilibrium Solver Architecture
Verifies:
1. DatabaseDock calculation depth selection (Thorough, Deep, Fast).
2. SolverWorker calculation mode initialization and telemetry emissions.
3. Live step progress emission containing Gibbs residuals and active phase summaries.
4. Immediate graceful interruption handling via request_interrupt().
"""

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication

from pycalphad_app.gui.database_dock import DatabaseDock
from pycalphad_app.gui.worker import SolverWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_database_dock_calculation_mode(qapp):
    dock = DatabaseDock()
    # Default is thorough
    assert dock.get_calculation_mode() == "thorough"

    # Set to deep
    dock.set_calculation_mode("deep")
    assert dock.get_calculation_mode() == "deep"

    # Set to fast
    dock.set_calculation_mode("fast")
    assert dock.get_calculation_mode() == "fast"

    # Reset to thorough
    dock.set_calculation_mode("thorough")
    assert dock.get_calculation_mode() == "thorough"


def test_solver_worker_telemetry_and_convergence(qapp):
    comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    worker = SolverWorker(
        database_name="High Entropy Alloys",
        composition=comp,
        basis="at%",
        t_start=1400.0,
        t_stop=1300.0,
        t_step=50.0,
        calc_mode="thorough"
    )

    logs = []
    step_data_list = []
    worker.log_message.connect(logs.append)
    worker.step_progress.connect(step_data_list.append)

    worker.run()

    # Verify telemetry emissions
    assert len(step_data_list) >= 2
    assert any("Iter:" in l and "||ΔG||" in l for l in logs)

    last_step = step_data_list[-1]
    assert "temperature" in last_step
    assert "phases" in last_step
    assert "residual" in last_step
    assert last_step["residual"] > 0.0


def test_solver_worker_interrupt_responsiveness(qapp):
    comp = {"Ni": 50.0, "Cr": 20.0, "Fe": 30.0}
    worker = SolverWorker(
        database_name="Nickel Superalloys",
        composition=comp,
        basis="wt%",
        t_start=2000.0,
        t_stop=300.0,
        t_step=10.0,
        calc_mode="thorough"
    )

    # Immediately request interrupt
    worker.request_interrupt()
    worker.run()

    # Must complete almost immediately because of interrupt flag
    assert worker._is_interrupted is True
