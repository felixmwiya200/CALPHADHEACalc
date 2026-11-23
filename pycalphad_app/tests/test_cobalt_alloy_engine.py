# -*- coding: utf-8 -*-
"""
test_cobalt_alloy_engine.py - Unit and benchmark tests for CobaltAlloyEngine
Tests Stellite 6 (allotropic FCC -> HCP transformation, carbide volume fraction,
wear/galling resistance) and biomedical Co-Cr-Mo (ASTM F75).
"""

import pytest
from pycalphad_app.core.cobalt_alloy_engine import CobaltAlloyEngine


def test_stellite_6_carbide_and_allotropy():
    # Stellite 6: Co-28Cr-4.5W-1.2C-1.5Fe-1.0Ni-1.0Si-1.0Mn (wt. %)
    comp = {
        "Co": 61.8, "Cr": 28.0, "W": 4.5, "C": 1.2,
        "Fe": 1.5, "Ni": 1.0, "Si": 1.0, "Mn": 1.0
    }
    engine = CobaltAlloyEngine("Cobalt Alloys", comp, grain_size_um=25.0, process_type="Casting")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "T_allotropic_fcc_to_hcp_C" in trans
    # In Stellite 6, Cr and W raise the FCC -> HCP transus to ~ 600 - 850 C
    assert 600.0 <= trans["T_allotropic_fcc_to_hcp_C"] <= 900.0
    assert "Eutectic_Carbide_C" in trans

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    # Stellite 6 has ~12-15 vol.% primary/eutectic M7C3 / M23C6 carbides
    assert "Carbides_M7C3_M23C6" in phases
    assert 0.10 <= phases["Carbides_M7C3_M23C6"] <= 0.20
    assert "HCP_Epsilon" in phases or "FCC_Gamma" in phases
    # Solidus ~ 1250 - 1300 C (1523 - 1573 K), Liquidus ~ 1350 - 1410 C (1623 - 1683 K)
    assert 1500.0 <= thermo["T_Solidus"] <= 1620.0
    assert 1600.0 <= thermo["T_Liquidus"] <= 1720.0

    # 3. Hardness and wear resistance
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Stellite 6 nominal hardness is ~ 38 - 44 HRC (~ 370 - 450 HV)
    assert 360.0 <= mech["VickersHardness_HV"] <= 480.0
    assert mech["ArchardWearCoeff_mm3_Nm"] < 5.0e-5


def test_f75_biomedical_cobalt_alloy():
    # ASTM F75 Co-Cr-Mo biomedical alloy: Co-28Cr-6Mo-0.2C
    comp = {"Co": 65.8, "Cr": 28.0, "Mo": 6.0, "C": 0.2}
    engine = CobaltAlloyEngine("Cobalt Alloys", comp, grain_size_um=35.0, process_type="Casting")

    trans = engine.compute_phase_transformations()
    assert trans["T_allotropic_fcc_to_hcp_C"] >= 650.0

    thermo = engine.compute_thermodynamics()
    mech = engine.compute_mechanical_properties(thermo, trans)
    # F75 has lower carbon than Stellite 6, so lower carbide fraction and higher ductility
    assert mech["Elongation_pct"] >= 8.0
    assert mech["YieldStrength_MPa"] >= 450.0
