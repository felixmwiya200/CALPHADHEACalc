% Test script for native MATLAB HEAThermoEngine
function test_thermo_engine()
    fprintf('=== Testing HEAThermoEngine Native Database & Calculator ===\n');
    
    % Test 1: Composition Conversions
    cantorComp = {'Co', 20; 'Cr', 20; 'Fe', 20; 'Mn', 20; 'Ni', 20};
    [wtComp, summaryAtToWt] = HEAThermoEngine.convertComposition(cantorComp, 'at', 'wt');
    assert(abs(sum(cell2mat(wtComp(:,2))) - 100) < 1e-4, 'Sum of wt% must be 100');
    fprintf('✓ Cantor at%% -> wt%% conversion verified (Sum = %.2f%%)\n', sum(cell2mat(wtComp(:,2))));
    
    % Convert back wt% to at%
    [atCompBack, summaryWtToAt] = HEAThermoEngine.convertComposition(wtComp, 'wt', 'at');
    for i = 1:size(atCompBack, 1)
        assert(abs(atCompBack{i,2} - 20.0) < 0.1, sprintf('Recovered at%% for %s should be ~20%%', atCompBack{i,1}));
    end
    fprintf('✓ Round-trip wt%% -> at%% matches original stoichiometry\n');
    
    % Test 2: Molar conversions
    molarComp = {'Fe', 1.0; 'Ni', 2.0};
    [atFromMol, summaryMol] = HEAThermoEngine.convertComposition(molarComp, 'mol', 'at');
    assert(abs(atFromMol{1,2} - 33.333) < 0.01, '1 mol Fe in 3 mol total should be 33.33%');
    assert(abs(atFromMol{2,2} - 66.667) < 0.01, '2 mol Ni in 3 mol total should be 66.67%');
    fprintf('✓ Molar to atomic conversion verified (Fe: %.2f%%, Ni: %.2f%%)\n', atFromMol{1,2}, atFromMol{2,2});
    
    % Test 3: Thermodynamic & Phase Stability Predictor
    % Cantor alloy
    cantorElems = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    cantorFractions = [0.2, 0.2, 0.2, 0.2, 0.2];
    thermoCantor = HEAThermoEngine.computeThermodynamics(cantorElems, cantorFractions);
    assert(abs(thermoCantor.VEC - 8.0) < 1e-4, 'Cantor VEC must be 8.0');
    assert(contains(thermoCantor.Phase, 'FCC'), 'Cantor phase must be predicted as FCC');
    assert(abs(thermoCantor.DeltaSmix - 8.314 * log(5)) < 0.1, 'Delta Smix must match R*ln(5)');
    assert(thermoCantor.T_Solidus < thermoCantor.T_Liquidus, 'Ts must be lower than Tl');
    fprintf('✓ Cantor thermodynamics verified: Phase = %s, VEC = %.2f, Delta Smix = %.2f J/mol*K, Ts = %.1f K, Tl = %.1f K\n', ...
        thermoCantor.Phase, thermoCantor.VEC, thermoCantor.DeltaSmix, thermoCantor.T_Solidus, thermoCantor.T_Liquidus);
    
    % Refractory HEA TiZrHfNbTa
    rheoElems = {'Ti', 'Zr', 'Hf', 'Nb', 'Ta'};
    rheoFractions = [0.2, 0.2, 0.2, 0.2, 0.2];
    thermoRhea = HEAThermoEngine.computeThermodynamics(rheoElems, rheoFractions);
    assert(thermoRhea.VEC < 6.87, 'RHEA VEC must be < 6.87 (BCC)');
    assert(contains(thermoRhea.Phase, 'BCC'), 'TiZrHfNbTa must be predicted as BCC');
    assert(thermoRhea.T_Solidus > 2100, 'RHEA solidus must exceed 2100 K');
    fprintf('✓ Refractory HEA TiZrHfNbTa verified: Phase = %s, VEC = %.2f, Ts = %.1f K, Tl = %.1f K\n', ...
        thermoRhea.Phase, thermoRhea.VEC, thermoRhea.T_Solidus, thermoRhea.T_Liquidus);
        
    % Test 4: Generation of JMatPro-compatible .dat file
    tempDir = fullfile(pwd, 'materials_data');
    if ~exist(tempDir, 'dir'), mkdir(tempDir); end
    [filePath, rawTable, metrics] = HEAThermoEngine.exportJMatProDatFile(cantorComp, 'at', tempDir, 'Test_Cantor_Model.dat');
    assert(isfile(filePath), 'Generated .dat file must exist');
    assert(height(rawTable) >= 300, 'Table must contain >= 300 temperature points');
    varNames = rawTable.Properties.VariableNames;
    assert(ismember('T__K_', varNames) || ismember('T (K)', varNames) || any(contains(varNames, 'T')), 'Must have Temperature column');
    fprintf('✓ Generated .dat file verified: %s (%d rows)\n', filePath, height(rawTable));
    
    fprintf('=== All HEAThermoEngine tests PASSED! ===\n');
end
