#!/bin/bash

set -euo pipefail

# Determine architecture
ARCH=${ARCH:-arm64}

# Prepare Docker environment
DOCKER_NAME=cs-sardinecan-packing-builder
docker rm -f $DOCKER_NAME || true

# Build the Docker image
docker buildx build -f .nextmv/Dockerfile -t $DOCKER_NAME --load --build-arg ARCH=$ARCH .

# Extract the compiled binary from the container
docker run --name $DOCKER_NAME $DOCKER_NAME
docker cp $DOCKER_NAME:/app/bin/Release/net8.0/linux-$ARCH/publish/cs-sardinecan-packing ./main
echo "🐰 Binary extracted to ./main"
docker rm $DOCKER_NAME
echo "🐰 Build completed successfully."
