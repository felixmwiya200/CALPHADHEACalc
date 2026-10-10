% Unit Test: Application Controller XRD Bridge Test
function test_app_xrd_bridge()
    fprintf('=== Testing MaterialPropertiesApp XRD Integration Bridge ===\n');
    
    % Test XRD calculation with cell matrix input
    alComp = {'Al', 20; 'Co', 20; 'Cr', 20; 'Fe', 20; 'Ni', 20};
    xrdRes = HEAXRDEngine.calculateXRD(alComp, 'at', 'Cu', 40, 0.003);
    
    assert(isstruct(xrdRes), 'XRD result must be a struct');
    assert(isfield(xrdRes, 'twoTheta'), 'Must contain twoTheta');
    assert(isfield(xrdRes, 'intensity'), 'Must contain intensity');
    assert(isfield(xrdRes, 'peaks'), 'Must contain peaks');
    assert(isfield(xrdRes, 'phases'), 'Must contain phases');
    assert(~isempty(xrdRes.peaks), 'Peaks array must not be empty');
    
    fprintf('✓ XRD Bridge test PASSED: Synthesized %d data points across 20-100 deg.\n', ...
        numel(xrdRes.twoTheta));
end
