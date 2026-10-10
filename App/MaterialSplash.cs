using System;
using System.IO;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;
using System.Threading;

public class MaterialSplashForm : Form {
    private System.Windows.Forms.Timer animTimer;
    private float currentPct = 0f;
    private float targetPct = 0f;
    private float wavePhase = 0f;
    private string statusTitle = "Initializing High-Entropy Alloy Core...";
    private string statusDetail = "Mounting secure local memory and configuration...";
    private string ipcFilePath;
    private bool isExiting = false;
    private float opacityVal = 0.05f;
    private int tickCount = 0;

    public MaterialSplashForm(string ipcPath) {
        this.ipcFilePath = ipcPath;
        this.FormBorderStyle = FormBorderStyle.None;
        this.StartPosition = FormStartPosition.CenterScreen;
        this.Size = new Size(520, 480);
        this.BackColor = Color.FromArgb(25, 31, 38); // Exact #191F26 Dark Slate
        this.ShowInTaskbar = true;
        this.TopMost = true;
        this.Opacity = 0.05;

        // Set application taskbar icon
        try {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string icoFile = Path.Combine(baseDir, "resources", "app_icon.ico");
            if (!File.Exists(icoFile)) {
                icoFile = Path.Combine(baseDir, "app_icon.ico");
            }
            if (File.Exists(icoFile)) {
                this.Icon = new Icon(icoFile);
            }
        } catch { }

        // Initialize IPC file with 0% (empty flask)
        try {
            if (!string.IsNullOrEmpty(ipcFilePath)) {
                File.WriteAllText(ipcFilePath, "0\nInitializing High-Entropy Alloy Core...\nMounting secure local memory and configuration...\n\n");
            }
        } catch { }

        // Animation & IPC polling timer: 40 FPS (25ms)
        animTimer = new System.Windows.Forms.Timer();
        animTimer.Interval = 25;
        animTimer.Tick += OnAnimTick;
        animTimer.Start();
    }

    private void OnAnimTick(object sender, EventArgs e) {
        tickCount++;
        wavePhase += 0.085f;
        if (wavePhase > 62.83f) wavePhase -= 62.83f;

        // Smooth fade-in on startup
        if (!isExiting && opacityVal < 1.0f) {
            opacityVal += 0.15f;
            if (opacityVal > 1.0f) opacityVal = 1.0f;
            this.Opacity = opacityVal;
        }

        // Smooth progress interpolation towards targetPct
        if (Math.Abs(targetPct - currentPct) > 0.1f) {
            currentPct += (targetPct - currentPct) * 0.18f;
        } else {
            currentPct = targetPct;
        }

        // Poll IPC file every ~50ms (every 2 ticks)
        if (tickCount % 2 == 0 && !string.IsNullOrEmpty(ipcFilePath) && File.Exists(ipcFilePath)) {
            try {
                using (var fs = new FileStream(ipcFilePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (var sr = new StreamReader(fs)) {
                    string l1 = sr.ReadLine();
                    string l2 = sr.ReadLine();
                    string l3 = sr.ReadLine();

                    if (!string.IsNullOrEmpty(l1)) {
                        string val = l1.Trim().ToUpper();
                        if (val == "EXIT") {
                            targetPct = 100f;
                            // When EXIT is signaled, ensure flask is completely full then smoothly exit
                            if (currentPct >= 96f || tickCount > 80) {
                                isExiting = true;
                            }
                        } else {
                            float p;
                            if (float.TryParse(val, out p)) {
                                targetPct = Math.Max(0f, Math.Min(100f, p));
                            }
                        }
                    }
                    if (!string.IsNullOrEmpty(l2)) statusTitle = l2.Trim();
                    if (!string.IsNullOrEmpty(l3)) statusDetail = l3.Trim();
                }
            } catch { }
        }

        // Smooth fade-out on exit
        if (isExiting) {
            opacityVal -= 0.12f;
            if (opacityVal <= 0.04f) {
                animTimer.Stop();
                this.Close();
                Application.Exit();
                return;
            }
            this.Opacity = Math.Max(0.0, opacityVal);
        }

        // Safety timeout: auto-close after 25 seconds
        if (tickCount > 25 * 40) {
            isExiting = true;
        }

        this.Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e) {
        Graphics g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TextRenderingHint = TextRenderingHint.ClearTypeGridFit;

        int W = this.ClientSize.Width;
        int H = this.ClientSize.Height;

        // 1. Background & Perimeter Border
        using (SolidBrush bgBrush = new SolidBrush(Color.FromArgb(25, 31, 38))) {
            g.FillRectangle(bgBrush, 0, 0, W, H);
        }
        using (Pen borderPen = new Pen(Color.FromArgb(38, 48, 60), 1f)) {
            g.DrawRectangle(borderPen, 0, 0, W - 1, H - 1);
        }

        // 2. Render Laboratory Florence Flask
        RenderFlorenceFlask(g, W, H, currentPct, wavePhase);
    }

    private void RenderFlorenceFlask(Graphics g, int W, int H, float pct, float phase) {
        float cx = W / 2f;
        float cyTop = 86f;
        float scale = 1.15f; // Crisp proportions for desktop display

        // High-fidelity control points traced from laboratory reference
        PointF[] leftContour = new PointF[] {
            new PointF(-23.5f * scale, 1.0f * scale),   // flared lip tip
            new PointF(-21.0f * scale, 4.0f * scale),
            new PointF(-19.0f * scale, 11.0f * scale),  // vertical neck start
            new PointF(-19.0f * scale, 35.0f * scale),
            new PointF(-19.0f * scale, 64.0f * scale),  // vertical neck end
            new PointF(-22.0f * scale, 71.0f * scale),  // shoulder flare
            new PointF(-32.0f * scale, 76.0f * scale),
            new PointF(-42.0f * scale, 83.0f * scale),
            new PointF(-49.0f * scale, 91.0f * scale),
            new PointF(-54.5f * scale, 101.0f * scale),
            new PointF(-57.5f * scale, 111.0f * scale),
            new PointF(-58.5f * scale, 118.0f * scale), // widest bulb
            new PointF(-57.5f * scale, 125.0f * scale),
            new PointF(-54.5f * scale, 134.0f * scale),
            new PointF(-49.5f * scale, 144.0f * scale),
            new PointF(-42.0f * scale, 153.0f * scale),
            new PointF(-33.0f * scale, 161.0f * scale), // base corner
            new PointF(-24.0f * scale, 166.0f * scale), // flat base left
            new PointF(0.0f, 167.0f * scale)            // flat base center
        };

        int nPts = leftContour.Length;
        PointF[] outerPts = new PointF[nPts * 2 - 1];
        PointF[] innerPts = new PointF[nPts * 2 - 1];

        float strokeHalf = 2.0f; // 4px stroke
        float yBaseCenter = cyTop + 167.0f * scale;

        for (int i = 0; i < nPts; i++) {
            float lx = cx + leftContour[i].X;
            float ly = cyTop + leftContour[i].Y;
            outerPts[i] = new PointF(lx, ly);

            // Inward deflated point for inner cavity clipping
            float inLx = (i == nPts - 1) ? cx : cx + (leftContour[i].X + strokeHalf * (leftContour[i].X < 0 ? 1 : -1));
            float inLy = (i == nPts - 1) ? ly - strokeHalf : ly;
            innerPts[i] = new PointF(inLx, inLy);

            if (i > 0) {
                int rIdx = nPts * 2 - 1 - i;
                float rx = cx - leftContour[i].X;
                float ry = cyTop + leftContour[i].Y;
                outerPts[rIdx] = new PointF(rx, ry);

                float inRx = cx - (leftContour[i].X + strokeHalf * (leftContour[i].X < 0 ? 1 : -1));
                innerPts[rIdx] = new PointF(inRx, inLy);
            }
        }

        using (GraphicsPath outerPath = new GraphicsPath())
        using (GraphicsPath innerPath = new GraphicsPath()) {
            outerPath.AddCurve(outerPts, 0.35f);
            innerPath.AddCurve(innerPts, 0.35f);
            innerPath.CloseFigure();

            // 1. Draw Rising Sloshing Liquid inside Flask if pct > 0
            if (pct > 0.4f) {
                GraphicsState gState = g.Save();
                g.SetClip(innerPath);

                float totalH = (167.0f - 14.0f) * scale;
                float clampedPct = Math.Min(100f, Math.Max(0f, pct));
                float liquidH = (clampedPct / 100f) * totalH;
                float baseSurfaceY = (yBaseCenter - strokeHalf) - liquidH;

                // Wave amplitude: settles gently as flask becomes completely full (100%)
                float waveAmp = (clampedPct > 94f) ? 1.4f : (clampedPct < 8f ? 1.5f : 3.8f);

                using (GraphicsPath liquidPath = new GraphicsPath()) {
                    float xStart = cx - 75f * scale;
                    float xEnd = cx + 75f * scale;
                    int steps = 60;
                    PointF[] wavePts = new PointF[steps + 3];

                    wavePts[0] = new PointF(xStart, H + 20);
                    for (int s = 0; s <= steps; s++) {
                        float curX = xStart + (xEnd - xStart) * (s / (float)steps);
                        float wy = baseSurfaceY +
                            waveAmp * (float)Math.Sin((curX - cx) * 0.075f + phase) +
                            (waveAmp * 0.35f) * (float)Math.Cos((curX - cx) * 0.15f - phase * 0.8f);
                        wavePts[s + 1] = new PointF(curX, wy);
                    }
                    wavePts[steps + 2] = new PointF(xEnd, H + 20);

                    liquidPath.AddPolygon(wavePts);

                    // Liquid fill: Gradient matching user GIF (#0AF0FF to #0070E0)
                    RectangleF liqRect = new RectangleF(cx - 75f * scale, baseSurfaceY - 5, 150f * scale, totalH + 40);
                    using (LinearGradientBrush liqBrush = new LinearGradientBrush(
                        liqRect,
                        Color.FromArgb(10, 240, 255), // #0AF0FF Electric Cyan
                        Color.FromArgb(0, 118, 230),  // #0076E6 Deep Azure
                        LinearGradientMode.Vertical)) {
                        g.FillPath(liqBrush, liquidPath);
                    }

                    // Gentle luminous wave crest highlight line
                    using (Pen crestPen = new Pen(Color.FromArgb(180, 255, 255, 255), 1.6f)) {
                        PointF[] crestLine = new PointF[steps + 1];
                        Array.Copy(wavePts, 1, crestLine, 0, steps + 1);
                        g.DrawCurve(crestPen, crestLine, 0.35f);
                    }
                }

                g.Restore(gState);
            }

            // 2. Draw Crisp White Outer Flask Outline (Open Lip at Top)
            using (Pen flaskPen = new Pen(Color.White, 3.8f)) {
                flaskPen.StartCap = LineCap.Round;
                flaskPen.EndCap = LineCap.Round;
                flaskPen.LineJoin = LineJoin.Round;
                g.DrawPath(flaskPen, outerPath);
            }
        }

        // 3. Draw "loading" in clean modern lowercase typography
        int dotStage = (tickCount / 10) % 4; // cycles 0, 1, 2, 3 every 250ms
        string dots = new string('.', dotStage);
        string loadDisplay = "loading" + dots;

        using (Font loadFont = new Font("Segoe UI", 16f, FontStyle.Regular))
        using (SolidBrush textBrush = new SolidBrush(Color.FromArgb(241, 245, 249))) {
            SizeF loadSize = g.MeasureString("loading...", loadFont);
            // Center based on fixed width so the text does not jitter
            float textX = cx - loadSize.Width / 2f + 8f;
            g.DrawString(loadDisplay, loadFont, textBrush, textX, yBaseCenter + 26f);
        }

        // 4. Draw Real-Time Subtitle and Progress
        using (Font statFont = new Font("Segoe UI", 10.5f, FontStyle.Regular))
        using (SolidBrush statBrush = new SolidBrush(Color.FromArgb(148, 163, 184))) {
            string statStr = string.Format("{0} • {1}%", statusTitle, (int)Math.Round(pct));
            if (pct >= 100f) statStr = "Ready! Workspace Mounted • 100%";
            SizeF statSize = g.MeasureString(statStr, statFont);
            g.DrawString(statStr, statFont, statBrush, cx - statSize.Width / 2f, yBaseCenter + 64f);
        }

        // 5. Draw Subtle Detail Subtext
        using (Font detFont = new Font("Segoe UI", 8.5f, FontStyle.Regular))
        using (SolidBrush detBrush = new SolidBrush(Color.FromArgb(100, 116, 139))) {
            SizeF detSize = g.MeasureString(statusDetail, detFont);
            g.DrawString(statusDetail, detFont, detBrush, cx - detSize.Width / 2f, yBaseCenter + 88f);
        }
    }

    [STAThread]
    public static void Main(string[] args) {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        string ipc = args.Length > 0 ? args[0] : Path.Combine(Path.GetTempPath(), "mat_splash_ipc.txt");
        Application.Run(new MaterialSplashForm(ipc));
    }
}
