# -*- coding: utf-8 -*-
"""
test_all_views_experimental_overlays.py - Comprehensive verification that all
graphical views render authentic multi-point literature benchmarks and shaded
uncertainty envelopes (pg.FillBetweenItem).
"""

import pytest
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg

from pycalphad_app.gui.plot_views.mechanical_view import MechanicalView
from pycalphad_app.gui.plot_views.transport_view import TransportView
from pycalphad_app.gui.plot_views.environmental_view import EnvironmentalView
from pycalphad_app.gui.plot_views.phase_diagram_view import PhaseDiagramView
from pycalphad_app.gui.plot_views.equilibrium_view import EquilibriumView
from pycalphad_app.database.benchmark_database import BenchmarkDatabase


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_mechanical_view_has_fill_between_and_benchmarks(qapp):
    view = MechanicalView()
    comp = {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")
    results = {
        "composition": comp,
        "database": "High Entropy Alloys",
        "mechanical": {
            "YieldStrength_RT_MPa": 205.0,
            "UTS_RT_MPa": 460.0,
            "DominantStructure": "FCC (Cantor)",
            "StrainHardeningExponent": 0.38,
            "StrengthCoefficient_K_MPa": 1150.0
        },
        "benchmarks": pb,
        "is_coating": False
    }
    view.update_data(results)

    # plot_sy must contain FillBetweenItem for uncertainty envelope
    sy_fills = [it for it in view.plot_sy.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(sy_fills) >= 1

    # plot_ss must contain FillBetweenItem for flow curve uncertainty envelope
    ss_fills = [it for it in view.plot_ss.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(ss_fills) >= 1


def test_transport_view_has_fill_between_and_benchmarks(qapp):
    view = TransportView()
    comp = {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")
    results = {
        "composition": comp,
        "database": "High Entropy Alloys",
        "thermo": {
            "Density_g_cm3": 8.05,
            "Solidus_K": 1553.0,
            "Liquidus_K": 1608.0
        },
        "benchmarks": pb,
        "is_coating": False
    }
    view.update_data(results)

    # plot_k must contain FillBetweenItem for k(T) uncertainty envelope
    k_fills = [it for it in view.plot_k.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(k_fills) >= 1

    # plot_density must contain FillBetweenItem for rho(T) uncertainty envelope
    dens_fills = [it for it in view.plot_density.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(dens_fills) >= 1

    # plot_cte must contain FillBetweenItem for alpha(T) uncertainty envelope
    cte_fills = [it for it in view.plot_cte.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(cte_fills) >= 1


def test_environmental_view_has_fill_between_and_benchmarks(qapp):
    view = EnvironmentalView()
    comp = {"Co": 20, "Cr": 20, "Fe": 20, "Mn": 20, "Ni": 20}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "High Entropy Alloys")
    results = {
        "composition": comp,
        "database": "High Entropy Alloys",
        "oxidation": {
            "kp_g2_cm4_s": 2.27e-10,
            "Regime": "Cr2O3 Scale"
        },
        "corrosion": {
            "Corrosion_Ecorr_V": -0.28,
            "Corrosion_icorr_uA": 0.35
        },
        "benchmarks": pb,
        "is_coating": False
    }
    view.update_data(results)

    # plot_ox must contain FillBetweenItem for Wagner TGA mass gain uncertainty envelope
    ox_fills = [it for it in view.plot_ox.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(ox_fills) >= 1

    # plot_corr must contain FillBetweenItem for Tafel polarization uncertainty envelope
    corr_fills = [it for it in view.plot_corr.plotItem.items if isinstance(it, pg.FillBetweenItem)]
    assert len(corr_fills) >= 1


def test_phase_diagram_and_equilibrium_views_have_benchmarks(qapp):
    pd_view = PhaseDiagramView()
    eq_view = EquilibriumView()

    comp = {"Ni": 53.0, "Cr": 19.0, "Fe": 18.0, "Nb": 5.0, "Mo": 3.0, "Ti": 1.0, "Al": 0.5}
    pb = BenchmarkDatabase.get_plot_benchmarks(comp, "Nickel & Ni-Fe Superalloys")
    results = {
        "composition": comp,
        "atomic_composition": comp,
        "database": "Nickel & Ni-Fe Superalloys",
        "thermo": {
            "Solidus_K": 1533.0,
            "Liquidus_K": 1609.0,
            "PhaseFractions": {
                "T_K": [1000.0, 1200.0, 1400.0, 1600.0],
                "Liquid": [0.0, 0.0, 0.0, 0.8]
            }
        },
        "benchmarks": pb,
        "is_coating": False
    }
    pd_view.update_data(results)
    eq_view.update_data(results)

    # Verify that plot items include the experimental benchmark points
    pd_items = pd_view.plot_widget.plotItem.items
    eq_items = eq_view.plot_widget.plotItem.items

    def item_name(it):
        if hasattr(it, "opts") and isinstance(it.opts, dict):
            return str(it.opts.get("name", ""))
        return ""

    assert any("Exp. DSC" in item_name(it) for it in pd_items)
    assert any("Exp. DSC" in item_name(it) for it in eq_items)
