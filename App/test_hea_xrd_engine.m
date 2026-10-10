% Unit Test: HEA X-Ray Diffraction (XRD) Simulation Engine
% Tests Bragg angle indexing, lattice parameter calculation, phase identification,
% wavelength switching, and continuous diffractogram synthesis.
function test_hea_xrd_engine()
    fprintf('=== Testing HEAXRDEngine Crystallographic & Diffraction Module ===\n');
    
    % Test 1: Cantor Alloy CoCrFeMnNi (Single FCC Phase, a ~ 3.596 A)
    elems_cantor = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    x_cantor = [0.2, 0.2, 0.2, 0.2, 0.2];
    
    xrdCantor = HEAXRDEngine.calculateXRD(elems_cantor, x_cantor, 'Cu', 45, 0.003);
    assert(isfield(xrdCantor, 'twoTheta'), 'Must contain twoTheta array');
    assert(isfield(xrdCantor, 'intensity'), 'Must contain intensity array');
    assert(isfield(xrdCantor, 'peaks'), 'Must contain indexed peaks struct array');
    assert(numel(xrdCantor.twoTheta) > 1000, 'Diffractogram must have high resolution');
    assert(abs(max(xrdCantor.intensity) - 100.0) < 1e-3, 'Intensity must be normalized to 100%');
    
    % Check Cantor lattice parameter
    assert(abs(xrdCantor.latticeParams.a_FCC - 3.596) < 0.03, ...
        sprintf('Cantor a_FCC should be ~3.596 A, got %.3f', xrdCantor.latticeParams.a_FCC));
    
    % Check primary FCC peaks: (111) at ~43.6 deg, (200) at ~50.8 deg, (220) at ~74.7 deg
    pList = xrdCantor.peaks;
    twoThetas = [pList.twoTheta];
    hklStrs = {pList.hkl};
    
    idx111 = find(strcmp(hklStrs, '(111)'), 1);
    assert(~isempty(idx111), 'Must identify (111) peak for FCC Cantor');
    assert(abs(twoThetas(idx111) - 43.6) < 0.5, ...
        sprintf('(111) peak should be at ~43.6 deg, got %.2f deg', twoThetas(idx111)));
    
    idx200 = find(strcmp(hklStrs, '(200)'), 1);
    assert(~isempty(idx200), 'Must identify (200) peak for FCC Cantor');
    assert(abs(twoThetas(idx200) - 50.8) < 0.5, ...
        sprintf('(200) peak should be at ~50.8 deg, got %.2f deg', twoThetas(idx200)));
    
    fprintf('✓ Cantor alloy FCC diffraction peaks verified: (111)=%.2f°, (200)=%.2f°, a=%.3f Å\n', ...
        twoThetas(idx111), twoThetas(idx200), xrdCantor.latticeParams.a_FCC);
    
    % Test 2: Equiatomic AlCoCrFeNi (BCC + B2 Ordered Phase, a ~ 2.885 A)
    elems_al = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    x_al = [0.2, 0.2, 0.2, 0.2, 0.2];
    xrdAl = HEAXRDEngine.calculateXRD(elems_al, x_al, 'Cu', 45, 0.0035);
    
    assert(any(strcmp(xrdAl.phases, 'BCC (A2)')) || any(contains(xrdAl.phases, 'BCC')), ...
        'AlCoCrFeNi must include BCC/B2 phases');
    assert(abs(xrdAl.latticeParams.a_BCC - 2.885) < 0.03, ...
        sprintf('AlCoCrFeNi a_BCC should be ~2.885 A, got %.3f', xrdAl.latticeParams.a_BCC));
    
    % Check primary BCC peak: (110) at ~44.4 deg and (200) at ~64.6 deg
    pAl = xrdAl.peaks;
    twoThetasAl = [pAl.twoTheta];
    hklAl = {pAl.hkl};
    
    idx110 = find(strcmp(hklAl, '(110)'), 1);
    assert(~isempty(idx110), 'Must identify (110) peak for BCC');
    assert(abs(twoThetasAl(idx110) - 44.4) < 0.5, ...
        sprintf('(110) peak should be at ~44.4 deg, got %.2f deg', twoThetasAl(idx110)));
    
    % Check for B2 superlattice reflection (100) at ~31.0 deg
    idx100 = find(strcmp(hklAl, '(100) B2'), 1);
    if isempty(idx100), idx100 = find(strcmp(hklAl, '(100)'), 1); end
    assert(~isempty(idx100), 'Must identify B2 (100) superlattice peak for AlCoCrFeNi');
    assert(abs(twoThetasAl(idx100) - 31.0) < 0.6, ...
        sprintf('B2 (100) peak should be at ~31.0 deg, got %.2f deg', twoThetasAl(idx100)));
    
    fprintf('✓ AlCoCrFeNi BCC+B2 diffraction peaks verified: (100)_B2=%.2f°, (110)=%.2f°, a=%.3f Å\n', ...
        twoThetasAl(idx100), twoThetasAl(idx110), xrdAl.latticeParams.a_BCC);
        
    % Test 3: Wavelength Switching (Co-Ka radiation lambda = 1.789 A)
    xrdCoTube = HEAXRDEngine.calculateXRD(elems_cantor, x_cantor, 'Co', 45, 0.003);
    pCo = xrdCoTube.peaks;
    idx111Co = find(strcmp({pCo.hkl}, '(111)'), 1);
    assert(~isempty(idx111Co), 'Co-Ka must have (111) peak');
    % Longer wavelength lambda=1.789 A shifts (111) from ~43.6 deg to ~51.1 deg
    assert(pCo(idx111Co).twoTheta > 49.0 && pCo(idx111Co).twoTheta < 53.0, ...
        sprintf('Co-Ka (111) should shift to ~51 deg, got %.2f deg', pCo(idx111Co).twoTheta));
    fprintf('✓ Wavelength switching to Co-Ka verified: (111) shifted to %.2f°\n', pCo(idx111Co).twoTheta);
    
    % Test 4: Benchmark Experimental Comparison Curve
    assert(isfield(xrdAl, 'benchmarkExp'), 'AlCoCrFeNi must include benchmark experimental pattern');
    assert(~isempty(xrdAl.benchmarkExp.twoTheta), 'Experimental twoTheta must not be empty');
    assert(~isempty(xrdAl.benchmarkExp.intensity), 'Experimental intensity must not be empty');
    fprintf('✓ Experimental XRD benchmark overlay present for AlCoCrFeNi (%d pts)\n', ...
        numel(xrdAl.benchmarkExp.twoTheta));
        
    fprintf('=== All HEAXRDEngine Tests PASSED! ===\n');
end
