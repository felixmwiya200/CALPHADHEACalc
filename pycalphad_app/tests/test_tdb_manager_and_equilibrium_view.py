# -*- coding: utf-8 -*-
"""
test_tdb_manager_and_equilibrium_view.py
Unit tests verifying the thermodynamic database registry (TDBManager)
and the upgraded flicker-free EquilibriumView real-time stepping.
"""

import os
import pytest
from PyQt6.QtWidgets import QApplication

from pycalphad_app.database.tdb_manager import TDBManager
from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.gui.plot_views.equilibrium_view import EquilibriumView

# Ensure single QApplication instance across tests
app = QApplication.instance()
if app is None:
    app = QApplication([])


def test_tdb_manager_discovery():
    """Verifies that TDBManager discovers the extracted TDB databases."""
    databases = TDBManager.list_all_databases()
    assert len(databases) >= 20, f"Expected at least 20 databases, found {len(databases)}"
    names = [d["name"] for d in databases]
    assert "fe_c.tdb" in names
    assert "ni_al_cr.tdb" in names
    assert "ti_al_v.tdb" in names
    assert "solder_sn_ag_cu.tdb" in names
    assert "cu_ni.tdb" in names


def test_tdb_manager_family_routing():
    """Verifies that all 14 alloy families map to authentic TDB databases."""
    for db_name in MaterialDatabaseSelector.get_database_list():
        tdb_path = TDBManager.get_tdb_for_family(db_name)
        assert tdb_path is not None, f"No TDB mapped for family: {db_name}"
        assert os.path.isfile(tdb_path), f"Mapped TDB file does not exist: {tdb_path}"
        meta = TDBManager.get_metadata(tdb_path)
        assert meta["num_elements"] > 0, f"No elements in TDB for {db_name}"


def test_tdb_manager_element_lookup():
    """Verifies that find_best_tdb_for_elements finds matching multi-component databases."""
    fe_c_tdb = TDBManager.find_best_tdb_for_elements(["Fe", "C"])
    assert fe_c_tdb is not None
    assert "fe_c" in os.path.basename(fe_c_tdb).lower() or "brosh" in os.path.basename(fe_c_tdb).lower()

    ni_al_cr_tdb = TDBManager.find_best_tdb_for_elements(["Ni", "Al", "Cr"])
    assert ni_al_cr_tdb is not None
    assert "ni" in os.path.basename(ni_al_cr_tdb).lower()

    ti_al_v_tdb = TDBManager.find_best_tdb_for_elements(["Ti", "Al", "V"])
    assert ti_al_v_tdb is not None
    assert "ti" in os.path.basename(ti_al_v_tdb).lower()


def test_equilibrium_view_default_temperature_and_reset():
    """Verifies that EquilibriumView defaults to 293.0 K and reset_step_data restores waiting state."""
    view = EquilibriumView()

    # Verify initial and reset state
    view.reset_step_data()
    assert view.step_history_t == []
    assert view.step_history_phases == {}
    assert view.step_curves == {}
    assert "Awaiting" in view.status_label.text()

    # Step without explicit temperature should default to 293.0 K
    view.update_step_point({"phases": {"FCC_A1": 0.85, "LIQUID": 0.0}, "step_index": 1})
    assert len(view.step_history_t) == 1
    assert view.step_history_t[0] == 293.0
    assert "FCC_A1" in view.step_curves

    # Step with explicit temperature should update curve in place via setData
    view.update_step_point({"temperature": 350.0, "phases": {"FCC_A1": 0.82, "LIQUID": 0.0}, "step_index": 2})
    assert len(view.step_history_t) == 2
    assert view.step_history_t[1] == 350.0
    assert "FCC_A1" in view.step_curves
    fcc_curve = view.step_curves["FCC_A1"]
    x_data, y_data = fcc_curve.getData()
    assert len(x_data) == 2
    assert x_data[0] == 293.0
    assert x_data[1] == 350.0

    # Reset clears step curves cleanly
    view.reset_step_data()
    assert len(view.step_curves) == 0
    assert "Awaiting" in view.status_label.text()
