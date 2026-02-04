#!/bin/bash
# Build script for EasyHID .deb package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building EasyHID .deb package..."
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf debian/easyhid
rm -rf dist
mkdir -p dist

# Build the package
echo "Building package..."
dpkg-buildpackage -b -uc -us

# Move the .deb to dist/
echo ""
echo "Moving package to dist/..."
mv ../easyhid_*.deb dist/ 2>/dev/null || true
mv ../easyhid_*.changes dist/ 2>/dev/null || true
mv ../easyhid_*.buildinfo dist/ 2>/dev/null || true

# Clean up build artifacts
echo "Cleaning up build artifacts..."
rm -rf debian/easyhid
rm -rf debian/files
rm -rf debian/.debhelper

# Find the .deb file
DEB_FILE=$(ls -1 dist/easyhid_*.deb 2>/dev/null | head -1)

if [ -n "$DEB_FILE" ]; then
    echo ""
    echo "=========================================="
    echo "Build successful!"
    echo "=========================================="
    echo ""
    echo "Package: $DEB_FILE"
    echo ""
    echo "To install, run:"
    echo "  sudo apt install ./$DEB_FILE"
    echo ""
else
    echo ""
    echo "Error: .deb file not found in dist/"
    exit 1
fi
