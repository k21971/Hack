#!/bin/bash
# 
# restoHack Hardened Build Script
# Clean rebuilds with hardening flags for security-focused testing
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build-hardened"

echo "🛡️  restoHack Hardened Build"
echo "=============================="
echo "Project root: $PROJECT_ROOT"
echo "Build dir: $BUILD_DIR"
echo

# Clean previous build
if [[ -d "$BUILD_DIR" ]]; then
    echo "🧹 Cleaning previous hardened build..."
    rm -rf "$BUILD_DIR"
fi

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "🔧 Configuring hardened build..."
cmake \
    -S "$PROJECT_ROOT" \
    -B . \
    -DCMAKE_BUILD_TYPE=Hardened \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DENABLE_STRUCT_PACKING=ON \
    -DENABLE_SAVE_VALIDATION=ON \
    -G "Unix Makefiles"

echo
echo "🔨 Building with hardening flags..."
echo "   - PIE (Position Independent Executable)"
echo "   - RELRO + BIND_NOW (immediate symbol resolution)"
echo "   - Stack protection + clash protection"
echo "   - FORTIFY_SOURCE=3 (if supported, fallback to =2)"
echo "   - NX bit (non-executable stack)"
echo

cmake --build . --parallel "$(nproc)"

echo
echo "✅ Hardened build complete!"
echo
echo "🔍 Security flags verification:"
echo "==============================="

# Verify hardening flags are applied
if command -v checksec >/dev/null 2>&1; then
    checksec --file="./hack"
elif command -v hardening-check >/dev/null 2>&1; then
    hardening-check ./hack
else
    echo "ℹ️  Install 'checksec' or 'hardening-check' to verify hardening flags"
    echo "   Checking with readelf instead:"
    echo
    echo "🔹 PIE/PIC status:"
    file ./hack | grep -i pie || echo "   (not explicitly shown as PIE)"
    
    echo "🔹 Dynamic section (RELRO/BIND_NOW):"
    readelf -d ./hack 2>/dev/null | grep -E "(BIND_NOW|FLAGS)" || echo "   (no BIND_NOW/FLAGS entries)"
    
    echo "🔹 GNU_STACK (NX bit):"
    readelf -l ./hack 2>/dev/null | grep -A1 GNU_STACK || echo "   (no GNU_STACK segment)"
fi

echo
echo "🎮 Run the hardened build:"
echo "   cd $BUILD_DIR && ./hack"
echo
echo "📊 For performance profiling:"
echo "   perf record -g ./hack"
echo "   perf report"
echo
echo "🐛 For debugging with symbols:"
echo "   gdb ./hack"
echo "   (gdb) set environment HACKDIR=$BUILD_DIR/hackdir"