#!/usr/bin/env bash
# =============================================================================
# CALPHADHEACalc: Software Installation Script (Linux & macOS)
# Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================================="
echo "  CALPHADHEACalc: Software Installation Wizard (Linux / macOS)               "
echo "  Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)        "
echo "============================================================================="
echo ""

# 1. Verify Core Repository Files
echo "[1/4] Verifying repository core files..."
REQUIRED_FILES=("index.html" "docs/index.html" "App/CALPHADHEACalc.m")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  [ERROR] Missing required file: $file"
        exit 1
    fi
done
echo "  Repository integrity verified."
echo ""

# 2. Set Execute Permissions
echo "[2/4] Setting execution permissions..."
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
echo "  Shell scripts made executable."
echo ""

# 3. Detect Runtimes
echo "[3/4] Detecting available runtimes..."
NODE_READY=0
if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node -v)
    echo "  [FOUND] Node.js $NODE_VER detected (Decoupled API Server ready)"
    NODE_READY=1
else
    echo "  [INFO] Node.js not found (Optional: required for decoupled API streaming)"
fi

MATLAB_READY=0
if command -v matlab >/dev/null 2>&1; then
    echo "  [FOUND] MATLAB detected in PATH"
    MATLAB_READY=1
    echo "  Registering search path in MATLAB..."
    matlab -batch "try, addpath(genpath('$SCRIPT_DIR')); savepath; disp('[SUCCESS] MATLAB search path saved.'); catch ME, disp(ME.message); end" >/dev/null 2>&1 || true
else
    echo "  [INFO] MATLAB not found (Standalone Web & Desktop suites run 100% without MATLAB)"
fi
echo ""

# 4. Create Desktop Launcher on Linux
echo "[4/4] Configuring desktop launcher..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DESKTOP_DIR="$HOME/.local/share/applications"
    if [ -d "$DESKTOP_DIR" ]; then
        CAT_FILE="$DESKTOP_DIR/calphadheacalc.desktop"
        cat > "$CAT_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CALPHADHEACalc
Comment=High-Entropy Alloy Multi-Physics Thermodynamic Software
Exec=xdg-open "$SCRIPT_DIR/index.html"
Icon=$SCRIPT_DIR/resources/AppIcon.png
Terminal=false
Categories=Science;Education;Physics;
EOF
        chmod +x "$CAT_FILE"
        echo "  [CREATED] Linux Desktop Application Entry: $CAT_FILE"
    fi
fi

echo ""
echo "============================================================================="
echo "  INSTALLATION SUMMARY                                                       "
echo "============================================================================="
echo "  Software Version   : CALPHADHEACalc v3.4.0"
echo "  Installation Path  : $SCRIPT_DIR"
echo "  Standalone Web App : Ready (Open index.html in any browser)"
if [ "$NODE_READY" -eq 1 ]; then
echo "  Decoupled Server   : Ready (Run: node scripts/server.js)"
fi
if [ "$MATLAB_READY" -eq 1 ]; then
echo "  MATLAB Suite       : Registered in MATLAB Search Path"
fi
echo ""
echo "  HOW TO LAUNCH:"
echo "  1. Double-click or open index.html in any web browser."
if [ "$NODE_READY" -eq 1 ]; then
echo "  2. Backend Service : npm start (or node scripts/server.js)"
fi
if [ "$MATLAB_READY" -eq 1 ]; then
echo "  3. MATLAB Interface: matlab -r \"CALPHADHEACalc\""
fi
echo "============================================================================="
echo ""
