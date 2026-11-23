"""
TDAT Database Registry & Multi-Dataset Manager
==============================================
Central registry managing the 8 authoritative thermodynamic datasets in the Databases directory:
1. thermo.com.V8.R6+.tdat (LLNL Wolery EQ3/6 V8.R6+ Master Thermodynamic Database)
2. thermo.tdat (LLNL / GWB Core Thermodynamic Database)
3. thermo_minteq.tdat (EPA MINTEQA2 Environmental & Industrial Database)
4. thermo_nea.tdat (OECD Nuclear Energy Agency TDB: Actinides & Nuclear Materials)
5. thermo_sit.tdat (Specific Ion Interaction Theory SIT High-Salinity Database)
6. thermo_phreeqc.R3.8.9.tdat (USGS PHREEQC R3.8.9 Core Geochemical Database)
7. thermo_wateq4f.tdat (USGS WATEQ4F Trace Element Database)
8. thermo_hmw.tdat (Harvie-Møller-Weare Pitzer Hyper-Saline Brine Database)

Author: Jane, Chief of Staff & Materials CAE Collaborator
License: Proprietary / CALPHAD Materials Engineering Suite
"""

from __future__ import annotations
import os
import glob
from typing import Dict, List, Optional, Any
from pycalphad_app.database.tdat_parser import TDATParser, TDATDatabase, TDATSpecies, TDATMineral


class TDATRegistry:
    """Manages indexing, discovery, and fast access to all .tdat databases."""
    _BASE_DIR = os.path.abspath(r"C:\Users\Dell\Documents\Material design\Databases")
    _CACHE: Dict[str, TDATDatabase] = {}

    _METADATA_PROFILES: Dict[str, Dict[str, str]] = {
        "thermo.com.V8.R6+.tdat": {
            "title": "LLNL EQ3/6 V8.R6+ Master Database",
            "provider": "Lawrence Livermore National Laboratory (Wolery et al.)",
            "scope": "Comprehensive Master Dataset: Transition Metals, Actinides, Rare Earths, Hydrothermal Steam to 300 °C",
            "standard": "SUPCRT92 / CODATA / EQ3/6 V8.R6+",
            "activity_model": "B-dot / Debye-Hückel Extended",
        },
        "thermo.tdat": {
            "title": "GWB Core Thermodynamic Database",
            "provider": "Lawrence Livermore National Laboratory / GWB",
            "scope": "General Metallurgical, Aqueous, and Mineral Equilibrium (0 to 300 °C, 1 to 86 bar)",
            "standard": "SUPCRT92 / Wolery 1990",
            "activity_model": "B-dot",
        },
        "thermo_minteq.tdat": {
            "title": "EPA MINTEQA2 Environmental & Chemical Database",
            "provider": "U.S. EPA / Visual MINTEQ",
            "scope": "Industrial Wastewater, Metal Speciation, Organic/Inorganic Complexes, Precipitation",
            "standard": "EPA MINTEQA2 / Allison et al.",
            "activity_model": "Davies / Debye-Hückel",
        },
        "thermo_nea.tdat": {
            "title": "OECD Nuclear Energy Agency TDB",
            "provider": "OECD Nuclear Energy Agency (NEA) Data Bank",
            "scope": "Peer-Reviewed High-Precision Actinides & Nuclear Materials (U, Np, Pu, Am, Tc, Zr, Ni, Se)",
            "standard": "OECD-NEA Thermochemical Database",
            "activity_model": "Specific Ion Interaction Theory (SIT)",
        },
        "thermo_sit.tdat": {
            "title": "Specific Ion Interaction Theory (SIT) Database",
            "provider": "OECD-NEA / GWB Program",
            "scope": "High-Ionic-Strength Electrolytes, Pickling Baths, Brines, Concentrated Solutions",
            "standard": "SIT / Brønsted-Guggenheim-Scatchard",
            "activity_model": "SIT Activity Model",
        },
        "thermo_phreeqc.R3.8.9.tdat": {
            "title": "USGS PHREEQC R3.8.9 Core Database",
            "provider": "U.S. Geological Survey (Parkhurst & Appelo)",
            "scope": "Aqueous Geochemical, Hydrogeology, Appelo Apparent Molar Volume Pressure Corrections",
            "standard": "USGS PHREEQC Version 3.8.9",
            "activity_model": "Phreeqc WATEQ Debye-Hückel",
        },
        "thermo_wateq4f.tdat": {
            "title": "USGS WATEQ4F Trace Elements Database",
            "provider": "U.S. Geological Survey (Ball & Nordstrom)",
            "scope": "Trace Elements, Heavy Metals, Arsenic, Selenium, Industrial Effluents",
            "standard": "USGS WATEQ4F",
            "activity_model": "Debye-Hückel / Davies",
        },
        "thermo_hmw.tdat": {
            "title": "Harvie-Møller-Weare (HMW) Pitzer Brine Database",
            "provider": "Harvie, Møller, & Weare / USGS",
            "scope": "Hypersaline Evaporation, High-Temperature Salt Solubility, Deep Well Brines",
            "standard": "Pitzer Ion-Interaction Virial Model",
            "activity_model": "Pitzer Virial Expansion",
        },
    }

    @classmethod
    def get_database_dir(cls) -> str:
        return cls._BASE_DIR

    @classmethod
    def list_databases(cls) -> List[Dict[str, Any]]:
        """Lists all 8 databases with summary stats and metadata."""
        results = []
        files = sorted(glob.glob(os.path.join(cls._BASE_DIR, "*.tdat")))
        for f in files:
            base = os.path.basename(f)
            meta = cls._METADATA_PROFILES.get(base, {
                "title": base,
                "provider": "Thermodynamic Consortium",
                "scope": "Thermodynamic Speciation Dataset",
                "standard": "Standard Thermodynamic State",
                "activity_model": "Debye-Hückel",
            })
            size_kb = round(os.path.getsize(f) / 1024.0, 1)

            # Fast peek if already parsed, else return profile
            summary_info: Dict[str, Any] = {}
            if base in cls._CACHE:
                summary_info = cls._CACHE[base].summary()

            results.append({
                "filename": base,
                "filepath": f,
                "size_kb": size_kb,
                "title": meta["title"],
                "provider": meta["provider"],
                "scope": meta["scope"],
                "standard": meta["standard"],
                "activity_model": meta["activity_model"],
                "summary": summary_info
            })
        return results

    @classmethod
    def get_database(cls, db_name: Optional[str] = None) -> TDATDatabase:
        """Retrieves and caches the requested TDATDatabase (defaults to V8.R6+ master)."""
        target = db_name.strip() if db_name else "thermo.com.V8.R6+.tdat"
        if not target.endswith(".tdat"):
            target += ".tdat"

        if target in cls._CACHE:
            return cls._CACHE[target]

        filepath = os.path.join(cls._BASE_DIR, target)
        if not os.path.exists(filepath):
            # Fallback to thermo.tdat
            filepath = os.path.join(cls._BASE_DIR, "thermo.tdat")
            target = "thermo.tdat"

        db = TDATParser.load(filepath)
        cls._CACHE[target] = db
        return db

    @classmethod
    def search_species(cls, query: str, db_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Searches across aqueous species, minerals, redox couples, and gases."""
        db = cls.get_database(db_name)
        q = query.lower().strip()
        hits = []

        # 1. Minerals
        for m_name, m in db.minerals.items():
            if q in m_name.lower() or q in m.formula.lower() or q in m.mineral_type.lower():
                hits.append({
                    "name": m.name,
                    "formula": m.formula,
                    "phase_type": "Mineral",
                    "subtype": m.mineral_type,
                    "mole_wt": round(m.mole_wt, 3),
                    "mole_vol_cc": round(m.mole_vol_cc, 3),
                    "log_k_25c": m.log_k[1] if len(m.log_k) > 1 and m.log_k[1] < 490.0 else None,
                    "log_k_100c": m.log_k[3] if len(m.log_k) > 3 and m.log_k[3] < 490.0 else None,
                    "reaction": cls.format_reaction(m.name, m.stoichiometry, is_mineral=True),
                    "delg0f_kj": m.delg0f_kj,
                })
                if len(hits) >= limit:
                    return hits

        # 2. Aqueous Species
        for a_name, a in db.aqueous_species.items():
            if q in a_name.lower() or q in a.formula.lower():
                hits.append({
                    "name": a.name,
                    "formula": a.formula,
                    "phase_type": "Aqueous Complex",
                    "subtype": f"Charge {a.charge:+d}",
                    "mole_wt": round(a.mole_wt, 3),
                    "mole_vol_cc": 0.0,
                    "log_k_25c": a.log_k[1] if len(a.log_k) > 1 and a.log_k[1] < 490.0 else None,
                    "log_k_100c": a.log_k[3] if len(a.log_k) > 3 and a.log_k[3] < 490.0 else None,
                    "reaction": cls.format_reaction(a.name, a.stoichiometry),
                    "delg0f_kj": None,
                })
                if len(hits) >= limit:
                    return hits

        # 3. Redox Couples
        for r_name, r in db.redox_couples.items():
            if q in r_name.lower() or q in r.formula.lower():
                hits.append({
                    "name": r.name,
                    "formula": r.formula,
                    "phase_type": "Redox Couple",
                    "subtype": f"Charge {r.charge:+d}",
                    "mole_wt": round(r.mole_wt, 3),
                    "mole_vol_cc": 0.0,
                    "log_k_25c": r.log_k[1] if len(r.log_k) > 1 and r.log_k[1] < 490.0 else None,
                    "log_k_100c": r.log_k[3] if len(r.log_k) > 3 and r.log_k[3] < 490.0 else None,
                    "reaction": cls.format_reaction(r.name, r.stoichiometry),
                    "delg0f_kj": None,
                })
                if len(hits) >= limit:
                    return hits

        # 4. Basis Species
        for b_name, b in db.basis_species.items():
            if q in b_name.lower() or q in b.formula.lower():
                hits.append({
                    "name": b.name,
                    "formula": b.formula,
                    "phase_type": "Basis Species",
                    "subtype": f"Charge {b.charge:+d}",
                    "mole_wt": round(b.mole_wt, 3),
                    "mole_vol_cc": 0.0,
                    "log_k_25c": 0.0,
                    "log_k_100c": 0.0,
                    "reaction": f"Primary Component ({b.name})",
                    "delg0f_kj": 0.0,
                })
                if len(hits) >= limit:
                    return hits

        return hits

    @classmethod
    def format_reaction(cls, product_name: str, stoich: Dict[str, float], is_mineral: bool = False) -> str:
        """Formats a balanced chemical dissociation or formation reaction string."""
        reactants = []
        products = []
        for sp, coeff in stoich.items():
            c_abs = abs(coeff)
            c_str = f"{c_abs:.2f} " if abs(c_abs - 1.0) > 0.01 else ""
            if coeff < 0:
                reactants.append(f"{c_str}{sp}")
            else:
                products.append(f"{c_str}{sp}")

        if is_mineral:
            # Mineral dissolution reaction: Mineral + Reactants -> Products
            lhs = f"{product_name}" + (" + " + " + ".join(reactants) if reactants else "")
            rhs = " + ".join(products) if products else "Aqueous Ions"
            return f"{lhs} ⇌ {rhs}"
        else:
            # Species formation: Reactants -> Product + Products
            lhs = " + ".join(reactants) if reactants else "Elements"
            rhs = f"{product_name}" + (" + " + " + ".join(products) if products else "")
            return f"{lhs} ⇌ {rhs}"
