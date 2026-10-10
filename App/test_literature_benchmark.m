% Test script for expanded LiteratureBenchmark with HEA datasets
function test_literature_benchmark()
    fprintf('=== Testing LiteratureBenchmark HEA Database ===\n');
    lb = LiteratureBenchmark();
    
    % Test 1: Lookup Cantor alloy (CoCrFeMnNi)
    resCantor = lb.lookupMaterial('CoCrFeMnNi');
    assert(~isempty(resCantor), 'Cantor alloy should be found in benchmark database');
    fprintf('✓ Cantor alloy found: %s\n', resCantor.displayName);
    assert(isfield(resCantor.properties, 'density'), 'Cantor should have density property');
    assert(isfield(resCantor.properties, 'thermal_conductivity'), 'Cantor should have thermal_conductivity property');
    assert(isfield(resCantor.properties, 'specific_heat'), 'Cantor should have specific_heat property');
    
    % Test 2: Lookup Refractory HEA TiZrHfNbTa
    resRHEA = lb.lookupMaterial('TiZrHfNbTa');
    assert(~isempty(resRHEA), 'TiZrHfNbTa should be found in benchmark database');
    fprintf('✓ Refractory HEA TiZrHfNbTa found: %s\n', resRHEA.displayName);
    
    % Test 3: Lookup Ultra-refractory HEA NbMoTaW
    resNbMoTaW = lb.lookupMaterial('NbMoTaW');
    assert(~isempty(resNbMoTaW), 'NbMoTaW should be found in benchmark database');
    fprintf('✓ Ultra-refractory HEA NbMoTaW found: %s\n', resNbMoTaW.displayName);
    
    % Test 4: Lookup Eutectic HEA AlCoCrFeNi2.1
    resEHEA = lb.lookupMaterial('AlCoCrFeNi2.1');
    assert(~isempty(resEHEA), 'AlCoCrFeNi2.1 should be found in benchmark database');
    fprintf('✓ Eutectic HEA AlCoCrFeNi2.1 found: %s\n', resEHEA.displayName);
    
    % Test 5: Verify DOI and citations exist
    assert(~isempty(resCantor.properties.density.doi), 'Cantor density must have DOI');
    fprintf('✓ Verified DOI for Cantor density: %s\n', resCantor.properties.density.doi);
    
    fprintf('=== All LiteratureBenchmark tests PASSED! ===\n');
end
