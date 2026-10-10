% test_optical_properties.m
% Verification test for temperature-dependent absorptivity and emissivity
% covering both Laser Hardening and Laser Remelting modes across JMatPro datasets.

fprintf('=== Testing Optical Properties Engine (Remelting & Hardening) ===\n');

scriptDir = fileparts(mfilename('fullpath'));
addpath(scriptDir);
rootFolder = fileparts(scriptDir);
dataFolder = fullfile(rootFolder, 'materials_data');
if ~exist(dataFolder, 'dir')
    dataFolder = fullfile(pwd, 'materials_data');
end

% 1. Test instantiation
app = MaterialPropertiesApp(dataFolder);
app.UIFigure.Visible = 'off'; % Headless mode for automated verification
fprintf('[PASS] MaterialPropertiesApp initialized successfully.\n');

% 2. Test dataset with explicit JMatPro resistivity: AlNi.dat
fprintf('\n--- Testing AlNi.dat (Direct Resistivity Column) ---\n');
app.CurrentFile = 'AlNi.dat';
app.onFileChange();

% Verify Laser Absorptivity column exists
props = app.CurrentData.Properties.VariableNames;
hasAbs = any(strcmp(props, 'Laser Absorptivity A(T)'));
assert(hasAbs, 'Laser Absorptivity A(T) column should be present in CurrentData');
fprintf('[PASS] Generated "Laser Absorptivity A(T)" column from JMatPro resistivity.\n');

% Test Remelting calculation
app.CurrentProperty = 'Laser Absorptivity A(T)';
app.LaserMode = 'Remelting';
app.LaserWavelength = 1.064;
app.SurfaceRoughFactor = 1.35;
app.onPropChange();

fprintf('Remelting Fit Result:\n');
disp(app.LastEquationLines);
assert(~isempty(app.LastFitT) && ~isempty(app.LastFitY), 'Fit curves should not be empty');
fprintf('[PASS] Laser Remelting calculation completed successfully.\n');

% Test Hardening calculation
fprintf('\n--- Testing Laser Hardening Mode ---\n');
app.LaserMode = 'Hardening';
app.SurfaceCondition = 'Graphite';
app.CoatingAbsorptivity = 0.82;
app.onPropChange();

fprintf('Hardening Fit Result:\n');
disp(app.LastEquationLines);
assert(~isempty(app.LastFitT) && ~isempty(app.LastFitY), 'Hardening fit curves should not be empty');
fprintf('[PASS] Laser Hardening calculation completed successfully.\n');

% 3. Test dataset without resistivity column (AlCo.dat -> Wiedemann-Franz)
fprintf('\n--- Testing AlCo.dat (Wiedemann-Franz Derivation) ---\n');
app.CurrentFile = 'AlCo.dat';
app.onFileChange();

props = app.CurrentData.Properties.VariableNames;
hasAbsWF = any(strcmp(props, 'Laser Absorptivity A(T)'));
assert(hasAbsWF, 'Laser Absorptivity A(T) should be derived via Wiedemann-Franz law');
A_vals = app.CurrentData.('Laser Absorptivity A(T)');
fprintf('Derived Absorptivity range for AlCo: min = %.3f, max = %.3f\n', ...
    min(A_vals), max(A_vals));
assert(all(A_vals > 0.1 & A_vals < 0.95), 'Derived absorptivity values must be physically realistic (10%% - 95%%)');
fprintf('[PASS] Wiedemann-Franz derivation physically valid.\n');

% Test Remelting on AlCo
app.CurrentProperty = 'Laser Absorptivity A(T)';
app.LaserMode = 'Remelting';
app.onPropChange();
fprintf('[PASS] AlCo Absorptivity Remelting succeeded.\n');

% 4. Test Surface Emissivity eps(T) directly
fprintf('\n--- Testing Surface Emissivity eps(T) Selection ---\n');
props = app.CurrentData.Properties.VariableNames;
hasEps = any(strcmp(props, 'Surface Emissivity eps(T)'));
assert(hasEps, 'Surface Emissivity eps(T) column should be present in CurrentData');
fprintf('[PASS] Generated "Surface Emissivity eps(T)" column.\n');

app.CurrentProperty = 'Surface Emissivity eps(T)';
app.LaserMode = 'Hardening';
app.SurfaceCondition = 'Bare';
app.onPropChange();
assert(~isempty(app.LastFitT) && ~isempty(app.LastFitY), 'Emissivity Hardening fit curves must not be empty');
fprintf('Emissivity Hardening primary range: min = %.3f, max = %.3f\n', min(app.LastFitY), max(app.LastFitY));
fprintf('[PASS] Surface Emissivity Hardening calculation succeeded.\n');

app.LaserMode = 'Remelting';
app.onPropChange();
assert(~isempty(app.LastFitT) && ~isempty(app.LastFitY), 'Emissivity Remelting fit curves must not be empty');
fprintf('Emissivity Remelting primary range: min = %.3f, max = %.3f\n', min(app.LastFitY), max(app.LastFitY));
fprintf('[PASS] Surface Emissivity Remelting calculation succeeded.\n');

delete(app);
fprintf('\n=== ALL OPTICAL TESTS (ABSORPTIVITY & EMISSIVITY) PASSED! ===\n');
exit(0);
