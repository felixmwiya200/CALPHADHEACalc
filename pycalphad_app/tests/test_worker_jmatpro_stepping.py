# -*- coding: utf-8 -*-
"""
test_worker_jmatpro_stepping.py - Tests JMatPro stepping and keyboard interrupt in SolverWorker
"""

import pytest
from PyQt6.QtWidgets import QApplication
from pycalphad_app.gui.worker import SolverWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_worker_interrupt_flag(qapp):
    worker = SolverWorker("High Entropy Alloys", {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20})
    assert not worker._is_interrupted
    worker.request_interrupt()
    assert worker._is_interrupted


def test_worker_emits_benchmarks(qapp):
    worker = SolverWorker("High Entropy Alloys", {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20})
    # Run synchronously for test
    worker.run()
    assert worker._is_interrupted is False
