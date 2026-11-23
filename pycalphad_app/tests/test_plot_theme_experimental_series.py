# -*- coding: utf-8 -*-
"""
test_plot_theme_experimental_series.py - Unit test for plot_experimental_series
Verifies discrete marker rendering, direct line connector, and shaded uncertainty envelope.
"""

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg

from pycalphad_app.gui.plot_theme import plot_experimental_series


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_plot_experimental_series_renders_envelope(qapp):
    plot_widget = pg.PlotWidget()
    x = [100.0, 300.0, 500.0, 700.0]
    y = [10.0, 20.0, 30.0, 40.0]

    item = plot_experimental_series(
        plot_widget, x, y,
        name="Exp. Benchmark Test (Otto 2013)",
        color="#D97706",
        symbol="o",
        uncertainty_pct=0.075,
        show_envelope=True
    )

    assert item is not None
    # Check that fill item exists in plot
    fill_items = [it for it in plot_widget.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(fill_items) == 1

    # Check data points match
    x_data, y_data = item.getData()
    assert len(x_data) == 4
    assert np.allclose(x_data, x)
    assert np.allclose(y_data, y)


def test_plot_experimental_series_without_envelope(qapp):
    plot_widget = pg.PlotWidget()
    x = [298.15]
    y = [205.0]

    item = plot_experimental_series(
        plot_widget, x, y,
        name="Single Point Benchmark",
        color="#DC2626",
        symbol="s",
        show_envelope=False
    )
    assert item is not None
    fill_items = [it for it in plot_widget.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(fill_items) == 0
