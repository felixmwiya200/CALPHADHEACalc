# -*- coding: utf-8 -*-
"""
test_hea_engine.py - Unit and benchmark tests for HEAEngine
Tests equiatomic Cantor alloy CoCrFeMnNi (VEC >= 8.0 FCC stability, AdaptiveContinuationSolver
thermodynamic integration, Varvenne-Curtin solid solution strengthening)
and refractory BCC HEA NbMoTaW.
"""

import pytest
from pycalphad_app.core.hea_engine import HEAEngine


def test_cantor_hea_equiatomic_fcc():
    # Cantor alloy: Co20 Cr20 Fe20 Mn20 Ni20 (at. %)
    # Mass fractions: Fe=19.86, Co=20.95, Ni=20.87, Cr=18.49, Mn=19.53
    comp = {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53}
    engine = HEAEngine("High-Entropy Alloys (HEAs)", comp, grain_size_um=20.0, process_type="Arc Melt / Cast")

    # 1. Phase transformations and VEC
    trans = engine.compute_phase_transformations()
    assert "VEC" in trans
    # For Cantor alloy: VEC = 0.2*(9 + 6 + 8 + 7 + 10) = 8.0 -> FCC solid solution
    assert 7.95 <= trans["VEC"] <= 8.05
    assert trans["PhasePrediction_Guo"] == "Single Phase FCC"

    # 2. Thermodynamics (Adaptive continuation solver)
    thermo = engine.compute_thermodynamics()
    assert "Phases" in thermo
    assert "FCC" in thermo["Phases"] or "FCC_A1" in thermo["Phases"]
    # Cantor melting interval: Solidus ~ 1280 C (1553 K), Liquidus ~ 1340 C (1613 K)
    assert 1500.0 <= thermo["T_Solidus"] <= 1590.0
    assert 1580.0 <= thermo["T_Liquidus"] <= 1650.0

    # 3. Mechanical properties (Varvenne-Curtin model)
    mech = engine.compute_mechanical_properties(thermo, trans)
    # Cantor proof strength ~ 200 - 280 MPa at RT, UTS ~ 500 - 650 MPa, Elongation ~ 40 - 55%
    assert 180.0 <= mech["YieldStrength_MPa"] <= 300.0
    assert mech["UTS_MPa"] >= 450.0
    assert mech["Elongation_pct"] >= 35.0


def test_refractory_hea_bcc():
    # Equiatomic NbMoTaW: BCC refractory HEA
    comp = {"Nb": 17.5, "Mo": 18.1, "Ta": 34.1, "W": 34.7}  # approx equiatomic
    engine = HEAEngine("High-Entropy Alloys (HEAs)", comp, grain_size_um=40.0, process_type="Arc Melt / Cast")

    trans = engine.compute_phase_transformations()
    # VEC of Nb(5), Mo(6), Ta(5), W(6) = 5.5 < 6.87 -> Single Phase BCC
    assert trans["VEC"] < 6.87
    assert "BCC" in trans["PhasePrediction_Guo"]

    thermo = engine.compute_thermodynamics()
    # Very high melting point > 2500 K
    assert thermo["T_Solidus"] >= 2500.0


def test_hea_multi_archetype_physics_discrimination():
    """Verifies authentic chemistry-driven differentiation across 5 distinct HEA classes."""
    cantor = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53},
        grain_size_um=20.0,
        process_type="Arc Melt / Cast",
    )
    nbmotaw = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Nb": 17.5, "Mo": 18.1, "Ta": 34.1, "W": 34.7},
        grain_size_um=20.0,
        process_type="Arc Melt / Cast",
    )
    tizrhfnbta = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Ti": 9.75, "Zr": 18.58, "Hf": 36.35, "Nb": 18.92, "Ta": 36.85},
        grain_size_um=20.0,
        process_type="Arc Melt / Cast",
    )
    lwhea = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Al": 17.87, "Li": 4.60, "Mg": 16.10, "Sc": 29.78, "Ti": 31.71},
        grain_size_um=20.0,
        process_type="Arc Melt / Cast",
    )
    alcocrfeni = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Al": 10.67, "Co": 23.31, "Cr": 20.57, "Fe": 22.09, "Ni": 23.22},
        grain_size_um=20.0,
        process_type="Arc Melt / Cast",
    )

    out = {}
    for name, eng in (
        ("cantor", cantor),
        ("nbmotaw", nbmotaw),
        ("tizrhfnbta", tizrhfnbta),
        ("lwhea", lwhea),
        ("alcocrfeni", alcocrfeni),
    ):
        tr = eng.compute_phase_transformations()
        th = eng.compute_thermodynamics()
        mc = eng.compute_mechanical_properties(th, tr)
        tp = eng.compute_transport_properties(th)
        cr, ox = eng.compute_environmental_properties(th)
        out[name] = (tr, th, mc, tp, cr, ox)

    # Phase selection and Yang-Zhang Omega stability
    assert "B2" in out["alcocrfeni"][1]["Phases"]
    assert out["cantor"][0]["Omega_Parameter"] > 1.1
    assert out["cantor"][0]["SS_Criterion_YangZhang"] is True

    # Thermophysical ordering: density and Neumann-Kopp Cp
    assert (
        out["lwhea"][3]["TheoreticalDensity_g_cm3"]
        < out["alcocrfeni"][3]["TheoreticalDensity_g_cm3"]
        < out["cantor"][3]["TheoreticalDensity_g_cm3"]
        < out["tizrhfnbta"][3]["TheoreticalDensity_g_cm3"]
        < out["nbmotaw"][3]["TheoreticalDensity_g_cm3"]
    )
    assert (
        out["lwhea"][3]["SpecificHeat_J_kgK"]
        > out["alcocrfeni"][3]["SpecificHeat_J_kgK"]
        > out["cantor"][3]["SpecificHeat_J_kgK"]
        > out["nbmotaw"][3]["SpecificHeat_J_kgK"]
    )
    assert out["lwhea"][3]["CTE_1e6_K"] > 18.0
    assert out["nbmotaw"][3]["CTE_1e6_K"] < 8.0

    # Elastic moduli and mechanical strength contrast
    assert out["tizrhfnbta"][2]["YoungsModulus_GPa"] < out["cantor"][2]["YoungsModulus_GPa"] < out["nbmotaw"][2]["YoungsModulus_GPa"]
    assert out["nbmotaw"][2]["YieldStrength_MPa"] > 850.0
    assert out["nbmotaw"][2]["Elongation_pct"] < 12.0
    assert out["tizrhfnbta"][2]["Elongation_pct"] > 25.0
    assert out["nbmotaw"][2]["Hardness_HRC"] > 30.0
    assert out["cantor"][2]["Hardness_HRB"] > 50.0

    # Environmental passivation, PREN, and oxidation scale physics
    assert out["nbmotaw"][4]["PREN"] == 0.0
    assert out["cantor"][4]["PREN"] > 15.0
    assert out["alcocrfeni"][5]["DominantScale"] == "alpha-Al2O3 Passivation Scale"
    assert out["alcocrfeni"][5]["kp_g2_cm4_s"] < out["cantor"][5]["kp_g2_cm4_s"] < out["nbmotaw"][5]["kp_g2_cm4_s"]
    assert out["lwhea"][4]["Ecorr_V"] < -0.80


def test_hea_grain_size_and_cooling_rate_sensitivity():
    """Verifies Hall-Petch grain refinement and cooling-rate kinetic/subcell effects."""
    comp_al = {"Al": 10.67, "Co": 23.31, "Cr": 20.57, "Fe": 22.09, "Ni": 23.22}
    fine = HEAEngine("High-Entropy Alloys (HEAs)", comp_al, grain_size_um=5.0, process_type="Wrought")
    coarse = HEAEngine("High-Entropy Alloys (HEAs)", comp_al, grain_size_um=80.0, process_type="Wrought")
    rapid = HEAEngine("High-Entropy Alloys (HEAs)", comp_al, grain_size_um=20.0, process_type="Laser Clad / DED")

    m_fine = fine.compute_mechanical_properties(fine.compute_thermodynamics(), fine.compute_phase_transformations())
    m_coarse = coarse.compute_mechanical_properties(coarse.compute_thermodynamics(), coarse.compute_phase_transformations())
    th_slow = coarse.compute_thermodynamics()
    th_rapid = rapid.compute_thermodynamics()
    m_rapid = rapid.compute_mechanical_properties(th_rapid, rapid.compute_phase_transformations())

    assert m_fine["YieldStrength_MPa"] > m_coarse["YieldStrength_MPa"]
    assert m_fine["HallPetchContribution_MPa"] > m_coarse["HallPetchContribution_MPa"]
    assert m_rapid["CoolingRateHardening_MPa"] > m_fine["CoolingRateHardening_MPa"]
    assert th_rapid["Phases"].get("Sigma", 0.0) < th_slow["Phases"].get("Sigma", 0.0)


def test_hea_single_temperature_step_and_daemon_contracts():
    """Checks G(T), Sy(T), HV(T)/HRC/HRB evolution, L12 ordering, and IPC keys."""
    cantor = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53},
        grain_size_um=20.0,
    )
    s150 = cantor.compute_single_temperature_step(150.0)
    s300 = cantor.compute_single_temperature_step(300.0)
    s1100 = cantor.compute_single_temperature_step(1100.0)
    s2000 = cantor.compute_single_temperature_step(2000.0)

    assert s150["YieldStrength_MPa"] > s300["YieldStrength_MPa"] > s1100["YieldStrength_MPa"] > s2000["YieldStrength_MPa"]
    assert s2000["YieldStrength_MPa"] == 0.0
    assert s2000["DominantPhase"] == "Liquid"
    assert s150["GibbsEnergy_J_mol"] > s300["GibbsEnergy_J_mol"] > s1100["GibbsEnergy_J_mol"] > s2000["GibbsEnergy_J_mol"]
    assert all(k in s300 for k in ("Hardness_HV", "Hardness_HRC", "Hardness_HRB", "RockwellHardness"))

    # L12 gamma-prime strengthened FCC HEA: (FeCoNi)86Al7Ti7 approx mass%
    l12_comp = {"Fe": 30.2, "Co": 31.8, "Ni": 31.7, "Al": 3.6, "Ti": 6.3}
    l12_eng = HEAEngine("High-Entropy Alloys (HEAs)", l12_comp, grain_size_um=20.0)
    tr = l12_eng.compute_phase_transformations()
    th = l12_eng.compute_thermodynamics()
    mc = l12_eng.compute_mechanical_properties(th, tr)
    tp = l12_eng.compute_transport_properties(th)
    cr, ox = l12_eng.compute_environmental_properties(th)

    assert "L12" in th["Phases"]
    assert th["Phases"]["L12"] > 0.10
    assert mc["PrecipitationHardening_MPa"] > 100.0
    for key in ("StrengthCoeff_K_MPa", "StrainHardening_n", "Hardness_HRC", "Hardness_HRB"):
        assert key in mc
    for key in ("ElectricalResistivity_uOhm_cm", "ElectricalConductivity_MS_m"):
        assert key in tp
    assert "PartitionCoeff" in th
    for key in ("Ecorr_V", "Ecorr_V_vs_SCE", "icorr_uA_cm2", "Icorr_uA_cm2"):
        assert key in cr
    for key in ("DominantScale", "ProtectiveOxide", "kp_g2_cm4_s", "Kp_g2_m4_s"):
        assert key in ox


def test_hea_sfe_trip_twip_csro_and_hcp_upgrades():
    """Verifies Olson-Cohen SFE TRIP/TWIP classification, CSRO, strain rate, HCP, Heusler, and CrTaO4 oxidation."""
    # 1. TRIP Fe50Mn30Co10Cr10 vs CoCrNi MEA vs High-Ni Slip FCC
    trip = HEAEngine("High-Entropy Alloys (HEAs)", {"Fe": 49.55, "Mn": 29.24, "Co": 10.46, "Cr": 9.23})
    cocrni = HEAEngine("High-Entropy Alloys (HEAs)", {"Co": 34.72, "Cr": 30.63, "Ni": 34.65})
    high_ni = HEAEngine("High-Entropy Alloys (HEAs)", {"Ni": 62.0, "Fe": 18.0, "Co": 12.0, "Al": 8.0})

    tr_trip = trip.compute_phase_transformations()
    th_trip = trip.compute_thermodynamics()
    tr_cocrni = cocrni.compute_phase_transformations()
    tr_ni = high_ni.compute_phase_transformations()

    assert tr_trip["StackingFaultEnergy_mJ_m2"] < 18.0
    assert "TRIP" in tr_trip["DeformationMechanism"]
    assert "HCP" in th_trip["Phases"]
    assert tr_trip["StackingFaultEnergy_mJ_m2"] < tr_cocrni["StackingFaultEnergy_mJ_m2"] < tr_ni["StackingFaultEnergy_mJ_m2"]
    assert tr_ni["StackingFaultEnergy_mJ_m2"] > 42.0
    assert "Slip" in tr_ni["DeformationMechanism"]

    # 2. CSRO & Strain-rate sensitivity
    cantor_slow = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53},
        strain_rate_s=1e-4,
    )
    cantor_fast = HEAEngine(
        "High-Entropy Alloys (HEAs)",
        {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53},
        strain_rate_s=1e3,
    )
    mc_slow = cantor_slow.compute_mechanical_properties(cantor_slow.compute_thermodynamics(), cantor_slow.compute_phase_transformations())
    mc_fast = cantor_fast.compute_mechanical_properties(cantor_fast.compute_thermodynamics(), cantor_fast.compute_phase_transformations())
    assert mc_fast["YieldStrength_MPa"] > mc_slow["YieldStrength_MPa"]

    nbmotaw = HEAEngine("High-Entropy Alloys (HEAs)", {"Nb": 17.5, "Mo": 18.1, "Ta": 34.1, "W": 34.7})
    tr_nb = nbmotaw.compute_phase_transformations()
    assert tr_nb["CSRO_WarrenCowley_min"] < -0.02
    assert tr_nb["YeParameter_phi"] > 0.0

    # 3. Rare-earth Single-Phase HCP HEA (HoDyYGdTb)
    hcp_hea = HEAEngine("High-Entropy Alloys (HEAs)", {"Ho": 24.5, "Dy": 24.1, "Y": 13.2, "Gd": 23.3, "Tb": 23.6})
    tr_hcp = hcp_hea.compute_phase_transformations()
    th_hcp = hcp_hea.compute_thermodynamics()
    assert tr_hcp["PhasePrediction_Guo"] == "Single Phase HCP"
    assert "HCP" in th_hcp["Phases"] and th_hcp["Phases"]["HCP"] > 0.9

    # 4. CrTaO4 / CrNbO4 protective refractory scale in Cr-Ta-Nb RHEA
    crnbta = HEAEngine("High-Entropy Alloys (HEAs)", {"Cr": 16.0, "Nb": 28.0, "Ta": 36.0, "Ti": 20.0})
    _, ox_crnbta = crnbta.compute_environmental_properties(crnbta.compute_thermodynamics())
    assert "CrTaO4" in ox_crnbta["DominantScale"]


def test_hea_high_temp_creep_coarsening_sigma_and_turbine_duty():
    """Verifies B2 coarsening, Bird-Mukherjee-Dorn + Coble creep, Sigma 600-900 C, CTE order, and bond-coat role."""
    mw = {"Al": 26.982, "Co": 58.933, "Cr": 51.996, "Fe": 55.845, "Ni": 58.693}
    alcocf_wt = {k: 20.0 * mw[k] for k in mw}
    fine = HEAEngine("High-Entropy Alloys (HEAs)", alcocf_wt, grain_size_um=1.5)
    coarse = HEAEngine("High-Entropy Alloys (HEAs)", alcocf_wt, grain_size_um=25.0)

    tr_f = fine.compute_phase_transformations()
    th_f = fine.compute_thermodynamics()
    mc_f = fine.compute_mechanical_properties(th_f, tr_f)
    tp_f = fine.compute_transport_properties(th_f)
    cr_f, _ = fine.compute_environmental_properties(th_f)

    s800_f = fine.compute_single_temperature_step(1073.15)
    s1000_f = fine.compute_single_temperature_step(1273.15)
    s1000_c = coarse.compute_single_temperature_step(1273.15)

    # Benchmark solidus/liquidus (1631 K / 1663 K), YSZ-matched B2 CTE, Sigma at 800 C, and Bond-Coat duty
    assert 1600.0 <= th_f["Solidus_K"] <= 1660.0
    assert 9.5 <= tp_f["CTE_1e6_K"] <= 12.8
    assert "Sigma" in th_f["Phases"] and "Sigma" in s800_f["Phases"]
    assert mc_f["SigmaEmbrittlementRisk"] is True
    assert "Bond Coat" in mc_f["RecommendedTurbineRole"]

    # High-T softening: sharp drop across 800-1000 C and inverse Hall-Petch Coble crossover at 1000 C
    assert 1150.0 <= mc_f["YieldStrength_MPa"] <= 1600.0
    assert s800_f["YieldStrength_MPa"] < 400.0
    assert s1000_f["YieldStrength_MPa"] < 120.0
    assert s1000_f["YieldStrength_MPa"] < s1000_c["YieldStrength_MPa"]

    # Micro-galvanic B2 dealloying gives higher icorr than single-phase Cantor FCC
    cantor = HEAEngine("High-Entropy Alloys (HEAs)", {"Fe": 19.86, "Co": 20.95, "Ni": 20.87, "Cr": 18.49, "Mn": 19.53})
    cr_c, _ = cantor.compute_environmental_properties(cantor.compute_thermodynamics())
    assert cr_f["icorr_uA_cm2"] > cr_c["icorr_uA_cm2"] * 2.5

    # Eutectic AlCoCrFeNi2.1 maintains FCC/L12 + B2 lamellae and higher creep viability than equiatomic fine powder
    ehea_wt = {"Al": 16.39 * 26.982, "Co": 16.39 * 58.933, "Cr": 16.39 * 51.996, "Fe": 16.39 * 55.845, "Ni": 34.44 * 58.693}
    ehea = HEAEngine("High-Entropy Alloys (HEAs)", ehea_wt, grain_size_um=15.0)
    mc_ehea = ehea.compute_mechanical_properties(ehea.compute_thermodynamics(), ehea.compute_phase_transformations())
    assert mc_ehea["SigmaEmbrittlementRisk"] is False
    assert "Primary Turbine Substrate" in mc_ehea["RecommendedTurbineRole"]
