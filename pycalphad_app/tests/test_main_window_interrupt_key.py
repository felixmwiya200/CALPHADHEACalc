# -*- coding: utf-8 -*-
"""
test_main_window_interrupt_key.py - Tests global 's' key interception on MainWindow
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from pycalphad_app.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_key_press_s_interrupts_worker(qapp):
    win = MainWindow()
    win.start_calculation("High Entropy Alloys", {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20})
    assert win.current_worker is not None

    # Simulate 's' keypress
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_S, Qt.KeyboardModifier.NoModifier, "s")
    win.keyPressEvent(event)

    assert win.current_worker._is_interrupted is True
    win.current_worker.wait(3000)
    win.close()
