using System;
using System.Runtime.InteropServices;

namespace PyCalphadSuite.Core.DataStructures
{
    /// <summary>
    /// 64-byte Cacheline / AVX-512 Aligned Unmanaged Thermodynamic Batch Buffer.
    /// Employs a Structure of Arrays (SoA) memory architecture to eliminate cache-line false sharing
    /// and enable zero-copy SIMD vectorization across C, C++, and C# (.NET 8).
    /// </summary>
    public sealed unsafe class NativeThermodynamicBatch : IDisposable
    {
        private double* _buffer;
        private readonly nuint _byteSize;
        private bool _disposed;

        public int Capacity { get; }

        public Span<double> Temperatures => CheckDisposed(new Span<double>(_buffer, Capacity));
        public Span<double> Pressures => CheckDisposed(new Span<double>(_buffer + Capacity, Capacity));
        public Span<double> GibbsEnergies => CheckDisposed(new Span<double>(_buffer + (2 * Capacity), Capacity));
        public Span<double> Entropies => CheckDisposed(new Span<double>(_buffer + (3 * Capacity), Capacity));
        public Span<double> HeatCapacities => CheckDisposed(new Span<double>(_buffer + (4 * Capacity), Capacity));

        /// <summary>
        /// Unmanaged raw pointer to the base contiguous buffer for direct C/C++ ABI passing.
        /// </summary>
        public double* RawPointer => _buffer;

        public NativeThermodynamicBatch(int capacity)
        {
            if (capacity <= 0)
                throw new ArgumentOutOfRangeException(nameof(capacity), "Capacity must be positive.");

            Capacity = capacity;
            // 5 contiguous channels: T, P, G, S, Cp
            _byteSize = (nuint)(capacity * 5 * sizeof(double));
            _buffer = (double*)NativeMemory.AlignedAlloc(_byteSize, 64);
            NativeMemory.Clear(_buffer, _byteSize);
        }

        private Span<double> CheckDisposed(Span<double> span)
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            return span;
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                if (_buffer != null)
                {
                    NativeMemory.AlignedFree(_buffer);
                    _buffer = null;
                }
                _disposed = true;
            }
            GC.SuppressFinalize(this);
        }

        ~NativeThermodynamicBatch()
        {
            Dispose();
        }
    }
}
