"""
Unit tests for UnaryDiagramEngine (Water P-T phase diagram & Clapeyron phase boundaries).
"""

import pytest
import math
from pycalphad_app.core.unary_diagram_engine import UnaryDiagramEngine


def test_unary_invariants_h2o():
    eng = UnaryDiagramEngine("H2O")
    diag = eng.compute_diagram_curves()

    invar = diag["invariants"]
    # Triple point
    assert invar["triple_point"]["T_C"] == 0.01
    assert abs(invar["triple_point"]["P_atm"] - 0.006) < 0.001

    # Critical point
    assert invar["critical_point"]["T_C"] == 374.0
    assert invar["critical_point"]["P_atm"] == 218.0

    # Normal melting point at 1 atm has negative offset (near 0 C)
    norm_melt = invar["normal_melting"]["T_C"]
    assert -5.0 < norm_melt < 0.1


def test_unary_phase_classification():
    eng = UnaryDiagramEngine("H2O")

    # Ice at -20 C, 1 atm (log10 P = 0)
    assert eng.evaluate_phase(-20.0, 0.0) == "solid"

    # Liquid water at 25 C, 1 atm
    assert eng.evaluate_phase(25.0, 0.0) == "liquid"

    # Steam at 150 C, 1 atm
    assert eng.evaluate_phase(150.0, 0.0) == "gas"

    # Low pressure vapor at -40 C, 1e-4 atm (log10 P = -4)
    assert eng.evaluate_phase(-40.0, -4.0) == "gas"

    # Supercritical fluid at 400 C, 300 atm (log10 P ~ 2.47)
    assert eng.evaluate_phase(400.0, math.log10(300.0)) == "supercritical"


def test_anomalous_fusion_slope():
    eng = UnaryDiagramEngine("H2O")
    # Melting temperature decreases as pressure increases: dP/dT < 0 -> dT/dP < 0
    t_fus_1atm = eng.fusion_temperature_c(0.0)
    t_fus_100atm = eng.fusion_temperature_c(2.0)
    assert t_fus_100atm < t_fus_1atm
