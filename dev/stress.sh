#!/usr/bin/env bash
# restoHack - comprehensive memory stress harness with per-failure logs
set -Eeuo pipefail

### -------------------- knobs --------------------
BUILD_SAN_DIR="${BUILD_SAN_DIR:-build-sanitizers}"
BUILD_REL_DIR="${BUILD_REL_DIR:-build-release}"
GAME_BIN="./hack"

SAN_RUNS="${SAN_RUNS:-450}"        # short randomized ASan runs
SAN_MED_RUNS="${SAN_MED_RUNS:-60}" # medium randomized ASan runs
SHORT_STEPS="${SHORT_STEPS:-40}"
MED_STEPS="${MED_STEPS:-160}"
LONG_STEPS="${LONG_STEPS:-600}"

FORTIFY_RUNS="${FORTIFY_RUNS:-200}"

TTY_WRAPPER="${TTY_WRAPPER:-script}"  # "" to disable PTY wrapper
CORE_BACKTRACE="${CORE_BACKTRACE:-1}" # 1 = gdb bt on core

SAFE_KEYS="${SAFE_KEYS:-hjkl.Ls.,> ?}" # safe random keys
ALWAYS_PREFIX="${ALWAYS_PREFIX:-n\n}"  # start new game
NAME_PREFIX="${NAME_PREFIX:-Player}"   # name prefix

# log root (timestamped)
LOG_ROOT="${LOG_ROOT:-logs/$(date -u +%Y%m%d-%H%M%S)}"
mkdir -p "$LOG_ROOT"

### -------------------- tooling --------------------
need() { command -v "$1" >/dev/null 2>&1 || {
  echo "ERROR: missing '$1'"
  exit 1
}; }
maybe() { command -v "$1" >/dev/null 2>&1 && echo 1 || echo 0; }
banner() { printf "\n==== %s ====\n" "$*"; }
cc_id() { ${CC:-cc} --version 2>/dev/null | head -n1 || true; }

need cmake
[[ -n "$TTY_WRAPPER" ]] && need "$TTY_WRAPPER" || true

LLVM_SYMBOLIZER="$(command -v llvm-symbolizer || true)"
ASAN_OPTS="detect_stack_use_after_return=1:detect_leaks=1:abort_on_error=0:strict_string_checks=1:symbolize=1"
UBSAN_OPTS="print_stacktrace=1:report_error_type=1:halt_on_error=1"
GDB="$(command -v gdb || true)"
VALGRIND_PRESENT=$(maybe valgrind)
MS_PRINT="$(command -v ms_print || true)"
RADAMSA_PRESENT=$(maybe radamsa)
ZZUF_PRESENT=$(maybe zzuf)

[[ "$CORE_BACKTRACE" = 1 && -n "$GDB" ]] && ulimit -c unlimited || true

### -------------------- input generation --------------------
rand_keys() {
  local n="$1" out=""
  
  # Start with realistic game opening: n (new game), space, space
  out+="n "
  
  # Add some random movement (hjkl) - 5-6 moves
  local movement_keys="hjkl"
  local moves=$((5 + RANDOM % 2))  # 5 or 6 moves
  for _ in $(seq 1 "$moves"); do
    local move="${movement_keys:RANDOM%${#movement_keys}:1}"
    out+="$move"
  done
  
  # Add inventory command
  out+="i "
  
  # Add search
  out+="/"
  
  # Add some down movements
  out+="jj"
  
  # Add quit sequence
  out+="Qy"
  
  # Fill remaining steps with safe random keys if needed
  local remaining=$((n - ${#out}))
  if [[ $remaining -gt 0 ]]; then
    local safe_keys="hjkl.Ls ?"
    for _ in $(seq 1 "$remaining"); do
      local c="${safe_keys:RANDOM%${#safe_keys}:1}"
      out+="$c"
      [[ "$c" =~ [\.\?Ls] ]] && out+=$'\n'
    done
  fi
  
  printf "%s" "$out"
}

gen_script() {
  local name="$1" steps="$2"
  printf "%s%s%02d\n" "$ALWAYS_PREFIX" "$NAME_PREFIX" "$name"
  rand_keys "$steps"
  printf "q\ny\n\n"
}

### -------------------- logging runner --------------------
# Executes a run, captures all IO to a temp dir; on success, deletes it; on failure, moves to LOG_ROOT/suite-###/
run_with_logs() {
  local suite="$1" run_id="$2" build_dir="$3" stdin_data="$4"
  local exe="${build_dir}/${GAME_BIN}"
  local tmpdir
  tmpdir="$(mktemp -d)"
  local tagdir="${LOG_ROOT}/${suite}-$(printf "%03d" "$run_id")"
  mkdir -p "$tmpdir"

  printf '%s' "$stdin_data" >"${tmpdir}/stdin.txt"

  # save environment & command used
  {
    echo "suite=${suite}"
    echo "run_id=${run_id}"
    echo "build_dir=${build_dir}"
    echo "exe=${exe}"
    echo "date_utc=$(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "ASAN_OPTIONS=${ASAN_OPTIONS:-}"
    echo "UBSAN_OPTIONS=${UBSAN_OPTIONS:-}"
    echo "ASAN_SYMBOLIZER_PATH=${ASAN_SYMBOLIZER_PATH:-}"
    echo "CC=$(cc -v 2>&1 | tr '\n' ' ')"
  } >"${tmpdir}/env.txt"

  if [[ -n "$TTY_WRAPPER" ]]; then
    # typescript captures raw PTY stream too
    ${TTY_WRAPPER} -qfec "printf '%s' \"${stdin_data}\" | ${exe}" "${tmpdir}/typescript" \
      1>"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt"
  else
    printf '%s' "$stdin_data" | "${exe}" >"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt"
  fi
  local rc=$?

  if [[ $rc -ne 0 ]]; then
    mv "$tmpdir" "$tagdir"
    # collect any core dumps from build dir
    shopt -s nullglob
    for corefile in "${build_dir}"/core* core*; do
      [[ -e "$corefile" ]] || continue
      mv "$corefile" "$tagdir"/
      if [[ -n "$GDB" ]]; then
        "$GDB" -q -ex "set pagination off" -ex "thread apply all bt" -ex "quit" \
          --core="$tagdir/$(basename "$corefile")" "${exe}" >"${tagdir}/gdb_bt.txt" 2>&1 || true
      fi
    done
    echo "📄 failure logged: $tagdir"
  else
    rm -rf "$tmpdir"
  fi
  return $rc
}

### -------------------- build helpers --------------------
build_sanitizers() {
  banner "Building (ASan+UBSan)"
  rm -rf "$BUILD_SAN_DIR"
  local cflags="-g -O1 -fno-omit-frame-pointer -fno-optimize-sibling-calls -fsanitize=address,undefined"
  cmake -S . -B "$BUILD_SAN_DIR" \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_FLAGS="$cflags" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" >/dev/null
  cmake --build "$BUILD_SAN_DIR" -j >/dev/null
}

build_debug_plain() {
  rm -rf "$BUILD_SAN_DIR"
  cmake -S . -B "$BUILD_SAN_DIR" -DCMAKE_BUILD_TYPE=Debug >/dev/null
  cmake --build "$BUILD_SAN_DIR" -j >/dev/null
}

build_release_fortify() {
  banner "Building (Release + FORTIFY=3)"
  rm -rf "$BUILD_REL_DIR"
  cmake -S . -B "$BUILD_REL_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_FLAGS="-O2 -D_FORTIFY_SOURCE=3 -Wformat-security -Werror=format-security" >/dev/null
  cmake --build "$BUILD_REL_DIR" -j >/dev/null
}

### -------------------- suites --------------------
asan_soak() {
  local runs="$1" steps="$2" label="$3"
  banner "ASan/UBSan soak: $runs runs x $steps steps ($label)"
  local pass=0 fail=0
  for i in $(seq 1 "$runs"); do
    local input
    input="$(gen_script "$i" "$steps")"
    if ASAN_SYMBOLIZER_PATH="${LLVM_SYMBOLIZER}" \
      ASAN_OPTIONS="${ASAN_OPTS}" \
      UBSAN_OPTIONS="${UBSAN_OPTS}" \
      run_with_logs "$label" "$i" "$BUILD_SAN_DIR" "$input" >/dev/null 2>&1; then
      echo "✅ $label $i"
      ((pass++))
    else
      echo "❌ $label $i FAILED"
      ((fail++))
    fi
  done
  echo "__RESULT__ $label pass=$pass fail=$fail"
  [[ $fail -eq 0 ]]
}

asan_long_run() {
  banner "ASan/UBSan long randomized run ($LONG_STEPS steps)"
  local input
  input="$(gen_script 999 "$LONG_STEPS")"
  ASAN_SYMBOLIZER_PATH="${LLVM_SYMBOLIZER}" \
    ASAN_OPTIONS="${ASAN_OPTS}" \
    UBSAN_OPTIONS="${UBSAN_OPTS}" \
    run_with_logs "SAN-LONG" 1 "$BUILD_SAN_DIR" "$input"
}

valgrind_memcheck() {
  [[ "$VALGRIND_PRESENT" -eq 1 ]] || {
    echo "⚠️  Valgrind not found; skipping."
    return 0
  }
  banner "Valgrind memcheck (long randomized run)"
  build_debug_plain
  local input
  input="$(gen_script 777 "$LONG_STEPS")"

  local tmpdir
  tmpdir="$(mktemp -d)"
  printf '%s' "$input" >"${tmpdir}/stdin.txt"
  local exe="${BUILD_SAN_DIR}/${GAME_BIN}"

  if [[ -n "$TTY_WRAPPER" ]]; then
    ${TTY_WRAPPER} -qfec "printf '%s' \"${input}\" | valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes --error-exitcode=1 ${exe}" "${tmpdir}/typescript" \
      1>"${tmpdir}/stdout.txt" 2>"${tmpdir}/valgrind.log" || {
      local tag="${LOG_ROOT}/VALGRIND-001"
      mkdir -p "$tag"
      mv "$tmpdir"/* "$tag"/
      rmdir "$tmpdir"
      echo "📄 failure logged: $tag"
      return 1
    }
  else
    printf '%s' "$input" | valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes --error-exitcode=1 "$exe" \
      >"${tmpdir}/stdout.txt" 2>"${tmpdir}/valgrind.log" || {
      local tag="${LOG_ROOT}/VALGRIND-001"
      mkdir -p "$tag"
      mv "$tmpdir"/* "$tag"/
      rmdir "$tmpdir"
      echo "📄 failure logged: $tag"
      return 1
    }
  fi
  rm -rf "$tmpdir"
}

valgrind_massif() {
  [[ "$VALGRIND_PRESENT" -eq 1 && -n "$MS_PRINT" ]] || {
    echo "⚠️  Massif not available; skipping."
    return 0
  }
  banner "Valgrind Massif (heap growth profile)"
  local out="massif.out.restohack"
  local input
  input="$(gen_script 555 "$LONG_STEPS")"
  local tag="${LOG_ROOT}/MASSIF-001"
  mkdir -p "$tag"

  if [[ -n "$TTY_WRAPPER" ]]; then
    ${TTY_WRAPPER} -qfec "printf '%s' \"${input}\" | valgrind --tool=massif --time-unit=B --stacks=no --massif-out-file=${tag}/${out} ${BUILD_SAN_DIR}/${GAME_BIN}" /dev/null \
      1>"${tag}/stdout.txt" 2>"${tag}/stderr.txt" || true
  else
    printf '%s' "$input" | valgrind --tool=massif --time-unit=B --stacks=no --massif-out-file="${tag}/${out}" "${BUILD_SAN_DIR}/${GAME_BIN}" \
      >"${tag}/stdout.txt" 2>"${tag}/stderr.txt" || true
  fi
  ms_print "${tag}/${out}" >"${tag}/massif-report.txt" || true
}

fuzz_optional() {
  banner "Optional fuzzer pass"
  if [[ "$(maybe radamsa)" -eq 1 ]]; then
    local tagbase="${LOG_ROOT}/FUZZ-RADAMSA"
    mkdir -p "$tagbase"
    for i in $(seq 1 50); do
      local input
      input="$(gen_script $i $SHORT_STEPS | radamsa)"
      if ! run_with_logs "FUZZ-RADAMSA" "$i" "$BUILD_SAN_DIR" "$input" >/dev/null 2>&1; then
        : # per-run logs already captured
      fi
    done
  elif [[ "$(maybe zzuf)" -eq 1 ]]; then
    local tagbase="${LOG_ROOT}/FUZZ-ZZUF"
    mkdir -p "$tagbase"
    for i in $(seq 1 50); do
      local input
      input="$(gen_script $i $SHORT_STEPS)"
      # wrap manually to keep zzuf in the command stream
      local tmpdir
      tmpdir="$(mktemp -d)"
      printf '%s' "$input" >"${tmpdir}/stdin.txt"
      if [[ -n "$TTY_WRAPPER" ]]; then
        ${TTY_WRAPPER} -qfec "printf '%s' \"${input}\" | zzuf -r 0.01 -s $i -- ${BUILD_SAN_DIR}/${GAME_BIN}" "${tmpdir}/typescript" \
          1>"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt" || {
          local tag="${LOG_ROOT}/FUZZ-ZZUF-$(printf %03d "$i")"
          mkdir -p "$tag"
          mv "$tmpdir"/* "$tag"/
          rmdir "$tmpdir"
          echo "📄 failure logged: $tag"
        }
      else
        printf '%s' "$input" | zzuf -r 0.01 -s "$i" -- "${BUILD_SAN_DIR}/${GAME_BIN}" \
          >"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt" || {
          local tag="${LOG_ROOT}/FUZZ-ZZUF-$(printf %03d "$i")"
          mkdir -p "$tag"
          mv "$tmpdir"/* "$tag"/
          rmdir "$tmpdir"
          echo "📄 failure logged: $tag"
        }
      fi
      rm -rf "$tmpdir" || true
    done
  else
    echo "• no radamsa/zzuf; skipped."
  fi
}

fortify_release_stress() {
  banner "FORTIFY Release stress (${FORTIFY_RUNS} runs)"
  local pass=0 fail=0
  for i in $(seq 1 "$FORTIFY_RUNS"); do
    local input
    input="$(gen_script "$i" "$SHORT_STEPS")"
    if run_with_logs "FORTIFY" "$i" "$BUILD_REL_DIR" "$input" >/dev/null 2>&1; then
      echo "✅ FORTIFY $i"
      ((pass++))
    else
      echo "❌ FORTIFY $i FAILED"
      ((fail++))
    fi
  done
  echo "__RESULT__ FORTIFY pass=$pass fail=$fail"
  [[ $fail -eq 0 ]]
}

### -------------------- orchestration --------------------
main() {
  banner "Compiler: $(cc_id)"
  echo "Logs -> $LOG_ROOT"

  build_sanitizers
  asan_soak "$SAN_RUNS" "$SHORT_STEPS" "SAN-SHORT" || true
  asan_soak "$SAN_MED_RUNS" "$MED_STEPS" "SAN-MED" || true
  asan_long_run || {
    echo "ASan long run failed (see logs)"
  }

  # Valgrind (rebuild Debug without sanitizers)
  valgrind_memcheck || {
    echo "Valgrind memcheck failed (see logs)"
  }
  valgrind_massif

  build_release_fortify
  fortify_release_stress || {
    echo "FORTIFY stress failures (see logs)"
  }

  banner "DONE"
  echo "✔ Memory stress suites completed. Failures (if any) are in: $LOG_ROOT"
}

main "$@"
