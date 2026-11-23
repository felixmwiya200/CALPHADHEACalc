# -*- coding: utf-8 -*-
"""
test_dialog_instantiation_safety.py - Verifies that all dialogs and calculation matrix actions
can be instantiated without TypeError or crashing.
"""

import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QDialog

from pycalphad_app.gui.main_window import MainWindow
from pycalphad_app.gui.options_dialogs import (
    ConcentrationSteppingDialog, SingleThermodynamicDialog,
    LatticeMismatchDialog, CreepModelingDialog, PrecipitationHardeningDialog
)
from pycalphad_app.gui.advanced_simulation_dialogs import (
    ScheilSolidificationDialog, HighTempStrengthDialog, FatigueModelingDialog,
    ExtendedPropertiesDialog, TTTCCTDiagramDialog, StackingFaultEnergyDialog,
    JominyHardenabilityDialog
)
from pycalphad_app.gui.utilities_dialogs import StressStrainCurveDialog

app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestDialogInstantiationSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = MainWindow()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def test_direct_dialog_instantiations(self):
        """Verifies each dialog opens with correct signature without raising TypeError."""
        comp = {"Ni": 70.0, "Cr": 20.0, "Al": 10.0}

        # 1. ConcentrationSteppingDialog
        d1 = ConcentrationSteppingDialog(parent=self.window, elements=list(comp.keys()))
        self.assertIsInstance(d1, QDialog)

        # 2. SingleThermodynamicDialog
        d2 = SingleThermodynamicDialog(parent=self.window)
        self.assertIsInstance(d2, QDialog)

        # 3. CreepModelingDialog
        d3 = CreepModelingDialog(parent=self.window)
        self.assertIsInstance(d3, QDialog)

        # 4. StressStrainCurveDialog
        d4 = StressStrainCurveDialog(parent=self.window)
        self.assertIsInstance(d4, QDialog)

        # 5. LatticeMismatchDialog
        d5 = LatticeMismatchDialog(parent=self.window)
        self.assertIsInstance(d5, QDialog)

        # 6. ScheilSolidificationDialog
        d6 = ScheilSolidificationDialog(comp, parent=self.window)
        self.assertIsInstance(d6, QDialog)

        # 7. HighTempStrengthDialog
        d7 = HighTempStrengthDialog(comp, parent=self.window)
        self.assertIsInstance(d7, QDialog)

        # 8. FatigueModelingDialog
        d8 = FatigueModelingDialog(comp, parent=self.window)
        self.assertIsInstance(d8, QDialog)

        # 9. ExtendedPropertiesDialog
        d9 = ExtendedPropertiesDialog(comp, parent=self.window)
        self.assertIsInstance(d9, QDialog)

        # 10. TTTCCTDiagramDialog
        d10 = TTTCCTDiagramDialog(comp, parent=self.window)
        self.assertIsInstance(d10, QDialog)

        # 11. StackingFaultEnergyDialog
        d11 = StackingFaultEnergyDialog(comp, parent=self.window)
        self.assertIsInstance(d11, QDialog)

        # 12. JominyHardenabilityDialog
        d12 = JominyHardenabilityDialog(comp, parent=self.window)
        self.assertIsInstance(d12, QDialog)

    @patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted)
    def test_all_matrix_action_handlers(self, mock_exec):
        """Simulates clicking all matrix buttons through MainWindow methods."""
        win = self.window

        # Category 1: Thermodynamic Properties
        win.on_matrix_step_concentration()
        win.on_matrix_single()

        # Category 2: Solidification
        win.on_matrix_phases_properties()
        win.on_matrix_homogenisation()

        # Category 3: Mechanical Properties
        win.on_matrix_strength_hardness()
        win.on_matrix_high_temp_strength()
        win.on_matrix_creep()
        win.on_matrix_flow_stress()
        win.on_matrix_fatigue()

        # Category 4: Thermo-Physical Properties
        win.on_matrix_extended_general()
        win.on_matrix_dynamic()
        win.on_matrix_gamma_mismatch()
        win.on_matrix_stacking_fault_energy()

        # Category 5: Phase transformation
        win.on_matrix_ttt_cct()
        win.on_matrix_coarsening()
        win.on_matrix_energy_changes()
        win.on_matrix_isothermal()
        win.on_matrix_heat_treatment()

        self.assertGreater(mock_exec.call_count, 5)

    def test_equilibrium_step_point_phase_transition_safety(self):
        """Simulates phases precipitating and disappearing without shape mismatch crash."""
        eq = self.window.tab_equilibrium
        eq.step_history_t.clear()
        eq.step_history_phases.clear()

        # Step 1: Only Liquid present
        eq.update_step_point({
            "temperature": 1600.0,
            "phases": {"Liquid": 1.0},
            "step_index": 1
        })
        self.assertEqual(len(eq.step_history_t), 1)

        # Step 2: Gamma precipitated, Liquid decreased
        eq.update_step_point({
            "temperature": 1400.0,
            "phases": {"Liquid": 0.6, "Gamma": 0.4},
            "step_index": 2
        })
        self.assertEqual(len(eq.step_history_t), 2)
        # Gamma must have been padded to length 2
        self.assertEqual(len(eq.step_history_phases["Gamma"]), 2)
        self.assertEqual(eq.step_history_phases["Gamma"][0], 0.0)
        self.assertEqual(eq.step_history_phases["Gamma"][1], 0.4)

        # Step 3: Liquid disappeared, Carbide precipitated
        eq.update_step_point({
            "temperature": 1000.0,
            "phases": {"Gamma": 0.85, "Carbide": 0.15},
            "step_index": 3
        })
        self.assertEqual(len(eq.step_history_t), 3)
        self.assertEqual(len(eq.step_history_phases["Carbide"]), 3)
        self.assertEqual(len(eq.step_history_phases["Liquid"]), 3)
        self.assertEqual(eq.step_history_phases["Liquid"][2], 0.0)


if __name__ == "__main__":
    unittest.main()
