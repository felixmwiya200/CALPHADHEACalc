// <copyright file="ExperimentalProcessOptionsTests.cs" company="PyCALPHAD Materials CAE">
// Unit verification of experimental options, hatch pitch calculations, and cellular strengthening models.
// </copyright>

using System;
using PyCalphadSuite.Core.Models;
using Xunit;

namespace PyCalphadSuite.Tests
{
    public class ExperimentalProcessOptionsTests
    {
        [Fact]
        public void DefaultOptions_CalculatesRealisticLpbfMetrics()
        {
            var opts = new ExperimentalProcessOptions();

            // Default: P=275W, v=800mm/s, h=80um (0.08mm), t=30um (0.03mm)
            // VED = 275 / (800 * 0.08 * 0.03) = 275 / 1.92 = 143.23 J/mm³
            Assert.True(opts.VolumetricEnergyDensity > 140.0 && opts.VolumetricEnergyDensity < 145.0);
            Assert.Equal("Optimal Conduction Window (>99.8% Relative Density)", opts.PorosityRegime);

            // Hall-Petch for 25 um
            // 450 / sqrt(25) = 90 MPa
            Assert.Equal(90.0, opts.HallPetchStrengtheningMpa, 1);

            // Cooling rate should be within 10^5 K/s
            Assert.True(opts.EstimatedCoolingRateKS >= 1e5 && opts.EstimatedCoolingRateKS <= 1e6);

            // Cellular spacing should be around 0.4 - 2.0 um
            Assert.True(opts.EstimatedCellularSpacingUm >= 0.4 && opts.EstimatedCellularSpacingUm <= 2.0);

            // Cellular strengthening should be positive
            Assert.True(opts.CellularStrengtheningMpa > 100.0);
        }

        [Fact]
        public void WideHatchPitch_TriggersLackOfFusionWarning()
        {
            var opts = new ExperimentalProcessOptions
            {
                LaserPowerW = 100.0,
                ScanSpeedMmS = 1500.0,
                HatchPitchUm = 200.0,
                LayerThicknessUm = 50.0
            };

            // VED = 100 / (1500 * 0.20 * 0.05) = 100 / 15 = 6.67 J/mm³ (< 50)
            Assert.True(opts.VolumetricEnergyDensity < 50.0);
            Assert.Equal("Lack-of-Fusion Risk (Insufficient Overlap)", opts.PorosityRegime);
        }

        [Fact]
        public void HighVed_TriggersKeyholePorosityWarning()
        {
            var opts = new ExperimentalProcessOptions
            {
                LaserPowerW = 500.0,
                ScanSpeedMmS = 300.0,
                HatchPitchUm = 50.0,
                LayerThicknessUm = 25.0
            };

            // VED = 500 / (300 * 0.05 * 0.025) = 500 / 0.375 = 1333.3 J/mm³ (> 160)
            Assert.True(opts.VolumetricEnergyDensity > 160.0);
            Assert.Equal("Keyhole Porosity Risk (Excessive Vaporization)", opts.PorosityRegime);
        }

        [Fact]
        public void Clone_CreatesIndependentCopy()
        {
            var original = new ExperimentalProcessOptions
            {
                GrainSizeUm = 12.5,
                HatchPitchUm = 95.0,
                ColdWorkPercent = 15.0
            };

            var clone = original.Clone();
            clone.GrainSizeUm = 50.0;
            clone.HatchPitchUm = 150.0;

            Assert.Equal(12.5, original.GrainSizeUm);
            Assert.Equal(95.0, original.HatchPitchUm);
            Assert.Equal(50.0, clone.GrainSizeUm);
            Assert.Equal(150.0, clone.HatchPitchUm);
        }
    }
}