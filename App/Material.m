classdef Material
    % Material class to calculate thermodynamic properties using NASA 7-coefficient polynomials.
    % The polynomials are piecewise functions with two temperature ranges.
    
    properties
        Name
        LowTempCoeffs  % Coefficients for low temperature range [a1, a2, a3, a4, a5, a6, a7]
        HighTempCoeffs % Coefficients for high temperature range [a1, a2, a3, a4, a5, a6, a7]
        MidTemp        % Temperature (K) dividing the low and high ranges
        R = 8.3144626; % Universal gas constant in J/(mol K)
    end
    
    methods
        function obj = Material(name, lowCoeffs, highCoeffs, midTemp)
            obj.Name = name;
            obj.LowTempCoeffs = lowCoeffs;
            obj.HighTempCoeffs = highCoeffs;
            obj.MidTemp = midTemp;
        end
        
        function cp = getCp(obj, T)
            % Returns Specific Heat Capacity at constant pressure (Cp) in J/(mol K)
            a = obj.getCoeffs(T);
            cp = obj.R * (a(1) + a(2).*T + a(3).*T.^2 + a(4).*T.^3 + a(5).*T.^4);
        end
        
        function h = getEnthalpy(obj, T)
            % Returns Enthalpy (H) in J/mol
            a = obj.getCoeffs(T);
            h = obj.R * T .* (a(1) + (a(2).*T)/2 + (a(3).*T.^2)/3 + (a(4).*T.^3)/4 + (a(5).*T.^4)/5 + a(6)./T);
        end
        
        function s = getEntropy(obj, T)
            % Returns Entropy (S) in J/(mol K)
            a = obj.getCoeffs(T);
            s = obj.R * (a(1).*log(T) + a(2).*T + (a(3).*T.^2)/2 + (a(4).*T.^3)/3 + (a(5).*T.^4)/4 + a(7));
        end
        
        function a = getCoeffs(obj, T)
            % Helper to pick correct coefficients based on piecewise temperature bounds
            if T <= obj.MidTemp
                a = obj.LowTempCoeffs;
            else
                a = obj.HighTempCoeffs;
            end
        end
    end
end
