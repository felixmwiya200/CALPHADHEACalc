# -*- coding: utf-8 -*-
"""
tdb_manager.py - CALPHAD Thermodynamic Database Manager & Registry
Discovers, indexes, validates, and routes genuine SGTE .tdb files across
all 14 alloy families in the PyCALPHAD Suite.
"""

import os
from typing import Dict, List, Optional, Tuple, Any

try:
    from pycalphad import Database
    PYCALPHAD_AVAILABLE = True
except Exception:
    PYCALPHAD_AVAILABLE = False


class TDBManager:
    """
    Centralized manager for physical CALPHAD thermodynamic databases (.tdb).
    Indexes local database directories, evaluates elemental coverage, and provides
    instant access to authentic SGTE models for thermodynamic solvers.
    """

    # Primary directories where .tdb files are persisted
    _SEARCH_PATHS = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "tdb")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "App", "databases")),
    ]

    # Explicit mapping of the 14 alloy families to preferred primary & fallback TDB databases
    _FAMILY_TDB_MAP: Dict[str, List[str]] = {
        "General Steel": [
            "fe_c.tdb", "FeC_Brosh_Steel.tdb", "FeMn_Steel.tdb", "GeneralSteel_FeCMnSi.tdb",
            "LibreCALPHAD_mf_steel.tdb", "LibreCALPHAD_mf_steel_3g.tdb", "MatCalc_mc_fe_v2062_clean.tdb",
            "FeNiTi_DeKeyzer2009.tdb", "IMC_Laves_Master.tdb", "SGTE_Unary50.tdb"
        ],
        "Cast Iron": [
            "fe_c.tdb", "FeC_Brosh_Steel.tdb", "LibreCALPHAD_mf_steel.tdb", "MatCalc_mc_fe_v2062_clean.tdb"
        ],
        "Stainless Steel": [
            "CrFeNi_StainlessSteel.tdb", "LibreCALPHAD_mf_steel.tdb", "MatCalc_mc_fe_v2062_clean.tdb",
            "FeCoCrNbTi_HEA.tdb", "IMC_Laves_Master.tdb", "fe_c.tdb"
        ],
        "Nickel Based Superalloy": [
            "ni_al_cr.tdb", "NiAl_Dupin2001.tdb", "AlCrNi_Superalloy.tdb", "NiAl_FCC4SL.tdb",
            "MatCalc_mc_fe_v2062_clean.tdb", "IMC_Laves_Master.tdb"
        ],
        "NiFe Based Superalloy": [
            "ni_al_cr.tdb", "FeCoCrNbTi_HEA.tdb", "CrFeNi_StainlessSteel.tdb",
            "MatCalc_mc_fe_v2062_clean.tdb", "FeNiTi_DeKeyzer2009.tdb", "IMC_Laves_Master.tdb"
        ],
        "Single Crystal": [
            "ni_al_cr.tdb", "NiAl_Dupin2001.tdb", "AlCrNi_Superalloy.tdb",
            "OpenCALPHAD_Al_Co_Cr_Fe_Ni.tdb", "IMC_Laves_Master.tdb"
        ],
        "Titanium Alloy": [
            "ti_al_v.tdb", "CrTiV_TitaniumGhosh.tdb", "TiO_TitaniumOxide.tdb",
            "FeNiTi_DeKeyzer2009.tdb", "IMC_Laves_Master.tdb"
        ],
        "Aluminium Alloy": [
            "COST507_LightAlloys.tdb", "COST507_LightAlloys_Git.tdb", "AlCuMgSi_6000Series.tdb",
            "AlFeSi_CommercialPurity.tdb", "AlFe_Fries.tdb", "AlMg_Zhong.tdb",
            "AlSb_Semiconductor.tdb", "IMC_Laves_Master.tdb"
        ],
        "Magnesium Alloy": [
            "COST507_LightAlloys.tdb", "COST507_LightAlloys_Git.tdb", "MgSiZn_MagnesiumAlloy.tdb",
            "AlMg_Zhong.tdb", "IMC_Laves_Master.tdb"
        ],
        "Cobalt Alloy": [
            "CoV_CobaltAlloy.tdb", "FeCoCrNbTi_HEA.tdb", "MatCalc_mc_fe_v2062_clean.tdb", "IMC_Laves_Master.tdb"
        ],
        "High Entropy Alloys": [
            "FeCoCrNbTi_HEA.tdb", "AlCoCrNi_HEA.tdb", "AlCoCrNi_Liu2016.tdb",
            "OpenCALPHAD_Al_Co_Cr_Fe_Ni.tdb", "Maraging_mc_fecocrnbti.tdb",
            "RHEA_Master_Refractory.tdb", "NbRe_Refractory.tdb",
            "Ti_ElasticPhases.tdb", "CrTiV_TitaniumGhosh.tdb", "IMC_Laves_Master.tdb"
        ],
        "Solder Alloy": [
            "solder_sn_ag_cu.tdb", "NIST-solder.tdb", "AuSn_Solder.tdb",
            "PbSn_Solder.tdb", "AlSb_Semiconductor.tdb", "IMC_Laves_Master.tdb"
        ],
        "Thermal Spray Coatings": [
            "Al2O3_ZrO2_Coating.tdb", "ZrLaYAlO_ThermalBarrier.tdb", "CuO_Oxide.tdb",
            "ni_al_cr.tdb", "WC_Co_Hardmetal.tdb"
        ],
        "Zirconium Alloy": [
            "AlCuZr_ZirconiumAlloy.tdb", "IMC_Laves_Master.tdb", "ZrLaYAlO_ThermalBarrier.tdb"
        ],
    }

    @classmethod
    def get_family_tdbs(cls, family_name: str) -> List[str]:
        """Returns existing TDB filenames registered for the specified alloy family."""
        out: List[str] = []
        for fname in cls._FAMILY_TDB_MAP.get(family_name, []):
            if cls.find_tdb_file(fname):
                out.append(fname)
        return out

    _DATABASE_CACHE: Dict[str, Any] = {}
    _METADATA_CACHE: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_search_directories(cls) -> List[str]:
        """Returns verified existing search directories for TDB databases."""
        return [p for p in cls._SEARCH_PATHS if os.path.isdir(p)]

    @classmethod
    def find_tdb_file(cls, filename: str) -> Optional[str]:
        """Resolves a TDB filename across registered search paths."""
        if os.path.isabs(filename) and os.path.isfile(filename):
            return filename
        for base in cls.get_search_directories():
            candidate = os.path.join(base, filename)
            if os.path.isfile(candidate):
                return candidate
        return None

    @classmethod
    def get_tdb_for_family(cls, family_name: str) -> Optional[str]:
        """
        Returns absolute path to the optimal TDB database for a given alloy family.
        """
        candidates = cls._FAMILY_TDB_MAP.get(family_name, [])
        for fname in candidates:
            resolved = cls.find_tdb_file(fname)
            if resolved:
                return resolved

        # Fallback to HEA or LightAlloys if specific database not found
        for default_name in ["FeCoCrNbTi_HEA.tdb", "COST507_LightAlloys.tdb", "AlCoCrNi_HEA.tdb"]:
            resolved = cls.find_tdb_file(default_name)
            if resolved:
                return resolved
        return None

    @classmethod
    def find_best_tdb_for_elements(cls, elements: List[str]) -> Optional[str]:
        """
        Scans all available TDB databases to find the one with highest element overlap
        and maximum elemental specificity (penalizing bloated super-databases for simple systems).
        """
        target_set = {el.upper() for el in elements if el.upper() not in ["VA", "/-"]}
        if not target_set:
            return None

        best_path: Optional[str] = None
        best_score: Tuple[int, int, int] = (-1, -1, -999)

        for meta in cls.list_all_databases():
            if not meta.get("is_valid", False):
                continue
            db_elems = set(meta.get("elements", []))
            overlap = len(target_set & db_elems)
            if overlap == 0:
                continue
            is_complete = 1 if overlap == len(target_set) else 0
            # Higher overlap is preferred; for equal completeness, tighter element count is preferred
            score = (is_complete, overlap, -abs(len(db_elems) - len(target_set)))
            if score > best_score:
                best_score = score
                best_path = meta["path"]

        return best_path

    @classmethod
    def list_all_databases(cls, validate_pycalphad: bool = True) -> List[Dict[str, Any]]:
        """
        Scans all search paths and returns structured metadata for all unique TDB files.
        """
        discovered: Dict[str, str] = {}
        for base_dir in cls.get_search_directories():
            try:
                for entry in sorted(os.listdir(base_dir)):
                    if entry.lower().endswith(".tdb"):
                        if entry not in discovered:
                            discovered[entry] = os.path.join(base_dir, entry)
            except Exception:
                continue

        results = []
        for filename, full_path in discovered.items():
            meta = cls.get_metadata(full_path, validate_pycalphad=validate_pycalphad)
            results.append(meta)
        return results

    @classmethod
    def get_metadata(cls, tdb_path: str, validate_pycalphad: bool = True) -> Dict[str, Any]:
        """Extracts elements, phases, size, and validity of a TDB file."""
        cache_key = f"{tdb_path}|{int(validate_pycalphad)}"
        if cache_key in cls._METADATA_CACHE:
            return cls._METADATA_CACHE[cache_key]

        fname = os.path.basename(tdb_path)
        size_bytes = os.path.getsize(tdb_path) if os.path.isfile(tdb_path) else 0

        elements: List[str] = []
        phases: List[str] = []
        is_valid = False
        error_msg = ""

        # Rapid header extraction for fast catalog listing
        try:
            with open(tdb_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    clean = line.strip().upper()
                    if clean.startswith("ELEMENT "):
                        parts = clean.split()
                        if len(parts) >= 2:
                            sym = parts[1]
                            if sym not in ["/-", "VA"] and sym not in elements:
                                elements.append(sym)
                    elif clean.startswith("PHASE "):
                        parts = clean.split()
                        if len(parts) >= 2:
                            p_name = parts[1].split(":")[0]
                            if p_name not in phases:
                                phases.append(p_name)
        except Exception as e:
            error_msg = str(e)

        # PyCALPHAD Database validation (skipped during fast catalog enumeration)
        if validate_pycalphad and PYCALPHAD_AVAILABLE:
            try:
                db = Database(tdb_path)
                elements = sorted([e for e in db.elements if e not in ["/-", "VA"]])
                phases = sorted(list(db.phases.keys()))
                is_valid = True
            except Exception as e:
                is_valid = False
                error_msg = str(e).split("\n")[0][:100]
        else:
            is_valid = len(elements) > 0 and len(phases) > 0

        info = {
            "name": fname,
            "path": tdb_path,
            "size_bytes": size_bytes,
            "elements": elements,
            "phases": phases,
            "num_elements": len(elements),
            "num_phases": len(phases),
            "is_valid": is_valid,
            "error": error_msg
        }
        cls._METADATA_CACHE[cache_key] = info
        return info

    @classmethod
    def load_database(cls, tdb_name_or_path: str) -> Optional[Any]:
        """
        Loads and caches a pycalphad.Database instance from file.
        Returns None if pycalphad is unavailable or parsing fails.
        """
        if not PYCALPHAD_AVAILABLE:
            return None

        resolved = cls.find_tdb_file(tdb_name_or_path)
        if not resolved:
            return None

        if resolved in cls._DATABASE_CACHE:
            return cls._DATABASE_CACHE[resolved]

        try:
            db = Database(resolved)
            cls._DATABASE_CACHE[resolved] = db
            return db
        except Exception:
            return None
