# -*- coding: utf-8 -*-
"""
test_mechanical_view_overlays.py - Tests experimental series and uncertainty envelopes in MechanicalView
"""

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg

from pycalphad_app.gui.plot_views.mechanical_view import MechanicalView
from pycalphad_app.database.benchmark_database import BenchmarkDatabase


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_mechanical_view_renders_benchmarks_and_envelopes(qapp):
    view = MechanicalView()
    comp = {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")

    results = {
        "composition": comp,
        "mechanical": {
            "YieldStrength_RT_MPa": 205.0,
            "UTS_RT_MPa": 570.0,
            "DominantStructure": "FCC_A1 (Cantor)",
            "VickersHardness_HV": 142.0,
            "YoungsModulus_GPa": 202.0
        },
        "thermo": {
            "Solidus_K": 1553.0,
            "Liquidus_K": 1608.0
        },
        "benchmarks": pb,
        "is_coating": False
    }

    view.update_data(results)

    # 1. Verify plot_sy has calculated curve and experimental series with envelope
    sy_items = view.plot_sy.plotItem.items
    sy_fills = [it for it in sy_items if isinstance(it, pg.FillBetweenItem)]
    assert len(sy_fills) >= 1

    # 2. Verify plot_ss has experimental stress-strain flow curve with envelope
    ss_items = view.plot_ss.plotItem.items
    ss_fills = [it for it in ss_items if isinstance(it, pg.FillBetweenItem)]
    assert len(ss_fills) >= 1
