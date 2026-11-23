# -*- coding: utf-8 -*-
"""
test_solder_engine.py - Unit and benchmark tests for SolderEngine
Tests SAC305 lead-free solder (eutectic at 217 C, Ag3Sn and Cu6Sn5 IMCs, Anand viscoplastic
creep parameters) and Sn-37Pb eutectic solder (melting at 183 C).
"""

import pytest
from pycalphad_app.core.solder_engine import SolderEngine


def test_sac305_lead_free_solder():
    # SAC305: Sn-3.0Ag-0.5Cu (wt. %)
    comp = {"Sn": 96.5, "Ag": 3.0, "Cu": 0.5}
    engine = SolderEngine("Solders", comp, grain_size_um=10.0, process_type="Casting")

    # 1. Phase transformations
    trans = engine.compute_phase_transformations()
    assert "Eutectic_Melting_C" in trans
    # SAC305 ternary eutectic is at 217 C (490.15 K)
    assert 216.0 <= trans["Eutectic_Melting_C"] <= 221.0
    assert 488.0 <= trans["T_Solidus_K"] <= 495.0
    assert trans["IsLeadFree"] is True

    # 2. Thermodynamics
    thermo = engine.compute_thermodynamics()
    phases = thermo.get("Phases", {})
    assert "BCT_Beta_Sn" in phases
    assert "Ag3Sn_IMC" in phases
    assert "Cu6Sn5_IMC" in phases
    assert phases["BCT_Beta_Sn"] >= 0.90

    # 3. Anand Viscoplastic Creep & Mechanical Properties
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Solders have low proof yield ~ 30 - 45 MPa at RT because homologous T/Tm > 0.6!
    assert 25.0 <= mech["YieldStrength_MPa"] <= 55.0
    assert mech["UTS_MPa"] <= 75.0
    assert mech["HomologousTemperature_RT"] >= 0.55
    assert "Anand_Q_R" in mech
    assert "Anand_A" in mech


def test_sn_37pb_eutectic_solder():
    # Sn-37Pb Eutectic: Sn-37.0Pb (wt. %)
    comp = {"Sn": 63.0, "Pb": 37.0}
    engine = SolderEngine("Solders", comp, grain_size_um=15.0, process_type="Casting")

    trans = engine.compute_phase_transformations()
    assert trans["IsLeadFree"] is False
    # Classic eutectic melting at 183 C (456.15 K)
    assert 181.0 <= trans["Eutectic_Melting_C"] <= 185.0
    assert 454.0 <= trans["T_Solidus_K"] <= 458.0
    assert abs(trans["T_Liquidus_K"] - trans["T_Solidus_K"]) <= 3.0  # Zero freezing range eutectic
