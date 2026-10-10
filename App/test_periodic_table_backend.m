% test_periodic_table_backend.m
% Verification script for periodic table dynamic matrix selection & HEA modeling

fprintf('\n=== Testing HEACalculator with Periodic Table Elements ===\n');

% 1. Test Refractory High-Entropy Alloy: Nb-Mo-Ta-W-V
compRHEA = {
    'Nb', 20.0;
    'Mo', 20.0;
    'Ta', 20.0;
    'W',  20.0;
    'V',  20.0
};

testFolder = fullfile(pwd, 'test_materials_temp');
if ~exist(testFolder, 'dir'), mkdir(testFolder); end

[filePathRHEA, phaseRHEA, vecRHEA] = HEACalculator.generateDatFile(compRHEA, testFolder);
fprintf('Refractory HEA generated at: %s\n', filePathRHEA);
fprintf('  VEC: %.2f | Phase: %s\n', vecRHEA, phaseRHEA);
assert(exist(filePathRHEA, 'file') == 2, 'RHEA dat file was not generated');
assert(vecRHEA < 6.87, 'Refractory HEA should predict BCC structure');

% 2. Test Cantor alloy with Titanium addition: Co-Cr-Fe-Mn-Ni-Ti
compCantorTi = {
    'Co', 18.0;
    'Cr', 18.0;
    'Fe', 18.0;
    'Mn', 18.0;
    'Ni', 18.0;
    'Ti', 10.0
};
[filePathCantor, phaseCantor, vecCantor] = HEACalculator.generateDatFile(compCantorTi, testFolder);
fprintf('Cantor+Ti generated at: %s\n', filePathCantor);
fprintf('  VEC: %.2f | Phase: %s\n', vecCantor, phaseCantor);
assert(exist(filePathCantor, 'file') == 2, 'Cantor+Ti dat file was not generated');

% 3. Test MaterialPropertiesApp dynamic matrix handling
fprintf('\n=== Testing MaterialPropertiesApp Dynamic Matrix Integration ===\n');
app = MaterialPropertiesApp(testFolder);
app.UIFigure.Visible = 'off';

% Verify initial state
fprintf('Initial element count: %d\n', numel(app.ElementList));
assert(numel(app.ElementList) == 5, 'Default element count should be 5 (Cantor base)');

% Simulate 'setCompositionElements' event from Periodic Table (e.g. user selected 4 refractory elements)
customElems = {'Ti', 'Zr', 'Nb', 'Ta'};
customVals  = [25.0, 25.0, 25.0, 25.0];
eventData = struct('HTMLEventName', 'setCompositionElements', ...
                   'HTMLEventData', struct('elements', {customElems}, 'values', customVals));
app.handleHTMLEvent(eventData);

fprintf('Updated ElementList: %s\n', strjoin(app.ElementList, ', '));
fprintf('Composition string: %s\n', app.CurrentCompositionStr);
assert(numel(app.ElementList) == 4, 'ElementList should contain 4 elements');
assert(strcmp(app.ElementList{1}, 'Ti'), 'First element should be Ti');

% Test 'matrixEdit'
editData = struct('HTMLEventName', 'matrixEdit', ...
                  'HTMLEventData', struct('element', 'Ti', 'value', 30.0));
app.handleHTMLEvent(editData);
assert(strcmp(app.MatrixData{1, 2}, '30.0'), 'Ti value should be updated to 30.0');

% Test 'matrixBalance'
balData = struct('HTMLEventName', 'matrixBalance', 'HTMLEventData', struct());
app.handleHTMLEvent(balData);
fprintf('Balanced composition string: %s\n', app.CurrentCompositionStr);

% Test 'matrixPreset'
presetData = struct('HTMLEventName', 'matrixPreset', ...
                    'HTMLEventData', struct('preset', 'SS316L : 316L stainless steel'));
app.handleHTMLEvent(presetData);
fprintf('Preset applied ElementList: %s\n', strjoin(app.ElementList, ', '));
fprintf('Preset composition string: %s\n', app.CurrentCompositionStr);
assert(any(strcmp(app.ElementList, 'Mo')), 'SS316L should include Mo');

delete(app.UIFigure);
if exist(testFolder, 'dir')
    try, rmdir(testFolder, 's'); catch; end
end

fprintf('\n>>> ALL PERIODIC TABLE TESTS PASSED SUCCESSFULLY! <<<\n');
