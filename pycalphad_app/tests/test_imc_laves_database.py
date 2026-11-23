# -*- coding: utf-8 -*-
"""
Verification suite for Laves Phases (C14, C15, C36), TCP Phases (Sigma, Mu, Chi),
and Intermetallic Compounds (IMCs) integration across TDBs, Engines, XRD, and IPC Daemon.
"""

import os
import pytest
from pycalphad import Database

from pycalphad_app.database import IMCLavesDatabase, TDBManager, UnifiedHEADatabase
from pycalphad_app.core.hea_engine import HEAEngine
from pycalphad_app.core.solder_engine import SolderEngine
from pycalphad_app.core.xrd_engine import XRDEngine
from pycalphad_app.server.cae_daemon import CAEDaemon


def test_imc_laves_registry_completeness():
    phases = {p["PhaseId"]: p for p in IMCLavesDatabase.get_all_phases()}
    for required in (
        "LAVES_C14", "LAVES_C15", "LAVES_C36",
        "SIGMA", "MU_PHASE", "CHI_A12",
        "BCC_B2", "FCC_L12", "HEUSLER_L21", "D022_NI3NB",
        "FE2NB", "CR2NB", "FE2ZR", "NI3TI", "NI3NB",
        "CU6SN5", "CU3SN", "AG3SN", "MGZN2", "AL2CU", "AL3FE",
        "CR7C3", "WC", "CO6W6C"
    ):
        assert required in phases, f"Missing {required} in IMCLavesDatabase"
        assert phases[required]["CEFModel"]
        assert phases[required]["DOI"]


@pytest.mark.parametrize("rel_dir", ["pycalphad_app/database/tdb", "App/databases"])
@pytest.mark.parametrize("tdb_name,expected_phases", [
    ("IMC_Laves_Master.tdb", {"LAVES_C14", "LAVES_C15", "LAVES_C36", "SIGMA", "MU_PHASE", "CHI_A12", "CU6SN5", "CU3SN", "AG3SN", "AL2CU", "WC"}),
    ("solder_sn_ag_cu.tdb", {"AG3SN", "CU6SN5", "CU3SN"}),
    ("CrFeNi_StainlessSteel.tdb", {"BCC_A2", "FCC_A1", "SIGMA"}),
    ("AlCrNi_Superalloy.tdb", {"B2", "BCC_A2", "FCC_A1", "L12_FCC", "SIGMA"}),
    ("FeCoCrNbTi_HEA.tdb", {"LAVES_PHASE", "MU_PHASE", "SIGMA", "CHI_A12"}),
])
def test_tdb_files_parse_cleanly_in_pycalphad(rel_dir, tdb_name, expected_phases):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    tdb_path = os.path.join(root, rel_dir, tdb_name)
    assert os.path.isfile(tdb_path), f"TDB missing: {tdb_path}"
    db = Database(tdb_path)
    parsed = set(db.phases.keys())
    missing = expected_phases - parsed
    assert not missing, f"{tdb_name} missing phases {missing}"


def test_tdb_manager_discovers_imc_laves_master():
    resolved = TDBManager.find_tdb_file("IMC_Laves_Master.tdb")
    assert resolved is not None and os.path.isfile(resolved)


def test_laves_and_tcp_formation_predictions():
    # 1. CoCrFeNiNb0.5 -> Yurchenko criteria (delta >= 5%, DeltaChi_Allen >= 7%) -> C14 Laves + Fe2Nb
    nb_hea = UnifiedHEADatabase.PRESETS["CoCrFeNiNb0.5 (C14 Laves Reinforced HEA)"]
    hea_nb = HEAEngine("High Entropy Alloys", nb_hea)
    thermo_nb = hea_nb.compute_thermodynamics()
    assert "Laves_C14" in thermo_nb["Phases"]
    assert thermo_nb["Phases"]["Laves_C14"] > 0.10

    # 2. CoCrFeNiZr0.3 -> C15 Laves (Fe2Zr prototype, ideal radius ratio R_Zr/R_Fe ~ 1.27)
    zr_hea = UnifiedHEADatabase.PRESETS["CoCrFeNiZr0.3 (C15 Laves Eutectic HEA)"]
    hea_zr = HEAEngine("High Entropy Alloys", zr_hea)
    thermo_zr = hea_zr.compute_thermodynamics()
    assert "Laves_C15" in thermo_zr["Phases"]
    assert thermo_zr["Phases"]["Laves_C15"] > 0.08

    # 3. Cantor CoCrFeMnNi -> should NOT trigger false-positive Laves
    cantor = UnifiedHEADatabase.PRESETS["CoCrFeMnNi (Cantor Alloy)"]
    hea_cantor = HEAEngine("High Entropy Alloys", cantor)
    thermo_cantor = hea_cantor.compute_thermodynamics()
    assert not any("Laves" in k for k in thermo_cantor["Phases"])

    # 4. SAC305 Solder -> Ag3Sn + Cu6Sn5 + Cu3Sn IMCs
    solder = SolderEngine("Solder Alloy", {"Sn": 96.5, "Ag": 3.0, "Cu": 0.5})
    s_thermo = solder.compute_thermodynamics()
    assert "Ag3Sn_IMC" in s_thermo["Phases"]
    assert "Cu6Sn5_IMC" in s_thermo["Phases"]
    assert "Cu3Sn_IMC" in s_thermo["Phases"]


def test_xrd_indexes_laves_and_sigma_peaks():
    nb_hea = UnifiedHEADatabase.PRESETS["CoCrFeNiNb0.5 (C14 Laves Reinforced HEA)"]
    xrd = XRDEngine.calculate(
        nb_hea,
        thermo_metrics={"VEC": 8.2, "DeltaSize_pct": 5.8},
    )
    assert any("Laves" in ph for ph in xrd["Phases"])
    assert any("C14" in pk["HKL"] for pk in xrd["Peaks"])


def test_daemon_exposes_imc_laves_db_and_laves_curves():
    mod_res = CAEDaemon.handle_run_simulation_module({"module": "imc_laves_db"})
    assert "imcs" in mod_res
    assert len(mod_res["imcs"]) >= 20

    nb_hea = UnifiedHEADatabase.PRESETS["CoCrFeNiNb0.5 (C14 Laves Reinforced HEA)"]
    eq_res = CAEDaemon.handle_calculate_equilibrium({
        "database_name": "High Entropy Alloys",
        "composition": nb_hea,
        "basis": "at%",
        "t_start": 400.0,
        "t_stop": 1800.0,
    })
    assert "Laves_C14" in eq_res["phase_curves"]["series"]
    assert max(eq_res["phase_curves"]["series"]["Laves_C14"]) > 0.08
