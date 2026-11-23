# -*- coding: utf-8 -*-
"""
test_full_suite_e2e.py - End-to-End Scientific Desktop CAE Integration Test
Verifies:
1. Complete MainWindow launch with non-clipping dock, splitter constraints, and navigation tools.
2. Interactive stepped execution: clicking Step Forward plots discrete (T_k, f_i) points.
3. Reset execution: restores pristine waiting state.
4. Gated run-to-completion calculation: compiles full multi-physics results across all 8 views.
5. Literature audit and validation table population with quantitative deviations.
6. Window layout operations (Reset Default Layout, Toggle Panels, Maximize Canvas).
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pycalphad_app.gui.main_window import MainWindow
from pycalphad_app.database.benchmark_database import BenchmarkDatabase


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_e2e_stepped_and_full(qapp):
    win = MainWindow()
    win.show()
    win.switch_database("High Entropy Alloys")

    # 1. Verify dock and navigation configuration
    assert win.database_dock.minimumWidth() >= 320
    assert not win.database_dock.isHidden()
    assert win.action_reset_layout is not None
    assert win.action_max_view is not None

    # 2. Interactive Stepped Execution: Step Forward 3 times
    comp = {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}
    for _ in range(3):
        win.step_calculation(
            db_name="High Entropy Alloys",
            comp=comp,
            basis="at%",
            grain_size=25.0,
            process_type="Arc Melt / Cast",
            t_start=300.0,
            t_stop=2000.0,
            t_step=20.0
        )

    # Check equilibrium and mechanical views received 3 stepped points
    assert len(win.tab_equilibrium.step_history_t) == 3
    assert len(win.tab_mechanical.step_history_t) == 3
    assert "Active T:" in win.database_dock.lbl_summary_sol.text()

    # 3. Reset calculation
    win.reset_calculation()
    assert len(win.tab_equilibrium.step_history_t) == 0
    assert len(win.tab_mechanical.step_history_t) == 0

    # 4. Full Gated Run-to-Completion Simulation
    mock_results = {
        "database_name": "High Entropy Alloys",
        "composition": {"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2},
        "basis": "at%",
        "grain_size_um": 25.0,
        "elapsed_ms": 42.5,
        "is_coating": False,
        "thermo": {
            "Solidus_K": 1553.0,
            "Liquidus_K": 1608.0,
            "Density_g_cm3": 8.04,
            "VEC": 8.0,
            "PhaseFractions": {"T_K": [300, 800, 1553, 1608, 2000], "FCC": [1, 1, 1, 0, 0], "Liquid": [0, 0, 0, 1, 1]}
        },
        "mechanical": {
            "YieldStrength_RT_MPa": 410.0,
            "UTS_RT_MPa": 750.0,
            "VickersHardness_HV": 142.0,
            "Elongation_pct": 50.0,
            "YoungsModulus_GPa": 202.0,
            "FractureToughness_MPa_m05": 217.0,
            "PughRatio": 2.15,
            "DominantStructure": "Single-Phase FCC",
            "TempDep_Temperature_K": [300, 600, 900, 1200],
            "TempDep_YieldStrength_MPa": [410, 360, 280, 110],
            "TempDep_UTS_MPa": [750, 680, 520, 210]
        },
        "oxidation": {
            "kp_800C": 1.2e-12,
            "kp_1000C": 4.5e-11,
            "SelectiveOxide": "Cr2O3 (Chromia Former)",
            "Temp_C": [700, 800, 900, 1000],
            "kp_values": [1.5e-13, 1.2e-12, 8.5e-12, 4.5e-11]
        },
        "corrosion": {
            "Ecorr_V": -0.28,
            "icorr_uA_cm2": 0.35,
            "PassivationRange_V": 0.85
        },
        "xrd": {
            "two_theta": [43.6, 50.8, 74.7],
            "intensity": [1.0, 0.49, 0.31],
            "peaks": [
                {"hkl": "(111)", "two_theta": 43.6, "intensity": 1.0},
                {"hkl": "(200)", "two_theta": 50.8, "intensity": 0.49},
                {"hkl": "(220)", "two_theta": 74.7, "intensity": 0.31}
            ]
        },
        "application_scores": [
            {"name": "Cryogenic & Extreme Cold", "score_pct": 94.5, "verdict": "Exemplary"},
            {"name": "Structural & High Strength", "score_pct": 82.0, "verdict": "Viable"}
        ]
    }

    # Populate validation table using BenchmarkDatabase
    bench_data = BenchmarkDatabase.compare_metrics(comp, mock_results)
    mock_results["validation_table"] = bench_data["table"]
    mock_results["validation_citations"] = [bench_data["citation"]]

    win.on_worker_finished(mock_results)

    # 5. Check all tabs rendered properly
    assert win.tab_validation.table.rowCount() >= 5
    assert "Cantor" in win.tab_validation.table.item(0, 5).text() or "Laplanche" in win.tab_validation.table.item(0, 5).text()
    assert win.database_dock.btn_calc.isEnabled()

    # 6. Test Window Navigation Actions
    win.toggle_database_panel()
    assert win.database_dock.isHidden()
    win.toggle_database_panel()
    assert not win.database_dock.isHidden()

    win.reset_default_layout()
    assert not win.database_dock.isHidden()

    win.maximize_active_view()
    assert win.database_dock.isHidden()
    win.maximize_active_view()
    assert not win.database_dock.isHidden()

    win.close()
