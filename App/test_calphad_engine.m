% Unit Test Suite for Advanced CALPHAD Engine in HEAThermoEngine.m
function test_calphad_engine()
    fprintf('=================================================================\n');
    fprintf('       TESTING NATIVE CALPHAD THERMODYNAMICS ENGINE IN MATLAB     \n');
    fprintf('=================================================================\n\n');
    
    %% TEST 1: SGTE Unary Database Evaluation
    fprintf('--- Test 1: SGTE Pure Element Unary Functions ---\n');
    testElems = {'Fe', 'Ni', 'Co', 'Cr', 'Al', 'Mn', 'Ti', 'Nb', 'Mo', 'Ta', 'W'};
    phases = {'FCC_A1', 'BCC_A2', 'LIQUID'};
    for i = 1:numel(testElems)
        el = testElems{i};
        for j = 1:numel(phases)
            ph = phases{j};
            g_val = HEAThermoEngine.computeSGTEUnaryGibbs(el, ph, 1000.0);
            assert(~isnan(g_val) && ~isinf(g_val), sprintf('SGTE G for %s (%s) must be finite', el, ph));
        end
    end
    fprintf('  [PASS] All 11 primary HEA elements evaluate finite SGTE Gibbs energies across FCC, BCC, and LIQUID\n');
    
    % Verify relative phase stability of pure elements at 1000 K
    g_ni_fcc = HEAThermoEngine.computeSGTEUnaryGibbs('Ni', 'FCC_A1', 1000.0);
    g_ni_bcc = HEAThermoEngine.computeSGTEUnaryGibbs('Ni', 'BCC_A2', 1000.0);
    assert(g_ni_fcc < g_ni_bcc, 'Pure Ni must be more stable in FCC than BCC');
    fprintf('  [PASS] Pure Ni: G_FCC (%.1f J/mol) < G_BCC (%.1f J/mol) correctly predicts FCC ground state\n', g_ni_fcc, g_ni_bcc);
    
    g_cr_bcc = HEAThermoEngine.computeSGTEUnaryGibbs('Cr', 'BCC_A2', 1000.0);
    g_cr_fcc = HEAThermoEngine.computeSGTEUnaryGibbs('Cr', 'FCC_A1', 1000.0);
    assert(g_cr_bcc < g_cr_fcc, 'Pure Cr must be more stable in BCC than FCC');
    fprintf('  [PASS] Pure Cr: G_BCC (%.1f J/mol) < G_FCC (%.1f J/mol) correctly predicts BCC ground state\n', g_cr_bcc, g_cr_fcc);
    
    %% TEST 2: Inden-Hillert-Jarl Magnetic Contribution
    fprintf('\n--- Test 2: Inden-Hillert-Jarl Magnetic Gibbs Energy ---\n');
    % Pure Fe BCC at 800 K (below Tc = 1043 K)
    g_mag_fe800 = HEAThermoEngine.computeMagneticGibbs({'Fe'}, [1.0], 'BCC_A2', 800.0);
    % Pure Fe BCC at 1500 K (above Tc = 1043 K)
    g_mag_fe1500 = HEAThermoEngine.computeMagneticGibbs({'Fe'}, [1.0], 'BCC_A2', 1500.0);
    
    fprintf('Pure Fe BCC: G_mag(800 K) = %.1f J/mol, G_mag(1500 K) = %.1f J/mol\n', g_mag_fe800, g_mag_fe1500);
    assert(g_mag_fe800 < -1000.0, 'Ferromagnetic Fe at 800 K must have large negative G_mag');
    assert(abs(g_mag_fe1500) < abs(g_mag_fe800), 'Magnetic energy magnitude must decrease well above Tc');
    fprintf('  [PASS] Inden-Hillert magnetic stabilization verified for ferromagnetic Fe\n');
    
    %% TEST 3: Multicomponent Cantor Alloy CALPHAD Stability (CoCrFeMnNi)
    fprintf('\n--- Test 3: Cantor Alloy (CoCrFeMnNi) CALPHAD Equilibrium ---\n');
    cantorElems = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    cantorX = [0.2, 0.2, 0.2, 0.2, 0.2];
    
    cantorStab = HEAThermoEngine.computeCALPHADPhaseStability(cantorElems, cantorX, 1000.0);
    fprintf('Cantor at 1000 K: G_FCC = %.1f J/mol, G_BCC = %.1f J/mol, Driving force (BCC - FCC) = %.1f J/mol\n', ...
        cantorStab.G_FCC, cantorStab.G_BCC, cantorStab.DrivingForce_BCC_vs_FCC);
    assert(contains(cantorStab.StablePhase, 'FCC'), 'Cantor alloy must be predicted as FCC stable by CALPHAD');
    assert(cantorStab.G_FCC < cantorStab.G_BCC, 'Cantor alloy G_FCC must be lower than G_BCC');
    assert(cantorStab.T0_Melting > 1400 && cantorStab.T0_Melting < 1800, sprintf('Cantor T0 must be ~1550-1650 K (got %.1f K)', cantorStab.T0_Melting));
    fprintf('  [PASS] Cantor alloy CALPHAD phase stability & T0 melting verified: %s, T0 = %.1f K\n', ...
        cantorStab.StablePhase, cantorStab.T0_Melting);
        
    %% TEST 4: Refractory HEA CALPHAD Stability (NbMoTaW)
    fprintf('\n--- Test 4: Refractory HEA (NbMoTaW) CALPHAD Equilibrium ---\n');
    rheoElems = {'Nb', 'Mo', 'Ta', 'W'};
    rheoX = [0.25, 0.25, 0.25, 0.25];
    
    rheoStab = HEAThermoEngine.computeCALPHADPhaseStability(rheoElems, rheoX, 1500.0);
    fprintf('NbMoTaW at 1500 K: G_BCC = %.1f J/mol, G_FCC = %.1f J/mol, Driving force = %.1f J/mol\n', ...
        rheoStab.G_BCC, rheoStab.G_FCC, rheoStab.DrivingForce_BCC_vs_FCC);
    assert(contains(rheoStab.StablePhase, 'BCC'), 'NbMoTaW must be predicted as BCC stable by CALPHAD');
    assert(rheoStab.G_BCC < rheoStab.G_FCC, 'NbMoTaW G_BCC must be substantially lower than G_FCC');
    assert(rheoStab.T0_Melting > 2600, sprintf('NbMoTaW refractory T0 melting > 2600 K (got %.1f K)', rheoStab.T0_Melting));
    fprintf('  [PASS] Refractory NbMoTaW CALPHAD stability & T0 melting verified: %s, T0 = %.1f K\n', ...
        rheoStab.StablePhase, rheoStab.T0_Melting);
        
    %% TEST 5: Integration into computeThermodynamics metrics struct
    fprintf('\n--- Test 5: Integration into computeThermodynamics API ---\n');
    cantorComp = {'Co', 20; 'Cr', 20; 'Fe', 20; 'Mn', 20; 'Ni', 20};
    metrics = HEAThermoEngine.computeThermodynamics(cantorComp, 'at');
    assert(isfield(metrics, 'CALPHAD'), 'metrics struct must contain CALPHAD field');
    assert(isfield(metrics.CALPHAD, 'G_FCC'), 'CALPHAD metrics must contain G_FCC');
    assert(isfield(metrics.CALPHAD, 'G_BCC'), 'CALPHAD metrics must contain G_BCC');
    assert(isfield(metrics.CALPHAD, 'T0_Melting'), 'CALPHAD metrics must contain T0_Melting');
    fprintf('  [PASS] computeThermodynamics successfully exposes metrics.CALPHAD\n');
    
    %% TEST 6: CALPHAD Heat Capacity Curve Evaluation
    fprintf('\n--- Test 6: CALPHAD Specific Heat Capacity Derivation ---\n');
    T_vec = (300:50:1500)';
    cpProps = HEAThermoEngine.computeCALPHADProperties(cantorElems, cantorX, T_vec, 'FCC_A1');
    assert(numel(cpProps.Cp) == numel(T_vec), 'Cp vector length must match T vector');
    assert(cpProps.Cp(1) > 23.0 && cpProps.Cp(1) < 27.0, sprintf('Room temp Cp ~ 25 J/(mol*K) (got %.2f)', cpProps.Cp(1)));
    assert(all(cpProps.Cp > 20.0 & cpProps.Cp < 55.0), 'All Cp values must remain within physical metallic bounds');
    fprintf('  [PASS] CALPHAD Cp curve verified across 300 - 1500 K (Cp_300K = %.2f J/mol*K)\n', cpProps.Cp(1));
    
    fprintf('\n=================================================================\n');
    fprintf('           ALL CALPHAD ENGINE UNIT TESTS PASSED (6/6)!           \n');
    fprintf('=================================================================\n');
end
