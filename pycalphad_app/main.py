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
from pycalphad_app.gui.styles import get_application_stylesheet


def main():
    # Enable high-DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("PyCALPHAD Materials Engineering Suite")
    app.setOrganizationName("SRM University-AP")
    app.setOrganizationDomain("srmap.edu.in")
    app.setStyleSheet(get_application_stylesheet())

    # Present startup database selector modal dialog matching standard CAE workflow
    startup_dlg = DatabaseModalDialog("Thermal Spray Coatings", theme="light")
    selected_db = "Thermal Spray Coatings"
    selected_preset = ""
    if startup_dlg.exec():
        selected_db = startup_dlg.get_selected_database()
        selected_preset = startup_dlg.get_selected_preset()

    # Launch Main Window
    window = MainWindow()
    # Set chosen database and preset archetype, then run initial calculation
    window.database_dock.db_combo.setCurrentText(selected_db)
    if selected_preset and hasattr(window.database_dock, "preset_combo"):
        window.database_dock.preset_combo.setCurrentText(selected_preset)
    window.database_dock.on_calculate_clicked()
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
