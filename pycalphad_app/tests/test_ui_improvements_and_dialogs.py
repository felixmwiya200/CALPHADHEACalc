# -*- coding: utf-8 -*-
"""
test_ui_improvements_and_dialogs.py - Verification suite for Light Theme,
Ellingham Diagram, Molar Basis, Scrollable Layout, 21-Row Validation Table,
and Interactive Simulation Dialog Suite.

Lead Materials Suite Developers: Felix Mwiya and Prof. (Dr.) Sheela Singh, SRM University-AP.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pycalphad_app.gui.plot_theme import (
    apply_scientific_light_theme,
    get_calculated_pen,
    plot_experimental_scatter,
    SCIENTIFIC_LIGHT_THEME
)
from pycalphad_app.gui.styles import get_application_stylesheet
from pycalphad_app.gui.database_dock import DatabaseDock
from pycalphad_app.gui.plot_views.environmental_view import EnvironmentalView
from pycalphad_app.gui.plot_views.validation_view import ValidationView
from pycalphad_app.gui.database_modal import DatabaseModalDialog
from pycalphad_app.gui.advanced_simulation_dialogs import (
    ScheilSolidificationDialog,
    LatticeMismatchDialog,
    PrecipitationHardeningDialog,
    JominyHardenabilityDialog,
    MetastablePhasesDialog,
    ExtendedPropertiesDialog,
    HighTempStrengthDialog,
    FatigueModelingDialog,
    TTTCCTDiagramDialog,
    StackingFaultEnergyDialog,
    FEAExportHelper
)
import pyqtgraph as pg


class TestScientificLightTheme(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_scientific_light_theme_configuration(self):
        self.assertEqual(SCIENTIFIC_LIGHT_THEME["canvas_background"], "#FFFFFF")
        self.assertEqual(SCIENTIFIC_LIGHT_THEME["axis_spine"], "#334155")
        self.assertEqual(SCIENTIFIC_LIGHT_THEME["grid_line"], "#E2E8F0")

        plot = pg.PlotWidget()
        apply_scientific_light_theme(plot, title="Verification Light Theme", x_label="Temperature", y_label="Yield Strength")
        self.assertIsNotNone(plot)

    def test_experimental_scatter_mapping(self):
        plot = pg.PlotWidget()
        apply_scientific_light_theme(plot)
        scatter_item = plot_experimental_scatter(
            plot,
            [100, 200, 300],
            [10, 20, 30],
            name="Benchmark Data",
            symbol="diamond"
        )
        self.assertIsNotNone(scatter_item)

    def test_application_stylesheet_renders(self):
        qss = get_application_stylesheet()
        self.assertIn("QMainWindow", qss)
        self.assertIn("#FFFFFF", qss)
        self.assertIn("QScrollBar", qss)
        self.assertIn("QTabWidget", qss)


class TestDatabaseDockFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dock = DatabaseDock()

    def test_molar_ratio_radio_presence(self):
        self.assertTrue(hasattr(self.dock, "rb_mol"))
        self.assertEqual(self.dock.rb_mol.text(), "Molar ratio")

    def test_scroll_area_structure(self):
        self.assertIsNotNone(self.dock.scroll_area)
        self.assertTrue(self.dock.scroll_area.widgetResizable())

    def test_composition_basis_conversion(self):
        # Cantor alloy equiatomic CoCrFeMnNi in at%
        cantor_at = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
        wt_comp = self.dock.convert_basis_composition(cantor_at, "at%", "wt%")
        self.assertAlmostEqual(sum(wt_comp.values()), 100.0, places=2)

        # Convert back to at%
        recon_at = self.dock.convert_basis_composition(wt_comp, "wt%", "at%")
        for el in cantor_at:
            self.assertAlmostEqual(recon_at[el], 20.0, delta=0.5)

        # Convert to mol
        mol_comp = self.dock.convert_basis_composition(cantor_at, "at%", "mol")
        for el in cantor_at:
            self.assertAlmostEqual(mol_comp[el], 1.0, delta=0.05)


class TestEllinghamDiagramView(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = EnvironmentalView()

    def test_ellingham_subtab_present(self):
        self.assertIsNotNone(self.view.plot_ellingham)
        self.assertIsNotNone(self.view.table_oxides)

    def test_environmental_view_data_update(self):
        synthetic_results = {
            "composition": {"Cr": 0.2, "Al": 0.1, "Ni": 0.7},
            "atomic_composition": {"Cr": 0.2, "Al": 0.1, "Ni": 0.7},
            "environmental": {
                "T_C": [600, 700, 800, 900, 1000, 1100],
                "kp_mg2_cm4_s": [1e-6, 5e-6, 2e-5, 8e-5, 3e-4, 1e-3],
                "time_h": [0, 5, 10, 20, 50, 100],
                "mass_gain_mg_cm2": [0.0, 0.2, 0.4, 0.7, 1.2, 1.9],
                "Ecorr_V": -0.22,
                "icorr_uA_cm2": 0.85
            }
        }
        self.view.update_data(synthetic_results)
        self.assertGreater(self.view.table_oxides.rowCount(), 0)


class TestValidationView(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = ValidationView()

    def test_validation_table_comprehensive_benchmarks(self):
        synthetic_results = {
            "database_name": "High Entropy Alloys",
            "composition": {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2},
            "thermo": {"Solidus_K": 1585.0, "Liquidus_K": 1608.0, "Entropy_J_molK": 13.38},
            "mechanical": {"YieldStrength_MPa": 235.0, "UTS_MPa": 560.0, "Hardness_HV": 175.0, "Elongation_pct": 52.0},
            "transport": {"ThermalConductivity_W_mK": 14.5, "ElectricalResistivity_uOhm_cm": 98.0},
            "environmental": {"icorr_uA_cm2": 1.25}
        }
        self.view.update_data(synthetic_results)
        self.assertGreaterEqual(self.view.table.rowCount(), 20)
        self.assertIsNotNone(self.view.plot_parity)


class TestInteractiveSimulationDialogs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_scheil_solidification_dialog(self):
        comp = {"Al": 10.0, "Cr": 20.0, "Fe": 20.0, "Ni": 50.0}
        dlg = ScheilSolidificationDialog(comp)
        self.assertIsNotNone(dlg.plot_widget)

    def test_lattice_mismatch_dialog(self):
        comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
        dlg = LatticeMismatchDialog(comp)
        self.assertGreater(dlg.table.rowCount(), 0)

    def test_precipitation_hardening_dialog(self):
        dlg = PrecipitationHardeningDialog()
        self.assertIsNotNone(dlg.plot_widget)

    def test_jominy_hardenability_dialog(self):
        comp = {"C": 0.4, "Mn": 0.8, "Cr": 1.0, "Mo": 0.2, "Fe": 97.6}
        dlg = JominyHardenabilityDialog(comp)
        self.assertIsNotNone(dlg.plot_widget)

    def test_metastable_phases_dialog(self):
        comp = {"Ti": 90.0, "Al": 6.0, "V": 4.0}
        dlg = MetastablePhasesDialog(comp)
        self.assertTrue(dlg.chk_gp.isChecked())
        self.assertTrue(dlg.chk_martensite.isChecked())

    def test_extended_properties_dialog(self):
        comp = {"Fe": 70.0, "Cr": 18.0, "Ni": 10.0, "Mn": 2.0}
        dlg = ExtendedPropertiesDialog(comp)
        self.assertGreater(dlg.table.rowCount(), 0)

    def test_high_temp_strength_dialog(self):
        dlg = HighTempStrengthDialog({"Ni": 60.0, "Cr": 20.0, "Co": 20.0})
        self.assertIsNotNone(dlg.plot_widget)

    def test_fatigue_modeling_dialog(self):
        dlg = FatigueModelingDialog({"Fe": 98.0, "C": 0.4, "Mn": 1.6})
        self.assertIsNotNone(dlg.plot_widget)

    def test_ttt_cct_diagram_dialog(self):
        dlg = TTTCCTDiagramDialog({"Fe": 98.5, "C": 0.45, "Mn": 0.8, "Si": 0.25})
        self.assertIsNotNone(dlg.plot_widget)

    def test_stacking_fault_energy_dialog(self):
        dlg = StackingFaultEnergyDialog({"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0})
        self.assertIsNotNone(dlg.plot_widget)

    def test_fea_export_helper(self):
        deck = FEAExportHelper.generate_deform_card(
            "Fe-0.4C-1Cr",
            {"Solidus_K": 1690.0, "Liquidus_K": 1780.0},
            {"YieldStrength_MPa": 580.0, "UTS_MPa": 820.0}
        )
        self.assertIn("*MATERIAL: Fe-0.4C-1Cr", deck)
        self.assertIn("TSOLIDUS = 1690.00 K", deck)


class TestDatabaseModalDialog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_modal_initialization_and_preselection(self):
        dlg = DatabaseModalDialog("Thermal Spray Coatings", theme="light")
        self.assertEqual(dlg.get_selected_database(), "Thermal Spray Coatings")
        self.assertEqual(dlg.db_list.count(), 14)
        self.assertIn("Thermal Spray", dlg.lbl_db_name.text())
        self.assertGreater(dlg.chem_chips_layout.count(), 0)
        self.assertGreater(dlg.phases_layout.count(), 0)

    def test_search_filtering(self):
        dlg = DatabaseModalDialog(theme="light")
        dlg.search_box.setText("Nickel")
        visible = [dlg.db_list.item(i).text() for i in range(dlg.db_list.count()) if not dlg.db_list.item(i).isHidden()]
        self.assertTrue(any("Nickel" in name for name in visible))

        # Clear filter
        dlg.search_box.setText("")
        visible_all = [dlg.db_list.item(i).text() for i in range(dlg.db_list.count()) if not dlg.db_list.item(i).isHidden()]
        self.assertEqual(len(visible_all), 14)

    def test_domain_filtering(self):
        dlg = DatabaseModalDialog(theme="light")
        dlg.combo_domain.setCurrentText("Lightweight Aerospace Alloys")
        visible = [dlg.db_list.item(i).text() for i in range(dlg.db_list.count()) if not dlg.db_list.item(i).isHidden()]
        self.assertIn("Aluminium Alloy", visible)
        self.assertIn("Titanium Alloy", visible)
        self.assertIn("Magnesium Alloy", visible)
        self.assertNotIn("General Steel", visible)

    def test_archetype_preset_switching(self):
        dlg = DatabaseModalDialog("Thermal Spray Coatings", theme="light")
        self.assertGreaterEqual(dlg.combo_preset.count(), 2)
        # Select second preset
        first_preset = dlg.combo_preset.itemText(0)
        second_preset = dlg.combo_preset.itemText(1)
        dlg.combo_preset.setCurrentText(second_preset)
        self.assertEqual(dlg.get_selected_preset(), second_preset)

    def test_theme_switching(self):
        dlg = DatabaseModalDialog(theme="dark")
        self.assertEqual(dlg.current_theme, "dark")
        dlg.apply_theme("light")
        self.assertEqual(dlg.current_theme, "light")


if __name__ == "__main__":
    unittest.main()
