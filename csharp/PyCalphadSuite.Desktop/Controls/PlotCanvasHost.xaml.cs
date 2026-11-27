// <copyright file="PlotCanvasHost.xaml.cs" company="PyCALPHAD Materials CAE">
// OriginLab-grade ScottPlot 5 canvas host with interactive navigation, DPI export, and CSV extraction.
// </copyright>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using PyCalphadSuite.Core.Services;
using ScottPlot;

namespace PyCalphadSuite.Desktop.Controls
{
    public partial class PlotCanvasHost : UserControl
    {
        private bool _gridVisible = true;
        private bool _hasLimits = false;
        private double _xMin, _xMax, _yMin, _yMax;
        private bool _isDarkTheme = false;
        private ScottPlot.Plottables.Crosshair? _crosshair;

        private string _plotTitle = "Scientific Property Visualization";
        private string _xAxisTitle = "X";
        private string _yAxisTitle = "Y";
        private readonly List<(string Name, double[] Xs, double[] Ys)> _exportSeries = new();
        private readonly List<string> _metadataLines = new();

        public string ExportBaseName { get; set; } = "CALPHAD_Plot";
        public string PlotTitle => _plotTitle;
        public string XAxisTitle => _xAxisTitle;
        public string YAxisTitle => _yAxisTitle;
        public IReadOnlyList<(string Name, double[] Xs, double[] Ys)> ExportSeries => _exportSeries;
        public IReadOnlyList<string> MetadataLines => _metadataLines;

        public string HeaderTitle
        {
            get => TxtHeaderTitle.Text;
            set => TxtHeaderTitle.Text = value;
        }

        public string HeaderSummary
        {
            get => TxtHeaderSummary.Text;
            set => TxtHeaderSummary.Text = value;
        }

        public Plot Plot => WpfPlotControl.Plot;

        public PlotCanvasHost()
        {
            InitializeComponent();
        }

        public void Refresh()
        {
            WpfPlotControl.Refresh();
        }

        public void ClearExportSeries()
        {
            _exportSeries.Clear();
        }

        public void AddMetadata(string line)
        {
            if (!string.IsNullOrWhiteSpace(line))
            {
                _metadataLines.Add(line);
            }
        }

        public void ClearMetadata()
        {
            _metadataLines.Clear();
        }

        public void AddExportSeries(string name, IEnumerable<double> xs, IEnumerable<double> ys)
        {
            _exportSeries.Add((name, xs.ToArray(), ys.ToArray()));
        }

        public void ApplyOtisLiuStyle(string title, string xLabel, string yLabel, bool darkTheme = false)
        {
            _isDarkTheme = darkTheme;
            _plotTitle = title;
            _xAxisTitle = xLabel;
            _yAxisTitle = yLabel;
            var plot = WpfPlotControl.Plot;
            plot.Clear();
            ClearExportSeries();
            ClearMetadata();

            if (darkTheme)
            {
                plot.FigureBackground.Color = ScottPlot.Color.FromHex("#12161F");
                plot.DataBackground.Color = ScottPlot.Color.FromHex("#0D1117");
                plot.Axes.Color(ScottPlot.Color.FromHex("#8B949E"));
                plot.Grid.MajorLineColor = ScottPlot.Color.FromHex("#212631");
                plot.Legend.BackgroundColor = ScottPlot.Color.FromHex("#161B22").WithAlpha(0.92);
                plot.Legend.OutlineColor = ScottPlot.Color.FromHex("#30363D");
                plot.Legend.FontColor = ScottPlot.Color.FromHex("#F0F6FC");

                RootGrid.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#0D1117"));
                HeaderBorder.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#161B22"));
                HeaderBorder.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#30363D"));
                ToolbarBorder.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#161B22"));
                ToolbarBorder.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#30363D"));
                TxtHeaderTitle.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#F0F6FC"));
                if (BadgeSummary != null)
                {
                    BadgeSummary.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#1E293B"));
                    BadgeSummary.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#38BDF8"));
                }
                TxtHeaderSummary.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#38BDF8"));
                if (CoordsBadge != null)
                {
                    CoordsBadge.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#21262D"));
                    CoordsBadge.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#30363D"));
                }
                TxtCursorCoords.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#38BDF8"));

                var btnBg = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#21262D"));
                var btnFg = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#F0F6FC"));
                var btnBorder = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#30363D"));
                BtnHome.Background = btnBg; BtnHome.Foreground = btnFg; BtnHome.BorderBrush = btnBorder;
                BtnZoomIn.Background = btnBg; BtnZoomIn.Foreground = btnFg; BtnZoomIn.BorderBrush = btnBorder;
                BtnZoomOut.Background = btnBg; BtnZoomOut.Foreground = btnFg; BtnZoomOut.BorderBrush = btnBorder;
                BtnGrid.Background = btnBg; BtnGrid.Foreground = btnFg; BtnGrid.BorderBrush = btnBorder;
                BtnCopy.Background = btnBg; BtnCopy.Foreground = btnFg; BtnCopy.BorderBrush = btnBorder;
                BtnExportImg.Background = btnBg; BtnExportImg.Foreground = btnFg; BtnExportImg.BorderBrush = btnBorder;
                BtnExportCsv.Background = btnBg; BtnExportCsv.Foreground = btnFg; BtnExportCsv.BorderBrush = btnBorder;
            }
            else
            {
                plot.FigureBackground.Color = ScottPlot.Colors.White;
                plot.DataBackground.Color = ScottPlot.Color.FromHex("#F8FAFC");
                plot.Axes.Color(ScottPlot.Color.FromHex("#475569"));
                plot.Grid.MajorLineColor = ScottPlot.Color.FromHex("#E2E8F0");
                plot.Legend.BackgroundColor = ScottPlot.Colors.White.WithAlpha(0.94);
                plot.Legend.OutlineColor = ScottPlot.Color.FromHex("#CBD5E1");
                plot.Legend.FontColor = ScottPlot.Color.FromHex("#0F172A");

                RootGrid.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#F8FAFC"));
                HeaderBorder.Background = Brushes.White;
                HeaderBorder.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#E2E8F0"));
                ToolbarBorder.Background = Brushes.White;
                ToolbarBorder.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#E2E8F0"));
                TxtHeaderTitle.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#0F172A"));
                if (BadgeSummary != null)
                {
                    BadgeSummary.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#E0F2FE"));
                    BadgeSummary.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#BAE6FD"));
                }
                TxtHeaderSummary.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#0284C7"));
                if (CoordsBadge != null)
                {
                    CoordsBadge.Background = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#E5E7EB"));
                    CoordsBadge.BorderBrush = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#9CA3AF"));
                }
                TxtCursorCoords.Foreground = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#000000"));

                var btnBg = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#F1F5F9"));
                var btnFg = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#0F172A"));
                var btnBorder = new SolidColorBrush((System.Windows.Media.Color)ColorConverter.ConvertFromString("#CBD5E1"));
                BtnHome.Background = btnBg; BtnHome.Foreground = btnFg; BtnHome.BorderBrush = btnBorder;
                BtnZoomIn.Background = btnBg; BtnZoomIn.Foreground = btnFg; BtnZoomIn.BorderBrush = btnBorder;
                BtnZoomOut.Background = btnBg; BtnZoomOut.Foreground = btnFg; BtnZoomOut.BorderBrush = btnBorder;
                BtnGrid.Background = btnBg; BtnGrid.Foreground = btnFg; BtnGrid.BorderBrush = btnBorder;
                BtnCopy.Background = btnBg; BtnCopy.Foreground = btnFg; BtnCopy.BorderBrush = btnBorder;
                BtnExportImg.Background = btnBg; BtnExportImg.Foreground = btnFg; BtnExportImg.BorderBrush = btnBorder;
                BtnExportCsv.Background = btnBg; BtnExportCsv.Foreground = btnFg; BtnExportCsv.BorderBrush = btnBorder;
            }

            plot.Grid.MajorLineWidth = 1.0f;
            plot.Axes.Title.Label.Text = title;
            plot.Axes.Title.Label.Bold = true;
            plot.Axes.Title.Label.FontSize = 13.5f;

            plot.Axes.Bottom.Label.Text = xLabel;
            plot.Axes.Bottom.Label.Bold = true;
            plot.Axes.Bottom.Label.FontSize = 11.5f;
            plot.Axes.Bottom.TickLabelStyle.FontSize = 10.5f;

            plot.Axes.Left.Label.Text = yLabel;
            plot.Axes.Left.Label.Bold = true;
            plot.Axes.Left.Label.FontSize = 11.5f;
            plot.Axes.Left.TickLabelStyle.FontSize = 10.5f;

            plot.Grid.IsVisible = _gridVisible;

            var existingLegendPanels = plot.Axes.GetPanels().OfType<ScottPlot.Panels.LegendPanel>().ToList();
            foreach (var p in existingLegendPanels)
            {
                plot.Axes.Remove(p);
            }
            plot.ShowLegend(Edge.Right);
            plot.Legend.FontSize = 10.0f;

            _crosshair = plot.Add.Crosshair(0, 0);
            _crosshair.IsVisible = false;
            _crosshair.LineColor = darkTheme
                ? ScottPlot.Color.FromHex("#94A3B8").WithAlpha(0.75)
                : ScottPlot.Color.FromHex("#64748B").WithAlpha(0.75);
            _crosshair.LineWidth = 1.0f;
            _crosshair.LinePattern = LinePattern.Dashed;
        }

        public void SetLimitsAndRemember(double xMin, double xMax, double yMin, double yMax)
        {
            if (Math.Abs(xMax - xMin) < 1e-9) { xMax = xMin + 1.0; }
            if (Math.Abs(yMax - yMin) < 1e-9) { yMax = yMin + 1.0; }

            _xMin = xMin;
            _xMax = xMax;
            _yMin = yMin;
            _yMax = yMax;
            _hasLimits = true;

            WpfPlotControl.Plot.Axes.SetLimits(xMin, xMax, yMin, yMax);
        }

        private void BtnHome_Click(object sender, RoutedEventArgs e)
        {
            if (_hasLimits)
            {
                WpfPlotControl.Plot.Axes.SetLimits(_xMin, _xMax, _yMin, _yMax);
            }
            else
            {
                WpfPlotControl.Plot.Axes.AutoScale();
            }
            WpfPlotControl.Refresh();
        }

        private void BtnZoomIn_Click(object sender, RoutedEventArgs e)
        {
            WpfPlotControl.Plot.Axes.Zoom(1.25, 1.25);
            WpfPlotControl.Refresh();
        }

        private void BtnZoomOut_Click(object sender, RoutedEventArgs e)
        {
            WpfPlotControl.Plot.Axes.Zoom(0.8, 0.8);
            WpfPlotControl.Refresh();
        }

        private void BtnGrid_Click(object sender, RoutedEventArgs e)
        {
            _gridVisible = !_gridVisible;
            BtnGrid.Content = _gridVisible ? "Grid: On" : "Grid: Off";
            WpfPlotControl.Plot.Grid.IsVisible = _gridVisible;
            WpfPlotControl.Refresh();
        }

        private void BtnCopy_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var bytes = WpfPlotControl.Plot.GetImageBytes(1400, 850, ScottPlot.ImageFormat.Png);
                using var ms = new MemoryStream(bytes);
                var bmp = new BitmapImage();
                bmp.BeginInit();
                bmp.CacheOption = BitmapCacheOption.OnLoad;
                bmp.StreamSource = ms;
                bmp.EndInit();
                bmp.Freeze();
                Clipboard.SetImage(bmp);
                TxtHeaderSummary.Text = "Graph copied to Clipboard (1400×850 PNG)";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Clipboard copy error: {ex.Message}", "Copy Failed", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void BtnExportImg_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SaveFileDialog
            {
                FileName = $"{ExportBaseName}_{DateTime.Now:yyyyMMdd_HHmm}",
                Filter = "PNG Publication Image (*.png)|*.png|Scalable Vector Graphics (*.svg)|*.svg|JPEG Image (*.jpg)|*.jpg"
            };
            if (dlg.ShowDialog() != true) return;

            try
            {
                var ext = Path.GetExtension(dlg.FileName).ToLowerInvariant();
                if (ext == ".svg")
                {
                    WpfPlotControl.Plot.SaveSvg(dlg.FileName, 1400, 850);
                }
                else if (ext == ".jpg")
                {
                    WpfPlotControl.Plot.SaveJpeg(dlg.FileName, 1400, 850, 95);
                }
                else
                {
                    WpfPlotControl.Plot.SavePng(dlg.FileName, 1400, 850);
                }
                TxtHeaderSummary.Text = $"Saved image: {Path.GetFileName(dlg.FileName)}";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Image export error: {ex.Message}", "Export Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        public byte[] RenderPngBytes(int width = 1400, int height = 850)
        {
            return WpfPlotControl.Plot.GetImageBytes(width, height, ScottPlot.ImageFormat.Png);
        }

        public bool HasExportSeries => _exportSeries.Count > 0;

        public string BuildCsvContent()
            => PlotCsvFormatter.BuildCsvContent(_plotTitle, _xAxisTitle, _yAxisTitle, _exportSeries, _metadataLines);

        private void BtnExportCsv_Click(object sender, RoutedEventArgs e)
        {
            if (_exportSeries.Count == 0)
            {
                MessageBox.Show("No plotted numerical series available yet. Run a calculation first.", "Export CSV", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dlg = new SaveFileDialog
            {
                FileName = $"{ExportBaseName}_RawData.csv",
                Filter = "OriginLab / Excel CSV (*.csv)|*.csv"
            };
            if (dlg.ShowDialog() != true) return;

            try
            {
                File.WriteAllText(dlg.FileName, BuildCsvContent(), Encoding.UTF8);
                TxtHeaderSummary.Text = $"Exported CSV: {Path.GetFileName(dlg.FileName)}";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"CSV export error: {ex.Message}", "Export Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void WpfPlotControl_MouseMove(object sender, MouseEventArgs e)
        {
            try
            {
                var pos = e.GetPosition(WpfPlotControl);
                var dpi = VisualTreeHelper.GetDpi(WpfPlotControl);
                Pixel px = new((float)(pos.X * dpi.DpiScaleX), (float)(pos.Y * dpi.DpiScaleY));
                Coordinates coords = WpfPlotControl.Plot.GetCoordinates(px);

                if (_crosshair != null)
                {
                    _crosshair.Position = coords;
                    _crosshair.IsVisible = true;
                    WpfPlotControl.Refresh();
                }

                string nearestInfo = FindNearestSeriesInfo(coords);
                TxtCursorCoords.Text = string.IsNullOrEmpty(nearestInfo)
                    ? $"X: {coords.X:G5}   Y: {coords.Y:G5}"
                    : $"X: {coords.X:G5}   Y: {coords.Y:G5}   |   {nearestInfo}";
            }
            catch
            {
                // Ignore coordinate probe errors before plot render
            }
        }

        private void WpfPlotControl_MouseLeave(object sender, MouseEventArgs e)
        {
            if (_crosshair != null && _crosshair.IsVisible)
            {
                _crosshair.IsVisible = false;
                WpfPlotControl.Refresh();
            }
            TxtCursorCoords.Text = "X: --   Y: --";
        }

        private string FindNearestSeriesInfo(Coordinates coords)
        {
            if (_exportSeries.Count == 0) return string.Empty;

            var limits = WpfPlotControl.Plot.Axes.GetLimits();
            double xSpan = Math.Max(1e-9, Math.Abs(limits.Right - limits.Left));
            double ySpan = Math.Max(1e-9, Math.Abs(limits.Top - limits.Bottom));

            double bestDist2 = double.MaxValue;
            string bestName = string.Empty;
            double bestX = 0.0, bestY = 0.0;

            foreach (var s in _exportSeries)
            {
                int n = Math.Min(s.Xs.Length, s.Ys.Length);
                for (int i = 0; i < n; i++)
                {
                    double dx = (s.Xs[i] - coords.X) / xSpan;
                    double dy = (s.Ys[i] - coords.Y) / ySpan;
                    double d2 = (dx * dx) + (dy * dy);
                    if (d2 < bestDist2)
                    {
                        bestDist2 = d2;
                        bestName = s.Name;
                        bestX = s.Xs[i];
                        bestY = s.Ys[i];
                    }
                }
            }

            if (bestDist2 > 0.015 || string.IsNullOrEmpty(bestName)) return string.Empty;
            return $"{bestName}: ({bestX:G5}, {bestY:G5})";
        }
    }
}
