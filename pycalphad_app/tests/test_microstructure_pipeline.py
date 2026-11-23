"""
Unit tests for the Second-Stage Microstructural Mesoscale Simulation Layer:
- Population Balance Model (KWN Precipitation Kinetics)
- Potts Monte Carlo (Grain Growth & Dynamic Zener Pinning)
- Microstructure Pipeline Coupling
"""

import pytest
import math
from pycalphad_app.core.population_balance_engine import PopulationBalanceEngine
from pycalphad_app.core.monte_carlo_engine import MonteCarloEngine
from pycalphad_app.core.microstructure_pipeline import MicrostructurePipeline


def test_population_balance_nucleation_and_growth():
    pbm = PopulationBalanceEngine(
        phase_name="Gamma_Prime",
        t_kelvin=1073.15,
        matrix_c0=0.14,
        matrix_ce=0.04,
        precip_cp=0.25,
        gamma_interfacial=0.035,
        eq_phase_fraction=0.15
    )

    r_star, delta_g_star, j_nuc = pbm.compute_critical_nucleus(0.14)
    assert r_star > 0.0, "Critical radius must be strictly positive."
    assert delta_g_star > 0.0, "Activation energy barrier must be positive."
    assert j_nuc >= 0.0, "Nucleation rate must be non-negative."

    # Solve across 10 hours
    res = pbm.solve(total_time_seconds=36000.0, n_bins=50, n_time_steps=80)
    assert res["volume_fraction_final"] > 0.0, "Volume fraction must increase."
    assert res["volume_fraction_final"] <= 0.1501, "Volume fraction must be bounded by CALPHAD eq fraction."
    assert res["mean_radius_nm_final"] > 0.0, "Mean radius must be positive."

    psd = res["psd_histogram"]
    assert len(psd["radius_nm"]) == 50
    assert len(psd["normalized_frequency"]) == 50


def test_monte_carlo_grain_growth_and_zener_pinning():
    mc = MonteCarloEngine(
        initial_grain_size_um=25.0,
        temp_kelvin=1273.15,
        gb_energy_j_m2=0.62,
        hall_petch_k=0.55
    )

    p_zener, d_limit_um = mc.compute_zener_drag(f_precip=0.08, r_precip_m=15e-9)
    assert p_zener > 0.0, "Zener drag pressure must be positive."
    assert d_limit_um > 0.0, "Zener limit grain size must be positive."

    sig_hp = mc.compute_hall_petch_strength(25.0)
    assert 90.0 <= sig_hp <= 130.0, f"Expected Hall-Petch strength ~110 MPa, got {sig_hp}"

    # Solve coupled grain growth
    res = mc.solve(
        total_time_seconds=36000.0,
        precip_volume_fraction=0.08,
        precip_mean_radius_nm=15.0,
        n_time_steps=50
    )
    assert res["final_grain_size_um"] >= 25.0, "Grain size must not decrease during annealing."
    assert "potts_simulation" in res
    assert "topological_distribution" in res["potts_simulation"]


def test_microstructure_pipeline_execution():
    thermo_res = {
        "Solidus_K": 1550.0,
        "Phases": {"FCC": 0.85, "Gamma_Prime": 0.15},
        "composition": {"Ni": 0.55, "Cr": 0.20, "Al": 0.15, "Ti": 0.10}
    }
    mech_res = {
        "YieldStrength_MPa": 380.0,
        "SolidSolutionHardening_MPa": 125.0
    }

    res = MicrostructurePipeline.execute(
        thermo_res=thermo_res,
        trans_res={},
        phase_curves={},
        mech_res=mech_res,
        user_opts={"grain_size_um": 20.0, "heat_treatment_hours": 15.0}
    )

    assert "population_balance" in res
    assert "monte_carlo_grain_growth" in res
    assert "strengthening_breakdown" in res

    sb = res["strengthening_breakdown"]
    assert sb["total_resolved_yield_strength_mpa"] > sb["matrix_friction_stress_mpa"]
    assert sb["hall_petch_grain_boundary_mpa"] > 0.0


def test_microstructure_pipeline_am_options_and_hatch_pitch():
    thermo_res = {
        "Solidus_K": 1600.0,
        "Phases": {"FCC": 0.90, "Laves": 0.10},
        "composition": {"Fe": 0.40, "Cr": 0.20, "Ni": 0.20, "Mo": 0.10, "Nb": 0.10}
    }
    mech_res = {
        "YieldStrength_MPa": 400.0,
        "SolidSolutionHardening_MPa": 140.0
    }

    # Standard L-PBF processing options
    res_std = MicrostructurePipeline.execute(
        thermo_res=thermo_res,
        trans_res={},
        phase_curves={},
        mech_res=mech_res,
        user_opts={
            "grain_size_um": 15.0,
            "hatch_pitch_um": 80.0,
            "laser_power_w": 275.0,
            "scan_speed_mm_s": 800.0,
            "layer_thickness_um": 30.0,
            "cold_work_pct": 10.0
        }
    )

    enh = res_std["enhanced_properties"]
    sb = res_std["strengthening_breakdown"]

    assert enh["volumetric_energy_density_j_mm3"] > 140.0
    assert "Optimal Conduction" in enh["porosity_regime"]
    assert enh["cooling_rate_k_s"] > 1e4
    assert enh["cellular_spacing_um"] > 0.0
    assert sb["cellular_subgrain_boundary_mpa"] > 0.0
    assert sb["cold_work_dislocation_mpa"] > 0.0

    # Finer hatch pitch produces higher cooling rate and higher cellular strengthening
    res_fine = MicrostructurePipeline.execute(
        thermo_res=thermo_res,
        trans_res={},
        phase_curves={},
        mech_res=mech_res,
        user_opts={
            "grain_size_um": 15.0,
            "hatch_pitch_um": 40.0,
            "laser_power_w": 275.0,
            "scan_speed_mm_s": 800.0,
            "layer_thickness_um": 30.0
        }
    )

    assert res_fine["enhanced_properties"]["cooling_rate_k_s"] > res_std["enhanced_properties"]["cooling_rate_k_s"]
    assert res_fine["strengthening_breakdown"]["cellular_subgrain_boundary_mpa"] > res_std["strengthening_breakdown"]["cellular_subgrain_boundary_mpa"]
