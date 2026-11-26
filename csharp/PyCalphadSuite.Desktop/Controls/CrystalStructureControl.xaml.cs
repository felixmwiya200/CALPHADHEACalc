using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Media.Media3D;
using System.Windows.Threading;
using Microsoft.Win32;
using PyCalphadSuite.Core.Models;

namespace PyCalphadSuite.Desktop.Controls
{
    public partial class CrystalStructureControl : UserControl
    {
        private readonly MeshGeometry3D _unitSphereMesh;
        private readonly MeshGeometry3D _unitCylinderMesh;
        private readonly Dictionary<Model3D, CrystalAtomDto> _atomLookup = new();
        private readonly DispatcherTimer _spinTimer;

        private List<CrystalStructureDto> _structures = new();
        private int _activePhaseIndex;
        private CrystalAtomDto? _selectedAtom;
        private bool _isDarkTheme;
        private bool _isPopOutWindow;
        private bool _is3DExpanded;
        private bool _suppressRebuildEvent;
        private bool _suppressPhaseTabEvent;
        private double _savedInspectorWidth = 340.0;

        // Interactive quaternion 360-degree trackball camera state (gimbal-lock free)
        private Quaternion _cameraOrientation = DefaultCameraOrientation();
        private double _cameraDistance = 16.0;
        private double _baseDistance = 16.0;
        private Vector3D _panOffset = new(0, 0, 0);
        private double _sweepRemainingDeg;
        private bool _atomLabelsEnabled = true;
        private bool _isSyncingLabelToggle;

        private bool _isOrbiting;
        private bool _isPanning;
        private Point _mouseDownPos;
        private Point _lastMousePos;

        public event Action<int, double>? RebuildStructuresRequested;
        public event Action<bool>? Expand3DToggled;

        public CrystalStructureControl()
        {
            InitializeComponent();
            _unitSphereMesh = BuildUnitSphereMesh(latBands: 14, lonBands: 22);
            _unitCylinderMesh = BuildUnitCylinderMesh(segments: 10);

            _spinTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(33)
            };
            _spinTimer.Tick += (_, _) =>
            {
                if (_structures.Count == 0)
                {
                    _sweepRemainingDeg = 0.0;
                    _spinTimer.Stop();
                    return;
                }

                if (!_isOrbiting && _sweepRemainingDeg > 0.0)
                {
                    double step = Math.Min(_sweepRemainingDeg, 4.5);
                    _sweepRemainingDeg -= step;
                    RotateCameraAroundLocalUp(step);
                    UpdateCamera();
                    if (_sweepRemainingDeg <= 0.0 && ChkAutoSpin.IsChecked != true)
                    {
                        _spinTimer.Stop();
                    }
                }
                else if (!_isOrbiting && ChkAutoSpin.IsChecked == true)
                {
                    RotateCameraAroundLocalUp(1.1);
                    UpdateCamera();
                }
            };
            SyncAtomLabelsToggle(true);
            PhaseTabsControl.Resources[typeof(TabItem)] = CreateTabItemStyle(_isDarkTheme);
        }

        private Style CreateTabItemStyle(bool dark)
        {
            var style = new Style(typeof(TabItem));
            style.Setters.Add(new Setter(TabItem.FontSizeProperty, 11.5));
            style.Setters.Add(new Setter(TabItem.FontWeightProperty, FontWeights.SemiBold));
            style.Setters.Add(new Setter(TabItem.MarginProperty, new Thickness(0, 0, 4, 0)));

            var template = new ControlTemplate(typeof(TabItem));
            var borderFactory = new FrameworkElementFactory(typeof(Border), "TabBorder");
            borderFactory.SetValue(Border.CornerRadiusProperty, new CornerRadius(4, 4, 0, 0));
            borderFactory.SetValue(Border.PaddingProperty, new Thickness(12, 6, 12, 6));

            var normalBg = (Color)ColorConverter.ConvertFromString(dark ? "#2D3748" : "#E2E8F0");
            var normalBc = (Color)ColorConverter.ConvertFromString(dark ? "#4A5568" : "#CBD5E1");
            var selBg = (Color)ColorConverter.ConvertFromString(dark ? "#1E293B" : "#FFFFFF");
            var selBc = (Color)ColorConverter.ConvertFromString(dark ? "#3B82F6" : "#2563EB");
            var hoverBg = (Color)ColorConverter.ConvertFromString(dark ? "#374151" : "#F1F5F9");

            borderFactory.SetValue(Border.BackgroundProperty, new SolidColorBrush(normalBg));
            borderFactory.SetValue(Border.BorderBrushProperty, new SolidColorBrush(normalBc));
            borderFactory.SetValue(Border.BorderThicknessProperty, new Thickness(1, 1, 1, 0));

            var contentFactory = new FrameworkElementFactory(typeof(ContentPresenter), "ContentSite");
            contentFactory.SetValue(ContentPresenter.VerticalAlignmentProperty, VerticalAlignment.Center);
            contentFactory.SetValue(ContentPresenter.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            contentFactory.SetValue(ContentPresenter.ContentSourceProperty, "Header");
            contentFactory.SetValue(ContentPresenter.RecognizesAccessKeyProperty, true);

            borderFactory.AppendChild(contentFactory);
            template.VisualTree = borderFactory;

            var selTrigger = new Trigger { Property = TabItem.IsSelectedProperty, Value = true };
            selTrigger.Setters.Add(new Setter(Border.BackgroundProperty, new SolidColorBrush(selBg), "TabBorder"));
            selTrigger.Setters.Add(new Setter(Border.BorderBrushProperty, new SolidColorBrush(selBc), "TabBorder"));
            selTrigger.Setters.Add(new Setter(Border.BorderThicknessProperty, new Thickness(1, 2, 1, 0), "TabBorder"));
            template.Triggers.Add(selTrigger);

            var hoverTrigger = new Trigger { Property = TabItem.IsMouseOverProperty, Value = true };
            hoverTrigger.Setters.Add(new Setter(Border.BackgroundProperty, new SolidColorBrush(hoverBg), "TabBorder"));
            template.Triggers.Add(hoverTrigger);

            style.Setters.Add(new Setter(TabItem.TemplateProperty, template));
            return style;
        }

        private static Quaternion DefaultCameraOrientation()
        {
            var qYaw = new Quaternion(new Vector3D(0, 1, 0), 40.0);
            var qPitch = new Quaternion(new Vector3D(1, 0, 0), -24.0);
            var q = qYaw * qPitch;
            q.Normalize();
            return q;
        }

        private static Vector3D RotateVector(Quaternion q, Vector3D v)
        {
            var m = Matrix3D.Identity;
            m.Rotate(q);
            return m.Transform(v);
        }

        private void RotateCameraAroundLocalUp(double angleDeg)
        {
            Vector3D up = RotateVector(_cameraOrientation, new Vector3D(0, 1, 0));
            if (up.Length < 1e-6) up = new Vector3D(0, 1, 0);
            up.Normalize();
            var qStep = new Quaternion(up, angleDeg);
            _cameraOrientation = qStep * _cameraOrientation;
            _cameraOrientation.Normalize();
        }

        public void SetCrystalStructures(List<CrystalStructureDto>? structures, string summaryText = "")
        {
            _structures = structures ?? new List<CrystalStructureDto>();
            _activePhaseIndex = 0;
            _selectedAtom = null;

            TxtHeaderSubtitle.Text = !string.IsNullOrWhiteSpace(summaryText)
                ? summaryText
                : _structures.Count > 0
                    ? $"Detected phases: {string.Join(" + ", _structures.Select(s => $"{s.PhaseName} ({s.PhaseFractionDisplay})"))}"
                    : "No crystal phases loaded. Run Calculate Equilibrium or click Rebuild 3D Cells.";

            RebuildPhaseTabs();
            GridPhaseCompare.ItemsSource = _structures;

            if (_structures.Count > 0)
            {
                CrystalSubTabs.Visibility = Visibility.Visible;
                ComparePanel.Visibility = Visibility.Collapsed;
                SelectPhaseIndex(0, resetCamera: true);
            }
            else
            {
                if (CrystalSceneRoot != null) CrystalSceneRoot.Content = null;
                if (HighlightRoot != null) HighlightRoot.Content = null;
                if (AtomLabelsOverlay != null) AtomLabelsOverlay.Children.Clear();
                TxtPhaseMetadata.Text = "Run equilibrium calculation to display active crystal structures.";
                TxtConfigSummary.Text = "No active phase selected.";
                GridSublattices.ItemsSource = null;
                GridAtomPositions.ItemsSource = null;
                PanelSpeciesLegend.Children.Clear();
            }
        }

        public void SetSnapshotControls(int supercellN, double tempK)
        {
            _suppressRebuildEvent = true;
            try
            {
                foreach (ComboBoxItem item in CmbSupercell.Items)
                {
                    if (int.TryParse(item.Tag?.ToString(), out var n) && n == supercellN)
                    {
                        CmbSupercell.SelectedItem = item;
                        break;
                    }
                }
                foreach (ComboBoxItem item in CmbSnapshotTemp.Items)
                {
                    if (double.TryParse(item.Tag?.ToString(), out var t) && Math.Abs(t - tempK) < 1.0)
                    {
                        CmbSnapshotTemp.SelectedItem = item;
                        break;
                    }
                }
            }
            finally
            {
                _suppressRebuildEvent = false;
            }
        }

        public int SelectedSupercellN =>
            CmbSupercell.SelectedItem is ComboBoxItem cbi && int.TryParse(cbi.Tag?.ToString(), out var n) ? n : 2;

        public double SelectedTemperatureK =>
            CmbSnapshotTemp.SelectedItem is ComboBoxItem cbi && double.TryParse(cbi.Tag?.ToString(), out var t) ? t : 300.0;

        public void ApplyTheme(bool dark)
        {
            _isDarkTheme = dark;
            var bg = new SolidColorBrush((Color)ColorConverter.ConvertFromString(dark ? "#1E1E1E" : "#F1F5F9"));
            var panel = new SolidColorBrush((Color)ColorConverter.ConvertFromString(dark ? "#252526" : "#E2E8F0"));
            var fg = dark ? Brushes.WhiteSmoke : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#0F172A"));
            var muted = new SolidColorBrush((Color)ColorConverter.ConvertFromString(dark ? "#CBD5E1" : "#475569"));

            RootGrid.Background = bg;
            HeaderBorder.Background = panel;
            PhaseTabsBarBorder.Background = panel;
            PhaseTabsControl.Background = panel;
            PhaseTabsControl.Foreground = fg;
            PhaseTabsControl.Resources[typeof(TabItem)] = CreateTabItemStyle(dark);
            CrystalSubTabs.Background = bg;
            CrystalSubTabs.Foreground = fg;
            SubTab1Grid.Background = bg;
            SubTab2Grid.Background = bg;
            ComparePanel.Background = bg;
            ViewportCard.Background = panel;
            ViewportSurface.Background = dark
                ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#111827"))
                : Brushes.White;

            TxtHeaderTitle.Foreground = fg;
            TxtHeaderSubtitle.Foreground = muted;
            LblSupercell.Foreground = fg;
            LblSnapshotTemp.Foreground = fg;
            TxtCameraStatus.Foreground = muted;
            TxtInteractionHint.Foreground = muted;
            TxtPhaseMetadata.Foreground = fg;
            TxtAtomInspector.Foreground = fg;
            TxtConfigSummary.Foreground = fg;
            GrpPhaseMeta.Background = panel;
            GrpPhaseMeta.Foreground = fg;
            GrpAtomInspect.Background = panel;
            GrpAtomInspect.Foreground = fg;
            GrpSpeciesLegend.Background = panel;

            // Re-apply tab header foregrounds for high contrast visibility
            foreach (var item in PhaseTabsControl.Items)
            {
                if (item is TabItem ti)
                {
                    if (ti.Header is StackPanel sp)
                    {
                        if (sp.Children.Count > 0 && sp.Children[0] is TextBlock tb1)
                            tb1.Foreground = dark ? Brushes.WhiteSmoke : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#0F172A"));
                        if (sp.Children.Count > 1 && sp.Children[1] is TextBlock tb2)
                            tb2.Foreground = dark ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CBD5E1")) : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#334155"));
                    }
                    else if (ti.Header is TextBlock tb)
                    {
                        tb.Foreground = dark ? Brushes.WhiteSmoke : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#0F172A"));
                    }
                }
            }
            GrpSpeciesLegend.Foreground = fg;
            GrpSublattices.Background = panel;
            GrpSublattices.Foreground = fg;
            GrpAtomSites.Background = panel;
            GrpAtomSites.Foreground = fg;
            ConfigSummaryBorder.Background = panel;

            foreach (var grid in new[] { GridSublattices, GridAtomPositions, GridPhaseCompare })
            {
                grid.Background = panel;
                grid.Foreground = fg;
                grid.RowBackground = panel;
                grid.AlternatingRowBackground = panel;
            }

            foreach (var chk in new[] { ChkAtomLabels, ChkUnitCellBox, ChkBonds, ChkSlipPlane, ChkAxesTriad, ChkAutoSpin })
            {
                chk.Foreground = fg;
            }

            SyncAtomLabelsToggle(_atomLabelsEnabled);
            RebuildPhaseTabs();
            RenderActiveScene();
        }

        private CrystalStructureDto? ActivePhase =>
            (_activePhaseIndex >= 0 && _activePhaseIndex < _structures.Count) ? _structures[_activePhaseIndex] : null;

        private void RebuildPhaseTabs()
        {
            _suppressPhaseTabEvent = true;
            try
            {
                PhaseTabsControl.Items.Clear();
                if (_structures.Count == 0)
                {
                    PhaseTabsControl.Items.Add(new TabItem
                    {
                        Header = "No Active Crystal Phases",
                        Foreground = _isDarkTheme ? Brushes.WhiteSmoke : Brushes.Black
                    });
                    PhaseTabsControl.SelectedIndex = 0;
                    return;
                }

                for (int i = 0; i < _structures.Count; i++)
                {
                    var ph = _structures[i];
                    var sp = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(2, 1, 2, 1) };
                    sp.Children.Add(new TextBlock
                    {
                        Text = $"{ph.PhaseName} ({ph.PhaseFractionDisplay})",
                        FontWeight = FontWeights.Bold,
                        FontSize = 12,
                        Foreground = _isDarkTheme ? Brushes.WhiteSmoke : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#0F172A"))
                    });
                    sp.Children.Add(new TextBlock
                    {
                        Text = $"  •  {ph.Strukturbericht} ({ph.PearsonSymbol})",
                        FontSize = 11,
                        VerticalAlignment = VerticalAlignment.Center,
                        Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(_isDarkTheme ? "#CBD5E1" : "#334155"))
                    });

                    PhaseTabsControl.Items.Add(new TabItem
                    {
                        Header = sp,
                        Tag = i,
                        ToolTip = $"{ph.PhaseName}: {ph.CrystalSystem}, {ph.SpaceGroup}"
                    });
                }

                PhaseTabsControl.Items.Add(new TabItem
                {
                    Header = new TextBlock
                    {
                        Text = "All Present Phases Comparison",
                        FontWeight = FontWeights.SemiBold,
                        FontSize = 12,
                        Foreground = _isDarkTheme ? Brushes.WhiteSmoke : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#0F172A"))
                    },
                    Tag = -1
                });

                PhaseTabsControl.SelectedIndex = Math.Clamp(_activePhaseIndex, 0, Math.Max(0, _structures.Count - 1));
            }
            finally
            {
                _suppressPhaseTabEvent = false;
            }
        }

        private void PhaseTabsControl_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_suppressPhaseTabEvent || !IsLoaded || e.Source != PhaseTabsControl) return;
            if (PhaseTabsControl.SelectedItem is not TabItem tab || tab.Tag is not int tagIdx) return;

            if (tagIdx == -1)
            {
                CrystalSubTabs.Visibility = Visibility.Collapsed;
                ComparePanel.Visibility = Visibility.Visible;
            }
            else if (tagIdx >= 0 && tagIdx < _structures.Count)
            {
                CrystalSubTabs.Visibility = Visibility.Visible;
                ComparePanel.Visibility = Visibility.Collapsed;
                SelectPhaseIndex(tagIdx, resetCamera: false);
            }
        }

        private void SelectPhaseIndex(int idx, bool resetCamera)
        {
            if (idx < 0 || idx >= _structures.Count) return;
            _activePhaseIndex = idx;
            _selectedAtom = null;

            _suppressPhaseTabEvent = true;
            try
            {
                if (idx < PhaseTabsControl.Items.Count)
                {
                    PhaseTabsControl.SelectedIndex = idx;
                }
            }
            finally
            {
                _suppressPhaseTabEvent = false;
            }

            var ph = ActivePhase;
            if (ph == null) return;

            if (resetCamera)
            {
                double maxCoord = 3.0;
                foreach (var a in ph.Atoms)
                {
                    double d = Math.Sqrt(a.X * a.X + a.Y * a.Y + a.Z * a.Z);
                    if (d > maxCoord) maxCoord = d;
                }
                _baseDistance = Math.Max(10.0, maxCoord * 3.15);
                _cameraDistance = _baseDistance;
                _panOffset = new Vector3D(0, 0, 0);
            }

            UpdatePhasePanels(ph);
            RenderActiveScene();
        }

        private void UpdatePhasePanels(CrystalStructureDto ph)
        {
            var lp = ph.LatticeParams ?? new LatticeParamsDto();
            TxtPhaseMetadata.Text =
                $"Phase Name      : {ph.PhaseName} ({ph.PhaseFractionDisplay})\n" +
                $"Crystal System  : {ph.CrystalSystem}\n" +
                $"Prototype       : {ph.Prototype}\n" +
                $"Space Group     : {ph.SpaceGroup}\n" +
                $"Strukturbericht : {ph.Strukturbericht}   |   Pearson: {ph.PearsonSymbol}\n" +
                $"Lattice (a,b,c) : {lp.A:F3}, {lp.B:F3}, {lp.C:F3} Å\n" +
                $"Angles (α,β,γ)  : {lp.Alpha:F1}°, {lp.Beta:F1}°, {lp.Gamma:F1}°\n" +
                $"Packing (APF)   : {ph.Apf:F2}   |   Coord. No.: CN {ph.CoordinationNumber}\n" +
                $"Nearest Bond    : {ph.NnDistanceA:F3} Å   |   Z = {ph.ZFormulaUnits}\n" +
                $"Primary Slip    : {ph.SlipSystem}\n" +
                $"Burgers |b|     : {ph.BurgersVectorA:F3} Å   |   Cell: {ph.Supercell}";

            TxtConfigSummary.Text =
                $"Configuration Mechanism ({ph.PhaseName}): {ph.ConfigurationMode} >> {ph.ConfigurationSummary}";

            GridSublattices.ItemsSource = ph.Sublattices;
            GridAtomPositions.ItemsSource = ph.Atoms;
            UpdateAtomInspector(null);

            PanelSpeciesLegend.Children.Clear();
            var colorByEl = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var a in ph.Atoms)
            {
                if (!colorByEl.ContainsKey(a.Symbol))
                    colorByEl[a.Symbol] = a.ColourHex;
            }
            foreach (var kvp in ph.SpeciesCounts.OrderByDescending(kv => kv.Value))
            {
                var hex = colorByEl.TryGetValue(kvp.Key, out var h) ? h : "#3B82F6";
                var chip = new Border
                {
                    Margin = new Thickness(0, 0, 6, 6),
                    Padding = new Thickness(7, 3, 7, 3),
                    CornerRadius = new CornerRadius(10),
                    BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CBD5E1")),
                    BorderThickness = new Thickness(1),
                    Background = _isDarkTheme ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#2D2D30")) : Brushes.White
                };
                var row = new StackPanel { Orientation = Orientation.Horizontal };
                row.Children.Add(new Border
                {
                    Width = 10,
                    Height = 10,
                    CornerRadius = new CornerRadius(5),
                    Background = SafeBrush(hex),
                    BorderBrush = Brushes.Gray,
                    BorderThickness = new Thickness(0.6),
                    Margin = new Thickness(0, 0, 5, 0),
                    VerticalAlignment = VerticalAlignment.Center
                });
                row.Children.Add(new TextBlock
                {
                    Text = $"{kvp.Key} ({kvp.Value})",
                    FontSize = 11,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = _isDarkTheme ? Brushes.WhiteSmoke : Brushes.Black
                });
                chip.Child = row;
                PanelSpeciesLegend.Children.Add(chip);
            }
        }

        private void RenderActiveScene()
        {
            if (HighlightRoot == null || CrystalSceneRoot == null) return;
            _atomLookup.Clear();
            HighlightRoot.Content = null;
            var ph = ActivePhase;
            if (ph == null)
            {
                CrystalSceneRoot.Content = null;
                if (AtomLabelsOverlay != null) AtomLabelsOverlay.Children.Clear();
                return;
            }

            if (NativeDx11Host != null && NativeDx11Host.Visibility == Visibility.Visible)
            {
                double a = ph.LatticeParams?.A ?? 3.59;
                double b = ph.LatticeParams?.B ?? 3.59;
                double c = ph.LatticeParams?.C ?? 3.59;
                NativeDx11Host.UpdatePhase(ph.PhaseName, ph.CrystalSystem, a, b, c, SelectedSupercellN);
                NativeDx11Host.InvalidateRender();
            }

            var group = new Model3DGroup();
            bool sublatticeColour = CmbColourMode.SelectedItem is ComboBoxItem cItem && (cItem.Tag?.ToString() == "sublattice");
            string scaleMode = (CmbScaleMode.SelectedItem is ComboBoxItem sItem ? sItem.Tag?.ToString() : null) ?? "metallic";

            // 1. Optional slip plane polygon
            if (ChkSlipPlane.IsChecked == true && ph.SlipPlanePolygon.Count >= 3)
            {
                var slipMesh = new MeshGeometry3D();
                foreach (var pt in ph.SlipPlanePolygon)
                {
                    slipMesh.Positions.Add(new Point3D(pt[0], pt[1], pt[2]));
                }
                for (int i = 1; i + 1 < ph.SlipPlanePolygon.Count; i++)
                {
                    slipMesh.TriangleIndices.Add(0);
                    slipMesh.TriangleIndices.Add(i);
                    slipMesh.TriangleIndices.Add(i + 1);
                }
                var slipMat = new DiffuseMaterial(new SolidColorBrush(Color.FromArgb(62, 37, 99, 235)));
                var slipModel = new GeometryModel3D(slipMesh, slipMat) { BackMaterial = slipMat };
                group.Children.Add(slipModel);
            }

            // 2. Unit-cell wireframe cage
            if (ChkUnitCellBox.IsChecked == true && ph.UnitCellBox != null)
            {
                var cageMat = new DiffuseMaterial(new SolidColorBrush(_isDarkTheme
                    ? Color.FromRgb(180, 195, 215)
                    : Color.FromRgb(71, 85, 105)));
                var verts = ph.UnitCellBox.Vertices;
                foreach (var edge in ph.UnitCellBox.Edges)
                {
                    if (edge.Count < 2 || edge[0] >= verts.Count || edge[1] >= verts.Count) continue;
                    var p1 = new Point3D(verts[edge[0]][0], verts[edge[0]][1], verts[edge[0]][2]);
                    var p2 = new Point3D(verts[edge[1]][0], verts[edge[1]][1], verts[edge[1]][2]);
                    var cyl = BuildCylinderModel(p1, p2, 0.028, cageMat);
                    if (cyl != null) group.Children.Add(cyl);
                }

                // Crystallographic axes (a=Red, b=Green, c=Blue) from origin vertex[0] -> [1],[3],[4]
                if (ChkAxesTriad.IsChecked == true && verts.Count >= 5)
                {
                    var origin = new Point3D(verts[0][0], verts[0][1], verts[0][2]);
                    AddAxisSegment(group, origin, new Point3D(verts[1][0], verts[1][1], verts[1][2]), Color.FromRgb(220, 38, 38));
                    AddAxisSegment(group, origin, new Point3D(verts[3][0], verts[3][1], verts[3][2]), Color.FromRgb(22, 163, 74));
                    AddAxisSegment(group, origin, new Point3D(verts[4][0], verts[4][1], verts[4][2]), Color.FromRgb(37, 99, 235));
                }
            }

            // 3. Nearest-neighbour cylindrical bonds
            if (ChkBonds.IsChecked == true && ph.Bonds.Count > 0)
            {
                var bondMat = new DiffuseMaterial(new SolidColorBrush(_isDarkTheme
                    ? Color.FromArgb(180, 148, 163, 184)
                    : Color.FromArgb(175, 100, 116, 139)));
                foreach (var b in ph.Bonds)
                {
                    if (b.A < 0 || b.A >= ph.Atoms.Count || b.B < 0 || b.B >= ph.Atoms.Count) continue;
                    var a1 = ph.Atoms[b.A];
                    var a2 = ph.Atoms[b.B];
                    var p1 = new Point3D(a1.X, a1.Y, a1.Z);
                    var p2 = new Point3D(a2.X, a2.Y, a2.Z);
                    var cyl = BuildCylinderModel(p1, p2, scaleMode == "cpk" ? 0.045 : 0.068, bondMat);
                    if (cyl != null) group.Children.Add(cyl);
                }
            }

            // 4. Atom spheres (shared UV-sphere mesh per atom for specular shading + O(1) hit-testing)
            foreach (var atom in ph.Atoms)
            {
                string hex = sublatticeColour ? atom.SublatticeColour : atom.ColourHex;
                var brush = SafeBrush(hex);
                var matGroup = new MaterialGroup();
                matGroup.Children.Add(new DiffuseMaterial(brush));
                matGroup.Children.Add(new SpecularMaterial(new SolidColorBrush(Color.FromArgb(140, 255, 255, 255)), 42.0));

                double r = scaleMode switch
                {
                    "ballstick" => Math.Max(0.24, atom.RadiusA * 0.28),
                    "cpk" => Math.Max(0.42, atom.RadiusA * 0.72),
                    _ => Math.Max(0.30, atom.RadiusA * 0.42)
                };

                var tx = new Transform3DGroup();
                tx.Children.Add(new ScaleTransform3D(r, r, r));
                tx.Children.Add(new TranslateTransform3D(atom.X, atom.Y, atom.Z));

                var model = new GeometryModel3D(_unitSphereMesh, matGroup) { Transform = tx };
                group.Children.Add(model);
                _atomLookup[model] = atom;
            }

            CrystalSceneRoot.Content = group;
            UpdateHighlightHalo();
            UpdateCamera();
        }

        private void UpdateHighlightHalo()
        {
            if (HighlightRoot == null) return;
            if (_selectedAtom == null)
            {
                HighlightRoot.Content = null;
                return;
            }
            var mat = new DiffuseMaterial(new SolidColorBrush(Color.FromArgb(95, 250, 204, 21)));
            double r = Math.Max(0.46, _selectedAtom.RadiusA * 0.58);
            var tx = new Transform3DGroup();
            tx.Children.Add(new ScaleTransform3D(r, r, r));
            tx.Children.Add(new TranslateTransform3D(_selectedAtom.X, _selectedAtom.Y, _selectedAtom.Z));
            HighlightRoot.Content = new GeometryModel3D(_unitSphereMesh, mat) { Transform = tx };
        }

        private void AddAxisSegment(Model3DGroup group, Point3D start, Point3D end, Color color)
        {
            var dir = end - start;
            if (dir.Length < 1e-4) return;
            var tip = start + dir * 0.55;
            var mat = new DiffuseMaterial(new SolidColorBrush(color));
            var cyl = BuildCylinderModel(start, tip, 0.055, mat);
            if (cyl != null) group.Children.Add(cyl);
        }

        private GeometryModel3D? BuildCylinderModel(Point3D p1, Point3D p2, double radius, Material material)
        {
            Vector3D v = p2 - p1;
            double len = v.Length;
            if (len < 1e-5) return null;

            v.Normalize();
            Vector3D yAxis = new(0, 1, 0);
            Vector3D cross = Vector3D.CrossProduct(yAxis, v);
            double dot = Vector3D.DotProduct(yAxis, v);

            var tx = new Transform3DGroup();
            tx.Children.Add(new ScaleTransform3D(radius, len, radius));

            if (cross.Length > 1e-6)
            {
                cross.Normalize();
                double angleDeg = Math.Acos(Math.Clamp(dot, -1.0, 1.0)) * 180.0 / Math.PI;
                tx.Children.Add(new RotateTransform3D(new AxisAngleRotation3D(cross, angleDeg)));
            }
            else if (dot < 0)
            {
                tx.Children.Add(new RotateTransform3D(new AxisAngleRotation3D(new Vector3D(1, 0, 0), 180.0)));
            }

            tx.Children.Add(new TranslateTransform3D(p1.X, p1.Y, p1.Z));
            return new GeometryModel3D(_unitCylinderMesh, material) { Transform = tx };
        }

        private void UpdateCamera()
        {
            if (SceneCamera == null || TxtCameraStatus == null) return;

            Vector3D outVec = RotateVector(_cameraOrientation, new Vector3D(0, 0, 1));
            Vector3D upVec = RotateVector(_cameraOrientation, new Vector3D(0, 1, 0));
            if (outVec.Length < 1e-6) outVec = new Vector3D(0, 0, 1);
            outVec.Normalize();
            if (upVec.Length < 1e-6) upVec = new Vector3D(0, 1, 0);
            upVec.Normalize();

            Point3D target = new(_panOffset.X, _panOffset.Y, _panOffset.Z);
            Point3D camPos = target + outVec * _cameraDistance;

            SceneCamera.Position = camPos;
            SceneCamera.LookDirection = target - camPos;
            SceneCamera.UpDirection = upVec;

            double azDeg = (Math.Atan2(outVec.X, outVec.Z) * 180.0 / Math.PI + 360.0) % 360.0;
            double elDeg = Math.Asin(Math.Clamp(outVec.Y, -1.0, 1.0)) * 180.0 / Math.PI;
            if (upVec.Y < 0.0)
            {
                // Represent continuous pitch beyond +-90 deg across full 360-degree range
                elDeg = elDeg >= 0 ? (180.0 - elDeg) : (-180.0 - elDeg);
            }
            double zoomFactor = _baseDistance / Math.Max(1.0, _cameraDistance);
            int atomCount = ActivePhase?.Atoms.Count ?? 0;
            TxtCameraStatus.Text = $"Azimuth: {azDeg:F0}° | Pitch: {elDeg:F0}° | Zoom: {zoomFactor:F2}× | Atoms: {atomCount}";

            UpdateAtomLabels();
        }

        /// <summary>
        /// Projects 3D atomic coordinates onto the 2D viewport canvas to render toggleable element symbol badges.
        /// </summary>
        private void UpdateAtomLabels()
        {
            if (AtomLabelsOverlay == null || ViewportSurface == null || SceneCamera == null) return;
            AtomLabelsOverlay.Children.Clear();

            if (!_atomLabelsEnabled) return;
            var ph = ActivePhase;
            if (ph == null || ph.Atoms.Count == 0) return;

            double w = ViewportSurface.ActualWidth;
            double h = ViewportSurface.ActualHeight;
            if (w < 20.0 || h < 20.0) return;

            Vector3D look = SceneCamera.LookDirection;
            if (look.Length < 1e-6) return;
            look.Normalize();

            Vector3D right = Vector3D.CrossProduct(look, SceneCamera.UpDirection);
            if (right.Length < 1e-6) return;
            right.Normalize();

            Vector3D up = Vector3D.CrossProduct(right, look);
            double tanHalfFov = Math.Tan((SceneCamera.FieldOfView * 0.5) * Math.PI / 180.0);
            double aspect = w / h;
            double tanHalfFovY = tanHalfFov / Math.Max(0.1, aspect);

            var projected = new List<(CrystalAtomDto Atom, double Sx, double Sy, double Depth)>(ph.Atoms.Count);
            foreach (var atom in ph.Atoms)
            {
                Vector3D rel = new Point3D(atom.X, atom.Y, atom.Z) - SceneCamera.Position;
                double zCam = Vector3D.DotProduct(rel, look);
                if (zCam <= 0.2) continue;

                double xCam = Vector3D.DotProduct(rel, right);
                double yCam = Vector3D.DotProduct(rel, up);

                double uNdc = xCam / (zCam * tanHalfFov);
                double vNdc = yCam / (zCam * tanHalfFovY);

                double sx = w * 0.5 * (1.0 + uNdc);
                double sy = h * 0.5 * (1.0 - vNdc);

                if (sx < -24 || sx > w + 24 || sy < -24 || sy > h + 24) continue;
                projected.Add((atom, sx, sy, zCam));
            }

            // Paint farthest atoms first so foreground atom labels stay cleanly on top
            foreach (var item in projected.OrderByDescending(p => p.Depth))
            {
                bool isSel = _selectedAtom != null && _selectedAtom.Index == item.Atom.Index;
                var badge = new Border
                {
                    Background = isSel
                        ? new SolidColorBrush(Color.FromArgb(245, 254, 240, 138))
                        : new SolidColorBrush(Color.FromArgb(228, 255, 255, 255)),
                    BorderBrush = isSel
                        ? new SolidColorBrush(Color.FromRgb(180, 83, 9))
                        : new SolidColorBrush(Color.FromRgb(100, 116, 139)),
                    BorderThickness = new Thickness(isSel ? 1.5 : 0.9),
                    CornerRadius = new CornerRadius(4),
                    Padding = new Thickness(3.5, 0.5, 3.5, 0.5),
                    Child = new TextBlock
                    {
                        Text = item.Atom.Symbol,
                        FontSize = 10.5,
                        FontWeight = FontWeights.Bold,
                        Foreground = Brushes.Black
                    }
                };
                badge.Measure(new Size(double.PositiveInfinity, double.PositiveInfinity));
                Canvas.SetLeft(badge, item.Sx - badge.DesiredSize.Width * 0.5);
                Canvas.SetTop(badge, item.Sy - badge.DesiredSize.Height * 0.5);
                AtomLabelsOverlay.Children.Add(badge);
            }
        }

        private void UpdateAtomInspector(CrystalAtomDto? atom)
        {
            if (atom == null)
            {
                TxtAtomInspector.Text = "Click any atom sphere inside the 3D viewport (or select a row in the Atomic Configuration sub-tab) to inspect its site metadata.";
                return;
            }
            TxtAtomInspector.Text =
                $"Atom Index      : #{atom.Index}\n" +
                $"Element         : {atom.Symbol} ({atom.ElementName})\n" +
                $"Wyckoff Site    : {atom.Wyckoff}\n" +
                $"Sublattice      : {atom.Sublattice}\n" +
                $"Atomic Radius   : {atom.RadiusPm:F1} pm ({atom.RadiusA:F3} Å)\n" +
                $"Fractional (u,v,w): {atom.FracDisplay}\n" +
                $"Cartesian (Å)   : {atom.CartDisplay}";
        }

        // -------------------------------------------------------------------
        // Viewport Mouse Orbit / Pan / Zoom & 3D Atom Hit-Testing
        // -------------------------------------------------------------------
        private void ViewportSurface_SizeChanged(object sender, SizeChangedEventArgs e)
        {
            if (IsLoaded) UpdateAtomLabels();
        }

        private void ViewportSurface_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            _mouseDownPos = e.GetPosition(ViewportSurface);
            _lastMousePos = _mouseDownPos;
            if ((Keyboard.Modifiers & ModifierKeys.Shift) == ModifierKeys.Shift)
            {
                _isPanning = true;
                _isOrbiting = false;
            }
            else
            {
                _isOrbiting = true;
                _isPanning = false;
            }
            ViewportSurface.CaptureMouse();
        }

        private void ViewportSurface_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (_isOrbiting || _isPanning)
            {
                bool wasOrbit = _isOrbiting;
                _isOrbiting = false;
                _isPanning = false;
                ViewportSurface.ReleaseMouseCapture();
                Point upPos = e.GetPosition(ViewportSurface);
                if (wasOrbit && (upPos - _mouseDownPos).Length < 5.0)
                {
                    PerformAtomHitTest(upPos);
                }
            }
        }

        private void ViewportSurface_MouseRightButtonDown(object sender, MouseButtonEventArgs e)
        {
            _lastMousePos = e.GetPosition(ViewportSurface);
            _isPanning = true;
            _isOrbiting = false;
            ViewportSurface.CaptureMouse();
        }

        private void ViewportSurface_MouseRightButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (_isPanning)
            {
                _isPanning = false;
                ViewportSurface.ReleaseMouseCapture();
            }
        }

        private void ViewportSurface_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Middle)
            {
                _lastMousePos = e.GetPosition(ViewportSurface);
                _isPanning = true;
                _isOrbiting = false;
                ViewportSurface.CaptureMouse();
                e.Handled = true;
            }
        }

        private void ViewportSurface_MouseUp(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Middle && _isPanning)
            {
                _isPanning = false;
                ViewportSurface.ReleaseMouseCapture();
                e.Handled = true;
            }
        }

        private void ViewportSurface_MouseMove(object sender, MouseEventArgs e)
        {
            Point cur = e.GetPosition(ViewportSurface);
            double dx = cur.X - _lastMousePos.X;
            double dy = cur.Y - _lastMousePos.Y;
            _lastMousePos = cur;

            if (_isOrbiting)
            {
                Vector3D right = RotateVector(_cameraOrientation, new Vector3D(1, 0, 0));
                Vector3D up = RotateVector(_cameraOrientation, new Vector3D(0, 1, 0));
                if (right.Length > 1e-6) right.Normalize();
                if (up.Length > 1e-6) up.Normalize();

                var qYaw = new Quaternion(up, -dx * 0.45);
                var qPitch = new Quaternion(right, -dy * 0.45);
                _cameraOrientation = qYaw * qPitch * _cameraOrientation;
                _cameraOrientation.Normalize();
                UpdateCamera();
            }
            else if (_isPanning)
            {
                Vector3D right = RotateVector(_cameraOrientation, new Vector3D(1, 0, 0));
                Vector3D up = RotateVector(_cameraOrientation, new Vector3D(0, 1, 0));
                if (right.Length > 1e-6) right.Normalize();
                if (up.Length > 1e-6) up.Normalize();

                double panScale = _cameraDistance * 0.0018;
                _panOffset -= right * (dx * panScale);
                _panOffset += up * (dy * panScale);
                UpdateCamera();
            }
        }

        private void ViewportSurface_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            double factor = e.Delta > 0 ? 0.88 : 1.13;
            _cameraDistance = Math.Clamp(_cameraDistance * factor, 3.0, Math.Max(45.0, _baseDistance * 3.5));
            UpdateCamera();
        }

        private void PerformAtomHitTest(Point ptInViewport)
        {
            PointHitTestParameters hp = new(ptInViewport);
            VisualTreeHelper.HitTest(CrystalViewport, null, res =>
            {
                if (res is RayMeshGeometry3DHitTestResult meshHit &&
                    meshHit.ModelHit != null &&
                    _atomLookup.TryGetValue(meshHit.ModelHit, out var atom))
                {
                    _selectedAtom = atom;
                    UpdateAtomInspector(atom);
                    UpdateHighlightHalo();
                    UpdateAtomLabels();
                    return HitTestResultBehavior.Stop;
                }
                return HitTestResultBehavior.Continue;
            }, hp);
        }

        // -------------------------------------------------------------------
        // Expand / Pop-Out / UI Control Handlers
        // -------------------------------------------------------------------
        private void BtnExpand3D_Click(object sender, RoutedEventArgs e)
        {
            _is3DExpanded = !_is3DExpanded;
            if (_is3DExpanded)
            {
                if (ColInspector.Width.Value > 10)
                    _savedInspectorWidth = ColInspector.Width.Value;
                ColInspector.Width = new GridLength(0);
                ColSplitter.Width = new GridLength(0);
                HeaderBorder.Visibility = Visibility.Collapsed;
                BtnExpand3D.Content = "✕ Restore View";
            }
            else
            {
                ColInspector.Width = new GridLength(Math.Max(260.0, _savedInspectorWidth));
                ColSplitter.Width = new GridLength(6);
                HeaderBorder.Visibility = Visibility.Visible;
                BtnExpand3D.Content = "⛶ Expand 3D";
            }

            if (!_isPopOutWindow)
            {
                Expand3DToggled?.Invoke(_is3DExpanded);
            }
            Dispatcher.BeginInvoke(DispatcherPriority.Render, new Action(UpdateAtomLabels));
        }

        private void BtnPopOut3D_Click(object sender, RoutedEventArgs e)
        {
            if (_structures.Count == 0) return;

            var childControl = new CrystalStructureControl { _isPopOutWindow = true };
            childControl.BtnPopOut3D.Visibility = Visibility.Collapsed;
            childControl.BtnExpand3D.ToolTip = "Collapse/expand inspector side panel";
            childControl.SetSnapshotControls(SelectedSupercellN, SelectedTemperatureK);
            childControl.ApplyTheme(_isDarkTheme);
            childControl.SyncAtomLabelsToggle(_atomLabelsEnabled);
            childControl.SetCrystalStructures(_structures, TxtHeaderSubtitle.Text);
            if (_activePhaseIndex >= 0 && _activePhaseIndex < _structures.Count)
            {
                childControl.SelectPhaseIndex(_activePhaseIndex, resetCamera: true);
            }
            childControl.RebuildStructuresRequested += (n, t) => RebuildStructuresRequested?.Invoke(n, t);

            var win = new Window
            {
                Title = "CALPHAD XOC >> Expanded 3D Crystal Structures Viewer",
                Width = 1180,
                Height = 760,
                MinWidth = 760,
                MinHeight = 540,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                Owner = Window.GetWindow(this),
                Background = _isDarkTheme ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1E1E1E")) : Brushes.White,
                Content = childControl
            };
            win.Show();
        }

        private void SyncAtomLabelsToggle(bool isEnabled)
        {
            if (_isSyncingLabelToggle) return;
            _isSyncingLabelToggle = true;
            try
            {
                _atomLabelsEnabled = isEnabled;
                if (ChkAtomLabels != null) ChkAtomLabels.IsChecked = isEnabled;
                if (BtnToggleAtomLabels != null)
                {
                    BtnToggleAtomLabels.IsChecked = isEnabled;
                    BtnToggleAtomLabels.Content = isEnabled ? "Element Labels: ON" : "Element Labels: OFF";
                    BtnToggleAtomLabels.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(
                        isEnabled ? (_isDarkTheme ? "#1E3A8A" : "#EFF6FF") : (_isDarkTheme ? "#2D2D30" : "#F8FAFC")));
                    BtnToggleAtomLabels.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(
                        isEnabled ? (_isDarkTheme ? "#DBEAFE" : "#1E3A8A") : (_isDarkTheme ? "#CBD5E1" : "#475569")));
                }
            }
            finally
            {
                _isSyncingLabelToggle = false;
            }
            UpdateAtomLabels();
        }

        private void BtnToggleAtomLabels_Changed(object sender, RoutedEventArgs e)
        {
            if (!IsLoaded || _isSyncingLabelToggle) return;
            SyncAtomLabelsToggle(BtnToggleAtomLabels?.IsChecked == true);
        }

        private void VisualOption_Changed(object sender, RoutedEventArgs e)
        {
            if (!IsLoaded) return;
            if (sender == ChkAtomLabels)
            {
                if (!_isSyncingLabelToggle)
                {
                    SyncAtomLabelsToggle(ChkAtomLabels?.IsChecked == true);
                }
                return;
            }
            RenderActiveScene();
        }

        private void VisualOption_ComboChanged(object sender, SelectionChangedEventArgs e)
        {
            if (IsLoaded) RenderActiveScene();
        }

        private void CmbRenderEngine_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (!IsLoaded || CmbRenderEngine == null || GridWpf3DViewport == null || NativeDx11Host == null) return;

            if (CmbRenderEngine.SelectedItem is ComboBoxItem item && item.Tag?.ToString() == "dx11")
            {
                GridWpf3DViewport.Visibility = Visibility.Collapsed;
                NativeDx11Host.Visibility = Visibility.Visible;
                if (ActivePhase != null)
                {
                    double a = ActivePhase.LatticeParams?.A ?? 3.59;
                    double b = ActivePhase.LatticeParams?.B ?? 3.59;
                    double c = ActivePhase.LatticeParams?.C ?? 3.59;
                    NativeDx11Host.UpdatePhase(ActivePhase.PhaseName, ActivePhase.CrystalSystem, a, b, c, SelectedSupercellN);
                }
                NativeDx11Host.InvalidateRender();
            }
            else
            {
                NativeDx11Host.Visibility = Visibility.Collapsed;
                GridWpf3DViewport.Visibility = Visibility.Visible;
                RenderActiveScene();
            }
        }

        private void ChkAutoSpin_Changed(object sender, RoutedEventArgs e)
        {
            if (_spinTimer == null || !IsLoaded) return;
            if (ChkAutoSpin.IsChecked == true || _sweepRemainingDeg > 0.0) _spinTimer.Start();
            else _spinTimer.Stop();
        }

        private void BtnRotate180_Click(object sender, RoutedEventArgs e)
        {
            RotateCameraAroundLocalUp(180.0);
            UpdateCamera();
        }

        private void BtnSpin360_Click(object sender, RoutedEventArgs e)
        {
            if (_structures.Count == 0) return;
            _sweepRemainingDeg = 360.0;
            _spinTimer.Start();
        }

        private void BtnResetCamera_Click(object sender, RoutedEventArgs e)
        {
            _sweepRemainingDeg = 0.0;
            _cameraOrientation = DefaultCameraOrientation();
            _cameraDistance = _baseDistance;
            _panOffset = new Vector3D(0, 0, 0);
            UpdateCamera();
        }

        public static void RenderVisualToPng(FrameworkElement visual, string filePath, double dpi = 192.0)
        {
            double width = Math.Max(1.0, visual.ActualWidth);
            double height = Math.Max(1.0, visual.ActualHeight);
            int pixelW = Math.Max(1, (int)Math.Ceiling(width * dpi / 96.0));
            int pixelH = Math.Max(1, (int)Math.Ceiling(height * dpi / 96.0));

            var rtb = new RenderTargetBitmap(pixelW, pixelH, dpi, dpi, PixelFormats.Pbgra32);
            rtb.Render(visual);

            var encoder = new PngBitmapEncoder();
            encoder.Frames.Add(BitmapFrame.Create(rtb));
            using var fs = new FileStream(filePath, FileMode.Create, FileAccess.Write, FileShare.None);
            encoder.Save(fs);
        }

        private void BtnExportPng_Click(object sender, RoutedEventArgs e)
        {
            if (ViewportSurface.ActualWidth < 10.0 || ViewportSurface.ActualHeight < 10.0)
            {
                MessageBox.Show("3D viewport is not yet rendered on screen.", "Export PNG", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string rawPhase = ActivePhase?.PhaseName ?? "Crystal_Structure";
            string safePhase = string.Concat(rawPhase.Select(ch => char.IsLetterOrDigit(ch) ? ch : '_')).Trim('_');
            if (string.IsNullOrWhiteSpace(safePhase)) safePhase = "Crystal_Structure";

            var dlg = new SaveFileDialog
            {
                Title = "Export 3D Crystal Structure PNG",
                Filter = "PNG Image (*.png)|*.png",
                DefaultExt = ".png",
                FileName = $"{safePhase}_3D_Crystal.png"
            };
            if (dlg.ShowDialog() != true) return;

            try
            {
                RenderVisualToPng(ViewportSurface, dlg.FileName, dpi: 192.0);
                TxtCameraStatus.Text = $"Saved PNG: {Path.GetFileName(dlg.FileName)}";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to export 3D crystal PNG:\n{ex.Message}", "Export PNG Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CmbRebuildParam_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (!_suppressRebuildEvent && IsLoaded)
            {
                RebuildStructuresRequested?.Invoke(SelectedSupercellN, SelectedTemperatureK);
            }
        }

        private void BtnRefreshStructures_Click(object sender, RoutedEventArgs e)
        {
            RebuildStructuresRequested?.Invoke(SelectedSupercellN, SelectedTemperatureK);
        }

        private void GridAtomPositions_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (GridAtomPositions.SelectedItem is CrystalAtomDto atom)
            {
                _selectedAtom = atom;
                UpdateAtomInspector(atom);
                UpdateHighlightHalo();
                UpdateAtomLabels();
            }
        }

        private void GridPhaseCompare_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (GridPhaseCompare.SelectedItem is CrystalStructureDto ph)
            {
                int idx = _structures.IndexOf(ph);
                if (idx >= 0)
                {
                    CrystalSubTabs.Visibility = Visibility.Visible;
                    ComparePanel.Visibility = Visibility.Collapsed;
                    SelectPhaseIndex(idx, resetCamera: false);
                }
            }
        }

        // -------------------------------------------------------------------
        // Static Unit Mesh Builders (Sphere & Cylinder Primitives)
        // -------------------------------------------------------------------
        private static SolidColorBrush SafeBrush(string? hex)
        {
            try
            {
                if (!string.IsNullOrWhiteSpace(hex))
                {
                    return new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
                }
            }
            catch
            {
                // Fallback on malformed hex strings
            }
            return new SolidColorBrush(Color.FromRgb(59, 130, 246));
        }

        private static MeshGeometry3D BuildUnitSphereMesh(int latBands, int lonBands)
        {
            var mesh = new MeshGeometry3D();
            for (int lat = 0; lat <= latBands; lat++)
            {
                double theta = lat * Math.PI / latBands;
                double sinT = Math.Sin(theta);
                double cosT = Math.Cos(theta);

                for (int lon = 0; lon <= lonBands; lon++)
                {
                    double phi = lon * 2.0 * Math.PI / lonBands;
                    double x = cosT < -0.9999 || cosT > 0.9999 ? 0.0 : sinT * Math.Cos(phi);
                    double y = cosT;
                    double z = cosT < -0.9999 || cosT > 0.9999 ? 0.0 : sinT * Math.Sin(phi);
                    mesh.Positions.Add(new Point3D(x, y, z));
                    mesh.Normals.Add(new Vector3D(x, y, z));
                }
            }

            int stride = lonBands + 1;
            for (int lat = 0; lat < latBands; lat++)
            {
                for (int lon = 0; lon < lonBands; lon++)
                {
                    int first = lat * stride + lon;
                    int second = first + stride;
                    mesh.TriangleIndices.Add(first);
                    mesh.TriangleIndices.Add(first + 1);
                    mesh.TriangleIndices.Add(second);

                    mesh.TriangleIndices.Add(second);
                    mesh.TriangleIndices.Add(first + 1);
                    mesh.TriangleIndices.Add(second + 1);
                }
            }
            mesh.Freeze();
            return mesh;
        }

        private static MeshGeometry3D BuildUnitCylinderMesh(int segments)
        {
            var mesh = new MeshGeometry3D();
            for (int i = 0; i <= segments; i++)
            {
                double angle = i * 2.0 * Math.PI / segments;
                double x = Math.Cos(angle);
                double z = Math.Sin(angle);
                var normal = new Vector3D(x, 0, z);
                mesh.Positions.Add(new Point3D(x, 0.0, z));
                mesh.Normals.Add(normal);
                mesh.Positions.Add(new Point3D(x, 1.0, z));
                mesh.Normals.Add(normal);
            }

            for (int i = 0; i < segments; i++)
            {
                int b0 = i * 2;
                int t0 = b0 + 1;
                int b1 = b0 + 2;
                int t1 = b0 + 3;

                mesh.TriangleIndices.Add(b0);
                mesh.TriangleIndices.Add(t0);
                mesh.TriangleIndices.Add(b1);

                mesh.TriangleIndices.Add(b1);
                mesh.TriangleIndices.Add(t0);
                mesh.TriangleIndices.Add(t1);
            }
            mesh.Freeze();
            return mesh;
        }
    }
}
