% calculate_thermo_properties.m
% Simple script to define materials and calculate their thermodynamic properties
% using NASA 7-coefficient polynomials (piecewise functions).

clear; clc; close all;

% 1. Define materials and their coefficients (from NASA Glenn database)
% [a1, a2, a3, a4, a5, a6, a7]

% --- O2 (Oxygen Gas) ---
o2_low = [3.78245636E+00, -2.99673416E-03, 9.84730201E-06, -9.68129509E-09, 3.24372837E-12, -1.06394356E+03, 3.65767573E+00];
o2_high = [3.28253784E+00, 1.48308754E-03, -7.57966669E-07, 2.09470555E-10, -2.16717794E-14, -1.08845772E+03, 5.45323129E+00];
o2_mid_temp = 1000; % Transition temperature

% --- CO2 (Carbon Dioxide Gas) ---
co2_low = [2.35677352E+00, 8.98459677E-03, -7.12356269E-06, 2.45919022E-09, -1.43699548E-13, -4.83719697E+04, 9.90105222E+00];
co2_high = [3.85746029E+00, 4.41437026E-03, -2.21481404E-06, 5.23490188E-10, -4.72084164E-15, -4.87591660E+04, 2.27163806E+00];
co2_mid_temp = 1000;

% Initialize the objects
oxygen = Material('O2 (Oxygen)', o2_low, o2_high, o2_mid_temp);
carbonDioxide = Material('CO2 (Carbon Dioxide)', co2_low, co2_high, co2_mid_temp);

% 2. Define the temperature range you want to predict (in Kelvin)
T_range = linspace(300, 3000, 200);

% Initialize arrays for storing results
num_points = length(T_range);
Cp_o2 = zeros(1, num_points); H_o2 = zeros(1, num_points); S_o2 = zeros(1, num_points);
Cp_co2 = zeros(1, num_points); H_co2 = zeros(1, num_points); S_co2 = zeros(1, num_points);

% 3. Calculate the piecewise functions over the temperature range
for i = 1:num_points
    T = T_range(i);
    
    Cp_o2(i) = oxygen.getCp(T);
    H_o2(i) = oxygen.getEnthalpy(T);
    S_o2(i) = oxygen.getEntropy(T);
    
    Cp_co2(i) = carbonDioxide.getCp(T);
    H_co2(i) = carbonDioxide.getEnthalpy(T);
    S_co2(i) = carbonDioxide.getEntropy(T);
end

% 4. Plot the results
fig = figure('Name', 'Thermodynamic Properties', 'Position', [100, 100, 800, 600]);

% Cp Plot
subplot(3,1,1);
plot(T_range, Cp_o2, 'b-', 'LineWidth', 2); hold on;
plot(T_range, Cp_co2, 'r-', 'LineWidth', 2);
title('Specific Heat Capacity (Cp)');
ylabel('Cp (J/mol\cdotK)');
legend(oxygen.Name, carbonDioxide.Name, 'Location', 'best');
grid on;

% Enthalpy Plot
subplot(3,1,2);
plot(T_range, H_o2/1000, 'b-', 'LineWidth', 2); hold on;
plot(T_range, H_co2/1000, 'r-', 'LineWidth', 2);
title('Enthalpy (H)');
ylabel('H (kJ/mol)');
grid on;

% Entropy Plot
subplot(3,1,3);
plot(T_range, S_o2, 'b-', 'LineWidth', 2); hold on;
plot(T_range, S_co2, 'r-', 'LineWidth', 2);
title('Entropy (S)');
xlabel('Temperature (K)');
ylabel('S (J/mol\cdotK)');
grid on;

disp('Prediction of thermodynamic properties completed successfully. Generating plots...');
saveas(fig, 'thermo_properties_plot.png');
disp('Saved plot to thermo_properties_plot.png');
