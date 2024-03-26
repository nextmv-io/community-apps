#!/usr/bin/env bash

set -e

# Get architecture
ARCH=$(uname -m)

# Install dependencies
apt update
apt install -y \
    curl \
    tar \
    xz-utils

# Install zig depending on ARCH
if [ "$ARCH" == "x86_64" ]; then
    curl -sSfL https://ziglang.org/download/0.11.0/zig-linux-x86_64-0.11.0.tar.xz | tar -xJf - -C /usr/local
    ln -s /usr/local/zig-linux-x86_64-0.11.0/zig /usr/bin/zig
elif [ "$ARCH" == "aarch64" ]; then
    curl -sSfL https://ziglang.org/download/0.11.0/zig-linux-aarch64-0.11.0.tar.xz | tar -xJf - -C /usr/local
    ln -s /usr/local/zig-linux-aarch64-0.11.0/zig /usr/bin/zig
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi
