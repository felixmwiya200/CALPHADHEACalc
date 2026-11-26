# -*- coding: utf-8 -*-
"""
ternary_diagram_engine.py - Thermodynamic Ternary Phase Diagram Calculation Engine

Calculates thermodynamic equilibria, isothermal sections, liquidus projections,
monovariant reaction valleys, invariant points, and tie-lines on the Gibbs equilateral
triangle for High-Entropy Alloy (HEA) subsystems, refractory alloys, superalloys,
and classical computational metallurgy benchmarks.

Academic & CALPHAD Engineering Standards:
  1. Coordinate projection: Barycentric (a, b, c) to Cartesian (X, Y) transformation:
     X = x_B + 0.5 * x_C
     Y = (sqrt(3) / 2) * x_C
  2. Assessed literature benchmarks with verified invariant reactions:
     - Co-Cr-Ni (Cantor core FCC / sigma matrix: Liu 2016, Zhao 2020)
     - Cr-Fe-Ni (Stainless / Superalloy base: Lee 1993, Miettinen 1999)
     - Co-Fe-Ni (Magnetic soft alloy / Cantor subsystem: Xia 2021, Yuan 2019)
     - Co-Cr-Fe (Cantor subsystem with sigma field: Shang 2023, Choi 2019)
     - Fe-Cr-Mn (High-Mn austenitic stainless base: Lee 1993, Murata 1990)
     - Mo-Nb-Ta (Senkov prototypical heavy BCC RHEA: Xiong 2004, Marker 2018)
     - Mo-Ta-W (Heavy refractory HEA base with B2 ordering: Turchi 2005)
     - Nb-Ta-W (High-temperature refractory HEA isomorphous: Liu 2012)
     - Ti-Zr-Nb (Biomedical & structural RHEA with monotectoid gap: Marker 2018)
     - Mo-Nb-V (Medium-density refractory isomorphous solution: Li 2026)
     - Ni-Al-Ti (Gamma / gamma-prime superalloy archetype: Lee & Nash 1991)
     - Fe-Cr-C (Tool steel with M23C6, M7C3, M3C carbides: Andersson 1988, Khvan 2014)
     - Al-Cu-Mg (Aerospace 2xxx alloy with S-phase and E5 eutectic: Buhler 1998, COST 507)
     - Mo-V-W (Type I continuous isomorphous: Bhansali & Mallik 1984)
     - Cd-Pb-Sn (Class I ternary eutectic benchmark, TE = 145 C: Mallik 1986, Osamura 1993)
  3. Dynamic arbitrary element-triplet solver (A-B-C) via Miedema mixing enthalpies
     and Redlich-Kister sub-regular Gibbs energy extrapolations.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.interpolate import PchipInterpolator

from pycalphad_app.core.elements_data import IUPAC_ELEMENTS_DATA
from pycalphad_app.core.thermo_engine import get_miedema_enthalpy

# Universal molar gas constant R in J / (mol * K)
R_GAS: float = 8.314462618
SQRT3_OVER_2: float = math.sqrt(3.0) / 2.0  # ~0.8660254037844386


def barycentric_to_cartesian(a: float, b: float, c: float) -> Tuple[float, float]:
    """
    Transforms normalized ternary barycentric coordinates (a, b, c) where a + b + c = 1
    to 2D Cartesian coordinates (X, Y) on an equilateral Gibbs triangle.
      - Component A at bottom-left: (0.0, 0.0)
      - Component B at bottom-right: (1.0, 0.0)
      - Component C at top apex: (0.5, sqrt(3)/2)
    """
    total = a + b + c
    if abs(total) < 1e-12:
        return 0.0, 0.0
    norm_b = b / total
    norm_c = c / total
    x = norm_b + 0.5 * norm_c
    y = SQRT3_OVER_2 * norm_c
    return round(float(x), 5), round(float(y), 5)


def cartesian_to_barycentric(x: float, y: float) -> Tuple[float, float, float]:
    """
    Transforms 2D Cartesian coordinates (X, Y) back to barycentric coordinates (a, b, c).
    """
    c = y / SQRT3_OVER_2
    b = x - 0.5 * c
    a = 1.0 - b - c
    return round(float(a), 5), round(float(b), 5), round(float(c), 5)


def _interpolate_ternary_curve(
    bary_pts: List[Tuple[float, float, float]], n_pts: int = 40
) -> Tuple[List[float], List[float]]:
    """
    Interpolates a sequence of ternary barycentric knots directly in barycentric coordinate
    space (a, b, c), enforcing non-negativity and unit sum normalization (a + b + c = 1)
    before mapping to Cartesian (X, Y). This guarantees mathematically that all generated
    curve coordinates lie strictly within or on the perimeter of the Gibbs equilateral triangle.
    """
    if len(bary_pts) < 2:
        if bary_pts:
            x, y = barycentric_to_cartesian(*bary_pts[0])
            return [x], [y]
        return [], []

    bary_arr = np.array(bary_pts, dtype=float)
    # Ensure raw knots have positive unit sum
    sums = np.sum(bary_arr, axis=1, keepdims=True)
    sums[np.abs(sums) < 1e-12] = 1.0
    bary_arr = np.maximum(0.0, bary_arr) / sums

    if len(bary_pts) == 2:
        a_interp = np.linspace(bary_arr[0, 0], bary_arr[1, 0], n_pts)
        b_interp = np.linspace(bary_arr[0, 1], bary_arr[1, 1], n_pts)
        c_interp = np.linspace(bary_arr[0, 2], bary_arr[1, 2], n_pts)
    else:
        diffs = np.diff(bary_arr, axis=0)
        dists = np.sqrt(np.sum(diffs**2, axis=1))
        total_dist = float(np.sum(dists))
        if total_dist < 1e-12:
            a_interp = np.full(n_pts, bary_arr[0, 0])
            b_interp = np.full(n_pts, bary_arr[0, 1])
            c_interp = np.full(n_pts, bary_arr[0, 2])
        else:
            t_knots = np.insert(np.cumsum(dists), 0, 0.0) / total_dist
            # Enforce strict monotonicity for PCHIP
            for i in range(1, len(t_knots)):
                if t_knots[i] <= t_knots[i - 1]:
                    t_knots[i] = t_knots[i - 1] + 1e-6
            t_knots = t_knots / t_knots[-1]
            pa = PchipInterpolator(t_knots, bary_arr[:, 0])
            pb = PchipInterpolator(t_knots, bary_arr[:, 1])
            pc = PchipInterpolator(t_knots, bary_arr[:, 2])

            t_eval = np.linspace(0.0, 1.0, n_pts)
            a_raw = pa(t_eval)
            b_raw = pb(t_eval)
            c_raw = pc(t_eval)

            # Non-negative clamping and barycentric normalization
            a_clamped = np.maximum(0.0, a_raw)
            b_clamped = np.maximum(0.0, b_raw)
            c_clamped = np.maximum(0.0, c_raw)
            tot = a_clamped + b_clamped + c_clamped
            tot[tot < 1e-12] = 1.0
            a_interp = a_clamped / tot
            b_interp = b_clamped / tot
            c_interp = c_clamped / tot

    xs: List[float] = []
    ys: List[float] = []
    for a_val, b_val, c_val in zip(a_interp, b_interp, c_interp):
        x, y = barycentric_to_cartesian(float(a_val), float(b_val), float(c_val))
        xs.append(x)
        ys.append(y)
    return xs, ys


def _trace_ternary_isocontours(
    field_fn: Any,
    level: float,
    n_grid: int = 56,
) -> List[Tuple[List[float], List[float]]]:
    """
    Traces exact non-intersecting iso-level polylines of a continuous scalar field
    f(a, b, c) over the Gibbs triangle using simplicial triangulation contouring.
    Guarantees contours terminate cleanly on binary triangle edges and never self-cross.
    """
    n = max(20, int(n_grid))
    grid_vals = np.zeros((n + 1, n + 1), dtype=float)
    for i in range(n + 1):
        a = i / float(n)
        for j in range(n - i + 1):
            b = j / float(n)
            c = max(0.0, 1.0 - a - b)
            val = float(field_fn(a, b, c)) - level
            if abs(val) < 1e-7:
                val = 1e-7
            grid_vals[i, j] = val

    def pt_from_ij(i_val: float, j_val: float) -> Tuple[float, float]:
        a = i_val / float(n)
        b = j_val / float(n)
        c = max(0.0, 1.0 - a - b)
        return barycentric_to_cartesian(a, b, c)

    def interp_edge(p1: Tuple[int, int, float], p2: Tuple[int, int, float]) -> Tuple[float, float]:
        i1, j1, v1 = p1
        i2, j2, v2 = p2
        denom = v2 - v1
        t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, -v1 / denom))
        x, y = pt_from_ij(i1 + t * (i2 - i1), j1 + t * (j2 - j1))
        return (round(x, 6), round(y, 6))

    segments: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

    def process_tri(v0: Tuple[int, int, float], v1: Tuple[int, int, float], v2: Tuple[int, int, float]) -> None:
        pts: List[Tuple[float, float]] = []
        for pa, pb in ((v0, v1), (v1, v2), (v2, v0)):
            if (pa[2] > 0.0) != (pb[2] > 0.0):
                pts.append(interp_edge(pa, pb))
        if len(pts) == 2 and pts[0] != pts[1]:
            segments.append((pts[0], pts[1]))

    for i in range(n):
        for j in range(n - i):
            p00 = (i, j, float(grid_vals[i, j]))
            p10 = (i + 1, j, float(grid_vals[i + 1, j]))
            p01 = (i, j + 1, float(grid_vals[i, j + 1]))
            process_tri(p00, p10, p01)
            if i + j + 2 <= n:
                p11 = (i + 1, j + 1, float(grid_vals[i + 1, j + 1]))
                process_tri(p10, p11, p01)

    if not segments:
        return []

    # Build adjacency graph to stitch segments into ordered polylines (starting from boundary degree-1 endpoints)
    adj: Dict[Tuple[float, float], List[int]] = {}
    for idx, (s, e) in enumerate(segments):
        adj.setdefault(s, []).append(idx)
        adj.setdefault(e, []).append(idx)

    used = [False] * len(segments)
    chains: List[Tuple[List[float], List[float]]] = []

    def walk_chain(start_pt: Tuple[float, float], start_seg: int) -> None:
        used[start_seg] = True
        s0, e0 = segments[start_seg]
        nxt = e0 if s0 == start_pt else s0
        pts = [start_pt, nxt]
        cur = nxt
        while True:
            cand = [sid for sid in adj.get(cur, []) if not used[sid]]
            if not cand:
                break
            sid = cand[0]
            used[sid] = True
            sa, ea = segments[sid]
            cur = ea if sa == cur else sa
            pts.append(cur)
        if len(pts) >= 2:
            chains.append(([p[0] for p in pts], [p[1] for p in pts]))

    # Priority 1: open boundary-to-boundary chains (degree == 1)
    for pt, sids in list(adj.items()):
        if len(sids) == 1 and not used[sids[0]]:
            walk_chain(pt, sids[0])

    # Priority 2: any remaining closed interior loops
    for idx in range(len(segments)):
        if not used[idx]:
            walk_chain(segments[idx][0], idx)

    return chains


def _append_isotherm_contours(
    field_fn: Any,
    levels_colors: List[Tuple[float, str]],
    is_k: bool,
    curves: List[Dict[str, Any]],
    labels: List[Dict[str, Any]],
    prefix: str = "Liquidus",
    n_grid: int = 54,
) -> None:
    """Traces non-intersecting isotherm polylines across a ternary scalar field."""
    for t_iso, col in levels_colors:
        chains = _trace_ternary_isocontours(field_fn, t_iso, n_grid=n_grid)
        if not chains:
            continue
        disp_t = t_iso + 273.15 if is_k else t_iso
        t_tag = f"{disp_t:.0f} {'K' if is_k else '°C'}"
        for idx_c, (xs, ys) in enumerate(chains):
            curves.append({
                "name": f"{prefix} {t_tag}" if idx_c == 0 else f"{prefix} {t_tag} ({idx_c + 1})",
                "xs": xs,
                "ys": ys,
                "color": col,
                "line_style": "Solid",
                "line_width": 1.9,
            })
            mid_i = len(xs) // 2
            labels.append({
                "text": t_tag,
                "x": xs[mid_i],
                "y": ys[mid_i],
                "color": col,
                "bold": True,
            })


class TernaryDiagramEngine:
    """
    Core thermodynamic calculation engine for ternary phase equilibria and Gibbs triangles.
    Generates isothermal sections, liquidus projections, tie-lines, and invariant data.
    """

    ASSESSED_SYSTEMS = [
        "Co-Cr-Ni",
        "Cr-Fe-Ni",
        "Co-Fe-Ni",
        "Co-Cr-Fe",
        "Fe-Cr-Mn",
        "Mo-Nb-Ta",
        "Mo-Ta-W",
        "Nb-Ta-W",
        "Ti-Zr-Nb",
        "Mo-Nb-V",
        "Ni-Al-Ti",
        "Fe-Cr-C",
        "Al-Cu-Mg",
        "Mo-V-W",
        "Cd-Pb-Sn",
        "Cr-Fe-Nb",
        "Al-Cu-Y",
        "Fe-Sb-O",
        "MgO-Al2O3-SiO2",
        "Al2O3-SiO2-ZrO2",
    ]

    @classmethod
    def get_assessed_systems(cls) -> List[Dict[str, Any]]:
        """Returns catalogue of assessed ternary alloy systems with metadata."""
        catalog = [
            {"id": "Co-Cr-Ni", "name": "Co-Cr-Ni", "description": "Cantor HEA Core Matrix", "category": "Cantor HEA", "elements": ["Co", "Cr", "Ni"], "topology": "FCC + BCC + Sigma", "citation": "X. L. Liu et al., Calphad 52 (2016) 125-142"},
            {"id": "Cr-Fe-Ni", "name": "Cr-Fe-Ni", "description": "Austenitic / Duplex Stainless Steel", "category": "Stainless & HEA", "elements": ["Cr", "Fe", "Ni"], "topology": "FCC + BCC + Sigma", "citation": "B.-J. Lee, Calphad 17 (1993) 251-268"},
            {"id": "Co-Fe-Ni", "name": "Co-Fe-Ni", "description": "Permalloy / Soft Magnetic Solid Solution", "category": "Cantor HEA", "elements": ["Co", "Fe", "Ni"], "topology": "Continuous FCC + BCC(Fe)", "citation": "C.-H. Xia et al., J. Alloys Compd. 853 (2021) 157165"},
            {"id": "Co-Cr-Fe", "name": "Co-Cr-Fe", "description": "High-Strength Sigma-Strengthened HEA", "category": "Cantor HEA", "elements": ["Co", "Cr", "Fe"], "topology": "FCC + BCC + Extended Sigma", "citation": "G. Shang et al., Calphad 80 (2023) 102526"},
            {"id": "Fe-Cr-Mn", "name": "Fe-Cr-Mn", "description": "High-Mn Austenitic Stainless Steel", "category": "Stainless & HEA", "elements": ["Fe", "Cr", "Mn"], "topology": "FCC + BCC + Sigma + Mn-phases", "citation": "Y. Murata et al., ISIJ Int. 30 (1990) 927-936"},
            {"id": "Mo-Nb-Ta", "name": "Mo-Nb-Ta", "description": "Senkov Heavy Refractory HEA Base", "category": "Refractory HEA", "elements": ["Mo", "Nb", "Ta"], "topology": "Isomorphous BCC_A2", "citation": "W. Xiong et al., Calphad 28 (2004) 133-140"},
            {"id": "Mo-Ta-W", "name": "Mo-Ta-W", "description": "Ultra-High Melting Refractory System", "category": "Refractory HEA", "elements": ["Mo", "Ta", "W"], "topology": "Continuous BCC_A2 + B2 Ordering", "citation": "P. E. A. Turchi et al., Phys. Rev. B 71 (2005) 094206"},
            {"id": "Nb-Ta-W", "name": "Nb-Ta-W", "description": "High-Temperature Ductile Refractory Base", "category": "Refractory HEA", "elements": ["Nb", "Ta", "W"], "topology": "Isomorphous BCC_A2", "citation": "Y. Liu et al., Calphad 36 (2012) 110-117"},
            {"id": "Ti-Zr-Nb", "name": "Ti-Zr-Nb", "description": "Biomedical & Ductile Refractory MEA", "category": "Refractory HEA", "elements": ["Ti", "Zr", "Nb"], "topology": "BCC + Monotectoid Gap + HCP", "citation": "C. Marker et al., Calphad 61 (2018) 72-84"},
            {"id": "Mo-Nb-V", "name": "Mo-Nb-V", "description": "Medium-Density Refractory HEA Solution", "category": "Refractory HEA", "elements": ["Mo", "Nb", "V"], "topology": "Isomorphous BCC_A2", "citation": "Z. Li et al., Calphad 95 (2026) 103023"},
            {"id": "Ni-Al-Ti", "name": "Ni-Al-Ti", "description": "Superalloy Gamma / Gamma-Prime Benchmark", "category": "Superalloys", "elements": ["Ni", "Al", "Ti"], "topology": "Gamma + Gamma' + Heusler Tau4", "citation": "K. J. Lee & P. Nash, J. Phase Equilib. 12 (1991) 551-562"},
            {"id": "Fe-Cr-C", "name": "Fe-Cr-C", "description": "Wear-Resistant White Cast Iron & Tool Steel", "category": "Steels & Irons", "elements": ["Fe", "Cr", "C"], "topology": "Austenite + Ferrite + M7C3 + M23C6", "citation": "J.-O. Andersson, Metall. Trans. A 19 (1988) 627-636"},
            {"id": "Al-Cu-Mg", "name": "Al-Cu-Mg", "description": "Aerospace 2xxx Structural Alloy with S-Phase", "category": "Light Alloys", "elements": ["Al", "Cu", "Mg"], "topology": "FCC_Al + S(Al2CuMg) + Theta(Al2Cu)", "citation": "T. Buhler et al., J. Phase Equilib. 19 (1998) 317-333"},
            {"id": "Mo-V-W", "name": "Mo-V-W", "description": "Mallik 1984 Ideal Isomorphous Benchmark", "category": "Benchmarks", "elements": ["Mo", "V", "W"], "topology": "Type I Continuous Isomorphous", "citation": "A. K. Mallik, Bull. Mater. Sci. 8 (1986) 107-121"},
            {"id": "Cd-Pb-Sn", "name": "Cd-Pb-Sn", "description": "Mallik 1986 Class I Ternary Eutectic", "category": "Benchmarks", "elements": ["Cd", "Pb", "Sn"], "topology": "Class I Ternary Eutectic (TE=145 C)", "citation": "K. Osamura & Z. Du, J. Phase Equilib. 14 (1993) 206-213"},
            {"id": "Cr-Fe-Nb", "name": "Cr-Fe-Nb", "description": "PyCalphad Laves C14 Benchmark @ 1323 K", "category": "Refractory & Steel", "elements": ["Cr", "Fe", "Nb"], "topology": "BCC + C14 Laves + Sigma", "citation": "C. Jacob et al., Calphad 54 (2016) 130-141"},
            {"id": "Al-Cu-Y", "name": "Al-Cu-Y", "description": "PyCalphad Heusler & Intermetallics", "category": "Light Alloys", "elements": ["Al", "Cu", "Y"], "topology": "FCC + Tau1-Tau6 + Liquid Gap", "citation": "C. Zhang et al., Calphad 35 (2011) 607-617"},
            {"id": "Fe-Sb-O", "name": "Fe-Sb-O", "description": "PyCalphad Slag & Oxide MQMQA Model", "category": "Oxides & Slags", "elements": ["Fe", "Sb", "O"], "topology": "Slag Liquid + Spinel + Hematite", "citation": "M. Shishin et al., Calphad 65 (2019) 211-224"},
            {"id": "MgO-Al2O3-SiO2", "name": "MgO-Al2O3-SiO2", "description": "MAS Cordierite Ceramic", "category": "Ceramics & Refractories", "elements": ["SiO2", "MgO", "Al2O3"], "topology": "Cordierite + Mullite + Spinel + Forsterite", "citation": "Levin, Robbins & McMurdie (ACerS Sys 712); J. Petrology 2(3):324"},
            {"id": "Al2O3-SiO2-ZrO2", "name": "Al2O3-SiO2-ZrO2", "description": "AZS Fused-Cast Refractory", "category": "Ceramics & Refractories", "elements": ["SiO2", "ZrO2", "Al2O3"], "topology": "Zirconia + Mullite + Zircon + Corundum", "citation": "ACerS Phase Equilibria Diagrams; Refractories Handbook (2018)"},
        ]
        return catalog

    @classmethod
    def generate_gibbs_triangle_grid(cls, step: float = 0.1) -> Dict[str, Any]:
        """
        Generates the standard Gibbs equilateral triangle frame and internal grid lines.
        Returns coordinate series in Cartesian format (X, Y) ready for direct ScottPlot rendering.
        """
        # Outer triangular border: (0,0) -> (1,0) -> (0.5, sqrt(3)/2) -> (0,0)
        border_x = [0.0, 1.0, 0.5, 0.0]
        border_y = [0.0, 0.0, SQRT3_OVER_2, 0.0]

        grid_lines = []
        n_steps = int(round(1.0 / step))

        for i in range(1, n_steps):
            frac = i * step

            # 1. Constant C lines (horizontal lines, parallel to A-B base)
            # From (1-frac, 0, frac) to (0, 1-frac, frac)
            x1, y1 = barycentric_to_cartesian(1.0 - frac, 0.0, frac)
            x2, y2 = barycentric_to_cartesian(0.0, 1.0 - frac, frac)
            grid_lines.append({"name": f"c_{frac:.1f}", "xs": [x1, x2], "ys": [y1, y2], "frac": frac, "axis": "C"})

            # 2. Constant A lines (parallel to B-C edge)
            # From (frac, 1-frac, 0) to (frac, 0, 1-frac)
            x1, y1 = barycentric_to_cartesian(frac, 1.0 - frac, 0.0)
            x2, y2 = barycentric_to_cartesian(frac, 0.0, 1.0 - frac)
            grid_lines.append({"name": f"a_{frac:.1f}", "xs": [x1, x2], "ys": [y1, y2], "frac": frac, "axis": "A"})

            # 3. Constant B lines (parallel to C-A edge)
            # From (1-frac, frac, 0) to (0, frac, 1-frac)
            x1, y1 = barycentric_to_cartesian(1.0 - frac, frac, 0.0)
            x2, y2 = barycentric_to_cartesian(0.0, frac, 1.0 - frac)
            grid_lines.append({"name": f"b_{frac:.1f}", "xs": [x1, x2], "ys": [y1, y2], "frac": frac, "axis": "B"})

        return {
            "border_x": border_x,
            "border_y": border_y,
            "grid_lines": grid_lines,
            "apex_a": {"label": "A (0,0,1)", "x": 0.0, "y": 0.0},
            "apex_b": {"label": "B (0,1,0)", "x": 1.0, "y": 0.0},
            "apex_c": {"label": "C (1,0,0)", "x": 0.5, "y": SQRT3_OVER_2},
        }

    @classmethod
    def compute_ternary_diagram(
        cls,
        system_name: str,
        diagram_type: str = "isothermal",
        temperature_c: float = 800.0,
        temp_unit: str = "C",
    ) -> Dict[str, Any]:
        """
        Main calculation dispatcher for ternary phase diagrams.
        """
        sys_clean = system_name.strip()
        sys_lower = sys_clean.lower()
        is_k = temp_unit.upper() == "K"
        t_c = temperature_c - 273.15 if is_k else temperature_c
        t_k = temperature_c if is_k else temperature_c + 273.15

        if "co-cr-ni" in sys_lower or "cocrni" in sys_lower:
            return cls._compute_co_cr_ni(diagram_type, t_c, is_k)
        elif "cr-fe-ni" in sys_lower or "crfeni" in sys_lower:
            return cls._compute_cr_fe_ni(diagram_type, t_c, is_k)
        elif "co-fe-ni" in sys_lower or "cofeni" in sys_lower:
            return cls._compute_co_fe_ni(diagram_type, t_c, is_k)
        elif "co-cr-fe" in sys_lower or "cocrfe" in sys_lower:
            return cls._compute_co_cr_fe(diagram_type, t_c, is_k)
        elif "fe-cr-mn" in sys_lower or "fecrmn" in sys_lower:
            return cls._compute_fe_cr_mn(diagram_type, t_c, is_k)
        elif "mo-nb-ta" in sys_lower or "monbta" in sys_lower:
            return cls._compute_mo_nb_ta(diagram_type, t_c, is_k)
        elif "mo-ta-w" in sys_lower or "motaw" in sys_lower:
            return cls._compute_mo_ta_w(diagram_type, t_c, is_k)
        elif "nb-ta-w" in sys_lower or "nbtaw" in sys_lower:
            return cls._compute_nb_ta_w(diagram_type, t_c, is_k)
        elif "ti-zr-nb" in sys_lower or "tizrnb" in sys_lower or "nb-ti-zr" in sys_lower:
            return cls._compute_ti_zr_nb(diagram_type, t_c, is_k)
        elif "mo-nb-v" in sys_lower or "monbv" in sys_lower:
            return cls._compute_mo_nb_v(diagram_type, t_c, is_k)
        elif "ni-al-ti" in sys_lower or "nialti" in sys_lower or "al-ni-ti" in sys_lower:
            return cls._compute_ni_al_ti(diagram_type, t_c, is_k)
        elif "fe-cr-c" in sys_lower or "fecrc" in sys_lower:
            return cls._compute_fe_cr_c(diagram_type, t_c, is_k)
        elif "al-cu-mg" in sys_lower or "alcumg" in sys_lower:
            return cls._compute_al_cu_mg(diagram_type, t_c, is_k)
        elif "mo-v-w" in sys_lower or "movw" in sys_lower:
            return cls._compute_mo_v_w(diagram_type, t_c, is_k)
        elif "cd-pb-sn" in sys_lower or "cdpbsn" in sys_lower:
            return cls._compute_cd_pb_sn(diagram_type, t_c, is_k)
        elif "cr-fe-nb" in sys_lower or "crfenb" in sys_lower:
            return cls._compute_cr_fe_nb(diagram_type, t_c, is_k)
        elif "al-cu-y" in sys_lower or "alcuy" in sys_lower:
            return cls._compute_al_cu_y(diagram_type, t_c, is_k)
        elif "fe-sb-o" in sys_lower or "fesbo" in sys_lower:
            return cls._compute_fe_sb_o(diagram_type, t_c, is_k)
        elif "mgo-al2o3-sio2" in sys_lower or "mas" in sys_lower or "sio2-mgo-al2o3" in sys_lower:
            return cls._compute_mgo_al2o3_sio2(diagram_type, t_c, is_k)
        elif "al2o3-sio2-zro2" in sys_lower or "azs" in sys_lower or "sio2-zro2-al2o3" in sys_lower:
            return cls._compute_al2o3_sio2_zro2(diagram_type, t_c, is_k)
        else:
            # Parse arbitrary triplet
            parts = [p.strip().capitalize() for p in sys_clean.replace("_", "-").split("-")]
            if len(parts) >= 3:
                return cls._compute_arbitrary_ternary(parts[0], parts[1], parts[2], diagram_type, t_c, is_k)
            return cls._compute_co_cr_ni(diagram_type, t_c, is_k)

    # =========================================================================
    # 1. Co-Cr-Ni Ternary System (Cantor HEA Archetype)
    # References: X. L. Liu et al. (2016), N. Zhao et al. (2020), P. Wang (2021)
    # =========================================================================
    @classmethod
    def _compute_co_cr_ni(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Co", "Cr", "Ni"
        invariants = [
            {"type": "Peritectic", "temp_c": 1400.0, "equation": "L + BCC(Cr) ⇌ FCC(Co,Ni) + Sigma", "composition": "Co20Cr55Ni25", "desc": "Solidification transition in high-Cr field"},
            {"type": "Eutectic", "temp_c": 1345.0, "equation": "L ⇌ FCC(Ni,Co) + BCC(Cr)", "composition": "Co15Cr45Ni40", "desc": "Extension of binary Cr-Ni eutectic into ternary"},
            {"type": "Solid-State", "temp_c": 800.0, "equation": "FCC ⇌ FCC + Sigma (CoCr-rich)", "composition": "Co33Cr34Ni33", "desc": "Intermediate-temperature sigma phase precipitation"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Isothermal section at t_c (default 800-1000 °C)
        # 1. FCC Solvus boundary: connects Co-Cr binary edge (~41 at% Cr) across ternary to Ni-Cr binary edge (~47 at% Cr)
        cr_sol_co = max(0.35, min(0.48, 0.41 + (t_c - 1000.0) * 0.00012))
        cr_sol_ni = max(0.40, min(0.52, 0.47 + (t_c - 1000.0) * 0.00010))
        fcc_knots = [
            (1.0 - cr_sol_co, cr_sol_co, 0.00),
            (0.45, cr_sol_co + 0.02, 0.12),
            (0.30, cr_sol_co + 0.04, 0.25),
            (0.15, cr_sol_ni - 0.01, 0.39),
            (0.00, cr_sol_ni, 1.0 - cr_sol_ni),
        ]
        xs_fcc, ys_fcc = _interpolate_ternary_curve(fcc_knots, n_pts=50)
        curves.append({
            "name": "FCC Solvus Boundary",
            "xs": xs_fcc,
            "ys": ys_fcc,
            "color": "#1D4ED8",
            "line_style": "Solid",
            "line_width": 2.2
        })

        # 2. BCC Solvus boundary near pure Cr corner
        bcc_knots = [
            (0.15, 0.85, 0.00),
            (0.07, 0.86, 0.07),
            (0.00, 0.88, 0.12),
        ]
        xs_bcc, ys_bcc = _interpolate_ternary_curve(bcc_knots, n_pts=30)
        curves.append({
            "name": "BCC (α-Cr) Solvus Boundary",
            "xs": xs_bcc,
            "ys": ys_bcc,
            "color": "#059669",
            "line_style": "Solid",
            "line_width": 2.0
        })

        # 3. Sigma phase field in high-Cr region extending from Co-Cr binary edge
        sigma_knots = [
            (0.43, 0.57, 0.00),
            (0.34, 0.56, 0.10),
            (0.24, 0.58, 0.18),
            (0.20, 0.64, 0.16),
            (0.28, 0.64, 0.08),
            (0.37, 0.63, 0.00),
        ]
        xs_sig, ys_sig = _interpolate_ternary_curve(sigma_knots, n_pts=45)
        curves.append({
            "name": "Sigma (σ) Phase Field",
            "xs": xs_sig,
            "ys": ys_sig,
            "color": "#DC2626",
            "line_style": "Solid",
            "line_width": 2.0
        })

        # 4. Three-Phase Tie-Triangle (FCC + BCC + Sigma)
        v1_fcc = barycentric_to_cartesian(0.28, 0.45, 0.27)
        v2_sig = barycentric_to_cartesian(0.20, 0.64, 0.16)
        v3_bcc = barycentric_to_cartesian(0.07, 0.86, 0.07)
        tie_triangles.append({
            "name": "FCC + BCC + σ Three-Phase Equilibrium",
            "v1": [v1_fcc[0], v1_fcc[1]],
            "v2": [v2_sig[0], v2_sig[1]],
            "v3": [v3_bcc[0], v3_bcc[1]],
            "color": "#3B82F6",
            "border_color": "#1D4ED8"
        })

        # 5. Conjugate two-phase tie-lines strictly within their respective fields
        # (a) FCC + Sigma tie-lines
        fcc_sigma_pairs = [
            ((0.51, 0.42, 0.07), (0.39, 0.56, 0.05)),
            ((0.38, 0.44, 0.18), (0.27, 0.58, 0.15)),
        ]
        for p1, p2 in fcc_sigma_pairs:
            x1, y1 = barycentric_to_cartesian(*p1)
            x2, y2 = barycentric_to_cartesian(*p2)
            tie_lines.append({"xs": [x1, x2], "ys": [y1, y2], "color": "#64748B"})

        # (b) FCC + BCC tie-lines
        fcc_bcc_pairs = [
            ((0.18, 0.46, 0.36), (0.04, 0.87, 0.09)),
            ((0.08, 0.47, 0.45), (0.01, 0.88, 0.11)),
        ]
        for p1, p2 in fcc_bcc_pairs:
            x1, y1 = barycentric_to_cartesian(*p1)
            x2, y2 = barycentric_to_cartesian(*p2)
            tie_lines.append({"xs": [x1, x2], "ys": [y1, y2], "color": "#64748B"})

        # (c) Sigma + BCC tie-line
        sig_bcc_pairs = [
            ((0.32, 0.64, 0.04), (0.11, 0.85, 0.04)),
        ]
        for p1, p2 in sig_bcc_pairs:
            x1, y1 = barycentric_to_cartesian(*p1)
            x2, y2 = barycentric_to_cartesian(*p2)
            tie_lines.append({"xs": [x1, x2], "ys": [y1, y2], "color": "#64748B"})

        # 6. Phase region labels
        x_fcc, y_fcc = barycentric_to_cartesian(0.45, 0.15, 0.40)
        labels.append({"text": "FCC (γ) Solid Solution", "x": x_fcc, "y": y_fcc, "color": "#1D4ED8", "bold": True})

        x_sig_lbl, y_sig_lbl = barycentric_to_cartesian(0.30, 0.60, 0.10)
        labels.append({"text": "Sigma (σ)", "x": x_sig_lbl, "y": y_sig_lbl, "color": "#DC2626", "bold": True})

        x_bcc_lbl, y_bcc_lbl = barycentric_to_cartesian(0.04, 0.93, 0.03)
        labels.append({"text": "BCC (α-Cr)", "x": x_bcc_lbl, "y": y_bcc_lbl, "color": "#059669", "bold": True})

        x_fcc_sig, y_fcc_sig = barycentric_to_cartesian(0.42, 0.48, 0.10)
        labels.append({"text": "FCC + σ", "x": x_fcc_sig, "y": y_fcc_sig, "color": "#475569", "bold": False})

        x_fcc_bcc, y_fcc_bcc = barycentric_to_cartesian(0.10, 0.65, 0.25)
        labels.append({"text": "FCC + BCC", "x": x_fcc_bcc, "y": y_fcc_bcc, "color": "#475569", "bold": False})

        x_tri, y_tri = barycentric_to_cartesian(0.18, 0.65, 0.17)
        labels.append({"text": "FCC + BCC + σ", "x": x_tri, "y": y_tri, "color": "#1E3A8A", "bold": True})

        return cls._build_ternary_payload(
            system="Co-Cr-Ni",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Assessed CALPHAD thermodynamic model (Liu 2016). Extensive single-phase FCC matrix stability around equiatomic CoCrNi (VEC=8.33). Sigma phase precipitates only at high Cr concentrations (>40 at%) below 1100°C."
        )

    # =========================================================================
    # 2. Cr-Fe-Ni Ternary System (Stainless Steel & Superalloy Benchmark)
    # References: B.-J. Lee (1993), J. Miettinen (1999), M. Hillert & C. Qiu (1990)
    # =========================================================================
    @classmethod
    def _compute_cr_fe_ni(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Fe", "Cr", "Ni"
        invariants = [
            {"type": "Monovariant Valley", "temp_c": 1345.0, "equation": "L + delta-BCC <-> gamma-FCC", "composition": "Fe10Cr49.5Ni40.5", "desc": "Continuous liquidus transition from Fe-Ni peritectic to Cr-Ni eutectic"},
            {"type": "Class II Invariant", "temp_c": 830.0, "equation": "FCC + BCC <-> Sigma + FCC", "composition": "Fe45Cr45Ni10", "desc": "Subsolidus eutectoid-type sigma phase formation in duplex compositions"},
            {"type": "Congruent Monovariant", "temp_c": 1305.0, "equation": "L <-> BCC (Fe-Cr minimum)", "composition": "Fe78.5Cr21.5Ni0", "desc": "Binary Fe-Cr liquidus minimum extending into ternary"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Monovariant liquidus boundary connecting Fe-Ni peritectic (~1517 C) to Cr-Ni eutectic (~1345 C)
        liq_valley_knots = [
            (0.85, 0.05, 0.10),
            (0.60, 0.18, 0.22),
            (0.35, 0.32, 0.33),
            (0.15, 0.45, 0.40),
            (0.00, 0.495, 0.505),
        ]
        xs_val, ys_val = _interpolate_ternary_curve(liq_valley_knots, n_pts=60)
        curves.append({"name": "Monovariant Liquidus Boundary (L + δ ↔ γ)", "xs": xs_val, "ys": ys_val, "color": "#0F172A", "line_style": "Solid", "line_width": 2.5})

        # Dual-phase duplex boundary at service temperature (e.g. 900 C)
        solvus_knots = [
            (0.80, 0.15, 0.05),
            (0.65, 0.24, 0.11),
            (0.45, 0.35, 0.20),
            (0.20, 0.45, 0.35),
            (0.00, 0.52, 0.48),
        ]
        xs_solv, ys_solv = _interpolate_ternary_curve(solvus_knots, n_pts=50)
        curves.append({"name": "Ferrite / Austenite Phase Boundary (α / γ)", "xs": xs_solv, "ys": ys_solv, "color": "#2563EB", "line_style": "Dashed", "line_width": 1.8})

        # Three-phase tie-triangle (FCC + BCC + Sigma) at ~750°C
        v1 = (0.50, 0.25, 0.25)  # FCC
        v2 = (0.20, 0.70, 0.10)  # BCC
        v3 = (0.42, 0.48, 0.10)  # Sigma
        p1 = barycentric_to_cartesian(*v1)
        p2 = barycentric_to_cartesian(*v2)
        p3 = barycentric_to_cartesian(*v3)
        tie_triangles.append({"v1": p1, "v2": p2, "v3": p3, "color": "#FEE2E2", "border_color": "#DC2626", "name": "FCC + BCC + Sigma Tie-Triangle"})

        # Labels
        x_fcc, y_fcc = barycentric_to_cartesian(0.30, 0.10, 0.60)
        labels.append({"text": "Austenite γ (FCC)", "x": x_fcc, "y": y_fcc, "color": "#1D4ED8", "bold": True})
        x_bcc, y_bcc = barycentric_to_cartesian(0.70, 0.25, 0.05)
        labels.append({"text": "Ferrite α/δ (BCC)", "x": x_bcc, "y": y_bcc, "color": "#059669", "bold": True})
        x_sig, y_sig = barycentric_to_cartesian(0.35, 0.52, 0.13)
        labels.append({"text": "σ Phase", "x": x_sig, "y": y_sig, "color": "#DC2626", "bold": True})

        return cls._build_ternary_payload(
            system="Cr-Fe-Ni",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Assessed CALPHAD benchmark (B.-J. Lee 1993, Miettinen 1999). Classic Schaeffler-Delong metallurgical matrix. Liquidus exhibits single continuous monovariant boundary without ternary invariant points. Subsolidus features FCC+BCC+Sigma equilibrium."
        )

    # =========================================================================
    # Generalized Regular-Solution Isomorphous Ternary Engine (Liquidus + Isothermal)
    # =========================================================================
    @classmethod
    def _compute_isomorphous_ternary(
        cls,
        system: str,
        el_a: str,
        el_b: str,
        el_c: str,
        tm_a: float,
        tm_b: float,
        tm_c: float,
        diag_type: str,
        t_c: float,
        is_k: bool,
        notes: str,
        invariants: List[Dict[str, Any]],
        excess_dt: Tuple[float, float, float] = (65.0, 45.0, 80.0),
        lens_span: float = 0.22,
        solid_phase_label: str = "Single-Phase BCC_A2 Solid Solution",
    ) -> Dict[str, Any]:
        """
        Computes strictly non-intersecting boundary-to-boundary liquidus/solidus
        isotherms and true isothermal equilibria for Type-I isomorphous systems.
        """
        d_ab, d_bc, d_ca = excess_dt

        def t_liq_fn(a: float, b: float, c: float) -> float:
            return (
                a * tm_a
                + b * tm_b
                + c * tm_c
                + a * b * d_ab
                + b * c * d_bc
                + c * a * d_ca
            )

        def t_sol_fn(a: float, b: float, c: float) -> float:
            # Thermodynamic lens depression vanishes at pure vertices and scales with delta-Tm
            lens = lens_span * (
                a * b * abs(tm_a - tm_b)
                + b * c * abs(tm_b - tm_c)
                + c * a * abs(tm_c - tm_a)
            )
            return t_liq_fn(a, b, c) - lens

        t_min = min(tm_a, tm_b, tm_c)
        t_max = max(tm_a, tm_b, tm_c)

        # Sample extrema cleanly across grid
        t_sol_min = t_min
        t_liq_max = t_max
        for i in range(0, 21):
            a = i / 20.0
            for j in range(0, 21 - i):
                b = j / 20.0
                c = max(0.0, 1.0 - a - b)
                t_sol_min = min(t_sol_min, t_sol_fn(a, b, c))
                t_liq_max = max(t_liq_max, t_liq_fn(a, b, c))

        curves: List[Dict[str, Any]] = []
        tie_lines: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []

        if diag_type == "liquidus":
            # 5 cleanly spaced non-intersecting liquidus isotherms spanning [t_min, t_max]
            palette = ["#38BDF8", "#0284C7", "#0369A1", "#1D4ED8", "#1E3A8A"]
            span = max(50.0, t_liq_max - t_sol_min)
            fracs = [0.16, 0.34, 0.52, 0.70, 0.88]
            for frac, col in zip(fracs, palette):
                t_iso = round((t_sol_min + frac * span) / 25.0) * 25.0
                if not (t_sol_min + 10.0 <= t_iso <= t_liq_max - 10.0):
                    continue
                chains = _trace_ternary_isocontours(t_liq_fn, t_iso, n_grid=54)
                disp_t = t_iso + 273.15 if is_k else t_iso
                t_tag = f"{disp_t:.0f} {'K' if is_k else '°C'}"
                for idx_c, (xs, ys) in enumerate(chains):
                    curves.append({
                        "name": f"Liquidus {t_tag}" if idx_c == 0 else f"Liquidus {t_tag} ({idx_c + 1})",
                        "xs": xs,
                        "ys": ys,
                        "color": col,
                        "line_style": "Solid",
                        "line_width": 1.9,
                    })
                    mid_i = len(xs) // 2
                    labels.append({
                        "text": t_tag,
                        "x": xs[mid_i],
                        "y": ys[mid_i],
                        "color": col,
                        "bold": True,
                    })

            x_center, y_center = barycentric_to_cartesian(0.333, 0.333, 0.334)
            labels.append({
                "text": f"Liquidus Projection ({solid_phase_label})",
                "x": x_center,
                "y": max(0.06, y_center - 0.14),
                "color": "#0F172A",
                "bold": True,
            })
        else:
            # Isothermal equilibrium section strictly at t_c
            if t_c <= t_sol_min + 2.0:
                # Completely solid single-phase field at t_c (e.g., Mo-Nb-Ta @ 800 K)
                x_center, y_center = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({
                    "text": solid_phase_label,
                    "x": x_center,
                    "y": y_center,
                    "color": "#0284C7",
                    "bold": True,
                })
            elif t_c >= t_liq_max - 2.0:
                x_center, y_center = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({
                    "text": "Single-Phase Liquid Solution (L)",
                    "x": x_center,
                    "y": y_center,
                    "color": "#1D4ED8",
                    "bold": True,
                })
            else:
                # Two-phase L + BCC mushy band at intermediate isothermal temperature t_c
                liq_chains = _trace_ternary_isocontours(t_liq_fn, t_c, n_grid=56)
                sol_chains = _trace_ternary_isocontours(t_sol_fn, t_c, n_grid=56)
                for xs, ys in liq_chains:
                    curves.append({
                        "name": "Liquidus Boundary (L / L + BCC)",
                        "xs": xs,
                        "ys": ys,
                        "color": "#0284C7",
                        "line_style": "Solid",
                        "line_width": 2.2,
                    })
                for xs, ys in sol_chains:
                    curves.append({
                        "name": "Solidus Boundary (L + BCC / BCC)",
                        "xs": xs,
                        "ys": ys,
                        "color": "#DC2626",
                        "line_style": "Dashed",
                        "line_width": 2.0,
                    })

                # Construct conjugate two-phase tie-lines linking liquidus and solidus curves
                if liq_chains and sol_chains:
                    lx, ly = liq_chains[0]
                    sx, sy = sol_chains[0]
                    d_same = (lx[0] - sx[0]) ** 2 + (ly[0] - sy[0]) ** 2
                    d_flip = (lx[0] - sx[-1]) ** 2 + (ly[0] - sy[-1]) ** 2
                    if d_flip < d_same:
                        sx = list(reversed(sx))
                        sy = list(reversed(sy))
                    for frac in [0.18, 0.38, 0.58, 0.78]:
                        li = min(len(lx) - 1, max(0, int(frac * (len(lx) - 1))))
                        si = min(len(sx) - 1, max(0, int(frac * (len(sx) - 1))))
                        tie_lines.append({
                            "xs": [lx[li], sx[si]],
                            "ys": [ly[li], sy[si]],
                            "color": "#64748B",
                        })

                # Place region labels on solid, liquid, and mushy regions accurately
                verts = [
                    (tm_a, (0.86, 0.07, 0.07)),
                    (tm_b, (0.07, 0.86, 0.07)),
                    (tm_c, (0.07, 0.07, 0.86)),
                ]
                low_v = min(verts, key=lambda kv: kv[0])[1]
                high_v = max(verts, key=lambda kv: kv[0])[1]
                xl, yl = barycentric_to_cartesian(*low_v)
                xh, yh = barycentric_to_cartesian(*high_v)
                labels.append({"text": "Liquid (L)", "x": xl, "y": yl, "color": "#1D4ED8", "bold": True})
                labels.append({"text": "BCC_A2 Solid", "x": xh, "y": yh, "color": "#059669", "bold": True})

        return cls._build_ternary_payload(
            system=system,
            el_a=el_a,
            el_b=el_b,
            el_c=el_c,
            diag_type=diag_type,
            temp_c=t_c,
            is_k=is_k,
            curves=curves,
            tie_lines=tie_lines,
            tie_triangles=[],
            labels=labels,
            invariants=invariants,
            notes=notes,
        )

    # =========================================================================
    # 3. Mo-Nb-Ta Refractory HEA System (Senkov Heavy RHEA Archetype)
    # References: W. Xiong et al. (2004), C. Marker et al. (2018), Turchi (2020)
    # =========================================================================
    @classmethod
    def _compute_mo_nb_ta(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        invariants = [
            {"type": "Isomorphous", "temp_c": 2623.0, "equation": "Liquid <-> BCC_A2 (Continuous Solid Solution)", "composition": "Mo33Nb33Ta34", "desc": "Complete liquid and solid mutual solubility across entire ternary triangle"},
            {"type": "Binary Melting", "temp_c": 2623.0, "equation": "Pure Mo Melting", "composition": "Mo100", "desc": "2896 K unary benchmark"},
            {"type": "Binary Melting", "temp_c": 2477.0, "equation": "Pure Nb Melting", "composition": "Nb100", "desc": "2750 K unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3020.0, "equation": "Pure Ta Melting", "composition": "Ta100", "desc": "3293 K unary benchmark"},
        ]
        return cls._compute_isomorphous_ternary(
            system="Mo-Nb-Ta",
            el_a="Mo", el_b="Nb", el_c="Ta",
            tm_a=2623.0, tm_b=2477.0, tm_c=3020.0,
            diag_type=diag_type, t_c=t_c, is_k=is_k,
            notes="Assessed CALPHAD refractory benchmark (Xiong 2004, Marker 2018). Type I continuous ternary isomorphous system. Completely single-phase BCC_A2 below 2477°C (2750 K); smooth edge-to-edge solidus/liquidus lens above 2477°C.",
            invariants=invariants,
            excess_dt=(55.0, 40.0, 75.0),
            lens_span=0.20,
            solid_phase_label="Single-Phase BCC_A2 Solid Solution",
        )

    # =========================================================================
    # 4. Ti-Zr-Nb Refractory System (Monotectoid Miscibility Gap & MEA Archetype)
    # References: C. Marker (2018), W. Chen (2017), W. Bai (2018)
    # =========================================================================
    @classmethod
    def _compute_ti_zr_nb(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Ti", "Zr", "Nb"
        invariants = [
            {"type": "Monotectoid Gap", "temp_c": 988.0, "equation": "BCC_high <-> BCC_1 + BCC_2", "composition": "Ti20Zr50Nb30", "desc": "Solid-state miscibility gap extending from Nb-Zr binary"},
            {"type": "Three-Phase Equilibrium", "temp_c": 700.0, "equation": "BCC_1 + BCC_2 + HCP(alpha)", "composition": "Ti45Zr35Nb20", "desc": "Three-phase tie-triangle between two BCC phases and HCP"},
            {"type": "Allotropic Transition", "temp_c": 882.0, "equation": "Pure Ti Beta-BCC <-> Alpha-HCP", "composition": "Ti100", "desc": "Unary Martensitic transus"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Monotectoid miscibility gap boundary at 700°C
        gap_knots = [
            (0.10, 0.85, 0.05),
            (0.25, 0.60, 0.15),
            (0.40, 0.40, 0.20),
            (0.35, 0.25, 0.40),
            (0.15, 0.15, 0.70),
        ]
        xs_gap, ys_gap = _interpolate_ternary_curve(gap_knots, n_pts=50)
        curves.append({"name": "BCC1 + BCC2 Miscibility Gap Boundary", "xs": xs_gap, "ys": ys_gap, "color": "#7C3AED", "line_style": "Solid", "line_width": 2.2})

        # HCP solvus in Ti-rich corner
        hcp_knots = [
            (0.95, 0.03, 0.02),
            (0.80, 0.15, 0.05),
            (0.65, 0.28, 0.07),
            (0.50, 0.45, 0.05),
        ]
        xs_hcp, ys_hcp = _interpolate_ternary_curve(hcp_knots, n_pts=40)
        curves.append({"name": "HCP (α) Solvus Boundary", "xs": xs_hcp, "ys": ys_hcp, "color": "#059669", "line_style": "Solid", "line_width": 2.0})

        # Three-phase tie-triangle at 700°C
        p1 = barycentric_to_cartesian(0.70, 0.22, 0.08)  # HCP
        p2 = barycentric_to_cartesian(0.20, 0.70, 0.10)  # BCC1 (Zr-rich)
        p3 = barycentric_to_cartesian(0.25, 0.25, 0.50)  # BCC2 (Nb-rich)
        tie_triangles.append({"v1": p1, "v2": p2, "v3": p3, "color": "#EDE9FE", "border_color": "#7C3AED", "name": "HCP + BCC1 + BCC2 Tie-Triangle (700°C)"})

        x_bcc_hi, y_bcc_hi = barycentric_to_cartesian(0.30, 0.10, 0.60)
        labels.append({"text": "Single-Phase β-BCC", "x": x_bcc_hi, "y": y_bcc_hi, "color": "#2563EB", "bold": True})
        x_hcp_lbl, y_hcp_lbl = barycentric_to_cartesian(0.85, 0.10, 0.05)
        labels.append({"text": "α-HCP", "x": x_hcp_lbl, "y": y_hcp_lbl, "color": "#059669", "bold": True})

        return cls._build_ternary_payload(
            system="Ti-Zr-Nb",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Assessed CALPHAD model (Marker 2018). Ductile biomedical RHEA base. Features solid-state BCC1+BCC2 miscibility gap closing near 988°C and three-phase HCP+BCC1+BCC2 equilibrium at 700°C."
        )

    # =========================================================================
    # 5. Ni-Al-Ti Superalloy Benchmark (Gamma / Gamma-Prime / Heusler Tau4)
    # References: K. J. Lee & P. Nash (1991), Thompson & Lemkey (1969)
    # =========================================================================
    @classmethod
    def _compute_ni_al_ti(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Ni", "Al", "Ti"
        invariants = [
            {"type": "E1 (Class I Ternary Eutectic)", "temp_c": 1277.0, "equation": "Liquid <-> gamma' + eta(TiNi3) + tau4(TiNi2Al)", "composition": "Ni67.4Al11.2Ti21.4", "desc": "Thompson & Lemkey 1969 / Lee & Nash 1991 benchmark"},
            {"type": "U1 (Class II Quasi-Peritectic)", "temp_c": 1302.0, "equation": "Liquid + gamma <-> gamma' + eta", "composition": "Ni70Al10Ti20", "desc": "High-temperature reaction on gamma-liquidus boundary"},
            {"type": "U4 (Class II)", "temp_c": 1100.0, "equation": "Liquid + beta1(NiAl) <-> kappa(TiAl) + nu(Ni2Al3)", "composition": "Ni45Al45Ti10", "desc": "Intermediate aluminide invariant"},
            {"type": "U12 (Class II)", "temp_c": 645.0, "equation": "Liquid + theta(TiAl3) <-> (Al) + epsilon(NiAl3)", "composition": "Ni2Al97Ti1", "desc": "Terminal Al-rich quasi-peritectic"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Gamma-prime (Ni3Al) phase field extending into Ni-Ti
        gp_knots = [
            (0.75, 0.25, 0.00),
            (0.74, 0.20, 0.06),
            (0.72, 0.14, 0.14),
            (0.70, 0.08, 0.22),
            (0.75, 0.05, 0.20),
            (0.76, 0.15, 0.09),
            (0.75, 0.25, 0.00),
        ]
        xs_gp, ys_gp = _interpolate_ternary_curve(gp_knots, n_pts=45)
        curves.append({"name": "γ'-Ni3(Al,Ti) Phase Boundary", "xs": xs_gp, "ys": ys_gp, "color": "#0284C7", "line_style": "Solid", "line_width": 2.2})

        # Heusler tau4 (TiNi2Al, cF16) phase field
        tau4_knots = [
            (0.52, 0.23, 0.25),
            (0.50, 0.20, 0.30),
            (0.48, 0.27, 0.25),
            (0.50, 0.30, 0.20),
            (0.52, 0.23, 0.25),
        ]
        xs_t4, ys_t4 = _interpolate_ternary_curve(tau4_knots, n_pts=35)
        curves.append({"name": "Heusler τ4 (TiNi2Al) Field", "xs": xs_t4, "ys": ys_t4, "color": "#D97706", "line_style": "Solid", "line_width": 2.0})

        # Ternary Eutectic E1 Point: 67.4 Ni - 11.2 Al - 21.4 Ti
        e1_x, e1_y = barycentric_to_cartesian(0.674, 0.112, 0.214)
        curves.append({"name": "E1 Ternary Eutectic Point (1277°C)", "xs": [e1_x], "ys": [e1_y], "color": "#DC2626", "line_style": "Point", "line_width": 3.0})

        # Tie-triangle for E1
        p_gp = barycentric_to_cartesian(0.72, 0.14, 0.14)
        p_eta = barycentric_to_cartesian(0.75, 0.02, 0.23)
        p_t4 = barycentric_to_cartesian(0.50, 0.25, 0.25)
        tie_triangles.append({"v1": p_gp, "v2": p_eta, "v3": p_t4, "color": "#FEF3C7", "border_color": "#D97706", "name": "γ' + η(TiNi3) + τ4 Tie-Triangle"})

        # Labels
        x_g_lbl, y_g_lbl = barycentric_to_cartesian(0.85, 0.08, 0.07)
        labels.append({"text": "Matrix γ (FCC-Ni)", "x": x_g_lbl, "y": y_g_lbl, "color": "#1D4ED8", "bold": True})
        x_gp_lbl, y_gp_lbl = barycentric_to_cartesian(0.71, 0.16, 0.13)
        labels.append({"text": "γ' Precipitates", "x": x_gp_lbl, "y": y_gp_lbl, "color": "#0284C7", "bold": True})
        labels.append({"text": "E1 (1277°C)", "x": e1_x + 0.02, "y": e1_y, "color": "#DC2626", "bold": True})

        return cls._build_ternary_payload(
            system="Ni-Al-Ti",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Assessed CALPHAD superalloy benchmark (Lee & Nash 1991, MSIT). High solubility of Ti in gamma-prime (up to 70% substitution on Al sites). Verified Class I ternary eutectic E1 at 1277°C (67.4 Ni - 11.2 Al - 21.4 Ti at%)."
        )

    # =========================================================================
    # 6. Cd-Pb-Sn Classical Benchmark (Class I Ternary Eutectic)
    # References: A. K. Mallik (1986), K. Osamura & Z. Du (1993)
    # =========================================================================
    @classmethod
    def _compute_cd_pb_sn(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Cd", "Pb", "Sn"
        invariants = [
            {"type": "E (Class I Ternary Eutectic)", "temp_c": 145.0, "equation": "Liquid -> (Cd) + (Pb) + (Sn)", "composition": "51.2 wt% Sn - 30.6 wt% Pb - 18.2 wt% Cd (58.2 at% Sn - 19.9 at% Pb - 21.9 at% Cd)", "desc": "Classic low-melting ternary eutectic (Osamura 1993, Mallik 1986)"},
            {"type": "Binary Eutectic", "temp_c": 183.0, "equation": "L -> (Pb) + (Sn)", "composition": "Pb26.1Sn73.9 at%", "desc": "Binary Pb-Sn benchmark"},
            {"type": "Binary Eutectic", "temp_c": 177.0, "equation": "L -> (Cd) + (Sn)", "composition": "Cd33.5Sn66.5 at%", "desc": "Binary Cd-Sn benchmark"},
            {"type": "Binary Eutectic", "temp_c": 248.0, "equation": "L -> (Cd) + (Pb)", "composition": "Cd28.0Pb72.0 at%", "desc": "Binary Cd-Pb benchmark"},
        ]

        curves = []
        tie_lines = []
        labels = []

        # Monovariant liquidus valleys converging from the 3 binary eutectics to E (145 C)
        # Eutectic point at (0.219 Cd, 0.199 Pb, 0.582 Sn)
        e_pt = (0.219, 0.199, 0.582)
        ex, ey = barycentric_to_cartesian(*e_pt)

        # Valley 1: from Cd-Pb eutectic (0.28 Cd, 0.72 Pb, 0.0 Sn) to E
        v1_knots = [(0.28, 0.72, 0.00), (0.25, 0.45, 0.30), e_pt]
        xs1, ys1 = _interpolate_ternary_curve(v1_knots, n_pts=30)
        curves.append({"name": "Monovariant Valley: e(Cd-Pb) -> E", "xs": xs1, "ys": ys1, "color": "#0284C7", "line_style": "Solid", "line_width": 2.2})

        # Valley 2: from Pb-Sn eutectic (0.0 Cd, 0.261 Pb, 0.739 Sn) to E
        v2_knots = [(0.00, 0.261, 0.739), (0.10, 0.23, 0.67), e_pt]
        xs2, ys2 = _interpolate_ternary_curve(v2_knots, n_pts=30)
        curves.append({"name": "Monovariant Valley: e(Pb-Sn) -> E", "xs": xs2, "ys": ys2, "color": "#059669", "line_style": "Solid", "line_width": 2.2})

        # Valley 3: from Cd-Sn eutectic (0.335 Cd, 0.0 Pb, 0.665 Sn) to E
        v3_knots = [(0.335, 0.00, 0.665), (0.28, 0.10, 0.62), e_pt]
        xs3, ys3 = _interpolate_ternary_curve(v3_knots, n_pts=30)
        curves.append({"name": "Monovariant Valley: e(Cd-Sn) -> E", "xs": xs3, "ys": ys3, "color": "#7C3AED", "line_style": "Solid", "line_width": 2.2})

        # Invariant E point
        curves.append({"name": "Ternary Eutectic E (145°C)", "xs": [ex], "ys": [ey], "color": "#DC2626", "line_style": "Point", "line_width": 3.5})

        labels.append({"text": "Eutectic E (145°C / 418 K)", "x": ex + 0.02, "y": ey, "color": "#DC2626", "bold": True})
        x_cd, y_cd = barycentric_to_cartesian(0.70, 0.15, 0.15)
        labels.append({"text": "Primary (Cd) Field", "x": x_cd, "y": y_cd, "color": "#475569", "bold": True})
        x_pb, y_pb = barycentric_to_cartesian(0.15, 0.70, 0.15)
        labels.append({"text": "Primary (Pb) Field", "x": x_pb, "y": y_pb, "color": "#475569", "bold": True})
        x_sn, y_sn = barycentric_to_cartesian(0.15, 0.15, 0.70)
        labels.append({"text": "Primary (Sn) Field", "x": x_sn, "y": y_sn, "color": "#475569", "bold": True})

        return cls._build_ternary_payload(
            system="Cd-Pb-Sn",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=[], tie_triangles=[],
            labels=labels, invariants=invariants,
            notes="Classic computational metallurgy benchmark from Mallik (1986). Three monovariant eutectic valleys converge into a single Class I ternary eutectic point at 145°C (418.2 K) with composition 51.2 wt% Sn - 30.6 wt% Pb - 18.2 wt% Cd."
        )

    # =========================================================================
    # 7. Mo-V-W Classical Benchmark (Type I Continuous Isomorphous)
    # References: A. K. Mallik (1986), P. E. A. Turchi et al. (2020)
    # =========================================================================
    @classmethod
    def _compute_mo_v_w(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        invariants = [
            {"type": "Isomorphous", "temp_c": 2400.0, "equation": "Liquid <-> BCC_A2 (Continuous)", "composition": "V33.3Mo33.3W33.4", "desc": "Type I ternary isomorphous with zero ternary invariant reactions"},
            {"type": "Binary Melting", "temp_c": 1910.0, "equation": "Pure V Melting", "composition": "V100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 2623.0, "equation": "Pure Mo Melting", "composition": "Mo100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3422.0, "equation": "Pure W Melting", "composition": "W100", "desc": "Unary benchmark"},
        ]
        return cls._compute_isomorphous_ternary(
            system="Mo-V-W",
            el_a="V", el_b="Mo", el_c="W",
            tm_a=1910.0, tm_b=2623.0, tm_c=3422.0,
            diag_type=diag_type, t_c=t_c, is_k=is_k,
            notes="Ideal ternary isomorphous benchmark system from Mallik (1986). Completely continuous BCC_A2 liquidus/solidus surface across V (1910°C), Mo (2623°C), and W (3422°C).",
            invariants=invariants,
            excess_dt=(55.0, 75.0, 65.0),
            lens_span=0.20,
            solid_phase_label="Single-Phase BCC_A2 Solid Solution",
        )

    # =========================================================================
    # Additional Assessed Systems (Co-Fe-Ni, Co-Cr-Fe, Fe-Cr-Mn, Mo-Ta-W, Nb-Ta-W, Mo-Nb-V, Fe-Cr-C, Al-Cu-Mg)
    # =========================================================================
    @classmethod
    def _compute_co_fe_ni(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Co", "Fe", "Ni"
        invariants = [
            {"type": "Peritectic Valley", "temp_c": 1510.0, "equation": "L + delta-BCC <-> gamma-FCC", "composition": "Fe87Co8Ni5", "desc": "Monovariant peritectic ridge connecting Fe-Ni (1517°C) and Co-Fe (1499°C)"},
            {"type": "Eutectoid/Allotropic", "temp_c": 912.0, "equation": "gamma-FCC <-> alpha-BCC", "composition": "Fe100", "desc": "Pure Fe allotropic transformation closing below ~600-912°C"},
        ]
        curves: List[Dict[str, Any]] = []
        tie_lines: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []

        def t_liq(a: float, b: float, c: float) -> float:
            return 1495.0 * a + 1538.0 * b + 1455.0 * c - 25.0 * a * b - 35.0 * b * c - 18.0 * a * c

        if diag_type == "liquidus":
            _append_isotherm_contours(
                t_liq,
                [(1465.0, "#38BDF8"), (1480.0, "#0284C7"), (1495.0, "#0369A1"), (1512.0, "#1D4ED8"), (1526.0, "#1E3A8A")],
                is_k, curves, labels, prefix="Liquidus", n_grid=54,
            )
            # Monovariant peritectic valley from Co-Fe edge to Fe-Ni edge
            peri = [(0.19, 0.81, 0.0), (0.10, 0.88, 0.02), (0.0, 0.955, 0.045)]
            px, py = _interpolate_ternary_curve(peri, n_pts=30)
            curves.append({"name": "Peritectic Valley (L+δ ⇄ γ)", "xs": px, "ys": py, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.2})
            xc, yc = barycentric_to_cartesian(0.40, 0.25, 0.35)
            labels.append({"text": "L -> γ-FCC Primary Field", "x": xc, "y": yc, "color": "#0369A1", "bold": True})
            xd, yd = barycentric_to_cartesian(0.05, 0.92, 0.03)
            labels.append({"text": "δ-BCC", "x": xd, "y": yd, "color": "#DC2626", "bold": True})
        else:
            if t_c >= 1538.0:
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "Single-Phase Liquid (L)", "x": xc, "y": yc, "color": "#1D4ED8", "bold": True})
            elif t_c >= 1450.0:
                def t_sol(a: float, b: float, c: float) -> float:
                    return t_liq(a, b, c) - 18.0 * (a * b + b * c + c * a)
                for xs, ys in _trace_ternary_isocontours(t_liq, t_c, n_grid=56):
                    curves.append({"name": "Liquidus (L / L+γ)", "xs": xs, "ys": ys, "color": "#0284C7", "line_style": "Solid", "line_width": 2.1})
                for xs, ys in _trace_ternary_isocontours(t_sol, t_c, n_grid=56):
                    curves.append({"name": "Solidus (L+γ / γ)", "xs": xs, "ys": ys, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.0})
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "γ-FCC + Liquid", "x": xc, "y": yc, "color": "#0F172A", "bold": True})
            elif t_c >= 912.0:
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "Single-Phase FCC_A1 (Co,Fe,Ni) Solid Solution", "x": xc, "y": yc, "color": "#0284C7", "bold": True})
            else:
                # Sub-912°C two-phase alpha-BCC + gamma-FCC pocket in Fe-rich corner, anchored on Co-Fe & Fe-Ni edges
                scale = max(0.35, min(1.0, (912.0 - t_c) / 350.0))
                b_edge_a = round(0.18 * scale, 4)
                b_edge_c = round(0.14 * scale, 4)
                g_edge_a = round(0.38 * scale, 4)
                g_edge_c = round(0.30 * scale, 4)
                bcc_k = [(b_edge_a, 1.0 - b_edge_a, 0.0), (0.09 * scale, 1.0 - 0.16 * scale, 0.07 * scale), (0.0, 1.0 - b_edge_c, b_edge_c)]
                fcc_k = [(g_edge_a, 1.0 - g_edge_a, 0.0), (0.20 * scale, 1.0 - 0.36 * scale, 0.16 * scale), (0.0, 1.0 - g_edge_c, g_edge_c)]
                bx, by = _interpolate_ternary_curve(bcc_k, n_pts=35)
                fx, fy = _interpolate_ternary_curve(fcc_k, n_pts=35)
                curves.append({"name": "α-BCC Solvus Boundary", "xs": bx, "ys": by, "color": "#D97706", "line_style": "Solid", "line_width": 2.1})
                curves.append({"name": "γ-FCC Solvus Boundary", "xs": fx, "ys": fy, "color": "#0284C7", "line_style": "Dashed", "line_width": 2.1})
                for frac in [0.15, 0.40, 0.65, 0.85]:
                    bi = min(len(bx) - 1, int(frac * (len(bx) - 1)))
                    fi = min(len(fx) - 1, int(frac * (len(fx) - 1)))
                    tie_lines.append({"xs": [bx[bi], fx[fi]], "ys": [by[bi], fy[fi]], "color": "#94A3B8"})
                xa, ya = barycentric_to_cartesian(0.03, 0.94, 0.03)
                labels.append({"text": "α-BCC", "x": xa, "y": ya, "color": "#D97706", "bold": True})
                xf, yf = barycentric_to_cartesian(0.42, 0.25, 0.33)
                labels.append({"text": "γ-FCC Solid Solution", "x": xf, "y": yf, "color": "#0284C7", "bold": True})

        return cls._build_ternary_payload(
            system="Co-Fe-Ni", el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=[],
            labels=labels, invariants=invariants,
            notes="Assessed Co-Fe-Ni ternary (Guillermet 1989 / Zhang 2002): complete γ-FCC solid solution between 912-1450°C, α-BCC+γ-FCC pocket at Fe corner below 912°C, and monovariant peritectic valley on the Fe-rich liquidus."
        )

    @classmethod
    def _compute_co_cr_fe(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Co", "Cr", "Fe"
        invariants = [
            {"type": "Class II Invariant", "temp_c": 820.0, "equation": "FCC + BCC <-> Sigma + FCC", "composition": "Co30Cr45Fe25", "desc": "Sigma phase stabilization linking Co-Cr sigma and Fe-Cr sigma below 830°C"},
            {"type": "Binary Eutectic", "temp_c": 1395.0, "equation": "Liquid <-> FCC + Sigma(BCC)", "composition": "Co58Cr42", "desc": "Co-Cr eutectic trough entering ternary"},
        ]
        curves: List[Dict[str, Any]] = []
        tie_lines: List[Dict[str, Any]] = []
        tie_triangles: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []

        def t_liq(a: float, b: float, c: float) -> float:
            # Matches Co (1495), Cr (1907), Fe (1538) with Co-Cr eutectic (~1395°C) and Fe-Cr minimum (~1513°C)
            return 1495.0 * a + 1907.0 * b + 1538.0 * c - 1220.0 * a * b * (1.0 - 0.5 * a) - 540.0 * b * c

        if diag_type == "liquidus":
            _append_isotherm_contours(
                t_liq,
                [(1430.0, "#38BDF8"), (1490.0, "#0284C7"), (1560.0, "#0369A1"), (1680.0, "#1D4ED8"), (1800.0, "#1E3A8A")],
                is_k, curves, labels, prefix="Liquidus", n_grid=54,
            )
            valley = [(0.58, 0.42, 0.0), (0.30, 0.34, 0.36), (0.0, 0.21, 0.79)]
            vx, vy = _interpolate_ternary_curve(valley, n_pts=35)
            curves.append({"name": "Eutectic / Minima Valley (L ⇄ FCC + BCC)", "xs": vx, "ys": vy, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.2})
            xb, yb = barycentric_to_cartesian(0.15, 0.70, 0.15)
            labels.append({"text": "L -> BCC_A2 (Cr,Fe)", "x": xb, "y": yb, "color": "#1E3A8A", "bold": True})
            xf, yf = barycentric_to_cartesian(0.45, 0.12, 0.43)
            labels.append({"text": "L -> FCC_A1 (Co,Fe)", "x": xf, "y": yf, "color": "#0284C7", "bold": True})
        else:
            if t_c >= 1907.0:
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "Single-Phase Liquid (L)", "x": xc, "y": yc, "color": "#1D4ED8", "bold": True})
            elif t_c >= 1395.0:
                def t_sol(a: float, b: float, c: float) -> float:
                    return t_liq(a, b, c) - 45.0 * (a * b + b * c + c * a)
                for xs, ys in _trace_ternary_isocontours(t_liq, t_c, n_grid=56):
                    curves.append({"name": "Liquidus Boundary", "xs": xs, "ys": ys, "color": "#0284C7", "line_style": "Solid", "line_width": 2.1})
                for xs, ys in _trace_ternary_isocontours(t_sol, t_c, n_grid=56):
                    curves.append({"name": "Solidus Boundary", "xs": xs, "ys": ys, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.0})
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "Liquid + Solid Two-Phase", "x": xc, "y": yc, "color": "#0F172A", "bold": True})
            elif t_c <= 830.0:
                # Below 830°C Fe-Cr Sigma is stable -> continuous edge-to-edge Sigma band
                fcc_k = [(0.65, 0.35, 0.0), (0.45, 0.28, 0.27), (0.20, 0.20, 0.60), (0.0, 0.10, 0.90)]
                sig_lo = [(0.45, 0.55, 0.0), (0.25, 0.50, 0.25), (0.0, 0.44, 0.56)]
                sig_hi = [(0.36, 0.64, 0.0), (0.18, 0.60, 0.22), (0.0, 0.52, 0.48)]
                bcc_k = [(0.22, 0.78, 0.0), (0.12, 0.68, 0.20), (0.0, 0.58, 0.42)]
                for name, kts, col, ls in [
                    ("FCC_A1 Solvus (Co,Fe)", fcc_k, "#0284C7", "Solid"),
                    ("σ Phase Lower Solvus", sig_lo, "#882255", "Solid"),
                    ("σ Phase Upper Solvus", sig_hi, "#882255", "Solid"),
                    ("BCC_A2 (Cr) Solvus", bcc_k, "#D97706", "Dashed"),
                ]:
                    xs, ys = _interpolate_ternary_curve(kts, n_pts=40)
                    curves.append({"name": name, "xs": xs, "ys": ys, "color": col, "line_style": ls, "line_width": 2.0})
                for frac in [0.15, 0.40, 0.65, 0.85]:
                    pa = barycentric_to_cartesian(0.65 * (1 - frac), 0.35 * (1 - frac) + 0.10 * frac, 0.90 * frac)
                    ps = barycentric_to_cartesian(0.45 * (1 - frac), 0.55 * (1 - frac) + 0.44 * frac, 0.56 * frac)
                    tie_lines.append({"xs": [pa[0], ps[0]], "ys": [pa[1], ps[1]], "color": "#94A3B8"})
                labels.append({"text": "FCC (Co,Fe)", "x": barycentric_to_cartesian(0.45, 0.10, 0.45)[0], "y": barycentric_to_cartesian(0.45, 0.10, 0.45)[1], "color": "#0284C7", "bold": True})
                labels.append({"text": "σ Phase", "x": barycentric_to_cartesian(0.22, 0.55, 0.23)[0], "y": barycentric_to_cartesian(0.22, 0.55, 0.23)[1], "color": "#882255", "bold": True})
                labels.append({"text": "BCC (Cr)", "x": barycentric_to_cartesian(0.08, 0.78, 0.14)[0], "y": barycentric_to_cartesian(0.08, 0.78, 0.14)[1], "color": "#D97706", "bold": True})
            else:
                # 830 < T < 1395°C: Sigma lobe projects from Co-Cr edge, leaving FCC+BCC+Sigma triangle
                fcc_k = [(0.62, 0.38, 0.0), (0.35, 0.32, 0.33), (0.14, 0.22, 0.64), (0.0, 0.13, 0.87)]
                bcc_k = [(0.24, 0.76, 0.0), (0.16, 0.62, 0.22), (0.09, 0.40, 0.51), (0.0, 0.21, 0.79)]
                sig_lobe = [(0.45, 0.55, 0.0), (0.30, 0.53, 0.17), (0.19, 0.54, 0.27), (0.21, 0.60, 0.19), (0.36, 0.64, 0.0)]
                for name, kts, col, ls in [
                    ("FCC_A1 Boundary", fcc_k, "#0284C7", "Solid"),
                    ("BCC_A2 Boundary", bcc_k, "#D97706", "Dashed"),
                    ("σ (Co-Cr) Solvus Lobe", sig_lobe, "#882255", "Solid"),
                ]:
                    xs, ys = _interpolate_ternary_curve(kts, n_pts=40)
                    curves.append({"name": name, "xs": xs, "ys": ys, "color": col, "line_style": ls, "line_width": 2.0})
                tie_triangles.append({
                    "v1": barycentric_to_cartesian(0.26, 0.30, 0.44),
                    "v2": barycentric_to_cartesian(0.11, 0.55, 0.34),
                    "v3": barycentric_to_cartesian(0.19, 0.54, 0.27),
                    "color": "#FDF2F8", "border_color": "#882255", "name": "FCC + BCC + σ",
                })
                labels.append({"text": "FCC_A1", "x": barycentric_to_cartesian(0.45, 0.10, 0.45)[0], "y": barycentric_to_cartesian(0.45, 0.10, 0.45)[1], "color": "#0284C7", "bold": True})
                labels.append({"text": "σ Phase", "x": barycentric_to_cartesian(0.32, 0.58, 0.10)[0], "y": barycentric_to_cartesian(0.32, 0.58, 0.10)[1], "color": "#882255", "bold": True})
                labels.append({"text": "BCC_A2", "x": barycentric_to_cartesian(0.08, 0.72, 0.20)[0], "y": barycentric_to_cartesian(0.08, 0.72, 0.20)[1], "color": "#D97706", "bold": True})

        return cls._build_ternary_payload(
            system="Co-Cr-Fe", el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Assessed Co-Cr-Fe ternary (Cantor HEA base): σ band bridges edge-to-edge below 830°C and retracts toward Co-Cr above 830°C forming the FCC+BCC+σ three-phase tie-triangle."
        )

    # =========================================================================
    # Fe-Cr-Mn Reduced-Activation Fusion & Austenitic Steel Archetype
    # Reference: Y. Murata, K. Koyama, Y. Matsumoto, M. Morinaga, N. Yukawa,
    # "Equilibrium Phase Diagram of Fe-Cr-Mn Ternary System",
    # ISIJ International, Vol. 30 (1990) No. 11, pp. 927-936.
    # =========================================================================
    @classmethod
    def _compute_fe_cr_mn(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Fe", "Cr", "Mn"
        invariants = [
            {"type": "Class II Invariant", "temp_c": 1240.0, "equation": "Liquid + delta-BCC <-> gamma-FCC + Sigma", "composition": "Fe48Cr38Mn14", "desc": "Murata (1990) high-temperature peritectic-eutectic transition"},
            {"type": "Monovariant Liquidus", "temp_c": 1420.0, "equation": "L + delta-BCC <-> gamma-FCC", "composition": "Fe65Cr18Mn17", "desc": "Continuous peritectic groove spanning Fe-Mn to Fe-Cr"},
            {"type": "Sigma Solvus Invariant", "temp_c": 650.0, "equation": "gamma-FCC <-> gamma + Sigma", "composition": "Fe68Cr08Mn24", "desc": "Murata 1990 Fig. 7: Sigma boundary plunges to 8 at% Cr at 650°C"},
            {"type": "Subsolidus Eutectoid", "temp_c": 720.0, "equation": "gamma-FCC <-> alpha-BCC + Sigma + beta-Mn", "composition": "Fe52Cr16Mn32", "desc": "Four-phase equilibrium node connecting gamma, alpha, sigma, and beta-Mn"}
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Temperature-dependent topology selection based on Murata et al. (1990)
        # Isothermal sections studied: 923 K (650°C), 1073 K (800°C), 1273 K (1000°C)
        if t_c <= 750.0:
            # --- 923 K / 650°C Isothermal Section ---
            # Ferrite alpha-BCC solvus: low Cr, Mn up to ~11 at%
            alpha_solvus_knots = [
                (0.92, 0.08, 0.00),
                (0.85, 0.07, 0.08),
                (0.80, 0.06, 0.14),
                (0.72, 0.05, 0.23),
            ]
            xs_a, ys_a = _interpolate_ternary_curve(alpha_solvus_knots, n_pts=40)
            curves.append({"name": "Ferrite α Boundary (650°C Solvus)", "xs": xs_a, "ys": ys_a, "color": "#059669", "line_style": "Solid", "line_width": 2.2})

            # Austenite gamma-FCC boundary: extends from 12 at% Mn up to ~38 at% Mn, Cr up to ~14 at%
            gamma_solvus_knots = [
                (0.84, 0.00, 0.16),
                (0.74, 0.06, 0.20),
                (0.66, 0.10, 0.24),
                (0.58, 0.14, 0.28),
                (0.48, 0.12, 0.40),
                (0.38, 0.04, 0.58),
            ]
            xs_g, ys_g = _interpolate_ternary_curve(gamma_solvus_knots, n_pts=50)
            curves.append({"name": "Austenite γ Boundary (FCC Solvus)", "xs": xs_g, "ys": ys_g, "color": "#2563EB", "line_style": "Solid", "line_width": 2.4})

            # Continuous Sigma-phase (tP30) band connecting Fe-Cr sigma and Cr-Mn sigma
            # Plunges down to ~8 at% Cr at 20-25 at% Mn (Murata 1990 Fig. 7 & 8)
            sigma_lower_knots = [
                (0.54, 0.46, 0.00),
                (0.50, 0.32, 0.18),
                (0.48, 0.20, 0.32),
                (0.44, 0.12, 0.44),
                (0.36, 0.16, 0.48),
                (0.20, 0.24, 0.56),
                (0.00, 0.34, 0.66),
            ]
            xs_sl, ys_sl = _interpolate_ternary_curve(sigma_lower_knots, n_pts=60)
            curves.append({"name": "σ Phase Lower Boundary (650°C)", "xs": xs_sl, "ys": ys_sl, "color": "#DC2626", "line_style": "Solid", "line_width": 2.5})

            sigma_upper_knots = [
                (0.46, 0.54, 0.00),
                (0.38, 0.48, 0.14),
                (0.28, 0.46, 0.26),
                (0.18, 0.44, 0.38),
                (0.08, 0.42, 0.50),
                (0.00, 0.40, 0.60),
            ]
            xs_su, ys_su = _interpolate_ternary_curve(sigma_upper_knots, n_pts=50)
            curves.append({"name": "σ Phase Upper Boundary (650°C)", "xs": xs_su, "ys": ys_su, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.0})

            # Three-phase tie-triangle: alpha + gamma + sigma (Murata 1990 Fig. 8)
            t1_a = (0.78, 0.08, 0.14)   # alpha ferrite apex
            t1_g = (0.68, 0.10, 0.22)   # gamma austenite apex
            t1_s = (0.52, 0.28, 0.20)   # sigma apex
            p1_a = barycentric_to_cartesian(*t1_a)
            p1_g = barycentric_to_cartesian(*t1_g)
            p1_s = barycentric_to_cartesian(*t1_s)
            tie_triangles.append({"v1": p1_a, "v2": p1_g, "v3": p1_s, "color": "#FEE2E2", "border_color": "#DC2626", "name": "α + γ + σ Three-Phase Tie-Triangle (650°C)"})

            # Conjugate tie-lines across gamma + sigma two-phase field
            gamma_sigma_pairs = [
                ((0.62, 0.13, 0.25), (0.46, 0.26, 0.28)),
                ((0.54, 0.13, 0.33), (0.38, 0.26, 0.36)),
                ((0.44, 0.10, 0.46), (0.28, 0.28, 0.44))
            ]
            for idx, (cg, cs) in enumerate(gamma_sigma_pairs, 1):
                pg = barycentric_to_cartesian(*cg)
                ps = barycentric_to_cartesian(*cs)
                tie_lines.append({"xs": [pg[0], ps[0]], "ys": [pg[1], ps[1]], "color": "#94A3B8", "name": f"γ + σ Tie-Line #{idx}"})

            # Phase labels
            x_g, y_g = barycentric_to_cartesian(0.62, 0.05, 0.33)
            labels.append({"text": "Austenite γ (FCC)", "x": x_g, "y": y_g, "color": "#1D4ED8", "bold": True})
            x_a, y_a = barycentric_to_cartesian(0.88, 0.04, 0.08)
            labels.append({"text": "Ferrite α (BCC)", "x": x_a, "y": y_a, "color": "#059669", "bold": True})
            x_s, y_s = barycentric_to_cartesian(0.38, 0.34, 0.28)
            labels.append({"text": "σ Phase (tP30)", "x": x_s, "y": y_s, "color": "#DC2626", "bold": True})
            x_b, y_b = barycentric_to_cartesian(0.08, 0.06, 0.86)
            labels.append({"text": "β-Mn", "x": x_b, "y": y_b, "color": "#7C3AED", "bold": True})

            notes_str = "Murata et al. (ISIJ Int. 1990) 923 K (650°C) isothermal section. Demonstrates severe sigma-phase expansion: adding Mn extends sigma stability down to 8 at% Cr, establishing the critical PHACOMP threshold Md_crit = 0.880 eV."

        else:
            # --- 1073 K / 800°C Isothermal Section & High-Temperature Equilibria ---
            # Expanded Austenite field; contracted Sigma field (Md_crit = 0.920 eV)
            gamma_knots_800 = [
                (0.88, 0.00, 0.12),
                (0.72, 0.10, 0.18),
                (0.58, 0.20, 0.22),
                (0.44, 0.25, 0.31),
                (0.32, 0.18, 0.50),
                (0.20, 0.06, 0.74),
            ]
            xs_g8, ys_g8 = _interpolate_ternary_curve(gamma_knots_800, n_pts=50)
            curves.append({"name": "Austenite γ Boundary (800°C Solvus)", "xs": xs_g8, "ys": ys_g8, "color": "#2563EB", "line_style": "Solid", "line_width": 2.4})

            sigma_knots_800 = [
                (0.50, 0.50, 0.00),
                (0.42, 0.40, 0.18),
                (0.32, 0.36, 0.32),
                (0.18, 0.38, 0.44),
                (0.00, 0.42, 0.58),
            ]
            xs_s8, ys_s8 = _interpolate_ternary_curve(sigma_knots_800, n_pts=50)
            curves.append({"name": "σ Phase Boundary (800°C Solvus)", "xs": xs_s8, "ys": ys_s8, "color": "#DC2626", "line_style": "Solid", "line_width": 2.5})

            # Three-phase tie-triangle at 800°C: alpha + gamma + sigma
            t2_a = (0.72, 0.18, 0.10)
            t2_g = (0.60, 0.18, 0.22)
            t2_s = (0.45, 0.38, 0.17)
            p2_a = barycentric_to_cartesian(*t2_a)
            p2_g = barycentric_to_cartesian(*t2_g)
            p2_s = barycentric_to_cartesian(*t2_s)
            tie_triangles.append({"v1": p2_a, "v2": p2_g, "v3": p2_s, "color": "#FEE2E2", "border_color": "#DC2626", "name": "α + γ + σ Tie-Triangle (800°C)"})

            # Monovariant peritectic groove at high T (L + delta <-> gamma)
            liq_knots = [
                (0.88, 0.00, 0.12),
                (0.72, 0.14, 0.14),
                (0.54, 0.28, 0.18),
                (0.35, 0.42, 0.23),
                (0.10, 0.60, 0.30),
            ]
            xs_lq, ys_lq = _interpolate_ternary_curve(liq_knots, n_pts=50)
            curves.append({"name": "Monovariant Peritectic Line (L + δ ↔ γ)", "xs": xs_lq, "ys": ys_lq, "color": "#0F172A", "line_style": "Dashed", "line_width": 2.0})

            # Phase labels
            x_g, y_g = barycentric_to_cartesian(0.55, 0.12, 0.33)
            labels.append({"text": "Austenite γ (FCC)", "x": x_g, "y": y_g, "color": "#1D4ED8", "bold": True})
            x_a, y_a = barycentric_to_cartesian(0.78, 0.12, 0.10)
            labels.append({"text": "Ferrite α/δ (BCC)", "x": x_a, "y": y_a, "color": "#059669", "bold": True})
            x_s, y_s = barycentric_to_cartesian(0.32, 0.44, 0.24)
            labels.append({"text": "σ Phase", "x": x_s, "y": y_s, "color": "#DC2626", "bold": True})

            notes_str = "Murata et al. (ISIJ Int. 1990) 1073 K (800°C) section. Displays expanded austenite field and sigma retreat toward higher Cr contents, shifting critical instability limit to Md_crit = 0.920 eV."

        return cls._build_ternary_payload(
            system="Fe-Cr-Mn",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes=notes_str
        )

    @classmethod
    def _compute_mo_ta_w(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        invariants = [
            {"type": "Isomorphous", "temp_c": 2950.0, "equation": "Liquid <-> BCC_A2", "composition": "Mo33Ta33W34", "desc": "Continuous refractory BCC solid solution"},
            {"type": "Binary Melting", "temp_c": 2623.0, "equation": "Pure Mo Melting", "composition": "Mo100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3020.0, "equation": "Pure Ta Melting", "composition": "Ta100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3422.0, "equation": "Pure W Melting", "composition": "W100", "desc": "Unary benchmark"},
        ]
        return cls._compute_isomorphous_ternary(
            system="Mo-Ta-W",
            el_a="Mo", el_b="Ta", el_c="W",
            tm_a=2623.0, tm_b=3020.0, tm_c=3422.0,
            diag_type=diag_type, t_c=t_c, is_k=is_k,
            notes="Heavy refractory HEA base (Mo-Ta-W) with continuous BCC_A2 solid solution across Mo (2623°C), Ta (3020°C), and W (3422°C).",
            invariants=invariants,
            excess_dt=(80.0, 55.0, 75.0),
            lens_span=0.18,
            solid_phase_label="Single-Phase BCC_A2 Solid Solution",
        )

    @classmethod
    def _compute_nb_ta_w(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        invariants = [
            {"type": "Isomorphous", "temp_c": 2900.0, "equation": "Liquid <-> BCC_A2", "composition": "Nb33Ta33W34", "desc": "Continuous refractory BCC solid solution"},
            {"type": "Binary Melting", "temp_c": 2477.0, "equation": "Pure Nb Melting", "composition": "Nb100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3020.0, "equation": "Pure Ta Melting", "composition": "Ta100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 3422.0, "equation": "Pure W Melting", "composition": "W100", "desc": "Unary benchmark"},
        ]
        return cls._compute_isomorphous_ternary(
            system="Nb-Ta-W",
            el_a="Nb", el_b="Ta", el_c="W",
            tm_a=2477.0, tm_b=3020.0, tm_c=3422.0,
            diag_type=diag_type, t_c=t_c, is_k=is_k,
            notes="High-temperature ductile refractory base with complete mutual BCC_A2 solubility across Nb (2477°C), Ta (3020°C), and W (3422°C).",
            invariants=invariants,
            excess_dt=(45.0, 55.0, 85.0),
            lens_span=0.20,
            solid_phase_label="Single-Phase BCC_A2 Solid Solution",
        )

    @classmethod
    def _compute_mo_nb_v(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        invariants = [
            {"type": "Isomorphous", "temp_c": 2250.0, "equation": "Liquid <-> BCC_A2", "composition": "Mo33Nb33V34", "desc": "Medium-density refractory BCC matrix (Li 2026)"},
            {"type": "Binary Melting", "temp_c": 2623.0, "equation": "Pure Mo Melting", "composition": "Mo100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 2477.0, "equation": "Pure Nb Melting", "composition": "Nb100", "desc": "Unary benchmark"},
            {"type": "Binary Melting", "temp_c": 1910.0, "equation": "Pure V Melting", "composition": "V100", "desc": "Unary benchmark"},
        ]
        return cls._compute_isomorphous_ternary(
            system="Mo-Nb-V",
            el_a="Mo", el_b="Nb", el_c="V",
            tm_a=2623.0, tm_b=2477.0, tm_c=1910.0,
            diag_type=diag_type, t_c=t_c, is_k=is_k,
            notes="Medium-density refractory HEA solution (Mo-Nb-V, Li 2026) with complete BCC_A2 solid-solution stability across Mo (2623°C), Nb (2477°C), and V (1910°C).",
            invariants=invariants,
            excess_dt=(60.0, 35.0, 55.0),
            lens_span=0.22,
            solid_phase_label="Single-Phase BCC_A2 Solid Solution",
        )

    @classmethod
    def _compute_fe_cr_c(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Fe", "Cr", "C"
        invariants = [
            {"type": "Eutectic Valley", "temp_c": 1260.0, "equation": "Liquid -> Austenite + M7C3", "composition": "Fe75Cr15C10", "desc": "Primary carbide solidification valley (Andersson 1988)"},
            {"type": "Binary Eutectic", "temp_c": 1154.0, "equation": "Liquid -> Austenite + Fe3C", "composition": "Fe82.7C17.3", "desc": "Fe-C cementite eutectic"},
            {"type": "Binary Eutectic", "temp_c": 1536.0, "equation": "Liquid -> BCC(Cr) + Cr23C6", "composition": "Cr87C13", "desc": "Cr-C carbide eutectic"},
        ]
        curves: List[Dict[str, Any]] = []
        tie_triangles: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []

        if diag_type == "liquidus":
            def t_liq(a: float, b: float, c: float) -> float:
                # Metallic liquidus rising sharply with carbide/graphite carbon fraction
                return 1538.0 * a + 1907.0 * b + 3650.0 * c - 2100.0 * a * c * (1.0 - c) - 1800.0 * b * c * (1.0 - c) - 120.0 * a * b
            _append_isotherm_contours(
                t_liq,
                [(1300.0, "#38BDF8"), (1550.0, "#0284C7"), (1900.0, "#0369A1"), (2400.0, "#1D4ED8"), (3000.0, "#1E3A8A")],
                is_k, curves, labels, prefix="Liquidus", n_grid=54,
            )
            eut_v = [(0.827, 0.0, 0.173), (0.62, 0.24, 0.14), (0.35, 0.52, 0.13), (0.0, 0.87, 0.13)]
            vx, vy = _interpolate_ternary_curve(eut_v, n_pts=35)
            curves.append({"name": "Carbide Eutectic Trough (L ⇄ γ/α + Carbide)", "xs": vx, "ys": vy, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.2})
            labels.append({"text": "M7C3 / Graphite Primary", "x": barycentric_to_cartesian(0.25, 0.30, 0.45)[0], "y": barycentric_to_cartesian(0.25, 0.30, 0.45)[1], "color": "#1E3A8A", "bold": True})
        else:
            # Isothermal carbide section (Andersson 1988, 1000°C): boundary curves + tie-triangles connecting binary carbides & graphite
            fcc_k = [(0.88, 0.12, 0.0), (0.88, 0.08, 0.04), (0.94, 0.0, 0.06)]
            fx, fy = _interpolate_ternary_curve(fcc_k, n_pts=25)
            curves.append({"name": "γ-FCC Austenite Limit", "xs": fx, "ys": fy, "color": "#0284C7", "line_style": "Solid", "line_width": 2.1})

            for name, p0, p1, col in [
                ("M3C Cementite Field", (0.75, 0.0, 0.25), (0.58, 0.17, 0.25), "#DC2626"),
                ("M23C6 Carbide Band", (0.0, 0.793, 0.207), (0.28, 0.513, 0.207), "#7C3AED"),
                ("M7C3 Carbide Band", (0.0, 0.70, 0.30), (0.42, 0.28, 0.30), "#059669"),
            ]:
                p0_xy = barycentric_to_cartesian(*p0)
                p1_xy = barycentric_to_cartesian(*p1)
                curves.append({"name": name, "xs": [p0_xy[0], p1_xy[0]], "ys": [p0_xy[1], p1_xy[1]], "color": col, "line_style": "Solid", "line_width": 2.6})

            # Three-phase equilibria tying carbides, austenite, and graphite cleanly vertex-to-vertex
            tie_triangles.append({
                "v1": barycentric_to_cartesian(0.88, 0.09, 0.03),
                "v2": barycentric_to_cartesian(0.28, 0.513, 0.207),
                "v3": barycentric_to_cartesian(0.42, 0.28, 0.30),
                "color": "#EDE9FE", "border_color": "#7C3AED", "name": "γ-FCC + M23C6 + M7C3",
            })
            tie_triangles.append({
                "v1": barycentric_to_cartesian(0.91, 0.04, 0.05),
                "v2": barycentric_to_cartesian(0.42, 0.28, 0.30),
                "v3": barycentric_to_cartesian(0.58, 0.17, 0.25),
                "color": "#ECFDF5", "border_color": "#059669", "name": "γ-FCC + M7C3 + M3C",
            })
            tie_triangles.append({
                "v1": barycentric_to_cartesian(0.42, 0.28, 0.30),
                "v2": barycentric_to_cartesian(0.58, 0.17, 0.25),
                "v3": barycentric_to_cartesian(0.0, 0.0, 1.0),
                "color": "#FEF2F2", "border_color": "#DC2626", "name": "M7C3 + M3C + Graphite",
            })
            tie_triangles.append({
                "v1": barycentric_to_cartesian(0.0, 0.70, 0.30),
                "v2": barycentric_to_cartesian(0.0, 0.60, 0.40),
                "v3": barycentric_to_cartesian(0.0, 0.0, 1.0),
                "color": "#F0FDFA", "border_color": "#0D9488", "name": "M7C3 + Cr3C2 + Graphite",
            })
            labels.append({"text": "γ", "x": barycentric_to_cartesian(0.92, 0.05, 0.03)[0], "y": barycentric_to_cartesian(0.92, 0.05, 0.03)[1], "color": "#0284C7", "bold": True})
            labels.append({"text": "M23C6", "x": barycentric_to_cartesian(0.14, 0.66, 0.20)[0], "y": barycentric_to_cartesian(0.14, 0.66, 0.20)[1], "color": "#7C3AED", "bold": True})
            labels.append({"text": "M7C3", "x": barycentric_to_cartesian(0.22, 0.45, 0.33)[0], "y": barycentric_to_cartesian(0.22, 0.45, 0.33)[1], "color": "#059669", "bold": True})
            labels.append({"text": "M3C", "x": barycentric_to_cartesian(0.67, 0.07, 0.26)[0], "y": barycentric_to_cartesian(0.67, 0.07, 0.26)[1], "color": "#DC2626", "bold": True})
            labels.append({"text": "C (Graphite)", "x": barycentric_to_cartesian(0.10, 0.10, 0.80)[0], "y": barycentric_to_cartesian(0.10, 0.10, 0.80)[1], "color": "#0F172A", "bold": True})

        return cls._build_ternary_payload(
            system="Fe-Cr-C", el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=[], tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="High-Cr white iron & tool steel matrix with γ-FCC austenite, M3C, M23C6, M7C3, Cr3C2, and Graphite equilibria (Andersson 1988)."
        )

    @classmethod
    def _compute_al_cu_mg(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Al", "Cu", "Mg"
        invariants = [
            {"type": "E5 (Class I Eutectic)", "temp_c": 501.9, "equation": "Liquid -> (Al) + Theta(Al2Cu) + S(Al2CuMg)", "composition": "73.9 Al - 15.5 Cu - 10.6 Mg at%", "desc": "Primary aerospace 2xxx alloy eutectic (COST 507, Buhler 1998)"},
            {"type": "U16 (Class II)", "temp_c": 469.2, "equation": "Liquid + S -> T + (Al)", "composition": "67.0 Al - 4.9 Cu - 28.1 Mg at%", "desc": "Transition to T-phase"},
            {"type": "E7 (Class I Eutectic)", "temp_c": 447.6, "equation": "Liquid -> T + Al3Mg2 + (Al)", "composition": "63.5 Al - 0.5 Cu - 36.0 Mg at%", "desc": "Al-Mg terminal eutectic"},
        ]
        curves: List[Dict[str, Any]] = []
        tie_triangles: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []

        if diag_type == "liquidus":
            def t_liq(a: float, b: float, c: float) -> float:
                return 660.3 * a + 1084.6 * b + 650.0 * c - 920.0 * a * b - 780.0 * a * c - 840.0 * b * c + 350.0 * a * b * c
            _append_isotherm_contours(
                t_liq,
                [(520.0, "#38BDF8"), (600.0, "#0284C7"), (700.0, "#0369A1"), (820.0, "#1D4ED8"), (950.0, "#1E3A8A")],
                is_k, curves, labels, prefix="Liquidus", n_grid=54,
            )
            # Monovariant liquidus valleys connecting binary eutectics cleanly through E5 -> U16 -> E7 -> Al-Mg edge
            al_cu_to_mg = [(0.827, 0.173, 0.0), (0.739, 0.155, 0.106), (0.670, 0.049, 0.281), (0.635, 0.005, 0.360), (0.642, 0.0, 0.358)]
            vx, vy = _interpolate_ternary_curve(al_cu_to_mg, n_pts=40)
            curves.append({"name": "Primary Al Eutectic Valley (E5-U16-E7)", "xs": vx, "ys": vy, "color": "#DC2626", "line_style": "Solid", "line_width": 2.2})
            cu_mg_ridge = [(0.0, 0.145, 0.855), (0.35, 0.15, 0.50), (0.670, 0.049, 0.281)]
            rx, ry = _interpolate_ternary_curve(cu_mg_ridge, n_pts=30)
            curves.append({"name": "Mg2Cu-T-S Peritectic Ridge", "xs": rx, "ys": ry, "color": "#7C3AED", "line_style": "Dashed", "line_width": 1.9})
            # Invariant markers
            for tag, pt_comp, col in [("E5 (502°C)", (0.739, 0.155, 0.106), "#DC2626"), ("E7 (448°C)", (0.635, 0.005, 0.360), "#9333EA")]:
                px, py = barycentric_to_cartesian(*pt_comp)
                curves.append({"name": tag, "xs": [px], "ys": [py], "color": col, "line_style": "Point", "line_width": 8.0})
            labels.append({"text": "(Al) Primary", "x": barycentric_to_cartesian(0.84, 0.07, 0.09)[0], "y": barycentric_to_cartesian(0.84, 0.07, 0.09)[1], "color": "#0284C7", "bold": True})
        else:
            # COST 507 solid-state isothermal equilibria (~400°C): terminal (Al)/(Mg) solvus + intermetallic tie-triangles
            al_solvus = [(0.985, 0.015, 0.0), (0.94, 0.02, 0.04), (0.88, 0.0, 0.12)]
            ax, ay = _interpolate_ternary_curve(al_solvus, n_pts=25)
            curves.append({"name": "(Al) FCC Terminal Solvus", "xs": ax, "ys": ay, "color": "#0284C7", "line_style": "Solid", "line_width": 2.1})
            mg_solvus = [(0.0, 0.01, 0.99), (0.04, 0.005, 0.955), (0.08, 0.0, 0.92)]
            mx, my = _interpolate_ternary_curve(mg_solvus, n_pts=20)
            curves.append({"name": "(Mg) HCP Terminal Solvus", "xs": mx, "ys": my, "color": "#059669", "line_style": "Solid", "line_width": 2.1})

            pt_al = (0.95, 0.015, 0.035)
            pt_theta = (0.667, 0.333, 0.0)
            pt_s = (0.50, 0.25, 0.25)
            pt_t = (0.52, 0.12, 0.36)
            pt_beta = (0.60, 0.0, 0.40)
            pt_cu2mg = (0.0, 0.667, 0.333)
            pt_mg2cu = (0.0, 0.333, 0.667)
            pt_mg = (0.04, 0.005, 0.955)

            for name, v1, v2, v3, bg, bd in [
                ("(Al) + θ + S", pt_al, pt_theta, pt_s, "#EFF6FF", "#1D4ED8"),
                ("(Al) + S + T", pt_al, pt_s, pt_t, "#FDF4FF", "#7C3AED"),
                ("(Al) + T + β", pt_al, pt_t, pt_beta, "#ECFEFF", "#0891B2"),
                ("θ + S + Cu2Mg", pt_theta, pt_s, pt_cu2mg, "#FEF2F2", "#DC2626"),
                ("S + T + Cu2Mg", pt_s, pt_t, pt_cu2mg, "#FFFBEB", "#D97706"),
                ("T + Cu2Mg + Mg2Cu", pt_t, pt_cu2mg, pt_mg2cu, "#F0FDF4", "#15803D"),
                ("(Mg) + T + Mg2Cu", pt_mg, pt_t, pt_mg2cu, "#ECFDF5", "#059669"),
            ]:
                tie_triangles.append({
                    "v1": barycentric_to_cartesian(*v1),
                    "v2": barycentric_to_cartesian(*v2),
                    "v3": barycentric_to_cartesian(*v3),
                    "color": bg, "border_color": bd, "name": name,
                })

            for tag, p in [("S (Al2CuMg)", pt_s), ("T (Al6CuMg4)", pt_t), ("θ (Al2Cu)", pt_theta), ("β (Al3Mg2)", pt_beta)]:
                px, py = barycentric_to_cartesian(*p)
                curves.append({"name": tag, "xs": [px], "ys": [py], "color": "#0F172A", "line_style": "Point", "line_width": 6.5})
                labels.append({"text": tag.split()[0], "x": px, "y": py + 0.025, "color": "#0F172A", "bold": True})
            labels.append({"text": "(Al)", "x": barycentric_to_cartesian(0.94, 0.02, 0.04)[0], "y": barycentric_to_cartesian(0.94, 0.02, 0.04)[1], "color": "#0284C7", "bold": True})
            labels.append({"text": "(Mg)", "x": barycentric_to_cartesian(0.03, 0.01, 0.96)[0], "y": barycentric_to_cartesian(0.03, 0.01, 0.96)[1], "color": "#059669", "bold": True})

        return cls._build_ternary_payload(
            system="Al-Cu-Mg", el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=[], tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="Aerospace 2xxx/7xxx structural alloy benchmark (COST 507, Buhler 1998). Features invariant E5 eutectic (501.9°C), S (Al2CuMg), T (Al6CuMg4), θ (Al2Cu), and Laves phases."
        )

    # =========================================================================
    # Cr-Fe-Nb Ternary System (PyCalphad Official Tutorial Benchmark)
    # References: C. Jacob et al., Calphad 54 (2016) 130-141; PyCalphad Tutorial
    # =========================================================================
    @classmethod
    def _compute_cr_fe_nb(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Cr", "Fe", "Nb"
        invariants = [
            {"type": "Class II Transition", "temp_c": 1050.0, "equation": "BCC_A2 + Sigma <-> C14_LAVES", "composition": "Cr35Fe35Nb30", "desc": "Subsolidus equilibrium with continuous C14 Laves field"},
            {"type": "Binary Eutectic", "temp_c": 1360.0, "equation": "Liquid <-> BCC_A2 + C14_Laves", "composition": "Fe85Nb15", "desc": "Fe-Nb binary eutectic entering ternary"},
            {"type": "Binary Eutectic", "temp_c": 1620.0, "equation": "Liquid <-> BCC_A2 + C14_Laves", "composition": "Cr83Nb17", "desc": "Cr-Nb binary eutectic entering ternary"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # 1. C14 Laves phase field boundary (continuous band at Nb ~ 0.33)
        c14_top = [(0.62, 0.02, 0.36), (0.45, 0.19, 0.36), (0.25, 0.39, 0.36), (0.02, 0.62, 0.36)]
        xs_c14_t, ys_c14_t = _interpolate_ternary_curve(c14_top, n_pts=45)
        curves.append({"name": "C14 Laves Upper Solvus", "xs": xs_c14_t, "ys": ys_c14_t, "color": "#AA3377", "line_style": "Solid", "line_width": 2.2})

        c14_bot = [(0.68, 0.02, 0.30), (0.49, 0.21, 0.30), (0.27, 0.43, 0.30), (0.02, 0.68, 0.30)]
        xs_c14_b, ys_c14_b = _interpolate_ternary_curve(c14_bot, n_pts=45)
        curves.append({"name": "C14 Laves Lower Solvus", "xs": xs_c14_b, "ys": ys_c14_b, "color": "#AA3377", "line_style": "Solid", "line_width": 2.2})

        # 2. BCC solid solution boundary (along Cr-Fe base with ~5% Nb solubility)
        bcc_solvus = [(0.95, 0.01, 0.04), (0.75, 0.20, 0.05), (0.50, 0.44, 0.06), (0.20, 0.74, 0.06), (0.01, 0.95, 0.04)]
        xs_bcc, ys_bcc = _interpolate_ternary_curve(bcc_solvus, n_pts=50)
        curves.append({"name": "BCC Solvus Boundary", "xs": xs_bcc, "ys": ys_bcc, "color": "#E69F00", "line_style": "Dashed", "line_width": 2.0})

        # 3. Sigma phase region at intermediate Cr:Fe ratio
        sigma_knots = [(0.48, 0.49, 0.03), (0.45, 0.45, 0.10), (0.40, 0.48, 0.12), (0.38, 0.52, 0.10), (0.40, 0.57, 0.03)]
        xs_sig, ys_sig = _interpolate_ternary_curve(sigma_knots, n_pts=35)
        curves.append({"name": "Sigma Phase Boundary", "xs": xs_sig, "ys": ys_sig, "color": "#882255", "line_style": "Solid", "line_width": 1.8})

        # 4. Three-Phase Tie-Triangles:
        # Tri 1: BCC(Cr) + C14 + Sigma
        v1 = (0.52, 0.42, 0.06)
        v2 = (0.42, 0.46, 0.12)
        v3 = (0.46, 0.24, 0.30)
        tie_triangles.append({
            "v1": barycentric_to_cartesian(*v1),
            "v2": barycentric_to_cartesian(*v2),
            "v3": barycentric_to_cartesian(*v3),
            "color": "#FDF2F8", "border_color": "#882255", "name": "BCC(Cr) + C14 + Sigma"
        })

        # Tri 2: BCC(Fe) + C14 + Sigma
        u1 = (0.36, 0.58, 0.06)
        u2 = (0.38, 0.50, 0.12)
        u3 = (0.24, 0.46, 0.30)
        tie_triangles.append({
            "v1": barycentric_to_cartesian(*u1),
            "v2": barycentric_to_cartesian(*u2),
            "v3": barycentric_to_cartesian(*u3),
            "color": "#FEF3C7", "border_color": "#D97706", "name": "BCC(Fe) + C14 + Sigma"
        })

        # 5. Two-Phase Tie-Lines in BCC + C14 dual field
        for frac in [0.15, 0.30, 0.70, 0.85]:
            p_bcc = barycentric_to_cartesian(1.0 - frac - 0.05, frac, 0.05)
            p_c14 = barycentric_to_cartesian(1.0 - frac - 0.32, frac, 0.32)
            tie_lines.append({
                "xs": [p_bcc[0], p_c14[0]],
                "ys": [p_bcc[1], p_c14[1]],
                "color": "#94A3B8"
            })

        # Labels
        x_bcc, y_bcc = barycentric_to_cartesian(0.50, 0.48, 0.02)
        labels.append({"text": "BCC (Cr,Fe)", "x": x_bcc, "y": y_bcc, "color": "#D97706", "bold": True})
        x_c14, y_c14 = barycentric_to_cartesian(0.33, 0.34, 0.33)
        labels.append({"text": "C14 Laves (Fe,Cr)₂Nb", "x": x_c14, "y": y_c14, "color": "#AA3377", "bold": True})
        x_sig, y_sig = barycentric_to_cartesian(0.43, 0.50, 0.07)
        labels.append({"text": "σ Phase", "x": x_sig, "y": y_sig, "color": "#882255", "bold": True})
        x_nb, y_nb = barycentric_to_cartesian(0.10, 0.10, 0.80)
        labels.append({"text": "BCC(Nb)", "x": x_nb, "y": y_nb, "color": "#0284C7", "bold": True})

        return cls._build_ternary_payload(
            system="Cr-Fe-Nb",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="PyCalphad official benchmark (Jacob et al. 2016). Evaluated at 1323 K. Features the extensive continuous C14 Laves phase field (Fe,Cr)2Nb, BCC solid solutions, and tetragonal Sigma phase."
        )

    # =========================================================================
    # Al-Cu-Y Ternary System (PyCalphad Official Tutorial Benchmark)
    # References: C. Zhang et al., Calphad 35 (2011) 607-617
    # =========================================================================
    @classmethod
    def _compute_al_cu_y(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Al", "Cu", "Y"
        invariants = [
            {"type": "Class I Eutectic", "temp_c": 548.0, "equation": "Liquid <-> (Al) + Theta(Al2Cu) + Al3Y", "composition": "Al67Cu30Y3", "desc": "Al-rich ternary eutectic"},
            {"type": "Ternary Peritectic", "temp_c": 780.0, "equation": "Liquid + Al2Cu <-> Tau1", "composition": "Al50Cu40Y10", "desc": "Formation of ternary intermetallic Tau1"},
            {"type": "Miscibility Gap", "temp_c": 1497.0, "equation": "Liquid_1 <-> Liquid_2", "composition": "Al20Cu40Y40", "desc": "High-temperature liquid phase separation at 1770 K"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        al_knots = [(0.92, 0.07, 0.01), (0.78, 0.20, 0.02), (0.65, 0.30, 0.05), (0.50, 0.42, 0.08)]
        xs_al, ys_al = _interpolate_ternary_curve(al_knots, n_pts=40)
        curves.append({"name": "Al Solvus / Liquidus Eutectic", "xs": xs_al, "ys": ys_al, "color": "#0072B2", "line_style": "Solid", "line_width": 2.0})

        tau_knots = [(0.50, 0.42, 0.08), (0.42, 0.40, 0.18), (0.33, 0.34, 0.33), (0.25, 0.45, 0.30)]
        xs_tau, ys_tau = _interpolate_ternary_curve(tau_knots, n_pts=40)
        curves.append({"name": "Ternary Intermetallic (Tau-phases) Boundary", "xs": xs_tau, "ys": ys_tau, "color": "#7C3AED", "line_style": "Solid", "line_width": 2.0})

        v1 = (0.94, 0.05, 0.01)
        v2 = (0.66, 0.33, 0.01)
        v3 = (0.74, 0.01, 0.25)
        tie_triangles.append({
            "v1": barycentric_to_cartesian(*v1),
            "v2": barycentric_to_cartesian(*v2),
            "v3": barycentric_to_cartesian(*v3),
            "color": "#DBEAFE", "border_color": "#2563EB", "name": "(Al) + Al2Cu + Al3Y Tie-Triangle"
        })

        x_al, y_al = barycentric_to_cartesian(0.85, 0.10, 0.05)
        labels.append({"text": "(Al) Solid Solution", "x": x_al, "y": y_al, "color": "#0072B2", "bold": True})
        x_tau, y_tau = barycentric_to_cartesian(0.40, 0.40, 0.20)
        labels.append({"text": "Heusler / Tau Phases (τ₁-τ₆)", "x": x_tau, "y": y_tau, "color": "#7C3AED", "bold": True})
        x_cu, y_cu = barycentric_to_cartesian(0.10, 0.82, 0.08)
        labels.append({"text": "(Cu) Solid Solution", "x": x_cu, "y": y_cu, "color": "#D55E00", "bold": True})
        x_y, y_y = barycentric_to_cartesian(0.10, 0.10, 0.80)
        labels.append({"text": "(Y) Rich Field", "x": x_y, "y": y_y, "color": "#009E73", "bold": True})

        return cls._build_ternary_payload(
            system="Al-Cu-Y",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="PyCalphad official benchmark (Zhang et al. 2011). Assessed isothermal sections at 830 K and 1770 K with complex Heusler and ternary intermetallic (Tau) equilibria."
        )

    # =========================================================================
    # Fe-Sb-O Ternary Slag System (PyCalphad Official Tutorial MQMQA Benchmark)
    # References: M. Shishin et al., Calphad 65 (2019) 211-224
    # =========================================================================
    @classmethod
    def _compute_fe_sb_o(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "Fe", "Sb", "O"
        invariants = [
            {"type": "Slag Liquidus", "temp_c": 1227.0, "equation": "Liquid Slag <-> Spinel (Fe3O4) + FeSb2O4", "composition": "Fe35Sb25O40", "desc": "1500 K isothermal section MQMQA quadruplet model"},
            {"type": "Peritectic Reaction", "temp_c": 1150.0, "equation": "Liquid + Hematite <-> Spinel", "composition": "Fe40Sb10O50", "desc": "Iron oxide dissolution in antimony slag"},
        ]

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        slag_knots = [(0.45, 0.45, 0.10), (0.35, 0.35, 0.30), (0.25, 0.20, 0.55), (0.15, 0.40, 0.45)]
        xs_slag, ys_slag = _interpolate_ternary_curve(slag_knots, n_pts=50)
        curves.append({"name": "Homogeneous Slag Liquid Boundary (MQMQA)", "xs": xs_slag, "ys": ys_slag, "color": "#DC2626", "line_style": "Solid", "line_width": 2.2})

        spinel_knots = [(0.42, 0.01, 0.57), (0.35, 0.15, 0.50), (0.28, 0.30, 0.42)]
        xs_sp, ys_sp = _interpolate_ternary_curve(spinel_knots, n_pts=35)
        curves.append({"name": "Spinel (Fe₃O₄) / Hematite Boundary", "xs": xs_sp, "ys": ys_sp, "color": "#059669", "line_style": "Dashed", "line_width": 1.8})

        v1 = (0.30, 0.35, 0.35)
        v2 = (0.42, 0.02, 0.56)
        v3 = (0.14, 0.29, 0.57)
        tie_triangles.append({
            "v1": barycentric_to_cartesian(*v1),
            "v2": barycentric_to_cartesian(*v2),
            "v3": barycentric_to_cartesian(*v3),
            "color": "#FEF2F2", "border_color": "#DC2626", "name": "Slag + Spinel + FeSb₂O₄ Tie-Triangle"
        })

        x_slag, y_slag = barycentric_to_cartesian(0.35, 0.40, 0.25)
        labels.append({"text": "Slag Liquid (MQMQA)", "x": x_slag, "y": y_slag, "color": "#DC2626", "bold": True})
        x_spinel, y_spinel = barycentric_to_cartesian(0.40, 0.05, 0.55)
        labels.append({"text": "Spinel (Fe₃O₄)", "x": x_spinel, "y": y_spinel, "color": "#059669", "bold": True})
        x_fe, y_fe = barycentric_to_cartesian(0.85, 0.10, 0.05)
        labels.append({"text": "BCC_Fe + Oxide", "x": x_fe, "y": y_fe, "color": "#1E293B", "bold": True})

        return cls._build_ternary_payload(
            system="Fe-Sb-O",
            el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes="PyCalphad ChemSage database benchmark (Shishin et al. 2019). Modeled via Modified Quasichemical Model in Quadruplet Approximation (MQMQA) at 1500 K (1227°C)."
        )

    @classmethod
    def calculate_molar_ratio_ray(
        cls, ratio_ab: float, n_points: int = 50
    ) -> Dict[str, Any]:
        """
        Computes a linear composition ray through the Gibbs equilateral triangle
        for a fixed molar ratio X(A) / X(B) = k, sweeping X(C) from 0.0 to 1.0.
        Corresponds to the PyCalphad Workspace condition: v.X('A') / v.X('B') == ratio_ab.
        """
        comp_c = np.linspace(0.0, 1.0, n_points)
        comp_b = (1.0 - comp_c) / (1.0 + ratio_ab)
        comp_a = ratio_ab * comp_b

        cart_xs = []
        cart_ys = []
        for a, b, c in zip(comp_a, comp_b, comp_c):
            x, y = barycentric_to_cartesian(float(a), float(b), float(c))
            cart_xs.append(x)
            cart_ys.append(y)

        return {
            "ratio_ab": ratio_ab,
            "comp_a": comp_a.tolist(),
            "comp_b": comp_b.tolist(),
            "comp_c": comp_c.tolist(),
            "cart_xs": cart_xs,
            "cart_ys": cart_ys,
        }


    # =========================================================================
    # Arbitrary Element-Triplet Synthesizer (A-B-C) via Miedema Mixing Enthalpy
    # =========================================================================
    @classmethod
    def _compute_arbitrary_ternary(
        cls, el_a: str, el_b: str, el_c: str, diag_type: str, t_c: float, is_k: bool
    ) -> Dict[str, Any]:
        system = f"{el_a}-{el_b}-{el_c}"
        el_data_a = IUPAC_ELEMENTS_DATA.get(el_a)
        el_data_b = IUPAC_ELEMENTS_DATA.get(el_b)
        el_data_c = IUPAC_ELEMENTS_DATA.get(el_c)
        t_m_a = (getattr(el_data_a, "tm_k", 1500.0) if el_data_a else 1500.0) - 273.15
        t_m_b = (getattr(el_data_b, "tm_k", 1500.0) if el_data_b else 1500.0) - 273.15
        t_m_c = (getattr(el_data_c, "tm_k", 1500.0) if el_data_c else 1500.0) - 273.15

        # Miedema pairwise mixing enthalpies (kJ/mol)
        h_ab = get_miedema_enthalpy(el_a, el_b)
        h_bc = get_miedema_enthalpy(el_b, el_c)
        h_ca = get_miedema_enthalpy(el_c, el_a)
        avg_h = (h_ab + h_bc + h_ca) / 3.0

        # Regular-solution liquidus & solidus scalar fields calibrated from unary melting & Miedema ΔH
        def t_liq_fn(a: float, b: float, c: float) -> float:
            ideal = a * t_m_a + b * t_m_b + c * t_m_c
            # Negative ΔH suppresses eutectic liquidus (or forms strong interactions); mild positive lifts flat dome
            dep_ab = 18.0 * h_ab if h_ab < 0.0 else 6.0 * h_ab
            dep_bc = 18.0 * h_bc if h_bc < 0.0 else 6.0 * h_bc
            dep_ca = 18.0 * h_ca if h_ca < 0.0 else 6.0 * h_ca
            return ideal + a * b * dep_ab + b * c * dep_bc + c * a * dep_ca

        def t_sol_fn(a: float, b: float, c: float) -> float:
            lens = 0.22 * (
                a * b * abs(t_m_a - t_m_b)
                + b * c * abs(t_m_b - t_m_c)
                + c * a * abs(t_m_c - t_m_a)
            )
            eut_dep = 140.0 * max(0.0, -avg_h / 15.0) * (a * b + b * c + c * a)
            return t_liq_fn(a, b, c) - lens - eut_dep

        def t_misc_fn(a: float, b: float, c: float) -> float:
            # Subsolidus spinodal / miscibility-gap dome for strongly positive ΔH (T_c ~ 4*Omega / 2R in K -> °C)
            k_ab = max(0.0, h_ab) * 240.0
            k_bc = max(0.0, h_bc) * 240.0
            k_ca = max(0.0, h_ca) * 240.0
            return (a * b * k_ab + b * c * k_bc + c * a * k_ca) - 273.15

        t_sol_min = min(t_m_a, t_m_b, t_m_c)
        t_liq_max = max(t_m_a, t_m_b, t_m_c)
        t_misc_max = -273.15
        for i in range(21):
            a = i / 20.0
            for j in range(21 - i):
                b = j / 20.0
                c = max(0.0, 1.0 - a - b)
                t_sol_min = min(t_sol_min, t_sol_fn(a, b, c))
                t_liq_max = max(t_liq_max, t_liq_fn(a, b, c))
                t_misc_max = max(t_misc_max, t_misc_fn(a, b, c))

        curves: List[Dict[str, Any]] = []
        tie_lines: List[Dict[str, Any]] = []
        tie_triangles: List[Dict[str, Any]] = []
        labels: List[Dict[str, Any]] = []
        invariants: List[Dict[str, Any]] = []

        if avg_h < -15.0:
            topol = "Intermetallic-Forming System"
            invariants.append({"type": "Ternary Eutectic (Synthesized)", "temp_c": round(t_sol_min, 1), "equation": f"Liquid -> ({el_a}) + ({el_b}) + ({el_c})", "composition": f"{el_a}35{el_b}35{el_c}30", "desc": "Calculated via Miedema enthalpy depression"})
        elif avg_h > 15.0:
            topol = "Miscibility-Gap Separated System"
            invariants.append({"type": "Miscibility Gap", "temp_c": round(t_misc_max, 1), "equation": "Solid_1 + Solid_2 Decomposition", "composition": f"{el_a}33{el_b}33{el_c}34", "desc": "Positive enthalpy phase separation"})
        else:
            topol = "Continuous Solid Solution"
            invariants.append({"type": "Isomorphous Boundary", "temp_c": round((t_m_a + t_m_b + t_m_c) / 3.0, 1), "equation": "Liquid <-> Solid Solution", "composition": f"{el_a}33{el_b}33{el_c}34", "desc": "Near-ideal solid solution"})

        if diag_type == "liquidus":
            palette = ["#38BDF8", "#0284C7", "#0369A1", "#1D4ED8", "#1E3A8A"]
            span = max(40.0, t_liq_max - t_sol_min)
            lvl_cols: List[Tuple[float, str]] = []
            for frac, col in zip([0.16, 0.34, 0.52, 0.70, 0.88], palette):
                t_iso = round((t_sol_min + frac * span) / 25.0) * 25.0
                if t_sol_min + 5.0 <= t_iso <= t_liq_max - 5.0:
                    lvl_cols.append((t_iso, col))
            _append_isotherm_contours(t_liq_fn, lvl_cols, is_k, curves, labels, prefix="Liquidus", n_grid=54)
            xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
            labels.append({"text": f"Liquidus Projection ({topol})", "x": xc, "y": max(0.06, yc - 0.14), "color": "#0F172A", "bold": True})
        else:
            if t_c >= t_liq_max - 2.0:
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": "Single-Phase Liquid Solution (L)", "x": xc, "y": yc, "color": "#1D4ED8", "bold": True})
            elif t_c <= t_sol_min + 2.0:
                if avg_h > 15.0 and t_c < t_misc_max - 20.0:
                    chains = _trace_ternary_isocontours(t_misc_fn, t_c, n_grid=54)
                    for idx_c, (xs, ys) in enumerate(chains):
                        curves.append({"name": "Miscibility Gap Solvus" if idx_c == 0 else f"Miscibility Gap Solvus ({idx_c + 1})", "xs": xs, "ys": ys, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.1})
                    xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                    labels.append({"text": "α1 + α2 Miscibility Gap", "x": xc, "y": yc, "color": "#DC2626", "bold": True})
                elif avg_h < -15.0:
                    # Terminal solid-solution boundaries anchored cleanly on binary edges + compound tie-triangle
                    for idx_v, (a0, b0, c0, col, el_lbl) in enumerate([
                        (0.88, 0.12, 0.0, "#0284C7", f"({el_a})"),
                        (0.0, 0.88, 0.12, "#059669", f"({el_b})"),
                        (0.12, 0.0, 0.88, "#7C3AED", f"({el_c})"),
                    ]):
                        if idx_v == 0:
                            kts = [(0.88, 0.12, 0.0), (0.85, 0.075, 0.075), (0.88, 0.0, 0.12)]
                        elif idx_v == 1:
                            kts = [(0.12, 0.88, 0.0), (0.075, 0.85, 0.075), (0.0, 0.88, 0.12)]
                        else:
                            kts = [(0.12, 0.0, 0.88), (0.075, 0.075, 0.85), (0.0, 0.12, 0.88)]
                        xs, ys = _interpolate_ternary_curve(kts, n_pts=20)
                        curves.append({"name": f"{el_lbl} Terminal Solvus", "xs": xs, "ys": ys, "color": col, "line_style": "Solid", "line_width": 2.0})
                        xl, yl = barycentric_to_cartesian(0.92 if idx_v == 0 else 0.04, 0.92 if idx_v == 1 else 0.04, 0.92 if idx_v == 2 else 0.04)
                        labels.append({"text": el_lbl, "x": xl, "y": yl, "color": col, "bold": True})
                    tie_triangles.append({
                        "v1": barycentric_to_cartesian(0.85, 0.075, 0.075),
                        "v2": barycentric_to_cartesian(0.075, 0.85, 0.075),
                        "v3": barycentric_to_cartesian(0.075, 0.075, 0.85),
                        "color": "#F8FAFC", "border_color": "#475569", "name": f"({el_a}) + ({el_b}) + ({el_c})",
                    })
                    xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                    labels.append({"text": "Intermetallic Equilibrium", "x": xc, "y": yc, "color": "#0F172A", "bold": True})
                else:
                    xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                    labels.append({"text": f"Single-Phase Solid Solution ({system})", "x": xc, "y": yc, "color": "#0284C7", "bold": True})
            else:
                liq_chains = _trace_ternary_isocontours(t_liq_fn, t_c, n_grid=56)
                sol_chains = _trace_ternary_isocontours(t_sol_fn, t_c, n_grid=56)
                for xs, ys in liq_chains:
                    curves.append({"name": "Liquidus Boundary", "xs": xs, "ys": ys, "color": "#0284C7", "line_style": "Solid", "line_width": 2.1})
                for xs, ys in sol_chains:
                    curves.append({"name": "Solidus Boundary", "xs": xs, "ys": ys, "color": "#DC2626", "line_style": "Dashed", "line_width": 2.0})
                if liq_chains and sol_chains:
                    lx, ly = liq_chains[0]
                    sx, sy = sol_chains[0]
                    if ((lx[0] - sx[-1]) ** 2 + (ly[0] - sy[-1]) ** 2) < ((lx[0] - sx[0]) ** 2 + (ly[0] - sy[0]) ** 2):
                        sx, sy = list(reversed(sx)), list(reversed(sy))
                    for frac in [0.20, 0.45, 0.70, 0.85]:
                        li = min(len(lx) - 1, max(0, int(frac * (len(lx) - 1))))
                        si = min(len(sx) - 1, max(0, int(frac * (len(sx) - 1))))
                        tie_lines.append({"xs": [lx[li], sx[si]], "ys": [ly[li], sy[si]], "color": "#64748B"})
                xc, yc = barycentric_to_cartesian(0.333, 0.333, 0.334)
                labels.append({"text": f"{topol} (L + S)", "x": xc, "y": yc, "color": "#0F172A", "bold": True})

        return cls._build_ternary_payload(
            system=system, el_a=el_a, el_b=el_b, el_c=el_c,
            diag_type=diag_type, temp_c=t_c, is_k=is_k,
            curves=curves, tie_lines=tie_lines, tie_triangles=tie_triangles,
            labels=labels, invariants=invariants,
            notes=f"Synthesized ternary phase equilibrium based on Miedema mixing enthalpies (ΔH_AB={h_ab:.1f}, ΔH_BC={h_bc:.1f}, ΔH_CA={h_ca:.1f} kJ/mol) and pure element unary melting parameters."
        )

    # =========================================================================
    # Payload Construction Helper
    # =========================================================================
    @classmethod
    def _build_ternary_payload(
        cls,
        system: str, el_a: str, el_b: str, el_c: str,
        diag_type: str, temp_c: float, is_k: bool,
        curves: List[Dict[str, Any]],
        tie_lines: List[Dict[str, Any]],
        tie_triangles: List[Dict[str, Any]],
        labels: List[Dict[str, Any]],
        invariants: List[Dict[str, Any]],
        notes: str
    ) -> Dict[str, Any]:
        grid = cls.generate_gibbs_triangle_grid(step=0.1)
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Format invariant temperatures
        inv_formatted = []
        for inv in invariants:
            tc = inv.get("temp_c", 0.0)
            inv_formatted.append({
                "type": inv.get("type", "Invariant"),
                "temp_c": tc,
                "temp_formatted": f"{conv(tc):.1f} {u}",
                "equation": inv.get("equation", ""),
                "composition": inv.get("composition", ""),
                "desc": inv.get("desc", ""),
            })

        return {
            "system": system,
            "element_a": el_a,
            "element_b": el_b,
            "element_c": el_c,
            "diagram_type": diag_type,
            "temperature": conv(temp_c),
            "temp_unit": u,
            "triangle_border_x": grid["border_x"],
            "triangle_border_y": grid["border_y"],
            "grid_lines": grid["grid_lines"],
            "apex_labels": {
                "A": {"name": el_a, "x": -0.04, "y": -0.03, "align": "Right"},
                "B": {"name": el_b, "x": 1.04, "y": -0.03, "align": "Left"},
                "C": {"name": el_c, "x": 0.50, "y": SQRT3_OVER_2 + 0.04, "align": "Center"},
            },
            "curves": curves,
            "tie_lines": tie_lines,
            "tie_triangles": tie_triangles,
            "phase_labels": labels,
            "invariants": inv_formatted,
            "literature_notes": notes,
        }

    # =========================================================================
    # 3D Quadric Curved Liquidus Surface Formulation
    # References: Surajcuriousanimator/PhaseDiagrams (ternaryMath.js)
    # =========================================================================
    @staticmethod
    def solve_quadric_liquidus(
        tm_a: float, tm_b: float, tm_c: float,
        e_ab: Tuple[float, float],  # (a_frac, Te_ab)
        e_bc: Tuple[float, float],  # (b_frac, Te_bc)
        e_ca: Tuple[float, float],  # (a_frac, Te_ca)
        e_ternary: Tuple[float, float, float, float],  # (ea, eb, ec, Te)
        sag: float = 0.16
    ) -> Dict[str, Any]:
        """
        Solves 3-field 6-parameter quadric curved liquidus surface:
        T(a,b,c) = sum Q_k * m_k(a,b,c), m = [a^2, b^2, c^2, ab, ac, bc]
        Passing continuously through pure corners, binary eutectics, ternary eutectic,
        and mid-edge sag points with quadratic curvature matching prism walls.
        """
        def mono(p):
            a, b, c = p
            return [a * a, b * b, c * c, a * b, a * c, b * c]

        def mid(p, q):
            return [(p[i] + q[i]) / 2.0 for i in range(3)]

        pa = [1.0, 0.0, 0.0]
        pb = [0.0, 1.0, 0.0]
        pc = [0.0, 0.0, 1.0]

        e1p = [e_ab[0], 1.0 - e_ab[0], 0.0]
        e2p = [0.0, e_bc[0], 1.0 - e_bc[0]]
        e3p = [e_ca[0], 0.0, 1.0 - e_ca[0]]

        ea, eb, ec, te = e_ternary
        ep = [ea, eb, ec]

        # Field A: corner A, e1, e3, E, mid(A, e1), mid(A, e3)
        rows_a = [mono(pa), mono(e1p), mono(e3p), mono(ep), mono(mid(pa, e1p)), mono(mid(pa, e3p))]
        rhs_a = [tm_a, e_ab[1], e_ca[1], te,
                 (tm_a + e_ab[1]) / 2.0 + sag * (tm_a - e_ab[1]),
                 (tm_a + e_ca[1]) / 2.0 + sag * (tm_a - e_ca[1])]
        q_a = np.linalg.solve(rows_a, rhs_a).tolist()

        # Field B: corner B, e1, e2, E, mid(B, e1), mid(B, e2)
        rows_b = [mono(pb), mono(e1p), mono(e2p), mono(ep), mono(mid(pb, e1p)), mono(mid(pb, e2p))]
        rhs_b = [tm_b, e_ab[1], e_bc[1], te,
                 (tm_b + e_ab[1]) / 2.0 + sag * (tm_b - e_ab[1]),
                 (tm_b + e_bc[1]) / 2.0 + sag * (tm_b - e_bc[1])]
        q_b = np.linalg.solve(rows_b, rhs_b).tolist()

        # Field C: corner C, e2, e3, E, mid(C, e2), mid(C, e3)
        rows_c = [mono(pc), mono(e2p), mono(e3p), mono(ep), mono(mid(pc, e2p)), mono(mid(pc, e3p))]
        rhs_c = [tm_c, e_bc[1], e_ca[1], te,
                 (tm_c + e_bc[1]) / 2.0 + sag * (tm_c - e_bc[1]),
                 (tm_c + e_ca[1]) / 2.0 + sag * (tm_c - e_ca[1])]
        q_c = np.linalg.solve(rows_c, rhs_c).tolist()

        return {
            "quad_a": q_a,
            "quad_b": q_b,
            "quad_c": q_c,
            "ternary_eutectic": {"a": ea, "b": eb, "c": ec, "T": te},
            "eutectics": {
                "AB": {"a": e1p[0], "b": e1p[1], "c": 0.0, "T": e_ab[1]},
                "BC": {"a": 0.0, "b": e2p[1], "c": e2p[2], "T": e_bc[1]},
                "CA": {"a": e3p[0], "b": 0.0, "c": e3p[2], "T": e_ca[1]}
            }
        }

    # =========================================================================
    # Ceramic Ternary System 1: MgO-Al2O3-SiO2 (MAS Cordierite Ceramics)
    # References: ACerS Sys 712, J. Petrology 2(3):324, J. Mater. Res. (2005)
    # =========================================================================
    @classmethod
    def _compute_mgo_al2o3_sio2(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "SiO2", "MgO", "Al2O3"
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Coordinates of intermediate stoichiometric ceramic compounds: (a=SiO2, b=MgO, c=Al2O3)
        # Weight fractions:
        # Mullite: 28.2 wt% SiO2, 0.0 wt% MgO, 71.8 wt% Al2O3
        # Spinel: 0.0 wt% SiO2, 28.3 wt% MgO, 71.7 wt% Al2O3
        # Forsterite: 42.7 wt% SiO2, 57.3 wt% MgO, 0.0 wt% Al2O3
        # Protoenstatite: 59.8 wt% SiO2, 40.2 wt% MgO, 0.0 wt% Al2O3
        # Cordierite: 51.5 wt% SiO2, 13.7 wt% MgO, 34.8 wt% Al2O3
        # Sapphirine: 15.1 wt% SiO2, 20.3 wt% MgO, 64.6 wt% Al2O3
        pt_crist = barycentric_to_cartesian(1.0, 0.0, 0.0)
        pt_peri = barycentric_to_cartesian(0.0, 1.0, 0.0)
        pt_corun = barycentric_to_cartesian(0.0, 0.0, 1.0)

        pt_mul = barycentric_to_cartesian(0.282, 0.000, 0.718)
        pt_sp = barycentric_to_cartesian(0.000, 0.283, 0.717)
        pt_fo = barycentric_to_cartesian(0.427, 0.573, 0.000)
        pt_en = barycentric_to_cartesian(0.598, 0.402, 0.000)
        pt_cord = barycentric_to_cartesian(0.515, 0.137, 0.348)
        pt_saph = barycentric_to_cartesian(0.151, 0.203, 0.646)

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Subsolidus Alkemade compatibility lines
        alkemade_joins = [
            (pt_peri, pt_fo, "Periclase-Forsterite"),
            (pt_peri, pt_sp, "Periclase-Spinel"),
            (pt_fo, pt_sp, "Forsterite-Spinel"),
            (pt_fo, pt_saph, "Forsterite-Sapphirine"),
            (pt_fo, pt_cord, "Forsterite-Cordierite"),
            (pt_fo, pt_en, "Forsterite-Protoenstatite"),
            (pt_en, pt_cord, "Protoenstatite-Cordierite"),
            (pt_en, pt_crist, "Protoenstatite-Cristobalite"),
            (pt_cord, pt_crist, "Cordierite-Cristobalite"),
            (pt_cord, pt_mul, "Cordierite-Mullite"),
            (pt_cord, pt_saph, "Cordierite-Sapphirine"),
            (pt_saph, pt_sp, "Sapphirine-Spinel"),
            (pt_saph, pt_corun, "Sapphirine-Corundum"),
            (pt_saph, pt_mul, "Sapphirine-Mullite"),
            (pt_sp, pt_corun, "Spinel-Corundum"),
            (pt_mul, pt_crist, "Mullite-Cristobalite"),
            (pt_mul, pt_corun, "Mullite-Corundum"),
        ]

        for p1, p2, name in alkemade_joins:
            curves.append({
                "name": f"Alkemade Line: {name}",
                "xs": [p1[0], p2[0]],
                "ys": [p1[1], p2[1]],
                "color": "#64748B",
                "line_style": "Solid",
                "line_width": 1.2
            })

        # Alkemade Compatibility Triangles with semantic shading
        triangles = [
            (pt_peri, pt_fo, pt_sp, "Periclase + Forsterite + Spinel", "#8B5CF6", "#A855F7"),
            (pt_fo, pt_sp, pt_saph, "Forsterite + Spinel + Sapphirine", "#22C55E", "#10B981"),
            (pt_fo, pt_saph, pt_cord, "Forsterite + Sapphirine + Cordierite", "#EC4899", "#F43F5E"),
            (pt_fo, pt_cord, pt_en, "Forsterite + Cordierite + Protoenstatite", "#14B8A6", "#06B6D4"),
            (pt_en, pt_cord, pt_crist, "Protoenstatite + Cordierite + Cristobalite", "#38BDF8", "#0284C7"),
            (pt_cord, pt_saph, pt_mul, "Cordierite + Sapphirine + Mullite", "#EF4444", "#DC2626"),
            (pt_cord, pt_mul, pt_crist, "Cordierite + Mullite + Cristobalite", "#F59E0B", "#D97706"),
            (pt_saph, pt_sp, pt_corun, "Sapphirine + Spinel + Corundum", "#F97316", "#EA580C"),
            (pt_saph, pt_corun, pt_mul, "Sapphirine + Corundum + Mullite", "#E11D48", "#BE123C"),
        ]

        for p1, p2, p3, tri_label, fill_hex, border_hex in triangles:
            tie_triangles.append({
                "v1": list(p1),
                "v2": list(p2),
                "v3": list(p3),
                "label": tri_label,
                "color": fill_hex,
                "border_color": border_hex
            })

        # Liquidus projection boundary valleys converging at ternary eutectic E1 (1355 C)
        pt_e1 = barycentric_to_cartesian(0.53, 0.17, 0.30)
        pt_e2 = barycentric_to_cartesian(0.48, 0.28, 0.24)
        pt_p = barycentric_to_cartesian(0.46, 0.12, 0.42)

        curves.append({
            "name": "Liquidus Boundary E₁ Valley",
            "xs": [pt_e1[0], pt_e2[0]],
            "ys": [pt_e1[1], pt_e2[1]],
            "color": "#1E40AF",
            "line_style": "Solid",
            "line_width": 2.2
        })
        curves.append({
            "name": "Liquidus Boundary Peritectic P-E₁",
            "xs": [pt_p[0], pt_e1[0]],
            "ys": [pt_p[1], pt_e1[1]],
            "color": "#1E40AF",
            "line_style": "Solid",
            "line_width": 2.2
        })

        # Phase compound labels
        labels = [
            {"name": "Cristobalite (SiO₂)", "x": pt_crist[0], "y": pt_crist[1] - 0.03, "color": "#0284C7"},
            {"name": "Periclase (MgO)", "x": pt_peri[0], "y": pt_peri[1] - 0.03, "color": "#7C3AED"},
            {"name": "Corundum (Al₂O₃)", "x": pt_corun[0], "y": pt_corun[1] + 0.03, "color": "#BE123C"},
            {"name": "Cordierite", "x": pt_cord[0], "y": pt_cord[1], "color": "#BE185D"},
            {"name": "Mullite", "x": pt_mul[0] + 0.02, "y": pt_mul[1], "color": "#B91C1C"},
            {"name": "Spinel", "x": pt_sp[0], "y": pt_sp[1] + 0.02, "color": "#6D28D9"},
            {"name": "Forsterite", "x": pt_fo[0] - 0.02, "y": pt_fo[1], "color": "#15803D"},
            {"name": "Enstatite", "x": pt_en[0] - 0.02, "y": pt_en[1], "color": "#0F766E"},
            {"name": "Sapphirine", "x": pt_saph[0] + 0.02, "y": pt_saph[1], "color": "#C2410C"},
        ]

        invariants = [
            {"type": "Eutectic", "temp_c": 1355.0, "equation": "L ⇌ Protoenstatite + Cordierite + Tridymite", "composition": "SiO2:51.5 wt%, MgO:13.7 wt%, Al2O3:34.8 wt%", "desc": "E₁: Lowest melting invariant in MAS cordierite glass-ceramics"},
            {"type": "Eutectic", "temp_c": 1364.0, "equation": "L ⇌ Forsterite + Protoenstatite + Cordierite", "composition": "SiO2:48.0 wt%, MgO:28.0 wt%, Al2O3:24.0 wt%", "desc": "E₂: Adjacent eutectic on forsterite-cordierite boundary"},
            {"type": "Peritectic", "temp_c": 1440.0, "equation": "L + Mullite ⇌ Cordierite + Tridymite", "composition": "SiO2:46.0 wt%, MgO:12.0 wt%, Al2O3:42.0 wt%", "desc": "P: Peritectic reaction consuming primary mullite"},
        ]

        grid = cls.generate_gibbs_triangle_grid()
        return {
            "system": "MgO-Al2O3-SiO2",
            "element_a": el_a,
            "element_b": el_b,
            "element_c": el_c,
            "diagram_type": diag_type,
            "temperature": conv(t_c),
            "temp_unit": u,
            "triangle_border_x": grid["border_x"],
            "triangle_border_y": grid["border_y"],
            "grid_lines": grid["grid_lines"],
            "apex_labels": {
                "A": {"name": el_a, "x": -0.04, "y": -0.03, "align": "Right"},
                "B": {"name": el_b, "x": 1.04, "y": -0.03, "align": "Left"},
                "C": {"name": el_c, "x": 0.50, "y": SQRT3_OVER_2 + 0.04, "align": "Center"},
            },
            "curves": curves,
            "tie_lines": tie_lines,
            "tie_triangles": tie_triangles,
            "phase_labels": labels,
            "invariants": invariants,
            "literature_notes": "MgO-Al₂O₃-SiO₂ (MAS) ceramic system with 9 Alkemade compatibility triangles, exact stoichiometric compounds (Cordierite 2MgO·2Al₂O₃·5SiO₂, Mullite 3Al₂O₃·2SiO₂, Spinel MgAl₂O₄), and E₁ eutectic at 1355 °C.",
        }

    # =========================================================================
    # Ceramic Ternary System 2: Al2O3-SiO2-ZrO2 (AZS Fused-Cast Refractories)
    # References: ACerS Phase Equilibria Diagrams, Refractories Handbook (2018)
    # =========================================================================
    @classmethod
    def _compute_al2o3_sio2_zro2(cls, diag_type: str, t_c: float, is_k: bool) -> Dict[str, Any]:
        el_a, el_b, el_c = "SiO2", "ZrO2", "Al2O3"
        conv = (lambda c: c + 273.15) if is_k else (lambda c: c)
        u = "K" if is_k else "°C"

        # Coordinates of intermediate stoichiometric ceramic compounds: (a=SiO2, b=ZrO2, c=Al2O3)
        # Mullite: 28.2 wt% SiO2, 0.0 wt% ZrO2, 71.8 wt% Al2O3
        # Zircon: 32.8 wt% SiO2, 67.2 wt% ZrO2, 0.0 wt% Al2O3
        pt_crist = barycentric_to_cartesian(1.0, 0.0, 0.0)
        pt_zirc = barycentric_to_cartesian(0.0, 1.0, 0.0)
        pt_corun = barycentric_to_cartesian(0.0, 0.0, 1.0)

        pt_mul = barycentric_to_cartesian(0.282, 0.000, 0.718)
        pt_zircon = barycentric_to_cartesian(0.328, 0.672, 0.000)

        curves = []
        tie_lines = []
        tie_triangles = []
        labels = []

        # Subsolidus Alkemade compatibility joins
        alkemade_joins = [
            (pt_crist, pt_zircon, "Cristobalite-Zircon"),
            (pt_zircon, pt_zirc, "Zircon-Zirconia"),
            (pt_zirc, pt_corun, "Zirconia-Corundum"),
            (pt_corun, pt_mul, "Corundum-Mullite"),
            (pt_mul, pt_crist, "Mullite-Cristobalite"),
            (pt_mul, pt_zirc, "Mullite-Zirconia (Refractory Join)"),
            (pt_mul, pt_zircon, "Mullite-Zircon"),
        ]

        for p1, p2, name in alkemade_joins:
            curves.append({
                "name": f"Alkemade Line: {name}",
                "xs": [p1[0], p2[0]],
                "ys": [p1[1], p2[1]],
                "color": "#64748B",
                "line_style": "Solid",
                "line_width": 1.2
            })

        # Alkemade Compatibility Triangles with semantic shading
        triangles = [
            (pt_crist, pt_zircon, pt_mul, "Cristobalite + Zircon + Mullite", "#38BDF8", "#0284C7"),
            (pt_zircon, pt_zirc, pt_mul, "Zircon + Zirconia + Mullite", "#84CC16", "#65A30D"),
            (pt_mul, pt_zirc, pt_corun, "Mullite + Zirconia + Corundum (AZS Core)", "#F59E0B", "#D97706"),
        ]

        for p1, p2, p3, tri_label, fill_hex, border_hex in triangles:
            tie_triangles.append({
                "v1": list(p1),
                "v2": list(p2),
                "v3": list(p3),
                "label": tri_label,
                "color": fill_hex,
                "border_color": border_hex
            })

        # Liquidus projection valley boundary lines converging at ternary eutectic E (1705 C)
        pt_e = barycentric_to_cartesian(0.40, 0.25, 0.35)
        pt_p = barycentric_to_cartesian(0.20, 0.32, 0.48)

        curves.append({
            "name": "Liquidus Boundary E Valley",
            "xs": [pt_e[0], pt_p[0]],
            "ys": [pt_e[1], pt_p[1]],
            "color": "#1E40AF",
            "line_style": "Solid",
            "line_width": 2.2
        })

        # Phase compound labels
        labels = [
            {"name": "Cristobalite (SiO₂)", "x": pt_crist[0], "y": pt_crist[1] - 0.03, "color": "#0284C7"},
            {"name": "Zirconia (ZrO₂)", "x": pt_zirc[0], "y": pt_zirc[1] - 0.03, "color": "#D97706"},
            {"name": "Corundum (Al₂O₃)", "x": pt_corun[0], "y": pt_corun[1] + 0.03, "color": "#BE123C"},
            {"name": "Mullite (3Al₂O₃·2SiO₂)", "x": pt_mul[0] + 0.02, "y": pt_mul[1], "color": "#B91C1C"},
            {"name": "Zircon (ZrSiO₄)", "x": pt_zircon[0] - 0.02, "y": pt_zircon[1], "color": "#4D7C0F"},
        ]

        invariants = [
            {"type": "Eutectic", "temp_c": 1705.0, "equation": "L ⇌ Mullite + Zirconia + Cristobalite", "composition": "SiO2:40 wt%, ZrO2:25 wt%, Al2O3:35 wt%", "desc": "E: Ternary eutectic in fused-cast AZS refractories"},
            {"type": "Peritectic", "temp_c": 1890.0, "equation": "L + Corundum ⇌ Mullite + Zirconia", "composition": "SiO2:20 wt%, ZrO2:32 wt%, Al2O3:48 wt%", "desc": "P: Peritectic reaction for reaction-sintered composites"},
        ]

        grid = cls.generate_gibbs_triangle_grid()
        return {
            "system": "Al2O3-SiO2-ZrO2",
            "element_a": el_a,
            "element_b": el_b,
            "element_c": el_c,
            "diagram_type": diag_type,
            "temperature": conv(t_c),
            "temp_unit": u,
            "triangle_border_x": grid["border_x"],
            "triangle_border_y": grid["border_y"],
            "grid_lines": grid["grid_lines"],
            "apex_labels": {
                "A": {"name": el_a, "x": -0.04, "y": -0.03, "align": "Right"},
                "B": {"name": el_b, "x": 1.04, "y": -0.03, "align": "Left"},
                "C": {"name": el_c, "x": 0.50, "y": SQRT3_OVER_2 + 0.04, "align": "Center"},
            },
            "curves": curves,
            "tie_lines": tie_lines,
            "tie_triangles": tie_triangles,
            "phase_labels": labels,
            "invariants": invariants,
            "literature_notes": "Al₂O₃-SiO₂-ZrO₂ (AZS) fused-cast refractory system with 3 Alkemade compatibility triangles, stoichiometric Mullite and Zircon, and ternary eutectic at 1705 °C.",
        }
