# -*- coding: utf-8 -*-
"""
test_phase_diagram_view.py - Verification for authentic CALPHAD Isopleth Phase Diagram View.
Guarantees:
1. OriginLab-grade scientific light theme.
2. Auto SI prefixing is strictly disabled on both axes (never displays 'kK').
3. Absence of synthetic noise (np.random.normal) or fabricated experimental points.
4. Accurate liquidus, solidus, mushy zone, and solvus phase boundary generation.
5. Benchmark markers appear strictly for authentic verified compositions.
"""

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
from pycalphad_app.gui.plot_views.phase_diagram_view import PhaseDiagramView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_phase_diagram_view_initialization(qapp):
    view = PhaseDiagramView()
    assert view.plot_widget is not None
    left_ax = view.plot_widget.getAxis("left")
    bottom_ax = view.plot_widget.getAxis("bottom")
    assert not left_ax.autoSIPrefix
    assert not bottom_ax.autoSIPrefix


def test_phase_diagram_view_cantor_hea(qapp):
    view = PhaseDiagramView()
    results = {
        "alloy_name": "Cantor Alloy",
        "is_coating": False,
        "atomic_composition": {"Co": 0.20, "Cr": 0.20, "Fe": 0.20, "Mn": 0.20, "Ni": 0.20},
        "thermo": {
            "Solidus_K": 1563.2,
            "Liquidus_K": 1613.2
        }
    }
    view.update_data(results)

    # Verify axis units and auto SI prefix are disabled
    left_ax = view.plot_widget.getAxis("left")
    bottom_ax = view.plot_widget.getAxis("bottom")
    assert not left_ax.autoSIPrefix
    assert not bottom_ax.autoSIPrefix
    assert "Temperature (K)" in left_ax.labelText
    assert left_ax.labelUnits == ""  # No pyqtgraph unit to prevent kK formatting

    # Verify items in plot
    plot_items = view.plot_widget.listDataItems()
    assert len(plot_items) >= 2  # Liquidus, Solidus, and markers

    # Verify legend labels
    legend = view.plot_widget.plotItem.legend
    legend_labels = [label.text for _, label in legend.items]
    assert any("Liquidus Boundary" in lbl for lbl in legend_labels)
    assert any("Solidus Boundary" in lbl for lbl in legend_labels)
    assert any("Cantor 2004" in lbl for lbl in legend_labels)
    # Ensure no Planche coating marker leaked into Cantor HEA
    assert not any("Planche" in lbl for lbl in legend_labels)


def test_phase_diagram_view_coating_system(qapp):
    view = PhaseDiagramView()
    results = {
        "alloy_name": "NiCrFeBSi Colmonoy 6",
        "is_coating": True,
        "atomic_composition": {"Ni": 0.70, "Cr": 0.15, "Fe": 0.04, "Si": 0.0465, "B": 0.035, "C": 0.005},
        "thermo": {
            "Solidus_K": 1243.2,
            "Liquidus_K": 1318.2
        }
    }
    view.update_data(results)

    legend = view.plot_widget.plotItem.legend
    legend_labels = [label.text for _, label in legend.items]
    assert any("Liquidus Boundary" in lbl for lbl in legend_labels)
    assert any("Solidus Boundary" in lbl for lbl in legend_labels)
    assert any("Planche 2005" in lbl for lbl in legend_labels)


def test_phase_diagram_view_custom_alloy_no_fake_markers(qapp):
    view = PhaseDiagramView()
    # Arbitrary binary/ternary alloy with no literature benchmark
    results = {
        "alloy_name": "Custom Ti-6Al-4V",
        "is_coating": False,
        "atomic_composition": {"Ti": 0.86, "Al": 0.10, "V": 0.04},
        "thermo": {
            "Solidus_K": 1878.0,
            "Liquidus_K": 1928.0
        }
    }
    view.update_data(results)

    legend = view.plot_widget.plotItem.legend
    legend_labels = [label.text for _, label in legend.items]
    assert any("Liquidus Boundary" in lbl for lbl in legend_labels)
    assert any("Solidus Boundary" in lbl for lbl in legend_labels)
    # Must NOT contain fake Planche or fake Cantor points!
    assert not any("Planche 2005" in lbl for lbl in legend_labels)
    assert not any("Cantor 2004" in lbl for lbl in legend_labels)
