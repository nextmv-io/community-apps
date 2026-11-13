#!/usr/bin/env bash
# Fails if any of the given binaries requires a newer glibc than the Nextmv
# runtime image provides. Statically linked binaries pass trivially.
#
# Usage: check.sh <binary>... (override the limit with MAX_GLIBC=2.34)
set -euo pipefail

MAX_GLIBC=${MAX_GLIBC:-2.34}

if [[ $# -eq 0 ]]; then
    >&2 echo "usage: $0 <binary>..."
    exit 2
fi
if ! command -v objdump > /dev/null; then
    >&2 echo "❌ objdump not found (install binutils or llvm)"
    exit 2
fi

status=0
for bin in "$@"; do
    required=$(objdump -T "$bin" 2> /dev/null | grep -o 'GLIBC_[0-9][0-9.]*' | sed 's/GLIBC_//' | sort -Vu | tail -1 || true)
    if [[ -z "$required" ]]; then
        echo "✅ $bin: no glibc symbol versions (static or not linked against glibc)"
    elif [[ "$(printf '%s\n%s\n' "$required" "$MAX_GLIBC" | sort -V | tail -1)" == "$MAX_GLIBC" ]]; then
        echo "✅ $bin: requires glibc $required (<= $MAX_GLIBC)"
    else
        echo "❌ $bin: requires glibc $required (> $MAX_GLIBC)"
        status=1
    fi
done
exit $status
