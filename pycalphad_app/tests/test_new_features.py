# -*- coding: utf-8 -*-
"""
test_new_features.py - Verification for Periodic Table 118, OriginLab Graph Navigation,
PyCALPHAD Embedding, and Translated Physics Engines.
"""

import unittest
from pycalphad_app.core.elements_data import ElementsData, get_element, get_all_elements, IUPAC_ELEMENTS_DATA
from pycalphad_app.core.lattice_distortion_engine import LatticeDistortionEngine
from pycalphad_app.core.pycalphad_embed import PyCalphadEmbed, DynamicTDBGenerator
from pycalphad_app.core.thermo_engine import ThermoEngine
from pycalphad_app.core.mechanical_engine import MechanicalEngine
from pycalphad_app.core.oxidation_engine import OxidationEngine
from pycalphad_app.core.coating_engine import CoatingEngine, HEACoatingEngine
from pycalphad_app.core.xrd_engine import XRDEngine
from pycalphad_app.core.application_scorer import ApplicationScorer


class TestPeriodicTable118(unittest.TestCase):

    def test_complete_118_elements(self):
        elems = ElementsData.get_118_list()
        self.assertEqual(len(elems), 118)
        self.assertEqual(elems[0].symbol, "H")
        self.assertEqual(elems[0].z, 1)
        self.assertEqual(elems[-1].symbol, "Og")
        self.assertEqual(elems[-1].z, 118)

    def test_all_elements_have_valid_properties(self):
        for e in ElementsData.get_118_list():
            self.assertGreater(e.z, 0)
            self.assertGreater(e.atomic_mass, 0.0)
            self.assertTrue(len(e.symbol) >= 1)
            self.assertTrue(len(e.name) >= 1)
            self.assertGreater(e.radius_pm, 0.0)
            self.assertGreater(e.tm_k, 0.0)


class TestLatticeDistortionEngine(unittest.TestCase):

    def test_cantor_lattice_distortion(self):
        elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
        fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
        thermo = ThermoEngine.calculate(dict(zip(elements, fractions)))

        res = LatticeDistortionEngine.compute_distortion_metrics(elements, fractions, thermo)
        self.assertIn("Delta_HardSphere_pct", res)
        self.assertIn("Eps_RMS_SoftSphere_pct", res)
        self.assertIn("CriticalEffectiveShearStrain_gamma_th", res)
        self.assertIn("DislocationGlideMechanism", res)
        self.assertIn("AmorphizationRisk", res)

        # Cantor alloy has atomic size mismatch delta < 4%
        self.assertLess(res["Delta_HardSphere_pct"], 5.0)
        self.assertEqual(res["AmorphizationRisk"], "Negligible (Crystalline Lattice Preserved)")


class TestPyCalphadEmbedding(unittest.TestCase):

    def test_dynamic_tdb_generator(self):
        elements = ["Co", "Cr", "Fe", "Ni"]
        tdb_str = DynamicTDBGenerator.generate_tdb_string(elements)
        self.assertIn("ELEMENT /-", tdb_str)
        self.assertIn("PARAMETER G", tdb_str)
        self.assertIn("PHASE LIQUID", tdb_str)
        self.assertIn("PHASE FCC_A1", tdb_str)

    def test_pycalphad_embed_run_equilibrium(self):
        elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
        fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
        res = PyCalphadEmbed.run_equilibrium(elements, fractions, t_min_c=600.0, t_max_c=1400.0, n_points=10)
        self.assertIn("Liquid", res)
        self.assertIn("FCC", res)
        self.assertIn("T_C", res)
        self.assertEqual(len(res["T_C"]), 10)


class TestTranslatedEngines(unittest.TestCase):

    def test_mechanical_engine_varvenne_curtin(self):
        elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
        fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
        thermo = ThermoEngine.calculate(dict(zip(elements, fractions)))

        res = MechanicalEngine.compute_mechanical_properties(elements, fractions, thermo, grain_size_um=20.0)
        self.assertIn("YieldStrength_MPa", res)
        self.assertIn("UTS_MPa", res)
        self.assertIn("Elongation_pct", res)
        self.assertIn("Hardness_HV", res)
        self.assertIn("FractureToughness_K1c", res)
        self.assertIn("Temp_K", res)
        self.assertIn("YieldStrength_vs_T_MPa", res)
        self.assertIn("PlasticStrain", res)
        self.assertIn("TrueStress_MPa", res)

        # Room temperature yield strength should be in physical range for Cantor (180 - 350 MPa)
        self.assertGreater(res["YieldStrength_MPa"], 180.0)
        self.assertLess(res["YieldStrength_MPa"], 350.0)
        self.assertGreater(res["UTS_MPa"], res["YieldStrength_MPa"])
        self.assertGreater(res["Hardness_HV"], 100.0)

    def test_oxidation_engine_wagner(self):
        elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
        fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
        thermo = ThermoEngine.calculate(dict(zip(elements, fractions)))

        res = OxidationEngine.compute_oxidation_kinetics(elements, fractions, thermo)
        self.assertIn("Regime", res)
        self.assertIn("kp_T_m2_s", res)
        self.assertIn("ThermalSpallationStress_MPa", res)
        self.assertIn("CriticalSoluteConcentration_Nstar", res)
        self.assertIn("Ellingham", res)
        self.assertIn("Time_hours", res)
        self.assertIn("MassGain_mg_cm2", res)
        self.assertIn("Arrhenius_1000_over_T", res)
        self.assertIn("Arrhenius_log10_kp", res)

        # Cantor alloy forms protective spinel / chromia scales
        self.assertTrue("Chromia" in res["Regime"] or "Spinel" in res["Regime"])

    def test_coating_engine_substrates_and_processes(self):
        substrates = HEACoatingEngine.get_substrate_database()
        self.assertIn("AISI 1045", substrates)
        self.assertIn("316L SS", substrates)
        self.assertIn("Ti-6Al-4V", substrates)
        self.assertIn("Inconel 718", substrates)

        processes = HEACoatingEngine.get_process_database()
        self.assertIn("Laser Cladding", processes)
        self.assertIn("HVOF", processes)
        self.assertIn("APS", processes)
        self.assertIn("Magnetron Sputtering", processes)


if __name__ == "__main__":
    unittest.main()
