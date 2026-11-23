// <copyright file="SaveCompositionWindow.xaml.cs" company="PyCALPHAD Materials CAE">
// Save, load, and manage persistent alloy composition presets and portable files.
// </copyright>

using System;
using System.IO;
using System.Linq;
using System.Windows;
using Microsoft.Win32;
using PyCalphadSuite.Core.Models;
using PyCalphadSuite.Core.Services;

namespace PyCalphadSuite.Desktop.Dialogs
{
    public partial class SaveCompositionWindow : Window
    {
        private readonly CompositionLibraryService _libService;
        private readonly SavedCompositionProfile _currentProfile;

        public SavedCompositionProfile? LoadedProfile { get; private set; }
        public bool LibraryUpdated { get; private set; }

        public SaveCompositionWindow(
            CompositionLibraryService libService,
            SavedCompositionProfile currentProfile,
            bool openManageTab,
            Window owner)
        {
            InitializeComponent();
            Owner = owner;
            _libService = libService;
            _currentProfile = currentProfile;

            TxtCompName.Text = string.IsNullOrWhiteSpace(currentProfile.Name)
                ? CompositionLibraryService.BuildDefaultAlloyName(currentProfile.Composition)
                : currentProfile.Name;

            var elemStr = string.Join(", ", currentProfile.Composition.Select(kv => $"{kv.Key}: {kv.Value:G4} {currentProfile.Basis}"));
            TxtPreviewSummary.Text =
                $"Database: {currentProfile.DatabaseName}  |  Grain: {currentProfile.GrainSizeUm:F0} μm  |  Process: {currentProfile.ProcessType}\n" +
                $"T: {currentProfile.TStart:F0}–{currentProfile.TStop:F0} K (ΔT={currentProfile.TStep:G4})\n" +
                $"Elements: {elemStr}";

            RefreshLibraryGrid();
            if (openManageTab)
            {
                ModeTabs.SelectedIndex = 1;
            }
        }

        private void RefreshLibraryGrid()
        {
            GridSavedComps.ItemsSource = _libService.LoadLibrary();
        }

        private void BtnSave_Click(object sender, RoutedEventArgs e)
        {
            string name = TxtCompName.Text.Trim();
            if (string.IsNullOrWhiteSpace(name))
            {
                name = CompositionLibraryService.BuildDefaultAlloyName(_currentProfile.Composition);
            }

            _currentProfile.Name = name;
            _currentProfile.Notes = TxtNotes.Text.Trim();
            _currentProfile.SavedAtUtc = DateTime.UtcNow;

            if (ChkSaveLibrary.IsChecked == true)
            {
                _libService.SaveToLibrary(_currentProfile);
                LibraryUpdated = true;
                RefreshLibraryGrid();
            }

            if (ChkExportFile.IsChecked == true)
            {
                SaveProfileWithDialog(name);
            }

            MessageBox.Show($"Composition '{name}' saved cleanly.", "Composition Saved", MessageBoxButton.OK, MessageBoxImage.Information);
            ModeTabs.SelectedIndex = 1;
        }

        private void BtnSaveFileOnly_Click(object sender, RoutedEventArgs e)
        {
            string name = TxtCompName.Text.Trim();
            if (string.IsNullOrWhiteSpace(name))
            {
                name = CompositionLibraryService.BuildDefaultAlloyName(_currentProfile.Composition);
            }

            _currentProfile.Name = name;
            _currentProfile.Notes = TxtNotes.Text.Trim();
            _currentProfile.SavedAtUtc = DateTime.UtcNow;

            if (SaveProfileWithDialog(name))
            {
                MessageBox.Show($"Composition '{name}' saved to file.", "Composition Saved", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private bool SaveProfileWithDialog(string name)
        {
            var dlg = new SaveFileDialog
            {
                FileName = $"{Sanitize(name)}.comp.json",
                Filter = "CALPHAD Composition Profile (*.comp.json)|*.comp.json|CSV Chemistry File (*.csv)|*.csv|JSON File (*.json)|*.json"
            };
            if (dlg.ShowDialog() == true)
            {
                CompositionLibraryService.SaveProfileToFile(_currentProfile, dlg.FileName);
                return true;
            }
            return false;
        }

        private void BtnLoadSelected_Click(object sender, RoutedEventArgs e)
        {
            if (GridSavedComps.SelectedItem is not SavedCompositionProfile prof)
            {
                MessageBox.Show("Select a composition from the table first.", "Load Composition", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            LoadedProfile = prof;
            DialogResult = true;
            Close();
        }

        private void BtnImportFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "Saved Composition Files (*.comp.json;*.json;*.csv;*.dat)|*.comp.json;*.json;*.csv;*.dat|All Files (*.*)|*.*"
            };
            if (dlg.ShowDialog() != true) return;

            try
            {
                var prof = CompositionLibraryService.LoadProfileFromFile(dlg.FileName);
                if (prof.Composition.Count == 0)
                {
                    MessageBox.Show("No valid chemical elements found in selected file.", "Import Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
                _libService.SaveToLibrary(prof);
                LibraryUpdated = true;
                RefreshLibraryGrid();

                LoadedProfile = prof;
                DialogResult = true;
                Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to import composition file:\n{ex.Message}", "Import Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnExportSelected_Click(object sender, RoutedEventArgs e)
        {
            var target = GridSavedComps.SelectedItem as SavedCompositionProfile ?? _currentProfile;
            var dlg = new SaveFileDialog
            {
                FileName = $"{Sanitize(target.Name)}.comp.json",
                Filter = "CALPHAD Composition Profile (*.comp.json)|*.comp.json|CSV Chemistry File (*.csv)|*.csv"
            };
            if (dlg.ShowDialog() == true)
            {
                CompositionLibraryService.SaveProfileToFile(target, dlg.FileName);
                MessageBox.Show($"Exported composition '{target.Name}' to:\n{dlg.FileName}", "Export Complete", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnDelete_Click(object sender, RoutedEventArgs e)
        {
            if (GridSavedComps.SelectedItem is not SavedCompositionProfile prof) return;
            if (_libService.DeleteFromLibrary(prof.Name))
            {
                LibraryUpdated = true;
                RefreshLibraryGrid();
            }
        }

        private static string Sanitize(string name)
        {
            var bad = Path.GetInvalidFileNameChars();
            return new string(name.Select(c => bad.Contains(c) ? '_' : c).ToArray());
        }
    }
}
