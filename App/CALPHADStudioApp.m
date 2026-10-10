classdef CALPHADStudioApp < CALPHADHEACalc
    % CALPHADStudioApp - Backward-Compatibility Wrapper for CALPHADHEACalc
    % Inherits all capabilities from CALPHADHEACalc.
    %
    % Authors & Academic Credits:
    %   Materials computational research engineer and lead developer: Felix Mwiya
    %   Under the guidance of Prof. (Dr.) Sheela Singh
    %   SRM University-AP, Andhra Pradesh, India
    %
    % Ensures legacy scripts and tests referencing CALPHADStudioApp continue
    % to operate seamlessly with zero disruption.

    methods
        function app = CALPHADStudioApp(varargin)
            app@CALPHADHEACalc(varargin{:});
        end
    end
end
