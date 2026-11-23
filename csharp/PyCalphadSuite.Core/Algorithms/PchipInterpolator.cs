using System;

namespace PyCalphadSuite.Core.Algorithms
{
    /// <summary>
    /// Monotone Piecewise Cubic Hermite Interpolating Polynomial (PCHIP / Fritsch-Carlson / Fritsch-Butland).
    /// Preserves strict monotonicity and local shape of scientific curves (phase fractions, cooling curves,
    /// enthalpy, and solid fraction trajectories) without non-physical Gibbs oscillations or negative overshoots.
    /// </summary>
    public sealed class PchipInterpolator
    {
        private readonly double[] _x;
        private readonly double[] _y;
        private readonly double[] _d; // Hermite derivative slopes at knot nodes
        private readonly int _n;

        public int Count => _n;

        public PchipInterpolator(double[] x, double[] y)
        {
            if (x == null) throw new ArgumentNullException(nameof(x));
            if (y == null) throw new ArgumentNullException(nameof(y));
            if (x.Length != y.Length)
                throw new ArgumentException("Array dimensions must match.", nameof(y));
            if (x.Length < 2)
                throw new ArgumentException("At least two data points are required.", nameof(x));

            _n = x.Length;
            _x = (double[])x.Clone();
            _y = (double[])y.Clone();
            _d = new double[_n];

            ComputeSlopes();
        }

        private void ComputeSlopes()
        {
            var h = new double[_n - 1];
            var delta = new double[_n - 1];

            for (int i = 0; i < _n - 1; i++)
            {
                h[i] = _x[i + 1] - _x[i];
                if (h[i] <= 0.0)
                {
                    throw new ArgumentException(
                        $"Knot abscissae must be strictly monotonically increasing. Non-increasing step detected at index {i}: {_x[i]} >= {_x[i + 1]}.",
                        nameof(_x));
                }
                delta[i] = (_y[i + 1] - _y[i]) / h[i];
            }

            // Endpoints: one-sided shape-preserving derivative estimates
            _d[0] = ComputeEndpointSlope(h[0], h.Length > 1 ? h[1] : h[0], delta[0], delta.Length > 1 ? delta[1] : delta[0]);
            _d[_n - 1] = ComputeEndpointSlope(h[_n - 2], _n >= 3 ? h[_n - 3] : h[_n - 2], delta[_n - 2], _n >= 3 ? delta[_n - 3] : delta[_n - 2]);

            // Interior knot points via Fritsch-Butland weighted harmonic slope limiter
            for (int i = 1; i < _n - 1; i++)
            {
                if (delta[i - 1] * delta[i] <= 0.0)
                {
                    // Local extremum: flat slope ensures strict monotonicity preservation
                    _d[i] = 0.0;
                }
                else
                {
                    // Weighted harmonic mean prevents overshoot while retaining curvature
                    double w1 = 2.0 * h[i] + h[i - 1];
                    double w2 = h[i] + 2.0 * h[i - 1];
                    _d[i] = (w1 + w2) / ((w1 / delta[i - 1]) + (w2 / delta[i]));
                }
            }
        }

        private static double ComputeEndpointSlope(double h1, double h2, double del1, double del2)
        {
            double d = (((2.0 * h1) + h2) * del1 - h1 * del2) / (h1 + h2);
            if (Math.Sign(d) != Math.Sign(del1))
            {
                d = 0.0;
            }
            else if (Math.Sign(del1) != Math.Sign(del2) && Math.Abs(d) > Math.Abs(3.0 * del1))
            {
                d = 3.0 * del1;
            }
            return d;
        }

        /// <summary>
        /// Evaluates the monotone interpolant at a single abscissa point xVal.
        /// </summary>
        public double Interpolate(double xVal)
        {
            if (xVal <= _x[0]) return _y[0];
            if (xVal >= _x[_n - 1]) return _y[_n - 1];

            int idx = FindInterval(xVal);
            return EvaluateCubic(idx, xVal);
        }

        /// <summary>
        /// High-throughput vectorized or contiguous span evaluation with zero heap allocations.
        /// </summary>
        public void Interpolate(ReadOnlySpan<double> xIn, Span<double> yOut)
        {
            if (xIn.Length != yOut.Length)
                throw new ArgumentException("Input and output span lengths must be identical.");

            for (int i = 0; i < xIn.Length; i++)
            {
                yOut[i] = Interpolate(xIn[i]);
            }
        }

        /// <summary>
        /// Evaluates both the interpolant and its analytical derivative (e.g. Cp = dH/dT).
        /// </summary>
        public (double Value, double Derivative) InterpolateWithDerivative(double xVal)
        {
            if (xVal <= _x[0]) return (_y[0], _d[0]);
            if (xVal >= _x[_n - 1]) return (_y[_n - 1], _d[_n - 1]);

            int idx = FindInterval(xVal);
            double h = _x[idx + 1] - _x[idx];
            double t = (xVal - _x[idx]) / h;
            double t2 = t * t;
            double t3 = t2 * t;

            // Hermite basis functions
            double h00 = (2.0 * t3) - (3.0 * t2) + 1.0;
            double h10 = t3 - (2.0 * t2) + t;
            double h01 = (-2.0 * t3) + (3.0 * t2);
            double h11 = t3 - t2;

            double val = (h00 * _y[idx]) + (h10 * h * _d[idx]) + (h01 * _y[idx + 1]) + (h11 * h * _d[idx + 1]);

            // Derivative basis functions
            double dh00 = (6.0 * t2) - (6.0 * t);
            double dh10 = (3.0 * t2) - (4.0 * t) + 1.0;
            double dh01 = (-6.0 * t2) + (6.0 * t);
            double dh11 = (3.0 * t2) - (2.0 * t);

            double deriv = ((dh00 * _y[idx]) + (dh10 * h * _d[idx]) + (dh01 * _y[idx + 1]) + (dh11 * h * _d[idx + 1])) / h;

            return (val, deriv);
        }

        private int FindInterval(double xVal)
        {
            int low = 0;
            int high = _n - 2;

            while (low <= high)
            {
                int mid = low + ((high - low) >> 1);
                if (_x[mid] <= xVal && xVal <= _x[mid + 1])
                {
                    return mid;
                }
                if (_x[mid] < xVal)
                {
                    low = mid + 1;
                }
                else
                {
                    high = mid - 1;
                }
            }

            return Math.Clamp(low, 0, _n - 2);
        }

        private double EvaluateCubic(int i, double xVal)
        {
            double h = _x[i + 1] - _x[i];
            double t = (xVal - _x[i]) / h;
            double t2 = t * t;
            double t3 = t2 * t;

            double h00 = (2.0 * t3) - (3.0 * t2) + 1.0;
            double h10 = t3 - (2.0 * t2) + t;
            double h01 = (-2.0 * t3) + (3.0 * t2);
            double h11 = t3 - t2;

            return (h00 * _y[i]) + (h10 * h * _d[i]) + (h01 * _y[i + 1]) + (h11 * h * _d[i + 1]);
        }
    }
}
