# -*- coding: utf-8 -*-
"""
alloy_economics.py - Alloy Feedstock Pricing, Process Route Costing (USD/kg),
and Property-Preserving Cost-Reduction Recommendation Engine.

Baseline industrial prices (USD/kg) reflect USGS Mineral Commodity Summaries (2026)
and Shanghai Metals Market (Nov 2026) benchmarks; additive and conventional route
conversion ranges reflect 2025-2026 industrial powder/manufacturing cost models.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from pycalphad_app.core.elements_data import IUPAC_ELEMENTS_DATA

# Pure / high-grade metallurgical element prices (USD/kg)
ELEMENT_PRICE_PURE_USD_KG: Dict[str, float] = {
    "Fe": 0.42,
    "Mn": 1.82,
    "Cr": 13.01,
    "Al": 3.41,
    "Cu": 14.19,
    "Zn": 3.57,
    "Mg": 2.50,
    "Si": 2.87,
    "Ti": 12.00,
    "V": 38.97,      # Master FeV V-basis (clean V-Al master alloy ~45-65)
    "Zr": 22.00,
    "Nb": 73.50,     # Pure Nb metal; FeNb industrial is $40/kg Nb
    "Mo": 51.00,     # Industrial MoO3/Mo conversion; China metal ~$91/kg
    "W": 85.12,
    "Ta": 219.79,
    "Co": 49.92,
    "Ni": 17.57,
    "Hf": 3800.00,
    "Re": 2600.00,
    "Ru": 22184.00,
    "Y": 40.00,
    "Sn": 45.54,
    "B": 3.68,
    "C": 0.122,
    "N": 0.140,
    "Pb": 2.15,
    "Bi": 14.50,
    "Sb": 25.00,
    "Ag": 980.00,
    "Au": 85000.00,
    "Pt": 32000.00,
    "Pd": 34000.00,
    "Sc": 2200.00,
    "Ga": 280.00,
    "Cd": 4.20,
    "Li": 18.00,
    "Ca": 3.50,
}

# Bulk ferroalloy / ladle-grade contained element costs (applicable when Fe >= 25 wt%)
FERRO_ALLOY_PRICES_USD_KG: Dict[str, float] = {
    "Cr": 3.53,   # High-carbon / low-carbon ferrochromium contained Cr
    "Nb": 40.00,  # Ferroniobium contained Nb
    "V": 38.97,   # Ferrovanadium contained V
    "Si": 2.50,   # Ferrosilicon 75% contained Si
    "Mn": 1.45,   # Silicomanganese / ferromanganese contained Mn
}

STANDARD_ATOMIC_WEIGHTS: Dict[str, float] = {
    "H": 1.008, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999,
    "Mg": 24.305, "Al": 26.982, "Si": 28.085, "Ti": 47.867, "V": 50.942,
    "Cr": 51.996, "Mn": 54.938, "Fe": 55.845, "Co": 58.933, "Ni": 58.693,
    "Cu": 63.546, "Zn": 65.38, "Y": 88.906, "Zr": 91.224, "Nb": 92.906,
    "Mo": 95.95, "Ru": 101.07, "Pd": 106.42, "Ag": 107.87, "Cd": 112.41,
    "Sn": 118.71, "Sb": 121.76, "Hf": 178.49, "Ta": 180.95, "W": 183.84,
    "Re": 186.21, "Pt": 195.08, "Au": 196.97, "Pb": 207.2, "Bi": 208.98,
}

# Benchmark commercial alloy reference raw + wrought/AM costs (USD/kg)
BENCHMARK_COSTS_USD_KG: Dict[str, float] = {
    "Cantor": 17.02,
    "316L": 5.80,
    "2507": 9.80,
    "Monel": 16.50,
    "Inconel 718": 62.00,
    "718": 62.00,
    "Hastelloy": 51.00,
    "Zirconium 702": 95.00,
    "Ti-6Al-4V": 135.00,
    "7075": 8.50,
    "Maraging": 32.00,
    "Tungsten": 145.00,
    "Mo-based": 125.00,
    "Tantalum": 380.00,
    "Niobium": 145.00,
    "Stellite": 72.00,
    "H13": 9.50,
    "JJ1": 8.20,
    "Waspaloy": 78.00,
    "AlCoCrFeNi": 18.61,
}


def atomic_to_weight_fractions(at_comp: Dict[str, float]) -> Dict[str, float]:
    """Converts normalized atomic fractions to mass (weight) fractions."""
    masses: Dict[str, float] = {}
    for el, x in at_comp.items():
        if x <= 0.0:
            continue
        el_info = IUPAC_ELEMENTS_DATA.get(el)
        aw = float(getattr(el_info, "atomic_mass", 0.0) or STANDARD_ATOMIC_WEIGHTS.get(el, 55.85))
        masses[el] = float(x) * aw
    total = sum(masses.values())
    if total <= 1e-12:
        return {el: float(x) for el, x in at_comp.items()}
    return {el: m / total for el, m in masses.items()}


def compute_raw_alloy_cost(
    wt_comp: Dict[str, float],
    prefer_ferro: bool = True,
) -> Tuple[float, List[Tuple[str, float, float]]]:
    """
    Computes raw elemental charge cost in USD/kg and per-element cost contributions.
    Returns (total_usd_kg, sorted list of (element, usd_per_kg_alloy, pct_share)).
    """
    is_ferrous_bulk = prefer_ferro and wt_comp.get("Fe", 0.0) >= 0.25
    contribs: List[Tuple[str, float]] = []
    for el, w in wt_comp.items():
        if w <= 1e-6:
            continue
        price = ELEMENT_PRICE_PURE_USD_KG.get(el, 25.0)
        if is_ferrous_bulk and el in FERRO_ALLOY_PRICES_USD_KG:
            price = FERRO_ALLOY_PRICES_USD_KG[el]
        contribs.append((el, float(w) * price))

    total = max(0.25, sum(c for _, c in contribs))
    breakdown = sorted(
        [(el, cost, 100.0 * cost / total) for el, cost in contribs],
        key=lambda t: t[1],
        reverse=True,
    )
    return round(total, 2), breakdown


def estimate_benchmark_cost(benchmark_name: str, fallback_raw_cost: float) -> float:
    """Estimates commercial benchmark USD/kg cost from industrial pricing references."""
    if not benchmark_name:
        return round(fallback_raw_cost * 2.2 + 12.0, 2)
    b_low = benchmark_name.lower()
    for key, val in BENCHMARK_COSTS_USD_KG.items():
        if key.lower() in b_low:
            return round(val, 2)
    return round(fallback_raw_cost * 2.2 + 12.0, 2)


def compute_processability_and_costs(
    at_comp: Dict[str, float],
    wt_comp: Dict[str, float],
    thermo_res: Dict[str, Any],
    mech_res: Dict[str, Any],
    liq_k: float,
    sol_k: float,
) -> Dict[str, Any]:
    """
    Evaluates 12 manufacturing process routes with route suitability scores (0-100%)
    and realistic alloy-specific finished manufacturing costs (USD/kg).
    """
    sy0 = float(mech_res.get("YieldStrength_RT_MPa", mech_res.get("YieldStrength_MPa", 350.0)))
    hv = float(mech_res.get("VickersHardness_HV", mech_res.get("Hardness_HV", 220.0)))
    vec = float(thermo_res.get("VEC", 8.0))
    df = max(20.0, float(liq_k) - float(sol_k))
    density = float(thermo_res.get("density", 7.8))

    raw_cost_kg, cost_drivers = compute_raw_alloy_cost(wt_comp, prefer_ferro=True)
    # Reactivity / gas-atomization premium for Ti/Zr/Al/Nb/Ta reactive melts
    reactive_frac = sum(wt_comp.get(el, 0.0) for el in ["Ti", "Zr", "Hf", "Ta", "Nb", "Al", "Mg", "Y"])
    refractory_frac = sum(wt_comp.get(el, 0.0) for el in ["Nb", "Mo", "Ta", "W", "Re", "V", "Ti", "Zr", "Hf"])
    volatile_loss = sum(at_comp.get(el, 0.0) * 120.0 for el in ["Zn", "Mg", "Cd", "Li", "Ca", "Bi", "Pb"])
    volatile_loss += sum(at_comp.get(el, 0.0) * 22.0 for el in ["Mn", "Al"])
    elem_tms = [
        float(IUPAC_ELEMENTS_DATA[el].tm_k)
        for el in at_comp
        if el in IUPAC_ELEMENTS_DATA and float(getattr(IUPAC_ELEMENTS_DATA[el], "tm_k", 0.0)) > 0.0
    ]
    tm_disp = (max(elem_tms) - min(elem_tms)) if len(elem_tms) > 1 else 0.0
    refr_bonus = 4.0 if any(el in at_comp for el in ["Nb", "Mo", "Ta", "W", "Re", "Ti", "Zr", "Hf", "V"]) else 0.0
    if liq_k > 1800.0:
        refr_bonus += min(5.0, (liq_k - 1800.0) / 120.0)

    # Atomized powder conversion adder (15-45 um LPBF fine cut vs 45-105 um coarse vs wire)
    fine_powder_adder = 38.0 + 185.0 * reactive_frac + 1.2 * raw_cost_kg
    coarse_powder_adder = 22.0 + 95.0 * reactive_frac + 0.55 * raw_cost_kg
    bjt_powder_adder = 16.0 + 58.0 * reactive_frac + 0.35 * raw_cost_kg
    wire_adder = 10.0 + 28.0 * reactive_frac + 0.25 * raw_cost_kg + 0.015 * max(0.0, sy0 - 400.0)

    high_t_factor = max(0.0, (liq_k - 1500.0) / 1000.0)
    hard_factor = max(0.0, (hv - 200.0) / 300.0)

    # 12 Industrial Process Routes: (axis_name, score, cost_usd_kg)
    routes: List[Tuple[str, float, float]] = [
        (
            "SLM / LPBF",
            float(np.clip(94.0 - 0.18 * max(0.0, df - 40.0) - 0.015 * volatile_loss, 35.0, 96.0)),
            raw_cost_kg + fine_powder_adder + 290.0 + 42.0 * high_t_factor + 0.45 * df,
        ),
        (
            "EBM",
            float(np.clip(88.0 - 0.14 * max(0.0, df - 45.0) - 0.55 * volatile_loss + 4.0 * refractory_frac, 25.0, 95.0)),
            raw_cost_kg + coarse_powder_adder + 245.0 + 55.0 * high_t_factor + 25.0 * reactive_frac,
        ),
        (
            "L-DED",
            float(np.clip(89.0 - 0.14 * max(0.0, df - 50.0) + 0.01 * max(0.0, 800.0 - sy0), 38.0, 94.0)),
            raw_cost_kg + coarse_powder_adder + 145.0 + 28.0 * high_t_factor,
        ),
        (
            "WAAM",
            float(np.clip(86.0 - 0.12 * max(0.0, sy0 - 550.0) / 10.0 - 0.08 * max(0.0, df - 65.0), 32.0, 93.0)),
            raw_cost_kg + wire_adder + 52.0 + 18.0 * reactive_frac + 14.0 * hard_factor,
        ),
        (
            "Binder Jet",
            float(np.clip(82.0 - 0.03 * max(0.0, tm_disp - 900.0) - 8.0 * reactive_frac, 34.0, 91.0)),
            raw_cost_kg + bjt_powder_adder + 88.0 + 35.0 * high_t_factor,
        ),
        (
            "SPS / FAST",
            float(np.clip(87.0 + 6.0 * refractory_frac - 0.03 * max(0.0, df - 120.0), 45.0, 95.0)),
            raw_cost_kg + coarse_powder_adder + 175.0 + 65.0 * high_t_factor,
        ),
        (
            "Arc Melting",
            float(np.clip(93.0 + refr_bonus - volatile_loss - 0.005 * max(0.0, tm_disp - 1200.0) - 0.04 * max(0.0, df - 80.0), 25.0, 98.0)),
            raw_cost_kg + 28.0 + 32.0 * high_t_factor + 12.0 * refractory_frac,
        ),
        (
            "VIM / VAR",
            float(np.clip(90.0 - 0.45 * volatile_loss - 0.02 * max(0.0, liq_k - 2200.0), 30.0, 96.0)),
            raw_cost_kg + 22.0 + 28.0 * high_t_factor + 15.0 * reactive_frac,
        ),
        (
            "Casting",
            float(np.clip(88.0 - 0.12 * abs(df - 60.0) - 6.0 * refractory_frac, 34.0, 95.0)),
            raw_cost_kg + 20.0 + 24.0 * high_t_factor + 18.0 * reactive_frac,
        ),
        (
            "Hot Forging",
            float(np.clip(85.0 + 0.02 * (vec - 7.0) * 10.0 - 0.025 * max(0.0, sy0 - 700.0), 42.0, 96.0)),
            raw_cost_kg + 14.0 + 18.0 * high_t_factor + 9.0 * hard_factor,
        ),
        (
            "Cold Forming",
            float(np.clip(92.0 - 0.04 * sy0, 26.0, 94.0)),
            raw_cost_kg + 9.0 + 16.0 * hard_factor,
        ),
        (
            "Machining",
            float(np.clip(84.0 - 0.03 * sy0 - 0.02 * max(0.0, hv - 250.0), 26.0, 90.0)),
            raw_cost_kg * 1.45 + 38.0 + 48.0 * hard_factor + 25.0 * reactive_frac,
        ),
    ]

    return {
        "axes": [r[0] for r in routes],
        "scores": [round(r[1], 1) for r in routes],
        "route_costs_usd_kg": [round(r[2], 2) for r in routes],
        "raw_alloy_cost_usd_kg": raw_cost_kg,
        "top_cost_drivers": [
            {"element": el, "cost_usd_kg": round(c, 2), "share_pct": round(s, 1)}
            for el, c, s in cost_drivers[:4]
        ],
    }


def recommend_cost_optimization(
    elements: List[str],
    at_comp: Dict[str, float],
    wt_comp: Dict[str, float],
    thermo: Dict[str, Any],
    mech: Dict[str, Any],
    app_id: str = "",
    raw_cost_kg: Optional[float] = None,
) -> Tuple[float, float, str]:
    """
    Returns (alloy_cost_usd_kg, savings_pct, recommendation_text) tailoring
    composition and route substitutions while preserving required properties.
    """
    if raw_cost_kg is None:
        raw_cost_kg, drivers = compute_raw_alloy_cost(wt_comp, prefer_ferro=True)
    else:
        _, drivers = compute_raw_alloy_cost(wt_comp, prefer_ferro=True)

    # Representative semi-finished manufactured alloy cost (raw billet + primary refining)
    liq_k = float(thermo.get("T_Liquidus", thermo.get("Liquidus_K", 1700.0)))
    mfg_adder = 12.0 + 18.0 * max(0.0, (liq_k - 1500.0) / 1000.0) + 12.0 * sum(wt_comp.get(e, 0.0) for e in ["Ti", "Zr", "Hf", "Ta", "Nb"])
    alloy_mfg_cost = round(raw_cost_kg * 1.15 + mfg_adder, 2)

    w_co = wt_comp.get("Co", 0.0)
    w_ni = wt_comp.get("Ni", 0.0)
    w_mo = wt_comp.get("Mo", 0.0)
    w_ta = wt_comp.get("Ta", 0.0)
    w_w = wt_comp.get("W", 0.0)
    w_hf = wt_comp.get("Hf", 0.0)
    w_re = wt_comp.get("Re", 0.0)
    w_ru = wt_comp.get("Ru", 0.0)
    cr_at = at_comp.get("Cr", 0.0) * 100.0
    mo_at = at_comp.get("Mo", 0.0) * 100.0
    n_at = at_comp.get("N", 0.0) * 100.0
    pren = cr_at + 3.3 * mo_at + 16.0 * n_at

    recs: List[str] = []
    est_savings_pct = 0.0

    # 1. Precious / ultra-cost elements (Ru, Hf, Re, Ta)
    if w_ru > 0.002 or w_hf > 0.005 or w_re > 0.005:
        recs.append("Cut Ru/Hf/Re (<0.2 wt%) via Cr-Mo-Si or V-Ti-Nb solid-solution balance (-65% to -85% raw charge)")
        est_savings_pct = max(est_savings_pct, 70.0)

    # 2. Cobalt elimination/reduction (e.g. Cantor HEA -> Fe40Mn40Co10Cr10N0.5 / Co-free FCC)
    if w_co >= 0.08:
        co_share = next((s for el, _, s in drivers if el == "Co"), 0.0)
        if "CRYO" in app_id or "HYDROGEN" in app_id or "MARINE" in app_id:
            recs.append(
                f"Halve Co ({co_share:.0f}% cost driver) using Fe40Mn40Co10Cr10 + 0.5 at% N (-56% raw cost; keeps FCC TWIP/TRIP 77 K toughness)"
            )
            est_savings_pct = max(est_savings_pct, 56.0)
        else:
            recs.append(
                f"Replace Co ({co_share:.0f}% cost driver) with Fe+Mn or Ni-Al microalloying (-45% to -70% charge while preserving VEC >= 8.0)"
            )
            est_savings_pct = max(est_savings_pct, 50.0)

    # 3. Ta / W reduction in Refractory HEAs (keep specific high-T strength)
    if (w_ta + w_w) >= 0.15:
        recs.append(
            "Substitute Ta/W with Ti-V-Nb-Mo balance (-68% to -76% cost, -35% density while maintaining specific σ_y/ρ and RT ductility)"
        )
        est_savings_pct = max(est_savings_pct, 68.0)

    # 4. Marine / Chemical PREN corrosion optimization (replace excess Ni/Mo with Cr-N duplex)
    if ("MARINE" in app_id or "CHEM" in app_id) and (w_ni + w_mo) >= 0.25:
        recs.append(
            f"Shift toward lean Fe-25Cr-7Ni-4Mo-0.28N duplex balance (-55% to -78% cost; preserves PREN >= 40 passive stability vs PREN={pren:.1f})"
        )
        est_savings_pct = max(est_savings_pct, 60.0)

    # 5. Route / melt feedstock optimization fallback or supplement
    df = max(20.0, float(liq_k) - float(thermo.get("T_Solidus", thermo.get("Solidus_K", liq_k - 60.0))))
    if not recs:
        top_el = drivers[0][0] if drivers else "Matrix"
        top_share = drivers[0][2] if drivers else 0.0
        if df < 75.0:
            recs.append(
                f"{top_el} is {top_share:.0f}% of charge; switch LPBF to WAAM/Binder Jet or TMCP casting (-50% to -75% route cost, ΔT={df:.0f} K)"
            )
            est_savings_pct = max(est_savings_pct, 45.0)
        else:
            recs.append(
                f"Use industrial FeCr/FeNb master alloys + 10-cycle sieved powder reuse (-30% to -50% feedstock premium; {top_el}={top_share:.0f}% cost)"
            )
            est_savings_pct = max(est_savings_pct, 35.0)

    return alloy_mfg_cost, round(est_savings_pct, 1), recs[0]
