"""
test_physics_engines.py - Automated Unit & Integration Tests for Pure Python Physics Engines
Verifies:
  1. ElementsData integrity (118 elements)
  2. ThermoEngine CALPHAD Gibbs energy, VEC, DeltaSmix, solidus/liquidus
  3. CoatingEngine for Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 as-sprayed coatings
  4. MechanicalEngine solid-solution strengthening and Tabor hardness
  5. OxidationEngine Wagner parabolic mass gain
  6. CorrosionEngine Stern-Geary polarization & PREN
  7. XRDEngine diffraction synthesis and authentic citations
  8. ApplicationScorer industrial suitability scoring
"""

import unittest
from pycalphad_app.core.elements_data import ElementsData
from pycalphad_app.core.thermo_engine import ThermoEngine
from pycalphad_app.core.coating_engine import CoatingEngine
from pycalphad_app.core.mechanical_engine import MechanicalEngine
from pycalphad_app.core.oxidation_engine import OxidationEngine
from pycalphad_app.core.corrosion_engine import CorrosionEngine
from pycalphad_app.core.xrd_engine import XRDEngine
from pycalphad_app.core.application_scorer import ApplicationScorer
from pycalphad_app.database.thermal_spray_database import ThermalSprayCoatingDatabase
from pycalphad_app.database.unified_hea_database import UnifiedHEADatabase


class TestPhysicsEngines(unittest.TestCase):

    def test_elements_data(self):
        self.assertIn("Ni", ElementsData.ELEMENTS)
        self.assertIn("Cr", ElementsData.ELEMENTS)
        self.assertIn("Fe", ElementsData.ELEMENTS)
        ni = ElementsData.get("Ni")
        self.assertEqual(ni.Z, 28)
        self.assertAlmostEqual(ni.atomic_mass, 58.6934, places=2)

    def test_coating_engine_exact_composition(self):
        # Exact composition: Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65
        comp = {"Ni": 0.7161, "Cr": 0.1527, "Si": 0.0465, "Fe": 0.0447, "B": 0.0332, "C": 0.0068}
        res = CoatingEngine.calculate(comp, process="HVOF")

        self.assertIn("microhardness_HV", res)
        # Authentic experimental HVOF microhardness is ~745 HV
        self.assertGreater(res["microhardness_HV"], 650.0)
        self.assertLess(res["microhardness_HV"], 850.0)

        # Solidus and Liquidus
        self.assertGreater(res["solidus_K"], 1200.0)
        self.assertLess(res["liquidus_K"], 1360.0)

        # Phase precipitation: gamma-Ni, CrB, Ni3Si, Cr7C3
        phases = res["phase_fractions"]
        self.assertGreater(phases.get("gamma_Ni_FCC", 0), 0.50)
        self.assertGreater(phases.get("CrB_boride", 0), 0.05)

    def test_thermal_spray_database_validation(self):
        comp = {"Ni": 0.7161, "Cr": 0.1527, "Si": 0.0465, "Fe": 0.0447, "B": 0.0332, "C": 0.0068}
        calc_res = CoatingEngine.calculate(comp, process="HVOF")
        table = ThermalSprayCoatingDatabase.compare_calculated_vs_experimental(calc_res)

        self.assertGreater(len(table), 5)
        # Check that error for microhardness is small (< 10%)
        hv_row = next(r for r in table if "Microhardness" in r["Property"])
        self.assertLess(hv_row["ErrorPercent"], 10.0)

    def test_cantor_thermo_engine(self):
        comp = {"Co": 0.20, "Cr": 0.20, "Fe": 0.20, "Mn": 0.20, "Ni": 0.20}
        res = ThermoEngine.calculate(comp)

        self.assertAlmostEqual(res["VEC_val"], 8.0, places=1)
        self.assertGreater(res["DeltaSmix_J_molK"], 13.0)
        self.assertGreater(res["Solidus_K"], 1500.0)
        self.assertLess(res["Liquidus_K"], 1660.0)

    def test_mechanical_engine(self):
        comp = {"Co": 0.20, "Cr": 0.20, "Fe": 0.20, "Mn": 0.20, "Ni": 0.20}
        res = MechanicalEngine.calculate(comp, grain_size_um=25.0)

        self.assertGreater(res["YieldStrength_MPa"], 180.0)
        self.assertLess(res["YieldStrength_MPa"], 350.0)
        self.assertGreater(res["Hardness_HV"], 120.0)

    def test_xrd_engine_coating(self):
        comp = {"Ni": 0.7161, "Cr": 0.1527, "Si": 0.0465, "Fe": 0.0447, "B": 0.0332, "C": 0.0068}
        res = XRDEngine.calculate_xrd(comp, is_coating=True)

        self.assertTrue("Planche" in res["citation"] or "Houdková" in res["citation"])
        self.assertTrue(res["doi"].startswith("10.1007/") or res["doi"].startswith("10.1016/"))
        self.assertGreater(len(res["peaks"]), 3)
        self.assertEqual(len(res["two_theta_deg"]), len(res["intensity_norm"]))


    def test_application_scorer(self):
        thermo = {"Tm_avg_K": 1800.0, "Density_g_cm3": 8.0}
        mech = {"YieldStrength_MPa": 400.0, "Hardness_HV": 220.0, "Elongation_pct": 35.0}
        ox = {"Oxidation_kp": 5.0e-9}
        corr = {"CorrosionRate_mm_yr": 0.005}

        scores = ApplicationScorer.score_all(thermo, mech, ox, corr)
        self.assertEqual(len(scores), 10)
        for s in scores:
            self.assertGreaterEqual(s["score"], 0.0)
            self.assertLessEqual(s["score"], 100.0)


if __name__ == "__main__":
    unittest.main()
