# -*- coding: utf-8 -*-
"""
test_ternary_diagram_engine.py - Verification for Ternary Phase Diagram Engine.
"""

import math
import pytest
from pycalphad_app.core.ternary_diagram_engine import (
    TernaryDiagramEngine,
    barycentric_to_cartesian,
    cartesian_to_barycentric,
)


def test_barycentric_cartesian_roundtrip():
    # Vertex A: (1, 0, 0) -> (0, 0)
    xa, ya = barycentric_to_cartesian(1.0, 0.0, 0.0)
    assert math.isclose(xa, 0.0, abs_tol=1e-4)
    assert math.isclose(ya, 0.0, abs_tol=1e-4)

    # Vertex B: (0, 1, 0) -> (1, 0)
    xb, yb = barycentric_to_cartesian(0.0, 1.0, 0.0)
    assert math.isclose(xb, 1.0, abs_tol=1e-4)
    assert math.isclose(yb, 0.0, abs_tol=1e-4)

    # Vertex C: (0, 0, 1) -> (0.5, sqrt(3)/2)
    xc, yc = barycentric_to_cartesian(0.0, 0.0, 1.0)
    assert math.isclose(xc, 0.5, abs_tol=1e-4)
    assert math.isclose(yc, math.sqrt(3) / 2.0, abs_tol=1e-4)

    # Center: (1/3, 1/3, 1/3)
    x_cent, y_cent = barycentric_to_cartesian(1 / 3, 1 / 3, 1 / 3)
    a, b, c = cartesian_to_barycentric(x_cent, y_cent)
    assert math.isclose(a, 1 / 3, abs_tol=1e-3)
    assert math.isclose(b, 1 / 3, abs_tol=1e-3)
    assert math.isclose(c, 1 / 3, abs_tol=1e-3)


def test_assessed_systems_list():
    systems = TernaryDiagramEngine.get_assessed_systems()
    assert len(systems) >= 15
    ids = [s["id"] for s in systems]
    assert "Co-Cr-Ni" in ids
    assert "Cr-Fe-Ni" in ids
    assert "Mo-Nb-Ta" in ids
    assert "Ti-Zr-Nb" in ids
    assert "Ni-Al-Ti" in ids
    assert "Cd-Pb-Sn" in ids
    assert "Cr-Fe-Nb" in ids
    assert "Al-Cu-Y" in ids
    assert "Fe-Sb-O" in ids


@pytest.mark.parametrize("sys_id", [
    "Co-Cr-Ni",
    "Cr-Fe-Ni",
    "Mo-Nb-Ta",
    "Ti-Zr-Nb",
    "Ni-Al-Ti",
    "Cd-Pb-Sn",
    "Mo-V-W",
    "Al-Cu-Mg",
    "Fe-Cr-C",
    "Cr-Fe-Nb",
    "Al-Cu-Y",
    "Fe-Sb-O",
])
def test_compute_assessed_ternary(sys_id):
    res = TernaryDiagramEngine.compute_ternary_diagram(sys_id, diagram_type="isothermal", temperature_c=800.0)
    assert res["system"] == sys_id
    assert len(res["triangle_border_x"]) == 4
    assert len(res["grid_lines"]) > 0
    assert len(res["curves"]) > 0
    assert len(res["invariants"]) > 0


def test_solve_quadric_liquidus_curved_surfaces():
    # Test solving 3-field quadric curved liquidus surface
    res = TernaryDiagramEngine.solve_quadric_liquidus(
        tm_a=1000.0, tm_b=920.0, tm_c=1060.0,
        e_ab=(0.45, 780.0),
        e_bc=(0.50, 810.0),
        e_ca=(0.40, 850.0),
        e_ternary=(0.35, 0.37, 0.28, 705.0),
        sag=0.16
    )
    assert "quad_a" in res
    assert "quad_b" in res
    assert "quad_c" in res
    assert len(res["quad_a"]) == 6
    assert len(res["quad_b"]) == 6
    assert len(res["quad_c"]) == 6

    # Verify quadric A passes through corner A [1, 0, 0] at Tm_A = 1000.0
    mono_a = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    t_a = sum(res["quad_a"][i] * mono_a[i] for i in range(6))
    assert abs(t_a - 1000.0) < 1e-4

    # Verify quadric A passes through ternary eutectic E at TE = 705.0
    ea, eb, ec = 0.35, 0.37, 0.28
    mono_e = [ea*ea, eb*eb, ec*ec, ea*eb, ea*ec, eb*ec]
    t_ea = sum(res["quad_a"][i] * mono_e[i] for i in range(6))
    assert abs(t_ea - 705.0) < 1e-4


def test_ceramic_mas_cordierite_system():
    diag = TernaryDiagramEngine.compute_ternary_diagram("MgO-Al2O3-SiO2")
    assert diag["system"] == "MgO-Al2O3-SiO2"
    assert len(diag["tie_triangles"]) == 9  # 9 Alkemade compatibility triangles
    assert any(inv["temp_c"] == 1355.0 for inv in diag["invariants"])  # E1 1355 C
    assert any("Cordierite" in lbl["name"] for lbl in diag["phase_labels"])


def test_ceramic_azs_refractory_system():
    diag = TernaryDiagramEngine.compute_ternary_diagram("Al2O3-SiO2-ZrO2")
    assert diag["system"] == "Al2O3-SiO2-ZrO2"
    assert len(diag["tie_triangles"]) == 3  # 3 Alkemade triangles
    assert any(inv["temp_c"] == 1705.0 for inv in diag["invariants"])  # Eutectic 1705 C
    assert any("Zircon" in lbl["name"] for lbl in diag["phase_labels"])
    assert "apex_labels" in res
    assert res["apex_labels"]["A"]["name"] != ""
    assert res["apex_labels"]["B"]["name"] != ""
    assert res["apex_labels"]["C"]["name"] != ""


def test_compute_molar_ratio_ray():
    ray = TernaryDiagramEngine.calculate_molar_ratio_ray(ratio_ab=1.0, n_points=25)
    assert ray["ratio_ab"] == 1.0
    assert len(ray["cart_xs"]) == 25
    assert len(ray["cart_ys"]) == 25
    # When X(C) = 0, X(A) = 0.5, X(B) = 0.5 -> Cartesian X = 0.5, Y = 0.0
    assert math.isclose(ray["cart_xs"][0], 0.5, abs_tol=1e-3)
    assert math.isclose(ray["cart_ys"][0], 0.0, abs_tol=1e-3)
    # When X(C) = 1, X(A) = 0, X(B) = 0 -> Apex C: Cartesian X = 0.5, Y = sqrt(3)/2
    assert math.isclose(ray["cart_xs"][-1], 0.5, abs_tol=1e-3)
    assert math.isclose(ray["cart_ys"][-1], math.sqrt(3) / 2.0, abs_tol=1e-3)


def test_compute_arbitrary_ternary():
    res = TernaryDiagramEngine.compute_ternary_diagram("V-Cr-Mo", diagram_type="isothermal", temperature_c=1000.0)
    assert res["element_a"] == "V"
    assert res["element_b"] == "Cr"
    assert res["element_c"] == "Mo"
    assert len(res["curves"]) > 0
    assert len(res["invariants"]) > 0


def test_solve_quadric_liquidus_curved_surfaces():
    # Test solving 3-field quadric curved liquidus surface
    res = TernaryDiagramEngine.solve_quadric_liquidus(
        tm_a=1000.0, tm_b=920.0, tm_c=1060.0,
        e_ab=(0.45, 780.0),
        e_bc=(0.50, 810.0),
        e_ca=(0.40, 850.0),
        e_ternary=(0.35, 0.37, 0.28, 705.0),
        sag=0.16
    )
    assert "quad_a" in res
    assert "quad_b" in res
    assert "quad_c" in res
    assert len(res["quad_a"]) == 6
    assert len(res["quad_b"]) == 6
    assert len(res["quad_c"]) == 6

    # Verify quadric A passes through corner A [1, 0, 0] at Tm_A = 1000.0
    mono_a = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    t_a = sum(res["quad_a"][i] * mono_a[i] for i in range(6))
    assert abs(t_a - 1000.0) < 1e-4

    # Verify quadric A passes through ternary eutectic E at TE = 705.0
    ea, eb, ec = 0.35, 0.37, 0.28
    mono_e = [ea*ea, eb*eb, ec*ec, ea*eb, ea*ec, eb*ec]
    t_ea = sum(res["quad_a"][i] * mono_e[i] for i in range(6))
    assert abs(t_ea - 705.0) < 1e-4


def test_ceramic_mas_cordierite_system():
    diag = TernaryDiagramEngine.compute_ternary_diagram("MgO-Al2O3-SiO2")
    assert diag["system"] == "MgO-Al2O3-SiO2"
    assert len(diag["tie_triangles"]) == 9  # 9 Alkemade compatibility triangles
    assert any(inv["temp_c"] == 1355.0 for inv in diag["invariants"])  # E1 1355 C
    assert any("Cordierite" in lbl["name"] for lbl in diag["phase_labels"])


def test_ceramic_azs_refractory_system():
    diag = TernaryDiagramEngine.compute_ternary_diagram("Al2O3-SiO2-ZrO2")
    assert diag["system"] == "Al2O3-SiO2-ZrO2"
    assert len(diag["tie_triangles"]) == 3  # 3 Alkemade triangles
    assert any(inv["temp_c"] == 1705.0 for inv in diag["invariants"])  # Eutectic 1705 C
    assert any("Zircon" in lbl["name"] for lbl in diag["phase_labels"])
