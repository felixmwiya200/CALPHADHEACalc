"""
Author: Felix Mwiya
Module: pycalphad_app.tests.test_application_scorer
Description: Unit verification suite for the multi-criteria industrial application sector scoring engine.
"""

import pytest
from pycalphad_app.core.application_scorer import ApplicationDatabase, ApplicationScorer


def test_application_database_completeness():
    apps = ApplicationDatabase.get_all_applications()
    assert len(apps) == 24, f"Expected 24 industrial applications, found {len(apps)}"

    app_ids = set()
    for app in apps:
        assert "id" in app and app["id"]
        assert app["id"] not in app_ids, f"Duplicate application id: {app['id']}"
        app_ids.add(app["id"])

        assert "name" in app and len(app["name"]) > 5
        assert "sector" in app and len(app["sector"]) > 3
        assert "desc" in app and len(app["desc"]) > 10
        assert "benchmark" in app and len(app["benchmark"]) > 3
        assert "git_ref" in app and len(app["git_ref"]) > 3
        assert "weights" in app and len(app["weights"]) > 0


def test_cantor_alloy_scoring():
    elements = ["Co", "Cr", "Fe", "Mn", "Ni"]
    at_fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
    thermo = {
        "Phase": "FCC",
        "T_Solidus": 1553.0,
        "density": 8.05
    }
    mech = {
        "YieldStrength_MPa": 410.0,
        "UTS_MPa": 750.0,
        "VickersHardness_HV": 210.0,
        "FractureToughness_MPa_m05": 140.0,
        "Elongation_pct": 50.0,
        "YoungsModulus_GPa": 210.0
    }
    ox = {
        "Regime": "Chromia Protective Scale"
    }

    scores = ApplicationScorer.score_alloy(elements, at_fractions, thermo, mech, ox)
    assert len(scores) == 24
    assert scores[0]["rank"] == 1
    assert scores[-1]["rank"] == 24

    # Cantor alloy is an optimal candidate for cryogenic service due to high ductility and toughness
    cryo_matches = [s for s in scores if "CRYO" in s["id"]]
    assert len(cryo_matches) >= 2
    for cm in cryo_matches:
        assert cm["score"] >= 70.0, f"Expected Cantor alloy to score highly in cryogenic sector, got {cm['score']}"

    # Biomedical should be vetoed because of Ni (toxic/allergenic)
    biomed = next(s for s in scores if s["id"] == "BIOMED_ORTHO_IMPLANT")
    assert "Vetoed" in biomed["tier"]
    assert "Ni" in biomed["bottleneck"]

    # Quantum cavity should be vetoed because of ferromagnetic elements (Fe, Co, Ni)
    quantum = next(s for s in scores if s["id"] == "QUANTUM_SUPERCONDUCTING_CAVITY")
    assert "Vetoed" in quantum["tier"]
    assert "Prohibited element present" in quantum["bottleneck"]


def test_refractory_rhea_scoring():
    # HfNbTaTiZr Refractory High-Entropy Alloy
    elements = ["Hf", "Nb", "Ta", "Ti", "Zr"]
    at_fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
    thermo = {
        "Phase": "BCC",
        "T_Solidus": 2350.0,
        "density": 9.9
    }
    mech = {
        "YieldStrength_MPa": 1150.0,
        "UTS_MPa": 1300.0,
        "VickersHardness_HV": 380.0,
        "FractureToughness_MPa_m05": 55.0,
        "Elongation_pct": 12.0,
        "YoungsModulus_GPa": 140.0
    }
    ox = {
        "Regime": "Mixed Refractory Oxide (HfO2/ZrO2)"
    }

    scores = ApplicationScorer.score_alloy(elements, at_fractions, thermo, mech, ox)
    assert len(scores) == 24

    # High-temperature refractory element should score well due to Ts > 2200 K
    uht = next(s for s in scores if s["id"] == "REFRACTORY_FURNACE")
    assert uht["score"] >= 70.0
    assert "Vetoed" not in uht["tier"]

    # Hypersonic leading edge should score well due to ultra-refractory elements
    hypersonic = next(s for s in scores if s["id"] == "AERO_HYPERSONIC_LEADING_EDGE")
    assert hypersonic["score"] >= 70.0
