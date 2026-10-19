% test_new_compositions.m
% Verification script for arbitrary and new HEA compositions

addpath(fullfile(pwd, 'App'));

testAlloys = {
    'NbMoTaW', {'Nb', 'Mo', 'Ta', 'W'}, [0.25, 0.25, 0.25, 0.25];
    'TiZrHfNbTa', {'Ti', 'Zr', 'Hf', 'Nb', 'Ta'}, [0.2, 0.2, 0.2, 0.2, 0.2];
    'Al0.5CoCrFeNi', {'Al', 'Co', 'Cr', 'Fe', 'Ni'}, [0.5/4.5, 1/4.5, 1/4.5, 1/4.5, 1/4.5];
    'AlCoCrFeNi2.1', {'Al', 'Co', 'Cr', 'Fe', 'Ni'}, [1/6.1, 1/6.1, 1/6.1, 1/6.1, 2.1/6.1];
    'CoCrNi', {'Co', 'Cr', 'Ni'}, [1/3, 1/3, 1/3];
    'TiNbTaZr', {'Ti', 'Nb', 'Ta', 'Zr'}, [0.25, 0.25, 0.25, 0.25];
    'Al20Li20Mg20Sc20Ti20', {'Al', 'Li', 'Mg', 'Sc', 'Ti'}, [0.2, 0.2, 0.2, 0.2, 0.2];
    'RuRhPdOsIrPt', {'Ru', 'Rh', 'Pd', 'Os', 'Ir', 'Pt'}, ones(1,6)/6;
    'Fe40Mn20Cr20Ni20', {'Fe', 'Mn', 'Cr', 'Ni'}, [0.4, 0.2, 0.2, 0.2];
    'AlMgTiZn', {'Al', 'Mg', 'Ti', 'Zn'}, [0.25, 0.25, 0.25, 0.25];
    'CrMoNbV', {'Cr', 'Mo', 'Nb', 'V'}, [0.25, 0.25, 0.25, 0.25];
    'Ti60Al20V20', {'Ti', 'Al', 'V'}, [0.6, 0.2, 0.2]
};

fprintf('========================================================================\n');
fprintf('RUNNING MULTI-PHYSICS PREDICTION TEST FOR NEW HEA COMPOSITIONS\n');
fprintf('========================================================================\n');

numPassed = 0;
totalAlloys = size(testAlloys, 1);

for i = 1:totalAlloys
    name = testAlloys{i, 1};
    elems = testAlloys{i, 2};
    at_frac = testAlloys{i, 3};
    
    fprintf('Alloy [%d/%d]: %s\n', i, totalAlloys, name);
    try
        % 1. Thermo
        tM = HEAThermoEngine.computeThermodynamics(elems, at_frac);
        if any(isnan([tM.DeltaHmix, tM.DeltaSmix, tM.Omega, tM.DeltaSize, tM.VEC, tM.T_Solidus, tM.T_Liquidus]))
            error('NaN detected in thermodynamics metrics');
        end
        
        % 2. Mechanical
        mM = HEAMechanicalEngine.computeMechanicalProperties(elems, at_frac, tM);
        if isfield(mM, 'Error')
            error('Mechanical error: %s', mM.Error);
        end
        if any(isnan([mM.YieldStrength_MPa, mM.UTS_MPa, mM.Elongation_pct, mM.VickersHardness_HV, mM.FractureToughness_MPa_m05]))
            error('NaN detected in mechanical metrics');
        end
        
        % 3. Oxidation
        oxM = HEAOxidationEngine.computeOxidationKinetics(elems, at_frac, tM);
        if isfield(oxM, 'Error')
            error('Oxidation error: %s', oxM.Error);
        end
        if any(isnan([oxM.kp_g2_cm4_s, oxM.ActivationEnergy_kJ, oxM.PBR]))
            error('NaN detected in oxidation metrics');
        end
        
        % 4. Coating & Tribology Engine (Li et al. Adv. Eng. Mater. 2019)
        coatM = tM.Coating;
        if isfield(coatM, 'Error')
            error('Coating error: %s', coatM.Error);
        end
        if any(isnan([coatM.DilutionRatio_D, coatM.CoatingHardness_HV, coatM.SpecificWearRate_1e6_mm3_Nm, coatM.FrictionCoefficient_COF, coatM.ScratchCriticalLoad_Lc_N]))
            error('NaN detected in coating metrics');
        end

        % 5. Advanced PDM Corrosion Checks (Li et al. JMRT 2025)
        corrM = tM.Corrosion;
        if isempty(corrM.SemiconductorType) || isnan(corrM.DefectDensity_cm3)
            error('Missing PDM semiconductor metrics in Corrosion');
        end
        
        % 6. Benchmark & Validation
        bench = HEABenchmarkDatabase.getBenchmark(elems, at_frac, tM, mM, oxM, tM.Corrosion);
        
        % 7. Application Scorer
        appScores = HEAApplicationScorer.scoreAlloy(elems, at_frac, tM, mM, oxM);
        
        fprintf('   Phase: %s | VEC: %.2f | sig_y: %.1f MPa | UTS: %.1f MPa | Elong: %.1f%% | Wear: %.2e | Semi: %s\n', ...
            tM.Phase, tM.VEC, mM.YieldStrength_MPa, mM.UTS_MPa, mM.Elongation_pct, coatM.SpecificWearRate_1e6_mm3_Nm, corrM.SemiconductorType(1:18));
        
        % Physical reasonableness checks
        if strcmp(name, 'NbMoTaW')
            if mM.Elongation_pct > 10.0
                fprintf('   [WARNING] NbMoTaW physical error: Elongation should be brittle (<5%%), got %.1f%%\n', mM.Elongation_pct);
            end
            if mM.FractureToughness_MPa_m05 > 25.0
                fprintf('   [WARNING] NbMoTaW physical error: K1c should be ~10-15 MPa*m^0.5, got %.1f\n', mM.FractureToughness_MPa_m05);
            end
        end
        
        numPassed = numPassed + 1;
    catch ME
        fprintf('   FAILED: %s (in %s at line %d)\n', ME.message, ME.stack(1).file, ME.stack(1).line);
    end
end

fprintf('------------------------------------------------------------------------\n');
fprintf('Summary: %d / %d alloys evaluated successfully.\n', numPassed, totalAlloys);
fprintf('========================================================================\n');
exit;
