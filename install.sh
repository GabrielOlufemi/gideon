#!/usr/bin/env bash
set -euo pipefail

# Gideon installer
# Usage: curl -fsSL https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.sh | sh

NAME="gideon"
REPO="GabrielOlufemi/gideon"
INSTALL_DIR="${GIDEON_INSTALL_DIR:-$HOME/.local/bin}"

# Detect platform
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)   PLATFORM="linux" ;;
    darwin)  PLATFORM="darwin" ;;
    mingw*|msys*|cygwin*) PLATFORM="windows" ;;
    *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

BINARY="${NAME}-${PLATFORM}-${ARCH}"
DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${BINARY}"

mkdir -p "$INSTALL_DIR"

echo "Downloading $NAME for $PLATFORM/$ARCH..."
if command -v curl &>/dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o "$INSTALL_DIR/$NAME"
elif command -v wget &>/dev/null; then
    wget -q "$DOWNLOAD_URL" -O "$INSTALL_DIR/$NAME"
else
    echo "Need curl or wget to download"
    exit 1
fi

chmod +x "$INSTALL_DIR/$NAME"
echo "Installed to $INSTALL_DIR/$NAME"

# Check if INSTALL_DIR is on PATH, and add it automatically if not
case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        ;;
    *)
        SHELL_CONFIG=""
        case "$SHELL" in
            */zsh) SHELL_CONFIG="$HOME/.zshrc" ;;
            */bash)
                [ "$OS" = "darwin" ] && SHELL_CONFIG="$HOME/.bash_profile" || SHELL_CONFIG="$HOME/.bashrc"
                ;;
        esac

        if [ -n "$SHELL_CONFIG" ] && [ -f "$SHELL_CONFIG" ]; then
            echo "Adding $INSTALL_DIR to PATH in $SHELL_CONFIG..."
            echo "" >> "$SHELL_CONFIG"
            echo "# Added by gideon installer" >> "$SHELL_CONFIG"
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_CONFIG"
            export PATH="$PATH:$INSTALL_DIR"
            echo "Restart your terminal or run 'source $SHELL_CONFIG' to pick up the change."
        else
            # Fallback: tell the user
            echo ""
            echo "  $INSTALL_DIR is not on your PATH."
            echo "  Add it to your shell config:"
            echo ""
            echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
            echo ""
        fi
        ;;
esac

echo ""
echo "  Done. Run 'gideon' to start."