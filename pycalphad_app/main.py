"""
main.py - Entry Point for PyCALPHAD Materials Engineering Suite
Launches the native C/C++ desktop suite (cpp/bin/PyCALPHAD_Suite.exe) or provides
headless CAE daemon execution if requested.
"""

import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if "--daemon" in sys.argv or "--server" in sys.argv:
        from pycalphad_app.server.cae_daemon import run_daemon
        run_daemon()
        return

    exe_path = os.path.join(BASE_DIR, "cpp", "bin", "PyCALPHAD_Suite.exe")
    if os.path.isfile(exe_path):
        subprocess.Popen([exe_path], cwd=BASE_DIR)
    else:
        print(f"[Error] Native executable not found at: {exe_path}")
        print("Please build the C/C++ suite using cpp/build.bat.")
        sys.exit(1)


if __name__ == "__main__":
    main()
