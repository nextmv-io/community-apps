#!/bin/bash

set -euo pipefail

# Determine architecture
ARCH=${ARCH:-arm64}

# Prepare Docker environment
DOCKER_NAME=cpp-hello-world-builder
docker rm -f $DOCKER_NAME || true

# Build the Docker image
docker buildx build -f .nextmv/Dockerfile -t $DOCKER_NAME --platform linux/$ARCH --load .

# Extract the compiled binary from the container
docker run --name $DOCKER_NAME --platform linux/$ARCH $DOCKER_NAME
docker cp $DOCKER_NAME:/app/build/linux/stress_test ./main
echo "🐰 Binary extracted to ./main"
docker rm $DOCKER_NAME
echo "🐰 Build completed successfully."
