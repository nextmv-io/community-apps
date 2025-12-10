FROM rust:1-slim-trixie

# Install necessary dependencies.
RUN apt update && apt install -y build-essential cmake libclang-dev

# Build the app.
WORKDIR /app
COPY . .
RUN cargo build --release --target-dir target/nextmv
