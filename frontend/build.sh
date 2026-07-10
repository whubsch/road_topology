#!/usr/bin/env bash
# Compiles input.css into a purged, production-ready style.css using the
# standalone Tailwind CSS CLI (no Node.js/npm required).
set -euo pipefail

cd "$(dirname "$0")"

TAILWIND_VERSION="v4.3.2"

# Map the local platform/arch to the matching standalone release asset.
os="$(uname -s)"
arch="$(uname -m)"

case "$os" in
  Linux)
    case "$arch" in
      x86_64) asset="tailwindcss-linux-x64" ;;
      aarch64|arm64) asset="tailwindcss-linux-arm64" ;;
      *) echo "Unsupported Linux architecture: $arch" >&2; exit 1 ;;
    esac
    ;;
  Darwin)
    case "$arch" in
      x86_64) asset="tailwindcss-macos-x64" ;;
      arm64) asset="tailwindcss-macos-arm64" ;;
      *) echo "Unsupported macOS architecture: $arch" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "Unsupported OS: $os (see https://github.com/tailwindlabs/tailwindcss/releases for other platforms)" >&2
    exit 1
    ;;
esac

bin="./.tailwindcss-cli"

if [ ! -x "$bin" ]; then
  echo "Downloading Tailwind CLI ($TAILWIND_VERSION, $asset)..."
  curl -sL -o "$bin" \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/${asset}"
  chmod +x "$bin"
fi

echo "Building style.css..."
"$bin" -i input.css -o style.css --minify

echo "Done."
