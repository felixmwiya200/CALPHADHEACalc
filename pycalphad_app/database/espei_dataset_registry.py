"""
ESPEI Dataset Registry & Benchmark Thermochemical Manager
==========================================================
Centralized discovery, indexing, and high-performance querying for the
Phases Research Lab ESPEI dataset repository (https://github.com/PhasesResearchLab/ESPEI-datasets).

Provides structured access to:
1. Zero Phase Fraction (ZPF) phase boundary experimental tie-lines (DSC, DTA, metallography).
2. Non-equilibrium thermochemical formation and mixing enthalpies/entropies (DFT / ab initio).
3. Chemical activities and thermochemical measurements.
4. Comprehensive BibTeX literature citation resolution from references.bib.

Author: Felix Mwiya | Materials CAE & Computational Metallurgy
License: Proprietary / CALPHAD Materials Engineering Suite
"""

from __future__ import annotations
import os
import re
import glob
import json
from typing import Dict, List, Optional, Any, Tuple


def parse_bibtex_file(bibtex_path: str) -> Dict[str, Dict[str, str]]:
    """
    Parse a BibTeX file into a structured dictionary keyed by entry key.
    Extracts author, title, journal, year, volume, number, pages, and doi.
    """
    if not os.path.isfile(bibtex_path):
        return {}

    with open(bibtex_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    entries: Dict[str, Dict[str, str]] = {}
    
    # Match entries of form @type{key, ...}
    raw_entries = re.split(r"(?=@\w+\s*\{)", content)
    for raw in raw_entries:
        raw = raw.strip()
        if not raw.startswith("@"):
            continue

        match = re.match(r"@(\w+)\s*\{\s*([^,]+),", raw)
        if not match:
            continue

        entry_type = match.group(1).lower()
        entry_key = match.group(2).strip()

        fields: Dict[str, str] = {
            "type": entry_type,
            "key": entry_key,
        }

        # Extract key-value pairs inside entry
        body = raw[match.end():]
        # Match field = {value} or field = "value" or field = number
        field_matches = re.findall(
            r'([a-zA-Z_]+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|(\d+))',
            body,
            re.DOTALL
        )
        for f_name, v_brace, v_quote, v_num in field_matches:
            val = (v_brace or v_quote or v_num or "").strip()
            # Clean braces and excessive whitespace
            val = re.sub(r"\s+", " ", val.replace("{", "").replace("}", "")).strip()
            fields[f_name.lower()] = val

        # Format a clean academic citation string
        author = fields.get("author", "Unknown Author")
        year = fields.get("year", "")
        journal = fields.get("journal", fields.get("booktitle", fields.get("publisher", "")))
        title = fields.get("title", "")

        first_author = author.split(" and ")[0].split(",")[0].strip() if author else "Unknown"
        short_citation = f"{first_author} et al. ({year})" if year else first_author
        fields["short_citation"] = short_citation
        fields["formatted_citation"] = f"{author}, \"{title}\", {journal} ({year}).".strip()

        entries[entry_key] = fields

    return entries


class EspeiDatasetRegistry:
    """
    Manages indexing, discovery, and fast querying of ESPEI thermodynamic datasets.
    """
    _BASE_DIR: Optional[str] = None
    _SYSTEMS_CACHE: Optional[List[Dict[str, Any]]] = None
    _DATASETS_CACHE: Optional[List[Dict[str, Any]]] = None
    _BIBTEX_CACHE: Optional[Dict[str, Dict[str, str]]] = None

    @classmethod
    def get_base_directory(cls) -> str:
        """Locate the root ESPEI-datasets folder across standard paths."""
        if cls._BASE_DIR and os.path.isdir(cls._BASE_DIR):
            return cls._BASE_DIR

        candidate_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Databases", "ESPEI-datasets"),
            os.path.join(os.getcwd(), "Databases", "ESPEI-datasets"),
            r"C:\Users\Dell\Documents\Material design\Databases\ESPEI-datasets",
        ]

        for p in candidate_paths:
            if os.path.isdir(p):
                cls._BASE_DIR = os.path.abspath(p)
                return cls._BASE_DIR

        # Fallback to default
        fallback = os.path.abspath(r"C:\Users\Dell\Documents\Material design\Databases\ESPEI-datasets")
        cls._BASE_DIR = fallback
        return fallback

    @classmethod
    def get_references(cls) -> Dict[str, Dict[str, str]]:
        """Retrieve parsed BibTeX references."""
        if cls._BIBTEX_CACHE is None:
            base_dir = cls.get_base_directory()
            bib_file = os.path.join(base_dir, "references.bib")
            cls._BIBTEX_CACHE = parse_bibtex_file(bib_file)
        return cls._BIBTEX_CACHE

    @classmethod
    def get_all_datasets(cls, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load and index all JSON dataset files."""
        if cls._DATASETS_CACHE is not None and not force_reload:
            return cls._DATASETS_CACHE

        base_dir = cls.get_base_directory()
        datasets_dir = os.path.join(base_dir, "datasets")
        references = cls.get_references()

        if not os.path.isdir(datasets_dir):
            cls._DATASETS_CACHE = []
            return []

        pattern = os.path.join(datasets_dir, "**", "*.json")
        json_paths = glob.glob(pattern, recursive=True)

        loaded_datasets: List[Dict[str, Any]] = []

        for f_path in json_paths:
            try:
                rel = os.path.relpath(f_path, datasets_dir)
                parts = rel.split(os.sep)
                if len(parts) < 3:
                    continue

                tier_folder = parts[0]  # e.g., '2-binary' or '3-ternary'
                system_folder = parts[1]  # e.g., 'Al-Ni'
                category_folder = parts[2]  # 'zpf', 'non-equilibrium-thermochemical', 'activity'

                with open(f_path, "r", encoding="utf-8", errors="ignore") as fp:
                    data = json.load(fp)

                ref_key = data.get("reference", "")
                citation = references.get(ref_key, {})

                components = [c.capitalize() if len(c) > 1 else c for c in data.get("components", [])]
                phases = data.get("phases", [])
                output_prop = data.get("output", "")
                conditions = data.get("conditions", {})
                values = data.get("values", [])

                dataset_record = {
                    "file_path": os.path.abspath(f_path),
                    "file_name": os.path.basename(f_path),
                    "tier": "ternary" if "3-ternary" in tier_folder else "binary",
                    "system": system_folder,
                    "category": category_folder,
                    "components": components,
                    "phases": phases,
                    "output": output_prop,
                    "conditions": conditions,
                    "values": values,
                    "reference_key": ref_key,
                    "citation": citation.get("formatted_citation", ref_key),
                    "short_citation": citation.get("short_citation", ref_key),
                    "comment": data.get("comment", ""),
                }
                loaded_datasets.append(dataset_record)
            except Exception:
                continue

        cls._DATASETS_CACHE = loaded_datasets
        return loaded_datasets

    @classmethod
    def list_systems(cls) -> List[Dict[str, Any]]:
        """
        Aggregate and summarize all available elemental systems in the ESPEI dataset.
        """
        if cls._SYSTEMS_CACHE is not None:
            return cls._SYSTEMS_CACHE

        datasets = cls.get_all_datasets()
        system_map: Dict[str, Dict[str, Any]] = {}

        for d in datasets:
            sys_name = d["system"]
            if sys_name not in system_map:
                elements = [e.capitalize() for e in sys_name.split("-")]
                system_map[sys_name] = {
                    "system": sys_name,
                    "elements": elements,
                    "tier": d["tier"],
                    "dataset_count": 0,
                    "zpf_dataset_count": 0,
                    "thermochemical_dataset_count": 0,
                    "outputs": set(),
                    "phases": set(),
                    "references": set(),
                }

            entry = system_map[sys_name]
            entry["dataset_count"] += 1
            if d["category"] == "zpf":
                entry["zpf_dataset_count"] += 1
            else:
                entry["thermochemical_dataset_count"] += 1

            if d["output"]:
                entry["outputs"].add(d["output"])
            for p in d["phases"]:
                entry["phases"].add(p)
            if d["reference_key"]:
                entry["references"].add(d["short_citation"])

        # Format sets into sorted lists
        summaries: List[Dict[str, Any]] = []
        for sys_name, info in system_map.items():
            summaries.append({
                "system": info["system"],
                "elements": info["elements"],
                "tier": info["tier"],
                "dataset_count": info["dataset_count"],
                "zpf_dataset_count": info["zpf_dataset_count"],
                "thermochemical_dataset_count": info["thermochemical_dataset_count"],
                "outputs": sorted(list(info["outputs"])),
                "phases": sorted(list(info["phases"])),
                "references": sorted(list(info["references"])),
            })

        summaries.sort(key=lambda s: (s["tier"] != "binary", s["system"]))
        cls._SYSTEMS_CACHE = summaries
        return summaries

    @classmethod
    def get_datasets_for_system(
        cls,
        system_or_elements: str | List[str],
        category: Optional[str] = None,
        output_prop: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter datasets for a given chemical system (e.g., 'Al-Ni' or ['Al', 'Ni'])."""
        datasets = cls.get_all_datasets()

        if isinstance(system_or_elements, list):
            target_sys = "-".join(sorted(system_or_elements, key=lambda x: x.upper())).upper()
        else:
            target_sys = system_or_elements.replace(" ", "").upper()

        results = []
        for d in datasets:
            current_sys = d["system"].upper()
            # Normalize hyphenated matching
            if current_sys != target_sys:
                # Check unordered match of components
                d_comps = sorted([c.upper() for c in d["components"]])
                t_comps = sorted(target_sys.split("-"))
                if d_comps != t_comps:
                    continue

            if category and d["category"] != category:
                continue
            if output_prop and d["output"].upper() != output_prop.upper():
                continue

            results.append(d)

        return results

    @classmethod
    def get_zpf_phase_boundaries(cls, system_or_elements: str | List[str]) -> List[Dict[str, Any]]:
        """
        Extract and flatten Zero Phase Fraction (ZPF) phase boundary tie-line coordinates.
        Returns a list of structured data points containing:
        - temperature_k: Temperature in Kelvin
        - temperature_c: Temperature in Celsius
        - phase: Phase name
        - element: Independent component symbol
        - composition: Mole fraction of component
        - reference: Citation reference
        - source_file: Originating JSON file
        """
        zpf_datasets = cls.get_datasets_for_system(system_or_elements, category="zpf")
        points: List[Dict[str, Any]] = []

        for d in zpf_datasets:
            conds = d.get("conditions", {})
            t_data = conds.get("T", [])
            if isinstance(t_data, (int, float)):
                t_list = [float(t_data)]
            elif isinstance(t_data, list):
                t_list = [float(t) for t in t_data]
            else:
                t_list = []

            values = d.get("values", [])
            ref_str = d.get("short_citation") or d.get("reference_key", "")
            f_name = d.get("file_name", "")

            # Match values against temperature conditions
            for idx, eq_group in enumerate(values):
                t_k = t_list[idx] if idx < len(t_list) else (t_list[0] if t_list else 298.15)
                t_c = t_k - 273.15

                if not isinstance(eq_group, list):
                    continue

                for phase_entry in eq_group:
                    # Expected format: [phase_name, [comp_elements], [comp_fractions]]
                    if not isinstance(phase_entry, list) or len(phase_entry) < 3:
                        continue

                    phase_name = str(phase_entry[0])
                    comp_elements = phase_entry[1] if isinstance(phase_entry[1], list) else []
                    comp_fractions = phase_entry[2] if isinstance(phase_entry[2], list) else []

                    for el, frac in zip(comp_elements, comp_fractions):
                        try:
                            val_float = float(frac)
                            points.append({
                                "system": d["system"],
                                "temperature_k": round(t_k, 2),
                                "temperature_c": round(t_c, 2),
                                "phase": phase_name,
                                "element": el.capitalize(),
                                "composition": round(val_float, 4),
                                "reference": ref_str,
                                "source_file": f_name,
                            })
                        except (ValueError, TypeError):
                            continue

        # Sort chronologically by temperature
        points.sort(key=lambda p: (p["temperature_k"], p["phase"], p["element"]))
        return points

    @classmethod
    def get_thermochemical_points(
        cls,
        system_or_elements: str | List[str],
        output_prop: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract and flatten thermochemical formation and mixing enthalpy/entropy data points.
        Returns a list of data points containing:
        - property: HM_MIX, HM_FORM, SM_MIX, SM_FORM, CPM, etc.
        - temperature_k: Temperature in Kelvin
        - phase: Phase name
        - value_si: Thermodynamic quantity in SI units (J/mol or J/(mol*K))
        - occupancy: Elemental or sublattice mole fraction if applicable
        - reference: Citation reference
        """
        datasets = cls.get_datasets_for_system(system_or_elements, output_prop=output_prop)
        points: List[Dict[str, Any]] = []

        for d in datasets:
            if d["category"] == "zpf":
                continue

            conds = d.get("conditions", {})
            t_val = conds.get("T", 298.15)
            t_k = float(t_val) if isinstance(t_val, (int, float)) else 298.15

            prop = d.get("output", "")
            phases = d.get("phases", ["UNKNOWN"])
            phase_name = phases[0] if phases else "UNKNOWN"
            ref_str = d.get("short_citation") or d.get("reference_key", "")
            f_name = d.get("file_name", "")

            # Derive units from property identifier
            unit = "J/mol" if "H" in prop else ("J/(mol*K)" if "S" in prop or "CP" in prop else "dimensionless")

            # Extract raw values (frequently nested in sublattice structures)
            def extract_numbers(val_obj: Any) -> List[float]:
                num_list = []
                if isinstance(val_obj, (int, float)):
                    num_list.append(float(val_obj))
                elif isinstance(val_obj, list):
                    for sub in val_obj:
                        num_list.extend(extract_numbers(sub))
                return num_list

            extracted_vals = extract_numbers(d.get("values", []))
            for v in extracted_vals:
                points.append({
                    "system": d["system"],
                    "property": prop,
                    "temperature_k": round(t_k, 2),
                    "phase": phase_name,
                    "value_si": round(v, 2),
                    "unit": unit,
                    "reference": ref_str,
                    "source_file": f_name,
                })

        return points

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Return global repository statistics."""
        systems = cls.list_systems()
        datasets = cls.get_all_datasets()
        references = cls.get_references()

        binary_systems = [s for s in systems if s["tier"] == "binary"]
        ternary_systems = [s for s in systems if s["tier"] == "ternary"]

        zpf_count = sum(s["zpf_dataset_count"] for s in systems)
        thermo_count = sum(s["thermochemical_dataset_count"] for s in systems)

        all_phases = set()
        for s in systems:
            all_phases.update(s["phases"])

        return {
            "total_datasets": len(datasets),
            "total_systems": len(systems),
            "binary_systems_count": len(binary_systems),
            "ternary_systems_count": len(ternary_systems),
            "total_references": len(references),
            "zpf_dataset_count": zpf_count,
            "thermochemical_dataset_count": thermo_count,
            "unique_phases_count": len(all_phases),
            "systems": [s["system"] for s in systems],
        }
