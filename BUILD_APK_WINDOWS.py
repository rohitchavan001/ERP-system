"""
Simple APK Builder for Windows
Builds APK using python-for-android without needing Linux
"""

import os
import sys
import subprocess
import zipfile
import urllib.request

print("=" * 60)
print("  ERP Mobile APK Builder for Windows")
print("=" * 60)
print()

# Check Python version
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required")
    sys.exit(1)

print("✓ Python version OK")

# Install required packages
print("\n[1/3] Installing dependencies...")
packages = ["python-for-android", "cython"]
for pkg in packages:
    subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)

print("\n[2/3] Preparing build...")
os.chdir("mobile")

# Create simple build script
build_script = """
from pythonforandroid.toolchain import main
import sys

sys.argv = [
    'p4a',
    'apk',
    '--private', '.',
    '--package', 'com.erpsystem.erpmobile',
    '--name', 'ERPMobile',
    '--version', '2.1',
    '--bootstrap', 'sdl2',
    '--requirements', 'python3,kivy,kivymd,pillow,python-dateutil,qrcode,requests',
    '--permission', 'INTERNET',
    '--permission', 'WRITE_EXTERNAL_STORAGE',
    '--orientation', 'portrait',
    '--arch', 'armeabi-v7a',
    '--debug'
]

main()
"""

with open("build_apk.py", "w") as f:
    f.write(build_script)

print("\n[3/3] Building APK...")
print("This will take 30-60 minutes...")
print()

try:
    subprocess.run([sys.executable, "build_apk.py"], check=True)
    print("\n" + "=" * 60)
    print("  ✅ APK Built Successfully!")
    print("=" * 60)
    print("\nAPK Location: mobile/dist/")
    print("\nInstall on phone:")
    print("  1. Copy APK to phone")
    print("  2. Enable 'Unknown sources'")
    print("  3. Install APK")
except Exception as e:
    print(f"\n❌ Build failed: {e}")
    print("\nThis method requires:")
    print("  - Android SDK")
    print("  - Android NDK")
    print("  - Complex setup on Windows")
    print("\nRecommended: Use GitHub Actions instead")
    print("  Go to: https://github.com/rohitchavan001/ERP-system/actions")
