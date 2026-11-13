# glibc compatibility check

The Nextmv runtime image (`ghcr.io/nextmv-io/runtime/default`) is based on
Amazon Linux 2023, which ships glibc 2.34. A dynamically linked binary that was
built against a newer glibc fails to start there with an error like
``version `GLIBC_2.38' not found``.

This script checks the glibc symbol versions a binary requires and fails if any
of them is newer than 2.34. Statically linked binaries (e.g. Go with
`CGO_ENABLED=0`, or musl builds) pass.

## Usage

Build the app first (e.g. `bash .nextmv/build.sh` in the app directory), then:

```bash
bash .nextmv/glibc-check/check.sh rust-goodlp-knapsack/main
```

Set `MAX_GLIBC` to check against a different limit. Requires `objdump` (GNU
binutils or LLVM).
