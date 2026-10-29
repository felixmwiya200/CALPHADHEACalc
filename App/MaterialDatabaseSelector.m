classdef MaterialDatabaseSelector
    % MaterialDatabaseSelector - Multi-Alloy Database Architecture & Startup Selector
    % Implements the comprehensive database catalog matching the standard materials
    % engineering database taxonomy:
    %   1. High Entropy Alloys (Compacted Unified Database)
    %   2. Thermal Spray Coatings (Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 As-Sprayed)
    %   3. Aluminium Alloy
    %   4. Magnesium Alloy
    %   5. Cast Iron
    %   6. General Steel
    %   7. Stainless Steel
    %   8. Cobalt Alloy
    %   9. Nickel Based Superalloy
    %  10. NiFe Based Superalloy
    %  11. Single Crystal
    %  12. Titanium Alloy
    %  13. Zirconium Alloy
    %  14. Solder Alloy
    %
    % Lead Materials Engineering Suite: CALPHADHEACalc
    % Authors: Felix Mwiya & Prof. Dr. Sheela Singh, SRM University-AP (2026)

    methods (Static)

        % =========================================================================
        % 1. MASTER ALLOY DATABASE CATALOG
        % =========================================================================
        function list = getDatabaseList()
            % Returns the ordered cell array of database names matching the catalog
            list = { ...
                'High Entropy Alloys', ...
                'Thermal Spray Coatings', ...
                'Aluminium Alloy', ...
                'Magnesium Alloy', ...
                'Cast Iron', ...
                'General Steel', ...
                'Stainless Steel', ...
                'Cobalt Alloy', ...
                'Nickel Based Superalloy', ...
                'NiFe Based Superalloy', ...
                'Single Crystal', ...
                'Titanium Alloy', ...
                'Zirconium Alloy', ...
                'Solder Alloy' ...
            };
        end

        % =========================================================================
        % 2. GET DATABASE SPECIFICATION & DEFAULT ALLOY
        % =========================================================================
        function spec = getDatabaseSpec(dbName)
            % Returns configuration, default alloy, chemistry and parameters for the selected DB
            dbName = strtrim(char(dbName));
            spec = struct();
            spec.Name = dbName;
            spec.Basis = 'wt%';

            switch dbName
                case 'High Entropy Alloys'
                    spec.Name = 'High Entropy Alloys';
                    spec.Basis = 'at%';
                    spec.DefaultAlloy = 'CoCrFeMnNi (Cantor Alloy)';
                    spec.Elements = {'Co', 'Cr', 'Fe', 'Mn', 'Ni'};
                    spec.Fractions = [0.20, 0.20, 0.20, 0.20, 0.20];
                    spec.Category = 'Concentrated Multi-Principal Element Alloys (MPEAs)';
                    spec.Description = 'Compacted master database of 51 HEA archetypes, 22 experimental benchmarks, 12,427 literature compositions, and SGTE unaries.';
                    spec.PrimaryPhases = {'FCC_A1', 'BCC_A2', 'B2', 'Sigma', 'Liquid'};

                case 'Thermal Spray Coatings'
                    spec.Name = 'Thermal Spray Coatings';
                    spec.Basis = 'wt%';
                    spec.DefaultAlloy = 'Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65 (As-Sprayed)';
                    spec.Elements = {'Ni', 'Cr', 'Si', 'Fe', 'B', 'C'};
                    spec.Fractions = [0.7161, 0.1527, 0.0465, 0.0447, 0.0332, 0.0068];
                    spec.Category = 'Self-Fluxing Hardfacing & Thermal Spray Coatings';
                    spec.Description = 'Dedicated experimental database for Ni-Cr-Fe-B-Si-C coatings in the as-sprayed condition (HVOF, APS, flame spray). Complete with measured microhardness (745 HV), porosity (1.8%), bond strength (58.4 MPa), and corrosion rates.';
                    spec.PrimaryPhases = {'gamma-Ni (FCC)', 'CrB (Orthorhombic)', 'Cr2B', 'Cr7C3', 'Ni3Si', 'Liquid'};

                case 'Aluminium Alloy'
                    spec.DefaultAlloy = 'AA 7075-T6 (Al-5.6Zn-2.5Mg-1.6Cu)';
                    spec.Elements = {'Al', 'Zn', 'Mg', 'Cu', 'Cr'};
                    spec.Fractions = [0.897, 0.056, 0.025, 0.016, 0.0023];
                    spec.Category = 'Wrought & Cast Aluminum Aerospace Alloys';
                    spec.Description = 'Precipitation-hardenable lightweight structural alloys. Calibrated for eta-prime (MgZn2) strengthening, GP zones, and liquidus/solidus freezing intervals.';
                    spec.PrimaryPhases = {'FCC_Al', 'MgZn2 (eta)', 'Al2CuMg (S-phase)', 'Al7Cu2Fe', 'Liquid'};

                case 'Magnesium Alloy'
                    spec.DefaultAlloy = 'AZ91D (Mg-9.0Al-0.7Zn-0.2Mn)';
                    spec.Elements = {'Mg', 'Al', 'Zn', 'Mn'};
                    spec.Fractions = [0.901, 0.090, 0.007, 0.002];
                    spec.Category = 'Ultra-Lightweight Structural Alloys';
                    spec.Description = 'Hexagonal close-packed (HCP) magnesium casting and wrought alloys, featuring Mg17Al12 intermetallic phase modeling.';
                    spec.PrimaryPhases = {'HCP_Mg', 'Mg17Al12 (beta)', 'Al8Mn5', 'Liquid'};

                case 'Cast Iron'
                    spec.DefaultAlloy = 'Ductile Nodular Iron 65-45-12 (Fe-3.6C-2.5Si-0.3Mn)';
                    spec.Elements = {'Fe', 'C', 'Si', 'Mn'};
                    spec.Fractions = [0.936, 0.036, 0.025, 0.003];
                    spec.Category = 'Ferrous Foundry Alloys & High-Carbon Systems';
                    spec.Description = 'Fe-C-Si ternary eutectic solidification, graphite flake/nodule nodularity models, pearlite/ferrite volume ratio prediction.';
                    spec.PrimaryPhases = {'Ferrite (BCC)', 'Austenite (FCC)', 'Graphite', 'Fe3C (Cementite)', 'Liquid'};

                case 'General Steel'
                    spec.DefaultAlloy = 'AISI 4340 Low-Alloy Structural Steel';
                    spec.Elements = {'Fe', 'Ni', 'Cr', 'Mn', 'Mo', 'Si', 'C'};
                    spec.Fractions = [0.957, 0.018, 0.008, 0.007, 0.0025, 0.0025, 0.004];
                    spec.Category = 'Carbon & Low-Alloy Construction Steels';
                    spec.Description = 'Quench-and-temper hardening models, martensite start (Ms) temperature calculation, hardenability bands, and pearlite/bainite kinetics.';
                    spec.PrimaryPhases = {'Ferrite (BCC)', 'Austenite (FCC)', 'Martensite', 'M23C6', 'Liquid'};

                case 'Stainless Steel'
                    spec.DefaultAlloy = 'AISI 316L Austenitic Stainless Steel';
                    spec.Elements = {'Fe', 'Cr', 'Ni', 'Mo', 'Mn', 'Si'};
                    spec.Fractions = [0.655, 0.170, 0.120, 0.025, 0.020, 0.010];
                    spec.Category = 'Corrosion & Acid Resistant Stainless Steels';
                    spec.Description = 'Schaeffler-Delong Cr-Ni equivalent phase balance, PREN pitting resistance index, delta-ferrite solidification, and sigma phase susceptibility.';
                    spec.PrimaryPhases = {'Austenite (FCC)', 'Delta-Ferrite (BCC)', 'Sigma', 'M23C6', 'Liquid'};

                case 'Cobalt Alloy'
                    spec.DefaultAlloy = 'Stellite 21 / Co-28Cr-6Mo-0.25C (Wear Resistant)';
                    spec.Elements = {'Co', 'Cr', 'Mo', 'Ni', 'Fe', 'C'};
                    spec.Fractions = [0.6275, 0.280, 0.060, 0.025, 0.005, 0.0025];
                    spec.Category = 'High-Temperature Wear & Medical Implant Alloys';
                    spec.Description = 'Solid-solution FCC/HCP cobalt matrix reinforced by skeletal Cr/Mo carbides. High resistance to cavitation, galling, and hot corrosion.';
                    spec.PrimaryPhases = {'FCC_Co', 'HCP_Co', 'M7C3', 'M23C6', 'Liquid'};

                case 'Nickel Based Superalloy'
                    spec.DefaultAlloy = 'Inconel 718 (Ni-19Cr-18.5Fe-5.1Nb-3Mo-0.9Ti-0.5Al)';
                    spec.Elements = {'Ni', 'Cr', 'Fe', 'Nb', 'Mo', 'Ti', 'Al'};
                    spec.Fractions = [0.530, 0.190, 0.185, 0.051, 0.030, 0.009, 0.005];
                    spec.Category = 'Aero-Engine & Gas Turbine Superalloys';
                    spec.Description = 'Gamma-prime (Ni3Al,Ti) and gamma-double-prime (Ni3Nb) precipitation kinetics, creep rupture lifetime, and high-temperature oxidation.';
                    spec.PrimaryPhases = {'gamma (FCC)', 'gamma-prime (L12)', 'gamma-double-prime (D022)', 'Delta (Ni3Nb)', 'Liquid'};

                case 'NiFe Based Superalloy'
                    spec.DefaultAlloy = 'Incoloy 800H (Fe-32Ni-21Cr-0.4Al-0.4Ti)';
                    spec.Elements = {'Fe', 'Ni', 'Cr', 'Al', 'Ti', 'C'};
                    spec.Fractions = [0.457, 0.320, 0.210, 0.004, 0.004, 0.005];
                    spec.Category = 'Petrochemical & Nuclear High-Temperature Steels';
                    spec.Description = 'High-strength austenitic Fe-Ni-Cr alloys resisting carburization and sulfidation up to 1100 deg C with TiC/AlN grain pinning.';
                    spec.PrimaryPhases = {'gamma (FCC)', 'TiC', 'M23C6', 'gamma-prime', 'Liquid'};

                case 'Single Crystal'
                    spec.DefaultAlloy = 'CMSX-4 2nd-Generation Single Crystal Superalloy';
                    spec.Elements = {'Ni', 'Co', 'Cr', 'W', 'Ta', 'Re', 'Al', 'Ti', 'Mo', 'Hf'};
                    spec.Fractions = [0.617, 0.090, 0.065, 0.060, 0.065, 0.030, 0.056, 0.010, 0.006, 0.001];
                    spec.Category = 'Turbine Blade Directionally Solidified / SX Alloys';
                    spec.Description = 'Grain-boundary-free casting architecture with 70 vol% coherent gamma-prime cubes, high Re solute partitioning, and rafting kinetics.';
                    spec.PrimaryPhases = {'gamma (FCC)', 'gamma-prime (L12)', 'TCP (Topologically Close-Packed)', 'Liquid'};

                case 'Titanium Alloy'
                    spec.DefaultAlloy = 'Ti-6Al-4V (Grade 5 Alpha-Beta Alloy)';
                    spec.Elements = {'Ti', 'Al', 'V', 'Fe'};
                    spec.Fractions = [0.897, 0.060, 0.040, 0.003];
                    spec.Category = 'Aerospace & Biomedical Alpha-Beta Titanium';
                    spec.Description = 'Alpha (HCP) / Beta (BCC) phase transformation, beta-transus temperature (~995 deg C), and Widmanstatten basketweave kinetics.';
                    spec.PrimaryPhases = {'Alpha (HCP)', 'Beta (BCC)', 'Ti3Al (alpha2)', 'Liquid'};

                case 'Zirconium Alloy'
                    spec.DefaultAlloy = 'Zircaloy-4 (Zr-1.5Sn-0.2Fe-0.1Cr)';
                    spec.Elements = {'Zr', 'Sn', 'Fe', 'Cr'};
                    spec.Fractions = [0.982, 0.015, 0.002, 0.001];
                    spec.Category = 'Nuclear Fuel Cladding & Low Neutron Capture Alloys';
                    spec.Description = 'Ultra-low thermal neutron capture cross-section, high corrosion resistance in pressurized hot water, and hydride embrittlement thresholds.';
                    spec.PrimaryPhases = {'Alpha_Zr (HCP)', 'Beta_Zr (BCC)', 'Zr(Fe,Cr)2', 'Liquid'};

                case 'Solder Alloy'
                    spec.DefaultAlloy = 'SAC305 Lead-Free Electronic Solder (Sn-3.0Ag-0.5Cu)';
                    spec.Elements = {'Sn', 'Ag', 'Cu'};
                    spec.Fractions = [0.965, 0.030, 0.005];
                    spec.Category = 'Microelectronics Lead-Free Interconnects';
                    spec.Description = 'Near-eutectic Sn-Ag-Cu solidification at 217 deg C, Ag3Sn intermetallic platelet network, and Cu6Sn5 scallop growth.';
                    spec.PrimaryPhases = {'Beta-Sn (BCT)', 'Ag3Sn', 'Cu6Sn5', 'Liquid'};

                otherwise
                    % Default fallback
                    spec = MaterialDatabaseSelector.getDatabaseSpec('High Entropy Alloys');
            end
        end

        % =========================================================================
        % 3. MODAL SELECTION DIALOG (MATCHING THE REFERENCE SCREENSHOT)
        % =========================================================================
        function dlg = showSelectionDialog(parentApp, onSelectedCallback)
            % Creates a standalone modal dialog matching the user's reference screenshot
            dlg = uifigure( ...
                'Name', 'CALPHADHEACalc - Select Active Materials Database', ...
                'Position', [450, 250, 680, 480], ...
                'WindowStyle', 'modal', ...
                'Resize', 'off', ...
                'Color', [1.0, 1.0, 1.0] ...
            );

            % Outer grid
            mGrid = uigridlayout(dlg, [4, 1]);
            mGrid.RowHeight = {45, '1x', 50, 35};
            mGrid.ColumnWidth = {'1x'};
            mGrid.Padding = [16, 14, 16, 12];
            mGrid.RowSpacing = 8;
            mGrid.BackgroundColor = [1.0, 1.0, 1.0];

            % 1. Header
            hBox = uipanel(mGrid, 'BorderType', 'none', 'BackgroundColor', [1.0, 1.0, 1.0]);
            hBox.Layout.Row = 1; hBox.Layout.Column = 1;
            uilabel(hBox, ...
                'Text', 'CALPHADHEACalc: Materials Database Selector', ...
                'FontName', 'Times New Roman', 'FontSize', 14, 'FontWeight', 'bold', ...
                'FontColor', [0, 0, 0], 'Position', [0, 22, 500, 22]);
            uilabel(hBox, ...
                'Text', 'Select the thermodynamic & physical database to calculate properties from:', ...
                'FontName', 'Times New Roman', 'FontSize', 10, 'FontAngle', 'italic', ...
                'FontColor', [0, 0, 0], 'Position', [0, 2, 600, 18]);

            % 2. Main Two-Column Content Area
            cGrid = uigridlayout(mGrid, [1, 2]);
            cGrid.Layout.Row = 2; cGrid.Layout.Column = 1;
            cGrid.RowHeight = {'1x'};
            cGrid.ColumnWidth = {240, '1x'};
            cGrid.Padding = [0, 0, 0, 0];
            cGrid.ColumnSpacing = 14;
            cGrid.BackgroundColor = [1.0, 1.0, 1.0];

            % Left: Database Listbox (Exact list from screenshot)
            dbList = MaterialDatabaseSelector.getDatabaseList();
            
            % Initial value
            currentActive = 'High Entropy Alloys';
            if ~isempty(parentApp) && isprop(parentApp, 'ActiveDatabase') && ~isempty(parentApp.ActiveDatabase)
                currentActive = parentApp.ActiveDatabase;
            end

            lbPanel = uipanel(cGrid, 'Title', 'Available Alloy Databases', ...
                'FontName', 'Times New Roman', 'FontWeight', 'bold', ...
                'BackgroundColor', [1.0, 1.0, 1.0], 'BorderType', 'line', ...
                'HighlightColor', [0, 0, 0]);
            lbPanel.Layout.Row = 1; lbPanel.Layout.Column = 1;
            lbInner = uigridlayout(lbPanel, [1, 1]);
            lbInner.Padding = [4, 4, 4, 4];
            lbInner.BackgroundColor = [1.0, 1.0, 1.0];

            listCtrl = uilistbox(lbInner, ...
                'Items', dbList, ...
                'Value', currentActive, ...
                'FontName', 'Times New Roman', ...
                'FontSize', 11, ...
                'FontColor', [0, 0, 0], ...
                'BackgroundColor', [1.0, 1.0, 1.0]);

            % Right: Detailed Database Dossier Panel
            dPanel = uipanel(cGrid, 'Title', 'Database Dossier & Default Alloy Archetype', ...
                'FontName', 'Times New Roman', 'FontWeight', 'bold', ...
                'BackgroundColor', [1.0, 1.0, 1.0], 'BorderType', 'line', ...
                'HighlightColor', [0, 0, 0]);
            dPanel.Layout.Row = 1; dPanel.Layout.Column = 2;
            dInner = uigridlayout(dPanel, [6, 1]);
            dInner.RowHeight = {24, 20, 20, 20, '1x', 20};
            dInner.Padding = [8, 8, 8, 8];
            dInner.RowSpacing = 4;
            dInner.BackgroundColor = [1.0, 1.0, 1.0];

            lblDbTitle = uilabel(dInner, 'Text', 'Database: High Entropy Alloys', ...
                'FontName', 'Times New Roman', 'FontSize', 12, 'FontWeight', 'bold', 'FontColor', [0, 0, 0]);
            lblCategory = uilabel(dInner, 'Text', 'Category: Multi-Principal Element Alloys', ...
                'FontName', 'Times New Roman', 'FontSize', 9.5, 'FontAngle', 'italic', 'FontColor', [0, 0, 0]);
            lblDefaultAlloy = uilabel(dInner, 'Text', 'Default Alloy: CoCrFeMnNi (Cantor)', ...
                'FontName', 'Times New Roman', 'FontSize', 9.5, 'FontWeight', 'bold', 'FontColor', [0, 0, 0]);
            lblElements = uilabel(dInner, 'Text', 'Constituents: Co-Cr-Fe-Mn-Ni (at%)', ...
                'FontName', 'Times New Roman', 'FontSize', 9.5, 'FontColor', [0, 0, 0]);
            txtDesc = uitextarea(dInner, ...
                'Value', {'Select an alloy database from the list on the left to review its scope and default archetype.'}, ...
                'FontName', 'Times New Roman', 'FontSize', 9.5, 'FontColor', [0, 0, 0], ...
                'BackgroundColor', [1.0, 1.0, 1.0], 'Editable', 'off');
            lblPhases = uilabel(dInner, 'Text', 'Key Phases: FCC_A1, BCC_A2, B2, Liquid', ...
                'FontName', 'Times New Roman', 'FontSize', 9, 'FontColor', [0, 0, 0]);

            % Update Details Function
            function updateDetails(selectedName)
                spec = MaterialDatabaseSelector.getDatabaseSpec(selectedName);
                lblDbTitle.Text = ['Database: ' spec.Name];
                lblCategory.Text = ['Category: ' spec.Category];
                lblDefaultAlloy.Text = ['Default Alloy: ' spec.DefaultAlloy];
                
                % Format composition string
                cStr = '';
                for k = 1:length(spec.Elements)
                    if strcmp(spec.Basis, 'wt%')
                        cStr = sprintf('%s%s: %.2f wt%%  ', cStr, spec.Elements{k}, spec.Fractions(k)*100);
                    else
                        cStr = sprintf('%s%s: %.1f at%%  ', cStr, spec.Elements{k}, spec.Fractions(k)*100);
                    end
                end
                lblElements.Text = ['Composition: ' strtrim(cStr)];
                txtDesc.Value = {spec.Description};
                lblPhases.Text = ['Equilibrium Phases: ' strjoin(spec.PrimaryPhases, ', ')];
            end

            % Attach Listbox ValueChanged callback
            listCtrl.ValueChangedFcn = @(~, evt) updateDetails(evt.Value);
            updateDetails(listCtrl.Value);

            % 3. Action Buttons
            btnPanel = uipanel(mGrid, 'BorderType', 'none', 'BackgroundColor', [1.0, 1.0, 1.0]);
            btnPanel.Layout.Row = 3; btnPanel.Layout.Column = 1;
            
            uibutton(btnPanel, 'push', ...
                'Text', 'Load Database & Calculate', ...
                'FontName', 'Times New Roman', 'FontSize', 11, 'FontWeight', 'bold', ...
                'FontColor', [0, 0, 0], 'BackgroundColor', [1.0, 1.0, 1.0], ...
                'Position', [460, 8, 185, 34], ...
                'ButtonPushedFcn', @(~, ~) onConfirmSelection(dlg, listCtrl.Value, onSelectedCallback));

            uibutton(btnPanel, 'push', ...
                'Text', 'Keep Current Database', ...
                'FontName', 'Times New Roman', 'FontSize', 10.5, ...
                'FontColor', [0, 0, 0], 'BackgroundColor', [1.0, 1.0, 1.0], ...
                'Position', [280, 8, 165, 34], ...
                'ButtonPushedFcn', @(~, ~) close(dlg));

            % 4. Status Bar
            sPanel = uipanel(mGrid, 'BorderType', 'line', 'HighlightColor', [0, 0, 0], 'BackgroundColor', [1.0, 1.0, 1.0]);
            sPanel.Layout.Row = 4; sPanel.Layout.Column = 1;
            uilabel(sPanel, ...
                'Text', 'Database selection establishes thermodynamic lattice stabilities, empirical bounds, and literature validation data.', ...
                'FontName', 'Times New Roman', 'FontSize', 8.5, 'FontColor', [0, 0, 0], ...
                'Position', [8, 4, 630, 20]);
        end

    end
end

% Local Helper for Dialog Confirmation
function onConfirmSelection(dlg, chosenDb, callback)
    if ~isempty(callback)
        try
            callback(chosenDb);
        catch ME
            fprintf('[MaterialDatabaseSelector] Callback error: %s\n', ME.message);
        end
    end
    if isvalid(dlg)
        close(dlg);
    end
end
