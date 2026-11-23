# -*- coding: utf-8 -*-
"""
test_zirconium_engine.py - Unit and benchmark tests for ZirconiumEngine
Tests Zircaloy-4 nuclear fuel cladding (alpha -> beta transus, low thermal neutron
capture cross-section, and hydride precipitation TSSH).
"""

import pytest
from pycalphad_app.core.zirconium_engine import ZirconiumEngine


def test_zircaloy_4_nuclear_cladding():
    # Zircaloy-4: Zr-1.50Sn-0.21Fe-0.10Cr-0.12O (wt. %)
    comp = {"Zr": 98.07, "Sn": 1.50, "Fe": 0.21, "Cr": 0.10, "O": 0.12}
    engine = ZirconiumEngine("Zirconium Alloys", comp, grain_size_um=10.0, process_type="Wrought")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "T_alpha_to_beta_transus_C" in trans
    # In Zircaloy-4, alpha+beta transus begins at ~ 815 C and reaches full beta at ~ 970 C
    assert 800.0 <= trans["T_alpha_start_C"] <= 840.0
    assert 940.0 <= trans["T_beta_finish_C"] <= 1000.0

    # 2. Nuclear thermal neutron cross-section
    assert "ThermalNeutronCrossSection_barns" in trans
    # Pure nuclear-grade Zircaloy has ultra-low absorption cross-section < 0.25 barns
    assert trans["ThermalNeutronCrossSection_barns"] <= 0.25

    # 3. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    assert "HCP_Alpha_Zr" in phases
    assert phases["HCP_Alpha_Zr"] >= 0.98
    # Solidus ~ 1810 C (2083 K), Liquidus ~ 1850 C (2123 K)
    assert 2050.0 <= thermo["T_Solidus"] <= 2120.0
    assert 2100.0 <= thermo["T_Liquidus"] <= 2160.0

    # 4. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Zircaloy-4 proof yield ~ 380 - 450 MPa, UTS ~ 500 - 580 MPa
    assert 360.0 <= mech["YieldStrength_MPa"] <= 480.0
    assert mech["UTS_MPa"] >= 480.0
    assert mech["Elongation_pct"] >= 16.0
