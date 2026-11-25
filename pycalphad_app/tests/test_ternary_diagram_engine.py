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
])
def test_compute_assessed_ternary(sys_id):
    res = TernaryDiagramEngine.compute_ternary_diagram(sys_id, diagram_type="isothermal", temperature_c=800.0)
    assert res["system"] == sys_id
    assert len(res["triangle_border_x"]) == 4
    assert len(res["grid_lines"]) > 0
    assert len(res["curves"]) > 0
    assert len(res["invariants"]) > 0
    assert "apex_labels" in res
    assert res["apex_labels"]["A"]["name"] != ""
    assert res["apex_labels"]["B"]["name"] != ""
    assert res["apex_labels"]["C"]["name"] != ""


def test_compute_arbitrary_ternary():
    res = TernaryDiagramEngine.compute_ternary_diagram("V-Cr-Mo", diagram_type="isothermal", temperature_c=1000.0)
    assert res["element_a"] == "V"
    assert res["element_b"] == "Cr"
    assert res["element_c"] == "Mo"
    assert len(res["curves"]) > 0
    assert len(res["invariants"]) > 0
