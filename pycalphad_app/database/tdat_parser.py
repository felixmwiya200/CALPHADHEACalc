"""
TDAT Thermodynamic Database Parser
==================================
High-performance parser for Geochemist's Workbench / EQ3/6 .tdat thermodynamic datasets.
Extracts elements, basis species, redox couples, aqueous species, minerals, gases,
and their temperature-dependent equilibrium constants (log K) across the standard
hydrothermal steam saturation grid [0, 25, 60, 100, 150, 200, 250, 300] °C.

Author: Felix Mwiya | Materials CAE & Computational Metallurgy
License: Proprietary / CALPHAD Materials Engineering Suite
"""

from __future__ import annotations
import os
import re
import pickle
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("TDATParser")


class TDATSpecies:
    """Represents a basis species, redox species, or aqueous complex."""
    def __init__(self, name: str, charge: int, ion_size_a: float, mole_wt: float,
                 stoichiometry: Dict[str, float], log_k: List[float],
                 phase_type: str = "Aqueous", formula: str = ""):
        self.name: str = name
        self.charge: int = charge
        self.ion_size_a: float = ion_size_a
        self.mole_wt: float = mole_wt
        self.stoichiometry: Dict[str, float] = stoichiometry
        self.log_k: List[float] = log_k
        self.phase_type: str = phase_type
        self.formula: str = formula or name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "charge": self.charge,
            "ion_size_a": self.ion_size_a,
            "mole_wt": self.mole_wt,
            "stoichiometry": self.stoichiometry,
            "log_k": self.log_k,
            "phase_type": self.phase_type,
            "formula": self.formula,
        }


class TDATMineral:
    """Represents a solid crystalline mineral, oxide, hydroxide, or intermetallic phase."""
    def __init__(self, name: str, formula: str, mineral_type: str, mole_vol_cc: float,
                 mole_wt: float, stoichiometry: Dict[str, float], log_k: List[float],
                 delg0f_kj: Optional[float] = None, delh0f_kj: Optional[float] = None):
        self.name: str = name
        self.formula: str = formula or name
        self.mineral_type: str = mineral_type or "Mineral"
        self.mole_vol_cc: float = mole_vol_cc
        self.mole_wt: float = mole_wt
        self.stoichiometry: Dict[str, float] = stoichiometry
        self.log_k: List[float] = log_k
        self.delg0f_kj: Optional[float] = delg0f_kj
        self.delh0f_kj: Optional[float] = delh0f_kj

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "formula": self.formula,
            "mineral_type": self.mineral_type,
            "mole_vol_cc": self.mole_vol_cc,
            "mole_wt": self.mole_wt,
            "stoichiometry": self.stoichiometry,
            "log_k": self.log_k,
            "delg0f_kj": self.delg0f_kj,
            "delh0f_kj": self.delh0f_kj,
        }


class TDATGas:
    """Represents a gas-phase species."""
    def __init__(self, name: str, formula: str, mole_vol_cc: float, mole_wt: float,
                 stoichiometry: Dict[str, float], log_k: List[float]):
        self.name: str = name
        self.formula: str = formula or name
        self.mole_vol_cc: float = mole_vol_cc
        self.mole_wt: float = mole_wt
        self.stoichiometry: Dict[str, float] = stoichiometry
        self.log_k: List[float] = log_k

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "formula": self.formula,
            "mole_vol_cc": self.mole_vol_cc,
            "mole_wt": self.mole_wt,
            "stoichiometry": self.stoichiometry,
            "log_k": self.log_k,
        }


class TDATDatabase:
    """In-memory parsed representation of a .tdat thermodynamic dataset."""
    def __init__(self, filename: str):
        self.filename: str = filename
        self.basename: str = os.path.basename(filename)
        self.dataset_format: str = ""
        self.activity_model: str = ""
        self.fugacity_model: str = ""
        self.temperatures_c: List[float] = [0.0, 25.0, 60.0, 100.0, 150.0, 200.0, 250.0, 300.0]
        self.pressures_bar: List[float] = [1.0134, 1.0134, 1.0134, 1.0134, 4.76, 15.549, 39.776, 85.927]
        self.elements: Dict[str, Dict[str, Any]] = {}
        self.basis_species: Dict[str, TDATSpecies] = {}
        self.redox_couples: Dict[str, TDATSpecies] = {}
        self.aqueous_species: Dict[str, TDATSpecies] = {}
        self.minerals: Dict[str, TDATMineral] = {}
        self.gases: Dict[str, TDATGas] = {}
        self.oxides: Dict[str, str] = {}

    def summary(self) -> Dict[str, Any]:
        return {
            "basename": self.basename,
            "dataset_format": self.dataset_format,
            "activity_model": self.activity_model,
            "fugacity_model": self.fugacity_model,
            "temperatures_c": self.temperatures_c,
            "num_elements": len(self.elements),
            "num_basis": len(self.basis_species),
            "num_redox": len(self.redox_couples),
            "num_aqueous": len(self.aqueous_species),
            "num_minerals": len(self.minerals),
            "num_gases": len(self.gases),
            "num_oxides": len(self.oxides),
        }


class TDATParser:
    """Parser with disk-caching for sub-5 millisecond loads."""
    _CACHE_DIR = os.path.join(os.path.dirname(__file__), ".tdat_cache")

    @classmethod
    def load(cls, filepath: str, force_reparse: bool = False) -> TDATDatabase:
        os.makedirs(cls._CACHE_DIR, exist_ok=True)
        base = os.path.basename(filepath)
        cache_path = os.path.join(cls._CACHE_DIR, f"{base}.pkl")

        if not force_reparse and os.path.exists(cache_path):
            try:
                src_mtime = os.path.getmtime(filepath)
                cache_mtime = os.path.getmtime(cache_path)
                if cache_mtime >= src_mtime:
                    with open(cache_path, "rb") as fp:
                        return pickle.load(fp)
            except Exception as e:
                logger.warning(f"Could not load cache for {base}: {e}")

        db = cls._parse_file(filepath)
        try:
            with open(cache_path, "wb") as fp:
                pickle.dump(db, fp, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logger.warning(f"Failed to cache {base}: {e}")
        return db

    @classmethod
    def _parse_file(cls, filepath: str) -> TDATDatabase:
        db = TDATDatabase(filepath)
        with open(filepath, "r", encoding="latin-1") as fp:
            lines = [l.rstrip("\r\n") for l in fp]

        n_lines = len(lines)
        idx = 0

        # Parse header keywords
        while idx < min(50, n_lines):
            l = lines[idx].strip()
            l_lower = l.lower()
            if l_lower.startswith("dataset format:"):
                db.dataset_format = l.split(":", 1)[1].strip()
            elif l_lower.startswith("activity model:"):
                db.activity_model = l.split(":", 1)[1].strip()
            elif l_lower.startswith("fugacity model:"):
                db.fugacity_model = l.split(":", 1)[1].strip()
            elif l_lower.startswith("* temperatures"):
                idx += 1
                t_vals = []
                while idx < n_lines and not lines[idx].strip().startswith("*") and not lines[idx].strip().startswith("Tmin"):
                    row = lines[idx].strip()
                    if row:
                        t_vals.extend([float(v) for v in row.split() if re.match(r"^-?\d+\.?\d*", v)])
                    idx += 1
                    if len(t_vals) >= 8:
                        break
                if t_vals:
                    db.temperatures_c = t_vals[:8]
                continue
            elif l_lower.startswith("* pressures"):
                idx += 1
                p_vals = []
                while idx < n_lines and not lines[idx].strip().startswith("*") and not lines[idx].strip().startswith("Pmin"):
                    row = lines[idx].strip()
                    if row:
                        p_vals.extend([float(v) for v in row.split() if re.match(r"^-?\d+\.?\d*", v)])
                    idx += 1
                    if len(p_vals) >= 8:
                        break
                if p_vals:
                    db.pressures_bar = p_vals[:8]
                continue
            idx += 1

        # Search for major sections by pattern
        idx = 0
        section_re = re.compile(r"^\s*(\d+)\s+([a-zA-Z\s]+)$")
        while idx < n_lines:
            line = lines[idx].strip()
            m = section_re.match(line)
            if m:
                count = int(m.group(1))
                sec_name = m.group(2).strip().lower()

                if "element" in sec_name and "in species" not in sec_name:
                    idx = cls._parse_elements(lines, idx + 1, count, db)
                    continue
                elif "basis species" in sec_name:
                    idx = cls._parse_basis_species(lines, idx + 1, count, db)
                    continue
                elif "redox couples" in sec_name:
                    idx = cls._parse_redox_couples(lines, idx + 1, count, db)
                    continue
                elif "aqueous species" in sec_name:
                    idx = cls._parse_aqueous_species(lines, idx + 1, count, db)
                    continue
                elif "minerals" in sec_name:
                    idx = cls._parse_minerals(lines, idx + 1, count, db)
                    continue
                elif "gases" in sec_name:
                    idx = cls._parse_gases(lines, idx + 1, count, db)
                    continue
                elif "oxides" in sec_name:
                    idx = cls._parse_oxides(lines, idx + 1, count, db)
                    continue
            idx += 1

        return db

    @classmethod
    def _parse_elements(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        n = len(lines)
        parsed = 0
        elem_re = re.compile(r"^([A-Za-z]+)\s+\(([A-Za-z]{1,2})\s*\)\s+mole wt\.=\s*([\d\.]+)\s*g")
        while idx < n and parsed < count:
            l = lines[idx].strip()
            if l == "-end-":
                idx += 1
                break
            m = elem_re.match(l)
            if m:
                name = m.group(1).strip()
                sym = m.group(2).strip()
                wt = float(m.group(3))
                db.elements[sym] = {"symbol": sym, "name": name, "mole_wt": wt}
                parsed += 1
            idx += 1
        return idx

    @classmethod
    def _parse_basis_species(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        n = len(lines)
        parsed = 0
        while idx < n and parsed < count:
            line = lines[idx].strip()
            if line == "-end-":
                idx += 1
                break
            if line and not line.startswith("*"):
                name = line.split()[0]
                idx += 1
                charge = 0
                ion_size = 3.0
                mole_wt = 0.0
                if idx < n and "charge=" in lines[idx]:
                    cl = lines[idx]
                    cm = re.search(r"charge=\s*(-?\d+)", cl)
                    ism = re.search(r"ion size=\s*(-?[\d\.]+)", cl)
                    mwm = re.search(r"mole wt\.=\s*([\d\.]+)", cl)
                    if cm: charge = int(cm.group(1))
                    if ism: ion_size = float(ism.group(1))
                    if mwm: mole_wt = float(mwm.group(1))
                    idx += 1

                stoich: Dict[str, float] = {}
                if idx < n and "elements in species" in lines[idx]:
                    idx += 1
                    while idx < n and lines[idx].strip() and not lines[idx].strip().startswith("*") and "species in reaction" not in lines[idx] and "charge=" not in lines[idx]:
                        parts = lines[idx].split()
                        i = 0
                        while i + 1 < len(parts):
                            try:
                                coeff = float(parts[i])
                                el = parts[i+1]
                                stoich[el] = coeff
                                i += 2
                            except ValueError:
                                i += 1
                        idx += 1
                        if idx < n and ("charge=" in lines[idx] or lines[idx].strip() == "-end-"):
                            break

                sp = TDATSpecies(name, charge, ion_size, mole_wt, stoich, [0.0]*8, phase_type="Basis")
                db.basis_species[name] = sp
                parsed += 1
                continue
            idx += 1
        return idx

    @classmethod
    def _parse_species_block(cls, lines: List[str], idx: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Parses a generic reaction-based block (redox, aqueous, mineral, or gas)."""
        n = len(lines)
        while idx < n and (not lines[idx].strip() or lines[idx].strip().startswith("*")):
            idx += 1
        if idx >= n or lines[idx].strip() == "-end-":
            return None, idx

        raw_head = lines[idx].strip()
        parts = raw_head.split()
        name = parts[0]
        meta_type = ""
        if "type=" in raw_head:
            meta_type = raw_head.split("type=", 1)[1].strip()

        idx += 1
        charge = 0
        ion_size = 3.0
        mole_wt = 0.0
        mole_vol = 0.0
        formula = ""
        delg0f: Optional[float] = None
        delh0f: Optional[float] = None

        # Read property lines before reaction
        while idx < n:
            l = lines[idx].strip()
            if not l:
                idx += 1
                continue
            if "formula=" in l:
                formula = l.split("formula=", 1)[1].strip()
                idx += 1
                continue
            if "charge=" in l:
                cm = re.search(r"charge=\s*(-?\d+)", l)
                ism = re.search(r"ion size=\s*(-?[\d\.]+)", l)
                mwm = re.search(r"mole wt\.=\s*([\d\.]+)", l)
                if cm: charge = int(cm.group(1))
                if ism: ion_size = float(ism.group(1))
                if mwm: mole_wt = float(mwm.group(1))
                idx += 1
                continue
            if "mole vol.=" in l:
                mvm = re.search(r"mole vol\.=\s*([\d\.]+)", l)
                mwm = re.search(r"mole wt\.=\s*([\d\.]+)", l)
                if mvm: mole_vol = float(mvm.group(1))
                if mwm: mole_wt = float(mwm.group(1))
                idx += 1
                continue
            if "species in reaction" in l:
                idx += 1
                break
            if l.startswith("*"):
                idx += 1
                continue
            # Next block start
            break

        # Read reaction stoichiometry
        stoich: Dict[str, float] = {}
        log_k_vals: List[float] = []

        while idx < n:
            l = lines[idx].strip()
            if not l:
                idx += 1
                continue
            if l.startswith("*"):
                # Check for delG0f or delH0f annotations in comments
                g_m = re.search(r"delG0f\s*=\s*(-?[\d\.]+)\s*(kj|kcal)/mol", l, re.IGNORECASE)
                if g_m:
                    val = float(g_m.group(1))
                    unit = g_m.group(2).lower()
                    delg0f = val if unit == "kj" else val * 4.184
                h_m = re.search(r"delH0f\s*=\s*(-?[\d\.]+)\s*(kj|kcal)/mol", l, re.IGNORECASE)
                if h_m:
                    val = float(h_m.group(1))
                    unit = h_m.group(2).lower()
                    delh0f = val if unit == "kj" else val * 4.184
                idx += 1
                continue

            # Check if this line is log K numbers (e.g. 4 numbers per line)
            tokens = l.split()
            all_floats = True
            try:
                nums = [float(x) for x in tokens]
            except ValueError:
                all_floats = False

            if all_floats and len(tokens) >= 2 and len(stoich) > 0:
                log_k_vals.extend(nums)
                idx += 1
                if len(log_k_vals) >= 8:
                    break
                continue

            # Stoichiometry line (e.g. "-4.000 H+  2.000 Ba++  3.000 SiO2(aq)")
            i = 0
            has_species = False
            while i + 1 < len(tokens):
                try:
                    coeff = float(tokens[i])
                    sp_name = tokens[i+1]
                    stoich[sp_name] = coeff
                    i += 2
                    has_species = True
                except ValueError:
                    i += 1
            if has_species:
                idx += 1
                continue

            # Reached next item
            break

        # Read any remaining log K values or comments for this item
        while idx < n and len(log_k_vals) < 8:
            l = lines[idx].strip()
            if not l:
                idx += 1
                continue
            if l.startswith("*"):
                g_m = re.search(r"delG0f\s*=\s*(-?[\d\.]+)\s*(kj|kcal)/mol", l, re.IGNORECASE)
                if g_m:
                    val = float(g_m.group(1))
                    delg0f = val if g_m.group(2).lower() == "kj" else val * 4.184
                idx += 1
                continue
            tokens = l.split()
            try:
                nums = [float(x) for x in tokens]
                log_k_vals.extend(nums)
                idx += 1
            except ValueError:
                break

        # Skip trailing comments for this entry
        while idx < n and lines[idx].strip().startswith("*"):
            idx += 1

        while len(log_k_vals) < 8:
            log_k_vals.append(500.0)

        data = {
            "name": name,
            "formula": formula or name,
            "meta_type": meta_type,
            "charge": charge,
            "ion_size": ion_size,
            "mole_wt": mole_wt,
            "mole_vol": mole_vol,
            "stoichiometry": stoich,
            "log_k": log_k_vals[:8],
            "delg0f": delg0f,
            "delh0f": delh0f,
        }
        return data, idx

    @classmethod
    def _parse_redox_couples(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        parsed = 0
        n = len(lines)
        while idx < n and parsed < count:
            data, idx = cls._parse_species_block(lines, idx)
            if not data:
                break
            sp = TDATSpecies(
                data["name"], data["charge"], data["ion_size"], data["mole_wt"],
                data["stoichiometry"], data["log_k"], phase_type="Redox", formula=data["formula"]
            )
            db.redox_couples[data["name"]] = sp
            parsed += 1
        return idx

    @classmethod
    def _parse_aqueous_species(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        parsed = 0
        n = len(lines)
        while idx < n and parsed < count:
            data, idx = cls._parse_species_block(lines, idx)
            if not data:
                break
            sp = TDATSpecies(
                data["name"], data["charge"], data["ion_size"], data["mole_wt"],
                data["stoichiometry"], data["log_k"], phase_type="Aqueous", formula=data["formula"]
            )
            db.aqueous_species[data["name"]] = sp
            parsed += 1
        return idx

    @classmethod
    def _parse_minerals(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        parsed = 0
        n = len(lines)
        while idx < n and parsed < count:
            data, idx = cls._parse_species_block(lines, idx)
            if not data:
                break
            m = TDATMineral(
                data["name"], data["formula"], data["meta_type"], data["mole_vol"],
                data["mole_wt"], data["stoichiometry"], data["log_k"],
                delg0f_kj=data["delg0f"], delh0f_kj=data["delh0f"]
            )
            db.minerals[data["name"]] = m
            parsed += 1
        return idx

    @classmethod
    def _parse_gases(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        parsed = 0
        n = len(lines)
        while idx < n and parsed < count:
            data, idx = cls._parse_species_block(lines, idx)
            if not data:
                break
            g = TDATGas(
                data["name"], data["formula"], data["mole_vol"], data["mole_wt"],
                data["stoichiometry"], data["log_k"]
            )
            db.gases[data["name"]] = g
            parsed += 1
        return idx

    @classmethod
    def _parse_oxides(cls, lines: List[str], start_idx: int, count: int, db: TDATDatabase) -> int:
        idx = start_idx
        n = len(lines)
        parsed = 0
        while idx < n and parsed < count:
            l = lines[idx].strip()
            if l == "-end-":
                idx += 1
                break
            if l and not l.startswith("*"):
                parts = l.split()
                if len(parts) >= 2:
                    db.oxides[parts[0]] = parts[1]
                    parsed += 1
            idx += 1
        return idx
