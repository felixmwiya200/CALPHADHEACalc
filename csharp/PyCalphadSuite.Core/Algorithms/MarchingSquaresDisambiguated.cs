using System;
using System.Collections.Generic;

namespace PyCalphadSuite.Core.Algorithms
{
    public readonly struct ContourPoint2D
    {
        public readonly double X;
        public readonly double Y;

        public ContourPoint2D(double x, double y)
        {
            X = x;
            Y = y;
        }
    }

    public readonly struct ContourSegment
    {
        public readonly ContourPoint2D Start;
        public readonly ContourPoint2D End;

        public ContourSegment(ContourPoint2D start, ContourPoint2D end)
        {
            Start = start;
            End = end;
        }
    }

    /// <summary>
    /// Topologically Disambiguated Marching Squares Contouring Engine.
    /// Incorporates the Nielson-Hamann Asymptotic Decider to eliminate unphysical reconnections
    /// and topological artifacts across hyperbolic saddle points in thermodynamic phase diagrams.
    /// </summary>
    public static class MarchingSquaresDisambiguated
    {
        /// <summary>
        /// Evaluates a single grid cell and appends generated line segments to destination list.
        /// </summary>
        public static void ContourCell(
            double x0, double y0, double dx, double dy,
            double f00, double f10, double f01, double f11,
            double isovalue,
            List<ContourSegment> destination)
        {
            int cellIndex = 0;
            if (f00 >= isovalue) cellIndex |= 1;
            if (f10 >= isovalue) cellIndex |= 2;
            if (f11 >= isovalue) cellIndex |= 4;
            if (f01 >= isovalue) cellIndex |= 8;

            // Completely below or completely above threshold -> no boundary
            if (cellIndex == 0 || cellIndex == 15) return;

            static ContourPoint2D Interpolate(double xA, double yA, double xB, double yB, double valA, double valB, double iso)
            {
                double denom = valB - valA;
                double t = Math.Abs(denom) < 1e-15 ? 0.5 : (iso - valA) / denom;
                t = Math.Clamp(t, 0.0, 1.0);
                return new ContourPoint2D(xA + (t * (xB - xA)), yA + (t * (yB - yA)));
            }

            var b = Interpolate(x0, y0, x0 + dx, y0, f00, f10, isovalue);          // Bottom edge (0)
            var r = Interpolate(x0 + dx, y0, x0 + dx, y0 + dy, f10, f11, isovalue);  // Right edge (1)
            var t = Interpolate(x0, y0 + dy, x0 + dx, y0 + dy, f01, f11, isovalue);  // Top edge (2)
            var l = Interpolate(x0, y0, x0, y0 + dy, f00, f01, isovalue);          // Left edge (3)

            // Asymptotic Decider for ambiguous cases 5 (0101) and 10 (1010)
            if (cellIndex == 5 || cellIndex == 10)
            {
                double denom = (f00 + f11) - (f10 + f01);
                double saddleVal = Math.Abs(denom) < 1e-14
                    ? 0.25 * (f00 + f10 + f01 + f11)
                    : ((f00 * f11) - (f10 * f01)) / denom;

                if (cellIndex == 5) // Corners (0,0) and (1,1) are >= isovalue
                {
                    if (saddleVal >= isovalue)
                    {
                        destination.Add(new ContourSegment(l, t));
                        destination.Add(new ContourSegment(b, r));
                    }
                    else
                    {
                        destination.Add(new ContourSegment(l, b));
                        destination.Add(new ContourSegment(t, r));
                    }
                    return;
                }
                else // cellIndex == 10: Corners (1,0) and (0,1) are >= isovalue
                {
                    if (saddleVal >= isovalue)
                    {
                        destination.Add(new ContourSegment(l, b));
                        destination.Add(new ContourSegment(t, r));
                    }
                    else
                    {
                        destination.Add(new ContourSegment(l, t));
                        destination.Add(new ContourSegment(b, r));
                    }
                    return;
                }
            }

            // Standard unambiguous cases
            switch (cellIndex)
            {
                case 1:
                case 14:
                    destination.Add(new ContourSegment(l, b));
                    break;
                case 2:
                case 13:
                    destination.Add(new ContourSegment(b, r));
                    break;
                case 3:
                case 12:
                    destination.Add(new ContourSegment(l, r));
                    break;
                case 4:
                case 11:
                    destination.Add(new ContourSegment(t, r));
                    break;
                case 6:
                case 9:
                    destination.Add(new ContourSegment(b, t));
                    break;
                case 7:
                case 8:
                    destination.Add(new ContourSegment(l, t));
                    break;
            }
        }
    }
}
