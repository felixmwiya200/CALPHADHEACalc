"""
Tests for interactive 3D crystallographic structure generation and Wyckoff atomic configuration.
"""

import pytest

from pycalphad_app.core.crystal_structure_engine import CrystalStructureEngine
from pycalphad_app.server.cae_daemon import CAEDaemon


def test_fcc_cantor_alloy_atoms_and_bonds():
    at_comp = {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}
    model = CrystalStructureEngine.build_phase_model(
        phase_name="FCC (A1)",
        phase_fraction=1.0,
        at_comp=at_comp,
        supercell_n=2,
    )
    assert model["archetype"] == "FCC_A1"
    assert model["strukturbericht"] == "A1"
    assert model["pearson_symbol"] == "cF4"
    assert len(model["atoms"]) == 32  # 4 sites/cell * 2x2x2 supercell
    assert len(model["bonds"]) > 0
    assert model["species_counts"]
    # All 5 Cantor elements appear in stoichiometrically balanced proportions
    for sym in ("Co", "Cr", "Fe", "Mn", "Ni"):
        assert model["species_counts"].get(sym, 0) >= 6


def test_l12_and_b2_sublattice_ordering():
    at_comp = {"Ni": 0.65, "Co": 0.10, "Al": 0.15, "Ti": 0.10}
    l12 = CrystalStructureEngine.build_phase_model("Gamma_Prime", 0.35, at_comp, supercell_n=1)
    assert l12["archetype"] == "L12_CU3AU"
    assert len(l12["sublattices"]) == 2
    corner_atoms = [a for a in l12["atoms"] if a["sublattice"] == "SL-1"]
    face_atoms = [a for a in l12["atoms"] if a["sublattice"] == "SL-2"]
    assert corner_atoms and all(a["symbol"] in ("Al", "Ti") for a in corner_atoms)
    assert face_atoms and all(a["symbol"] in ("Ni", "Co") for a in face_atoms)

    b2 = CrystalStructureEngine.build_phase_model("B2 Ordered", 0.40, {"Ni": 0.5, "Al": 0.5}, supercell_n=2)
    assert b2["archetype"] == "B2_CSCL"
    assert len(b2["atoms"]) == 16
    assert any(a["symbol"] == "Al" for a in b2["atoms"])
    assert any(a["symbol"] == "Ni" for a in b2["atoms"])


def test_laves_and_sigma_tcp_cells():
    c14 = CrystalStructureEngine.build_phase_model(
        "Eta_MgZn2",
        0.15,
        {"Al": 0.88, "Zn": 0.08, "Mg": 0.04},
        supercell_n=1,
    )
    assert c14["archetype"] == "LAVES_C14"
    assert c14["pearson_symbol"] == "hP12"
    assert len(c14["atoms"]) == 12
    assert len(c14["unit_cell_box"]["vertices"]) == 8

    sigma = CrystalStructureEngine.build_phase_model(
        "Sigma",
        0.10,
        {"Fe": 0.4, "Cr": 0.4, "Ni": 0.1, "Mo": 0.1},
        supercell_n=1,
    )
    assert sigma["archetype"] == "SIGMA_D8B"
    assert sigma["pearson_symbol"] == "tP30"
    assert len(sigma["atoms"]) == 30
    assert len(sigma["sublattices"]) == 3


def test_cae_daemon_crystal_structures_rpc():
    resp = CAEDaemon.handle_get_crystal_structures({
        "database_name": "Nickel Based Superalloy",
        "composition": {"Ni": 52.5, "Cr": 19.0, "Fe": 18.5, "Nb": 5.1, "Mo": 3.0, "Ti": 0.9, "Al": 0.5},
        "basis": "wt%",
        "temperature": 300.0,
        "supercell_n": 1,
    })
    models = resp["crystal_structures"]
    assert len(models) >= 3
    names = {m["phase_name"] for m in models}
    assert "Gamma_Matrix" in names
    assert "Gamma_Prime" in names
    for m in models:
        assert len(m["atoms"]) > 0
        assert len(m["sublattices"]) >= 1


def test_sigma_auto_surfacing_chi_and_heusler_models():
    """Verifies Sigma models always build cleanly for Sigma-forming HEAs, plus Chi A12 and Heusler L2_1."""
    # Greek symbol and string mapping
    assert CrystalStructureEngine.map_phase_to_archetype("σ") == "SIGMA_D8B"
    assert CrystalStructureEngine.map_phase_to_archetype("Sigma (TCP)") == "SIGMA_D8B"
    assert CrystalStructureEngine.map_phase_to_archetype("Chi_A12") == "CHI_A12"
    assert CrystalStructureEngine.map_phase_to_archetype("Heusler_L21") == "HEUSLER_L21"

    # CoCrFeNiMo0.3 at 300 K even if active_phases only reports FCC matrix should still surface Sigma TCP model
    at_comp = {"Co": 0.2325, "Cr": 0.2325, "Fe": 0.2325, "Ni": 0.2325, "Mo": 0.070}
    models = CrystalStructureEngine.build_alloy_crystal_models(
        at_comp=at_comp,
        active_phases={"FCC": 1.0},
        supercell_n=1,
    )
    sigma_models = [m for m in models if m["archetype"] == "SIGMA_D8B"]
    assert len(sigma_models) == 1
    assert sigma_models[0]["pearson_symbol"] == "tP30"
    assert len(sigma_models[0]["atoms"]) == 30

    # Pure liquid above melting point should not spuriously emit solid-state Sigma
    melt_models = CrystalStructureEngine.build_alloy_crystal_models(
        at_comp=at_comp,
        active_phases={"Liquid": 1.0},
        supercell_n=1,
    )
    assert all(m["archetype"] != "SIGMA_D8B" for m in melt_models)

    # Chi A12 & Heusler L2_1 cells
    chi = CrystalStructureEngine.build_phase_model("Chi_A12", 0.08, {"Fe": 0.55, "Cr": 0.25, "Mo": 0.20}, supercell_n=1)
    assert chi["archetype"] == "CHI_A12"
    assert chi["pearson_symbol"] == "cI58"
    assert len(chi["atoms"]) == 34

    heusler = CrystalStructureEngine.build_phase_model("Heusler_L21", 0.20, {"Ni": 0.50, "Ti": 0.25, "Al": 0.25}, supercell_n=1)
    assert heusler["archetype"] == "HEUSLER_L21"
    assert heusler["strukturbericht"] == "L2_1"
    assert len(heusler["atoms"]) > 16  # 16 core + boundary image atoms
