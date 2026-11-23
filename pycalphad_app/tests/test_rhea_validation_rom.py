# test_rhea_validation_rom.py - Verification for RHEA benchmark error reduction and Rule of Mixtures columns

import pytest
from pycalphad_app.database.benchmark_database import BenchmarkDatabase
from pycalphad_app.core.rom_engine import RuleOfMixturesEngine


def test_rhea_archetype_identification_never_defaults_to_cantor():
    """Verify that refractory alloys always match RHEA archetypes, never falling back to Cantor alloy."""
    # 1. Equiatomic TiZrNbTa
    comp_tizrnbta = {"Ti": 25.0, "Zr": 25.0, "Nb": 25.0, "Ta": 25.0}
    key1 = BenchmarkDatabase.identify_alloy_key(comp_tizrnbta)
    assert key1 == "TIZRNBTA_RHEA"

    # 2. CrNbTiVZr
    comp_crnbtivzr = {"Cr": 20.0, "Nb": 20.0, "Ti": 20.0, "V": 20.0, "Zr": 20.0}
    key2 = BenchmarkDatabase.identify_alloy_key(comp_crnbtivzr)
    assert key2 == "CRNBTIVZR_RHEA"

    # 3. AlMo0.5NbTa0.5TiZr
    comp_almo = {"Al": 20.0, "Mo": 10.0, "Nb": 20.0, "Ta": 10.0, "Ti": 20.0, "Zr": 20.0}
    key3 = BenchmarkDatabase.identify_alloy_key(comp_almo)
    assert key3 == "ALMO05NBTA05TIZR_RHEA"

    # 4. Nb40Ti30Al15Hf10V5
    comp_nb40 = {"Nb": 40.0, "Ti": 30.0, "Al": 15.0, "Hf": 10.0, "V": 5.0}
    key4 = BenchmarkDatabase.identify_alloy_key(comp_nb40)
    assert key4 == "NB40TI30AL15HF10V5_RHEA"

    # 5. Generic high-refractory composition (e.g. Nb-Mo-W with minor additives)
    comp_custom_refr = {"Nb": 35.0, "Mo": 35.0, "W": 20.0, "Ti": 10.0}
    key5 = BenchmarkDatabase.identify_alloy_key(comp_custom_refr, db_name="High Entropy Alloys (Refractory RHEA)")
    assert "_RHEA" in key5
    assert key5 != "CANTOR_COCRFEMNNI"


def test_rhea_yield_strength_percentage_error_is_accurate():
    """Verify that a calculated RHEA yield strength of ~1250 MPa has low percentage error (< 15%), not 525%."""
    comp_almo = {"Al": 20.0, "Mo": 10.0, "Nb": 20.0, "Ta": 10.0, "Ti": 20.0, "Zr": 20.0}
    mock_calc = {
        "Density_g_cm3": 7.42,
        "Solidus_K": 1995.0,
        "Liquidus_K": 2125.0,
        "YieldStrength_RT_MPa": 1282.5,
        "UTS_RT_MPa": 1410.0,
        "Elongation_pct": 9.5,
        "VickersHardness_HV": 490.0,
        "YoungsModulus_GPa": 138.0
    }

    res = BenchmarkDatabase.compare_metrics(comp_almo, mock_calc)
    assert res["alloy_key"] == "ALMO05NBTA05TIZR_RHEA"

    # Find yield strength row
    sy_row = next(r for r in res["table"] if "Yield Strength" in r["Property"])
    assert sy_row["Experimental"] == 1250.0  # Authentic Couzinié/Senkov benchmark
    assert sy_row["Calculated"] == 1282.5
    # Error must be ~2.6%, NOT 525%!
    assert sy_row["ErrorPercent"] < 5.0


def test_validation_table_contains_rule_of_mixture_column():
    """Verify that RomCalculated, RomDeviation, and RomErrorPercent are populated across all property rows."""
    comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    mock_calc = {
        "Density_g_cm3": 8.02,
        "Solidus_K": 1560.0,
        "Liquidus_K": 1615.0,
        "YieldStrength_RT_MPa": 208.0,
        "UTS_RT_MPa": 575.0,
        "VickersHardness_HV": 144.0,
        "YoungsModulus_GPa": 204.0,
        "ThermalConductivity_W_mK": 13.0
    }

    res = BenchmarkDatabase.compare_metrics(comp, mock_calc)
    assert len(res["table"]) >= 6

    for row in res["table"]:
        # Verify Rule of Mixtures calculated value is present
        assert "RomCalculated" in row
        assert row["RomCalculated"] is not None
        assert isinstance(row["RomCalculated"], (int, float))
        assert row["RomCalculated"] > 0
        assert "RomDeviation" in row
        assert "RomErrorPercent" in row
