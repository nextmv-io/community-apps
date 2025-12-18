FROM rust:1-slim-trixie

# Build the app.
WORKDIR /app
COPY . .
RUN cargo build --release --target-dir target/nextmv
