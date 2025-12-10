#!/bin/bash

set -euo pipefail

# Determine architecture
ARCH=${ARCH:-arm64}

# Prepare Docker environment
DOCKER_NAME=rust-hello-world
docker rm -f $DOCKER_NAME || true

# Build the Docker image
docker buildx build -f .nextmv/Dockerfile -t $DOCKER_NAME --platform linux/$ARCH --load .

# Extract the compiled binary from the container
docker run --name $DOCKER_NAME --platform linux/arm64 $DOCKER_NAME
docker cp $DOCKER_NAME:/app/target/nextmv/release/rust-hello-world ./main
echo "🐰 Binary extracted to ./main"
docker rm $DOCKER_NAME
echo "🐰 Build completed successfully."
