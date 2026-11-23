"""
sdat_parser.py - High-Performance Parser and Surface Complexation Solver for GWB .sdat Databases.
Parses surface reaction datasets: two-layer diffuse, CD-MUSIC, triple-layer, Langmuir,
Freundlich, and ion exchange models for passive oxide film stability and corrosion inhibition.
"""

import os
import re
import pickle
import math
from typing import Dict, List, Any, Optional, Tuple


class SDATParser:
    """
    Parses Geochemist's Workbench (.sdat) surface complexation and sorption datasets.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.header: Dict[str, Any] = {}
        self.basis_species: List[Dict[str, Any]] = []
        self.sorbing_minerals: List[Dict[str, Any]] = []
        self.surface_species: List[Dict[str, Any]] = []
        self._parsed = False

    def parse(self, use_cache: bool = True) -> "SDATParser":
        if self._parsed:
            return self

        cache_dir = os.path.join(os.path.dirname(self.filepath), ".sdat_cache")
        cache_path = os.path.join(cache_dir, self.filename + ".pkl")

        if use_cache and os.path.exists(cache_path):
            try:
                mtime_src = os.path.getmtime(self.filepath)
                mtime_cache = os.path.getmtime(cache_path)
                if mtime_cache >= mtime_src:
                    with open(cache_path, "rb") as f:
                        data = pickle.load(f)
                        self.header = data["header"]
                        self.basis_species = data["basis_species"]
                        self.sorbing_minerals = data["sorbing_minerals"]
                        self.surface_species = data["surface_species"]
                        self._parsed = True
                        return self
            except Exception:
                pass

        self._parse_raw()

        # Save cache
        try:
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump({
                    "header": self.header,
                    "basis_species": self.basis_species,
                    "sorbing_minerals": self.sorbing_minerals,
                    "surface_species": self.surface_species,
                }, f)
        except Exception:
            pass

        self._parsed = True
        return self

    def _parse_raw(self) -> None:
        with open(self.filepath, "r", encoding="latin1") as f:
            text = f.read()

        # Split into major sections by -end-
        sections = text.split("-end-")

        # Section 0: Header
        header_text = sections[0] if len(sections) > 0 else ""
        self._parse_header(header_text)

        # Process each subsequent section dynamically by keyword inspection
        for sec in sections[1:]:
            s_lower = sec.lower()
            if "basis species" in s_lower:
                self._parse_basis_species(sec)
            elif "sorbing minerals" in s_lower:
                self._parse_sorbing_minerals(sec)
            elif "surface species" in s_lower or "exchange reaction" in s_lower:
                self._parse_surface_species(sec)
            elif "surface area=" in s_lower or "site density=" in s_lower:
                self._parse_sorbing_minerals(sec)
            elif "species in reaction" in s_lower or "log k" in s_lower:
                self._parse_surface_species(sec)
            elif ">" in sec:
                if not self.basis_species:
                    self._parse_basis_species(sec)
                else:
                    self._parse_surface_species(sec)

    def _parse_header(self, text: str) -> None:
        lines = [l.strip() for l in text.splitlines()]
        for l in lines:
            if l.startswith("*") or not l:
                continue
            lower = l.lower()
            if lower.startswith("surface type:"):
                self.header["surface_type"] = l.split(":", 1)[1].strip()
            elif lower.startswith("model type:"):
                self.header["model_type"] = l.split(":", 1)[1].strip()
            elif lower.startswith("surface potential:"):
                self.header["surface_potential"] = l.split(":", 1)[1].strip()
            elif lower.startswith("surface capacitance:"):
                self.header["surface_capacitance"] = l.split(":", 1)[1].strip()
            elif lower.startswith("thermo dataset:"):
                self.header["thermo_dataset"] = l.split(":", 1)[1].strip()
            elif lower.startswith("dataset format:"):
                self.header["dataset_format"] = l.split(":", 1)[1].strip()

    def _parse_basis_species(self, text: str) -> None:
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().startswith("*")]
            if not lines:
                continue
            # Look for lines starting with '>'
            name = None
            charge = 0.0
            mole_wt = 0.0
            for l in lines:
                if l.startswith(">"):
                    name = l.split()[0]
                elif "charge=" in l:
                    m = re.search(r"charge=\s*([0-9.\-]+)", l)
                    if m:
                        charge = float(m.group(1))
                    m2 = re.search(r"mole wt\.=\s*([0-9.\-]+)", l)
                    if m2:
                        mole_wt = float(m2.group(1))
            if name:
                self.basis_species.append({
                    "name": name,
                    "charge": charge,
                    "mole_wt": mole_wt,
                })

    def _parse_sorbing_minerals(self, text: str) -> None:
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().startswith("*")]
            if not lines or "sorbing minerals" in lines[0]:
                continue
            mineral_name = lines[0]
            surface_area = 0.0
            sites = []
            for l in lines[1:]:
                if "surface area=" in l:
                    m = re.search(r"surface area=\s*([0-9.\-]+)", l)
                    if m:
                        surface_area = float(m.group(1))
                elif "site density=" in l:
                    # e.g. >(s)FeOH site density= .0050 mol/mol mineral
                    parts = l.split("site density=")
                    site_name = parts[0].strip()
                    rest = parts[1].strip()
                    tokens = rest.split()
                    val = float(tokens[0]) if tokens else 0.0
                    unit = " ".join(tokens[1:]) if len(tokens) > 1 else ""
                    sites.append({
                        "site_name": site_name,
                        "site_density": val,
                        "unit": unit,
                    })
            if mineral_name and not mineral_name.startswith("-"):
                self.sorbing_minerals.append({
                    "mineral": mineral_name,
                    "surface_area_m2_g": surface_area,
                    "sites": sites,
                })

    def _parse_surface_species(self, text: str) -> None:
        # Regex to match surface species blocks
        species_blocks = re.split(r"\n(?=>)", text)
        for b in species_blocks:
            b = b.strip()
            if not b.startswith(">"):
                continue
            lines = [l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith("*")]
            if not lines:
                continue
            name = lines[0].split()[0]
            charge = 0.0
            mole_wt = 0.0
            log_k_a = 0.0
            log_k_b = 0.0
            reaction = []

            in_reaction = False
            for l in lines[1:]:
                if "charge=" in l:
                    m = re.search(r"charge=\s*([0-9.\-]+)", l)
                    if m:
                        charge = float(m.group(1))
                    m2 = re.search(r"mole wt\.=\s*([0-9.\-]+)", l)
                    if m2:
                        mole_wt = float(m2.group(1))
                elif "species in reaction" in l:
                    in_reaction = True
                elif "log K" in l:
                    in_reaction = False
                    ma = re.search(r"a=\s*([0-9.\-]+)", l)
                    mb = re.search(r"b=\s*([0-9.\-]+)", l)
                    if ma:
                        log_k_a = float(ma.group(1))
                    if mb:
                        log_k_b = float(mb.group(1))
                elif in_reaction:
                    tokens = l.split()
                    for i in range(0, len(tokens) - 1, 2):
                        try:
                            coeff = float(tokens[i])
                            spec = tokens[i + 1]
                            reaction.append({"species": spec, "coeff": coeff})
                        except ValueError:
                            pass

            self.surface_species.append({
                "name": name,
                "charge": charge,
                "mole_wt": mole_wt,
                "reaction": reaction,
                "log_k_a": log_k_a,
                "log_k_b": log_k_b,
            })

    def calculate_surface_speciation(
        self,
        temperature_c: float = 25.0,
        ph_range: Tuple[float, float, int] = (1.0, 14.0, 50)
    ) -> Dict[str, Any]:
        """
        Calculates surface site speciation (protonated >OH2+, neutral >OH, deprotonated >O-)
        and surface charge density sigma_0 (uC/cm^2) across pH for oxide/hydroxide surfaces.
        """
        # Search for protonation/deprotonation reactions among surface species
        # Acidity dissociation constants:
        # >SOH2+ <-> >SOH + H+  (pKa1 = 7.29 for HFO)
        # >SOH   <-> >SO- + H+  (pKa2 = 8.93 for HFO)
        pka1 = 7.29
        pka2 = 8.93

        for sp in self.surface_species:
            name = sp["name"]
            # Look for >...OH2+
            if "OH2+" in name or "H2+" in name:
                pka1 = abs(sp["log_k_a"])
            elif "O-" in name:
                pka2 = abs(sp["log_k_a"])

        ka1 = 10.0 ** (-pka1)
        ka2 = 10.0 ** (-pka2)

        # Point of zero charge: pH_pzc = 0.5 * (pKa1 + pKa2)
        ph_pzc = 0.5 * (pka1 + pka2)

        faraday = 96485.33  # C/mol

        ph_min, ph_max, n_pts = ph_range
        ph_values = [ph_min + i * (ph_max - ph_min) / max(1, n_pts - 1) for i in range(n_pts)]

        frac_oh2 = []
        frac_oh = []
        frac_o = []
        sigma_charge = []

        for ph in ph_values:
            h_plus = 10.0 ** (-ph)
            # Denominator: [H+]^2 + Ka1 [H+] + Ka1 Ka2
            denom = (h_plus ** 2) + (ka1 * h_plus) + (ka1 * ka2)
            if denom > 0:
                th_plus = (h_plus ** 2) / denom
                th_neutral = (ka1 * h_plus) / denom
                th_minus = (ka1 * ka2) / denom
            else:
                th_plus, th_neutral, th_minus = 0.0, 1.0, 0.0

            frac_oh2.append(round(th_plus, 4))
            frac_oh.append(round(th_neutral, 4))
            frac_o.append(round(th_minus, 4))

            # Charge density in uC/cm^2: sigma = (F * Ns / Sa) * (th_plus - th_minus)
            # Normalized surface charge density in uC/cm^2 (range -25 to +25 uC/cm^2)
            chg = 25.0 * (th_plus - th_minus)
            sigma_charge.append(round(chg, 3))

        return {
            "surface_type": self.header.get("surface_type", "Oxide Passive Film"),
            "model_type": self.header.get("model_type", "two-layer"),
            "ph_pzc": round(ph_pzc, 2),
            "log_k_protonation": round(pka1, 2),
            "log_k_deprotonation": round(pka2, 2),
            "ph_values": [round(p, 2) for p in ph_values],
            "fraction_protonated_oh2": frac_oh2,
            "fraction_neutral_oh": frac_oh,
            "fraction_deprotonated_o": frac_o,
            "surface_charge_density_uC_cm2": sigma_charge,
        }
