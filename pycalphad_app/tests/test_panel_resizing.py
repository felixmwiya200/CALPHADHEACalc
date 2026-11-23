"""
test_panel_resizing.py - Tests for non-clipping dock, resizability, and simple controls
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pycalphad_app.gui.database_dock import DatabaseDock
from pycalphad_app.gui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_database_dock_sizing_and_scroll_policy(qapp):
    dock = DatabaseDock()
    assert dock.minimumWidth() >= 320
    assert dock.scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert dock.scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    
    # Verify title is concise to prevent truncation
    assert len(dock.windowTitle()) <= 24

    # Verify buttons for stepped execution
    assert hasattr(dock, "btn_calc")
    assert hasattr(dock, "btn_step")
    assert hasattr(dock, "btn_reset")


def test_main_window_dock_and_splitter_setup(qapp):
    win = MainWindow()
    assert win.database_dock is not None
    assert win.database_dock.minimumWidth() >= 320
    
    # Check that calculation is NOT automatically executed without explicit trigger
    assert getattr(win, "last_results", None) is None or win.central_stack.currentIndex() == 0
    win.close()
