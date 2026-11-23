// <copyright file="PeriodicTableControl.xaml.cs" company="PyCALPHAD Materials CAE">
// Complete 118-element interactive IUPAC Periodic Table in C# WPF.
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

            foreach (var kvp in _tiles)
            {
                StyleTile(kvp.Value, kvp.Value.IsChecked == true);
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
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(10) });
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(68) });
            GridElements.RowDefinitions.Add(new RowDefinition { Height = new GridLength(68) });

            // Col 0: Period numbers | Cols 1..18: IUPAC Groups 1..18 (74 px width gives generous room for full element names)
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

            var centerBanner = new Border
            {
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#2B2D31" : "#F8FAFC")),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#3F4248" : "#CBD5E1")),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Margin = new Thickness(8, 6, 8, 6),
                Padding = new Thickness(8, 4, 8, 4),
                Child = new TextBlock
                {
                    Text = "IUPAC PERIODIC TABLE OF THE ELEMENTS\n18 Groups  •  7 Periods  •  Complete 118-Element CALPHAD Registry",
                    FontSize = 11.5,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDark ? "#F2F3F5" : "#0F172A")),
                    TextAlignment = TextAlignment.Center,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                }
            };
            Grid.SetRow(centerBanner, 1);
            Grid.SetColumn(centerBanner, 3);
            Grid.SetRowSpan(centerBanner, 2);
            Grid.SetColumnSpan(centerBanner, 10);
            GridElements.Children.Add(centerBanner);

            AddSeriesMarker(6, 3, "57–71 *\nLa–Lu\nLanthanides", _isDark ? "#3C2337" : "#FAE8FF", _isDark ? "#76376C" : "#E879F9", _isDark ? "#F0ABFC" : "#701A75");
            AddSeriesMarker(7, 3, "89–103 **\nAc–Lr\nActinides", _isDark ? "#2E223B" : "#EDE9FE", _isDark ? "#5B357A" : "#A78BFA", _isDark ? "#D8B4FE" : "#4C1D95");
            AddSeriesRowLabel(9, "* Lanthanides");
            AddSeriesRowLabel(10, "** Actinides");

            foreach (var el in elements)
            {
                _elementData[el.Symbol] = el;

                int rowIdx = Math.Clamp(el.GridRow, 1, 10);
                int colIdx = Math.Clamp(el.GridCol, 1, 18);

                var (bgHex, borderHex, fgHex) = GetCategoryPalette(el.Category, _isDark);
                string shortName = el.Name;
                double tmC = el.TmK - 273.15;

                var tb = new ToggleButton
                {
                    Margin = new Thickness(0.8),
                    Padding = new Thickness(1, 1, 1, 1),
                    Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex)),
                    BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex)),
                    Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex)),
                    BorderThickness = new Thickness(1),
                    Tag = el.Symbol,
                    Cursor = System.Windows.Input.Cursors.Hand,
                    ToolTip = $"{el.Name} ({el.Symbol}) | Z={el.Z}\n" +
                              $"Atomic Mass: {el.AtomicMass:F3} g/mol | VEC: {el.Vec:F1}\n" +
                              $"Structure: {el.CrystalStructure} | Tm: {el.TmK:F1} K ({tmC:F1} °C)\n" +
                              $"Density: {el.DensityGCm3:F3} g/cm³ | E: {el.YoungsModulusGpa:F1} GPa"
                };

                // Dynamic font sizing ensures long names like Praseodymium or Darmstadtium are never cut short
                double nameFontSize = shortName.Length switch
                {
                    >= 13 => 4.8,
                    >= 11 => 5.2,
                    >= 9  => 5.8,
                    >= 7  => 6.3,
                    _     => 6.9
                };

                var content = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
                content.Children.Add(new TextBlock
                {
                    Text = el.Z.ToString(),
                    FontSize = 7.0,
                    FontWeight = FontWeights.SemiBold,
                    HorizontalAlignment = HorizontalAlignment.Left,
                    Margin = new Thickness(2, 0, 0, 0)
                });
                content.Children.Add(new TextBlock
                {
                    Text = el.Symbol,
                    FontSize = 12.0,
                    FontWeight = FontWeights.Bold,
                    HorizontalAlignment = HorizontalAlignment.Center
                });
                content.Children.Add(new TextBlock
                {
                    Text = shortName,
                    FontSize = nameFontSize,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    TextTrimming = TextTrimming.None,
                    TextWrapping = TextWrapping.NoWrap,
                    MaxWidth = 72,
                    Opacity = 0.95
                });
                content.Children.Add(new TextBlock
                {
                    Text = el.AtomicMass.ToString("F2"),
                    FontSize = 6.4,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Opacity = 0.85
                });
                tb.Content = content;

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
                        TxtHoverInfo.Text = $"{d.Name} ({d.Symbol}) • Z={d.Z} • {d.AtomicMass:F2} g/mol • Tm={d.TmK:F0} K ({dTmC:F0} °C) • ρ={d.DensityGCm3:F2} g/cm³ • {d.CrystalStructure}";
                    }
                };

                Grid.SetRow(tb, rowIdx);
                Grid.SetColumn(tb, colIdx);
                GridElements.Children.Add(tb);
                _tiles[el.Symbol] = tb;
            }
        }

        private void AddSeriesMarker(int row, int col, string text, string bgHex, string borderHex, string fgHex)
        {
            var border = new Border
            {
                Margin = new Thickness(1.5),
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex)),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
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
            }
            UpdateSelectionStatus();
        }

        private void StyleTile(ToggleButton btn, bool selected)
        {
            var sym = btn.Tag as string ?? "";
            if (selected)
            {
                btn.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#15803D"));
                btn.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#22C55E"));
                btn.Foreground = Brushes.White;
                btn.BorderThickness = new Thickness(2);
            }
            else if (_elementData.TryGetValue(sym, out var el))
            {
                var (bgHex, borderHex, fgHex) = GetCategoryPalette(el.Category, _isDark);
                btn.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bgHex));
                btn.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(borderHex));
                btn.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fgHex));
                btn.BorderThickness = new Thickness(1);
            }
        }

        private static (string bg, string border, string fg) GetCategoryPalette(string category, bool isDark = true)
        {
            if (!isDark)
            {
                return (category ?? "").ToLowerInvariant() switch
                {
                    "transition" => ("#F3E8FF", "#C084FC", "#581C87"),
                    "post-transition" => ("#DCFCE7", "#4ADE80", "#14532D"),
                    "metalloid" => ("#FEF3C7", "#FBBF24", "#78350F"),
                    "nonmetal" => ("#DBEAFE", "#60A5FA", "#1E3A8A"),
                    "alkali" => ("#FEE2E2", "#F87171", "#7F1D1D"),
                    "alkaline-earth" => ("#FFEDD5", "#FB923C", "#7C2D12"),
                    "noble" => ("#F3F4F6", "#9CA3AF", "#1F2937"),
                    "lanthanide" => ("#FAE8FF", "#E879F9", "#701A75"),
                    "actinide" => ("#EDE9FE", "#A78BFA", "#4C1D95"),
                    _ => ("#F1F5F9", "#94A3B8", "#0F172A")
                };
            }

            return (category ?? "").ToLowerInvariant() switch
            {
                "transition" => ("#2E283F", "#524673", "#D8B4FE"),
                "post-transition" => ("#1E332A", "#356250", "#86EFAC"),
                "metalloid" => ("#362C1C", "#6B5329", "#FCD34D"),
                "nonmetal" => ("#1F2E40", "#35567D", "#93C5FD"),
                "alkali" => ("#3C2227", "#773641", "#FCA5A5"),
                "alkaline-earth" => ("#39271C", "#70452D", "#FDBA74"),
                "noble" => ("#2B2D32", "#4B515C", "#E2E8F0"),
                "lanthanide" => ("#3C2337", "#76376C", "#F0ABFC"),
                "actinide" => ("#2E223B", "#5B357A", "#D8B4FE"),
                _ => ("#26282D", "#404550", "#F1F5F9")
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
            _activeCategory = cat;

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
            ApplyTileFilters();
        }

        private void ApplyTileFilters()
        {
            string q = TxtFilter.Text.Trim().ToLowerInvariant();
            foreach (var kvp in _tiles)
            {
                if (_elementData.TryGetValue(kvp.Key, out var d))
                {
                    bool catMatch = _activeCategory == "all"
                                 || string.Equals(d.Category, _activeCategory, StringComparison.OrdinalIgnoreCase);
                    bool textMatch = string.IsNullOrEmpty(q)
                                  || d.Symbol.ToLowerInvariant().Contains(q)
                                  || d.Name.ToLowerInvariant().Contains(q)
                                  || d.Z.ToString() == q;
                    kvp.Value.Opacity = (catMatch && textMatch) ? 1.0 : 0.18;
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
