"""
main.py - Entry Point for PyCALPHAD Materials Engineering Suite
Initializes PyQt6 application, enables high-DPI scaling, and launches the desktop suite
directly into the signature JMatPro-style startup workspace.

Lead Materials Suite Developers: Felix Mwiya and Prof. (Dr.) Sheela Singh, SRM University-AP.
"""

import sys
import os

# Direct top-level imports to guarantee PyInstaller dependency discovery
import numpy as np
import scipy
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure pycalphad_app is discoverable on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pycalphad_app.gui.main_window import MainWindow
from pycalphad_app.gui.styles import get_application_stylesheet


def main():
    # Enable high-DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("PyCALPHAD Materials Engineering Suite")
    app.setOrganizationName("SRM University-AP")
    app.setOrganizationDomain("srmap.edu.in")
    app.setStyleSheet(get_application_stylesheet())

    # Launch Main Window directly into JMatPro-style startup workspace
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
