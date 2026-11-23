// <copyright file="NativePolyglotCore.cs" company="PyCALPHAD Materials CAE">
// Unified polyglot interoperability bridge connecting C# .NET 8 WPF with native C11 and C++20 engines.
// </copyright>

using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace PyCalphadSuite.Core.Services
{
    /// <summary>
    /// Direct P/Invoke bridge to the native C11 metallurgy physics core and C++20 DirectX 11 engine.
    /// Incorporates C, C++, and C# seamlessly into a single unified front-end process.
    /// </summary>
    public static class NativePolyglotCore
    {
        private const string NativeDll = "pycalphad_native.dll";
        private static readonly bool _isAvailable;

        static NativePolyglotCore()
        {
            try
            {
                // Verify DLL resolution across application base and workspace directories
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string dllPath = Path.Combine(baseDir, NativeDll);

                if (!File.Exists(dllPath))
                {
                    // Check sibling and parent build directories
                    string[] probes = new[]
                    {
                        Path.Combine(baseDir, @"..\..\..\..\..\cpp\bin", NativeDll),
                        Path.Combine(baseDir, @"..\..\..\cpp\bin", NativeDll),
                        Path.Combine(@"C:\Users\Dell\Documents\Material design\cpp\bin", NativeDll)
                    };
                    foreach (var probe in probes)
                    {
                        if (File.Exists(probe))
                        {
                            try { File.Copy(probe, dllPath, true); break; }
                            catch { }
                        }
                    }
                }

                var buf = new byte[256];
                int len = native_get_engine_info(buf, buf.Length);
                _isAvailable = len > 0;
            }
            catch
            {
                _isAvailable = false;
            }
        }

        public static bool IsAvailable => _isAvailable;

        public static string GetEngineInfo()
        {
            if (!_isAvailable) return "C# Managed Fallback Core";
            try
            {
                var buf = new byte[256];
                int len = native_get_engine_info(buf, buf.Length);
                return len > 0 ? Encoding.UTF8.GetString(buf, 0, len) : "C11/C++20 Native Engine";
            }
            catch
            {
                return "C# Managed Core";
            }
        }

        public static double CalculateYieldStrength(double baseSigma, double ky, double grainSizeUm, double sss, double tempK)
        {
            if (_isAvailable)
            {
                try
                {
                    return native_calc_yield_strength(baseSigma, ky, grainSizeUm, sss, tempK);
                }
                catch { }
            }
            // Managed fallback
            double dM = Math.Max(1.0, grainSizeUm) * 1e-6;
            double hp = baseSigma + (ky / Math.Sqrt(dM)) * 1e-6 + sss;
            double tRatio = Math.Clamp((tempK - 298.15) / (1623.0 - 298.15), 0.0, 0.95);
            return hp * Math.Pow(1.0 - tRatio, 1.25);
        }

        public static double CalculateLatticeDistortion(double[] radiiPm, double[] fractions)
        {
            if (radiiPm == null || fractions == null || radiiPm.Length == 0 || radiiPm.Length != fractions.Length)
                return 0.0;

            if (_isAvailable)
            {
                try
                {
                    return native_calc_lattice_distortion(radiiPm, fractions, fractions.Length);
                }
                catch { }
            }
            // Managed fallback
            double sumC = 0.0, rBar = 0.0;
            for (int i = 0; i < fractions.Length; i++)
            {
                sumC += fractions[i];
                rBar += fractions[i] * radiiPm[i];
            }
            if (sumC <= 0.0 || rBar <= 0.0) return 0.0;
            rBar /= sumC;

            double deltaSq = 0.0;
            for (int i = 0; i < fractions.Length; i++)
            {
                double ci = fractions[i] / sumC;
                double diff = 1.0 - (radiiPm[i] / rBar);
                deltaSq += ci * diff * diff;
            }
            return Math.Sqrt(deltaSq) * 100.0;
        }

        public static double CalculateMixingEntropy(double[] fractions)
        {
            if (fractions == null || fractions.Length == 0) return 0.0;
            if (_isAvailable)
            {
                try
                {
                    return native_calc_mixing_entropy(fractions, fractions.Length);
                }
                catch { }
            }
            double sumC = 0.0;
            for (int i = 0; i < fractions.Length; i++) sumC += fractions[i];
            if (sumC <= 0.0) return 0.0;
            const double R = 8.314462618;
            double sConf = 0.0;
            for (int i = 0; i < fractions.Length; i++)
            {
                double ci = fractions[i] / sumC;
                if (ci > 1e-12) sConf -= ci * Math.Log(ci);
            }
            return R * sConf;
        }

        public static double CalculateValenceElectronConcentration(double[] vecValues, double[] fractions)
        {
            if (vecValues == null || fractions == null || vecValues.Length != fractions.Length || fractions.Length == 0)
                return 0.0;
            if (_isAvailable)
            {
                try
                {
                    return native_calc_valence_electron_concentration(vecValues, fractions, fractions.Length);
                }
                catch { }
            }
            double sumC = 0.0, vecSum = 0.0;
            for (int i = 0; i < fractions.Length; i++)
            {
                sumC += fractions[i];
                vecSum += fractions[i] * vecValues[i];
            }
            return sumC > 0 ? (vecSum / sumC) : 0.0;
        }

        public static int ComputeAtomBonds(double[] coordsXyz, int atomCount, double maxBondDist, int[] outBondsA, int[] outBondsB, int maxBonds)
        {
            if (_isAvailable)
            {
                try
                {
                    return native_compute_atom_bonds(coordsXyz, atomCount, maxBondDist, outBondsA, outBondsB, maxBonds);
                }
                catch { }
            }
            return 0;
        }

        #region P/Invoke Signatures

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern int native_get_engine_info(byte[] outBuf, int maxLen);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern double native_calc_yield_strength(double baseSigma, double ky, double grainSizeUm, double sss, double tempK);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern double native_calc_lattice_distortion(double[] radiiPm, double[] fractions, int count);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern double native_calc_mixing_entropy(double[] fractions, int count);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern double native_calc_valence_electron_concentration(double[] vecValues, double[] fractions, int count);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern double native_calc_thermal_conductivity(double lorentzNum, double electricalResistivity, double tempK, double latticeK);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        private static extern int native_compute_atom_bonds(double[] coordsXyz, int atomCount, double maxBondDist, int[] outBondsA, int[] outBondsB, int maxBonds);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern IntPtr native_create_dx11_host_window(IntPtr hParent, int width, int height);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern void native_resize_dx11_host_window(IntPtr hWnd, int width, int height);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern void native_render_dx11_host_frame(IntPtr hWnd);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern void native_destroy_dx11_host_window(IntPtr hWnd);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern void native_set_dx11_crystal_phase(IntPtr hWnd, [MarshalAs(UnmanagedType.LPStr)] string phaseName, [MarshalAs(UnmanagedType.LPStr)] string crystalSystem, double a, double b, double c, int supercellN);

        [DllImport(NativeDll, CallingConvention = CallingConvention.Cdecl)]
        public static extern void native_update_dx11_camera(IntPtr hWnd, float azimuthDeg, float pitchDeg, float zoomScale);

        #endregion
    }
}
