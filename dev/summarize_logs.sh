#!/usr/bin/env bash
# Summarize all failures under a logs/… folder:
# - shows suite/run
# - extracts ASan/UBSan error header
# - shows the top non-lib frame (file:line) when present
#
# Usage: ./summarize_logs.sh logs/20250818-011527

set -Eeuo pipefail
root="${1:-logs}"

shopt -s nullglob
for d in $(find "$root" -maxdepth 2 -mindepth 2 -type d -name '*-[0-9][0-9][0-9]'); do
  suite="$(basename "$d")"
  err="$(grep -m1 -E '==[0-9]+==ERROR: (AddressSanitizer|UndefinedBehaviorSanitizer):' "$d"/stderr.txt 2>/dev/null || true)"
  [[ -z "$err" ]] && err="$(grep -m1 -E 'SUMMARY: AddressSanitizer' "$d"/stderr.txt 2>/dev/null || true)"
  top="$(grep -m1 -E ' at .*:( [0-9]+)?$|\.c:[0-9]+|\.cc:[0-9]+|\.cpp:[0-9]+' "$d"/stderr.txt 2>/dev/null || true)"
  # Prefer frames from your source tree, not system libs
  top_local="$(grep -m1 -E '/src/.*\.(c|cc|cpp):[0-9]+' "$d"/stderr.txt 2>/dev/null || true)"
  [[ -n "$top_local" ]] && top="$top_local"
  echo "• $suite"
  [[ -n "$err" ]] && echo "  $err"
  [[ -n "$top" ]] && echo "  ↳ $top"
done | sed 's/\x1b\[[0-9;]*m//g'
