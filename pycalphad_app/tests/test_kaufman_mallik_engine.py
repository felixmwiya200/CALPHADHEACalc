# -*- coding: utf-8 -*-
"""
test_kaufman_mallik_engine.py - Automated Unit & Integration Tests for Kaufman-Mallik Engine

Validates the computational metallurgy methods from:
A. K. Mallik, 'Computer calculations of phase diagrams',
Bull. Mater. Sci., Vol. 8, No. 2, May 1986, pp. 107-121.
"""

import math
import numpy as np
import pytest

from pycalphad_app.core.kaufman_mallik_engine import KaufmanMallikEngine, R_CAL_MOL_K, R_J_MOL_K
from pycalphad_app.server.cae_daemon import CAEDaemon


class TestKaufmanMallikEngine:
    """Tests the analytical 2D/3D solvers, parameter inversion, and Gibbs minimization."""

    def test_solve_binary_common_tangent_convergence(self):
        """Tests that 2D Newton-Raphson solver converges with residual norm < 1e-6."""
        # 1200 K, Delta G_A = -1500 cal/mol, Delta G_B = 2000 cal/mol, E_alpha = 4500 cal/mol, E_beta = 4500 cal/mol
        res = KaufmanMallikEngine.solve_binary_common_tangent(
            t_kelvin=1200.0,
            delta_g_a=-1500.0,
            delta_g_b=2000.0,
            e_alpha=4500.0,
            e_beta=4500.0,
            use_calories=True,
        )

        assert res["converged"] is True
        assert res["iterations"] < 25
        assert res["residual_norm"] < 1e-6
        assert 0.0 < res["x_alpha"] < 1.0
        assert 0.0 < res["x_beta"] < 1.0
        assert abs(res["x_alpha"] - res["x_beta"]) > 0.05

    def test_invert_interaction_parameters_exact_recovery(self):
        """
        Validates Mallik Appendix 1 parameter inversion:
        Solves forward (E -> X_alpha, X_beta) and inverts backward (X_alpha, X_beta -> E)
        to confirm exact circular mathematical recovery.
        """
        t_k = 1100.0
        true_e_alpha = 3500.0  # cal/mol
        true_e_beta = 2800.0   # cal/mol
        dg_a = -1200.0
        dg_b = 1800.0

        # Forward calculation
        fwd = KaufmanMallikEngine.solve_binary_common_tangent(
            t_kelvin=t_k,
            delta_g_a=dg_a,
            delta_g_b=dg_b,
            e_alpha=true_e_alpha,
            e_beta=true_e_beta,
            use_calories=True,
        )
        assert fwd["converged"] is True

        # Inversion calculation
        inv = KaufmanMallikEngine.invert_interaction_parameters(
            t_kelvin=t_k,
            x_alpha=fwd["x_alpha"],
            x_beta=fwd["x_beta"],
            delta_g_a=dg_a,
            delta_g_b=dg_b,
            use_calories=True,
        )

        # Confirm recovered parameters match within 0.05%
        assert math.isclose(inv["e_alpha"], true_e_alpha, rel_tol=1e-3)
        assert math.isclose(inv["e_beta"], true_e_beta, rel_tol=1e-3)
        assert abs(inv["residual_f"]) < 1e-8
        assert abs(inv["residual_g"]) < 1e-8

    def test_invert_interaction_parameters_validation_errors(self):
        """Verifies proper error handling for invalid or degenerate physical inputs."""
        with pytest.raises(ValueError, match="Temperature must be strictly positive"):
            KaufmanMallikEngine.invert_interaction_parameters(-100.0, 0.2, 0.8, 0.0, 0.0)

        with pytest.raises(ValueError, match="Phase compositions must lie strictly in"):
            KaufmanMallikEngine.invert_interaction_parameters(1000.0, -0.1, 0.8, 0.0, 0.0)

        with pytest.raises(ValueError, match="Phase boundaries cannot be identical"):
            KaufmanMallikEngine.invert_interaction_parameters(1000.0, 0.5, 0.5, 0.0, 0.0)

    def test_calculate_miscibility_gap(self):
        """Tests symmetrical miscibility gap calculations when E > 2RT (Mallik Section 8.2)."""
        e_solid = 3000.0  # cal/mol
        # Critical temperature T_c = E / (2R) = 3000 / (2 * 1.987204) = 754.83 K
        t_crit_expected = e_solid / (2.0 * R_CAL_MOL_K)

        # Above critical temperature: completely miscible
        above = KaufmanMallikEngine.calculate_miscibility_gap(
            interaction_parameter=e_solid,
            t_kelvin=800.0,
            use_calories=True,
        )
        assert above is None

        # Below critical temperature: miscibility gap present
        below = KaufmanMallikEngine.calculate_miscibility_gap(
            interaction_parameter=e_solid,
            t_kelvin=600.0,
            use_calories=True,
        )
        assert below is not None
        assert math.isclose(below["t_critical"], t_crit_expected, rel_tol=1e-3)
        # Symmetry: binodal_x1 + binodal_x2 == 1.0
        assert math.isclose(below["binodal_x1"] + below["binodal_x2"], 1.0, abs_tol=1e-5)
        # Spinodal inside binodal
        assert below["binodal_x1"] < below["spinodal_x1"] < 0.5
        assert 0.5 < below["spinodal_x2"] < below["binodal_x2"]

    def test_calculate_binary_phase_boundaries(self):
        """Tests phase boundary continuation tracing over a temperature window."""
        t_m_a = 1000.0
        t_m_b = 1500.0
        delta_s = 10.0  # cal / (mol * K)

        # Delta G = Delta S * (T_m - T)
        dg_a_fn = lambda t: delta_s * (t_m_a - t)
        dg_b_fn = lambda t: delta_s * (t_m_b - t)

        series = KaufmanMallikEngine.calculate_binary_phase_boundaries(
            delta_g_a_fn=dg_a_fn,
            delta_g_b_fn=dg_b_fn,
            e_alpha=1000.0,
            e_beta=1000.0,
            t_min=1100.0,
            t_max=1400.0,
            num_temperatures=15,
            use_calories=True,
        )

        assert series["count"] > 5
        assert len(series["temperatures"]) == series["count"]
        assert len(series["x_alpha"]) == series["count"]
        assert len(series["x_beta"]) == series["count"]

    def test_nelder_mead_gibbs_minimizer(self):
        """Tests the Nelder-Mead direct search optimizer on multi-dimensional free energy."""
        # Minimum at (0.25, 0.40)
        target = np.array([0.25, 0.40])
        fn = lambda x: float(np.sum((x - target) ** 2))

        init_simplex = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0]
        ], dtype=float)

        opt = KaufmanMallikEngine.nelder_mead_gibbs_minimizer(
            gibbs_function=fn,
            initial_simplex=init_simplex,
            max_iter=150,
            tol=1e-6,
        )

        assert opt["converged"] is True
        assert math.isclose(opt["optimal_composition"][0], 0.25, abs_tol=1e-3)
        assert math.isclose(opt["optimal_composition"][1], 0.40, abs_tol=1e-3)
        assert opt["min_gibbs_energy"] < 1e-5

    def test_classic_presets_catalog(self):
        """Verifies presence and configuration of all Mallik (1986) historical presets."""
        presets = KaufmanMallikEngine.get_classic_presets()
        required_keys = [
            "isomorphous_ideal",
            "miscibility_gap_solid",
            "peritectic_positive_E",
            "monotectic_high_E",
            "allotropy_eutectoid",
            "ternary_mo_v_w",
            "ternary_cd_pb_sn",
        ]
        for rk in required_keys:
            assert rk in presets
            assert "name" in presets[rk]
            assert "topology" in presets[rk]


class TestCAEDaemonKaufmanMallikRPC:
    """Verifies that CAE Daemon properly routes all Kaufman-Mallik RPC requests."""

    def test_daemon_handle_calculate_kaufman_mallik_binary(self):
        req = {
            "t_kelvin": 1200.0,
            "delta_g_a": -1500.0,
            "delta_g_b": 2000.0,
            "e_alpha": 4500.0,
            "e_beta": 4500.0,
            "use_calories": True,
        }
        res = CAEDaemon.handle_calculate_kaufman_mallik_binary(req)
        assert res["converged"] is True
        assert "x_alpha" in res
        assert "x_beta" in res

    def test_daemon_handle_invert_interaction_parameters(self):
        req = {
            "t_kelvin": 1200.0,
            "x_alpha": 0.887756,
            "x_beta": 0.079397,
            "delta_g_a": -1500.0,
            "delta_g_b": 2000.0,
            "use_calories": True,
        }
        res = CAEDaemon.handle_invert_interaction_parameters(req)
        assert math.isclose(res["e_alpha"], 4500.0, abs_tol=1.0)
        assert math.isclose(res["e_beta"], 4500.0, abs_tol=1.0)

    def test_daemon_handle_calculate_miscibility_gap(self):
        req = {
            "interaction_parameter": 3000.0,
            "t_kelvin": 600.0,
            "use_calories": True,
        }
        res = CAEDaemon.handle_calculate_miscibility_gap(req)
        assert res.get("miscible") is not True
        assert "binodal_x1" in res
        assert "spinodal_x1" in res

    def test_daemon_handle_get_kaufman_mallik_presets(self):
        res = CAEDaemon.handle_get_kaufman_mallik_presets({})
        assert "presets" in res
        assert "peritectic_positive_E" in res["presets"]
        assert "monotectic_high_E" in res["presets"]
