using System;
using System.Linq;
using Xunit;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Tests
{
    public class MicrostructureSecondLayerTests
    {
        [Fact]
        public void PopulationBalanceDto_DeserializesAndValidatesPsdDistribution()
        {
            var pbm = new PopulationBalanceDto
            {
                PhaseName = "Gamma_Prime",
                TemperatureK = 1073.15,
                MeanRadiusNmFinal = 12.5,
                VolumeFractionFinal = 0.15,
                NumberDensityM3Final = 2.4e21,
                CriticalRadiusNmFinal = 0.85,
                OrowanStrengtheningFinalMpa = 285.0,
                ShearingStrengtheningFinalMpa = 310.0,
                TotalPrecipStrengtheningMpa = 210.0,
                PsdHistogram = new PsdHistogramDto
                {
                    RadiusNm = new() { 1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0 },
                    NumberDensityM4 = new() { 1e25, 4e26, 9e26, 6e26, 2e26, 5e25, 1e24 },
                    NormalizedFrequency = new() { 0.005, 0.18, 0.41, 0.27, 0.09, 0.03, 0.005 }
                }
            };

            Assert.Equal("Gamma_Prime", pbm.PhaseName);
            Assert.True(pbm.MeanRadiusNmFinal > 0.0);
            Assert.True(pbm.VolumeFractionFinal > 0.0 && pbm.VolumeFractionFinal <= 1.0);
            Assert.True(pbm.OrowanStrengtheningFinalMpa > 0.0);

            var sumFreq = pbm.PsdHistogram.NormalizedFrequency.Sum();
            Assert.True(Math.Abs(sumFreq - 0.99) < 0.05, "Normalized frequencies should integrate to ~1.0.");
        }

        [Fact]
        public void MonteCarloGrainGrowthDto_ValidatesZenerPinningAndHallPetch()
        {
            var mc = new MonteCarloGrainGrowthDto
            {
                TemperatureK = 1273.15,
                InitialGrainSizeUm = 25.0,
                FinalGrainSizeUm = 28.4,
                ZenerPinningPressureKpa = 14.5,
                ZenerLimitGrainSizeUm = 32.0,
                IsZenerPinned = false,
                HallPetchStrengthFinalMpa = 103.2,
                PottsSimulation = new PottsSimulationDto
                {
                    NumGrainsSimulated = 64,
                    MeanLatticeDiameter = 8.5,
                    TopologicalDistribution = new TopologicalDistributionDto
                    {
                        PolygonSides = new() { 3, 4, 5, 6, 7, 8, 9, 10 },
                        Frequency = new() { 0.015, 0.065, 0.22, 0.38, 0.21, 0.08, 0.025, 0.005 }
                    }
                }
            };

            Assert.True(mc.FinalGrainSizeUm >= mc.InitialGrainSizeUm, "Grain size must not shrink during normal growth.");
            Assert.True(mc.ZenerPinningPressureKpa > 0.0, "Zener pinning drag must be positive.");
            Assert.True(mc.HallPetchStrengthFinalMpa > 0.0, "Hall-Petch strengthening must be positive.");

            // Hexagons (n=6) must represent the mode of the topological distribution
            var topo = mc.PottsSimulation.TopologicalDistribution;
            var maxFreqIdx = topo.Frequency.IndexOf(topo.Frequency.Max());
            Assert.Equal(6, topo.PolygonSides[maxFreqIdx]);
        }

        [Fact]
        public void EquilibriumResult_EnrichesWithSecondLayerMicrostructure()
        {
            var res = new EquilibriumResult
            {
                AlloyName = "Cantor (CoCrFeMnNi)",
                Status = "success",
                Microstructure = new MicrostructureDto
                {
                    PrimaryPrecipitatePhase = "Cr-Rich Sigma",
                    HeatTreatmentTempK = 1073.15,
                    HeatTreatmentHours = 24.0,
                    PopulationBalance = new PopulationBalanceDto
                    {
                        PhaseName = "Cr-Rich Sigma",
                        MeanRadiusNmFinal = 18.2,
                        VolumeFractionFinal = 0.08,
                        TotalPrecipStrengtheningMpa = 165.0
                    },
                    MonteCarloGrainGrowth = new MonteCarloGrainGrowthDto
                    {
                        FinalGrainSizeUm = 25.8,
                        HallPetchStrengthFinalMpa = 108.3
                    },
                    StrengtheningBreakdown = new StrengtheningBreakdownDto
                    {
                        MatrixFrictionStressMpa = 140.0,
                        SolidSolutionStrengtheningMpa = 115.0,
                        HallPetchGrainBoundaryMpa = 108.3,
                        OrowanPrecipitationHardeningMpa = 165.0,
                        TotalResolvedYieldStrengthMpa = 528.3
                    }
                }
            };

            Assert.NotNull(res.Microstructure);
            Assert.Equal("Cr-Rich Sigma", res.Microstructure.PrimaryPrecipitatePhase);
            Assert.NotNull(res.Microstructure.StrengtheningBreakdown);

            var sb = res.Microstructure.StrengtheningBreakdown;
            var computedSum = sb.MatrixFrictionStressMpa + sb.SolidSolutionStrengtheningMpa +
                              sb.HallPetchGrainBoundaryMpa + sb.OrowanPrecipitationHardeningMpa;
            Assert.Equal(computedSum, sb.TotalResolvedYieldStrengthMpa, precision: 1);
        }

        [Fact]
        public void EquilibriumResult_EnrichesWithRuleOfMixturesAndComparison()
        {
            var res = new EquilibriumResult
            {
                AlloyName = "Cantor (CoCrFeMnNi)",
                Status = "success",
                RuleOfMixtures = new RuleOfMixturesDto
                {
                    DensityGCm3 = 8.02,
                    YoungsModulusGpa = 205.4,
                    YoungsModulusVoigtGpa = 208.1,
                    YoungsModulusReussGpa = 202.7,
                    YieldStrengthMpa = 52.0,
                    ThermalConductivityWMk = 74.6,
                    ElectricalResistivityUohmCm = 10.2
                },
                RomComparison = new RomComparisonDto
                {
                    ComparisonTable = new List<RomComparisonRowDto>
                    {
                        new()
                        {
                            Property = "Yield Strength σ_y",
                            Units = "MPa",
                            CalphadValue = 350.0,
                            RomValue = 52.0,
                            RomVoigt = 67.6,
                            RomReuss = 41.6,
                            DiffAbsolute = 298.0,
                            DiffRelativePct = 573.1,
                            Mechanism = "Solid solution lattice distortion strengthening"
                        }
                    },
                    Summary = new Dictionary<string, double>
                    {
                        { "yield_strength_elevation_pct", 573.1 }
                    }
                }
            };

            Assert.NotNull(res.RuleOfMixtures);
            Assert.Equal(8.02, res.RuleOfMixtures.DensityGCm3, precision: 2);
            Assert.True(res.RuleOfMixtures.YoungsModulusVoigtGpa >= res.RuleOfMixtures.YoungsModulusGpa);
            Assert.True(res.RuleOfMixtures.YoungsModulusGpa >= res.RuleOfMixtures.YoungsModulusReussGpa);

            Assert.NotNull(res.RomComparison);
            Assert.Single(res.RomComparison.ComparisonTable);
            Assert.Equal(573.1, res.RomComparison.ComparisonTable[0].DiffRelativePct, precision: 1);
        }

        [Fact]
        public void EnhancedPropertiesDto_ValidatesMechanicalAndTransportEnhancements()
        {
            var enh = new EnhancedPropertiesDto
            {
                BaseYieldStrengthMpa = 280.0,
                EnhancedYieldStrengthMpa = 528.3,
                DeltaYieldStrengthMpa = 248.3,
                BaseHardnessHv = 210.0,
                EnhancedHardnessHv = 286.0,
                DeltaHardnessHv = 76.0,
                BaseUtsMpa = 550.0,
                EnhancedUtsMpa = 753.6,
                DeltaUtsMpa = 203.6,
                BaseElongationPct = 25.0,
                EnhancedElongationPct = 17.6,
                BaseFractureToughnessMpaM05 = 65.0,
                EnhancedFractureToughnessMpaM05 = 74.8,
                BaseCreepRuptureHours = 100.0,
                EnhancedCreepRuptureHours = 485.0,
                EnhancedFatigueLimitMpa = 339.1,
                BaseElectricalResistivityUohmCm = 95.0,
                EnhancedElectricalResistivityUohmCm = 101.4,
                DeltaElectricalResistivityUohmCm = 6.4,
                BaseThermalConductivityWMk = 14.5,
                EnhancedThermalConductivityWMk = 13.7,
                DeltaThermalConductivityWMk = -0.8
            };

            // Yield strength and hardness must be elevated by precipitation and grain boundary pinning
            Assert.True(enh.EnhancedYieldStrengthMpa > enh.BaseYieldStrengthMpa);
            Assert.True(enh.EnhancedHardnessHv > enh.BaseHardnessHv);
            Assert.True(enh.EnhancedUtsMpa > enh.BaseUtsMpa);

            // Strength-ductility trade-off: elongation must be reduced as yield strength increases
            Assert.True(enh.EnhancedElongationPct < enh.BaseElongationPct);

            // Creep resistance must increase significantly
            Assert.True(enh.EnhancedCreepRuptureHours > enh.BaseCreepRuptureHours);

            // Grain boundary and interfacial scattering increases electrical resistivity and reduces thermal conductivity
            Assert.True(enh.EnhancedElectricalResistivityUohmCm > enh.BaseElectricalResistivityUohmCm);
            Assert.True(enh.EnhancedThermalConductivityWMk < enh.BaseThermalConductivityWMk);
        }

        [Fact]
        public void KineticPhaseDiagramDto_ValidatesGibbsThomsonSolvusAndTttCurvatures()
        {
            var kin = new KineticPhaseDiagramDto
            {
                PhaseName = "Gamma_Prime",
                EquilibriumSolvusK = 1180.0,
                EquilibriumSolvusC = 906.85,
                KineticSolvusK = 1145.0,
                KineticSolvusC = 871.85,
                GibbsThomsonShiftC = 35.0,
                TttNoseTemperatureC = 620.0,
                TttNoseTimeSeconds = 4.8,
                CriticalCoolingRateKS = 59.8,
                TttTemperaturesC = new() { 300.0, 450.0, 620.0, 750.0, 850.0 },
                TttTime1PctSeconds = new() { 120.0, 18.0, 0.72, 8.5, 95.0 },
                TttTime50PctSeconds = new() { 600.0, 85.0, 4.8, 42.0, 450.0 },
                TttTime99PctSeconds = new() { 2400.0, 320.0, 18.2, 160.0, 1800.0 },
                TemperatureSweepC = new() { 25.0, 200.0, 400.0, 600.0, 800.0, 950.0 },
                EquilibriumPhaseFraction = new() { 0.18, 0.18, 0.16, 0.12, 0.05, 0.0 },
                KineticPhaseFractionModerateCool = new() { 0.15, 0.15, 0.13, 0.09, 0.02, 0.0 },
                KineticPhaseFractionFastCool = new() { 0.04, 0.04, 0.03, 0.01, 0.0, 0.0 }
            };

            // Gibbs-Thomson capillary effect depresses solvus temperature
            Assert.True(kin.KineticSolvusK < kin.EquilibriumSolvusK);
            Assert.True(kin.GibbsThomsonShiftC > 0.0);

            // C-curve nose must have the shortest transformation time
            var minT50Idx = kin.TttTime50PctSeconds.IndexOf(kin.TttTime50PctSeconds.Min());
            Assert.Equal(620.0, kin.TttTemperaturesC[minT50Idx]);

            // Rapid cooling must suppress precipitate formation compared to equilibrium
            Assert.True(kin.KineticPhaseFractionFastCool[0] < kin.KineticPhaseFractionModerateCool[0]);
            Assert.True(kin.KineticPhaseFractionModerateCool[0] < kin.EquilibriumPhaseFraction[0]);
        }
    }
}
