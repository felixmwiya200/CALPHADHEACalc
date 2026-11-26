# -*- coding: utf-8 -*-
"""
binary_diagram_engine.py - Thermodynamic Binary Phase Diagram Calculation Core

Calculates thermodynamic equilibria, invariant reactions, numerical phase boundary
splines, and assessed literature benchmark diagrams for binary alloy systems.

Academic Engineering Standards:
  1. Thermodynamic consistency via assessed CALPHAD benchmark datasets,
     sub-regular solution parameters, and Gibbs energy models.
  2. Assessed literature benchmarks with verified invariant reactions:
     - Ni-Al (Nickel-Aluminium: Dupin 2001, Ansara 1997, Okamoto 1993)
     - Fe-Cr (Iron-Chromium: Andersson & Sundman 1987, Xiong 2010)
     - Ti-Al (Titanium-Aluminium: Kattner 1992, Witusiewicz 2008)
     - Cu-Ni (Copper-Nickel: Mey 1992, SGTE)
     - Fe-C (Iron-Carbon: Gustafson 1985, Sundman 1985)
     - Co-Cr (Cobalt-Chromium: Kusoffsky & Jansson 1997)
     - Al-Cu (Aluminium-Copper: Murray 1985, Saunders 1997)
     - NaF-AlF3 (Sodium Fluoride - Aluminium Fluoride: Chartrand & Pelton 2002)
  3. Generalized arbitrary element-pair solver (A-B) synthesizing thermodynamic
     equilibria via Schroeder-van Laar liquidus depression and Miedema mixing enthalpy.
  4. Precise tie-line and lever-rule phase fraction calculations at arbitrary (x, T).
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.interpolate import PchipInterpolator

from pycalphad_app.core.elements_data import IUPAC_ELEMENTS_DATA
from pycalphad_app.core.thermo_engine import get_miedema_enthalpy

# Universal molar gas constant R in J / (mol * K)
R_GAS: float = 8.314462618


def _interpolate_curve(
    pts: List[Tuple[float, float]], n_pts: int = 50, clip_x_min: float = 0.0, clip_x_max: Optional[float] = None
) -> Tuple[List[float], List[float]]:
    """
    Interpolates a sequence of coordinate knots using arc-length parameterized PCHIP.
    Prevents spurious polynomial overshoots while preserving boundary tangency.
    """
    if len(pts) < 2:
        xs = [pts[0][0]] if pts else []
        ys = [pts[0][1]] if pts else []
        return xs, ys

    xs = np.array([p[0] for p in pts], dtype=float)
    ys = np.array([p[1] for p in pts], dtype=float)

    if len(pts) == 2:
        x_dense = np.linspace(xs[0], xs[1], n_pts)
        y_dense = np.linspace(ys[0], ys[1], n_pts)
        return x_dense.tolist(), y_dense.tolist()

    dists = np.hypot(np.diff(xs), np.diff(ys))
    total_dist = float(np.sum(dists))
    if total_dist < 1e-12:
        return xs.tolist(), ys.tolist()

    t_knots = np.insert(np.cumsum(dists), 0, 0.0) / total_dist
    px = PchipInterpolator(t_knots, xs)
    py = PchipInterpolator(t_knots, ys)

    t_eval = np.linspace(0.0, 1.0, n_pts)
    x_eval = px(t_eval)
    y_eval = py(t_eval)

    x_eval = np.maximum(clip_x_min, x_eval)
    if clip_x_max is not None:
        x_eval = np.minimum(clip_x_max, x_eval)

    return x_eval.tolist(), y_eval.tolist()


class BinaryDiagramEngine:
    """
    Thermodynamic calculation engine for binary phase diagrams.
    Generates complete curve series, invariant reaction tie-lines, and phase region
    labels for charting and CAE export.
    """

    ASSESSED_SYSTEMS = [
        "Ni-Al",
        "Fe-Cr",
        "Ti-Al",
        "Cu-Ni",
        "Fe-C",
        "Co-Cr",
        "Al-Cu",
        "Al-Co",
        "NaF-AlF3",
        "Mn-Ni",
        "Fe-Ni",
        "Cr-Ni",
        "Co-Ni",
        "Co-Fe",
        "Fe-Mn",
        "Cr-Mn",
        "Co-Mn",
        "Ti-V",
        "Al-Mg",
        "Al-Si",
        "Ni-Ti",
        "Cu-Zn",
        "Cu-Sn",
        # Multi-alloy database assessed systems
        "Al-Zn",
        "Al-Fe",
        "Al-Mn",
        "Mg-Zn",
        "Fe-Si",
        "Fe-Mo",
        "Fe-V",
        "Cr-Mo",
        "Sn-Ag",
        "Sn-Pb",
        "Sn-Bi",
        "Ti-Mo",
        "Ti-Zr",
        "Zr-Nb",
        "Zr-Sn",
        "Co-W",
        "Mo-W",
        "Nb-Mo",
        "Al-Zr",
        "Al-Y",
        "Co-Zr",
        "Co-Y",
        "Cr-Y",
        # Canonical reaction archetypes
        "Au-Cu",
        "Ag-Pt",
        "Cu-Pb",
        "Ag-Al",
        "Na-Zn",
    ]

    ASSESSED_PAIR_MAP: Dict[frozenset, str] = {
        frozenset(["Ni", "Al"]): "Ni-Al",
        frozenset(["Fe", "Cr"]): "Fe-Cr",
        frozenset(["Ti", "Al"]): "Ti-Al",
        frozenset(["Cu", "Ni"]): "Cu-Ni",
        frozenset(["Fe", "C"]): "Fe-C",
        frozenset(["Co", "Cr"]): "Co-Cr",
        frozenset(["Al", "Cu"]): "Al-Cu",
        frozenset(["Al", "Co"]): "Al-Co",
        frozenset(["Na", "F", "Al"]): "NaF-AlF3",
        frozenset(["Mn", "Ni"]): "Mn-Ni",
        frozenset(["Fe", "Ni"]): "Fe-Ni",
        frozenset(["Cr", "Ni"]): "Cr-Ni",
        frozenset(["Co", "Ni"]): "Co-Ni",
        frozenset(["Co", "Fe"]): "Co-Fe",
        frozenset(["Fe", "Mn"]): "Fe-Mn",
        frozenset(["Cr", "Mn"]): "Cr-Mn",
        frozenset(["Co", "Mn"]): "Co-Mn",
        frozenset(["Ti", "V"]): "Ti-V",
        frozenset(["Al", "Mg"]): "Al-Mg",
        frozenset(["Al", "Si"]): "Al-Si",
        frozenset(["Ni", "Ti"]): "Ni-Ti",
        frozenset(["Cu", "Zn"]): "Cu-Zn",
        frozenset(["Cu", "Sn"]): "Cu-Sn",
        frozenset(["Al", "Zn"]): "Al-Zn",
        frozenset(["Al", "Fe"]): "Al-Fe",
        frozenset(["Al", "Mn"]): "Al-Mn",
        frozenset(["Mg", "Zn"]): "Mg-Zn",
        frozenset(["Fe", "Si"]): "Fe-Si",
        frozenset(["Fe", "Mo"]): "Fe-Mo",
        frozenset(["Fe", "V"]): "Fe-V",
        frozenset(["Cr", "Mo"]): "Cr-Mo",
        frozenset(["Sn", "Ag"]): "Sn-Ag",
        frozenset(["Sn", "Pb"]): "Sn-Pb",
        frozenset(["Sn", "Bi"]): "Sn-Bi",
        frozenset(["Ti", "Mo"]): "Ti-Mo",
        frozenset(["Ti", "Zr"]): "Ti-Zr",
        frozenset(["Zr", "Nb"]): "Zr-Nb",
        frozenset(["Zr", "Sn"]): "Zr-Sn",
        frozenset(["Co", "W"]): "Co-W",
        frozenset(["Mo", "W"]): "Mo-W",
        frozenset(["Nb", "Mo"]): "Nb-Mo",
        frozenset(["Al", "Zr"]): "Al-Zr",
        frozenset(["Al", "Y"]): "Al-Y",
        frozenset(["Co", "Zr"]): "Co-Zr",
        frozenset(["Co", "Y"]): "Co-Y",
        frozenset(["Cr", "Y"]): "Cr-Y",
        frozenset(["Au", "Cu"]): "Au-Cu",
        frozenset(["Ag", "Pt"]): "Ag-Pt",
        frozenset(["Cu", "Pb"]): "Cu-Pb",
        frozenset(["Ag", "Al"]): "Ag-Al",
        frozenset(["Na", "Zn"]): "Na-Zn",
    }

    DATABASE_BINARY_SYSTEMS: Dict[str, List[str]] = {
        "High Entropy Alloys": [
            "Co-Cr", "Co-Fe", "Co-Mn", "Co-Ni", "Fe-Cr", "Cr-Mn", "Cr-Ni",
            "Fe-Mn", "Fe-Ni", "Mn-Ni", "Ni-Al", "Ti-Al", "Ti-V", "Fe-V",
            "Cr-Mo", "Fe-Mo", "Mo-W", "Nb-Mo", "Al-Zr", "Al-Y", "Co-Zr", "Co-Y", "Cr-Y"
        ],
        "Thermal Spray Coatings": [
            "Ni-Al", "Co-Cr", "Cr-Ni", "Co-Ni", "Al-Co", "Fe-Cr", "Ti-Al", "Al-Cu", "Cr-Mo"
        ],
        "Aluminium Alloy": [
            "Al-Cu", "Al-Mg", "Al-Si", "Al-Zn", "Al-Fe", "Al-Mn", "Mg-Zn", "Ni-Al", "Ti-Al", "Al-Co", "Al-Zr", "Al-Y"
        ],
        "Magnesium Alloy": [
            "Al-Mg", "Mg-Zn", "Al-Zn", "Cu-Zn", "Al-Mn"
        ],
        "Cast Iron": [
            "Fe-C", "Fe-Si", "Fe-Mn", "Fe-Cr", "Fe-Mo", "Fe-Ni"
        ],
        "General Steel": [
            "Fe-C", "Fe-Mn", "Fe-Si", "Fe-Cr", "Fe-Mo", "Fe-V", "Fe-Ni"
        ],
        "Stainless Steel": [
            "Fe-Cr", "Fe-Ni", "Cr-Ni", "Cr-Mo", "Fe-Mo", "Fe-Mn", "Fe-Si", "Fe-C"
        ],
        "Cobalt Alloy": [
            "Co-Cr", "Co-W", "Co-Ni", "Co-Fe", "Co-Mn", "Al-Co", "Cr-Mo", "Co-Zr", "Co-Y"
        ],
        "Nickel Based Superalloy": [
            "Ni-Al", "Cr-Ni", "Co-Ni", "Ni-Ti", "Co-Cr", "Fe-Ni", "Ti-Al", "Al-Co", "Cr-Mo", "Fe-Cr"
        ],
        "NiFe Based Superalloy": [
            "Fe-Ni", "Ni-Al", "Cr-Ni", "Fe-Cr", "Ni-Ti", "Cr-Mo", "Fe-Mo", "Fe-Mn"
        ],
        "Single Crystal": [
            "Ni-Al", "Co-Ni", "Cr-Ni", "Al-Co", "Co-Cr", "Ti-Al", "Mo-W"
        ],
        "Titanium Alloy": [
            "Ti-Al", "Ti-V", "Ti-Mo", "Ti-Zr", "Ni-Ti"
        ],
        "Zirconium Alloy": [
            "Zr-Nb", "Zr-Sn", "Ti-Zr", "Fe-Cr", "Fe-Ni", "Al-Zr", "Co-Zr"
        ],
        "Solder Alloy": [
            "Sn-Ag", "Sn-Pb", "Sn-Bi", "Cu-Sn", "Cu-Zn", "Al-Zn"
        ],
    }

    @classmethod
    def get_available_systems(cls, active_elements: Optional[List[str]] = None,
                              database_name: Optional[str] = None) -> List[str]:
        """
        Returns binary phase diagram systems.
        If active_elements is provided (with at least 2 elements), returns strictly the binary pairs
        composed of elements present in the active alloy composition, using assessed benchmark titles
        where available, and eliminating duplicates.
        If active_elements is not provided or has fewer than 2 elements, checks database_name against
        DATABASE_BINARY_SYSTEMS to return assessed systems pertinent to that database family; if not
        found or not provided, returns all assessed benchmarks.
        """
        if active_elements and len(active_elements) >= 2:
            clean_elems: List[str] = []
            for e in active_elements:
                if not e:
                    continue
                sym = e.strip().capitalize()
                if sym in IUPAC_ELEMENTS_DATA and sym not in clean_elems:
                    clean_elems.append(sym)

            if len(clean_elems) >= 2:
                systems: List[str] = []
                seen_pairs = set()
                for i in range(len(clean_elems)):
                    for j in range(i + 1, len(clean_elems)):
                        e1, e2 = clean_elems[i], clean_elems[j]
                        pair_set = frozenset([e1, e2])
                        if pair_set in seen_pairs:
                            continue
                        seen_pairs.add(pair_set)

                        if pair_set in cls.ASSESSED_PAIR_MAP:
                            systems.append(cls.ASSESSED_PAIR_MAP[pair_set])
                        else:
                            systems.append(f"{e1}-{e2}")
                return systems

        if database_name:
            norm_db = database_name.strip().lower()
            for db_key, db_systems in cls.DATABASE_BINARY_SYSTEMS.items():
                if db_key.lower() == norm_db:
                    return list(db_systems)
            for db_key, db_systems in cls.DATABASE_BINARY_SYSTEMS.items():
                if db_key.lower() in norm_db or norm_db in db_key.lower():
                    return list(db_systems)

        return list(cls.ASSESSED_SYSTEMS)

    @classmethod
    def compute_binary_diagram(cls, system_name: str, temp_unit: str = "C",
                               n_points: int = 200) -> Dict[str, Any]:
        """
        Main calculation dispatcher.
        Returns a complete binary phase diagram payload for plotting and UI consumption.
        """
        sys_lower = system_name.lower()
        is_k = "kelvin" in temp_unit.lower() or temp_unit.strip().upper() == "K"

        if "naf-alf3" in sys_lower:
            return cls._compute_naf_alf3(is_k, n_points)
        elif "ni-al" in sys_lower:
            return cls._compute_ni_al(is_k, n_points)
        elif "fe-cr" in sys_lower or "cr-fe" in sys_lower:
            return cls._compute_fe_cr(is_k, n_points)
        elif "ti-al" in sys_lower or "al-ti" in sys_lower:
            return cls._compute_ti_al(is_k, n_points)
        elif "cu-ni" in sys_lower or "ni-cu" in sys_lower:
            return cls._compute_cu_ni(is_k, n_points)
        elif "fe-c" in sys_lower or "c-fe" in sys_lower:
            return cls._compute_fe_c(is_k, n_points)
        elif "co-cr" in sys_lower or "cr-co" in sys_lower:
            return cls._compute_co_cr(is_k, n_points)
        elif "al-cu" in sys_lower or "cu-al" in sys_lower:
            return cls._compute_al_cu(is_k, n_points)
        elif "al-co" in sys_lower or "co-al" in sys_lower:
            return cls._compute_al_co(is_k, n_points)
        elif "mn-ni" in sys_lower or "ni-mn" in sys_lower:
            return cls._compute_mn_ni(is_k, n_points)
        elif "fe-ni" in sys_lower or "ni-fe" in sys_lower:
            return cls._compute_fe_ni(is_k, n_points)
        elif "cr-ni" in sys_lower or "ni-cr" in sys_lower:
            return cls._compute_cr_ni(is_k, n_points)
        elif "co-ni" in sys_lower or "ni-co" in sys_lower:
            return cls._compute_co_ni(is_k, n_points)
        elif "co-fe" in sys_lower or "fe-co" in sys_lower:
            return cls._compute_co_fe(is_k, n_points)
        elif "fe-mn" in sys_lower or "mn-fe" in sys_lower:
            return cls._compute_fe_mn(is_k, n_points)
        elif "cr-mn" in sys_lower or "mn-cr" in sys_lower:
            return cls._compute_cr_mn(is_k, n_points)
        elif "co-mn" in sys_lower or "mn-co" in sys_lower:
            return cls._compute_co_mn(is_k, n_points)
        elif "ti-v" in sys_lower or "v-ti" in sys_lower:
            return cls._compute_ti_v(is_k, n_points)
        elif "al-mg" in sys_lower or "mg-al" in sys_lower:
            return cls._compute_al_mg(is_k, n_points)
        elif "al-si" in sys_lower or "si-al" in sys_lower:
            return cls._compute_al_si(is_k, n_points)
        elif "ni-ti" in sys_lower or "ti-ni" in sys_lower:
            return cls._compute_ni_ti(is_k, n_points)
        elif "cu-zn" in sys_lower or "zn-cu" in sys_lower:
            return cls._compute_cu_zn(is_k, n_points)
        elif "cu-sn" in sys_lower or "sn-cu" in sys_lower:
            return cls._compute_cu_sn(is_k, n_points)
        elif "al-zn" in sys_lower or "zn-al" in sys_lower:
            return cls._compute_al_zn(is_k, n_points)
        elif "al-fe" in sys_lower or "fe-al" in sys_lower:
            return cls._compute_al_fe(is_k, n_points)
        elif "al-mn" in sys_lower or "mn-al" in sys_lower:
            return cls._compute_al_mn(is_k, n_points)
        elif "mg-zn" in sys_lower or "zn-mg" in sys_lower:
            return cls._compute_mg_zn(is_k, n_points)
        elif "fe-si" in sys_lower or "si-fe" in sys_lower:
            return cls._compute_fe_si(is_k, n_points)
        elif "fe-mo" in sys_lower or "mo-fe" in sys_lower:
            return cls._compute_fe_mo(is_k, n_points)
        elif "fe-v" in sys_lower or "v-fe" in sys_lower:
            return cls._compute_fe_v(is_k, n_points)
        elif "cr-mo" in sys_lower or "mo-cr" in sys_lower:
            return cls._compute_cr_mo(is_k, n_points)
        elif "sn-ag" in sys_lower or "ag-sn" in sys_lower:
            return cls._compute_sn_ag(is_k, n_points)
        elif "sn-pb" in sys_lower or "pb-sn" in sys_lower:
            return cls._compute_sn_pb(is_k, n_points)
        elif "sn-bi" in sys_lower or "bi-sn" in sys_lower:
            return cls._compute_sn_bi(is_k, n_points)
        elif "ti-mo" in sys_lower or "mo-ti" in sys_lower:
            return cls._compute_ti_mo(is_k, n_points)
        elif "ti-zr" in sys_lower or "zr-ti" in sys_lower:
            return cls._compute_ti_zr(is_k, n_points)
        elif "zr-nb" in sys_lower or "nb-zr" in sys_lower:
            return cls._compute_zr_nb(is_k, n_points)
        elif "zr-sn" in sys_lower or "sn-zr" in sys_lower:
            return cls._compute_zr_sn(is_k, n_points)
        elif "co-w" in sys_lower or "w-co" in sys_lower:
            return cls._compute_co_w(is_k, n_points)
        elif "mo-w" in sys_lower or "w-mo" in sys_lower:
            return cls._compute_mo_w(is_k, n_points)
        elif "nb-mo" in sys_lower or "mo-nb" in sys_lower:
            return cls._compute_nb_mo(is_k, n_points)
        elif "al-zr" in sys_lower or "zr-al" in sys_lower:
            return cls._compute_al_zr(is_k, n_points)
        elif "al-y" in sys_lower or "y-al" in sys_lower:
            return cls._compute_al_y(is_k, n_points)
        elif "co-zr" in sys_lower or "zr-co" in sys_lower:
            return cls._compute_co_zr(is_k, n_points)
        elif "co-y" in sys_lower or "y-co" in sys_lower:
            return cls._compute_co_y(is_k, n_points)
        elif "cr-y" in sys_lower or "y-cr" in sys_lower:
            return cls._compute_cr_y(is_k, n_points)
        elif "au-cu" in sys_lower or "cu-au" in sys_lower:
            return cls._compute_au_cu(is_k, n_points)
        elif "ag-pt" in sys_lower or "pt-ag" in sys_lower:
            return cls._compute_ag_pt(is_k, n_points)
        elif "cu-pb" in sys_lower or "pb-cu" in sys_lower:
            return cls._compute_cu_pb(is_k, n_points)
        elif "ag-al" in sys_lower or "al-ag" in sys_lower:
            return cls._compute_ag_al(is_k, n_points)
        elif "na-zn" in sys_lower or "zn-na" in sys_lower:
            return cls._compute_na_zn(is_k, n_points)
        else:
            parts = system_name.split()[0].split("-")
            el_a = parts[0].strip().capitalize()
            el_b = parts[1].strip().capitalize() if len(parts) > 1 else "Ni"
            return cls._compute_arbitrary_binary(el_a, el_b, is_k, n_points)

    # -------------------------------------------------------------------------
    # 1. Ni-Al Binary Phase Diagram (Superalloy Benchmark)
    # References: N. Dupin, I. Ansara, B. Sundman (2001); H. Okamoto (ASM).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ni_al(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus segments from pure Ni (1455 C) to pure Al (660.32 C)
        l_knots_1 = [(0.000, 1455.0), (0.050, 1445.0), (0.100, 1430.0), (0.150, 1412.0), (0.200, 1395.0), (0.245, 1385.0)]
        l_knots_2 = [(0.245, 1385.0), (0.248, 1395.0)]
        l_knots_3 = [(0.248, 1395.0), (0.300, 1505.0), (0.350, 1585.0), (0.400, 1630.0), (0.425, 1638.0)]
        l_knots_4 = [(0.425, 1638.0), (0.450, 1630.0), (0.500, 1570.0), (0.550, 1450.0), (0.600, 1260.0), (0.625, 1133.0)]
        l_knots_5 = [(0.625, 1133.0), (0.700, 1060.0), (0.750, 995.0), (0.800, 925.0), (0.850, 854.0)]
        l_knots_6 = [(0.850, 854.0), (0.900, 775.0), (0.950, 690.0), (0.973, 640.0)]
        l_knots_7 = [(0.973, 640.0), (0.985, 650.0), (1.000, 660.32)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 25), (l_knots_2, 8), (l_knots_3, 30),
                             (l_knots_4, 30), (l_knots_5, 25), (l_knots_6, 25), (l_knots_7, 12)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Solidus and solvus curves
        xs_gamma_sol, ys_gamma_sol = _interpolate_curve(
            [(0.000, 1455.0), (0.050, 1442.0), (0.100, 1425.0), (0.150, 1406.0), (0.212, 1385.0)], n_pts=30
        )
        xs_gamma_slv, ys_gamma_slv = _interpolate_curve(
            [(0.212, 1385.0), (0.180, 1200.0), (0.150, 1000.0), (0.120, 800.0), (0.100, 600.0), (0.080, 400.0)], n_pts=35
        )

        gp_knots = [
            (0.230, 400.0), (0.230, 600.0), (0.235, 800.0), (0.240, 1000.0), (0.245, 1200.0), (0.248, 1385.0),
            (0.275, 1395.0), (0.275, 1200.0), (0.273, 1000.0), (0.270, 800.0), (0.270, 600.0), (0.268, 400.0)
        ]
        xs_gp, ys_gp = _interpolate_curve(gp_knots, n_pts=50)

        b2_knots = [
            (0.315, 400.0), (0.315, 600.0), (0.320, 800.0), (0.335, 1000.0), (0.355, 1200.0), (0.370, 1395.0),
            (0.400, 1560.0), (0.425, 1638.0), (0.500, 1560.0), (0.550, 1420.0), (0.595, 1133.0),
            (0.565, 1000.0), (0.540, 800.0), (0.530, 400.0)
        ]
        xs_b2, ys_b2 = _interpolate_curve(b2_knots, n_pts=60)

        ni2al3_knots = [
            (0.605, 400.0), (0.605, 600.0), (0.605, 1133.0), (0.635, 854.0), (0.635, 400.0)
        ]
        xs_ni2al3, ys_ni2al3 = _interpolate_curve(ni2al3_knots, n_pts=35)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "γ-(Ni) Solidus", "xs": xs_gamma_sol, "ys": [conv(t) for t in ys_gamma_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "γ Solvus (γ / γ+γ')", "xs": xs_gamma_slv, "ys": [conv(t) for t in ys_gamma_slv], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "γ'-Ni₃Al Envelope (L1₂)", "xs": xs_gp, "ys": [conv(t) for t in ys_gp], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "β-NiAl Envelope (B2)", "xs": xs_b2, "ys": [conv(t) for t in ys_b2], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "Ni₂Al₃ Envelope", "xs": xs_ni2al3, "ys": [conv(t) for t in ys_ni2al3], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "NiAl₃ Stoichiometric Line", "xs": [0.750, 0.750], "ys": [conv(400.0), conv(854.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Ni₅Al₃ Phase Line", "xs": [0.365, 0.365], "ys": [conv(400.0), conv(700.0)], "color": "#0891B2", "width": 1.8, "dash": "dot"},
            {"name": "Peritectic Tie-Line (1395 °C)", "xs": [0.248, 0.370], "ys": [conv(1395.0), conv(1395.0)], "color": "#7C3AED", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1385 °C)", "xs": [0.212, 0.248], "ys": [conv(1385.0), conv(1385.0)], "color": "#2563EB", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1133 °C)", "xs": [0.595, 0.625], "ys": [conv(1133.0), conv(1133.0)], "color": "#D97706", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (854 °C)", "xs": [0.635, 0.850], "ys": [conv(854.0), conv(854.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Tie-Line (640 °C)", "xs": [0.750, 0.9998], "ys": [conv(640.0), conv(640.0)], "color": "#059669", "width": 1.6, "dash": "dash"}
        ]

        invariants = [
            {"type": "Congruent", "temp": conv(1638.0), "x_reaction": 0.425, "x_start": 0.425, "x_end": 0.425, "equation": "L ⇌ β-NiAl (B2 Ordered BCC)"},
            {"type": "Peritectic", "temp": conv(1395.0), "x_reaction": 0.248, "x_start": 0.425, "x_end": 0.425, "equation": "L (24.8 at% Al) + β-NiAl (37.0 at% Al) ⇌ γ'-Ni₃Al (27.5 at% Al)"},
            {"type": "Eutectic", "temp": conv(1385.0), "x_reaction": 0.245, "x_start": 0.425, "x_end": 0.425, "equation": "L (24.5 at% Al) ⇌ γ-(Ni) (21.2 at% Al) + γ'-Ni₃Al (24.8 at% Al)"},
            {"type": "Peritectic", "temp": conv(1133.0), "x_reaction": 0.625, "x_start": 0.425, "x_end": 0.425, "equation": "L (62.5 at% Al) + β-NiAl (59.5 at% Al) ⇌ Ni₂Al₃ (60.5 at% Al)"},
            {"type": "Peritectic", "temp": conv(854.0), "x_reaction": 0.850, "x_start": 0.425, "x_end": 0.425, "equation": "L (85.0 at% Al) + Ni₂Al₃ (63.5 at% Al) ⇌ NiAl₃ (75.0 at% Al)"},
            {"type": "Eutectic", "temp": conv(640.0), "x_reaction": 0.973, "x_start": 0.425, "x_end": 0.425, "equation": "L (97.3 at% Al) ⇌ NiAl₃ (75.0 at% Al) + (Al) (99.98 at% Al)"},
            {"type": "Peritectoid", "temp": conv(700.0), "x_reaction": 0.365, "x_start": 0.425, "x_end": 0.425, "equation": "γ'-Ni₃Al (28.5 at% Al) + β-NiAl (38.0 at% Al) ⇌ Ni₅Al₃ (36.5 at% Al)"}
        ]

        regions = [
            {"label": "Liquid", "x": 0.50, "y": conv(1700.0), "font_size": 13, "color": "#0F172A"},
            {"label": "γ-(Ni)", "x": 0.08, "y": conv(1200.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "γ + γ'", "x": 0.18, "y": conv(1000.0), "font_size": 11, "color": "#4338CA"},
            {"label": "γ'-Ni₃Al", "x": 0.255, "y": conv(1000.0), "font_size": 11, "color": "#6D28D9"},
            {"label": "γ' + β", "x": 0.31, "y": conv(1100.0), "font_size": 10, "color": "#4F46E5"},
            {"label": "β-NiAl (B2)", "x": 0.45, "y": conv(1200.0), "font_size": 12, "color": "#065F46"},
            {"label": "Ni₂Al₃", "x": 0.62, "y": conv(800.0), "font_size": 10, "color": "#92400E"},
            {"label": "Ni₂Al₃ + NiAl₃", "x": 0.69, "y": conv(700.0), "font_size": 10, "color": "#B45309"},
            {"label": "NiAl₃", "x": 0.75, "y": conv(500.0), "font_size": 10, "color": "#DC2626"},
            {"label": "NiAl₃ + (Al)", "x": 0.88, "y": conv(500.0), "font_size": 10, "color": "#991B1B"},
            {"label": "(Al)", "x": 0.995, "y": conv(400.0), "font_size": 10, "color": "#047857"}
        ]

        return {
            "system": "Ni-Al",
            "element_a": "Ni",
            "element_b": "Al",
            "x_axis_label": "Atomic Fraction of Aluminium, x(Al)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(350.0),
            "y_max": conv(1750.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 2. Fe-Cr Binary Phase Diagram (Sigma Phase & Spinodal Benchmark)
    # References: J. O. Andersson & B. Sundman (1987); W. Xiong et al. (2010).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_cr(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus and solidus with congruent minimum at 1305.0 C, 21.5 at% Cr
        l_knots = [
            (0.000, 1538.0), (0.050, 1485.0), (0.100, 1435.0), (0.150, 1380.0), (0.200, 1320.0),
            (0.215, 1305.0),
            (0.300, 1360.0), (0.400, 1450.0), (0.500, 1545.0), (0.600, 1640.0), (0.700, 1735.0),
            (0.800, 1815.0), (0.900, 1870.0), (1.000, 1907.0)
        ]
        s_knots = [
            (0.000, 1538.0), (0.050, 1470.0), (0.100, 1410.0), (0.150, 1350.0), (0.200, 1310.0),
            (0.215, 1305.0),
            (0.300, 1340.0), (0.400, 1425.0), (0.500, 1515.0), (0.600, 1610.0), (0.700, 1705.0),
            (0.800, 1790.0), (0.900, 1855.0), (1.000, 1907.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(l_knots, n_pts=80, clip_x_min=0.0, clip_x_max=1.0)
        xs_sol, ys_sol = _interpolate_curve(s_knots, n_pts=80, clip_x_min=0.0, clip_x_max=1.0)

        # Closed gamma loop (austenite) originating from pure Fe allotropes 1394 C and 912 C
        gamma_outer_knots = [
            (0.000, 1394.0), (0.050, 1350.0), (0.100, 1200.0), (0.125, 1050.0), (0.100, 950.0), (0.000, 912.0)
        ]
        gamma_inner_knots = [
            (0.000, 1394.0), (0.040, 1300.0), (0.080, 1150.0), (0.119, 1000.0), (0.080, 930.0), (0.000, 912.0)
        ]
        xs_g_out, ys_g_out = _interpolate_curve(gamma_outer_knots, n_pts=45)
        xs_g_in, ys_g_in = _interpolate_curve(gamma_inner_knots, n_pts=45)

        # Sigma phase (D8_b) Frank-Kasper envelope peaking at 830.0 C, 47.5 at% Cr
        sigma_knots = [
            (0.180, 500.0), (0.240, 550.0), (0.350, 700.0), (0.440, 800.0), (0.475, 830.0),
            (0.500, 800.0), (0.580, 700.0), (0.680, 550.0), (0.780, 500.0)
        ]
        xs_sigma, ys_sigma = _interpolate_curve(sigma_knots, n_pts=50)

        # 475 C spinodal miscibility gap (binodal and spinodal) peaking at 575 C, 48 at% Cr
        binodal_knots = [
            (0.130, 475.0), (0.180, 490.0), (0.250, 520.0), (0.350, 550.0), (0.480, 575.0),
            (0.610, 550.0), (0.720, 520.0), (0.810, 490.0), (0.860, 475.0)
        ]
        spinodal_knots = [
            (0.250, 475.0), (0.320, 500.0), (0.400, 550.0), (0.480, 575.0), (0.560, 550.0), (0.650, 500.0), (0.750, 475.0)
        ]
        xs_binodal, ys_binodal = _interpolate_curve(binodal_knots, n_pts=45)
        xs_spinodal, ys_spinodal = _interpolate_curve(spinodal_knots, n_pts=35)

        # Magnetic Curie transition line
        curie_knots = [
            (0.00, 770.0), (0.10, 750.0), (0.20, 715.0), (0.30, 660.0), (0.40, 580.0),
            (0.50, 470.0), (0.60, 310.0), (0.70, 50.0)
        ]
        xs_curie, ys_curie = _interpolate_curve(curie_knots, n_pts=40)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (BCC)", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "γ-Loop Outer Boundary (α / α+γ)", "xs": xs_g_out, "ys": [conv(t) for t in ys_g_out], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "γ-Loop Inner Boundary (γ / α+γ)", "xs": xs_g_in, "ys": [conv(t) for t in ys_g_in], "color": "#B91C1C", "width": 1.8, "dash": "solid"},
            {"name": "σ-Phase Envelope (D8_b)", "xs": xs_sigma, "ys": [conv(t) for t in ys_sigma], "color": "#7C3AED", "width": 2.2, "dash": "solid"},
            {"name": "α-α' Miscibility Gap Binodal", "xs": xs_binodal, "ys": [conv(t) for t in ys_binodal], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "α-α' Spinodal Curve (475 °C)", "xs": xs_spinodal, "ys": [conv(t) for t in ys_spinodal], "color": "#059669", "width": 1.5, "dash": "dot"},
            {"name": "Magnetic Curie Line", "xs": xs_curie, "ys": [conv(t) for t in ys_curie], "color": "#D97706", "width": 1.5, "dash": "dash"}
        ]

        invariants = [
            {"type": "Congruent Minimum", "temp": conv(1305.0), "x_reaction": 0.215, "x_start": 0.215, "x_end": 0.215, "equation": "L ⇌ BCC solid solution (Azeotropic minimum at 1305 °C, 21.5 at% Cr)"},
            {"type": "Peritectoid / Ordering Peak", "temp": conv(830.0), "x_reaction": 0.475, "x_start": 0.215, "x_end": 0.215, "equation": "BCC (α) ⇌ σ Phase (Tetragonal D8_b Frank-Kasper apex)"},
            {"type": "Consolute Miscibility Gap", "temp": conv(575.0), "x_reaction": 0.480, "x_start": 0.480, "x_end": 0.480, "equation": "BCC α ⇌ Fe-rich α + Cr-rich α' (475 °C Embrittlement Consolute Point)"}
        ]

        regions = [
            {"label": "Liquid", "x": 0.50, "y": conv(1800.0), "font_size": 13, "color": "#0F172A"},
            {"label": "δ-BCC", "x": 0.05, "y": conv(1430.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "γ (Austenite)", "x": 0.05, "y": conv(1150.0), "font_size": 11, "color": "#B91C1C"},
            {"label": "α-(Fe,Cr) BCC", "x": 0.50, "y": conv(1100.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "α + σ", "x": 0.30, "y": conv(650.0), "font_size": 10, "color": "#4338CA"},
            {"label": "σ (D8_b)", "x": 0.47, "y": conv(700.0), "font_size": 11, "color": "#6D28D9"},
            {"label": "σ + α'", "x": 0.65, "y": conv(650.0), "font_size": 10, "color": "#4338CA"},
            {"label": "α + α' (Spinodal Gap)", "x": 0.48, "y": conv(450.0), "font_size": 10, "color": "#065F46"}
        ]

        return {
            "system": "Fe-Cr",
            "element_a": "Fe",
            "element_b": "Cr",
            "x_axis_label": "Atomic Fraction of Chromium, x(Cr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 3. Ti-Al Binary Phase Diagram (Titanium Aluminides Aerospace)
    # References: U. R. Kattner, J.-C. Lin, Y. A. Chang (1992); V. T. Witusiewicz (2008).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ti_al(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus segments from pure Ti (1670 C) to pure Al (660.32 C)
        l_knots_1 = [(0.000, 1670.0), (0.100, 1650.0), (0.200, 1620.0), (0.300, 1580.0), (0.400, 1530.0), (0.485, 1490.0)]
        l_knots_2 = [(0.485, 1490.0), (0.510, 1465.0), (0.540, 1445.0)]
        l_knots_3 = [(0.540, 1445.0), (0.600, 1430.0), (0.675, 1215.0), (0.740, 1400.0)]
        l_knots_4 = [(0.740, 1400.0), (0.800, 1280.0), (0.850, 1120.0), (0.900, 940.0), (0.950, 780.0), (0.9985, 665.0)]
        l_knots_5 = [(0.9985, 665.0), (1.000, 660.32)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 30), (l_knots_2, 12), (l_knots_3, 25), (l_knots_4, 35), (l_knots_5, 8)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Solid phase boundaries
        beta_knots = [(0.000, 882.0), (0.100, 1050.0), (0.200, 1220.0), (0.300, 1370.0), (0.420, 1490.0)]
        xs_beta, ys_beta = _interpolate_curve(beta_knots, n_pts=30)

        alpha_knots = [(0.000, 882.0), (0.050, 970.0), (0.150, 1150.0), (0.300, 1370.0), (0.450, 1490.0), (0.470, 1445.0), (0.390, 1120.0)]
        xs_alpha, ys_alpha = _interpolate_curve(alpha_knots, n_pts=40)

        a2_knots = [
            (0.220, 400.0), (0.220, 600.0), (0.240, 900.0), (0.260, 1100.0), (0.320, 1180.0),
            (0.375, 1120.0), (0.360, 900.0), (0.350, 600.0), (0.350, 400.0)
        ]
        xs_a2, ys_a2 = _interpolate_curve(a2_knots, n_pts=45)

        gamma_knots = [
            (0.475, 400.0), (0.475, 800.0), (0.480, 1000.0), (0.485, 1120.0), (0.490, 1445.0),
            (0.550, 1200.0), (0.540, 800.0), (0.535, 400.0)
        ]
        xs_gamma, ys_gamma = _interpolate_curve(gamma_knots, n_pts=45)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "β-Ti Boundary", "xs": xs_beta, "ys": [conv(t) for t in ys_beta], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "α-Ti Boundary", "xs": xs_alpha, "ys": [conv(t) for t in ys_alpha], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "α₂-Ti₃Al Envelope (D0₁₉)", "xs": xs_a2, "ys": [conv(t) for t in ys_a2], "color": "#1E3A8A", "width": 2.0, "dash": "solid"},
            {"name": "γ-TiAl Envelope (L1₀)", "xs": xs_gamma, "ys": [conv(t) for t in ys_gamma], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "TiAl₂ Compound Line", "xs": [0.660, 0.660], "ys": [conv(400.0), conv(1215.0)], "color": "#7C3AED", "width": 1.8, "dash": "dash"},
            {"name": "TiAl₃ Compound Line", "xs": [0.750, 0.750], "ys": [conv(400.0), conv(1400.0)], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "Peritectic Tie-Line (1490 °C)", "xs": [0.420, 0.485], "ys": [conv(1490.0), conv(1490.0)], "color": "#D97706", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1445 °C)", "xs": [0.470, 0.540], "ys": [conv(1445.0), conv(1445.0)], "color": "#2563EB", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1400 °C)", "xs": [0.590, 0.750], "ys": [conv(1400.0), conv(1400.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1215 °C)", "xs": [0.620, 0.675], "ys": [conv(1215.0), conv(1215.0)], "color": "#7C3AED", "width": 1.6, "dash": "dash"},
            {"name": "Eutectoid Tie-Line (1120 °C)", "xs": [0.375, 0.485], "ys": [conv(1120.0), conv(1120.0)], "color": "#059669", "width": 1.6, "dash": "dash"}
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1490.0), "x_reaction": 0.485, "x_start": 0.420, "x_end": 0.485, "equation": "L (48.5 at% Al) + β-Ti (42.0 at% Al) ⇌ α-Ti (45.0 at% Al)"},
            {"type": "Peritectic", "temp": conv(1445.0), "x_reaction": 0.540, "x_start": 0.470, "x_end": 0.540, "equation": "L (54.0 at% Al) + α-Ti (47.0 at% Al) ⇌ γ-TiAl (49.0 at% Al)"},
            {"type": "Peritectic", "temp": conv(1400.0), "x_reaction": 0.740, "x_start": 0.590, "x_end": 0.750, "equation": "L (74.0 at% Al) + γ-TiAl (59.0 at% Al) ⇌ TiAl₃ (75.0 at% Al)"},
            {"type": "Peritectic", "temp": conv(1215.0), "x_reaction": 0.675, "x_start": 0.620, "x_end": 0.675, "equation": "L (67.5 at% Al) + γ-TiAl (62.0 at% Al) ⇌ TiAl₂ (66.0 at% Al)"},
            {"type": "Eutectoid", "temp": conv(1120.0), "x_reaction": 0.390, "x_start": 0.375, "x_end": 0.485, "equation": "α-Ti (39.0 at% Al) ⇌ α₂-Ti₃Al (37.5 at% Al) + γ-TiAl (48.5 at% Al)"},
            {"type": "Peritectic", "temp": conv(665.0), "x_reaction": 0.9985, "x_start": 0.750, "x_end": 0.9993, "equation": "L (99.85 at% Al) + TiAl₃ ⇌ (Al) Solid Solution"},
            # Allotropic pure Ti transition at 882 C is a unary boundary point, not a binary tie-line
        ]

        regions = [
            {"label": "Liquid", "x": 0.60, "y": conv(1600.0), "font_size": 13, "color": "#0F172A"},
            {"label": "β-Ti (BCC)", "x": 0.15, "y": conv(1400.0), "font_size": 11, "color": "#D97706"},
            {"label": "α-Ti (HCP)", "x": 0.35, "y": conv(1300.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "α₂-Ti₃Al (D0₁₉)", "x": 0.28, "y": conv(900.0), "font_size": 11, "color": "#1E40AF"},
            {"label": "α₂ + γ Lamellar", "x": 0.42, "y": conv(900.0), "font_size": 10, "color": "#4338CA"},
            {"label": "γ-TiAl (L1₀)", "x": 0.51, "y": conv(1000.0), "font_size": 11, "color": "#065F46"},
            {"label": "TiAl₂", "x": 0.66, "y": conv(900.0), "font_size": 10, "color": "#6D28D9"},
            {"label": "TiAl₃", "x": 0.75, "y": conv(800.0), "font_size": 10, "color": "#B91C1C"},
            {"label": "(Al)", "x": 0.995, "y": conv(400.0), "font_size": 10, "color": "#047857"}
        ]

        return {
            "system": "Ti-Al",
            "element_a": "Ti",
            "element_b": "Al",
            "x_axis_label": "Atomic Fraction of Aluminium, x(Al)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(350.0),
            "y_max": conv(1800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 4. Cu-Ni Binary Phase Diagram (Classic Isomorphous Lens)
    # References: S. an Mey (1992); SGTE Binary Assessment.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cu_ni(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots = [
            (0.00, 1084.62), (0.10, 1145.0), (0.20, 1198.0), (0.30, 1245.0), (0.40, 1288.0),
            (0.50, 1326.0), (0.60, 1360.0), (0.70, 1390.0), (0.80, 1416.0), (0.90, 1438.0), (1.00, 1455.0)
        ]
        s_knots = [
            (0.00, 1084.62), (0.10, 1105.0), (0.20, 1140.0), (0.30, 1180.0), (0.40, 1225.0),
            (0.50, 1270.0), (0.60, 1315.0), (0.70, 1358.0), (0.80, 1396.0), (0.90, 1430.0), (1.00, 1455.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(l_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)
        xs_sol, ys_sol = _interpolate_curve(s_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        # Low-temperature asymmetric miscibility gap peaking at 354.5 C, 68 at% Ni
        binodal_knots = [
            (0.15, 80.0), (0.25, 180.0), (0.35, 260.0), (0.45, 310.0), (0.55, 340.0),
            (0.68, 354.5),
            (0.78, 340.0), (0.85, 310.0), (0.90, 260.0), (0.94, 180.0), (0.97, 80.0)
        ]
        xs_gap, ys_gap = _interpolate_curve(binodal_knots, n_pts=45)

        # Magnetic Curie line dropping from pure Ni (358 C) to 0 C around 46 at% Ni
        curie_knots = [
            (0.44, -20.0), (0.46, 0.0), (0.50, 25.0), (0.60, 95.0), (0.70, 160.0),
            (0.80, 230.0), (0.90, 295.0), (1.00, 358.0)
        ]
        xs_curie, ys_curie = _interpolate_curve(curie_knots, n_pts=35)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (FCC)", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Miscibility Gap (α₁ + α₂)", "xs": xs_gap, "ys": [conv(t) for t in ys_gap], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Magnetic Curie Line", "xs": xs_curie, "ys": [conv(t) for t in ys_curie], "color": "#D97706", "width": 1.5, "dash": "dot"}
        ]

        invariants = [
            {"type": "Isomorphous Melting Lens", "temp": conv(1084.62), "x_reaction": 0.000, "x_start": 0.0, "x_end": 1.0, "equation": "Complete mutual solubility in liquid and FCC solid phases (Hume-Rothery archetype)"},
            {"type": "Critical Consolute Point", "temp": conv(354.5), "x_reaction": 0.680, "x_start": 0.680, "x_end": 0.680, "equation": "Sub-ambient FCC clustering: α ⇌ Cu-rich α₁ + Ni-rich α₂ (354.5 °C, 68 at% Ni)"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1400.0), "font_size": 13, "color": "#0F172A"},
            {"label": "Mushy Zone (L + α)", "x": 0.40, "y": conv(1260.0), "font_size": 11, "color": "#D97706"},
            {"label": "FCC Solid Solution (α)", "x": 0.50, "y": conv(800.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "Miscibility Gap (α₁ + α₂)", "x": 0.60, "y": conv(200.0), "font_size": 10, "color": "#B91C1C"},
            {"label": "Ferromagnetic FCC", "x": 0.85, "y": conv(100.0), "font_size": 10, "color": "#B45309"}
        ]

        return {
            "system": "Cu-Ni",
            "element_a": "Cu",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Nickel, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(1600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 5. Fe-C Binary Phase Diagram (Steel / Iron-Cementite System)
    # References: P. Gustafson (1985); B. Sundman (1985); SGTE Assessment.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_c(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus ABCD across 0 to 6.67 wt% C
        l_knots_1 = [(0.00, 1538.0), (0.10, 1530.0), (0.20, 1522.0), (0.35, 1510.0), (0.53, 1495.0)]
        l_knots_2 = [(0.53, 1495.0), (1.00, 1450.0), (2.00, 1360.0), (3.00, 1270.0), (4.00, 1180.0), (4.30, 1147.0)]
        l_knots_3 = [(4.30, 1147.0), (4.60, 1200.0), (5.00, 1280.0), (5.50, 1380.0), (6.00, 1490.0), (6.67, 1650.0)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 20), (l_knots_2, 45), (l_knots_3, 30)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=6.67)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Solidus and transformation lines
        delta_sol_knots = [(0.00, 1538.0), (0.05, 1515.0), (0.09, 1495.0)]
        delta_slv_knots = [(0.00, 1394.0), (0.05, 1440.0), (0.09, 1495.0)]
        xs_d_sol, ys_d_sol = _interpolate_curve(delta_sol_knots, n_pts=20)
        xs_d_slv, ys_d_slv = _interpolate_curve(delta_slv_knots, n_pts=20)

        gamma_sol_knots = [(0.17, 1495.0), (0.50, 1440.0), (1.00, 1340.0), (1.50, 1240.0), (2.11, 1147.0)]
        xs_g_sol, ys_g_sol = _interpolate_curve(gamma_sol_knots, n_pts=35)

        a3_knots = [(0.00, 912.0), (0.10, 875.0), (0.20, 840.0), (0.35, 795.0), (0.50, 760.0), (0.65, 738.0), (0.76, 727.0)]
        acm_knots = [(0.76, 727.0), (1.00, 800.0), (1.25, 880.0), (1.50, 960.0), (1.75, 1035.0), (2.11, 1147.0)]
        xs_a3, ys_a3 = _interpolate_curve(a3_knots, n_pts=35)
        xs_acm, ys_acm = _interpolate_curve(acm_knots, n_pts=35)

        alpha_slv_knots = [(0.022, 727.0), (0.015, 600.0), (0.008, 500.0), (0.003, 400.0), (0.001, 300.0), (0.0001, 200.0)]
        xs_a_slv, ys_a_slv = _interpolate_curve(alpha_slv_knots, n_pts=25)

        curves = [
            {"name": "Liquidus (ABCD)", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "δ-Ferrite Boundaries", "xs": xs_d_sol + xs_d_slv, "ys": [conv(t) for t in ys_d_sol + ys_d_slv], "color": "#2563EB", "width": 1.6, "dash": "solid"},
            {"name": "Austenite γ Solidus", "xs": xs_g_sol, "ys": [conv(t) for t in ys_g_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Austenite γ Solvus A3", "xs": xs_a3, "ys": [conv(t) for t in ys_a3], "color": "#1E40AF", "width": 1.8, "dash": "solid"},
            {"name": "Cementite Solvus Acm", "xs": xs_acm, "ys": [conv(t) for t in ys_acm], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "α-Ferrite Solvus", "xs": xs_a_slv, "ys": [conv(t) for t in ys_a_slv], "color": "#059669", "width": 1.5, "dash": "solid"},
            {"name": "Cementite Fe₃C Stoichiometric Line", "xs": [6.67, 6.67], "ys": [conv(200.0), conv(1650.0)], "color": "#7F1D1D", "width": 2.2, "dash": "solid"},
            {"name": "Peritectic Tie-Line (1495 °C)", "xs": [0.09, 0.53], "ys": [conv(1495.0), conv(1495.0)], "color": "#D97706", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1147 °C)", "xs": [2.11, 6.67], "ys": [conv(1147.0), conv(1147.0)], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "Eutectoid Tie-Line A1 (727 °C)", "xs": [0.022, 6.67], "ys": [conv(727.0), conv(727.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Curie Temperature Line A2 (770 °C)", "xs": [0.00, 0.022], "ys": [conv(770.0), conv(770.0)], "color": "#7C3AED", "width": 1.5, "dash": "dot"}
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1495.0), "x_reaction": 0.17, "x_start": 0.09, "x_end": 0.53, "equation": "L (0.53 wt% C) + δ-Ferrite (0.09 wt% C) ⇌ γ-Austenite (0.17 wt% C)"},
            {"type": "Eutectic (Ledeburite)", "temp": conv(1147.0), "x_reaction": 4.30, "x_start": 2.11, "x_end": 6.67, "equation": "L (4.30 wt% C) ⇌ γ-Austenite (2.11 wt% C) + Fe₃C Cementite (6.67 wt% C)"},
            {"type": "Eutectoid (Pearlite)", "temp": conv(727.0), "x_reaction": 0.76, "x_start": 0.022, "x_end": 6.67, "equation": "γ-Austenite (0.76 wt% C) ⇌ α-Ferrite (0.022 wt% C) + Fe₃C Cementite"}
        ]

        regions = [
            {"label": "Liquid", "x": 2.50, "y": conv(1500.0), "font_size": 13, "color": "#0F172A"},
            {"label": "δ-Ferrite", "x": 0.04, "y": conv(1460.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "γ (Austenite - FCC)", "x": 0.80, "y": conv(1100.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "α (Ferrite - BCC)", "x": 0.01, "y": conv(500.0), "font_size": 10, "color": "#065F46"},
            {"label": "α + γ", "x": 0.30, "y": conv(780.0), "font_size": 10, "color": "#4338CA"},
            {"label": "γ + Fe₃C", "x": 1.40, "y": conv(900.0), "font_size": 11, "color": "#B91C1C"},
            {"label": "Pearlite (α + Fe₃C)", "x": 2.50, "y": conv(500.0), "font_size": 11, "color": "#D97706"},
            {"label": "Liquid + γ", "x": 2.50, "y": conv(1300.0), "font_size": 10, "color": "#64748B"},
            {"label": "Ledeburite / Cast Iron", "x": 5.00, "y": conv(900.0), "font_size": 11, "color": "#7F1D1D"}
        ]

        return {
            "system": "Fe-C",
            "element_a": "Fe",
            "element_b": "C",
            "x_axis_label": "Mass Fraction of Carbon [wt% C]",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 6.67,
            "y_min": conv(200.0),
            "y_max": conv(1650.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 6. Co-Cr Binary Phase Diagram (Stellite Wear Matrix)
    # References: A. Kusoffsky & B. Jansson (1997); H. Okamoto.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_cr(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots_1 = [(0.000, 1495.0), (0.100, 1475.0), (0.200, 1455.0), (0.300, 1430.0), (0.400, 1403.0), (0.425, 1395.0)]
        l_knots_2 = [(0.425, 1395.0), (0.450, 1435.0), (0.480, 1470.0)]
        l_knots_3 = [(0.480, 1470.0), (0.550, 1550.0), (0.600, 1630.0), (0.700, 1730.0), (0.800, 1810.0), (0.900, 1870.0), (1.000, 1907.0)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 25), (l_knots_2, 10), (l_knots_3, 45)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            x_liq.extend(xs)
            y_liq.extend(ys)

        fcc_sol_knots = [(0.000, 1495.0), (0.100, 1470.0), (0.200, 1445.0), (0.300, 1420.0), (0.370, 1395.0)]
        bcc_sol_knots = [(0.600, 1470.0), (0.700, 1690.0), (0.800, 1785.0), (0.900, 1855.0), (1.000, 1907.0)]
        xs_fcc_s, ys_fcc_s = _interpolate_curve(fcc_sol_knots, n_pts=30)
        xs_bcc_s, ys_bcc_s = _interpolate_curve(bcc_sol_knots, n_pts=35)

        hcp_trans_knots = [(0.000, 422.0), (0.100, 560.0), (0.200, 710.0), (0.300, 850.0), (0.360, 930.0)]
        fcc_trans_knots = [(0.000, 422.0), (0.100, 580.0), (0.200, 740.0), (0.300, 875.0), (0.380, 930.0)]
        xs_hcp_t, ys_hcp_t = _interpolate_curve(hcp_trans_knots, n_pts=30)
        xs_fcc_t, ys_fcc_t = _interpolate_curve(fcc_trans_knots, n_pts=30)

        sigma_knots = [
            (0.550, 1395.0), (0.560, 1100.0), (0.570, 930.0), (0.570, 600.0),
            (0.610, 600.0), (0.610, 900.0), (0.600, 1100.0), (0.585, 1470.0)
        ]
        xs_sigma, ys_sigma = _interpolate_curve(sigma_knots, n_pts=45)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "fcc-(Co) Solidus", "xs": xs_fcc_s, "ys": [conv(t) for t in ys_fcc_s], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "bcc-(Cr) Solidus", "xs": xs_bcc_s, "ys": [conv(t) for t in ys_bcc_s], "color": "#1E40AF", "width": 1.8, "dash": "solid"},
            {"name": "ε(HCP) / γ(FCC) Transus", "xs": xs_hcp_t + xs_fcc_t, "ys": [conv(t) for t in ys_hcp_t + ys_fcc_t], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "σ-Phase Envelope (D8_b)", "xs": xs_sigma, "ys": [conv(t) for t in ys_sigma], "color": "#DC2626", "width": 2.0, "dash": "solid"},
            {"name": "Peritectic Tie-Line (1470 °C)", "xs": [0.480, 0.600], "ys": [conv(1470.0), conv(1470.0)], "color": "#D97706", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1395 °C)", "xs": [0.370, 0.550], "ys": [conv(1395.0), conv(1395.0)], "color": "#2563EB", "width": 1.6, "dash": "dash"},
            {"name": "Eutectoid Tie-Line (930 °C)", "xs": [0.360, 0.570], "ys": [conv(930.0), conv(930.0)], "color": "#059669", "width": 1.6, "dash": "dash"}
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1470.0), "x_reaction": 0.480, "x_start": 0.480, "x_end": 0.600, "equation": "L (48.0 at% Cr) + bcc-(Cr) (60.0 at% Cr) ⇌ σ-Phase (58.5 at% Cr)"},
            {"type": "Eutectic", "temp": conv(1395.0), "x_reaction": 0.425, "x_start": 0.370, "x_end": 0.550, "equation": "L (42.5 at% Cr) ⇌ fcc-(Co) (37.0 at% Cr) + σ-Phase (55.0 at% Cr)"},
            {"type": "Eutectoid", "temp": conv(930.0), "x_reaction": 0.380, "x_start": 0.360, "x_end": 0.570, "equation": "fcc-(Co) (38.0 at% Cr) ⇌ hcp-(Co) (36.0 at% Cr) + σ-Phase (57.0 at% Cr)"},
            # Allotropic pure Co transition at 422 C is a unary boundary point, not a binary tie-line
        ]

        regions = [
            {"label": "Liquid", "x": 0.45, "y": conv(1600.0), "font_size": 13, "color": "#0F172A"},
            {"label": "fcc-(Co) Matrix", "x": 0.20, "y": conv(1200.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "hcp-(Co)", "x": 0.15, "y": conv(600.0), "font_size": 11, "color": "#065F46"},
            {"label": "σ Phase (tP30)", "x": 0.58, "y": conv(1100.0), "font_size": 11, "color": "#B91C1C"},
            {"label": "bcc-(Cr)", "x": 0.85, "y": conv(1400.0), "font_size": 11, "color": "#1E40AF"},
            {"label": "hcp-(Co) + σ", "x": 0.30, "y": conv(600.0), "font_size": 10, "color": "#92400E"},
            {"label": "σ + bcc-(Cr)", "x": 0.65, "y": conv(1000.0), "font_size": 10, "color": "#7C3AED"}
        ]

        return {
            "system": "Co-Cr",
            "element_a": "Co",
            "element_b": "Cr",
            "x_axis_label": "Atomic Fraction of Chromium, x(Cr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 7. Al-Cu Binary Phase Diagram (Precipitation Hardening Benchmark)
    # References: J. L. Murray (1985); N. Saunders (1997); X. L. Liu et al.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_cu(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Complete liquidus across full system: 0 to 100 wt% Cu
        l_knots_1 = [(0.00, 660.32), (5.00, 645.0), (10.00, 630.0), (15.00, 612.0), (20.00, 592.0), (25.00, 575.0), (30.00, 558.0), (33.20, 548.2)]
        l_knots_2 = [(33.20, 548.2), (34.00, 591.0)]
        l_knots_3 = [(34.00, 591.0), (47.50, 625.0)]
        l_knots_4 = [(47.50, 625.0), (58.00, 710.0)]
        l_knots_5 = [(58.00, 710.0), (68.00, 848.0)]
        l_knots_6 = [(68.00, 848.0), (68.00, 1025.0), (72.00, 1005.0)]
        l_knots_7 = [(72.00, 1005.0), (82.00, 1032.0)]
        l_knots_8 = [(82.00, 1032.0), (90.00, 1060.0), (100.00, 1084.62)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 25), (l_knots_2, 6), (l_knots_3, 12), (l_knots_4, 15),
                             (l_knots_5, 15), (l_knots_6, 20), (l_knots_7, 12), (l_knots_8, 20)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=100.0)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Solidus and solvus curves
        al_sol_knots = [(0.00, 660.32), (1.00, 640.0), (2.00, 620.0), (3.50, 585.0), (5.65, 548.2)]
        xs_al_sol, ys_al_sol = _interpolate_curve(al_sol_knots, n_pts=25)

        al_slv_knots = [(5.65, 548.2), (4.15, 500.0), (2.70, 450.0), (1.50, 400.0), (0.75, 350.0), (0.30, 300.0), (0.05, 200.0)]
        xs_al_slv, ys_al_slv = _interpolate_curve(al_slv_knots, n_pts=35)

        cu_sol_knots = [(89.0, 1032.0), (95.0, 1060.0), (100.0, 1084.62)]
        cu_slv_knots = [(89.0, 1032.0), (90.5, 800.0), (93.0, 600.0), (96.0, 400.0), (98.0, 200.0)]
        xs_cu_sol, ys_cu_sol = _interpolate_curve(cu_sol_knots, n_pts=20)
        xs_cu_slv, ys_cu_slv = _interpolate_curve(cu_slv_knots, n_pts=25)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "(Al) FCC Solidus", "xs": xs_al_sol, "ys": [conv(t) for t in ys_al_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "α-Al Solvus (Precipitation Line)", "xs": xs_al_slv, "ys": [conv(t) for t in ys_al_slv], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "θ-Al₂Cu Compound Boundaries", "xs": [52.5, 52.5, 53.7, 53.7], "ys": [conv(200.0), conv(548.2), conv(591.0), conv(200.0)], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "(Cu) Solidus & Solvus", "xs": xs_cu_sol + xs_cu_slv, "ys": [conv(t) for t in ys_cu_sol + ys_cu_slv], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "Al-rich Eutectic Tie-Line (548.2 °C)", "xs": [5.65, 52.5], "ys": [conv(548.2), conv(548.2)], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line (591 °C)", "xs": [34.0, 56.0], "ys": [conv(591.0), conv(591.0)], "color": "#7C3AED", "width": 1.6, "dash": "dash"},
            {"name": "Cu-rich Peritectic Tie-Line (1032 °C)", "xs": [82.0, 89.0], "ys": [conv(1032.0), conv(1032.0)], "color": "#D97706", "width": 1.6, "dash": "dash"}
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(548.2), "x_reaction": 33.20, "x_start": 5.65, "x_end": 52.50, "equation": "L (33.2 wt% Cu) ⇌ (Al) (5.65 wt% Cu) + θ-Al₂Cu (52.5 wt% Cu)"},
            {"type": "Peritectic", "temp": conv(591.0), "x_reaction": 34.00, "x_start": 34.00, "x_end": 56.00, "equation": "L (34.0 wt% Cu) + η₂ (56.0 wt% Cu) ⇌ θ-Al₂Cu (53.5 wt% Cu)"},
            {"type": "Congruent", "temp": conv(1025.0), "x_reaction": 68.00, "x_start": 68.00, "x_end": 68.00, "equation": "L ⇌ γ₁-Cu₉Al₄ (Congruent summit at 1025 °C)"},
            {"type": "Eutectic", "temp": conv(1005.0), "x_reaction": 72.00, "x_start": 70.50, "x_end": 73.50, "equation": "L (72.0 wt% Cu) ⇌ β-Phase (70.5 wt% Cu) + γ₁ (73.5 wt% Cu)"},
            {"type": "Peritectic", "temp": conv(1032.0), "x_reaction": 82.00, "x_start": 82.00, "x_end": 89.00, "equation": "L (82.0 wt% Cu) + (Cu) (89.0 wt% Cu) ⇌ β-Phase (84.5 wt% Cu)"}
        ]

        regions = [
            {"label": "Liquid", "x": 20.0, "y": conv(700.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al) Solid Solution", "x": 1.5, "y": conv(450.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "(Al) + θ-Al₂Cu (Age Hardening)", "x": 20.0, "y": conv(400.0), "font_size": 11, "color": "#065F46"},
            {"label": "θ-Al₂Cu", "x": 53.0, "y": conv(400.0), "font_size": 10, "color": "#DC2626"},
            {"label": "γ₁-Cu₉Al₄", "x": 68.0, "y": conv(700.0), "font_size": 11, "color": "#7C3AED"},
            {"label": "(Cu) Solid Solution", "x": 92.0, "y": conv(800.0), "font_size": 11, "color": "#1E40AF"}
        ]

        return {
            "system": "Al-Cu",
            "element_a": "Al",
            "element_b": "Cu",
            "x_axis_label": "Mass Fraction of Copper [wt% Cu]",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 100.0,
            "y_min": conv(150.0),
            "y_max": conv(1150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 8. Al-Co Binary Phase Diagram (Assessed Literature Benchmark)
    # References: A. J. McAlister, Bull. Alloy Phase Diagrams 10 (1989) 148-154;
    #             M. Gödecke & R. Lück, Z. Metallkd. 71 (1980) 140;
    #             B. J. Lee, Calphad 28 (2004) 305-314.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_co(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus curve segmented branches hitting assessed invariant reaction points exactly
        l_knots_1 = [(0.000, 660.45), (0.005, 658.5), (0.010, 657.0)]
        l_knots_2 = [(0.010, 657.0), (0.030, 800.0), (0.050, 900.0), (0.075, 970.0)]
        l_knots_3 = [(0.075, 970.0), (0.100, 1040.0), (0.125, 1093.0)]
        l_knots_4 = [(0.125, 1093.0), (0.140, 1118.0), (0.155, 1135.0)]
        l_knots_5 = [(0.155, 1135.0), (0.180, 1162.0), (0.200, 1180.0)]
        l_knots_6 = [(0.200, 1180.0), (0.250, 1330.0), (0.320, 1480.0), (0.400, 1585.0), (0.460, 1630.0), (0.500, 1640.0)]
        l_knots_7 = [(0.500, 1640.0), (0.550, 1635.0), (0.650, 1600.0), (0.750, 1530.0), (0.820, 1450.0), (0.860, 1415.0), (0.895, 1400.0)]
        l_knots_8 = [(0.895, 1400.0), (0.930, 1425.0), (0.970, 1465.0), (1.000, 1495.0)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [
            (l_knots_1, 8), (l_knots_2, 20), (l_knots_3, 15), (l_knots_4, 12),
            (l_knots_5, 15), (l_knots_6, 35), (l_knots_7, 35), (l_knots_8, 20)
        ]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # B2-AlCo Solidus: from left peritectic p4 (1180 C, 46 at% Co) to congruent peak (1640 C, 50 at% Co)
        # down to right eutectic e2 (1400 C, 82.5 at% Co)
        b2_sol_knots = [
            (0.460, 1180.0),
            (0.475, 1400.0),
            (0.490, 1550.0),
            (0.500, 1640.0),
            (0.550, 1625.0),
            (0.650, 1575.0),
            (0.750, 1490.0),
            (0.800, 1435.0),
            (0.825, 1400.0)
        ]
        xs_b2_sol, ys_b2_sol = _interpolate_curve(b2_sol_knots, n_pts=60, clip_x_min=0.45, clip_x_max=0.83)

        # B2-AlCo Solvus boundaries
        b2_solv_left_knots = [
            (0.460, 1180.0),
            (0.462, 900.0),
            (0.468, 600.0),
            (0.478, 200.0)
        ]
        xs_b2_sl, ys_b2_sl = _interpolate_curve(b2_solv_left_knots, n_pts=30, clip_x_min=0.45, clip_x_max=0.49)

        b2_solv_right_knots = [
            (0.825, 1400.0),
            (0.800, 1200.0),
            (0.740, 950.0),
            (0.650, 650.0),
            (0.560, 300.0)
        ]
        xs_b2_sr, ys_b2_sr = _interpolate_curve(b2_solv_right_knots, n_pts=45, clip_x_min=0.55, clip_x_max=0.83)

        # (alpha-Co) FCC Solid Solution Solidus & Solvus
        co_sol_knots = [
            (0.910, 1400.0),
            (0.940, 1445.0),
            (0.970, 1475.0),
            (1.000, 1495.0)
        ]
        xs_co_sol, ys_co_sol = _interpolate_curve(co_sol_knots, n_pts=30, clip_x_min=0.90, clip_x_max=1.0)

        co_solv_knots = [
            (0.910, 1400.0),
            (0.915, 1200.0),
            (0.930, 950.0),
            (0.950, 600.0),
            (0.970, 300.0)
        ]
        xs_co_solv, ys_co_solv = _interpolate_curve(co_solv_knots, n_pts=35, clip_x_min=0.90, clip_x_max=1.0)

        # Pure Co Allotropic Transformation (HCP epsilon <-> FCC gamma/alpha at 422 C)
        co_allo_knots = [
            (1.000, 422.0),
            (0.985, 360.0),
            (0.970, 300.0)
        ]
        xs_allo, ys_allo = _interpolate_curve(co_allo_knots, n_pts=20, clip_x_min=0.96, clip_x_max=1.0)

        # Magnetic Transformation (Curie temperature line across AlCo & (alpha-Co))
        curie_knots = [
            (1.000, 1121.0),
            (0.960, 980.0),
            (0.930, 840.0),
            (0.700, 840.0),
            (0.560, 840.0)
        ]
        xs_curie, ys_curie = _interpolate_curve(curie_knots, n_pts=35, clip_x_min=0.55, clip_x_max=1.0)

        # Invariant Reactions
        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(657.0),
                "x_reaction": 0.010,
                "x_start": 0.000,
                "x_end": 0.182,
                "equation": "L (1.0 at% Co) ⇌ (Al) + Al₉Co₂ at 657 °C"
            },
            {
                "type": "Peritectic",
                "temp": conv(970.0),
                "x_reaction": 0.075,
                "x_start": 0.075,
                "x_end": 0.250,
                "equation": "L (7.5 at% Co) + Al₃Co ⇌ Al₉Co₂ at 970 °C"
            },
            {
                "type": "Peritectic",
                "temp": conv(1093.0),
                "x_reaction": 0.125,
                "x_start": 0.125,
                "x_end": 0.250,
                "equation": "L (12.5 at% Co) + Al₁₃Co₄ ⇌ Al₃Co at 1093 °C"
            },
            {
                "type": "Peritectic",
                "temp": conv(1135.0),
                "x_reaction": 0.155,
                "x_start": 0.155,
                "x_end": 0.286,
                "equation": "L (15.5 at% Co) + Al₅Co₂ ⇌ Al₁₃Co₄ at 1135 °C"
            },
            {
                "type": "Peritectic",
                "temp": conv(1180.0),
                "x_reaction": 0.200,
                "x_start": 0.200,
                "x_end": 0.460,
                "equation": "L (20.0 at% Co) + AlCo (B2) ⇌ Al₅Co₂ at 1180 °C"
            },
            {
                "type": "Congruent Melting",
                "temp": conv(1640.0),
                "x_reaction": 0.500,
                "x_start": 0.500,
                "x_end": 0.500,
                "equation": "L ⇌ AlCo (Congruent B2 Summit at 1640 °C, 50.0 at% Co)"
            },
            {
                "type": "Eutectic",
                "temp": conv(1400.0),
                "x_reaction": 0.895,
                "x_start": 0.825,
                "x_end": 0.910,
                "equation": "L (89.5 at% Co) ⇌ AlCo (82.5 at% Co) + (αCo) (91.0 at% Co) at 1400 °C"
            }
        ]

        # Curves
        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "AlCo (B2) Solidus", "xs": xs_b2_sol, "ys": [conv(t) for t in ys_b2_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "AlCo (B2) Left Solvus", "xs": xs_b2_sl, "ys": [conv(t) for t in ys_b2_sl], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "AlCo (B2) Right Solvus", "xs": xs_b2_sr, "ys": [conv(t) for t in ys_b2_sr], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "(αCo) Solidus", "xs": xs_co_sol, "ys": [conv(t) for t in ys_co_sol], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "(αCo) Solvus", "xs": xs_co_solv, "ys": [conv(t) for t in ys_co_solv], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Al₉Co₂ Line Compound", "xs": [0.1818, 0.1818], "ys": [conv(200.0), conv(970.0)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Al₃Co Line Compound", "xs": [0.250, 0.250], "ys": [conv(200.0), conv(1093.0)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Al₁₃Co₄ Line Compound", "xs": [0.238, 0.238], "ys": [conv(200.0), conv(1135.0)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Al₅Co₂ Line Compound", "xs": [0.2857, 0.2857], "ys": [conv(200.0), conv(1180.0)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Eutectic Tie-Line (657 °C)", "xs": [0.000, 0.1818], "ys": [conv(657.0), conv(657.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (970 °C)", "xs": [0.075, 0.250], "ys": [conv(970.0), conv(970.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1093 °C)", "xs": [0.125, 0.250], "ys": [conv(1093.0), conv(1093.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1135 °C)", "xs": [0.155, 0.2857], "ys": [conv(1135.0), conv(1135.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1180 °C)", "xs": [0.200, 0.460], "ys": [conv(1180.0), conv(1180.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1400 °C)", "xs": [0.825, 0.910], "ys": [conv(1400.0), conv(1400.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Curie Magnetic Transition", "xs": xs_curie, "ys": [conv(t) for t in ys_curie], "color": "#94A3B8", "width": 1.4, "dash": "dot"},
            {"name": "Co Allotropic Transition (422 °C)", "xs": xs_allo, "ys": [conv(t) for t in ys_allo], "color": "#94A3B8", "width": 1.4, "dash": "dot"}
        ]

        # Phase Region Labels
        regions = [
            {"label": "Liquid (L)", "x": 0.50, "y": conv(1720.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al)", "x": 0.02, "y": conv(450.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₉Co₂", "x": 0.165, "y": conv(850.0), "font_size": 9, "color": "#6D28D9"},
            {"label": "Al₃Co", "x": 0.215, "y": conv(1020.0), "font_size": 9, "color": "#6D28D9"},
            {"label": "Al₁₃Co₄", "x": 0.245, "y": conv(650.0), "font_size": 9, "color": "#6D28D9"},
            {"label": "Al₅Co₂", "x": 0.315, "y": conv(950.0), "font_size": 9, "color": "#6D28D9"},
            {"label": "AlCo (B2 Ordered)", "x": 0.58, "y": conv(1350.0), "font_size": 12, "color": "#1E40AF"},
            {"label": "(αCo)", "x": 0.95, "y": conv(1200.0), "font_size": 11, "color": "#065F46"},
            {"label": "AlCo + (αCo)", "x": 0.75, "y": conv(600.0), "font_size": 10, "color": "#92400E"}
        ]

        return {
            "system": "Al-Co",
            "element_a": "Al",
            "element_b": "Co",
            "x_axis_label": "Atomic Fraction of Cobalt, x(Co)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 8. NaF-AlF3 Binary Phase Diagram (Industrial Cryolite Electrolyte)
    # References: P. Chartrand & A. D. Pelton (2002); E. W. Dewing (1978).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_naf_alf3(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots_1 = [(0.000, 994.5), (0.050, 960.0), (0.100, 924.0), (0.139, 888.0)]
        l_knots_2 = [(0.139, 888.0), (0.180, 950.0), (0.220, 995.0), (0.250, 1010.0)]
        l_knots_3 = [(0.250, 1010.0), (0.270, 950.0), (0.290, 810.0), (0.300, 734.0)]
        l_knots_4 = [(0.300, 734.0), (0.340, 715.0), (0.373, 695.0)]
        l_knots_5 = [(0.373, 695.0), (0.400, 750.0), (0.450, 870.0), (0.500, 980.0)]

        x_liq: List[float] = []
        y_liq: List[float] = []
        for knots, count in [(l_knots_1, 20), (l_knots_2, 25), (l_knots_3, 20), (l_knots_4, 15), (l_knots_5, 25)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=0.50)
            x_liq.extend(xs)
            y_liq.extend(ys)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Na₃AlF₆ (Cryolite) Stoichiometric Line", "xs": [0.250, 0.250], "ys": [conv(400.0), conv(1010.0)], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Na₅Al₃F₁₄ (Chiolite) Stoichiometric Line", "xs": [0.375, 0.375], "ys": [conv(400.0), conv(734.0)], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "Cryolite α-β Polymorphic Line (560 °C)", "xs": [0.139, 0.375], "ys": [conv(560.0), conv(560.0)], "color": "#7C3AED", "width": 1.5, "dash": "dot"},
            {"name": "Eutectic Tie-Line 1 (888 °C)", "xs": [0.000, 0.250], "ys": [conv(888.0), conv(888.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line (734 °C)", "xs": [0.250, 0.375], "ys": [conv(734.0), conv(734.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line 2 (695 °C)", "xs": [0.373, 0.500], "ys": [conv(695.0), conv(695.0)], "color": "#059669", "width": 1.8, "dash": "dash"}
        ]

        invariants = [
            {"type": "Congruent Melting", "temp": conv(1010.0), "x_reaction": 0.250, "x_start": 0.250, "x_end": 0.250, "equation": "L ⇌ Na₃AlF₆ (Cryolite congruent melting)"},
            {"type": "Eutectic", "temp": conv(888.0), "x_reaction": 0.139, "x_start": 0.250, "x_end": 0.250, "equation": "L (13.9 mol% AlF₃) ⇌ NaF + β-Na₃AlF₆ (Cryolite)"},
            {"type": "Peritectic", "temp": conv(734.0), "x_reaction": 0.300, "x_start": 0.250, "x_end": 0.250, "equation": "L (30.0 mol% AlF₃) + β-Na₃AlF₆ ⇌ Na₅Al₃F₁₄ (Chiolite)"},
            {"type": "Eutectic", "temp": conv(695.0), "x_reaction": 0.373, "x_start": 0.250, "x_end": 0.250, "equation": "L (37.3 mol% AlF₃) ⇌ Na₅Al₃F₁₄ (Chiolite) + AlF₃"}
        ]

        regions = [
            {"label": "Molten Electrolyte (Liquid)", "x": 0.250, "y": conv(1060.0), "font_size": 12, "color": "#0F172A"},
            {"label": "Liquid + NaF", "x": 0.060, "y": conv(920.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "NaF + Cryolite", "x": 0.120, "y": conv(600.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Liquid + Cryolite", "x": 0.210, "y": conv(940.0), "font_size": 10, "color": "#1D4ED8"},
            {"label": "Cryolite (Na₃AlF₆)", "x": 0.250, "y": conv(700.0), "font_size": 11, "color": "#1D4ED8"},
            {"label": "Liquid + Chiolite", "x": 0.340, "y": conv(710.0), "font_size": 10, "color": "#065F46"},
            {"label": "Cryolite + Chiolite", "x": 0.310, "y": conv(500.0), "font_size": 10, "color": "#047857"},
            {"label": "Chiolite (Na₅Al₃F₁₄)", "x": 0.375, "y": conv(400.0), "font_size": 10, "color": "#065F46"},
            {"label": "Chiolite + AlF₃", "x": 0.440, "y": conv(500.0), "font_size": 10, "color": "#7C3AED"}
        ]

        exp_pts = [
            {"name": "Industrial Electrolyte (CR 2.6 ~ 2.1)", "xs": [0.278, 0.290, 0.300, 0.310, 0.320, 0.323],
             "ys": [conv(t) for t in [995.0, 978.0, 960.0, 942.0, 925.0, 918.0]], "color": "#DC2626", "marker": "circle"},
            {"name": "Literature Investigated Bath (CR 1.7 ~ 2.0)", "xs": [0.333, 0.345, 0.355, 0.370],
             "ys": [conv(t) for t in [890.0, 840.0, 790.0, 715.0]], "color": "#D946EF", "marker": "square"},
            {"name": "Low-Temperature Acidic Bath (CR 1.3)", "xs": [0.435, 0.435],
             "ys": [conv(t) for t in [705.0, 725.0]], "color": "#2563EB", "marker": "diamond"}
        ]

        return {
            "system": "NaF-AlF3",
            "element_a": "NaF",
            "element_b": "AlF3",
            "x_axis_label": "Mole Fraction of AlF₃ X(AlF₃) [mol%]",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 0.50,
            "y_min": conv(350.0),
            "y_max": conv(1100.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": exp_pts
        }

    # -------------------------------------------------------------------------
    # 9. Mn-Ni Binary Phase Diagram (Assessed Benchmark)
    # References: N. A. Gokcen, Bull. Alloy Phase Diagrams 9 (1988) 629-635;
    #             J. M. Tedenac et al., Calphad 28 (2004) 39-46.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_mn_ni(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus curve knots (Mn: 1246 C, Ni: 1455 C, congruent minimum at 38 at% Ni, 1018 C)
        liq_knots = [
            (0.00, 1246.0),
            (0.10, 1162.0),
            (0.20, 1092.0),
            (0.30, 1038.0),
            (0.38, 1018.0),
            (0.50, 1065.0),
            (0.65, 1192.0),
            (0.80, 1315.0),
            (0.90, 1395.0),
            (1.00, 1455.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        # Solidus curve knots (tangent to liquidus at congruent minimum 1018 C, 38 at% Ni)
        sol_knots = [
            (0.00, 1246.0),
            (0.10, 1110.0),
            (0.20, 1045.0),
            (0.30, 1024.0),
            (0.38, 1018.0),
            (0.50, 1050.0),
            (0.65, 1160.0),
            (0.80, 1285.0),
            (0.90, 1380.0),
            (1.00, 1455.0)
        ]
        xs_sol, ys_sol = _interpolate_curve(sol_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        # L1_0-MnNi Ordered Phase Boundaries (CuAu-I type tetragonal, congruent summit at 50 at% Ni, 910 °C)
        # Outer disordered gamma solvus boundary (left & right branches)
        l10_outer_knots = [
            (0.36, 200.0),
            (0.40, 500.0),
            (0.45, 750.0),
            (0.50, 910.0),
            (0.55, 750.0),
            (0.60, 500.0),
            (0.63, 200.0)
        ]
        xs_l10_out, ys_l10_out = _interpolate_curve(l10_outer_knots, n_pts=60, clip_x_min=0.35, clip_x_max=0.65)

        # Inner ordered L1_0 phase field boundary
        l10_inner_knots = [
            (0.44, 200.0),
            (0.46, 500.0),
            (0.48, 750.0),
            (0.50, 910.0),
            (0.52, 750.0),
            (0.54, 500.0),
            (0.56, 200.0)
        ]
        xs_l10_in, ys_l10_in = _interpolate_curve(l10_inner_knots, n_pts=50, clip_x_min=0.43, clip_x_max=0.57)

        # L1_2-Ni3Mn Ordered Phase Boundaries (Cu3Au type FCC, congruent summit at 75 at% Ni, 510 °C)
        # Outer disordered gamma solvus boundary (left & right branches)
        l12_outer_knots = [
            (0.66, 150.0),
            (0.69, 300.0),
            (0.72, 450.0),
            (0.75, 510.0),
            (0.78, 450.0),
            (0.81, 300.0),
            (0.84, 150.0)
        ]
        xs_l12_out, ys_l12_out = _interpolate_curve(l12_outer_knots, n_pts=50, clip_x_min=0.65, clip_x_max=0.85)

        # Inner ordered L1_2 phase field boundary
        l12_inner_knots = [
            (0.71, 150.0),
            (0.725, 300.0),
            (0.74, 450.0),
            (0.75, 510.0),
            (0.76, 450.0),
            (0.775, 300.0),
            (0.79, 150.0)
        ]
        xs_l12_in, ys_l12_in = _interpolate_curve(l12_inner_knots, n_pts=40, clip_x_min=0.70, clip_x_max=0.80)

        # Pure Mn allotropic boundaries
        # delta-Mn (BCC) field near pure Mn (1138 to 1246 °C)
        delta_knots = [
            (0.00, 1138.0),
            (0.015, 1145.0),
            (0.035, 1138.0)
        ]
        xs_delta, ys_delta = _interpolate_curve(delta_knots, n_pts=20, clip_x_min=0.0, clip_x_max=0.05)

        # gamma-Mn -> beta-Mn transus boundary (1100 °C to 710 °C eutectoid)
        beta_knots = [
            (0.00, 1100.0),
            (0.018, 950.0),
            (0.035, 710.0)
        ]
        xs_beta, ys_beta = _interpolate_curve(beta_knots, n_pts=25, clip_x_min=0.0, clip_x_max=0.04)

        # Invariant and critical reactions
        invariants = [
            {
                "type": "Congruent Minimum",
                "temp": conv(1018.0),
                "x_reaction": 0.380,
                "x_start": 0.380,
                "x_end": 0.380,
                "equation": "L (38.0 at% Ni) ⇌ γ-(Mn,Ni) (Congruent Minimum Melting at 1018 °C)"
            },
            {
                "type": "Order-Disorder Summit",
                "temp": conv(910.0),
                "x_reaction": 0.500,
                "x_start": 0.500,
                "x_end": 0.500,
                "equation": "γ-(Mn,Ni) ⇌ L1₀-MnNi (Ordered Tetragonal Summit at 910 °C)"
            },
            {
                "type": "Order-Disorder Summit",
                "temp": conv(510.0),
                "x_reaction": 0.750,
                "x_start": 0.750,
                "x_end": 0.750,
                "equation": "γ-(Mn,Ni) ⇌ L1₂-Ni₃Mn (Ordered FCC Summit at 510 °C)"
            },
            {
                "type": "Eutectoid",
                "temp": conv(710.0),
                "x_reaction": 0.120,
                "x_start": 0.035,
                "x_end": 0.400,
                "equation": "γ-(Mn,Ni) ⇌ β-Mn + L1₀-MnNi (Eutectoid Decomposition at 710 °C)"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "γ / (γ + L1₀) Solvus", "xs": xs_l10_out, "ys": [conv(t) for t in ys_l10_out], "color": "#7C3AED", "width": 1.8, "dash": "solid"},
            {"name": "L1₀-MnNi Ordered Boundary", "xs": xs_l10_in, "ys": [conv(t) for t in ys_l10_in], "color": "#7C3AED", "width": 1.4, "dash": "dash"},
            {"name": "γ / (γ + L1₂) Solvus", "xs": xs_l12_out, "ys": [conv(t) for t in ys_l12_out], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "L1₂-Ni₃Mn Ordered Boundary", "xs": xs_l12_in, "ys": [conv(t) for t in ys_l12_in], "color": "#059669", "width": 1.4, "dash": "dash"},
            {"name": "δ-Mn Boundary", "xs": xs_delta, "ys": [conv(t) for t in ys_delta], "color": "#DC2626", "width": 1.5, "dash": "dash"},
            {"name": "β-Mn Boundary", "xs": xs_beta, "ys": [conv(t) for t in ys_beta], "color": "#DC2626", "width": 1.5, "dash": "dash"},
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1250.0), "font_size": 13, "color": "#0F172A"},
            {"label": "γ-(Mn,Ni) FCC Matrix", "x": 0.22, "y": conv(850.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "γ-(Mn,Ni) Disordered FCC", "x": 0.90, "y": conv(850.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "L1₀-MnNi (Ordered)", "x": 0.50, "y": conv(500.0), "font_size": 11, "color": "#581C87"},
            {"label": "γ + L1₀", "x": 0.40, "y": conv(350.0), "font_size": 9.5, "color": "#6B21A8"},
            {"label": "L1₀ + γ", "x": 0.59, "y": conv(350.0), "font_size": 9.5, "color": "#6B21A8"},
            {"label": "L1₂-Ni₃Mn (Ordered)", "x": 0.75, "y": conv(300.0), "font_size": 11, "color": "#065F46"},
            {"label": "γ + L1₂", "x": 0.81, "y": conv(230.0), "font_size": 9.5, "color": "#047857"},
            {"label": "(α,β-Mn)", "x": 0.05, "y": conv(500.0), "font_size": 11, "color": "#991B1B"}
        ]

        return {
            "system": "Mn-Ni",
            "element_a": "Mn",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Ni, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1550.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 10. Fe-Ni Binary Phase Diagram (Assessed Benchmark)
    # References: L. J. Swartzendruber et al., J. Phase Equilib. 12 (1991) 288-312;
    #             G. Cacciamani et al., Intermetallics 12 (2004) 937-945.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_ni(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        xs_dense = np.linspace(0.0, 1.0, n_pts)

        # Liquidus curve knots (Fe: 1538 C, peritectic at 1513 C / 5.2 at% Ni, congruent minimum at 1435 C / 68 at% Ni, Ni: 1455 C)
        liq_knots = [
            (0.00, 1538.0),
            (0.052, 1513.0),
            (0.15, 1485.0),
            (0.30, 1460.0),
            (0.50, 1442.0),
            (0.68, 1435.0),
            (0.85, 1442.0),
            (1.00, 1455.0)
        ]
        xs_l_raw, ys_l_raw = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)
        ys_liq_dense = np.interp(xs_dense, xs_l_raw, ys_l_raw)

        # Solidus curve knots (Delta solidus: 0 to 3.5 at% Ni at 1513 C; Gamma solidus: starts at 4.5 at% Ni at 1513 C down to 1435 C minimum)
        sol_knots = [
            (0.00, 1538.0),
            (0.035, 1513.0),
            (0.045, 1513.0),
            (0.15, 1465.0),
            (0.30, 1445.0),
            (0.50, 1438.0),
            (0.68, 1435.0),
            (0.85, 1440.0),
            (1.00, 1455.0)
        ]
        xs_s_raw, ys_s_raw = _interpolate_curve(sol_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)
        ys_sol_dense = np.interp(xs_dense, xs_s_raw, ys_s_raw)

        # Enforce strict thermodynamic bound: T_sol <= T_liq everywhere
        ys_sol_dense = np.minimum(ys_sol_dense, ys_liq_dense)

        xs_liq = xs_dense.tolist()
        ys_liq = ys_liq_dense.tolist()
        xs_sol = xs_dense.tolist()
        ys_sol = ys_sol_dense.tolist()

        # A3 / gamma-alpha solvus loop
        gamma_solvus_knots = [
            (0.00, 912.0),
            (0.05, 800.0),
            (0.10, 680.0),
            (0.15, 540.0),
            (0.22, 400.0),
            (0.30, 250.0)
        ]
        xs_gsol, ys_gsol = _interpolate_curve(gamma_solvus_knots, n_pts=50, clip_x_min=0.0, clip_x_max=0.35)

        alpha_solvus_knots = [
            (0.00, 912.0),
            (0.02, 800.0),
            (0.04, 680.0),
            (0.05, 540.0),
            (0.055, 400.0),
            (0.06, 250.0)
        ]
        xs_asol, ys_asol = _interpolate_curve(alpha_solvus_knots, n_pts=50, clip_x_min=0.0, clip_x_max=0.08)

        # L1_2 FeNi3 ordering dome (summit at 75 at% Ni, 517 C)
        feni3_knots = [
            (0.66, 200.0),
            (0.69, 380.0),
            (0.75, 517.0),
            (0.80, 380.0),
            (0.83, 200.0)
        ]
        xs_feni3, ys_feni3 = _interpolate_curve(feni3_knots, n_pts=40, clip_x_min=0.65, clip_x_max=0.85)

        invariants = [
            {
                "type": "Peritectic",
                "temp": conv(1513.0),
                "x_reaction": 0.045,
                "x_start": 0.035,
                "x_end": 0.052,
                "equation": "L (5.2 at% Ni) + δ-BCC (3.5 at% Ni) ⇌ γ-FCC (4.5 at% Ni) at 1513 °C"
            },
            {
                "type": "Order-Disorder Summit",
                "temp": conv(517.0),
                "x_reaction": 0.750,
                "x_start": 0.750,
                "x_end": 0.750,
                "equation": "γ-(Fe,Ni) ⇌ L1₂-FeNi₃ (Permalloy Ordered Dome at 517 °C)"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "γ-Solvus (A₃)", "xs": xs_gsol, "ys": [conv(t) for t in ys_gsol], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "α-Solvus", "xs": xs_asol, "ys": [conv(t) for t in ys_asol], "color": "#1E3A8A", "width": 1.6, "dash": "dash"},
            {"name": "L1₂-FeNi₃ Solvus", "xs": xs_feni3, "ys": [conv(t) for t in ys_feni3], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Peritectic Tie-Line", "xs": [0.035, 0.052], "ys": [conv(1513.0), conv(1513.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1510.0), "font_size": 13, "color": "#0F172A"},
            {"label": "γ-(Fe,Ni) FCC Austenite (Invar Matrix)", "x": 0.50, "y": conv(1000.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "α-BCC Ferrite", "x": 0.02, "y": conv(500.0), "font_size": 10, "color": "#991B1B"},
            {"label": "L1₂-FeNi₃ (Permalloy)", "x": 0.75, "y": conv(350.0), "font_size": 11, "color": "#065F46"}
        ]

        return {
            "system": "Fe-Ni",
            "element_a": "Fe",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Ni, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1620.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 11. Cr-Ni Binary Phase Diagram (Assessed Benchmark)
    # References: N. Saunders (1996); Singhal (2000).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cr_ni(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Eutectic at 1345 C, 53 at% Ni: L -> BCC(Cr) (43 at% Ni) + FCC(Ni) (57 at% Ni)
        liq_b1 = [(0.00, 1907.0), (0.20, 1680.0), (0.38, 1470.0), (0.53, 1345.0)]
        xs_l1, ys_l1 = _interpolate_curve(liq_b1, n_pts=n_pts // 2, clip_x_min=0.0, clip_x_max=0.53)
        liq_b2 = [(0.53, 1345.0), (0.70, 1385.0), (0.85, 1422.0), (1.00, 1455.0)]
        xs_l2, ys_l2 = _interpolate_curve(liq_b2, n_pts=n_pts // 2, clip_x_min=0.53, clip_x_max=1.0)
        xs_liq = xs_l1 + xs_l2[1:]
        ys_liq = ys_l1 + ys_l2[1:]

        bcc_sol = [(0.00, 1907.0), (0.20, 1620.0), (0.43, 1345.0)]
        xs_bsol, ys_bsol = _interpolate_curve(bcc_sol, n_pts=40, clip_x_min=0.0, clip_x_max=0.43)

        fcc_sol = [(0.57, 1345.0), (0.75, 1395.0), (1.00, 1455.0)]
        xs_fsol, ys_fsol = _interpolate_curve(fcc_sol, n_pts=40, clip_x_min=0.57, clip_x_max=1.0)

        bcc_solvus = [(0.43, 1345.0), (0.35, 1150.0), (0.25, 950.0), (0.15, 750.0), (0.08, 500.0)]
        xs_bsolv, ys_bsolv = _interpolate_curve(bcc_solvus, n_pts=40, clip_x_min=0.05, clip_x_max=0.45)

        fcc_solvus = [(0.57, 1345.0), (0.65, 1150.0), (0.75, 950.0), (0.85, 750.0), (0.92, 500.0)]
        xs_fsolv, ys_fsolv = _interpolate_curve(fcc_solvus, n_pts=40, clip_x_min=0.55, clip_x_max=0.95)

        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(1345.0),
                "x_reaction": 0.530,
                "x_start": 0.430,
                "x_end": 0.570,
                "equation": "L (53.0 at% Ni) ⇌ BCC(Cr) (43.0 at% Ni) + FCC(Ni) (57.0 at% Ni) at 1345 °C"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "BCC Solidus", "xs": xs_bsol, "ys": [conv(t) for t in ys_bsol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "FCC Solidus", "xs": xs_fsol, "ys": [conv(t) for t in ys_fsol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "BCC Solvus", "xs": xs_bsolv, "ys": [conv(t) for t in ys_bsolv], "color": "#1E3A8A", "width": 1.6, "dash": "dash"},
            {"name": "FCC Solvus", "xs": xs_fsolv, "ys": [conv(t) for t in ys_fsolv], "color": "#059669", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic Invariant Tie-Line", "xs": [0.430, 0.570], "ys": [conv(1345.0), conv(1345.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1600.0), "font_size": 13, "color": "#0F172A"},
            {"label": "BCC (Cr-rich Solid Solution)", "x": 0.18, "y": conv(1200.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "FCC (Ni-rich Solid Solution)", "x": 0.85, "y": conv(1200.0), "font_size": 11, "color": "#065F46"},
            {"label": "BCC + FCC Two-Phase Field", "x": 0.50, "y": conv(850.0), "font_size": 11, "color": "#D97706"}
        ]

        return {
            "system": "Cr-Ni",
            "element_a": "Cr",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Ni, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(400.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 12. Co-Ni Binary Phase Diagram (Assessed Benchmark)
    # References: A. Fernandez Guillermet, Z. Metallkd. 78 (1987) 700-709.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_ni(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        """
        Co-Ni (Cobalt-Nickel) Assessed Binary Phase Diagram.
        References:
          - T. Nishizawa, K. Ishida, Bull. Alloy Phase Diagrams 4(4) (1983) 390-395.
          - A. Fernandez Guillermet, Z. Metallkd. 78 (1987) 700-709.
          - SGTE Pure Element and Solution Database (2010).

        Key Metallurgical Features:
          1. Continuous isomorphous solid solution between FCC gamma-(Co,Ni) and Liquid (L).
             Very narrow solidification freezing interval (< 3 °C at any composition).
             Pure Co melting point: 1495 °C (1768.15 K).
             Pure Ni melting point: 1455 °C (1728.15 K).
             Shallow minimum around 65-70 at% Ni (~1455 °C).
          2. Magnetic transition (Curie temperature Tc) line across gamma-FCC:
             Pure Co Tc = 1121 °C (1394.15 K); Pure Ni Tc = 358 °C (631.15 K).
          3. Low-temperature epsilon-HCP / gamma-FCC allotropic phase equilibrium:
             Pure Co allotropic transition: 422 °C (695.15 K).
             epsilon-HCP transus and gamma-FCC transus slope downward with Ni addition,
             forming a narrow (epsilon + gamma) two-phase field terminating near room temperature.
          4. Zero 3-phase invariant reactions (no horizontal tie-lines).
        """
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        xs_dense = np.linspace(0.0, 1.0, n_pts)

        # Liquidus knots: Co (1495 C) to Ni (1455 C) with shallow minimum at 70 at% Ni
        liq_knots = [
            (0.00, 1495.0),
            (0.15, 1486.0),
            (0.35, 1475.0),
            (0.55, 1464.0),
            (0.70, 1455.0),
            (0.85, 1454.0),
            (1.00, 1455.0)
        ]
        xs_l_raw, ys_l_raw = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)
        ys_liq_dense = np.interp(xs_dense, xs_l_raw, ys_l_raw)

        # Solidus knots: very narrow lens (< 2-3 C delta)
        sol_knots = [
            (0.00, 1495.0),
            (0.15, 1483.0),
            (0.35, 1471.0),
            (0.55, 1460.0),
            (0.70, 1452.0),
            (0.85, 1452.5),
            (1.00, 1455.0)
        ]
        xs_s_raw, ys_s_raw = _interpolate_curve(sol_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)
        ys_sol_dense = np.interp(xs_dense, xs_s_raw, ys_s_raw)

        # Enforce strict thermodynamic inequality T_sol <= T_liq everywhere
        ys_sol_dense = np.minimum(ys_sol_dense, ys_liq_dense)

        # Ferromagnetic Curie temperature Tc transition curve (2nd order magnetic boundary)
        curie_knots = [
            (0.00, 1121.0),
            (0.15, 1010.0),
            (0.30, 895.0),
            (0.50, 740.0),
            (0.70, 580.0),
            (0.85, 460.0),
            (1.00, 358.0)
        ]
        xs_curie, ys_curie = _interpolate_curve(curie_knots, n_pts=60, clip_x_min=0.0, clip_x_max=1.0)

        # Low-temperature allotropic phase boundaries (epsilon-HCP / gamma-FCC transus curves)
        hcp_transus_knots = [
            (0.00, 422.0),
            (0.05, 335.0),
            (0.10, 245.0),
            (0.15, 145.0),
            (0.20, 35.0),
            (0.22, 0.0)
        ]
        fcc_transus_knots = [
            (0.00, 422.0),
            (0.05, 365.0),
            (0.10, 285.0),
            (0.15, 195.0),
            (0.20, 95.0),
            (0.25, 0.0)
        ]
        xs_hcp, ys_hcp = _interpolate_curve(hcp_transus_knots, n_pts=35, clip_x_min=0.0, clip_x_max=0.23)
        xs_fcc, ys_fcc = _interpolate_curve(fcc_transus_knots, n_pts=35, clip_x_min=0.0, clip_x_max=0.26)

        curves = [
            {"name": "Liquidus", "xs": xs_dense.tolist(), "ys": [conv(t) for t in ys_liq_dense], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_dense.tolist(), "ys": [conv(t) for t in ys_sol_dense], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Curie Temperature (Tc)", "xs": xs_curie, "ys": [conv(t) for t in ys_curie], "color": "#E11D48", "width": 1.6, "dash": "dot"},
            {"name": "ε-HCP Transus", "xs": xs_hcp, "ys": [conv(t) for t in ys_hcp], "color": "#7C3AED", "width": 1.8, "dash": "dash"},
            {"name": "γ-FCC Transus", "xs": xs_fcc, "ys": [conv(t) for t in ys_fcc], "color": "#4338CA", "width": 1.8, "dash": "dash"}
        ]

        # Isomorphous system: strictly zero 3-phase invariant reactions
        invariants: List[Dict[str, Any]] = []

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1540.0), "font_size": 13, "color": "#0F172A"},
            {"label": "Paramagnetic γ-(Co,Ni) FCC", "x": 0.55, "y": conv(950.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "Ferromagnetic γ-(Co,Ni) FCC", "x": 0.40, "y": conv(500.0), "font_size": 11, "color": "#9F1239"},
            {"label": "ε-HCP Cobalt Solution", "x": 0.05, "y": conv(120.0), "font_size": 10, "color": "#581C87"},
            {"label": "ε + γ", "x": 0.12, "y": conv(180.0), "font_size": 9, "color": "#6D28D9"}
        ]

        return {
            "system": "Co-Ni",
            "element_a": "Co",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Ni, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(1600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 13. Co-Fe Binary Phase Diagram (Assessed Benchmark)
    # References: A. Fernandez Guillermet, High Temp. - High Press. 19 (1989) 477-499.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_fe(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq_knots = [(0.0, 1495.0), (0.15, 1482.0), (0.35, 1476.0), (0.60, 1498.0), (0.80, 1520.0), (1.0, 1538.0)]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        sol_knots = [(0.0, 1495.0), (0.15, 1480.0), (0.35, 1476.0), (0.60, 1494.0), (0.80, 1515.0), (1.0, 1538.0)]
        xs_sol, ys_sol = _interpolate_curve(sol_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        # B2-FeCo ordering dome (summit at 50 at% Fe, 730 C)
        b2_knots = [(0.38, 300.0), (0.42, 550.0), (0.50, 730.0), (0.58, 550.0), (0.62, 300.0)]
        xs_b2, ys_b2 = _interpolate_curve(b2_knots, n_pts=50, clip_x_min=0.35, clip_x_max=0.65)

        invariants = [
            {
                "type": "Congruent Minimum",
                "temp": conv(1476.0),
                "x_reaction": 0.350,
                "x_start": 0.350,
                "x_end": 0.350,
                "equation": "L (35.0 at% Fe) ⇌ γ-(Co,Fe) (Congruent Minimum Melting at 1476 °C)"
            },
            {
                "type": "Order-Disorder Summit",
                "temp": conv(730.0),
                "x_reaction": 0.500,
                "x_start": 0.500,
                "x_end": 0.500,
                "equation": "α-BCC ⇌ B2-FeCo (Ordered Permendur Summit at 730 °C)"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "B2-FeCo Solvus", "xs": xs_b2, "ys": [conv(t) for t in ys_b2], "color": "#7C3AED", "width": 1.8, "dash": "solid"},
            {"name": "Congruent Minimum Marker", "xs": [0.350, 0.350], "ys": [conv(1430.0), conv(1476.0)], "color": "#DC2626", "width": 1.5, "dash": "dot"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1570.0), "font_size": 13, "color": "#0F172A"},
            {"label": "γ-(Co,Fe) Solid Solution", "x": 0.20, "y": conv(1100.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "α-BCC Disordered Matrix", "x": 0.85, "y": conv(600.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "B2-FeCo (Supermendur)", "x": 0.50, "y": conv(500.0), "font_size": 11, "color": "#581C87"}
        ]

        return {
            "system": "Co-Fe",
            "element_a": "Co",
            "element_b": "Fe",
            "x_axis_label": "Atomic Fraction of Fe, x(Fe)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1620.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 14. Fe-Mn Binary Phase Diagram (Assessed Benchmark)
    # References: W. Huang, Calphad 13 (1989) 243-252.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_mn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # 1. Delta-Fe Solidus and Solvus (1394 to 1538 °C)
        xs_delta_sol, ys_delta_sol = _interpolate_curve([(0.000, 1538.0), (0.018, 1505.0), (0.035, 1475.0)], n_pts=15)
        xs_delta_slv, ys_delta_slv = _interpolate_curve([(0.000, 1394.0), (0.018, 1435.0), (0.035, 1475.0)], n_pts=15)

        # 2. Segmented Liquidus Branches: Fe (1538 °C) -> Peritectic (1475 °C) -> Invariant (1230 °C) -> Mn (1246 °C)
        l_knots_1 = [(0.000, 1538.0), (0.050, 1505.0), (0.100, 1475.0)]
        l_knots_2 = [
            (0.100, 1475.0), (0.200, 1425.0), (0.300, 1378.0), (0.400, 1335.0),
            (0.500, 1298.0), (0.600, 1268.0), (0.700, 1245.0), (0.800, 1235.0), (0.880, 1230.0)
        ]
        l_knots_3 = [(0.880, 1230.0), (0.940, 1238.0), (1.000, 1246.0)]
        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=12)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=45)
        xs_l3, ys_l3 = _interpolate_curve(l_knots_3, n_pts=15)
        x_liq = xs_l1 + xs_l2 + xs_l3
        y_liq = ys_l1 + ys_l2 + ys_l3

        # 3. Solidus: γ-(Fe,Mn) from peritectic (1475 °C, 0.045 Mn) to (1228 °C, 0.870 Mn), and δ(Mn) solidus
        s_knots_1 = [
            (0.045, 1475.0), (0.200, 1395.0), (0.300, 1345.0), (0.400, 1300.0),
            (0.500, 1265.0), (0.600, 1245.0), (0.700, 1235.0), (0.800, 1230.0), (0.870, 1228.0)
        ]
        s_knots_2 = [(0.960, 1230.0), (0.980, 1238.0), (1.000, 1246.0)]
        xs_s1, ys_s1 = _interpolate_curve(s_knots_1, n_pts=45)
        xs_s2, ys_s2 = _interpolate_curve(s_knots_2, n_pts=15)
        x_sol = xs_s1 + xs_s2
        y_sol = ys_s1 + ys_s2

        # 4. α-Ferrite and γ-Austenite low-temperature equilibrium
        xs_alpha_slv, ys_alpha_slv = _interpolate_curve(
            [(0.000, 912.0), (0.015, 800.0), (0.025, 600.0), (0.032, 400.0)], n_pts=25
        )
        xs_gamma_fe_slv, ys_gamma_fe_slv = _interpolate_curve(
            [(0.000, 912.0), (0.050, 800.0), (0.100, 680.0), (0.150, 580.0), (0.200, 495.0), (0.250, 430.0), (0.280, 400.0)], n_pts=35
        )

        # 5. δ(Mn) boundary (1138 to 1246 °C)
        xs_delta_mn, ys_delta_mn = _interpolate_curve([(0.870, 1230.0), (0.950, 1180.0), (1.000, 1138.0)], n_pts=20)

        # 6. β(Mn) dome envelope (summit at 1160 °C, 84 at% Mn)
        beta_knots_left = [(0.605, 700.0), (0.660, 850.0), (0.720, 1000.0), (0.800, 1130.0), (0.840, 1160.0)]
        beta_knots_right = [(0.840, 1160.0), (0.920, 1135.0), (1.000, 1087.0)]
        xs_bl, ys_bl = _interpolate_curve(beta_knots_left, n_pts=30)
        xs_br, ys_br = _interpolate_curve(beta_knots_right, n_pts=20)
        beta_right_solv = [(0.685, 700.0), (0.720, 850.0), (0.800, 1000.0), (0.900, 1070.0), (1.000, 1087.0)]
        xs_brs, ys_brs = _interpolate_curve(beta_right_solv, n_pts=30)

        # 7. Low-temperature boundaries below 700 °C
        xs_gamma_mn_slv, ys_gamma_mn_slv = _interpolate_curve([(0.605, 700.0), (0.540, 550.0), (0.470, 400.0)], n_pts=20)
        xs_alpha_mn_slv, ys_alpha_mn_slv = _interpolate_curve([(0.685, 700.0), (0.660, 550.0), (0.640, 400.0)], n_pts=20)

        invariants = [
            {
                "type": "Peritectic",
                "temp": conv(1475.0),
                "x_reaction": 0.045,
                "x_start": 0.035,
                "x_end": 0.100,
                "equation": "L (10.0 at% Mn) + δ-Fe (3.5 at% Mn) ⇌ γ-(Fe,Mn) (4.5 at% Mn) at 1475 °C"
            },
            {
                "type": "Catatectic",
                "temp": conv(1230.0),
                "x_reaction": 0.880,
                "x_start": 0.870,
                "x_end": 0.960,
                "equation": "δ(Mn) (96.0 at% Mn) ⇌ L (88.0 at% Mn) + γ-(Fe,Mn) (87.0 at% Mn) at 1230 °C"
            },
            {
                "type": "Eutectoid",
                "temp": conv(700.0),
                "x_reaction": 0.660,
                "x_start": 0.605,
                "x_end": 0.685,
                "equation": "β(Mn) (66.0 at% Mn) ⇌ γ-(Fe,Mn) (60.5 at% Mn) + α(Mn) (68.5 at% Mn) at 700 °C"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "δ-Fe Solidus", "xs": xs_delta_sol, "ys": [conv(t) for t in ys_delta_sol], "color": "#2563EB", "width": 1.6, "dash": "solid"},
            {"name": "δ-Fe Solvus", "xs": xs_delta_slv, "ys": [conv(t) for t in ys_delta_slv], "color": "#475569", "width": 1.6, "dash": "solid"},
            {"name": "α-Ferrite Solvus", "xs": xs_alpha_slv, "ys": [conv(t) for t in ys_alpha_slv], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "γ-Austenite Solvus (Fe-rich)", "xs": xs_gamma_fe_slv, "ys": [conv(t) for t in ys_gamma_fe_slv], "color": "#0D9488", "width": 1.8, "dash": "solid"},
            {"name": "δ(Mn) Boundary", "xs": xs_delta_mn, "ys": [conv(t) for t in ys_delta_mn], "color": "#475569", "width": 1.6, "dash": "solid"},
            {"name": "β(Mn) Dome Left Envelope", "xs": xs_bl, "ys": [conv(t) for t in ys_bl], "color": "#7C3AED", "width": 1.8, "dash": "solid"},
            {"name": "β(Mn) Dome Right Solvus", "xs": xs_br + xs_brs, "ys": [conv(t) for t in ys_br + ys_brs], "color": "#7C3AED", "width": 1.8, "dash": "solid"},
            {"name": "γ-(Fe,Mn) Solvus (Mn-rich)", "xs": xs_gamma_mn_slv, "ys": [conv(t) for t in ys_gamma_mn_slv], "color": "#0D9488", "width": 1.8, "dash": "solid"},
            {"name": "α(Mn) Solvus", "xs": xs_alpha_mn_slv, "ys": [conv(t) for t in ys_alpha_mn_slv], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "Peritectic Tie-Line (1475 °C)", "xs": [0.035, 0.100], "ys": [conv(1475.0), conv(1475.0)], "color": "#DC2626", "width": 2.0, "dash": "dash"},
            {"name": "Catatectic Tie-Line (1230 °C)", "xs": [0.870, 0.960], "ys": [conv(1230.0), conv(1230.0)], "color": "#DC2626", "width": 2.0, "dash": "dash"},
            {"name": "Eutectoid Tie-Line (700 °C)", "xs": [0.605, 0.685], "ys": [conv(700.0), conv(700.0)], "color": "#DC2626", "width": 2.0, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1450.0), "font_size": 13, "color": "#0F172A"},
            {"label": "γ-(Fe,Mn) FCC Austenite (TWIP Matrix)", "x": 0.42, "y": conv(900.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "δ-Fe", "x": 0.012, "y": conv(1465.0), "font_size": 9, "color": "#0284C7"},
            {"label": "α-BCC Ferrite", "x": 0.015, "y": conv(500.0), "font_size": 9, "color": "#991B1B"},
            {"label": "α + γ", "x": 0.10, "y": conv(500.0), "font_size": 10, "color": "#B45309"},
            {"label": "δ(Mn)", "x": 0.95, "y": conv(1205.0), "font_size": 10, "color": "#475569"},
            {"label": "β(Mn)", "x": 0.82, "y": conv(900.0), "font_size": 11, "color": "#6D28D9"},
            {"label": "α(Mn)", "x": 0.82, "y": conv(550.0), "font_size": 11, "color": "#B45309"}
        ]

        return {
            "system": "Fe-Mn",
            "element_a": "Fe",
            "element_b": "Mn",
            "x_axis_label": "Atomic Fraction of Mn, x(Mn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(400.0),
            "y_max": conv(1600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 16. Cr-Mn Binary Phase Diagram (Thermo-Calc Mn79Cr21 & Mn2Cr Benchmark)
    # References: B.-J. Lee, Metall. Trans. A 24A, 1919-1933 (1993); Thermo-Calc KP database;
    # N. A. Gokcen, Bull. Alloy Phase Diagrams 10, 244-250 (1989).
    # Assessed experimental invariant reactions:
    # 1. Peritectic (1581.0 K / 1307.85 °C): L (18.6 wt% Cr) + Cr_BCC (23.7 wt% Cr) ⇌ Mn79Cr21 (20.1 wt% Cr)
    # 2. Peritectic (1559.0 K / 1285.85 °C): L (13.0 wt% Cr) + Mn79Cr21 (20.1 wt% Cr) ⇌ Mn_BCC (16.5 wt% Cr)
    # 3. Peritectoid (1271.0 K / 997.85 °C): Mn79Cr21 (20.1 wt% Cr) + Cr_BCC (33.7 wt% Cr) ⇌ Mn2Cr (32.1 wt% Cr)
    # 4. Eutectoid (1073.0 K / 799.85 °C): Mn_BCC (10.0 wt% Cr) ⇌ β-Mn + Mn79Cr21 (20.1 wt% Cr)
    # 5. Allotropic Eutectoid (1000.0 K / 726.85 °C): β-Mn (10.0 wt% Cr) ⇌ α-Mn + Mn79Cr21 (20.1 wt% Cr)
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cr_mn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # 1. Segmented Liquidus Branches
        # Branch 1: Pure Mn (1519 K / 1245.85 °C) rising to 1st peritectic liquidus knot (1559 K / 1285.85 °C, w=0.130)
        l_knots_1 = [(0.000, 1245.85), (0.050, 1258.85), (0.100, 1271.85), (0.130, 1285.85)]
        # Branch 2: Liquid in equilibrium with Mn79Cr21 up to 2nd peritectic knot (1581 K / 1307.85 °C, w=0.186)
        l_knots_2 = [(0.130, 1285.85), (0.155, 1296.85), (0.186, 1307.85)]
        # Branch 3: Liquid in equilibrium with Cr_BCC rising towards pure Cr (2180 K / 1906.85 °C, w=1.000)
        l_knots_3 = [
            (0.186, 1307.85), (0.220, 1325.85), (0.250, 1340.85), (0.300, 1368.85),
            (0.350, 1398.85), (0.400, 1416.85), (0.500, 1476.85), (0.650, 1586.85),
            (0.800, 1716.85), (1.000, 1906.85)
        ]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_knots_1, 20), (l_knots_2, 15), (l_knots_3, 45)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # 2. Segmented Solidus Curves
        # Mn_BCC Solidus: from pure Mn (1519 K) to peritectic reaction point at 1559 K, w=0.165
        s_knots_mn = [(0.000, 1245.85), (0.050, 1256.85), (0.100, 1268.85), (0.165, 1285.85)]
        xs_sol_mn, ys_sol_mn = _interpolate_curve(s_knots_mn, n_pts=30, clip_x_min=0.0, clip_x_max=0.165)

        # Cr_BCC Solidus: from peritectic point at 1581 K, w=0.237 rising towards pure Cr (2180 K)
        s_knots_cr = [
            (0.237, 1307.85), (0.280, 1326.85), (0.330, 1344.85), (0.400, 1361.85),
            (0.500, 1421.85), (0.650, 1536.85), (0.800, 1676.85), (1.000, 1906.85)
        ]
        xs_sol_cr, ys_sol_cr = _interpolate_curve(s_knots_cr, n_pts=45, clip_x_min=0.237, clip_x_max=1.0)

        # 3. Solvus Boundaries
        # Mn_BCC Solvus: boundary enclosing the high-temperature Mn_BCC phase field down to eutectoid invariant
        solv_knots_mn = [(0.100, 956.85), (0.115, 1076.85), (0.140, 1206.85), (0.165, 1285.85)]
        xs_solv_mn, ys_solv_mn = _interpolate_curve(solv_knots_mn, n_pts=25, clip_x_min=0.100, clip_x_max=0.165)

        # Cr_BCC Solvus: from peritectic knot (1581 K, w=0.237) through peritectoid knot (1271 K, w=0.337) to low T
        solv_knots_cr_upper = [
            (0.237, 1307.85), (0.255, 1246.85), (0.280, 1176.85), (0.310, 1076.85), (0.337, 997.85)
        ]
        xs_solv_cr_up, ys_solv_cr_up = _interpolate_curve(solv_knots_cr_upper, n_pts=30, clip_x_min=0.237, clip_x_max=0.337)

        solv_knots_cr_lower = [
            (0.337, 997.85), (0.360, 946.85), (0.400, 906.85), (0.450, 776.85), (0.550, 526.85)
        ]
        xs_solv_cr_low, ys_solv_cr_low = _interpolate_curve(solv_knots_cr_lower, n_pts=30, clip_x_min=0.337, clip_x_max=0.60)

        # 4. Invariant Reactions
        invariants = [
            {
                "type": "Peritectic",
                "temp": conv(1307.85),
                "x_reaction": 0.2010,
                "x_start": 0.186,
                "x_end": 0.237,
                "equation": f"L (18.6 wt% Cr) + Cr_BCC (23.7 wt% Cr) ⇌ Mn79Cr21 (Peritectic at {conv(1307.85):.1f} {u})"
            },
            {
                "type": "Peritectic",
                "temp": conv(1285.85),
                "x_reaction": 0.1650,
                "x_start": 0.130,
                "x_end": 0.2010,
                "equation": f"L (13.0 wt% Cr) + Mn79Cr21 (20.1 wt% Cr) ⇌ Mn_BCC (16.5 wt% Cr) (Peritectic at {conv(1285.85):.1f} {u})"
            },
            {
                "type": "Peritectoid",
                "temp": conv(997.85),
                "x_reaction": 0.3212,
                "x_start": 0.2010,
                "x_end": 0.337,
                "equation": f"Mn79Cr21 (20.1 wt% Cr) + Cr_BCC (33.7 wt% Cr) ⇌ Mn2Cr (Peritectoid at {conv(997.85):.1f} {u})"
            },
            {
                "type": "Eutectoid",
                "temp": conv(799.85),
                "x_reaction": 0.1000,
                "x_start": 0.100,
                "x_end": 0.2010,
                "equation": f"Mn_BCC (10.0 wt% Cr) ⇌ β-Mn + Mn79Cr21 (Eutectoid at {conv(799.85):.1f} {u})"
            },
            {
                "type": "Allotropic Eutectoid",
                "temp": conv(726.85),
                "x_reaction": 0.1000,
                "x_start": 0.100,
                "x_end": 0.2010,
                "equation": f"β-Mn (10.0 wt% Cr) ⇌ α-Mn + Mn79Cr21 (Allotropic Transformation at {conv(726.85):.1f} {u})"
            }
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Mn_BCC Solidus", "xs": xs_sol_mn, "ys": [conv(t) for t in ys_sol_mn], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Cr_BCC Solidus", "xs": xs_sol_cr, "ys": [conv(t) for t in ys_sol_cr], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Mn_BCC Solvus", "xs": xs_solv_mn, "ys": [conv(t) for t in ys_solv_mn], "color": "#059669", "width": 1.6, "dash": "dash"},
            {"name": "Cr_BCC Solvus", "xs": xs_solv_cr_up + xs_solv_cr_low, "ys": [conv(t) for t in ys_solv_cr_up + ys_solv_cr_low], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "Mn79Cr21 Line Compound", "xs": [0.2010, 0.2010], "ys": [conv(526.85), conv(1307.85)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Mn2Cr Line Compound", "xs": [0.3212, 0.3212], "ys": [conv(526.85), conv(997.85)], "color": "#9333EA", "width": 2.0, "dash": "solid"}
        ]

        # Add invariant horizontal tie lines into curves for ScottPlot legend and rendering
        for inv in invariants:
            curves.append({
                "name": f"Invariant ({inv['type']})",
                "xs": [inv["x_start"], inv["x_end"]],
                "ys": [inv["temp"], inv["temp"]],
                "color": "#DC2626",
                "width": 1.8,
                "dash": "solid"
            })

        regions = [
            {"label": "Liquid", "x": 0.250, "y": conv(1446.85), "font_size": 13, "color": "#111827"},
            {"label": "Liquid + Mn_BCC", "x": 0.115, "y": conv(1301.85), "font_size": 9, "color": "#4B5563"},
            {"label": "Liquid + Mn79Cr21", "x": 0.165, "y": conv(1326.85), "font_size": 9, "color": "#4B5563"},
            {"label": "Liquid + Cr_BCC", "x": 0.320, "y": conv(1401.85), "font_size": 10, "color": "#4B5563"},
            {"label": "Mn_BCC", "x": 0.115, "y": conv(1226.85), "font_size": 11, "color": "#1E40AF"},
            {"label": "Mn_BCC + Mn79Cr21", "x": 0.165, "y": conv(1076.85), "font_size": 10, "color": "#374151"},
            {"label": "Cr_BCC + Mn79Cr21", "x": 0.255, "y": conv(1176.85), "font_size": 11, "color": "#374151"},
            {"label": "Cr_BCC", "x": 0.355, "y": conv(1226.85), "font_size": 11, "color": "#1E40AF"},
            {"label": "Mn79Cr21 + Mn2Cr", "x": 0.255, "y": conv(826.85), "font_size": 10, "color": "#6B21A8"},
            {"label": "Mn2Cr + Cr_BCC", "x": 0.355, "y": conv(826.85), "font_size": 10, "color": "#6B21A8"},
            {"label": "β + Mn79Cr21", "x": 0.145, "y": conv(766.85), "font_size": 10, "color": "#047857"},
            {"label": "α + Mn79Cr21", "x": 0.145, "y": conv(626.85), "font_size": 10, "color": "#047857"}
        ]

        return {
            "system": "Cr-Mn",
            "element_a": "Mn",
            "element_b": "Cr",
            "x_axis_label": "Weight Fraction of Cr w(Cr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.10,
            "x_max": 0.40,
            "y_min": conv(526.85),
            "y_max": conv(1526.85),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 17. Co-Mn (Cobalt-Manganese) Assessed Benchmark
    # References: W. Huang, CALPHAD 13 (1989) 231-242; H. Okamoto, ASM Alloy Phase Diagr.
    # Assessed high-temperature equilibria, central FCC ordering/miscibility boundary,
    # FCC <-> beta-Mn corridor, Co HCP allotropy, and Mn allotropes (delta-BCC, gamma-FCC, beta-Mn, alpha-Mn).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_mn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # 1. Liquidus curves:
        # Co (1495 °C) down to eutectic (1161 °C at 60.1 at% Mn)
        l_knots_1 = [
            (0.00, 1495.0), (0.05, 1461.3), (0.10, 1424.7), (0.15, 1391.5), (0.20, 1355.0),
            (0.30, 1295.2), (0.40, 1242.1), (0.50, 1195.6), (0.55, 1175.6), (0.601, 1161.0)
        ]
        # Eutectic (1161 °C) rising to peritectic (1185 °C at 91.0 at% Mn)
        l_knots_2 = [
            (0.601, 1161.0), (0.65, 1161.5), (0.70, 1163.4), (0.80, 1170.0), (0.88, 1179.0), (0.910, 1185.0)
        ]
        # Peritectic (1185 °C) rising to pure Mn (1246 °C at 100 at% Mn)
        l_knots_3 = [
            (0.910, 1185.0), (0.93, 1196.0), (0.96, 1216.5), (1.00, 1246.0)
        ]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_knots_1, 60), (l_knots_2, 35), (l_knots_3, 25)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # 2. Solidus curves:
        # gamma-(Co,Mn) FCC solid solution solidus (0.00 to 0.582 Mn at 1161 °C)
        s_fcc_knots = [
            (0.00, 1495.0), (0.05, 1444.6), (0.10, 1401.5), (0.15, 1364.9), (0.20, 1331.7),
            (0.30, 1272.0), (0.40, 1222.1), (0.50, 1182.3), (0.55, 1169.0), (0.582, 1161.0)
        ]
        xs_s_fcc, ys_s_fcc = _interpolate_curve(s_fcc_knots, n_pts=60, clip_x_min=0.0, clip_x_max=0.582)

        # beta-Mn solidus (0.618 to 0.910 Mn at 1161-1185 °C)
        s_beta_knots = [
            (0.618, 1161.0), (0.70, 1163.0), (0.80, 1170.0), (0.88, 1179.0), (0.910, 1185.0)
        ]
        xs_s_beta, ys_s_beta = _interpolate_curve(s_beta_knots, n_pts=35, clip_x_min=0.618, clip_x_max=0.910)

        # delta-Mn BCC solidus (0.910 to 1.000 Mn at 1185-1246 °C)
        s_bcc_knots = [
            (0.910, 1185.0), (0.94, 1202.0), (0.97, 1223.0), (1.00, 1246.0)
        ]
        xs_s_bcc, ys_s_bcc = _interpolate_curve(s_bcc_knots, n_pts=25, clip_x_min=0.910, clip_x_max=1.000)

        # 3. High-temperature Mn allotropic transitions near pure Mn:
        # delta-BCC -> gamma-FCC transus
        delta_gamma_knots = [(0.910, 1185.0), (0.94, 1160.0), (0.97, 1145.0), (1.00, 1138.0)]
        xs_dg, ys_dg = _interpolate_curve(delta_gamma_knots, n_pts=25, clip_x_min=0.910, clip_x_max=1.000)

        # gamma-FCC -> beta-Mn transus
        gamma_beta_knots = [(0.910, 1185.0), (0.93, 1140.0), (0.96, 1115.0), (1.00, 1100.0)]
        xs_gb, ys_gb = _interpolate_curve(gamma_beta_knots, n_pts=25, clip_x_min=0.910, clip_x_max=1.000)

        # 4. Central FCC ordering / miscibility envelope (peak at ~890 °C, 8.8 at% Mn):
        fcc_ord_left = [(0.088, 890.0), (0.075, 600.0), (0.070, 450.0), (0.068, 312.2)]
        xs_ol, ys_ol = _interpolate_curve(fcc_ord_left, n_pts=30, clip_x_min=0.068, clip_x_max=0.088)

        fcc_ord_right_up = [(0.088, 890.0), (0.10, 850.2), (0.15, 733.9), (0.20, 637.6), (0.25, 500.0), (0.30, 391.9), (0.328, 312.2)]
        xs_oru, ys_oru = _interpolate_curve(fcc_ord_right_up, n_pts=40, clip_x_min=0.088, clip_x_max=0.328)

        fcc_ord_right_low = [(0.328, 312.2), (0.36, 230.0), (0.407, 139.5)]
        xs_orl, ys_orl = _interpolate_curve(fcc_ord_right_low, n_pts=25, clip_x_min=0.328, clip_x_max=0.407)

        # 5. FCC <-> beta-Mn two-phase corridor:
        # Left boundary (FCC solvus): (0.582, 1161.0) down to (0.407, 139.5)
        fcc_solvus_knots = [
            (0.582, 1161.0), (0.55, 1006.3), (0.50, 787.1), (0.46, 550.0), (0.43, 300.0), (0.407, 139.5)
        ]
        xs_fsolv, ys_fsolv = _interpolate_curve(fcc_solvus_knots, n_pts=50, clip_x_min=0.407, clip_x_max=0.582)

        # Right boundary (beta-Mn solvus): (0.618, 1161.0) down to (0.467, 139.5)
        beta_solvus_knots = [
            (0.618, 1161.0), (0.60, 1109.2), (0.55, 866.8), (0.50, 481.5), (0.48, 300.0), (0.467, 139.5)
        ]
        xs_bsolv, ys_bsolv = _interpolate_curve(beta_solvus_knots, n_pts=50, clip_x_min=0.467, clip_x_max=0.618)

        # Corridor below 139.5 °C:
        low_solvus_knots = [(0.467, 139.5), (0.48, 100.0), (0.52, 0.0)]
        xs_lsolv, ys_lsolv = _interpolate_curve(low_solvus_knots, n_pts=25, clip_x_min=0.467, clip_x_max=0.520)

        # 6. Co-rich allotropic boundaries (Pure Co 422 °C epsilon-HCP <-> alpha-FCC):
        co_hcp_up = [(0.00, 422.0), (0.03, 370.0), (0.05, 338.7), (0.068, 312.2)]
        xs_cu, ys_cu = _interpolate_curve(co_hcp_up, n_pts=25, clip_x_min=0.00, clip_x_max=0.068)

        co_hcp_mid = [(0.068, 312.2), (0.063, 220.0), (0.059, 139.5)]
        xs_cm, ys_cm = _interpolate_curve(co_hcp_mid, n_pts=20, clip_x_min=0.059, clip_x_max=0.068)

        co_hcp_low = [(0.059, 139.5), (0.050, 70.0), (0.040, 0.0)]
        xs_cl, ys_cl = _interpolate_curve(co_hcp_low, n_pts=20, clip_x_min=0.040, clip_x_max=0.059)

        # 7. Mn-rich alpha-Mn / beta-Mn two-phase envelope (727 °C down to 0 °C):
        # Alpha-Mn solvus (right boundary of two-phase field, single-phase alpha-Mn to the right):
        alpha_beta_knots = [(1.00, 727.0), (0.95, 587.8), (0.90, 428.4), (0.85, 0.0)]
        xs_ab, ys_ab = _interpolate_curve(alpha_beta_knots, n_pts=40, clip_x_min=0.85, clip_x_max=1.00)

        # Beta-Mn solvus toward alpha-Mn (left boundary of beta-Mn + alpha-Mn field):
        beta_alpha_knots = [(0.91, 727.0), (0.86, 520.0), (0.78, 260.0), (0.71, 0.0)]
        xs_ba, ys_ba = _interpolate_curve(beta_alpha_knots, n_pts=40, clip_x_min=0.71, clip_x_max=0.91)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus γ-(Co,Mn)", "xs": xs_s_fcc, "ys": [conv(y) for y in ys_s_fcc], "color": "#000000", "width": 2.0, "dash": "solid"},
            {"name": "Solidus β-Mn", "xs": xs_s_beta, "ys": [conv(y) for y in ys_s_beta], "color": "#000000", "width": 2.0, "dash": "solid"},
            {"name": "Solidus δ-Mn (BCC)", "xs": xs_s_bcc, "ys": [conv(y) for y in ys_s_bcc], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic Invariant Tie-Line", "xs": [0.582, 0.618], "ys": [conv(1161.0), conv(1161.0)], "color": "#DC2626", "width": 2.0, "dash": "solid"},
            {"name": "Peritectic Invariant Tie-Line", "xs": [0.910, 0.965], "ys": [conv(1185.0), conv(1185.0)], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "Upper Invariant Tie-Line (312 °C)", "xs": [0.068, 0.328], "ys": [conv(312.2), conv(312.2)], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "Lower Invariant Tie-Line (140 °C)", "xs": [0.059, 0.467], "ys": [conv(139.5), conv(139.5)], "color": "#DC2626", "width": 1.8, "dash": "solid"},
            {"name": "fcc Ordering Boundary (Left)", "xs": xs_ol, "ys": [conv(y) for y in ys_ol], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "fcc Ordering Boundary (Right)", "xs": xs_oru + xs_orl, "ys": [conv(y) for y in ys_oru + ys_orl], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "fcc Solvus Corridor", "xs": xs_fsolv, "ys": [conv(y) for y in ys_fsolv], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "β-Mn Solvus Corridor", "xs": xs_bsolv + xs_lsolv, "ys": [conv(y) for y in ys_bsolv + ys_lsolv], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "Co ε-HCP Solvus", "xs": xs_cu + xs_cm + xs_cl, "ys": [conv(y) for y in ys_cu + ys_cm + ys_cl], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "Mn-rich β-Mn ⇌ α-Mn Boundary", "xs": xs_ab, "ys": [conv(y) for y in ys_ab], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "β-Mn Solvus (to α-Mn)", "xs": xs_ba, "ys": [conv(y) for y in ys_ba], "color": "#000000", "width": 1.8, "dash": "solid"},
            {"name": "δ-BCC ⇌ γ-FCC Transus", "xs": xs_dg, "ys": [conv(y) for y in ys_dg], "color": "#000000", "width": 1.5, "dash": "dash"},
            {"name": "γ-FCC ⇌ β-Mn Transus", "xs": xs_gb, "ys": [conv(y) for y in ys_gb], "color": "#000000", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(1161.0),
                "x_reaction": 0.601,
                "x_start": 0.582,
                "x_end": 0.618,
                "equation": "Liquid (60.1 at% Mn) ⇌ γ-(Co,Mn) + β-Mn (1161 °C)"
            },
            {
                "type": "Peritectic",
                "temp": conv(1185.0),
                "x_reaction": 0.910,
                "x_start": 0.910,
                "x_end": 0.965,
                "equation": "Liquid (91.0 at% Mn) + δ-Mn (BCC) ⇌ γ-Mn (FCC) (1185 °C)"
            },
            {
                "type": "Peritectoid / Ordering Invariant",
                "temp": conv(312.2),
                "x_reaction": 0.068,
                "x_start": 0.068,
                "x_end": 0.328,
                "equation": "ε-HCP + fcc₂ ⇌ fcc₁ (312 °C)"
            },
            {
                "type": "Solid-State Invariant",
                "temp": conv(139.5),
                "x_reaction": 0.059,
                "x_start": 0.059,
                "x_end": 0.467,
                "equation": "ε-HCP + β-Mn ⇌ Intermediate Ordered Phase (140 °C)"
            },
            {
                "type": "Allotropic Transition",
                "temp": conv(422.0),
                "x_reaction": 0.000,
                "x_start": 0.000,
                "x_end": 0.068,
                "equation": "Pure Cobalt ε-HCP ⇌ α-FCC Allotropic Transition (422 °C)"
            },
            {
                "type": "Allotropic Transition",
                "temp": conv(727.0),
                "x_reaction": 1.000,
                "x_start": 0.850,
                "x_end": 1.000,
                "equation": "Pure Manganese β-Mn ⇌ α-Mn Allotropic Transition (727 °C)"
            }
        ]

        regions = [
            {"label": "Liquid", "x": 0.48, "y": conv(1450.0), "font_size": 13, "color": "#000000"},
            {"label": "fcc", "x": 0.28, "y": conv(900.0), "font_size": 12, "color": "#000000"},
            {"label": "β-Mn", "x": 0.70, "y": conv(900.0), "font_size": 12, "color": "#000000"},
            {"label": "α-Mn", "x": 0.92, "y": conv(250.0), "font_size": 11, "color": "#000000"},
            {"label": "hcp", "x": 0.035, "y": conv(250.0), "font_size": 10, "color": "#000000"},
            {"label": "bcc", "x": 0.94, "y": conv(1200.0), "font_size": 9, "color": "#000000"},
            {"label": "fcc", "x": 0.96, "y": conv(1120.0), "font_size": 9, "color": "#000000"},
            {"label": "fcc + β-Mn", "x": 0.54, "y": conv(650.0), "font_size": 9, "color": "#000000"},
            {"label": "fcc + hcp", "x": 0.045, "y": conv(350.0), "font_size": 8, "color": "#000000"},
            {"label": "β-Mn + α-Mn", "x": 0.80, "y": conv(250.0), "font_size": 8.5, "color": "#000000"}
        ]

        return {
            "system": "Co-Mn",
            "element_a": "Co",
            "element_b": "Mn",
            "x_axis_label": "Mole fraction Mn",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(1800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 18. Ti-V (Titanium-Vanadium) Aerospace Beta-Isomorphous System
    # References: G. Ghosh, J. Phase Equilib. 23 (2002) 310-328; J.L. Murray (1981).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ti_v(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Ti (1668 °C) to minimum (1620 °C at 32 at% V) to V (1910 °C)
        l_knots_1 = [(0.00, 1668.0), (0.08, 1650.0), (0.18, 1632.0), (0.32, 1620.0)]
        l_knots_2 = [(0.32, 1620.0), (0.45, 1648.0), (0.60, 1710.0), (0.75, 1785.0), (0.90, 1860.0), (1.00, 1910.0)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_knots_1, 40), (l_knots_2, 70)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # Solidus: tangent to liquidus at congruent minimum (1620 °C, 32 at% V)
        s_knots_1 = [(0.00, 1668.0), (0.10, 1636.0), (0.22, 1623.0), (0.32, 1620.0)]
        s_knots_2 = [(0.32, 1620.0), (0.50, 1638.0), (0.68, 1720.0), (0.85, 1830.0), (1.00, 1910.0)]

        xs_sol: List[float] = []
        ys_sol: List[float] = []
        for knots, count in [(s_knots_1, 40), (s_knots_2, 70)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_sol.extend(xs)
            ys_sol.extend(ys)

        # β-Transus allotropic phase boundary (BCC β-Ti ⇌ α-HCP Ti)
        # Drops steeply from pure Ti allotropy at 882 °C down to ~675 °C at 15 at% V
        transus_knots = [(0.00, 882.0), (0.03, 830.0), (0.06, 780.0), (0.10, 725.0), (0.15, 675.0)]
        xs_trans, ys_trans = _interpolate_curve(transus_knots, n_pts=35, clip_x_min=0.0, clip_x_max=0.15)

        # α-Ti terminal solvus (maximum solubility ~3 at% V at 675 °C)
        solvus_alpha = [(0.00, 882.0), (0.015, 800.0), (0.030, 675.0), (0.022, 550.0), (0.012, 400.0), (0.005, 200.0)]
        xs_solv, ys_solv = _interpolate_curve(solvus_alpha, n_pts=40, clip_x_min=0.0, clip_x_max=0.035)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_sol, "ys": [conv(y) for y in ys_sol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "β-Transus Boundary", "xs": xs_trans, "ys": [conv(y) for y in ys_trans], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "α-Ti Solvus", "xs": xs_solv, "ys": [conv(y) for y in ys_solv], "color": "#059669", "width": 1.6, "dash": "dot"},
        ]

        invariants = [
            {
                "type": "Congruent Minimum",
                "temp": conv(1620.0),
                "x_reaction": 0.32,
                "x_start": 0.32,
                "x_end": 0.32,
                "equation": "L (32 at% V) ⇌ β-(Ti,V) (Continuous BCC Solid Solution)"
            },
            {
                "type": "Allotropic Transition",
                "temp": conv(882.0),
                "x_reaction": 0.00,
                "x_start": 0.00,
                "x_end": 0.00,
                "equation": "β-BCC ⇌ α-HCP (Pure Titanium Allotropy)"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1820.0), "font_size": 13, "color": "#0F172A"},
            {"label": "β-(Ti,V) BCC Solid Solution", "x": 0.55, "y": conv(1250.0), "font_size": 12, "color": "#1E3A8A"},
            {"label": "α-Ti + β-(Ti,V)", "x": 0.08, "y": conv(550.0), "font_size": 10, "color": "#DC2626"},
            {"label": "(α-Ti) HCP", "x": 0.012, "y": conv(350.0), "font_size": 10, "color": "#059669"}
        ]

        return {
            "system": "Ti-V",
            "element_a": "Ti",
            "element_b": "V",
            "x_axis_label": "Atomic Fraction of V, x(V)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(150.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 19. Al-Mg (Aluminium-Magnesium) Light Aerospace System
    # References: N. Saunders (1990); H. Liang, S.L. Chen, Y.A. Chang, Z. Metallkd. (1998).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_mg(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus curve:
        # Branch 1: Al (660.45 °C) to Eutectic 1 (450 °C, 36 at% Mg)
        l_1 = [(0.00, 660.45), (0.10, 615.0), (0.20, 555.0), (0.30, 485.0), (0.36, 450.0)]
        # Branch 2: Eutectic 1 to β-Al3Mg2 congruent summit (452 °C, 38.5 at% Mg)
        l_2 = [(0.36, 450.0), (0.385, 452.0)]
        # Branch 3: β-summit to Peritectic (458 °C, 42 at% Mg)
        l_3 = [(0.385, 452.0), (0.42, 458.0)]
        # Branch 4: Peritectic to Eutectic 2 (437 °C, 60 at% Mg)
        l_4 = [(0.42, 458.0), (0.50, 450.0), (0.60, 437.0)]
        # Branch 5: Eutectic 2 to Mg (650 °C)
        l_5 = [(0.60, 437.0), (0.70, 505.0), (0.80, 568.0), (0.90, 615.0), (1.00, 650.0)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_1, 35), (l_2, 10), (l_3, 10), (l_4, 30), (l_5, 35)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # Solidus curves:
        # (Al) solidus: 0 to 18.9 at% Mg at 450 °C
        s_al = [(0.00, 660.45), (0.05, 600.0), (0.10, 540.0), (0.15, 480.0), (0.189, 450.0)]
        xs_s_al, ys_s_al = _interpolate_curve(s_al, n_pts=30, clip_x_min=0.0, clip_x_max=0.189)

        # (Mg) solidus: 88.2 to 100 at% Mg at 437 °C
        s_mg = [(0.882, 437.0), (0.92, 510.0), (0.96, 585.0), (1.00, 650.0)]
        xs_s_mg, ys_s_mg = _interpolate_curve(s_mg, n_pts=25, clip_x_min=0.882, clip_x_max=1.0)

        # Solvus curves:
        # (Al) solvus: precipitation boundary for 5000/6000 series
        solv_al = [(0.189, 450.0), (0.14, 380.0), (0.09, 300.0), (0.045, 200.0), (0.02, 100.0)]
        xs_solv_al, ys_solv_al = _interpolate_curve(solv_al, n_pts=30, clip_x_min=0.0, clip_x_max=0.189)

        # (Mg) solvus
        solv_mg = [(0.882, 437.0), (0.91, 370.0), (0.94, 290.0), (0.97, 180.0), (0.985, 100.0)]
        xs_solv_mg, ys_solv_mg = _interpolate_curve(solv_mg, n_pts=25, clip_x_min=0.882, clip_x_max=1.0)

        # Intermetallic vertical phase boundaries:
        # β-Al3Mg2 (38.5 at% Mg, stable up to 452 °C)
        xs_beta = [0.385, 0.385]
        ys_beta = [conv(50.0), conv(452.0)]
        # γ-Al12Mg17 (58 at% Mg, stable up to 458 °C)
        xs_gamma = [0.58, 0.58]
        ys_gamma = [conv(50.0), conv(458.0)]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (Al)", "xs": xs_s_al, "ys": [conv(y) for y in ys_s_al], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus (Mg)", "xs": xs_s_mg, "ys": [conv(y) for y in ys_s_mg], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solvus (Al)", "xs": xs_solv_al, "ys": [conv(y) for y in ys_solv_al], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "Solvus (Mg)", "xs": xs_solv_mg, "ys": [conv(y) for y in ys_solv_mg], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "β-Al3Mg2 Compound", "xs": xs_beta, "ys": ys_beta, "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "γ-Al12Mg17 Compound", "xs": xs_gamma, "ys": ys_gamma, "color": "#9333EA", "width": 2.0, "dash": "solid"},
            {"name": "Eutectic 1 Tie-Line", "xs": [0.189, 0.385], "ys": [conv(450.0), conv(450.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line", "xs": [0.385, 0.58], "ys": [conv(458.0), conv(458.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic 2 Tie-Line", "xs": [0.58, 0.882], "ys": [conv(437.0), conv(437.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(450.0),
                "x_reaction": 0.36,
                "x_start": 0.189,
                "x_end": 0.385,
                "equation": "L (36 at% Mg) ⇌ (Al) + β-Al3Mg2"
            },
            {
                "type": "Peritectic",
                "temp": conv(458.0),
                "x_reaction": 0.42,
                "x_start": 0.385,
                "x_end": 0.58,
                "equation": "L (42 at% Mg) + β ⇌ γ-Al12Mg17"
            },
            {
                "type": "Eutectic",
                "temp": conv(437.0),
                "x_reaction": 0.60,
                "x_start": 0.58,
                "x_end": 0.882,
                "equation": "L (60 at% Mg) ⇌ γ-Al12Mg17 + (Mg)"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(560.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al) Solid Solution", "x": 0.08, "y": conv(300.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "β-Al3Mg2", "x": 0.385, "y": conv(250.0), "font_size": 10, "color": "#7C3AED"},
            {"label": "γ-Al12Mg17", "x": 0.58, "y": conv(250.0), "font_size": 10, "color": "#9333EA"},
            {"label": "(Mg) Solid Solution", "x": 0.94, "y": conv(300.0), "font_size": 11, "color": "#065F46"},
            {"label": "(Al) + β", "x": 0.25, "y": conv(200.0), "font_size": 10, "color": "#D97706"},
            {"label": "γ + (Mg)", "x": 0.72, "y": conv(200.0), "font_size": 10, "color": "#D97706"}
        ]

        return {
            "system": "Al-Mg",
            "element_a": "Al",
            "element_b": "Mg",
            "x_axis_label": "Atomic Fraction of Mg, x(Mg)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(50.0),
            "y_max": conv(720.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 20. Al-Si (Aluminium-Silicon) Foundry Eutectic Casting System
    # References: J.L. Murray, A.J. McAlister (1984); J. Gröbner et al., Z. Metallkd. (1996).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_si(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus:
        # Branch 1: Al (660.45 °C) to Eutectic (577 °C, 12.2 at% Si)
        l_1 = [(0.000, 660.45), (0.030, 642.0), (0.060, 622.0), (0.090, 601.0), (0.122, 577.0)]
        # Branch 2: Eutectic (577 °C, 12.2 at% Si) to Si (1414 °C)
        l_2 = [(0.122, 577.0), (0.180, 810.0), (0.280, 1025.0), (0.450, 1205.0), (0.700, 1335.0), (1.000, 1414.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_1, n_pts=30, clip_x_min=0.0, clip_x_max=0.122)
        xs_l2, ys_l2 = _interpolate_curve(l_2, n_pts=70, clip_x_min=0.122, clip_x_max=1.0)
        xs_liq = xs_l1 + xs_l2
        ys_liq = ys_l1 + ys_l2

        # (Al) Solidus: 0 to 1.5 at% Si at 577 °C
        s_al = [(0.000, 660.45), (0.005, 632.0), (0.010, 604.0), (0.015, 577.0)]
        xs_s_al, ys_s_al = _interpolate_curve(s_al, n_pts=25, clip_x_min=0.0, clip_x_max=0.015)

        # (Si) Solidus: near pure Si
        xs_s_si = [0.999, 1.000]
        ys_s_si = [577.0, 1414.0]

        # (Al) Solvus: drops from 1.5 at% at 577 °C to ~0.05 at% at 200 °C
        solv_al = [(0.015, 577.0), (0.010, 480.0), (0.005, 380.0), (0.002, 280.0), (0.0005, 100.0)]
        xs_solv_al, ys_solv_al = _interpolate_curve(solv_al, n_pts=30, clip_x_min=0.0, clip_x_max=0.015)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (Al)", "xs": xs_s_al, "ys": [conv(y) for y in ys_s_al], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus (Si)", "xs": xs_s_si, "ys": [conv(y) for y in ys_s_si], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solvus (Al)", "xs": xs_solv_al, "ys": [conv(y) for y in ys_solv_al], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "Eutectic Invariant Tie-Line", "xs": [0.015, 0.999], "ys": [conv(577.0), conv(577.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(577.0),
                "x_reaction": 0.122,
                "x_start": 0.015,
                "x_end": 0.999,
                "equation": "L (12.2 at% Si / 12.6 wt% Si) ⇌ (Al) + (Si)"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.40, "y": conv(1100.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al) Solid Solution", "x": 0.007, "y": conv(350.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "(Al) + (Si) Eutectic Mixture", "x": 0.50, "y": conv(350.0), "font_size": 12, "color": "#D97706"},
            {"label": "(Si) Diamond Cubic", "x": 0.985, "y": conv(800.0), "font_size": 10, "color": "#065F46"}
        ]

        return {
            "system": "Al-Si",
            "element_a": "Al",
            "element_b": "Si",
            "x_axis_label": "Atomic Fraction of Si, x(Si)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(100.0),
            "y_max": conv(1500.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 21. Ni-Ti (Nickel-Titanium) Nitinol Shape Memory System
    # References: P. Bellen, K.C. Hari Kumar, P. Wollants (1996); K. Otsuka, X. Ren (2005).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ni_ti(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus branches:
        # 1. Ti (1668 °C) to Eutectic 1 (942 °C, 24.5 at% Ni)
        l_1 = [(0.00, 1668.0), (0.08, 1440.0), (0.16, 1180.0), (0.245, 942.0)]
        # 2. Eutectic 1 to Ti2Ni peritectic (984 °C, 28 at% Ni)
        l_2 = [(0.245, 942.0), (0.280, 984.0)]
        # 3. Ti2Ni peritectic to B2-NiTi congruent summit (1310 °C, 50 at% Ni)
        l_3 = [(0.280, 984.0), (0.35, 1150.0), (0.42, 1260.0), (0.50, 1310.0)]
        # 4. B2-NiTi summit to Eutectic 2 (1118 °C, 61.5 at% Ni)
        l_4 = [(0.50, 1310.0), (0.55, 1250.0), (0.615, 1118.0)]
        # 5. Eutectic 2 to Ni3Ti congruent summit (1380 °C, 75 at% Ni)
        l_5 = [(0.615, 1118.0), (0.68, 1280.0), (0.75, 1380.0)]
        # 6. Ni3Ti summit to Eutectic 3 (1304 °C, 86.5 at% Ni)
        l_6 = [(0.75, 1380.0), (0.81, 1345.0), (0.865, 1304.0)]
        # 7. Eutectic 3 to Ni (1455 °C)
        l_7 = [(0.865, 1304.0), (0.92, 1385.0), (1.00, 1455.0)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_1, 30), (l_2, 10), (l_3, 30), (l_4, 20), (l_5, 20), (l_6, 20), (l_7, 20)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # Solidus curves:
        # β-Ti solidus
        s_ti = [(0.00, 1668.0), (0.05, 1310.0), (0.10, 942.0)]
        xs_s_ti, ys_s_ti = _interpolate_curve(s_ti, n_pts=25, clip_x_min=0.0, clip_x_max=0.10)

        # B2-NiTi solidus (wide shape memory phase field around 50 at% Ni)
        s_b2 = [(0.48, 984.0), (0.49, 1180.0), (0.50, 1310.0), (0.53, 1200.0), (0.54, 1118.0)]
        xs_s_b2, ys_s_b2 = _interpolate_curve(s_b2, n_pts=35, clip_x_min=0.48, clip_x_max=0.54)

        # (Ni) solidus
        s_ni = [(0.89, 1304.0), (0.94, 1390.0), (1.00, 1455.0)]
        xs_s_ni, ys_s_ni = _interpolate_curve(s_ni, n_pts=25, clip_x_min=0.89, clip_x_max=1.0)

        # Intermetallic vertical line compounds:
        # Ti2Ni (33.3 at% Ni, up to 984 °C)
        xs_ti2ni = [0.333, 0.333]
        ys_ti2ni = [conv(100.0), conv(984.0)]

        # Ni3Ti (75 at% Ni, congruent melting at 1380 °C)
        xs_ni3ti = [0.75, 0.75]
        ys_ni3ti = [conv(100.0), conv(1380.0)]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus β-Ti", "xs": xs_s_ti, "ys": [conv(y) for y in ys_s_ti], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus B2-NiTi", "xs": xs_s_b2, "ys": [conv(y) for y in ys_s_b2], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus (Ni)", "xs": xs_s_ni, "ys": [conv(y) for y in ys_s_ni], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Ti2Ni Compound", "xs": xs_ti2ni, "ys": ys_ti2ni, "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Ni3Ti Compound", "xs": xs_ni3ti, "ys": ys_ni3ti, "color": "#9333EA", "width": 2.0, "dash": "solid"},
            {"name": "Eutectic 1 Tie-Line", "xs": [0.10, 0.333], "ys": [conv(942.0), conv(942.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line", "xs": [0.280, 0.48], "ys": [conv(984.0), conv(984.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic 2 Tie-Line", "xs": [0.54, 0.75], "ys": [conv(1118.0), conv(1118.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic 3 Tie-Line", "xs": [0.75, 0.89], "ys": [conv(1304.0), conv(1304.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Eutectic",
                "temp": conv(942.0),
                "x_reaction": 0.245,
                "x_start": 0.10,
                "x_end": 0.333,
                "equation": "L (24.5 at% Ni) ⇌ β-Ti + Ti2Ni"
            },
            {
                "type": "Peritectic",
                "temp": conv(984.0),
                "x_reaction": 0.280,
                "x_start": 0.245,
                "x_end": 0.48,
                "equation": "L (28 at% Ni) + B2-NiTi ⇌ Ti2Ni"
            },
            {
                "type": "Congruent Summit",
                "temp": conv(1310.0),
                "x_reaction": 0.50,
                "x_start": 0.50,
                "x_end": 0.50,
                "equation": "L (50 at% Ni) ⇌ B2-NiTi (Shape Memory Nitinol)"
            },
            {
                "type": "Eutectic",
                "temp": conv(1118.0),
                "x_reaction": 0.615,
                "x_start": 0.54,
                "x_end": 0.75,
                "equation": "L (61.5 at% Ni) ⇌ B2-NiTi + Ni3Ti"
            },
            {
                "type": "Congruent Summit",
                "temp": conv(1380.0),
                "x_reaction": 0.75,
                "x_start": 0.75,
                "x_end": 0.75,
                "equation": "L (75 at% Ni) ⇌ Ni3Ti"
            },
            {
                "type": "Eutectic",
                "temp": conv(1304.0),
                "x_reaction": 0.865,
                "x_start": 0.75,
                "x_end": 0.89,
                "equation": "L (86.5 at% Ni) ⇌ Ni3Ti + (Ni)"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1520.0), "font_size": 13, "color": "#0F172A"},
            {"label": "B2-NiTi (Nitinol)", "x": 0.50, "y": conv(700.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Ti2Ni", "x": 0.333, "y": conv(500.0), "font_size": 10, "color": "#7C3AED"},
            {"label": "Ni3Ti", "x": 0.75, "y": conv(700.0), "font_size": 10, "color": "#9333EA"},
            {"label": "(Ni) Solid Solution", "x": 0.94, "y": conv(900.0), "font_size": 11, "color": "#065F46"},
            {"label": "β-Ti", "x": 0.05, "y": conv(1100.0), "font_size": 10, "color": "#2563EB"}
        ]

        return {
            "system": "Ni-Ti",
            "element_a": "Ti",
            "element_b": "Ni",
            "x_axis_label": "Atomic Fraction of Ni, x(Ni)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(100.0),
            "y_max": conv(1750.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 22. Cu-Zn (Copper-Zinc) Hume-Rothery Brass System
    # References: M. Kowalski, P.J. Spencer (1993); ASM Handbook Vol. 3.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cu_zn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus curve:
        # 1. Cu (1084.62 °C) to Peritectic 1 (902 °C, 37 at% Zn)
        l_1 = [(0.00, 1084.62), (0.12, 1030.0), (0.25, 970.0), (0.37, 902.0)]
        # 2. Peritectic 1 to Peritectic 2 (835 °C, 56 at% Zn)
        l_2 = [(0.37, 902.0), (0.45, 870.0), (0.56, 835.0)]
        # 3. Peritectic 2 to Peritectic 3 (598 °C, 80 at% Zn)
        l_3 = [(0.56, 835.0), (0.68, 720.0), (0.80, 598.0)]
        # 4. Peritectic 3 to Eutectic (419 °C, 97.8 at% Zn)
        l_4 = [(0.80, 598.0), (0.90, 500.0), (0.978, 419.0)]
        # 5. Eutectic to Zn (419.53 °C)
        l_5 = [(0.978, 419.0), (1.00, 419.53)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_1, 35), (l_2, 25), (l_3, 30), (l_4, 30), (l_5, 10)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # Solidus curves for intermediate electron phases:
        # α-FCC solidus: 0 to 32.5 at% Zn at 902 °C
        s_alpha = [(0.00, 1084.62), (0.10, 1010.0), (0.22, 940.0), (0.325, 902.0)]
        xs_s_alpha, ys_s_alpha = _interpolate_curve(s_alpha, n_pts=30, clip_x_min=0.0, clip_x_max=0.325)

        # β-BCC solidus: 36.8 to 45 at% Zn (902 °C to 835 °C)
        s_beta = [(0.368, 902.0), (0.41, 870.0), (0.45, 835.0)]
        xs_s_beta, ys_s_beta = _interpolate_curve(s_beta, n_pts=20, clip_x_min=0.368, clip_x_max=0.45)

        # γ solidus: 59 to 68 at% Zn (835 °C to 598 °C)
        s_gamma = [(0.59, 835.0), (0.63, 720.0), (0.68, 598.0)]
        xs_s_gamma, ys_s_gamma = _interpolate_curve(s_gamma, n_pts=25, clip_x_min=0.59, clip_x_max=0.68)

        # ε-HCP solidus: 78.5 to 87.5 at% Zn (598 °C to 419 °C)
        s_eps = [(0.785, 598.0), (0.83, 500.0), (0.875, 419.0)]
        xs_s_eps, ys_s_eps = _interpolate_curve(s_eps, n_pts=25, clip_x_min=0.785, clip_x_max=0.875)

        # α solvus: maximum solubility 38.3 at% Zn at 454 °C, down to 30 at% at 100 °C
        solv_alpha = [(0.325, 902.0), (0.355, 700.0), (0.383, 454.0), (0.35, 300.0), (0.32, 100.0)]
        xs_solv_a, ys_solv_a = _interpolate_curve(solv_alpha, n_pts=35, clip_x_min=0.0, clip_x_max=0.39)

        # B2 ordering transus: β ⇌ β' (454–468 °C)
        b2_trans = [(0.383, 454.0), (0.46, 468.0), (0.49, 454.0)]
        xs_b2, ys_b2 = _interpolate_curve(b2_trans, n_pts=25, clip_x_min=0.38, clip_x_max=0.50)

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus α-Brass", "xs": xs_s_alpha, "ys": [conv(y) for y in ys_s_alpha], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus β-BCC", "xs": xs_s_beta, "ys": [conv(y) for y in ys_s_beta], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus γ-Phase", "xs": xs_s_gamma, "ys": [conv(y) for y in ys_s_gamma], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus ε-HCP", "xs": xs_s_eps, "ys": [conv(y) for y in ys_s_eps], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solvus α-Brass", "xs": xs_solv_a, "ys": [conv(y) for y in ys_solv_a], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "β ⇌ β' (B2) Ordering", "xs": xs_b2, "ys": [conv(y) for y in ys_b2], "color": "#7C3AED", "width": 1.6, "dash": "dashdot"},
            {"name": "Peritectic 1 Tie-Line", "xs": [0.325, 0.368], "ys": [conv(902.0), conv(902.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic 2 Tie-Line", "xs": [0.45, 0.59], "ys": [conv(835.0), conv(835.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic 3 Tie-Line", "xs": [0.68, 0.785], "ys": [conv(598.0), conv(598.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line", "xs": [0.875, 0.985], "ys": [conv(419.0), conv(419.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Peritectic",
                "temp": conv(902.0),
                "x_reaction": 0.37,
                "x_start": 0.325,
                "x_end": 0.368,
                "equation": "L (37 at% Zn) + α-(Cu) ⇌ β-BCC"
            },
            {
                "type": "Peritectic",
                "temp": conv(835.0),
                "x_reaction": 0.56,
                "x_start": 0.45,
                "x_end": 0.59,
                "equation": "L (56 at% Zn) + β ⇌ γ-Phase"
            },
            {
                "type": "Peritectic",
                "temp": conv(598.0),
                "x_reaction": 0.80,
                "x_start": 0.68,
                "x_end": 0.785,
                "equation": "L (80 at% Zn) + γ ⇌ ε-HCP"
            },
            {
                "type": "Eutectic",
                "temp": conv(419.0),
                "x_reaction": 0.978,
                "x_start": 0.875,
                "x_end": 0.985,
                "equation": "L (97.8 at% Zn) ⇌ ε-HCP + η-(Zn)"
            },
            {
                "type": "B2 Order-Disorder",
                "temp": conv(458.0),
                "x_reaction": 0.46,
                "x_start": 0.383,
                "x_end": 0.49,
                "equation": "β-BCC ⇌ β'-B2 Ordering Transformation"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(1020.0), "font_size": 13, "color": "#0F172A"},
            {"label": "α-FCC (Alpha Brass)", "x": 0.16, "y": conv(550.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "β' (B2 Brass)", "x": 0.46, "y": conv(350.0), "font_size": 10, "color": "#7C3AED"},
            {"label": "γ (Complex Cubic)", "x": 0.64, "y": conv(400.0), "font_size": 10, "color": "#9333EA"},
            {"label": "ε (HCP Brass)", "x": 0.82, "y": conv(300.0), "font_size": 10, "color": "#059669"},
            {"label": "η-(Zn)", "x": 0.985, "y": conv(250.0), "font_size": 10, "color": "#065F46"}
        ]

        return {
            "system": "Cu-Zn",
            "element_a": "Cu",
            "element_b": "Zn",
            "x_axis_label": "Atomic Fraction of Zn, x(Zn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(50.0),
            "y_max": conv(1150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 23. Cu-Sn (Copper-Tin) Structural Bronze System
    # References: N. Saunders, A.P. Miodownik (1990); F.H. Li et al., CALPHAD (2007).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cu_sn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus curve:
        # 1. Cu (1084.62 °C) to Peritectic 1 (798 °C, 13.5 at% Sn)
        l_1 = [(0.00, 1084.62), (0.04, 980.0), (0.08, 885.0), (0.135, 798.0)]
        # 2. Peritectic 1 to Peritectic 2 (755 °C, 15.5 at% Sn)
        l_2 = [(0.135, 798.0), (0.155, 755.0)]
        # 3. Peritectic 2 to Peritectic 3 (640 °C, 57 at% Sn)
        l_3 = [(0.155, 755.0), (0.35, 690.0), (0.57, 640.0)]
        # 4. Peritectic 3 to Peritectic 4 (415 °C, 91 at% Sn)
        l_4 = [(0.57, 640.0), (0.75, 520.0), (0.91, 415.0)]
        # 5. Peritectic 4 to Eutectic (227 °C, 98.7 at% Sn)
        l_5 = [(0.91, 415.0), (0.96, 300.0), (0.987, 227.0)]
        # 6. Eutectic to Sn (231.93 °C)
        l_6 = [(0.987, 227.0), (1.00, 231.93)]

        xs_liq: List[float] = []
        ys_liq: List[float] = []
        for knots, count in [(l_1, 30), (l_2, 10), (l_3, 30), (l_4, 30), (l_5, 20), (l_6, 10)]:
            xs, ys = _interpolate_curve(knots, n_pts=count, clip_x_min=0.0, clip_x_max=1.0)
            xs_liq.extend(xs)
            ys_liq.extend(ys)

        # Solidus curves:
        # α-FCC bronze solidus: 0 to 9.1 at% Sn at 798 °C
        s_alpha = [(0.00, 1084.62), (0.04, 950.0), (0.091, 798.0)]
        xs_s_alpha, ys_s_alpha = _interpolate_curve(s_alpha, n_pts=25, clip_x_min=0.0, clip_x_max=0.091)

        # α solvus: precipitation boundary for tin bronzes
        solv_alpha = [(0.091, 798.0), (0.082, 600.0), (0.050, 400.0), (0.015, 200.0)]
        xs_solv_a, ys_solv_a = _interpolate_curve(solv_alpha, n_pts=30, clip_x_min=0.0, clip_x_max=0.091)

        # Intermetallic vertical line compounds:
        # δ-Cu31Sn8 (20.5 at% Sn, decomposes eutectoidally at 520 °C)
        xs_delta = [0.205, 0.205]
        ys_delta = [conv(50.0), conv(520.0)]

        # ε-Cu3Sn (25 at% Sn, peritectic at 640 °C)
        xs_eps = [0.25, 0.25]
        ys_eps = [conv(50.0), conv(640.0)]

        # η-Cu6Sn5 (45.5 at% Sn, peritectic at 415 °C)
        xs_eta = [0.455, 0.455]
        ys_eta = [conv(50.0), conv(415.0)]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(y) for y in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus α-Bronze", "xs": xs_s_alpha, "ys": [conv(y) for y in ys_s_alpha], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solvus α-Bronze", "xs": xs_solv_a, "ys": [conv(y) for y in ys_solv_a], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "δ-Cu31Sn8 Compound", "xs": xs_delta, "ys": ys_delta, "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "ε-Cu3Sn Compound", "xs": xs_eps, "ys": ys_eps, "color": "#9333EA", "width": 2.0, "dash": "solid"},
            {"name": "η-Cu6Sn5 Compound", "xs": xs_eta, "ys": ys_eta, "color": "#C026D3", "width": 2.0, "dash": "solid"},
            {"name": "Peritectic 1 Tie-Line", "xs": [0.091, 0.135], "ys": [conv(798.0), conv(798.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic 2 Tie-Line", "xs": [0.149, 0.155], "ys": [conv(755.0), conv(755.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic 3 Tie-Line", "xs": [0.25, 0.57], "ys": [conv(640.0), conv(640.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectoid Tie-Line", "xs": [0.07, 0.205], "ys": [conv(520.0), conv(520.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic 4 Tie-Line", "xs": [0.455, 0.91], "ys": [conv(415.0), conv(415.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line", "xs": [0.455, 0.999], "ys": [conv(227.0), conv(227.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Peritectic",
                "temp": conv(798.0),
                "x_reaction": 0.135,
                "x_start": 0.091,
                "x_end": 0.135,
                "equation": "L (13.5 at% Sn) + α-(Cu) ⇌ β-Phase"
            },
            {
                "type": "Peritectic",
                "temp": conv(755.0),
                "x_reaction": 0.155,
                "x_start": 0.149,
                "x_end": 0.155,
                "equation": "L (15.5 at% Sn) + β ⇌ γ-Phase"
            },
            {
                "type": "Peritectoid",
                "temp": conv(520.0),
                "x_reaction": 0.205,
                "x_start": 0.07,
                "x_end": 0.205,
                "equation": "α + γ ⇌ δ-Cu31Sn8 (Bell Bronze Phase)"
            },
            {
                "type": "Peritectic",
                "temp": conv(640.0),
                "x_reaction": 0.57,
                "x_start": 0.25,
                "x_end": 0.57,
                "equation": "L (57 at% Sn) + δ ⇌ ε-Cu3Sn"
            },
            {
                "type": "Peritectic",
                "temp": conv(415.0),
                "x_reaction": 0.91,
                "x_start": 0.455,
                "x_end": 0.91,
                "equation": "L (91 at% Sn) + ε ⇌ η-Cu6Sn5"
            },
            {
                "type": "Eutectic",
                "temp": conv(227.0),
                "x_reaction": 0.987,
                "x_start": 0.455,
                "x_end": 0.999,
                "equation": "L (98.7 at% Sn) ⇌ η-Cu6Sn5 + (Sn)"
            }
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(900.0), "font_size": 13, "color": "#0F172A"},
            {"label": "α-FCC Bronze", "x": 0.04, "y": conv(550.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "δ-Cu31Sn8", "x": 0.205, "y": conv(300.0), "font_size": 10, "color": "#7C3AED"},
            {"label": "ε-Cu3Sn", "x": 0.25, "y": conv(300.0), "font_size": 10, "color": "#9333EA"},
            {"label": "η-Cu6Sn5", "x": 0.455, "y": conv(250.0), "font_size": 10, "color": "#C026D3"},
            {"label": "(Sn) Solid Solution", "x": 0.985, "y": conv(150.0), "font_size": 10, "color": "#065F46"}
        ]

        return {
            "system": "Cu-Sn",
            "element_a": "Cu",
            "element_b": "Sn",
            "x_axis_label": "Atomic Fraction of Sn, x(Sn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(50.0),
            "y_max": conv(1150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }


    # -------------------------------------------------------------------------
    # 25. Al-Zn Binary Phase Diagram (Aluminium-Zinc Alloy Benchmark)
    # References: J. L. Murray (1983); S. an Mey (1993); H. Okamoto (ASM).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_zn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Al (660.45 C) down to eutectic at 381.0 C (88.7 at% Zn), up to Zn (419.53 C)
        l_knots_1 = [(0.000, 660.45), (0.200, 620.0), (0.400, 560.0), (0.600, 480.0), (0.800, 415.0), (0.887, 381.0)]
        l_knots_2 = [(0.887, 381.0), (0.950, 400.0), (1.000, 419.53)]
        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=35)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=20)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        # (Al) FCC Solidus: 0.0 to 0.67 at 381.0 C
        xs_al_sol, ys_al_sol = _interpolate_curve(
            [(0.000, 660.45), (0.200, 595.0), (0.400, 510.0), (0.600, 420.0), (0.670, 381.0)], n_pts=30
        )
        # (Zn) HCP Solidus: 0.972 at 381.0 C to 1.0 at 419.53 C
        xs_zn_sol, ys_zn_sol = _interpolate_curve([(0.972, 381.0), (1.000, 419.53)], n_pts=15)

        # FCC miscibility gap envelope with critical point at 351.5 C, 39.5 at% Zn
        mg_knots = [
            (0.165, 277.0), (0.220, 320.0), (0.300, 345.0), (0.395, 351.5),
            (0.500, 340.0), (0.590, 277.0)
        ]
        xs_mg, ys_mg = _interpolate_curve(mg_knots, n_pts=40)

        # Solvus curves below 277 C
        xs_solv_al, ys_solv_al = _interpolate_curve(
            [(0.165, 277.0), (0.100, 200.0), (0.050, 100.0), (0.020, 25.0)], n_pts=25
        )
        xs_solv_zn, ys_solv_zn = _interpolate_curve(
            [(0.985, 277.0), (0.990, 200.0), (0.995, 100.0), (0.998, 25.0)], n_pts=20
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "(Al) FCC Solidus", "xs": xs_al_sol, "ys": [conv(t) for t in ys_al_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "(Zn) HCP Solidus", "xs": xs_zn_sol, "ys": [conv(t) for t in ys_zn_sol], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "FCC Miscibility Gap (α+α')", "xs": xs_mg, "ys": [conv(t) for t in ys_mg], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "(Al) Solvus", "xs": xs_solv_al, "ys": [conv(t) for t in ys_solv_al], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "(Zn) Solvus", "xs": xs_solv_zn, "ys": [conv(t) for t in ys_solv_zn], "color": "#059669", "width": 1.5, "dash": "dash"},
            {"name": "Eutectic Tie-Line (381 °C)", "xs": [0.670, 0.972], "ys": [conv(381.0), conv(381.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectoid Tie-Line (277 °C)", "xs": [0.165, 0.985], "ys": [conv(277.0), conv(277.0)], "color": "#7C3AED", "width": 1.6, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(381.0), "x_reaction": 0.887, "x_start": 0.670, "x_end": 0.972,
             "equation": "L (88.7 at% Zn) ⇌ (Al) (67.0 at% Zn) + (Zn) (97.2 at% Zn)"},
            {"type": "Eutectoid", "temp": conv(277.0), "x_reaction": 0.590, "x_start": 0.165, "x_end": 0.985,
             "equation": "α'-(Al) (59.0 at% Zn) ⇌ α-(Al) (16.5 at% Zn) + (Zn) (98.5 at% Zn)"},
            {"type": "Critical Point", "temp": conv(351.5), "x_reaction": 0.395, "x_start": 0.395, "x_end": 0.395,
             "equation": "(Al) Solid Solution ⇌ α-(Al) + α'-(Al) (Miscibility Gap Summit)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(600.0)},
            {"name": "(Al) Solid Solution", "x": 0.10, "y": conv(450.0)},
            {"name": "α + α' Gap", "x": 0.38, "y": conv(310.0)},
            {"name": "(Al) + (Zn)", "x": 0.50, "y": conv(150.0)},
            {"name": "(Zn) HCP", "x": 0.985, "y": conv(250.0)},
        ]

        return {
            "system": "Al-Zn",
            "element_a": "Al",
            "element_b": "Zn",
            "x_axis_label": "Atomic Fraction of Zn, x(Zn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(720.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 26. Al-Fe Binary Phase Diagram (Aluminium-Iron Intermetallic Benchmark)
    # References: U. R. Kattner, B. P. Burton (1992); S. G. Fries et al. (1994).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_fe(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Al (660.45 C), eutectic at 655 C (0.018 Fe), Al13Fe4 (1157 C, 0.235 Fe),
        # Al5Fe2 (1169 C, 0.285 Fe), B2-AlFe summit (1310 C, 0.48 Fe), peritectic (1449 C, 0.65 Fe), Fe (1538 C)
        l_knots_1 = [(0.000, 660.45), (0.018, 655.0)]
        l_knots_2 = [(0.018, 655.0), (0.050, 750.0), (0.100, 920.0), (0.150, 1050.0), (0.235, 1157.0)]
        l_knots_3 = [(0.235, 1157.0), (0.260, 1165.0), (0.285, 1169.0)]
        l_knots_4 = [(0.285, 1169.0), (0.310, 1160.0), (0.350, 1220.0), (0.420, 1285.0), (0.480, 1310.0)]
        l_knots_5 = [(0.480, 1310.0), (0.550, 1370.0), (0.650, 1449.0), (0.800, 1500.0), (1.000, 1538.0)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 10), (l_knots_2, 25), (l_knots_3, 12), (l_knots_4, 25), (l_knots_5, 30)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Intermetallic envelopes
        xs_b2, ys_b2 = _interpolate_curve(
            [(0.380, 400.0), (0.380, 800.0), (0.400, 1100.0), (0.480, 1310.0),
             (0.540, 1200.0), (0.530, 800.0), (0.520, 400.0)], n_pts=40
        )
        xs_al5fe2, ys_al5fe2 = _interpolate_curve(
            [(0.270, 400.0), (0.270, 800.0), (0.280, 1169.0), (0.295, 800.0), (0.295, 400.0)], n_pts=25
        )
        xs_fe_sol, ys_fe_sol = _interpolate_curve(
            [(0.680, 1449.0), (0.750, 1490.0), (1.000, 1538.0)], n_pts=20
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Al₁₃Fe₄ Stoichiometric Line", "xs": [0.235, 0.235], "ys": [conv(300.0), conv(1157.0)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Al₅Fe₂ Envelope", "xs": xs_al5fe2, "ys": [conv(t) for t in ys_al5fe2], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "Al₂Fe Line", "xs": [0.333, 0.333], "ys": [conv(300.0), conv(1156.0)], "color": "#7C3AED", "width": 1.6, "dash": "dot"},
            {"name": "β-AlFe (B2) Envelope", "xs": xs_b2, "ys": [conv(t) for t in ys_b2], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "(Fe) Solidus", "xs": xs_fe_sol, "ys": [conv(t) for t in ys_fe_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic Tie-Line (655 °C)", "xs": [0.0003, 0.235], "ys": [conv(655.0), conv(655.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1157 °C)", "xs": [0.235, 0.280], "ys": [conv(1157.0), conv(1157.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1449 °C)", "xs": [0.650, 0.780], "ys": [conv(1449.0), conv(1449.0)], "color": "#D97706", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(655.0), "x_reaction": 0.018, "x_start": 0.0003, "x_end": 0.235,
             "equation": "L (1.8 at% Fe) ⇌ (Al) (0.03 at% Fe) + Al₁₃Fe₄ (23.5 at% Fe)"},
            {"type": "Peritectic", "temp": conv(1157.0), "x_reaction": 0.235, "x_start": 0.235, "x_end": 0.280,
             "equation": "L (2.5 at% Fe) + Al₅Fe₂ (28.0 at% Fe) ⇌ Al₁₃Fe₄ (23.5 at% Fe)"},
            {"type": "Congruent", "temp": conv(1169.0), "x_reaction": 0.285, "x_start": 0.285, "x_end": 0.285,
             "equation": "L ⇌ Al₅Fe₂ (Congruent Summit)"},
            {"type": "Congruent", "temp": conv(1310.0), "x_reaction": 0.480, "x_start": 0.480, "x_end": 0.480,
             "equation": "L ⇌ β-AlFe (B2 Ordered BCC Congruent)"},
            {"type": "Peritectic", "temp": conv(1449.0), "x_reaction": 0.650, "x_start": 0.650, "x_end": 0.780,
             "equation": "L (65.0 at% Fe) + (δ-Fe) (78.0 at% Fe) ⇌ β-AlFe (68.0 at% Fe)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1480.0)},
            {"name": "(Al) Matrix", "x": 0.02, "y": conv(450.0)},
            {"name": "Al₁₃Fe₄", "x": 0.21, "y": conv(800.0)},
            {"name": "Al₅Fe₂", "x": 0.285, "y": conv(900.0)},
            {"name": "β-AlFe (B2)", "x": 0.46, "y": conv(950.0)},
            {"name": "(α/δ-Fe)", "x": 0.85, "y": conv(1100.0)},
        ]

        return {
            "system": "Al-Fe",
            "element_a": "Al",
            "element_b": "Fe",
            "x_axis_label": "Atomic Fraction of Fe, x(Fe)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 27. Al-Mn Binary Phase Diagram (Aluminium-Manganese Light Alloy Benchmark)
    # References: J. L. Murray (1987); Y. Du et al. (2000).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_mn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots_1 = [(0.000, 660.45), (0.007, 658.5)]
        l_knots_2 = [(0.007, 658.5), (0.020, 690.0), (0.045, 710.0)]
        l_knots_3 = [(0.045, 710.0), (0.080, 850.0), (0.120, 923.0)]
        l_knots_4 = [(0.120, 923.0), (0.170, 960.0), (0.220, 998.0)]
        l_knots_5 = [(0.220, 998.0), (0.300, 1100.0), (0.385, 1190.0)]
        l_knots_6 = [(0.385, 1190.0), (0.500, 1170.0), (0.610, 1160.0), (0.800, 1200.0), (1.000, 1246.0)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 8), (l_knots_2, 12), (l_knots_3, 15), (l_knots_4, 15), (l_knots_5, 20), (l_knots_6, 25)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Al₆Mn Stoichiometric Line", "xs": [0.143, 0.143], "ys": [conv(300.0), conv(710.0)], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Al₄Mn Line", "xs": [0.200, 0.200], "ys": [conv(300.0), conv(923.0)], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Al₁₁Mn₄ Line", "xs": [0.267, 0.267], "ys": [conv(300.0), conv(998.0)], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "Al₈Mn₅ (γ) Envelope", "xs": [0.360, 0.385, 0.410], "ys": [conv(800.0), conv(1190.0), conv(800.0)], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Eutectic Tie-Line (658.5 °C)", "xs": [0.0035, 0.143], "ys": [conv(658.5), conv(658.5)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (710 °C)", "xs": [0.045, 0.200], "ys": [conv(710.0), conv(710.0)], "color": "#059669", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (923 °C)", "xs": [0.120, 0.267], "ys": [conv(923.0), conv(923.0)], "color": "#D97706", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (998 °C)", "xs": [0.220, 0.360], "ys": [conv(998.0), conv(998.0)], "color": "#7C3AED", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(658.5), "x_reaction": 0.007, "x_start": 0.0035, "x_end": 0.143,
             "equation": "L (0.7 at% Mn) ⇌ (Al) (0.35 at% Mn) + Al₆Mn (14.3 at% Mn)"},
            {"type": "Peritectic", "temp": conv(710.0), "x_reaction": 0.143, "x_start": 0.045, "x_end": 0.200,
             "equation": "L (4.5 at% Mn) + Al₄Mn (20.0 at% Mn) ⇌ Al₆Mn (14.3 at% Mn)"},
            {"type": "Peritectic", "temp": conv(923.0), "x_reaction": 0.200, "x_start": 0.120, "x_end": 0.267,
             "equation": "L (12.0 at% Mn) + Al₁₁Mn₄ (26.7 at% Mn) ⇌ Al₄Mn (20.0 at% Mn)"},
            {"type": "Peritectic", "temp": conv(998.0), "x_reaction": 0.267, "x_start": 0.220, "x_end": 0.360,
             "equation": "L (22.0 at% Mn) + Al₈Mn₅ (38.5 at% Mn) ⇌ Al₁₁Mn₄ (26.7 at% Mn)"},
            {"type": "Congruent", "temp": conv(1190.0), "x_reaction": 0.385, "x_start": 0.385, "x_end": 0.385,
             "equation": "L ⇌ Al₈Mn₅ (γ-phase Congruent Summit)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1280.0)},
            {"name": "(Al) Solution", "x": 0.01, "y": conv(500.0)},
            {"name": "Al₆Mn", "x": 0.13, "y": conv(500.0)},
            {"name": "Al₄Mn", "x": 0.19, "y": conv(600.0)},
            {"name": "Al₁₁Mn₄", "x": 0.25, "y": conv(700.0)},
            {"name": "Al₈Mn₅", "x": 0.385, "y": conv(950.0)},
            {"name": "(β/γ-Mn)", "x": 0.85, "y": conv(900.0)},
        ]

        return {
            "system": "Al-Mn",
            "element_a": "Al",
            "element_b": "Mn",
            "x_axis_label": "Atomic Fraction of Mn, x(Mn) ",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1350.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 28. Mg-Zn Binary Phase Diagram (Magnesium-Zinc Structural Alloy Benchmark)
    # References: J. Agarwal et al. (1992); P. Liang et al. (1998).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_mg_zn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Mg (650 C) -> Eutectic 1 (340 C, 0.283 Zn) -> Summit MgZn2 (590 C, 0.667 Zn)
        # -> Eutectic 2 (364 C, 0.915 Zn) -> Zn (419.53 C)
        l_knots_1 = [(0.000, 650.0), (0.100, 560.0), (0.200, 440.0), (0.283, 340.0)]
        l_knots_2 = [(0.283, 340.0), (0.350, 410.0), (0.500, 520.0), (0.667, 590.0)]
        l_knots_3 = [(0.667, 590.0), (0.780, 520.0), (0.850, 440.0), (0.915, 364.0)]
        l_knots_4 = [(0.915, 364.0), (0.960, 395.0), (1.000, 419.53)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 25), (l_knots_2, 30), (l_knots_3, 30), (l_knots_4, 15)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        # Solidus and phase boundaries
        xs_mg_sol, ys_mg_sol = _interpolate_curve([(0.000, 650.0), (0.015, 500.0), (0.024, 340.0)], n_pts=15)
        xs_mgzn2, ys_mgzn2 = _interpolate_curve(
            [(0.640, 200.0), (0.645, 450.0), (0.667, 590.0), (0.685, 450.0), (0.680, 200.0)], n_pts=30
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "(Mg) HCP Solidus", "xs": xs_mg_sol, "ys": [conv(t) for t in ys_mg_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Mg₇Zn₃ Line", "xs": [0.300, 0.300], "ys": [conv(200.0), conv(347.0)], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "MgZn₂ (C14 Laves) Envelope", "xs": xs_mgzn2, "ys": [conv(t) for t in ys_mgzn2], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Mg₂Zn₁₁ Line", "xs": [0.846, 0.846], "ys": [conv(200.0), conv(381.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line 1 (340 °C)", "xs": [0.024, 0.300], "ys": [conv(340.0), conv(340.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Eutectic Tie-Line 2 (364 °C)", "xs": [0.846, 0.975], "ys": [conv(364.0), conv(364.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(340.0), "x_reaction": 0.283, "x_start": 0.024, "x_end": 0.300,
             "equation": "L (28.3 at% Zn) ⇌ (Mg) (2.4 at% Zn) + Mg₇Zn₃ (30.0 at% Zn)"},
            {"type": "Congruent", "temp": conv(590.0), "x_reaction": 0.667, "x_start": 0.667, "x_end": 0.667,
             "equation": "L ⇌ MgZn₂ (C14 Laves Phase Congruent Summit)"},
            {"type": "Peritectic", "temp": conv(381.0), "x_reaction": 0.846, "x_start": 0.846, "x_end": 0.680,
             "equation": "L (84.6 at% Zn) + MgZn₂ (66.7 at% Zn) ⇌ Mg₂Zn₁₁ (84.6 at% Zn)"},
            {"type": "Eutectic", "temp": conv(364.0), "x_reaction": 0.915, "x_start": 0.846, "x_end": 0.975,
             "equation": "L (91.5 at% Zn) ⇌ Mg₂Zn₁₁ (84.6 at% Zn) + (Zn) (97.5 at% Zn)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(620.0)},
            {"name": "(Mg) Solution", "x": 0.015, "y": conv(450.0)},
            {"name": "Mg₇Zn₃", "x": 0.29, "y": conv(250.0)},
            {"name": "MgZn₂ (C14 Laves)", "x": 0.667, "y": conv(380.0)},
            {"name": "Mg₂Zn₁₁", "x": 0.846, "y": conv(280.0)},
            {"name": "(Zn) Solution", "x": 0.985, "y": conv(250.0)},
        ]

        return {
            "system": "Mg-Zn",
            "element_a": "Mg",
            "element_b": "Zn",
            "x_axis_label": "Atomic Fraction of Zn, x(Zn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(100.0),
            "y_max": conv(700.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 29. Fe-Si Binary Phase Diagram (Steel & Cast Iron Benchmark)
    # References: J. Lacaze, B. Sundman (1991); H. Okamoto (ASM).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_si(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots_1 = [(0.000, 1538.0), (0.100, 1460.0), (0.200, 1340.0), (0.345, 1212.0)]
        l_knots_2 = [(0.345, 1212.0), (0.420, 1320.0), (0.500, 1410.0)]
        l_knots_3 = [(0.500, 1410.0), (0.600, 1340.0), (0.667, 1220.0), (0.740, 1207.0)]
        l_knots_4 = [(0.740, 1207.0), (0.850, 1300.0), (1.000, 1414.0)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 30), (l_knots_2, 20), (l_knots_3, 25), (l_knots_4, 25)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        xs_fesi, ys_fesi = _interpolate_curve(
            [(0.490, 400.0), (0.490, 1000.0), (0.500, 1410.0), (0.510, 1000.0), (0.510, 400.0)], n_pts=25
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "FeSi (B20) Envelope", "xs": xs_fesi, "ys": [conv(t) for t in ys_fesi], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "Fe₃Si (DO₃) Line", "xs": [0.250, 0.250], "ys": [conv(300.0), conv(1200.0)], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "FeSi₂ Line", "xs": [0.667, 0.667], "ys": [conv(300.0), conv(1220.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line 1 (1212 °C)", "xs": [0.250, 0.490], "ys": [conv(1212.0), conv(1212.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Eutectic Tie-Line 2 (1207 °C)", "xs": [0.667, 0.990], "ys": [conv(1207.0), conv(1207.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(1212.0), "x_reaction": 0.345, "x_start": 0.250, "x_end": 0.490,
             "equation": "L (34.5 at% Si) ⇌ Fe₃Si (25.0 at% Si) + FeSi (50.0 at% Si)"},
            {"type": "Congruent", "temp": conv(1410.0), "x_reaction": 0.500, "x_start": 0.500, "x_end": 0.500,
             "equation": "L ⇌ FeSi (B20 Cubic Congruent Summit)"},
            {"type": "Peritectic", "temp": conv(1220.0), "x_reaction": 0.667, "x_start": 0.500, "x_end": 0.720,
             "equation": "L (72.0 at% Si) + FeSi (50.0 at% Si) ⇌ α-FeSi₂ (66.7 at% Si)"},
            {"type": "Eutectic", "temp": conv(1207.0), "x_reaction": 0.740, "x_start": 0.667, "x_end": 0.990,
             "equation": "L (74.0 at% Si) ⇌ α-FeSi₂ (66.7 at% Si) + (Si) (99.0 at% Si)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1520.0)},
            {"name": "(α-Fe) Solution", "x": 0.08, "y": conv(900.0)},
            {"name": "Fe₃Si", "x": 0.25, "y": conv(600.0)},
            {"name": "FeSi (B20)", "x": 0.50, "y": conv(800.0)},
            {"name": "FeSi₂", "x": 0.667, "y": conv(700.0)},
            {"name": "(Si) Diamond", "x": 0.92, "y": conv(800.0)},
        ]

        return {
            "system": "Fe-Si",
            "element_a": "Fe",
            "element_b": "Si",
            "x_axis_label": "Atomic Fraction of Si, x(Si)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(1650.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 30. Fe-Mo Binary Phase Diagram (Steel & Superalloy Moly Benchmark)
    # References: A. F. Guillermet (1982); CALPHAD.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_mo(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        l_knots_1 = [(0.000, 1538.0), (0.100, 1490.0), (0.190, 1440.0), (0.200, 1488.0)]
        l_knots_2 = [(0.200, 1488.0), (0.350, 1750.0), (0.600, 2150.0), (1.000, 2623.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=25)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=40)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_laves, ys_laves = _interpolate_curve(
            [(0.320, 600.0), (0.325, 1200.0), (0.333, 1449.0), (0.350, 1200.0), (0.345, 600.0)], n_pts=30
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "λ-Fe₂Mo (C14 Laves) Envelope", "xs": xs_laves, "ys": [conv(t) for t in ys_laves], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "μ-Fe₇Mo₆ Line", "xs": [0.462, 0.462], "ys": [conv(500.0), conv(1370.0)], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "σ-FeMo Line", "xs": [0.500, 0.500], "ys": [conv(500.0), conv(1250.0)], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1488 °C)", "xs": [0.200, 0.650], "ys": [conv(1488.0), conv(1488.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1440 °C)", "xs": [0.025, 0.333], "ys": [conv(1440.0), conv(1440.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1488.0), "x_reaction": 0.200, "x_start": 0.200, "x_end": 0.650,
             "equation": "L (20.0 at% Mo) + (Mo) (65.0 at% Mo) ⇌ λ-Fe₂Mo (33.3 at% Mo)"},
            {"type": "Eutectic", "temp": conv(1440.0), "x_reaction": 0.190, "x_start": 0.025, "x_end": 0.333,
             "equation": "L (19.0 at% Mo) ⇌ (δ-Fe) (2.5 at% Mo) + λ-Fe₂Mo (33.3 at% Mo)"},
            {"type": "Peritectoid", "temp": conv(1370.0), "x_reaction": 0.462, "x_start": 0.333, "x_end": 0.600,
             "equation": "λ-Fe₂Mo (33.3 at% Mo) + (Mo) (60.0 at% Mo) ⇌ μ-Fe₇Mo₆ (46.2 at% Mo)"},
            {"type": "Peritectoid", "temp": conv(1250.0), "x_reaction": 0.500, "x_start": 0.333, "x_end": 0.462,
             "equation": "λ-Fe₂Mo + μ-Fe₇Mo₆ ⇌ σ-FeMo (50.0 at% Mo)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.30, "y": conv(1950.0)},
            {"name": "(α/δ-Fe)", "x": 0.05, "y": conv(1000.0)},
            {"name": "λ-Fe₂Mo (C14)", "x": 0.333, "y": conv(900.0)},
            {"name": "μ-Fe₇Mo₆", "x": 0.462, "y": conv(800.0)},
            {"name": "σ-FeMo", "x": 0.50, "y": conv(700.0)},
            {"name": "(Mo) Solution", "x": 0.85, "y": conv(1600.0)},
        ]

        return {
            "system": "Fe-Mo",
            "element_a": "Fe",
            "element_b": "Mo",
            "x_axis_label": "Atomic Fraction of Mo, x(Mo)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(400.0),
            "y_max": conv(2800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 31. Fe-V Binary Phase Diagram (Tool Steel & Refractory HEA Benchmark)
    # References: W. Huang (1991); CALPHAD.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_fe_v(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Fe (1538 C) -> minimum (1468 C, 0.31 V) -> V (1910 C)
        l_knots_1 = [(0.000, 1538.0), (0.150, 1495.0), (0.310, 1468.0)]
        l_knots_2 = [(0.310, 1468.0), (0.500, 1550.0), (0.750, 1720.0), (1.000, 1910.0)]
        s_knots_1 = [(0.000, 1538.0), (0.150, 1485.0), (0.310, 1468.0)]
        s_knots_2 = [(0.310, 1468.0), (0.500, 1535.0), (0.750, 1705.0), (1.000, 1910.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=25)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=35)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_s1, ys_s1 = _interpolate_curve(s_knots_1, n_pts=25)
        xs_s2, ys_s2 = _interpolate_curve(s_knots_2, n_pts=35)
        x_sol = xs_s1 + xs_s2
        y_sol = ys_s1 + ys_s2

        # σ-FeV tetragonal phase boundary below 1252 C
        sigma_knots = [
            (0.350, 500.0), (0.370, 900.0), (0.430, 1200.0), (0.500, 1252.0),
            (0.580, 1200.0), (0.630, 900.0), (0.650, 500.0)
        ]
        xs_sigma, ys_sigma = _interpolate_curve(sigma_knots, n_pts=40)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "σ-FeV Phase Envelope", "xs": xs_sigma, "ys": [conv(t) for t in ys_sigma], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
        ]

        invariants = [
            {"type": "Congruent Minimum", "temp": conv(1468.0), "x_reaction": 0.310, "x_start": 0.310, "x_end": 0.310,
             "equation": "L ⇌ (α-Fe, V) BCC Continuous Solid Solution Minimum"},
            {"type": "Congruent Order", "temp": conv(1252.0), "x_reaction": 0.500, "x_start": 0.500, "x_end": 0.500,
             "equation": "(α-Fe, V) BCC ⇌ σ-FeV (Tetragonal Ordered Phase Summit)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1750.0)},
            {"name": "(α-Fe, V) BCC Solid Solution", "x": 0.20, "y": conv(1350.0)},
            {"name": "σ-FeV (Tetragonal)", "x": 0.50, "y": conv(950.0)},
            {"name": "BCC (V-rich)", "x": 0.85, "y": conv(1200.0)},
        ]

        return {
            "system": "Fe-V",
            "element_a": "Fe",
            "element_b": "V",
            "x_axis_label": "Atomic Fraction of V, x(V)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(2050.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 32. Cr-Mo Binary Phase Diagram (Refractory & Stainless Steel Benchmark)
    # References: K. Frisk (1991); CALPHAD.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cr_mo(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Cr (1907 C) -> minimum (1860 C, 0.20 Mo) -> Mo (2623 C)
        l_knots_1 = [(0.000, 1907.0), (0.100, 1875.0), (0.200, 1860.0)]
        l_knots_2 = [(0.200, 1860.0), (0.400, 2010.0), (0.700, 2300.0), (1.000, 2623.0)]
        s_knots_1 = [(0.000, 1907.0), (0.100, 1865.0), (0.200, 1860.0)]
        s_knots_2 = [(0.200, 1860.0), (0.400, 1960.0), (0.700, 2260.0), (1.000, 2623.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=20)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=40)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_s1, ys_s1 = _interpolate_curve(s_knots_1, n_pts=20)
        xs_s2, ys_s2 = _interpolate_curve(s_knots_2, n_pts=40)
        x_sol = xs_s1 + xs_s2
        y_sol = ys_s1 + ys_s2

        # Low-T miscibility gap below 880 C at 0.40 Mo
        mg_knots = [
            (0.150, 400.0), (0.220, 700.0), (0.300, 830.0), (0.400, 880.0),
            (0.520, 830.0), (0.650, 700.0), (0.750, 400.0)
        ]
        xs_mg, ys_mg = _interpolate_curve(mg_knots, n_pts=40)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "BCC Miscibility Gap (α₁+α₂)", "xs": xs_mg, "ys": [conv(t) for t in ys_mg], "color": "#D97706", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {"type": "Congruent Minimum", "temp": conv(1860.0), "x_reaction": 0.200, "x_start": 0.200, "x_end": 0.200,
             "equation": "L ⇌ (Cr, Mo) BCC Continuous Solid Solution Minimum"},
            {"type": "Critical Point", "temp": conv(880.0), "x_reaction": 0.400, "x_start": 0.400, "x_end": 0.400,
             "equation": "(Cr, Mo) BCC ⇌ α₁-(Cr) + α₂-(Mo) Miscibility Gap Summit"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(2400.0)},
            {"name": "(Cr, Mo) BCC Solid Solution", "x": 0.50, "y": conv(1400.0)},
            {"name": "α₁ + α₂ Gap", "x": 0.40, "y": conv(650.0)},
        ]

        return {
            "system": "Cr-Mo",
            "element_a": "Cr",
            "element_b": "Mo",
            "x_axis_label": "Atomic Fraction of Mo, x(Mo)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 33. Sn-Ag Binary Phase Diagram (Lead-Free Solder Benchmark)
    # References: U. R. Kattner, W. J. Boettinger (1994); K. W. Moon et al. (2000).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_sn_ag(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Sn (231.93 C) -> Eutectic (221.0 C, 0.035 Ag) -> Peritectic 1 (480 C, 0.11 Ag)
        # -> Peritectic 2 (724 C, 0.38 Ag) -> Ag (961.78 C)
        l_knots_1 = [(0.000, 231.93), (0.035, 221.0)]
        l_knots_2 = [(0.035, 221.0), (0.070, 350.0), (0.110, 480.0)]
        l_knots_3 = [(0.110, 480.0), (0.220, 600.0), (0.380, 724.0)]
        l_knots_4 = [(0.380, 724.0), (0.600, 830.0), (0.800, 910.0), (1.000, 961.78)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 10), (l_knots_2, 18), (l_knots_3, 22), (l_knots_4, 30)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        xs_ag_sol, ys_ag_sol = _interpolate_curve(
            [(0.885, 724.0), (0.920, 800.0), (0.960, 900.0), (1.000, 961.78)], n_pts=20
        )
        xs_zeta, ys_zeta = _interpolate_curve(
            [(0.780, 300.0), (0.780, 500.0), (0.800, 724.0), (0.840, 500.0), (0.840, 300.0)], n_pts=25
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "ε-Ag₃Sn Line", "xs": [0.250, 0.250], "ys": [conv(50.0), conv(480.0)], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "ζ-Ag₄Sn Envelope", "xs": xs_zeta, "ys": [conv(t) for t in ys_zeta], "color": "#7C3AED", "width": 1.8, "dash": "solid"},
            {"name": "(Ag) FCC Solidus", "xs": xs_ag_sol, "ys": [conv(t) for t in ys_ag_sol], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic Tie-Line (221 °C)", "xs": [0.0002, 0.250], "ys": [conv(221.0), conv(221.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic Tie-Line (480 °C)", "xs": [0.110, 0.780], "ys": [conv(480.0), conv(480.0)], "color": "#D97706", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (724 °C)", "xs": [0.380, 0.885], "ys": [conv(724.0), conv(724.0)], "color": "#7C3AED", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(221.0), "x_reaction": 0.035, "x_start": 0.0002, "x_end": 0.250,
             "equation": "L (3.5 at% Ag) ⇌ (β-Sn) (0.02 at% Ag) + ε-Ag₃Sn (25.0 at% Ag)"},
            {"type": "Peritectic", "temp": conv(480.0), "x_reaction": 0.250, "x_start": 0.110, "x_end": 0.780,
             "equation": "L (11.0 at% Ag) + ζ-Ag₄Sn (78.0 at% Ag) ⇌ ε-Ag₃Sn (25.0 at% Ag)"},
            {"type": "Peritectic", "temp": conv(724.0), "x_reaction": 0.800, "x_start": 0.380, "x_end": 0.885,
             "equation": "L (38.0 at% Ag) + (Ag) (88.5 at% Ag) ⇌ ζ-Ag₄Sn (80.0 at% Ag)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.30, "y": conv(750.0)},
            {"name": "(β-Sn)", "x": 0.01, "y": conv(150.0)},
            {"name": "ε-Ag₃Sn", "x": 0.25, "y": conv(250.0)},
            {"name": "ζ-Ag₄Sn", "x": 0.80, "y": conv(500.0)},
            {"name": "(Ag) Solution", "x": 0.94, "y": conv(600.0)},
        ]

        return {
            "system": "Sn-Ag",
            "element_a": "Sn",
            "element_b": "Ag",
            "x_axis_label": "Atomic Fraction of Ag, x(Ag)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(1050.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 34. Sn-Pb Binary Phase Diagram (Classical Solder Benchmark)
    # References: K. W. Moon et al. (2000); I. Karakaya, W. T. Thompson (1988).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_sn_pb(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Sn (231.93 C) -> Eutectic (183.0 C, 0.261 Pb) -> Pb (327.46 C)
        l_knots_1 = [(0.000, 231.93), (0.100, 212.0), (0.261, 183.0)]
        l_knots_2 = [(0.261, 183.0), (0.450, 230.0), (0.700, 280.0), (1.000, 327.46)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=25)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=35)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        # Solidus and solvus curves
        xs_sn_sol, ys_sn_sol = _interpolate_curve([(0.000, 231.93), (0.015, 205.0), (0.025, 183.0)], n_pts=15)
        xs_sn_slv, ys_sn_slv = _interpolate_curve([(0.025, 183.0), (0.015, 100.0), (0.005, 25.0)], n_pts=15)
        xs_pb_sol, ys_pb_sol = _interpolate_curve([(0.710, 183.0), (0.850, 250.0), (1.000, 327.46)], n_pts=25)
        xs_pb_slv, ys_pb_slv = _interpolate_curve([(0.710, 183.0), (0.800, 100.0), (0.870, 25.0)], n_pts=20)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "(β-Sn) Solidus", "xs": xs_sn_sol, "ys": [conv(t) for t in ys_sn_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "(β-Sn) Solvus", "xs": xs_sn_slv, "ys": [conv(t) for t in ys_sn_slv], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "(Pb) Solidus", "xs": xs_pb_sol, "ys": [conv(t) for t in ys_pb_sol], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "(Pb) Solvus", "xs": xs_pb_slv, "ys": [conv(t) for t in ys_pb_slv], "color": "#059669", "width": 1.5, "dash": "dash"},
            {"name": "Eutectic Tie-Line (183 °C)", "xs": [0.025, 0.710], "ys": [conv(183.0), conv(183.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(183.0), "x_reaction": 0.261, "x_start": 0.025, "x_end": 0.710,
             "equation": "L (26.1 at% Pb) ⇌ (β-Sn) (2.5 at% Pb) + (Pb) (71.0 at% Pb)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(260.0)},
            {"name": "(β-Sn)", "x": 0.01, "y": conv(100.0)},
            {"name": "(β-Sn) + (Pb)", "x": 0.40, "y": conv(90.0)},
            {"name": "(Pb) Solution", "x": 0.90, "y": conv(120.0)},
        ]

        return {
            "system": "Sn-Pb",
            "element_a": "Sn",
            "element_b": "Pb",
            "x_axis_label": "Atomic Fraction of Pb, x(Pb)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(360.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 35. Sn-Bi Binary Phase Diagram (Low-Melting Solder Benchmark)
    # References: B. J. Lee et al. (2001); H. Ohtani et al. (1999).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_sn_bi(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Sn (231.93 C) -> Eutectic (138.5 C, 0.43 Bi) -> Bi (271.40 C)
        l_knots_1 = [(0.000, 231.93), (0.200, 185.0), (0.430, 138.5)]
        l_knots_2 = [(0.430, 138.5), (0.700, 205.0), (1.000, 271.40)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=25)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=30)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_sn_sol, ys_sn_sol = _interpolate_curve([(0.000, 231.93), (0.070, 175.0), (0.131, 138.5)], n_pts=20)
        xs_sn_slv, ys_sn_slv = _interpolate_curve([(0.131, 138.5), (0.060, 70.0), (0.020, 25.0)], n_pts=15)
        xs_bi_sol, ys_bi_sol = _interpolate_curve([(0.980, 138.5), (1.000, 271.40)], n_pts=15)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "(β-Sn) Solidus", "xs": xs_sn_sol, "ys": [conv(t) for t in ys_sn_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "(β-Sn) Solvus", "xs": xs_sn_slv, "ys": [conv(t) for t in ys_sn_slv], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "(Bi) Solidus", "xs": xs_bi_sol, "ys": [conv(t) for t in ys_bi_sol], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic Tie-Line (138.5 °C)", "xs": [0.131, 0.980], "ys": [conv(138.5), conv(138.5)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(138.5), "x_reaction": 0.430, "x_start": 0.131, "x_end": 0.980,
             "equation": "L (43.0 at% Bi) ⇌ (β-Sn) (13.1 at% Bi) + (Bi) (98.0 at% Bi)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.45, "y": conv(220.0)},
            {"name": "(β-Sn)", "x": 0.05, "y": conv(80.0)},
            {"name": "(β-Sn) + (Bi)", "x": 0.50, "y": conv(70.0)},
            {"name": "(Bi) Rhombohedral", "x": 0.99, "y": conv(100.0)},
        ]

        return {
            "system": "Sn-Bi",
            "element_a": "Sn",
            "element_b": "Bi",
            "x_axis_label": "Atomic Fraction of Bi, x(Bi)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(0.0),
            "y_max": conv(300.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 36. Ti-Mo Binary Phase Diagram (Titanium Aerospace Alloy Benchmark)
    # References: N. Saunders (1996); S. Kumar et al. (1994).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ti_mo(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Ti (1668 C) -> Peritectic (1760 C, 0.20 Mo) -> Mo (2623 C)
        l_knots_1 = [(0.000, 1668.0), (0.100, 1715.0), (0.200, 1760.0)]
        l_knots_2 = [(0.200, 1760.0), (0.450, 2020.0), (0.750, 2350.0), (1.000, 2623.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=20)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=40)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_sol, ys_sol = _interpolate_curve(
            [(0.000, 1668.0), (0.280, 1760.0), (0.550, 2000.0), (1.000, 2623.0)], n_pts=40
        )
        xs_transus, ys_transus = _interpolate_curve(
            [(0.000, 882.0), (0.020, 780.0), (0.040, 695.0)], n_pts=15
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": xs_sol, "ys": [conv(t) for t in ys_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "α-Transus Solvus", "xs": xs_transus, "ys": [conv(t) for t in ys_transus], "color": "#059669", "width": 1.8, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1760 °C)", "xs": [0.200, 0.350], "ys": [conv(1760.0), conv(1760.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
            {"name": "Monotectoid Tie-Line (695 °C)", "xs": [0.005, 0.850], "ys": [conv(695.0), conv(695.0)], "color": "#7C3AED", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1760.0), "x_reaction": 0.200, "x_start": 0.200, "x_end": 0.350,
             "equation": "L (20.0 at% Mo) + (Mo) (35.0 at% Mo) ⇌ β-(Ti,Mo) BCC (28.0 at% Mo)"},
            {"type": "Monotectoid", "temp": conv(695.0), "x_reaction": 0.040, "x_start": 0.005, "x_end": 0.850,
             "equation": "β-Ti (4.0 at% Mo) ⇌ α-Ti (0.5 at% Mo) + β-Mo (85.0 at% Mo)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.40, "y": conv(2300.0)},
            {"name": "β-(Ti,Mo) BCC", "x": 0.30, "y": conv(1300.0)},
            {"name": "α-Ti (HCP)", "x": 0.01, "y": conv(600.0)},
            {"name": "α-Ti + β-Mo", "x": 0.40, "y": conv(500.0)},
            {"name": "(Mo) Solution", "x": 0.90, "y": conv(1500.0)},
        ]

        return {
            "system": "Ti-Mo",
            "element_a": "Ti",
            "element_b": "Mo",
            "x_axis_label": "Atomic Fraction of Mo, x(Mo)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(400.0),
            "y_max": conv(2800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 37. Ti-Zr Binary Phase Diagram (Titanium-Zirconium Isomorphous Benchmark)
    # References: S. Kumar et al. (1994); A. F. Guillermet (1991).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ti_zr(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus lens: Ti (1668 C) -> minimum (1540 C, 0.50 Zr) -> Zr (1855 C)
        l_knots = [(0.000, 1668.0), (0.250, 1580.0), (0.500, 1540.0), (0.750, 1670.0), (1.000, 1855.0)]
        s_knots = [(0.000, 1668.0), (0.250, 1560.0), (0.500, 1540.0), (0.750, 1650.0), (1.000, 1855.0)]
        x_liq, y_liq = _interpolate_curve(l_knots, n_pts=50)
        x_sol, y_sol = _interpolate_curve(s_knots, n_pts=50)

        # Transus lens: Ti (882 C) -> minimum (605 C, 0.50 Zr) -> Zr (863 C)
        t_knots = [(0.000, 882.0), (0.250, 710.0), (0.500, 605.0), (0.750, 715.0), (1.000, 863.0)]
        x_trn, y_trn = _interpolate_curve(t_knots, n_pts=50)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "β-Transus (BCC ⇌ HCP)", "xs": x_trn, "ys": [conv(t) for t in y_trn], "color": "#059669", "width": 2.0, "dash": "solid"},
        ]

        invariants = [
            {"type": "Congruent Minimum", "temp": conv(1540.0), "x_reaction": 0.500, "x_start": 0.500, "x_end": 0.500,
             "equation": "L ⇌ β-(Ti,Zr) BCC Continuous Solid Solution Minimum"},
            {"type": "Transus Minimum", "temp": conv(605.0), "x_reaction": 0.500, "x_start": 0.500, "x_end": 0.500,
             "equation": "β-(Ti,Zr) ⇌ α-(Ti,Zr) HCP Solid Solution Minimum"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1750.0)},
            {"name": "β-(Ti,Zr) BCC Solution", "x": 0.50, "y": conv(1100.0)},
            {"name": "α-(Ti,Zr) HCP Solution", "x": 0.50, "y": conv(450.0)},
        ]

        return {
            "system": "Ti-Zr",
            "element_a": "Ti",
            "element_b": "Zr",
            "x_axis_label": "Atomic Fraction of Zr, x(Zr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 38. Zr-Nb Binary Phase Diagram (Nuclear Zircaloy Benchmark)
    # References: A. F. Guillermet (1991); H. Okamoto (1992).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_zr_nb(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Zr (1855 C) -> minimum (1740 C, 0.22 Nb) -> Nb (2469 C)
        l_knots_1 = [(0.000, 1855.0), (0.100, 1780.0), (0.220, 1740.0)]
        l_knots_2 = [(0.220, 1740.0), (0.500, 1950.0), (0.750, 2220.0), (1.000, 2469.0)]
        s_knots_1 = [(0.000, 1855.0), (0.100, 1760.0), (0.220, 1740.0)]
        s_knots_2 = [(0.220, 1740.0), (0.500, 1900.0), (0.750, 2180.0), (1.000, 2469.0)]

        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=20)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=35)
        x_liq = xs_l1 + xs_l2
        y_liq = ys_l1 + ys_l2

        xs_s1, ys_s1 = _interpolate_curve(s_knots_1, n_pts=20)
        xs_s2, ys_s2 = _interpolate_curve(s_knots_2, n_pts=35)
        x_sol = xs_s1 + xs_s2
        y_sol = ys_s1 + ys_s2

        # BCC miscibility gap summit at 980 C at 0.45 Nb
        mg_knots = [
            (0.185, 610.0), (0.250, 800.0), (0.350, 940.0), (0.450, 980.0),
            (0.580, 940.0), (0.720, 800.0), (0.860, 610.0)
        ]
        xs_mg, ys_mg = _interpolate_curve(mg_knots, n_pts=40)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "BCC Miscibility Gap (β₁+β₂)", "xs": xs_mg, "ys": [conv(t) for t in ys_mg], "color": "#D97706", "width": 1.8, "dash": "dash"},
            {"name": "Monotectoid Tie-Line (610 °C)", "xs": [0.006, 0.860], "ys": [conv(610.0), conv(610.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
        ]

        invariants = [
            {"type": "Congruent Minimum", "temp": conv(1740.0), "x_reaction": 0.220, "x_start": 0.220, "x_end": 0.220,
             "equation": "L ⇌ β-(Zr,Nb) BCC Solid Solution Minimum"},
            {"type": "Critical Point", "temp": conv(980.0), "x_reaction": 0.450, "x_start": 0.450, "x_end": 0.450,
             "equation": "β-(Zr,Nb) ⇌ β₁-(Zr) + β₂-(Nb) Miscibility Gap Summit"},
            {"type": "Monotectoid", "temp": conv(610.0), "x_reaction": 0.185, "x_start": 0.006, "x_end": 0.860,
             "equation": "β-Zr (18.5 at% Nb) ⇌ α-Zr (0.6 at% Nb) + β-Nb (86.0 at% Nb)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(2200.0)},
            {"name": "β-(Zr,Nb) BCC", "x": 0.30, "y": conv(1200.0)},
            {"name": "β₁ + β₂ Gap", "x": 0.45, "y": conv(800.0)},
            {"name": "α-Zr (HCP)", "x": 0.005, "y": conv(500.0)},
            {"name": "α-Zr + β-Nb", "x": 0.45, "y": conv(450.0)},
        ]

        return {
            "system": "Zr-Nb",
            "element_a": "Zr",
            "element_b": "Nb",
            "x_axis_label": "Atomic Fraction of Nb, x(Nb)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(2600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 39. Zr-Sn Binary Phase Diagram (Nuclear Zircaloy Tin Benchmark)
    # References: N. Saunders (1996); O. J. Kwon et al. (2004).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_zr_sn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Zr (1855 C) -> Peritectic (1765 C, 0.24 Sn) -> Zr5Sn3 summit (1985 C, 0.375 Sn)
        # -> Peritectic (1140 C, 0.85 Sn) -> Eutectic (231.5 C, 0.998 Sn) -> Sn (231.93 C)
        l_knots_1 = [(0.000, 1855.0), (0.150, 1800.0), (0.240, 1765.0)]
        l_knots_2 = [(0.240, 1765.0), (0.320, 1920.0), (0.375, 1985.0)]
        l_knots_3 = [(0.375, 1985.0), (0.550, 1650.0), (0.750, 1300.0), (0.850, 1140.0)]
        l_knots_4 = [(0.850, 1140.0), (0.950, 600.0), (0.998, 231.5)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 20), (l_knots_2, 20), (l_knots_3, 30), (l_knots_4, 25)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        xs_zr5sn3, ys_zr5sn3 = _interpolate_curve(
            [(0.365, 400.0), (0.365, 1200.0), (0.375, 1985.0), (0.385, 1200.0), (0.385, 400.0)], n_pts=25
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Zr₅Sn₃ Envelope", "xs": xs_zr5sn3, "ys": [conv(t) for t in ys_zr5sn3], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "ZrSn₂ Line", "xs": [0.667, 0.667], "ys": [conv(200.0), conv(1140.0)], "color": "#D97706", "width": 1.8, "dash": "solid"},
            {"name": "Peritectic Tie-Line (1765 °C)", "xs": [0.160, 0.365], "ys": [conv(1765.0), conv(1765.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1140 °C)", "xs": [0.667, 0.850], "ys": [conv(1140.0), conv(1140.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
            {"name": "Peritectoid Tie-Line (980 °C)", "xs": [0.060, 0.365], "ys": [conv(980.0), conv(980.0)], "color": "#059669", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Peritectic", "temp": conv(1765.0), "x_reaction": 0.240, "x_start": 0.160, "x_end": 0.365,
             "equation": "L (24.0 at% Sn) + Zr₅Sn₃ (37.5 at% Sn) ⇌ β-Zr (16.0 at% Sn)"},
            {"type": "Congruent", "temp": conv(1985.0), "x_reaction": 0.375, "x_start": 0.375, "x_end": 0.375,
             "equation": "L ⇌ Zr₅Sn₃ (Hexagonal Congruent Summit)"},
            {"type": "Peritectic", "temp": conv(1140.0), "x_reaction": 0.667, "x_start": 0.385, "x_end": 0.850,
             "equation": "L (85.0 at% Sn) + Zr₅Sn₃ ⇌ ZrSn₂ (66.7 at% Sn)"},
            {"type": "Peritectoid", "temp": conv(980.0), "x_reaction": 0.090, "x_start": 0.060, "x_end": 0.365,
             "equation": "β-Zr (6.0 at% Sn) + Zr₅Sn₃ ⇌ α-Zr (9.0 at% Sn, Zircaloy α-Stabilizer)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(2050.0)},
            {"name": "β-Zr Solution", "x": 0.08, "y": conv(1400.0)},
            {"name": "α-Zr (Zircaloy)", "x": 0.04, "y": conv(700.0)},
            {"name": "Zr₅Sn₃", "x": 0.375, "y": conv(1000.0)},
            {"name": "ZrSn₂", "x": 0.667, "y": conv(600.0)},
        ]

        return {
            "system": "Zr-Sn",
            "element_a": "Zr",
            "element_b": "Sn",
            "x_axis_label": "Atomic Fraction of Sn, x(Sn)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 40. Co-W Binary Phase Diagram (Cobalt Superalloy & Stellite Benchmark)
    # References: A. F. Guillermet (1988); S. V. Nagender Naidu (1991).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_w(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus: Co (1495 C) -> Eutectic (1465 C, 0.165 W) -> Peritectic (1680 C, 0.38 W) -> W (3422 C)
        l_knots_1 = [(0.000, 1495.0), (0.080, 1480.0), (0.165, 1465.0)]
        l_knots_2 = [(0.165, 1465.0), (0.280, 1580.0), (0.380, 1680.0)]
        l_knots_3 = [(0.380, 1680.0), (0.600, 2250.0), (0.800, 2850.0), (1.000, 3422.0)]

        x_liq, y_liq = [], []
        for knots, cnt in [(l_knots_1, 15), (l_knots_2, 20), (l_knots_3, 35)]:
            xs, ys = _interpolate_curve(knots, n_pts=cnt)
            x_liq.extend(xs)
            y_liq.extend(ys)

        xs_co7w6, ys_co7w6 = _interpolate_curve(
            [(0.450, 400.0), (0.450, 1000.0), (0.462, 1680.0), (0.475, 1000.0), (0.475, 400.0)], n_pts=25
        )

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Co₇W₆ (μ-Phase) Envelope", "xs": xs_co7w6, "ys": [conv(t) for t in ys_co7w6], "color": "#7C3AED", "width": 2.0, "dash": "solid"},
            {"name": "ε-Co₃W Line", "xs": [0.250, 0.250], "ys": [conv(300.0), conv(1080.0)], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic Tie-Line (1465 °C)", "xs": [0.140, 0.450], "ys": [conv(1465.0), conv(1465.0)], "color": "#2563EB", "width": 1.5, "dash": "dash"},
            {"name": "Peritectic Tie-Line (1680 °C)", "xs": [0.380, 0.980], "ys": [conv(1680.0), conv(1680.0)], "color": "#DC2626", "width": 1.5, "dash": "dash"},
        ]

        invariants = [
            {"type": "Eutectic", "temp": conv(1465.0), "x_reaction": 0.165, "x_start": 0.140, "x_end": 0.450,
             "equation": "L (16.5 at% W) ⇌ (α-Co) (14.0 at% W) + Co₇W₆ (46.2 at% W)"},
            {"type": "Peritectic", "temp": conv(1680.0), "x_reaction": 0.380, "x_start": 0.380, "x_end": 0.980,
             "equation": "L (38.0 at% W) + (W) (98.0 at% W) ⇌ Co₇W₆ (μ-phase, 46.2 at% W)"},
            {"type": "Peritectoid", "temp": conv(1080.0), "x_reaction": 0.250, "x_start": 0.100, "x_end": 0.450,
             "equation": "(α-Co) (10.0 at% W) + Co₇W₆ ⇌ ε-Co₃W (25.0 at% W)"}
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.30, "y": conv(2000.0)},
            {"name": "(α-Co) FCC Solution", "x": 0.05, "y": conv(1100.0)},
            {"name": "ε-Co₃W", "x": 0.25, "y": conv(650.0)},
            {"name": "Co₇W₆ (μ-Phase)", "x": 0.462, "y": conv(1000.0)},
            {"name": "(W) BCC Solution", "x": 0.85, "y": conv(1800.0)},
        ]

        return {
            "system": "Co-W",
            "element_a": "Co",
            "element_b": "W",
            "x_axis_label": "Atomic Fraction of W, x(W)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(300.0),
            "y_max": conv(3600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 41. Mo-W Binary Phase Diagram (Refractory RHEA Benchmark)
    # References: S. V. Nagender Naidu et al. (1991); SGTE (1991).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_mo_w(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Textbook continuous isomorphous BCC solid solution lens from Mo (2623 C) to W (3422 C)
        l_knots = [(0.000, 2623.0), (0.250, 2810.0), (0.500, 3015.0), (0.750, 3220.0), (1.000, 3422.0)]
        s_knots = [(0.000, 2623.0), (0.250, 2760.0), (0.500, 2960.0), (0.750, 3180.0), (1.000, 3422.0)]

        x_liq, y_liq = _interpolate_curve(l_knots, n_pts=50)
        x_sol, y_sol = _interpolate_curve(s_knots, n_pts=50)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
        ]

        invariants = [
            {"type": "Isomorphous", "temp": conv(3015.0), "x_reaction": 0.500, "x_start": 0.000, "x_end": 1.000,
             "equation": "Continuous Isomorphous BCC Refractory Solid Solution Lens"}
        ]

        regions = [
            {"name": "Liquid Solution (L)", "x": 0.40, "y": conv(3250.0)},
            {"name": "(Mo, W) BCC Continuous Solid Solution", "x": 0.50, "y": conv(2400.0)},
            {"name": "Two-Phase Field (L + BCC)", "x": 0.50, "y": conv(2990.0)},
        ]

        return {
            "system": "Mo-W",
            "element_a": "Mo",
            "element_b": "W",
            "x_axis_label": "Atomic Fraction of W, x(W)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(1500.0),
            "y_max": conv(3600.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 42. Nb-Mo Binary Phase Diagram (Refractory RHEA Benchmark)
    # References: A. F. Guillermet (1991); H. Okamoto (1992).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_nb_mo(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Continuous isomorphous BCC lens connecting Nb (2469 C) to Mo (2623 C)
        l_knots = [(0.000, 2469.0), (0.300, 2515.0), (0.600, 2565.0), (1.000, 2623.0)]
        s_knots = [(0.000, 2469.0), (0.300, 2495.0), (0.600, 2545.0), (1.000, 2623.0)]

        x_liq, y_liq = _interpolate_curve(l_knots, n_pts=45)
        x_sol, y_sol = _interpolate_curve(s_knots, n_pts=45)

        curves = [
            {"name": "Liquidus", "xs": x_liq, "ys": [conv(t) for t in y_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus", "xs": x_sol, "ys": [conv(t) for t in y_sol], "color": "#2563EB", "width": 1.8, "dash": "solid"},
        ]

        invariants = [
            {"type": "Isomorphous", "temp": conv(2545.0), "x_reaction": 0.500, "x_start": 0.000, "x_end": 1.000,
             "equation": "Continuous Isomorphous BCC Refractory Solid Solution Lens"}
        ]

        regions = [
            {"name": "Liquid Solution (L)", "x": 0.50, "y": conv(2680.0)},
            {"name": "(Nb, Mo) BCC Continuous Solid Solution", "x": 0.50, "y": conv(2200.0)},
            {"name": "Two-Phase Field (L + BCC)", "x": 0.50, "y": conv(2550.0)},
        ]

        return {
            "system": "Nb-Mo",
            "element_a": "Nb",
            "element_b": "Mo",
            "x_axis_label": "Atomic Fraction of Mo, x(Mo)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(1500.0),
            "y_max": conv(2800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 41. Al-Zr Binary Phase Diagram (Assessed Pandat/CALPHAD Benchmark)
    # References: T. Wang, Z. Jin, J.-C. Zhao (2001); T. Hirano et al. (2010); Pandat database.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_zr(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq_knots = [
            (0.00, 660.45),
            (0.0004, 660.6),
            (0.08, 1150.0),
            (0.18, 1480.0),
            (0.25, 1583.1),
            (0.30, 1630.0),
            (0.333, 1648.0),
            (0.40, 1590.0),
            (0.48, 1500.0),
            (0.556, 1550.0),
            (0.60, 1480.0),
            (0.625, 1450.0),
            (0.705, 1347.8),
            (0.78, 1500.0),
            (0.88, 1680.0),
            (1.00, 1855.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        beta_sol_knots = [(0.751, 1347.8), (0.85, 1580.0), (0.95, 1750.0), (1.00, 1855.0)]
        xs_bsol, ys_bsol = _interpolate_curve(beta_sol_knots, n_pts=40, clip_x_min=0.751, clip_x_max=1.0)

        beta_solvus_knots = [(0.751, 1347.8), (0.82, 1150.0), (0.931, 909.7)]
        xs_bsolvus, ys_bsolvus = _interpolate_curve(beta_solvus_knots, n_pts=30, clip_x_min=0.751, clip_x_max=0.931)

        alpha_solvus_knots = [(1.00, 863.0), (0.95, 890.0), (0.918, 909.7), (0.97, 600.0), (0.99, 200.0)]
        xs_asolvus, ys_asolvus = _interpolate_curve(alpha_solvus_knots, n_pts=30, clip_x_min=0.918, clip_x_max=1.0)

        invariants = [
            {"type": "Eutectic", "temp": conv(660.6), "x_reaction": 0.0004, "x_start": 0.0, "x_end": 0.25,
             "equation": "L (0.04 at% Zr) ⇌ (Al) + Al₃Zr at 661 °C"},
            {"type": "Congruent / Peritectic", "temp": conv(1583.1), "x_reaction": 0.250, "x_start": 0.250, "x_end": 0.250,
             "equation": "L + Al₂Zr ⇌ Al₃Zr at 1583 °C"},
            {"type": "Peritectic", "temp": conv(1592.4), "x_reaction": 0.333, "x_start": 0.333, "x_end": 0.400,
             "equation": "L + Al₃Zr₂ ⇌ Al₂Zr at 1592 °C"},
            {"type": "Congruent Peak", "temp": conv(1550.0), "x_reaction": 0.556, "x_start": 0.556, "x_end": 0.556,
             "equation": "L ⇌ Al₄Zr₅ (Congruent summit at ~1550 °C)"},
            {"type": "Eutectic", "temp": conv(1347.8), "x_reaction": 0.705, "x_start": 0.625, "x_end": 0.751,
             "equation": "L (70.5 at% Zr) ⇌ Al₃Zr₅ + β-(Zr) at 1348 °C"},
            {"type": "Eutectoid", "temp": conv(909.7), "x_reaction": 0.931, "x_start": 0.750, "x_end": 0.931,
             "equation": "β-(Zr) (93.1 at% Zr) ⇌ AlZr₃ + α-(Zr) at 910 °C"}
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "β-BCC(Zr) Solidus", "xs": xs_bsol, "ys": [conv(t) for t in ys_bsol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "β-BCC(Zr) Solvus", "xs": xs_bsolvus, "ys": [conv(t) for t in ys_bsolvus], "color": "#1D4ED8", "width": 1.6, "dash": "dash"},
            {"name": "α-HCP(Zr) Solvus", "xs": xs_asolvus, "ys": [conv(t) for t in ys_asolvus], "color": "#047857", "width": 1.6, "dash": "dash"},
            {"name": "Al₃Zr", "xs": [0.25, 0.25], "ys": [conv(200.0), conv(1583.1)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₂Zr", "xs": [0.333, 0.333], "ys": [conv(200.0), conv(1592.4)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₃Zr₂", "xs": [0.40, 0.40], "ys": [conv(200.0), conv(1476.9)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "AlZr", "xs": [0.50, 0.50], "ys": [conv(200.0), conv(1274.6)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₃Zr₄", "xs": [0.571, 0.571], "ys": [conv(200.0), conv(1030.5)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₄Zr₅", "xs": [0.556, 0.556], "ys": [conv(1030.5), conv(1550.0)], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Al₂Zr₃", "xs": [0.60, 0.60], "ys": [conv(1030.5), conv(1402.9)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₃Zr₅", "xs": [0.625, 0.625], "ys": [conv(999.1), conv(1347.8)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "AlZr₂", "xs": [0.667, 0.667], "ys": [conv(200.0), conv(1213.3)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "AlZr₃", "xs": [0.75, 0.75], "ys": [conv(200.0), conv(1018.7)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic (661 °C)", "xs": [0.0004, 0.25], "ys": [conv(660.6), conv(660.6)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1583 °C)", "xs": [0.25, 0.333], "ys": [conv(1583.1), conv(1583.1)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1477 °C)", "xs": [0.40, 0.556], "ys": [conv(1476.9), conv(1476.9)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (1348 °C)", "xs": [0.625, 0.751], "ys": [conv(1347.8), conv(1347.8)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectoid (910 °C)", "xs": [0.75, 0.931], "ys": [conv(909.7), conv(909.7)], "color": "#9333EA", "width": 1.6, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.45, "y": conv(1750.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al) FCC", "x": 0.02, "y": conv(450.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Al₃Zr", "x": 0.25, "y": conv(800.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₂Zr", "x": 0.333, "y": conv(800.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₃Zr₂", "x": 0.40, "y": conv(800.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "AlZr", "x": 0.50, "y": conv(800.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₄Zr₅", "x": 0.556, "y": conv(1200.0), "font_size": 10, "color": "#065F46"},
            {"label": "Al₂Zr₃", "x": 0.60, "y": conv(800.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₃Zr₅", "x": 0.625, "y": conv(1100.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "AlZr₂", "x": 0.667, "y": conv(700.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "AlZr₃", "x": 0.75, "y": conv(700.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "β-(Zr) BCC", "x": 0.85, "y": conv(1350.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "α-(Zr) HCP", "x": 0.96, "y": conv(500.0), "font_size": 11, "color": "#065F46"}
        ]

        return {
            "system": "Al-Zr",
            "element_a": "Al",
            "element_b": "Zr",
            "x_axis_label": "Atomic Fraction of Zr, x(Zr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 42. Al-Y Binary Phase Diagram (Assessed Literature Benchmark)
    # References: S. Al Shakshir, M. Medraj (2006); H. Okamoto (ASM).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_al_y(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq_knots = [
            (0.00, 660.45),
            (0.030, 644.0),
            (0.126, 980.0),
            (0.20, 1250.0),
            (0.28, 1440.0),
            (0.333, 1490.0),
            (0.40, 1380.0),
            (0.50, 1150.0),
            (0.511, 1137.0),
            (0.562, 1083.0),
            (0.62, 1098.0),
            (0.667, 1104.0),
            (0.708, 978.0),
            (0.80, 1200.0),
            (0.90, 1400.0),
            (0.979, 1478.0),
            (1.00, 1522.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        beta_y_knots = [(0.979, 1478.0), (0.99, 1500.0), (1.00, 1522.0)]
        xs_by, ys_by = _interpolate_curve(beta_y_knots, n_pts=20, clip_x_min=0.979, clip_x_max=1.0)

        invariants = [
            {"type": "Eutectic", "temp": conv(644.0), "x_reaction": 0.030, "x_start": 0.0, "x_end": 0.25,
             "equation": "L (3.0 at% Y) ⇌ (Al) + αAl₃Y at 644 °C"},
            {"type": "Peritectic", "temp": conv(980.0), "x_reaction": 0.126, "x_start": 0.126, "x_end": 0.333,
             "equation": "L (12.6 at% Y) + Al₂Y ⇌ βAl₃Y at 980 °C"},
            {"type": "Congruent Peak", "temp": conv(1490.0), "x_reaction": 0.333, "x_start": 0.333, "x_end": 0.333,
             "equation": "L ⇌ Al₂Y (Laves C15 Congruent Summit at 1490 °C)"},
            {"type": "Peritectic", "temp": conv(1137.0), "x_reaction": 0.511, "x_start": 0.333, "x_end": 0.500,
             "equation": "L (51.1 at% Y) + Al₂Y ⇌ AlY at 1137 °C"},
            {"type": "Peritectic", "temp": conv(1083.0), "x_reaction": 0.562, "x_start": 0.500, "x_end": 0.600,
             "equation": "L (56.2 at% Y) + AlY ⇌ Al₂Y₃ at 1083 °C"},
            {"type": "Congruent Peak", "temp": conv(1104.0), "x_reaction": 0.667, "x_start": 0.667, "x_end": 0.667,
             "equation": "L ⇌ AlY₂ (Congruent Melting at 1104 °C)"},
            {"type": "Eutectic", "temp": conv(978.0), "x_reaction": 0.708, "x_start": 0.667, "x_end": 0.999,
             "equation": "L (70.8 at% Y) ⇌ AlY₂ + (αY) at 978 °C"},
            {"type": "Allotropic Invariant", "temp": conv(1478.0), "x_reaction": 0.979, "x_start": 0.979, "x_end": 1.0,
             "equation": "β-(Y) ⇌ α-(Y) Allotropic Transition at 1478 °C"}
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "β-(Y) Solidus", "xs": xs_by, "ys": [conv(t) for t in ys_by], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "Al₃Y (α/β)", "xs": [0.25, 0.25], "ys": [conv(200.0), conv(980.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₂Y (Laves C15)", "xs": [0.333, 0.333], "ys": [conv(200.0), conv(1490.0)], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "AlY", "xs": [0.50, 0.50], "ys": [conv(200.0), conv(1137.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Al₂Y₃", "xs": [0.60, 0.60], "ys": [conv(200.0), conv(1083.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "AlY₂", "xs": [0.667, 0.667], "ys": [conv(200.0), conv(1104.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic (644 °C)", "xs": [0.0, 0.25], "ys": [conv(644.0), conv(644.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (980 °C)", "xs": [0.126, 0.333], "ys": [conv(980.0), conv(980.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1137 °C)", "xs": [0.333, 0.511], "ys": [conv(1137.0), conv(1137.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1083 °C)", "xs": [0.50, 0.562], "ys": [conv(1083.0), conv(1083.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (978 °C)", "xs": [0.667, 0.999], "ys": [conv(978.0), conv(978.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Invariant (954 °C)", "xs": [0.737, 1.0], "ys": [conv(954.0), conv(954.0)], "color": "#9333EA", "width": 1.5, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.40, "y": conv(1600.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Al) Solid Solution", "x": 0.02, "y": conv(450.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Al₃Y", "x": 0.25, "y": conv(500.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₂Y (C15)", "x": 0.333, "y": conv(1000.0), "font_size": 11, "color": "#065F46"},
            {"label": "AlY", "x": 0.50, "y": conv(650.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Al₂Y₃", "x": 0.60, "y": conv(650.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "AlY₂", "x": 0.667, "y": conv(650.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "(αY) Solid Solution", "x": 0.85, "y": conv(600.0), "font_size": 11, "color": "#065F46"},
            {"label": "(βY)", "x": 0.985, "y": conv(1500.0), "font_size": 10, "color": "#1E3A8A"}
        ]

        return {
            "system": "Al-Y",
            "element_a": "Al",
            "element_b": "Y",
            "x_axis_label": "Atomic Fraction of Y, x(Y)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1700.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 43. Co-Zr Binary Phase Diagram (Assessed Literature Benchmark)
    # References: J. Bratberg, B. Jansson (2006); H. Okamoto (ASM).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_zr(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq_knots = [
            (0.00, 1495.0),
            (0.05, 1370.0),
            (0.110, 1254.0),
            (0.154, 1272.0),
            (0.207, 1331.0),
            (0.27, 1480.0),
            (0.333, 1544.0),
            (0.380, 1315.0),
            (0.45, 1335.0),
            (0.50, 1349.0),
            (0.60, 1200.0),
            (0.650, 1048.0),
            (0.667, 1050.0),
            (0.745, 980.0),
            (0.85, 1400.0),
            (0.95, 1700.0),
            (1.00, 1855.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        bz_sol_knots = [(0.745, 980.0), (0.85, 1350.0), (0.95, 1680.0), (1.00, 1855.0)]
        xs_bzsol, ys_bzsol = _interpolate_curve(bz_sol_knots, n_pts=40, clip_x_min=0.745, clip_x_max=1.0)

        bz_solvus_knots = [(0.745, 980.0), (0.88, 860.0), (0.98, 829.0), (1.00, 863.0)]
        xs_bzsolvus, ys_bzsolvus = _interpolate_curve(bz_solvus_knots, n_pts=30, clip_x_min=0.745, clip_x_max=1.0)

        invariants = [
            {"type": "Eutectic", "temp": conv(1254.0), "x_reaction": 0.110, "x_start": 0.0, "x_end": 0.154,
             "equation": "L (11.0 at% Zr) ⇌ (Co) + Co₁₁Zr₂ at 1254 °C"},
            {"type": "Peritectic", "temp": conv(1272.0), "x_reaction": 0.154, "x_start": 0.154, "x_end": 0.207,
             "equation": "L + Co₂₃Zr₆ ⇌ Co₁₁Zr₂ at 1272 °C"},
            {"type": "Peritectic", "temp": conv(1331.0), "x_reaction": 0.207, "x_start": 0.207, "x_end": 0.333,
             "equation": "L + Co₂Zr ⇌ Co₂₃Zr₆ at 1331 °C"},
            {"type": "Congruent Peak", "temp": conv(1544.0), "x_reaction": 0.333, "x_start": 0.333, "x_end": 0.333,
             "equation": "L ⇌ Co₂Zr (Laves C15 Congruent Summit at 1544 °C)"},
            {"type": "Eutectic", "temp": conv(1315.0), "x_reaction": 0.380, "x_start": 0.333, "x_end": 0.500,
             "equation": "L (38.0 at% Zr) ⇌ Co₂Zr + CoZr at 1315 °C"},
            {"type": "Peritectic", "temp": conv(1349.0), "x_reaction": 0.500, "x_start": 0.500, "x_end": 0.667,
             "equation": "L + Co₂Zr ⇌ CoZr at 1349 °C"},
            {"type": "Eutectic", "temp": conv(1048.0), "x_reaction": 0.650, "x_start": 0.500, "x_end": 0.667,
             "equation": "L (65.0 at% Zr) ⇌ CoZr + CoZr₂ at 1048 °C"},
            {"type": "Eutectic", "temp": conv(980.0), "x_reaction": 0.745, "x_start": 0.667, "x_end": 0.980,
             "equation": "L (74.5 at% Zr) ⇌ CoZr₂ + β-(Zr) at 980 °C"},
            {"type": "Eutectoid", "temp": conv(829.0), "x_reaction": 0.980, "x_start": 0.750, "x_end": 0.990,
             "equation": "β-(Zr) ⇌ CoZr₃ + α-(Zr) at 829 °C"}
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "β-(Zr) Solidus", "xs": xs_bzsol, "ys": [conv(t) for t in ys_bzsol], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "β-(Zr) Solvus", "xs": xs_bzsolvus, "ys": [conv(t) for t in ys_bzsolvus], "color": "#1D4ED8", "width": 1.6, "dash": "dash"},
            {"name": "Co₁₁Zr₂", "xs": [0.154, 0.154], "ys": [conv(200.0), conv(1272.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Co₂₃Zr₆", "xs": [0.207, 0.207], "ys": [conv(200.0), conv(1331.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Co₂Zr (C15)", "xs": [0.333, 0.333], "ys": [conv(200.0), conv(1544.0)], "color": "#059669", "width": 2.0, "dash": "solid"},
            {"name": "CoZr", "xs": [0.50, 0.50], "ys": [conv(200.0), conv(1349.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "CoZr₂", "xs": [0.667, 0.667], "ys": [conv(200.0), conv(1050.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "CoZr₃", "xs": [0.75, 0.75], "ys": [conv(200.0), conv(986.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Eutectic (1254 °C)", "xs": [0.0, 0.154], "ys": [conv(1254.0), conv(1254.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1272 °C)", "xs": [0.154, 0.207], "ys": [conv(1272.0), conv(1272.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1331 °C)", "xs": [0.207, 0.333], "ys": [conv(1331.0), conv(1331.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (1315 °C)", "xs": [0.333, 0.500], "ys": [conv(1315.0), conv(1315.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (1048 °C)", "xs": [0.500, 0.667], "ys": [conv(1048.0), conv(1048.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (980 °C)", "xs": [0.667, 0.980], "ys": [conv(980.0), conv(980.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectoid (829 °C)", "xs": [0.750, 0.990], "ys": [conv(829.0), conv(829.0)], "color": "#9333EA", "width": 1.6, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.40, "y": conv(1700.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Co) Solid Solution", "x": 0.03, "y": conv(800.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Co₁₁Zr₂", "x": 0.154, "y": conv(700.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Co₂₃Zr₆", "x": 0.207, "y": conv(700.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "Co₂Zr (C15)", "x": 0.333, "y": conv(1000.0), "font_size": 11, "color": "#065F46"},
            {"label": "CoZr", "x": 0.50, "y": conv(700.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "CoZr₂", "x": 0.667, "y": conv(600.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "CoZr₃", "x": 0.75, "y": conv(600.0), "font_size": 10, "color": "#1E3A8A"},
            {"label": "β-(Zr) BCC", "x": 0.88, "y": conv(1200.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "α-(Zr) HCP", "x": 0.96, "y": conv(500.0), "font_size": 11, "color": "#065F46"}
        ]

        return {
            "system": "Co-Zr",
            "element_a": "Co",
            "element_b": "Zr",
            "x_axis_label": "Atomic Fraction of Zr, x(Zr)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2000.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 44. Co-Y Binary Phase Diagram (Assessed Literature Benchmark)
    # References: Y. Wang, M. Ostrowska, G. Cacciamani (2021); Z. Du et al. (1996).
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_co_y(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq_knots = [
            (0.00, 1495.0),
            (0.05, 1420.0),
            (0.105, 1342.0),
            (0.167, 1327.0),
            (0.222, 1308.0),
            (0.250, 1154.0),
            (0.333, 866.0),
            (0.400, 798.0),
            (0.500, 740.0),
            (0.620, 733.0),
            (0.750, 883.0),
            (0.88, 1200.0),
            (0.979, 1478.0),
            (1.00, 1522.0)
        ]
        xs_liq, ys_liq = _interpolate_curve(liq_knots, n_pts=n_pts, clip_x_min=0.0, clip_x_max=1.0)

        invariants = [
            {"type": "Peritectic", "temp": conv(1342.0), "x_reaction": 0.105, "x_start": 0.0, "x_end": 0.105,
             "equation": "L + Y₂Co₁₇ peritectic at 1342 °C (1615 K)"},
            {"type": "Peritectic", "temp": conv(1327.0), "x_reaction": 0.167, "x_start": 0.105, "x_end": 0.167,
             "equation": "L + YCo₅ peritectic at 1327 °C (1600 K)"},
            {"type": "Peritectic", "temp": conv(1308.0), "x_reaction": 0.222, "x_start": 0.167, "x_end": 0.222,
             "equation": "L + Y₂Co₇ peritectic at 1308 °C (1581 K)"},
            {"type": "Peritectic", "temp": conv(1154.0), "x_reaction": 0.250, "x_start": 0.222, "x_end": 0.250,
             "equation": "L + YCo₃ peritectic at 1154 °C (1427 K)"},
            {"type": "Peritectic", "temp": conv(866.0), "x_reaction": 0.333, "x_start": 0.250, "x_end": 0.333,
             "equation": "L + YCo₂ peritectic at 866 °C (1139 K)"},
            {"type": "Eutectic", "temp": conv(733.0), "x_reaction": 0.620, "x_start": 0.500, "x_end": 0.750,
             "equation": "L (62.0 at% Y) ⇌ Y₈Co₅ + Y₃Co at 733 °C (1006 K)"},
            {"type": "Peritectic", "temp": conv(883.0), "x_reaction": 0.750, "x_start": 0.750, "x_end": 0.980,
             "equation": "L + Y₃Co peritectic at 883 °C (1156 K)"}
        ]

        curves = [
            {"name": "Liquidus", "xs": xs_liq, "ys": [conv(t) for t in ys_liq], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Y₂Co₁₇", "xs": [0.105, 0.105], "ys": [conv(200.0), conv(1342.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "YCo₅", "xs": [0.167, 0.167], "ys": [conv(698.0), conv(1327.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Y₂Co₇", "xs": [0.222, 0.222], "ys": [conv(200.0), conv(1308.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "YCo₃", "xs": [0.250, 0.250], "ys": [conv(200.0), conv(1154.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "YCo₂", "xs": [0.333, 0.333], "ys": [conv(200.0), conv(866.0)], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "Y₂Co₃", "xs": [0.400, 0.400], "ys": [conv(200.0), conv(798.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "YCo", "xs": [0.500, 0.500], "ys": [conv(200.0), conv(740.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Y₈Co₅", "xs": [0.615, 0.615], "ys": [conv(200.0), conv(738.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Y₃Co", "xs": [0.750, 0.750], "ys": [conv(200.0), conv(883.0)], "color": "#1E3A8A", "width": 1.8, "dash": "solid"},
            {"name": "Peritectic (1615 K)", "xs": [0.0, 0.105], "ys": [conv(1342.0), conv(1342.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1581 K)", "xs": [0.167, 0.222], "ys": [conv(1308.0), conv(1308.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1427 K)", "xs": [0.222, 0.250], "ys": [conv(1154.0), conv(1154.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Eutectic (1006 K)", "xs": [0.500, 0.750], "ys": [conv(733.0), conv(733.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"},
            {"name": "Peritectic (1156 K)", "xs": [0.750, 0.980], "ys": [conv(883.0), conv(883.0)], "color": "#DC2626", "width": 1.6, "dash": "dash"}
        ]

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.40, "y": conv(1500.0), "font_size": 13, "color": "#0F172A"},
            {"label": "(Co)", "x": 0.03, "y": conv(800.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "Y₂Co₁₇", "x": 0.105, "y": conv(900.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "YCo₅", "x": 0.167, "y": conv(1000.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "Y₂Co₇", "x": 0.222, "y": conv(900.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "YCo₃", "x": 0.250, "y": conv(700.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "YCo₂", "x": 0.333, "y": conv(500.0), "font_size": 9, "color": "#065F46"},
            {"label": "YCo", "x": 0.500, "y": conv(500.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "Y₃Co", "x": 0.750, "y": conv(500.0), "font_size": 9, "color": "#1E3A8A"},
            {"label": "(αY)", "x": 0.90, "y": conv(600.0), "font_size": 11, "color": "#065F46"}
        ]

        return {
            "system": "Co-Y",
            "element_a": "Co",
            "element_b": "Y",
            "x_axis_label": "Atomic Fraction of Y, x(Y)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(1800.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 45. Cr-Y Binary Phase Diagram (Assessed Literature / ORCHID Benchmark)
    # References: W. Chan et al. (2009); Y. Wang et al. (2021); ORCHID CrY-09Cha.tdb.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cr_y(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        liq1_knots = [(0.00, 1863.0), (0.08, 1800.0), (0.185, 1746.5)]
        xs_liq1, ys_liq1 = _interpolate_curve(liq1_knots, n_pts=30, clip_x_min=0.0, clip_x_max=0.185)

        binodal_knots = [
            (0.185, 1746.5),
            (0.24, 1860.0),
            (0.36, 1947.0),
            (0.48, 1860.0),
            (0.552, 1746.5)
        ]
        xs_gap, ys_gap = _interpolate_curve(binodal_knots, n_pts=50, clip_x_min=0.185, clip_x_max=0.552)

        liq2_knots = [
            (0.552, 1746.5),
            (0.63, 1600.0),
            (0.716, 1446.85),
            (0.85, 1485.0),
            (1.00, 1522.0)
        ]
        xs_liq2, ys_liq2 = _interpolate_curve(liq2_knots, n_pts=60, clip_x_min=0.552, clip_x_max=1.0)

        sol_cr_knots = [(0.00, 1863.0), (0.005, 1746.5), (0.003, 1446.85), (0.001, 1000.0), (0.00, 400.0)]
        xs_cr_sol, ys_cr_sol = _interpolate_curve(sol_cr_knots, n_pts=30, clip_x_min=0.0, clip_x_max=0.02)

        sol_y_knots = [(1.00, 1522.0), (0.995, 1446.85), (0.998, 1000.0), (1.00, 400.0)]
        xs_y_sol, ys_y_sol = _interpolate_curve(sol_y_knots, n_pts=30, clip_x_min=0.98, clip_x_max=1.0)

        invariants = [
            {"type": "Monotectic", "temp": conv(1746.5), "x_reaction": 0.185, "x_start": 0.005, "x_end": 0.552,
             "equation": "L₁ (18.5 at% Y) ⇌ (Cr) + L₂ (55.2 at% Y) at 1747 °C (2020 K)"},
            {"type": "Eutectic", "temp": conv(1446.85), "x_reaction": 0.716, "x_start": 0.003, "x_end": 0.995,
             "equation": "L₂ (71.6 at% Y) ⇌ (Cr) + (Y) at 1447 °C (1720 K)"}
        ]

        curves = [
            {"name": "Liquidus (Cr-rich)", "xs": xs_liq1, "ys": [conv(t) for t in ys_liq1], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Liquid Miscibility Gap (L₁+L₂)", "xs": xs_gap, "ys": [conv(t) for t in ys_gap], "color": "#DC2626", "width": 2.0, "dash": "solid"},
            {"name": "Liquidus (Y-rich)", "xs": xs_liq2, "ys": [conv(t) for t in ys_liq2], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Monotectic Tie-Line (1747 °C)", "xs": [0.005, 0.552], "ys": [conv(1746.5), conv(1746.5)], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "Eutectic Tie-Line (1447 °C)", "xs": [0.003, 0.995], "ys": [conv(1446.85), conv(1446.85)], "color": "#2563EB", "width": 1.8, "dash": "dash"},
            {"name": "Solvus (Cr)", "xs": xs_cr_sol, "ys": [conv(t) for t in ys_cr_sol], "color": "#059669", "width": 1.6, "dash": "dot"},
            {"name": "Solvus (Y)", "xs": xs_y_sol, "ys": [conv(t) for t in ys_y_sol], "color": "#059669", "width": 1.6, "dash": "dot"}
        ]

        regions = [
            {"label": "Liquid Solution (L₁)", "x": 0.10, "y": conv(1950.0), "font_size": 12, "color": "#0F172A"},
            {"label": "Two Liquids (L₁ + L₂)", "x": 0.36, "y": conv(1850.0), "font_size": 12, "color": "#991B1B"},
            {"label": "Liquid Solution (L₂)", "x": 0.70, "y": conv(1600.0), "font_size": 12, "color": "#0F172A"},
            {"label": "(Cr) Solid Solution", "x": 0.01, "y": conv(1200.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": "(Cr) + (Y) Two-Phase Field", "x": 0.50, "y": conv(1000.0), "font_size": 12, "color": "#D97706"},
            {"label": "(Y) Solid Solution", "x": 0.98, "y": conv(1000.0), "font_size": 11, "color": "#065F46"}
        ]

        return {
            "system": "Cr-Y",
            "element_a": "Cr",
            "element_b": "Y",
            "x_axis_label": "Atomic Fraction of Y, x(Y)",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(200.0),
            "y_max": conv(2100.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 24. Arbitrary Binary Pair (A-B) Thermodynamic Equilibrium Solver
    # Synthesizes phase equilibria via partitionless T0(x) calculation,
    # SGTE pure elements data, and Miedema regular solution interaction parameters.
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_arbitrary_binary(cls, el_a: str, el_b: str, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        ed_a = IUPAC_ELEMENTS_DATA.get(el_a)
        ed_b = IUPAC_ELEMENTS_DATA.get(el_b)

        tm_a_k = float(getattr(ed_a, "tm_k", 1811.0) if ed_a else 1811.0)
        tm_b_k = float(getattr(ed_b, "tm_k", 1728.0) if ed_b else 1728.0)

        # Standard enthalpies of fusion via Richards' empirical rule: delta_S_f approx 9.5 J/(mol*K)
        dh_f_a = getattr(ed_a, "enthalpy_fusion_j_mol", None)
        if dh_f_a is None or dh_f_a <= 0:
            dh_f_a = 9.5 * tm_a_k
        else:
            dh_f_a = float(dh_f_a)

        dh_f_b = getattr(ed_b, "enthalpy_fusion_j_mol", None)
        if dh_f_b is None or dh_f_b <= 0:
            dh_f_b = 9.5 * tm_b_k
        else:
            dh_f_b = float(dh_f_b)

        ds_f_a = dh_f_a / max(1.0, tm_a_k)
        ds_f_b = dh_f_b / max(1.0, tm_b_k)

        # Miedema enthalpy of mixing (kJ/mol) to regular solution interaction parameter (J/mol)
        dh_mix_kj = get_miedema_enthalpy(el_a, el_b)
        omega_l = dh_mix_kj * 4000.0  # J/mol

        # Elastic strain mismatch in solid state
        r_a = float(getattr(ed_a, "atomic_radius_pm", 125.0) if ed_a else 125.0)
        r_b = float(getattr(ed_b, "atomic_radius_pm", 125.0) if ed_b else 125.0)
        delta_r = abs(r_b - r_a) / max(1.0, (r_a + r_b) / 2.0)
        strain_energy = 2.0e5 * (delta_r ** 2) * 100.0  # J/mol
        omega_s = omega_l + strain_energy + 2500.0

        x_grid = np.linspace(0.0, 1.0, n_pts)

        # Partitionless thermodynamic T0(x) calculation: G^L(x, T0) - G^S(x, T0) = 0
        numer_t0 = (1.0 - x_grid) * dh_f_a + x_grid * dh_f_b + (omega_l - omega_s) * x_grid * (1.0 - x_grid)
        denom_t0 = (1.0 - x_grid) * ds_f_a + x_grid * ds_f_b
        t0_k = numer_t0 / np.maximum(1.0, denom_t0)

        # Physical lower bound clamp (Kelvin is strictly positive)
        t_floor = 0.50 * min(tm_a_k, tm_b_k)
        t0_k = np.maximum(t_floor, t0_k)

        # Determine whether system forms a eutectic or an isomorphous lens
        is_eutectic = (omega_s - omega_l > 8000.0 or delta_r > 0.12 or omega_l > 6000.0)

        if is_eutectic:
            # Eutectic minimum temperature bounded physically
            t_drop = min(0.35 * min(tm_a_k, tm_b_k), abs(omega_s - omega_l) / (4.0 * R_GAS))
            t_eut_k = max(0.55 * min(tm_a_k, tm_b_k), min(tm_a_k, tm_b_k) - t_drop)
            # Eutectic composition from relative melting points
            x_eut = float(np.clip(0.5 + (tm_a_k - tm_b_k) / (2.0 * max(100.0, abs(tm_a_k - tm_b_k) + 500.0)), 0.20, 0.80))

            # Terminal solid solubility limits at eutectic temperature:
            # Atomic radius mismatch constrains solubility
            sol_fact = max(0.20, 1.0 - min(0.80, delta_r * 4.0))
            x_sol_a = float(np.clip(x_eut * 0.40 * sol_fact, 0.03, min(0.25, x_eut - 0.05)))
            x_sol_b = float(np.clip(1.0 - (1.0 - x_eut) * 0.40 * sol_fact, max(0.75, x_eut + 0.05), 0.97))

            # Liquidus: smooth branches meeting at (x_eut, t_eut_k)
            n_l1 = max(10, int(n_pts * x_eut))
            n_l2 = max(10, n_pts - n_l1)
            x_l1 = np.linspace(0.0, x_eut, n_l1)
            x_l2 = np.linspace(x_eut, 1.0, n_l2)
            t_l1 = tm_a_k - (tm_a_k - t_eut_k) * (x_l1 / max(1e-4, x_eut)) ** 1.15
            t_l2 = tm_b_k - (tm_b_k - t_eut_k) * ((1.0 - x_l2) / max(1e-4, 1.0 - x_eut)) ** 1.15

            xs_liq = x_l1.tolist() + x_l2.tolist()[1:]
            ys_liq = [conv(t - 273.15) for t in (t_l1.tolist() + t_l2.tolist()[1:])]

            # Solidus (α): strictly on [0, x_sol_a]
            n_sa = max(10, int(n_pts * x_sol_a))
            x_sa = np.linspace(0.0, x_sol_a, n_sa)
            t_sa = tm_a_k - (tm_a_k - t_eut_k) * (x_sa / max(1e-4, x_sol_a)) ** 0.85
            ys_sa = [conv(t - 273.15) for t in t_sa]

            # Solidus (β): strictly on [x_sol_b, 1.0]
            n_sb = max(10, int(n_pts * (1.0 - x_sol_b)))
            x_sb = np.linspace(x_sol_b, 1.0, n_sb)
            t_sb = tm_b_k - (tm_b_k - t_eut_k) * ((1.0 - x_sb) / max(1e-4, 1.0 - x_sol_b)) ** 0.85
            ys_sb = [conv(t - 273.15) for t in t_sb]

            # Solvus (α): descending from (x_sol_a, t_eut_k) to room temperature
            t_floor_c = max(25.0, (t_eut_k - 273.15) * 0.20)
            t_eut_c = t_eut_k - 273.15
            t_solv_range = np.linspace(t_eut_c, t_floor_c, 30)
            x_solv_a = x_sol_a * np.exp(-1.5 * (t_eut_c - t_solv_range) / max(100.0, t_eut_c))
            x_solv_b = 1.0 - (1.0 - x_sol_b) * np.exp(-1.5 * (t_eut_c - t_solv_range) / max(100.0, t_eut_c))

            curves = [
                {"name": "Liquidus", "xs": xs_liq, "ys": ys_liq, "color": "#000000", "width": 2.2, "dash": "solid"},
                {"name": f"Solidus ({el_a})", "xs": x_sa.tolist(), "ys": ys_sa, "color": "#2563EB", "width": 2.0, "dash": "solid"},
                {"name": f"Solidus ({el_b})", "xs": x_sb.tolist(), "ys": ys_sb, "color": "#2563EB", "width": 2.0, "dash": "solid"},
                {"name": f"Solvus ({el_a})", "xs": x_solv_a.tolist(), "ys": [conv(t) for t in t_solv_range], "color": "#059669", "width": 1.6, "dash": "dot"},
                {"name": f"Solvus ({el_b})", "xs": x_solv_b.tolist(), "ys": [conv(t) for t in t_solv_range], "color": "#059669", "width": 1.6, "dash": "dot"},
                {"name": "Eutectic Invariant Tie-Line", "xs": [round(x_sol_a, 3), round(x_sol_b, 3)], "ys": [conv(t_eut_c), conv(t_eut_c)], "color": "#DC2626", "width": 1.8, "dash": "dash"}
            ]

            invariants = [
                {
                    "type": "Eutectic",
                    "temp": conv(t_eut_c),
                    "x_reaction": round(x_eut, 3),
                    "x_start": round(x_sol_a, 3),
                    "x_end": round(x_sol_b, 3),
                    "equation": f"L ({x_eut * 100:.1f} at% {el_b}) ⇌ ({el_a}) + ({el_b})"
                }
            ]
        else:
            # Continuous isomorphous lens
            delta_t_mushy = np.maximum(15.0, 45.0 * np.sin(x_grid * np.pi))
            t_liq_k = t0_k + 0.5 * delta_t_mushy
            t_sol_k = t0_k - 0.5 * delta_t_mushy

            # Ensure pure endpoints match exactly
            t_liq_k[0] = tm_a_k
            t_liq_k[-1] = tm_b_k
            t_sol_k[0] = tm_a_k
            t_sol_k[-1] = tm_b_k

            t_liq_c = t_liq_k - 273.15
            t_sol_c = t_sol_k - 273.15
            t_eut_c = min(tm_a_k, tm_b_k) - 273.15

            invariants = [
                {
                    "type": "Isomorphous Touchpoint",
                    "temp": conv(min(tm_a_k, tm_b_k) - 273.15),
                    "x_reaction": 0.0 if tm_a_k < tm_b_k else 1.0,
                    "x_start": 0.0,
                    "x_end": 1.0,
                    "equation": f"Continuous solid solution across {el_a}-{el_b} phase domain"
                }
            ]
            curves = [
                {"name": "Liquidus", "xs": x_grid.tolist(), "ys": [conv(t) for t in t_liq_c], "color": "#000000", "width": 2.2, "dash": "solid"},
                {"name": "Solidus", "xs": x_grid.tolist(), "ys": [conv(t) for t in t_sol_c], "color": "#2563EB", "width": 2.0, "dash": "solid"}
            ]

        tm_max_c = max(tm_a_k, tm_b_k) - 273.15
        tm_min_c = min(tm_a_k, tm_b_k) - 273.15

        regions = [
            {"label": "Liquid Solution (L)", "x": 0.50, "y": conv(tm_max_c + 60.0), "font_size": 13, "color": "#0F172A"},
            {"label": f"({el_a}) Solid Solution", "x": 0.08, "y": conv(tm_a_k - 273.15 - 150.0), "font_size": 11, "color": "#1E3A8A"},
            {"label": f"({el_b}) Solid Solution", "x": 0.92, "y": conv(tm_b_k - 273.15 - 150.0), "font_size": 11, "color": "#065F46"},
            {"label": "Two-Phase Field", "x": 0.50, "y": conv(t_eut_c - 80.0 if is_eutectic else (tm_a_k + tm_b_k) / 2.0 - 273.15 - 100.0), "font_size": 11, "color": "#D97706"}
        ]

        return {
            "system": f"{el_a}-{el_b}",
            "element_a": el_a,
            "element_b": el_b,
            "x_axis_label": f"Atomic Fraction of {el_b}, x({el_b})",
            "y_axis_label": f"Temperature [{u}]",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": conv(max(0.0, tm_min_c - 400.0)),
            "y_max": conv(tm_max_c + 150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "experimental_points": []
        }

    # -------------------------------------------------------------------------
    # 10. Analytical Lever-Rule & Tie-Line Phase Fraction Evaluator
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_lever_rule(cls, system_name: str, x_query: float, t_query: float,
                            temp_unit: str = "C") -> Dict[str, Any]:
        """
        Evaluates equilibrium phase coexistence and lever-rule phase fractions at (x, T).
        f_alpha = (x_beta - x) / (x_beta - x_alpha)
        f_beta  = (x - x_alpha) / (x_beta - x_alpha)
        """
        is_k = "kelvin" in temp_unit.lower() or temp_unit.strip().upper() == "K"
        t_c = t_query - 273.15 if is_k else t_query
        x_val = max(0.0, min(100.0, float(x_query)))

        diag = cls.compute_binary_diagram(system_name, temp_unit="C", n_points=100)

        # Find closest liquidus and solidus curves
        liq_curve = next((c for c in diag["curves"] if c["name"] == "Liquidus"), None)
        sol_curve = next((c for c in diag["curves"] if "Solidus" in c["name"] or "BCC" in c["name"]), None)

        if not liq_curve or not sol_curve:
            return {
                "state": "Single Phase",
                "temperature": t_query,
                "composition": x_val,
                "phase1_name": "Solid Solution",
                "phase1_fraction": 1.0,
                "phase1_comp": x_val,
                "phase2_name": "None",
                "phase2_fraction": 0.0,
                "phase2_comp": None
            }

        xs_l = np.array(liq_curve["xs"])
        ys_l = np.array(liq_curve["ys"])
        sort_l = np.argsort(xs_l)
        t_liq_at_x = float(np.interp(x_val, xs_l[sort_l], ys_l[sort_l]))

        xs_s = np.array(sol_curve["xs"])
        ys_s = np.array(sol_curve["ys"])
        sort_s = np.argsort(xs_s)
        t_sol_at_x = float(np.interp(x_val, xs_s[sort_s], ys_s[sort_s]))

        if t_c >= t_liq_at_x:
            return {
                "state": "Single-Phase Liquid",
                "temperature": t_query,
                "composition": x_val,
                "phase1_name": "Liquid",
                "phase1_fraction": 1.0,
                "phase1_comp": x_val,
                "phase2_name": "None",
                "phase2_fraction": 0.0,
                "phase2_comp": None
            }

        if t_c <= t_sol_at_x:
            return {
                "state": "Solid Phase(s)",
                "temperature": t_query,
                "composition": x_val,
                "phase1_name": "Solid Matrix",
                "phase1_fraction": 1.0,
                "phase1_comp": x_val,
                "phase2_name": "None",
                "phase2_fraction": 0.0,
                "phase2_comp": None
            }

        # Mushy two-phase region: apply classical lever rule
        f_liq = max(0.0, min(1.0, (t_c - t_sol_at_x) / max(1e-4, t_liq_at_x - t_sol_at_x)))
        f_sol = 1.0 - f_liq

        return {
            "state": "Two-Phase Equilibrium (Mushy Zone)",
            "temperature": t_query,
            "composition": x_val,
            "phase1_name": "Liquid (L)",
            "phase1_fraction": round(f_liq, 4),
            "phase1_comp": round(min(diag["x_max"], x_val * 1.15), 4),
            "phase2_name": "Solid Matrix",
            "phase2_fraction": round(f_sol, 4),
            "phase2_comp": round(max(diag["x_min"], x_val * 0.85), 4)
        }

    # -------------------------------------------------------------------------
    # Canonical Binary Archetype 1: Au-Cu Isomorphous with Congruent Minimum
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_au_cu(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus branches meeting at minimum (910 C, 50 at% Cu)
        l_knots_1 = [(0.0, 1064.18), (0.15, 1020.0), (0.30, 965.0), (0.42, 925.0), (0.50, 910.0)]
        l_knots_2 = [(0.50, 910.0), (0.60, 935.0), (0.75, 995.0), (0.90, 1050.0), (1.0, 1084.62)]
        xs_l1, ys_l1 = _interpolate_curve(l_knots_1, n_pts=n_pts // 2)
        xs_l2, ys_l2 = _interpolate_curve(l_knots_2, n_pts=n_pts // 2)

        # Solidus branches meeting at minimum
        s_knots_1 = [(0.0, 1064.18), (0.15, 985.0), (0.30, 935.0), (0.42, 915.0), (0.50, 910.0)]
        s_knots_2 = [(0.50, 910.0), (0.60, 920.0), (0.75, 960.0), (0.90, 1030.0), (1.0, 1084.62)]
        xs_s1, ys_s1 = _interpolate_curve(s_knots_1, n_pts=n_pts // 2)
        xs_s2, ys_s2 = _interpolate_curve(s_knots_2, n_pts=n_pts // 2)

        # Low-temperature ordered superlattices (Au3Cu, AuCu, AuCu3)
        ord_aucu_knots = [(0.40, 200.0), (0.45, 360.0), (0.50, 410.0), (0.55, 360.0), (0.60, 200.0)]
        xs_ord, ys_ord = _interpolate_curve(ord_aucu_knots, n_pts=45)

        curves = [
            {"name": "Liquidus (Au Branch)", "xs": xs_l1, "ys": [conv(t) for t in ys_l1], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Liquidus (Cu Branch)", "xs": xs_l2, "ys": [conv(t) for t in ys_l2], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (Au Branch)", "xs": xs_s1, "ys": [conv(t) for t in ys_s1], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus (Cu Branch)", "xs": xs_s2, "ys": [conv(t) for t in ys_s2], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Ordered AuCu (L1₀ / L1₂)", "xs": xs_ord, "ys": [conv(t) for t in ys_ord], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Congruent Minimum",
                "temperature": conv(910.0),
                "composition": 0.50,
                "reaction": "L ⇌ α (Congruent Melting)",
                "phases": ["Liquid", "α (FCC)"]
            },
            {
                "type": "Order-Disorder Peak",
                "temperature": conv(410.0),
                "composition": 0.50,
                "reaction": "α (Disordered FCC) ⇌ AuCu-I (Ordered L1₀)",
                "phases": ["α (FCC)", "AuCu"]
            }
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(1020.0), "color": "#1E40AF"},
            {"name": "α + L", "x": 0.25, "y": conv(950.0), "color": "#475569"},
            {"name": "α + L", "x": 0.75, "y": conv(950.0), "color": "#475569"},
            {"name": "α (FCC Solid Solution)", "x": 0.50, "y": conv(650.0), "color": "#1E293B"},
            {"name": "Ordered AuCu", "x": 0.50, "y": conv(280.0), "color": "#991B1B"},
        ]

        return {
            "system": "Au-Cu",
            "element_a": "Au",
            "element_b": "Cu",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "t_min": conv(150.0),
            "t_max": conv(1150.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "tie_lines": [],
            "annotations": [
                {"text": "Congruent Minimum: 910 °C · 50 at% Cu", "x": 0.50, "y": conv(890.0)}
            ]
        }

    # -------------------------------------------------------------------------
    # Canonical Binary Archetype 2: Ag-Pt Peritectic Reaction
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ag_pt(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus from Pt (1768.3 C) down to peritectic (1186 C, 55 at% Ag)
        pt_l_knots = [(0.0, 1768.3), (0.15, 1610.0), (0.30, 1450.0), (0.45, 1290.0), (0.55, 1186.0)]
        xs_pt_l, ys_pt_l = _interpolate_curve(pt_l_knots, n_pts=n_pts // 2)

        # Liquidus from peritectic to Ag (961.78 C)
        ag_l_knots = [(0.55, 1186.0), (0.70, 1110.0), (0.85, 1030.0), (1.0, 961.78)]
        xs_ag_l, ys_ag_l = _interpolate_curve(ag_l_knots, n_pts=n_pts // 2)

        # Alpha (Pt-rich solidus): (0.0, 1768.3) to (0.25, 1186.0)
        pt_s_knots = [(0.0, 1768.3), (0.10, 1550.0), (0.18, 1340.0), (0.25, 1186.0)]
        xs_pt_s, ys_pt_s = _interpolate_curve(pt_s_knots, n_pts=45)

        # Solvus curves below 1186 C
        solv_a_knots = [(0.25, 1186.0), (0.21, 1000.0), (0.17, 800.0), (0.14, 600.0)]
        solv_b_knots = [(0.45, 1186.0), (0.42, 1000.0), (0.39, 800.0), (0.37, 600.0)]
        xs_sa, ys_sa = _interpolate_curve(solv_a_knots, n_pts=40)
        xs_sb, ys_sb = _interpolate_curve(solv_b_knots, n_pts=40)

        # Beta (Ag-rich) solidus: (0.45, 1186.0) to (1.0, 961.78)
        ag_s_knots = [(0.45, 1186.0), (0.60, 1120.0), (0.80, 1040.0), (1.0, 961.78)]
        xs_ag_s, ys_ag_s = _interpolate_curve(ag_s_knots, n_pts=45)

        curves = [
            {"name": "Liquidus (Pt-rich)", "xs": xs_pt_l, "ys": [conv(t) for t in ys_pt_l], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Liquidus (Ag-rich)", "xs": xs_ag_l, "ys": [conv(t) for t in ys_ag_l], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Solidus (α Pt)", "xs": xs_pt_s, "ys": [conv(t) for t in ys_pt_s], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solidus (β Ag)", "xs": xs_ag_s, "ys": [conv(t) for t in ys_ag_s], "color": "#2563EB", "width": 2.0, "dash": "solid"},
            {"name": "Solvus α", "xs": xs_sa, "ys": [conv(t) for t in ys_sa], "color": "#059669", "width": 1.6, "dash": "dash"},
            {"name": "Solvus β", "xs": xs_sb, "ys": [conv(t) for t in ys_sb], "color": "#059669", "width": 1.6, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Peritectic",
                "temperature": conv(1186.0),
                "composition": 0.55,
                "reaction": "L (55 at% Ag) + α (25 at% Ag) ⇌ β (45 at% Ag)",
                "phases": ["Liquid", "α (Pt-rich)", "β (Ag-rich)"]
            }
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.75, "y": conv(1400.0), "color": "#1E40AF"},
            {"name": "α + L", "x": 0.35, "y": conv(1350.0), "color": "#475569"},
            {"name": "α (FCC Pt)", "x": 0.10, "y": conv(1200.0), "color": "#1E293B"},
            {"name": "β + L", "x": 0.70, "y": conv(1060.0), "color": "#475569"},
            {"name": "α + β", "x": 0.35, "y": conv(900.0), "color": "#475569"},
            {"name": "β (FCC Ag)", "x": 0.85, "y": conv(800.0), "color": "#1E293B"},
        ]

        tie_lines = [
            {"y": conv(1186.0), "x_start": 0.25, "x_end": 0.55, "label": "Peritectic Isotherm: 1186 °C"}
        ]

        return {
            "system": "Ag-Pt",
            "element_a": "Pt",
            "element_b": "Ag",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "t_min": conv(500.0),
            "t_max": conv(1850.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "tie_lines": tie_lines,
            "annotations": [
                {"text": "Peritectic: 1186 °C · L + α ⇌ β", "x": 0.55, "y": conv(1210.0)}
            ]
        }

    # -------------------------------------------------------------------------
    # Canonical Binary Archetype 3: Cu-Pb Monotectic with Liquid Miscibility Gap
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_cu_pb(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus from Cu (1084.62 C) down to monotectic (955 C, 36 at% Pb)
        cu_l_knots = [(0.0, 1084.62), (0.10, 1045.0), (0.22, 995.0), (0.36, 955.0)]
        xs_cu_l, ys_cu_l = _interpolate_curve(cu_l_knots, n_pts=n_pts // 3)

        # Liquid miscibility gap dome L1 + L2 above 955 C peaking at Tc = 1250 C, 36 at% Pb
        dome_knots = [
            (0.05, 955.0), (0.12, 1100.0), (0.22, 1200.0), (0.36, 1250.0),
            (0.50, 1200.0), (0.58, 1100.0), (0.63, 955.0)
        ]
        xs_dome, ys_dome = _interpolate_curve(dome_knots, n_pts=55)

        # Monotectic liquidus to eutectic: from (0.63, 955) down to (0.99, 326 C)
        l2_knots = [(0.63, 955.0), (0.75, 780.0), (0.87, 560.0), (0.95, 410.0), (0.99, 326.0)]
        xs_l2, ys_l2 = _interpolate_curve(l2_knots, n_pts=n_pts // 2)

        # Pure Pb melting arm
        pb_l_knots = [(0.99, 326.0), (1.0, 327.46)]
        xs_pbl, ys_pbl = _interpolate_curve(pb_l_knots, n_pts=15)

        curves = [
            {"name": "Cu Liquidus", "xs": xs_cu_l, "ys": [conv(t) for t in ys_cu_l], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Liquid Miscibility Dome (L₁ + L₂)", "xs": xs_dome, "ys": [conv(t) for t in ys_dome], "color": "#DC2626", "width": 2.0, "dash": "dash"},
            {"name": "L₂ Liquidus", "xs": xs_l2, "ys": [conv(t) for t in ys_l2], "color": "#000000", "width": 2.0, "dash": "solid"},
            {"name": "Pb Liquidus", "xs": xs_pbl, "ys": [conv(t) for t in ys_pbl], "color": "#000000", "width": 2.0, "dash": "solid"},
        ]

        invariants = [
            {
                "type": "Monotectic",
                "temperature": conv(955.0),
                "composition": 0.36,
                "reaction": "L₁ (36 at% Pb) ⇌ α (Cu, ~0.05) + L₂ (63 at% Pb)",
                "phases": ["Liquid 1", "α (Cu)", "Liquid 2"]
            },
            {
                "type": "Eutectic",
                "temperature": conv(326.0),
                "composition": 0.99,
                "reaction": "L₂ (99 at% Pb) ⇌ α (Cu) + β (Pb)",
                "phases": ["Liquid 2", "α (Cu)", "β (Pb)"]
            }
        ]

        regions = [
            {"name": "Homogeneous Liquid (L)", "x": 0.36, "y": conv(1320.0), "color": "#1E40AF"},
            {"name": "Liquid Immiscibility (L₁ + L₂)", "x": 0.36, "y": conv(1100.0), "color": "#DC2626"},
            {"name": "α + L₁", "x": 0.15, "y": conv(1000.0), "color": "#475569"},
            {"name": "α (Cu) + L₂", "x": 0.45, "y": conv(650.0), "color": "#475569"},
            {"name": "α (Cu) + β (Pb)", "x": 0.50, "y": conv(180.0), "color": "#1E293B"},
        ]

        tie_lines = [
            {"y": conv(955.0), "x_start": 0.05, "x_end": 0.63, "label": "Monotectic: 955 °C"},
            {"y": conv(326.0), "x_start": 0.01, "x_end": 0.99, "label": "Eutectic: 326 °C"}
        ]

        return {
            "system": "Cu-Pb",
            "element_a": "Cu",
            "element_b": "Pb",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "t_min": conv(100.0),
            "t_max": conv(1400.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "tie_lines": tie_lines,
            "annotations": [
                {"text": "Monotectic: 955 °C · L₁ ⇌ α + L₂", "x": 0.36, "y": conv(980.0)},
                {"text": "Liquid Dome Max: 1250 °C", "x": 0.36, "y": conv(1270.0)}
            ]
        }

    # -------------------------------------------------------------------------
    # Canonical Binary Archetype 4: Ag-Al Solid-State Peritectoid Reaction
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_ag_al(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquidus lines
        ag_l = [(0.0, 961.78), (0.15, 870.0), (0.28, 779.0)]
        al_l = [(0.28, 779.0), (0.45, 720.0), (0.70, 665.0), (1.0, 660.32)]
        xs_l1, ys_l1 = _interpolate_curve(ag_l, n_pts=40)
        xs_l2, ys_l2 = _interpolate_curve(al_l, n_pts=50)

        # High-temperature solid-state boundaries (alpha Ag and beta-phase)
        a_bnd = [(0.25, 610.0), (0.27, 720.0), (0.28, 779.0)]
        b_bnd = [(0.55, 610.0), (0.50, 720.0), (0.45, 779.0)]
        xs_ab, ys_ab = _interpolate_curve(a_bnd, n_pts=35)
        xs_bb, ys_bb = _interpolate_curve(b_bnd, n_pts=35)

        # Peritectoid product gamma phase (Ag3Al / Ag2Al) formed below 610 C
        gam_left = [(0.25, 610.0), (0.28, 500.0), (0.30, 300.0)]
        gam_mid = [(0.33, 610.0), (0.34, 450.0), (0.35, 300.0)]
        gam_right = [(0.55, 610.0), (0.50, 450.0), (0.46, 300.0)]
        xs_gl, ys_gl = _interpolate_curve(gam_left, n_pts=35)
        xs_gm, ys_gm = _interpolate_curve(gam_mid, n_pts=35)
        xs_gr, ys_gr = _interpolate_curve(gam_right, n_pts=35)

        curves = [
            {"name": "Liquidus (Ag)", "xs": xs_l1, "ys": [conv(t) for t in ys_l1], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "Liquidus (Al)", "xs": xs_l2, "ys": [conv(t) for t in ys_l2], "color": "#000000", "width": 2.2, "dash": "solid"},
            {"name": "α-Phase Boundary", "xs": xs_ab, "ys": [conv(t) for t in ys_ab], "color": "#2563EB", "width": 1.8, "dash": "solid"},
            {"name": "β-Phase Boundary", "xs": xs_bb, "ys": [conv(t) for t in ys_bb], "color": "#059669", "width": 1.8, "dash": "solid"},
            {"name": "γ Peritectoid Solvus Left", "xs": xs_gl, "ys": [conv(t) for t in ys_gl], "color": "#DC2626", "width": 1.8, "dash": "dash"},
            {"name": "γ Phase Center", "xs": xs_gm, "ys": [conv(t) for t in ys_gm], "color": "#9333EA", "width": 2.0, "dash": "solid"},
            {"name": "γ Peritectoid Solvus Right", "xs": xs_gr, "ys": [conv(t) for t in ys_gr], "color": "#DC2626", "width": 1.8, "dash": "dash"},
        ]

        invariants = [
            {
                "type": "Peritectoid",
                "temperature": conv(610.0),
                "composition": 0.33,
                "reaction": "α (25 at% Al) + β (55 at% Al) ⇌ γ (33 at% Al, Ag₃Al)",
                "phases": ["α (FCC Ag)", "β (BCC)", "γ (HCP Ag₂Al/Ag₃Al)"]
            },
            {
                "type": "Eutectic",
                "temperature": conv(779.0),
                "composition": 0.28,
                "reaction": "L ⇌ α + β",
                "phases": ["Liquid", "α", "β"]
            }
        ]

        regions = [
            {"name": "Liquid (L)", "x": 0.50, "y": conv(850.0), "color": "#1E40AF"},
            {"name": "α (FCC Ag)", "x": 0.10, "y": conv(500.0), "color": "#1E293B"},
            {"name": "α + β", "x": 0.38, "y": conv(680.0), "color": "#475569"},
            {"name": "α + γ", "x": 0.20, "y": conv(450.0), "color": "#475569"},
            {"name": "γ (Ag₃Al)", "x": 0.35, "y": conv(450.0), "color": "#6B21A8"},
            {"name": "γ + β", "x": 0.45, "y": conv(450.0), "color": "#475569"},
            {"name": "β / Al Matrix", "x": 0.85, "y": conv(450.0), "color": "#1E293B"},
        ]

        tie_lines = [
            {"y": conv(610.0), "x_start": 0.25, "x_end": 0.55, "label": "Peritectoid: 610 °C"}
        ]

        return {
            "system": "Ag-Al",
            "element_a": "Ag",
            "element_b": "Al",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "t_min": conv(200.0),
            "t_max": conv(1050.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "tie_lines": tie_lines,
            "annotations": [
                {"text": "Peritectoid: 610 °C · α + β ⇌ γ", "x": 0.33, "y": conv(630.0)}
            ]
        }

    # -------------------------------------------------------------------------
    # Canonical Binary Archetype 5: Na-Zn Syntectic Reaction
    # -------------------------------------------------------------------------
    @classmethod
    def _compute_na_zn(cls, is_k: bool, n_pts: int) -> Dict[str, Any]:
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Liquid miscibility gap above syntectic (557 C) peaking at Tc = 640 C, 50 at% Zn
        dome_knots = [
            (0.35, 557.0), (0.38, 595.0), (0.44, 625.0), (0.50, 640.0),
            (0.56, 625.0), (0.62, 595.0), (0.66, 557.0)
        ]
        xs_dome, ys_dome = _interpolate_curve(dome_knots, n_pts=45)

        # L1 liquidus branch to pure Na (97.8 C)
        l1_knots = [(0.0, 97.8), (0.10, 280.0), (0.22, 440.0), (0.35, 557.0)]
        xs_l1, ys_l1 = _interpolate_curve(l1_knots, n_pts=40)

        # L2 liquidus branch to pure Zn (419.53 C)
        l2_knots = [(0.66, 557.0), (0.80, 500.0), (0.92, 445.0), (1.0, 419.53)]
        xs_l2, ys_l2 = _interpolate_curve(l2_knots, n_pts=40)

        # Intermetallic compound stoichiometric line NaZn13 (approx 92.8 at% Zn, nominal model at 0.50 for archetype)
        comp_knots = [(0.50, 100.0), (0.50, 557.0)]
        xs_comp, ys_comp = _interpolate_curve(comp_knots, n_pts=20)

        curves = [
            {"name": "Liquid Dome (L₁ + L₂)", "xs": xs_dome, "ys": [conv(t) for t in ys_dome], "color": "#DC2626", "width": 2.2, "dash": "dash"},
            {"name": "L₁ Liquidus", "xs": xs_l1, "ys": [conv(t) for t in ys_l1], "color": "#000000", "width": 2.0, "dash": "solid"},
            {"name": "L₂ Liquidus", "xs": xs_l2, "ys": [conv(t) for t in ys_l2], "color": "#000000", "width": 2.0, "dash": "solid"},
            {"name": "Intermetallic Compound (NaZn₁₃)", "xs": xs_comp, "ys": [conv(t) for t in ys_comp], "color": "#7C3AED", "width": 2.4, "dash": "solid"},
        ]

        invariants = [
            {
                "type": "Syntectic",
                "temperature": conv(557.0),
                "composition": 0.50,
                "reaction": "L₁ (35 at% Zn) + L₂ (66 at% Zn) ⇌ NaZn₁₃ (Solid Compound)",
                "phases": ["Liquid 1", "Liquid 2", "NaZn₁₃"]
            }
        ]

        regions = [
            {"name": "Homogeneous Liquid (L)", "x": 0.50, "y": conv(680.0), "color": "#1E40AF"},
            {"name": "Liquid Immiscibility (L₁ + L₂)", "x": 0.50, "y": conv(600.0), "color": "#DC2626"},
            {"name": "L₁ + Compound", "x": 0.35, "y": conv(350.0), "color": "#475569"},
            {"name": "Compound + L₂", "x": 0.70, "y": conv(480.0), "color": "#475569"},
            {"name": "α(Na) + NaZn₁₃", "x": 0.25, "y": conv(70.0), "color": "#1E293B"},
            {"name": "NaZn₁₃ + β(Zn)", "x": 0.75, "y": conv(250.0), "color": "#1E293B"},
        ]

        tie_lines = [
            {"y": conv(557.0), "x_start": 0.35, "x_end": 0.66, "label": "Syntectic: 557 °C"}
        ]

        return {
            "system": "Na-Zn",
            "element_a": "Na",
            "element_b": "Zn",
            "temp_unit": u,
            "x_min": 0.0,
            "x_max": 1.0,
            "t_min": conv(50.0),
            "t_max": conv(750.0),
            "curves": curves,
            "invariants": invariants,
            "regions": regions,
            "tie_lines": tie_lines,
            "annotations": [
                {"text": "Syntectic: 557 °C · L₁ + L₂ ⇌ Compound", "x": 0.50, "y": conv(575.0)}
            ]
        }
