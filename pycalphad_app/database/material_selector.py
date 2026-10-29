"""
material_selector.py - Master Multi-Alloy Database Registry & Router
Coordinates the 14 individual alloy databases:
  1. High Entropy Alloys (UnifiedHEADatabase)
  2. Thermal Spray Coatings (ThermalSprayCoatingDatabase)
  3. Aluminium Alloy (AluminiumAlloyDatabase)
  4. Magnesium Alloy (MagnesiumAlloyDatabase)
  5. Cast Iron (CastIronDatabase)
  6. General Steel (GeneralSteelDatabase)
  7. Stainless Steel (StainlessSteelDatabase)
  8. Cobalt Alloy (CobaltAlloyDatabase)
  9. Nickel Based Superalloy (NickelSuperalloyDatabase)
 10. NiFe Based Superalloy (NiFeSuperalloyDatabase)
 11. Single Crystal (SingleCrystalDatabase)
 12. Titanium Alloy (TitaniumAlloyDatabase)
 13. Zirconium Alloy (ZirconiumAlloyDatabase)
 14. Solder Alloy (SolderAlloyDatabase)
"""

from typing import Dict, List, Any, Optional

from pycalphad_app.database.unified_hea_database import UnifiedHEADatabase
from pycalphad_app.database.thermal_spray_database import ThermalSprayCoatingDatabase
from pycalphad_app.database.aluminium_database import AluminiumAlloyDatabase
from pycalphad_app.database.magnesium_database import MagnesiumAlloyDatabase
from pycalphad_app.database.cast_iron_database import CastIronDatabase
from pycalphad_app.database.general_steel_database import GeneralSteelDatabase
from pycalphad_app.database.stainless_steel_database import StainlessSteelDatabase
from pycalphad_app.database.cobalt_database import CobaltAlloyDatabase
from pycalphad_app.database.nickel_superalloy_database import NickelSuperalloyDatabase
from pycalphad_app.database.nife_superalloy_database import NiFeSuperalloyDatabase
from pycalphad_app.database.single_crystal_database import SingleCrystalDatabase
from pycalphad_app.database.titanium_database import TitaniumAlloyDatabase
from pycalphad_app.database.zirconium_database import ZirconiumAlloyDatabase
from pycalphad_app.database.solder_database import SolderAlloyDatabase


class MaterialDatabaseSelector:
    DATABASES: List[str] = [
        "High Entropy Alloys",
        "Thermal Spray Coatings",
        "Aluminium Alloy",
        "Magnesium Alloy",
        "Cast Iron",
        "General Steel",
        "Stainless Steel",
        "Cobalt Alloy",
        "Nickel Based Superalloy",
        "NiFe Based Superalloy",
        "Single Crystal",
        "Titanium Alloy",
        "Zirconium Alloy",
        "Solder Alloy"
    ]

    MODULE_MAP = {
        "High Entropy Alloys": UnifiedHEADatabase,
        "Thermal Spray Coatings": ThermalSprayCoatingDatabase,
        "Aluminium Alloy": AluminiumAlloyDatabase,
        "Magnesium Alloy": MagnesiumAlloyDatabase,
        "Cast Iron": CastIronDatabase,
        "General Steel": GeneralSteelDatabase,
        "Stainless Steel": StainlessSteelDatabase,
        "Cobalt Alloy": CobaltAlloyDatabase,
        "Nickel Based Superalloy": NickelSuperalloyDatabase,
        "NiFe Based Superalloy": NiFeSuperalloyDatabase,
        "Single Crystal": SingleCrystalDatabase,
        "Titanium Alloy": TitaniumAlloyDatabase,
        "Zirconium Alloy": ZirconiumAlloyDatabase,
        "Solder Alloy": SolderAlloyDatabase
    }

    @classmethod
    def get_database_list(cls) -> List[str]:
        return cls.DATABASES

    @classmethod
    def get_module(cls, db_name: str):
        return cls.MODULE_MAP.get(db_name, UnifiedHEADatabase)

    @classmethod
    def get_spec(cls, db_name: str) -> Dict[str, Any]:
        mod = cls.get_module(db_name)
        if hasattr(mod, "PRESETS") and mod.PRESETS:
            first_key = list(mod.PRESETS.keys())[0]
            first_comp = mod.PRESETS[first_key]
        else:
            first_key = getattr(mod, "NAME", db_name)
            first_comp = {"Ni": 71.61, "Cr": 15.27, "Si": 4.65, "Fe": 4.47, "B": 3.32, "C": 0.68}

        # Normalize fractions
        total = sum(first_comp.values())
        norm_comp = {k: v / total for k, v in first_comp.items()}

        return {
            "name": getattr(mod, "NAME", db_name),
            "basis": getattr(mod, "BASIS", "wt%"),
            "default_alloy": first_key,
            "composition": norm_comp,
            "raw_composition": first_comp,
            "category": getattr(mod, "CATEGORY", "Materials Database"),
            "description": getattr(mod, "DESCRIPTION", ""),
            "primary_phases": getattr(mod, "PRIMARY_PHASES", ["Solid", "Liquid"])
        }

    @classmethod
    def get_presets_for_database(cls, db_name: str) -> Dict[str, Dict[str, float]]:
        mod = cls.get_module(db_name)
        if hasattr(mod, "PRESETS"):
            return mod.PRESETS
        elif db_name == "Thermal Spray Coatings":
            return {
                "Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 (As-Sprayed)": {
                    "Ni": 71.61, "Cr": 15.27, "Si": 4.65, "Fe": 4.47, "B": 3.32, "C": 0.68
                },
                "Colmonoy 6 Standard (Ni-15Cr-4Fe-3.5B-4.5Si-0.7C)": {
                    "Ni": 71.80, "Cr": 15.00, "Si": 4.50, "Fe": 4.00, "B": 3.50, "C": 0.70
                }
            }
        return {}

    @classmethod
    def compare_benchmarks(cls, db_name: str, calc_metrics: Dict[str, Any], preset: Optional[str] = None) -> List[Dict[str, Any]]:
        mod = cls.get_module(db_name)
        if hasattr(mod, "compare_calculated_vs_experimental"):
            try:
                if preset:
                    return mod.compare_calculated_vs_experimental(calc_metrics, preset=preset)
                return mod.compare_calculated_vs_experimental(calc_metrics)
            except TypeError:
                return mod.compare_calculated_vs_experimental(calc_metrics)
        elif hasattr(mod, "compare_calculated_vs_benchmark"):
            alloy_key = UnifiedHEADatabase.identify_alloy_key(calc_metrics.get("composition", {}))
            return mod.compare_calculated_vs_benchmark(alloy_key, calc_metrics)
        return []

    @classmethod
    def get_xrd_benchmark(cls, db_name: str) -> Optional[Dict[str, Any]]:
        mod = cls.get_module(db_name)
        if hasattr(mod, "get_xrd_benchmark"):
            return mod.get_xrd_benchmark()
        return None
