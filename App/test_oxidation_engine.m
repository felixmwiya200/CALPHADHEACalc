% test_oxidation_engine.m - Comprehensive Validation of HEAOxidationEngine
% Validates 100% native MATLAB high-temperature oxidation kinetics calculations against
% peer-reviewed experimental literature benchmarks (Wagner parabolic law,
% Alumina-formers vs Chromia-formers vs Spinel vs Refractory Pesting).

function test_oxidation_engine()
    fprintf('========================================================================\n');
    fprintf('   HEA HIGH-TEMPERATURE OXIDATION ENGINE - AUTOMATED TEST SUITE        \n');
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

    %% Test 1: Al1.0CoCrFeNi Alumina Former (Ultra-Protective alpha-Al2O3)
    fprintf('Test 1: Al1.0CoCrFeNi Alumina Former Benchmark (900 °C, 100 h)\n');
    elemsAl10 = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    xAl10 = [0.20, 0.20, 0.20, 0.20, 0.20];
    
    opts = struct('Temperature_C', 900.0, 'ExposureHours', 100.0);
    resAl10 = HEAOxidationEngine.computeOxidationKinetics(elemsAl10, xAl10, [], opts);

    assertCondition(strcmp(resAl10.Regime, 'Alumina Former'), ...
        'Al1.0CoCrFeNi classified as Alumina Former', resAl10.Regime);

    assertCondition(strcmp(resAl10.DominantOxide, 'alpha-Al2O3'), ...
        'Dominant oxide scale is alpha-Al2O3', resAl10.DominantOxide);

    % Wagner rate constant for Al2O3 at 900 °C: kp ~ 10^-14 to 10^-13 g^2/(cm^4*s)
    assertCondition(resAl10.kp_g2_cm4_s < 1.0e-13, ...
        'Parabolic rate constant kp < 1e-13 g^2/cm^4*s (Ultra-protective)', ...
        sprintf('kp = %.2e g^2/cm^4*s', resAl10.kp_g2_cm4_s));

    assertCondition(resAl10.ActivationEnergy_kJ >= 300, ...
        'Activation energy matches alpha-Al2O3 diffusion barrier (~310 kJ/mol)', ...
        sprintf('Q_ox = %.1f kJ/mol', resAl10.ActivationEnergy_kJ));

    % Wagner critical solute criterion (Al = 20 at% >= 13 at%)
    assertCondition(resAl10.CriticalSoluteMet == true, ...
        'Wagner critical solute criterion met (continuous external scale)', ...
        resAl10.CriticalSoluteStatus);

    % Scale thickness at 100 h: x_ox should be protective and thin (< 3 um)
    assertCondition(resAl10.ScaleThickness_um >= 0.01 && resAl10.ScaleThickness_um <= 3.0, ...
        'Oxide scale thickness at 100 h is protective (< 3 um)', ...
        sprintf('x_ox = %.2f um, mass gain = %.3f mg/cm^2', resAl10.ScaleThickness_um, resAl10.MassGain_mg_cm2));

    %% Test 2: Al0.3CoCrFeNi Chromia Former
    fprintf('\nTest 2: Al0.3CoCrFeNi Chromia Former Benchmark (900 °C, 100 h)\n');
    xAl03 = [0.0698, 0.2326, 0.2326, 0.2326, 0.2326];
    resAl03 = HEAOxidationEngine.computeOxidationKinetics(elemsAl10, xAl03, [], opts);

    assertCondition(strcmp(resAl03.Regime, 'Chromia Former'), ...
        'Al0.3CoCrFeNi classified as Chromia Former (low Al, high Cr)', resAl03.Regime);

    assertCondition(strcmp(resAl03.DominantOxide, 'Cr2O3'), ...
        'Dominant oxide scale is Cr2O3', resAl03.DominantOxide);

    % Chromia oxidizes faster than alumina at 900 °C
    assertCondition(resAl03.kp_g2_cm4_s > resAl10.kp_g2_cm4_s, ...
        'Chromia oxidation rate is higher than alumina oxidation rate', ...
        sprintf('kp(Cr2O3) = %.2e > kp(Al2O3) = %.2e', resAl03.kp_g2_cm4_s, resAl10.kp_g2_cm4_s));

    assertCondition(resAl03.ActivationEnergy_kJ >= 240 && resAl03.ActivationEnergy_kJ <= 270, ...
        'Activation energy matches Cr2O3 growth (~255 kJ/mol)', ...
        sprintf('Q_ox = %.1f kJ/mol', resAl03.ActivationEnergy_kJ));

    %% Test 3: Cantor CoCrFeMnNi Spinel Regime (Rapid Oxidation)
    fprintf('\nTest 3: Cantor CoCrFeMnNi Spinel Regime (Mn-Cr Interdiffusion)\n');
    elemsCantor = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    xCantor = [0.2, 0.2, 0.2, 0.2, 0.2];
    resCantor = HEAOxidationEngine.computeOxidationKinetics(elemsCantor, xCantor, [], opts);

    assertCondition(contains(resCantor.Regime, 'Spinel') || contains(resCantor.DominantOxide, 'Spinel'), ...
        'Cantor alloy identified in Spinel formation regime', ...
        sprintf('Regime: %s, Oxide: %s', resCantor.Regime, resCantor.DominantOxide));

    % Spinel oxidizes significantly faster than alumina (> 100x)
    assertCondition(resCantor.kp_g2_cm4_s > resAl10.kp_g2_cm4_s * 50, ...
        'Cantor spinel oxidizes much faster than alumina (>50x faster)', ...
        sprintf('kp(Cantor) = %.2e vs kp(Al1.0) = %.2e', resCantor.kp_g2_cm4_s, resAl10.kp_g2_cm4_s));

    %% Test 4: Refractory HEA Pesting & Volatilization Alerts (NbMoTaW)
    fprintf('\nTest 4: Refractory NbMoTaW Pesting & Volatilization Alerts\n');
    elemsNbMo = {'Nb', 'Mo', 'Ta', 'W'};
    xNbMo = [0.25, 0.25, 0.25, 0.25];
    optsHighT = struct('Temperature_C', 950.0, 'ExposureHours', 50.0);
    resNbMo = HEAOxidationEngine.computeOxidationKinetics(elemsNbMo, xNbMo, [], optsHighT);

    assertCondition(resNbMo.PestingAlert == true, ...
        'Refractory pest oxidation alert triggered for NbMoTaW', ...
        resNbMo.PestingMessage);

    assertCondition(resNbMo.VolatilizationAlert == true, ...
        'Volatile sublimation alert triggered (MoO3 & WO3 sublimation)', ...
        resNbMo.VolatilizationMessage);

    %% Test 5: Mathematical Scaling of Wagner Parabolic Law
    fprintf('\nTest 5: Wagner Parabolic Kinetic Law Scaling (DeltaW/A proportional to sqrt(t))\n');
    opts1h   = struct('Temperature_C', 900.0, 'ExposureHours', 1.0);
    opts100h = struct('Temperature_C', 900.0, 'ExposureHours', 100.0);
    res1h   = HEAOxidationEngine.computeOxidationKinetics(elemsAl10, xAl10, [], opts1h);
    res100h = HEAOxidationEngine.computeOxidationKinetics(elemsAl10, xAl10, [], opts100h);

    ratio = res100h.MassGain_mg_cm2 / res1h.MassGain_mg_cm2;
    assertCondition(abs(ratio - 10.0) < 0.25, ...
        'Mass gain scales exactly with sqrt(t) (sqrt(100/1) = 10.0)', ...
        sprintf('Gain(100h)/Gain(1h) = %.2f (Theoretical: 10.00)', ratio));

    %% Test 6: Thermal Spallation Compressive Stress
    fprintf('\nTest 6: Thermal Spallation Compressive Stress Upon Cooling\n');
    assertCondition(resAl10.SpallationStress_MPa < 0, ...
        'Thermal residual stress upon cooling is compressive (negative)', ...
        sprintf('sigma_th = %.1f MPa', resAl10.SpallationStress_MPa));

    %% Test 7: Full HEAThermoEngine Integration
    fprintf('\nTest 7: HEAThermoEngine Integration with Mechanical & Oxidation Engines\n');
    thermoRes = HEAThermoEngine.computeThermodynamics(elemsAl10, xAl10);

    assertCondition(isfield(thermoRes, 'Mechanical') && isstruct(thermoRes.Mechanical), ...
        'thermoRes contains Mechanical struct', ...
        sprintf('sig_y = %.1f MPa, HV = %.0f', thermoRes.Mechanical.YieldStrength_RT_MPa, thermoRes.Mechanical.VickersHardness_HV));

    assertCondition(isfield(thermoRes, 'Oxidation') && isstruct(thermoRes.Oxidation), ...
        'thermoRes contains Oxidation struct', ...
        sprintf('Regime = %s, kp = %.2e', thermoRes.Oxidation.Regime, thermoRes.Oxidation.kp_g2_cm4_s));

    %% Summary
    fprintf('\n========================================================================\n');
    fprintf('   OXIDATION ENGINE TEST RESULTS: %d PASSED, %d FAILED\n', passCount, failCount);
    fprintf('========================================================================\n');

    if failCount > 0
        error('test_oxidation_engine:FailuresDetected', '%d tests failed.', failCount);
    end
end
