classdef HEAApplicationDatabase
    % HEAApplicationDatabase - Curated High Entropy Alloy Engineering Applications Database
    % Curated from open Git datasets and authoritative materials science literature:
    %   - Citrine Informatics MPEA Dataset (CitrineInformatics/MPEA_dataset)
    %   - Clemson University COD'HEM Database (ChenCheng-976/COD_HEM)
    %   - Phases Research Lab ULTERA Refractory Database (PhasesResearchLab/PyQAlloy)
    %   - Matminer Benchmark Dataset (cast_mpea_ouyang)
    %   - HEAPS / Bio-HEA Database (Biomedical orthopedic HEAs)
    %   - Idaho National Laboratory Nuclear HEA Code (IdahoLabResearch/HEA_Code)
    %   - Nature Scientific Data 2026 LLM-extracted HEA Dataset (12,427 records)

    methods (Static)

        function apps = getAllApplications()
            % Returns cell array of structs representing all 12 curated industrial applications
            apps = {
                HEAApplicationDatabase.getAeroTurbineBlade();
                HEAApplicationDatabase.getCryoLngVessel();
                HEAApplicationDatabase.getNuclearGen4Clad();
                HEAApplicationDatabase.getBiomedOrthoImplant();
                HEAApplicationDatabase.getMarineSubseaValve();
                HEAApplicationDatabase.getToolingHotDie();
                HEAApplicationDatabase.getRefractoryFurnace();
                HEAApplicationDatabase.getHydrogenStorage();
                HEAApplicationDatabase.getEnergyCatalysis();
                HEAApplicationDatabase.getAeroDiscRotor();
                HEAApplicationDatabase.getLaserCladdingWearOverlay();
                HEAApplicationDatabase.getCavitationCorrosionOverlay()
            };
        end

        function app = getApplication(appId)
            % Retrieve a specific application definition by its unique identifier
            allApps = HEAApplicationDatabase.getAllApplications();
            app = [];
            for i = 1:numel(allApps)
                thisApp = allApps{i};
                if strcmp(thisApp.ID, appId)
                    app = thisApp;
                    return;
                end
            end
            error('Application ID "%s" not found in HEAApplicationDatabase.', appId);
        end

        function sectors = getSectors()
            % Return unique list of engineering sectors as a 1xN row cell array
            allApps = HEAApplicationDatabase.getAllApplications();
            secList = cell(numel(allApps), 1);
            for i = 1:numel(allApps)
                secList{i} = allApps{i}.Sector;
            end
            sectors = reshape(unique(secList), 1, []);
        end

        function sigmaMap = getThermalNeutronCrossSections()
            % Thermal neutron capture cross section (sigma_abs in barns) for alloy elements
            % Key metric for Generation IV nuclear reactor core and cladding applications
            sigmaMap = containers.Map();
            sigmaMap('Zr') = 0.185;   % Outstanding transparency
            sigmaMap('Al') = 0.231;   % Excellent transparency
            sigmaMap('Si') = 0.171;   % Excellent
            sigmaMap('Mg') = 0.063;   % Very low
            sigmaMap('C')  = 0.0035;  % Exceptionally low
            sigmaMap('Nb') = 1.15;    % Acceptable
            sigmaMap('Mo') = 2.48;    % Moderate
            sigmaMap('Fe') = 2.56;    % Moderate / Standard structural
            sigmaMap('Cr') = 3.05;    % Moderate
            sigmaMap('Ni') = 4.49;    % High
            sigmaMap('V')  = 5.08;    % High
            sigmaMap('Ti') = 6.09;    % High
            sigmaMap('W')  = 18.3;    % Very high
            sigmaMap('Ta') = 20.6;    % Very high (Severe penalty)
            sigmaMap('Co') = 37.2;    % Disqualifying / severe activation (Co-60)
            sigmaMap('Hf') = 104.0;   % Nuclear control rod poison (Veto for cladding)
            sigmaMap('B')  = 767.0;   % Extreme poison
            sigmaMap('Gd') = 49700.0; % Burnable poison
        end

        function toxMap = getBiocompatibilityMap()
            % Cytotoxicity, allergenicity, and biocompatibility classification
            % Classification: 1 = Biocompatible / Osteophilic, 0 = Cytotoxic / Allergenic
            toxMap = containers.Map();
            toxMap('Ti') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Excellent osseointegration & passive TiO2');
            toxMap('Zr') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Non-toxic, bio-inert ZrO2 passive scale');
            toxMap('Nb') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Non-toxic, highly tissue-tolerant');
            toxMap('Ta') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Superb biocompatibility & bone ingrowth');
            toxMap('Mo') = struct('Safe', true,  'Class', 'Tolerable',     'Reason', 'Trace essential micronutrient (<10 at%)');
            toxMap('Hf') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Bio-inert similar to Zr');
            toxMap('Si') = struct('Safe', true,  'Class', 'Biocompatible', 'Reason', 'Trace biocompatible');
            
            % Prohibited elements for permanent orthopedic implants
            toxMap('Ni') = struct('Safe', false, 'Class', 'Toxic/Allergenic', 'Reason', 'Severe Type IV contact allergy, DNA damage');
            toxMap('Co') = struct('Safe', false, 'Class', 'Cytotoxic',        'Reason', 'Metallosis, local cardiomyopathy, toxicity');
            toxMap('Cr') = struct('Safe', false, 'Class', 'Cytotoxic (Cr VI)','Reason', 'Release of carcinogenic hexavalent Cr ions');
            toxMap('Al') = struct('Safe', false, 'Class', 'Neurotoxic',       'Reason', 'Linked to osteomalacia & Alzheimer pathology');
            toxMap('V')  = struct('Safe', false, 'Class', 'Cytotoxic',        'Reason', 'Strong cytotoxicity & cellular inhibition');
            toxMap('Cu') = struct('Safe', false, 'Class', 'Cytotoxic (burst)','Reason', 'High ion cytotoxicity in soft tissues');
        end

        % =========================================================================
        % APPLICATION DEFINITION GENERATORS (Standardized Schema)
        % =========================================================================

        function app = createBaseApp(id, name, sector, desc, benchmark, gitRef, vetoElems, criteria)
            app = struct();
            app.ID              = id;
            app.Name            = name;
            app.Sector          = sector;
            app.Description     = desc;
            app.BenchmarkAlloy  = benchmark;
            app.GitReference    = gitRef;
            app.VetoElements    = vetoElems;
            app.MinSolidus_K    = [];
            app.MinDuctility_pct= [];
            app.MaxModulus_GPa  = [];
            app.MaxNeutronBarns = [];
            app.Criteria        = criteria;
        end

        function app = getAeroTurbineBlade()
            desc = ['High-pressure turbine blades operating at 800-1150 °C under extreme centrifugal stress, ', ...
                    'hot corrosion, and oxidation. Requires high solidus temperature, high-temperature yield strength, ', ...
                    'protective alumina/chromia scale, low density for centrifugal load reduction, and creep resistance.'];
            criteria = {
                'Solidus_K',           0.20, 'max', 1500.0, 1850.0, 'K';
                'YieldStrength_800C',  0.25, 'max',  350.0,  650.0, 'MPa';
                'Density_g_cm3',       0.15, 'min',   9.50,   7.50, 'g/cm^3';
                'Oxidation_kp',        0.20, 'min',  1e-10,  1e-13, 'g^2/(cm^4*s)';
                'FractureToughness',   0.10, 'max',   35.0,   80.0, 'MPa*m^0.5';
                'HighTempCreepLimit',  0.10, 'max',  200.0,  450.0, 'MPa'
            };
            app = HEAApplicationDatabase.createBaseApp('AERO_TURBINE_BLADE', ...
                'Aerospace Gas Turbine High-Pressure Blades', 'Aerospace & Propulsion', ...
                desc, 'Al0.7CoCrFeNi / MoNbTaW', 'CitrineInformatics/MPEA_dataset | ULTERA Zenodo:15716150', ...
                {'Zn', 'Sn', 'Bi', 'Pb', 'Cd', 'Hg'}, criteria);
            app.MinSolidus_K = 1450.0;
        end

        function app = getCryoLngVessel()
            desc = ['Structural containment vessels, cryogenic transfer piping, and LNG/LH2 fuel tanks operating ', ...
                    'at liquid nitrogen (77 K) and liquid hydrogen (20 K) temperatures. Demands absence of ductile-to-brittle ', ...
                    'transition (DBTT), exceptional fracture toughness K1c > 150 MPa*m^0.5, and high uniform elongation.'];
            criteria = {
                'FractureToughness',   0.30, 'max',   70.0,  180.0, 'MPa*m^0.5';
                'Elongation_pct',      0.25, 'max',   20.0,   50.0, '%';
                'YieldStrength_RT',    0.20, 'max',  240.0,  450.0, 'MPa';
                'PhaseStabilityFCC',   0.15, 'max',    0.6,    1.0, 'fraction';
                'CorrosionRate_NaCl',  0.10, 'min',   0.05,  0.005, 'mm/yr'
            };
            app = HEAApplicationDatabase.createBaseApp('CRYO_LNG_VESSEL', ...
                'Cryogenic Storage & LNG / Liquid H2 Fuel Tanks', 'Cryogenics & Clean Fuels', ...
                desc, 'CoCrFeMnNi (Cantor Alloy) / CoCrFeNi', 'Materials Cloud Gludovatz 2014 | COD_HEM Clemson', ...
                {'Zn', 'Bi', 'Pb'}, criteria);
            app.MinDuctility_pct = 15.0;
        end

        function app = getNuclearGen4Clad()
            desc = ['Fuel cladding tubes and core structural components exposed to high fast neutron fluxes, liquid metal ', ...
                    '(lead/sodium) or supercritical water coolant, and temperatures up to 800 °C. Demands low neutron capture ', ...
                    'cross-section (sigma < 2.5 barns), high irradiation swelling resistance, and high-T strength.'];
            criteria = {
                'NeutronCrossSection', 0.30, 'min',    3.5,    1.5, 'barns';
                'YieldStrength_800C',  0.25, 'max',  250.0,  550.0, 'MPa';
                'Solidus_K',           0.15, 'max', 1550.0, 1900.0, 'K';
                'Oxidation_kp',        0.15, 'min',  5e-11,  1e-13, 'g^2/(cm^4*s)';
                'SwellingResistance',  0.15, 'max',    0.6,    1.0, 'index'
            };
            app = HEAApplicationDatabase.createBaseApp('NUCLEAR_GEN4_CLAD', ...
                'Generation IV Nuclear Reactor Core Cladding', 'Nuclear Energy', ...
                desc, 'FeCrAl-HEA / V35Ti35Cr20Fe10 / ZrTiNbV', 'IdahoLabResearch/HEA_Code | INL Nuclear MPEA Repository', ...
                {'Co', 'Hf', 'B', 'Cd', 'Gd'}, criteria);
            app.MaxNeutronBarns = 4.0;
        end

        function app = getBiomedOrthoImplant()
            desc = ['Load-bearing hip stems, bone fracture plates, and dental fixtures. Requires 100% biocompatible, non-toxic ', ...
                    'elements (Ti, Zr, Nb, Ta, Mo only), low Youngs modulus (E < 80 GPa matching cortical bone to prevent ', ...
                    'stress shielding), high pitting corrosion resistance in human body fluid, and high fatigue strength.'];
            criteria = {
                'BiocompatibilityScore',0.30, 'max',   0.70,   1.00, 'index';
                'YoungsModulus_GPa',    0.25, 'min',  120.0,   65.0, 'GPa';
                'PREN',                 0.20, 'max',   35.0,   55.0, 'index';
                'YieldStrength_RT',     0.15, 'max',  650.0, 1100.0, 'MPa';
                'CorrosionRate_NaCl',   0.10, 'min',   0.02, 0.001, 'mm/yr'
            };
            app = HEAApplicationDatabase.createBaseApp('BIOMED_ORTHO_IMPLANT', ...
                'Orthopedic & Dental Medical Implants', 'Biomedical Engineering', ...
                desc, 'TiZrNbTaMo / Ti25Zr25Nb25Ta25', 'HEAPS Bio-HEA Database | Nature Sci Data 12,427 LLM DB', ...
                {'Ni', 'Co', 'Cr', 'Al', 'V', 'Cu', 'Pb', 'Cd', 'Be'}, criteria);
            app.MaxModulus_GPa = 130.0;
        end

        function app = getMarineSubseaValve()
            desc = ['Deepwater subsea valves, offshore manifold components, and desalination pump impellers exposed to ', ...
                    'high chloride seawater, biofouling, and cavitation wear. Demands PREN > 45 (super-austenitic/hyper-duplex level), ', ...
                    'minimal micro-galvanic potential difference (Delta E < 0.2 V), and high yield strength.'];
            criteria = {
                'PREN',                0.30, 'max',   32.0,   50.0, 'index';
                'CorrosionRate_NaCl',  0.25, 'min',   0.05,  0.002, 'mm/yr';
                'GalvanicImmunity',    0.20, 'max',   0.50,   0.90, 'index';
                'YieldStrength_RT',    0.15, 'max',  450.0,  850.0, 'MPa';
                'FractureToughness',   0.10, 'max',   50.0,  120.0, 'MPa*m^0.5'
            };
            app = HEAApplicationDatabase.createBaseApp('MARINE_SUBSEA_VALVE', ...
                'Subsea Offshore, Desalination & Marine Valves', 'Marine & Offshore', ...
                desc, 'Al0.3CoCrFeNi / FeCoCrNiMo0.3', 'COD_HEM Clemson | ml-hea-corrosion-code-data', ...
                {'Mg', 'Zn', 'Ca'}, criteria);
        end

        function app = getToolingHotDie()
            desc = ['Hot forging dies, high-speed metal cutting inserts, and hot stamping tools subjected to severe sliding wear, ', ...
                    'thermal fatigue, and abrasive contact. Requires Vickers hardness HV > 500, yield strength > 1200 MPa, ', ...
                    'high shear modulus, and resistance to thermal softening.'];
            criteria = {
                'VickersHardness_HV',  0.30, 'max',  300.0,  600.0, 'HV';
                'YieldStrength_RT',    0.25, 'max',  700.0, 1400.0, 'MPa';
                'UTS_RT_MPa',          0.15, 'max',  950.0, 1600.0, 'MPa';
                'ShearModulus_GPa',    0.15, 'max',   65.0,   95.0, 'GPa';
                'ThermalStability_K',  0.15, 'max',  900.0, 1250.0, 'K'
            };
            app = HEAApplicationDatabase.createBaseApp('TOOLING_HOT_DIE', ...
                'High-Hardness Wear Tooling & Hot Stamping Dies', 'Manufacturing & Tooling', ...
                desc, 'Al1.0CoCrFeNi / AlCoCrFeNiTi0.5', 'CitrineInformatics/MPEA_dataset (hardness.csv)', ...
                {'Sn', 'Pb', 'Bi'}, criteria);
        end

        function app = getRefractoryFurnace()
            desc = ['Heating elements, structural hot-zone fasteners, and thermal radiation heat shields for vacuum and inert-gas ', ...
                    'furnaces operating at 1200-2000 °C. Demands ultra-high melting point (Ts > 2200 K), single-phase BCC refractory ', ...
                    'stability, and yield strength retention at 1200 °C > 300 MPa.'];
            criteria = {
                'Solidus_K',           0.35, 'max', 1900.0, 2600.0, 'K';
                'YieldStrength_1200C', 0.35, 'max',  150.0,  450.0, 'MPa';
                'ThermalConductivity', 0.15, 'max',   20.0,   60.0, 'W/(m*K)';
                'ElasticModulus_GPa',  0.15, 'max',  120.0,  240.0, 'GPa'
            };
            app = HEAApplicationDatabase.createBaseApp('REFRACTORY_FURNACE', ...
                'Ultra-High Temperature Vacuum Furnaces & Thermal Shields', 'Ultra-High Temp Furnaces', ...
                desc, 'NbMoTaW / TaNbHfZrTi', 'PhasesResearchLab/PyQAlloy (ULTERA RHEA Database)', ...
                {'Al', 'Zn', 'Sn', 'Pb', 'Bi', 'Mg', 'Cu'}, criteria);
        end

        function app = getHydrogenStorage()
            desc = ['Solid-state hydrogen absorption and release beds for fuel-cell vehicles and stationary energy storage. ', ...
                    'Requires high BCC/C14 Laves phase fraction for interstitial tetrahedral site hydrogen storage, favorable ', ...
                    'hydride formation enthalpy (-20 to -45 kJ/mol H2), and resistance to pulverization upon cycling.'];
            criteria = {
                'HydrogenAffinity',    0.35, 'max',   0.50,   0.95, 'index';
                'BCC_PhaseFraction',   0.25, 'max',   0.50,   1.00, 'fraction';
                'LatticeExpansion',    0.20, 'max',   0.03,   0.08, 'strain';
                'Solidus_K',           0.10, 'max', 1400.0, 1800.0, 'K';
                'Density_g_cm3',       0.10, 'min',   8.50,   5.80, 'g/cm^3'
            };
            app = HEAApplicationDatabase.createBaseApp('HYDROGEN_STORAGE', ...
                'Solid-State Hydrogen Storage & Hydride Carriers', 'Hydrogen & Clean Energy', ...
                desc, 'TiZrVNbHf / TiVZrNb', 'Science/Nature ML HEA Discovery | mathsphy/dataset-ML', ...
                {'Au', 'Ag', 'Pt'}, criteria);
        end

        function app = getEnergyCatalysis()
            desc = ['Electrocatalytic electrodes for Hydrogen Evolution Reaction (HER) and Oxygen Evolution Reaction (OER) in ', ...
                    'alkaline water electrolyzers. Requires high density of mixed active transition metal d-orbitals, corrosion ', ...
                    'immunity in 1 M KOH, and resistance to electrochemical surface leaching.'];
            criteria = {
                'ElectrocatalyticActivity', 0.35, 'max', 0.60, 0.95, 'index';
                'CorrosionRate_NaCl',       0.25, 'min', 0.04, 0.001,'mm/yr';
                'TransitionMetalCount',     0.20, 'max',  3.0,  5.0, 'count';
                'PBR_Stability',            0.10, 'max', 0.70, 0.98, 'index';
                'VEC',                      0.10, 'target', 8.2, 8.5, 'e/a'
            };
            app = HEAApplicationDatabase.createBaseApp('ENERGY_CATALYSIS', ...
                'Alkaline Water Electrolysis & Fuel Cell Catalysts', 'Hydrogen & Clean Energy', ...
                desc, 'FeCoCrNiMo / FeCoNiMnMo', 'Nature Communications HEA Electrocatalyst Git Repositories', ...
                {'Al', 'Zn', 'Mg'}, criteria);
        end

        function app = getAeroDiscRotor()
            desc = ['Aero-engine compressor and turbine rotating discs operating at 550-750 °C under severe low-cycle fatigue, ', ...
                    'burst stress, and thermal gradients. Requires ultimate tensile strength UTS > 1200 MPa, fatigue endurance, ', ...
                    'controlled density (< 8.3 g/cm^3), and ductility > 15%.'];
            criteria = {
                'UTS_RT_MPa',          0.25, 'max',  950.0, 1450.0, 'MPa';
                'YieldStrength_RT',    0.20, 'max',  750.0, 1150.0, 'MPa';
                'Density_g_cm3',       0.20, 'min',   8.80,   7.60, 'g/cm^3';
                'Elongation_pct',      0.15, 'max',   12.0,   25.0, '%';
                'FractureToughness',   0.10, 'max',   45.0,   90.0, 'MPa*m^0.5';
                'YieldStrength_800C',  0.10, 'max',  300.0,  550.0, 'MPa'
            };
            app = HEAApplicationDatabase.createBaseApp('AERO_DISC_ROTOR', ...
                'Turbine Compressor Disc & High-Stress Rotors', 'Aerospace & Propulsion', ...
                desc, 'Gamma/Gamma-prime Co-Ni-based HEA', 'CitrineInformatics/MPEA_dataset | COD_HEM Clemson', ...
                {'Zn', 'Sn', 'Bi', 'Pb'}, criteria);
        end

        function app = getLaserCladdingWearOverlay()
            desc = ['High-durability wear-resistant HEA cladding on structural steels (AISI 1045, Q235, H13). ', ...
                    'Requires Vickers hardness HV > 550, low specific wear rate (< 3.5e-6 mm^3/(N*m)), dilution tolerance, ', ...
                    'and high plastic deformation resistance (H^3/E^2 > 0.03 GPa).'];
            criteria = {
                'Hardness_HV',          0.30, 'max',  400.0,  850.0, 'HV';
                'WearRate_Archard',     0.25, 'min',   10.0,    1.5, '1e-6 mm^3/(N*m)';
                'PlasticResistance',    0.20, 'max',  0.015,  0.080, 'GPa';
                'ThermalStress_MPa',    0.15, 'min',  450.0,  120.0, 'MPa';
                'Ductility_pct',        0.10, 'max',    5.0,   25.0, '%'
            };
            app = HEAApplicationDatabase.createBaseApp('WEAR_CLADDING_OVERLAY', ...
                'Wear-Resistant Laser Cladding on Structural Steels', 'Surface Engineering & Mining', ...
                desc, 'Al0.5CoCrFeNi / FeCoCrNiMo', 'Li et al., Adv. Eng. Mater. 21, 1900343 (2019)', ...
                {'Pb', 'Bi', 'Cd', 'Hg'}, criteria);
        end

        function app = getCavitationCorrosionOverlay()
            desc = ['Marine pump impellers, subsea hydro-turbines, and chemical processing valves exposed to ', ...
                    'synergistic cavitation erosion and aggressive seawater pitting. Requires passivating p-type ', ...
                    'protective film, PREN > 32, low corrosion rate (< 0.005 mm/yr), and high work-hardening capacity.'];
            criteria = {
                'CorrosionRate_NaCl',   0.30, 'min',   0.05,  0.002, 'mm/yr';
                'PREN_Effective',       0.25, 'max',   22.0,   45.0, 'PREN';
                'Hardness_HV',          0.20, 'max',  300.0,  650.0, 'HV';
                'PittingBreakdown_V',   0.15, 'max',   0.10,   0.85, 'V vs SCE';
                'WorkHardeningExponent',0.10, 'max',   0.25,   0.55, 'n'
            };
            app = HEAApplicationDatabase.createBaseApp('CAVITATION_CORROSION_OVERLAY', ...
                'Marine Cavitation-Erosion & Corrosion Resistant Overlay', 'Marine & Offshore Engineering', ...
                desc, 'Al0.3CoCrFeNi / CoCrFeNiMo0.2', 'Li et al., JMRT 35, 4142 (2025) & AEM (2019)', ...
                {'Mg', 'Zn', 'Ca', 'Li'}, criteria);
        end

    end
end
