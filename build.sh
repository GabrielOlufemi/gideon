#!/usr/bin/env bash
set -euo pipefail

# Build standalone binaries with PyInstaller
# Usage: ./build.sh [version]
# Produces dist/gideon-{os}-{arch}[-{tag}] for the current platform
# If a version tag is given, the old binary is preserved under that tag.

NAME="gideon"
TAG="${1:-}"

echo "Building $NAME${TAG:+ ($TAG)}..."

# If a tag is provided, copy the current binary before building
if [[ -n "$TAG" ]]; then
    EXISTING="dist/${NAME}"
    # Check for the platform-renamed version too
    OS_TEMP="$(uname -s | tr '[:upper:]' '[:lower:]')"
    ARCH_TEMP="$(uname -m)"
    [[ "$ARCH_TEMP" == "x86_64" ]] && ARCH_TEMP="x86_64"
    [[ "$ARCH_TEMP" == "aarch64" || "$ARCH_TEMP" == "arm64" ]] && ARCH_TEMP="arm64"
    RENAMED="dist/${NAME}-${OS_TEMP}-${ARCH_TEMP}"

    if [[ -f "$RENAMED" ]]; then
        cp "$RENAMED" "dist/${NAME}-${OS_TEMP}-${ARCH_TEMP}-${TAG}"
        echo "Preserved existing binary as ${NAME}-${OS_TEMP}-${ARCH_TEMP}-${TAG}"
    elif [[ -f "$EXISTING" ]]; then
        cp "$EXISTING" "dist/${NAME}-${OS_TEMP}-${ARCH_TEMP}-${TAG}"
        echo "Preserved existing binary as ${NAME}-${OS_TEMP}-${ARCH_TEMP}-${TAG}"
    fi
fi

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

FINAL="dist/${NAME}-${OS}-${ARCH}"
mv "dist/$NAME" "$FINAL"
echo "Built $FINAL"
echo "Done."