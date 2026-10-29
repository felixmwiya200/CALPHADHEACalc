"""
main.py - Entry Point for PyCALPHAD Materials Engineering Suite
Initializes PyQt6 application, enables high-DPI scaling, presents startup database
selection dialog matching user requirement, and launches the desktop suite.
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
from pycalphad_app.gui.database_modal import DatabaseModalDialog


def main():
    # Enable high-DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("PyCALPHAD Materials Engineering Suite")
    app.setOrganizationName("SRM University-AP")
    app.setOrganizationDomain("srmap.edu.in")

    # Present startup database selector modal dialog as requested
    startup_dlg = DatabaseModalDialog("Thermal Spray Coatings")
    selected_db = "Thermal Spray Coatings"
    if startup_dlg.exec():
        selected_db = startup_dlg.get_selected_database()

    # Launch Main Window
    window = MainWindow()
    # Set chosen database and run initial calculation
    window.database_dock.db_combo.setCurrentText(selected_db)
    window.database_dock.on_calculate_clicked()
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
