using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace PyCalphadSuite.Core.DataStructures
{
    /// <summary>
    /// Compact Contiguous Thermodynamic Temperature Polynomial Parameter Block.
    /// Evaluates: G(T) = A + B*T + C*T*ln(T) + D*T^2 + E*T^3 + F/T
    /// </summary>
    [StructLayout(LayoutKind.Sequential, Pack = 8)]
    public readonly struct CalphadParameterRange
    {
        public readonly double TLow;
        public readonly double THigh;
        public readonly double A;
        public readonly double B;
        public readonly double C;
        public readonly double D;
        public readonly double E;
        public readonly double F;

        public CalphadParameterRange(
            double tLow, double tHigh,
            double a, double b, double c, double d, double e, double f)
        {
            TLow = tLow;
            THigh = tHigh;
            A = a;
            B = b;
            C = c;
            D = d;
            E = e;
            F = f;
        }

        /// <summary>
        /// Fused single-pass analytical evaluation of Gibbs energy, Entropy (-dG/dT), and Heat Capacity (-T*d2G/dT2).
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public (double G, double S, double Cp) EvaluateFused(double tempK)
        {
            double t = Math.Max(0.1, tempK);
            double lnT = Math.Log(t);
            double t2 = t * t;
            double invT = 1.0 / t;
            double invT2 = invT * invT;

            // G(T) = A + B*T + C*T*ln(T) + D*T^2 + E*T^3 + F/T
            double g = A + (B * t) + (C * t * lnT) + (D * t2) + (E * t2 * t) + (F * invT);

            // S(T) = -dG/dT = -(B + C*(1 + lnT) + 2*D*T + 3*E*T^2 - F/T^2)
            double s = -(B + (C * (1.0 + lnT)) + (2.0 * D * t) + (3.0 * E * t2) - (F * invT2));

            // Cp(T) = -T * d2G/dT2 = -(C + 2*D*T + 6*E*T^2 + 2*F/T^2)
            double cp = -(C + (2.0 * D * t) + (6.0 * E * t2) + (2.0 * F * invT2));

            return (g, s, cp);
        }
    }

    /// <summary>
    /// Compact Horner's Rule Evaluator for Binary Redlich-Kister Excess Parameters.
    /// Sum_{nu=0}^M L_nu * (yA - yB)^nu = L_0 + (yA - yB)*(L_1 + (yA - yB)*(L_2 + ...))
    /// </summary>
    public static class RedlichKisterEvaluator
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static double EvaluateBinary(ReadOnlySpan<double> lCoeffs, double yA, double yB)
        {
            if (lCoeffs.Length == 0) return 0.0;
            double deltaY = yA - yB;

            // Horner's rule backwards
            double result = lCoeffs[^1];
            for (int i = lCoeffs.Length - 2; i >= 0; i--)
            {
                result = (result * deltaY) + lCoeffs[i];
            }
            return result;
        }
    }
}
