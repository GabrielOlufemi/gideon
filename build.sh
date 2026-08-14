#!/usr/bin/env bash
set -euo pipefail

# Build standalone binaries with PyInstaller
# Usage: ./build.sh [version]
# Produces dist/gideon-{os}-{arch} for the current platform

NAME="gideon"
VERSION="${1:-dev}"

echo "Building $NAME v$VERSION..."

pyinstaller \
    --onefile \
    --name "$NAME" \
    --distpath dist \
    --workpath build/pyinstaller \
    --specpath build \
    --clean \
    --noconfirm \
    src/gideon/main.py

# Rename with platform suffix
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
esac

mv "dist/$NAME" "dist/${NAME}-${OS}-${ARCH}"
echo "Built dist/${NAME}-${OS}-${ARCH}"
echo "Done."