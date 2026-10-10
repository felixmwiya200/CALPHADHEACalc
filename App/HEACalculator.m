classdef HEACalculator
    % Thermodynamic and empirical estimator for multicomponent High-Entropy Alloys (HEAs)
    % Uses Guo's Valence Electron Concentration (VEC) model to predict FCC vs BCC stability,
    % Boltzmann mixing entropy, and mixture density/heat capacity curves.
    
    methods (Static)
        function [filePath, phaseStr, VEC] = generateDatFile(compData, dataFolder)
            % Extract composition array from the UI matrix and convert to atomic fractions
            elements = compData(:, 1);
            at_pct = zeros(size(compData, 1), 1);
            for i = 1:size(compData, 1)
                v = compData{i, 2};
                if ischar(v) || isstring(v), v = str2double(v); end
                if isempty(v) || isnan(v), v = 0; end
                at_pct(i) = v;
            end
            
            totalAt = sum(at_pct);
            if totalAt == 0
                x = zeros(size(at_pct));
            else
                x = at_pct / totalAt;
            end
            
            % Elemental properties lookup: [VEC (valence electron count), Density (g/cm^3), Atomic mass (g/mol)]
            % Covers transition metals, refractory HEA elements, light alloys, and interstitials.
            elemDb = containers.Map();
            elemDb('H')  = [1, 0.07,  1.008];
            elemDb('Li') = [1, 0.534, 6.94];
            elemDb('Be') = [2, 1.85,  9.012];
            elemDb('B')  = [3, 2.34,  10.81];
            elemDb('C')  = [4, 2.26,  12.011];
            elemDb('N')  = [5, 1.25e-3, 14.007];
            elemDb('O')  = [6, 1.43e-3, 15.999];
            elemDb('Na') = [1, 0.97,  22.99];
            elemDb('Mg') = [2, 1.738, 24.305];
            elemDb('Al') = [3, 2.70,  26.982];
            elemDb('Si') = [4, 2.329, 28.085];
            elemDb('P')  = [5, 1.82,  30.974];
            elemDb('S')  = [6, 2.07,  32.06];
            elemDb('K')  = [1, 0.89,  39.098];
            elemDb('Ca') = [2, 1.54,  40.078];
            elemDb('Sc') = [3, 2.985, 44.956];
            elemDb('Ti') = [4, 4.506, 47.867];
            elemDb('V')  = [5, 6.11,  50.942];
            elemDb('Cr') = [6, 7.19,  51.996];
            elemDb('Mn') = [7, 7.44,  54.938];
            elemDb('Fe') = [8, 7.874, 55.845];
            elemDb('Co') = [9, 8.90,  58.933];
            elemDb('Ni') = [10, 8.908, 58.693];
            elemDb('Cu') = [11, 8.96, 63.546];
            elemDb('Zn') = [12, 7.14, 65.38];
            elemDb('Ga') = [3, 5.91,  69.723];
            elemDb('Ge') = [4, 5.323, 72.63];
            elemDb('As') = [5, 5.727, 74.922];
            elemDb('Se') = [6, 4.819, 78.971];
            elemDb('Rb') = [1, 1.53,  85.468];
            elemDb('Sr') = [2, 2.64,  87.62];
            elemDb('Y')  = [3, 4.472, 88.906];
            elemDb('Zr') = [4, 6.52,  91.224];
            elemDb('Nb') = [5, 8.57,  92.906];
            elemDb('Mo') = [6, 10.28, 95.95];
            elemDb('Tc') = [7, 11.0,  98.0];
            elemDb('Ru') = [8, 12.45, 101.07];
            elemDb('Rh') = [9, 12.41, 102.91];
            elemDb('Pd') = [10, 12.023, 106.42];
            elemDb('Ag') = [11, 10.49, 107.87];
            elemDb('Cd') = [12, 8.65,  112.41];
            elemDb('In') = [3, 7.31,  114.82];
            elemDb('Sn') = [4, 7.265, 118.71];
            elemDb('Sb') = [5, 6.697, 121.76];
            elemDb('Te') = [6, 6.24,  127.60];
            elemDb('Cs') = [1, 1.93,  132.91];
            elemDb('Ba') = [2, 3.62,  137.33];
            elemDb('La') = [3, 6.162, 138.91];
            elemDb('Ce') = [4, 6.77,  140.12];
            elemDb('Pr') = [3, 6.77,  140.91];
            elemDb('Nd') = [3, 7.01,  144.24];
            elemDb('Sm') = [3, 7.52,  150.36];
            elemDb('Eu') = [2, 5.244, 151.96];
            elemDb('Gd') = [3, 7.90,  157.25];
            elemDb('Tb') = [3, 8.23,  158.93];
            elemDb('Dy') = [3, 8.54,  162.50];
            elemDb('Ho') = [3, 8.79,  164.93];
            elemDb('Er') = [3, 9.066, 167.26];
            elemDb('Tm') = [3, 9.32,  168.93];
            elemDb('Yb') = [2, 6.90,  173.05];
            elemDb('Lu') = [3, 9.841, 174.97];
            elemDb('Hf') = [4, 13.31, 178.49];
            elemDb('Ta') = [5, 16.69, 180.95];
            elemDb('W')  = [6, 19.25, 183.84];
            elemDb('Re') = [7, 21.02, 186.21];
            elemDb('Os') = [8, 22.59, 190.23];
            elemDb('Ir') = [9, 22.56, 192.22];
            elemDb('Pt') = [10, 21.45, 195.08];
            elemDb('Au') = [11, 19.30, 196.97];
            elemDb('Hg') = [12, 13.534, 200.59];
            elemDb('Tl') = [3, 11.85, 204.38];
            elemDb('Pb') = [4, 11.34, 207.2];
            elemDb('Bi') = [5, 9.78,  208.98];
            elemDb('Th') = [4, 11.72, 232.04];
            elemDb('U')  = [6, 19.1,  238.03];
            
            % Resolve properties for each constituent in the active composition
            nElem = numel(elements);
            VEC_vals = zeros(nElem, 1);
            rho_vals = zeros(nElem, 1);
            M_vals   = zeros(nElem, 1);
            
            for i = 1:nElem
                sym = strtrim(elements{i});
                if isKey(elemDb, sym)
                    props = elemDb(sym);
                    VEC_vals(i) = props(1);
                    rho_vals(i) = props(2);
                    M_vals(i)   = props(3);
                else
                    % Safe fallback for unlisted elements
                    VEC_vals(i) = 6.0;
                    rho_vals(i) = 8.0;
                    M_vals(i)   = 55.0;
                end
            end
            
            VEC = sum(x .* VEC_vals);
            
            % Guo et al. (2011) criterion for phase stability in 3d-transition HEAs
            if VEC >= 8.0
                phaseStr = 'FCC (Solid Solution)';
            elseif VEC < 6.87
                phaseStr = 'BCC (Solid Solution)';
            else
                phaseStr = 'FCC + BCC (Duplex)';
            end
            
            % Ideal configurational mixing entropy: Delta S_mix = -R * sum(x_i * ln(x_i))
            R = 8.314; % J/(mol*K)
            S_mix = 0;
            for i = 1:length(x)
                if x(i) > 0
                    S_mix = S_mix - R * x(i) * log(x(i));
                end
            end
            
            % Temperature range (20 to 1200 deg C)
            T = (20:10:1200)';
            vec_array = repmat(VEC, size(T));
            smix_array = repmat(S_mix, size(T));
            
            % Molar volume rule of mixtures for theoretical mixture density
            rho_den = sum(x .* M_vals ./ max(rho_vals, 1e-6));
            if rho_den == 0
                rho_mix = 0;
            else
                rho_mix = sum(x .* M_vals) / rho_den;
            end
            % Linear thermal expansion density drop
            density_array = rho_mix - 0.0001 * (T - 20);
            
            % Kopp-Neumann estimate for high-temperature heat capacity
            M_mix = sum(x .* M_vals) / 1000; % kg/mol
            if M_mix == 0
                Cp_mix = 0;
            else
                Cp_mix = 3 * R / M_mix;
            end
            cp_array = Cp_mix + 0.1 * (T - 20);
            
            rawTable = table(T, vec_array, smix_array, density_array, cp_array, ...
                'VariableNames', {'Temperature (C)', 'Valence Electron Concentration (VEC)', ...
                'Configurational Entropy (J/mol*K)', 'Density (g/cm^3)', 'Specific Heat (J/kg*C)'});
                
            if ~exist(dataFolder, 'dir')
                try, mkdir(dataFolder); catch; end
            end
            
            filePath = fullfile(dataFolder, 'Dynamic_HEA_Model.dat');
            writetable(rawTable, filePath, 'Delimiter', '\t');
        end
    end
end
