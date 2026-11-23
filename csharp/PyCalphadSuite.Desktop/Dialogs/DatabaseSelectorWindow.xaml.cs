// <copyright file="DatabaseSelectorWindow.xaml.cs" company="PyCALPHAD Materials CAE">
// Modal database and preset selection dialog in C# WPF.
// </copyright>

using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Dialogs
{
    public partial class DatabaseSelectorWindow : Window
    {
        private readonly DatabaseCatalogResult _catalog;

        public string SelectedDatabase { get; private set; } = string.Empty;
        public string SelectedPreset { get; private set; } = string.Empty;

        public DatabaseSelectorWindow(DatabaseCatalogResult catalog, string currentDatabase, Window owner)
        {
            InitializeComponent();
            Owner = owner;
            _catalog = catalog;

            LstDatabases.ItemsSource = _catalog.Names;
            if (!string.IsNullOrEmpty(currentDatabase) && _catalog.Names.Contains(currentDatabase))
            {
                LstDatabases.SelectedItem = currentDatabase;
            }
            else if (_catalog.Names.Count > 0)
            {
                LstDatabases.SelectedIndex = 0;
            }
        }

        private void LstDatabases_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (LstDatabases.SelectedItem is not string dbName) return;
            SelectedDatabase = dbName;

            if (_catalog.Databases.TryGetValue(dbName, out var spec))
            {
                TxtDbName.Text = dbName;
                string tdbs = spec.AvailableTdbs.Count > 0
                    ? string.Join(", ", spec.AvailableTdbs)
                    : (spec.TdbFile ?? "Dynamic SGTE Synthesis");
                int totalCatalog = _catalog.TdbCatalog.Count;
                TxtDbTdb.Text = totalCatalog > 0
                    ? $"Basis: {spec.Basis}  |  Mounted TDBs ({spec.AvailableTdbs.Count}): {tdbs}  [Total Installed: {totalCatalog} .tdb files]"
                    : $"Basis: {spec.Basis}  |  Mounted TDBs: {tdbs}";
                TxtDbElements.Text = $"Supported Elements ({spec.Elements.Count}): {string.Join(", ", spec.Elements)}";
                LstPresets.ItemsSource = spec.Presets.Keys.ToList();
                if (spec.Presets.Count > 0)
                {
                    LstPresets.SelectedIndex = 0;
                }
            }
        }

        private void LstPresets_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            AcceptSelection();
        }

        private void BtnOk_Click(object sender, RoutedEventArgs e)
        {
            AcceptSelection();
        }

        private void AcceptSelection()
        {
            SelectedDatabase = LstDatabases.SelectedItem?.ToString() ?? _catalog.Names.FirstOrDefault() ?? "High Entropy Alloys";
            SelectedPreset = LstPresets.SelectedItem?.ToString() ?? string.Empty;
            DialogResult = true;
            Close();
        }
    }
}
