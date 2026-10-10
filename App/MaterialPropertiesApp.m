classdef MaterialPropertiesApp < CALPHADHEACalc
    % MaterialPropertiesApp - CALPHADHEACalc 2026 Workstation Primary Entry Point
    % 100% Pure Native MATLAB CAE Desktop Architecture mirroring Pandat PanGUI & Thermo-Calc.
    %
    % Authors & Academic Provenance:
    %   Materials computational research engineer and lead developer: Felix Mwiya
    %   Research Guidance: Prof. (Dr.) Sheela Singh
    %   Department of Mechanical Engineering, School of Engineering and Sciences,
    %   SRM University-AP, Andhra Pradesh, India.
    %
    % Formal Citation:
    %   Mwiya, F., & Singh, S. (2026). CALPHADHEACalc: High-Entropy Alloy Multi-Physics
    %   Thermodynamic and Property Workstation (v3.4.0). Department of Mechanical Engineering,
    %   School of Engineering and Sciences, SRM University-AP, Andhra Pradesh, India.
    %
    % Key Architecture:
    %   1. Left Upper Pane:  Workspace Tree Explorer (uitree)
    %   2. Left Lower Pane:  Thermodynamic Condition & Property Inspector (uitable + controls)
    %   3. Center Main Area: Multi-Document Tabs (uitabgroup) with OriginLab Publication Plots & Worksheets
    %   4. Dedicated Tab 7:  HEA Applications Hub with real-time suitability scoring (0-100%)
    %   5. Bottom Pane:      CALPHAD Engine Console & Event Log (uitextarea - Consolas monospace)
    %   6. Status Bar:       Thermodynamic telemetry strip with live coordinate tracking
    %   7. Legal & Licenses: Embedded Thermo-Calc style Third-Party Licenses panel & Inspector

    methods
        function app = MaterialPropertiesApp(varargin)
            % Supports both modern and legacy launch signatures:
            %   app = MaterialPropertiesApp()
            %   app = MaterialPropertiesApp(initialAlloy)
            %   app = MaterialPropertiesApp(customDataFolder, isStandalone)
            %   app = MaterialPropertiesApp(initialAlloy, isStandalone)
            %   app = MaterialPropertiesApp(initialAlloy, isHeadless, isStandalone)

            initialAlloy = 'Cantor (CoCrFeMnNi)';
            isStandalone = false;
            isHeadless = false;

            if nargin >= 1 && ~isempty(varargin{1})
                if ischar(varargin{1}) || isstring(varargin{1})
                    strArg = char(varargin{1});
                    if exist(strArg, 'dir')
                        % Legacy customDataFolder argument passed -> use default alloy
                        initialAlloy = 'Cantor (CoCrFeMnNi)';
                    else
                        initialAlloy = strArg;
                    end
                end
            end

            if nargin >= 2 && ~isempty(varargin{2})
                if islogical(varargin{2}) || isnumeric(varargin{2})
                    % When launched from Launch_Material_Intelligence.vbs or desktop shortcut:
                    % MaterialPropertiesApp([], true) means isStandalone = true!
                    % Standalone desktop applications MUST BE VISIBLE! Never headless!
                    isStandalone = logical(varargin{2});
                end
            end

            if nargin >= 3 && ~isempty(varargin{3})
                if islogical(varargin{3}) || isnumeric(varargin{3})
                    isHeadless = logical(varargin{3});
                end
            end

            % Invoke parent CALPHADHEACalc constructor with resolved options
            app@CALPHADHEACalc(initialAlloy, isHeadless, isStandalone);
        end
    end
end
