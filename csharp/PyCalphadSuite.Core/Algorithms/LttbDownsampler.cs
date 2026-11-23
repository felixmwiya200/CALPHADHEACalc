using System;

namespace PyCalphadSuite.Core.Algorithms
{
    /// <summary>
    /// Largest Triangle Three Buckets (LTTB) Downsampling Algorithm.
    /// Downsamples ultra-dense time-series and temperature sweeps (100,000+ points)
    /// to screen-pixel resolution in O(N) linear time with zero memory allocations,
    /// rigorously preserving latent heat peaks, invariant arrests, and inflection points.
    /// </summary>
    public static class LttbDownsampler
    {
        /// <summary>
        /// Downsamples input series (x, y) into preallocated output spans (outX, outY).
        /// </summary>
        /// <param name="x">Input strictly monotonic abscissa array (e.g. Temperature or Time).</param>
        /// <param name="y">Input ordinate values.</param>
        /// <param name="outX">Preallocated span to receive downsampled abscissae.</param>
        /// <param name="outY">Preallocated span to receive downsampled ordinates.</param>
        /// <param name="threshold">Target downsampled point count (must be >= 3 and <= input length).</param>
        public static void Downsample(
            ReadOnlySpan<double> x,
            ReadOnlySpan<double> y,
            Span<double> outX,
            Span<double> outY,
            int threshold)
        {
            int n = x.Length;
            if (n != y.Length)
                throw new ArgumentException("Input x and y spans must have identical length.");
            if (outX.Length < threshold || outY.Length < threshold)
                throw new ArgumentException("Output spans must be at least as large as the target threshold.");

            // If input is smaller than or equal to threshold, copy directly
            if (threshold >= n || threshold <= 2)
            {
                x.CopyTo(outX[..n]);
                y.CopyTo(outY[..n]);
                return;
            }

            // Always preserve the very first point
            outX[0] = x[0];
            outY[0] = y[0];

            double bucketSize = (double)(n - 2) / (threshold - 2);
            int a = 0; // Index of selected point from the previous bucket

            for (int i = 0; i < threshold - 2; i++)
            {
                // Calculate centroid average of next bucket (bucket i + 1)
                int cStart = (int)Math.Floor((i + 1) * bucketSize) + 1;
                int cEnd = Math.Min((int)Math.Floor((i + 2) * bucketSize) + 1, n);

                double avgX = 0.0;
                double avgY = 0.0;
                int cCount = cEnd - cStart;
                if (cCount <= 0)
                {
                    avgX = x[Math.Min(cStart, n - 1)];
                    avgY = y[Math.Min(cStart, n - 1)];
                }
                else
                {
                    for (int c = cStart; c < cEnd; c++)
                    {
                        avgX += x[c];
                        avgY += y[c];
                    }
                    avgX /= cCount;
                    avgY /= cCount;
                }

                // Range of current bucket i
                int bStart = (int)Math.Floor(i * bucketSize) + 1;
                int bEnd = (int)Math.Floor((i + 1) * bucketSize) + 1;

                double maxArea = -1.0;
                int maxIdx = bStart;

                double ax = x[a];
                double ay = y[a];

                // Find point in current bucket maximizing triangular area with point 'a' and centroid (avgX, avgY)
                for (int b = bStart; b < bEnd && b < n; b++)
                {
                    // Triangle area = 0.5 * |(Ax - AvgX)*(Yb - Ay) - (Ax - Xb)*(AvgY - Ay)|
                    double area = Math.Abs(((ax - avgX) * (y[b] - ay)) - ((ax - x[b]) * (avgY - ay)));
                    if (area > maxArea)
                    {
                        maxArea = area;
                        maxIdx = b;
                    }
                }

                outX[i + 1] = x[maxIdx];
                outY[i + 1] = y[maxIdx];
                a = maxIdx;
            }

            // Always preserve the very last point
            outX[threshold - 1] = x[n - 1];
            outY[threshold - 1] = y[n - 1];
        }

        /// <summary>
        /// Convenience downsampling overload returning newly allocated arrays.
        /// </summary>
        public static (double[] X, double[] Y) Downsample(double[] x, double[] y, int threshold)
        {
            if (x.Length <= threshold)
            {
                return ((double[])x.Clone(), (double[])y.Clone());
            }

            var outX = new double[threshold];
            var outY = new double[threshold];
            Downsample(x.AsSpan(), y.AsSpan(), outX.AsSpan(), outY.AsSpan(), threshold);
            return (outX, outY);
        }
    }
}
