#!/usr/bin/env bash
# MODERN: TOOLING: build + grep for discarded-qualifiers
set -euo pipefail
: "${BUILD_LOG:=build.log}"
: "${BUILD_DIR:=build-hardened}"

rm -rf "$BUILD_DIR" >/dev/null 2>&1 || true
cmake -S .. -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Hardened >/dev/null 2>&1 || true
cmake --build "$BUILD_DIR" 2> "$BUILD_LOG" || true

echo "Remaining -Wdiscarded-qualifiers:"
grep -c 'discarded-qualifiers' "$BUILD_LOG" || true