using System;

namespace PyCalphadSuite.Core.Algorithms
{
    /// <summary>
    /// Physical Kinetics and High-Temperature Transport Solver.
    /// Incorporates Wagner mixed linear-parabolic oxidation kinetics,
    /// Bloch-Grüneisen electron-phonon transport, and Mooij saturation for high-entropy alloys.
    /// </summary>
    public static class MaterialsKineticsTransport
    {
        public const double GasConstant = 8.314462618;          // J / (mol * K)
        public const double LorenzNumber = 2.44355e-8;         // Sommerfeld constant, W * Ohm / K^2

        /// <summary>
        /// Solves oxide scale thickness (in meters) under mixed linear-parabolic kinetics (Deal-Grove formulation).
        /// Reverts seamlessly to pure parabolic Wagner kinetics at macroscopic exposure times.
        /// </summary>
        public static double SolveOxideThickness(
            double tSeconds,
            double tempKelvin,
            double k0Parabolic,
            double qParabolicJoules,
            double k0Linear,
            double qLinearJoules,
            double initialThicknessMeters = 0.0)
        {
            if (tSeconds <= 0.0) return initialThicknessMeters;

            double kp = k0Parabolic * Math.Exp(-qParabolicJoules / (GasConstant * tempKelvin));
            double kl = k0Linear * Math.Exp(-qLinearJoules / (GasConstant * tempKelvin));

            // Deal-Grove: x^2 + (kp / kl)*x - (kp * t + x0^2 + (kp / kl)*x0) = 0
            double a = kp / Math.Max(1e-18, kl);
            double b = -(kp * tSeconds + (initialThicknessMeters * initialThicknessMeters) + (a * initialThicknessMeters));

            // Positive root of quadratic equation
            double disc = (a * a) - (4.0 * b);
            return (-a + Math.Sqrt(Math.Max(0.0, disc))) / 2.0;
        }

        /// <summary>
        /// Evaluates high-temperature electrical resistivity (in μΩ·cm) for High-Entropy Alloys,
        /// coupling Nordheim chemical disorder, acoustic phonon scattering, and Mooij saturation.
        /// </summary>
        public static double CalculateHeaResistivity(
            double tempKelvin,
            double thetaDebyeKelvin,
            double rho0MicroOhmCm,
            double electronPhononCoeff,
            double rhoSatMicroOhmCm = 175.0)
        {
            if (tempKelvin <= 1e-3)
            {
                return rho0MicroOhmCm;
            }

            double bgIntegral = SimpsonBlochGruneisen(thetaDebyeKelvin / tempKelvin);
            double tRatio = tempKelvin / thetaDebyeKelvin;
            double rhoEPh = electronPhononCoeff * Math.Pow(tRatio, 5) * bgIntegral;

            // Wiesmann-Fisk-Webb additive saturation: phonon scattering saturates in parallel
            // while residual defect/disorder scattering rho0 remains additive:
            // rho(T) = rho0 + (rho_ph * rho_sat) / (rho_ph + rho_sat)
            return rho0MicroOhmCm + ((rhoEPh * rhoSatMicroOhmCm) / (rhoEPh + rhoSatMicroOhmCm));
        }

        /// <summary>
        /// Evaluates electronic thermal conductivity (W / (m·K)) via the Sommerfeld-Lorenz Wiedemann-Franz relation.
        /// </summary>
        public static double CalculateElectronicThermalConductivity(double tempKelvin, double resistivityMicroOhmCm)
        {
            if (resistivityMicroOhmCm <= 0.0) return 0.0;
            double rhoOhmM = resistivityMicroOhmCm * 1e-8;
            return (LorenzNumber * tempKelvin) / rhoOhmM;
        }

        private static double SimpsonBlochGruneisen(double upperLimit, int intervals = 100)
        {
            // Rapid exponential convergence for upperLimit > 40
            double limit = Math.Min(40.0, Math.Max(0.01, upperLimit));
            double h = limit / intervals;
            double sum = 0.0;

            for (int i = 0; i <= intervals; i++)
            {
                double z = i * h;
                double fz;
                if (z < 1e-5)
                {
                    fz = 0.0;
                }
                else
                {
                    double expZ = Math.Exp(z);
                    fz = Math.Pow(z, 5) / ((expZ - 1.0) * (1.0 - Math.Exp(-z)));
                }

                int weight = (i == 0 || i == intervals) ? 1 : ((i % 2 == 1) ? 4 : 2);
                sum += weight * fz;
            }

            return (h / 3.0) * sum;
        }
    }
}
