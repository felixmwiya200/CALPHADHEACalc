"""
published_data_repository.py - Repository of Published Literature Materials Properties
Integrates the complete 19-material temperature-dependent property database from published_materials_data.json:
- Pure Aluminum (Al), Al10, Pure Cobalt (Co), AlNi, AlCo
- AlxCoCrFeNi series (AlCoCrFeNi, Al0.3CoCrFeNi, Al0.5CoCrFeNi, Al0.7CoCrFeNi, Al1.5CoCrFeNi, AlCoCrFeNi2.1)
- Cantor and FCC HEAs (CoCrFeNi, CoCrFeMnNi, CoCrNi, Fe50Mn30Co10Cr10, Fe40Mn20Cr20Ni20)
- Refractory HEAs (TiZrHfNbTa, NbMoTaW, MoNbTaVW)

Each material provides validated analytical functions for:
- Density rho(T) [kg/m^3]
- Thermal conductivity k(T) [W/(m*K)]
- Dynamic viscosity eta(T) [mPa*s]
- Surface tension gamma(T) [N/m]
- Young's modulus E(T) [GPa]
- Poisson's ratio nu(T)
- Specific heat Cp(T) [J/(kg*K)]
Complete with Scopus indexing, citations, and peer-reviewed DOI references.
"""

import os
import json
from typing import Dict, Any, List, Optional


class PublishedDataRepository:
    _DATA_CACHE: Optional[Dict[str, Any]] = None

    @classmethod
    def _load_data(cls) -> Dict[str, Any]:
        if cls._DATA_CACHE is None:
            import sys
            candidate_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "App", "published_materials_data.json"),
                os.path.join(getattr(sys, "_MEIPASS", ""), "App", "published_materials_data.json"),
                os.path.join(os.getcwd(), "App", "published_materials_data.json"),
            ]
            json_path = None
            for p in candidate_paths:
                if p and os.path.exists(p):
                    json_path = p
                    break

            if json_path and os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    cls._DATA_CACHE = json.load(f)
            else:
                cls._DATA_CACHE = {}
        return cls._DATA_CACHE

    @classmethod
    def get_available_materials(cls) -> List[str]:
        data = cls._load_data()
        return list(data.keys())

    @classmethod
    def get_material_display_name(cls, mat_id: str) -> str:
        data = cls._load_data()
        mat = data.get(mat_id, {})
        return mat.get("displayName", mat_id.capitalize())

    @classmethod
    def get_material(cls, mat_id: str) -> Optional[Dict[str, Any]]:
        data = cls._load_data()
        return data.get(mat_id)

    @classmethod
    def evaluate_property(cls, mat_id: str, prop_name: str, temp_k: float) -> Optional[float]:
        """Evaluates analytical temperature-dependent property function at given Kelvin temperature."""
        mat = cls.get_material(mat_id)
        if not mat:
            return None
        props = mat.get("properties", {})
        prop = props.get(prop_name)
        if not prop:
            return None

        t_melt = mat.get("meltingPoint_K", 1600.0)
        # Evaluate piecewise equations
        solid_expr = prop.get("solid")
        liquid_expr = prop.get("liquid")

        # Context for eval
        scope = {"T": temp_k, "math": __import__("math")}

        try:
            if temp_k < t_melt and solid_expr:
                return float(eval(solid_expr, {}, scope))
            elif temp_k >= t_melt and liquid_expr:
                return float(eval(liquid_expr, {}, scope))
            elif solid_expr:
                return float(eval(solid_expr, {}, scope))
        except Exception:
            return None
        return None

    @classmethod
    def get_all_citations(cls) -> List[Dict[str, str]]:
        data = cls._load_data()
        citations = []
        for mat_id, mat in data.items():
            name = mat.get("displayName", mat_id)
            for prop_name, pdata in mat.get("properties", {}).items():
                if "doi" in pdata:
                    citations.append({
                        "Material": name,
                        "Property": prop_name.replace("_", " ").title(),
                        "Citation": pdata.get("citation", ""),
                        "Journal": pdata.get("journal", ""),
                        "DOI": pdata.get("doi", ""),
                        "Indexes": ", ".join(pdata.get("indexes", []))
                    })
        return citations
