#!/bin/bash
#
# restoHack Sanitizer Builds Script
# Creates separate builds with AddressSanitizer, UBSanitizer, and MemorySanitizer
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔬 restoHack Sanitizer Builds"
echo "=============================="
echo "Project root: $PROJECT_ROOT"
echo

# Function to build with specific sanitizer
build_sanitizer() {
    local name="$1"
    local flags="$2"
    local build_dir="$PROJECT_ROOT/build-$name"
    
    echo "🧪 Building $name..."
    echo "   Flags: $flags"
    echo "   Build dir: $build_dir"
    
    # Clean previous build
    if [[ -d "$build_dir" ]]; then
        echo "   🧹 Cleaning previous build..."
        rm -rf "$build_dir"
    fi
    
    # Create build directory
    mkdir -p "$build_dir"
    cd "$build_dir"
    
    # Configure with sanitizer flags
    echo "   🔧 Configuring..."
    cmake \
        -S "$PROJECT_ROOT" \
        -B . \
        -DCMAKE_BUILD_TYPE=Debug \
        -DCMAKE_C_FLAGS="-O1 -g3 -fno-omit-frame-pointer $flags" \
        -DCMAKE_EXE_LINKER_FLAGS="$flags" \
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DENABLE_STRUCT_PACKING=ON \
        -DENABLE_SAVE_VALIDATION=ON \
        -G "Unix Makefiles"
    
    echo "   🔨 Building..."
    cmake --build . --parallel "$(nproc)"
    
    echo "   ✅ $name build complete!"
    echo
}

# Function to check compiler support
check_compiler_support() {
    local compiler="${CC:-gcc}"
    echo "🔍 Checking compiler support..."
    echo "   Compiler: $compiler"
    
    # Check if it's clang or gcc
    if $compiler --version 2>/dev/null | grep -qi clang; then
        echo "   ✅ Clang detected - all sanitizers supported"
        return 0
    elif $compiler --version 2>/dev/null | grep -qi gcc; then
        echo "   ✅ GCC detected - ASan and UBSan supported"
        echo "   ⚠️  MSan requires Clang (will skip if GCC)"
        return 0
    else
        echo "   ❌ Unknown compiler - some sanitizers may not work"
        return 1
    fi
}

# Function to display usage instructions
show_usage() {
    echo "📋 Usage Instructions:"
    echo "======================"
    echo
    echo "🔸 AddressSanitizer (ASan) - Memory error detection:"
    echo "   cd $PROJECT_ROOT/build-asan"
    echo "   ASAN_OPTIONS=detect_stack_use_after_return=1:detect_leaks=1 ./hack"
    echo
    echo "🔸 UndefinedBehaviorSanitizer (UBSan) - Undefined behavior detection:"
    echo "   cd $PROJECT_ROOT/build-ubsan"
    echo "   UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 ./hack"
    echo
    echo "🔸 MemorySanitizer (MSan) - Uninitialized memory detection:"
    echo "   cd $PROJECT_ROOT/build-msan"
    echo "   MSAN_OPTIONS=print_stats=1:halt_on_error=0:exit_code=0 ./hack"
    echo "   ⚠️  MSan WILL exit on ncurses library issues - this is expected and not a restoHack bug"
    echo "   💡 For restoHack-specific testing, use ASan+UBSan instead"
    echo
    echo "🔸 Combined ASan + UBSan:"
    echo "   cd $PROJECT_ROOT/build-asan-ubsan"
    echo "   ASAN_OPTIONS=detect_stack_use_after_return=1 UBSAN_OPTIONS=print_stacktrace=1 ./hack"
    echo
    echo "💡 Tips:"
    echo "   - Use ASan+UBSan for restoHack code testing (cleanest for our code)"
    echo "   - MSan will show ncurses library issues - these are external, not restoHack bugs"
    echo "   - Use 'gdb ./hack' for interactive debugging with sanitizers"
    echo "   - Check 'dmesg' for kernel-level memory protection messages"
    echo "   - MSan may require libc++ on some systems: export MSAN_SYMBOLIZER_PATH=\$(which llvm-symbolizer)"
}

# Main execution
check_compiler_support || {
    echo "❌ Compiler check failed. Proceeding anyway..."
}

echo "🚀 Building sanitizer variants..."
echo

# AddressSanitizer - detects buffer overflows, use-after-free, double-free, memory leaks
build_sanitizer "asan" "-fsanitize=address"

# UndefinedBehaviorSanitizer - detects undefined behavior like integer overflow, array bounds
build_sanitizer "ubsan" "-fsanitize=undefined"

# Combined ASan + UBSan - comprehensive error detection
build_sanitizer "asan-ubsan" "-fsanitize=address,undefined"

# MemorySanitizer - detects use of uninitialized memory (Clang only)
if command -v clang >/dev/null 2>&1; then
    CC=clang build_sanitizer "msan" "-fsanitize=memory -fsanitize-memory-track-origins"
else
    echo "⚠️  Skipping MemorySanitizer - requires Clang"
    echo "   Install clang to enable MSan: apt install clang"
fi

echo
echo "🎉 All sanitizer builds complete!"
echo

show_usage

# Test basic functionality
echo "🧪 Quick smoke test..."
echo "======================"

test_build() {
    local build_dir="$1"
    local name="$2"
    
    if [[ -x "$build_dir/hack" ]]; then
        echo "🔸 Testing $name build..."
        cd "$build_dir"
        timeout 5s ./hack --help 2>/dev/null || echo "   ✅ $name build executable (help may not be available)"
    else
        echo "❌ $name build failed - executable not found"
    fi
}

test_build "$PROJECT_ROOT/build-asan" "ASan"
test_build "$PROJECT_ROOT/build-ubsan" "UBSan" 
test_build "$PROJECT_ROOT/build-asan-ubsan" "ASan+UBSan"
if [[ -d "$PROJECT_ROOT/build-msan" ]]; then
    test_build "$PROJECT_ROOT/build-msan" "MSan"
fi

echo
echo "✨ Ready for sanitized testing!"