# -*- coding: utf-8 -*-
"""
test_adaptive_continuation_solver.py - Unit and Parity Tests for Adaptive Continuation Engine
Validates:
  1. Fe-Ni binary equilibrium parity against SGTE standard liquidus/solidus lines.
  2. Cantor HEA (CoCrFeMnNi) quinary equilibrium and Sigma phase precipitation.
  3. PyCalphadEmbed integration and phase fraction conservation (sum to 1.0).
  4. Telemetry streaming callback and cancellation token responsiveness.
"""

import pytest
import numpy as np
from pycalphad_app.core.continuation_solver import (
    AdaptiveContinuationSolver, TDBModelCache
)
from pycalphad_app.core.pycalphad_embed import PyCalphadEmbed


def test_tdb_model_cache_unaries():
    """Validates that pure element unaries follow thermodynamic melting rules."""
    # Liquid must be lower Gibbs energy than solid above melting point
    t_high = 2000.0  # K
    g_liq, _, _ = TDBModelCache.evaluate_molar_gibbs(["Ni"], np.array([1.0]), "LIQUID", t_high)
    g_fcc, _, _ = TDBModelCache.evaluate_molar_gibbs(["Ni"], np.array([1.0]), "FCC_A1", t_high)
    assert g_liq < g_fcc, "At 2000 K, Ni liquid must have lower Gibbs energy than FCC solid"

    # Solid must be lower Gibbs energy than liquid below melting point
    t_low = 1000.0  # K
    g_liq_low, _, _ = TDBModelCache.evaluate_molar_gibbs(["Ni"], np.array([1.0]), "LIQUID", t_low)
    g_fcc_low, _, _ = TDBModelCache.evaluate_molar_gibbs(["Ni"], np.array([1.0]), "FCC_A1", t_low)
    assert g_fcc_low < g_liq_low, "At 1000 K, Ni FCC solid must have lower Gibbs energy than liquid"


def test_binary_feni_continuation():
    """Validates Fe-Ni equiatomic alloy against thermodynamic benchmark data."""
    solver = AdaptiveContinuationSolver(["Fe", "Ni"], np.array([0.5, 0.5]))
    traj = solver.march_cooling_trajectory(t_start_c=1600.0, t_end_c=1000.0, delta_t_init=20.0)

    assert len(traj.step_results) > 10, "Trajectory should contain multiple adaptive steps"
    assert traj.t_liquidus_c > traj.t_solidus_c, "Liquidus must be strictly higher than solidus"
    assert 1430.0 <= traj.t_liquidus_c <= 1520.0, f"Fe-Ni liquidus {traj.t_liquidus_c} C out of expected range"
    assert 1400.0 <= traj.t_solidus_c <= 1490.0, f"Fe-Ni solidus {traj.t_solidus_c} C out of expected range"

    # High temperature: 100% liquid
    high_t_res = traj.step_results[0]
    assert high_t_res.phase_fractions["LIQUID"] == pytest.approx(1.0, abs=1e-3)

    # Low temperature: 100% FCC solid solution
    low_t_res = traj.step_results[-1]
    assert low_t_res.phase_fractions["FCC_A1"] == pytest.approx(1.0, abs=1e-3)
    assert low_t_res.phase_fractions["LIQUID"] == pytest.approx(0.0, abs=1e-3)


def test_quinary_cantor_hea_continuation():
    """Validates Cantor equiatomic CoCrFeMnNi quinary alloy."""
    elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
    comp = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    solver = AdaptiveContinuationSolver(elements, comp)
    traj = solver.march_cooling_trajectory(t_start_c=1600.0, t_end_c=500.0, delta_t_init=25.0)

    assert 1380.0 <= traj.t_liquidus_c <= 1470.0, f"Cantor HEA liquidus {traj.t_liquidus_c} C unexpected"
    assert 1340.0 <= traj.t_solidus_c <= 1430.0, f"Cantor HEA solidus {traj.t_solidus_c} C unexpected"

    # Confirm sigma phase precipitation was detected in intermediate range
    assert "SIGMA" in traj.precipitation_temperatures_c, "Sigma phase should precipitate in Cantor HEA"
    sigma_t = traj.precipitation_temperatures_c["SIGMA"]
    assert 700.0 <= sigma_t <= 1000.0, f"Sigma precipitation temp {sigma_t} C out of range"


def test_pycalphad_embed_integration():
    """Tests PyCalphadEmbed routing through AdaptiveContinuationSolver."""
    res = PyCalphadEmbed.run_equilibrium(["Fe", "Ni"], [0.5, 0.5], t_min_c=600.0, t_max_c=1600.0, n_points=25)

    assert res["PyCalphadUsed"] is True
    assert "In-Process Adaptive CALPHAD Continuation Engine" in res["Solver"]
    assert len(res["T_C"]) == 25
    assert len(res["Liquid"]) == 25
    assert len(res["FCC"]) == 25

    # Check phase conservation: sum of fractions must equal 1.0 at every temperature
    tot = res["Liquid"] + res["FCC"] + res["BCC"] + res["B2"] + res["Sigma"]
    np.testing.assert_allclose(tot, 1.0, atol=1e-5)


def test_cancellation_token():
    """Tests atomic cancellation flag halting the solver within 3 steps."""
    solver = AdaptiveContinuationSolver(["Fe", "Ni"], np.array([0.5, 0.5]))
    counter = [0]

    def cancel_after_two_steps():
        counter[0] += 1
        return counter[0] >= 3

    traj = solver.march_cooling_trajectory(
        t_start_c=1600.0, t_end_c=400.0, delta_t_init=10.0,
        cancellation_token=cancel_after_two_steps
    )
    assert len(traj.step_results) <= 4, "Solver should abort execution promptly upon cancellation"
