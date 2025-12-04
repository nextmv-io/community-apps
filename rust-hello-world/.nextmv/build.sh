#!/bin/bash

set -euo pipefail

# Determine architecture
ARCH=${ARCH:-arm64}

# Build Linux binary using Docker
docker run --rm -v $(pwd):/workspace -w /workspace --platform linux/$ARCH rust:1 bash -c "
  cargo build --release --target-dir target/nextmv
"

# Copy main binary to app root (preparing for nextmv app packaging)
cp -v target/nextmv/release/rust-echo main
