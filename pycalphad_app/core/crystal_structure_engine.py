# -*- coding: utf-8 -*-
"""
crystal_structure_engine.py - Interactive 3D Crystallographic & Atomic Configuration Engine

Generates unit-cell, supercell, Wyckoff sublattice occupancy, nearest-neighbour bond,
and slip-plane data for the crystal phases detected by the CALPHAD and alloy physics engines.
"""

import hashlib
import math
from typing import Any, Dict, List, Optional, Tuple

from pycalphad_app.core.elements_data import get_element
from pycalphad_app.database.imc_laves_database import IMCLavesDatabase


# Palette for sublattice-colouring mode (distinct academic colours for up to 6 Wyckoff sites)
SUBLATTICE_COLOURS = [
    "#2563EB",  # Site 0 - Cobalt Blue
    "#DC2626",  # Site 1 - Crimson Red
    "#059669",  # Site 2 - Emerald Green
    "#D97706",  # Site 3 - Amber
    "#7C3AED",  # Site 4 - Violet
    "#0891B2",  # Site 5 - Teal
]


def _frac_dist_sq(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    cell: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]],
) -> float:
    """Computes squared Euclidean distance in Angstroms between two Cartesian points."""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    dz = a[2] - b[2]
    _ = cell
    return dx * dx + dy * dy + dz * dz


def _mat_mul_vec(
    cell: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]],
    frac: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Converts fractional coordinates (u, v, w) to Cartesian Angstroms."""
    a1, a2, a3 = cell
    u, v, w = frac
    return (
        u * a1[0] + v * a2[0] + w * a3[0],
        u * a1[1] + v * a2[1] + w * a3[1],
        u * a1[2] + v * a2[2] + w * a3[2],
    )


def _deterministic_seed(phase_name: str, at_comp: Dict[str, float]) -> int:
    sig = "|".join(f"{k}:{v:.4f}" for k, v in sorted(at_comp.items()))
    digest = hashlib.sha256(f"{phase_name}::{sig}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _assign_elements_to_slots(slot_count: int, weights: Dict[str, float], seed: int) -> List[str]:
    """
    Assigns `slot_count` discrete atomic sites to elements in strict proportion to
    `weights` using largest-remainder rounding and a deterministic golden-ratio permutation
    so even small 1x1x1 and 2x2x2 supercells reflect exact bulk/sublattice chemistry.
    """
    if slot_count <= 0:
        return []
    clean = {k: max(0.0, float(v)) for k, v in weights.items() if float(v) > 1e-6}
    if not clean:
        return ["Fe"] * slot_count

    total = sum(clean.values())
    norm = {k: v / total for k, v in clean.items()}

    exact = [(k, norm[k] * slot_count) for k in sorted(norm.keys())]
    counts: Dict[str, int] = {k: int(math.floor(val)) for k, val in exact}
    remainder = slot_count - sum(counts.values())

    # Distribute remaining atoms by largest fractional remainder (Hamilton apportionment)
    remainders = sorted(exact, key=lambda kv: (-(kv[1] - math.floor(kv[1])), -norm[kv[0]], kv[0]))
    for i in range(remainder):
        counts[remainders[i % len(remainders)][0]] += 1

    pool: List[str] = []
    for k in sorted(counts.keys()):
        pool.extend([k] * counts[k])

    # Deterministic Fisher-Yates shuffle for uniform spatial dispersion
    state = (seed ^ 0x9E3779B9) & 0xFFFFFFFF
    for i in range(len(pool) - 1, 0, -1):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        j = state % (i + 1)
        pool[i], pool[j] = pool[j], pool[i]
    return pool


def _subset_weights(at_comp: Dict[str, float], preferred: List[str], fallback: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Extracts atomic fractions for `preferred` elements present in the alloy, falling back cleanly."""
    sub = {el: float(at_comp[el]) for el in preferred if el in at_comp and float(at_comp[el]) > 1e-4}
    if sub:
        tot = sum(sub.values())
        return {k: v / tot for k, v in sub.items()}
    if fallback:
        return dict(fallback)
    # Remove interstitial C/B/N if metallic fallback is possible
    metallic = {k: float(v) for k, v in at_comp.items() if k not in ("C", "B", "N", "O") and float(v) > 1e-4}
    src = metallic if metallic else at_comp
    tot = sum(src.values()) or 1.0
    return {k: float(v) / tot for k, v in src.items()}


class CrystalStructureEngine:
    """Builds 3D crystallographic models and site-occupancy metadata for active phases."""

    # Prototype archetype metadata table (eliminates duplicated branching across phases)
    ARCHETYPES: Dict[str, Dict[str, Any]] = {
        "FCC_A1": {
            "crystal_system": "Cubic (Face-Centred)",
            "space_group": "Fm-3m (No. 225)",
            "pearson": "cF4",
            "strukturbericht": "A1",
            "prototype": "Cu (Random Substitutional Solid Solution)",
            "apf": 0.74,
            "coordination_number": 12,
            "slip_system": "{111}<110>",
            "slip_plane_normal": [1.0, 1.0, 1.0],
            "burgers_factor": 1.0 / math.sqrt(2.0),
            "configuration_mode": "Disordered Substitutional Solid Solution",
            "configuration_summary": "Atoms randomly populate the 4a face-centred cubic sites in proportion to bulk atomic composition, maximising configurational mixing entropy.",
            "z_formula_units": 4,
            "sites": [
                ("4a (Corner/Face)", (0.0, 0.0, 0.0), "matrix"),
                ("4a (Corner/Face)", (0.0, 0.5, 0.5), "matrix"),
                ("4a (Corner/Face)", (0.5, 0.0, 0.5), "matrix"),
                ("4a (Corner/Face)", (0.5, 0.5, 0.0), "matrix"),
            ],
        },
        "BCC_A2": {
            "crystal_system": "Cubic (Body-Centred)",
            "space_group": "Im-3m (No. 229)",
            "pearson": "cI2",
            "strukturbericht": "A2",
            "prototype": "W / alpha-Fe (Substitutional Solid Solution)",
            "apf": 0.68,
            "coordination_number": 8,
            "slip_system": "{110}<111>",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": math.sqrt(3.0) / 2.0,
            "configuration_mode": "Disordered Body-Centred Solid Solution",
            "configuration_summary": "Atoms occupy equivalent 2a corner and body-centre sites statistically according to bulk composition, giving open 8-fold coordination.",
            "z_formula_units": 2,
            "sites": [
                ("2a (Corner)", (0.0, 0.0, 0.0), "matrix"),
                ("2a (Body Centre)", (0.5, 0.5, 0.5), "matrix"),
            ],
        },
        "BCT_M": {
            "crystal_system": "Tetragonal (Body-Centred)",
            "space_group": "I4/mmm (No. 139)",
            "pearson": "tI2",
            "strukturbericht": "A6 / BCT",
            "prototype": "alpha'-Fe(C) Martensite",
            "apf": 0.68,
            "coordination_number": 8,
            "slip_system": "{110}<111> / {112}<111>",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": math.sqrt(3.0) / 2.0,
            "configuration_mode": "Tetragonal Distorted Matrix + Octahedral Interstitials",
            "configuration_summary": "Metallic species occupy 2a body-centred tetragonal positions while carbon/nitrogen atoms expand the c-axis at 2b octahedral z-interstices.",
            "z_formula_units": 2,
            "sites": [
                ("2a (Host Corner)", (0.0, 0.0, 0.0), "host_fe"),
                ("2a (Host Body)", (0.5, 0.5, 0.5), "host_fe"),
                ("2b (Octahedral Interstitial)", (0.0, 0.0, 0.5), "interstitial_c"),
            ],
        },
        "BCT_BETA_SN": {
            "crystal_system": "Tetragonal (Body-Centred)",
            "space_group": "I4_1/amd (No. 141)",
            "pearson": "tI4",
            "strukturbericht": "A5",
            "prototype": "beta-Sn (White Tin)",
            "apf": 0.54,
            "coordination_number": 6,
            "slip_system": "{100}<001> / {110}<001>",
            "slip_plane_normal": [1.0, 0.0, 0.0],
            "burgers_factor": 0.55,
            "configuration_mode": "Tetragonal Metallic-Covalent Matrix",
            "configuration_summary": "Sn-rich 4a diamond-compressed tetragonal sites form flattened tetrahedra along c with trace solid-solution solute substitution.",
            "z_formula_units": 4,
            "sites": [
                ("4a", (0.0, 0.0, 0.0), "sn_host"),
                ("4a", (0.5, 0.5, 0.5), "sn_host"),
                ("4a", (0.0, 0.5, 0.25), "sn_host"),
                ("4a", (0.5, 0.0, 0.75), "sn_host"),
            ],
        },
        "HCP_A3": {
            "crystal_system": "Hexagonal (Close-Packed)",
            "space_group": "P6_3/mmc (No. 194)",
            "pearson": "hP2",
            "strukturbericht": "A3",
            "prototype": "Mg / alpha-Ti (ABAB Close-Packed)",
            "apf": 0.74,
            "coordination_number": 12,
            "slip_system": "{0001}<11-20> Basal / {10-10} Prismatic",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Hexagonal ABAB Close-Packed Solid Solution",
            "configuration_summary": "Atoms stack in alternating A-B-A-B basal planes on Wyckoff 2c sites with ideal c/a ~ 1.58-1.63 and 12-fold coordination.",
            "z_formula_units": 2,
            "sites": [
                ("2c (A-Plane)", (0.333333, 0.666667, 0.25), "matrix"),
                ("2c (B-Plane)", (0.666667, 0.333333, 0.75), "matrix"),
            ],
        },
        "B2_CSCL": {
            "crystal_system": "Cubic (Primitive Ordered)",
            "space_group": "Pm-3m (No. 221)",
            "pearson": "cP2",
            "strukturbericht": "B2",
            "prototype": "CsCl (NiAl / FeAl Ordered Superlattice)",
            "apf": 0.68,
            "coordination_number": 8,
            "slip_system": "{110}<001> (Antiphase Boundary Coupled)",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Ordered Two-Sublattice Superlattice (CEF alpha:beta)",
            "configuration_summary": "Long-range chemical ordering separates late transition metals (Ni, Fe, Co) on 1a corners from p-block/early solutes (Al, Ti, Ga) on the 1b body centre.",
            "z_formula_units": 2,
            "sites": [
                ("1a (TM Sublattice)", (0.0, 0.0, 0.0), "b2_tm"),
                ("1b (Al/Ti Sublattice)", (0.5, 0.5, 0.5), "b2_al"),
            ],
        },
        "L12_CU3AU": {
            "crystal_system": "Cubic (Ordered Gamma-Prime)",
            "space_group": "Pm-3m (No. 221)",
            "pearson": "cP4",
            "strukturbericht": "L1_2",
            "prototype": "Cu3Au (Ni3Al / Co3(Al,W))",
            "apf": 0.74,
            "coordination_number": 12,
            "slip_system": "{111}<110> (Superdislocation a/2<110> pairs)",
            "slip_plane_normal": [1.0, 1.0, 1.0],
            "burgers_factor": 1.0 / math.sqrt(2.0),
            "configuration_mode": "Ordered L1_2 Superlattice (3:1 Sublattice Ratio)",
            "configuration_summary": "Host Ni/Co/Fe atoms occupy the three 3c face-centre sites while larger Al/Ti/Nb/Ta gamma'-formers order exclusively onto the 1a cube corners.",
            "z_formula_units": 4,
            "sites": [
                ("1a (Corner Al/Ti/Nb)", (0.0, 0.0, 0.0), "l12_b"),
                ("3c (Face Ni/Co/Fe)", (0.5, 0.5, 0.0), "l12_a"),
                ("3c (Face Ni/Co/Fe)", (0.5, 0.0, 0.5), "l12_a"),
                ("3c (Face Ni/Co/Fe)", (0.0, 0.5, 0.5), "l12_a"),
            ],
        },
        "D022_NI3NB": {
            "crystal_system": "Tetragonal (Ordered Gamma'')",
            "space_group": "I4/mmm (No. 139)",
            "pearson": "tI8",
            "strukturbericht": "D0_22",
            "prototype": "Al3Ti (Ni3Nb Metastable Coherent Disc)",
            "apf": 0.74,
            "coordination_number": 12,
            "slip_system": "{111}<112> Coherency Hardening",
            "slip_plane_normal": [1.0, 1.0, 1.0],
            "burgers_factor": 0.71,
            "configuration_mode": "Ordered Tetragonal D0_22 (c ~ 2a)",
            "configuration_summary": "Alternating (Ni,Fe)-rich and (Nb,Ti)-shifted planes double the c-axis relative to L1_2, generating strong coherency strains on {100} discs.",
            "z_formula_units": 8,
            "sites": [
                ("2a (Nb/Ti Corner)", (0.0, 0.0, 0.0), "d022_b"),
                ("2a (Nb/Ti Body-Shift)", (0.5, 0.5, 0.5), "d022_b"),
                ("2b (Ni/Fe z=0.5)", (0.0, 0.0, 0.5), "d022_a"),
                ("2b (Ni/Fe Face)", (0.5, 0.5, 0.0), "d022_a"),
                ("4d (Ni/Fe Layer)", (0.0, 0.5, 0.25), "d022_a"),
                ("4d (Ni/Fe Layer)", (0.5, 0.0, 0.25), "d022_a"),
                ("4d (Ni/Fe Layer)", (0.0, 0.5, 0.75), "d022_a"),
                ("4d (Ni/Fe Layer)", (0.5, 0.0, 0.75), "d022_a"),
            ],
        },
        "LAVES_C14": {
            "crystal_system": "Hexagonal (Topologically Close-Packed)",
            "space_group": "P6_3/mmc (No. 194)",
            "pearson": "hP12",
            "strukturbericht": "C14",
            "prototype": "MgZn2 (AB_2 Laves Phase)",
            "apf": 0.71,
            "coordination_number": 14,
            "slip_system": "Synchroshear on {0001} Kagome Planes",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Size-Driven Frank-Kasper Cage (R_A / R_B ~ 1.225)",
            "configuration_summary": "Larger A atoms (Nb, Zr, Mg, Ti) reside in 4f CN16 Friauf polyhedra while smaller B atoms (Fe, Cr, Zn, Ni) form 2a/6h Kagome-pyramidal networks.",
            "z_formula_units": 12,
            "sites": [
                ("4f (Large-A Cage)", (0.333333, 0.666667, 0.0625), "laves_large"),
                ("4f (Large-A Cage)", (0.666667, 0.333333, 0.5625), "laves_large"),
                ("4f (Large-A Cage)", (0.666667, 0.333333, 0.9375), "laves_large"),
                ("4f (Large-A Cage)", (0.333333, 0.666667, 0.4375), "laves_large"),
                ("2a (Small-B Apex)", (0.0, 0.0, 0.0), "laves_small"),
                ("2a (Small-B Apex)", (0.0, 0.0, 0.5), "laves_small"),
                ("6h (Kagome-B z=0.25)", (0.830, 0.660, 0.25), "laves_small"),
                ("6h (Kagome-B z=0.25)", (0.340, 0.170, 0.25), "laves_small"),
                ("6h (Kagome-B z=0.25)", (0.830, 0.170, 0.25), "laves_small"),
                ("6h (Kagome-B z=0.75)", (0.170, 0.340, 0.75), "laves_small"),
                ("6h (Kagome-B z=0.75)", (0.660, 0.830, 0.75), "laves_small"),
                ("6h (Kagome-B z=0.75)", (0.170, 0.830, 0.75), "laves_small"),
            ],
        },
        "LAVES_C15": {
            "crystal_system": "Cubic (Frank-Kasper TCP)",
            "space_group": "Fd-3m (No. 227)",
            "pearson": "cF24",
            "strukturbericht": "C15",
            "prototype": "MgCu2 (AB_2 Cubic Laves Phase)",
            "apf": 0.71,
            "coordination_number": 14,
            "slip_system": "{111}<112> Synchroshear Partial",
            "slip_plane_normal": [1.0, 1.0, 1.0],
            "burgers_factor": 0.41,
            "configuration_mode": "Cubic Diamond-A + Pyrochlore-B Network",
            "configuration_summary": "Large A atoms (Zr, Nb, Ta, Hf) form an 8a diamond network interlocked with 16d corner-sharing tetrahedra of smaller B transition metals.",
            "z_formula_units": 24,
            "sites": [
                # 8a diamond sites of large A atom
                ("8a (Large-A Diamond)", (0.0, 0.0, 0.0), "laves_large"),
                ("8a (Large-A Diamond)", (0.0, 0.5, 0.5), "laves_large"),
                ("8a (Large-A Diamond)", (0.5, 0.0, 0.5), "laves_large"),
                ("8a (Large-A Diamond)", (0.5, 0.5, 0.0), "laves_large"),
                ("8a (Large-A Diamond)", (0.25, 0.25, 0.25), "laves_large"),
                ("8a (Large-A Diamond)", (0.25, 0.75, 0.75), "laves_large"),
                ("8a (Large-A Diamond)", (0.75, 0.25, 0.75), "laves_large"),
                ("8a (Large-A Diamond)", (0.75, 0.75, 0.25), "laves_large"),
                # 16d pyrochlore tetrahedra of smaller B atom (5/8, 5/8, 5/8 family)
                ("16d (Small-B Pyrochlore)", (0.625, 0.625, 0.625), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.625, 0.875, 0.875), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.875, 0.625, 0.875), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.875, 0.875, 0.625), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.625, 0.125, 0.125), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.625, 0.375, 0.375), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.875, 0.125, 0.375), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.875, 0.375, 0.125), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.125, 0.625, 0.125), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.125, 0.875, 0.375), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.375, 0.625, 0.375), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.375, 0.875, 0.125), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.125, 0.125, 0.625), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.125, 0.375, 0.875), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.375, 0.125, 0.875), "laves_small"),
                ("16d (Small-B Pyrochlore)", (0.375, 0.375, 0.625), "laves_small"),
            ],
        },
        "SIGMA_D8B": {
            "crystal_system": "Tetragonal (TCP Sigma)",
            "space_group": "P4_2/mnm (No. 136)",
            "pearson": "tP30",
            "strukturbericht": "D8_b",
            "prototype": "FeCr Sigma Phase (30-Atom TCP Cell)",
            "apf": 0.72,
            "coordination_number": 14,
            "slip_system": "Brittle Frank-Kasper (Dislocation Locking)",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 1.0,
            "configuration_mode": "5-Sublattice Frank-Kasper Polyhedra (CN 12, 14, 15)",
            "configuration_summary": "30 atoms partition across CN12 (2a/8i2 Fe/Ni/Co-rich), CN14 (8i1/8j mixed), and CN15 (4f Cr/Mo/W-rich) kagome layers perpendicular to [001].",
            "z_formula_units": 30,
            "sites": [
                # 2a (CN12)
                ("2a (CN12 Late-TM)", (0.0, 0.0, 0.0), "sigma_a"),
                ("2a (CN12 Late-TM)", (0.5, 0.5, 0.5), "sigma_a"),
                # 4f (CN15, x=0.398)
                ("4f (CN15 Refractory/Cr)", (0.398, 0.398, 0.0), "sigma_b"),
                ("4f (CN15 Refractory/Cr)", (0.602, 0.602, 0.0), "sigma_b"),
                ("4f (CN15 Refractory/Cr)", (0.102, 0.898, 0.5), "sigma_b"),
                ("4f (CN15 Refractory/Cr)", (0.898, 0.102, 0.5), "sigma_b"),
                # 8i1 (CN14, x=0.537, y=0.131)
                ("8i1 (CN14 Mixed)", (0.537, 0.131, 0.0), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.463, 0.869, 0.0), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.869, 0.537, 0.0), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.131, 0.463, 0.0), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.037, 0.369, 0.5), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.963, 0.631, 0.5), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.369, 0.037, 0.5), "sigma_c"),
                ("8i1 (CN14 Mixed)", (0.631, 0.963, 0.5), "sigma_c"),
                # 8i2 (CN12, x=0.065, y=0.262)
                ("8i2 (CN12 Late-TM)", (0.065, 0.262, 0.0), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.935, 0.738, 0.0), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.738, 0.065, 0.0), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.262, 0.935, 0.0), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.565, 0.238, 0.5), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.435, 0.762, 0.5), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.238, 0.565, 0.5), "sigma_a"),
                ("8i2 (CN12 Late-TM)", (0.762, 0.435, 0.5), "sigma_a"),
                # 8j (CN14, x=0.317, z=0.252)
                ("8j (CN14 Kagome)", (0.317, 0.317, 0.252), "sigma_b"),
                ("8j (CN14 Kagome)", (0.683, 0.683, 0.252), "sigma_b"),
                ("8j (CN14 Kagome)", (0.317, 0.317, 0.748), "sigma_b"),
                ("8j (CN14 Kagome)", (0.683, 0.683, 0.748), "sigma_b"),
                ("8j (CN14 Kagome)", (0.183, 0.817, 0.252), "sigma_b"),
                ("8j (CN14 Kagome)", (0.817, 0.183, 0.252), "sigma_b"),
                ("8j (CN14 Kagome)", (0.183, 0.817, 0.748), "sigma_b"),
                ("8j (CN14 Kagome)", (0.817, 0.183, 0.748), "sigma_b"),
            ],
        },
        "CHI_A12": {
            "crystal_system": "Cubic (TCP Chi / alpha-Mn)",
            "space_group": "I-43m (No. 217)",
            "pearson": "cI58",
            "strukturbericht": "A12",
            "prototype": "alpha-Mn / Fe36Cr12Mo10 Chi Phase",
            "apf": 0.72,
            "coordination_number": 14,
            "slip_system": "Brittle Frank-Kasper TCP (Cleavage / Pinning)",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": 0.5,
            "configuration_mode": "BCC-Derivative Polyhedral Cell (2a, 8c, 24g1, 24g2)",
            "configuration_summary": "Large refractory Mo/W/Nb/Cr atoms occupy high-coordination 2a (CN16) and 8c (CN16) sites inside an I-43m transition-metal frame.",
            "z_formula_units": 34,
            "sites": [
                # 2a (CN16 Refractory Mo/Nb/W)
                ("2a (CN16 Refractory)", (0.0, 0.0, 0.0), "chi_a"),
                ("2a (CN16 Refractory)", (0.5, 0.5, 0.5), "chi_a"),
                # 8c (x=0.317, CN16 Refractory/Cr)
                ("8c (CN16 Cr/Mo)", (0.317, 0.317, 0.317), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.683, 0.683, 0.317), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.683, 0.317, 0.683), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.317, 0.683, 0.683), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.817, 0.817, 0.817), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.183, 0.183, 0.817), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.183, 0.817, 0.183), "chi_a"),
                ("8c (CN16 Cr/Mo)", (0.817, 0.183, 0.183), "chi_a"),
                # 24g (x=0.356, z=0.042, CN13/CN12 Fe/Cr/Ni shell - symmetric representatives)
                ("24g (CN12 TM Frame)", (0.356, 0.356, 0.042), "chi_b"),
                ("24g (CN12 TM Frame)", (0.644, 0.644, 0.042), "chi_b"),
                ("24g (CN12 TM Frame)", (0.356, 0.644, 0.958), "chi_b"),
                ("24g (CN12 TM Frame)", (0.644, 0.356, 0.958), "chi_b"),
                ("24g (CN12 TM Frame)", (0.042, 0.356, 0.356), "chi_b"),
                ("24g (CN12 TM Frame)", (0.042, 0.644, 0.644), "chi_b"),
                ("24g (CN12 TM Frame)", (0.958, 0.356, 0.644), "chi_b"),
                ("24g (CN12 TM Frame)", (0.958, 0.644, 0.356), "chi_b"),
                ("24g (CN12 TM Frame)", (0.356, 0.042, 0.356), "chi_b"),
                ("24g (CN12 TM Frame)", (0.644, 0.042, 0.644), "chi_b"),
                ("24g (CN12 TM Frame)", (0.356, 0.958, 0.644), "chi_b"),
                ("24g (CN12 TM Frame)", (0.644, 0.958, 0.356), "chi_b"),
                ("24g (CN12 TM Frame)", (0.856, 0.856, 0.542), "chi_b"),
                ("24g (CN12 TM Frame)", (0.144, 0.144, 0.542), "chi_b"),
                ("24g (CN12 TM Frame)", (0.856, 0.144, 0.458), "chi_b"),
                ("24g (CN12 TM Frame)", (0.144, 0.856, 0.458), "chi_b"),
                ("24g (CN12 TM Frame)", (0.542, 0.856, 0.856), "chi_b"),
                ("24g (CN12 TM Frame)", (0.542, 0.144, 0.144), "chi_b"),
                ("24g (CN12 TM Frame)", (0.458, 0.856, 0.144), "chi_b"),
                ("24g (CN12 TM Frame)", (0.458, 0.144, 0.856), "chi_b"),
                ("24g (CN12 TM Frame)", (0.856, 0.542, 0.856), "chi_b"),
                ("24g (CN12 TM Frame)", (0.144, 0.542, 0.144), "chi_b"),
                ("24g (CN12 TM Frame)", (0.856, 0.458, 0.144), "chi_b"),
                ("24g (CN12 TM Frame)", (0.144, 0.458, 0.856), "chi_b"),
            ],
        },
        "HEUSLER_L21": {
            "crystal_system": "Cubic (Ordered Heusler L2_1)",
            "space_group": "Fm-3m (No. 225)",
            "pearson": "cF16",
            "strukturbericht": "L2_1",
            "prototype": "AlCu2Mn (Ni2TiAl / Fe2TiAl Full-Heusler)",
            "apf": 0.68,
            "coordination_number": 8,
            "slip_system": "{110}<1-11> Superdislocation (4-fold APB)",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": 0.5 * math.sqrt(3.0),
            "configuration_mode": "4 Interpenetrating FCC Sublattices (8c X : 4a Z : 4b Y)",
            "configuration_summary": "A 2x2x2 B2 superlattice where (Al,Si,Sn) at 4a and (Ti,Zr,Hf,Nb) at 4b alternate within a CsCl-type Ni/Co/Fe 8c matrix.",
            "z_formula_units": 16,
            "sites": [
                # 4a (Z: Al/Si/Ga/Sn)
                ("4a (Al/Si Sublattice)", (0.0, 0.0, 0.0), "heusler_z"),
                ("4a (Al/Si Sublattice)", (0.0, 0.5, 0.5), "heusler_z"),
                ("4a (Al/Si Sublattice)", (0.5, 0.0, 0.5), "heusler_z"),
                ("4a (Al/Si Sublattice)", (0.5, 0.5, 0.0), "heusler_z"),
                # 4b (Y: Ti/Zr/Nb/Mn/Cr)
                ("4b (Ti/Nb Sublattice)", (0.5, 0.5, 0.5), "heusler_y"),
                ("4b (Ti/Nb Sublattice)", (0.5, 0.0, 0.0), "heusler_y"),
                ("4b (Ti/Nb Sublattice)", (0.0, 0.5, 0.0), "heusler_y"),
                ("4b (Ti/Nb Sublattice)", (0.0, 0.0, 0.5), "heusler_y"),
                # 8c (X2: Ni/Co/Fe/Cu)
                ("8c (Ni/Co Matrix)", (0.25, 0.25, 0.25), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.25, 0.75, 0.75), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.75, 0.25, 0.75), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.75, 0.75, 0.25), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.75, 0.75, 0.75), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.75, 0.25, 0.25), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.25, 0.75, 0.25), "heusler_x"),
                ("8c (Ni/Co Matrix)", (0.25, 0.25, 0.75), "heusler_x"),
            ],
        },
        "MU_D85": {
            "crystal_system": "Trigonal / Hexagonal Setting (TCP Mu)",
            "space_group": "R-3m (No. 166)",
            "pearson": "hR13",
            "strukturbericht": "D8_5",
            "prototype": "Fe7W6 (Rhombohedral TCP Mu)",
            "apf": 0.73,
            "coordination_number": 15,
            "slip_system": "Brittle Frank-Kasper (Non-Close-Packed Layers)",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Ordered Alternating Zr4Al3 + Laves Slabs along c",
            "configuration_summary": "Refractory Mo/W/Nb/Ta atoms occupy CN15/16 sites interleaved with Fe/Co/Ni CN12 icosahedral sheets stacked along c (c ~ 25.6 A).",
            "z_formula_units": 13,
            "sites": [
                ("3a (CN12 TM)", (0.0, 0.0, 0.0), "mu_tm"),
                ("18h (CN12 TM)", (0.5, 0.0, 0.09), "mu_tm"),
                ("18h (CN12 TM)", (0.0, 0.5, 0.09), "mu_tm"),
                ("18h (CN12 TM)", (0.5, 0.5, 0.09), "mu_tm"),
                ("6c (CN16 W/Mo)", (0.0, 0.0, 0.167), "mu_ref"),
                ("6c (CN15 W/Mo)", (0.0, 0.0, 0.346), "mu_ref"),
                ("6c (CN14 Nb/Mo)", (0.0, 0.0, 0.449), "mu_ref"),
                ("18h (CN12 TM)", (0.5, 0.5, 0.255), "mu_tm"),
                ("18h (CN12 TM)", (0.167, 0.333, 0.423), "mu_tm"),
                ("18h (CN12 TM)", (0.833, 0.667, 0.577), "mu_tm"),
                ("6c (CN16 W/Mo)", (0.333, 0.667, 0.500), "mu_ref"),
                ("6c (CN15 W/Mo)", (0.333, 0.667, 0.679), "mu_ref"),
                ("3a (CN12 TM)", (0.667, 0.333, 0.333), "mu_tm"),
            ],
        },
        "CARBIDE_B1": {
            "crystal_system": "Cubic (Rocksalt MC Carbide)",
            "space_group": "Fm-3m (No. 225)",
            "pearson": "cF8",
            "strukturbericht": "B1",
            "prototype": "NaCl (TiC / NbC / (Ti,Nb,Cr)C)",
            "apf": 0.72,
            "coordination_number": 6,
            "slip_system": "{110}<1-10> Covalent-Metallic",
            "slip_plane_normal": [1.0, 1.0, 0.0],
            "burgers_factor": 1.0 / math.sqrt(2.0),
            "configuration_mode": "Interpenetrating FCC Sublattices (M 4a : C 4b)",
            "configuration_summary": "Carbide-forming refractory metals (Ti, Nb, Ta, Cr, Mo, W) form the 4a FCC frame while Carbon occupies every 4b octahedral interstice in NaCl B1 coordination.",
            "z_formula_units": 8,
            "sites": [
                ("4a (Metal FCC)", (0.0, 0.0, 0.0), "carbide_m"),
                ("4a (Metal FCC)", (0.0, 0.5, 0.5), "carbide_m"),
                ("4a (Metal FCC)", (0.5, 0.0, 0.5), "carbide_m"),
                ("4a (Metal FCC)", (0.5, 0.5, 0.0), "carbide_m"),
                ("4b (Carbon Octahedral)", (0.5, 0.5, 0.5), "carbide_c"),
                ("4b (Carbon Octahedral)", (0.5, 0.0, 0.0), "carbide_c"),
                ("4b (Carbon Octahedral)", (0.0, 0.5, 0.0), "carbide_c"),
                ("4b (Carbon Octahedral)", (0.0, 0.0, 0.5), "carbide_c"),
            ],
        },
        "DIAMOND_A4": {
            "crystal_system": "Cubic (Diamond Cubic)",
            "space_group": "Fd-3m (No. 227)",
            "pearson": "cF8",
            "strukturbericht": "A4",
            "prototype": "Diamond / Silicon (Covalent sp3)",
            "apf": 0.34,
            "coordination_number": 4,
            "slip_system": "{111}<110> Peierls-Limited",
            "slip_plane_normal": [1.0, 1.0, 1.0],
            "burgers_factor": 1.0 / math.sqrt(2.0),
            "configuration_mode": "Tetrahedral sp3 Covalent Network (Wyckoff 8a)",
            "configuration_summary": "Two interpenetrating FCC sublattices offset by (1/4, 1/4, 1/4) form four directional covalent bonds per Si/C atom.",
            "z_formula_units": 8,
            "sites": [
                ("8a (Tetrahedral)", (0.0, 0.0, 0.0), "diamond_si"),
                ("8a (Tetrahedral)", (0.0, 0.5, 0.5), "diamond_si"),
                ("8a (Tetrahedral)", (0.5, 0.0, 0.5), "diamond_si"),
                ("8a (Tetrahedral)", (0.5, 0.5, 0.0), "diamond_si"),
                ("8a (Offset +1/4)", (0.25, 0.25, 0.25), "diamond_si"),
                ("8a (Offset +1/4)", (0.25, 0.75, 0.75), "diamond_si"),
                ("8a (Offset +1/4)", (0.75, 0.25, 0.75), "diamond_si"),
                ("8a (Offset +1/4)", (0.75, 0.75, 0.25), "diamond_si"),
            ],
        },
        "GRAPHITE_A9": {
            "crystal_system": "Hexagonal (Layered sp2)",
            "space_group": "P6_3/mmc (No. 194)",
            "pearson": "hP4",
            "strukturbericht": "A9",
            "prototype": "Graphite (AB Stacked Graphene Sheets)",
            "apf": 0.17,
            "coordination_number": 3,
            "slip_system": "{0001}<11-20> Easy van der Waals Shear",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Layered sp2 Honeycomb (Covalently Bonded Basal Planes)",
            "configuration_summary": "Trigonal sp2 carbon atoms form strong hexagonal rings in basal planes held apart by weak pi-van der Waals bonding along c.",
            "z_formula_units": 4,
            "sites": [
                ("2b (Basal A1)", (0.0, 0.0, 0.25), "graphite_c"),
                ("2c (Basal A2)", (0.333333, 0.666667, 0.25), "graphite_c"),
                ("2b (Basal B1)", (0.0, 0.0, 0.75), "graphite_c"),
                ("2d (Basal B2)", (0.666667, 0.333333, 0.75), "graphite_c"),
            ],
        },
        "CEMENTITE_D011": {
            "crystal_system": "Orthorhombic (Pearlite Fe3C + Alpha-Fe Lamellae)",
            "space_group": "Pnma (No. 62)",
            "pearson": "oP16",
            "strukturbericht": "D0_11",
            "prototype": "Fe3C Cementite (Trigonal Prism Network)",
            "apf": 0.69,
            "coordination_number": 10,
            "slip_system": "{001}<010> Lamellar Interface",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 0.5,
            "configuration_mode": "Trigonal Fe6C Prisms Alternating with BCC Ferrite",
            "configuration_summary": "12 Fe atoms on 4c/8d positions cage 4 interstitial C atoms inside corner-sharing trigonal prisms inside each Fe3C cementite lamella.",
            "z_formula_units": 16,
            "sites": [
                ("4c (Fe Special)", (0.036, 0.25, 0.852), "host_fe"),
                ("4c (Fe Special)", (0.964, 0.75, 0.148), "host_fe"),
                ("4c (Fe Special)", (0.464, 0.25, 0.648), "host_fe"),
                ("4c (Fe Special)", (0.536, 0.75, 0.352), "host_fe"),
                ("8d (Fe General)", (0.186, 0.063, 0.328), "host_fe"),
                ("8d (Fe General)", (0.814, 0.563, 0.672), "host_fe"),
                ("8d (Fe General)", (0.314, 0.937, 0.828), "host_fe"),
                ("8d (Fe General)", (0.686, 0.437, 0.172), "host_fe"),
                ("8d (Fe General)", (0.814, 0.937, 0.672), "host_fe"),
                ("8d (Fe General)", (0.186, 0.437, 0.328), "host_fe"),
                ("8d (Fe General)", (0.686, 0.063, 0.172), "host_fe"),
                ("8d (Fe General)", (0.314, 0.563, 0.828), "host_fe"),
                ("4c (C Interstitial)", (0.890, 0.25, 0.450), "interstitial_c"),
                ("4c (C Interstitial)", (0.110, 0.75, 0.550), "interstitial_c"),
                ("4c (C Interstitial)", (0.390, 0.75, 0.950), "interstitial_c"),
                ("4c (C Interstitial)", (0.610, 0.25, 0.050), "interstitial_c"),
            ],
        },
        "THETA_AL2CU": {
            "crystal_system": "Tetragonal (Intermetallic C16)",
            "space_group": "I4/mcm (No. 140)",
            "pearson": "tI12",
            "strukturbericht": "C16",
            "prototype": "Al2Cu (CuAl2 Square-Antiprism Columns)",
            "apf": 0.72,
            "coordination_number": 10,
            "slip_system": "Semi-coherent Precipitate Cutting / Orowan Bypass",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 0.6,
            "configuration_mode": "Ordered Cu-Column Square Antiprisms in Al Matrix",
            "configuration_summary": "4 Cu atoms form linear chains along [001] at (0,0,1/4) enclosed by 8 Al square antiprisms on Wyckoff 8h sites.",
            "z_formula_units": 12,
            "sites": [
                ("4a (Cu Chain)", (0.0, 0.0, 0.25), "imc_cu"),
                ("4a (Cu Chain)", (0.0, 0.0, 0.75), "imc_cu"),
                ("4a (Cu Chain)", (0.5, 0.5, 0.25), "imc_cu"),
                ("4a (Cu Chain)", (0.5, 0.5, 0.75), "imc_cu"),
                ("8h (Al Cage)", (0.158, 0.658, 0.0), "imc_al"),
                ("8h (Al Cage)", (0.842, 0.342, 0.0), "imc_al"),
                ("8h (Al Cage)", (0.342, 0.158, 0.0), "imc_al"),
                ("8h (Al Cage)", (0.658, 0.842, 0.0), "imc_al"),
                ("8h (Al Cage)", (0.658, 0.158, 0.5), "imc_al"),
                ("8h (Al Cage)", (0.342, 0.842, 0.5), "imc_al"),
                ("8h (Al Cage)", (0.842, 0.658, 0.5), "imc_al"),
                ("8h (Al Cage)", (0.158, 0.342, 0.5), "imc_al"),
            ],
        },
        "IMC_AG3SN": {
            "crystal_system": "Orthorhombic (Ordered D0_a IMC)",
            "space_group": "Pmmn (No. 59)",
            "pearson": "oP8",
            "strukturbericht": "D0_a",
            "prototype": "beta-Cu3Ti (Ag3Sn Solder Platelet)",
            "apf": 0.73,
            "coordination_number": 12,
            "slip_system": "Ordered HCP-Derived Orthorhombic",
            "slip_plane_normal": [0.0, 1.0, 0.0],
            "burgers_factor": 0.7,
            "configuration_mode": "Ordered 3:1 Close-Packed Orthorhombic Sublattices",
            "configuration_summary": "Ag atoms occupy 4f and 2a sites in hexagonal-like close-packed rows ordered with Sn atoms on 2b positions.",
            "z_formula_units": 8,
            "sites": [
                ("2b (Sn Ordered)", (0.25, 0.25, 0.17), "sn_host"),
                ("2b (Sn Ordered)", (0.75, 0.75, 0.83), "sn_host"),
                ("2a (Ag/Cu Layer)", (0.25, 0.75, 0.67), "imc_ag"),
                ("2a (Ag/Cu Layer)", (0.75, 0.25, 0.33), "imc_ag"),
                ("4f (Ag/Cu Basal)", (0.00, 0.25, 0.66), "imc_ag"),
                ("4f (Ag/Cu Basal)", (0.50, 0.25, 0.66), "imc_ag"),
                ("4f (Ag/Cu Basal)", (0.00, 0.75, 0.34), "imc_ag"),
                ("4f (Ag/Cu Basal)", (0.50, 0.75, 0.34), "imc_ag"),
            ],
        },
        "IMC_CU6SN5": {
            "crystal_system": "Hexagonal (NiAs B8_1 Eta'-IMC)",
            "space_group": "P6_3/mmc (No. 194)",
            "pearson": "hP4",
            "strukturbericht": "B8_1",
            "prototype": "NiAs (eta-Cu6Sn5 Solder Interfacial)",
            "apf": 0.71,
            "coordination_number": 6,
            "slip_system": "{0001} Interfacial Cleavage",
            "slip_plane_normal": [0.0, 0.0, 1.0],
            "burgers_factor": 0.8,
            "configuration_mode": "Hexagonal Sn Frame with Octahedral/Bipyramidal Cu",
            "configuration_summary": "Sn atoms form an HCP-like 2c sublattice while Cu atoms occupy 2a octahedral and partial 2d trigonal-bipyramidal interstices.",
            "z_formula_units": 6,
            "sites": [
                ("2c (Sn Frame)", (0.333333, 0.666667, 0.25), "sn_host"),
                ("2c (Sn Frame)", (0.666667, 0.333333, 0.75), "sn_host"),
                ("2a (Cu Octahedral)", (0.0, 0.0, 0.0), "imc_cu"),
                ("2a (Cu Octahedral)", (0.0, 0.0, 0.5), "imc_cu"),
                ("2d (Cu Partial)", (0.333333, 0.666667, 0.75), "imc_cu"),
                ("2d (Cu Partial)", (0.666667, 0.333333, 0.25), "imc_cu"),
            ],
        },
        "AMORPHOUS_LIQUID": {
            "crystal_system": "Non-Crystalline Melt (Short-Range Order)",
            "space_group": "P1 (Disordered SRO)",
            "pearson": "Liquid",
            "strukturbericht": "SRO",
            "prototype": "Dense Random Packing / Icosahedral SRO",
            "apf": 0.64,
            "coordination_number": 11,
            "slip_system": "Viscous Newtonian Flow (No Slip Planes)",
            "slip_plane_normal": [0.0, 1.0, 0.0],
            "burgers_factor": 1.0,
            "configuration_mode": "Thermally Disordered Dense Random Packing",
            "configuration_summary": "Above the solidus, long-range translational periodicity vanishes while nearest-neighbour chemical short-range order persists around ~11-fold clusters.",
            "z_formula_units": 12,
            "sites": [
                ("SRO", (0.50, 0.50, 0.50), "matrix"),
                ("SRO", (0.21, 0.34, 0.42), "matrix"),
                ("SRO", (0.78, 0.29, 0.58), "matrix"),
                ("SRO", (0.35, 0.77, 0.39), "matrix"),
                ("SRO", (0.66, 0.71, 0.64), "matrix"),
                ("SRO", (0.44, 0.22, 0.78), "matrix"),
                ("SRO", (0.62, 0.41, 0.19), "matrix"),
                ("SRO", (0.19, 0.62, 0.69), "matrix"),
                ("SRO", (0.81, 0.59, 0.33), "matrix"),
                ("SRO", (0.38, 0.48, 0.18), "matrix"),
                ("SRO", (0.55, 0.84, 0.82), "matrix"),
                ("SRO", (0.29, 0.18, 0.23), "matrix"),
            ],
        },
    }

    @classmethod
    def map_phase_to_archetype(cls, phase_name: str) -> str:
        """Maps any database or XRD phase identifier to a canonical crystallographic archetype."""
        u = phase_name.upper().strip()
        if "LIQUID" in u:
            return "AMORPHOUS_LIQUID"
        if "L12" in u or "L1_2" in u or "GAMMA_PRIME" in u or "NI3SI" in u:
            return "L12_CU3AU"
        if "DOUBLE_PRIME" in u or "D022" in u or "D0_22" in u or "NI3NB" in u:
            return "D022_NI3NB"
        if "HEUSLER" in u or "L21" in u or "L2_1" in u:
            return "HEUSLER_L21"
        if "B2" in u:
            return "B2_CSCL"
        if "C15" in u or "FE2ZR" in u or "CR2NB" in u:
            return "LAVES_C15"
        if "LAVES" in u or "C14" in u or "C36" in u or "MGZN2" in u or "FE2NB" in u or "ZRFECR" in u or "INTERMETALLICS" in u:
            return "LAVES_C14"
        if "SIGMA" in u or "σ" in phase_name or "D8B" in u or "D8_B" in u:
            return "SIGMA_D8B"
        if "CHI" in u or "A12" in u:
            return "CHI_A12"
        if "MU" in u or "MG17AL12" in u:
            return "MU_D85"
        if "CARBIDE" in u or "BORIDE" in u or "WC" in u or "TIC" in u or "CR7C3" in u or "CR23C6" in u:
            return "CARBIDE_B1"
        if "SILICON" in u:
            return "DIAMOND_A4"
        if "GRAPHITE" in u:
            return "GRAPHITE_A9"
        if "PEARLITE" in u or "CEMENTITE" in u or "FE3C" in u:
            return "CEMENTITE_D011"
        if "AL2CU" in u or "THETA" in u or "MG2SI" in u:
            return "THETA_AL2CU"
        if "AG3SN" in u or "CU3SN" in u:
            return "IMC_AG3SN"
        if "CU6SN5" in u:
            return "IMC_CU6SN5"
        if "BETA_SN" in u:
            return "BCT_BETA_SN"
        if "MARTENSITE" in u or "BCT" in u:
            return "BCT_M"
        if "HCP" in u or "EPSILON" in u:
            return "HCP_A3"
        if "BCC" in u or "FERRITE" in u or "A2" in u:
            return "BCC_A2"
        if "FCC" in u or "AUSTENITE" in u or "GAMMA" in u or "A1" in u:
            return "FCC_A1"
        return "FCC_A1"

    @classmethod
    def _compute_lattice_vectors(
        cls,
        archetype_key: str,
        at_comp: Dict[str, float],
        xrd_lattice: Dict[str, float],
    ) -> Tuple[Dict[str, float], Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]]:
        """Computes Vegard/benchmark lattice parameters (Angstroms & degrees) and Cartesian cell vectors."""
        # Weighted atomic radius (Angstrom) from 118-element registry
        r_ang = 0.0
        w_sum = 0.0
        for sym, frac in at_comp.items():
            if float(frac) <= 0.0:
                continue
            el = get_element(sym)
            rad = (el.radius_pm if el and el.radius_pm > 0 else 130.0) * 0.01
            r_ang += float(frac) * rad
            w_sum += float(frac)
        r_bar = r_ang / max(1e-6, w_sum) if w_sum > 0 else 1.28

        a_fcc = float(xrd_lattice.get("a_FCC", 0.0) or 0.0)
        if a_fcc <= 0.0:
            a_fcc = 2.0 * math.sqrt(2.0) * r_bar
        a_bcc = float(xrd_lattice.get("a_BCC", 0.0) or 0.0)
        if a_bcc <= 0.0:
            a_bcc = (4.0 / math.sqrt(3.0)) * r_bar

        a, b, c = a_fcc, a_fcc, a_fcc
        alpha, beta, gamma = 90.0, 90.0, 90.0

        if archetype_key == "BCC_A2":
            a = b = c = a_bcc
        elif archetype_key == "B2_CSCL":
            a = b = c = max(2.86, a_bcc)
        elif archetype_key == "BCT_M":
            c_frac = float(at_comp.get("C", 0.0)) + float(at_comp.get("N", 0.0))
            c_over_a = 1.0 + 0.045 * max(0.4, c_frac * 25.0)
            a = b = a_bcc * 0.992
            c = a * min(1.12, c_over_a)
        elif archetype_key == "BCT_BETA_SN":
            a = b = 5.831
            c = 3.182
        elif archetype_key == "HCP_A3":
            a_hcp = float(xrd_lattice.get("a_HCP", 0.0) or 0.0)
            c_hcp = float(xrd_lattice.get("c_HCP", 0.0) or 0.0)
            a = b = a_hcp if a_hcp > 0.0 else 2.0 * r_bar
            c = c_hcp if c_hcp > 0.0 else 1.615 * a
            gamma = 120.0
        elif archetype_key == "L12_CU3AU":
            a = b = c = max(3.56, a_fcc)
        elif archetype_key == "D022_NI3NB":
            a = b = 3.624
            c = 7.406
        elif archetype_key == "LAVES_C14":
            a = b = float(xrd_lattice.get("a_Laves_C14", 0.0) or 4.837)
            c = float(xrd_lattice.get("c_Laves_C14", 0.0) or 7.884)
            gamma = 120.0
        elif archetype_key == "LAVES_C15":
            a = b = c = float(xrd_lattice.get("a_Laves_C15", 0.0) or 6.991)
        elif archetype_key == "SIGMA_D8B":
            scale_r = r_bar / 1.28
            a = b = float(xrd_lattice.get("a_Sigma", 0.0) or (8.800 * scale_r))
            c = float(xrd_lattice.get("c_Sigma", 0.0) or (4.545 * scale_r))
        elif archetype_key == "CHI_A12":
            scale_r = r_bar / 1.28
            a = b = c = float(xrd_lattice.get("a_Chi", 0.0) or (8.920 * scale_r))
        elif archetype_key == "HEUSLER_L21":
            a = b = c = float(xrd_lattice.get("a_Heusler", 0.0) or max(5.78, 2.0 * a_bcc))
        elif archetype_key == "MU_D85":
            a = b = 4.757
            c = 25.63
            gamma = 120.0
        elif archetype_key == "CARBIDE_B1":
            a = b = c = 4.328
        elif archetype_key == "DIAMOND_A4":
            a = b = c = 5.431
        elif archetype_key == "GRAPHITE_A9":
            a = b = 2.464
            c = 6.711
            gamma = 120.0
        elif archetype_key == "CEMENTITE_D011":
            a, b, c = 5.089, 6.743, 4.524
        elif archetype_key == "THETA_AL2CU":
            a = b = 6.067
            c = 4.877
        elif archetype_key == "IMC_AG3SN":
            a, b, c = 5.968, 4.780, 5.184
        elif archetype_key == "IMC_CU6SN5":
            a = b = 4.192
            c = 5.037
            gamma = 120.0
        elif archetype_key == "AMORPHOUS_LIQUID":
            a = b = c = max(5.6, 2.1 * a_fcc * 0.85)

        if abs(gamma - 120.0) < 0.5:
            cell = (
                (a, 0.0, 0.0),
                (-0.5 * b, 0.5 * math.sqrt(3.0) * b, 0.0),
                (0.0, 0.0, c),
            )
        else:
            cell = ((a, 0.0, 0.0), (0.0, b, 0.0), (0.0, 0.0, c))

        params = {
            "a": round(a, 3),
            "b": round(b, 3),
            "c": round(c, 3),
            "alpha": round(alpha, 1),
            "beta": round(beta, 1),
            "gamma": round(gamma, 1),
        }
        return params, cell

    @classmethod
    def _build_sublattice_chemistry(cls, archetype_key: str, at_comp: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Resolves element composition distributions per Wyckoff sublattice role."""
        full = _subset_weights(at_comp, list(at_comp.keys()))
        metallic = _subset_weights(at_comp, [k for k in at_comp if k not in ("C", "B", "N", "O")], full)

        roles: Dict[str, Dict[str, float]] = {
            "matrix": metallic if metallic else full,
            "host_fe": _subset_weights(at_comp, ["Fe", "Ni", "Cr", "Mn", "Co", "Mo"], {"Fe": 1.0}),
            "interstitial_c": _subset_weights(at_comp, ["C", "N", "B"], {"C": 1.0}),
            "sn_host": _subset_weights(at_comp, ["Sn", "Pb", "Bi", "In"], {"Sn": 1.0}),
            "b2_tm": _subset_weights(at_comp, ["Ni", "Fe", "Co", "Cr", "Cu", "Ru"], {"Ni": 0.5, "Fe": 0.5}),
            "b2_al": _subset_weights(at_comp, ["Al", "Ti", "Ga", "Si", "Zr", "Hf"], {"Al": 1.0}),
            "l12_a": _subset_weights(at_comp, ["Ni", "Co", "Fe", "Cr"], {"Ni": 1.0}),
            "l12_b": _subset_weights(at_comp, ["Al", "Ti", "Nb", "Ta", "W", "Si"], {"Al": 0.75, "Ti": 0.25}),
            "d022_a": _subset_weights(at_comp, ["Ni", "Fe", "Co"], {"Ni": 0.85, "Fe": 0.15}),
            "d022_b": _subset_weights(at_comp, ["Nb", "Ti", "Ta", "V"], {"Nb": 0.8, "Ti": 0.2}),
            "laves_large": _subset_weights(at_comp, ["Zr", "Nb", "Hf", "Ta", "Ti", "Mg", "Y"], {"Nb": 0.6, "Ti": 0.4}),
            "laves_small": _subset_weights(at_comp, ["Fe", "Cr", "Co", "Ni", "Zn", "Mn", "Al"], {"Cr": 0.5, "Fe": 0.5}),
            "sigma_a": _subset_weights(at_comp, ["Fe", "Ni", "Co", "Mn", "Cu"], {"Fe": 0.6, "Ni": 0.4}),
            "sigma_b": _subset_weights(at_comp, ["Cr", "Mo", "W", "V", "Nb", "Ta", "Ti", "Re"], {"Cr": 0.75, "Mo": 0.25}),
            "sigma_c": metallic,
            "chi_a": _subset_weights(at_comp, ["Mo", "W", "Nb", "Ta", "Cr", "Ti"], {"Cr": 0.55, "Mo": 0.45}),
            "chi_b": _subset_weights(at_comp, ["Fe", "Cr", "Ni", "Co", "Mn"], {"Fe": 0.7, "Cr": 0.3}),
            "heusler_x": _subset_weights(at_comp, ["Ni", "Co", "Fe", "Cu"], {"Ni": 0.8, "Co": 0.2}),
            "heusler_y": _subset_weights(at_comp, ["Ti", "Zr", "Hf", "Nb", "V", "Cr", "Mn"], {"Ti": 1.0}),
            "heusler_z": _subset_weights(at_comp, ["Al", "Si", "Ga", "Sn", "Ge"], {"Al": 1.0}),
            "mu_tm": _subset_weights(at_comp, ["Fe", "Co", "Ni", "Cr"], {"Co": 0.5, "Fe": 0.3, "Ni": 0.2}),
            "mu_ref": _subset_weights(at_comp, ["Mo", "W", "Nb", "Ta", "Re"], {"Mo": 0.6, "W": 0.4}),
            "carbide_m": _subset_weights(at_comp, ["Ti", "Nb", "Ta", "Cr", "Mo", "W", "V"], {"Cr": 0.6, "Ti": 0.4}),
            "carbide_c": _subset_weights(at_comp, ["C", "B", "N"], {"C": 1.0}),
            "diamond_si": _subset_weights(at_comp, ["Si", "Ge", "C"], {"Si": 1.0}),
            "graphite_c": {"C": 1.0},
            "imc_cu": _subset_weights(at_comp, ["Cu", "Ni"], {"Cu": 1.0}),
            "imc_al": _subset_weights(at_comp, ["Al", "Mg", "Si"], {"Al": 1.0}),
            "imc_ag": _subset_weights(at_comp, ["Ag", "Cu", "Au"], {"Ag": 0.85, "Cu": 0.15}),
        }
        return roles

    @classmethod
    def _augment_boundary_atoms(
        cls,
        archetype_key: str,
        cell_atoms: List[Dict[str, Any]],
        supercell_n: int,
    ) -> List[Dict[str, Any]]:
        """
        Adds periodic corner/edge image atoms at u=1, v=1, w=1 for small simple Bravais cells
        when supercell_n == 1 so conventional unit-cell cages look complete in 3D view.
        """
        if supercell_n != 1 or archetype_key not in (
            "FCC_A1", "BCC_A2", "B2_CSCL", "L12_CU3AU", "BCT_M", "CARBIDE_B1", "DIAMOND_A4", "HEUSLER_L21"
        ):
            return cell_atoms

        expanded: List[Dict[str, Any]] = []
        seen = set()
        for atom in cell_atoms:
            u0, v0, w0 = atom["frac"]
            shifts_u = (0, 1) if abs(u0) < 1e-4 else (0,)
            shifts_v = (0, 1) if abs(v0) < 1e-4 else (0,)
            shifts_w = (0, 1) if abs(w0) < 1e-4 else (0,)
            for su in shifts_u:
                for sv in shifts_v:
                    for sw in shifts_w:
                        uf, vf, wf = round(u0 + su, 5), round(v0 + sv, 5), round(w0 + sw, 5)
                        key = (uf, vf, wf)
                        if key in seen:
                            continue
                        seen.add(key)
                        copy_atom = dict(atom)
                        copy_atom["frac"] = [uf, vf, wf]
                        copy_atom["is_image"] = (su + sv + sw) > 0
                        expanded.append(copy_atom)
        return expanded

    @classmethod
    def build_phase_model(
        cls,
        phase_name: str,
        phase_fraction: float,
        at_comp: Dict[str, float],
        xrd_lattice: Optional[Dict[str, float]] = None,
        supercell_n: int = 2,
    ) -> Dict[str, Any]:
        """Builds a complete 3D crystal structure + atomic configuration model for one phase."""
        xrd_lattice = xrd_lattice or {}
        archetype_key = cls.map_phase_to_archetype(phase_name)
        arch = cls.ARCHETYPES[archetype_key]
        params, cell = cls._compute_lattice_vectors(archetype_key, at_comp, xrd_lattice)
        roles = cls._build_sublattice_chemistry(archetype_key, at_comp)

        base_sites: List[Tuple[str, Tuple[float, float, float], str]] = arch["sites"]
        # Determine Wyckoff role order for consistent colour index
        role_order: List[str] = []
        for _, _, r in base_sites:
            if r not in role_order:
                role_order.append(r)

        seed = _deterministic_seed(phase_name, at_comp)
        n_rep = max(1, min(3, int(supercell_n)))
        # Keep large TCP cells at max 2x2x2 so 3D viewport stays responsive (< 260 spheres)
        if len(base_sites) >= 12 and n_rep > 2:
            n_rep = 2
        if archetype_key == "AMORPHOUS_LIQUID":
            n_rep = 1

        # Group site slots across the requested supercell by Wyckoff role for stoichiometric sampling
        role_indices: Dict[str, List[Tuple[int, str, Tuple[float, float, float]]]] = {r: [] for r in role_order}
        raw_slots: List[Tuple[str, Tuple[float, float, float], str]] = []
        for ix in range(n_rep):
            for iy in range(n_rep):
                for iz in range(n_rep):
                    for wyckoff, (u, v, w), role in base_sites:
                        idx = len(raw_slots)
                        frac = (u + ix, v + iy, w + iz)
                        raw_slots.append((wyckoff, frac, role))
                        role_indices[role].append((idx, wyckoff, frac))

        assigned_symbols: List[str] = ["Fe"] * len(raw_slots)
        sublattice_breakdown: List[Dict[str, Any]] = []

        for r_idx, role in enumerate(role_order):
            slots = role_indices[role]
            weights = roles.get(role, {"Fe": 1.0})
            picked = _assign_elements_to_slots(len(slots), weights, seed + r_idx * 97)
            for (slot_idx, _, _), sym in zip(slots, picked):
                assigned_symbols[slot_idx] = sym

            wyckoff_names = ", ".join(sorted({w for _, w, _ in slots}))
            occ_str = ", ".join(
                f"{el} {val * 100.0:.1f}%"
                for el, val in sorted(weights.items(), key=lambda kv: -kv[1])
                if val > 0.005
            )
            sublattice_breakdown.append({
                "sublattice_id": f"SL-{r_idx + 1}",
                "wyckoff_sites": wyckoff_names,
                "site_count_per_cell": sum(1 for _, _, r in base_sites if r == role),
                "sublattice_colour": SUBLATTICE_COLOURS[r_idx % len(SUBLATTICE_COLOURS)],
                "occupancy_summary": occ_str,
                "element_fractions": {k: round(float(v), 4) for k, v in weights.items()},
            })

        raw_atoms: List[Dict[str, Any]] = []
        for idx, (wyckoff, frac, role) in enumerate(raw_slots):
            sym = assigned_symbols[idx]
            r_idx = role_order.index(role)
            el_data = get_element(sym)
            rad_pm = float(el_data.radius_pm) if el_data and el_data.radius_pm > 0 else 130.0
            col_hex = el_data.color_hex if el_data and el_data.color_hex else "#3B82F6"
            el_name = el_data.name if el_data else sym
            raw_atoms.append({
                "symbol": sym,
                "element_name": el_name,
                "wyckoff": wyckoff,
                "sublattice": f"SL-{r_idx + 1}",
                "sublattice_colour": SUBLATTICE_COLOURS[r_idx % len(SUBLATTICE_COLOURS)],
                "colour_hex": col_hex,
                "radius_pm": round(rad_pm, 1),
                "radius_a": round(rad_pm * 0.01, 3),
                "frac": [round(frac[0], 5), round(frac[1], 5), round(frac[2], 5)],
                "is_image": False,
            })

        full_atoms = cls._augment_boundary_atoms(archetype_key, raw_atoms, n_rep)

        # Convert fractional coordinates to centred Cartesian coordinates (Angstroms)
        centre_frac = (0.5 * n_rep, 0.5 * n_rep, 0.5 * n_rep)
        centre_cart = _mat_mul_vec(cell, centre_frac)
        atoms_out: List[Dict[str, Any]] = []
        cart_pts: List[Tuple[float, float, float]] = []
        for idx, atom in enumerate(full_atoms):
            uf, vf, wf = atom["frac"]
            px, py, pz = _mat_mul_vec(cell, (uf, vf, wf))
            cx = px - centre_cart[0]
            cy = py - centre_cart[1]
            cz = pz - centre_cart[2]
            cart_pts.append((cx, cy, cz))
            atom["index"] = idx
            atom["x"] = round(cx, 4)
            atom["y"] = round(cy, 4)
            atom["z"] = round(cz, 4)
            atoms_out.append(atom)

        # Compute nearest-neighbour bonds geometrically (within 1.18x shortest interatomic distance)
        bonds: List[Dict[str, Any]] = []
        min_d_sq = float("inf")
        n_at = len(cart_pts)
        for i in range(n_at):
            for j in range(i + 1, n_at):
                d2 = _frac_dist_sq(cart_pts[i], cart_pts[j], cell)
                if d2 > 0.8 and d2 < min_d_sq:
                    min_d_sq = d2

        nn_dist = math.sqrt(min_d_sq) if min_d_sq < float("inf") else 2.55
        cutoff_sq = (nn_dist * 1.18) ** 2
        if archetype_key == "CARBIDE_B1" or archetype_key == "BCT_M":
            cutoff_sq = (nn_dist * 1.38) ** 2

        for i in range(n_at):
            for j in range(i + 1, n_at):
                d2 = _frac_dist_sq(cart_pts[i], cart_pts[j], cell)
                if 0.6 < d2 <= cutoff_sq:
                    bonds.append({
                        "a": i,
                        "b": j,
                        "length_a": round(math.sqrt(d2), 3),
                    })
                    if len(bonds) >= 750:
                        break
            if len(bonds) >= 750:
                break

        # Unit-cell wireframe box vertices (origin-shifted to match centred coordinates)
        box_corners_frac = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
        ]
        box_vertices: List[List[float]] = []
        for u, v, w in box_corners_frac:
            px, py, pz = _mat_mul_vec(cell, (float(u), float(v), float(w)))
            box_vertices.append([
                round(px - centre_cart[0], 4),
                round(py - centre_cart[1], 4),
                round(pz - centre_cart[2], 4),
            ])
        box_edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7],
        ]

        # Characteristic slip-plane polygon inside first unit cell
        slip_poly: List[List[float]] = []
        nrm = arch["slip_plane_normal"]
        if nrm == [1.0, 1.0, 1.0]:
            slip_fracs = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
        elif nrm == [1.0, 1.0, 0.0]:
            slip_fracs = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0)]
        else:
            slip_fracs = [(0.0, 0.0, 0.25), (1.0, 0.0, 0.25), (1.0, 1.0, 0.25), (0.0, 1.0, 0.25)]
        for sf in slip_fracs:
            px, py, pz = _mat_mul_vec(cell, sf)
            slip_poly.append([
                round(px - centre_cart[0], 4),
                round(py - centre_cart[1], 4),
                round(pz - centre_cart[2], 4),
            ])

        burgers_a = round(params["a"] * float(arch["burgers_factor"]), 3)
        # Count discrete species placed in this supercell
        species_counts: Dict[str, int] = {}
        for at in atoms_out:
            species_counts[at["symbol"]] = species_counts.get(at["symbol"], 0) + 1

        return {
            "phase_name": phase_name,
            "archetype": archetype_key,
            "phase_fraction": round(float(phase_fraction), 4),
            "crystal_system": arch["crystal_system"],
            "space_group": arch["space_group"],
            "pearson_symbol": arch["pearson"],
            "strukturbericht": arch["strukturbericht"],
            "prototype": arch["prototype"],
            "lattice_params": params,
            "apf": arch["apf"],
            "coordination_number": arch["coordination_number"],
            "slip_system": arch["slip_system"],
            "burgers_vector_a": burgers_a,
            "nn_distance_a": round(nn_dist, 3),
            "z_formula_units": arch["z_formula_units"],
            "supercell": f"{n_rep}x{n_rep}x{n_rep}",
            "configuration_mode": arch["configuration_mode"],
            "configuration_summary": arch["configuration_summary"],
            "sublattices": sublattice_breakdown,
            "species_counts": species_counts,
            "unit_cell_box": {"vertices": box_vertices, "edges": box_edges},
            "slip_plane_polygon": slip_poly,
            "atoms": atoms_out,
            "bonds": bonds,
        }

    @classmethod
    def build_alloy_crystal_models(
        cls,
        at_comp: Dict[str, float],
        active_phases: Optional[Dict[str, float]] = None,
        xrd_data: Optional[Dict[str, Any]] = None,
        supercell_n: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Builds ordered crystal models for every active phase present in the alloy, sorted by
        phase fraction descending, augmented with secondary XRD / Laves / TCP detections if needed.
        """
        xrd_data = xrd_data or {}
        xrd_lattice = xrd_data.get("lattice_params", xrd_data.get("LatticeParams", {})) or {}

        merged_phases: Dict[str, float] = {}
        if active_phases:
            for pname, frac in active_phases.items():
                if float(frac) > 0.004:
                    merged_phases[str(pname)] = float(frac)

        # Incorporate distinct XRD phases not already covered by archetype
        existing_archetypes = {cls.map_phase_to_archetype(p) for p in merged_phases}
        for xp in xrd_data.get("phases", xrd_data.get("Phases", [])) or []:
            xp_str = str(xp)
            xp_arch = cls.map_phase_to_archetype(xp_str)
            if xp_arch not in existing_archetypes:
                merged_phases[xp_str] = 0.05
                existing_archetypes.add(xp_arch)

        # Fallback if no phases recorded (e.g. direct call)
        if not merged_phases:
            merged_phases["FCC (A1)"] = 1.0

        # Also incorporate solid-state IMC/Laves and TCP (Sigma, Mu, Chi) secondary tendencies when not predominantly liquid
        liquid_frac = sum(v for k, v in merged_phases.items() if "LIQUID" in k.upper())
        if liquid_frac < 0.90:
            try:
                vec_val = 0.0
                r_vals: List[Tuple[float, float]] = []
                for sym, f in at_comp.items():
                    el = get_element(sym)
                    if el:
                        vec_val += float(f) * float(el.vec)
                        r_vals.append((float(f), float(el.radius_pm)))
                r_mean = sum(f * r for f, r in r_vals) or 130.0
                delta_pct = 100.0 * math.sqrt(sum(f * ((1.0 - r / r_mean) ** 2) for f, r in r_vals))
                imc = IMCLavesDatabase.evaluate_formation_tendency(at_comp, vec_val, delta_pct)
                laves_poly = imc.get("LavesPolytype")
                if laves_poly and "LAVES" not in " ".join(existing_archetypes) and float(imc.get("MaxLavesFraction", 0.0)) >= 0.05:
                    tag = "Laves_C15" if "C15" in str(laves_poly) else "Laves_C14"
                    merged_phases[tag] = float(imc.get("MaxLavesFraction", 0.05))
                    existing_archetypes.add(cls.map_phase_to_archetype(tag))

                max_sigma = float(imc.get("MaxSigmaFraction", 0.0))
                if max_sigma >= 0.015 and "SIGMA_D8B" not in existing_archetypes:
                    merged_phases["Sigma"] = max_sigma
                    existing_archetypes.add("SIGMA_D8B")

                max_mu = float(imc.get("MaxMuFraction", 0.0))
                if max_mu >= 0.04 and "MU_D85" not in existing_archetypes:
                    merged_phases["Mu_Phase"] = max_mu
                    existing_archetypes.add("MU_D85")

                max_chi = float(imc.get("MaxChiFraction", 0.0))
                if max_chi >= 0.03 and "CHI_A12" not in existing_archetypes:
                    merged_phases["Chi_A12"] = max_chi
                    existing_archetypes.add("CHI_A12")
            except Exception:
                pass

        ordered = sorted(merged_phases.items(), key=lambda kv: -kv[1])
        return [
            cls.build_phase_model(
                phase_name=pname,
                phase_fraction=pfrac,
                at_comp=at_comp,
                xrd_lattice=xrd_lattice,
                supercell_n=supercell_n,
            )
            for pname, pfrac in ordered
        ]
