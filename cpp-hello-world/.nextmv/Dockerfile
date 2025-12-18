FROM ubuntu:22.04

# Install necessary dependencies.
RUN apt update && apt install -y build-essential cmake

# Build the app.
WORKDIR /app
COPY . .
RUN mkdir -p build/linux && cd build/linux && \
    cmake ../.. && \
    make
