"""
Tests for ESPEI Dataset Registry & Benchmark Manager
=====================================================
Validates discovery, indexing, BibTeX resolution, and ZPF / thermochemical
data point extraction from the PhasesResearchLab/ESPEI-datasets repository.

Author: Felix Mwiya | Materials CAE & Computational Metallurgy
"""

import pytest
from pycalphad_app.database.espei_dataset_registry import (
    EspeiDatasetRegistry,
    parse_bibtex_file,
)


def test_espei_dataset_discovery_and_statistics():
    """Verify registry discovers all 215 datasets across 34 elemental systems."""
    stats = EspeiDatasetRegistry.get_statistics()
    assert stats["total_datasets"] == 215
    assert stats["total_systems"] == 34
    assert stats["binary_systems_count"] == 21
    assert stats["ternary_systems_count"] == 13
    assert stats["zpf_dataset_count"] >= 90
    assert stats["thermochemical_dataset_count"] >= 100
    assert stats["total_references"] >= 70


def test_bibtex_parser():
    """Verify BibTeX parser resolves literature citations from references.bib."""
    refs = EspeiDatasetRegistry.get_references()
    assert len(refs) >= 70

    # Test sample authoritative entry
    assert "King1964" in refs
    king = refs["King1964"]
    assert "King" in king.get("author", "")
    assert king.get("year") == "1964"
    assert "Acta Metallurgica" in king.get("journal", "")
    assert "short_citation" in king


def test_system_listing_and_properties():
    """Verify listing and component decomposition for binary and ternary systems."""
    systems = EspeiDatasetRegistry.list_systems()
    sys_dict = {s["system"]: s for s in systems}

    # Binary system check
    assert "Al-Ni" in sys_dict
    al_ni = sys_dict["Al-Ni"]
    assert al_ni["tier"] == "binary"
    assert set(al_ni["elements"]) == {"Al", "Ni"}
    assert "ZPF" in al_ni["outputs"]

    # Ternary system check
    assert "Al-Co-Cr" in sys_dict
    al_co_cr = sys_dict["Al-Co-Cr"]
    assert al_co_cr["tier"] == "ternary"
    assert set(al_co_cr["elements"]) == {"Al", "Co", "Cr"}


def test_zpf_phase_boundary_extraction():
    """Verify Zero Phase Fraction tie-lines extraction for Al-Ni and Cu-Mg."""
    al_ni_zpf = EspeiDatasetRegistry.get_zpf_phase_boundaries("Al-Ni")
    assert len(al_ni_zpf) > 0

    for pt in al_ni_zpf:
        assert pt["system"] == "Al-Ni"
        assert pt["temperature_k"] > 300.0
        assert 0.0 <= pt["composition"] <= 1.0
        assert pt["element"] in ["Al", "Ni"]
        assert len(pt["phase"]) > 0
        assert len(pt["reference"]) > 0

    # Check phase variety in Al-Ni
    phases = {pt["phase"] for pt in al_ni_zpf}
    assert "LIQUID" in phases or "FCC_L12" in phases or "BCC_B2" in phases


def test_thermochemical_points_extraction():
    """Verify thermochemical formation and mixing enthalpy extraction."""
    al_co_thermo = EspeiDatasetRegistry.get_thermochemical_points("Al-Co")
    assert len(al_co_thermo) > 0

    props = {pt["property"] for pt in al_co_thermo}
    assert "HM_MIX" in props or "HM_FORM" in props

    for pt in al_co_thermo:
        assert pt["system"] == "Al-Co"
        if "H" in pt["property"]:
            assert pt["unit"] == "J/mol"
        elif "S" in pt["property"] or "CP" in pt["property"]:
            assert pt["unit"] == "J/(mol*K)"
        assert isinstance(pt["value_si"], float)
