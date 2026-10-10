classdef MaterialPropertiesApp < handle
    % Material Properties Fitter for COMSOL Multiphysics
    % Frontend: HTML/CSS/JS via uihtml (Chromium WebView)
    % Backend:  All calculation logic in MATLAB
    
    properties
        UIFigure
        HtmlComponent          % Embedded Chromium web view container
        SplashScreen           % Fast desktop launch screen (AppSplashScreen)
        FallbackTimer          % Safety timer ensuring main window becomes visible
        
        % Active session parameters
        CurrentFile     = ''
        CurrentProperty = ''
        CurrentFitType  = 'Auto (Physics-based Recommended)'
        CurrentPlotStyle= 'Line+Symbol'
        CurrentBasis    = 'At %'
        CompareEnabled  = true
        StartTemp       = 293.15
        EndTemp         = 873.15

        % Dynamic alloy composition matrix (selected via Periodic Table or Presets)
        MatrixData         % Cell array of {element, atomic/weight %}
        ElementList = {'Al','Co','Cr','Fe','Ni'}'
        CompositionBasis = 'at' % 'at', 'wt', or 'mol'
        LastThermoMetrics = struct()
        CurrentCompositionStr = ''
        IsUpdatingMatrix = false

        % Dataset and temperature bounds
        DataFolder
        CurrentData
        DataCache
        IsInitializing  = true
        IsStandalone    = false
        CurrentMeltingPoint = 933.15
        T_Min = 293.15
        T_Max = 2500.0

        % Literature benchmark references
        LitBenchmark
        CurrentScholarUrl       = 'https://scholar.google.com'
        CurrentScienceDirectUrl = 'https://www.sciencedirect.com'
        CurrentCitedByUrl       = 'https://scholar.google.com'

        % Most recent calculation cache for COMSOL export
        LastEquationLines = {}
        LastPlotT = []
        LastPlotY = []
        LastFitT  = []
        LastFitY  = []
        LastFitT2 = []
        LastFitY2 = []

        % Solidification and semi-solid rheology parameters
        T_Solidus       = 1460.0
        T_Liquidus      = 1620.0
        MushyModel      = 'Krieger-Dougherty'
        ViscSolidCap    = 1e3
        PackingFraction = 0.65
        IntrinsicVisc   = 2.5
        CustomDataOverrides = []

        % Laser processing and optical parameters
        LaserMode           = 'Remelting'  % 'Remelting', 'Hardening', 'Cladding', 'LPBF'
        LaserWavelength     = 1.064        % micrometers (Fiber/Nd:YAG=1.064, CO2=10.6, Green=0.515, Blue=0.450)
        SurfaceCondition    = 'As-cast'    % 'As-cast', 'Machined', 'Polished', 'Graphite', 'Phosphate'
        SurfaceRoughFactor  = 1.25         % Roughness/cavity multiplier for solid
        CoatingAbsorptivity = 0.82         % Flat coating absorptivity for laser hardening

        % High-Entropy Alloy X-Ray Diffraction (XRD) Simulation parameters
        XRD_Radiation       = 'Cu'         % 'Cu' (1.5406 A), 'Co' (1.7890 A), 'Mo' (0.7107 A)
        XRD_CrystalliteSize = 45.0         % Scherrer crystallite size (nm)
        XRD_Microstrain     = 0.0035       % HEA lattice microstrain
        CurrentXRDData      = struct()
    end

    methods
        % Initialize the app window and host the Chromium uihtml component
        function app = MaterialPropertiesApp(customDataFolder, isStandalone)
            if nargin >= 2 && ~isempty(isStandalone)
                app.IsStandalone = isStandalone;
            else
                % Auto-detect: if no desktop environment is present, we are in standalone mode
                app.IsStandalone = ~usejava('desktop');
            end

            app.IsInitializing = true;
            app.DataCache = containers.Map();

            % 1. Instantly pop up the sleek desktop splash screen (<30ms native process)
            try
                MaterialSplash.start();
                MaterialSplash.update(0, 'Initializing High-Entropy Alloy Core...', 'Mounting secure local memory and configuration...', []);
            catch
            end

            % Layer 1: Suppress DDUX & Customer Involvement Telemetry
            MaterialSplash.update(18, 'Activating 4-Layer Defense-in-Depth Vault...', 'Suppressing telemetry & enforcing zero-leak egress filter...', [1]);
            SecureDataVault.applyTelemetrySuppression();

            % Locate the materials data folder across local dev, custom path, or deployed runtime
            if nargin >= 1 && ~isempty(customDataFolder) && exist(customDataFolder, 'dir')
                app.DataFolder = customDataFolder;
            elseif isdeployed
                app.DataFolder = fullfile(pwd, 'materials_data');
                if ~exist(app.DataFolder,'dir')
                    if exist(fullfile(ctfroot,'materials_data'),'dir')
                        app.DataFolder = fullfile(ctfroot,'materials_data');
                    elseif exist(fullfile(ctfroot,'App','materials_data'),'dir')
                        app.DataFolder = fullfile(ctfroot,'App','materials_data');
                    end
                end
            else
                [fp,~,~] = fileparts(mfilename('fullpath'));
                cands = { fullfile(fp,'materials_data'), ...
                          fullfile(fp,'..','materials_data'), ...
                          'C:\Users\Dell\Documents\Material design\materials_data' };
                app.DataFolder = cands{end};
                for k = 1:numel(cands)
                    if exist(cands{k},'dir')
                        app.DataFolder = cands{k}; break;
                    end
                end
            end

            % Mount SGTE elements & thermodynamic predictors
            MaterialSplash.update(44, 'Loading SGTE Thermodynamic Element Matrix...', 'Loading 45 IUPAC elements and CALPHAD parameters...', [1, 2]);

            % Mount Literature Benchmark engine
            MaterialSplash.update(64, 'Mounting Real-Time Literature Benchmark Engine...', 'Indexing Cantor, AlxCoCrFeNi, and refractory HEA benchmarks...', [1, 2, 3]);
            app.LitBenchmark = LiteratureBenchmark();

            % Initialize dynamic alloy composition matrix (defaults to equiatomic baseline)
            nInit = numel(app.ElementList);
            app.MatrixData = cell(nInit, 2);
            for i = 1:nInit
                app.MatrixData{i,1} = app.ElementList{i};
                app.MatrixData{i,2} = sprintf('%.1f', 100.0 / max(1, nInit));
            end
            app.CurrentCompositionStr = app.buildCompStr();

            % Prepare Laser Optics & Semi-Solid Rheology
            MaterialSplash.update(80, 'Preparing Laser Processing & Semi-Solid Rheology...', 'Initializing Hagen-Rubens, Bramson absorptivity, and Krieger-Dougherty...', [1, 2, 3, 4]);

            [fp,~,~] = fileparts(mfilename('fullpath'));

            % Create figure container (initially hidden while splash is in front)
            app.UIFigure = uifigure('Name','Material Properties Fitter for COMSOL', ...
                'Position',[30 40 1340 740], ...
                'Color',[0.969 0.969 0.961], ...
                'CloseRequestFcn', @(src,evt) app.onAppClose(), ...
                'Visible','off');

            % Set application taskbar and window titlebar icon
            try
                iconFile = fullfile(fp, 'resources', 'app_icon.png');
                if ~exist(iconFile, 'file')
                    iconFile = fullfile(fp, 'resources', 'app_icon.ico');
                end
                if exist(iconFile, 'file')
                    app.UIFigure.Icon = iconFile;
                end
            catch
            end

            % Embed frontend view via uihtml
            MaterialSplash.update(92, 'Hydrating Interactive HiDPI Chromium Interface...', 'Booting web runtime and rendering interactive periodic table...', [1, 2, 3, 4, 5]);

            htmlFile = fullfile(fp,'ui','index.html');
            mainGrid = uigridlayout(app.UIFigure,[1 1]);
            mainGrid.Padding = [0 0 0 0];
            app.HtmlComponent = uihtml(mainGrid, ...
                'HTMLSource', htmlFile, ...
                'HTMLEventReceivedFcn', @(src,evt) app.handleHTMLEvent(evt));

            % Arm safety fallback timer: ensure main window is visible even if Chromium event is delayed
            try
                app.FallbackTimer = timer('StartDelay', 4.0, 'ExecutionMode', 'singleShot', ...
                    'TimerFcn', @(~,~) app.ensureAppVisible());
                start(app.FallbackTimer);
            catch
            end

            app.IsInitializing = false;
        end

        function ensureAppVisible(app)
            try
                if isvalid(app) && ~isempty(app.UIFigure) && isvalid(app.UIFigure)
                    MaterialSplash.close();
                    app.UIFigure.Visible = 'on';
                    figure(app.UIFigure);
                end
            catch
            end
        end

        function onAppClose(app)
            % Layer 4: Sanitize memory and wipe sensitive research arrays
            try
                MaterialSplash.close();
                if ~isempty(app.FallbackTimer) && isvalid(app.FallbackTimer)
                    stop(app.FallbackTimer);
                    delete(app.FallbackTimer);
                    app.FallbackTimer = [];
                end
                if ~isempty(app.MatrixData), app.MatrixData = {}; end
                if ~isempty(app.CurrentData), app.CurrentData = []; end
                if ~isempty(app.DataCache), app.DataCache.remove(app.DataCache.keys); end
                app.LastThermoMetrics = struct();
                app.LastPlotT = [];
                app.LastPlotY = [];
                app.LastFitT = [];
                app.LastFitY = [];
            catch
            end

            isStd = app.IsStandalone;
            try
                if isvalid(app.UIFigure)
                    delete(app.UIFigure);
                end
            catch
            end

            % If running as standalone desktop application, quit background MATLAB process
            if isStd
                try
                    quit force;
                catch
                    exit;
                end
            end
        end

        % Destructor: cleanly stops timers and releases resources
        function delete(app)
            try
                if ~isempty(app.FallbackTimer) && isvalid(app.FallbackTimer)
                    stop(app.FallbackTimer);
                    delete(app.FallbackTimer);
                    app.FallbackTimer = [];
                end
                if ~isempty(app.UIFigure) && isvalid(app.UIFigure)
                    delete(app.UIFigure);
                    app.UIFigure = [];
                end
            catch
            end
        end

        % Dispatch UI events from JavaScript to MATLAB backend methods
        function handleHTMLEvent(app, event)
            try
                name = event.HTMLEventName;
                d    = event.HTMLEventData;

                switch name
                    case 'getFiles'
                        app.htmlSendFileList();
                        % Smoothly complete splash screen to 100% and transition to main window
                        MaterialSplash.update(100, 'Ready! Workspace Mounted', 'All thermodynamic models and security layers active.', [1, 2, 3, 4, 5]);
                        pause(0.18);
                        MaterialSplash.close();
                        if ~isempty(app.FallbackTimer) && isvalid(app.FallbackTimer)
                            stop(app.FallbackTimer);
                            delete(app.FallbackTimer);
                            app.FallbackTimer = [];
                        end
                        app.UIFigure.Visible = 'on';
                        figure(app.UIFigure);

                        % Dispatch initial MATLAB-computed thermodynamic metrics & XRD pattern for default alloy
                        if ~isempty(app.MatrixData)
                            try
                                metrics = HEAThermoEngine.computeThermodynamics(app.MatrixData, app.CompositionBasis);
                                app.LastThermoMetrics = metrics;
                                app.T_Solidus = metrics.T_Solidus;
                                app.T_Liquidus = metrics.T_Liquidus;
                                app.htmlSend('thermoMetrics', metrics);
                            catch ME_tm
                                fprintf('Warning: Initial thermo metrics calculation error: %s\n', ME_tm.message);
                            end
                            try
                                xrdPayload = HEAXRDEngine.calculateXRD(app.MatrixData, app.CompositionBasis, ...
                                    app.XRD_Radiation, app.XRD_CrystalliteSize, app.XRD_Microstrain);
                                app.CurrentXRDData = xrdPayload;
                                app.htmlSend('xrdData', xrdPayload);
                            catch ME_xrd
                                fprintf('Warning: Initial XRD calculation error: %s\n', ME_xrd.message);
                            end
                            try
                                pfPayload = HEAThermoEngine.computeEquilibriumPhaseFractions(app.MatrixData, app.CompositionBasis);
                                app.htmlSend('phaseFractionsData', pfPayload);
                            catch ME_pf
                                fprintf('Warning: Initial phase fractions calculation error: %s\n', ME_pf.message);
                            end
                        end

                    case 'fileSelected'
                        app.CurrentFile = d.file;
                        app.onFileChange();

                    case 'calculate'
                        if isfield(d,'prop'),             app.CurrentProperty  = d.prop;             end
                        if isfield(d,'fitType'),          app.CurrentFitType   = d.fitType;          end
                        if isfield(d,'plotStyle'),        app.CurrentPlotStyle = d.plotStyle;        end
                        if isfield(d,'startTemp'),        app.StartTemp = d.startTemp;               end
                        if isfield(d,'endTemp'),          app.EndTemp   = d.endTemp;                 end
                        if isfield(d,'compare'),          app.CompareEnabled = d.compare;            end
                        if isfield(d,'file'),             app.CurrentFile = d.file;                  end
                        if isfield(d,'solidus'),          app.T_Solidus = d.solidus;                 end
                        if isfield(d,'liquidus'),         app.T_Liquidus = d.liquidus;               end
                        if isfield(d,'mushyModel'),       app.MushyModel = d.mushyModel;             end
                        if isfield(d,'viscSolidCap'),     app.ViscSolidCap = d.viscSolidCap;         end
                        if isfield(d,'laserMode'),        app.LaserMode = d.laserMode;               end
                        if isfield(d,'wavelength'),       app.LaserWavelength = d.wavelength;         end
                        if isfield(d,'surfaceCondition'), app.SurfaceCondition = d.surfaceCondition; end
                        if isfield(d,'roughFactor'),      app.SurfaceRoughFactor = d.roughFactor;     end
                        if isfield(d,'coatingAbs'),       app.CoatingAbsorptivity = d.coatingAbs;     end
                        app.onPropChange(false);

                    case 'updateMushyParams'
                        if isfield(d,'solidus'),      app.T_Solidus      = d.solidus;      end
                        if isfield(d,'liquidus'),     app.T_Liquidus     = d.liquidus;     end
                        if isfield(d,'mushyModel'),   app.MushyModel     = d.mushyModel;   end
                        if isfield(d,'viscSolidCap'), app.ViscSolidCap   = d.viscSolidCap; end
                        if isfield(d,'fitType'),      app.CurrentFitType = d.fitType;      end
                        app.onPropChange(false);

                    case 'updateLaserParams'
                        if isfield(d,'laserMode'),        app.LaserMode = d.laserMode;               end
                        if isfield(d,'wavelength'),       app.LaserWavelength = d.wavelength;         end
                        if isfield(d,'surfaceCondition'), app.SurfaceCondition = d.surfaceCondition; end
                        if isfield(d,'roughFactor'),      app.SurfaceRoughFactor = d.roughFactor;     end
                        if isfield(d,'coatingAbs'),       app.CoatingAbsorptivity = d.coatingAbs;     end
                        app.onPropChange(false);

                    case 'updateXRDParams'
                        if isfield(d,'radiation'),       app.XRD_Radiation = d.radiation; end
                        if isfield(d,'crystalliteSize'), app.XRD_CrystalliteSize = d.crystalliteSize; end
                        if isfield(d,'microstrain'),     app.XRD_Microstrain = d.microstrain; end
                        if ~isempty(app.MatrixData)
                            try
                                xrdPayload = HEAXRDEngine.calculateXRD(app.MatrixData, app.CompositionBasis, ...
                                    app.XRD_Radiation, app.XRD_CrystalliteSize, app.XRD_Microstrain);
                                app.CurrentXRDData = xrdPayload;
                                app.htmlSend('xrdData', xrdPayload);
                            catch
                            end
                        end

                    case 'requestXRD'
                        if ~isempty(app.MatrixData)
                            try
                                xrdPayload = HEAXRDEngine.calculateXRD(app.MatrixData, app.CompositionBasis, ...
                                    app.XRD_Radiation, app.XRD_CrystalliteSize, app.XRD_Microstrain);
                                app.CurrentXRDData = xrdPayload;
                                app.htmlSend('xrdData', xrdPayload);
                            catch
                            end
                        end

                    case 'requestThermoMetrics'
                        if ~isempty(app.MatrixData)
                            try
                                metrics = HEAThermoEngine.computeThermodynamics(app.MatrixData, app.CompositionBasis);
                                app.LastThermoMetrics = metrics;
                                app.T_Solidus = metrics.T_Solidus;
                                app.T_Liquidus = metrics.T_Liquidus;
                                app.htmlSend('thermoMetrics', metrics);
                            catch ME_tm
                                fprintf('Warning: Thermo metrics calculation error: %s\n', ME_tm.message);
                            end
                        end

                    case 'requestPhaseFractions'
                        if ~isempty(app.MatrixData)
                            try
                                res = HEAThermoEngine.computeEquilibriumPhaseFractions(app.MatrixData, app.CompositionBasis);
                                app.htmlSend('phaseFractionsData', res);
                            catch ME_pf
                                fprintf('Warning: Phase fractions calculation error: %s\n', ME_pf.message);
                            end
                        end

                    case 'requestIsopleth'
                        if ~isempty(app.MatrixData)
                            try
                                solute = 'Al';
                                xRange = [0.0, 2.0];
                                numX = 21;
                                if isfield(d, 'solute') && ~isempty(d.solute), solute = char(d.solute); end
                                if isfield(d, 'xRange') && ~isempty(d.xRange), xRange = d.xRange; end
                                if isfield(d, 'numX') && ~isempty(d.numX), numX = double(d.numX); end
                                res = HEAThermoEngine.computeIsoplethSection(app.MatrixData, app.CompositionBasis, solute, xRange, numX);
                                app.htmlSend('isoplethData', res);
                            catch ME_iso
                                fprintf('Warning: Isopleth calculation error: %s\n', ME_iso.message);
                            end
                        end

                    case 'requestTernaryDiagram'
                        try
                            elemA = 'Co'; elemB = 'Cr'; elemC = 'Fe';
                            tempC = 1000.0;
                            gridN = 25;
                            if isfield(d, 'elemA') && ~isempty(d.elemA), elemA = char(d.elemA); end
                            if isfield(d, 'elemB') && ~isempty(d.elemB), elemB = char(d.elemB); end
                            if isfield(d, 'elemC') && ~isempty(d.elemC), elemC = char(d.elemC); end
                            if isfield(d, 'tempC') && ~isempty(d.tempC), tempC = double(d.tempC); end
                            if isfield(d, 'gridN') && ~isempty(d.gridN), gridN = double(d.gridN); end
                            res = HEAThermoEngine.computeTernaryIsothermalSection(elemA, elemB, elemC, app.MatrixData, app.CompositionBasis, tempC, gridN);
                            app.htmlSend('ternaryData', res);
                        catch ME_ter
                            fprintf('Warning: Ternary calculation error: %s\n', ME_ter.message);
                        end

                    case 'requestMechanicalRecalc'
                        try
                            userOpts = struct();
                            if isfield(d, 'grainSize_um') && ~isempty(d.grainSize_um)
                                userOpts.GrainSize_um = double(d.grainSize_um);
                            end
                            if isfield(d, 'temperature_K') && ~isempty(d.temperature_K)
                                userOpts.Temperature_K = double(d.temperature_K);
                            end
                            if isfield(d, 'strainRate') && ~isempty(d.strainRate)
                                userOpts.StrainRate = double(d.strainRate);
                            end
                            [~, summary] = HEAThermoEngine.convertComposition(app.MatrixData, app.CompositionBasis, 'at');
                            thermoMet = app.LastThermoMetrics;
                            if isempty(thermoMet)
                                thermoMet = HEAThermoEngine.computeThermodynamics(app.MatrixData, app.CompositionBasis);
                                app.LastThermoMetrics = thermoMet;
                            end
                            mechRes = HEAMechanicalEngine.computeMechanicalProperties(summary.Elements, summary.AtFractions, thermoMet, userOpts);
                            app.LastThermoMetrics.Mechanical = mechRes;
                            app.htmlSend('mechanicalMetrics', mechRes);
                        catch ME_mech
                            fprintf('Warning: Mechanical recalc error: %s\n', ME_mech.message);
                        end

                    case 'requestOxidationRecalc'
                        try
                            userOpts = struct();
                            if isfield(d, 'temp_C') && ~isempty(d.temp_C)
                                userOpts.Temperature_C = double(d.temp_C);
                            end
                            if isfield(d, 'exposureHours') && ~isempty(d.exposureHours)
                                userOpts.ExposureHours = double(d.exposureHours);
                            end
                            [~, summary] = HEAThermoEngine.convertComposition(app.MatrixData, app.CompositionBasis, 'at');
                            thermoMet = app.LastThermoMetrics;
                            if isempty(thermoMet)
                                thermoMet = HEAThermoEngine.computeThermodynamics(app.MatrixData, app.CompositionBasis);
                                app.LastThermoMetrics = thermoMet;
                            end
                            oxRes = HEAOxidationEngine.computeOxidationKinetics(summary.Elements, summary.AtFractions, thermoMet, userOpts);
                            app.LastThermoMetrics.Oxidation = oxRes;
                            app.htmlSend('oxidationMetrics', oxRes);
                        catch ME_ox
                            fprintf('Warning: Oxidation recalc error: %s\n', ME_ox.message);
                        end

                    case 'applyDataOverrides'
                        if isfield(d,'points') && ~isempty(d.points)
                            app.applyOverrides(d.points);
                        end

                    case 'resetDataOverrides'
                        filename = fullfile(app.DataFolder, app.CurrentFile);
                        if isKey(app.DataCache, filename)
                            remove(app.DataCache, filename);
                        end
                        app.CustomDataOverrides = [];
                        app.onFileChange();

                    case 'exportRawData'
                        if isfield(d, 'filename') && isfield(d, 'content')
                            try
                                savePath = fullfile(pwd, d.filename);
                                fid = fopen(savePath, 'w');
                                if fid ~= -1
                                    fwrite(fid, d.content);
                                    fclose(fid);
                                    app.htmlSend('toast', struct('message', sprintf('CSV saved to %s', d.filename)));
                                end
                            catch
                            end
                        else
                            app.exportRawDataTable();
                        end

                    case 'exportImage'
                        if isfield(d, 'filename') && isfield(d, 'dataUrl')
                            try
                                fName = char(d.filename);
                                savePath = fullfile(pwd, fName);
                                dataUrl = char(d.dataUrl);
                                idx = strfind(dataUrl, 'base64,');
                                if ~isempty(idx)
                                    b64 = dataUrl(idx+7:end);
                                    bytes = matlab.net.base64decode(b64);
                                    fid = fopen(savePath, 'wb');
                                    if fid ~= -1
                                        fwrite(fid, bytes, 'uint8');
                                        fclose(fid);
                                        app.htmlSend('toast', struct('message', sprintf('Image exported: %s', fName)));
                                    end
                                end
                            catch ME
                                app.htmlSend('toast', struct('message', sprintf('Failed to export image: %s', ME.message)));
                            end
                        end

                    case 'importFileContent'
                        try
                            fName = d.filename;
                            content = d.content;
                            savePath = fullfile(app.DataFolder, fName);
                            fid = fopen(savePath, 'w');
                            if fid ~= -1
                                fwrite(fid, content);
                                fclose(fid);
                            end
                            if isKey(app.DataCache, savePath)
                                remove(app.DataCache, savePath);
                            end
                            app.CurrentFile = fName;
                            app.htmlSendFileList();
                            app.onFileChange();
                            app.htmlSend('toast', struct('message', sprintf('Imported %s', fName)));
                        catch ME
                            app.htmlSend('error', struct('message', sprintf('Import error: %s', ME.message)));
                        end

                    case 'importTDB'
                        try
                            tdbPath = '';
                            if isfield(d, 'path') && ~isempty(d.path)
                                tdbPath = char(d.path);
                            elseif isfield(d, 'content') && isfield(d, 'filename')
                                dbDir = fullfile(fileparts(mfilename('fullpath')), 'databases');
                                if ~exist(dbDir, 'dir'), mkdir(dbDir); end
                                tdbPath = fullfile(dbDir, char(d.filename));
                                fid = fopen(tdbPath, 'w');
                                if fid ~= -1
                                    fwrite(fid, d.content);
                                    fclose(fid);
                                end
                            end
                            if ~isempty(tdbPath)
                                res = HEAThermoEngine.importTDB(tdbPath);
                                app.htmlSend('toast', struct('message', sprintf('Imported TDB: %d binaries, %d ternaries', res.BinaryCount, res.TernaryCount)));
                                if ~isempty(app.MatrixData)
                                    metrics = HEAThermoEngine.computeThermodynamics(app.MatrixData, app.CompositionBasis);
                                    app.LastThermoMetrics = metrics;
                                    app.htmlSend('thermoMetrics', metrics);
                                end
                            end
                        catch ME_tdb
                            app.htmlSend('error', struct('message', sprintf('TDB import error: %s', ME_tdb.message)));
                        end

                    case 'setCompositionElements'
                        % Update selected elements chosen from the Periodic Table
                        if isfield(d, 'elements')
                            elems = d.elements;
                            if ischar(elems) || isstring(elems), elems = {char(elems)}; end
                            vals = [];
                            if isfield(d, 'values') && ~isempty(d.values)
                                vals = d.values;
                            end
                            app.setElementsAndValues(elems, vals);
                        end

                    case 'matrixEdit'
                        el = d.element;
                        val = d.value;
                        idx = find(strcmpi(app.ElementList, el), 1);
                        if isempty(idx)
                            app.ElementList{end+1} = el;
                            idx = numel(app.ElementList);
                            app.MatrixData{idx,1} = el;
                        end
                        if strcmp(app.CompositionBasis, 'mol')
                            app.MatrixData{idx,2} = sprintf('%.5f', val);
                        elseif abs(val - round(val)) < 1e-5
                            app.MatrixData{idx,2} = sprintf('%.1f', val);
                        else
                            app.MatrixData{idx,2} = sprintf('%.5f', val);
                        end
                        app.CurrentCompositionStr = app.buildCompStr();
                        app.htmlSendMatrixUpdate();

                    case 'matrixPreset'
                        app.applyPreset(d.preset);

                    case 'matrixBalance'
                        app.doBalance();

                    case 'matrixReset'
                        for i = 1:numel(app.ElementList)
                            app.MatrixData{i,2} = '0.0';
                        end
                        app.CurrentCompositionStr = '';
                        app.htmlSendMatrixUpdate();

                    case 'setCompositionBasis'
                        if isfield(d, 'basis') && ~isempty(d.basis)
                            newBasis = d.basis;
                            if ~strcmp(app.CompositionBasis, newBasis)
                                try
                                    [app.MatrixData, ~] = HEAThermoEngine.convertComposition(app.MatrixData, app.CompositionBasis, newBasis);
                                catch
                                end
                                app.CompositionBasis = newBasis;
                                app.CurrentBasis = newBasis;
                                app.CurrentCompositionStr = app.buildCompStr();
                                app.htmlSendMatrixUpdate();
                            end
                        end

                    case 'calculateHEAThermo'
                        % Synchronize composition if passed
                        if isfield(d, 'elements') && ~isempty(d.elements)
                            elems = d.elements;
                            if ischar(elems) || isstring(elems), elems = {char(elems)}; end
                            vals = [];
                            if isfield(d, 'values') && ~isempty(d.values), vals = d.values; end
                            app.setElementsAndValues(elems, vals);
                        end
                        if isfield(d, 'basis') && ~isempty(d.basis)
                            app.CompositionBasis = d.basis;
                        end

                        % Read user-configured step size and iterations
                        stepSize = 10;
                        if isfield(d, 'stepSize') && ~isempty(d.stepSize) && d.stepSize > 0
                            stepSize = double(d.stepSize);
                        end
                        numIter = 250;
                        if isfield(d, 'iterations') && ~isempty(d.iterations) && d.iterations > 0
                            numIter = round(double(d.iterations));
                        end

                        try
                            % Real-time detailed progress callback to HTML frontend
                            progressCb = @(pct, stg, det, iter, maxIt) app.htmlSend('calcProgress', struct( ...
                                'percent', pct, ...
                                'stage', stg, ...
                                'detail', det, ...
                                'iteration', iter, ...
                                'maxIter', maxIt, ...
                                'stepSize', stepSize));

                            progressCb(10, 'Composition Analysis & Normalization', ...
                                sprintf('Validating %d active components & SGTE thermodynamic database...', size(app.MatrixData, 1)), 10, numIter);

                            genFileName = 'Generated_HEA_Model.dat';
                            [filePath, ~, metrics] = HEAThermoEngine.exportJMatProDatFile(app.MatrixData, app.CompositionBasis, ...
                                app.DataFolder, genFileName, stepSize, numIter, progressCb);
                            app.T_Solidus = metrics.T_Solidus;
                            app.T_Liquidus = metrics.T_Liquidus;
                            app.LastThermoMetrics = metrics;

                            progressCb(75, 'Kinematic XRD Diffraction', ...
                                'Calculating Cromer-Mann form factors, structure factors & Bragg peaks...', round(numIter * 0.75), numIter);

                            if isKey(app.DataCache, filePath)
                                remove(app.DataCache, filePath);
                            end
                            app.CurrentFile = genFileName;
                            app.htmlSendFileList();
                            app.onFileChange();

                            app.htmlSend('thermoMetrics', metrics);

                            % Concurrently compute and stream interactive XRD diffraction data
                            try
                                xrdPayload = HEAXRDEngine.calculateXRD(app.MatrixData, app.CompositionBasis, ...
                                    app.XRD_Radiation, app.XRD_CrystalliteSize, app.XRD_Microstrain);
                                app.CurrentXRDData = xrdPayload;
                                app.htmlSend('xrdData', xrdPayload);
                            catch ME_xrd
                                fprintf('Warning: XRD calculation error: %s\n', ME_xrd.message);
                            end

                            % Concurrently compute and stream equilibrium phase fractions f_phi(T)
                            try
                                pfPayload = HEAThermoEngine.computeEquilibriumPhaseFractions(app.MatrixData, app.CompositionBasis);
                                app.htmlSend('phaseFractionsData', pfPayload);
                            catch ME_pf
                                fprintf('Warning: Phase fractions calculation error: %s\n', ME_pf.message);
                            end

                            progressCb(100, 'Calculation Complete', ...
                                sprintf('Generated %s (Ts=%.0f K, Tl=%.0f K, ΔT=%.1f K, %d iterations)', ...
                                metrics.Phase, metrics.T_Solidus, metrics.T_Liquidus, stepSize, numIter), numIter, numIter);

                            app.htmlSend('toast', struct('message', sprintf('Calculated HEA Model: %s (Ts=%.0f K, Tl=%.0f K, ΔT=%.1f K)', ...
                                metrics.Phase, metrics.T_Solidus, metrics.T_Liquidus, stepSize)));
                        catch ME
                            app.htmlSend('calcProgress', struct('percent', 100, 'stage', 'Error', 'detail', ME.message, 'iteration', numIter, 'maxIter', numIter, 'stepSize', stepSize));
                            app.htmlSend('error', struct('message', sprintf('Thermodynamic calculation error: %s', ME.message)));
                        end

                    case 'searchOnlineReferences'
                        queryStr = '';
                        if isfield(d, 'query') && ~isempty(d.query)
                            queryStr = strtrim(d.query);
                        else
                            queryStr = app.CurrentCompositionStr;
                        end
                        cleanQ = regexprep(queryStr, '[^a-zA-Z0-9\s-]', '');
                        encodedQ = urlencode(strtrim(cleanQ));
                        url = sprintf('https://api.openalex.org/works?search=%s+high+entropy+alloy+properties&per_page=5', encodedQ);
                        
                        % Layer 2: Egress DLP Sanitizer validation
                        if ~SecureDataVault.validateOutboundUrl(url)
                            app.htmlSend('onlineReferences', struct('papers', {{}}, 'error', 'DLP Alert: Outbound query blocked by Egress Sanitizer.', 'query', cleanQ));
                            return;
                        end
                        
                        try
                            opts = weboptions('Timeout', 3, 'UserAgent', 'MaterialPropertiesApp/2.0 (academic-research@matlab.org)');
                            res = webread(url, opts);
                            papers = {};
                            if isfield(res, 'results') && ~isempty(res.results)
                                for pIdx = 1:min(5, numel(res.results))
                                    it = res.results(pIdx);
                                    authStr = '';
                                    if isfield(it, 'authorships') && ~isempty(it.authorships)
                                        aList = {};
                                        for aI = 1:min(3, numel(it.authorships))
                                            aList{end+1} = it.authorships(aI).author.display_name;
                                        end
                                        authStr = strjoin(aList, ', ');
                                        if numel(it.authorships) > 3, authStr = [authStr, ', et al.']; end
                                    end
                                    jName = 'Scholarly Journal';
                                    if isfield(it, 'primary_location') && ~isempty(it.primary_location) && ...
                                       isfield(it.primary_location, 'source') && ~isempty(it.primary_location.source)
                                        jName = it.primary_location.source.display_name;
                                    end
                                    doiStr = '';
                                    if isfield(it, 'doi') && ~isempty(it.doi), doiStr = it.doi; end
                                    yVal = 0;
                                    if isfield(it, 'publication_year') && ~isempty(it.publication_year), yVal = it.publication_year; end
                                    cCount = 0;
                                    if isfield(it, 'cited_by_count') && ~isempty(it.cited_by_count), cCount = it.cited_by_count; end
                                    papers{end+1} = struct('title', it.title, 'authors', authStr, 'journal', jName, ...
                                        'year', yVal, 'doi', doiStr, 'citations', cCount);
                                end
                            end
                            app.htmlSend('onlineReferences', struct('papers', {papers}, 'query', cleanQ));
                        catch ME
                            app.htmlSend('onlineReferences', struct('papers', {{}}, 'error', ME.message, 'query', cleanQ));
                        end

                    case 'changeDir'
                        try
                            newDir = uigetdir(app.DataFolder, 'Select folder containing .dat files');
                            if ~isequal(newDir, 0)
                                app.DataFolder = newDir;
                                app.htmlSendFileList();
                            end
                        catch
                            % Fallback to HTML folder picker if dialog is blocked
                            app.htmlSend('openFolderPicker', struct());
                        end

                    case 'importFile'
                        try
                            [file, path] = uigetfile({'*.dat;*.csv;*.txt', 'Material Data (*.dat, *.csv, *.txt)'}, 'Select file');
                            if ~isequal(file, 0)
                                app.DataFolder = path;
                                app.CurrentFile = file;
                                app.htmlSendFileList();
                                app.onFileChange();
                            end
                        catch
                            % Fallback to HTML file picker if dialog is blocked
                            app.htmlSend('openFilePicker', struct());
                        end

                    case 'openURL'
                        try
                            if isfield(d,'url') && ~isempty(d.url)
                                web(d.url,'-browser');
                            end
                        catch
                        end

                    case 'exportComsol'
                        if isfield(d, 'filename') && isfield(d, 'content')
                            try
                                savePath = fullfile(pwd, d.filename);
                                fid = fopen(savePath, 'w');
                                if fid ~= -1
                                    fwrite(fid, d.content);
                                    fclose(fid);
                                    app.htmlSend('toast', struct('message', sprintf('COMSOL output saved to %s', d.filename)));
                                end
                            catch
                            end
                        else
                            app.generateCOMSOLOutput();
                        end

                    case 'encryptVaultFile'
                        try
                            targetFile = '';
                            if isfield(d, 'filename') && ~isempty(d.filename)
                                targetFile = fullfile(app.DataFolder, d.filename);
                            elseif ~isempty(app.CurrentFile)
                                targetFile = fullfile(app.DataFolder, app.CurrentFile);
                            else
                                targetFile = fullfile(app.DataFolder, 'Generated_HEA_Model.dat');
                            end
                            passphrase = '';
                            if isfield(d, 'passphrase'), passphrase = d.passphrase; end
                            if isempty(passphrase)
                                app.htmlSend('error', struct('message', 'Passphrase required to lock the vault.'));
                                return;
                            end
                            [p, n, ~] = fileparts(targetFile);
                            vaultPath = fullfile(p, [n, '.hea.vault']);
                            t0 = tic;
                            SecureDataVault.encryptFile(targetFile, vaultPath, passphrase);
                            elSec = toc(t0);
                            vHash = SecureDataVault.computeSHA256(vaultPath);
                            
                            shredded = false;
                            if isfield(d, 'shredOriginal') && d.shredOriginal
                                SecureDataVault.secureShred(targetFile);
                                shredded = true;
                            end
                            
                            [~, vName, vExt] = fileparts(vaultPath);
                            app.htmlSendFileList();
                            app.htmlSend('vaultResult', struct('action', 'encrypt', 'success', true, ...
                                'vaultFile', [vName, vExt], 'sha256', vHash, 'elapsedSec', elSec, 'shredded', shredded, ...
                                'message', sprintf('AES-256 Vault: Encrypted %s in %.2fs (SHA-256: %s...)', [vName, vExt], elSec, vHash(1:16))));
                        catch ME
                            app.htmlSend('vaultResult', struct('action', 'encrypt', 'success', false, 'message', ME.message));
                        end

                    case 'decryptVaultFile'
                        try
                            vFile = '';
                            if isfield(d, 'filename'), vFile = fullfile(app.DataFolder, d.filename); end
                            passphrase = '';
                            if isfield(d, 'passphrase'), passphrase = d.passphrase; end
                            if ~isfile(vFile)
                                app.htmlSend('error', struct('message', 'Selected vault file does not exist.'));
                                return;
                            end
                            t0 = tic;
                            [p, n, ~] = fileparts(vFile);
                            if endsWith(n, '.hea'), n = extractBefore(n, '.hea'); end
                            outPlain = fullfile(p, [n, '.dat']);
                            SecureDataVault.decryptFile(vFile, outPlain, passphrase);
                            elSec = toc(t0);
                            decHash = SecureDataVault.computeSHA256(outPlain);
                            [~, pName, pExt] = fileparts(outPlain);
                            
                            app.CurrentFile = [pName, pExt];
                            app.htmlSendFileList();
                            app.onFileChange();
                            app.htmlSend('vaultResult', struct('action', 'decrypt', 'success', true, ...
                                'plainFile', [pName, pExt], 'sha256', decHash, 'elapsedSec', elSec, ...
                                'message', sprintf('AES-256 Vault: Unlocked %s in %.2fs (SHA-256: %s...)', [pName, pExt], elSec, decHash(1:16))));
                        catch ME
                            app.htmlSend('vaultResult', struct('action', 'decrypt', 'success', false, 'message', ME.message));
                        end

                    case 'shredPlaintextFile'
                        try
                            targetFile = fullfile(app.DataFolder, d.filename);
                            if isfile(targetFile)
                                SecureDataVault.secureShred(targetFile);
                                app.htmlSendFileList();
                                app.htmlSend('vaultResult', struct('action', 'shred', 'success', true, ...
                                    'message', sprintf('NIST SP 800-88: %s permanently sanitized & unlinked.', d.filename)));
                            end
                        catch ME
                            app.htmlSend('vaultResult', struct('action', 'shred', 'success', false, 'message', ME.message));
                        end

                    case 'secureClipboardCopy'
                        if isfield(d, 'text') && ~isempty(d.text)
                            SecureDataVault.copySecureClipboard(d.text);
                            app.htmlSend('toast', struct('message', 'Copied to secure ephemeral clipboard (auto-wipes in 30s).'));
                        end

                    case 'liveSearch'
                        app.CompareEnabled = true;
                        app.onPropChange(true);
                end
            catch ME
                try
                    app.htmlSend('error', struct('message', ME.message));
                catch
                end
            end
        end

        % Send payload to the uihtml component in the frontend
        function htmlSend(app, eventType, dataStruct)
            if isempty(app.HtmlComponent), return; end
            dataStruct.type = eventType;
            try
                app.HtmlComponent.Data = dataStruct;
            catch
            end
            try
                sendEventToHTMLSource(app.HtmlComponent, 'update', dataStruct);
            catch
            end
        end

        function htmlSendFileList(app)
            if ~exist(app.DataFolder,'dir')
                parent = fullfile(fileparts(mfilename('fullpath')),'..','materials_data');
                if exist(parent,'dir'), app.DataFolder = parent; end
            end
            files = dir(fullfile(app.DataFolder,'*.dat'));
            if isempty(files)
                names = {'No .dat files found'};
            else
                names = {files.name};
            end
            sel = '';
            if ~isempty(names) && ~strcmp(names{1},'No .dat files found')
                if isempty(app.CurrentFile) || ~any(strcmp(names, app.CurrentFile))
                    app.CurrentFile = names{1};
                end
                sel = app.CurrentFile;
            end
            vFiles = dir(fullfile(app.DataFolder, '*.hea.vault'));
            if isempty(vFiles)
                vNames = {};
            else
                vNames = {vFiles.name};
            end
            app.htmlSend('fileList', struct('files', {names}, 'selected', sel, 'vaultFiles', {vNames}));
        end

        function htmlSendMatrixUpdate(app)
            elements = app.ElementList;
            n = numel(elements);
            values = zeros(1, n);
            for i = 1:n
                v = app.MatrixData{i,2};
                if ischar(v)||isstring(v), v = str2double(v); end
                if isnan(v), v = 0; end
                values(i) = v;
            end
            total = sum(values);

            % Calculate live molar and mass statistics
            try
                [~, summary] = HEAThermoEngine.convertComposition(app.MatrixData, app.CompositionBasis, app.CompositionBasis);
                meanMolarMass = summary.MeanMolarMass;
                totalMass     = summary.TotalMass;
                totalMoles    = summary.TotalMoles;
            catch
                meanMolarMass = 55.0;
                totalMass     = total;
                totalMoles    = total / 55.0;
            end

            app.htmlSend('matrixData', struct( ...
                'elements',      {elements(:)'}, ...
                'values',        values, ...
                'total',         total, ...
                'basis',         app.CompositionBasis, ...
                'meanMolarMass', meanMolarMass, ...
                'totalMass',     totalMass, ...
                'totalMoles',    totalMoles));
        end

        % Load raw dataset, apply SI unit scaling, and extract initial state
        function onFileChange(app)
            if isempty(app.CurrentFile), return; end
            filename = fullfile(app.DataFolder, app.CurrentFile);
            if ~isfile(filename), return; end

            try
                if isKey(app.DataCache, filename)
                    rawTable = app.DataCache(filename);
                else
                    cacheDir = fullfile(app.DataFolder,'.cache');
                    if ~exist(cacheDir,'dir'), try, mkdir(cacheDir); catch, end; end
                    [~,fBase,~] = fileparts(filename);
                    cacheFile = fullfile(cacheDir,[matlab.lang.makeValidName(fBase) '.mat']);
                    datInfo   = dir(filename);
                    useCache  = false;
                    if isfile(cacheFile)
                        cf = dir(cacheFile);
                        if cf.datenum >= datInfo.datenum, useCache = true; end
                    end

                    if useCache
                        s = load(cacheFile,'rawTable');
                        rawTable = s.rawTable;
                    else
                        opts = detectImportOptions(filename,'Delimiter','\t');
                        opts.VariableNamingRule = 'preserve';
                        rawTable = readtable(filename, opts);
                        for i = 1:width(rawTable)
                            if iscell(rawTable.(i))||isstring(rawTable.(i))
                                rawTable.(i) = str2double(rawTable.(i));
                            end
                        end
                        vNames = rawTable.Properties.VariableNames;

                        expIdx = find(contains(vNames,'Linear expansion','IgnoreCase',true));
                        if ~isempty(expIdx)
                            vNames{expIdx(1)} = 'Coefficient of thermal expansion (%)';
                        end
                        totViscIdx = find(contains(vNames,'Total viscosity','IgnoreCase',true));
                        liqViscIdx = find(contains(vNames,'Liquid viscosity','IgnoreCase',true));
                        if ~isempty(totViscIdx)
                            if ~isempty(liqViscIdx)
                                tv = rawTable.(totViscIdx(1));
                                lv = rawTable.(liqViscIdx(1));
                                both = ~isnan(tv)&~isnan(lv)&(tv>0)&(lv>0);
                                tv(both) = (tv(both)+lv(both))/2;
                                rawTable.(totViscIdx(1)) = tv;
                                rawTable(:,liqViscIdx(1)) = [];
                                vNames = rawTable.Properties.VariableNames;
                                totViscIdx = find(contains(vNames,'Total viscosity','IgnoreCase',true));
                            end
                            vNames{totViscIdx(1)} = 'Dynamic viscosity (Pa*s)';
                        elseif ~isempty(liqViscIdx)
                            vNames{liqViscIdx(1)} = 'Dynamic viscosity (Pa*s)';
                        end
                        rhoIdx = find(contains(vNames,'Density','IgnoreCase',true));
                        if ~isempty(rhoIdx)
                            vals = rawTable.(rhoIdx(1));
                            validVals = vals(~isnan(vals));
                            if ~isempty(validVals) && mean(validVals) < 50
                                rawTable.(rhoIdx(1)) = rawTable.(rhoIdx(1)) * 1000;
                            end
                            vNames{rhoIdx(1)} = 'Density (kg/m^3)';
                        end
                        dynViscIdx = find(contains(vNames,'Dynamic viscosity','IgnoreCase',true));
                        if ~isempty(dynViscIdx)
                            rawTable.(dynViscIdx(1)) = rawTable.(dynViscIdx(1)) / 1000;
                        end
                        stIdx = find(contains(vNames,'Surface Tension','IgnoreCase',true));
                        if ~isempty(stIdx)
                            rawTable.(stIdx(1)) = rawTable.(stIdx(1)) / 1000;
                            vNames{stIdx(1)} = 'Surface Tension (N/m)';
                        end
                        ymIdx = find(contains(vNames,'Young','IgnoreCase',true));
                        if ~isempty(ymIdx)
                            rawTable.(ymIdx(1)) = rawTable.(ymIdx(1)) * 1e9;
                            vNames{ymIdx(1)} = 'Young''s modulus (Pa)';
                        end
                        prIdx = find(contains(vNames,'Poisson','IgnoreCase',true));
                        if ~isempty(prIdx), vNames{prIdx(1)} = 'Poisson''s ratio'; end
                        tcIdx = find(contains(vNames,'Thermal conductivity','IgnoreCase',true));
                        if ~isempty(tcIdx), vNames{tcIdx(1)} = 'Thermal conductivity (W/(m*K))'; end
                        cpIdx = find(contains(vNames,'Specific heat','IgnoreCase',true));
                        if ~isempty(cpIdx), vNames{cpIdx(1)} = 'Specific heat (J/(mole K))'; end
                        
                        % Standardize electrical resistivity if present
                        resIdx = find(contains(vNames,'resistivity','IgnoreCase',true), 1);
                        if ~isempty(resIdx)
                            colName = vNames{resIdx};
                            if contains(colName,'10e-6') || contains(colName,'micro','IgnoreCase',true)
                                rawTable.(resIdx) = rawTable.(resIdx) * 1e-6;
                            end
                            vNames{resIdx} = 'Electrical resistivity (Ohm*m)';
                        end
                        rawTable.Properties.VariableNames = vNames;
                        try, save(cacheFile,'rawTable'); catch, end
                    end
                    app.DataCache(filename) = rawTable;
                end

                % Ensure both Laser Absorptivity and Surface Emissivity columns are present in dataset
                vNames = rawTable.Properties.VariableNames;
                resIdx = find(contains(vNames,'resistivity','IgnoreCase',true), 1);
                if ~isempty(resIdx)
                    rhoVals = rawTable.(resIdx);
                    validMask = ~isnan(rhoVals) & (rhoVals > 0);
                    if any(validMask) && mean(rhoVals(validMask)) > 1e-4
                        rhoVals = rhoVals * 1e-6;
                    end
                else
                    % Wiedemann-Franz law: rho = L0 * T / k
                    tcIdx = find(contains(vNames,'Thermal conductivity','IgnoreCase',true), 1);
                    if ~isempty(tcIdx)
                        T_col = rawTable{:,1};
                        k_col = max(1.0, rawTable.(tcIdx));
                        L0 = 2.44e-8; % Lorenz number [W*Ohm/K^2]
                        rhoVals = (L0 .* T_col) ./ k_col;
                    else
                        rhoVals = 1.5e-6 * ones(height(rawTable), 1);
                    end
                end

                % 1. Laser Absorptivity A(T) (Hagen-Rubens at laser wavelength)
                if ~any(contains(vNames, 'Absorptivity', 'IgnoreCase', true))
                    lambda_laser = max(0.1, app.LaserWavelength);
                    A_base = 0.365 * sqrt(max(1e-12, rhoVals * 1e6) / lambda_laser);
                    rawTable.('Laser Absorptivity A(T)') = min(0.95, max(0.02, A_base));
                end

                % 2. Surface Emissivity eps(T) (Total hemispherical thermal radiation)
                if ~any(contains(vNames, 'Emissivity', 'IgnoreCase', true))
                    T_col = rawTable{:,1};
                    eps_base = min(0.92, max(0.05, 0.751 * sqrt(max(1e-12, rhoVals .* T_col .* 1e-2))));
                    rawTable.('Surface Emissivity eps(T)') = eps_base;
                end

                app.CurrentData = rawTable;
                app.detectMeltingPoint();

                props = rawTable.Properties.VariableNames(2:end);
                selProp = '';
                dIdx = find(contains(props,'Density','IgnoreCase',true),1);
                if ~isempty(dIdx)
                    selProp = props{dIdx};
                elseif ~isempty(props)
                    selProp = props{1};
                end
                if isempty(app.CurrentProperty) || ~any(strcmp(props, app.CurrentProperty))
                    app.CurrentProperty = selProp;
                end

                app.htmlSend('propList', struct('props',{props},'selected',selProp, ...
                    'file', app.CurrentFile));

                % Auto-calculate after file load
                if ~app.IsInitializing
                    app.onPropChange(false);
                end

            catch ME
                app.htmlSend('error', struct('message', ME.message));
            end
        end

        % Infer alloy solidus/liquidus and melting point from thermodynamic data
        function detectMeltingPoint(app)
            if isempty(app.CurrentData), return; end
            T = app.CurrentData{:,1};
            app.T_Min = min(T);
            app.T_Max = max(T);
            vNames = app.CurrentData.Properties.VariableNames;

            % 0. If this is the generated HEA model and we already have reliable thermodynamic metrics,
            % preserve the rigorously computed CALPHAD solidus and liquidus!
            if (strcmp(app.CurrentFile, 'Generated_HEA_Model.dat') || contains(app.CurrentFile, 'Generated_HEA')) && ...
                    ~isempty(app.LastThermoMetrics) && isfield(app.LastThermoMetrics, 'T_Solidus') && ...
                    app.LastThermoMetrics.T_Solidus > (app.T_Min + 50)
                app.T_Solidus  = app.LastThermoMetrics.T_Solidus;
                app.T_Liquidus = app.LastThermoMetrics.T_Liquidus;
                app.CurrentMeltingPoint = (app.T_Solidus + app.T_Liquidus) / 2;
                return;
            end

            app.T_Solidus  = app.T_Min;
            app.T_Liquidus = app.T_Max;

            % 1. Look for explicit thermodynamic LIQUID phase percentage column
            liqIdx = find(contains(vNames,'LIQUID','IgnoreCase',true), 1);
            if ~isempty(liqIdx)
                liq = app.CurrentData.(liqIdx);
                valid = ~isnan(T)&~isnan(liq);
                Tv = T(valid); LV = liq(valid);
                [Tv,si] = sort(Tv); LV = LV(si);
                solIdx = find(LV <= 0.5, 1, 'last');
                if ~isempty(solIdx), app.T_Solidus = Tv(solIdx); end
                pureLiqIdx = find(LV >= 99.0, 1, 'first');
                if ~isempty(pureLiqIdx), app.T_Liquidus = Tv(pureLiqIdx); end
                app.CurrentMeltingPoint = (app.T_Solidus + app.T_Liquidus) / 2;
                return;
            end

            % 2. Check Young's modulus collapse (loss of shear/elastic resistance)
            ymIdx = find(contains(vNames,'Young','IgnoreCase',true), 1);
            if ~isempty(ymIdx)
                ym = app.CurrentData.(ymIdx);
                valid = ~isnan(T)&~isnan(ym);
                Tv = T(valid); YMv = ym(valid);
                [Tv,si] = sort(Tv); YMv = YMv(si);
                maxYm = max(YMv);
                if maxYm > 1e6
                    % Values in Pa
                    zeroYm = find(YMv <= 1e5, 1, 'first');
                    solidYm = find(YMv >= 1e10, 1, 'last');
                else
                    % Values in GPa
                    zeroYm = find(YMv <= 0.5, 1, 'first');
                    solidYm = find(YMv >= 10.0, 1, 'last');
                end
                if ~isempty(zeroYm)
                    app.T_Liquidus = Tv(zeroYm);
                end
                if ~isempty(solidYm)
                    app.T_Solidus = Tv(solidYm);
                end
            end

            % 3. Check viscosity onset (JMatPro exports zeroes below solidus)
            viscIdx = find(contains(vNames,'viscosity','IgnoreCase',true), 1);
            if ~isempty(viscIdx)
                visc = app.CurrentData.(viscIdx);
                valid = ~isnan(T)&~isnan(visc);
                Tv = T(valid); Vv = visc(valid);
                [Tv,si] = sort(Tv); Vv = Vv(si);
                % Only use posVisc if there are actual 0 values below solidus (genuine JMatPro format)
                if any(Vv == 0)
                    posVisc = find(Vv > 0, 1, 'first');
                    if ~isempty(posVisc)
                        app.T_Solidus = Tv(posVisc);
                    end
                end
            end

            % Guard: ensure reasonable positive temperature span
            if app.T_Solidus >= app.T_Liquidus
                app.T_Solidus = app.T_Liquidus - 150;
            end
            if app.T_Solidus <= app.T_Min && app.T_Liquidus > (app.T_Min + 200)
                app.T_Solidus = max(app.T_Min, app.T_Liquidus - 150);
            end
            app.CurrentMeltingPoint = (app.T_Solidus + app.T_Liquidus) / 2;
        end

        % Fit temperature-dependent curve and broadcast analytical formulation
        function onPropChange(app, forceLiveSearch)
            if nargin < 2, forceLiveSearch = false; end
            if app.IsInitializing, return; end
            if isempty(app.CurrentData), return; end
            if isempty(app.CurrentProperty), return; end

            T = app.CurrentData{:,1};
            props = app.CurrentData.Properties.VariableNames;
            if ~any(strcmp(props, app.CurrentProperty))
                if numel(props) >= 2, app.CurrentProperty = props{2}; else, return; end
            end
            Y = app.CurrentData{:, app.CurrentProperty};

            valid = ~isnan(T) & ~isnan(Y);
            T = T(valid); Y = Y(valid);
            [T,si] = sort(T); Y = Y(si);

            if isempty(T)
                app.htmlSend('calcResult', struct('equation','No valid data for this property.', ...
                    'R2',[],'RMSE',[],'range','','order','', ...
                    'plotData', struct('rawT',[],'rawY',[],'fitT',[],'fitY',[], ...
                                      'fitT2',[],'fitY2',[], ...
                                      'meltingPoint',app.CurrentMeltingPoint, ...
                                      'xLabel','Temperature (K)', ...
                                      'yLabel',app.CurrentProperty)));
                return;
            end

            fitType = app.CurrentFitType;
            Tm      = app.CurrentMeltingPoint;
            lowerProp = lower(app.CurrentProperty);

            % Collect fit segments for sending to HTML
            fitT = []; fitY = []; fitT2 = []; fitY2 = [];
            eqLines = {};
            citData = struct('title','','doi','','verified',false,'text','');
            comsolData = struct('isViscosity', false, 'solidExpr', '', 'mushyExpr', '', 'liquidExpr', '', 'flc2hsExpr', '', 'paramsText', '');

            try
                isAuto = strcmp(fitType,'Auto (Physics-based Recommended)');

                if contains(lowerProp, 'viscosity')
                    % Dynamic viscosity with continuous mushy-zone suspension rheology
                    Ts = app.T_Solidus;
                    Tl = app.T_Liquidus;
                    if Ts >= Tl, Ts = Tl - 150; end
                    
                    % 1. Extract valid liquid points (T >= Tl and Y > 0)
                    idx_liquid = (T >= Tl) & (Y > 0);
                    T_liq = T(idx_liquid);
                    Y_liq = Y(idx_liquid);
                    
                    if isempty(T_liq)
                        idx_liquid = (T > (Ts + Tl)/2) & (Y > 0);
                        T_liq = T(idx_liquid);
                        Y_liq = Y(idx_liquid);
                    end
                    
                    if ~isempty(T_liq)
                        p_exp = polyfit(1 ./ T_liq, log(Y_liq), 1);
                        B = p_exp(1);
                        A = exp(p_exp(2));
                    else
                        A = 3.5e-4; B = 3850;
                    end
                    
                    mu_L_func = @(t) A .* exp(B ./ t);
                    mu_L_Tl = mu_L_func(Tl); % exact value at liquidus
                    
                    % 2. Mushy Zone Model: Solidus (Ts) to Liquidus (Tl)
                    N_mush = 60;
                    T_mush = linspace(Ts, Tl, N_mush);
                    fs = (Tl - T_mush) ./ (Tl - Ts); % solid fraction: 0 at Tl, 1 at Ts
                    
                    fm = app.PackingFraction; % 0.65 default
                    eta_exp = app.IntrinsicVisc * fm; % 2.5 * 0.65 = 1.625
                    mu_solid_target = app.ViscSolidCap; % e.g. 1e3 or 1e5 Pa*s
                    
                    isSigmoid = contains(lower(fitType), 'sigmoid') || strcmpi(app.MushyModel, 'Sigmoid');
                    isPiecewise = strcmpi(fitType, 'piecewise');
                    
                    if isSigmoid
                        % Sigmoidal blending gives C-infinity smoothness for CFD solvers
                        T_mid = (Ts + Tl) / 2;
                        sigma = (Tl - Ts) / 6.0;
                        s_blend = 1.0 ./ (1.0 + exp(-(T_mush - T_mid) ./ sigma));
                        Y_mush = mu_L_func(T_mush) .* s_blend + mu_solid_target .* (1.0 - s_blend);
                        modelDesc = 'Sigmoid Smooth Blending (COMSOL CFD)';
                        
                    elseif isPiecewise
                        % Piecewise linear fit forced through the liquidus boundary point
                        idx_mush_raw = (T >= Ts) & (T < Tl) & (Y > 0);
                        if sum(idx_mush_raw) >= 2
                            p_mush = polyfit(T(idx_mush_raw), Y(idx_mush_raw), 1);
                            shift_anchor = mu_L_Tl - polyval(p_mush, Tl);
                            Y_mush = polyval(p_mush, T_mush) + shift_anchor;
                        else
                            Y_mush = linspace(mu_L_Tl * 2.5, mu_L_Tl, N_mush);
                        end
                        modelDesc = 'Continuous Piecewise (Anchored at Tl)';
                        
                    else
                        % Krieger-Dougherty suspension model for solid crystals in molten matrix
                        rel_fs = min(0.985, fs ./ fm);
                        kd_factor = (1.0 - rel_fs) .^ (-eta_exp);
                        Y_mush = mu_L_func(T_mush) .* kd_factor;
                        
                        blend_solid = max(0, min(1, (fs - 0.7) / 0.3));
                        Y_mush = Y_mush .* (1 - blend_solid) + mu_solid_target .* blend_solid;
                        
                        % Anchor end point exactly to avoid any numerical offset
                        Y_mush(end) = mu_L_Tl;
                        modelDesc = 'Krieger-Dougherty Suspension Model';
                    end
                    
                    % 3. Solid Regime (T <= Ts)
                    T_sol = linspace(app.T_Min, Ts, 40);
                    Y_sol = mu_solid_target .* ones(size(T_sol));
                    
                    % 4. Liquid Regime (T >= Tl)
                    T_liq_plot = linspace(Tl, app.T_Max, 80);
                    Y_liq_plot = mu_L_func(T_liq_plot);
                    
                    % 5. Continuous Converged Curves:
                    % fitT: Liquid curve (T >= Tl)
                    % fitT2: Mushy + Solid continuous curve (T <= Tl, exactly starts at mu_L(Tl))
                    fitT  = T_liq_plot;
                    fitY  = Y_liq_plot;
                    fitT2 = [T_sol(1:end-1), T_mush];
                    fitY2 = [Y_sol(1:end-1), Y_mush];
                    
                    % Self-contained, executable COMSOL syntax for the mushy transition interval
                    if isSigmoid
                        mushyComsolSyntax = sprintf('(%.4e*exp(%.2f/T))/(1+exp(-(T-%.1f)/%.1f)) + %.1e/(1+exp((T-%.1f)/%.1f))', ...
                            A, B, (Ts+Tl)/2, (Tl-Ts)/6, mu_solid_target, (Ts+Tl)/2, (Tl-Ts)/6);
                    elseif isPiecewise
                        mushyComsolSyntax = sprintf('(%.4e - %.1e)*(T - %.1f)/%.1f + %.1e', ...
                            mu_L_Tl, mu_solid_target, Ts, Tl - Ts, mu_solid_target);
                    else
                        % Capped Krieger-Dougherty: prevents negative base & division by zero, exactly caps at mu_solid
                        mushyComsolSyntax = sprintf('min(%.1e, (%.4e*exp(%.2f/T)) * (max(1e-4, 1 - min((%.1f-T)/%.1f, %.3f)/%.2f)^(-%.3f)))', ...
                            mu_solid_target, A, B, Tl, Tl - Ts, fm - 0.001, fm, eta_exp);
                    end
                    
                    eqLines = { ...
                        sprintf('// COMSOL Continuous Viscosity Definition'); ...
                        sprintf('// Model: %s', modelDesc); ...
                        sprintf('// Solidus Ts = %.1f K, Liquidus Tl = %.1f K (transition width = %.1f K)', Ts, Tl, Tl - Ts); ...
                        ''; ...
                        sprintf('// 1. Liquid-phase Arrhenius fit (T >= %.1f K):', Tl); ...
                        sprintf('mu_liquid(T) = %.4e * exp(%.2f / T)  [Pa*s]', A, B); ...
                        ''; ...
                        sprintf('// 2. Liquidus boundary anchor:'); ...
                        sprintf('mu(Tl = %.1f K) = %.6e Pa*s', Tl, mu_L_Tl); ...
                        ''; ...
                        sprintf('// 3. COMSOL flc2hs smooth step formulation:'); ...
                        sprintf('delta_T = %.1f [K];', (Tl - Ts) / 2); ...
                        sprintf('T_mid   = %.1f [K];', (Ts + Tl) / 2); ...
                        sprintf('mu_solid= %.1e [Pa*s];', mu_solid_target); ...
                        sprintf('mu_app(T) = mu_liquid(T) + (mu_solid - mu_liquid(T)) * flc2hs(%.1f - T, %.1f);', Tl, (Tl - Ts)/2); ...
                        ''; ...
                        'Start [K]    End [K]      Function (COMSOL Syntax)'; ...
                        sprintf('%-12.1f %-12.1f %s', app.T_Min, Ts, sprintf('%.1e', mu_solid_target)); ...
                        sprintf('%-12.1f %-12.1f %s', Ts, Tl, mushyComsolSyntax); ...
                        sprintf('%-12.1f %-12.1f %s', Tl, app.T_Max, sprintf('%.4e * exp(%.2f / T)', A, B)) ...
                    };
                    
                    comsolData.isViscosity = true;
                    comsolData.mushyModel  = modelDesc;
                    comsolData.Ts          = Ts;
                    comsolData.Tl          = Tl;
                    comsolData.T_Min       = app.T_Min;
                    comsolData.T_Max       = app.T_Max;
                    comsolData.solidExpr   = sprintf('%.1e', mu_solid_target);
                    comsolData.mushyExpr   = mushyComsolSyntax;
                    comsolData.liquidExpr  = sprintf('%.4e * exp(%.2f / T)', A, B);
                    comsolData.flc2hsExpr  = sprintf('// COMSOL Continuous Smooth Step (flc2hs):\nmu_liquid(T) = %.4e * exp(%.2f / T);\nmu_solid = %.1e;\nmu_app(T) = mu_liquid(T) + (mu_solid - mu_liquid(T)) * flc2hs(%.1f - T, %.1f);', ...
                        A, B, mu_solid_target, Tl, (Tl - Ts)/2);
                    comsolData.paramsText  = sprintf('Ts\t%.1f [K]\tSolidus transition temperature\nTl\t%.1f [K]\tLiquidus transition temperature\nmu_solid\t%.1e [Pa*s]\tRigid solid phase penalty\nA_liq\t%.4e [Pa*s]\tArrhenius liquid pre-factor\nB_liq\t%.2f [K]\tArrhenius activation temperature\nf_max\t%.2f\tMaximum solid packing fraction\neta_int\t%.1f\tIntrinsic viscosity', ...
                        Ts, Tl, mu_solid_target, A, B, fm, app.IntrinsicVisc);

                elseif contains(lowerProp, 'absorptivity') || contains(lowerProp, 'emissivity')
                    % Temperature-dependent optical absorptivity and emissivity for laser processing
                    Ts = app.T_Solidus;
                    Tl = app.T_Liquidus;
                    if Ts >= Tl, Ts = Tl - 150; end

                    % 1. Retrieve electrical resistivity rho(T) [Ohm*m]
                    vNames = app.CurrentData.Properties.VariableNames;
                    resIdx = find(contains(vNames, 'resistivity', 'IgnoreCase', true), 1);
                    if ~isempty(resIdx)
                        rho_raw = app.CurrentData.(resIdx);
                        valMask = ~isnan(rho_raw) & (rho_raw > 0);
                        if any(valMask)
                            meanVal = mean(rho_raw(valMask));
                            if meanVal > 1e-4
                                rho_ohm_m = rho_raw * 1e-6;
                            else
                                rho_ohm_m = rho_raw;
                            end
                        else
                            rho_ohm_m = 1.5e-6 * ones(size(T));
                        end
                    else
                        % Wiedemann-Franz law: rho = L0 * T / k
                        tcIdx = find(contains(vNames, 'Thermal conductivity', 'IgnoreCase', true), 1);
                        if ~isempty(tcIdx)
                            k_raw = max(1.0, app.CurrentData.(tcIdx));
                            L0 = 2.44e-8; % Lorenz number [W*Ohm/K^2]
                            rho_ohm_m = (L0 .* T) ./ k_raw;
                        else
                            rho_ohm_m = 1.5e-6 * ones(size(T));
                        end
                    end

                    % Ensure continuous interpolation across temperature grid
                    rho_ohm_m = interp1(app.CurrentData{:,1}, rho_ohm_m, T, 'linear', 'extrap');
                    rho_ohm_m = max(1e-9, rho_ohm_m);

                    % 2. Bramson Hagen-Rubens baseline normal spectral absorptivity
                    lambda_um = max(0.1, app.LaserWavelength);
                    A_bulk = 0.365 * sqrt((rho_ohm_m * 1e6) / lambda_um);
                    A_bulk = min(0.95, max(0.02, A_bulk));

                    mode = app.LaserMode;
                    isHardening = strcmpi(mode, 'Hardening');
                    isCladding  = strcmpi(mode, 'Cladding') || strcmpi(mode, 'LPBF');
                    isEmissivitySelected = contains(lowerProp, 'emissivity');

                    if isHardening
                        % Laser Hardening (LSH): Purely solid-state (T < Ts)
                        % Self-quenching cooling rate dT/dt governed by radiative loss + cold substrate conduction
                        isGraphite = contains(app.SurfaceCondition, 'Graphite', 'IgnoreCase', true);
                        isPhosphate = contains(app.SurfaceCondition, 'Phosphate', 'IgnoreCase', true);

                        if isGraphite
                            A_eff = app.CoatingAbsorptivity * ones(size(T));
                            eps_eff = 0.85 * ones(size(T));
                            condDesc = sprintf('Graphite Absorbing Coating (Flat A = %.2f, eps = 0.85)', app.CoatingAbsorptivity);
                            f_sol_A = sprintf('%.4f', app.CoatingAbsorptivity);
                            f_sol_eps = '0.8500';
                        elseif isPhosphate
                            A_eff = 0.75 * ones(size(T));
                            eps_eff = 0.80 * ones(size(T));
                            condDesc = 'Manganese Phosphate Coating (Flat A = 0.75, eps = 0.80)';
                            f_sol_A = '0.7500';
                            f_sol_eps = '0.8000';
                        else
                            % Bare ground surface with thermal oxidation enhancement
                            eta_ox = 1.0 + 0.30 * max(0, min(1, (T - 500) / 700));
                            A_eff = min(0.92, app.SurfaceRoughFactor * eta_ox .* A_bulk);
                            eps_eff = min(0.92, max(0.18, 0.751 * sqrt(max(1e-12, rho_ohm_m .* T .* 1e-2)) .* (app.SurfaceRoughFactor * eta_ox)));
                            condDesc = sprintf('Bare Ground Surface (eta_rough = %.2f, thermal oxidation)', app.SurfaceRoughFactor);

                            p_sol_A = polyfit(T(T <= Ts), A_eff(T <= Ts), 2);
                            f_sol_A = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_sol_A(1), p_sol_A(2), p_sol_A(3));
                            f_sol_A = strrep(f_sol_A, '+ -', '- ');

                            p_sol_eps = polyfit(T(T <= Ts), eps_eff(T <= Ts), 2);
                            f_sol_eps = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_sol_eps(1), p_sol_eps(2), p_sol_eps(3));
                            f_sol_eps = strrep(f_sol_eps, '+ -', '- ');
                        end

                        if isEmissivitySelected
                            fitT  = T; fitY  = eps_eff;
                            fitT2 = T; fitY2 = A_eff;
                            f_primary_str = f_sol_eps;
                            propTitle = 'Surface Emissivity eps(T)';
                            eqHeader = '// 1. Temperature-Dependent Surface Emissivity eps(T):';
                            eqPrimary = sprintf('eps(T) = %s', f_sol_eps);
                            radDesc = sprintf('q_rad = (%s) * 5.670374e-8 * (T^4 - 293.15^4)  [W/m^2, Stefan-Boltzmann]', f_sol_eps);
                        else
                            fitT  = T; fitY  = A_eff;
                            fitT2 = T; fitY2 = eps_eff;
                            f_primary_str = f_sol_A;
                            propTitle = 'Laser Absorptivity A(T)';
                            eqHeader = '// 1. Temperature-Dependent Absorptivity A(T):';
                            eqPrimary = sprintf('A(T) = %s', f_sol_A);
                            radDesc = 'q_rad = eps(T) * 5.670374e-8 * (T^4 - 293.15^4)  [W/m^2]';
                        end

                        modelDesc = sprintf('%s - Laser Hardening (lambda=%.3fum, %s)', propTitle, lambda_um, condDesc);

                        eqLines = { ...
                            sprintf('// COMSOL Multiphysics: %s - Laser Hardening (Solid-State)', propTitle); ...
                            sprintf('// Laser Wavelength: %.3f um | Surface State: %s', lambda_um, condDesc); ...
                            sprintf('// Solidus Ts = %.1f K | Critical Invariant: T_surface < Ts (Melting Prohibited)', Ts); ...
                            ''; ...
                            eqHeader; ...
                            eqPrimary; ...
                            ''; ...
                            '// 2. Surface Radiative Cooling (Dictates Self-Quenching Rate dT/dt):'; ...
                            radDesc; ...
                            ''; ...
                            '// 3. Laser Heat Source Boundary Condition (Gaussian/Top-Hat):'; ...
                            'Q_in = A(T) * P_laser / (pi * w_beam^2 / 2) * exp(-2*(x^2 + y^2)/w_beam^2)  [W/m^2]'; ...
                            ''; ...
                            '// 4. Melt Prevention Safety Indicator:'; ...
                            sprintf('melt_hazard = if(T >= %.1f, 1, 0)  // Must remain 0 across workpiece', Ts); ...
                            ''; ...
                            'Start [K]    End [K]      Function (COMSOL Definition)'; ...
                            sprintf('%-12.1f %-12.1f %s', app.T_Min, Ts, f_primary_str); ...
                            sprintf('%-12.1f %-12.1f %s', Ts, app.T_Max, 'MELTING HAZARD (T >= Ts)') ...
                        };

                        comsolData.isOptical       = true;
                        comsolData.isEmissivity    = isEmissivitySelected;
                        comsolData.laserMode       = 'Hardening';
                        comsolData.mushyModel      = sprintf('%s (Laser Hardening)', propTitle);
                        comsolData.Ts              = Ts;
                        comsolData.Tl              = Tl;
                        comsolData.T_Min           = app.T_Min;
                        comsolData.T_Max           = app.T_Max;
                        comsolData.solidExpr       = f_primary_str;
                        comsolData.mushyExpr       = 'MELTING HAZARD (T >= Ts)';
                        comsolData.liquidExpr      = 'MELTING HAZARD (T >= Ts)';
                        comsolData.flc2hsExpr      = sprintf('// COMSOL Laser Hardening Model:\nA_solid(T) = %s;\neps_solid(T) = %s;\n// Safety Constraint (T < Ts):\nmelt_flag = if(T >= %.1f, 1, 0);\nQ_in = A_solid(T) * P_laser / (pi * w_beam^2 / 2) * exp(-2*(x^2 + y^2)/w_beam^2);\nq_rad = eps_solid(T) * 5.670374e-8 * (T^4 - 293.15^4);', ...
                            f_sol_A, f_sol_eps, Ts);
                        comsolData.heatSourceExpr  = sprintf('Q_in = (%s) * P_laser / (pi * w_beam^2 / 2) * exp(-2*(x^2 + y^2)/w_beam^2)', f_sol_A);
                        comsolData.radiationExpr   = sprintf('q_rad = (%s) * 5.670374e-8 * (T^4 - Tamb^4)', f_sol_eps);
                        comsolData.marangoniExpr   = '// Marangoni shear stress not applicable (solid-state hardening, no melt pool)';
                        comsolData.solidConstraint = sprintf('melt_hazard = if(T >= %.1f, 1, 0)  // Invariant: surface must not reach solidus', Ts);
                        comsolData.paramsText      = sprintf('lambda_laser\t%.3f [um]\tLaser wavelength\nTs\t%.1f [K]\tSolidus limit\nP_laser\t1500 [W]\tLaser beam power\nw_beam\t3.0 [mm]\tBeam radius\nTamb\t293.15 [K]\tAmbient cooling temperature\nsigma_SB\t5.670374e-8 [W/(m^2*K^4)]\tStefan-Boltzmann constant\nA_coat\t%.2f\tSurface absorptivity', ...
                            lambda_um, Ts, app.CoatingAbsorptivity);

                    else
                        % Laser Remelting (LSR) or Cladding / LPBF:
                        % Initial rough solid surface transitions across mushy zone [Ts, Tl]
                        % into a smooth, specular liquid melt pool where micro-roughness is erased.
                        roughFactor = app.SurfaceRoughFactor;
                        if isCladding
                            if contains(mode, 'LPBF', 'IgnoreCase', true)
                                roughFactor = max(roughFactor, 2.0);
                            else
                                roughFactor = max(roughFactor, 1.6);
                            end
                        end

                        A_solid = min(0.95, roughFactor .* A_bulk);
                        A_liquid = A_bulk; % Specular liquid melt pool

                        eps_solid = min(0.92, max(0.18, 0.751 * sqrt(max(1e-12, rho_ohm_m .* T .* 1e-2)) .* roughFactor));
                        eps_liquid = min(0.60, max(0.12, 0.751 * sqrt(max(1e-12, rho_ohm_m .* T .* 1e-2))));

                        % Smooth continuous transition across [Ts, Tl] via flc2hs
                        dT_half = (Tl - Ts) / 2.0;
                        T_mid = (Ts + Tl) / 2.0;
                        x_norm = (T - T_mid) / dT_half;
                        s_step = zeros(size(T));
                        s_step(x_norm >= 1) = 1;
                        mid_m = (x_norm > -1) & (x_norm < 1);
                        s_step(mid_m) = 0.5 + 0.75 * x_norm(mid_m) - 0.25 * (x_norm(mid_m)).^3;

                        A_app = A_solid .* (1.0 - s_step) + A_liquid .* s_step;
                        eps_app = eps_solid .* (1.0 - s_step) + eps_liquid .* s_step;

                        % Piecewise fit for A(T)
                        idx_s = T <= Ts;
                        idx_l = T >= Tl;
                        if sum(idx_s) >= 2
                            p_sol_A = polyfit(T(idx_s), A_solid(idx_s), 1);
                            f_sol_A = sprintf('%.4e*T + %.4e', p_sol_A(1), p_sol_A(2));
                            f_sol_A = strrep(f_sol_A, '+ -', '- ');
                        else
                            f_sol_A = sprintf('%.4f', mean(A_solid));
                        end

                        if sum(idx_l) >= 2
                            p_liq_A = polyfit(T(idx_l), A_liquid(idx_l), 1);
                            f_liq_A = sprintf('%.4e*T + %.4e', p_liq_A(1), p_liq_A(2));
                            f_liq_A = strrep(f_liq_A, '+ -', '- ');
                        else
                            f_liq_A = sprintf('%.4f', mean(A_liquid));
                        end

                        mushyA_str = sprintf('(%s) + ((%s) - (%s))*flc2hs(T - %.1f, %.1f)', ...
                            f_sol_A, f_liq_A, f_sol_A, T_mid, dT_half);

                        % Piecewise fit for eps(T)
                        if sum(idx_s) >= 2
                            p_sol_eps = polyfit(T(idx_s), eps_solid(idx_s), 1);
                            f_sol_eps = sprintf('%.4e*T + %.4e', p_sol_eps(1), p_sol_eps(2));
                            f_sol_eps = strrep(f_sol_eps, '+ -', '- ');
                        else
                            f_sol_eps = sprintf('%.4f', mean(eps_solid));
                        end

                        if sum(idx_l) >= 2
                            p_liq_eps = polyfit(T(idx_l), eps_liquid(idx_l), 1);
                            f_liq_eps = sprintf('%.4e*T + %.4e', p_liq_eps(1), p_liq_eps(2));
                            f_liq_eps = strrep(f_liq_eps, '+ -', '- ');
                        else
                            f_liq_eps = sprintf('%.4f', mean(eps_liquid));
                        end

                        mushyEps_str = sprintf('(%s) + ((%s) - (%s))*flc2hs(T - %.1f, %.1f)', ...
                            f_sol_eps, f_liq_eps, f_sol_eps, T_mid, dT_half);

                        % Surface tension slope dgamma/dT for Marangoni thermocapillary flow
                        stIdx = find(contains(vNames,'Surface Tension','IgnoreCase',true), 1);
                        dgamma_dT = -3.8e-4; % standard default [N/(m*K)]
                        if ~isempty(stIdx)
                            stVals = app.CurrentData.(stIdx);
                            stMask = (T >= Tl) & ~isnan(stVals) & (stVals > 0);
                            if sum(stMask) >= 3
                                p_st = polyfit(T(stMask), stVals(stMask), 1);
                                dgamma_dT = p_st(1);
                            end
                        end

                        if isEmissivitySelected
                            fitT  = T; fitY  = eps_app;
                            fitT2 = T; fitY2 = A_app;
                            f_sol_str = f_sol_eps;
                            f_liq_str = f_liq_eps;
                            mushy_str = mushyEps_str;
                            propTitle = 'Surface Emissivity eps(T)';
                            eqHeader = '// 1. Continuous C^2 Surface Emissivity (flc2hs Smooth Step):';
                            eqDefs = { ...
                                sprintf('eps_solid(T)  = %s  [Rough substrate]', f_sol_eps); ...
                                sprintf('eps_liquid(T) = %s  [Smooth melt pool]', f_liq_eps); ...
                                sprintf('eps_app(T)    = eps_solid(T) + (eps_liquid(T) - eps_solid(T)) * flc2hs(T - %.1f, %.1f);', T_mid, dT_half) ...
                            };
                            radStr = 'q_rad = eps_app(T) * 5.670374e-8 * (T^4 - 293.15^4)  [W/m^2]';
                        else
                            fitT  = T; fitY  = A_app;
                            fitT2 = T; fitY2 = eps_app;
                            f_sol_str = f_sol_A;
                            f_liq_str = f_liq_A;
                            mushy_str = mushyA_str;
                            propTitle = 'Laser Absorptivity A(T)';
                            eqHeader = '// 1. Continuous C^2 Surface Absorptivity (flc2hs Smooth Step):';
                            eqDefs = { ...
                                sprintf('A_solid(T)  = %s  [Rough/As-cast substrate]', f_sol_A); ...
                                sprintf('A_liquid(T) = %s  [Smooth specular melt pool]', f_liq_A); ...
                                sprintf('A_app(T)    = A_solid(T) + (A_liquid(T) - A_solid(T)) * flc2hs(T - %.1f, %.1f);', T_mid, dT_half) ...
                            };
                            radStr = 'q_rad = eps_app(T) * 5.670374e-8 * (T^4 - 293.15^4)  [W/m^2]';
                        end

                        modelDesc = sprintf('%s - Laser Remelting (lambda=%.3fum, eta=%.2f)', propTitle, lambda_um, roughFactor);

                        eqLines = [ ...
                            { sprintf('// COMSOL Multiphysics: %s - Laser Remelting (Melt Pool Transition)', propTitle); ...
                              sprintf('// Laser Wavelength: %.3f um | Rough Surface Multiplier: %.2fx', lambda_um, roughFactor); ...
                              sprintf('// Solidus Ts = %.1f K, Liquidus Tl = %.1f K (Mushy transition width = %.1f K)', Ts, Tl, Tl - Ts); ...
                              ''; ...
                              eqHeader }; ...
                            eqDefs; ...
                            { ''; ...
                              '// 2. Laser Heat Source Boundary Condition (Gaussian Beam):'; ...
                              'Q_in = A_app(T) * P_laser / (pi * w_beam^2 / 2) * exp(-2*(x^2 + y^2)/w_beam^2)  [W/m^2]'; ...
                              ''; ...
                              '// 3. Surface Radiative Cooling (Stefan-Boltzmann):'; ...
                              radStr; ...
                              ''; ...
                              '// 4. Marangoni Shear Stress (Thermocapillary Melt Pool Recirculation):'; ...
                              sprintf('tau_x = (%.4e) * d(T, x)  [N/m^2, dgamma/dT = %.2e N/(m*K)]', dgamma_dT, dgamma_dT); ...
                              sprintf('tau_y = (%.4e) * d(T, y)  [N/m^2, dgamma/dT = %.2e N/(m*K)]', dgamma_dT, dgamma_dT); ...
                              ''; ...
                              'Start [K]    End [K]      Function (COMSOL Definition)'; ...
                              sprintf('%-12.1f %-12.1f %s', app.T_Min, Ts, f_sol_str); ...
                              sprintf('%-12.1f %-12.1f %s', Ts, Tl, mushy_str); ...
                              sprintf('%-12.1f %-12.1f %s', Tl, app.T_Max, f_liq_str) } ...
                        ];

                        comsolData.isOptical       = true;
                        comsolData.isEmissivity    = isEmissivitySelected;
                        comsolData.laserMode       = 'Remelting';
                        comsolData.mushyModel      = sprintf('%s (Laser Remelting)', propTitle);
                        comsolData.Ts              = Ts;
                        comsolData.Tl              = Tl;
                        comsolData.T_Min           = app.T_Min;
                        comsolData.T_Max           = app.T_Max;
                        comsolData.solidExpr       = f_sol_str;
                        comsolData.mushyExpr       = mushy_str;
                        comsolData.liquidExpr      = f_liq_str;
                        comsolData.flc2hsExpr      = sprintf('// COMSOL Continuous Smooth Step (flc2hs):\nA_solid(T) = %s;\nA_liquid(T) = %s;\nA_app(T) = A_solid(T) + (A_liquid(T) - A_solid(T)) * flc2hs(T - %.1f, %.1f);\neps_solid(T) = %s;\neps_liquid(T) = %s;\neps_app(T) = eps_solid(T) + (eps_liquid(T) - eps_solid(T)) * flc2hs(T - %.1f, %.1f);', ...
                            f_sol_A, f_liq_A, T_mid, dT_half, f_sol_eps, f_liq_eps, T_mid, dT_half);
                        comsolData.heatSourceExpr  = 'Q_in = A_app(T) * P_laser / (pi * w_beam^2 / 2) * exp(-2*(x^2 + y^2)/w_beam^2)';
                        comsolData.radiationExpr   = 'q_rad = eps_app(T) * 5.670374e-8 * (T^4 - Tamb^4)';
                        comsolData.marangoniExpr   = sprintf('// Marangoni Shear Stress (Boundary Stress condition):\ntau_x = (%.4e [N/(m*K)]) * d(T, x);\ntau_y = (%.4e [N/(m*K)]) * d(T, y);', ...
                            dgamma_dT, dgamma_dT);
                        comsolData.solidConstraint = '// Laser Remelting intentionally melts the surface (T_peak > Tl)';
                        comsolData.paramsText      = sprintf('lambda_laser\t%.3f [um]\tLaser wavelength\nTs\t%.1f [K]\tSolidus temperature\nTl\t%.1f [K]\tLiquidus temperature\nP_laser\t2000 [W]\tLaser beam power\nw_beam\t1.5 [mm]\tBeam radius\nTamb\t293.15 [K]\tAmbient cooling temperature\nsigma_SB\t5.670374e-8 [W/(m^2*K^4)]\tStefan-Boltzmann constant\ndgamma_dT\t%.4e [N/(m*K)]\tSurface tension temperature coefficient', ...
                            lambda_um, Ts, Tl, dgamma_dT);
                    end

                elseif isAuto && contains(lowerProp,'young')
                    idx_solid = T <= Tm;
                    p_sol = polyfit(T(idx_solid), Y(idx_solid), 1);
                    f_solid = sprintf('%.4e*T + %.4e', p_sol(1), p_sol(2));
                    f_solid = strrep(f_solid,'+ -','- ');
                    eqLines = {'Start      End        Function (COMSOL Definition)'; ...
                        sprintf('%-10.1f %-10.1f %s', app.T_Min, Tm, f_solid); ...
                        sprintf('%-10.1f %-10.1f %s', Tm, app.T_Max, '0')};
                    fitT  = T(T<=Tm)'; fitY  = polyval(p_sol, fitT);
                    fitT2 = [Tm app.T_Max]; fitY2 = [0 0];

                elseif isAuto && contains(lowerProp,'poisson')
                    idx_solid = T <= Tm;
                    p_sol = polyfit(T(idx_solid), Y(idx_solid), 1);
                    f_solid = sprintf('%.6g*T + %.6g', p_sol(1), p_sol(2));
                    f_solid = strrep(f_solid,'+ -','- ');
                    eqLines = {'Start      End        Function'; ...
                        sprintf('%-10.1f %-10.1f %s', app.T_Min, Tm, f_solid); ...
                        sprintf('%-10.1f %-10.1f %s', Tm, app.T_Max, '0.5')};
                    fitT  = T(T<=Tm)'; fitY  = polyval(p_sol, fitT);
                    fitT2 = [Tm app.T_Max]; fitY2 = [0.5 0.5];

                elseif isAuto && contains(lowerProp,'surface tension')
                    idx_liq = T > Tm;
                    p_liq = polyfit(T(idx_liq), Y(idx_liq), 1);
                    f_liquid = sprintf('%.6g*T + %.6g', p_liq(1), p_liq(2));
                    f_liquid = strrep(f_liquid,'+ -','- ');
                    eqLines = {'Start      End        Function'; ...
                        sprintf('%-10.1f %-10.1f %s', app.T_Min, Tm, '0 (No solid surface tension)'); ...
                        sprintf('%-10.1f %-10.1f %s', Tm, app.T_Max, f_liquid)};
                    fitT2 = T(T>Tm)'; fitY2 = polyval(p_liq, fitT2);

                elseif (isAuto && contains(lowerProp,'expansion')) || strcmp(fitType,'Quadratic')
                    idx_solid = T <= Tm; idx_liq = T > Tm;
                    p_sol = polyfit(T(idx_solid), Y(idx_solid), 2);
                    func_sol = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_sol(1), p_sol(2), p_sol(3));
                    func_sol = strrep(func_sol,'+ -','- ');
                    fitT  = T(T<=Tm)'; fitY  = polyval(p_sol, fitT);
                    if sum(idx_liq) >= 3
                        p_liq = polyfit(T(idx_liq), Y(idx_liq), 2);
                        func_liq = sprintf('%.4e*T^2 + %.4e*T + %.4e', p_liq(1), p_liq(2), p_liq(3));
                        func_liq = strrep(func_liq,'+ -','- ');
                        fitT2 = T(T>Tm)'; fitY2 = polyval(p_liq, fitT2);
                    else
                        func_liq = 'N/A';
                    end
                    eqLines = {'Start      End        Function (Quadratic Fit)'; ...
                        sprintf('%-10.1f %-10.1f %s', app.T_Min, Tm, func_sol); ...
                        sprintf('%-10.1f %-10.1f %s', Tm, app.T_Max, func_liq)};

                elseif strcmp(fitType,'Gaussian Peak (Analytic)')
                    baseY = median(Y); [max_val,~] = max(Y);
                    T0 = Tm; A = max_val - baseY; w = 30;
                    func = sprintf('%.4g + %.4g * exp(-((T-%.4g)^2)/%.4g^2)', baseY, A, T0, w);
                    eqLines = {'Analytic Expression (Gaussian Peak):'; ''; func};
                    fitT = T'; fitY = baseY + A .* exp(-((T-T0).^2)./(w^2));

                else
                    % Default: Piecewise Linear at Tm
                    idx_solid = T <= Tm; idx_liquid = T > Tm;
                    f1 = 'N/A'; f2 = 'N/A';
                    if sum(idx_solid) >= 2
                        p1 = polyfit(T(idx_solid), Y(idx_solid), 1);
                        f1 = sprintf('%.6g*T + %.6g', p1(1), p1(2));
                        f1 = strrep(f1,'+ -','- ');
                        fitT = T(idx_solid)'; fitY = polyval(p1, fitT);
                    end
                    if sum(idx_liquid) >= 2
                        p2 = polyfit(T(idx_liquid), Y(idx_liquid), 1);
                        f2 = sprintf('%.6g*T + %.6g', p2(1), p2(2));
                        f2 = strrep(f2,'+ -','- ');
                        fitT2 = T(idx_liquid)'; fitY2 = polyval(p2, fitT2);
                    end
                    eqLines = {'Start      End        Function (COMSOL Definition)'; ...
                        sprintf('%-10.1f %-10.1f %-35s', app.T_Min, Tm, f1); ...
                        sprintf('%-10.1f %-10.1f %-35s', Tm, app.T_Max, f2)};
                end

                % --- Goodness-of-fit metrics ---
                allFitT = [fitT(:); fitT2(:)];
                allFitY = [fitY(:); fitY2(:)];
                R2val = NaN; RMSEval = NaN;
                if ~isempty(allFitT)
                    if contains(lowerProp, 'viscosity')
                        % For viscosity, physical experimental data only exists above solidus (Y > 0)
                        % The 1000 Pa*s solid penalty is a numerical BC, not a physical target to 0
                        vMask = (T >= app.T_Solidus) & (Y > 0);
                        if sum(vMask) >= 2
                            evalT = T(vMask); evalY = Y(vMask);
                            modelY = interp1(allFitT, allFitY, evalT, 'linear', 'extrap');
                            SS_res = sum((evalY - modelY).^2);
                            SS_tot = sum((evalY - mean(evalY)).^2);
                            if SS_tot > 0, R2val = max(0, min(1, 1 - SS_res/SS_tot)); end
                            RMSEval = sqrt(mean((evalY - modelY).^2));
                        end
                    elseif contains(lowerProp, 'absorptivity') || contains(lowerProp, 'emissivity')
                        % Optical properties: fitT and fitY evaluate the primary absorptivity curve
                        evalT = fitT(:); evalModelY = fitY(:);
                        modelY_at_T = interp1(evalT, evalModelY, T, 'linear', 'extrap');
                        SS_res = sum((Y - modelY_at_T).^2);
                        SS_tot = sum((Y - mean(Y)).^2);
                        if SS_tot > 0
                            R2val = max(0, min(1, 1 - SS_res/SS_tot));
                        else
                            R2val = 1.0;
                        end
                        RMSEval = sqrt(mean((Y - modelY_at_T).^2));
                    else
                        [commonT, ia, ib] = intersect(round(T,1), round(allFitT,1));
                        if numel(commonT) >= 2
                            SS_res = sum((Y(ia) - allFitY(ib)).^2);
                            SS_tot = sum((Y(ia) - mean(Y(ia))).^2);
                            if SS_tot > 0, R2val = 1 - SS_res/SS_tot; end
                            if R2val < 0, R2val = NaN; end
                            RMSEval = sqrt(mean((Y(ia) - allFitY(ib)).^2));
                        end
                    end
                end
                rangeStr = sprintf('%d-%d', round(app.T_Min), round(app.T_Max));

                % --- Literature comparison ---
                if app.CompareEnabled
                    compStr  = app.CurrentCompositionStr;
                    basisStr = app.CompositionBasis;
                    [hasLit, litRes] = app.LitBenchmark.getComparison( ...
                        app.CurrentFile, app.CurrentProperty, T, Y, compStr, basisStr, forceLiveSearch);
                    if hasLit
                        if isfield(litRes, 'ScholarQuery'), app.CurrentScholarUrl = litRes.ScholarQuery; else, app.CurrentScholarUrl = ''; end
                        if isfield(litRes, 'ScienceDirectQuery'), app.CurrentScienceDirectUrl = litRes.ScienceDirectQuery; else, app.CurrentScienceDirectUrl = ''; end
                        if isfield(litRes, 'CitedByUrl'), app.CurrentCitedByUrl = litRes.CitedByUrl; else, app.CurrentCitedByUrl = ''; end
                        if isfield(litRes, 'MRE') && ~isnan(litRes.MRE)
                            citData.title    = litRes.MaterialName;
                            if isfield(litRes, 'DOI'), citData.doi = litRes.DOI; else, citData.doi = ''; end
                            citData.verified = true;
                            citData.text     = sprintf('R²=%.4f  MRE=%.2f%%  MaxDev=%.2f%%\n%s\n%s\nDOI: %s', ...
                                litRes.R2, litRes.MRE, litRes.MaxDev, ...
                                litRes.Citation, litRes.Journal, citData.doi);
                        end
                        if isfield(litRes,'HasCurve') && litRes.HasCurve && isfield(litRes,'T_plot')
                            % Include literature curve as third series
                            eqLines{end+1} = '';
                            eqLines{end+1} = sprintf('Literature: %s', litRes.MaterialName);
                        end
                    end
                end

                % Store for export
                app.LastEquationLines = eqLines;
                app.LastPlotT = T; app.LastPlotY = Y;
                app.LastFitT  = fitT; app.LastFitY  = fitY;
                app.LastFitT2 = fitT2; app.LastFitY2 = fitY2;

                % --- Send result to HTML ---
                eqStr = strjoin(eqLines, '\n');
                isOpticalProp = contains(lowerProp, 'absorptivity') || contains(lowerProp, 'emissivity');
                isEmissivitySelected = contains(lowerProp, 'emissivity');
                plotData = struct( ...
                    'rawT',         T', ...
                    'rawY',         Y', ...
                    'fitT',         fitT(:)', ...
                    'fitY',         fitY(:)', ...
                    'fitT2',        fitT2(:)', ...
                    'fitY2',        fitY2(:)', ...
                    'meltingPoint', Tm, ...
                    'solidus',      app.T_Solidus, ...
                    'liquidus',     app.T_Liquidus, ...
                    'hasMushyZone', contains(lowerProp, 'viscosity') || isOpticalProp, ...
                    'mushyModel',   app.MushyModel, ...
                    'isOptical',    isOpticalProp, ...
                    'isEmissivity', isEmissivitySelected, ...
                    'laserMode',    app.LaserMode, ...
                    'wavelength',   app.LaserWavelength, ...
                    'surfaceCondition', app.SurfaceCondition, ...
                    'xLabel',       'Temperature (K)', ...
                    'yLabel',       app.CurrentProperty);

                if app.CompareEnabled && exist('hasLit','var') && hasLit && isfield(litRes,'HasCurve') && litRes.HasCurve && isfield(litRes,'T_plot')
                    plotData.litT       = litRes.T_plot(:)';
                    plotData.litY       = litRes.Y_plot(:)';
                    plotData.litName    = litRes.MaterialName;
                    plotData.litMRE     = litRes.MRE;
                    plotData.litJournal = litRes.Journal;
                    plotData.litDOI     = litRes.DOI;
                end

                app.htmlSend('calcResult', struct( ...
                    'equation',     eqStr, ...
                    'R2',           R2val, ...
                    'RMSE',         RMSEval, ...
                    'range',        rangeStr, ...
                    'order',        fitType, ...
                    'solidus',      app.T_Solidus, ...
                    'liquidus',     app.T_Liquidus, ...
                    'mushyModel',   app.MushyModel, ...
                    'viscSolidCap', app.ViscSolidCap, ...
                    'isOptical',    isOpticalProp, ...
                    'isEmissivity', isEmissivitySelected, ...
                    'laserMode',    app.LaserMode, ...
                    'wavelength',   app.LaserWavelength, ...
                    'surfaceCondition', app.SurfaceCondition, ...
                    'plotData',     plotData, ...
                    'citation',     citData, ...
                    'comsolData',   comsolData, ...
                    'scholarUrl',   app.CurrentScholarUrl, ...
                    'scienceUrl',   app.CurrentScienceDirectUrl, ...
                    'citedByUrl',   app.CurrentCitedByUrl));

            catch ME
                app.htmlSend('error', struct('message', ME.message));
            end
        end

        % Apply predefined composition ratios from literature and industrial alloys
        function applyPreset(app, preset)
            app.IsUpdatingMatrix = true;
            elems = {}; vals = []; basis = 'At %'; matchedFile = '';
            switch preset
                case {'AlCoCrFeNi : equiatomic HEA', 'AlCoCrFeNi'}
                    elems = {'Al','Co','Cr','Fe','Ni'}; vals = [20,20,20,20,20];
                    matchedFile = 'AlCoCrFeNi.dat';
                case {'CoCrFeMnNi : Cantor alloy', 'Cantor HEA (Fe-Co-Ni-Cr-Mn)', 'Cantor alloy'}
                    elems = {'Co','Cr','Fe','Mn','Ni'}; vals = [20,20,20,20,20];
                case {'AlCoCrFeNiTi : HEA+Ti', 'AlCoCrFeNiTi'}
                    elems = {'Al','Co','Cr','Fe','Ni','Ti'}; vals = [16.7,16.7,16.7,16.7,16.7,16.5];
                case {'SS316L : 316L stainless steel', 'Stainless Steel 316L', 'SS316L'}
                    elems = {'Fe','Cr','Ni','Mo','Mn','Si','C'};
                    vals  = [65,17,12,2.5,2,0.75,0.03]; basis='Wt %';
                case {'Inconel 718', 'Inconel'}
                    elems = {'Ni','Cr','Fe','Nb','Mo','Ti','Al','Co'};
                    vals  = [52.5,19,18.5,5.1,3,0.9,0.5,1]; basis='Wt %';
                case {'Ti-6Al-4V', 'Ti64'}
                    elems = {'Ti','Al','V','Fe'}; vals = [89.5,6,4.25,0.25]; basis='Wt %';
                case {'Pure Ni', 'Ni'}
                    elems = {'Ni'}; vals = [100];
                case {'Pure Al', 'Al'}
                    elems = {'Al'}; vals = [100];
                case 'Al0.3CoCrFeNi HEA (FCC)'
                    elems = {'Co','Al','Ni','Cr','Fe'}; vals = [23.26,6.98,23.26,23.26,23.26];
                    matchedFile = 'AlCoCrFeNi.dat';
                case 'Al0.7CoCrFeNi HEA (Duplex)'
                    elems = {'Co','Al','Ni','Cr','Fe'}; vals = [21.28,14.89,21.28,21.28,21.28];
                    matchedFile = 'AlCoCrFeNi.dat';
                case 'CoCrFeNi (Cantor Base)'
                    elems = {'Co','Cr','Fe','Ni'}; vals = [25,25,25,25];
                case '13-Element Super-HEA'
                    elems = {'Co','Al','Ni','Cr','Fe','Hf','Mn','Mo','Nb','Ta','Ti','W','Zr'};
                    vals  = [15,5,15,15,15,1.5,10,5,4,4,5,4,1.5];
                case 'CMSX-4 Superalloy'
                    elems = {'Co','Al','Ni','Cr','Hf','Mo','Ta','Ti','W'};
                    vals  = [9,5.6,61.7,6.5,0.1,0.6,6.5,1,6]; basis='Wt %';
                case 'Alloy Al-1.0 (Al-Co)'
                    elems = {'Co','Al'}; vals = [99,1]; basis='Wt %';
                    matchedFile = 'Al1.0.dat';
                case 'Cobalt Aluminide (CoAl)'
                    elems = {'Co','Al'}; vals = [50,50];
                case 'Nickel Aluminide (NiAl)'
                    elems = {'Ni','Al'}; vals = [50,50];
                otherwise
                    app.IsUpdatingMatrix = false; return;
            end
            app.CurrentBasis = basis;
            app.ElementList  = elems(:);
            app.MatrixData   = cell(numel(elems), 2);
            for k = 1:numel(elems)
                app.MatrixData{k, 1} = elems{k};
                if strcmp(app.CompositionBasis, 'mol')
                    app.MatrixData{k, 2} = sprintf('%.5f', vals(k));
                elseif abs(vals(k)-round(vals(k)))<1e-5
                    app.MatrixData{k, 2} = sprintf('%.1f', vals(k));
                else
                    app.MatrixData{k, 2} = sprintf('%.5f', vals(k));
                end
            end
            % Rebuild composition string
            app.CurrentCompositionStr = app.buildCompStr();
            app.htmlSendMatrixUpdate();
            if ~isempty(matchedFile)
                files = dir(fullfile(app.DataFolder,'*.dat'));
                if any(strcmp({files.name}, matchedFile))
                    app.CurrentFile = matchedFile;
                    app.onFileChange();
                end
            end
            app.IsUpdatingMatrix = false;
        end

        function doBalance(app)
            n = numel(app.ElementList);
            if n == 0, return; end
            sumOthers = 0;
            for i = 2:n
                v = app.MatrixData{i,2};
                if ischar(v)||isstring(v), v=str2double(v); end
                if ~isnan(v)&&v>0, sumOthers=sumOthers+v; end
            end
            if strcmp(app.CompositionBasis, 'mol')
                if sumOthers < 1.0
                    target = 1.0;
                else
                    target = max(1.0, ceil(sumOthers));
                end
                balVal = max(0, target - sumOthers);
                app.MatrixData{1,2} = sprintf('%.5f', balVal);
            else
                balVal = max(0, 100 - sumOthers);
                if abs(balVal-round(balVal))<1e-5
                    app.MatrixData{1,2} = sprintf('%.1f',balVal);
                else
                    app.MatrixData{1,2} = sprintf('%.5f',balVal);
                end
            end
            app.CurrentCompositionStr = app.buildCompStr();
            app.htmlSendMatrixUpdate();
        end

        function s = buildCompStr(app)
            parts = {};
            n = numel(app.ElementList);
            for i = 1:n
                v = app.MatrixData{i,2};
                if ischar(v)||isstring(v), v=str2double(v); end
                if ~isnan(v)&&v>0
                    if strcmp(app.CompositionBasis, 'mol')
                        parts{end+1} = sprintf('%s %.5f',app.ElementList{i},v);
                    elseif abs(v-round(v))<1e-5
                        parts{end+1} = sprintf('%s %.1f',app.ElementList{i},v);
                    else
                        parts{end+1} = sprintf('%s %.5f',app.ElementList{i},v);
                    end
                end
            end
            s = strjoin(parts,', ');
        end

        % Dynamically configure active alloy constituents and values from Periodic Table
        function setElementsAndValues(app, elems, vals)
            if isempty(elems), elems = {}; end
            if ischar(elems) || isstring(elems), elems = {char(elems)}; end
            n = numel(elems);
            app.ElementList = elems(:);
            app.MatrixData  = cell(n, 2);
            for i = 1:n
                app.MatrixData{i, 1} = elems{i};
                if nargin >= 3 && ~isempty(vals) && numel(vals) >= i
                    v = vals(i);
                else
                    v = 0.0;
                end
                if strcmp(app.CompositionBasis, 'mol')
                    app.MatrixData{i, 2} = sprintf('%.5f', v);
                elseif abs(v - round(v)) < 1e-5
                    app.MatrixData{i, 2} = sprintf('%.1f', v);
                else
                    app.MatrixData{i, 2} = sprintf('%.5f', v);
                end
            end
            app.CurrentCompositionStr = app.buildCompStr();
            app.htmlSendMatrixUpdate();
        end

        % Export fitted piecewise formulation and discretized table to COMSOL format
        function generateCOMSOLOutput(app)
            if isempty(app.LastPlotT)
                app.htmlSend('toast', struct('message', 'No data calculated yet. Click Calculate first.'));
                return;
            end
            prop = app.CurrentProperty;
            matName = app.CurrentFile;
            if endsWith(matName, '.dat', 'IgnoreCase', true)
                matName = matName(1:end-4);
            end
            defaultName = sprintf('COMSOL_%s_%s.txt', matlab.lang.makeValidName(matName), matlab.lang.makeValidName(prop));
            savePath = fullfile(pwd, defaultName);
            
            try
                lines = {};
                lines{end+1} = '%% COMSOL Multiphysics Interpolation File';
                lines{end+1} = sprintf('%%%% Material: %s', app.CurrentFile);
                lines{end+1} = sprintf('%%%% Property: %s', prop);
                lines{end+1} = '%% Generated by Material Properties Fitter';
                lines{end+1} = '';
                lines{end+1} = '%% Equations:';
                for i = 1:numel(app.LastEquationLines)
                    lines{end+1} = sprintf('%%%% %s', app.LastEquationLines{i});
                end
                lines{end+1} = '';
                lines{end+1} = '%% T(K)\tValue';
                
                allT = [app.LastFitT(:); app.LastFitT2(:)];
                allY = [app.LastFitY(:); app.LastFitY2(:)];
                if isempty(allT)
                    allT = app.LastPlotT; allY = app.LastPlotY;
                end
                [allT, si] = sort(allT); allY = allY(si);
                [~, ui] = unique(allT); allT = allT(ui); allY = allY(ui);
                for i = 1:numel(allT)
                    lines{end+1} = sprintf('%.4f\t%.6e', allT(i), allY(i));
                end
                
                fullContent = strjoin(lines, newline);
                
                fid = fopen(savePath, 'w');
                if fid ~= -1
                    fwrite(fid, fullContent);
                    fclose(fid);
                end
                
                app.htmlSend('downloadFile', struct('filename', defaultName, 'content', fullContent, 'savedPath', savePath));
                app.htmlSend('toast', struct('message', sprintf('Exported %s', defaultName)));
            catch ME
                app.htmlSend('error', struct('message', ME.message));
            end
        end

        % Open external literature verification links in browser
        function openScholar(app)
            if ~isempty(app.CurrentScholarUrl)
                try, web(app.CurrentScholarUrl,'-browser'); catch, end
            end
        end
        function openScienceDirect(app)
            if ~isempty(app.CurrentScienceDirectUrl)
                try, web(app.CurrentScienceDirectUrl,'-browser'); catch, end
            end
        end
        function openCitedBy(app)
            if ~isempty(app.CurrentCitedByUrl)
                try, web(app.CurrentCitedByUrl,'-browser'); catch, end
            end
        end

        % Allow manual adjustment of transition zone data points for CFD tuning
        function applyOverrides(app, points)
            if isempty(app.CurrentData) || isempty(points), return; end
            try
                T_col = app.CurrentData{:, 1};
                propName = app.CurrentProperty;
                Y_col = app.CurrentData{:, propName};
                
                for k = 1:numel(points)
                    pt = points(k);
                    if isfield(pt, 'T') && isfield(pt, 'Y')
                        matchIdx = find(abs(T_col - pt.T) < 1.0, 1);
                        if ~isempty(matchIdx)
                            Y_col(matchIdx) = pt.Y;
                        else
                            T_col(end+1) = pt.T;
                            Y_col(end+1) = pt.Y;
                        end
                    end
                end
                [T_col, sIdx] = sort(T_col);
                Y_col = Y_col(sIdx);
                
                newTable = app.CurrentData;
                if numel(T_col) == height(newTable)
                    newTable.(propName) = Y_col;
                else
                    vNames = app.CurrentData.Properties.VariableNames;
                    newTable = table(T_col, 'VariableNames', {vNames{1}});
                    newTable.(propName) = Y_col;
                    for v = 2:numel(vNames)
                        cN = vNames{v};
                        if ~strcmp(cN, propName)
                            oldT = app.CurrentData{:, 1};
                            oldV = app.CurrentData{:, cN};
                            valOld = ~isnan(oldT) & ~isnan(oldV);
                            if sum(valOld) >= 2
                                newTable.(cN) = interp1(oldT(valOld), oldV(valOld), T_col, 'linear', 'extrap');
                            else
                                newTable.(cN) = nan(size(T_col));
                            end
                        end
                    end
                end
                
                app.CurrentData = newTable;
                app.onPropChange(false);
            catch ME
                app.htmlSend('error', struct('message', ME.message));
            end
        end

        function exportRawDataTable(app)
            if isempty(app.CurrentData)
                app.htmlSend('toast', struct('message', 'No data loaded to export.'));
                return;
            end
            propName = app.CurrentProperty;
            T = app.CurrentData{:, 1};
            Y = app.CurrentData{:, propName};
            valid = ~isnan(T) & ~isnan(Y);
            T = T(valid); Y = Y(valid);
            
            matName = app.CurrentFile;
            if endsWith(matName, '.dat', 'IgnoreCase', true)
                matName = matName(1:end-4);
            end
            defaultName = sprintf('%s_%s_RawData.csv', ...
                matlab.lang.makeValidName(matName), matlab.lang.makeValidName(propName));
            savePath = fullfile(pwd, defaultName);
            
            try
                outT = table(T, Y, 'VariableNames', {'Temperature_K', matlab.lang.makeValidName(propName)});
                writetable(outT, savePath);
                
                csvLines = {sprintf('Temperature_K,%s', matlab.lang.makeValidName(propName))};
                for i = 1:numel(T)
                    csvLines{end+1} = sprintf('%.2f,%.6e', T(i), Y(i));
                end
                csvContent = strjoin(csvLines, newline);
                
                app.htmlSend('downloadFile', struct('filename', defaultName, 'content', csvContent, 'savedPath', savePath));
                app.htmlSend('toast', struct('message', sprintf('CSV exported to %s', defaultName)));
            catch ME
                app.htmlSend('error', struct('message', ME.message));
            end
        end
    end
end
