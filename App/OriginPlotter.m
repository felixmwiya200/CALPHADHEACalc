classdef OriginPlotter
    % OriginPlotter - OriginLab Origin 2024/2025 Publication Plotting Engine for MATLAB
    % Formats native MATLAB UIAxes to commercial CALPHAD & OriginLab graphics standards:
    %   - 4-sided closed rectangular boxed frame (Box = 'on')
    %   - Inward-pointing major and minor ticks on all 4 axes (TickDir = 'in')
    %   - Solid crisp black borders (LineWidth = 1.25 pt)
    %   - Mirrored top and right ticks without redundant numeric labels
    %   - Academic TeX / LaTeX typography with bracketed physical units
    %   - Inset occluding legends with thin border and clean white background
    %   - On-canvas phase field annotations and tie-line bundles
    %   - 600 DPI publication vector graphics export (PDF, EPS, SVG, TIFF, PNG)

    methods (Static)

        function formatAxes(ax, xLabelStr, yLabelStr, titleStr)
            % Formats a UIAxes object to strict OriginLab standards
            if nargin < 2, xLabelStr = ''; end
            if nargin < 3, yLabelStr = ''; end
            if nargin < 4, titleStr = ''; end

            % Boxed 4-sided frame with inward ticks
            ax.Box          = 'on';
            try
                ax.BoxStyle = 'full';
            catch
                % Some MATLAB releases do not expose BoxStyle on UIAxes
            end
            ax.TickDir      = 'in';
            ax.TickLength   = [0.018, 0.038]; % [major, minor] relative lengths
            ax.XMinorTick   = 'on';
            ax.YMinorTick   = 'on';
            ax.LineWidth    = 1.25;

            % Color & Typography
            ax.Color        = [1.0, 1.0, 1.0];
            ax.XColor       = [0.12, 0.12, 0.12];
            ax.YColor       = [0.12, 0.12, 0.12];
            ax.FontName     = 'Arial';
            ax.FontSize     = 10.5;
            ax.FontWeight   = 'normal';

            % Subtle scientific grid
            ax.XGrid        = 'on';
            ax.YGrid        = 'on';
            ax.GridLineStyle= ':';
            ax.GridColor    = [0.85, 0.85, 0.85];
            ax.GridAlpha    = 0.75;

            % Labels with TeX interpreter
            if ~isempty(xLabelStr)
                ax.XLabel.Interpreter = 'tex';
                ax.XLabel.String      = xLabelStr;
                ax.XLabel.FontSize    = 11.5;
                ax.XLabel.Color       = [0.1, 0.1, 0.1];
            end
            if ~isempty(yLabelStr)
                ax.YLabel.Interpreter = 'tex';
                ax.YLabel.String      = yLabelStr;
                ax.YLabel.FontSize    = 11.5;
                ax.YLabel.Color       = [0.1, 0.1, 0.1];
            end
            if ~isempty(titleStr)
                ax.Title.Interpreter  = 'tex';
                ax.Title.String       = titleStr;
                ax.Title.FontSize     = 12.0;
                ax.Title.FontWeight   = 'bold';
                ax.Title.Color        = [0.15, 0.15, 0.15];
            else
                ax.Title.String       = '';
            end

            % Origin/CALPHAD Interactive Canvas Toolbar (Pan, Zoom In/Out, Restore, DataTip)
            try
                tb = axtoolbar(ax, {'pan', 'zoomin', 'zoomout', 'restoreview', 'datacursor'});
                tb.Visible = 'on';
            catch
            end
            try
                enableDefaultInteractivity(ax);
            catch
            end
        end

        function formatLegend(lgd, location, fontSize)
            % Formats an Origin-style floating or inset legend box
            if nargin < 2 || isempty(location)
                location = 'northeast';
            end
            if nargin < 3 || isempty(fontSize)
                fontSize = 9.5;
            end
            lgd.Location    = location;
            lgd.Box         = 'on';
            lgd.EdgeColor   = [0.65, 0.65, 0.65];
            lgd.LineWidth   = 0.85;
            lgd.Color       = [1.0, 1.0, 1.0];
            lgd.FontName    = 'Arial';
            lgd.FontSize    = fontSize;
            lgd.Interpreter = 'tex';
            try
                lgd.ItemHitMode = 'toggle'; % Click legend item to show/hide curve
            catch
            end
        end

        function addPhaseBadge(ax, x, y, textStr)
            % Adds an on-canvas phase annotation with a semi-transparent white box
            text(ax, x, y, textStr, ...
                'FontName', 'Arial', ...
                'FontSize', 9.5, ...
                'FontWeight', 'bold', ...
                'Color', [0.15, 0.15, 0.15], ...
                'HorizontalAlignment', 'center', ...
                'VerticalAlignment', 'middle', ...
                'BackgroundColor', [1.0, 1.0, 1.0], ...
                'EdgeColor', [0.70, 0.70, 0.70], ...
                'LineWidth', 0.8, ...
                'Margin', 2.5, ...
                'Interpreter', 'tex', ...
                'PickableParts', 'all');
        end

        function drawTieLines(ax, x1Arr, x2Arr, yArr, color)
            % Renders a bundle of conjugate tie-lines in two-phase equilibrium regions
            if nargin < 5 || isempty(color)
                color = [0.5, 0.5, 0.5];
            end
            hold(ax, 'on');
            nLines = min(length(x1Arr), length(yArr));
            for i = 1:nLines
                plot(ax, [x1Arr(i), x2Arr(i)], [yArr(i), yArr(i)], ...
                    'Color', color, ...
                    'LineStyle', ':', ...
                    'LineWidth', 0.9, ...
                    'HandleVisibility', 'off');
            end
            hold(ax, 'off');
        end

        function colors = getOriginPalette()
            % OriginLab Classic 8-color high-contrast scientific palette
            colors = [
                0.00, 0.00, 0.00;  % 1: Solid Black
                0.85, 0.15, 0.15;  % 2: Pure Red
                0.12, 0.40, 0.85;  % 3: Cobalt Blue
                0.10, 0.62, 0.28;  % 4: Forest Green
                0.80, 0.45, 0.05;  % 5: Amber Orange
                0.65, 0.15, 0.70;  % 6: Royal Purple
                0.05, 0.65, 0.75;  % 7: Deep Cyan
                0.45, 0.45, 0.45   % 8: Slate Gray
            ];
        end

        function c = getColor(idx)
            % Retrieve color by 1-based index (wrapping modulo 8)
            palette = OriginPlotter.getOriginPalette();
            n = size(palette, 1);
            modIdx = mod(idx - 1, n) + 1;
            c = palette(modIdx, :);
        end

        function success = exportGraphic(targetObj, filePath, dpi)
            % Exports target axes or figure at specified DPI (default 600 DPI)
            if nargin < 3 || isempty(dpi)
                dpi = 600;
            end
            try
                exportgraphics(targetObj, filePath, 'Resolution', dpi);
                success = true;
            catch err
                warning('OriginPlotter:ExportFailed', 'exportgraphics failed: %s', err.message);
                success = false;
            end
        end

        function success = exportPublicationPlot(targetObj, filePath, dpi)
            % Convenience alias for publication graphics export
            if nargin < 3 || isempty(dpi), dpi = 600; end
            success = OriginPlotter.exportGraphic(targetObj, filePath, dpi);
        end

        function success = copyToClipboard(targetObj)
            % Copies target axes or figure directly to system clipboard as high-res bitmap
            success = false;
            try
                tempPng = fullfile(tempdir, sprintf('origin_clip_%d.png', round(rand()*1e6)));
                exportgraphics(targetObj, tempPng, 'Resolution', 300);
                if ispc
                    psCmd = sprintf('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile(''%s''))"', tempPng);
                    [stat, ~] = system(psCmd);
                    success = (stat == 0);
                elseif ismac
                    system(sprintf('osascript -e ''set the clipboard to (read POSIX file "%s" as JPEG picture)''', tempPng));
                    success = true;
                else
                    system(sprintf('xclip -selection clipboard -t image/png -i "%s"', tempPng));
                    success = true;
                end
            catch err
                warning('OriginPlotter:ClipboardFailed', 'Clipboard copy failed: %s', err.message);
            end
        end

        function [success, savedPath] = exportWithDialog(targetObj, defaultName)
            % Opens file chooser dialog and exports graph to computer at 600 DPI
            if nargin < 2 || isempty(defaultName)
                defaultName = sprintf('CALPHAD_Graph_%s.png', datestr(now, 'yyyymmdd_HHMMSS'));
            end
            [file, path] = uiputfile(...
                {'*.png', 'Portable Network Graphics 600 DPI (*.png)'; ...
                 '*.pdf', 'Vector PDF Document (*.pdf)'; ...
                 '*.svg', 'Scalable Vector Graphics (*.svg)'; ...
                 '*.tif;*.tiff', 'TIFF High-Res Image (*.tif)'}, ...
                'Save Graph to Computer', defaultName);
            if isequal(file, 0) || isequal(path, 0)
                success = false;
                savedPath = '';
                return;
            end
            savedPath = fullfile(path, file);
            success = OriginPlotter.exportGraphic(targetObj, savedPath, 600);
        end

    end
end
