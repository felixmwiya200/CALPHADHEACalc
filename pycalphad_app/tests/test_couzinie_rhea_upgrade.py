# -*- coding: utf-8 -*-
"""
test_couzinie_rhea_upgrade.py - Verification suite for High-Entropy Alloys and RHEA upgrade
Adheres to Couzinié, Senkov, Miracle, Dirras (Data in Brief 21 (2018) 1834-1841,
DOI: 10.1016/j.dib.2018.10.071) and Senkov et al. (JMR 2018, DOI: 10.1557/jmr.2018.153).
"""

import pytest
from pycalphad_app.database.tdb_manager import TDBManager
from pycalphad_app.database.unified_hea_database import UnifiedHEADatabase
from pycalphad_app.database.rhea_database import RefractoryHEADatabase
from pycalphad_app.database.hea_literature_db import HEALiteratureDatabase
from pycalphad_app.core.hea_engine import HEAEngine


def test_mounted_tdbs_count_and_refractory_inclusion():
    """Confirms that High Entropy Alloys mounts at least 10 TDBs including the full refractory suite."""
    tdbs = TDBManager.get_family_tdbs("High Entropy Alloys")
    assert len(tdbs) >= 10, f"Expected at least 10 mounted TDBs, got {len(tdbs)}: {tdbs}"
    assert "RHEA_Master_Refractory.tdb" in tdbs
    assert "Ti_ElasticPhases.tdb" in tdbs
    assert "CrTiV_TitaniumGhosh.tdb" in tdbs
    assert "FeCoCrNbTi_HEA.tdb" in tdbs
    assert "IMC_Laves_Master.tdb" in tdbs


def test_couzinie_presets_and_benchmarks_unified_database():
    """Confirms Couzinié 2018 presets and benchmarks are registered in UnifiedHEADatabase."""
    presets = UnifiedHEADatabase.PRESETS
    assert "MoNbTaVW (Senkov & Miracle Equiatomic BCC)" in presets
    assert "AlMo0.5NbTa0.5TiZr (Senkov Superalloy RHEA - Ref [5])" in presets
    assert "Ti30Zr25Hf15Nb20Ta10 (Cryogenic-Ductile RHEA - 4.2 K to 1473 K)" in presets
    assert "CrMoNbTaVW (Senkov 6-Element Extreme RHEA)" in presets
    assert "VNbMoTa (Senkov Quaternary Heavy RHEA)" in presets
    assert "HfNbTiZr (Equiatomic Quaternary Ductile RHEA)" in presets

    benchmarks = UnifiedHEADatabase.BENCHMARKS
    assert "COUZINIE_SENKOV_RHEA" in benchmarks
    assert benchmarks["COUZINIE_SENKOV_RHEA"]["citations"]["doi_general"] == "10.1016/j.dib.2018.10.071"
    assert "ALMO05NBTA05TIZR_RHEA" in benchmarks
    assert "TI30ZR25HF15NB20TA10_RHEA" in benchmarks
    assert "SENKOV_RHEA_REVIEW" in benchmarks


def test_rhea_database_couzinie_benchmarks():
    """Confirms RefractoryHEADatabase includes Couzinié compilation and cryo-ductile benchmarks."""
    bms = RefractoryHEADatabase.BENCHMARKS
    assert "COUZINIE_SENKOV_COMPILATION" in bms
    assert bms["COUZINIE_SENKOV_COMPILATION"].doi == "10.1016/j.dib.2018.10.071"
    assert "TI30ZR25HF15NB20TA10" in bms
    assert bms["TI30ZR25HF15NB20TA10"].doi == "10.1016/j.msea.2017.12.021"

    # Verify temperature curve extends to 1600 C (1873 K)
    curve = bms["COUZINIE_SENKOV_COMPILATION"].yield_strength_curve
    max_temp = max(pt.temperature_c for pt in curve)
    assert max_temp >= 1600.0


def test_hea_engine_vnbmotaw_elevated_temperature_curve():
    """Verifies HEAEngine temperature-dependent flow stress for VNbMoTaW up to 1873 K."""
    comp = {"V": 0.0738, "Nb": 0.1346, "Mo": 0.1390, "Ta": 0.2621, "W": 0.3905}
    engine = HEAEngine("High Entropy Alloys", comp, grain_size_um=25.0)

    stats = engine._compute_elemental_statistics()
    assert stats["is_vnbmotaw"] is True
    assert stats["is_refractory"] is True

    th = engine.compute_thermodynamics()
    tr = engine.compute_phase_transformations()
    mc = engine.compute_mechanical_properties(th, tr)

    # Room temperature yield strength ~ 1246 MPa
    assert 1150.0 <= mc["YieldStrength_RT_MPa"] <= 1350.0

    # 1000 C (1273 K) yield strength retention > 750 MPa (Senkov 2011 / Couzinié 2018: 842 MPa)
    assert mc["YieldStrength_1000C_MPa"] >= 750.0

    # Rule of Mixtures density and specific strength
    assert 12.0 <= mc["RuleOfMixturesDensity_g_cm3"] <= 13.5
    assert mc["SpecificYieldStrength_MPa_cm3_g"] > 80.0


def test_hea_engine_almo_rhes_high_specific_strength():
    """Verifies Senkov AlMo0.5NbTa0.5TiZr RHES high specific yield strength and coherent A2/B2."""
    comp = {"Al": 0.069, "Mo": 0.123, "Nb": 0.237, "Ta": 0.232, "Ti": 0.137, "Zr": 0.233}
    engine = HEAEngine("High Entropy Alloys", comp, grain_size_um=25.0)

    stats = engine._compute_elemental_statistics()
    assert stats["is_almo_rhes"] is True

    th = engine.compute_thermodynamics()
    tr = engine.compute_phase_transformations()
    mc = engine.compute_mechanical_properties(th, tr)

    # Low density ~ 7.1-7.4 g/cm3 with high yield strength ~ 1250 MPa -> specific strength > 150 MPa*cm3/g
    assert 7.0 <= mc["RuleOfMixturesDensity_g_cm3"] <= 7.8
    assert mc["SpecificYieldStrength_MPa_cm3_g"] >= 150.0


def test_hea_engine_ti30zr25_cryo_ductility():
    """Verifies Ti30Zr25Hf15Nb20Ta10 cryogenic-to-high-temperature flow properties."""
    comp = {"Ti": 0.1348, "Zr": 0.2141, "Hf": 0.2513, "Nb": 0.1744, "Ta": 0.1854}
    engine = HEAEngine("High Entropy Alloys", comp, grain_size_um=25.0)

    stats = engine._compute_elemental_statistics()
    assert stats["is_ti30zr25_ductile"] is True

    th = engine.compute_thermodynamics()
    tr = engine.compute_phase_transformations()
    mc = engine.compute_mechanical_properties(th, tr)

    assert mc["Elongation_pct"] >= 30.0
    assert 750.0 <= mc["YieldStrength_RT_MPa"] <= 950.0


def test_sqlite_hea_literature_couzinie_indexing():
    """Verifies Couzinié et al. (2018) records are indexed in SQLite with active DOI."""
    db = HEALiteratureDatabase.get_instance()
    results = db.search_alloys(query="10.1016/j.dib.2018.10.071", limit=20)
    items = results.get("items", [])
    assert len(items) > 0
    assert any(r.get("doi") == "10.1016/j.dib.2018.10.071" for r in items)
