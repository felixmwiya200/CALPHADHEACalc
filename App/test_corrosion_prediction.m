% Test script for native MATLAB HEAThermoEngine Corrosion Prediction
function test_corrosion_prediction()
    fprintf('=================================================================\n');
    fprintf('    TESTING THERMODYNAMIC CORROSION PREDICTION ENGINE IN MATLAB  \n');
    fprintf('=================================================================\n\n');
    
    % Test 1: Corrosion Elemental Database Completeness
    fprintf('--- Test 1: Corrosion Database Completeness (All 45 Elements) ---\n');
    db = HEAThermoEngine.getCorrosionDatabase();
    assert(isa(db, 'containers.Map'), 'Corrosion database must be a containers.Map');
    assert(db.Count >= 45, sprintf('Expected >= 45 elements, got %d', db.Count));
    
    keyElems = {'Cr', 'Ni', 'Fe', 'Co', 'Mo', 'Ti', 'Al', 'Ta', 'Nb', 'W', 'Zr', 'Hf'};
    for i = 1:numel(keyElems)
        el = keyElems{i};
        assert(isKey(db, el), sprintf('Database must contain %s', el));
        rec = db(el);
        assert(isfield(rec, 'E0') && isfield(rec, 'n') && isfield(rec, 'dG_ox') && ...
               isfield(rec, 'PBR') && isfield(rec, 'oxide') && isfield(rec, 'M_ox') && ...
               isfield(rec, 'rho_ox') && isfield(rec, 'n_metal'), ...
               sprintf('Element %s missing required corrosion properties', el));
        assert(rec.dG_ox < 0, sprintf('Oxide formation energy for %s must be negative', el));
        assert(rec.PBR > 0, sprintf('PBR for %s must be positive', el));
    end
    fprintf('  Database contains %d elements with reduction potentials, Ellingham energies, and PBR values\n', db.Count);
    
    % Test 2: Cantor Equiatomic Alloy (CoCrFeMnNi) Validation
    fprintf('\n--- Test 2: Cantor Equiatomic Alloy (CoCrFeMnNi) Validation ---\n');
    cantorElems = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    cantorFracs = [0.2, 0.2, 0.2, 0.2, 0.2];
    metricsCantor = HEAThermoEngine.computeThermodynamics(cantorElems, cantorFracs);
    
    assert(isfield(metricsCantor, 'Corrosion'), 'computeThermodynamics must attach .Corrosion struct');
    cCantor = metricsCantor.Corrosion;
    
    fprintf('  PREN_ASTM: %.2f | PREN_HEA: %.2f\n', cCantor.PREN_ASTM, cCantor.PREN_HEA);
    fprintf('  Delta G_ox_eff: %.1f kJ/mol O2 (Primary Oxide: %s)\n', cCantor.DeltaG_ox_eff, cCantor.PrimaryOxide);
    fprintf('  PBR_eff (Xu-Gao): %.3f (%s)\n', cCantor.PBR_eff, cCantor.PBR_Status);
    fprintf('  Delta E_galv: %.3f V | Phase Immunity: %.3f (%s)\n', cCantor.DeltaE_galv, cCantor.PhaseImmunity, cCantor.GalvanicRisk);
    fprintf('  Equivalent Weight (ASTM G102): %.3f g/eq\n', cCantor.EquivalentWeight);
    fprintf('  Predicted 3.5%% NaCl: E_corr = %.3f V_SCE, i_corr = %.4f uA/cm^2, CR = %.5f mm/yr\n', ...
        cCantor.E_corr_pred, cCantor.i_corr_NaCl, cCantor.CR_mm_yr_NaCl);
    fprintf('  Performance Grade: %s (%s)\n', cCantor.Grade, cCantor.PittingClass);
    
    assert(abs(cCantor.PREN_ASTM - 18.5) < 1.0, 'Cantor PREN_ASTM should be ~18.5');
    assert(contains(cCantor.PrimaryOxide, 'Cr2O3') || contains(cCantor.PrimaryOxide, 'MnO'), 'Cantor primary protective oxide must contain Cr2O3 or MnO');
    assert(cCantor.PBR_eff >= 1.0 && cCantor.PBR_eff <= 2.1, 'Cantor effective PBR must be in protective window [1.0, 2.1]');
    assert(contains(cCantor.PBR_Status, 'Tenacious'), 'Cantor PBR status must be Tenacious');
    assert(cCantor.PhaseImmunity > 0.70, 'Cantor single-phase FCC should exhibit high phase immunity');
    assert(abs(cCantor.EquivalentWeight - 25.5) < 0.5, 'Cantor EW should be ~25.5 g/eq');
    assert(cCantor.CR_mm_yr_NaCl < 0.02, 'Cantor corrosion rate in 3.5% NaCl must be low (< 0.02 mm/yr)');
    assert(contains(cCantor.Grade, 'Grade A'), 'Cantor grade should be Grade A');
    assert(cCantor.Benchmark.matched, 'Cantor benchmark should be matched');
    fprintf('  Cantor alloy verified against Shi et al. (2017) benchmark!\n');
    
    % Test 3: Refractory HEA (TiZrHfNbTa) Super-Passivation Validation
    fprintf('\n--- Test 3: Refractory HEA (TiZrHfNbTa) Super-Passivation ---\n');
    rheaElems = {'Ti', 'Zr', 'Hf', 'Nb', 'Ta'};
    rheaFracs = [0.2, 0.2, 0.2, 0.2, 0.2];
    metricsRhea = HEAThermoEngine.computeThermodynamics(rheaElems, rheaFracs);
    cRhea = metricsRhea.Corrosion;
    
    fprintf('  PREN_HEA: %.2f | Delta G_ox_eff: %.1f kJ/mol O2\n', cRhea.PREN_HEA, cRhea.DeltaG_ox_eff);
    fprintf('  Primary Oxide: %s | PBR_eff: %.3f (%s)\n', cRhea.PrimaryOxide, cRhea.PBR_eff, cRhea.PBR_Status);
    fprintf('  Predicted 3.5%% NaCl CR: %.6f mm/yr\n', cRhea.CR_mm_yr_NaCl);
    fprintf('  Performance Grade: %s (%s)\n', cRhea.Grade, cRhea.PittingClass);
    
    assert(cRhea.PREN_HEA > 60, 'RHEA PREN_HEA should be > 60 due to high Ti, Ta, Nb content');
    assert(cRhea.DeltaG_ox_eff < -850, 'RHEA should have very negative oxide formation energy (< -850 kJ/mol O2)');
    assert(contains(cRhea.PrimaryOxide, 'HfO2') || contains(cRhea.PrimaryOxide, 'ZrO2'), 'Primary oxide should be HfO2 or ZrO2');
    assert(cRhea.PBR_eff >= 1.0 && cRhea.PBR_eff <= 2.1, 'RHEA PBR must be in protective window');
    assert(cRhea.CR_mm_yr_NaCl < 0.002, 'RHEA corrosion rate should be ultra-low (< 0.002 mm/yr)');
    assert(contains(cRhea.Grade, 'Grade A+'), 'RHEA grade should be Grade A+');
    assert(cRhea.Benchmark.matched, 'RHEA benchmark should be matched');
    fprintf('  Refractory HEA TiZrHfNbTa verified against Shang et al. (2019) benchmark!\n');
    
    % Test 4: Phase-Separated Al1.0CoCrFeNi vs Single-Phase Al0.3CoCrFeNi
    fprintf('\n--- Test 4: Phase Separation Effect (Al1.0CoCrFeNi vs Al0.3CoCrFeNi) ---\n');
    % Al1.0CoCrFeNi (BCC + ordered B2 multiphase, known for severe galvanic pitting)
    al1Elems = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    al1Fracs = [0.2, 0.2, 0.2, 0.2, 0.2];
    metricsAl1 = HEAThermoEngine.computeThermodynamics(al1Elems, al1Fracs);
    cAl1 = metricsAl1.Corrosion;
    
    % Al0.3CoCrFeNi (FCC single phase)
    al03Fracs = [0.3/4.3, 1/4.3, 1/4.3, 1/4.3, 1/4.3];
    metricsAl03 = HEAThermoEngine.computeThermodynamics(al1Elems, al03Fracs);
    cAl03 = metricsAl03.Corrosion;
    
    fprintf('  Al0.3CoCrFeNi (Single FCC): Phase Immunity = %.3f, i_corr = %.4f uA/cm^2, Grade = %s\n', ...
        cAl03.PhaseImmunity, cAl03.i_corr_NaCl, cAl03.Grade);
    fprintf('  Al1.0CoCrFeNi (BCC + B2):   Phase Immunity = %.3f, i_corr = %.4f uA/cm^2, Grade = %s\n', ...
        cAl1.PhaseImmunity, cAl1.i_corr_NaCl, cAl1.Grade);
    
    assert(cAl1.PhaseImmunity < cAl03.PhaseImmunity, 'Al1.0 should have lower phase immunity than Al0.3');
    assert(cAl1.i_corr_NaCl > cAl03.i_corr_NaCl, 'Al1.0 should have higher corrosion current than Al0.3');
    assert(cAl1.i_corr_H2SO4 > cAl03.i_corr_H2SO4, 'Al1.0 should suffer far higher acid corrosion due to B2 dissolution');
    assert(strcmp(cAl1.Benchmark.name, 'Al1.0CoCrFeNi (BCC + B2 Multiphase)'), 'Al1.0 benchmark should match Qiu et al.');
    assert(strcmp(cAl03.Benchmark.name, 'Al0.3CoCrFeNi (Single FCC)'), 'Al0.3 benchmark should match Qiu et al.');
    fprintf('  Thermodynamic phase separation effect on micro-galvanic corrosion verified!\n');
    
    % Test 5: JMatPro Data Export Metric Verification
    fprintf('\n--- Test 5: JMatPro Data Export Metric Verification ---\n');
    tempDir = fullfile(pwd, 'materials_data');
    if ~exist(tempDir, 'dir'), mkdir(tempDir); end
    cantorComp = {'Co', 20; 'Cr', 20; 'Fe', 20; 'Mn', 20; 'Ni', 20};
    [filePath, ~, metricsExport] = HEAThermoEngine.exportJMatProDatFile(cantorComp, 'at', tempDir, 'Test_Corrosion_Export.dat');
    assert(isfield(metricsExport, 'Corrosion'), 'Exported metrics must include Corrosion field');
    assert(metricsExport.Corrosion.EquivalentWeight > 0, 'Corrosion EW must be positive');
    fprintf('  Export pipeline retains all corrosion thermodynamic metrics!\n');
    
    fprintf('\n=================================================================\n');
    fprintf('        ALL CORROSION PREDICTION UNIT TESTS PASSED (5/5)!        \n');
    fprintf('=================================================================\n');
end
