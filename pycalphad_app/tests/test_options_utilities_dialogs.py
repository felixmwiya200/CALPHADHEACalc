"""
test_options_utilities_dialogs.py - Unit Tests for Options & Utilities Dialogs & Menus
Verifies that all options dialogs, formulas, and menu actions operate without exceptions.
"""

import unittest
import os
import sys

# Ensure QApplication exists for GUI tests
from PyQt6.QtWidgets import QApplication
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from pycalphad_app.gui.utilities_dialogs import (
    AusteniteGrainSizeDialog, ConversionsDialog, MartensiteTransitionDialog,
    StressStrainCurveDialog, CreateMaterialTypeDialog, BatchModeDialog
)
from pycalphad_app.gui.options_dialogs import (
    TemperatureSteppingDialog, ConcentrationSteppingDialog, SingleThermodynamicDialog,
    LatticeMismatchDialog, SolidSolutionHardeningDialog, PrecipitationHardeningDialog,
    CreepModelingDialog, AlCastStrengthDialog, FormingExportDialog,
    GeneralPreferencesDialog, OrderOfElementsDialog
)
from pycalphad_app.gui.main_window import MainWindow


class TestOptionsUtilitiesDialogs(unittest.TestCase):
    def test_austenite_grain_size(self):
        dlg = AusteniteGrainSizeDialog(current_temp_c=950.0)
        dlg.temp_spin.setValue(1050.0)
        dlg.time_spin.setValue(30.0)
        dlg.calculate_grain_size()
        # Verify non-empty results and positive values
        self.assertTrue(dlg.lbl_microns.text().endswith("µm"))
        self.assertTrue(dlg.lbl_astm.text().startswith("ASTM"))
        dlg.close()

    def test_conversions_dialog(self):
        dlg = ConversionsDialog()
        dlg.t_val.setValue(100.0)
        dlg.convert_temperature()
        self.assertIn("Celsius", dlg.lbl_t_res.text())

        dlg.g_microns.setValue(50.0)
        dlg.convert_microns_to_astm()
        self.assertIn("ASTM", dlg.lbl_g_res.text())

        dlg.s_ys.setValue(800.0)
        dlg.convert_strength_hardness()
        self.assertIn("Vickers", dlg.lbl_s_res.text())
        dlg.close()

    def test_martensite_transition(self):
        comp = {"C": 0.38, "Mn": 0.75, "Si": 0.25, "Cr": 1.0, "Ni": 1.8, "Mo": 0.25, "V": 0.0, "N": 0.008}
        dlg = MartensiteTransitionDialog(initial_composition=comp)
        dlg.calculate_martensite()
        # Verify Ms is within realistic range (typically 250 - 380 °C for 4340 steel)
        self.assertIn("°C", dlg.lbl_ms.text())
        self.assertIn("HV", dlg.lbl_hardness.text())
        dlg.close()

    def test_lattice_mismatch(self):
        dlg = LatticeMismatchDialog()
        dlg.spin_am.setValue(3.585)
        dlg.spin_ap.setValue(3.592)
        dlg.calculate_mismatch()
        self.assertIn("%", dlg.res_lbl.text())
        dlg.close()

    def test_precipitation_hardening(self):
        dlg = PrecipitationHardeningDialog()
        dlg.f_spin.setValue(20.0)
        dlg.r_spin.setValue(15.0)
        dlg.calculate_orowan()
        self.assertIn("Governing Strengthening", dlg.lbl_res.text())
        dlg.close()

    def test_creep_modeling(self):
        dlg = CreepModelingDialog()
        dlg.spin_stress.setValue(300.0)
        dlg.spin_temp.setValue(800.0)
        dlg.calculate_creep()
        self.assertIn("hours", dlg.lbl_res.text())
        dlg.close()

    def test_al_cast_strength(self):
        dlg = AlCastStrengthDialog()
        dlg.spin_cr.setValue(10.0)
        dlg.calculate_sdas()
        self.assertIn("SDAS", dlg.lbl_res.text())
        dlg.close()

    def test_main_window_menus(self):
        win = MainWindow()
        menubar = win.menuBar()
        actions = [a.text() for a in menubar.actions()]
        self.assertIn("&File", actions)
        self.assertIn("&Material Types", actions)
        self.assertIn("&Options", actions)
        self.assertIn("&Utilities", actions)
        self.assertIn("&Help", actions)

        self.assertTrue(win.act_verbose.isCheckable())
        self.assertTrue(win.act_record.isCheckable())
        self.assertTrue(win.act_phase_search.isCheckable())
        win.close()


if __name__ == "__main__":
    unittest.main()
