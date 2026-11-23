# -*- coding: utf-8 -*-
"""
test_aluminium_engine.py - Unit and benchmark tests for AluminiumEngine
Tests AA 7075-T6 aerospace zinc-magnesium precipitation hardening (FCC_Al matrix,
MgZn2 solvus, yield strength >= 480 MPa) and A356 casting eutectic.
"""

import pytest
from pycalphad_app.core.aluminium_engine import AluminiumEngine


def test_aa_7075_t6_aerospace_alloy():
    # AA 7075: Al-5.6Zn-2.5Mg-1.6Cu-0.23Cr-0.4Fe-0.4Si (wt. %)
    comp = {
        "Al": 89.27, "Zn": 5.6, "Mg": 2.5, "Cu": 1.6,
        "Cr": 0.23, "Fe": 0.4, "Si": 0.4
    }
    engine = AluminiumEngine("Aluminium Alloys", comp, grain_size_um=25.0, process_type="Wrought")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "T_solvus_C" in trans
    # In 7075, eta (MgZn2) solvus is approx 460 - 490 C
    assert 450.0 <= trans["T_solvus_C"] <= 510.0
    assert trans["Series"] == "7xxx (Al-Zn-Mg-Cu)"

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    # MUST be FCC_Al matrix, never BCC!
    assert "FCC_Al" in phases
    assert "Eta_MgZn2" in phases
    assert phases["FCC_Al"] >= 0.90
    # AA 7075 solidus is ~ 477 C (750.15 K), liquidus is ~ 635 C (908.15 K)
    assert 730.0 <= thermo["T_Solidus"] <= 770.0
    assert 890.0 <= thermo["T_Liquidus"] <= 930.0

    # 3. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # T6 temper yields high strength: Proof yield >= 480 MPa (ASTM B209)
    assert 470.0 <= mech["YieldStrength_MPa"] <= 560.0
    assert mech["UTS_MPa"] >= 530.0
    assert mech["Elongation_pct"] >= 8.0

    # 4. Density ~ 2.81 g/cm3
    transp = engine.compute_transport_properties(thermo)
    assert 2.75 <= transp["TheoreticalDensity_g_cm3"] <= 2.85


def test_a356_cast_aluminium_alloy():
    # A356: Al-7.0Si-0.35Mg-0.1Fe (wt. %)
    comp = {"Al": 92.55, "Si": 7.0, "Mg": 0.35, "Fe": 0.1}
    engine = AluminiumEngine("Aluminium Alloys", comp, grain_size_um=35.0, process_type="Casting")

    trans = engine.compute_phase_transformations()
    assert trans["Series"] == "Cast Al-Si (A3xx)"
    # Al-Si eutectic is at ~ 577 C (850 K)
    assert 560.0 <= trans["Eutectic_Al_Si_C"] <= 585.0

    thermo = engine.compute_thermodynamics()
    assert "Eutectic_Silicon" in thermo["Phases"]
    assert thermo["Phases"]["FCC_Al"] >= 0.88
