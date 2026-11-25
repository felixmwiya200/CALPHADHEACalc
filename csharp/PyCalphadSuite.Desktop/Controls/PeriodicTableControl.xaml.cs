// <copyright file="PeriodicTableControl.xaml.cs" company="PyCALPHAD Materials CAE">
// Complete 118-element interactive IUPAC Periodic Table in C# WPF matching high-contrast reference chart styling.
// </copyright>

using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Media;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Controls
{
    public partial class PeriodicTableControl : UserControl
    {
        private static readonly HashSet<string> HalogenSymbols = new(StringComparer.OrdinalIgnoreCase)
        {
            "F", "Cl", "Br", "I", "At", "Ts"
        };

        private readonly Dictionary<string, ToggleButton> _tiles = new(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, ElementDto> _elementData = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _selectedSymbols = new(StringComparer.OrdinalIgnoreCase);
        private string _activeCategory = "all";
        private bool _isDark = true;
        private List<ElementDto>? _cachedElements;

        public event Action<Dictionary<string, double>>? ApplyCompositionRequested;
        public event Action<IReadOnlyCollection<string>>? MergeCompositionRequested;

        public PeriodicTableControl()
        {
            InitializeComponent();
        }

        public void ApplyTheme(bool isDark)
        {
            _isDark = isDark;
            var bgHex = isDark ? "#202225" : "#FFFFFF";
            var barHex = isDark ? "#2B2D31" : "#F8FAFC";
            var borderHex = isDark ? "#3F4248" : "#CBD5E1";
            var fgHex = isDark ? "#F2F3F5" : "#0F172A";
            var mutedHex = isDark ? "#949BA4" : "#64748B";

            RootGrid.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex));
            HeaderBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(barHex));
            HeaderBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex));
            CategoryRibbonBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(barHex));
            CategoryRibbonBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex));
            BottomInspectorBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(barHex));
            BottomInspectorBorder.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex));
            ElementsScrollViewer.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex));

            TxtFilter.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(isDark ? "#202225" : "#FFFFFF"));
            TxtFilter.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex));
            TxtFilter.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex));
            TxtFilter.CaretBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex));

            TxtHeaderTitle.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex));
            TxtSelectedList.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex));
            TxtHoverInfo.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(mutedHex));

            SyncRibbonCategoryButtons();

            if (_cachedElements != null && _cachedElements.Count > 0)
            {
                var currentSelected = _selectedSymbols.ToList();
                PopulateElements(_cachedElements);
                SyncSelectedElements(currentSelected);
            }
        }

        public void PopulateElements(List<ElementDto> elements)
        {
            _cachedElements = elements;
            GridElements.Children.Clear();
            GridElements.RowDefinitions.Clear();
            GridElements.ColumnDefinitions.Clear();
            _tiles.Clear();
            _elementData.Clear();

            // Row 0: Group headers | Rows 1..7: Periods 1..7 | Row 8: Spacer | Rows 9..10: Lanthanides & Actinides
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(24) });
            for (int r = 1; r <= 7; r++)
            {
                GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(68) });
            }
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(12) });
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(68) });
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(68) });

            // Col 0: Period numbers | Cols 1..18: IUPAC Groups 1..18
            GridElements.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(36) });
            for (int c = 1; c <= 18; c++)
            {
                GridElements.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(74) });
            }

            string[] groupLabels =
            {
                "1 IA", "2 IIA", "3 IIIB", "4 IVB", "5 VB", "6 VIB", "7 VIIB",
                "8 VIII", "9 VIII", "10 VIII", "11 IB", "12 IIB",
                "13 IIIA", "14 IVA", "15 VA", "16 VIA", "17 VIIA", "18 VIIIA"
            };
            var grCorner = new TextBlock
            {
                Text = "Gr.",
                FontSize = 9.5,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#949BA4" : "#64748B")),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetRow(grCorner, 0);
            Grid.SetColumn(grCorner, 0);
            GridElements.Children.Add(grCorner);

            for (int c = 0; c < 18; c++)
            {
                var gLbl = new TextBlock
                {
                    Text = groupLabels[c],
                    FontSize = 9,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#949BA4" : "#64748B")),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                Grid.SetRow(gLbl, 0);
                Grid.SetColumn(gLbl, c + 1);
                GridElements.Children.Add(gLbl);
            }

            for (int p = 1; p <= 7; p++)
            {
                var pLbl = new TextBlock
                {
                    Text = p.ToString(),
                    FontSize = 10,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#949BA4" : "#64748B")),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                Grid.SetRow(pLbl, p);
                Grid.SetColumn(pLbl, 0);
                GridElements.Children.Add(pLbl);
            }

            // Center Banner: Faithful Reference Chart Anatomy Sample & 10-Category Legend (Rows 1..3, Cols 3..12)
            var centerBanner = BuildCenterBanner();
            Grid.SetRow(centerBanner, 1);
            Grid.SetColumn(centerBanner, 3);
            Grid.SetRowSpan(centerBanner, 3);
            Grid.SetColumnSpan(centerBanner, 10);
            GridElements.Children.Add(centerBanner);

            // Lanthanide & Actinide Series Placeholders
            AddSeriesMarker(6, 3, "57–71 *\nLa–Lu\nLanthanides", "#FEFBCB", "#000000", "#000000");
            AddSeriesMarker(7, 3, "89–103 **\nAc–Lr\nActinides", "#FAC2A4", "#000000", "#000000");
            AddSeriesRowLabel(9, "* Lanthanides");
            AddSeriesRowLabel(10, "** Actinides");

            foreach (var el in elements)
            {
                _elementData[el.Symbol] = el;

                int rowIdx = Math.Clamp(el.GridRow, 1, 10);
                int colIdx = Math.Clamp(el.GridCol, 1, 18);

                string resolvedCat = ResolveCategory(el);
                var (bgHex, borderHex, fgHex) = GetCategoryPalette(resolvedCat, el.Symbol);
                string shortName = el.Name;
                double tmC = el.TmK - 273.15;

                var tb = new ToggleButton
                {
                    Style = (Style)FindResource("ElementTileButtonStyle"),
                    Margin = new Thickness(0.8),
                    Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex)),
                    BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex)),
                    BorderThickness = new Thickness(1.2),
                    Tag = el.Symbol,
                    Cursor = System.Windows.Input.Cursors.Hand,
                    ToolTip = $"{el.Name} ({el.Symbol}) | Z={el.Z}\n" +
                              $"Category: {FormatCategoryName(resolvedCat)}\n" +
                              $"Atomic Mass: {el.AtomicMass:F3} g/mol | VEC: {el.Vec:F1}\n" +
                              $"Structure: {el.CrystalStructure} | Tm: {el.TmK:F1} K ({tmC:F1} °C)\n" +
                              $"Density: {el.DensityGCm3:F3} g/cm³ | E: {el.YoungsModulusGpa:F1} GPa"
                };

                // 4-row layout matching reference chart cell anatomy
                var tileGrid = new Grid();
                tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(14) });
                tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(28) });
                tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(13) });
                tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(13) });

                // Row 0: Top Dock with Selection Badge (Left) and Atomic Number Z (Right)
                var topDock = new DockPanel { LastChildFill = false };
                Grid.SetRow(topDock, 0);

                var txtCheck = new TextBlock
                {
                    Name = "TxtCheck",
                    Text = "✓",
                    FontSize = 9.0,
                    FontWeight = FontWeights.ExtraBold,
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1D4ED8")),
                    Margin = new Thickness(3, 0, 0, 0),
                    Visibility = Visibility.Collapsed
                };
                DockPanel.SetDock(txtCheck, Dock.Left);
                topDock.Children.Add(txtCheck);

                var txtZ = new TextBlock
                {
                    Text = el.Z.ToString(),
                    FontSize = 8.5,
                    FontWeight = FontWeights.Bold,
                    Foreground = Brushes.Black,
                    Margin = new Thickness(0, 1, 3, 0)
                };
                DockPanel.SetDock(txtZ, Dock.Right);
                topDock.Children.Add(txtZ);
                tileGrid.Children.Add(topDock);

                // Row 1: Symbol (Prominent, Bold, Centered)
                var txtSym = new TextBlock
                {
                    Text = el.Symbol,
                    FontSize = el.Symbol.Length switch
                    {
                        1 => 21.0,
                        2 => 19.0,
                        _ => 15.0
                    },
                    FontWeight = FontWeights.Bold,
                    Foreground = Brushes.Black,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, -2, 0, 0)
                };
                Grid.SetRow(txtSym, 1);
                tileGrid.Children.Add(txtSym);

                // Row 2: Element Name (Sentence Case, Centered)
                double nameFontSize = shortName.Length switch
                {
                    >= 14 => 5.0,
                    >= 12 => 5.4,
                    >= 10 => 6.0,
                    >= 8  => 6.6,
                    _     => 7.2
                };
                var txtName = new TextBlock
                {
                    Text = shortName,
                    FontSize = nameFontSize,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = Brushes.Black,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    TextTrimming = TextTrimming.None,
                    TextWrapping = TextWrapping.NoWrap
                };
                Grid.SetRow(txtName, 2);
                tileGrid.Children.Add(txtName);

                // Row 3: Atomic Weight (Centered)
                string massStr = el.AtomicMass >= 200 && Math.Abs(el.AtomicMass - Math.Round(el.AtomicMass)) < 0.001
                    ? $"[{Math.Round(el.AtomicMass):F0}]"
                    : el.AtomicMass.ToString("F3").TrimEnd('0').TrimEnd('.');
                if (massStr.Length > 7) massStr = el.AtomicMass.ToString("F2");

                var txtMass = new TextBlock
                {
                    Text = massStr,
                    FontSize = 6.8,
                    Foreground = Brushes.Black,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, 0, 0, 1)
                };
                Grid.SetRow(txtMass, 3);
                tileGrid.Children.Add(txtMass);

                tb.Content = tileGrid;

                tb.Checked += (s, _) =>
                {
                    if (s is ToggleButton btn && btn.Tag is string sym)
                    {
                        _selectedSymbols.Add(sym);
                        StyleTile(btn, true);
                        UpdateSelectionStatus();
                    }
                };
                tb.Unchecked += (s, _) =>
                {
                    if (s is ToggleButton btn && btn.Tag is string sym)
                    {
                        _selectedSymbols.Remove(sym);
                        StyleTile(btn, false);
                        UpdateSelectionStatus();
                    }
                };
                tb.MouseEnter += (s, _) =>
                {
                    if (s is ToggleButton btn && btn.Tag is string sym && _elementData.TryGetValue(sym, out var d))
                    {
                        double dTmC = d.TmK - 273.15;
                        string catName = FormatCategoryName(ResolveCategory(d));
                        TxtHoverInfo.Text = $"{d.Name} ({d.Symbol}) • Z={d.Z} • {catName} • {d.AtomicMass:F2} g/mol • Tm={d.TmK:F0} K ({dTmC:F0} °C) • ρ={d.DensityGCm3:F2} g/cm³ • {d.CrystalStructure}";
                    }
                };

                Grid.SetRow(tb, rowIdx);
                Grid.SetColumn(tb, colIdx);
                GridElements.Children.Add(tb);
                _tiles[el.Symbol] = tb;
            }
        }

        private Border BuildCenterBanner()
        {
            var container = new Border
            {
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#26282D" : "#FFFFFF")),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#3F4248" : "#CBD5E1")),
                BorderThickness = new Thickness(1.5),
                CornerRadius = new CornerRadius(0),
                Margin = new Thickness(6, 4, 6, 4),
                Padding = new Thickness(12, 8, 12, 8)
            };

            var rootGrid = new Grid();
            rootGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(270) });
            rootGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            // --- Left: Sample Anatomy Card with Indicator Callouts ---
            var sampleCardGrid = new Grid { VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Left };
            sampleCardGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(80) });
            sampleCardGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(185) });

            var sampleTile = new Border
            {
                Width = 74,
                Height = 68,
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CBD9F9")),
                BorderBrush = Brushes.Black,
                BorderThickness = new Thickness(1.5),
                CornerRadius = new CornerRadius(0),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Center
            };

            var tileGrid = new Grid();
            tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(14) });
            tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(28) });
            tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(13) });
            tileGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(13) });

            var sZ = new TextBlock { Text = "26", FontSize = 8.5, FontWeight = FontWeights.Bold, Foreground = Brushes.Black, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 1, 4, 0) };
            Grid.SetRow(sZ, 0); tileGrid.Children.Add(sZ);

            var sSym = new TextBlock { Text = "Fe", FontSize = 21.0, FontWeight = FontWeights.Bold, Foreground = Brushes.Black, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, -2, 0, 0) };
            Grid.SetRow(sSym, 1); tileGrid.Children.Add(sSym);

            var sName = new TextBlock { Text = "Iron", FontSize = 7.2, FontWeight = FontWeights.SemiBold, Foreground = Brushes.Black, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };
            Grid.SetRow(sName, 2); tileGrid.Children.Add(sName);

            var sMass = new TextBlock { Text = "55.845", FontSize = 6.8, Foreground = Brushes.Black, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };
            Grid.SetRow(sMass, 3); tileGrid.Children.Add(sMass);
            sampleTile.Child = tileGrid;
            Grid.SetColumn(sampleTile, 0);
            sampleCardGrid.Children.Add(sampleTile);

            var calloutsStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(8, 0, 0, 0) };
            var cFg = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#E2E8F0" : "#1E293B"));

            calloutsStack.Children.Add(new TextBlock { Text = "······· Atomic Number", FontSize = 9.5, FontWeight = FontWeights.SemiBold, Foreground = cFg, Margin = new Thickness(0, 0, 0, 4) });
            calloutsStack.Children.Add(new TextBlock { Text = "······· Chemical Symbol", FontSize = 9.5, FontWeight = FontWeights.Bold, Foreground = cFg, Margin = new Thickness(0, 2, 0, 4) });
            calloutsStack.Children.Add(new TextBlock { Text = "······· Element Name", FontSize = 9.5, FontWeight = FontWeights.SemiBold, Foreground = cFg, Margin = new Thickness(0, 2, 0, 4) });
            calloutsStack.Children.Add(new TextBlock { Text = "······· Atomic Weight", FontSize = 9.5, FontWeight = FontWeights.Normal, Foreground = cFg, Margin = new Thickness(0, 2, 0, 0) });

            Grid.SetColumn(calloutsStack, 1);
            sampleCardGrid.Children.Add(calloutsStack);
            Grid.SetColumn(sampleCardGrid, 0);
            rootGrid.Children.Add(sampleCardGrid);

            // --- Right: Title and 10-Category Palette Legend ---
            var rightPanel = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(14, 0, 0, 0) };

            var headerStack = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 8) };
            headerStack.Children.Add(new TextBlock
            {
                Text = "IUPAC PERIODIC TABLE OF THE ELEMENTS",
                FontSize = 13.0,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#F8FAFC" : "#0F172A")),
                VerticalAlignment = VerticalAlignment.Center
            });
            headerStack.Children.Add(new TextBlock
            {
                Text = "  •  18 Groups  •  7 Periods",
                FontSize = 10.5,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#94A3B8" : "#64748B")),
                VerticalAlignment = VerticalAlignment.Center
            });
            rightPanel.Children.Add(headerStack);

            var legendGrid = new Grid();
            legendGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            legendGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var col1 = new StackPanel();
            var col2 = new StackPanel();

            col1.Children.Add(CreateLegendItem("Reactive Nonmetals", "nonmetal", "#B4A0DC"));
            col1.Children.Add(CreateLegendItem("Alkali Metals", "alkali", "#69C5F8"));
            col1.Children.Add(CreateLegendItem("Alkaline Earth Metals", "alkaline-earth", "#FAB147"));
            col1.Children.Add(CreateLegendItem("Transition Metals", "transition", "#CBD9F9"));
            col1.Children.Add(CreateLegendItem("Metalloids", "metalloid", "#FDE573"));

            col2.Children.Add(CreateLegendItem("Post-Transition Metals", "post-transition", "#C2EF97"));
            col2.Children.Add(CreateLegendItem("Halogens", "halogen", "#F598CE"));
            col2.Children.Add(CreateLegendItem("Noble Gases", "noble", "#75D09F"));
            col2.Children.Add(CreateLegendItem("Lanthanides", "lanthanide", "#FEFBCB"));
            col2.Children.Add(CreateLegendItem("Actinides", "actinide", "#FAC2A4"));

            Grid.SetColumn(col1, 0);
            Grid.SetColumn(col2, 1);
            legendGrid.Children.Add(col1);
            legendGrid.Children.Add(col2);
            rightPanel.Children.Add(legendGrid);

            Grid.SetColumn(rightPanel, 1);
            rootGrid.Children.Add(rightPanel);
            container.Child = rootGrid;
            return container;
        }

        private FrameworkElement CreateLegendItem(string label, string code, string colorHex)
        {
            var sp = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                Margin = new Thickness(0, 2, 8, 2),
                Cursor = System.Windows.Input.Cursors.Hand,
                ToolTip = $"Click to filter by {label}"
            };

            var swatch = new Border
            {
                Width = 20,
                Height = 13,
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(colorHex)),
                BorderBrush = Brushes.Black,
                BorderThickness = new Thickness(1.2),
                CornerRadius = new CornerRadius(0),
                Margin = new Thickness(0, 0, 7, 0),
                VerticalAlignment = VerticalAlignment.Center
            };
            sp.Children.Add(swatch);

            var txt = new TextBlock
            {
                Text = label,
                FontSize = 9.5,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#E2E8F0" : "#1E293B")),
                VerticalAlignment = VerticalAlignment.Center
            };
            sp.Children.Add(txt);

            sp.MouseDown += (_, _) =>
            {
                _activeCategory = string.Equals(_activeCategory, code, StringComparison.OrdinalIgnoreCase) ? "all" : code;
                SyncRibbonCategoryButtons();
                ApplyTileFilters();
            };

            return sp;
        }

        private void AddSeriesMarker(int row, int col, string text, string bgHex, string borderHex, string fgHex)
        {
            var border = new Border
            {
                Margin = new Thickness(0.8),
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex)),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex)),
                BorderThickness = new Thickness(1.2),
                CornerRadius = new CornerRadius(0),
                Child = new TextBlock
                {
                    Text = text,
                    FontSize = 7.5,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex)),
                    TextAlignment = TextAlignment.Center,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                }
            };
            Grid.SetRow(border, row);
            Grid.SetColumn(border, col);
            GridElements.Children.Add(border);
        }

        private void AddSeriesRowLabel(int row, string text)
        {
            var lbl = new TextBlock
            {
                Text = text,
                FontSize = 9.5,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#949BA4" : "#64748B")),
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 8, 0)
            };
            Grid.SetRow(lbl, row);
            Grid.SetColumn(lbl, 0);
            Grid.SetColumnSpan(lbl, 4);
            GridElements.Children.Add(lbl);
        }

        public void SyncSelectedElements(IEnumerable<string> activeSymbols)
        {
            var targetSet = new HashSet<string>(activeSymbols.Select(s => s.Trim()), StringComparer.OrdinalIgnoreCase);
            _selectedSymbols.Clear();
            foreach (var kvp in _tiles)
            {
                bool shouldCheck = targetSet.Contains(kvp.Key);
                kvp.Value.IsChecked = shouldCheck;
                if (shouldCheck) _selectedSymbols.Add(kvp.Key);
                StyleTile(kvp.Value, shouldCheck);
            }
            UpdateSelectionStatus();
        }

        private void StyleTile(ToggleButton btn, bool selected)
        {
            var sym = btn.Tag as string ?? "";
            if (!_elementData.TryGetValue(sym, out var el)) return;

            var (bgHex, _, _) = GetCategoryPalette(ResolveCategory(el), sym);
            btn.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex));

            if (selected)
            {
                btn.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1D4ED8"));
                btn.BorderThickness = new Thickness(3.0);
            }
            else
            {
                btn.BorderBrush = Brushes.Black;
                btn.BorderThickness = new Thickness(1.2);
            }

            if (btn.Content is Grid g && g.Children.Count > 0 && g.Children[0] is DockPanel dp)
            {
                foreach (UIElement child in dp.Children)
                {
                    if (child is TextBlock tb && tb.Name == "TxtCheck")
                    {
                        tb.Visibility = selected ? Visibility.Visible : Visibility.Collapsed;
                    }
                }
            }
        }

        public static string ResolveCategory(ElementDto el)
        {
            if (HalogenSymbols.Contains(el.Symbol)) return "halogen";
            var cat = (el.Category ?? "").ToLowerInvariant().Trim();
            return cat switch
            {
                "noble" or "noble-gas" or "noble gas" => "noble",
                "alkali" or "alkali-metal" => "alkali",
                "alkaline-earth" or "alkaline earth" => "alkaline-earth",
                "transition" or "transition-metal" => "transition",
                "post-transition" or "post transition" or "other-metal" or "other metal" => "post-transition",
                "metalloid" or "semimetal" => "metalloid",
                "nonmetal" or "reactive-nonmetal" => "nonmetal",
                "lanthanide" => "lanthanide",
                "actinide" => "actinide",
                _ => cat
            };
        }

        public static (string bg, string border, string fg) GetCategoryPalette(string category, string symbol = "")
        {
            if (HalogenSymbols.Contains(symbol))
            {
                return ("#F598CE", "#000000", "#000000");
            }

            return (category ?? "").ToLowerInvariant().Trim() switch
            {
                "nonmetal" => ("#B4A0DC", "#000000", "#000000"),        // Soft Lavender Lilac
                "alkali" => ("#69C5F8", "#000000", "#000000"),          // Vibrant Sky Blue
                "alkaline-earth" => ("#FAB147", "#000000", "#000000"),  // Warm Golden Amber
                "transition" => ("#CBD9F9", "#000000", "#000000"),      // Soft Periwinkle Ice Blue
                "metalloid" => ("#FDE573", "#000000", "#000000"),       // Canary Yellow
                "post-transition" => ("#C2EF97", "#000000", "#000000"), // Soft Light Mint Green
                "halogen" => ("#F598CE", "#000000", "#000000"),         // Candy Rose Pink
                "noble" => ("#75D09F", "#000000", "#000000"),           // Mint Aqua / Seafoam
                "lanthanide" => ("#FEFBCB", "#000000", "#000000"),      // Pale Lemon Chiffon / Cream
                "actinide" => ("#FAC2A4", "#000000", "#000000"),        // Soft Peach / Apricot
                _ => ("#E2E8F0", "#000000", "#000000")
            };
        }

        private static string FormatCategoryName(string cat)
        {
            return cat.ToLowerInvariant().Trim() switch
            {
                "nonmetal" => "Reactive Nonmetal",
                "alkali" => "Alkali Metal",
                "alkaline-earth" => "Alkaline Earth Metal",
                "transition" => "Transition Metal",
                "metalloid" => "Metalloid",
                "post-transition" => "Post-Transition Metal",
                "halogen" => "Halogen",
                "noble" => "Noble Gas",
                "lanthanide" => "Lanthanide",
                "actinide" => "Actinide",
                _ => cat
            };
        }

        private void UpdateSelectionStatus()
        {
            if (_selectedSymbols.Count == 0)
            {
                TxtSelectedList.Text = "Selected Elements: (none selected)";
            }
            else
            {
                double eqFrac = 100.0 / _selectedSymbols.Count;
                TxtSelectedList.Text = $"Selected ({_selectedSymbols.Count} elements, ~{eqFrac:F1}% each): {string.Join(", ", _selectedSymbols)}";
            }
        }

        private void TxtFilter_TextChanged(object sender, TextChangedEventArgs e)
        {
            ApplyTileFilters();
        }

        private void BtnCategoryFilter_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button clicked || clicked.Tag is not string cat) return;
            _activeCategory = string.Equals(_activeCategory, cat, StringComparison.OrdinalIgnoreCase) ? "all" : cat;
            SyncRibbonCategoryButtons();
            ApplyTileFilters();
        }

        private void SyncRibbonCategoryButtons()
        {
            foreach (var child in PanelCategoryFilters.Children)
            {
                if (child is Button b)
                {
                    bool active = string.Equals(b.Tag as string, _activeCategory, StringComparison.OrdinalIgnoreCase);
                    b.FontWeight = active ? FontWeights.Bold : FontWeights.Normal;
                    b.BorderBrush = active ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#60A5FA")) : new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#4E5058" : "#CBD5E1"));
                    b.Background = active ? new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#3F4248" : "#DBEAFE")) : new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#2B2D31" : "#F8FAFC"));
                    b.BorderThickness = new Thickness(active ? 1.5 : 1.0);
                }
            }
        }

        private void ApplyTileFilters()
        {
            string q = TxtFilter.Text.Trim().ToLowerInvariant();
            foreach (var kvp in _tiles)
            {
                if (_elementData.TryGetValue(kvp.Key, out var d))
                {
                    string cat = ResolveCategory(d);
                    bool catMatch = _activeCategory == "all"
                                 || string.Equals(cat, _activeCategory, StringComparison.OrdinalIgnoreCase);
                    bool textMatch = string.IsNullOrEmpty(q)
                                  || d.Symbol.ToLowerInvariant().Contains(q)
                                  || d.Name.ToLowerInvariant().Contains(q)
                                  || d.Z.ToString() == q;
                    kvp.Value.Opacity = (catMatch && textMatch) ? 1.0 : 0.15;
                }
            }
        }

        private void BtnPreset_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button btn || btn.Tag is not string csv) return;
            BtnClear_Click(sender, e);
            foreach (var sym in csv.Split(',', StringSplitOptions.RemoveEmptyEntries))
            {
                if (_tiles.TryGetValue(sym.Trim(), out var tb))
                {
                    tb.IsChecked = true;
                }
            }
        }

        private void BtnClear_Click(object sender, RoutedEventArgs e)
        {
            foreach (var tb in _tiles.Values)
            {
                tb.IsChecked = false;
            }
            _selectedSymbols.Clear();
            UpdateSelectionStatus();
        }

        private void BtnMergeApply_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedSymbols.Count == 0)
            {
                MessageBox.Show("Please select at least one element on the Periodic Table.", "No Elements Selected", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            MergeCompositionRequested?.Invoke(_selectedSymbols.ToList());
        }

        private void BtnApply_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedSymbols.Count == 0)
            {
                MessageBox.Show("Please select at least one element on the Periodic Table.", "No Elements Selected", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            double pct = Math.Round(100.0 / _selectedSymbols.Count, 2);
            var dict = _selectedSymbols.ToDictionary(s => s, _ => pct);
            ApplyCompositionRequested?.Invoke(dict);
        }
    }
}
