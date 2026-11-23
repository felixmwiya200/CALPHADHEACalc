# -*- coding: utf-8 -*-
"""
test_nickel_superalloy_engine.py - Unit and benchmark tests for NickelSuperalloyEngine
Tests Inconel 718 (gamma'' / gamma' precipitation, solvus), CMSX-4 single crystal
lattice misfit rafting parameter, New PHACOMP Md calculation for TCP phase stability,
and Monkman-Grant high-temperature creep response.
"""

import pytest
from pycalphad_app.core.nickel_superalloy_engine import NickelSuperalloyEngine


def test_inconel_718_precipitation_and_mechanics():
    # Inconel 718: Ni-19Cr-18.5Fe-5.1Nb-3.0Mo-0.9Ti-0.5Al-0.04C (wt. %)
    comp = {
        "Ni": 53.0, "Cr": 19.0, "Fe": 18.5, "Nb": 5.1,
        "Mo": 3.0, "Ti": 0.9, "Al": 0.5, "C": 0.04
    }
    engine = NickelSuperalloyEngine("Nickel & Fe-Ni Superalloys", comp, grain_size_um=15.0, process_type="Forging")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "T_gamma_prime_solvus_C" in trans
    assert "T_gamma_double_prime_solvus_C" in trans
    # Inconel 718 gamma'' solvus is approx 900 - 1020 C (delta solvus ~ 1010 C)
    assert 880.0 <= trans["T_gamma_double_prime_solvus_C"] <= 1040.0
    assert trans["HasGammaDoublePrime"] is True

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    assert "Gamma_Matrix" in phases
    assert "Gamma_Double_Prime" in phases or "Gamma_Prime" in phases
    # Inconel 718 liquidus is ~ 1335 C (1608 K), solidus ~ 1260 C (1533 K)
    assert 1550.0 <= thermo["T_Liquidus"] <= 1650.0

    # 3. High-strength precipitation hardening
    mech = engine.compute_mechanical_properties(thermo, trans)
    assert mech["YieldStrength_MPa"] >= 950.0
    assert mech["UTS_MPa"] >= 1200.0


def test_cmsx4_single_crystal_rafting_and_phacomp():
    # CMSX-4 Second Generation Single Crystal Superalloy:
    # Ni-6.5Cr-9.0Co-0.6Mo-6.0W-5.6Al-1.0Ti-6.5Ta-3.0Re-0.1Hf (wt. %)
    comp = {
        "Ni": 61.8, "Cr": 6.5, "Co": 9.0, "Mo": 0.6, "W": 6.0,
        "Al": 5.6, "Ti": 1.0, "Ta": 6.5, "Re": 3.0, "Hf": 0.1
    }
    engine = NickelSuperalloyEngine("Nickel & Fe-Ni Superalloys", comp, grain_size_um=1000.0, process_type="Wrought")

    trans = engine.compute_phase_transformations()
    # CMSX-4 gamma' solvus is very high: ~ 1250 - 1300 C
    assert trans["T_gamma_prime_solvus_C"] >= 1200.0

    # New PHACOMP Md calculation
    assert "New_PHACOMP_Md" in trans
    # CMSX-4 is chemically balanced to avoid TCP embrittlement (Md <= 0.985)
    assert trans["New_PHACOMP_Md"] <= 0.985
    assert trans["TCP_Risk"] == "Safe (Microstructurally Stable)"

    # Negative lattice misfit delta < 0 promotes N-type rafting perpendicular to tensile axis
    assert "LatticeMisfit_delta" in trans
    assert trans["LatticeMisfit_delta"] < 0.0

    thermo = engine.compute_thermodynamics()
    # High volume fraction of gamma' (approx 65-70%)
    assert thermo["Phases"]["Gamma_Prime"] >= 0.55
