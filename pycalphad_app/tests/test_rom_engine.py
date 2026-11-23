# -*- coding: utf-8 -*-
"""
test_rom_engine.py - Unit and Integration Verification for Independent Rule of Mixtures Engine
Tests:
  1. Pure single-element identity and boundary conditions.
  2. Multi-component Cantor alloy (CoCrFeMnNi) Rule of Mixtures calculations.
  3. Voigt-Reuss-Hill continuum composite bounds ordering (Voigt >= Hill >= Reuss).
  4. Temperature-dependent property trajectories and comparative series.
  5. Side-by-side CALPHAD vs ROM comparison table generation and physical mechanisms.
  6. CAEDaemon equilibrium handler integration and simulation module execution.
"""

import math
import pytest
import numpy as np

from pycalphad_app.core.rom_engine import (
    RuleOfMixturesEngine,
    ELEMENTAL_RESISTIVITY_UOHM_CM,
    ELEMENTAL_YIELD_STRESS_MPA,
    ELEMENTAL_HARDNESS_HV
)
from pycalphad_app.server.cae_daemon import CAEDaemon


class TestRuleOfMixturesEngine:
    """Rigorous scientific verification of the RuleOfMixturesEngine."""

    def test_single_element_boundary_condition(self):
        """Single pure element must return elemental constants with exact Voigt-Reuss-Hill coincidence."""
        engine = RuleOfMixturesEngine({"Fe": 1.0}, basis="at%")
        props = engine.compute_properties()

        # Pure Fe density: ~7.87 g/cm3
        assert abs(props["density_g_cm3"] - 7.87) < 0.05
        # Moduli coincidence: Voigt == Hill == Reuss for single phase
        assert abs(props["youngs_modulus_voigt_gpa"] - props["youngs_modulus_gpa"]) < 1e-4
        assert abs(props["youngs_modulus_reuss_gpa"] - props["youngs_modulus_gpa"]) < 1e-4
        assert abs(props["bulk_modulus_voigt_gpa"] - props["bulk_modulus_gpa"]) < 1e-4
        assert abs(props["shear_modulus_voigt_gpa"] - props["shear_modulus_gpa"]) < 1e-4
        # Single element ideal mixing entropy is zero
        assert abs(props["delta_s_mix_ideal_j_mol_k"]) < 1e-6
        assert abs(props["delta_h_mix_kj_mol"]) < 1e-6

    def test_cantor_alloy_ideal_thermodynamics(self):
        """Equiatomic 5-element Cantor alloy must yield Delta S_mix = R * ln(5) ~ 13.38 J/(mol*K)."""
        comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
        engine = RuleOfMixturesEngine(comp, basis="at%")
        props = engine.compute_properties()

        # R * ln(5) = 8.314462 * 1.609438 = 13.3816 J/(mol*K)
        expected_s = 8.314462618 * math.log(5.0)
        assert abs(props["delta_s_mix_ideal_j_mol_k"] - expected_s) < 1e-3
        assert abs(props["delta_h_mix_kj_mol"]) < 1e-6

        # Density must lie within the range of pure constituents (7.19 - 8.91 g/cm3)
        assert 7.90 <= props["density_g_cm3"] <= 8.20

    def test_voigt_reuss_hill_bounds_hierarchy(self):
        """
        By the principles of minimum potential energy and minimum complementary energy:
        E_Voigt >= E_Hill >= E_Reuss
        G_Voigt >= G_Hill >= G_Reuss
        K_Voigt >= K_Hill >= K_Reuss
        """
        # Alloy with strongly disparate constituents to accentuate bounds: Al-Co-Cr-Fe-Ni-W
        comp = {"Al": 0.15, "Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Ni": 0.15, "W": 0.1}
        engine = RuleOfMixturesEngine(comp, basis="at%")
        props = engine.compute_properties()

        # Young's modulus
        assert props["youngs_modulus_voigt_gpa"] >= props["youngs_modulus_gpa"]
        assert props["youngs_modulus_gpa"] >= props["youngs_modulus_reuss_gpa"]

        # Shear modulus
        assert props["shear_modulus_voigt_gpa"] >= props["shear_modulus_gpa"]
        assert props["shear_modulus_gpa"] >= props["shear_modulus_reuss_gpa"]

        # Bulk modulus
        assert props["bulk_modulus_voigt_gpa"] >= props["bulk_modulus_gpa"]
        assert props["bulk_modulus_gpa"] >= props["bulk_modulus_reuss_gpa"]

        # Thermal conductivity bounds
        assert props["thermal_conductivity_voigt_w_mk"] >= props["thermal_conductivity_reuss_w_mk"]

    def test_temperature_dependent_curves(self):
        """ROM curves must soften yield strength and expand volume with temperature."""
        comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
        engine = RuleOfMixturesEngine(comp, basis="at%")
        t_arr = np.linspace(300.0, 1400.0, 40)
        curves = engine.compute_temperature_dependent_curves(t_arr)

        assert len(curves["yield_strength"]) == 40
        assert len(curves["density"]) == 40
        assert len(curves["cte"]) == 40

        # Yield strength must monotonically decrease with thermal softening
        assert curves["yield_strength"][0] > curves["yield_strength"][-1]
        # Density must monotonically decrease due to thermal expansion
        assert curves["density"][0] > curves["density"][-1]

    def test_compare_with_calphad_divergence_metrics(self):
        """
        compare_with_calphad must produce comprehensive comparison metrics
        showing solid solution strengthening elevation and thermal conductivity suppression.
        """
        comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
        engine = RuleOfMixturesEngine(comp, basis="at%")

        # Mock high-fidelity CALPHAD and physics properties
        calphad_thermo = {
            "Liquidus_K": 1608.0,
            "Solidus_K": 1553.0,
            "ApparentDensity_g_cm3": 8.05
        }
        calphad_mech = {
            "ProofStress_Rp02_MPa": 340.0,
            "TensileStrength_Rm_MPa": 750.0,
            "VickersHardness_HV": 220.0,
            "YoungsModulus_E_GPa": 204.0,
            "ShearModulus_G_GPa": 78.0,
            "BulkModulus_K_GPa": 160.0,
            "PoissonsRatio_nu": 0.31
        }
        calphad_trans = {
            "ThermalConductivity_W_mK": 13.5,
            "ElectricalResistivity_uOhm_cm": 115.0,
            "LinearCTE_1e6_K": 14.8
        }
        temp_series = {
            "t_k": np.linspace(300.0, 1500.0, 25).tolist()
        }

        res = engine.compare_with_calphad(
            calphad_thermo=calphad_thermo,
            calphad_mech=calphad_mech,
            calphad_trans=calphad_trans,
            temp_series=temp_series
        )

        assert "comparison_table" in res
        assert "comparative_series" in res
        assert "summary" in res

        table = res["comparison_table"]
        assert len(table) >= 11

        # Check required columns on every row
        for row in table:
            assert "property" in row
            assert "units" in row
            assert "calphad_value" in row
            assert "rom_value" in row
            assert "diff_absolute" in row
            assert "diff_relative_pct" in row
            assert "mechanism" in row
            assert len(row["mechanism"]) > 10

        # Physical divergence checks:
        # 1. Yield strength elevation: CALPHAD (340 MPa) vs ROM uncoupled friction (~47 MPa) -> ~+600%
        sy_row = next(r for r in table if "Yield Strength" in r["property"])
        assert sy_row["diff_relative_pct"] > 200.0

        # 2. Thermal conductivity suppression: CALPHAD (13.5 W/mK) vs ROM (~74 W/mK) -> ~-80%
        k_row = next(r for r in table if "Thermal Conductivity" in r["property"])
        assert k_row["diff_relative_pct"] < -50.0

        # 3. Electrical resistivity elevation: CALPHAD (115 uOhm*cm) vs ROM (~35.7 uOhm*cm) -> +221.8%
        rho_row = next(r for r in table if "Electrical Resistivity" in r["property"])
        assert rho_row["diff_relative_pct"] > 150.0


class TestCAEDaemonROMIntegration:
    """Verifies that CAEDaemon executes the Rule of Mixtures engine on main equilibrium calculation."""

    def test_handle_calculate_equilibrium_contains_rom_payload(self):
        """Calling handle_calculate_equilibrium must return 'rule_of_mixtures' and 'rom_comparison'."""
        req = {
            "database_name": "High Entropy Alloys",
            "composition": {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0},
            "basis": "at%",
            "grain_size_um": 25.0,
            "process_type": "Wrought",
            "calc_mode": "standard"
        }

        result = CAEDaemon.handle_calculate_equilibrium(req)
        assert result["status"] == "success"

        # Rule of Mixtures payload check
        assert "rule_of_mixtures" in result
        rom = result["rule_of_mixtures"]
        assert rom["density_g_cm3"] > 7.0
        assert rom["youngs_modulus_gpa"] > 100.0
        assert rom["yield_strength_mpa"] > 0.0

        # ROM comparison check
        assert "rom_comparison" in result
        comp = result["rom_comparison"]
        assert "comparison_table" in comp
        assert len(comp["comparison_table"]) >= 11
        assert "comparative_series" in comp
        assert len(comp["comparative_series"]["rom_yield_strength"]) > 0

    def test_handle_run_simulation_module_rule_of_mixtures(self):
        """Standalone module call for 'rule_of_mixtures' returns curves and summary."""
        req = {
            "module": "rule_of_mixtures",
            "database_name": "High Entropy Alloys",
            "composition": {"Nb": 25.0, "Mo": 25.0, "Ta": 25.0, "W": 25.0},
            "basis": "at%"
        }

        res = CAEDaemon.handle_run_simulation_module(req)
        assert "title" in res
        assert "curves" in res
        assert len(res["curves"]) >= 3
        assert "summary" in res
        assert "properties" in res

    def test_step_size_increase_reduces_error_deviation(self):
        """
        Increasing the step size (t_step: 25 -> 50 -> 100 K) must systematically
        and monotonically reduce the error deviation from experimental results.
        Uses wt% composition matching the user's exact benchmark scenario.
        """
        base_req = {
            "database_name": "High Entropy Alloys",
            "composition": {"Al": 20.0, "Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Ni": 20.0},
            "basis": "wt%",
            "grain_size_um": 25.0,
            "process_type": "Wrought",
            "calc_mode": "fast"
        }

        # Step size 25 K
        req_25 = dict(base_req, t_step=25.0)
        res_25 = CAEDaemon.handle_calculate_equilibrium(req_25)

        # Step size 50 K
        req_50 = dict(base_req, t_step=50.0)
        res_50 = CAEDaemon.handle_calculate_equilibrium(req_50)

        # Step size 100 K
        req_100 = dict(base_req, t_step=100.0)
        res_100 = CAEDaemon.handle_calculate_equilibrium(req_100)

        val_25 = res_25.get("validation_table", [])
        val_50 = res_50.get("validation_table", [])
        val_100 = res_100.get("validation_table", [])

        assert len(val_25) > 0
        assert len(val_50) == len(val_25)
        assert len(val_100) == len(val_25)

        # Verify validation table rows contain ROM calculated fields
        assert "RomCalculated" in val_25[0]
        assert "RomErrorPercent" in val_25[0]

        # Verify monotonic reduction in error deviation as step size increases
        mean_err_25 = np.mean([abs(float(r["ErrorPercent"])) for r in val_25 if "ErrorPercent" in r])
        mean_err_50 = np.mean([abs(float(r["ErrorPercent"])) for r in val_50 if "ErrorPercent" in r])
        mean_err_100 = np.mean([abs(float(r["ErrorPercent"])) for r in val_100 if "ErrorPercent" in r])

        assert mean_err_50 < mean_err_25, f"Expected mean_err_50 ({mean_err_50}) < mean_err_25 ({mean_err_25})"
        assert mean_err_100 < mean_err_50, f"Expected mean_err_100 ({mean_err_100}) < mean_err_50 ({mean_err_50})"
