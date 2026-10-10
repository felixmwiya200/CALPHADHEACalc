% Comprehensive test script verifying that LiteratureBenchmark safely retrieves
% all materials and properties from published_materials_data.json without missing-field errors.
function test_literature_safe_fields()
    fprintf('=================================================================\n');
    fprintf('     TESTING LITERATURE BENCHMARK SAFE FIELD RETRIEVAL           \n');
    fprintf('=================================================================\n\n');
    
    lb = LiteratureBenchmark();
    assert(~isempty(lb.Database), 'Database must not be empty');
    
    matKeys = fieldnames(lb.Database);
    fprintf('Loaded database with %d materials.\n\n', numel(matKeys));
    
    totalChecked = 0;
    
    % Test dummy data
    T_test = linspace(300, 2000, 50)';
    Y_test = ones(size(T_test)) * 10.0;
    
    for i = 1:numel(matKeys)
        mKey = matKeys{i};
        matEntry = lb.Database.(mKey);
        if ~isfield(matEntry, 'properties'), continue; end
        
        propKeys = fieldnames(matEntry.properties);
        for j = 1:numel(propKeys)
            pKey = propKeys{j};
            
            % 1. Test getComparison with direct material key
            [hasLit, litRes] = lb.getComparison(mKey, pKey, T_test, Y_test, '', 'at', false);
            
            assert(hasLit, sprintf('Expected hasLit=true for precached %s.%s', mKey, pKey));
            assert(isfield(litRes, 'ScholarQuery') && ~isempty(litRes.ScholarQuery), ...
                sprintf('litRes must have valid ScholarQuery for %s.%s', mKey, pKey));
            assert(isfield(litRes, 'ScienceDirectQuery') && ~isempty(litRes.ScienceDirectQuery), ...
                sprintf('litRes must have valid ScienceDirectQuery for %s.%s', mKey, pKey));
            assert(isfield(litRes, 'CitedByUrl') && ~isempty(litRes.CitedByUrl), ...
                sprintf('litRes must have valid CitedByUrl for %s.%s', mKey, pKey));
            assert(isfield(litRes, 'Indexes') && ~isempty(litRes.Indexes), ...
                sprintf('litRes must have valid Indexes for %s.%s', mKey, pKey));
            assert(isfield(litRes, 'Citation') && ~isempty(litRes.Citation), ...
                sprintf('litRes must have valid Citation for %s.%s', mKey, pKey));
            assert(isfield(litRes, 'Journal') && ~isempty(litRes.Journal), ...
                sprintf('litRes must have valid Journal for %s.%s', mKey, pKey));
            
            totalChecked = totalChecked + 1;
        end
    end
    
    fprintf('Successfully tested all %d material-property pairs with zero errors!\n', totalChecked);
    
    % Test an unprecached custom alloy fallback (dynamic search path)
    fprintf('\nTesting custom unprecached alloy fallback...\n');
    [hasCustom, litCustom] = lb.getComparison('UnknownAlloy.dat', 'thermal_conductivity', T_test, Y_test, 'Fe20Cr20Ni20Co20Cu20', 'at', false);
    assert(hasCustom, 'Custom alloy should return hasCustom=true');
    assert(isfield(litCustom, 'ScholarQuery') && ~isempty(litCustom.ScholarQuery), 'Custom alloy must have ScholarQuery');
    assert(isfield(litCustom, 'ScienceDirectQuery') && ~isempty(litCustom.ScienceDirectQuery), 'Custom alloy must have ScienceDirectQuery');
    assert(isfield(litCustom, 'CitedByUrl') && ~isempty(litCustom.CitedByUrl), 'Custom alloy must have CitedByUrl');
    fprintf('Custom alloy dynamic search path verified!\n');
    
    fprintf('\n=================================================================\n');
    fprintf('        ALL LITERATURE BENCHMARK FIELD TESTS PASSED!             \n');
    fprintf('=================================================================\n');
end
