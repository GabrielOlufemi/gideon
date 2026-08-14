#!/usr/bin/env bash
set -euo pipefail

# Gideon installer & updater
# Usage: curl -fsSL https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.sh | sh
#        curl -fsSL https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.sh | sh -s v0.2.0

NAME="gideon"
REPO="GabrielOlufemi/gideon"
INSTALL_DIR="${GIDEON_INSTALL_DIR:-$HOME/.local/bin}"

# Default to latest release if no version specified
VERSION="${1:-latest}"

# Detect platform
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)   PLATFORM="linux" ;;
    darwin)  PLATFORM="darwin" ;;
    mingw*|msys*|cygwin*) PLATFORM="windows" ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

BINARY="${NAME}-${PLATFORM}-${ARCH}"
INSTALLED_BIN="${INSTALL_DIR}/${NAME}"
TEMP_BIN="${INSTALL_DIR}/.${NAME}.tmp"

# Fetch the latest release tag from GitHub if version is "latest"
if [ "$VERSION" = "latest" ]; then
    echo "Checking for latest release..."
    API_URL="https://api.github.com/repos/${REPO}/releases/latest"
    VERSION=$(curl -fsSL "$API_URL" | grep '"tag_name"' | sed 's/.*"tag_name": "\(.*\)",/\1/')

    if [ -z "$VERSION" ]; then
        echo "Could not determine latest version. Falling back to 'latest' tag."
        VERSION="latest"
    else
        echo "Latest version: $VERSION"
    fi
fi

# Check if already installed and compare versions
if [ -f "$INSTALLED_BIN" ]; then
    # Try to get the current version from the binary itself
    CURRENT_VERSION=$("$INSTALLED_BIN" --version 2>/dev/null || echo "")

    if [ -n "$CURRENT_VERSION" ] && [ "$VERSION" != "latest" ]; then
        if [ "$CURRENT_VERSION" = "$VERSION" ]; then
            echo "Already at version $VERSION. Nothing to do."
            exit 0
        fi
        echo "Updating $CURRENT_VERSION -> $VERSION..."
    else
        echo "Existing installation found. Updating..."
    fi
else
    echo "Installing $NAME..."
fi

# Construct download URL
if [ "$VERSION" = "latest" ]; then
    DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${BINARY}"
else
    DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${VERSION}/${BINARY}"
fi

mkdir -p "$INSTALL_DIR"

# Download to temp location so we don't clobber a running binary
echo "Downloading $BINARY..."
if command -v curl &>/dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o "$TEMP_BIN"
elif command -v wget &>/dev/null; then
    wget -q "$DOWNLOAD_URL" -O "$TEMP_BIN"
else
    echo "Need curl or wget to download"
    exit 1
fi

chmod +x "$TEMP_BIN"
mv "$TEMP_BIN" "$INSTALLED_BIN"

echo "Installed to $INSTALLED_BIN"

# Check if INSTALL_DIR is on PATH
case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *)
        echo ""
        echo "  $INSTALL_DIR is not on your PATH."
        echo "  Add it to your shell config:"
        echo ""
        echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
        echo ""
        ;;
esac

echo ""
echo "  $NAME installed/updated successfully."
echo "  Run 'gideon' to start."
echo ""