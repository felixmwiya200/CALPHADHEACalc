"""
test_new_databases_integration.py - Comprehensive Unit & Integration Tests for New Databases.
Tests the 12,427 HEA literature database, 17 GWB .sdat surface complexation datasets,
OLI Studio industrial streams (.oad), USGS McCleskey conductivity, and TCHEA benchmarks.
"""

import os
import pytest
from pycalphad_app.database.hea_literature_db import HEALiteratureDatabase
from pycalphad_app.database.sdat_parser import SDATParser
from pycalphad_app.database.sdat_registry import SDATRegistry
from pycalphad_app.database.oad_parser import OADParser
from pycalphad_app.database.usgs_conductivity import USGSConductivityEngine
from pycalphad_app.core.tchea_benchmarks import TCHEABenchmarkLibrary
from pycalphad_app.server.cae_daemon import CAEDaemon


class TestNewDatabasesIntegration:

    def test_hea_literature_database_counts(self):
        db = HEALiteratureDatabase.get_instance()
        count = db.count()
        assert count >= 12000, f"Expected at least 12,000 records, got {count}"
        stats = db.get_summary_stats()
        assert stats["total_records"] >= 12000
        assert stats["unique_alloys"] >= 5000
        assert len(stats["top_phases"]) > 0

    def test_hea_literature_search_and_filtering(self):
        db = HEALiteratureDatabase.get_instance()
        res = db.search_alloys(query="AlCoCrFeNi", limit=10)
        assert res["total"] > 0
        assert len(res["items"]) > 0
        first = res["items"][0]
        assert "AlCoCrFeNi" in first["alloy"]
        assert len(first["phase"]) > 0
        assert len(first["doi"]) > 0

        # Test phase filtering
        res_fcc = db.search_alloys(query="CoCrFeNi", phase_filter="FCC", limit=10)
        assert res_fcc["total"] > 0
        for it in res_fcc["items"]:
            assert "fcc" in it["phase"].lower()

    def test_hea_literature_nearest_composition_matching(self):
        db = HEALiteratureDatabase.get_instance()
        # Find nearest to Cantor alloy analogue
        nearest = db.find_nearest("Al0.7CoCrFeNi", top_k=5)
        assert len(nearest) > 0
        top = nearest[0]
        assert top["match_percent"] >= 90.0
        assert "phase" in top
        assert "synthesis_details" in top

    def test_sdat_registry_all_17_databases(self):
        reg = SDATRegistry.get_instance()
        dbs = reg.list_databases()
        assert len(dbs) == 17, f"Expected 17 SDAT databases, got {len(dbs)}"
        filenames = [d["filename"] for d in dbs]
        assert "FeOH.sdat" in filenames
        assert "Gibbsite.sdat" in filenames
        assert "Goethite.sdat" in filenames
        assert "Langmuir.sdat" in filenames
        assert "IonEx.sdat" in filenames

    def test_sdat_surface_speciation_and_pzc(self):
        reg = SDATRegistry.get_instance()
        spec = reg.calculate_surface_speciation("FeOH.sdat", temperature_c=25.0)
        assert "ph_pzc" in spec
        assert 7.0 <= spec["ph_pzc"] <= 9.0  # HFO pzc is ~8.11
        assert len(spec["ph_values"]) == len(spec["surface_charge_density_uC_cm2"])
        # Acidic pH should give positive surface charge
        assert spec["surface_charge_density_uC_cm2"][0] > 0.0
        # Alkaline pH should give negative surface charge
        assert spec["surface_charge_density_uC_cm2"][-1] < 0.0

    def test_oad_parser_industrial_streams(self):
        streams = OADParser.list_all_streams()
        assert len(streams) >= 2
        stream_ids = [s["stream_id"] for s in streams]
        assert "AMD_LION_18" in stream_ids or any("amd" in sid.lower() for sid in stream_ids)
        assert "REE_QUILLINAN_GTO" in stream_ids or any("ree" in sid.lower() for sid in stream_ids)

        amd = next(s for s in streams if "amd" in s["name"].lower() or "lion" in s["name"].lower())
        assert amd["ph"] < 4.0
        assert len(amd["major_inflows"]) > 0

    def test_usgs_conductivity_calculation(self):
        eng = USGSConductivityEngine.get_instance()
        res = eng.calculate_conductivity(temperature_c=25.0, molarities={"Na+": 0.5, "Cl-": 0.5})
        assert res["conductivity_uS_cm"] > 30000.0  # ~0.5M NaCl is ~40,000-50,000 uS/cm
        assert res["conductivity_mS_cm"] > 30.0
        assert res["resistivity_ohm_cm"] > 0.0

    def test_epa_compliance_check(self):
        eng = USGSConductivityEngine.get_instance()
        comp = eng.check_epa_compliance({"Cr+++": 0.5, "Al+++": 0.02})
        assert len(comp) == 2
        cr = next(c for c in comp if "Cr" in c["species"])
        assert cr["status"] == "EXCEEDS_LIMIT"  # 0.5 mg/kg > 0.1 mg/kg limit
        al = next(c for c in comp if "Al" in c["species"])
        assert al["status"] == "COMPLIANT"  # 0.02 mg/kg < 0.05 mg/kg limit

    def test_tchea_benchmarks_collection(self):
        benches = TCHEABenchmarkLibrary.list_benchmarks()
        assert len(benches) >= 4
        cocrfeni = TCHEABenchmarkLibrary.get_benchmark("CoCrFeNi")
        assert cocrfeni is not None
        assert "FCC_A1" in cocrfeni["phases"]
        assert cocrfeni["solidus_c"] == 1340.0

        alx = TCHEABenchmarkLibrary.get_benchmark("AlxCoCrFeNi")
        assert alx is not None
        assert len(alx["al_content_x"]) > 0

    def test_cae_daemon_new_rpc_handlers(self):
        stats = CAEDaemon.handle_get_hea_literature_stats({})
        assert stats["total_records"] >= 12000

        search = CAEDaemon.handle_search_hea_literature({"query": "AlCoCrFeNi", "limit": 2})
        assert len(search["items"]) > 0

        nearest = CAEDaemon.handle_find_nearest_hea_literature({"target": "AlCoCrFeNi", "top_k": 3})
        assert len(nearest["matches"]) == 3

        sdats = CAEDaemon.handle_get_sdat_databases({})
        assert len(sdats["databases"]) == 17

        speciation = CAEDaemon.handle_calculate_sdat_surface_speciation({"filename": "FeOH.sdat"})
        assert speciation["ph_pzc"] > 0.0

        oads = CAEDaemon.handle_get_oad_streams({})
        assert len(oads["streams"]) >= 2

        cond = CAEDaemon.handle_calculate_electrolyte_conductivity({"temperature_c": 25.0})
        assert cond["conductivity_uS_cm"] > 0.0

        tchea = CAEDaemon.handle_get_tchea_benchmarks({})
        assert len(tchea["benchmarks"]) >= 4
