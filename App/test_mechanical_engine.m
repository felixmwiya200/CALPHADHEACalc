% test_mechanical_engine.m - Comprehensive Validation of HEAMechanicalEngine
% Validates 100% native MATLAB mechanical properties calculations against
% peer-reviewed experimental literature benchmarks (Gludovatz 2014, Otto 2013,
% Varvenne-Curtin 2016, Toda-Caraballo 2015, Senkov 2010/2011).

function test_mechanical_engine()
    fprintf('========================================================================\n');
    fprintf('   HEA MECHANICAL PROPERTIES ENGINE - AUTOMATED TEST SUITE             \n');
    fprintf('========================================================================\n\n');

    passCount = 0;
    failCount = 0;

    function assertCondition(cond, testName, detailStr)
        if cond
            fprintf('  [PASS] %s\n', testName);
            if nargin >= 3 && ~isempty(detailStr)
                fprintf('         -> %s\n', detailStr);
            end
            passCount = passCount + 1;
        else
            fprintf('  [FAIL] %s\n', testName);
            if nargin >= 3 && ~isempty(detailStr)
                fprintf('         -> ERROR: %s\n', detailStr);
            end
            failCount = failCount + 1;
        end
    end

    %% Test 1: Cantor Equiatomic CoCrFeMnNi (FCC Single-Phase Benchmark)
    fprintf('Test 1: Cantor Alloy (CoCrFeMnNi) Room Temperature Benchmark\n');
    elemsCantor = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    xCantor = [0.2, 0.2, 0.2, 0.2, 0.2];
    
    opts = struct('GrainSize_um', 30.0, 'Temperature_K', 293.15);
    resCantor = HEAMechanicalEngine.computeMechanicalProperties(elemsCantor, xCantor, [], opts);

    assertCondition(strcmp(resCantor.DominantStructure, 'FCC'), ...
        'Cantor Dominant Structure is FCC', resCantor.DominantStructure);

    % Literature: Otto et al. (2013) & Gludovatz et al. (2014): sig_y ~ 200 - 240 MPa for d=30um
    assertCondition(resCantor.YieldStrength_RT_MPa >= 190 && resCantor.YieldStrength_RT_MPa <= 260, ...
        'Cantor Yield Strength within literature bounds (190 - 260 MPa)', ...
        sprintf('sig_y = %.1f MPa (Literature: ~210-230 MPa)', resCantor.YieldStrength_RT_MPa));

    % Hall-Petch component for Cantor: Otto 2013 ky = 494 MPa*um^0.5 -> 494/sqrt(30) ~ 90.2 MPa
    assertCondition(resCantor.Breakdown.HallPetch_MPa >= 80 && resCantor.Breakdown.HallPetch_MPa <= 100, ...
        'Cantor Hall-Petch hardening matches Otto (2013) benchmark', ...
        sprintf('sig_HP = %.1f MPa', resCantor.Breakdown.HallPetch_MPa));

    % Ultimate Tensile Strength: Cantor UTS ~ 550 - 650 MPa
    assertCondition(resCantor.UTS_RT_MPa >= 500 && resCantor.UTS_RT_MPa <= 680, ...
        'Cantor UTS within literature range (500 - 680 MPa)', ...
        sprintf('UTS = %.1f MPa', resCantor.UTS_RT_MPa));

    % High Ductility: Cantor uniform elongation > 45%
    assertCondition(resCantor.Elongation_RT_pct >= 45.0, ...
        'Cantor Ductility is high (> 45%)', ...
        sprintf('Elongation = %.1f %%', resCantor.Elongation_RT_pct));

    % Vickers Hardness: Tabor HV ~ 130 - 160 HV
    assertCondition(resCantor.VickersHardness_HV >= 120 && resCantor.VickersHardness_HV <= 170, ...
        'Cantor Vickers Hardness matches literature (120 - 170 HV)', ...
        sprintf('HV = %.0f HV', resCantor.VickersHardness_HV));

    % Gludovatz 2014 Science benchmark: Fracture toughness KJc > 200 MPa*m^0.5
    assertCondition(resCantor.FractureToughness_MPa_m05 >= 180, ...
        'Cantor Fracture Toughness exceeds Gludovatz (2014) benchmark (>180 MPa*m^0.5)', ...
        sprintf('K1c = %.1f MPa*m^0.5, Pugh B/G = %.2f', resCantor.FractureToughness_MPa_m05, resCantor.PughRatio));

    %% Test 2: Hall-Petch Grain Size Sensitivity
    fprintf('\nTest 2: Hall-Petch Real-Time Grain Size Recalculation (1 to 200 um)\n');
    optsFine   = struct('GrainSize_um', 5.0);
    optsCoarse = struct('GrainSize_um', 150.0);
    resFine   = HEAMechanicalEngine.computeMechanicalProperties(elemsCantor, xCantor, [], optsFine);
    resCoarse = HEAMechanicalEngine.computeMechanicalProperties(elemsCantor, xCantor, [], optsCoarse);

    assertCondition(resFine.YieldStrength_RT_MPa > resCoarse.YieldStrength_RT_MPa, ...
        'Hall-Petch: Fine grains (5 um) significantly harder than coarse (150 um)', ...
        sprintf('d=5um: sig_y=%.1f MPa vs d=150um: sig_y=%.1f MPa (Delta = +%.1f MPa)', ...
        resFine.YieldStrength_RT_MPa, resCoarse.YieldStrength_RT_MPa, ...
        resFine.YieldStrength_RT_MPa - resCoarse.YieldStrength_RT_MPa));

    assertCondition(resFine.Breakdown.HallPetch_MPa > 200, ...
        'Hall-Petch grain boundary hardening at 5 um is substantial (>200 MPa)', ...
        sprintf('sig_HP(5um) = %.1f MPa', resFine.Breakdown.HallPetch_MPa));

    %% Test 3: Cryogenic vs High-Temperature Strength Evolution (77 K to 1400 K)
    fprintf('\nTest 3: Temperature-Dependent Softening and Cryogenic Hardening\n');
    tc = resCantor.TempCurve;
    idx77  = find(tc.T_K == 77, 1);
    idx293 = find(tc.T_K > 290 & tc.T_K < 300, 1);
    idx1000 = find(tc.T_K == 1000, 1);

    assertCondition(tc.YieldStrength_MPa(idx77) > tc.YieldStrength_MPa(idx293), ...
        'Cryogenic Strengthening at 77 K (thermal SSS + friction increase)', ...
        sprintf('sig_y(77K)=%.1f MPa > sig_y(293K)=%.1f MPa', ...
        tc.YieldStrength_MPa(idx77), tc.YieldStrength_MPa(idx293)));

    assertCondition(tc.YieldStrength_MPa(idx293) > tc.YieldStrength_MPa(idx1000), ...
        'High-temperature thermally-activated softening at 1000 K', ...
        sprintf('sig_y(293K)=%.1f MPa > sig_y(1000K)=%.1f MPa', ...
        tc.YieldStrength_MPa(idx293), tc.YieldStrength_MPa(idx1000)));

    %% Test 4: AlxCoCrFeNi Series (Al0.3 FCC vs Al1.0 Duplex/BCC+B2)
    fprintf('\nTest 4: AlxCoCrFeNi Phase Transformation & Orowan/B2 Strengthening\n');
    elemsAl = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    xAl03 = [0.0698, 0.2326, 0.2326, 0.2326, 0.2326];
    xAl10 = [0.2000, 0.2000, 0.2000, 0.2000, 0.2000];

    resAl03 = HEAMechanicalEngine.computeMechanicalProperties(elemsAl, xAl03, []);
    resAl10 = HEAMechanicalEngine.computeMechanicalProperties(elemsAl, xAl10, []);

    assertCondition(strcmp(resAl03.DominantStructure, 'FCC'), ...
        'Al0.3CoCrFeNi stabilizes ductile FCC solid solution', resAl03.DominantStructure);

    assertCondition(resAl10.YieldStrength_RT_MPa > resAl03.YieldStrength_RT_MPa * 2.5, ...
        'Al1.0CoCrFeNi displays massive B2 interphase & modulus hardening', ...
        sprintf('Al0.3: sig_y=%.1f MPa vs Al1.0: sig_y=%.1f MPa', ...
        resAl03.YieldStrength_RT_MPa, resAl10.YieldStrength_RT_MPa));

    assertCondition(resAl10.VickersHardness_HV >= 450, ...
        'Al1.0CoCrFeNi Vickers hardness exceeds 450 HV (Literature: 480 - 520 HV)', ...
        sprintf('Al1.0 HV = %.0f HV', resAl10.VickersHardness_HV));

    assertCondition(resAl10.Breakdown.OrowanPrecipitation_MPa > 200, ...
        'Al1.0CoCrFeNi exhibits strong Orowan / interphase barrier', ...
        sprintf('Delta_sig_ppt = %.1f MPa', resAl10.Breakdown.OrowanPrecipitation_MPa));

    %% Test 5: Refractory HEAs (TiZrHfNbTa Ductile vs NbMoTaW High-Strength BCC)
    fprintf('\nTest 5: Refractory HEAs (TiZrHfNbTa vs NbMoTaW)\n');
    elemsTiZr = {'Ti', 'Zr', 'Hf', 'Nb', 'Ta'};
    xTiZr = [0.2, 0.2, 0.2, 0.2, 0.2];
    resTiZr = HEAMechanicalEngine.computeMechanicalProperties(elemsTiZr, xTiZr, []);

    assertCondition(strcmp(resTiZr.DominantStructure, 'BCC'), ...
        'TiZrHfNbTa is BCC solid solution', resTiZr.DominantStructure);

    assertCondition(resTiZr.PughRatio > 2.0 && strcmp(resTiZr.DuctilityClass, 'Ductile'), ...
        'TiZrHfNbTa exhibits intrinsic ductility (Pugh B/G > 2.0)', ...
        sprintf('Pugh B/G = %.2f, Cauchy = %.1f GPa', resTiZr.PughRatio, resTiZr.CauchyPressure_GPa));

    elemsNbMo = {'Nb', 'Mo', 'Ta', 'W'};
    xNbMo = [0.25, 0.25, 0.25, 0.25];
    resNbMo = HEAMechanicalEngine.computeMechanicalProperties(elemsNbMo, xNbMo, []);

    assertCondition(resNbMo.YieldStrength_RT_MPa >= 1000, ...
        'NbMoTaW exhibits ultra-high yield strength (> 1000 MPa, Senkov 2010)', ...
        sprintf('sig_y = %.1f MPa', resNbMo.YieldStrength_RT_MPa));

    %% Test 6: Flow Curve Constitutive Integrity
    fprintf('\nTest 6: Constitutive Flow Curve & Strain Hardening Monotonicity\n');
    flow = resCantor.StressStrainCurve;
    assertCondition(numel(flow.Strain_pct) >= 30, ...
        'Flow curve contains >= 30 discretized plastic strain points', ...
        sprintf('%d points generated', numel(flow.Strain_pct)));

    % Monotonic strain hardening
    isMonotonic = all(diff(flow.Stress_MPa) >= 0);
    assertCondition(isMonotonic, ...
        'Flow curve exhibits continuous positive work hardening (dsigma/deps >= 0)');

    assertCondition(abs(flow.Stress_MPa(1) - resCantor.YieldStrength_RT_MPa) < 1.0, ...
        'Flow curve starts exactly at Yield Strength sigma_y(0.2%)', ...
        sprintf('Start: %.1f MPa vs sig_y: %.1f MPa', flow.Stress_MPa(1), resCantor.YieldStrength_RT_MPa));

    %% Summary
    fprintf('\n========================================================================\n');
    fprintf('   MECHANICAL ENGINE TEST RESULTS: %d PASSED, %d FAILED\n', passCount, failCount);
    fprintf('========================================================================\n');

    if failCount > 0
        error('test_mechanical_engine:FailuresDetected', '%d tests failed.', failCount);
    end
end
