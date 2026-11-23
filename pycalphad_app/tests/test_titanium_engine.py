# -*- coding: utf-8 -*-
"""
test_titanium_engine.py - Unit and benchmark tests for TitaniumEngine
Tests Ti-6Al-4V (alpha+beta transus, Al/Mo equivalents, martensitic transformation,
and mechanical strength) and CP-Ti (unalloyed alpha Grade 2).
"""

import pytest
from pycalphad_app.core.titanium_engine import TitaniumEngine


def test_ti_6al_4v_transus_and_mechanics():
    # Ti-6Al-4V (Grade 5): Ti-6.0Al-4.0V-0.2Fe-0.18O (wt. %)
    comp = {"Ti": 89.62, "Al": 6.0, "V": 4.0, "Fe": 0.2, "O": 0.18}
    engine = TitaniumEngine("Titanium Alloys", comp, grain_size_um=12.0, process_type="Wrought")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "T_beta_transus_C" in trans
    assert "Al_Equivalent" in trans
    assert "Mo_Equivalent" in trans
    # Benchmark: Ti-6Al-4V beta transus is 995 +/- 15 C (approx 980 - 1010 C)
    assert 975.0 <= trans["T_beta_transus_C"] <= 1015.0
    assert trans["AlloyClass"] == "Alpha+Beta Alloy"

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    assert "HCP_Alpha" in phases
    assert "BCC_Beta" in phases
    # In annealed state at room temp, ~90-95% alpha and ~5-10% retained beta
    assert 0.85 <= phases["HCP_Alpha"] <= 0.96
    # Liquidus ~ 1660 C (1933 K), Solidus ~ 1605 C (1878 K)
    assert 1850.0 <= thermo["T_Solidus"] <= 1920.0
    assert 1900.0 <= thermo["T_Liquidus"] <= 1980.0

    # 3. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Ti-6Al-4V annealed proof yield >= 828 MPa (ASTM B265 requirement, typical ~880-920 MPa)
    assert 850.0 <= mech["YieldStrength_MPa"] <= 1000.0
    assert mech["UTS_MPa"] >= 930.0
    assert mech["Elongation_pct"] >= 10.0
    # Density ~ 4.43 g/cm3
    transp = engine.compute_transport_properties(thermo)
    assert 4.35 <= transp["TheoreticalDensity_g_cm3"] <= 4.50


def test_cp_titanium_grade_2():
    # Grade 2 CP Titanium: unalloyed Ti with controlled interstitial O
    comp = {"Ti": 99.5, "O": 0.2, "Fe": 0.2, "C": 0.05, "N": 0.02}
    engine = TitaniumEngine("Titanium Alloys", comp, grain_size_um=20.0, process_type="Annealed")

    trans = engine.compute_phase_transformations()
    assert trans["AlloyClass"] == "Alpha Alloy (CP-Ti)"
    # Pure Ti transus is 882 C; 0.2% O raises it slightly to ~ 910-920 C
    assert 885.0 <= trans["T_beta_transus_C"] <= 935.0

    thermo = engine.compute_thermodynamics()
    assert thermo["Phases"]["HCP_Alpha"] >= 0.98

    mech = engine.compute_mechanical_properties(thermo, trans)
    # Grade 2 Yield ~ 275 - 380 MPa
    assert 250.0 <= mech["YieldStrength_MPa"] <= 420.0
    assert mech["Elongation_pct"] >= 20.0
