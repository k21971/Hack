#!/usr/bin/env bash
# restoHack ABSOLUTE GAUNTLET - Comprehensive stress testing harness
# Built for testing security fixes before HardFought.org deployment
set -Eeuo pipefail

### -------------------- CONFIGURATION --------------------
BUILD_SAN_DIR="${BUILD_SAN_DIR:-build-sanitizers}"
BUILD_REL_DIR="${BUILD_REL_DIR:-build-release}"
BUILD_HARDENED_DIR="${BUILD_HARDENED_DIR:-build-hardened}"
BUILD_DEBUG_DIR="${BUILD_DEBUG_DIR:-build-debug}"
BUILD_TSAN_DIR="${BUILD_TSAN_DIR:-build-tsan}"
BUILD_MSAN_DIR="${BUILD_MSAN_DIR:-build-msan}"
GAME_BIN="./hack"

# GAUNTLET MODE: More aggressive than stress.sh
GAUNTLET_SHORT_RUNS="${GAUNTLET_SHORT_RUNS:-1000}"     # 1000 short runs
GAUNTLET_MED_RUNS="${GAUNTLET_MED_RUNS:-200}"          # 200 medium runs  
GAUNTLET_LONG_RUNS="${GAUNTLET_LONG_RUNS:-50}"         # 50 long runs
GAUNTLET_EXTREME_RUNS="${GAUNTLET_EXTREME_RUNS:-10}"   # 10 extreme runs

SHORT_STEPS="${SHORT_STEPS:-40}"
MED_STEPS="${MED_STEPS:-160}"
LONG_STEPS="${LONG_STEPS:-600}"
EXTREME_STEPS="${EXTREME_STEPS:-2000}"

FORTIFY_RUNS="${FORTIFY_RUNS:-500}"
FUZZ_RUNS="${FUZZ_RUNS:-200}"

TTY_WRAPPER="${TTY_WRAPPER:-script}"
CORE_BACKTRACE="${CORE_BACKTRACE:-1}"

# Chaos testing parameters
CHAOS_SIGNAL_TESTS="${CHAOS_SIGNAL_TESTS:-100}"
STRESS_CPU_CORES="${STRESS_CPU_CORES:-$(nproc)}"
MEMORY_PRESSURE_MB="${MEMORY_PRESSURE_MB:-1024}"

# Log root (timestamped)
LOG_ROOT="${LOG_ROOT:-gauntlet-logs/$(date -u +%Y%m%d-%H%M%S)}"
mkdir -p "$LOG_ROOT"

### -------------------- TOOL DETECTION --------------------
need() { command -v "$1" >/dev/null 2>&1 || {
  echo "ERROR: missing '$1'"
  exit 1
}; }
maybe() { command -v "$1" >/dev/null 2>&1 && echo 1 || echo 0; }
banner() { printf "\n🔥 ==== %s ====\n" "$*"; }
gauntlet_log() { echo "🎯 GAUNTLET: $*" | tee -a "$LOG_ROOT/gauntlet.log"; }
cc_id() { ${CC:-cc} --version 2>/dev/null | head -n1 || true; }

need cmake
[[ -n "$TTY_WRAPPER" ]] && need "$TTY_WRAPPER" || true

# Advanced tooling detection
LLVM_SYMBOLIZER="$(command -v llvm-symbolizer || true)"
VALGRIND_PRESENT=$(maybe valgrind)
GDB_PRESENT=$(maybe gdb)
PERF_PRESENT=$(maybe perf)
STRACE_PRESENT=$(maybe strace)
STRESS_PRESENT=$(maybe stress-ng)
RADAMSA_PRESENT=$(maybe radamsa)
ZZUF_PRESENT=$(maybe zzuf)
AFL_PRESENT=$(maybe afl-fuzz)
RR_PRESENT=$(maybe rr)

# Sanitizer configurations
ASAN_OPTS="detect_stack_use_after_return=1:detect_leaks=1:abort_on_error=0:strict_string_checks=1:symbolize=1:check_initialization_order=1:strict_init_order=1:detect_invalid_pointer_pairs=1"
UBSAN_OPTS="print_stacktrace=1:report_error_type=1:halt_on_error=1:print_module_map=1"
TSAN_OPTS="detect_thread_leaks=1:report_bugs=1:history_size=7:symbolize=1"
MSAN_OPTS="print_stats=1:symbolize=1:abort_on_error=0:exit_code=0"

[[ "$CORE_BACKTRACE" = 1 && -n "$(command -v gdb)" ]] && ulimit -c unlimited || true

### -------------------- ENHANCED INPUT GENERATION --------------------
# More aggressive input generation
rand_keys_chaos() {
  local n="$1" out=""
  
  # Realistic game start
  out+="n "
  
  # Random movement with occasional dangerous commands
  local all_keys="hjklyubn.>< ?siI#qQ"
  local dangerous_keys="Q#"
  
  for i in $(seq 1 "$n"); do
    if [[ $((RANDOM % 20)) -eq 0 ]]; then
      # 5% chance of dangerous key
      local key="${dangerous_keys:RANDOM%${#dangerous_keys}:1}"
      out+="$key"
      [[ "$key" == "Q" ]] && out+="n" # Cancel quit
    else
      # Regular key
      local key="${all_keys:RANDOM%${#all_keys}:1}"
      out+="$key"
    fi
    
    # Occasional newlines for commands that need them
    [[ $((RANDOM % 10)) -eq 0 ]] && out+=$'\n'
  done
  
  # Proper quit sequence
  out+="Qy"
  printf "%s" "$out"
}

# Generate malformed input (SAFE VERSION)
gen_malformed_input() {
  local steps="$1"
  # Mix of valid and invalid sequences (SAFE: no null bytes)
  printf "n\nPlayer\n"
  printf "\x01\x02\x7F"      # SAFE: Control chars but no null bytes
  rand_keys_chaos "$steps"
  printf "\x1b\x1b\x1b"      # Escape sequences (safe)
  printf "Qy\n"
}

# Generate ultra-long input
gen_extreme_input() {
  local steps="$1"
  printf "n\nPlayer\n"
  
  # Flood with specific command patterns
  for i in $(seq 1 "$((steps/4))"); do
    printf "hjkl"
  done
  
  # Memory stress patterns
  for i in $(seq 1 100); do
    printf "i " # Inventory spam
  done
  
  # Search spam
  for i in $(seq 1 50); do
    printf "s "
  done
  
  printf "Qy\n"
}

gen_script_enhanced() {
  local name="$1" steps="$2" mode="${3:-normal}"
  printf "Player%02d\n" "$name"
  
  case "$mode" in
    chaos)    rand_keys_chaos "$steps" ;;
    malformed) gen_malformed_input "$steps" ;;
    extreme)  gen_extreme_input "$steps" ;;
    *)        rand_keys_chaos "$steps" ;;  # Default to chaos
  esac
  
  printf "\n"
}

### -------------------- ENHANCED LOGGING --------------------
run_with_enhanced_logs() {
  local suite="$1" run_id="$2" build_dir="$3" stdin_data="$4" extra_env="${5:-}"
  local exe="${build_dir}/${GAME_BIN}"
  local tmpdir tagdir
  tmpdir="$(mktemp -d)"
  tagdir="${LOG_ROOT}/${suite}-$(printf "%03d" "$run_id")"
  mkdir -p "$tmpdir"

  printf '%s' "$stdin_data" >"${tmpdir}/stdin.txt"

  # Enhanced environment capture
  {
    echo "suite=${suite}"
    echo "run_id=${run_id}"
    echo "build_dir=${build_dir}"
    echo "exe=${exe}"
    echo "date_utc=$(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "hostname=$(hostname 2>/dev/null || echo 'unknown')"
    echo "kernel=$(uname -a)"
    echo "ulimit_core=$(ulimit -c)"
    echo "ASAN_OPTIONS=${ASAN_OPTIONS:-}"
    echo "UBSAN_OPTIONS=${UBSAN_OPTIONS:-}"
    echo "TSAN_OPTIONS=${TSAN_OPTIONS:-}"
    echo "MSAN_OPTIONS=${MSAN_OPTIONS:-}"
    echo "ASAN_SYMBOLIZER_PATH=${ASAN_SYMBOLIZER_PATH:-}"
    echo "extra_env=${extra_env}"
    echo "CC=$(${CC:-cc} -v 2>&1 | tr '\n' ' ')"
    echo "stdin_size=$(printf '%s' "$stdin_data" | wc -c)"
    echo "memory_free=$(free -m | awk '/^Mem:/ {print $7}')MB"
  } >"${tmpdir}/env.txt"

  # Execute with enhanced monitoring
  local start_time end_time
  start_time=$(date +%s.%N)
  
  if [[ -n "$TTY_WRAPPER" ]]; then
    timeout 300s ${TTY_WRAPPER} -qfec "printf '%s' \"${stdin_data}\" | ${extra_env} ${exe}" "${tmpdir}/typescript" \
      1>"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt"
  else
    timeout 300s bash -c "printf '%s' \"${stdin_data}\" | ${extra_env} ${exe}" \
      >"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt"
  fi
  local rc=$?
  
  end_time=$(date +%s.%N)
  echo "execution_time=$(echo "$end_time - $start_time" | bc)s" >>"${tmpdir}/env.txt"

  if [[ $rc -ne 0 ]]; then
    mv "$tmpdir" "$tagdir"
    
    # Enhanced failure analysis
    {
      echo "=== FAILURE ANALYSIS ==="
      echo "exit_code=$rc"
      [[ $rc -eq 124 ]] && echo "TIMEOUT: Process killed after 300s"
      [[ $rc -eq 139 ]] && echo "SEGFAULT: Signal 11 (SIGSEGV)"
      [[ $rc -eq 134 ]] && echo "ABORT: Signal 6 (SIGABRT)"
    } >>"${tagdir}/analysis.txt"
    
    # Core dump analysis
    shopt -s nullglob
    for corefile in "${build_dir}"/core* core*; do
      [[ -e "$corefile" ]] || continue
      mv "$corefile" "$tagdir"/
      if [[ -n "$(command -v gdb)" ]]; then
        gdb -q -ex "set pagination off" -ex "thread apply all bt" -ex "info registers" -ex "quit" \
          --core="$tagdir/$(basename "$corefile")" "${exe}" >"${tagdir}/gdb_bt.txt" 2>&1 || true
      fi
    done
    
    gauntlet_log "💀 FAILURE: $suite-$run_id (rc=$rc) -> $tagdir"
  else
    rm -rf "$tmpdir"
  fi
  return $rc
}

### -------------------- ADVANCED BUILD CONFIGURATIONS --------------------
build_asan_ubsan() {
  banner "Building ASan+UBSan (Enhanced)"
  rm -rf "$BUILD_SAN_DIR"
  local cflags="-g -O1 -fno-omit-frame-pointer -fno-optimize-sibling-calls"
  cflags+=" -fsanitize=address,undefined -fsanitize-address-use-after-scope"
  cflags+=" -fstack-protector-strong -D_FORTIFY_SOURCE=2"
  
  cmake -S . -B "$BUILD_SAN_DIR" \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_FLAGS="$cflags" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" >/dev/null
  cmake --build "$BUILD_SAN_DIR" -j >/dev/null
}

build_tsan() {
  if [[ "$(maybe clang)" -eq 1 ]]; then
    banner "Building ThreadSanitizer"
    rm -rf "$BUILD_TSAN_DIR"
    local cflags="-g -O1 -fsanitize=thread -fPIE"
    
    CC=clang cmake -S . -B "$BUILD_TSAN_DIR" \
      -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_C_FLAGS="$cflags" \
      -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread -pie" >/dev/null 2>&1 || {
      echo "⚠️  TSan build failed, skipping"
      return 1
    }
    cmake --build "$BUILD_TSAN_DIR" -j >/dev/null 2>&1
  else
    echo "⚠️  Clang not found, skipping TSan build"
    return 1
  fi
}

build_msan() {
  if [[ "$(maybe clang)" -eq 1 ]]; then
    banner "Building MemorySanitizer"
    rm -rf "$BUILD_MSAN_DIR"
    local cflags="-g -O1 -fsanitize=memory -fsanitize-memory-track-origins=2 -fPIE"
    
    CC=clang cmake -S . -B "$BUILD_MSAN_DIR" \
      -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_C_FLAGS="$cflags" \
      -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=memory -pie" >/dev/null 2>&1 || {
      echo "⚠️  MSan build failed, skipping"
      return 1
    }
    cmake --build "$BUILD_MSAN_DIR" -j >/dev/null 2>&1
  else
    echo "⚠️  Clang not found, skipping MSan build"
    return 1
  fi
}

build_hardened_extreme() {
  banner "Building Hardened Extreme"
  rm -rf "$BUILD_HARDENED_DIR"
  local cflags="-O2 -D_FORTIFY_SOURCE=3 -fstack-protector-strong"
  cflags+=" -Wformat-security -Werror=format-security -fPIE"
  cflags+=" -fcf-protection=full -fstack-clash-protection"
  cflags+=" -Wl,-z,relro,-z,now -Wl,-z,noexecstack"
  
  cmake -S . -B "$BUILD_HARDENED_DIR" \
    -DCMAKE_BUILD_TYPE=Hardened \
    -DCMAKE_C_FLAGS="$cflags" \
    -DCMAKE_EXE_LINKER_FLAGS="-pie -Wl,-z,relro,-z,now" >/dev/null
  cmake --build "$BUILD_HARDENED_DIR" -j >/dev/null
}

### -------------------- GAUNTLET TEST SUITES --------------------
gauntlet_asan_chaos() {
  local runs="$1" steps="$2" label="$3"
  banner "GAUNTLET ASan Chaos: $runs runs x $steps steps ($label)"
  local pass=0 fail=0
  
  for i in $(seq 1 "$runs"); do
    local input mode
    # Mix different input types
    case $((i % 4)) in
      0) mode="chaos" ;;
      1) mode="normal" ;;
      2) mode="malformed" ;;
      3) mode="extreme" ;;
    esac
    input="$(gen_script_enhanced "$i" "$steps" "$mode")"
    # SECURITY: Do not inject null bytes that could corrupt file paths
    # input="${input:0:1}"$'\x00'"${input:1}"  # REMOVED: Dangerous null byte injection
    if ASAN_SYMBOLIZER_PATH="${LLVM_SYMBOLIZER}" \
      ASAN_OPTIONS="${ASAN_OPTS}" \
      UBSAN_OPTIONS="${UBSAN_OPTS}" \
      run_with_enhanced_logs "$label" "$i" "$BUILD_SAN_DIR" "$input" >/dev/null 2>&1; then
      echo "✅ $label $i ($mode)"
      ((pass++))
    else
      echo "💀 $label $i FAILED ($mode)"
      ((fail++))
    fi
  done
  
  gauntlet_log "RESULT $label: pass=$pass fail=$fail (failure_rate=$(echo "scale=2; $fail*100/($pass+$fail)" | bc)%)"
  [[ $fail -lt $((runs / 10)) ]] # Allow up to 10% failure rate for chaos testing
}

gauntlet_thread_sanitizer() {
  build_tsan || return 0
  banner "GAUNTLET ThreadSanitizer"
  
  local input
  input="$(gen_script_enhanced 1 "$LONG_STEPS" "normal")"
  
  TSAN_OPTIONS="${TSAN_OPTS}" \
    run_with_enhanced_logs "TSAN" 1 "$BUILD_TSAN_DIR" "$input" || {
    gauntlet_log "TSan detected threading issues"
  }
}

gauntlet_memory_sanitizer() {
  build_msan || return 0
  banner "GAUNTLET MemorySanitizer"
  
  local input
  input="$(gen_script_enhanced 1 "$MED_STEPS" "normal")"
  
  # MSAN NOTE: Expected false positives from uninstrumented ncurses/libc
  # Let MSan continue and log issues without aborting
  gauntlet_log "MSan running with non-aborting mode (logs uninstrumented library issues)"
  MSAN_OPTIONS="${MSAN_OPTS}" \
    run_with_enhanced_logs "MSAN" 1 "$BUILD_MSAN_DIR" "$input" 2>&1 | \
    tee "${LOG_ROOT}/msan_output.log" || true
  
  gauntlet_log "MSan completed - check ${LOG_ROOT}/msan_output.log for details"
}

gauntlet_valgrind_extreme() {
  [[ "$VALGRIND_PRESENT" -eq 1 ]] || {
    echo "⚠️  Valgrind not found; skipping extreme tests"
    return 0
  }
  
  banner "GAUNTLET Valgrind Extreme"
  
  # Multiple valgrind tools
  local tools=("memcheck" "helgrind" "drd")
  
  for tool in "${tools[@]}"; do
    local input
    input="$(gen_script_enhanced 1 "$LONG_STEPS" "chaos")"
    
    local tmpdir tagdir
    tmpdir="$(mktemp -d)"
    tagdir="${LOG_ROOT}/VALGRIND-${tool^^}"
    mkdir -p "$tagdir"
    
    printf '%s' "$input" >"${tmpdir}/stdin.txt"
    
    # Use hardened build instead of debug build
    local exe_path="${BUILD_HARDENED_DIR}/${GAME_BIN}"
    if [[ ! -x "$exe_path" ]]; then
      gauntlet_log "Valgrind $tool: binary not found at $exe_path"
      continue
    fi
    
    timeout 600s valgrind --tool="$tool" --error-exitcode=1 \
      --log-file="${tagdir}/valgrind-${tool}.log" \
      "$exe_path" \
      <"${tmpdir}/stdin.txt" >"${tagdir}/stdout.txt" 2>"${tagdir}/stderr.txt" || {
      gauntlet_log "Valgrind $tool detected issues"
      mv "$tmpdir"/* "$tagdir"/ 2>/dev/null || true
    }
    
    rm -rf "$tmpdir"
  done
}

gauntlet_stress_environment() {
  [[ "$STRESS_PRESENT" -eq 1 ]] || {
    echo "⚠️  stress-ng not found; skipping environment stress"
    return 0
  }
  
  banner "GAUNTLET Environment Stress"
  
  # Start background stress
  stress-ng --cpu "$STRESS_CPU_CORES" --vm 2 --vm-bytes "${MEMORY_PRESSURE_MB}M" \
    --timeout 60s --quiet &
  local stress_pid=$!
  
  # Run tests under stress
  local input
  input="$(gen_script_enhanced 1 "$MED_STEPS" "chaos")"
  
  ASAN_SYMBOLIZER_PATH="${LLVM_SYMBOLIZER}" \
    ASAN_OPTIONS="${ASAN_OPTS}" \
    UBSAN_OPTIONS="${UBSAN_OPTS}" \
    run_with_enhanced_logs "STRESS-ENV" 1 "$BUILD_SAN_DIR" "$input" || {
    gauntlet_log "Failed under environment stress"
  }
  
  # Clean up stress
  kill "$stress_pid" 2>/dev/null || true
  wait "$stress_pid" 2>/dev/null || true
}

gauntlet_signal_chaos() {
  banner "GAUNTLET Signal Chaos"
  
  for i in $(seq 1 "$CHAOS_SIGNAL_TESTS"); do
    local input
    input="$(gen_script_enhanced "$i" "$SHORT_STEPS" "normal")"
    
    # Start the game in background
    printf '%s' "$input" | timeout 30s "${BUILD_SAN_DIR}/${GAME_BIN}" >/dev/null 2>&1 &
    local game_pid=$!
    
    # Wait random time then send random signal
    sleep "0.$(shuf -i 1-9 -n 1)"
    local signals=(TERM INT USR1 USR2 PIPE)
    local sig="${signals[RANDOM % ${#signals[@]}]}"
    
    kill -"$sig" "$game_pid" 2>/dev/null || true
    wait "$game_pid" 2>/dev/null || true
  done
  
  gauntlet_log "Signal chaos testing complete ($CHAOS_SIGNAL_TESTS signals sent)"
}

gauntlet_fuzz_extreme() {
  banner "GAUNTLET Extreme Fuzzing"
  
  # SECURITY WARNING: This function creates files with potentially dangerous names
  echo "⚠️  FUZZING DISABLED: Can create files with dangerous characters that are hard to delete"
  echo "⚠️  To enable: Fix file creation to sanitize fuzzer output first"
  return 0
  
  # UNSAFE CODE BELOW - DO NOT ENABLE WITHOUT FIXES
  # 
  # if [[ "$RADAMSA_PRESENT" -eq 1 ]]; then
  #   gauntlet_log "Running Radamsa fuzzing"
  #   for i in $(seq 1 "$FUZZ_RUNS"); do
  #     local input
  #     input="$(gen_script_enhanced "$i" "$MED_STEPS" "normal" | radamsa -n 1)"
  #     
  #     run_with_enhanced_logs "FUZZ-RADAMSA" "$i" "$BUILD_SAN_DIR" "$input" >/dev/null 2>&1 || true
  #   done
  # fi
  # 
  # if [[ "$ZZUF_PRESENT" -eq 1 ]]; then
  #   gauntlet_log "Running zzuf fuzzing"
  #   for i in $(seq 1 "$FUZZ_RUNS"); do
  #     local input
  #     input="$(gen_script_enhanced "$i" "$MED_STEPS" "normal")"
  #     
  #     # Use zzuf to corrupt input
  #     local tmpdir
  #     tmpdir="$(mktemp -d)"
  #     printf '%s' "$input" | zzuf -r 0.05 -s "$i" >"${tmpdir}/fuzzed_input.txt"
  #     
  #     run_with_enhanced_logs "FUZZ-ZZUF" "$i" "$BUILD_SAN_DIR" "$(cat "${tmpdir}/fuzzed_input.txt")" >/dev/null 2>&1 || true
  #     rm -rf "$tmpdir"
  #   done
  # fi
}

gauntlet_performance_regression() {
  banner "GAUNTLET Performance Regression"
  
  if [[ "$PERF_PRESENT" -eq 1 ]]; then
    local input
    input="$(gen_script_enhanced 1 "$EXTREME_STEPS" "normal")"
    
    local tmpdir
    tmpdir="$(mktemp -d)"
    
    # Performance profiling
    timeout 300s perf record -g --call-graph=dwarf -o "${tmpdir}/perf.data" \
      "${BUILD_REL_DIR}/${GAME_BIN}" <<<"$input" >"${tmpdir}/stdout.txt" 2>"${tmpdir}/stderr.txt" || true
    
    perf report --input="${tmpdir}/perf.data" >"${LOG_ROOT}/perf-report.txt" 2>/dev/null || true
    
    mv "$tmpdir"/* "${LOG_ROOT}/" 2>/dev/null || true
    rm -rf "$tmpdir"
    
    gauntlet_log "Performance profiling complete"
  fi
}

### -------------------- GAUNTLET ORCHESTRATION --------------------
gauntlet_summary() {
  banner "GAUNTLET SUMMARY"
  
  local total_failures
  total_failures=$(find "$LOG_ROOT" -name "*-[0-9][0-9][0-9]" -type d | wc -l)
  
  gauntlet_log "=== GAUNTLET COMPLETE ==="
  gauntlet_log "Log directory: $LOG_ROOT"
  gauntlet_log "Total failure cases: $total_failures"
  
  if [[ $total_failures -gt 0 ]]; then
    gauntlet_log "💀 FAILURES DETECTED - Investigation required!"
    gauntlet_log "Failure breakdown:"
    find "$LOG_ROOT" -name "*-[0-9][0-9][0-9]" -type d | sed 's/.*\///' | sort | uniq -c | while read -r count pattern; do
      gauntlet_log "  $pattern: $count failures"
    done
  else
    gauntlet_log "🎉 ALL TESTS PASSED - Code is battle-ready!"
  fi
  
  # Generate summary report
  {
    echo "# restoHack Gauntlet Test Report"
    echo "Generated: $(date -u)"
    echo "Total failure cases: $total_failures"
    echo ""
    echo "## Test Configuration"
    echo "- Short runs: $GAUNTLET_SHORT_RUNS"
    echo "- Medium runs: $GAUNTLET_MED_RUNS" 
    echo "- Long runs: $GAUNTLET_LONG_RUNS"
    echo "- Extreme runs: $GAUNTLET_EXTREME_RUNS"
    echo "- Fuzz runs: $FUZZ_RUNS"
    echo "- Signal chaos tests: $CHAOS_SIGNAL_TESTS"
    echo ""
    echo "## Available Tools"
    echo "- Valgrind: $([[ $VALGRIND_PRESENT -eq 1 ]] && echo "✅" || echo "❌")"
    echo "- Radamsa: $([[ $RADAMSA_PRESENT -eq 1 ]] && echo "✅" || echo "❌")"
    echo "- zzuf: $([[ $ZZUF_PRESENT -eq 1 ]] && echo "✅" || echo "❌")"
    echo "- stress-ng: $([[ $STRESS_PRESENT -eq 1 ]] && echo "✅" || echo "❌")"
    echo "- perf: $([[ $PERF_PRESENT -eq 1 ]] && echo "✅" || echo "❌")"
  } >"$LOG_ROOT/GAUNTLET-REPORT.md"
}

main() {
  banner "🔥 RESTOHACK ABSOLUTE GAUNTLET 🔥"
  gauntlet_log "Starting gauntlet run with $(cc_id)"
  gauntlet_log "Logs: $LOG_ROOT"
  
  # Build all configurations
  build_asan_ubsan
  build_hardened_extreme
  
  # Core gauntlet tests
  gauntlet_asan_chaos "$GAUNTLET_SHORT_RUNS" "$SHORT_STEPS" "GAUNTLET-SHORT" || true
  gauntlet_asan_chaos "$GAUNTLET_MED_RUNS" "$MED_STEPS" "GAUNTLET-MED" || true
  gauntlet_asan_chaos "$GAUNTLET_LONG_RUNS" "$LONG_STEPS" "GAUNTLET-LONG" || true
  gauntlet_asan_chaos "$GAUNTLET_EXTREME_RUNS" "$EXTREME_STEPS" "GAUNTLET-EXTREME" || true
  
  # Advanced sanitizer tests
  gauntlet_thread_sanitizer || true
  gauntlet_memory_sanitizer || true
  
  # Valgrind extreme testing
  gauntlet_valgrind_extreme || true
  
  # Environment stress
  gauntlet_stress_environment || true
  
  # Chaos testing
  gauntlet_signal_chaos || true
  
  # SECURITY WARNING: Fuzzing DISABLED - creates files with dangerous characters
  # gauntlet_fuzz_extreme || true  # UNSAFE: Can create undeletable files
  
  # Performance regression
  gauntlet_performance_regression || true
  
  # Final summary
  gauntlet_summary
}

# Allow sourcing for individual function testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi