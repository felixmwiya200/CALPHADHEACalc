% process_material_dat_files.m
% This script reads material properties from .dat files and plots all defined properties.

clear; clc; close all;

if exist('materials_data', 'dir')
    data_folder = 'materials_data';
elseif exist(fullfile('..', 'materials_data'), 'dir')
    data_folder = fullfile('..', 'materials_data');
else
    data_folder = 'materials_data';
    mkdir(data_folder);
end

dat_files = dir(fullfile(data_folder, '*.dat'));
if isempty(dat_files)
    disp('No .dat files found in the folder.');
    return;
end

% Base temperature range for predictions
T_range = linspace(293, 3500, 500);

for k = 1:length(dat_files)
    filename = fullfile(data_folder, dat_files(k).name);
    [~, mat_name, ~] = fileparts(filename);
    
    opts = detectImportOptions(filename);
    opts.VariableNamingRule = 'preserve';
    try
        MaterialData = readtable(filename, opts);
    catch ME
        warning('Could not read %s. Please ensure correct format.', dat_files(k).name);
        continue;
    end
    
    % Check for expected columns
    if ~all(ismember({'Property', 'FunctionName', 'Start', 'End', 'Function'}, MaterialData.Properties.VariableNames))
        warning('File %s missing required columns. Using legacy format...', dat_files(k).name);
        continue;
    end
    
    % Group by Property
    properties = unique(MaterialData.Property);
    num_props = length(properties);
    
    fig = figure('Name', ['Material: ', mat_name], 'Position', [100, 100, 1000, 800]);
    
    for p = 1:num_props
        prop_name = properties{p};
        prop_rows = MaterialData(strcmp(MaterialData.Property, prop_name), :);
        func_name = prop_rows.FunctionName{1};
        
        % Calculate values
        Property_vals = zeros(size(T_range));
        for i = 1:length(T_range)
            T = T_range(i);
            
            % Find correct interval
            idx = find(T >= prop_rows.Start & T <= prop_rows.End, 1);
            if ~isempty(idx)
                func_str = prop_rows{idx, 'Function'};
                if iscell(func_str)
                    func_str = func_str{1};
                end
                
                % Handle ^ for element-wise power in matlab if needed, 
                % but we process one T at a time so it's fine.
                % Convert string to MATLAB evaluated result
                eval_str = strrep(func_str, 'T', num2str(T, 10));
                
                % Add element-wise operators just in case
                eval_str = strrep(eval_str, '^', '.^');
                eval_str = strrep(eval_str, '*', '.*');
                eval_str = strrep(eval_str, '/', './');
                
                try
                    Property_vals(i) = eval(eval_str);
                catch
                    Property_vals(i) = NaN;
                end
            else
                Property_vals(i) = NaN;
            end
        end
        
        % Subplot for this property
        subplot(ceil(num_props/2), 2, p);
        plot(T_range, Property_vals, 'b-', 'LineWidth', 2);
        title([prop_name, ' (', func_name, ')']);
        xlabel('Temperature (K)');
        ylabel(func_name);
        grid on;
    end
    
    sgtitle(['Properties for ', strrep(mat_name, '_', ' ')]);
    saveas(fig, [mat_name, '_properties_plot.png']);
    disp(['Generated plots for ', mat_name]);
end
