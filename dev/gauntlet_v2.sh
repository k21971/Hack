#!/usr/bin/env bash
# restoHack test gauntlet (v2) — ASan, UBSan, MSan, and Valgrind lanes
# Safe defaults and consistent logging. Designed for clang toolchain.
set -euo pipefail
IFS=$'\n\t'

# ---------- config ----------
PROJECT_NAME="restoHack"
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="${ROOT_DIR}/gauntlet-logs/$(date +%Y%m%d-%H%M%S)"
BUILD_ASAN="${ROOT_DIR}/build-asan"
BUILD_UBSAN="${ROOT_DIR}/build-ubsan"
BUILD_MSAN="${ROOT_DIR}/build-msan"
BUILD_REL="${ROOT_DIR}/build-rel"

# If you have a custom stress script, point here
STRESS_SCRIPT="${ROOT_DIR}/scripts/stress.sh"  # optional; falls back to quick smoke if missing

# SECURITY NOTE: This script does not include fuzzing to avoid file creation issues

# Sanitizer knobs
export ASAN_OPTIONS="abort_on_error=1:strict_string_checks=1:detect_stack_use_after_return=1:check_initialization_order=1"
export UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
# Track origins gives better MSan diagnostics (2 is a good default). 
# Note: MSan requires instrumented libc; see README note emitted below.
# Set to non-aborting to capture logs from uninstrumented libraries
export MSAN_OPTIONS="halt_on_error=0:exit_code=0:report_umrs=1:poison_in_dtor=1:track_origins=2"

mkdir -p "${LOG_DIR}"

say() { printf "\033[1;36m[%s]\033[0m %s\n" "$1" "${2-}"; }
die() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$1"; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# ---------- helpers ----------
build_lane() {
  local lane="$1"; shift
  local bdir="$1"; shift
  local cflags="$1"; shift
  local toolchain="${2:-clang}"

  say "BUILD" "$lane -> $bdir"
  rm -rf "$bdir"
  cmake -S "${ROOT_DIR}" -B "$bdir" \
    -DCMAKE_BUILD_TYPE=Hardened \
    -DCMAKE_C_COMPILER="$toolchain" \
    -DCMAKE_C_FLAGS="$cflags" \
    | tee "${LOG_DIR}/${lane}_configure.log"

  cmake --build "$bdir" -j \
    | tee "${LOG_DIR}/${lane}_build.log"
}

run_game() {
  local bin="$1"
  local tag="$2"
  if [[ -x "$bin" ]]; then
    say "RUN" "$tag smoke"
    # quick smoke: start then immediate quit (stdin 'Q')
    ( echo "Q" | "$bin" -D ) | true
  else
    die "Binary not found or not executable: $bin"
  fi
}

run_stress() {
  local bin="$1"; local tag="$2"
  if [[ -f "$STRESS_SCRIPT" ]]; then
    say "STRESS" "$tag via $STRESS_SCRIPT"
    bash "$STRESS_SCRIPT" "$bin" | tee "${LOG_DIR}/${tag}_stress.log"
  else
    say "STRESS" "$tag (fallback quick loop x25)"
    for i in $(seq 1 25); do
      ( echo "Q" | "$bin" -D ) >/dev/null 2>&1 || die "$tag run $i failed"
    done
  fi
}

grep_warns() {
  local file="$1"; shift
  say "SCAN" "warnings in $(basename "$file")"
  if have rg; then
    rg -n "uninitialized|may be used uninitialized|strict-alias|aliasing|buffer|overflow|use-after-free" "$file" || true
  else
    grep -En "uninitialized|may be used uninitialized|strict-alias|aliasing|buffer|overflow|use-after-free" "$file" || true
  fi
}

note_msan_libc() {
  cat <<'EOF' | tee "${LOG_DIR}/MSAN_README.txt" >/dev/null
[MSan note]
MemorySanitizer requires instrumented libc (and other deps). If your distro toolchain
does not ship an msan-instrumented libc, you may see false positives or link errors.
Options:
  1) Use Clang's msan libc from compiler-rt (build from source).
  2) Run MSan only on units with no libc calls (limited but sometimes useful).
  3) Use ASan+UBSan for system-wide coverage and keep MSan as advisory.
EOF
}

# ---------- lanes ----------

# ASan lane (heap/stack, OOB, UAF)
build_lane "asan" "$BUILD_ASAN" "-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all"
run_game   "${BUILD_ASAN}/hack" "asan"
run_stress "${BUILD_ASAN}/hack" "asan"
grep_warns "${LOG_DIR}/asan_build.log"

# UBSan-focused lane (logic UB at O2)
build_lane "ubsan" "$BUILD_UBSAN" "-O2 -g -fsanitize=undefined -fno-omit-frame-pointer -fno-sanitize-recover=all -Wall -Wextra -Wshadow -Wuninitialized -Wconditional-uninitialized"
run_game   "${BUILD_UBSAN}/hack" "ubsan"
run_stress "${BUILD_UBSAN}/hack" "ubsan"
grep_warns "${LOG_DIR}/ubsan_build.log"

# MSan lane (uninitialized memory) — advisory if libc not instrumented
build_lane "msan" "$BUILD_MSAN" "-O1 -g -fsanitize=memory -fno-omit-frame-pointer -fno-sanitize-recover=all -fsanitize-memory-track-origins=2"
note_msan_libc
say "MSAN" "Non-aborting mode - will capture uninstrumented library issues to logs"
run_game   "${BUILD_MSAN}/hack" "msan" 2>&1 | tee "${LOG_DIR}/msan_game.log" || true
run_stress "${BUILD_MSAN}/hack" "msan" 2>&1 | tee "${LOG_DIR}/msan_stress.log" || true
grep_warns "${LOG_DIR}/msan_build.log"

# Valgrind (if available) on Hardened
build_lane "rel" "$BUILD_REL" "-O2 -g -fno-omit-frame-pointer -Wall -Wextra"
run_game   "${BUILD_REL}/hack" "rel"
run_stress "${BUILD_REL}/hack" "rel"

if have valgrind; then
  say "VALGRIND" "running memcheck quick pass"
  valgrind --error-exitcode=99 --leak-check=full --show-leak-kinds=all \
           --quiet --track-origins=yes "${BUILD_REL}/hack" -D < <(echo "Q") \
           2> "${LOG_DIR}/valgrind_memcheck.log" || true
  say "SCAN" "valgrind findings"
  grep -nE "ERROR SUMMARY|Invalid|definitely lost|indirectly lost|uninitialised" "${LOG_DIR}/valgrind_memcheck.log" || true
else
  say "VALGRIND" "not found; skipping"
fi

say "DONE" "Logs in ${LOG_DIR}"
