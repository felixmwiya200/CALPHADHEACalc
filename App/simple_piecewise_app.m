% simple_piecewise_app.m
% A script to define piecewise functions using a table format (Start, End, Function)
% and evaluate/predict thermodynamic properties.

clear; clc; close all;

% 1. Define the table as shown in the image
Start = [293; 2250];
End = [2250; 3500];
Function = {'-0.125*T+4031.3'; '-0.8*T+5050'};

% Create a MATLAB table for easy viewing and management
MaterialData = table(Start, End, Function);
disp('--- Material Piecewise Functions ---');
disp(MaterialData);

% 2. Define the temperature range you want to predict (e.g., 293K to 3500K)
T_range = linspace(min(Start), max(End), 500);
Property_vals = zeros(size(T_range));

% 3. Evaluate the piecewise functions
for i = 1:length(T_range)
    T = T_range(i);
    
    % Find which interval T falls into
    % We use T >= Start and T <= End. For overlapping boundaries, it picks the first match.
    idx = find(T >= MaterialData.Start & T <= MaterialData.End, 1);
    
    if ~isempty(idx)
        % Get the string representation of the function
        func_str = MaterialData.Function{idx};
        
        % Convert the string equation into a MATLAB evaluatable function
        % We replace 'T' with the actual value for evaluation
        % (str2func can also be used, but eval is simple for basic equations)
        eval_str = strrep(func_str, 'T', num2str(T));
        Property_vals(i) = eval(eval_str);
    else
        Property_vals(i) = NaN; % Out of defined bounds
    end
end

% 4. Plot the predicted thermodynamic property
fig = figure('Name', 'Predicted Thermodynamic Property', 'Position', [100, 100, 800, 400]);
plot(T_range, Property_vals, 'b-', 'LineWidth', 2);

title('Thermodynamic Property Prediction using Piecewise Functions');
xlabel('Temperature T');
ylabel('Property Value');
grid on;

% Add vertical line indicating the boundary at T = 2250
xline(2250, 'r--', 'Boundary T=2250', 'LabelVerticalAlignment', 'bottom');

saveas(fig, 'piecewise_prediction_plot.png');
disp('Successfully evaluated the piecewise functions and saved the plot to piecewise_prediction_plot.png');
