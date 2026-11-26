"""
Unit tests for SpinodalEngine (regular solution miscibility gap & Cahn-Hilliard spinodal decomposition).
"""

import pytest
import math
from pycalphad_app.core.spinodal_engine import SpinodalEngine


def test_spinodal_engine_initialization():
    eng = SpinodalEngine(tc_c=900.0)
    assert eng.tc_c == 900.0
    assert abs(eng.tc_k - 1173.15) < 0.01
    assert eng.omega > 0.0
    # Omega = 2 * R * Tc
    expected_omega = 2.0 * SpinodalEngine.R_GAS * (900.0 + 273.15)
    assert abs(eng.omega - expected_omega) < 1e-4


def test_free_energy_of_mixing_symmetry():
    eng = SpinodalEngine(tc_c=900.0)
    t_c = 600.0
    g1 = eng.free_energy_of_mixing(0.2, t_c)
    g2 = eng.free_energy_of_mixing(0.8, t_c)
    assert abs(g1["G_mix_J_mol"] - g2["G_mix_J_mol"]) < 1e-5
    assert abs(g1["d2G_dx2_J_mol"] - g2["d2G_dx2_J_mol"]) < 1e-5
    # First derivative is antisymmetric: dG/dx(x) = -dG/dx(1-x)
    assert abs(g1["dG_dx_J_mol"] + g2["dG_dx_J_mol"]) < 1e-5


def test_critical_temperature_stability():
    eng = SpinodalEngine(tc_c=900.0)
    # At Tc and x = 0.5, d2G/dx2 must be 0
    res_tc = eng.free_energy_of_mixing(0.5, 900.0)
    assert abs(res_tc["d2G_dx2_J_mol"]) < 1e-4

    # Above Tc, homogeneous solution is stable everywhere (d2G/dx2 > 0)
    for x in [0.1, 0.3, 0.5, 0.7, 0.9]:
        res_above = eng.free_energy_of_mixing(x, 950.0)
        assert res_above["d2G_dx2_J_mol"] > 0.0
        assert eng.classify_stability(x, 950.0) == "stable_single_phase"


def test_spinodal_and_binodal_boundaries():
    eng = SpinodalEngine(tc_c=900.0)
    t_c = 650.0
    xs1, xs2 = eng.compute_spinodal(t_c)
    xb1, xb2 = eng.compute_binodal(t_c)

    # Binodal miscibility gap must enclose spinodal curve: xb1 < xs1 < 0.5 < xs2 < xb2
    assert 0.0 < xb1 < xs1 < 0.5
    assert 0.5 < xs2 < xb2 < 1.0
    assert abs((1.0 - xb1) - xb2) < 1e-5
    assert abs((1.0 - xs1) - xs2) < 1e-5

    # Check stability classification
    assert eng.classify_stability(xb1 * 0.5, t_c) == "stable_single_phase"
    assert eng.classify_stability(0.5 * (xb1 + xs1), t_c) == "metastable"
    assert eng.classify_stability(0.5, t_c) == "unstable_spinodal"


def test_cahn_hilliard_kinetics():
    eng = SpinodalEngine(tc_c=900.0)
    # Inside spinodal (x = 0.5 at 600 C)
    kin = eng.compute_cahn_hilliard_kinetics(0.5, 600.0)
    assert kin["is_spinodal"] is True
    assert kin["d2G_dx2"] < 0.0
    assert kin["lambda_max_nm"] > 0.0
    assert kin["q_max_inv_nm"] > 0.0
    assert kin["max_amplification_rate_s"] > 0.0
    assert len(kin["spectrum_q_inv_nm"]) > 0

    # Outside spinodal (x = 0.05 at 600 C)
    kin_out = eng.compute_cahn_hilliard_kinetics(0.05, 600.0)
    assert kin_out["is_spinodal"] is False
    assert kin_out["lambda_max_nm"] is None
