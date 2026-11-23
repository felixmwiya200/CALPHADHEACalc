# -*- coding: utf-8 -*-
"""
test_magnesium_engine.py - Unit and benchmark tests for MagnesiumEngine
Tests AZ91D die casting alloy (HCP_Mg matrix, Mg17Al12 eutectic, density ~ 1.81 g/cm3)
and AZ31B wrought alloy tension-compression yield asymmetry.
"""

import pytest
from pycalphad_app.core.magnesium_engine import MagnesiumEngine


def test_az91d_die_casting_properties():
    # AZ91D: Mg-9.0Al-0.7Zn-0.2Mn (wt. %)
    comp = {"Mg": 90.1, "Al": 9.0, "Zn": 0.7, "Mn": 0.2}
    engine = MagnesiumEngine("Magnesium Alloys", comp, grain_size_um=20.0, process_type="Casting")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "Eutectic_Mg17Al12_C" in trans
    # Mg-Al eutectic reaction L -> alpha + Mg17Al12 is at 437 C
    assert 430.0 <= trans["Eutectic_Mg17Al12_C"] <= 445.0
    assert 850.0 <= trans["T_Liquidus_K"] <= 890.0

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    assert "HCP_Mg" in phases
    assert "Beta_Mg17Al12" in phases
    # AZ91D typically has ~ 10-14% divorced/eutectic beta phase
    assert 0.08 <= phases["Beta_Mg17Al12"] <= 0.16

    # 3. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Die cast AZ91D proof strength ~ 140 - 180 MPa, UTS ~ 210 - 260 MPa
    assert 130.0 <= mech["YieldStrength_MPa"] <= 190.0
    assert mech["UTS_MPa"] >= 200.0

    # 4. Ultra-low density
    transp = engine.compute_transport_properties(thermo)
    assert 1.78 <= transp["TheoreticalDensity_g_cm3"] <= 1.84


def test_az31b_tension_compression_asymmetry():
    # AZ31B Wrought: Mg-3.0Al-1.0Zn-0.3Mn (wt. %)
    comp = {"Mg": 95.7, "Al": 3.0, "Zn": 1.0, "Mn": 0.3}
    engine = MagnesiumEngine("Magnesium Alloys", comp, grain_size_um=15.0, process_type="Wrought")

    trans = engine.compute_phase_transformations()
    thermo = engine.compute_thermodynamics()
    mech = engine.compute_mechanical_properties(thermo, trans)

    # In wrought Mg alloys, {10-12} extension twinning causes profound yield asymmetry:
    # Compressive yield strength is significantly lower than tensile yield strength!
    assert "TensileYieldStrength_MPa" in mech
    assert "CompressiveYieldStrength_MPa" in mech
    assert mech["TensileYieldStrength_MPa"] > mech["CompressiveYieldStrength_MPa"]
    asymmetry_ratio = mech["CompressiveYieldStrength_MPa"] / mech["TensileYieldStrength_MPa"]
    assert 0.60 <= asymmetry_ratio <= 0.88
