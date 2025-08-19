#!/usr/bin/env bash
# Replay a failing run captured by stress_mem.sh
# Usage: ./repro.sh logs/20250818-011527/SAN-LONG-001

set -euo pipefail
run_dir="${1:?path to failing run dir}"
exe="$(grep '^exe=' "$run_dir/env.txt" | cut -d= -f2)"
[[ -x "$exe" ]] || {
  echo "No exe at $exe"
  exit 1
}

ASAN_SYMBOLIZER_PATH="$(command -v llvm-symbolizer || true)"
export ASAN_SYMBOLIZER_PATH

# Use the same strict opts we used in the harness + more detail for triage
export ASAN_OPTIONS="detect_stack_use_after_return=1:detect_leaks=1:strict_string_checks=1:halt_on_error=1:symbolize=1:fast_unwind_on_malloc=0:allocator_may_return_null=0:print_full_thread_history=1:detect_container_overflow=1:alloc_dealloc_mismatch=1"
export UBSAN_OPTIONS="print_stacktrace=1:report_error_type=1:halt_on_error=1"

# Show crash in the terminal with colors and symbols
cat "$run_dir/stdin.txt" | "$exe"
