% test_alloy_benchmark_expansion.m
% Validates the expanded peer-reviewed HEA/MEA/RHEA database across
% LiteratureBenchmark, HEAThermoEngine, and HEAXRDEngine.

fprintf('=== Testing Expanded Alloy Benchmark Database ===\n');

% Initialize engines
litBench = LiteratureBenchmark();

%% 1. Test LiteratureBenchmark Key Matching & Curve Retrieval
testCases = {
    'cocrni', {'Co', 'Cr', 'Ni'}, [33.33, 33.33, 33.34], 1703, 'CoCrNi';
    'fe50mn30co10cr10', {'Fe', 'Mn', 'Co', 'Cr'}, [50, 30, 10, 10], 1615, 'Fe50Mn30Co10Cr10';
    'fe40mn20cr20ni20', {'Fe', 'Mn', 'Cr', 'Ni'}, [40, 20, 20, 20], 1595, 'Fe40Mn20Cr20Ni20';
    'monbtavw', {'Mo', 'Nb', 'Ta', 'V', 'W'}, [20, 20, 20, 20, 20], 2900, 'MoNbTaVW';
    'tizrhfnbta', {'Ti', 'Zr', 'Hf', 'Nb', 'Ta'}, [20, 20, 20, 20, 20], 2453, 'TiZrHfNbTa'
};

for i = 1:size(testCases, 1)
    key = testCases{i, 1};
    elems = testCases{i, 2};
    vals = testCases{i, 3};
    expTm = testCases{i, 4};
    name = testCases{i, 5};
    
    [hasMat, matData] = litBench.lookupMaterial(key);
    assert(hasMat, sprintf('Failed to lookup material %s in published database', key));
    assert(abs(matData.meltingPoint_K - expTm) <= 20, ...
        sprintf('%s melting point mismatch: expected ~%d, got %.1f', name, expTm, matData.meltingPoint_K));
    assert(isfield(matData.properties, 'density'), sprintf('%s missing density', name));
    assert(isfield(matData.properties, 'thermal_conductivity'), sprintf('%s missing thermal conductivity', name));
    
    % Test dynamic composition parsing & key matching
    compStr = '';
    for k = 1:numel(elems)
        compStr = sprintf('%s%s %.1f ', compStr, elems{k}, vals(k));
    end
    cComp = litBench.parseComposition(compStr, 'at%');
    matchedKey = litBench.matchMaterialKey('', cComp);
    assert(strcmp(matchedKey, key), ...
        sprintf('matchMaterialKey for %s returned %s instead of %s', name, matchedKey, key));
    
    fprintf('  [PASS] LiteratureBenchmark: %s matched key "%s" (Tm = %d K)\n', name, key, expTm);
end

%% 2. Test HEAThermoEngine Solidus/Liquidus Calibration & Phases
fprintf('\n--- Testing HEAThermoEngine Calibrations ---\n');

% CoCrNi MEA
resCoCrNi = HEAThermoEngine.computeThermodynamics({'Co', 'Cr', 'Ni'}, [1/3, 1/3, 1/3]);
assert(abs(resCoCrNi.T_Solidus - 1673.0) <= 2.0, sprintf('CoCrNi Ts error: %.1f', resCoCrNi.T_Solidus));
assert(abs(resCoCrNi.T_Liquidus - 1703.0) <= 2.0, sprintf('CoCrNi Tl error: %.1f', resCoCrNi.T_Liquidus));
assert(contains(resCoCrNi.Phase, 'FCC'), 'CoCrNi should be FCC');
fprintf('  [PASS] CoCrNi MEA: Ts = %.1f K, Tl = %.1f K, Phase = %s\n', ...
    resCoCrNi.T_Solidus, resCoCrNi.T_Liquidus, resCoCrNi.Phase);

% Fe50Mn30Co10Cr10 TRIP-HEA
resTRIP = HEAThermoEngine.computeThermodynamics({'Fe', 'Mn', 'Co', 'Cr'}, [0.50, 0.30, 0.10, 0.10]);
assert(abs(resTRIP.T_Solidus - 1515.0) <= 2.0, sprintf('TRIP Ts error: %.1f', resTRIP.T_Solidus));
assert(abs(resTRIP.T_Liquidus - 1615.0) <= 2.0, sprintf('TRIP Tl error: %.1f', resTRIP.T_Liquidus));
assert(contains(resTRIP.Phase, 'HCP') || contains(resTRIP.Phase, 'TRIP'), 'TRIP HEA should note HCP/TRIP');
fprintf('  [PASS] Fe50Mn30Co10Cr10 TRIP-HEA: Ts = %.1f K, Tl = %.1f K, Phase = %s\n', ...
    resTRIP.T_Solidus, resTRIP.T_Liquidus, resTRIP.Phase);

% Fe40Mn20Cr20Ni20 TWIP-HEA
resTWIP = HEAThermoEngine.computeThermodynamics({'Fe', 'Mn', 'Cr', 'Ni'}, [0.40, 0.20, 0.20, 0.20]);
assert(abs(resTWIP.T_Solidus - 1530.0) <= 2.0, sprintf('TWIP Ts error: %.1f', resTWIP.T_Solidus));
assert(abs(resTWIP.T_Liquidus - 1595.0) <= 2.0, sprintf('TWIP Tl error: %.1f', resTWIP.T_Liquidus));
assert(contains(resTWIP.Phase, 'FCC'), 'TWIP HEA should be FCC');
fprintf('  [PASS] Fe40Mn20Cr20Ni20 TWIP-HEA: Ts = %.1f K, Tl = %.1f K, Phase = %s\n', ...
    resTWIP.T_Solidus, resTWIP.T_Liquidus, resTWIP.Phase);

% MoNbTaVW Refractory HEA
resMoNbTaVW = HEAThermoEngine.computeThermodynamics({'Mo', 'Nb', 'Ta', 'V', 'W'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
assert(abs(resMoNbTaVW.T_Solidus - 2650.0) <= 2.0, sprintf('MoNbTaVW Ts error: %.1f', resMoNbTaVW.T_Solidus));
assert(abs(resMoNbTaVW.T_Liquidus - 2900.0) <= 2.0, sprintf('MoNbTaVW Tl error: %.1f', resMoNbTaVW.T_Liquidus));
assert(contains(resMoNbTaVW.Phase, 'BCC'), 'MoNbTaVW should be BCC');
fprintf('  [PASS] MoNbTaVW Refractory HEA: Ts = %.1f K, Tl = %.1f K, Phase = %s\n', ...
    resMoNbTaVW.T_Solidus, resMoNbTaVW.T_Liquidus, resMoNbTaVW.Phase);

% TiZrHfNbTa Refractory HEA
resTiZrHf = HEAThermoEngine.computeThermodynamics({'Ti', 'Zr', 'Hf', 'Nb', 'Ta'}, [0.2, 0.2, 0.2, 0.2, 0.2]);
assert(abs(resTiZrHf.T_Solidus - 2225.0) <= 2.0, sprintf('TiZrHfNbTa Ts error: %.1f', resTiZrHf.T_Solidus));
assert(abs(resTiZrHf.T_Liquidus - 2380.0) <= 2.0, sprintf('TiZrHfNbTa Tl error: %.1f', resTiZrHf.T_Liquidus));
assert(contains(resTiZrHf.Phase, 'BCC'), 'TiZrHfNbTa should be BCC');
fprintf('  [PASS] TiZrHfNbTa Refractory HEA: Ts = %.1f K, Tl = %.1f K, Phase = %s\n', ...
    resTiZrHf.T_Solidus, resTiZrHf.T_Liquidus, resTiZrHf.Phase);

%% 3. Test HEAXRDEngine Diffraction & Benchmark Curves
fprintf('\n--- Testing HEAXRDEngine Crystallography & Benchmark Diffraction ---\n');

% Test CoCrNi XRD
xrdCoCrNi = HEAXRDEngine.calculateXRD({'Co', 'Cr', 'Ni'}, [1/3, 1/3, 1/3], 'Cu');
assert(xrdCoCrNi.benchmarkExp.hasData, 'CoCrNi should have experimental benchmark overlay');
assert(contains(xrdCoCrNi.benchmarkExp.title, 'CoCrNi'), 'Overlay should match CoCrNi');
twoThetas = [xrdCoCrNi.peaks.twoTheta];
assert(any(abs(twoThetas - 43.95) < 0.5), 'CoCrNi should have (111) peak near 43.95 deg');
fprintf('  [PASS] CoCrNi XRD: (111) at %.2f deg, Benchmark overlay present (%d pts)\n', ...
    twoThetas(1), numel(xrdCoCrNi.benchmarkExp.intensity));

% Test Fe50Mn30Co10Cr10 TRIP-HEA XRD (FCC + HCP)
xrdTRIP = HEAXRDEngine.calculateXRD({'Fe', 'Mn', 'Co', 'Cr'}, [0.50, 0.30, 0.10, 0.10], 'Cu');
assert(xrdTRIP.benchmarkExp.hasData, 'TRIP-HEA should have experimental benchmark overlay');
assert(any(contains(xrdTRIP.phases, 'HCP')), 'TRIP-HEA should identify HCP phase');
peakPhases = {xrdTRIP.peaks.phase};
assert(any(contains(peakPhases, 'HCP')), 'TRIP-HEA should have indexed HCP peaks');
fprintf('  [PASS] Fe50Mn30Co10Cr10 TRIP-HEA XRD: Indexed dual-phase FCC + HCP reflections, Benchmark overlay present\n');

% Test MoNbTaVW Refractory HEA XRD
xrdMoNbTaVW = HEAXRDEngine.calculateXRD({'Mo', 'Nb', 'Ta', 'V', 'W'}, [0.2, 0.2, 0.2, 0.2, 0.2], 'Cu');
assert(xrdMoNbTaVW.benchmarkExp.hasData, 'MoNbTaVW should have experimental benchmark overlay');
twoThetasMo = [xrdMoNbTaVW.peaks.twoTheta];
assert(any(abs(twoThetasMo - 39.90) < 0.5), 'MoNbTaVW should have (110) peak near 39.90 deg');
fprintf('  [PASS] MoNbTaVW XRD: (110) at %.2f deg, Benchmark overlay present\n', twoThetasMo(1));

% Test TiZrHfNbTa Refractory HEA XRD
xrdTiZrHf = HEAXRDEngine.calculateXRD({'Ti', 'Zr', 'Hf', 'Nb', 'Ta'}, [0.2, 0.2, 0.2, 0.2, 0.2], 'Cu');
assert(xrdTiZrHf.benchmarkExp.hasData, 'TiZrHfNbTa should have experimental benchmark overlay');
twoThetasTi = [xrdTiZrHf.peaks.twoTheta];
assert(any(abs(twoThetasTi - 37.25) < 0.5), 'TiZrHfNbTa should have (110) peak near 37.25 deg');
fprintf('  [PASS] TiZrHfNbTa XRD: (110) at %.2f deg, Benchmark overlay present\n', twoThetasTi(1));

fprintf('\n=================================================================\n');
fprintf('  ALL ALLOY BENCHMARK EXPANSION TESTS PASSED PERFECTLY!\n');
fprintf('=================================================================\n');
