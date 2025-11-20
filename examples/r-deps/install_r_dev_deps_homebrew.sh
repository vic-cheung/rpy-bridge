#!/bin/bash
set -e

echo "Installing system dependencies for R packages via Homebrew..."

# Check if Homebrew is installed
if ! command -v brew &>/dev/null; then
    echo "Homebrew is not installed. Install it then rerun this script."
    exit 1
fi

brew update

# Verify R installation
if ! command -v R &>/dev/null; then
    echo "R installation failed or R is not in your PATH."
    exit 1
fi

# Install common R build dependencies
brew install \
    pkg-config \
    freetype \
    harfbuzz \
    fribidi \
    libtiff \
    libjpeg \
    cairo \
    glib \
    fontconfig \
    cmake \
    pandoc \
    librsvg \
    python \
    homebrew/cask/basictex

# Update PATH for Homebrew-installed tools (optional, for new shells)
eval "$(/usr/libexec/path_helper)"

echo "All required system libraries and R have been installed."
echo "If you still see errors about missing R libraries (like libRblas.dylib), try restarting your terminal or your R session."
