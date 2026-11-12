#!/usr/bin/env bash
set -euo pipefail

# Build standalone binaries with PyInstaller
# Usage: ./build.sh [version]
# Builds dist/gideon-{os}-{arch}/  (directory with binary + _internal/)
# Produces     dist/gideon-{os}-{arch}.tar.gz  (for distribution)
# Creates a convenience symlink at dist/gideon -> dist/gideon-{os}-{arch}/gideon

NAME="gideon"
TAG="${1:-}"

echo "Building $NAME${TAG:+ ($TAG)}..."

# Detect platform early so we can reference the existing build directory
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
esac

# Tag-preservation for the new onedir model: tarball the current build
if [[ -n "$TAG" ]]; then
    EXISTING_DIR="dist/${NAME}-${OS}-${ARCH}"
    if [[ -d "$EXISTING_DIR" ]]; then
        ARCHIVED="dist/${NAME}-${OS}-${ARCH}-${TAG}.tar.gz"
        (cd dist && tar -czf "$(basename "$ARCHIVED")" "$(basename "$EXISTING_DIR")")
        echo "Preserved existing build as $(basename "$ARCHIVED")"
    fi
fi

# Clean stale output from previous builds
rm -rf "dist/${NAME}" "dist/${NAME}-${OS}-${ARCH}" "dist/${NAME}-${OS}-${ARCH}.tar.gz"

pyinstaller \
    --onedir \
    --name "$NAME" \
    --distpath dist \
    --workpath build/pyinstaller \
    --specpath build \
    --clean \
    --noconfirm \
    src/gideon/main.py

# Rename directory with platform suffix
mv "dist/$NAME" "dist/${NAME}-${OS}-${ARCH}"

# Convenience symlink so you can run dist/gideon too
ln -sf "${NAME}-${OS}-${ARCH}/${NAME}" "dist/${NAME}"

# Package as a portable archive for distribution
(cd dist && tar -czf "${NAME}-${OS}-${ARCH}.tar.gz" "${NAME}-${OS}-${ARCH}")

echo ""
echo "Built:"
echo "  dist/${NAME}-${OS}-${ARCH}/"
echo "    └─ ${NAME}"
echo "    └─ _internal/"
echo "  dist/${NAME}  ->  ${NAME}-${OS}-${ARCH}/${NAME}  (symlink)"
echo "  dist/${NAME}-${OS}-${ARCH}.tar.gz"
echo "Done."