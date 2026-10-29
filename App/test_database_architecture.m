classdef test_database_architecture < matlab.unittest.TestCase
    % Unit test suite for UnifiedHEADatabase, ThermalSprayCoatingDatabase,
    % and MaterialDatabaseSelector.

    methods (Test)

        function testUnifiedHEADatabaseMetadata(testCase)
            meta = UnifiedHEADatabase.getDatabaseMetadata();
            testCase.verifyNotEmpty(meta.Name);
            testCase.verifyEqual(meta.OxidesCount, 54);
            testCase.verifyEqual(meta.BenchmarkCount, 22);
            testCase.verifyEqual(meta.TotalCuratedCompositions, 12427);
        end

        function testUnifiedHEADatabasePresets(testCase)
            presets = UnifiedHEADatabase.getAllPresets();
            testCase.verifyTrue(isKey(presets, 'CoCrFeMnNi (Cantor Alloy)'));
            testCase.verifyTrue(isKey(presets, 'NbMoTaW (Senkov Classic RHEA)'));
            testCase.verifyTrue(isKey(presets, 'Al0.3CoCrFeNi (FCC + Nanoscale Spinodal)'));
        end

        function testThermalSprayCoatingChemistry(testCase)
            alloy = ThermalSprayCoatingDatabase.getPrimaryAlloy();
            testCase.verifyEqual(alloy.Formula, 'Ni71.61Fe4.47Cr15.27B3.32C0.68Si4.65');
            testCase.verifyEqual(round(sum(alloy.WeightPercents), 2), 100.00);
            testCase.verifyEqual(round(sum(alloy.AtomicPercents), 2), 100.00);
            testCase.verifyTrue(ismember('Ni', alloy.Elements));
            testCase.verifyTrue(ismember('Si', alloy.Elements));
            testCase.verifyTrue(ismember('B', alloy.Elements));
        end

        function testThermalSprayCoatingBenchmarks(testCase)
            expData = ThermalSprayCoatingDatabase.getExperimentalBenchmarks();
            testCase.verifyEqual(expData.Microhardness_HV03_HVOF, 745.0);
            testCase.verifyEqual(expData.Porosity_Percent_HVOF, 1.8);
            testCase.verifyEqual(expData.Solidus_K, 1243.15);
            testCase.verifyEqual(expData.Liquidus_K, 1318.15);
            testCase.verifyEqual(expData.AdhesionBondStrength_MPa, 58.4);
            testCase.verifyEqual(expData.WearRate_mm3_Nm, 2.2e-5);
            testCase.verifyEqual(expData.Icorr_uA_cm2, 2.45);
        end

        function testMaterialDatabaseCatalog(testCase)
            dbList = MaterialDatabaseSelector.getDatabaseList();
            testCase.verifyTrue(ismember('High Entropy Alloys', dbList));
            testCase.verifyTrue(ismember('Thermal Spray Coatings', dbList));
            testCase.verifyTrue(ismember('Aluminium Alloy', dbList));
            testCase.verifyTrue(ismember('Titanium Alloy', dbList));
            testCase.verifyTrue(ismember('Stainless Steel', dbList));
            testCase.verifyTrue(ismember('Nickel Based Superalloy', dbList));
        end

        function testDatabaseSpecLookup(testCase)
            specHEA = MaterialDatabaseSelector.getDatabaseSpec('High Entropy Alloys');
            testCase.verifyEqual(specHEA.Name, 'High Entropy Alloys');
            testCase.verifyEqual(specHEA.Basis, 'at%');

            specCoating = MaterialDatabaseSelector.getDatabaseSpec('Thermal Spray Coatings');
            testCase.verifyEqual(specCoating.Name, 'Thermal Spray Coatings');
            testCase.verifyEqual(specCoating.Basis, 'wt%');
            testCase.verifyTrue(ismember('Ni', specCoating.Elements));
            testCase.verifyTrue(ismember('Si', specCoating.Elements));
        end

    end
end
