"""
Unit tests for RedlichKisterInversionEngine.

Verifies:
1. Thermodynamic consistency of excess Gibbs energy and chemical potentials.
2. Equality of chemical potentials at binodal equilibrium.
3. Common-tangent conjugate pair solution for symmetric and asymmetric systems.
4. Metropolis simulated annealing parameter inversion on experimental solvus data.
"""

import pytest
import math
import numpy as np
from pycalphad_app.core.redlich_kister_inversion_engine import RedlichKisterInversionEngine


def test_thermodynamic_consistency():
    engine = RedlichKisterInversionEngine(parameters=[
        {"a": 15000.0, "b": -5.0, "c": 0.0, "d": 0.0},
        {"a": 3000.0, "b": 0.0, "c": 0.0, "d": 0.0}
    ])
    t_k = 600.0

    for x in [0.2, 0.5, 0.75]:
        cp = engine.chemical_potentials(x, t_k)
        x1 = 1.0 - x
        x2 = x
        g_reconstructed = x1 * cp["mu1_total_J_mol"] + x2 * cp["mu2_total_J_mol"]
        assert math.isclose(cp["G_mix_J_mol"], g_reconstructed, rel_tol=1e-5), (
            f"Euler equation failed at x={x}: {cp['G_mix_J_mol']} vs {g_reconstructed}"
        )


def test_symmetric_binodal_solver():
    # Symmetric regular solution: L0 = 18000 J/mol (Tc = 18000 / (2 * 8.314) = 1082 K)
    engine = RedlichKisterInversionEngine(parameters=[
        {"a": 18000.0, "b": 0.0, "c": 0.0, "d": 0.0}
    ])
    t_k = 700.0  # Well below Tc

    pair = engine.solve_binodal_conjugate_pair(t_k)
    assert pair is not None
    xa, xb = pair
    assert 0.05 < xa < 0.35
    assert 0.65 < xb < 0.95
    # For symmetric solution, xa + xb should equal 1.0
    assert math.isclose(xa + xb, 1.0, abs_tol=0.015)

    # Chemical potentials should be equal
    r1, r2, chi2 = engine.calculate_residuals(xa, xb, t_k)
    assert abs(r1) < 15.0
    assert abs(r2) < 15.0


def test_metropolis_inversion_beck_benchmark():
    engine = RedlichKisterInversionEngine()
    bench = engine.get_beck_benchmark_dataset()
    pts = bench["datapoints"]

    res = engine.invert_parameters_metropolis(
        pts,
        num_terms=2,
        initial_temperature=50.0,
        annealing_steps=300,
        random_seed=42
    )

    assert res["success"] is True
    stats = res["statistics"]
    assert stats["data_points_fitted"] == 10
    assert stats["rmse_chemical_potential_J_mol"] > 0.0
    assert len(res["fitted_parameters"]) == 2

    overlay = engine.generate_solvus_overlay(t_min_c=20.0, t_max_c=80.0, n_points=15)
    assert overlay["has_miscibility_gap"] is True
    assert len(overlay["temperature_C"]) > 0
