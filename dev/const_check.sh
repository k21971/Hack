#!/usr/bin/env bash
# MODERN: TOOLING: helper script to track const-correctness progress

set -euo pipefail
: ${BUILD_LOG:=build.log}

# Build with warnings captured
make clean >/dev/null 2>&1 || true
make 2> "$BUILD_LOG" || true

echo "Top -Wdiscarded-qualifiers emitters:"
awk -F: '/discarded-qualifiers/ {print $1}' "$BUILD_LOG" | sed 's|.*/||' | sort | uniq -c | sort -nr | head

echo
echo "Callees still expecting writable char*:"
awk -F"'" '/expected .* but argument is of type/ {print $2}' "$BUILD_LOG" | sort | uniq -c | sort -nr | head