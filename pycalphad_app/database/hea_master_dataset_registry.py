"""
HEA Master Dataset Registry & Literature Benchmark Manager
===========================================================
Unified registry managing experimental, mechanical, phase stability, and
thermodynamic datasets extracted from leading open-source High-Entropy Alloy
repositories on GitHub:

1. Citrine Informatics MPEA Database (1,545 experimental alloys with yield
   strength, tensile strength, hardness, elongation, modulus, and processing).
2. Peivaste Phase & Thermodynamic Dataset (11,252 alloys with phase structures
   and physical descriptors including VEC, atomic size difference, and mixing entropy).
3. High-Temperature Refractory HEA Mechanical Dataset (668 measurements of yield
   strength from 25 °C to 1200 °C and hardness).
4. Vladimirchizh HEA Synthesis Database (12,427 alloys with detailed arc melting,
   purities, repetitions, and heat treatments).
5. Yan Single-Phase Solid Solution Stability Dataset (1,807 alloys categorized by
   solid solution phase formation).

Author: Felix Mwiya | Materials CAE & Computational Metallurgy
License: Proprietary / CALPHAD Materials Engineering Suite
"""

from __future__ import annotations
import os
import re
import csv
from typing import Dict, List, Optional, Any, Set, Tuple


def parse_formula_elements(formula: str) -> Set[str]:
    """Extract unique elemental constituent symbols from a chemical formula string."""
    if not formula:
        return set()
    cleaned = formula.strip().replace(" ", "")
    tokens = re.findall(r"([A-Z][a-z]?)(?:[\d\.]*)", cleaned)
    # Filter valid chemical symbols (1 to 2 chars)
    return {el for el in tokens if el and el[0].isupper()}


def normalize_formula(formula: str) -> str:
    """Normalize alloy formula for consistent matching."""
    if not formula:
        return ""
    return formula.strip().replace(" ", "")


class HeaMasterDatasetRegistry:
    """
    Centralized high-performance registry for all High-Entropy Alloy datasets.
    """
    _BASE_DIR: Optional[str] = None
    _MPEA_CACHE: Optional[List[Dict[str, Any]]] = None
    _PHASE_CACHE: Optional[List[Dict[str, Any]]] = None
    _HT_MECHANICAL_CACHE: Optional[List[Dict[str, Any]]] = None
    _SYNTHESIS_CACHE: Optional[List[Dict[str, Any]]] = None
    _CORROSION_CACHE: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def get_base_directory(cls) -> str:
        """Locate Databases directory across standard repository layouts."""
        if cls._BASE_DIR and os.path.isdir(cls._BASE_DIR):
            return cls._BASE_DIR

        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Databases"),
            os.path.join(os.getcwd(), "Databases"),
            r"C:\Users\Dell\Documents\Material design\Databases",
        ]
        for p in candidates:
            if os.path.isdir(p):
                cls._BASE_DIR = os.path.abspath(p)
                return cls._BASE_DIR

        fallback = os.path.abspath(r"C:\Users\Dell\Documents\Material design\Databases")
        cls._BASE_DIR = fallback
        return fallback

    # -------------------------------------------------------------------------
    # 1. Citrine Informatics MPEA Mechanical Properties Database
    # -------------------------------------------------------------------------
    @classmethod
    def get_mpea_records(cls) -> List[Dict[str, Any]]:
        """Load and cache Citrine MPEA mechanical properties dataset."""
        if cls._MPEA_CACHE is not None:
            return cls._MPEA_CACHE

        base_dir = cls.get_base_directory()
        csv_path = os.path.join(base_dir, "MPEA_dataset", "MPEA_dataset.csv")
        records: List[Dict[str, Any]] = []

        if not os.path.isfile(csv_path):
            cls._MPEA_CACHE = []
            return []

        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    formula = row.get("FORMULA", "").strip()
                    if not formula:
                        continue

                    def to_float(k: str) -> Optional[float]:
                        v = row.get(k, "")
                        try:
                            return float(v) if v and v.strip() else None
                        except (ValueError, TypeError):
                            return None

                    rec = {
                        "source": "Citrine Informatics MPEA Database",
                        "reference_id": row.get("IDENTIFIER: Reference ID", "").strip(),
                        "formula": formula,
                        "elements": sorted(list(parse_formula_elements(formula))),
                        "microstructure": row.get("PROPERTY: Microstructure", "").strip(),
                        "processing_method": row.get("PROPERTY: Processing method", "").strip(),
                        "phase_structure": row.get("PROPERTY: BCC/FCC/other", "").strip(),
                        "grain_size_um": to_float("PROPERTY: grain size ($\\mu$m)"),
                        "density_exp_g_cm3": to_float("PROPERTY: Exp. Density (g/cm$^3$)"),
                        "density_calc_g_cm3": to_float("PROPERTY: Calculated Density (g/cm$^3$)"),
                        "hardness_hv": to_float("PROPERTY: HV"),
                        "test_type": row.get("PROPERTY: Type of test", "").strip(),
                        "test_temperature_c": to_float("PROPERTY: Test temperature ($^\\circ$C)"),
                        "yield_strength_mpa": to_float("PROPERTY: YS (MPa)"),
                        "uts_mpa": to_float("PROPERTY: UTS (MPa)"),
                        "elongation_pct": to_float("PROPERTY: Elongation (%)"),
                        "plastic_elongation_pct": to_float("PROPERTY: Elongation plastic (%)"),
                        "youngs_modulus_gpa": to_float("PROPERTY: Exp. Young modulus (GPa)"),
                    }
                    records.append(rec)
        except Exception:
            pass

        cls._MPEA_CACHE = records
        return records

    # -------------------------------------------------------------------------
    # 2. Peivaste ML HEA Phase Stability & Physical Properties Database
    # -------------------------------------------------------------------------
    @classmethod
    def get_phase_stability_records(cls) -> List[Dict[str, Any]]:
        """Load and cache Peivaste 11,252 HEA phase classifications."""
        if cls._PHASE_CACHE is not None:
            return cls._PHASE_CACHE

        base_dir = cls.get_base_directory()
        csv_path = os.path.join(base_dir, "ML_HEAs_Phase_Dataset", "Dataset", "dataset11252_79.csv")
        records: List[Dict[str, Any]] = []

        if not os.path.isfile(csv_path):
            cls._PHASE_CACHE = []
            return []

        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    formula = row.get("index", "").strip()
                    if not formula:
                        continue

                    def to_float(k: str) -> Optional[float]:
                        v = row.get(k, "")
                        try:
                            return float(v) if v and v.strip() else None
                        except (ValueError, TypeError):
                            return None

                    phase = row.get("Phase", "").strip()
                    num_el = int(float(row.get("Num_el", "0"))) if row.get("Num_el") else 0

                    rec = {
                        "source": "Peivaste ML HEA Phase Dataset",
                        "formula": formula,
                        "elements": sorted(list(parse_formula_elements(formula))),
                        "num_elements": num_el,
                        "phase_structure": phase,
                        "vec": to_float("VEC"),
                        "mixing_enthalpy_kj_mol": to_float("Enthalpy"),
                        "mixing_entropy_j_mol_k": to_float("entropy"),
                        "atomic_size_difference_delta": to_float("Atomic_radius_calculated_dif"),
                        "electronegativity_difference": to_float("Pauling_EN_div"),
                        "calculated_melting_k": to_float("Melting_point_K"),
                    }
                    records.append(rec)
        except Exception:
            pass

        cls._PHASE_CACHE = records
        return records

    # -------------------------------------------------------------------------
    # 3. High-Temperature Refractory HEA Mechanical Properties
    # -------------------------------------------------------------------------
    @classmethod
    def get_ht_mechanical_records(cls) -> List[Dict[str, Any]]:
        """Load and cache Dovahkiin high-temperature yield strength and hardness."""
        if cls._HT_MECHANICAL_CACHE is not None:
            return cls._HT_MECHANICAL_CACHE

        base_dir = cls.get_base_directory()
        ys_path = os.path.join(base_dir, "representations_hea", "dataset", "yield_strength.csv")
        h_path = os.path.join(base_dir, "representations_hea", "dataset", "hardness.csv")
        records: List[Dict[str, Any]] = []

        # Yield strength table
        if os.path.isfile(ys_path):
            try:
                with open(ys_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        comp = row.get("Composition", "").strip()
                        if not comp:
                            continue
                        try:
                            ys_val = float(row.get("Yield Strength", ""))
                        except (ValueError, TypeError):
                            continue
                        try:
                            t_val = float(row.get("Temperature (Celcius)", 25.0))
                        except (ValueError, TypeError):
                            t_val = 25.0

                        records.append({
                            "source": "High-Temperature RHEA Database",
                            "formula": comp,
                            "elements": sorted(list(parse_formula_elements(comp))),
                            "property_type": "Yield Strength",
                            "yield_strength_mpa": round(ys_val, 1),
                            "test_temperature_c": round(t_val, 1),
                            "condition": row.get("As-cast/other", "").strip(),
                            "phase_type": row.get("Single/MultiPhase", "").strip(),
                        })
            except Exception:
                pass

        # Hardness table
        if os.path.isfile(h_path):
            try:
                with open(h_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        comp = (row.get("Composition") or row.get("\ufeffComposition") or "").strip()
                        if not comp:
                            continue
                        h_str = row.get("HV") or row.get("Hardness") or ""
                        try:
                            h_val = float(h_str)
                        except (ValueError, TypeError):
                            continue

                        records.append({
                            "source": "High-Entropy Alloy Hardness Database",
                            "formula": comp,
                            "elements": sorted(list(parse_formula_elements(comp))),
                            "property_type": "Hardness",
                            "hardness_hv": round(h_val, 1),
                            "test_temperature_c": 25.0,
                            "reference": row.get("Source", "").strip(),
                        })
            except Exception:
                pass

        cls._HT_MECHANICAL_CACHE = records
        return records

    # -------------------------------------------------------------------------
    # 4. Vladimirchizh HEA Synthesis and Metallurgy Database
    # -------------------------------------------------------------------------
    @classmethod
    def get_synthesis_records(cls) -> List[Dict[str, Any]]:
        """Load and cache Vladimirchizh HEA synthesis and metallurgy records."""
        if cls._SYNTHESIS_CACHE is not None:
            return cls._SYNTHESIS_CACHE

        base_dir = cls.get_base_directory()
        csv_path = os.path.join(base_dir, "hea_database-main", "hea_database-main", "database_of_HEAs.csv")
        records: List[Dict[str, Any]] = []

        if not os.path.isfile(csv_path):
            cls._SYNTHESIS_CACHE = []
            return []

        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    alloy = row.get("Alloy", "").strip()
                    if not alloy:
                        continue

                    records.append({
                        "source": "Vladimirchizh HEA Synthesis Database",
                        "formula": alloy,
                        "elements": sorted(list(parse_formula_elements(alloy))),
                        "phase_structure": row.get("Phase", "").strip(),
                        "nb_phases": row.get("Nb of phase", "").strip(),
                        "study_type": row.get("Experimental or theoretical", "").strip(),
                        "experimental_details": row.get("Experimental details", "").strip(),
                        "theoretical_details": row.get("Theoretical details", "").strip(),
                        "special_conditions": row.get("Special conditions", "").strip(),
                        "solution_type": row.get("Type of solution", "").strip(),
                        "paper_id": row.get("Paper", "").strip(),
                    })
        except Exception:
            pass

        cls._SYNTHESIS_CACHE = records
        return records

    # -------------------------------------------------------------------------
    # 5. Global Search & Retrieval API
    # -------------------------------------------------------------------------
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Return comprehensive counts across all extracted HEA datasets."""
        mpea = cls.get_mpea_records()
        phase = cls.get_phase_stability_records()
        ht_mech = cls.get_ht_mechanical_records()
        synthesis = cls.get_synthesis_records()

        ys_count = sum(1 for r in mpea if r.get("yield_strength_mpa") is not None)
        ys_count += sum(1 for r in ht_mech if r.get("yield_strength_mpa") is not None)

        hv_count = sum(1 for r in mpea if r.get("hardness_hv") is not None)
        hv_count += sum(1 for r in ht_mech if r.get("hardness_hv") is not None)

        uts_count = sum(1 for r in mpea if r.get("uts_mpa") is not None)
        mod_count = sum(1 for r in mpea if r.get("youngs_modulus_gpa") is not None)

        unique_elements: Set[str] = set()
        for r in mpea:
            unique_elements.update(r["elements"])
        for r in phase:
            unique_elements.update(r["elements"])

        return {
            "total_mpea_experimental_records": len(mpea),
            "total_phase_stability_records": len(phase),
            "total_high_temperature_mechanical_records": len(ht_mech),
            "total_synthesis_process_records": len(synthesis),
            "total_aggregate_records": len(mpea) + len(phase) + len(ht_mech) + len(synthesis),
            "alloys_with_yield_strength": ys_count,
            "alloys_with_hardness": hv_count,
            "alloys_with_uts": uts_count,
            "alloys_with_youngs_modulus": mod_count,
            "unique_elements_modeled": sorted(list(unique_elements)),
            "element_coverage_count": len(unique_elements),
        }

    @classmethod
    def search_alloys(
        cls,
        query: str = "",
        elements: Optional[List[str]] = None,
        property_filter: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search across all HEA databases by formula, component elements, or property filter.
        property_filter options: 'yield_strength', 'hardness', 'phase', 'synthesis', 'all'.
        """
        results: List[Dict[str, Any]] = []
        clean_q = query.strip().upper() if query else ""
        elem_set = {e.capitalize() for e in elements} if elements else set()

        def matches_filter(rec: Dict[str, Any]) -> bool:
            if not property_filter or property_filter == "all":
                return True
            pf = property_filter.lower()
            if pf == "yield_strength" and rec.get("yield_strength_mpa") is None:
                return False
            if pf == "hardness" and rec.get("hardness_hv") is None:
                return False
            if pf == "phase" and not rec.get("phase_structure"):
                return False
            if pf == "synthesis" and not rec.get("experimental_details"):
                return False
            return True

        def matches_elements(rec: Dict[str, Any]) -> bool:
            if not elem_set:
                return True
            rec_elements = set(rec.get("elements", []))
            # True if all specified search elements are in the alloy
            return elem_set.issubset(rec_elements)

        def matches_query(rec: Dict[str, Any]) -> bool:
            if not clean_q:
                return True
            raw_formula = rec.get("formula", "").upper().replace(" ", "")
            if clean_q in raw_formula:
                return True
            # Match formula without numbers if query contains no digits
            if not any(ch.isdigit() for ch in clean_q):
                stripped_form = re.sub(r"[\d\.]+", "", raw_formula)
                if clean_q in stripped_form:
                    return True
            return False

        # Prioritize rich experimental MPEA and mechanical records first
        for rec in cls.get_mpea_records():
            if matches_query(rec) and matches_elements(rec) and matches_filter(rec):
                results.append(rec)
                if len(results) >= max_results:
                    return results

        for rec in cls.get_ht_mechanical_records():
            if matches_query(rec) and matches_elements(rec) and matches_filter(rec):
                results.append(rec)
                if len(results) >= max_results:
                    return results

        for rec in cls.get_phase_stability_records():
            if matches_query(rec) and matches_elements(rec) and matches_filter(rec):
                results.append(rec)
                if len(results) >= max_results:
                    return results

        for rec in cls.get_synthesis_records():
            if matches_query(rec) and matches_elements(rec) and matches_filter(rec):
                results.append(rec)
                if len(results) >= max_results:
                    return results

        return results

    @classmethod
    def get_mechanical_benchmarks(cls, formula_or_elements: str | List[str]) -> List[Dict[str, Any]]:
        """Retrieve all experimental mechanical test data for an alloy formula or element set."""
        if isinstance(formula_or_elements, list):
            return cls.search_alloys(elements=formula_or_elements, property_filter="yield_strength", max_results=40)
        return cls.search_alloys(query=formula_or_elements, property_filter="yield_strength", max_results=40)

    @classmethod
    def get_temperature_yield_curve(cls, formula: str) -> Dict[str, Any]:
        """
        Extract temperature-dependent yield strength data points (e.g., from 25 °C to 1200 °C)
        for an alloy formula such as Al0.25NbTaTiZr or refractory HEAs.
        """
        clean_q = formula.strip().upper()
        points: List[Dict[str, Any]] = []

        # Check high-temperature mechanical database
        for rec in cls.get_ht_mechanical_records():
            if rec.get("property_type") == "Yield Strength":
                if clean_q in rec.get("formula", "").upper():
                    points.append({
                        "temperature_c": rec["test_temperature_c"],
                        "temperature_k": round(rec["test_temperature_c"] + 273.15, 1),
                        "yield_strength_mpa": rec["yield_strength_mpa"],
                        "condition": rec.get("condition", "As-cast"),
                    })

        # Check Citrine MPEA database
        for rec in cls.get_mpea_records():
            if rec.get("yield_strength_mpa") is not None and clean_q in rec.get("formula", "").upper():
                t_c = rec.get("test_temperature_c", 25.0) or 25.0
                points.append({
                    "temperature_c": round(t_c, 1),
                    "temperature_k": round(t_c + 273.15, 1),
                    "yield_strength_mpa": rec["yield_strength_mpa"],
                    "condition": rec.get("processing_method", "Experimental"),
                })

        points.sort(key=lambda pt: pt["temperature_c"])
        return {
            "formula": formula,
            "data_points": points,
            "count": len(points),
        }
