% run_candidate_calculations.m
% Executes CALPHADHEACalc thermodynamic, mechanical, oxidation, and application
% scoring engines for 10 candidate high entropy alloys designed for mechanical
% alloying and film-cooled turbine blade service.

addpath('App');

fprintf('========================================================================\n');
fprintf('CALPHADHEACalc 2026: Multi-Physics Candidate Alloy Evaluation Pipeline\n');
fprintf('Target Application: Film-Cooled Gas Turbine Blades via Mechanical Alloying\n');
fprintf('========================================================================\n\n');

% Define 10 candidate alloys
candidates = {
    % 1. ODS-Al0.5CoCrFeNi (FCC + B2 + Y2O3 ODS)
    struct('Name', 'ODS-Al0.5CoCrFeNi (0.5wt% Y2O3)', ...
           'Formula', 'Al11.1Co22.2Cr22.2Fe22.2Ni22.2+ODS', ...
           'Category', 'Oxide-Dispersion-Strengthened HEA', ...
           'Elements', {{'Al', 'Co', 'Cr', 'Fe', 'Ni'}}, ...
           'Fractions', [11.11, 22.22, 22.22, 22.22, 22.23], ...
           'ODS_wt_pct', 0.5, ...
           'MillingTime_h', 30, 'MillingRPM', 350, 'BPR', 10, ...
           'Consolidation', 'SPS (1100 °C, 50 MPa, 10 min)', ...
           'DesignRationale', 'Mechanical alloying homogenously disperses 10-20 nm Y2O3 nanoparticles; FCC matrix gives excellent ductility (>18%) for micro-EDM/laser hole drilling without recast cracking; coherent B2 and ODS yield exceptional creep resistance at 900-1100 °C; forms hermetic alpha-Al2O3 scale.'), ...
           
    % 2. High-Entropy Superalloy Co1.5CrFeNi1.5Al0.2Ti0.2 (HESA)
    struct('Name', 'Co1.5CrFeNi1.5Al0.2Ti0.2 (HESA-gamma/gamma_prime)', ...
           'Formula', 'Co27.8Cr18.5Fe18.5Ni27.8Al3.7Ti3.7', ...
           'Category', 'High-Entropy Superalloy (HESA)', ...
           'Elements', {{'Co', 'Cr', 'Fe', 'Ni', 'Al', 'Ti'}}, ...
           'Fractions', [27.78, 18.52, 18.52, 27.78, 3.70, 3.70], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 25, 'MillingRPM', 300, 'BPR', 10, ...
           'Consolidation', 'HIP (1200 °C, 150 MPa, 4 h) + Age (850 °C)', ...
           'DesignRationale', 'Designed with 45-55 vol% coherent cuboidal L12 gamma-prime precipitates in FCC matrix; MA creates segregation-free pre-alloyed powder; high solidus (1645 K); exceptional thermal fatigue resistance and CTE match with YSZ TBC.'), ...
           
    % 3. Eutectic HEA AlCoCrFeNi2.1 (EHEA)
    struct('Name', 'AlCoCrFeNi2.1 (Eutectic HEA)', ...
           'Formula', 'Al16.4Co16.4Cr16.4Fe16.4Ni34.4', ...
           'Category', 'Eutectic High-Entropy Alloy (EHEA)', ...
           'Elements', {{'Al', 'Co', 'Cr', 'Fe', 'Ni'}}, ...
           'Fractions', [16.39, 16.39, 16.39, 16.39, 34.44], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 28, 'MillingRPM', 320, 'BPR', 12, ...
           'Consolidation', 'SPS (1050 °C, 45 MPa, 8 min)', ...
           'DesignRationale', 'Dual-phase fine lamellar L12 (FCC) + B2 (ordered BCC) eutectic; MA+SPS refines lamellar spacing down to 200-400 nm; gives high yield strength at 800 °C (580 MPa) and high tensile ductility (15%) preventing hole edge cracking.'), ...
           
    % 4. CoNiAlTiCrTa (Refractory-Reinforced HESA)
    struct('Name', 'CoNiAlTiCrTa (Ta-Strengthened HESA)', ...
           'Formula', 'Co20Ni20Al20Ti20Cr10Ta10', ...
           'Category', 'Refractory-Reinforced Superalloy', ...
           'Elements', {{'Co', 'Ni', 'Al', 'Ti', 'Cr', 'Ta'}}, ...
           'Fractions', [20.0, 20.0, 20.0, 20.0, 10.0, 10.0], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 35, 'MillingRPM', 350, 'BPR', 15, ...
           'Consolidation', 'SPS (1250 °C, 50 MPa, 12 min)', ...
           'DesignRationale', 'Tantalum and Titanium strongly partition to ordered intermetallic phases, providing high-T strength; high Al guarantees rapid alpha-Al2O3 scale formation; MA is critical to bypass massive Ta melting point disparity (3290 K).'), ...
           
    % 5. Al0.7CoCrFeNi (Duplex FCC+B2)
    struct('Name', 'Al0.7CoCrFeNi (Duplex FCC+B2)', ...
           'Formula', 'Al14.9Co21.3Cr21.3Fe21.3Ni21.3', ...
           'Category', 'Transition Metal Duplex HEA', ...
           'Elements', {{'Al', 'Co', 'Cr', 'Fe', 'Ni'}}, ...
           'Fractions', [14.89, 21.28, 21.28, 21.28, 21.27], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 24, 'MillingRPM', 300, 'BPR', 10, ...
           'Consolidation', 'SPS (1100 °C, 50 MPa, 10 min)', ...
           'DesignRationale', 'Balanced ~45% FCC and ~55% B2 duplex structure; FCC imparts sufficient ductility for laser hole cutting without cracking; high Al content enables continuous alumina scale formation.'), ...
           
    % 6. MoNbTaTiV (Low-Density Refractory HEA)
    struct('Name', 'MoNbTaTiV (Low-Density RHEA)', ...
           'Formula', 'Mo20Nb20Ta20Ti20V20', ...
           'Category', 'Refractory High-Entropy Alloy (RHEA)', ...
           'Elements', {{'Mo', 'Nb', 'Ta', 'Ti', 'V'}}, ...
           'Fractions', [20.0, 20.0, 20.0, 20.0, 20.0], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 40, 'MillingRPM', 380, 'BPR', 15, ...
           'Consolidation', 'SPS (1450 °C, 60 MPa, 15 min)', ...
           'DesignRationale', 'Refractory HEA tailored for ultra-high temperature structural service; density is 8.4 g/cm3 (much lighter than W-RHEAs >12 g/cm3); solidus >2180 K; yield strength >650 MPa at 1000 °C; requires environmental barrier coating (EBC) against pest oxidation.'), ...
           
    % 7. Al0.5CoCrFeNi (High-Ductility FCC Matrix)
    struct('Name', 'Al0.5CoCrFeNi (High-Ductility FCC/B2)', ...
           'Formula', 'Al11.1Co22.2Cr22.2Fe22.2Ni22.2', ...
           'Category', 'Transition Metal Duplex HEA', ...
           'Elements', {{'Al', 'Co', 'Cr', 'Fe', 'Ni'}}, ...
           'Fractions', [11.11, 22.22, 22.22, 22.22, 22.23], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 24, 'MillingRPM', 300, 'BPR', 10, ...
           'Consolidation', 'SPS (1080 °C, 45 MPa, 10 min)', ...
           'DesignRationale', 'Predominantly FCC matrix with nano-B2 precipitates; high tensile ductility (21%) and high fracture toughness (>85 MPa*m0.5); minimizes thermal fatigue cracking around film-cooling holes during cycling.'), ...
           
    % 8. Ni2CoCrFeNb0.45 (Eutectic Laves EHEA)
    struct('Name', 'Ni2CoCrFeNb0.45 (Eutectic Laves HEA)', ...
           'Formula', 'Ni36.7Co18.3Cr18.3Fe18.3Nb8.4', ...
           'Category', 'Eutectic Laves-Strengthened HEA', ...
           'Elements', {{'Ni', 'Co', 'Cr', 'Fe', 'Nb'}}, ...
           'Fractions', [36.7, 18.3, 18.3, 18.3, 8.4], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 30, 'MillingRPM', 320, 'BPR', 10, ...
           'Consolidation', 'SPS (1120 °C, 50 MPa, 10 min)', ...
           'DesignRationale', 'C14 Laves phase network at interlamellar boundaries suppresses grain boundary sliding and creep at 850-950 °C; MA+SPS suppresses macro-segregation of Nb.'), ...
           
    % 9. Ti20Zr20Hf20Nb20Ta20 (Ductile RHEA)
    struct('Name', 'TiZrHfNbTa (Ductile Refractory BCC)', ...
           'Formula', 'Ti20Zr20Hf20Nb20Ta20', ...
           'Category', 'Refractory High-Entropy Alloy (RHEA)', ...
           'Elements', {{'Ti', 'Zr', 'Hf', 'Nb', 'Ta'}}, ...
           'Fractions', [20.0, 20.0, 20.0, 20.0, 20.0], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 36, 'MillingRPM', 350, 'BPR', 12, ...
           'Consolidation', 'SPS (1380 °C, 55 MPa, 12 min)', ...
           'DesignRationale', 'Ductile single-phase BCC refractory alloy with melting point >2150 K and compressive ductility >15%; excellent fracture toughness; requires pack cementation or HEA bond coat for oxidation resistance.'), ...
           
    % 10. Al1.0CoCrFeNi (High-Strength B2/BCC HEA)
    struct('Name', 'Al1.0CoCrFeNi (Nanostructured B2/BCC)', ...
           'Formula', 'Al20Co20Cr20Fe20Ni20', ...
           'Category', 'Transition Metal High-Strength HEA', ...
           'Elements', {{'Al', 'Co', 'Cr', 'Fe', 'Ni'}}, ...
           'Fractions', [20.0, 20.0, 20.0, 20.0, 20.0], ...
           'ODS_wt_pct', 0.0, ...
           'MillingTime_h', 30, 'MillingRPM', 350, 'BPR', 10, ...
           'Consolidation', 'SPS (1120 °C, 50 MPa, 10 min)', ...
           'DesignRationale', 'Spinodal decomposed B2 + BCC nanostructure; very high yield strength (>1200 MPa at RT, 480 MPa at 800 °C); rapid continuous alpha-Al2O3 scale formation; lower ductility (~6%) requires non-thermal laser drilling to prevent hole cracking.')
};

results = [];

for idx = 1:numel(candidates)
    c = candidates{idx};
    fprintf('[%2d/10] Computing multi-physics for: %s...\n', idx, c.Name);
    
    elems = c.Elements;
    fracs = c.Fractions / sum(c.Fractions);
    
    % 1. Thermodynamic Core
    th = HEAThermoEngine.computeThermodynamics(elems, fracs);
    
    % 2. Mechanical Engine (grain size: 1.5 um for MA+SPS consolidated powder)
    mOpts = struct('GrainSize_um', 1.5);
    mech = HEAMechanicalEngine.computeMechanicalProperties(elems, fracs, th, mOpts);
    
    % 3. Oxidation Engine (tested at 950 °C for 100 hours)
    oxOpts = struct('Temperature_C', 950, 'ExposureHours', 100);
    ox = HEAOxidationEngine.computeOxidationKinetics(elems, fracs, th, oxOpts);
    
    % 4. Application Suitability Scorer for Aerospace Turbine Blades
    app = HEAApplicationDatabase.getAeroTurbineBlade();
    appScore = HEAApplicationScorer.evaluateSingleApplication(app, elems, fracs, th, mech, ox);
    
    % Extract high-temperature yield strength at 800 °C and 1000 °C from TempCurve
    ys_800 = mech.YieldStrength_RT_MPa * 0.55; % baseline
    ys_1000 = mech.YieldStrength_RT_MPa * 0.32;
    if isfield(mech, 'TempCurve') && isfield(mech.TempCurve, 'T_C') && isfield(mech.TempCurve, 'YieldStrength_MPa')
        tArr = mech.TempCurve.T_C;
        yArr = mech.TempCurve.YieldStrength_MPa;
        [~, i800] = min(abs(tArr - 800));
        [~, i1000] = min(abs(tArr - 1000));
        ys_800 = yArr(i800);
        ys_1000 = yArr(i1000);
    end
    
    % If ODS alloy, credit nano-oxide grain boundary pinning: +180 MPa at 800°C, +140 MPa at 1000°C
    if c.ODS_wt_pct > 0
        ys_800 = ys_800 + 180.0;
        ys_1000 = ys_1000 + 140.0;
    end
    
    % High Temperature Creep Limit (estimated as 0.70 of 800°C yield strength)
    creep_limit = ys_800 * 0.70;
    
    % Thermal conductivity, density, CTE
    k_th = th.ThermalConductivity_W_mK;
    rho = th.Density_g_cm3;
    E_gpa = mech.YoungsModulus_GPa;
    alpha_cte = 12.5; % average 1e-6 / K
    if isfield(th, 'alpha') && th.alpha > 0
        % if alpha is thermal diffusivity or CTE
        if th.alpha < 1e-4
            alpha_cte = 12.0;
        else
            alpha_cte = th.alpha;
        end
    end
    
    % Film Cooling Thermophysical Figures of Merit:
    % 1. Thermal Fatigue Resistance Index R' = (k * sig_y) / (E * alpha)
    % Higher R' prevents thermal gradient cracking around film cooling holes
    R_prime = (k_th * (ys_800 * 1e6)) / ((E_gpa * 1e9) * (alpha_cte * 1e-6));
    
    % 2. Centrifugal Stress Reduction vs CMSX-4 (rho_ref = 8.70 g/cm3)
    % sigma_centrifugal is proportional to density
    centrifugal_rel = (rho / 8.70);
    
    % 3. Solidus Temperature Safety Margin over 1100 °C (1373 K) metal temperature
    solidus_margin_K = th.T_Solidus - 1373.15;
    
    % 4. Drillability & Micro-Crack Resistance Index (product of ductility and toughness)
    drillability_index = (mech.Elongation_RT_pct / 10.0) * (mech.FractureToughness_K1c / 50.0);
    
    % Package result struct
    res = struct();
    res.Rank = idx;
    res.Name = c.Name;
    res.Formula = c.Formula;
    res.Category = c.Category;
    res.DesignRationale = c.DesignRationale;
    res.ODS_wt_pct = c.ODS_wt_pct;
    res.MillingTime_h = c.MillingTime_h;
    res.MillingRPM = c.MillingRPM;
    res.BPR = c.BPR;
    res.Consolidation = c.Consolidation;
    
    % CALPHAD Thermodynamic Parameters
    res.VEC = round(th.VEC, 2);
    res.Phase = th.Phase;
    res.DeltaH_mix_kJ_mol = round(th.DeltaH_mix, 2);
    res.DeltaS_mix_J_molK = round(th.DeltaS_mix, 2);
    res.Omega = round(th.Omega, 2);
    res.Delta_size_pct = round(th.Delta_size, 2);
    res.Delta_chi = round(th.Delta_chi, 3);
    res.T_Solidus_K = round(th.T_Solidus, 1);
    res.T_Liquidus_K = round(th.T_Liquidus, 1);
    res.MeltingRange_K = round(th.T_Liquidus - th.T_Solidus, 1);
    res.SolidusMargin_over_1100C_K = round(solidus_margin_K, 1);
    
    % Physical & Thermophysical Parameters
    res.Density_g_cm3 = round(rho, 2);
    res.CentrifugalLoadRatio_vs_CMSX4 = round(centrifugal_rel, 2);
    res.ThermalConductivity_W_mK = round(k_th, 1);
    res.EstimatedCTE_ppm_K = round(alpha_cte, 1);
    res.ThermalFatigue_R_prime = round(R_prime, 1);
    
    % Mechanical Parameters
    res.YieldStrength_RT_MPa = round(mech.YieldStrength_RT_MPa, 1);
    res.UTS_RT_MPa = round(mech.UTS_RT_MPa, 1);
    res.Elongation_RT_pct = round(mech.Elongation_RT_pct, 1);
    res.YoungsModulus_GPa = round(E_gpa, 1);
    res.VickersHardness_HV = round(mech.VickersHardness_HV, 0);
    res.FractureToughness_K1c = round(mech.FractureToughness_K1c, 1);
    res.PughRatio_B_over_G = round(mech.PughRatio_B_over_G, 2);
    res.YieldStrength_800C_MPa = round(ys_800, 1);
    res.YieldStrength_1000C_MPa = round(ys_1000, 1);
    res.HighTempCreepLimit_MPa = round(creep_limit, 1);
    res.DrillabilityIndex = round(drillability_index, 2);
    
    % Oxidation Kinetics (950 °C, 100 h)
    res.OxidationRegime = ox.Regime;
    res.DominantOxide = ox.DominantOxide;
    res.ProtectiveRating = ox.ProtectiveRating;
    res.kp_g2_cm4_s = ox.kp_g2_cm4_s;
    res.kp_scientific = sprintf('%.2e', ox.kp_g2_cm4_s);
    res.MassGain_mg_cm2 = round(ox.MassGain_mg_cm2, 3);
    res.ScaleThickness_um = round(ox.ScaleThickness_um, 2);
    res.PBR = round(ox.PBR, 2);
    res.SpallationStress_MPa = round(ox.SpallationStress_MPa, 0);
    
    % Turbine Blade Application Match Score
    res.AeroTurbineScore_pct = round(appScore.Score_pct, 1);
    res.SuitabilityTier = appScore.Tier;
    
    results = [results; res];
end

% Compute Comprehensive Multi-Criteria Ranking for Film-Cooled Turbine Blades:
% Combines AeroTurbineScore (40%), Solidus Safety Margin (15%), High-T Strength/Creep (20%),
% Thermal Fatigue R' for Film Cooling (15%), and Drillability/Crack-Resistance (10%).
composite_scores = zeros(numel(results), 1);
for i = 1:numel(results)
    r = results(i);
    % Normalize components:
    % Solidus margin (0 at 0 margin, 1.0 at 800 K margin)
    s_margin_norm = min(1.0, max(0.0, r.SolidusMargin_over_1100C_K / 800.0));
    % 800C Strength (0 at 250 MPa, 1.0 at 750 MPa)
    s_strength_norm = min(1.0, max(0.0, (r.YieldStrength_800C_MPa - 250) / 500.0));
    % Thermal Fatigue R' (0 at 100, 1.0 at 600)
    s_rfatigue_norm = min(1.0, max(0.0, (r.ThermalFatigue_R_prime - 100) / 500.0));
    % Drillability (0 at 0.5, 1.0 at 3.0)
    s_drill_norm = min(1.0, max(0.0, (r.DrillabilityIndex - 0.5) / 2.5));
    % Base Aero Score
    s_aero_norm = r.AeroTurbineScore_pct / 100.0;
    % Penalty if non-protective oxide or extreme spallation
    ox_multiplier = 1.0;
    if contains(r.OxidationRegime, 'Non-Protective') || contains(r.ProtectiveRating, 'Catastrophic')
        ox_multiplier = 0.70;
    end
    
    final_score = (0.35 * s_aero_norm + 0.20 * s_strength_norm + 0.15 * s_margin_norm + ...
                   0.15 * s_rfatigue_norm + 0.15 * s_drill_norm) * 100.0 * ox_multiplier;
    composite_scores(i) = final_score;
end

% Sort descending by composite score
[sorted_scores, sort_order] = sort(composite_scores, 'descend');
sorted_results = results(sort_order);

for rk = 1:numel(sorted_results)
    sorted_results(rk).Rank = rk;
    sorted_results(rk).TurbineBladeCompositeScore_pct = round(sorted_scores(rk), 1);
end

fprintf('\nFinal Ranking Results:\n');
fprintf('------------------------------------------------------------------------------------------------------------------------\n');
fprintf('%-4s %-36s %-12s %-10s %-10s %-10s %-12s %-14s\n', ...
        'Rank', 'Alloy Name', 'Phase', 'Ts (K)', 'YS_800(MPa)', 'Elong(%)', 'Density(g/cm3)', 'Overall Score');
fprintf('------------------------------------------------------------------------------------------------------------------------\n');
for i = 1:numel(sorted_results)
    r = sorted_results(i);
    fprintf('%-4d %-36s %-12s %-10.1f %-10.1f %-10.1f %-12.2f %-6.1f%% (%s)\n', ...
            r.Rank, r.Name, r.Phase(1:min(12,end)), r.T_Solidus_K, r.YieldStrength_800C_MPa, ...
            r.Elongation_RT_pct, r.Density_g_cm3, r.TurbineBladeCompositeScore_pct, r.SuitabilityTier);
end
fprintf('------------------------------------------------------------------------------------------------------------------------\n\n');

% Write structured JSON
jsonStr = jsonencode(sorted_results, 'PrettyPrint', true);
fid = fopen('candidate_materials_results.json', 'w');
fwrite(fid, jsonStr, 'char');
fclose(fid);
fprintf('Successfully generated candidate_materials_results.json\n');
exit;
