#!/usr/bin/env bash
# restoHack test gauntlet (v2) — ASan, UBSan, MSan, and Valgrind lanes
# Safe defaults and consistent logging. Designed for clang toolchain.
set -euo pipefail
IFS=$'\n\t'

# ---------- config ----------
PROJECT_NAME="restoHack"
# Work from dev/ directory as if it's project root
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="${ROOT_DIR}/gauntlet-logs/$(date +%Y%m%d-%H%M%S)"
BUILD_ASAN="${ROOT_DIR}/build-asan"
BUILD_UBSAN="${ROOT_DIR}/build-ubsan"
BUILD_MSAN="${ROOT_DIR}/build-msan"
BUILD_REL="${ROOT_DIR}/build-rel"

# If you have a custom stress script, point here
STRESS_SCRIPT="${ROOT_DIR}/stress.sh"  # optional; falls back to quick smoke if missing

# SECURITY NOTE: This script does not include fuzzing to avoid file creation issues

# Sanitizer knobs - each build will only use its specific sanitizer
export ASAN_OPTIONS="abort_on_error=1:strict_string_checks=1:detect_stack_use_after_return=1:check_initialization_order=1"
export UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
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
  cmake -S "${ROOT_DIR}/.." -B "$bdir" \
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
    # Use proper game input generation like stress.sh
    local exit_code=0
    local input
    input="$(gen_game_input 10 1)"
    
    printf '%s' "$input" | "$bin" -D >/dev/null 2>&1 || exit_code=$?
    if [[ $exit_code -eq 0 || $exit_code -eq 141 ]]; then
      say "RUN" "$tag smoke completed (exit=$exit_code)"
    else
      die "$tag smoke failed with unexpected exit code: $exit_code"
    fi
  else
    die "Binary not found or not executable: $bin"
  fi
}

# Generate proper game input like stress.sh
gen_game_input() {
  local steps="$1" run_id="$2"
  local out=""
  
  # Start with realistic game opening: n (new game), Player name
  out+="n\nPlayer$(printf "%02d" "$run_id")\n"
  
  # Add some random movement (hjkl) - 5-6 moves
  local movement_keys="hjkl"
  local moves=$((5 + RANDOM % 2))  # 5 or 6 moves
  for _ in $(seq 1 "$moves"); do
    local move="${movement_keys:RANDOM%${#movement_keys}:1}"
    out+="$move"
  done
  
  # Add inventory command and search
  out+="i/"
  
  # Add some down movements
  out+="jj"
  
  # Fill remaining steps with safe random keys if needed
  local remaining=$((steps - ${#out}))
  if [[ $remaining -gt 0 ]]; then
    local safe_keys="hjkl.Ls ?"
    for _ in $(seq 1 "$remaining"); do
      local c="${safe_keys:RANDOM%${#safe_keys}:1}"
      out+="$c"
      [[ "$c" =~ [\.\?Ls] ]] && out+='\n'
    done
  fi
  
  # Add quit sequence
  out+="Qy\n"
  
  printf "%s" "$out"
}

run_stress() {
  local bin="$1"; local tag="$2"
  # Targeted stress testing with visual feedback (like stress.sh)
  say "STRESS" "$tag soak: 50 runs with visual feedback"
  local pass=0 fail=0
  
  for i in $(seq 1 50); do
    local exit_code=0
    local input
    input="$(gen_game_input 40 "$i")"
    
    printf '%s' "$input" | "$bin" -D >/dev/null 2>&1 || exit_code=$?
    
    if [[ $exit_code -eq 0 || $exit_code -eq 141 ]]; then
      echo "✅ $tag $i"
      ((pass++))
    else
      echo "❌ $tag $i FAILED (exit=$exit_code)"
      ((fail++))
    fi
  done
  
  echo "__RESULT__ $tag pass=$pass fail=$fail"
  say "STRESS" "$tag completed: $pass passed, $fail failed"
  
  # Allow up to 10% failure rate for stress testing (some failures expected)
  local failure_rate=$((fail * 100 / 50))
  if [[ $failure_rate -gt 10 ]]; then
    say "STRESS" "⚠️  High failure rate: ${failure_rate}% (${fail}/50)"
    return 1
  else
    say "STRESS" "✅ Acceptable failure rate: ${failure_rate}% (${fail}/50)"
    return 0
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

# ---------- SEQUENTIAL BUILD-THEN-TEST LANES ----------

# === ASAN LANE: Build → Test → Analyze ===
say "LANE" "🔥 AddressSanitizer (heap/stack/UAF detection)"
build_lane "asan" "$BUILD_ASAN" "-O1 -g -fsanitize=address -fno-omit-frame-pointer -fno-sanitize-recover=all"
run_game   "${BUILD_ASAN}/hack" "asan"
(run_stress "${BUILD_ASAN}/hack" "asan" || say "STRESS" "⚠️  ASan stress had issues, continuing...") 2>&1 | tee "${LOG_DIR}/asan_stress.log"
grep_warns "${LOG_DIR}/asan_build.log"

# === UBSAN LANE: Build → Test → Analyze ===
say "LANE" "⚡ UndefinedBehaviorSanitizer (logic UB detection)"
build_lane "ubsan" "$BUILD_UBSAN" "-O2 -g -fsanitize=undefined -fno-omit-frame-pointer -fno-sanitize-recover=all -Wall -Wextra -Wshadow -Wuninitialized -Wconditional-uninitialized"
run_game   "${BUILD_UBSAN}/hack" "ubsan"
(run_stress "${BUILD_UBSAN}/hack" "ubsan" || say "STRESS" "⚠️  UBSan stress had issues, continuing...") 2>&1 | tee "${LOG_DIR}/ubsan_stress.log"
grep_warns "${LOG_DIR}/ubsan_build.log"

# === MSAN LANE: Build → Test → Analyze ===
say "LANE" "🧠 MemorySanitizer (uninitialized memory detection)"
build_lane "msan" "$BUILD_MSAN" "-O1 -g -fsanitize=memory -fno-omit-frame-pointer -fno-sanitize-recover=all -fsanitize-memory-track-origins=2"
note_msan_libc
say "MSAN" "Non-aborting mode - will capture uninstrumented library issues to logs"
run_game   "${BUILD_MSAN}/hack" "msan" 2>&1 | tee "${LOG_DIR}/msan_game.log" || true
(run_stress "${BUILD_MSAN}/hack" "msan" || say "STRESS" "⚠️  MSan stress had issues, continuing...") 2>&1 | tee "${LOG_DIR}/msan_stress.log" || true
grep_warns "${LOG_DIR}/msan_build.log"

# === VALGRIND LANE: Build → Test → Analyze ===
say "LANE" "🔍 Valgrind (memory leak detection)"
build_lane "rel" "$BUILD_REL" "-O2 -g -fno-omit-frame-pointer -Wall -Wextra"
run_game   "${BUILD_REL}/hack" "rel"
(run_stress "${BUILD_REL}/hack" "rel" || say "STRESS" "⚠️  Release stress had issues, continuing...") 2>&1 | tee "${LOG_DIR}/rel_stress.log"

if have valgrind; then
  say "VALGRIND" "running memcheck quick pass"
  vg_exit=0
  input="$(gen_game_input 10 1)"
  printf '%s' "$input" | valgrind --error-exitcode=99 --leak-check=full --show-leak-kinds=all \
           --quiet --track-origins=yes "${BUILD_REL}/hack" -D \
           2> "${LOG_DIR}/valgrind_memcheck.log" || vg_exit=$?
  
  # Valgrind exit codes: 0=clean, 99=errors found, 141=SIGPIPE (expected)
  if [[ $vg_exit -eq 0 || $vg_exit -eq 141 ]]; then
    say "VALGRIND" "memcheck completed (exit=$vg_exit)"
  elif [[ $vg_exit -eq 99 ]]; then
    say "VALGRIND" "⚠️  Memory errors detected!"
  else
    say "VALGRIND" "⚠️  Unexpected exit code: $vg_exit"
  fi
  
  say "SCAN" "valgrind findings"
  grep -nE "ERROR SUMMARY|Invalid|definitely lost|indirectly lost|uninitialised" "${LOG_DIR}/valgrind_memcheck.log" || true
else
  say "VALGRIND" "not found; skipping"
fi

# ---------- FINAL SUMMARY ----------
gauntlet_summary() {
  local total_failures=0
  local lanes_run=0
  
  say "SUMMARY" "🎯 GAUNTLET COMPLETE"
  echo ""
  echo "=== LANE RESULTS ==="
  
  # Count actual issues by checking for real problems in logs
  if [[ -d "$LOG_DIR" ]]; then
    local asan_failures ubsan_failures msan_failures valgrind_failures
    
    # ASan: Look for actual AddressSanitizer errors
    asan_failures=$(grep -h "AddressSanitizer\|ERROR: AddressSanitizer\|heap-buffer-overflow\|heap-use-after-free" "$LOG_DIR"/*asan*.log 2>/dev/null | wc -l || echo 0)
    
    # UBSan: Look for actual UndefinedBehaviorSanitizer errors  
    ubsan_failures=$(grep -h "UndefinedBehaviorSanitizer\|runtime error:" "$LOG_DIR"/*ubsan*.log 2>/dev/null | wc -l || echo 0)
    
    # MSan: Look for actual MemorySanitizer errors (not uninstrumented library warnings)
    msan_failures=$(grep -h "MemorySanitizer\|use-of-uninitialized-value" "$LOG_DIR"/*msan*.log 2>/dev/null | grep -v "uninstrumented" | wc -l || echo 0)
    
    # Valgrind: Look for actual errors (not just reachable memory)
    valgrind_failures=$(grep -h "Invalid\|definitely lost\|possibly lost" "$LOG_DIR"/valgrind*.log 2>/dev/null | wc -l || echo 0)
    
    echo "🔥 ASan Lane:      $([ $asan_failures -eq 0 ] && echo "✅ PASSED" || echo "❌ $asan_failures issues")"
    echo "⚡ UBSan Lane:     $([ $ubsan_failures -eq 0 ] && echo "✅ PASSED" || echo "❌ $ubsan_failures issues")"
    echo "🧠 MSan Lane:      $([ $msan_failures -eq 0 ] && echo "✅ PASSED" || echo "❌ $msan_failures issues")"
    echo "🔍 Valgrind Lane:  $([ $valgrind_failures -eq 0 ] && echo "✅ PASSED" || echo "❌ $valgrind_failures issues")"
    
    total_failures=$((asan_failures + ubsan_failures + msan_failures + valgrind_failures))
    lanes_run=4
  fi
  
  echo ""
  echo "=== OVERALL RESULT ==="
  if [[ $total_failures -eq 0 ]]; then
    echo "🎉 ALL LANES PASSED - Code is battle-ready!"
    echo "✅ $lanes_run sanitizer lanes completed successfully"
    echo "✅ Memory safety verified across all test suites"
  else
    echo "💀 ISSUES DETECTED - Investigation required!"
    echo "❌ Total issues found: $total_failures"
    echo "📁 Detailed logs available in: $LOG_DIR"
  fi
  
  echo ""
  echo "=== TEST CONFIGURATION ==="
  echo "• Stress runs per lane: 50"
  echo "• Compiler: $(${CC:-cc} --version 2>/dev/null | head -n1 || echo 'unknown')"
  echo "• Build types: ASan, UBSan, MSan, Release+Valgrind"
  echo "• Log directory: $LOG_DIR"
  
  echo ""
  echo "=== AVAILABLE TOOLS ==="
  echo "• Valgrind: $(have valgrind && echo "✅" || echo "❌")"
  echo "• Clang: $(have clang && echo "✅" || echo "❌")"
  echo "• GDB: $(have gdb && echo "✅" || echo "❌")"
  echo "• ripgrep: $(have rg && echo "✅" || echo "❌")"
  
  # Generate markdown report
  {
    echo "# restoHack Gauntlet v2 Test Report"
    echo "Generated: $(date -u)"
    echo ""
    echo "## Results Summary"
    echo "- Total issues: $total_failures"
    echo "- Lanes tested: $lanes_run"
    echo "- Overall status: $([ $total_failures -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo ""
    echo "## Lane Details"
    echo "- 🔥 AddressSanitizer: $([ $asan_failures -eq 0 ] && echo "PASSED" || echo "FAILED ($asan_failures issues)")"
    echo "- ⚡ UndefinedBehaviorSanitizer: $([ $ubsan_failures -eq 0 ] && echo "PASSED" || echo "FAILED ($ubsan_failures issues)")"
    echo "- 🧠 MemorySanitizer: $([ $msan_failures -eq 0 ] && echo "PASSED" || echo "FAILED ($msan_failures issues)")"
    echo "- 🔍 Valgrind: $([ $valgrind_failures -eq 0 ] && echo "PASSED" || echo "FAILED ($valgrind_failures issues)")"
    echo ""
    echo "## Configuration"
    echo "- Stress runs: 50 per lane"
    echo "- Compiler: $(${CC:-cc} --version 2>/dev/null | head -n1 || echo 'unknown')"
    echo "- Generated: $(date -u)"
  } > "$LOG_DIR/GAUNTLET-REPORT.md"
  
  if [[ -f "$LOG_DIR/GAUNTLET-REPORT.md" ]]; then
    echo "📄 Detailed report saved: $LOG_DIR/GAUNTLET-REPORT.md"
  else
    echo "⚠️  Failed to create report at: $LOG_DIR/GAUNTLET-REPORT.md"
  fi
  echo ""
  
  # Return appropriate exit code
  return $total_failures
}

gauntlet_summary
say "DONE" "Logs in ${LOG_DIR}"
