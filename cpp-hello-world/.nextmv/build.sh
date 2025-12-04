#!/bin/bash

set -euo pipefail

# Determine architecture
ARCH=${ARCH:-arm64}

# Build Linux binary using Docker
docker run --rm -v $(pwd):/workspace -w /workspace --platform linux/$ARCH ubuntu:22.04 bash -c "
  apt-get update && apt-get install -y build-essential cmake && \
  mkdir -p build/linux-$ARCH && cd build/linux-$ARCH && \
  cmake ../.. && make
"

# Copy main binary to app root (preparing for nextmv app packaging)
cp -v build/linux-$ARCH/stress_test main
