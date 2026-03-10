#!/bin/bash

echo "=========================================="
echo "  ERP Mobile APK Builder (Ubuntu)"
echo "=========================================="
echo ""

# Check if we're on Ubuntu/Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script must run on Ubuntu/Linux"
    echo "   Please run this in your Ubuntu VM"
    exit 1
fi

echo "[1/4] Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    openjdk-11-jdk \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    cmake \
    libffi-dev \
    libssl-dev \
    zip \
    unzip

echo ""
echo "[2/4] Installing buildozer..."
pip3 install --upgrade pip
pip3 install buildozer==1.5.0 cython==0.29.33

echo ""
echo "[3/4] Building APK..."
echo "This will take 30-60 minutes on first build..."
echo ""

buildozer android debug

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ APK Built Successfully!"
    echo "=========================================="
    echo ""
    echo "APK Location:"
    ls -lh bin/*.apk
    echo ""
    echo "Copy APK to Windows:"
    echo "  The APK is in: $(pwd)/bin/"
    echo ""
    echo "Install on phone:"
    echo "  1. Copy APK to phone"
    echo "  2. Enable 'Unknown sources'"
    echo "  3. Install APK"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "  ❌ Build Failed!"
    echo "=========================================="
    echo ""
    echo "Check the errors above and try again."
    echo ""
fi
