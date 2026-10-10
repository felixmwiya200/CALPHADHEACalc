% Test Suite: XRD Controls, Curves, Al1.5 Benchmark, and Export Functionality
function test_xrd_controls_and_export()
    fprintf('=== Running test_xrd_controls_and_export ===\n');

    % 1. Test Al1.5CoCrFeNi Composition
    fprintf('Testing Al1.5CoCrFeNi XRD calculation...\n');
    compAl15 = {'Al', 1.5/5.5*100; 'Co', 1/5.5*100; 'Cr', 1/5.5*100; 'Fe', 1/5.5*100; 'Ni', 1/5.5*100};
    xrdAl15 = HEAXRDEngine.calculateXRD(compAl15, 'at', 'Cu', 45, 0.0035);

    % Verify phases: must be BCC (A2) + B2 Ordered
    assert(numel(xrdAl15.phases) >= 2, 'Al1.5CoCrFeNi should have dual BCC+B2 phases');
    assert(any(strcmp(xrdAl15.phases, 'BCC (A2)')), 'Must include BCC (A2)');
    assert(any(strcmp(xrdAl15.phases, 'B2 Ordered')), 'Must include B2 Ordered');
    assert(abs(xrdAl15.latticeParams.a_BCC - 2.885) < 0.01, 'Lattice parameter a_BCC should be 2.885 A');
    
    % Verify clean radiation formatting
    assert(~contains(xrdAl15.radiation, '\alpha'), 'Radiation string should not contain raw LaTeX \alpha');
    assert(~contains(xrdAl15.radiation, '\AA'), 'Radiation string should not contain raw LaTeX \AA');
    assert(contains(xrdAl15.radiation, 'Cu-Kα'), 'Radiation string should be Cu-Kα');
    fprintf('  ✓ Al1.5CoCrFeNi phases: %s, radiation: %s\n', strjoin(xrdAl15.phases, ', '), xrdAl15.radiation);

    % Verify bottomCurve and topCurve exist
    assert(isfield(xrdAl15, 'bottomCurve'), 'Result must include bottomCurve');
    assert(isfield(xrdAl15, 'topCurve'), 'Result must include topCurve');
    assert(~isempty(xrdAl15.bottomCurve.twoTheta), 'bottomCurve twoTheta must not be empty');
    assert(~isempty(xrdAl15.bottomCurve.intensity), 'bottomCurve intensity must not be empty');
    assert(~isempty(xrdAl15.topCurve.twoTheta), 'topCurve twoTheta must not be empty');
    assert(~isempty(xrdAl15.topCurve.intensity), 'topCurve intensity must not be empty');
    fprintf('  ✓ Al1.5CoCrFeNi bottomCurve ("%s") and topCurve ("%s") successfully generated\n', ...
        xrdAl15.bottomCurve.name, xrdAl15.topCurve.name);

    % Verify benchmark data for Al1.5CoCrFeNi
    assert(xrdAl15.benchmarkExp.hasData == true, 'Al1.5CoCrFeNi must have benchmark experimental data');
    assert(contains(xrdAl15.benchmarkExp.title, 'Al_{1.5}CoCrFeNi') || contains(xrdAl15.benchmarkExp.title, 'Al1.5CoCrFeNi'), ...
        'Benchmark title must reference Al1.5CoCrFeNi');
    fprintf('  ✓ Benchmark data verified: %s\n', xrdAl15.benchmarkExp.title);

    % 2. Test Cantor Alloy CoCrFeMnNi
    fprintf('Testing Cantor alloy XRD calculation...\n');
    compCantor = {'Co', 20; 'Cr', 20; 'Fe', 20; 'Mn', 20; 'Ni', 20};
    xrdCantor = HEAXRDEngine.calculateXRD(compCantor, 'at', 'Cu', 45, 0.0035);
    assert(any(strcmp(xrdCantor.phases, 'FCC (A1)')), 'Cantor must be FCC (A1)');
    assert(xrdCantor.benchmarkExp.hasData == true, 'Cantor must have benchmark data');
    assert(~isempty(xrdCantor.bottomCurve.twoTheta), 'Cantor bottomCurve must not be empty');
    assert(~isempty(xrdCantor.topCurve.twoTheta), 'Cantor topCurve must not be empty');
    fprintf('  ✓ Cantor alloy curves verified\n');

    % 3. Test Co-Ka radiation switching
    fprintf('Testing Co-Ka radiation switching...\n');
    xrdCo = HEAXRDEngine.calculateXRD(compCantor, 'at', 'Co', 45, 0.0035);
    assert(contains(xrdCo.radiation, 'Co-Kα'), 'Radiation string should be Co-Kα');
    assert(~contains(xrdCo.radiation, '\alpha'), 'Radiation string should not contain LaTeX escapes');
    fprintf('  ✓ Co-Ka radiation string verified: %s\n', xrdCo.radiation);

    % 4. Test base64 image decoding logic for exportImage
    fprintf('Testing base64 PNG export decoding logic...\n');
    % Minimal 1x1 transparent PNG base64 string
    samplePngB64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
    dataUrl = ['data:image/png;base64,', samplePngB64];
    idx = strfind(dataUrl, 'base64,');
    assert(~isempty(idx), 'Must find base64 prefix');
    b64Payload = dataUrl(idx+7:end);
    bytes = matlab.net.base64decode(b64Payload);
    assert(~isempty(bytes), 'Decoded bytes must not be empty');
    
    testImgPath = fullfile(pwd, 'test_export_image_tmp.png');
    fid = fopen(testImgPath, 'wb');
    assert(fid ~= -1, 'File handle must be valid');
    fwrite(fid, bytes, 'uint8');
    fclose(fid);
    
    assert(exist(testImgPath, 'file') == 2, 'Exported image file must exist on disk');
    dInfo = dir(testImgPath);
    assert(dInfo.bytes > 0, 'Exported file size must be > 0 bytes');
    delete(testImgPath);
    fprintf('  ✓ Base64 PNG export decode & file write verified (size: %d bytes)\n', dInfo.bytes);

    fprintf('=== ALL XRD CONTROLS AND EXPORT TESTS PASSED SUCCESSFULLY! ===\n');
end
