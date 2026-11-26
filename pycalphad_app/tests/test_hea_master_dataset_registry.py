"""
Tests for HEA Master Dataset Registry & Literature Benchmark Manager
=====================================================================
Validates indexing, querying, mechanical property extraction, and
high-temperature yield strength curves across all extracted git HEA datasets.

Author: Felix Mwiya | Materials CAE & Computational Metallurgy
"""

import pytest
from pycalphad_app.database.hea_master_dataset_registry import (
    HeaMasterDatasetRegistry,
    parse_formula_elements,
)


def test_parse_formula_elements():
    """Verify chemical formula decomposition into constituent elements."""
    elems = parse_formula_elements("Al0.3CoCrFeNi")
    assert elems == {"Al", "Co", "Cr", "Fe", "Ni"}

    elems_rhea = parse_formula_elements("Ti65Zr18Nb16Mo1")
    assert elems_rhea == {"Ti", "Zr", "Nb", "Mo"}

    elems_senkov = parse_formula_elements("NbMoTaW")
    assert elems_senkov == {"Nb", "Mo", "Ta", "W"}


def test_hea_master_dataset_statistics():
    """Verify aggregated metrics across the 25,800+ extracted HEA records."""
    stats = HeaMasterDatasetRegistry.get_statistics()
    assert stats["total_aggregate_records"] >= 25000
    assert stats["total_mpea_experimental_records"] == 1545
    assert stats["total_phase_stability_records"] == 11252
    assert stats["total_synthesis_process_records"] >= 12000
    assert stats["alloys_with_yield_strength"] >= 1300
    assert stats["alloys_with_hardness"] >= 800
    assert stats["alloys_with_uts"] >= 500
    assert stats["element_coverage_count"] >= 50


def test_citrine_mpea_mechanical_properties():
    """Verify extraction of experimental yield strength, UTS, and hardness from Citrine MPEA."""
    records = HeaMasterDatasetRegistry.search_alloys("AlCoCrFeNi", property_filter="yield_strength", max_results=10)
    assert len(records) > 0

    found_with_ys = False
    for r in records:
        if r.get("yield_strength_mpa") is not None:
            found_with_ys = True
            assert r["yield_strength_mpa"] > 500.0  # AlCoCrFeNi alloys exceed 500 MPa
            assert "Al" in r["elements"] and "Ni" in r["elements"]
    assert found_with_ys


def test_peivaste_phase_stability_records():
    """Verify phase structure (BCC/FCC/HCP/IM) and physical descriptors from Peivaste dataset."""
    phase_records = HeaMasterDatasetRegistry.get_phase_stability_records()
    assert len(phase_records) == 11252

    # Check Cantor HEA or sample multi-element record
    first_with_vec = [r for r in phase_records if r.get("vec") is not None][0]
    assert first_with_vec.get("phase_structure") is not None
    assert first_with_vec.get("vec") is not None
    assert first_with_vec.get("mixing_entropy_j_mol_k") is not None


def test_high_temperature_yield_curve():
    """Verify elevated temperature yield strength curve extraction (25 °C up to 1000 °C)."""
    curve = HeaMasterDatasetRegistry.get_temperature_yield_curve("Al0.25NbTaTiZr")
    assert curve["count"] >= 2

    pts = curve["data_points"]
    temps = [p["temperature_c"] for p in pts]
    assert 25.0 in temps
    assert 1000.0 in temps

    # Check yield strength at 25 °C exceeds high-temperature yield strength
    ys_room = [p["yield_strength_mpa"] for p in pts if p["temperature_c"] == 25.0][0]
    ys_1000 = [p["yield_strength_mpa"] for p in pts if p["temperature_c"] == 1000.0][0]
    assert ys_room > ys_1000
