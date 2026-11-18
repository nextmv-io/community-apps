# Build on Amazon Linux 2023 (glibc 2.34), the same base as the Nextmv runtime
# image, so the binary does not require a newer glibc than the runtime has.
FROM amazonlinux:2023

# Install necessary dependencies.
RUN dnf install -y rust cargo gcc gcc-c++ cmake clang-devel && dnf clean all

# Build the app.
WORKDIR /app
COPY . .
RUN cargo build --release --target-dir target/nextmv
