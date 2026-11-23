# -*- coding: utf-8 -*-
"""
test_piecewise_and_tables.py - Unit Tests for OriginLab Graph Styling,
Interactive Scientific Tables, Verified DOI Resolution, and Piecewise Function Engine.
"""

import unittest
import os
import sys
import tempfile
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg

# Ensure QApplication exists for GUI tests
app = QApplication.instance()
if app is None:
    app = QApplication([sys.argv[0], "-platform", "offscreen"])

from pycalphad_app.core.piecewise_engine import PiecewiseEngine, PROPERTIES_LIST
from pycalphad_app.gui.widgets.scientific_table import ScientificTableWidget, is_valid_doi
from pycalphad_app.gui.plot_theme import apply_scientific_light_theme, plot_origin_parity
from pycalphad_app.gui.plot_views.validation_view import ValidationView
from pycalphad_app.gui.plot_views.applications_view import ApplicationsView
from pycalphad_app.gui.options_dialogs import CreepModelingDialog


class TestPiecewiseEngine(unittest.TestCase):
    def setUp(self):
        self.thermo = {
            "T_Solidus": 1243.15,
            "T_Liquidus": 1318.15,
            "Density_g_cm3": 8.24,
            "ThermalConductivity_W_mK": 16.5,
            "SpecificHeat_J_kgK": 462.0,
            "dH_fus": 260.0,
            "ElectricalResistivity": 95.0,
            "CTE_1e6_K": 14.1
        }
        self.mech = {
            "YoungsModulus_GPa": 208.0,
            "YieldStrength_RT_MPa": 1265.0,
            "PoissonsRatio": 0.308
        }

    def test_properties_list_count(self):
        props = PiecewiseEngine.get_available_properties()
        self.assertEqual(len(props), 21)
        self.assertIn("Thermal Conductivity k(T) [W/(m*K)]", props)
        self.assertIn("Apparent Heat Capacity Cp_app(T) [J/(kg*K)] (Phase Change)", props)
        self.assertIn("Liquid Surface Tension gamma(T) [N/m] (Marangoni)", props)

    def test_thermal_conductivity_piecewise(self):
        res = PiecewiseEngine.generate_property_piecewise(
            "Thermal Conductivity k(T) [W/(m*K)]", self.thermo, self.mech, "Alloy-A"
        )
        self.assertIn("pw_k_solid(T)", res["code_text"])
        self.assertIn("pw_k_mushy(T)", res["code_text"])
        self.assertIn("pw_k_liquid(T)", res["code_text"])
        self.assertIn("flc2hs", res["code_text"])
        self.assertAlmostEqual(res["ts"], 1243.15)
        self.assertAlmostEqual(res["tl"], 1318.15)
        self.assertEqual(len(res["discrete_intervals"]), 3)

    def test_apparent_heat_capacity_latent_peak(self):
        res = PiecewiseEngine.generate_property_piecewise(
            "Apparent Heat Capacity Cp_app(T) [J/(kg*K)] (Phase Change)", self.thermo, self.mech, "Alloy-A"
        )
        self.assertIn("Latent Peak", res["code_text"])
        self.assertIn("Cp_app_cont(T)", res["code_text"])
        self.assertGreater(len(res["discrete_intervals"]), 0)

    def test_batch_generate_all(self):
        all_res = PiecewiseEngine.generate_all_properties(self.thermo, self.mech, "Test-Alloy")
        self.assertEqual(len(all_res), 21)
        for p, data in all_res.items():
            self.assertTrue(len(data["code_text"]) > 50)
            self.assertTrue(len(data["discrete_intervals"]) > 0)


class TestScientificTableWidget(unittest.TestCase):
    def test_doi_regex_validation(self):
        # Valid DOIs
        self.assertTrue(is_valid_doi("10.1007/s11666-014-0112-9"))
        self.assertTrue(is_valid_doi("10.1016/j.surfcoat.2004.10.141"))
        self.assertTrue(is_valid_doi("10.1016/j.wear.2006.05.009"))
        self.assertTrue(is_valid_doi("10.1038/nature12345"))

        # Invalid or plain references
        self.assertFalse(is_valid_doi(""))
        self.assertFalse(is_valid_doi(None))
        self.assertFalse(is_valid_doi("ISO 14919 Standard"))
        self.assertFalse(is_valid_doi("ASTM E9 / Houdkova (2014)"))
        self.assertFalse(is_valid_doi("https://doi.org/10.1016"))

    def test_table_tsv_serialization(self):
        table = ScientificTableWidget(2, 2)
        table.setHorizontalHeaderLabels(["Col A", "Col B"])
        from PyQt6.QtWidgets import QTableWidgetItem
        table.setItem(0, 0, QTableWidgetItem("Val 1"))
        table.setItem(0, 1, QTableWidgetItem("Val 2"))
        table.setItem(1, 0, QTableWidgetItem("Val 3"))
        table.setItem(1, 1, QTableWidgetItem("Val 4"))

        tsv = ScientificTableWidget.table_to_tsv(table, include_headers=True)
        lines = tsv.strip().split("\n")
        self.assertEqual(lines[0], "Col A\tCol B")
        self.assertEqual(lines[1], "Val 1\tVal 2")
        self.assertEqual(lines[2], "Val 3\tVal 4")

    def test_set_verified_doi_cell(self):
        table = ScientificTableWidget(2, 2)
        table.set_verified_doi_cell(0, 0, "Houdkova et al. (2014)", "10.1007/s11666-014-0112-9")
        table.set_verified_doi_cell(1, 0, "ISO 14919 Standard", "")

        # Row 0: Verified DOI should have rich link label and valid underlying text
        widget0 = table.cellWidget(0, 0)
        self.assertIsInstance(widget0, QLabel)
        self.assertIn("href='https://doi.org/10.1007/s11666-014-0112-9'", widget0.text())
        self.assertIn("https://doi.org/10.1007/s11666-014-0112-9", table.item(0, 0).text())

        # Row 1: Unverified should have plain text label without href
        widget1 = table.cellWidget(1, 0)
        self.assertIsInstance(widget1, QLabel)
        self.assertNotIn("href=", widget1.text())
        self.assertEqual(table.item(1, 0).text(), "ISO 14919 Standard")


class TestOriginLabGraphTheme(unittest.TestCase):
    def test_originlab_box_axes_and_ticks(self):
        plot = pg.PlotWidget()
        apply_scientific_light_theme(
            plot,
            title="OriginLab Test Plot",
            x_label="Temperature / K",
            y_label="Enthalpy / (kJ·kg⁻¹)"
        )
        # All 4 bounding axes must be visible
        for ax_name in ("left", "bottom", "top", "right"):
            ax = plot.getAxis(ax_name)
            self.assertIsNotNone(ax)
            self.assertTrue(ax.isVisible())
            # Inward ticks: tickLength must be negative (-6)
            self.assertEqual(ax.style.get("tickLength"), -6)

        # Top and Right spines must suppress numeric text labels
        self.assertFalse(plot.getAxis("top").style.get("showValues"))
        self.assertFalse(plot.getAxis("right").style.get("showValues"))
        # Left and Bottom spines must display numeric text labels
        self.assertTrue(plot.getAxis("bottom").style.get("showValues"))
        self.assertTrue(plot.getAxis("left").style.get("showValues"))

    def test_plot_origin_parity(self):
        plot = pg.PlotWidget()
        apply_scientific_light_theme(plot, title="Parity Test")
        plot_origin_parity(plot, x_range=(0.8, 1.2), show_confidence_corridor=True)
        # Parity plot adds 1:1 line plus confidence corridor curves
        items = plot.getPlotItem().listDataItems()
        self.assertGreaterEqual(len(items), 4)


class TestValidationAndApplicationsViews(unittest.TestCase):
    def test_validation_view_structure(self):
        v = ValidationView()
        self.assertIsInstance(v.table, ScientificTableWidget)
        self.assertEqual(v.tabs.count(), 2)
        self.assertEqual(v.tabs.tabText(0), "Literature Validation & OriginLab Parity")
        self.assertEqual(v.tabs.tabText(1), "COMSOL Multiphysics Code Vault (Piecewise & Smooth Steps)")

        # Update data test
        data = {
            "validation_table": [
                {
                    "Property": "Vickers Microhardness [HV]",
                    "Calculated": 750.0,
                    "Experimental": 748.0,
                    "Deviation": 2.0,
                    "ErrorPercent": 0.27,
                    "Reference": "Houdkova et al. (2014)",
                    "DOI": "10.1007/s11666-014-0112-9"
                }
            ],
            "thermo": {"T_Solidus": 1200.0, "T_Liquidus": 1300.0}
        }
        v.update_data(data)
        self.assertEqual(v.table.rowCount(), 1)
        self.assertIn("750.00", v.table.item(0, 1).text())
        self.assertIn("Houdkova", v.table.item(0, 5).text())

    def test_applications_view_structure(self):
        av = ApplicationsView()
        self.assertIsInstance(av.table, ScientificTableWidget)
        data = {
            "application_scores": [
                {"name": "Tooling & Metal Extrusion Dies", "score": 95.2, "tier": "Prime Candidate", "bottleneck": "Balanced"}
            ]
        }
        av.update_data(data)
        self.assertEqual(av.table.rowCount(), 1)
        self.assertEqual(av.table.item(0, 0).text(), "Tooling & Metal Extrusion Dies")


class TestDialogContrastAndVisibility(unittest.TestCase):
    def test_creep_dialog_styling(self):
        dlg = CreepModelingDialog()
        # Verify result label has high-contrast styling with explicit text color
        style = dlg.lbl_res.styleSheet()
        self.assertIn("color: #0F172A", style)
        self.assertIn("background: #F8FAFC", style)
        self.assertIn("border: 1px solid #CBD5E1", style)
        self.assertNotIn("background: #252526", style)


if __name__ == "__main__":
    unittest.main()
