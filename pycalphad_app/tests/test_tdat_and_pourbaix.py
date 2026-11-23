"""
Unit and Integration Tests for TDAT Databases & Pourbaix Diagram Engine
=======================================================================
Validates the parsing, indexing, and thermodynamic calculations across the
8 GWB .tdat databases and verifies the Pourbaix (E-pH) phase stability solver.

Author: Jane, Chief of Staff & Materials CAE Collaborator
License: Proprietary / CALPHAD Materials Engineering Suite
"""

import pytest
import numpy as np
from pycalphad_app.database.tdat_parser import TDATParser
from pycalphad_app.database.tdat_registry import TDATRegistry
from pycalphad_app.core.pourbaix_engine import PourbaixEngine
from pycalphad_app.server.cae_daemon import CAEDaemon


class TestTDATDatabasesAndParser:
    """Verifies that all 8 .tdat files in Databases are successfully parsed and indexed."""

    def test_tdat_parser_loads_all_8_databases(self):
        dbs = TDATRegistry.list_databases()
        assert len(dbs) == 8, f"Expected 8 databases, found {len(dbs)}"

        for item in dbs:
            fname = item["filename"]
            db = TDATRegistry.get_database(fname)
            assert len(db.elements) > 0, f"Database {fname} has 0 elements"
            assert len(db.temperatures_c) == 8, f"Database {fname} missing standard 8-point temperature grid"
            assert len(db.minerals) > 0, f"Database {fname} has 0 minerals"

    def test_tdat_registry_search_species_and_reactions(self):
        # Search Eskolaite in V8.R6+
        hits = TDATRegistry.search_species("Eskolaite", db_name="thermo.com.V8.R6+.tdat")
        assert len(hits) > 0
        esk = hits[0]
        assert esk["formula"] == "Cr2O3"
        assert esk["phase_type"] == "Mineral"
        assert "CrO4--" in esk["reaction"] or "H+" in esk["reaction"]

        # Search Bunsenite (NiO)
        ni_hits = TDATRegistry.search_species("Bunsenite", db_name="thermo.com.V8.R6+.tdat")
        assert len(ni_hits) > 0
        assert ni_hits[0]["formula"] == "NiO"

        # Search Hematite (Fe2O3)
        fe_hits = TDATRegistry.search_species("Hematite", db_name="thermo.tdat")
        assert len(fe_hits) > 0
        assert fe_hits[0]["formula"] == "Fe2O3"


class TestPourbaixEngine:
    """Verifies the Pourbaix (E-pH) phase stability solver."""

    def test_pourbaix_water_stability_lines(self):
        w_25 = PourbaixEngine.calculate_water_lines(temp_c=25.0)
        assert abs(w_25["nernst_slope_v_ph"] - 0.05916) < 0.001
        assert abs(w_25["e_her"][0] - 0.0) < 0.05
        assert abs(w_25["e_oer"][0] - 1.229) < 0.05

        w_250 = PourbaixEngine.calculate_water_lines(temp_c=250.0)
        assert w_250["nernst_slope_v_ph"] > 0.095  # Slope increases linearly with absolute temperature
        assert w_250["e0_oer"] < 1.229  # Reversible OER potential decreases with temperature

    def test_pourbaix_stainless_steel_passivation(self):
        comp = {"Fe": 70.0, "Cr": 18.0, "Ni": 12.0}
        res = PourbaixEngine.calculate_pourbaix(comp, temp_c=25.0)
        assert "Eskolaite" in res["composite_envelope"]["dominant_oxide"] or "Cr2O3" in res["composite_envelope"]["dominant_formula"]
        assert res["composite_envelope"]["is_passivating"] is True

        metrics = res["metrics"]
        assert metrics["Delta_E_pass_V"] > 1.2  # Broad protective passivity window
        assert metrics["pH_pass_min"] <= 3.5  # Stable passivation even at acidic pH due to Cr2O3

    def test_pourbaix_temperature_hydrothermal_scaling(self):
        comp = {"Al": 20.0, "Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Ni": 20.0}
        res_25 = PourbaixEngine.calculate_pourbaix(comp, temp_c=25.0)
        res_200 = PourbaixEngine.calculate_pourbaix(comp, temp_c=200.0)

        # Hydrothermal conditions increase steam saturation pressure
        assert res_200["pressure_bar"] > 1.0
        # Passivity bounds shift with temperature
        assert res_200["water_lines"]["nernst_slope_v_ph"] > res_25["water_lines"]["nernst_slope_v_ph"]


class TestCAEDaemonTDATIntegration:
    """Verifies that CAEDaemon handles TDAT queries and includes Pourbaix in equilibrium results."""

    def test_daemon_tdat_database_catalog(self):
        res = CAEDaemon.handle_get_tdat_databases({})
        assert res["status"] == "success"
        assert len(res["databases"]) == 8

    def test_daemon_calculate_pourbaix(self):
        req = {
            "composition": {"Ti": 90.0, "Al": 6.0, "V": 4.0},
            "temperature_c": 50.0,
            "database_name": "thermo.com.V8.R6+.tdat"
        }
        res = CAEDaemon.handle_calculate_pourbaix(req)
        assert res["status"] == "success"
        assert "composite_envelope" in res
        assert "water_lines" in res
        assert len(res["passivating_minerals"]) > 0

    def test_daemon_calculate_equilibrium_contains_pourbaix(self):
        req = {
            "database_name": "High Entropy Alloys",
            "composition": {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0},
            "basis": "at%",
            "calc_mode": "fast"
        }
        res = CAEDaemon.handle_calculate_equilibrium(req)
        assert res["status"] == "success"
        assert "pourbaix_diagram" in res
        p_diag = res["pourbaix_diagram"]
        assert "water_lines" in p_diag
        assert "composite_envelope" in p_diag
        assert "aqueous_corrosion" in res
