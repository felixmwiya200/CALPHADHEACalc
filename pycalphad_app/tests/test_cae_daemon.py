# -*- coding: utf-8 -*-
"""
test_cae_daemon.py - Unit tests for headless CAE IPC Daemon
Verifies JSON-RPC protocol handling over standard IO pipes for C# frontend client.
"""

import json
import pytest
from pycalphad_app.server.cae_daemon import CAEDaemon


def test_daemon_ping():
    resp = CAEDaemon.handle_ping({})
    assert resp["status"] == "ok"
    assert "version" in resp
    assert resp["pycalphad_ready"] is True


def test_daemon_get_databases():
    resp = CAEDaemon.handle_get_databases({})
    assert "databases" in resp
    assert "names" in resp
    assert "High Entropy Alloys" in resp["names"]
    assert len(resp["names"]) == 14


def test_daemon_get_presets():
    resp = CAEDaemon.handle_get_presets({"database_name": "High Entropy Alloys"})
    assert resp["database_name"] == "High Entropy Alloys"
    assert any("Cantor" in p for p in resp["presets"])


def test_daemon_calculate_equilibrium():
    payload = {
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20},
        "basis": "at%",
        "grain_size_um": 25.0,
        "calc_mode": "fast"
    }
    resp = CAEDaemon.handle_calculate_equilibrium(payload)
    assert resp["status"] == "success"
    assert "thermo" in resp
    assert "transformations" in resp
    assert "mechanical" in resp
    assert "transport" in resp
    assert "piecewise" in resp
    assert len(resp["piecewise"]) == 21
    for pw in resp["piecewise"]:
        assert pw["property"]
        assert pw["code"].strip(), f"Empty COMSOL piecewise code for {pw['property']}"
        assert pw["smooth_expr"].strip(), f"Empty smooth_expr for {pw['property']}"


def test_daemon_calculate_single_step():
    payload = {
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20},
        "temperature": 1400.0
    }
    resp = CAEDaemon.handle_calculate_single_step(payload)
    assert resp["temperature"] == 1400.0
    assert "phases" in resp
    assert isinstance(resp["phases"], dict)
    assert "hardness_hv" in resp
    assert "hardness_hrc" in resp
    assert "hardness_hrb" in resp
    assert "rockwell_hardness" in resp and resp["rockwell_hardness"]


def test_daemon_basis_consistency_wt_at_mol():
    req_at = {
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20},
        "basis": "at%",
        "calc_mode": "fast"
    }
    req_mol = {
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2},
        "basis": "mol",
        "calc_mode": "fast"
    }
    r_at = CAEDaemon.handle_calculate_equilibrium(req_at)
    r_mol = CAEDaemon.handle_calculate_equilibrium(req_mol)
    assert abs(r_at["thermo"]["Solidus_K"] - r_mol["thermo"]["Solidus_K"]) < 0.5
    assert abs(r_at["thermo"]["Density_g_cm3"] - r_mol["thermo"]["Density_g_cm3"]) < 0.01


def test_daemon_calc_log_iterations_and_interrupt():
    import threading
    resp = CAEDaemon.handle_calculate_equilibrium({
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 22.2, "Cr": 22.2, "Fe": 22.2, "Ni": 22.2, "Nb": 11.2},
        "basis": "at%",
        "calc_mode": "fast"
    })
    assert "calc_log" in resp and len(resp["calc_log"]) >= 5
    assert any("Calculating...to interrupt press the 's' key" in line for line in resp["calc_log"])
    assert any("T(K) =" in line for line in resp["calc_log"])

    ev = threading.Event()
    ev.set()
    interrupted_resp = CAEDaemon.handle_calculate_equilibrium({
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20},
        "basis": "at%",
        "calc_mode": "fast"
    }, cancel_event=ev)
    assert interrupted_resp["status"] == "interrupted"


def test_daemon_rockwell_and_vickers_hardness():
    resp = CAEDaemon.handle_calculate_equilibrium({
        "database_name": "General Steel",
        "composition": {"Fe": 98.0, "C": 0.8, "Mn": 0.7, "Si": 0.5},
        "basis": "wt%",
        "calc_mode": "fast"
    })
    mech = resp["mechanical"]
    assert mech["VickersHardness_HV"] > 0
    assert "RockwellHardness_HRC" in mech
    assert "RockwellHardness_HRB" in mech
    assert mech["RockwellScale"] in ("HRC", "HRB")
    assert len(resp["temp_series"]["hardness_hv"]) == len(resp["temp_series"]["t_mech_k"])
    assert len(resp["temp_series"]["hardness_hrc"]) == len(resp["temp_series"]["t_mech_k"])
    assert len(resp["temp_series"]["hardness_hrb"]) == len(resp["temp_series"]["t_mech_k"])

    sim_h = CAEDaemon.handle_run_simulation_module({
        "module": "strength_hardness",
        "database_name": "General Steel",
        "composition": {"Fe": 98.0, "C": 0.8, "Mn": 0.7, "Si": 0.5}
    })
    assert len(sim_h["curves"]) == 3
    assert "HV" in sim_h["summary"] and ("HRC" in sim_h["summary"] or "HRB" in sim_h["summary"])


def test_git_tdb_catalog_and_updated_periodic_elements():
    db_resp = CAEDaemon.handle_get_databases({})
    tdb_names = {item["name"] for item in db_resp.get("tdb_catalog", [])}
    for expected in [
        "LibreCALPHAD_mf_steel.tdb",
        "MatCalc_mc_fe_v2062_clean.tdb",
        "OpenCALPHAD_Al_Co_Cr_Fe_Ni.tdb",
        "COST507_LightAlloys_Git.tdb"
    ]:
        assert expected in tdb_names

    elems_resp = CAEDaemon.handle_get_elements({})
    elems = {e["symbol"]: e for e in elems_resp["elements"]}
    assert len(elems) == 118
    assert elems["Na"]["tm_k"] < 400.0
    assert elems["K"]["tm_k"] < 400.0
    assert elems["U"]["density_g_cm3"] > 18.0


def test_daemon_export_cae_card_all_targets():
    """Verifies all FEA/forming deck exporters work cleanly through CAEDaemon, even before calculation."""
    comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    expected_markers = {
        "abaqus": "*MATERIAL",
        "ansys": "MPDATA,DENS",
        "comsol": "% COMSOL Multiphysics",
        "forge": "TRANSVALOR FORGE",
        "deform": "SFTC DEFORM-3D",
        "simufact": "<SimufactMaterial",
        "lsdyna": "*MAT_THERMAL_ISOTROPIC_TD_LC",
        "sysweld": "/PREP7",
    }
    for fmt, marker in expected_markers.items():
        res = CAEDaemon.handle_export_cae_card({
            "format": fmt,
            "alloy_name": "Cantor_HEA",
            "composition": comp,
            "thermo": None,
            "mechanical": None,
        })
        assert res["format"] == fmt
        assert marker in res["content"]


def test_daemon_sigma_crystal_and_physics_temp_series():
    """Verifies Sigma crystal model generation and HEAEngine-backed temp_series Sy(T) via CAEDaemon."""
    resp = CAEDaemon.handle_calculate_equilibrium({
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 23.25, "Cr": 23.25, "Fe": 23.25, "Ni": 23.25, "Mo": 7.0},
        "basis": "at%",
        "grain_size_um": 20.0,
        "calc_mode": "fast",
    })
    assert resp["status"] == "success"
    archetypes = {m["archetype"] for m in resp["crystal_structures"]}
    assert "SIGMA_D8B" in archetypes

    sy_curve = resp["temp_series"]["yield_strength"]
    assert sy_curve[0] > sy_curve[-1]  # 77 K > 1273 K
    assert resp["transformations"]["StackingFaultEnergy_mJ_m2"] > 0.0


def test_daemon_cef_and_uhtc_handlers():
    """Verifies Compound Energy Formalism, ternary extrapolation, and UHTC reactive wetting RPC handlers."""
    # 1. Test CEF Energy Handler
    cef_req = {
        "phase_name": "C15_LAVES",
        "sublattices": [
            {"name": "Sub1", "multiplicity": 1.0, "constituents": ["Mg", "Cu"], "site_fractions": {"Mg": 0.8, "Cu": 0.2}},
            {"name": "Sub2", "multiplicity": 2.0, "constituents": ["Mg", "Cu"], "site_fractions": {"Mg": 0.1, "Cu": 0.9}},
        ],
        "end_members": {
            "Mg:Cu": {"a": -35000.0, "b": -12.0},
            "Cu:Cu": {"a": -8000.0, "b": -4.0},
        },
        "magnetic_params": {"p": 0.28, "Tc": 0.0, "beta": 0.0},
        "t_start_c": 100.0,
        "t_end_c": 500.0,
        "t_step_c": 100.0,
    }
    cef_res = CAEDaemon.handle_calculate_cef_energy(cef_req)
    assert cef_res["phase_name"] == "C15_LAVES"
    assert len(cef_res["temperature_series"]["temperatures_C"]) == 5
    assert len(cef_res["temperature_series"]["G_m"]) == 5

    # 2. Test Extrapolation Handler
    extrap_req = {
        "x3_fixed": 0.2,
        "temperature_c": 1000.0,
        "rk_12": [[-15000.0, 2.0]],
        "rk_23": [[-10000.0, 1.0]],
        "rk_13": [[-20000.0, 3.0]],
        "num_points": 10,
    }
    extrap_res = CAEDaemon.handle_calculate_extrapolation(extrap_req)
    assert len(extrap_res["x1"]) == 11
    assert len(extrap_res["G_ex_muggianu"]) == 11
    assert len(extrap_res["G_ex_kohler"]) == 11
    assert len(extrap_res["G_ex_toop"]) == 11

    # 3. Test UHTC Wetting Handler
    uhtc_req = {
        "substrate": "ZrB2",
        "temperature_c": 1130.0,
        "steps": 20,
    }
    uhtc_res = CAEDaemon.handle_calculate_uhtc_wetting(uhtc_req)
    assert "isothermal_reaction" in uhtc_res
    assert "cooling_solidification" in uhtc_res
    iso_data = uhtc_res["isothermal_reaction"]["data"]
    assert max(iso_data["transient_tau_fraction"]) > 0.0

