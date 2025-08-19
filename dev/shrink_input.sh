#!/usr/bin/env bash
# Delta-debug the stdin of a failing run.
# Usage: ./shrink_input.sh logs/…/SAN-LONG-001  [optional: max_iters]
set -Eeuo pipefail
run_dir="${1:?run dir}"
max="${2:-200}"
exe="$(grep '^exe=' "$run_dir/env.txt" | cut -d= -f2)"
[[ -x "$exe" ]] || {
  echo "No exe at $exe"
  exit 1
}

ASAN_SYMBOLIZER_PATH="$(command -v llvm-symbolizer || true)"
export ASAN_SYMBOLIZER_PATH
export ASAN_OPTIONS="detect_stack_use_after_return=1:detect_leaks=1:strict_string_checks=1:halt_on_error=1:symbolize=1:fast_unwind_on_malloc=0"
export UBSAN_OPTIONS="print_stacktrace=1:report_error_type=1:halt_on_error=1"

work="$run_dir/shrink.stdin"
cp "$run_dir/stdin.txt" "$work"

crashes() {
  cat "$work" | "$exe" >/dev/null 2>&1
  return $?
}

if crashes; then
  sz=$(wc -c <"$work")
  echo "Starting size: $sz bytes"
else
  echo "Not crashing as-is; aborting."
  exit 1
fi

iter=0
while ((iter < max)); do
  ((iter++))
  sz=$(wc -c <"$work")
  ((sz < 8)) && break
  # remove a middle chunk
  start=$((sz / 4))
  len=$((sz / 4))
  tmp="$work.tmp"
  (
    head -c "$start" "$work"
    tail -c +$((start + len + 1)) "$work"
  ) >"$tmp"
  mv "$tmp" "$work" || true
  if crashes; then
    echo "Iter $iter: reduced to $(wc -c <"$work") bytes (still crashes)"
  else
    # revert & try smaller deletion
    cp "$run_dir/stdin.txt" "$work"
    echo "Iter $iter: deletion lost crash; stopping."
    break
  fi
done

echo "Reduced stdin at: $work"
