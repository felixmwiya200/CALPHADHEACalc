# -*- coding: utf-8 -*-
"""
test_all_alloy_engines.py - Comprehensive Multi-Alloy Family Integration Test
Runs calculations across all 14 databases using MaterialDatabaseSelector.get_engine(...)
and verifies that every alloy family produces authentic domain-specific thermodynamics,
phase transformations, constitutive mechanics, transport, and environmental properties.
"""

import pytest
from pycalphad_app.database.material_selector import MaterialDatabaseSelector


@pytest.mark.parametrize("db_name", MaterialDatabaseSelector.get_database_list())
def test_all_14_database_engines_execute_cleanly(db_name):
    presets = MaterialDatabaseSelector.get_presets_for_database(db_name)
    if presets:
        first_preset_name = list(presets.keys())[0]
        comp = presets[first_preset_name]
    else:
        comp = {"Fe": 70.0, "Ni": 20.0, "Cr": 10.0}

    engine = MaterialDatabaseSelector.get_engine(db_name, comp, grain_size_um=20.0, process_type="Wrought")
    assert engine is not None

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert isinstance(trans, dict)
    assert "T_Liquidus_K" in trans
    assert "T_Solidus_K" in trans
    assert trans["T_Liquidus_K"] >= trans["T_Solidus_K"]

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    assert isinstance(thermo, dict)
    assert "Phases" in thermo
    assert len(thermo["Phases"]) >= 1
    # Check sum of phase fractions is approximately 1.0
    total_frac = sum(thermo["Phases"].values())
    assert 0.95 <= total_frac <= 1.05

    # 3. Mechanical properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    assert isinstance(mech, dict)
    assert "YieldStrength_MPa" in mech
    assert mech["YieldStrength_MPa"] > 0
    assert "UTS_MPa" in mech
    assert mech["UTS_MPa"] >= mech["YieldStrength_MPa"]
    assert "Elongation_pct" in mech
    assert "VickersHardness_HV" in mech

    # 4. Transport properties
    transp = engine.compute_transport_properties(thermo)
    assert isinstance(transp, dict)
    assert "TheoreticalDensity_g_cm3" in transp
    assert transp["TheoreticalDensity_g_cm3"] > 1.0
    assert "ThermalConductivity_W_mK" in transp
    assert transp["ThermalConductivity_W_mK"] > 0.0

    # 5. Environmental properties
    corr, ox = engine.compute_environmental_properties(thermo)
    assert isinstance(corr, dict)
    assert isinstance(ox, dict)
    assert "CorrosionRate_mpy" in corr
    assert "MaxServiceTemperature_C" in ox

    # 6. Single temperature step
    step = engine.compute_single_temperature_step(300.0)
    assert isinstance(step, dict)
    assert "Phases" in step
    assert "DominantPhase" in step
