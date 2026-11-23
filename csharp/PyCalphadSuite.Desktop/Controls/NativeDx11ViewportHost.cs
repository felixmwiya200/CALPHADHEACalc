// <copyright file="NativeDx11ViewportHost.cs" company="PyCALPHAD Materials CAE">
// Embedded native C++ DirectX 11 hardware viewport seamlessly hosted inside WPF via HwndHost.
// </copyright>

using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using PyCalphadSuite.Core.Services;

namespace PyCalphadSuite.Desktop.Controls
{
    /// <summary>
    /// Hosts the native C++ DirectX 11 3D hardware viewport directly inside the WPF visual tree.
    /// Eliminates the need for multiple front-end windows by embedding C++ hardware rendering into C# WPF.
    /// </summary>
    public class NativeDx11ViewportHost : HwndHost
    {
        private IntPtr _hwndHost = IntPtr.Zero;

        public NativeDx11ViewportHost()
        {
            Loaded += (_, _) => InvalidateRender();
            SizeChanged += OnSizeChanged;
        }

        public IntPtr NativeHwnd => _hwndHost;

        protected override HandleRef BuildWindowCore(HandleRef hwndParent)
        {
            int w = (int)Math.Max(100, ActualWidth > 0 ? ActualWidth : 800);
            int h = (int)Math.Max(100, ActualHeight > 0 ? ActualHeight : 600);

            if (NativePolyglotCore.IsAvailable)
            {
                _hwndHost = NativePolyglotCore.native_create_dx11_host_window(hwndParent.Handle, w, h);
            }

            return new HandleRef(this, _hwndHost);
        }

        protected override void DestroyWindowCore(HandleRef hwnd)
        {
            if (_hwndHost != IntPtr.Zero && NativePolyglotCore.IsAvailable)
            {
                NativePolyglotCore.native_destroy_dx11_host_window(_hwndHost);
                _hwndHost = IntPtr.Zero;
            }
        }

        private void OnSizeChanged(object sender, SizeChangedEventArgs e)
        {
            if (_hwndHost != IntPtr.Zero && NativePolyglotCore.IsAvailable && e.NewSize.Width > 0 && e.NewSize.Height > 0)
            {
                NativePolyglotCore.native_resize_dx11_host_window(_hwndHost, (int)e.NewSize.Width, (int)e.NewSize.Height);
            }
        }

        public void UpdatePhase(string phaseName, string crystalSystem, double a, double b, double c, int supercellN)
        {
            if (_hwndHost != IntPtr.Zero && NativePolyglotCore.IsAvailable)
            {
                NativePolyglotCore.native_set_dx11_crystal_phase(_hwndHost, phaseName, crystalSystem, a, b, c, supercellN);
            }
        }

        public void InvalidateRender()
        {
            if (_hwndHost != IntPtr.Zero && NativePolyglotCore.IsAvailable)
            {
                NativePolyglotCore.native_render_dx11_host_frame(_hwndHost);
            }
        }
    }
}
