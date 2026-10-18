classdef AppSplashScreen < handle
    % APPSPLASHSCREEN Ultra-Fast, Sleek Desktop Launch & Loading Screen
    % Displays instantly (<150ms) when the application launches,
    % showing real-time subsystem initialization progress with modern dark styling.
    
    properties
        Figure
        LabelTitle
        LabelSub
        LabelStatus
        LabelDetail
        LabelPct
        ProgressTrack
        ProgressBar
        BadgePanels = {}
        BadgeLabels = {}
        IsClosed = false
    end
    
    methods
        function obj = AppSplashScreen()
            % Compute centered screen position
            screenSize = get(0, 'ScreenSize');
            w = 640;
            h = 380;
            x = max(10, round((screenSize(3) - w) / 2));
            y = max(10, round((screenSize(4) - h) / 2));
            
            % Create frameless, always-on-top modern figure
            obj.Figure = uifigure('Name', 'Material Intelligence Studio - Launching', ...
                'Position', [x y w h], ...
                'Color', [25 31 38] / 255.0, ...  % Dark Slate (#191F26 matching reference GIF)
                'WindowStyle', 'alwaysontop', ...
                'Resize', 'off');
            
            % Set application taskbar icon
            try
                iconFile = fullfile(fileparts(mfilename('fullpath')), 'resources', 'app_icon.png');
                if exist(iconFile, 'file')
                    obj.Figure.Icon = iconFile;
                end
            catch
            end
            
            % 1. Header Category Tag
            uilabel(obj.Figure, ...
                'Position', [40 332 560 18], ...
                'Text', 'HIGH-ENTROPY ALLOYS & THERMODYNAMICS PLATFORM', ...
                'FontColor', [0.22 0.74 0.97], ... % Sky Cyan (#38BDF8)
                'FontSize', 9.5, ...
                'FontWeight', 'bold');
            
            % 2. Main Title
            obj.LabelTitle = uilabel(obj.Figure, ...
                'Position', [40 292 480 36], ...
                'Text', 'Material Intelligence Studio', ...
                'FontColor', [0.97 0.98 0.99], ... % Near-White (#F8FAFC)
                'FontSize', 22, ...
                'FontWeight', 'bold');
            
            % 3. Version & Security Tag
            uilabel(obj.Figure, ...
                'Position', [40 268 560 20], ...
                'Text', 'v3.4.0 Production Edition | Lead Dev: Felix Mwiya | Guide: Prof. Sheela Singh (SRM University-AP)', ...
                'FontColor', [0.58 0.64 0.72], ... % Slate-400 (#94A3B8)
                'FontSize', 9.5);
            
            % Accent separator line
            uipanel(obj.Figure, ...
                'Position', [40 252 560 1.5], ...
                'BackgroundColor', [0.12 0.16 0.24], ...
                'BorderType', 'none');
            
            % 4. Status Title & Percentage Readout
            obj.LabelStatus = uilabel(obj.Figure, ...
                'Position', [40 198 460 24], ...
                'Text', 'Initializing Core Environment...', ...
                'FontColor', [0.93 0.95 0.98], ...
                'FontSize', 13, ...
                'FontWeight', 'bold');
            
            obj.LabelPct = uilabel(obj.Figure, ...
                'Position', [520 198 80 24], ...
                'Text', '0%', ...
                'HorizontalAlignment', 'right', ...
                'FontColor', [0.22 0.74 0.97], ...
                'FontSize', 14, ...
                'FontWeight', 'bold');
            
            % 5. Sub-detail Text
            obj.LabelDetail = uilabel(obj.Figure, ...
                'Position', [40 174 560 18], ...
                'Text', 'Mounting application memory and security layers...', ...
                'FontColor', [0.47 0.54 0.64], ... % Slate-500
                'FontSize', 10);
            
            % 6. Progress Bar Track (Outer)
            obj.ProgressTrack = uipanel(obj.Figure, ...
                'Position', [40 148 560 10], ...
                'BackgroundColor', [0.10 0.14 0.22], ...
                'BorderType', 'none');
            
            % Progress Bar Fill (Inner)
            obj.ProgressBar = uipanel(obj.ProgressTrack, ...
                'Position', [0 0 10 10], ...
                'BackgroundColor', [0.14 0.55 0.95], ... % Laser Blue / Cyan (#248CF2)
                'BorderType', 'none');
            
            % 7. Subsystem Status Badges (5 Modules)
            badgeNames = {
                'Security Vault', ...
                '45 Elements', ...
                'Lit Benchmark', ...
                'Laser Optics', ...
                'Desktop CAE UI'
            };
            
            nBadges = numel(badgeNames);
            badgeW = 104;
            badgeH = 34;
            badgeSpacing = (560 - nBadges * badgeW) / (nBadges - 1);
            
            for i = 1:nBadges
                bx = 40 + (i - 1) * (badgeW + badgeSpacing);
                p = uipanel(obj.Figure, ...
                    'Position', [bx 82 badgeW badgeH], ...
                    'BackgroundColor', [0.08 0.11 0.18], ...
                    'BorderType', 'line', ...
                    'HighlightColor', [0.14 0.19 0.29]);
                
                lbl = uilabel(p, ...
                    'Position', [4 4 badgeW-8 badgeH-8], ...
                    'Text', badgeNames{i}, ...
                    'HorizontalAlignment', 'center', ...
                    'FontColor', [0.45 0.52 0.62], ...
                    'FontSize', 9.5, ...
                    'FontWeight', 'bold');
                
                obj.BadgePanels{end+1} = p;
                obj.BadgeLabels{end+1} = lbl;
            end
            
            % 8. Footer Copyright & Academic attribution
            uilabel(obj.Figure, ...
                'Position', [40 34 560 16], ...
                'Text', 'CALPHADHEACalc 2026 • Felix Mwiya & Prof. Sheela Singh • SRM University-AP', ...
                'HorizontalAlignment', 'center', ...
                'FontColor', [0.38 0.46 0.56], ...
                'FontSize', 8.5);
            
            % Force instant initial render
            drawnow;
        end
        
        % Update progress bar, main status title, and detail message
        function update(obj, progressFrac, statusTitle, detailText)
            if obj.IsClosed || isempty(obj.Figure) || ~isvalid(obj.Figure)
                return;
            end
            
            try
                frac = max(0, min(1.0, progressFrac));
                trackW = 560;
                barW = max(4, round(frac * trackW));
                obj.ProgressBar.Position = [0 0 barW 10];
                
                if frac >= 0.95
                    obj.ProgressBar.BackgroundColor = [0.06 0.72 0.48]; % Emerald when ready
                else
                    obj.ProgressBar.BackgroundColor = [0.14 0.55 0.95]; % Blue / Cyan
                end
                
                if nargin >= 3 && ~isempty(statusTitle)
                    obj.LabelStatus.Text = statusTitle;
                end
                if nargin >= 4 && ~isempty(detailText)
                    obj.LabelDetail.Text = detailText;
                end
                
                obj.LabelPct.Text = sprintf('%d%%', round(frac * 100));
                drawnow limitrate;
            catch
            end
        end
        
        % Activate a subsystem badge with glowing emerald color and checkmark
        function setSubsystemStatus(obj, badgeIndex, isReady)
            if obj.IsClosed || isempty(obj.Figure) || ~isvalid(obj.Figure)
                return;
            end
            
            try
                if badgeIndex >= 1 && badgeIndex <= numel(obj.BadgePanels)
                    p = obj.BadgePanels{badgeIndex};
                    lbl = obj.BadgeLabels{badgeIndex};
                    
                    if isReady
                        p.BackgroundColor = [0.04 0.16 0.12]; % Translucent emerald
                        p.HighlightColor  = [0.06 0.72 0.48]; % Vibrant emerald border
                        lbl.FontColor     = [0.20 0.88 0.60]; % Bright emerald text
                        curTxt = lbl.Text;
                        if ~contains(curTxt, '[OK]')
                            lbl.Text = [curTxt, ' [OK]'];
                        end
                    end
                    drawnow limitrate;
                end
            catch
            end
        end
        
        % Smooth finish & close
        function close(obj)
            if obj.IsClosed
                return;
            end
            obj.IsClosed = true;
            try
                if ~isempty(obj.Figure) && isvalid(obj.Figure)
                    delete(obj.Figure);
                end
            catch
            end
        end
        
        function delete(obj)
            obj.close();
        end
    end
end
