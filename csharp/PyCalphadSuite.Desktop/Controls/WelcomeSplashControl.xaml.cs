// <copyright file="WelcomeSplashControl.xaml.cs" company="PyCALPHAD Materials CAE">
// Interactive JMatPro Startup Dashboard in C# WPF.
// </copyright>

using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Controls
{
    public partial class WelcomeSplashControl : UserControl
    {
        public event Action<string>? DatabaseSelected;
        public event Action? OpenDatabaseModalRequested;
        public event Action? OpenPeriodicTableRequested;
        public event Action? OpenLiteratureHeasRequested;

        public WelcomeSplashControl()
        {
            InitializeComponent();
        }

        public void PopulateCatalog(DatabaseCatalogResult catalog)
        {
            GridDatabases.Children.Clear();
            var accentColors = new[]
            {
                "#2563EB", "#0891B2", "#059669", "#D97706", "#DC2626", "#7C3AED", "#0284C7"
            };

            int idx = 0;
            foreach (var dbName in catalog.Names)
            {
                catalog.Databases.TryGetValue(dbName, out var spec);
                string hex = accentColors[idx % accentColors.Length];
                idx++;

                var btn = new Button
                {
                    Margin = new Thickness(5),
                    Padding = new Thickness(14, 12, 14, 12),
                    Background = Brushes.White,
                    BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CBD5E1")),
                    BorderThickness = new Thickness(1),
                    HorizontalContentAlignment = HorizontalAlignment.Stretch,
                    VerticalContentAlignment = VerticalAlignment.Top,
                    Cursor = System.Windows.Input.Cursors.Hand,
                    Tag = dbName
                };

                var sp = new StackPanel();
                var headerPanel = new DockPanel();
                var accentBar = new Border
                {
                    Width = 4,
                    Height = 16,
                    CornerRadius = new CornerRadius(2),
                    Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex)),
                    Margin = new Thickness(0, 0, 8, 0)
                };
                DockPanel.SetDock(accentBar, Dock.Left);
                headerPanel.Children.Add(accentBar);

                var titleTb = new TextBlock
                {
                    Text = dbName,
                    FontWeight = FontWeights.Bold,
                    FontSize = 13,
                    Foreground = Brushes.Black,
                    TextTrimming = TextTrimming.CharacterEllipsis
                };
                headerPanel.Children.Add(titleTb);
                sp.Children.Add(headerPanel);

                string elementsPreview = spec != null && spec.Elements.Count > 0
                    ? $"Elements: {string.Join(", ", spec.Elements)}"
                    : "Multi-component SGTE System";
                sp.Children.Add(new TextBlock
                {
                    Text = elementsPreview,
                    FontSize = 11,
                    Foreground = Brushes.Black,
                    Margin = new Thickness(12, 5, 0, 2),
                    TextTrimming = TextTrimming.CharacterEllipsis
                });

                sp.Children.Add(new TextBlock
                {
                    Text = $"Basis: {spec?.Basis ?? "wt%"}",
                    FontSize = 10,
                    Foreground = Brushes.Black,
                    Margin = new Thickness(12, 0, 0, 0)
                });

                btn.Content = sp;
                btn.Click += (s, _) =>
                {
                    if (s is Button b && b.Tag is string name)
                    {
                        DatabaseSelected?.Invoke(name);
                    }
                };
                GridDatabases.Children.Add(btn);
            }
        }

        private void BtnSelectModal_Click(object sender, RoutedEventArgs e) => OpenDatabaseModalRequested?.Invoke();
        private void BtnPeriodic_Click(object sender, RoutedEventArgs e) => OpenPeriodicTableRequested?.Invoke();
        private void BtnLitHea_Click(object sender, RoutedEventArgs e) => OpenLiteratureHeasRequested?.Invoke();
    }
}
