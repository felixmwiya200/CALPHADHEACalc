# -*- coding: utf-8 -*-
"""
test_cae_export_manager.py - Unit test suite for CAE / FEA Material Exporters
Tests FORGE (.mat), DEFORM (.dat), and Simufact (.xml) export fidelity.
"""

import os
import tempfile
import unittest
from pycalphad_app.core.cae_export_manager import CAEExportManager


class TestCAEExportManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.alloy_name = "Inconel 718"
        self.comp = {"Ni": 52.5, "Cr": 19.0, "Fe": 18.5, "Nb": 5.1, "Mo": 3.0, "Ti": 0.9, "Al": 0.5, "C": 0.04}
        self.thermo = {"Solidus_K": 1533.15, "Liquidus_K": 1609.15}
        self.mech = {"YieldStrength_MPa": 1180.0, "UTS_MPa": 1400.0, "YoungsModulus_GPa": 211.0}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_forge(self):
        """Verifies Transvalor FORGE .mat export format and Hansel-Spittel parameters."""
        path = os.path.join(self.temp_dir.name, "inconel718.mat")
        out = CAEExportManager.export_forge(path, self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertTrue(os.path.exists(out))

        with open(out, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("TRANSVALOR FORGE MATERIAL DATA CARD", content)
        self.assertIn("[RHEOLOGY_HANSEL_SPITTEL]", content)
        self.assertIn("A  =", content)
        self.assertIn("m1 =", content)
        self.assertIn("[THERMAL_PROPERTIES]", content)
        self.assertIn("SOLIDUS_TEMPERATURE_C = 1260.00", content)

    def test_export_deform(self):
        """Verifies DEFORM .dat flow stress table format."""
        path = os.path.join(self.temp_dir.name, "inconel718.dat")
        out = CAEExportManager.export_deform(path, self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertTrue(os.path.exists(out))

        with open(out, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("SFTC DEFORM-3D", content)
        self.assertIn("TABLE_DIMENSIONS =", content)
        self.assertIn("SOLIDUS_TEMPERATURE_K = 1533.15", content)

    def test_export_simufact(self):
        """Verifies Simufact MatildA XML export format."""
        path = os.path.join(self.temp_dir.name, "inconel718.xml")
        out = CAEExportManager.export_simufact(path, self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertTrue(os.path.exists(out))

        with open(out, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<SimufactMaterial", content)
        self.assertIn("<FlowStressCurves", content)
        self.assertIn('<Element name="Ni"', content)
        self.assertIn("</SimufactMaterial>", content)

    def test_in_memory_preview_all_formats_without_filepath(self):
        """Verifies preview generation (`filepath=''`) works without file I/O across all exporters."""
        simufact_xml = CAEExportManager.export_simufact("", "CoCrFeNi & Nb", self.comp, None, None)
        self.assertIn('<SimufactMaterial xmlns="http://www.simufact.de/material"', simufact_xml)
        self.assertIn("<MaterialName>CoCrFeNi &amp; Nb</MaterialName>", simufact_xml)
        self.assertIn("</SimufactMaterial>", simufact_xml)

        forge_mat = CAEExportManager.export_forge("", self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertIn("TRANSVALOR FORGE MATERIAL DATA CARD", forge_mat)

        deform_dat = CAEExportManager.export_deform("", self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertIn("SFTC DEFORM-3D", deform_dat)

        abaqus_inp = CAEExportManager.export_abaqus("", self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertIn("*MATERIAL, NAME=Inconel_718", abaqus_inp)

        ansys_apdl = CAEExportManager.export_ansys("", self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertIn("MPDATA,DENS", ansys_apdl)

        comsol_txt = CAEExportManager.export_comsol("", self.alloy_name, self.comp, self.thermo, self.mech)
        self.assertIn("% COMSOL Multiphysics Material Model", comsol_txt)


if __name__ == "__main__":
    unittest.main()
