% test_hea_full_e2e.m
% Comprehensive End-to-End Test Suite for Native HEA Thermodynamic Database,
% Unit Conversions (at%, wt%, mol), Literature Benchmarking, and Export.

global numPassed numTotal;
numPassed = 0;
numTotal = 0;

fprintf('=================================================================\n');
fprintf('  RUNNING COMPREHENSIVE HEA THERMODYNAMIC & BENCHMARK E2E TESTS\n');
fprintf('=================================================================\n\n');

try
    %% TEST 1: Element Database & Constants Coverage
    fprintf('--- Test 1: Periodic Table & SGTE Elements Coverage ---\n');
    elements = HEAThermoEngine.getAllSupportedElements();
    checkAssertion(numel(elements) >= 40, sprintf('Supported elements count (%d >= 40)', numel(elements)));
    checkAssertion(ismember('Fe', elements), 'Fe is supported');
    checkAssertion(ismember('Co', elements), 'Co is supported');
    checkAssertion(ismember('Cr', elements), 'Cr is supported');
    checkAssertion(ismember('Ni', elements), 'Ni is supported');
    checkAssertion(ismember('Mn', elements), 'Mn is supported');
    checkAssertion(ismember('Al', elements), 'Al is supported');
    checkAssertion(ismember('Ti', elements), 'Ti is supported');
    checkAssertion(ismember('Zr', elements), 'Zr is supported');
    checkAssertion(ismember('Hf', elements), 'Hf is supported');
    checkAssertion(ismember('Nb', elements), 'Nb is supported');
    checkAssertion(ismember('Ta', elements), 'Ta is supported');
    checkAssertion(ismember('W',  elements), 'W is supported');
    checkAssertion(ismember('Mo', elements), 'Mo is supported');
    checkAssertion(ismember('V',  elements), 'V is supported');

    %% TEST 2: Bidirectional Conversions (at%, wt%, mol)
    fprintf('\n--- Test 2: Composition Unit Conversions (at%% <-> wt%% <-> mol) ---\n');
    % Cantor alloy: Equiatomic Co-Cr-Fe-Mn-Ni (20% each)
    cantorAt = {'Co', 20; 'Cr', 20; 'Fe', 20; 'Mn', 20; 'Ni', 20};

    % Convert at% -> wt%
    [cantorWt, sumWt] = HEAThermoEngine.convertComposition(cantorAt, 'at', 'wt');
    checkAssertion(abs(sumWt.TotalComposition - 100) < 1e-3, 'Cantor wt% sum is 100%');
    checkAssertion(abs(sumWt.MeanMolarMass - 55.67) < 0.5, sprintf('Cantor mean molar mass is ~55.67 g/mol (got %.2f)', sumWt.MeanMolarMass));

    % Convert wt% back to at%
    [cantorAtBack, sumAtBack] = HEAThermoEngine.convertComposition(cantorWt, 'wt', 'at');
    for i = 1:5
        checkAssertion(abs(cantorAtBack{i,2} - 20) < 1e-2, sprintf('Cantor element %s converted back to 20 at%% (got %.3f)', cantorAtBack{i,1}, cantorAtBack{i,2}));
    end

    % Convert at% -> mol (1 mol basis)
    [cantorMol, sumMol] = HEAThermoEngine.convertComposition(cantorAt, 'at', 'mol');
    checkAssertion(abs(sumMol.TotalMoles - 1.0) < 1e-4, 'Cantor total moles is 1.0 mol');
    for i = 1:5
        checkAssertion(abs(cantorMol{i,2} - 0.2) < 1e-4, sprintf('Cantor element %s has 0.2 mol (got %.4f)', cantorMol{i,1}, cantorMol{i,2}));
    end

    % Convert mol -> wt%
    [cantorWtFromMol, sumWtFromMol] = HEAThermoEngine.convertComposition(cantorMol, 'mol', 'wt');
    for i = 1:5
        checkAssertion(abs(cantorWtFromMol{i,2} - cantorWt{i,2}) < 1e-3, sprintf('Cantor wt%% from mol matches direct wt%% for %s', cantorWtFromMol{i,1}));
    end

    %% TEST 3: Thermodynamic Solid Solution Predictors (Guo VEC, Yang-Zhang Omega, delta)
    fprintf('\n--- Test 3: Thermodynamic Solid Solution & Phase Predictors ---\n');
    % Cantor alloy
    cantorMetrics = HEAThermoEngine.computeThermodynamics(cantorAt, 'at');
    checkAssertion(abs(cantorMetrics.VEC - 8.0) < 0.1, sprintf('Cantor VEC is 8.0 (got %.2f)', cantorMetrics.VEC));
    checkAssertion(contains(cantorMetrics.Phase, 'FCC'), sprintf('Cantor predicted phase contains FCC (got %s)', cantorMetrics.Phase));
    checkAssertion(cantorMetrics.DeltaS_mix > 13.0, sprintf('Cantor DeltaS_mix is high entropy > 13 J/(mol K) (got %.2f)', cantorMetrics.DeltaS_mix));
    checkAssertion(cantorMetrics.Delta_size < 5.0, sprintf('Cantor atomic size mismatch delta < 5%% (got %.2f%%)', cantorMetrics.Delta_size));
    checkAssertion(cantorMetrics.T_Solidus > 1500 && cantorMetrics.T_Solidus < 1650, sprintf('Cantor solidus in realistic range 1500-1650 K (got %.0f K)', cantorMetrics.T_Solidus));

    % Refractory HEA: NbMoTaW (VEC = 5.5, BCC solid solution)
    nbmotawAt = {'Nb', 25; 'Mo', 25; 'Ta', 25; 'W', 25};
    nbmotawMetrics = HEAThermoEngine.computeThermodynamics(nbmotawAt, 'at');
    checkAssertion(abs(nbmotawMetrics.VEC - 5.5) < 0.1, sprintf('NbMoTaW VEC is 5.5 (got %.2f)', nbmotawMetrics.VEC));
    checkAssertion(contains(nbmotawMetrics.Phase, 'BCC'), sprintf('NbMoTaW predicted phase contains BCC (got %s)', nbmotawMetrics.Phase));
    checkAssertion(nbmotawMetrics.T_Solidus > 2800, sprintf('NbMoTaW refractory solidus > 2800 K (got %.0f K)', nbmotawMetrics.T_Solidus));

    % Refractory HEA: TiZrHfNbTa (VEC = 4.4, BCC solid solution)
    tizrhfAt = {'Ti', 20; 'Zr', 20; 'Hf', 20; 'Nb', 20; 'Ta', 20};
    tizrhfMetrics = HEAThermoEngine.computeThermodynamics(tizrhfAt, 'at');
    checkAssertion(abs(tizrhfMetrics.VEC - 4.4) < 0.1, sprintf('TiZrHfNbTa VEC is 4.4 (got %.2f)', tizrhfMetrics.VEC));
    checkAssertion(contains(tizrhfMetrics.Phase, 'BCC'), sprintf('TiZrHfNbTa predicted phase contains BCC (got %s)', tizrhfMetrics.Phase));
    checkAssertion(tizrhfMetrics.T_Solidus > 2200, sprintf('TiZrHfNbTa solidus > 2200 K (got %.0f K)', tizrhfMetrics.T_Solidus));

    %% TEST 4: Temperature-Dependent Table Generation & Physics Consistency
    fprintf('\n--- Test 4: Temperature-Dependent Property Curves (293 - 3500 K) ---\n');
    T_range = [293.15, 3000];
    [tab, metrics] = HEAThermoEngine.computePropertyCurves(cantorAt, 'at', T_range, 100);
    checkAssertion(height(tab) == 100, 'Property curve has 100 points');
    
    dens_kg_m3 = tab.("Density (g/(cm)^3)-TOTAL") * 1000;
    checkAssertion(all(dens_kg_m3 > 6000 & dens_kg_m3 < 8500), 'Cantor density in realistic 6000-8500 kg/m^3 range up to 3000 K');
    checkAssertion(dens_kg_m3(1) > 7900 && dens_kg_m3(1) < 8200, sprintf('Cantor room-temp density is ~8050 kg/m^3 (got %.1f)', dens_kg_m3(1)));
    
    k_val = tab.("Thermal conductivity (W/(m*K))-TOTAL");
    checkAssertion(all(k_val > 5 & k_val < 100), 'Cantor thermal conductivity in realistic 5-100 W/(m K) range');
    checkAssertion(k_val(1) > 8 && k_val(1) < 22, sprintf('Cantor room-temp thermal conductivity ~12 W/(m K) (got %.1f)', k_val(1)));
    
    e_val = tab.("Young's modulus (GPa)-TOTAL");
    checkAssertion(all(e_val >= 0 & e_val <= 230), 'Cantor Young modulus non-negative and <= 230 GPa');
    checkAssertion(e_val(1) > 180, 'Cantor Young modulus at room temp > 180 GPa');
    checkAssertion(e_val(end) == 0, 'Cantor Young modulus in liquid pool drops to 0 GPa');

    %% TEST 5: JMatPro .dat Export Compatibility
    fprintf('\n--- Test 5: JMatPro .dat Export Compatibility ---\n');
    dataFolder = fullfile(pwd, 'materials_data');
    if ~exist(dataFolder, 'dir'), mkdir(dataFolder); end
    [filePath, exportedTab, expMetrics] = HEAThermoEngine.exportJMatProDatFile(cantorAt, 'at', dataFolder, 'Generated_HEA_Model.dat');
    checkAssertion(isfile(filePath), 'Generated_HEA_Model.dat exists on disk');
    checkAssertion(height(exportedTab) > 50, 'Exported table has > 50 temperature rows');

    % Verify file can be read line by line
    rawLines = readlines(filePath);
    checkAssertion(numel(rawLines) > 60, 'File has sufficient lines');
    checkAssertion(contains(rawLines(1), 'T (K)'), 'Header contains T (K)');
    checkAssertion(contains(rawLines(1), 'Density'), 'Header contains Density');

    %% TEST 6: Literature Benchmark Lookup & Experimental Validation
    fprintf('\n--- Test 6: Literature Benchmark Lookup & Experimental Validation ---\n');
    litBench = LiteratureBenchmark();
    [hasCantor, cantorLit] = litBench.lookupMaterial('CoCrFeMnNi');
    checkAssertion(hasCantor, 'Cantor alloy matched in Literature Benchmark database');
    checkAssertion(~isempty(cantorLit.properties.density.citation), 'Cantor benchmark has density citation');
    checkAssertion(~isempty(cantorLit.properties.density.doi), 'Cantor benchmark has density DOI');

    [hasNbMoTaW, nbmotawLit] = litBench.lookupMaterial('NbMoTaW');
    checkAssertion(hasNbMoTaW, 'NbMoTaW matched in Literature Benchmark database');
    checkAssertion(nbmotawLit.meltingPoint_K > 2800, 'NbMoTaW benchmark melting point > 2800 K');

    [hasTiZr, tizrhfLit] = litBench.lookupMaterial('TiZrHfNbTa');
    checkAssertion(hasTiZr, 'TiZrHfNbTa matched in Literature Benchmark database');

    % Check comparison error calculation
    T_user = linspace(300, 1500, 30)';
    Y_user = 8050 - 0.35 * (T_user - 293.15); % Synthetic realistic density
    [hasComp, compRes] = litBench.getComparison('Generated_HEA_Model.dat', 'Density', T_user, Y_user, 'Co20Cr20Fe20Mn20Ni20', 'at', false);
    checkAssertion(hasComp, 'Comparison successfully evaluated');
    checkAssertion(compRes.MRE < 5.0, sprintf('Cantor density MRE < 5%% (got %.2f%%)', compRes.MRE));
    checkAssertion(compRes.HasCurve, 'Comparison returned benchmark curve');
    checkAssertion(~isempty(compRes.T_plot) && ~isempty(compRes.Y_plot), 'Benchmark T_plot and Y_plot are populated');

    %% SUMMARY
    fprintf('\n=================================================================\n');
    fprintf('  ALL %d/%d HEA TESTS PASSED PERFECTLY!\n', numPassed, numTotal);
    fprintf('=================================================================\n');

catch ME
    fprintf('\n[ERROR] Test execution failed:\n%s\n', ME.message);
    for s = 1:numel(ME.stack)
        fprintf('  File: %s (Line: %d)\n', ME.stack(s).file, ME.stack(s).line);
    end
    exit(1);
end

exit(0);

function checkAssertion(cond, name)
    global numPassed numTotal;
    numTotal = numTotal + 1;
    if cond
        fprintf('  [PASS] %s\n', name);
        numPassed = numPassed + 1;
    else
        fprintf('  [FAIL] %s\n', name);
        error('Assertion failed: %s', name);
    end
end
