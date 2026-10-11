% test_headless_engine.m - Automated Verification of Headless CALPHAD Solver & Fluent Logging
function test_headless_engine()
    fprintf('=================================================================\n');
    fprintf('   TESTING HEADLESS CALPHAD SOLVER & ANSYS FLUENT LOGGING PROTOCOL\n');
    fprintf('=================================================================\n\n');

    testInputDir = fullfile(pwd, 'test_tmp');
    if ~exist(testInputDir, 'dir')
        mkdir(testInputDir);
    end

    inputFile = fullfile(testInputDir, 'cantor_input.json');
    outputFile = fullfile(testInputDir, 'cantor_output.json');
    transcriptFile = fullfile(testInputDir, 'cantor_fluent.trn');

    % Clean up old files
    if exist(outputFile, 'file'), delete(outputFile); end
    if exist(transcriptFile, 'file'), delete(transcriptFile); end

    % 1. Create Test Input JSON
    inputCfg = struct(...
        'alloyName', 'Cantor Alloy (CoCrFeMnNi)', ...
        'elements', {{'Co', 'Cr', 'Fe', 'Mn', 'Ni'}}, ...
        'fractions', [0.2, 0.2, 0.2, 0.2, 0.2], ...
        'temperatureRange', [1000, 1600], ...
        'temperatureStep', 100, ...
        'grainSize', 20, ...
        'oxidationTemp', 950, ...
        'oxidationHours', 50, ...
        'xrdSource', 'Cu' ...
    );

    jsonStr = jsonencode(inputCfg);
    fid = fopen(inputFile, 'w');
    assert(fid > 0, 'Cannot create test input file.');
    fwrite(fid, jsonStr, 'char');
    fclose(fid);
    fprintf('--- Test 1: Created Test Input JSON ---\n  File: %s\n', inputFile);

    % 2. Execute Headless Solver
    fprintf('\n--- Test 2: Executing Headless Solver with ANSYS Fluent Logging ---\n');
    t0 = tic;
    res = CALPHADHeadlessSolver(inputFile, outputFile, transcriptFile);
    elapsed = toc(t0);
    fprintf('  Headless solver completed in %.2f seconds!\n', elapsed);

    % 3. Verify Output JSON File
    fprintf('\n--- Test 3: Verifying Structured JSON Output ---\n');
    assert(exist(outputFile, 'file') == 2, 'Output JSON file was not generated.');
    outRaw = fileread(outputFile);
    outData = jsondecode(outRaw);

    assert(outData.Success == true, 'Solver result Success must be true.');
    assert(isfield(outData, 'Thermodynamics'), 'Must contain Thermodynamics field.');
    assert(isfield(outData, 'Mechanical'), 'Must contain Mechanical field.');
    assert(isfield(outData, 'Oxidation'), 'Must contain Oxidation field.');
    assert(isfield(outData, 'Corrosion'), 'Must contain Corrosion field.');
    assert(isfield(outData, 'XRD'), 'Must contain XRD field.');
    assert(isfield(outData, 'Applications'), 'Must contain Applications field.');
    assert(isfield(outData, 'Telemetry'), 'Must contain Telemetry field.');

    fprintf('  Solidus Ts: %.1f K | Liquidus Tl: %.1f K\n', ...
        outData.Thermodynamics.T_Solidus, outData.Thermodynamics.T_Liquidus);
    fprintf('  Yield Strength: %.1f MPa | Hardness: %d HV\n', ...
        outData.Mechanical.YieldStrength_RT_MPa, outData.Mechanical.VickersHardness_HV);
    fprintf('  PREN: %.1f | Corrosion Rate: %.5f mm/yr\n', ...
        outData.Corrosion.PREN_HEA, outData.Corrosion.CR_mm_yr_NaCl);
    fprintf('  Telemetry Points: %d iterations recorded.\n', numel(outData.Telemetry));
    assert(numel(outData.Telemetry) > 0, 'Must record solver telemetry iterations.');

    % 4. Verify ANSYS Fluent Transcript (.trn) File
    fprintf('\n--- Test 4: Verifying ANSYS Fluent Transcript (.trn) File ---\n');
    assert(exist(transcriptFile, 'file') == 2, 'Fluent transcript .trn file was not created.');
    trnLines = regexp(fileread(transcriptFile), '\r?\n', 'split');
    fprintf('  Transcript contains %d lines.\n', numel(trnLines));

    % Check for Fluent table headers and columns
    hasHeader = any(contains(trnLines, 'Step   T (K)   Iter    Mass-Res'));
    assert(hasHeader, 'Transcript must contain the ANSYS Fluent columnar header.');

    hasConverged = any(contains(trnLines, '------- equilibrium converged at T ='));
    assert(hasConverged, 'Transcript must contain equilibrium convergence notices.');

    hasSummary = any(contains(trnLines, 'STEPPING SWEEP SUMMARY:'));
    assert(hasSummary, 'Transcript must contain the final stepping sweep summary banner.');

    fprintf('  ANSYS Fluent columnar formatting and headers verified successfully!\n');

    % Clean up test directory
    try
        rmdir(testInputDir, 's');
    catch
    end

    fprintf('\n=================================================================\n');
    fprintf('  ALL HEADLESS SOLVER & FLUENT LOGGING TESTS PASSED (100%%)!\n');
    fprintf('=================================================================\n');
end
