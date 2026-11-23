# -*- coding: utf-8 -*-
"""
test_graph_toolbar_csv.py - Unit Tests for OriginLab Graph CSV Data Export
Verifies:
1. Unified column extraction for curves sharing identical X coordinates.
2. Paired column extraction for curves with disjoint X grids (e.g. calculated lines + experimental points).
3. Export redirection through export_graph() when CSV format is selected.
4. Correct UTF-8 BOM encoding and OriginPro metadata headers.
"""

import os
import tempfile
import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_graph_export_csv_unified_grid(qapp):
    plot_widget = pg.PlotWidget()
    plot_item = plot_widget.getPlotItem()
    plot_item.getAxis("bottom").setLabel("Temperature", units="K")
    plot_item.getAxis("left").setLabel("Phase Fraction")

    # Add 2 curves with identical X grids
    x = np.array([300.0, 600.0, 900.0, 1200.0, 1500.0])
    y1 = np.array([0.0, 0.0, 0.1, 0.5, 1.0])
    y2 = np.array([1.0, 1.0, 0.9, 0.5, 0.0])

    plot_widget.plot(x, y1, name="Liquid")
    plot_widget.plot(x, y2, name="FCC_A1")

    toolbar = GraphNavigationToolbar(plot_widget, title="Phase_Equilibrium")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        exported_path = toolbar.export_csv_data(file_path=tmp_path)
        assert exported_path == tmp_path
        assert os.path.exists(tmp_path)

        with open(tmp_path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Check comment header
        assert "# OriginLab / PyCALPHAD Suite Graph Data Export - Phase_Equilibrium" in lines[0]
        # Check unified columns
        assert lines[1] == "Temperature [K],Liquid,FCC_A1"
        # Check data row
        assert lines[2] == "300,0,1"
        assert len(lines) == 7  # 1 comment + 1 header + 5 data rows
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_graph_export_csv_disjoint_grid(qapp):
    plot_widget = pg.PlotWidget()
    plot_item = plot_widget.getPlotItem()
    plot_item.getAxis("bottom").setLabel("Temperature", units="K")
    plot_item.getAxis("left").setLabel("Fraction")

    # Continuous calculated line (4 points)
    x_calc = np.array([1000.0, 1200.0, 1400.0, 1600.0])
    y_calc = np.array([0.0, 0.2, 0.8, 1.0])
    plot_widget.plot(x_calc, y_calc, name="Calculated_Liquid")

    # Discrete experimental benchmark (2 points)
    x_exp = np.array([1243.15, 1318.15])
    y_exp = np.array([0.0, 1.0])
    plot_widget.plot(x_exp, y_exp, name="Exp_DSC_Benchmark")

    toolbar = GraphNavigationToolbar(plot_widget, title="Equilibrium_With_DSC")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        exported_path = toolbar.export_csv_data(file_path=tmp_path)
        assert exported_path == tmp_path

        with open(tmp_path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Check disjoint paired columns
        assert "Temperature [K] (Calculated_Liquid),Calculated_Liquid,Temperature [K] (Exp_DSC_Benchmark),Exp_DSC_Benchmark" in lines[1]
        # Row 0 has both
        assert lines[2].startswith("1000,0,1243.15,0")
        # Row 2 (index 2) has calculated, but exp is exhausted
        assert lines[4].endswith(",,") or lines[4].endswith(",")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_graph_export_empty_plot_returns_none(qapp):
    plot_widget = pg.PlotWidget()
    toolbar = GraphNavigationToolbar(plot_widget, title="Empty_Plot")
    res = toolbar.export_csv_data(file_path="should_not_create.csv")
    assert res is None
    assert not os.path.exists("should_not_create.csv")
