# -*- coding: utf-8 -*-
"""
test_binary_diagram_engine.py - Formal Verification of CALPHAD Binary Phase Diagrams
Tests all 8 assessed literature benchmark systems, arbitrary pair thermodynamic solvers,
and analytical lever-rule tie-line evaluations.
"""

import pytest
from pycalphad_app.core.binary_diagram_engine import BinaryDiagramEngine


def test_get_available_systems():
    systems = BinaryDiagramEngine.get_available_systems()
    assert len(systems) >= 8
    assert any("Ni-Al" in s for s in systems)
    assert any("Fe-Cr" in s for s in systems)
    assert any("Ti-Al" in s for s in systems)
    assert any("Cu-Ni" in s for s in systems)
    assert any("Fe-C" in s for s in systems)
    assert any("Co-Cr" in s for s in systems)
    assert any("Al-Cu" in s for s in systems)
    assert any("NaF-AlF3" in s for s in systems)
    assert any("Mn-Ni" in s for s in systems)
    assert any("Fe-Ni" in s for s in systems)

    # Test dynamic pair filtering: strictly returns pairs formed by elements in the composition
    pair_systems = BinaryDiagramEngine.get_available_systems(["Fe", "Ni", "Cr"])
    assert any("Fe-Ni" in s for s in pair_systems)
    assert any("Ni-Cr" in s or "Cr-Ni" in s for s in pair_systems)
    assert any("Fe-Cr" in s for s in pair_systems)
    # Excludes systems containing elements outside the active composition
    assert not any("Cu-Ni" in s for s in pair_systems)
    assert not any("Fe-C " in s or "Iron-Cementite" in s for s in pair_systems)
    assert not any("NaF-AlF3" in s for s in pair_systems)
    assert not any("Ti-Al" in s for s in pair_systems)
    assert len(pair_systems) == 3


@pytest.mark.parametrize("system_key", [
    "Ni-Al",
    "Fe-Cr",
    "Ti-Al",
    "Cu-Ni",
    "Fe-C",
    "Co-Cr",
    "Al-Cu",
    "Al-Co",
    "NaF-AlF3",
    "Mn-Ni",
    "Fe-Ni",
    "Cr-Ni",
    "Co-Ni",
    "Co-Fe",
    "Fe-Mn",
    "Cr-Mn",
    "Co-Mn",
    "Ti-V",
    "Al-Mg",
    "Al-Si",
    "Ni-Ti",
    "Cu-Zn",
    "Cu-Sn",
    "Al-Zn",
    "Al-Fe",
    "Al-Mn",
    "Mg-Zn",
    "Fe-Si",
    "Fe-Mo",
    "Fe-V",
    "Cr-Mo",
    "Sn-Ag",
    "Sn-Pb",
    "Sn-Bi",
    "Ti-Mo",
    "Ti-Zr",
    "Zr-Nb",
    "Zr-Sn",
    "Co-W",
    "Mo-W",
    "Nb-Mo",
])
def test_compute_binary_diagram_all_systems(system_key):
    diag = BinaryDiagramEngine.compute_binary_diagram(system_key, temp_unit="C", n_points=80)
    assert diag["system"] == system_key
    assert "(" not in diag["system"] and ")" not in diag["system"]
    assert "system" in diag
    assert "curves" in diag
    assert len(diag["curves"]) > 0
    assert "invariants" in diag
    assert "regions" in diag
    assert diag["x_min"] >= 0.0
    assert diag["x_max"] <= 100.0

    # Ensure every curve has equal length valid coordinates
    for c in diag["curves"]:
        assert len(c["xs"]) == len(c["ys"])
        assert len(c["xs"]) > 0
        assert not any(val is None for val in c["xs"])
        assert not any(val is None for val in c["ys"])


def test_ni_al_invariants_and_regions():
    diag = BinaryDiagramEngine.compute_binary_diagram("Ni-Al (Superalloy Ni3Al / B2)", temp_unit="C")
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Peritectic" in inv_types
    assert "Congruent" in inv_types

    # Verified invariant temperatures
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1638.0 in inv_temps
    assert 1395.0 in inv_temps
    assert 1385.0 in inv_temps
    assert 1133.0 in inv_temps
    assert 854.0 in inv_temps
    assert 640.0 in inv_temps

    region_labels = [r["label"] for r in diag["regions"]]
    assert any("Liquid" in lbl for lbl in region_labels)
    assert any("Ni₃Al" in lbl or "γ'" in lbl for lbl in region_labels)
    assert any("NiAl" in lbl or "β" in lbl for lbl in region_labels)


def test_fe_cr_invariants_and_features():
    diag = BinaryDiagramEngine.compute_binary_diagram("Fe-Cr (Sigma Phase Embrittlement)", temp_unit="C")
    inv_eqs = [inv["equation"] for inv in diag["invariants"]]
    assert any("1305" in eq or "Azeotropic" in eq for eq in inv_eqs)
    assert any("830" in str(inv["temp"]) for inv in diag["invariants"])
    assert any("575" in str(inv["temp"]) for inv in diag["invariants"])

    curve_names = [c["name"] for c in diag["curves"]]
    assert any("γ-Loop" in name for name in curve_names)
    assert any("σ-Phase" in name for name in curve_names)
    assert any("Miscibility Gap" in name for name in curve_names)


def test_ti_al_invariants():
    diag = BinaryDiagramEngine.compute_binary_diagram("Ti-Al (Titanium Aluminides)", temp_unit="C")
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1490.0 in inv_temps
    assert 1445.0 in inv_temps
    assert 1400.0 in inv_temps
    assert 1215.0 in inv_temps
    assert 1120.0 in inv_temps


def test_fe_c_invariants():
    diag = BinaryDiagramEngine.compute_binary_diagram("Fe-C (Iron-Cementite Steel System)", temp_unit="C")
    assert diag["x_max"] == 6.67
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1495.0 in inv_temps
    assert 1147.0 in inv_temps
    assert 727.0 in inv_temps


def test_al_cu_invariants():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Cu (Precipitation Hardening Duralumin)", temp_unit="C")
    assert diag["x_max"] == 100.0
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 548.2 in inv_temps
    assert 591.0 in inv_temps
    assert 1025.0 in inv_temps


def test_co_cr_invariants():
    diag = BinaryDiagramEngine.compute_binary_diagram("Co-Cr (Stellite Wear Matrix)", temp_unit="C")
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1470.0 in inv_temps
    assert 1395.0 in inv_temps
    assert 930.0 in inv_temps


def test_cu_ni_invariants():
    diag = BinaryDiagramEngine.compute_binary_diagram("Cu-Ni (Isomorphous Solid Solution Lens)", temp_unit="C")
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 354.5 in inv_temps


def test_naf_alf3_invariants_and_exp():
    diag = BinaryDiagramEngine.compute_binary_diagram("NaF-AlF3 (Cryolite Industrial Electrolyte)", temp_unit="C")
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1010.0 in inv_temps
    assert 888.0 in inv_temps
    assert 734.0 in inv_temps
    assert 695.0 in inv_temps
    assert len(diag["experimental_points"]) > 0


def test_evaluate_lever_rule():
    # 1. High-temperature single phase liquid
    liq = BinaryDiagramEngine.evaluate_lever_rule("Ni-Al (Superalloy Ni3Al / B2)", 0.50, 1750.0, "C")
    assert "Liquid" in liq["state"]
    assert pytest.approx(liq["phase1_fraction"], 0.01) == 1.0

    # 2. Intermediate temperature two-phase mushy zone
    mushy = BinaryDiagramEngine.evaluate_lever_rule("Ni-Al (Superalloy Ni3Al / B2)", 0.35, 1450.0, "C")
    assert "phase1_fraction" in mushy
    assert "phase2_fraction" in mushy
    assert pytest.approx(mushy["phase1_fraction"] + mushy["phase2_fraction"], 0.01) == 1.0


def test_mn_ni_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Mn-Ni (CALPHAD Assessed Benchmark)", temp_unit="C")
    assert diag["element_a"] == "Mn"
    assert diag["element_b"] == "Ni"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Congruent Minimum" in inv_types
    assert "Order-Disorder Summit" in inv_types

    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1018.0 in inv_temps
    assert 910.0 in inv_temps
    assert 510.0 in inv_temps

    liq = next(c for c in diag["curves"] if c["name"] == "Liquidus")
    assert all(t > 0.0 for t in liq["ys"])
    assert min(liq["ys"]) >= 1017.0


def test_fe_ni_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Fe-Ni (CALPHAD Assessed Benchmark)", temp_unit="C")
    assert diag["element_a"] == "Fe"
    assert diag["element_b"] == "Ni"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Peritectic" in inv_types
    assert "Order-Disorder Summit" in inv_types


def test_al_co_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Co (B2-AlCo & Aluminides)", temp_unit="C")
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Co"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Peritectic" in inv_types
    assert "Congruent Melting" in inv_types

    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 657.0 in inv_temps
    assert 970.0 in inv_temps
    assert 1093.0 in inv_temps
    assert 1135.0 in inv_temps
    assert 1180.0 in inv_temps
    assert 1640.0 in inv_temps
    assert 1400.0 in inv_temps

    liq = next(c for c in diag["curves"] if c["name"] == "Liquidus")
    assert min(liq["ys"]) <= 657.01
    assert max(liq["ys"]) >= 1639.9


def test_cr_mn_benchmark():
    # Test Kelvin units
    diag_k = BinaryDiagramEngine.compute_binary_diagram("Cr-Mn (Thermo-Calc Mn79Cr21 & Mn2Cr Benchmark)", temp_unit="K")
    assert diag_k["element_a"] == "Mn"
    assert diag_k["element_b"] == "Cr"
    assert diag_k["x_min"] == 0.10
    assert diag_k["x_max"] == 0.40
    assert round(diag_k["y_min"]) == 800
    assert round(diag_k["y_max"]) == 1800

    inv_temps_k = [round(inv["temp"]) for inv in diag_k["invariants"]]
    assert 1581 in inv_temps_k
    assert 1559 in inv_temps_k
    assert 1271 in inv_temps_k
    assert 1073 in inv_temps_k
    assert 1000 in inv_temps_k

    # Test Celsius units
    diag_c = BinaryDiagramEngine.compute_binary_diagram("Cr-Mn (CALPHAD Pair from Alloy)", temp_unit="C")
    inv_c_vals = [inv["temp"] for inv in diag_c["invariants"]]
    for target in [1307.85, 1285.85, 997.85, 799.85, 726.85]:
        assert any(abs(t - target) < 0.05 for t in inv_c_vals), f"Target {target} not found in {inv_c_vals}"

    # Check pair mapping in composition
    systems = BinaryDiagramEngine.get_available_systems(["Co", "Cr", "Fe", "Mn", "Ni"])
    assert "Cr-Mn" in systems
    # Ensure all names contain only elemental symbols (no parentheses or descriptors)
    for s in systems:
        assert "(" not in s and ")" not in s, f"System name '{s}' has descriptor parentheses"

    # Check line compounds exist
    compound_curves = [c["name"] for c in diag_k["curves"]]
    assert "Mn79Cr21 Line Compound" in compound_curves
    assert "Mn2Cr Line Compound" in compound_curves


def test_arbitrary_binary_strictly_positive():
    for pair in [("Mn", "Ni"), ("Co", "Fe"), ("Cr", "Mn"), ("Co", "Cr"), ("Ti", "Ni")]:
        diag = BinaryDiagramEngine._compute_arbitrary_binary(pair[0], pair[1], is_k=True, n_pts=50)
        for c in diag["curves"]:
            for y in c["ys"]:
                assert y > 0.0, f"Temperature {y} <= 0 for pair {pair} in curve {c['name']}"


def test_co_mn_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Co-Mn (Cobalt-Manganese Benchmark)", temp_unit="C")
    assert diag["element_a"] == "Co"
    assert diag["element_b"] == "Mn"
    assert diag["y_min"] == 0.0
    assert diag["y_max"] == 1800.0

    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Peritectic" in inv_types
    assert "Allotropic Transition" in inv_types
    assert "Peritectoid / Ordering Invariant" in inv_types
    assert "Solid-State Invariant" in inv_types

    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1161.0 in inv_temps
    assert 1185.0 in inv_temps
    assert 422.0 in inv_temps
    assert 312.2 in inv_temps
    assert 139.5 in inv_temps
    assert 727.0 in inv_temps

    curve_names = [c["name"] for c in diag["curves"]]
    assert "Liquidus" in curve_names
    assert "Solidus γ-(Co,Mn)" in curve_names
    assert "Solidus β-Mn" in curve_names
    assert "fcc Ordering Boundary (Left)" in curve_names
    assert "fcc Ordering Boundary (Right)" in curve_names
    assert "fcc Solvus Corridor" in curve_names
    assert "β-Mn Solvus Corridor" in curve_names
    assert "Co ε-HCP Solvus" in curve_names
    assert "Mn-rich β-Mn ⇌ α-Mn Boundary" in curve_names


def test_ti_v_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Ti-V (Aerospace Beta-Isomorphous System)", temp_unit="C")
    assert diag["element_a"] == "Ti"
    assert diag["element_b"] == "V"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Congruent Minimum" in inv_types
    assert "Allotropic Transition" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 1620.0 in inv_temps
    assert 882.0 in inv_temps


def test_al_mg_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Mg (Light Aerospace & Automotive System)", temp_unit="C")
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Mg"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Peritectic" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 450.0 in inv_temps
    assert 458.0 in inv_temps
    assert 437.0 in inv_temps


def test_al_si_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Si (Foundry Eutectic Casting System)", temp_unit="C")
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Si"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 577.0 in inv_temps
    eut_inv = next(i for i in diag["invariants"] if i["type"] == "Eutectic")
    assert eut_inv["x_reaction"] == 0.122


def test_ni_ti_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Ni-Ti (Nitinol Shape Memory System)", temp_unit="C")
    assert diag["element_a"] == "Ti"
    assert diag["element_b"] == "Ni"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Peritectic" in inv_types
    assert "Congruent Summit" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 942.0 in inv_temps
    assert 984.0 in inv_temps
    assert 1310.0 in inv_temps
    assert 1118.0 in inv_temps
    assert 1380.0 in inv_temps
    assert 1304.0 in inv_temps


def test_cu_zn_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Cu-Zn (Hume-Rothery Brass System)", temp_unit="C")
    assert diag["element_a"] == "Cu"
    assert diag["element_b"] == "Zn"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Peritectic" in inv_types
    assert "Eutectic" in inv_types
    assert "B2 Order-Disorder" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 902.0 in inv_temps
    assert 835.0 in inv_temps
    assert 598.0 in inv_temps
    assert 419.0 in inv_temps


def test_cu_sn_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Cu-Sn (Structural Bronze System)", temp_unit="C")
    assert diag["element_a"] == "Cu"
    assert diag["element_b"] == "Sn"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Peritectic" in inv_types
    assert "Peritectoid" in inv_types
    assert "Eutectic" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 798.0 in inv_temps
    assert 755.0 in inv_temps
    assert 520.0 in inv_temps
    assert 640.0 in inv_temps
    assert 415.0 in inv_temps
    assert 227.0 in inv_temps


def test_arbitrary_binary_eutectic_solvus_and_tie_line():
    # Cu-Ag is a classic eutectic system
    diag = BinaryDiagramEngine.compute_binary_diagram("Cu-Ag (Arbitrary)", temp_unit="C", n_points=60)
    curve_names = [c["name"] for c in diag["curves"]]
    assert "Liquidus" in curve_names
    assert any("Solidus" in name for name in curve_names)
    assert any("Solvus" in name for name in curve_names)
    assert "Eutectic Invariant Tie-Line" in curve_names

    tie = next(c for c in diag["curves"] if c["name"] == "Eutectic Invariant Tie-Line")
    # Horizontal tie line
    assert tie["ys"][0] == tie["ys"][1]
    # Spans between terminal solid solutions
    assert tie["xs"][0] < tie["xs"][1]



def test_database_queries_all_14_databases():
    for db_name, expected_systems in BinaryDiagramEngine.DATABASE_BINARY_SYSTEMS.items():
        avail = BinaryDiagramEngine.get_available_systems(database_name=db_name)
        assert len(avail) == len(expected_systems)
        for s in expected_systems:
            assert s in avail


def test_al_zn_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Zn", temp_unit="C")
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Zn"
    inv_types = [inv["type"] for inv in diag["invariants"]]
    assert "Eutectic" in inv_types
    assert "Eutectoid" in inv_types
    inv_temps = [inv["temp"] for inv in diag["invariants"]]
    assert 381.0 in inv_temps
    assert 277.0 in inv_temps


def test_sn_ag_and_sn_pb_solders():
    diag_ag = BinaryDiagramEngine.compute_binary_diagram("Sn-Ag", temp_unit="C")
    assert diag_ag["element_a"] == "Sn"
    assert diag_ag["element_b"] == "Ag"
    assert any(inv["temp"] == 221.0 for inv in diag_ag["invariants"])

    diag_pb = BinaryDiagramEngine.compute_binary_diagram("Sn-Pb", temp_unit="C")
    assert diag_pb["element_a"] == "Sn"
    assert diag_pb["element_b"] == "Pb"
    assert any(inv["temp"] == 183.0 for inv in diag_pb["invariants"])


def test_ti_zr_and_zr_nb():
    diag_tz = BinaryDiagramEngine.compute_binary_diagram("Ti-Zr", temp_unit="C")
    assert any(inv["temp"] == 1540.0 for inv in diag_tz["invariants"])
    assert any(inv["temp"] == 605.0 for inv in diag_tz["invariants"])

    diag_zn = BinaryDiagramEngine.compute_binary_diagram("Zr-Nb", temp_unit="C")
    assert any(inv["temp"] == 610.0 for inv in diag_zn["invariants"])


def test_mo_w_and_nb_mo_refractory():
    diag_mw = BinaryDiagramEngine.compute_binary_diagram("Mo-W", temp_unit="C")
    assert diag_mw["element_a"] == "Mo"
    assert diag_mw["element_b"] == "W"
    assert len(diag_mw["curves"]) == 2

    diag_nm = BinaryDiagramEngine.compute_binary_diagram("Nb-Mo", temp_unit="C")
    assert diag_nm["element_a"] == "Nb"
    assert diag_nm["element_b"] == "Mo"
    assert len(diag_nm["curves"]) == 2


def test_al_zr_pandat_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Zr", temp_unit="C")
    assert diag["system"] == "Al-Zr"
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Zr"
    # Verify 10 intermetallics + liquidus + solidus/solvus curves
    assert len(diag["curves"]) >= 15
    curve_names = [c["name"] for c in diag["curves"]]
    assert "Al₃Zr" in curve_names
    assert "Al₂Zr" in curve_names
    assert "Al₃Zr₂" in curve_names
    assert "Al₄Zr₅" in curve_names
    assert "Al₂Zr₃" in curve_names
    assert "Al₃Zr₅" in curve_names
    assert "AlZr₂" in curve_names
    assert "AlZr₃" in curve_names
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 660.6) < 1.0 for inv in diag["invariants"])
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 1347.8) < 1.0 for inv in diag["invariants"])


def test_al_y_calphad_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Al-Y", temp_unit="C")
    assert diag["system"] == "Al-Y"
    assert diag["element_a"] == "Al"
    assert diag["element_b"] == "Y"
    curve_names = [c["name"] for c in diag["curves"]]
    assert "Al₂Y (Laves C15)" in curve_names
    assert "Al₃Y (α/β)" in curve_names
    assert "AlY" in curve_names
    assert "Al₂Y₃" in curve_names
    assert "AlY₂" in curve_names
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 644.0) < 1.0 for inv in diag["invariants"])
    assert any("Congruent Peak" in inv["type"] and abs(inv["temp"] - 1490.0) < 1.0 for inv in diag["invariants"])


def test_co_zr_calphad_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Co-Zr", temp_unit="C")
    assert diag["system"] == "Co-Zr"
    assert diag["element_a"] == "Co"
    assert diag["element_b"] == "Zr"
    curve_names = [c["name"] for c in diag["curves"]]
    assert "Co₂Zr (C15)" in curve_names
    assert "Co₁₁Zr₂" in curve_names
    assert "Co₂₃Zr₆" in curve_names
    assert "CoZr" in curve_names
    assert "CoZr₂" in curve_names
    assert "CoZr₃" in curve_names
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 1254.0) < 1.0 for inv in diag["invariants"])
    assert any("Congruent Peak" in inv["type"] and abs(inv["temp"] - 1544.0) < 1.0 for inv in diag["invariants"])


def test_co_y_calphad_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Co-Y", temp_unit="C")
    assert diag["system"] == "Co-Y"
    assert diag["element_a"] == "Co"
    assert diag["element_b"] == "Y"
    curve_names = [c["name"] for c in diag["curves"]]
    assert "Y₂Co₁₇" in curve_names
    assert "YCo₅" in curve_names
    assert "Y₂Co₇" in curve_names
    assert "YCo₃" in curve_names
    assert "YCo₂" in curve_names
    assert "Y₃Co" in curve_names
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 733.0) < 1.0 for inv in diag["invariants"])


def test_cr_y_orchid_benchmark():
    diag = BinaryDiagramEngine.compute_binary_diagram("Cr-Y", temp_unit="C")
    assert diag["system"] == "Cr-Y"
    assert diag["element_a"] == "Cr"
    assert diag["element_b"] == "Y"
    curve_names = [c["name"] for c in diag["curves"]]
    assert any("Miscibility Gap" in n for n in curve_names)
    assert any("Monotectic" in n for n in curve_names)
    assert any(inv["type"] == "Monotectic" and abs(inv["temp"] - 1746.5) < 1.0 for inv in diag["invariants"])
    assert any(inv["type"] == "Eutectic" and abs(inv["temp"] - 1446.85) < 1.0 for inv in diag["invariants"])


def test_fe_ni_solidus_liquidus_ordering():
    diag = BinaryDiagramEngine.compute_binary_diagram("Fe-Ni", temp_unit="C")
    liq = next(c for c in diag["curves"] if c["name"] == "Liquidus")
    sol = next(c for c in diag["curves"] if c["name"] == "Solidus")
    for x, yl, ys in zip(liq["xs"], liq["ys"], sol["ys"]):
        assert ys <= yl + 1e-2, f"Solidus exceeds Liquidus at x={x}: sol={ys} > liq={yl}"
    assert any(inv["type"] == "Peritectic" and abs(inv["temp"] - 1513.0) < 1.0 for inv in diag["invariants"])
