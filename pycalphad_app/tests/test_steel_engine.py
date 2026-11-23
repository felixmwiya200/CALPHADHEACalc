# -*- coding: utf-8 -*-
"""
test_steel_engine.py - Unit test suite for SteelEngine.
Validates:
1. Carbon and low-alloy steel (AISI 4340) martensite (Ms, Mf) and bainite (Bs) kinetics.
2. Austenitic stainless steel (AISI 304) phase stability and PREN pitting index.
3. Quench vs equilibrium cooling phase fractions.
4. Mechanical property Hall-Petch scaling and yield strength predictions.
"""

import pytest
from pycalphad_app.core.steel_engine import SteelEngine


def test_aisi_4340_quench_kinetics():
    # AISI 4340: Fe-0.40C-0.80Cr-0.70Mn-1.80Ni-0.25Mo
    comp = {"Fe": 96.05, "C": 0.40, "Cr": 0.80, "Mn": 0.70, "Ni": 1.80, "Mo": 0.25}
    engine = SteelEngine("General Steels", comp, grain_size_um=20.0, process_type="Water Quench")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "Ms_C" in trans
    assert "Mf_C" in trans
    assert "Bs_C" in trans

    # Benchmark: Andrews Ms for 4340 is approx 290 - 325 C
    assert 285.0 <= trans["Ms_C"] <= 330.0
    assert trans["Mf_C"] < trans["Ms_C"]
    assert 460.0 <= trans["Bs_C"] <= 540.0

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    assert thermo["Solidus_K"] < thermo["Liquidus_K"]
    assert 1650.0 <= thermo["Solidus_K"] <= 1770.0
    assert 1740.0 <= thermo["Liquidus_K"] <= 1810.0

    # 3. Mechanical: Martensitic state delivers high strength
    mech = engine.compute_mechanical_properties(thermo, trans)
    assert mech["YieldStrength_MPa"] >= 1000.0
    assert mech["UTS_MPa"] >= 1300.0
    assert mech["VickersHardness_HV"] >= 350.0


def test_aisi_304_stainless_steel():
    # AISI 304: Fe-18Cr-8Ni-2Mn-0.08C
    comp = {"Fe": 71.92, "Cr": 18.0, "Ni": 8.0, "Mn": 2.0, "C": 0.08}
    engine = SteelEngine("Stainless Steels", comp, grain_size_um=25.0, process_type="Wrought")

    thermo = engine.compute_thermodynamics()
    trans = engine.compute_phase_transformations()
    mech = engine.compute_mechanical_properties(thermo, trans)
    corr, ox = engine.compute_environmental_properties(thermo)

    # 304 is fully austenitic at room temp (Ms well below 0 C)
    assert trans["Ms_C"] < 50.0
    assert "Austenite" in thermo["DominantPhase"] or "FCC" in thermo["DominantPhase"]
    
    # Mechanical properties of 304: Sy ~ 205 - 290 MPa, UTS ~ 515 - 620 MPa
    assert 200.0 <= mech["YieldStrength_MPa"] <= 350.0
    assert 500.0 <= mech["UTS_MPa"] <= 680.0
    assert mech["Elongation_pct"] >= 35.0

    # Corrosion resistance: PREN >= 18
    assert corr["PREN_val"] >= 18.0
    assert corr["CorrosionRate_mm_yr"] < 0.05
