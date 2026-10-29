"""
test_all_individual_databases.py - Automated Verification of All 14 Individual Material Databases
Tests:
  1. Aluminium Alloy (AluminiumAlloyDatabase)
  2. Magnesium Alloy (MagnesiumAlloyDatabase)
  3. Cast Iron (CastIronDatabase)
  4. General Steel (GeneralSteelDatabase)
  5. Stainless Steel (StainlessSteelDatabase)
  6. Cobalt Alloy (CobaltAlloyDatabase)
  7. Nickel Based Superalloy (NickelSuperalloyDatabase)
  8. NiFe Based Superalloy (NiFeSuperalloyDatabase)
  9. Single Crystal (SingleCrystalDatabase)
 10. Titanium Alloy (TitaniumAlloyDatabase)
 11. Zirconium Alloy (ZirconiumAlloyDatabase)
 12. Solder Alloy (SolderAlloyDatabase)
 13. High Entropy Alloys (UnifiedHEADatabase)
 14. Thermal Spray Coatings (ThermalSprayCoatingDatabase)
"""

import unittest
from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.gui.worker import SolverWorker


class TestAllIndividualDatabases(unittest.TestCase):

    def test_database_registry_completeness(self):
        dbs = MaterialDatabaseSelector.get_database_list()
        self.assertEqual(len(dbs), 14)
        for db_name in dbs:
            spec = MaterialDatabaseSelector.get_spec(db_name)
            self.assertIn("name", spec)
            self.assertIn("category", spec)
            self.assertIn("composition", spec)
            self.assertIn("primary_phases", spec)
            self.assertGreater(len(spec["composition"]), 0)
            self.assertGreater(len(spec["primary_phases"]), 0)

    def test_presets_for_each_database(self):
        dbs = MaterialDatabaseSelector.get_database_list()
        for db_name in dbs:
            presets = MaterialDatabaseSelector.get_presets_for_database(db_name)
            self.assertGreater(len(presets), 0, f"Database {db_name} has no presets")
            for p_name, comp in presets.items():
                self.assertGreater(len(comp), 0, f"Preset {p_name} in {db_name} has empty chemistry")
                self.assertGreater(sum(comp.values()), 0.0)

    def test_xrd_benchmarks_available(self):
        dbs = MaterialDatabaseSelector.get_database_list()
        for db_name in dbs:
            xrd = MaterialDatabaseSelector.get_xrd_benchmark(db_name)
            if xrd:
                self.assertIn("two_theta_deg", xrd)
                self.assertIn("intensity_norm", xrd)
                self.assertIn("peaks", xrd)
                self.assertIn("citation", xrd)
                self.assertIn("doi", xrd)
                self.assertGreater(len(xrd["peaks"]), 0)

    def test_solver_worker_execution_all_14_databases(self):
        dbs = MaterialDatabaseSelector.get_database_list()
        for db_name in dbs:
            spec = MaterialDatabaseSelector.get_spec(db_name)
            comp = spec["composition"]

            worker = SolverWorker(db_name, comp, basis=spec.get("basis", "wt%"),
                                  grain_size_um=25.0, process_type="HVOF")

            results = {}
            def on_finished(res):
                nonlocal results
                results = res

            worker.finished.connect(on_finished)
            worker.run()

            self.assertIn("thermo", results, f"Failed thermo for {db_name}")
            self.assertIn("mechanical", results, f"Failed mechanical for {db_name}")
            self.assertIn("validation_table", results, f"Failed validation for {db_name}")
            self.assertIn("xrd", results, f"Failed XRD for {db_name}")
            self.assertGreater(len(results["validation_table"]), 0, f"No validation rows for {db_name}")


if __name__ == "__main__":
    unittest.main()
