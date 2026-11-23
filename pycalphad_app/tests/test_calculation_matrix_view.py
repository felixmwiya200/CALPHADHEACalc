# -*- coding: utf-8 -*-
"""
test_calculation_matrix_view.py - Tests for the JMatPro Calculation Matrix View
Verifies all 21 buttons exist, adapt dynamically to alloy systems, and emit signals.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from pycalphad_app.gui.plot_views.calculation_matrix_view import CalculationMatrixView

app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestCalculationMatrixView(unittest.TestCase):
    def setUp(self):
        self.view = CalculationMatrixView("Nickel Based Superalloy")

    def test_all_23_buttons_exist(self):
        """Verifies that all 23 buttons from the 6 categorical groups are present."""
        expected_buttons = [
            # Group 1: Thermodynamic Properties
            self.view.btn_step_temp,
            self.view.btn_step_conc,
            self.view.btn_profile,
            self.view.btn_single,
            # Group 2: Solidification
            self.view.btn_phases_properties,
            self.view.btn_homogenisation,
            # Group 3: Mechanical Properties
            self.view.btn_strength_hardness,
            self.view.btn_high_temp_str,
            self.view.btn_creep,
            self.view.btn_flow_stress,
            self.view.btn_fatigue,
            # Group 4: Thermo-Physical Properties
            self.view.btn_extended_general,
            self.view.btn_dynamic,
            self.view.btn_gamma_mismatch,
            self.view.btn_sfe,
            # Group 5: Phase transformation
            self.view.btn_ttt_cct,
            self.view.btn_coarsening,
            self.view.btn_energy_changes,
            self.view.btn_isothermal,
            self.view.btn_heat_treatment,
            # Group 6: Data Export
            self.view.btn_forge,
            self.view.btn_deform,
            self.view.btn_simufact
        ]
        self.assertEqual(len(expected_buttons), 23)
        for btn in expected_buttons:
            self.assertIsNotNone(btn)
            self.assertGreater(len(btn.text()), 0)

    def test_superalloy_adaptation(self):
        """Gamma/Gamma' mismatch must be enabled for Nickel superalloys."""
        self.view.adapt_to_alloy("Nickel Based Superalloy")
        self.assertTrue(self.view.btn_gamma_mismatch.isEnabled())
        self.assertEqual(self.view.lbl_alloy_title.text(), "Nickel Based Superalloy")

    def test_steel_adaptation(self):
        """Gamma/Gamma' mismatch must be disabled for General Steel."""
        self.view.adapt_to_alloy("General Steel")
        self.assertFalse(self.view.btn_gamma_mismatch.isEnabled())
        self.assertIn("Quench & Temper", self.view.btn_heat_treatment.toolTip())

    def test_signal_emission(self):
        """Verifies that button clicks fire the corresponding pyqtSignals."""
        fired = []
        self.view.step_temperature_clicked.connect(lambda: fired.append("step_temp"))
        self.view.export_forge_clicked.connect(lambda: fired.append("forge"))
        self.view.creep_clicked.connect(lambda: fired.append("creep"))

        self.view.btn_step_temp.click()
        self.view.btn_forge.click()
        self.view.btn_creep.click()

        self.assertEqual(fired, ["step_temp", "forge", "creep"])


if __name__ == "__main__":
    unittest.main()
