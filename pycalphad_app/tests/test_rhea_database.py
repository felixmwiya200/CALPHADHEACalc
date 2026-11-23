"""
test_rhea_database.py - Test Suite for Refractory High Entropy Alloy (RHEA) Database and CALPHAD Models.
"""

import os
import pytest
from pycalphad_app.database.rhea_database import RefractoryHEADatabase
from pycalphad_app.server.cae_daemon import CAEDaemon


def test_rhea_benchmarks_catalog():
    """Verify curated RHEA benchmarks list and individual alloy retrieval."""
    bms = RefractoryHEADatabase.list_benchmarks()
    assert len(bms) >= 12, f"Expected at least 12 RHEA benchmarks, got {len(bms)}"

    keys = [b["key"] for b in bms]
    assert "NBMOTAW" in keys
    assert "VNBMOTAW" in keys
    assert "HFNBTATIZR" in keys
    assert "ALCRTIV" in keys
    assert "CRNBTIVZR" in keys

    nbmotaw = RefractoryHEADatabase.get_benchmark("NBMOTAW")
    assert nbmotaw is not None
    assert nbmotaw["formula"] == "NbMoTaW"
    assert nbmotaw["density_exp_g_cm3"] > 13.0
    assert len(nbmotaw["yield_strength_curve"]) >= 5
    assert nbmotaw["doi"] != ""


def test_rhea_temperature_strength_curves():
    """Verify elevated temperature yield strength curves up to 1600 deg C."""
    curves = RefractoryHEADatabase.get_strength_curves(["NBMOTAW", "VNBMOTAW", "HFNBTATIZR"])
    assert "NBMOTAW" in curves
    assert "VNBMOTAW" in curves
    assert "HFNBTATIZR" in curves

    v_curve = curves["VNBMOTAW"]
    temps = v_curve["temperatures_c"]
    strengths = v_curve["yield_strengths_mpa"]
    assert 25.0 in temps
    assert 1600.0 in temps
    # Yield strength at room temperature must be higher than at 1600 deg C
    idx_rt = temps.index(25.0)
    idx_1600 = temps.index(1600.0)
    assert strengths[idx_rt] > strengths[idx_1600]
    assert strengths[idx_rt] == 1246.0


def test_rhea_literature_query():
    """Verify querying the 5,800+ refractory HEA dataset."""
    res = RefractoryHEADatabase.search_literature_rhea(elements=["Nb", "Mo", "Ta", "W"], limit=10)
    assert res["total"] > 0
    assert len(res["alloys"]) <= 10
    first = res["alloys"][0]
    assert "alloy" in first
    assert "paper" in first


def test_rhea_tdb_database_files():
    """Verify existence and phase contents of master refractory TDB files."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tdb1 = os.path.join(repo_root, "Databases", "RHEA_Master_Refractory.tdb")
    tdb2 = os.path.join(repo_root, "App", "databases", "RHEA_Master_Refractory.tdb")

    assert os.path.exists(tdb1), f"Missing {tdb1}"
    assert os.path.exists(tdb2), f"Missing {tdb2}"

    content = open(tdb1, "r", encoding="utf-8").read()
    assert "PHASE LIQUID" in content
    assert "PHASE BCC_A2" in content
    assert "PHASE C14_LAVES" in content
    assert "PHASE C15_LAVES" in content
    assert "PARAMETER L(BCC_A2,CR,TA;0)" in content
    assert "PARAMETER L(BCC_A2,V,TA;0)" in content
    assert "PARAMETER L(BCC_A2,MO,NB;0)" in content


def test_daemon_rhea_rpc_handlers():
    """Verify CAE daemon RPC endpoints for RHEA benchmarks, strength curves, and literature."""
    # 1. get_rhea_benchmarks
    res1 = CAEDaemon.handle_get_rhea_benchmarks({})
    assert "benchmarks" in res1
    assert len(res1["benchmarks"]) >= 12

    res1_single = CAEDaemon.handle_get_rhea_benchmarks({"key": "HFNBTATIZR"})
    assert res1_single.get("formula") == "HfNbTaTiZr"
    assert res1_single.get("density_exp_g_cm3") == 9.94

    # 2. get_rhea_strength_curves
    res2 = CAEDaemon.handle_get_rhea_strength_curves({"keys": ["NBMOTAW", "VNBMOTAW"]})
    assert "NBMOTAW" in res2
    assert "VNBMOTAW" in res2

    # 3. query_rhea_literature
    res3 = CAEDaemon.handle_query_rhea_literature({"elements": ["Hf", "Nb", "Ta", "Ti", "Zr"], "limit": 5})
    assert res3.get("total", 0) > 0
    assert len(res3.get("alloys", [])) > 0
