"""
test_splash_screen.py - Unit tests for QuickSplashScreen startup sequence
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pycalphad_app.gui.splash_screen import QuickSplashScreen


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_splash_screen_creation(qapp):
    splash = QuickSplashScreen()
    assert splash is not None
    assert splash.windowFlags() & Qt.WindowType.SplashScreen or splash.windowFlags() & Qt.WindowType.FramelessWindowHint
    
    # Test progress update
    splash.set_progress(30, "Loading thermodynamic models...")
    assert splash.progress_bar.value() == 30
    assert "Loading thermodynamic models..." in splash.status_label.text()

    splash.close()
