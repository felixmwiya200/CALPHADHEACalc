"""
sdat_registry.py - Registry and Catalog of Surface Complexation and Sorption (.sdat) Databases.
Manages 17 surface complexation datasets covering hydrous ferric oxide (HFO), goethite,
ferrihydrite, gibbsite (aluminum oxide), Langmuir, Freundlich, and ion exchange models.
"""

import os
import glob
from typing import Dict, List, Any, Optional
from pycalphad_app.database.sdat_parser import SDATParser


class SDATRegistry:
    """
    Registry for GWB .sdat surface complexation datasets.
    """

    _METADATA_PROFILES: Dict[str, Dict[str, str]] = {
        "FeOH.sdat": {
            "title": "HFO Dzombak & Morel Standard",
            "description": "Hydrous ferric oxide (HFO) standard two-layer model (Dzombak & Morel 1990) for iron oxide passive films.",
            "category": "Iron Oxides",
        },
        "FeOH+.sdat": {
            "title": "HFO Dzombak & Morel Extended",
            "description": "Hydrous ferric oxide expanded to include estimated heavy metal binding constants.",
            "category": "Iron Oxides",
        },
        "FeOH_minteq.sdat": {
            "title": "HFO EPA MINTEQA2",
            "description": "EPA MINTEQA2 surface complexation compilation with 112 surface species on iron oxyhydroxides.",
            "category": "Iron Oxides",
        },
        "Ferrihydrite_cdmusic.sdat": {
            "title": "Ferrihydrite CD-MUSIC",
            "description": "Charge distribution multi-site complexation (CD-MUSIC) on ferrihydrite by Hiemstra & Van Riemsdijk.",
            "category": "Iron Oxides",
        },
        "Gibbsite.sdat": {
            "title": "Gibbsite Al(OH)3 Standard",
            "description": "Aluminum hydroxide passive oxide film sorption and surface protonation model.",
            "category": "Aluminum Oxides",
        },
        "Gibbsite+.sdat": {
            "title": "Gibbsite Al(OH)3 Extended",
            "description": "Extended aluminum oxide surface complexation reactions including heavy metal binding.",
            "category": "Aluminum Oxides",
        },
        "Gibbsite_minteq.sdat": {
            "title": "Gibbsite MINTEQA2",
            "description": "MINTEQA2 surface complexation reactions for aluminum oxide surfaces.",
            "category": "Aluminum Oxides",
        },
        "Goethite.sdat": {
            "title": "Goethite Two-Layer Model",
            "description": "Two-layer diffuse double layer model for alpha-FeO(OH) passive rust layers.",
            "category": "Iron Oxides",
        },
        "Goethite_cdmusic.sdat": {
            "title": "Goethite CD-MUSIC Model",
            "description": "CD-MUSIC multi-site complexation model on goethite crystallographic planes.",
            "category": "Iron Oxides",
        },
        "Goethite_NaCl.sdat": {
            "title": "Goethite Triple-Layer (NaCl)",
            "description": "Three-layer capacitance model for goethite in concentrated NaCl brine environments.",
            "category": "Iron Oxides",
        },
        "Goethite_NaClO4.sdat": {
            "title": "Goethite Triple-Layer (NaClO4)",
            "description": "Three-layer capacitance model for goethite in perchlorate media.",
            "category": "Iron Oxides",
        },
        "Goethite_P.sdat": {
            "title": "Goethite Phosphate Adsorption",
            "description": "CD-MUSIC modeling of phosphate adsorption and passivation film inhibition.",
            "category": "Iron Oxides",
        },
        "Goethite_Se.sdat": {
            "title": "Goethite Selenite Adsorption",
            "description": "Triple-layer model for selenite and selenate oxyanion sorption on goethite.",
            "category": "Iron Oxides",
        },
        "Langmuir.sdat": {
            "title": "Langmuir Monolayer Isotherm",
            "description": "Standard Langmuir isotherm model for monolayer surface adsorption and inhibitor coverage.",
            "category": "Isotherms",
        },
        "Freundlich.sdat": {
            "title": "Freundlich Heterogeneous Isotherm",
            "description": "Empirical Freundlich exponential isotherm for heterogeneous multi-site adsorption.",
            "category": "Isotherms",
        },
        "IonEx.sdat": {
            "title": "Gaines-Thomas Ion Exchange",
            "description": "Cation exchange capacity (CEC) model using Gaines-Thomas selectivity coefficients.",
            "category": "Ion Exchange",
        },
        "Kd.sdat": {
            "title": "Linear Distribution Coefficient (Kd)",
            "description": "Linear equilibrium partitioning model for chemical species between solution and solid phases.",
            "category": "Partitioning",
        },
    }

    _INSTANCE: Optional["SDATRegistry"] = None

    def __init__(self, databases_dir: Optional[str] = None):
        if databases_dir is None:
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Databases"),
                r"C:\Users\Dell\Documents\Material design\Databases",
            ]
            for c in candidates:
                if os.path.exists(c):
                    databases_dir = c
                    break
            if databases_dir is None:
                databases_dir = os.path.dirname(os.path.abspath(__file__))
        self.databases_dir = databases_dir
        self._parsers: Dict[str, SDATParser] = {}

    @classmethod
    def get_instance(cls) -> "SDATRegistry":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def list_databases(self) -> List[Dict[str, Any]]:
        """
        Lists all available .sdat databases with metadata and counts.
        """
        files = glob.glob(os.path.join(self.databases_dir, "*.sdat"))
        results = []
        for f in sorted(files):
            fname = os.path.basename(f)
            parser = self.get_parser(fname)
            meta = self._METADATA_PROFILES.get(fname, {
                "title": fname,
                "description": f"Surface dataset {fname}",
                "category": "Surface Complexation",
            })
            results.append({
                "filename": fname,
                "title": meta["title"],
                "description": meta["description"],
                "category": meta["category"],
                "surface_type": parser.header.get("surface_type", ""),
                "model_type": parser.header.get("model_type", ""),
                "mineral_count": len(parser.sorbing_minerals),
                "species_count": len(parser.surface_species),
            })
        return results

    def get_parser(self, filename: str) -> SDATParser:
        if filename not in self._parsers:
            filepath = os.path.join(self.databases_dir, filename)
            if not os.path.exists(filepath):
                # Search without path
                matches = glob.glob(os.path.join(self.databases_dir, "**", filename), recursive=True)
                if matches:
                    filepath = matches[0]
            parser = SDATParser(filepath)
            parser.parse(use_cache=True)
            self._parsers[filename] = parser
        return self._parsers[filename]

    def get_database_details(self, filename: str) -> Dict[str, Any]:
        parser = self.get_parser(filename)
        meta = self._METADATA_PROFILES.get(filename, {
            "title": filename,
            "description": f"Surface dataset {filename}",
            "category": "Surface Complexation",
        })
        return {
            "filename": filename,
            "title": meta["title"],
            "description": meta["description"],
            "category": meta["category"],
            "header": parser.header,
            "basis_species": parser.basis_species,
            "sorbing_minerals": parser.sorbing_minerals,
            "surface_species": parser.surface_species,
        }

    def calculate_surface_speciation(
        self,
        filename: str = "FeOH.sdat",
        temperature_c: float = 25.0
    ) -> Dict[str, Any]:
        parser = self.get_parser(filename)
        return parser.calculate_surface_speciation(temperature_c=temperature_c)
