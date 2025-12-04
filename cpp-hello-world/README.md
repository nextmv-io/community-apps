# C++ compute/memory load simulation app

This is a simple C++ application that simulates compute and memory load.

## Remote usage

### Pre-requisites (remotely)

- Docker

### Usage (remotely)

```bash
# Configure aarch64 or amd64 build in app.yaml
nextmv app push -a <app-id>
echo '{"hello":"memory"}' | nextmv app run -a <app-id> --tail
```

## Local usage

If interested in using locally or cross-compiling manually, see below.

### Pre-requisites (locally, Linux host)

- C++ compiler (e.g., g++)
- CMake
- Make
- Cross-compilation tools, e.g.:
  - Arch: `sudo pacman -S aarch64-linux-gnu-gcc`
  - Ubuntu: `sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu`

### Usage (locally, Linux host)

Locally (see Linux builds below for building):

```bash
echo '{"hello":"memory"}' | ./stress_test -memory=1000 -threads=10 -duration=10
```

### Build

Local build (Linux host):

```bash
mkdir -p build/amd64 && cd build/amd64
cmake ../..
make
```

Cross-compile for aarch64 (Linux host):

```bash
mkdir -p build/aarch64 && cd build/aarch64
cmake -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ ../..
make
```
