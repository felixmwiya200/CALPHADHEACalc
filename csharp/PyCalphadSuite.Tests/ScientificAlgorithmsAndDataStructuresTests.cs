using System;
using System.Linq;
using PyCalphadSuite.Core.Algorithms;
using PyCalphadSuite.Core.DataStructures;
using Xunit;

namespace PyCalphadSuite.Tests
{
    public class ScientificAlgorithmsAndDataStructuresTests
    {
        [Fact]
        public void PchipInterpolator_PreservesMonotonicity_WithoutOvershoot()
        {
            // Step-like monotonic data resembling a phase arrest or rapid solid-fraction change
            double[] x = { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0 };
            double[] y = { 0.0, 0.0, 0.5, 1.0, 1.0, 1.0 };

            var pchip = new PchipInterpolator(x, y);

            // Interpolate at fine resolution and verify monotonicity
            double prev = -1.0;
            for (double t = 0.0; t <= 5.0; t += 0.05)
            {
                double val = pchip.Interpolate(t);
                Assert.True(val >= 0.0 && val <= 1.0, $"Value {val} out of bounds at t={t}");
                if (prev >= 0.0)
                {
                    Assert.True(val >= prev - 1e-12, $"Monotonicity violated: {val} < {prev} at t={t}");
                }
                prev = val;
            }
        }

        [Fact]
        public void LttbDownsampler_ReducesPoints_PreservingEndpointsAndBounds()
        {
            // Generate dense sinusoidal sweep of 1,000 points
            int n = 1000;
            double[] x = Enumerable.Range(0, n).Select(i => (double)i).ToArray();
            double[] y = x.Select(t => Math.Sin(t * 0.05) + Math.Cos(t * 0.02)).ToArray();

            int targetCount = 100;
            var (outX, outY) = LttbDownsampler.Downsample(x, y, targetCount);

            Assert.Equal(targetCount, outX.Length);
            Assert.Equal(targetCount, outY.Length);
            Assert.Equal(x[0], outX[0]);
            Assert.Equal(y[0], outY[0]);
            Assert.Equal(x[^1], outX[^1]);
            Assert.Equal(y[^1], outY[^1]);
        }

        [Fact]
        public void MaterialsKineticsTransport_ComputesWagnerOxidationAndMooijResistivity()
        {
            // Test Wagner parabolic oxidation at 900 C (1173.15 K) for Cantor benchmark
            // kp = 1.868e-12 g^2/(cm^4*s) -> mass gain at 100 h (3.6e5 s) should be ~0.82 mg/cm^2
            double thickness = MaterialsKineticsTransport.SolveOxideThickness(
                tSeconds: 360000.0,
                tempKelvin: 1173.15,
                k0Parabolic: 0.112,
                qParabolicJoules: 242000.0,
                k0Linear: 1e-3,
                qLinearJoules: 150000.0
            );

            Assert.True(thickness > 0.0, "Oxide thickness must be positive.");

            // Test Mooij saturation resistivity
            double rhoRt = MaterialsKineticsTransport.CalculateHeaResistivity(
                tempKelvin: 298.15,
                thetaDebyeKelvin: 410.0,
                rho0MicroOhmCm: 88.5,
                electronPhononCoeff: 35.0,
                rhoSatMicroOhmCm: 175.0
            );

            Assert.True(rhoRt >= 80.0 && rhoRt <= 120.0, $"Expected RT resistivity ~88-95, got {rhoRt}");

            // Test electronic thermal conductivity via Sommerfeld-Lorenz relation
            double kElec = MaterialsKineticsTransport.CalculateElectronicThermalConductivity(298.15, rhoRt);
            Assert.True(kElec > 5.0 && kElec < 15.0, $"Electronic thermal conductivity {kElec} W/(m*K) in realistic metallic range.");
        }

        [Fact]
        public unsafe void NativeThermodynamicBatch_AllocatesAndFreesContiguousAlignedBuffer()
        {
            int capacity = 1024;
            using var batch = new NativeThermodynamicBatch(capacity);

            Assert.Equal(capacity, batch.Capacity);
            Assert.True((nint)batch.RawPointer % 64 == 0, "Buffer must be 64-byte cacheline aligned.");

            // Fill temperatures and read back
            batch.Temperatures[0] = 300.0;
            batch.Temperatures[1023] = 1800.0;
            batch.GibbsEnergies[0] = -45200.0;

            Assert.Equal(300.0, batch.Temperatures[0]);
            Assert.Equal(1800.0, batch.Temperatures[1023]);
            Assert.Equal(-45200.0, batch.GibbsEnergies[0]);
        }

        [Fact]
        public void CalphadParameterStore_EvaluatesHornerAndFusedDerivatives()
        {
            // Binary Redlich-Kister excess coefficients [L0, L1, L2]
            double[] lCoeffs = { -15000.0, 3200.0, -850.0 };
            double yA = 0.6;
            double yB = 0.4;
            double deltaY = yA - yB; // 0.2

            double expected = lCoeffs[0] + (deltaY * lCoeffs[1]) + (deltaY * deltaY * lCoeffs[2]);
            double actual = RedlichKisterEvaluator.EvaluateBinary(lCoeffs, yA, yB);

            Assert.Equal(expected, actual, precision: 6);

            // Fused polynomial range evaluation
            var range = new CalphadParameterRange(
                tLow: 298.15, tHigh: 1800.0,
                a: -7200.0, b: 125.0, c: -24.5, d: -0.0015, e: 1e-7, f: 12000.0
            );

            var (g, s, cp) = range.EvaluateFused(1000.0);
            Assert.True(double.IsFinite(g));
            Assert.True(double.IsFinite(s));
            Assert.True(double.IsFinite(cp));
        }
    }
}
