function generate_validation_snapshots()
    % generate_validation_snapshots
    % Renders and saves high-resolution publication figures of all 8 graphic canvases
    % with database benchmark overlays directly using exportgraphics on UIAxes.

    artifactDir = 'C:\Users\Dell\.gemini\antigravity\brain\4a040a8a-1de2-4dac-ae93-9ec24252248a';
    if ~exist(artifactDir, 'dir')
        artifactDir = pwd;
    end

    fprintf('Generating validation benchmark graphics for Cantor alloy...\n');
    app = CALPHADHEACalc('Cantor (CoCrFeMnNi)', true);
    app.calculateAll();

    % 1. AxEquilibrium Snapshot
    try
        exportgraphics(app.AxEquilibrium, fullfile(artifactDir, 'calphad_equilibrium_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [1/8] Saved calphad_equilibrium_benchmark_overlay.png\n');
    catch err
        fprintf('  [1/8] Failed to export AxEquilibrium: %s\n', err.message);
    end

    % 2. AxIsopleth Snapshot
    try
        exportgraphics(app.AxIsopleth, fullfile(artifactDir, 'calphad_isopleth_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [2/8] Saved calphad_isopleth_benchmark_overlay.png\n');
    catch err
        fprintf('  [2/8] Failed to export AxIsopleth: %s\n', err.message);
    end

    % 3. AxTernary Snapshot
    try
        exportgraphics(app.AxTernary, fullfile(artifactDir, 'calphad_ternary_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [3/8] Saved calphad_ternary_benchmark_overlay.png\n');
    catch err
        fprintf('  [3/8] Failed to export AxTernary: %s\n', err.message);
    end

    % 4. AxTransport Snapshot (Thermal Conductivity)
    try
        app.DropdownTransportProp.Value = 'Thermal Conductivity k(T) [W/(m*K)]';
        app.renderTransportView();
        exportgraphics(app.AxTransport, fullfile(artifactDir, 'calphad_transport_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [4/8] Saved calphad_transport_benchmark_overlay.png\n');
    catch err
        fprintf('  [4/8] Failed to export AxTransport: %s\n', err.message);
    end

    % 5. AxMechanical Snapshot
    try
        exportgraphics(app.AxMechanical, fullfile(artifactDir, 'calphad_mechanical_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [5/8] Saved calphad_mechanical_benchmark_overlay.png\n');
    catch err
        fprintf('  [5/8] Failed to export AxMechanical: %s\n', err.message);
    end

    % 6. AxOxidation Snapshot
    try
        exportgraphics(app.AxOxidation, fullfile(artifactDir, 'calphad_oxidation_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [6/8] Saved calphad_oxidation_benchmark_overlay.png\n');
    catch err
        fprintf('  [6/8] Failed to export AxOxidation: %s\n', err.message);
    end

    % 7. AxCorrosion Snapshot
    try
        exportgraphics(app.AxCorrosion, fullfile(artifactDir, 'calphad_corrosion_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [7/8] Saved calphad_corrosion_benchmark_overlay.png\n');
    catch err
        fprintf('  [7/8] Failed to export AxCorrosion: %s\n', err.message);
    end

    % 8. AxXRD Snapshot
    try
        exportgraphics(app.AxXRD, fullfile(artifactDir, 'calphad_xrd_benchmark_overlay.png'), 'Resolution', 300);
        fprintf('  [8/8] Saved calphad_xrd_benchmark_overlay.png\n');
    catch err
        fprintf('  [8/8] Failed to export AxXRD: %s\n', err.message);
    end

    % 9. Export Tab 8 Validation Metrics Table as formatted summary report
    try
        tData = app.TableValidationMetrics.Data;
        reportFile = fullfile(artifactDir, 'calphad_validation_table_data.txt');
        fid = fopen(reportFile, 'w');
        if fid ~= -1
            fprintf(fid, '%-35s | %-18s | %-18s | %-16s | %-10s | %-28s\n', ...
                'Property', 'Calculated', 'Database (Exp)', 'Deviation', '% Error', 'Status / Tolerance');
            fprintf(fid, '%s\n', repmat('-', 1, 135));
            for r = 1:size(tData, 1)
                fprintf(fid, '%-35s | %-18s | %-18s | %-16s | %-10s | %-28s\n', ...
                    tData{r, 1}, tData{r, 2}, tData{r, 3}, tData{r, 4}, tData{r, 5}, tData{r, 6});
            end
            fclose(fid);
            fprintf('  Saved calphad_validation_table_data.txt\n');
        end
    catch err
        fprintf('  Failed to export validation table text: %s\n', err.message);
    end

    delete(app.UIFigure);
    fprintf('All validation snapshots successfully exported to %s!\n', artifactDir);
end
