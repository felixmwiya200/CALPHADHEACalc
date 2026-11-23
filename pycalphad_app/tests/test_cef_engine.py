"""
Unit tests for the Compound Energy Formalism (CEF) and Advanced CALPHAD Engine
==============================================================================
Validates theoretical models and numerical algorithms based on:
    Gabriele Cacciamani (2016), Tecnol. Metal. Mater. Miner., 13(1), 16-24.
"""

import math
import pytest
from pycalphad_app.core.cef_engine import (
    Sublattice,
    SgtePolynomial,
    CompoundEnergyFormalismEngine,
    ExtrapolationEngine,
    UhtcReactiveWettingSolver,
    R_GAS,
)


class TestSublatticeModel:
    """Verifies site fraction constraints and macroscopic composition calculations."""

    def test_sublattice_validation_and_normalization(self):
        sub = Sublattice(
            name="Metallic",
            multiplicity=1.0,
            constituents=["Fe", "Ni"],
            site_fractions={"Fe": 0.7, "Ni": 0.3},
        )
        assert sub.validate() is True

        sub_unnorm = Sublattice(
            name="Unnormalized",
            multiplicity=2.0,
            constituents=["Al", "Ti"],
            site_fractions={"Al": 2.0, "Ti": 2.0},
        )
        assert sub_unnorm.validate() is False
        sub_unnorm.normalize()
        assert sub_unnorm.validate() is True
        assert pytest.approx(sub_unnorm.site_fractions["Al"], 1e-4) == 0.5
        assert pytest.approx(sub_unnorm.site_fractions["Ti"], 1e-4) == 0.5

    def test_overall_composition_with_vacancies(self):
        # Model: (Fe)1 (C, VA)3, e.g. bcc interstitial solution
        # If y_Fe^(1) = 1.0, y_C^(2) = 0.1, y_VA^(2) = 0.9
        # Total formula units: 1 Fe + 3 * (0.1 C + 0.9 VA)
        # Denominator excluding VA = 1 + 3 * (1 - 0.9) = 1 + 0.3 = 1.3 atoms
        # Moles of Fe = 1.0 => x_Fe = 1.0 / 1.3 = 0.76923
        # Moles of C = 3 * 0.1 = 0.3 => x_C = 0.3 / 1.3 = 0.23077
        s1 = Sublattice("Sub1", multiplicity=1.0, constituents=["Fe"], site_fractions={"Fe": 1.0})
        s2 = Sublattice(
            "Sub2",
            multiplicity=3.0,
            constituents=["C", "VA"],
            site_fractions={"C": 0.1, "VA": 0.9},
        )
        engine = CompoundEnergyFormalismEngine("BCC_FE_C", [s1, s2])
        x = engine.calculate_overall_composition()
        assert pytest.approx(x["Fe"], 1e-4) == 1.0 / 1.3
        assert pytest.approx(x["C"], 1e-4) == 0.3 / 1.3
        assert pytest.approx(x["Fe"] + x["C"], 1e-6) == 1.0


class TestCompoundEnergyFormalismEngine:
    """Verifies G_ref, G_id, G_ex, and G_mag thermodynamic evaluations."""

    def test_reference_energy_c15_laves(self):
        # C15 Laves phase (Mg, Cu)1 (Mg, Cu)2
        s1 = Sublattice("Sub1", 1.0, ["Mg", "Cu"], {"Mg": 0.8, "Cu": 0.2})
        s2 = Sublattice("Sub2", 2.0, ["Mg", "Cu"], {"Mg": 0.1, "Cu": 0.9})

        end_members = {
            ("Mg", "Mg"): SgtePolynomial(a=-10000.0, b=-5.0),
            ("Mg", "Cu"): SgtePolynomial(a=-35000.0, b=-12.0),  # Stable MgCu2
            ("Cu", "Mg"): SgtePolynomial(a=-15000.0, b=-7.0),
            ("Cu", "Cu"): SgtePolynomial(a=-8000.0, b=-4.0),
        }
        engine = CompoundEnergyFormalismEngine("C15_LAVES", [s1, s2], end_members=end_members)

        T = 1000.0  # K
        g_ref = engine.calculate_reference_energy(T)

        # Expected:
        # P(Mg:Mg) = 0.8 * 0.1 = 0.08
        # P(Mg:Cu) = 0.8 * 0.9 = 0.72
        # P(Cu:Mg) = 0.2 * 0.1 = 0.02
        # P(Cu:Cu) = 0.2 * 0.9 = 0.18
        expected_g_ref = (
            0.08 * (-10000.0 - 5.0 * 1000.0)
            + 0.72 * (-35000.0 - 12.0 * 1000.0)
            + 0.02 * (-15000.0 - 7.0 * 1000.0)
            + 0.18 * (-8000.0 - 4.0 * 1000.0)
        )
        assert pytest.approx(g_ref, 1e-3) == expected_g_ref

    def test_ideal_entropy_pure_and_mixed(self):
        # When sublattices are completely pure, G_id must be 0
        s1_pure = Sublattice("Sub1", 1.0, ["Fe"], {"Fe": 1.0})
        s2_pure = Sublattice("Sub2", 1.0, ["Ni"], {"Ni": 1.0})
        engine_pure = CompoundEnergyFormalismEngine("ORDERED", [s1_pure, s2_pure])
        assert engine_pure.calculate_ideal_entropy_energy(1000.0) == 0.0

        # When equiatomic mixing on 1 sublattice of multiplicity 1
        s_mix = Sublattice("Sub1", 1.0, ["A", "B"], {"A": 0.5, "B": 0.5})
        engine_mix = CompoundEnergyFormalismEngine("SOLUTION", [s_mix])
        # G_id = R * T * (0.5 * ln(0.5) + 0.5 * ln(0.5)) = R * T * ln(0.5)
        T = 800.0
        expected_g_id = R_GAS * T * math.log(0.5)
        assert pytest.approx(engine_mix.calculate_ideal_entropy_energy(T), 1e-4) == expected_g_id

    def test_excess_energy_redlich_kister(self):
        s1 = Sublattice("Sub1", 1.0, ["Cr", "Fe"], {"Cr": 0.6, "Fe": 0.4})
        # L0 = -15000 + 2.5 * T, L1 = 5000 - 1.0 * T
        binary_interactions = {
            (0, ("Cr", "Fe")): [(-15000.0, 2.5), (5000.0, -1.0)]
        }
        engine = CompoundEnergyFormalismEngine(
            "FCC", [s1], binary_interactions=binary_interactions
        )
        T = 1200.0
        g_ex = engine.calculate_excess_energy(T)

        y_cr = 0.6
        y_fe = 0.4
        diff = y_cr - y_fe  # 0.2
        l0 = -15000.0 + 2.5 * 1200.0  # -12000.0
        l1 = 5000.0 - 1.0 * 1200.0    # 3800.0
        expected_g_ex = y_cr * y_fe * (l0 + l1 * diff)
        assert pytest.approx(g_ex, 1e-4) == expected_g_ex

    def test_magnetic_energy_hillert_jarl(self):
        # Test BCC ferromagnetic phase (p = 0.40) like pure Fe (Tc = 1043 K, beta = 2.22)
        s1 = Sublattice("Sub1", 1.0, ["Fe"], {"Fe": 1.0})
        mag_params = {"p": 0.40, "Tc": 1043.0, "beta": 2.22}
        engine = CompoundEnergyFormalismEngine("BCC_FE", [s1], magnetic_params=mag_params)

        # Test at T < Tc (e.g. 500 K)
        g_mag_low = engine.calculate_magnetic_energy(500.0)
        assert g_mag_low < 0.0, "Magnetic ordering should stabilize the phase (negative G_mag)"

        # Test at T > Tc (e.g. 1500 K)
        g_mag_high = engine.calculate_magnetic_energy(1500.0)
        assert g_mag_high < 0.0

        # At Tc, both branches must be continuous
        g_mag_below_tc = engine.calculate_magnetic_energy(1042.999)
        g_mag_above_tc = engine.calculate_magnetic_energy(1043.001)
        assert pytest.approx(g_mag_below_tc, abs=1e-1) == g_mag_above_tc

    def test_complete_temperature_series(self):
        s1 = Sublattice("Sub1", 1.0, ["Ni"], {"Ni": 1.0})
        end_members = {("Ni",): SgtePolynomial(a=-5000.0, b=-10.0, d=-0.001)}
        mag_params = {"p": 0.28, "Tc": 631.0, "beta": 0.52}
        engine = CompoundEnergyFormalismEngine(
            "FCC_NI", [s1], end_members=end_members, magnetic_params=mag_params
        )

        res = engine.calculate_temperature_series(100.0, 500.0, step_c=100.0)
        assert len(res["temperatures_C"]) == 5
        assert res["temperatures_C"][0] == 100.0
        assert res["temperatures_C"][-1] == 500.0
        assert all(m < 0.0 for m in res["G_m"])


class TestExtrapolationEngine:
    """Verifies Muggianu, Kohler, and Toop ternary geometric extrapolation models."""

    def test_extrapolation_models_at_binary_edge(self):
        # When x3 = 0, all three models must degenerate to the same binary excess energy
        rk_12 = [(-12000.0, 1.5)]
        rk_23 = [(-8000.0, 0.5)]
        rk_13 = [(-5000.0, 0.0)]
        T = 1000.0
        x1 = 0.4
        x2 = 0.6
        x3 = 0.0

        g_mugg = ExtrapolationEngine.muggianu_extrapolation(x1, x2, x3, T, rk_12, rk_23, rk_13)
        g_kohl = ExtrapolationEngine.kohler_extrapolation(x1, x2, x3, T, rk_12, rk_23, rk_13)
        g_toop = ExtrapolationEngine.toop_extrapolation(x1, x2, x3, T, rk_12, rk_23, rk_13)

        assert pytest.approx(g_mugg, 1e-4) == g_kohl
        assert pytest.approx(g_mugg, 1e-4) == g_toop

    def test_compare_ternary_section_sweep(self):
        rk_12 = [(-15000.0, 2.0)]
        rk_23 = [(-10000.0, 1.0)]
        rk_13 = [(-20000.0, 3.0)]

        res = ExtrapolationEngine.compare_ternary_section(
            x3_fixed=0.2, t_kelvin=1273.15, rk_12=rk_12, rk_23=rk_23, rk_13=rk_13, num_points=10
        )
        assert len(res["x1"]) == 11
        assert res["x3"][0] == 0.2
        assert len(res["G_ex_muggianu"]) == 11
        assert len(res["G_ex_kohler"]) == 11
        assert len(res["G_ex_toop"]) == 11


class TestUhtcReactiveWettingSolver:
    """Verifies UHTC reactive wetting dissolution, transient precipitation, and cooling."""

    def test_isothermal_reaction_path_zrb2_precipitation_redissolution(self):
        solver = UhtcReactiveWettingSolver(substrate="ZrB2", temperature_c=1130.0)
        res = solver.simulate_isothermal_reaction_path(steps=50)

        assert res["substrate"] == "ZrB2"
        assert res["transient_compound"] == "Zr3Ni20B6"

        data = res["data"]
        tau_fractions = data["transient_tau_fraction"]

        # 1. At start (dissolution = 0), tau fraction must be 0
        assert tau_fractions[0] == 0.0

        # 2. In intermediate stages, tau fraction must become non-zero (transient precipitation)
        max_tau = max(tau_fractions)
        assert max_tau > 0.05, "Transient tau-phase Zr3Ni20B6 must precipitate"

        # 3. At completion (dissolution = 1.0, equilibrium with ZrB2), tau fraction must re-dissolve to 0
        assert tau_fractions[-1] == 0.0

    def test_cooling_solidification_phase_sequence(self):
        solver = UhtcReactiveWettingSolver(substrate="ZrB2", temperature_c=1130.0)
        res = solver.simulate_cooling_solidification()

        assert res["liquidus_temperature_C"] == 1120.0
        assert res["eutectic_temperature_C"] == 1040.0

        # At room temperature (25°C), liquid fraction must be 0
        assert res["liquid_fraction"][-1] == 0.0
        # Solid eutectic constituent phases must be present
        assert res["zrb2_fraction"][-1] > 0.0
        assert res["tau_fraction"][-1] > 0.0
        assert res["ni3b_fraction"][-1] > 0.0
        assert res["niss_fraction"][-1] > 0.0
