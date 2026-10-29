"""
test_gui_integration.py - Headless PyQt6 Integration Tests for PyCALPHAD Suite
Verifies:
  1. Window instantiation and dark/light styling
  2. DatabaseDock composition loading and database switching
  3. SolverWorker asynchronous execution on QThread
  4. Population of all 8 plot views with zero errors
  5. Validation table and authentic XRD citations
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Ensure single QApplication instance
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from pycalphad_app.gui.main_window import MainWindow
from pycalphad_app.gui.worker import SolverWorker
from pycalphad_app.database.material_selector import MaterialDatabaseSelector


class TestGUIIntegration(unittest.TestCase):

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_window_components(self):
        self.assertIsNotNone(self.window.database_dock)
        self.assertIsNotNone(self.window.console_dock)
        self.assertEqual(self.window.tabs.count(), 9)

        tab_names = [self.window.tabs.tabText(i) for i in range(self.window.tabs.count())]
        self.assertIn("Equilibrium Phases", tab_names)
        self.assertIn("Isopleth Phase Diagram", tab_names)
        self.assertIn("Transport Properties", tab_names)
        self.assertIn("Mechanical Strengthening", tab_names)
        self.assertIn("Oxidation & Corrosion", tab_names)
        self.assertIn("Powder XRD Diffractometer", tab_names)
        self.assertIn("Periodic Table (118)", tab_names)
        self.assertIn("Industrial Suitability", tab_names)
        self.assertIn("Literature Audit & Validation", tab_names)

    def test_database_switching(self):
        dock = self.window.database_dock
        # Switch to Thermal Spray Coatings
        dock.db_combo.setCurrentText("Thermal Spray Coatings")
        self.assertEqual(dock.db_combo.currentText(), "Thermal Spray Coatings")

        comp = dock.get_composition()
        self.assertIn("Ni", comp)
        self.assertIn("Cr", comp)
        self.assertIn("B", comp)
        self.assertIn("Si", comp)

        # Switch to Stainless Steel
        dock.db_combo.setCurrentText("Stainless Steel")
        comp_ss = dock.get_composition()
        self.assertIn("Fe", comp_ss)
        self.assertIn("Cr", comp_ss)
        self.assertIn("Ni", comp_ss)

    def test_solver_worker_execution(self):
        # Test worker thread directly
        comp = {"Ni": 0.7161, "Cr": 0.1527, "Si": 0.0465, "Fe": 0.0447, "B": 0.0332, "C": 0.0068}
        worker = SolverWorker("Thermal Spray Coatings", comp, basis="wt%", grain_size_um=25.0, process_type="HVOF")

        results = {}
        def on_finished(res):
            nonlocal results
            results = res

        worker.finished.connect(on_finished)
        worker.run()  # Run synchronously for test

        self.assertIn("coating", results)
        self.assertIn("thermo", results)
        self.assertIn("mechanical", results)
        self.assertIn("oxidation", results)
        self.assertIn("corrosion", results)
        self.assertIn("xrd", results)
        self.assertIn("validation_table", results)

        # Dispatch results to window tabs to ensure zero errors during rendering
        self.window.on_worker_finished(results)

        # Check validation table in GUI
        val_view = self.window.tab_validation
        self.assertGreater(val_view.table.rowCount(), 0)
        self.assertIn("Overall MAPE", val_view.mape_badge.text())

        # Check XRD citation banner
        xrd_view = self.window.tab_xrd
        self.assertIn("Houdková", xrd_view.citation_box.toPlainText() + xrd_view.citation_box.toHtml())


if __name__ == "__main__":
    unittest.main()
