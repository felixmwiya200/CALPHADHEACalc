% Unit Test: HEA Thermodynamic Model Calibration & Validation
% Verifies that solidus/liquidus temperatures match authoritative peer-reviewed
% literature benchmarks (Zhang et al. JOM 2012, Cantor MSEA 2004, Senkov MSEA 2011)
function test_hea_thermo_calibration()
    fprintf('=== Testing HEA Thermodynamic Model Calibration ===\n');
    
    % Test 1: Equiatomic AlCoCrFeNi (The user-reported bug case)
    % Literature: Ts ~ 1593-1620 K (1320-1347 C), Tl ~ 1653-1680 K (1380-1407 C)
    % Previously buggy output was Ts = 1124 K, Tl = 1199 K due to unphysical DeltaHmix subtraction
    elems_al = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    x_al = [0.2, 0.2, 0.2, 0.2, 0.2];
    m_al = HEAThermoEngine.computeThermodynamics(elems_al, x_al);
    
    fprintf('AlCoCrFeNi: VEC = %.2f, Phase = %s, Ts = %.1f K, Tl = %.1f K (Tm_avg = %.1f K)\n', ...
        m_al.VEC, m_al.Phase, m_al.T_Solidus, m_al.T_Liquidus, m_al.Tm_avg);
    
    assert(m_al.T_Solidus >= 1550 && m_al.T_Solidus <= 1640, ...
        sprintf('AlCoCrFeNi Ts must be ~1593-1620 K, but got %.1f K', m_al.T_Solidus));
    assert(m_al.T_Liquidus >= 1630 && m_al.T_Liquidus <= 1700, ...
        sprintf('AlCoCrFeNi Tl must be ~1653-1680 K, but got %.1f K', m_al.T_Liquidus));
    assert(m_al.T_Liquidus > m_al.T_Solidus, 'Liquidus must exceed solidus');
    assert(contains(m_al.Phase, 'BCC'), 'AlCoCrFeNi equiatomic must predict BCC/B2 phase');
    fprintf('✓ Equiatomic AlCoCrFeNi melting range verified: [%.0f - %.0f K] matches DSC literature!\n', ...
        m_al.T_Solidus, m_al.T_Liquidus);
    
    % Test 2: Cantor Alloy CoCrFeMnNi
    % Literature: Ts ~ 1553 K (1280 C), Tl ~ 1613 K (1340 C)
    elems_cantor = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
    x_cantor = [0.2, 0.2, 0.2, 0.2, 0.2];
    m_cantor = HEAThermoEngine.computeThermodynamics(elems_cantor, x_cantor);
    
    fprintf('CoCrFeMnNi: VEC = %.2f, Phase = %s, Ts = %.1f K, Tl = %.1f K\n', ...
        m_cantor.VEC, m_cantor.Phase, m_cantor.T_Solidus, m_cantor.T_Liquidus);
    
    assert(m_cantor.T_Solidus >= 1520 && m_cantor.T_Solidus <= 1585, ...
        sprintf('Cantor Ts must be ~1553 K, but got %.1f K', m_cantor.T_Solidus));
    assert(m_cantor.T_Liquidus >= 1590 && m_cantor.T_Liquidus <= 1640, ...
        sprintf('Cantor Tl must be ~1613 K, but got %.1f K', m_cantor.T_Liquidus));
    assert(contains(m_cantor.Phase, 'FCC'), 'Cantor alloy must be FCC');
    fprintf('✓ Cantor alloy CoCrFeMnNi melting range verified: [%.0f - %.0f K] matches DSC literature!\n', ...
        m_cantor.T_Solidus, m_cantor.T_Liquidus);
    
    % Test 3: Al0.3CoCrFeNi (FCC single phase)
    % Literature: Ts ~ 1653 K (1380 C), Tl ~ 1698 K (1425 C)
    % Stoichiometry: Al0.3 = 0.3 / 4.3 = 0.06977; others = 1.0 / 4.3 = 0.23256
    elems_al03 = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    x_al03 = [0.3/4.3, 1.0/4.3, 1.0/4.3, 1.0/4.3, 1.0/4.3];
    m_al03 = HEAThermoEngine.computeThermodynamics(elems_al03, x_al03);
    
    fprintf('Al0.3CoCrFeNi: VEC = %.2f, Phase = %s, Ts = %.1f K, Tl = %.1f K\n', ...
        m_al03.VEC, m_al03.Phase, m_al03.T_Solidus, m_al03.T_Liquidus);
    assert(m_al03.T_Solidus >= 1620 && m_al03.T_Solidus <= 1680, 'Al0.3 Ts calibration check');
    assert(contains(m_al03.Phase, 'FCC'), 'Al0.3CoCrFeNi must be FCC');
    fprintf('✓ Al0.3CoCrFeNi melting range and FCC phase verified\n');
    
    % Test 4: Eutectic HEA AlCoCrFeNi2.1
    % Literature: Ts ~ 1588 K, Tl ~ 1618 K (narrow eutectic freezing window ~30 K)
    elems_eut = {'Al', 'Co', 'Cr', 'Fe', 'Ni'};
    x_eut = [1.0/6.1, 1.0/6.1, 1.0/6.1, 1.0/6.1, 2.1/6.1];
    m_eut = HEAThermoEngine.computeThermodynamics(elems_eut, x_eut);
    
    fprintf('AlCoCrFeNi2.1: Phase = %s, Ts = %.1f K, Tl = %.1f K, Freezing Window = %.1f K\n', ...
        m_eut.Phase, m_eut.T_Solidus, m_eut.T_Liquidus, m_eut.T_Liquidus - m_eut.T_Solidus);
    assert(m_eut.T_Solidus >= 1560 && m_eut.T_Solidus <= 1610, 'Eutectic Ts check');
    assert((m_eut.T_Liquidus - m_eut.T_Solidus) <= 50, 'Eutectic freezing window should be narrow (<= 50 K)');
    fprintf('✓ AlCoCrFeNi2.1 near-eutectic window verified\n');
    
    % Test 5: Refractory HEA NbMoTaW
    % Literature: Ts ~ 2800 K, Tl ~ 3100 K
    elems_rheo = {'Nb', 'Mo', 'Ta', 'W'};
    x_rheo = [0.25, 0.25, 0.25, 0.25];
    m_rheo = HEAThermoEngine.computeThermodynamics(elems_rheo, x_rheo);
    
    fprintf('NbMoTaW: Phase = %s, Ts = %.1f K, Tl = %.1f K\n', ...
        m_rheo.Phase, m_rheo.T_Solidus, m_rheo.T_Liquidus);
    assert(m_rheo.T_Solidus >= 2700 && m_rheo.T_Solidus <= 2950, 'Refractory Ts check');
    assert(m_rheo.T_Liquidus >= 2950 && m_rheo.T_Liquidus <= 3250, 'Refractory Tl check');
    assert(contains(m_rheo.Phase, 'BCC'), 'NbMoTaW must be BCC');
    fprintf('✓ Refractory NbMoTaW melting range verified\n');
    
    fprintf('=== All HEA Thermodynamic Calibration Tests PASSED! ===\n');
end
