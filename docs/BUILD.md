# 📋 restoHack Build Instructions

Comprehensive build instructions for all platforms and development scenarios.

## Table of Contents

- [Requirements](#requirements)
- [Build Variants](#build-variants)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [IDE Integration](#ide-integration)
- [Development & Testing](#development--testing)
- [Troubleshooting](#troubleshooting)

---

## Requirements

**Minimum:**
- `git`
- `cmake` (≥3.16)
- C compiler (`gcc` or `clang`)
- `ncurses` or `termcap` library

**Platform-specific dependency installation:**
- **Ubuntu/Debian:** `sudo apt install git cmake build-essential libncurses-dev`
- **Fedora/RHEL:** `sudo dnf install git cmake gcc ncurses-devel`
- **Arch Linux:** `sudo pacman -S git cmake gcc ncurses`
- **macOS:** `brew install cmake ncurses` (Xcode command line tools for compiler)

---

## Build Variants

### Release Build (Optimized for Playing)

**Modern CMake:**
```bash
cmake --preset=release
cmake --build build
./build/hack
```

**Traditional CMake:**
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/hack
```

### Debug Build (Development with Symbols)

**Modern CMake:**
```bash
cmake --preset=debug
cmake --build build-debug
./build-debug/hack
```

**Traditional CMake:**
```bash
cmake -S . -B build-debug -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
cmake --build build-debug
./build-debug/hack
```

### Hardened Build (Security-Focused for Servers)

**Modern CMake:**
```bash
cmake --preset=hardened
cmake --build build-hardened
./build-hardened/hack
```

**Traditional CMake:**
```bash
cmake -S . -B build-hardened -DCMAKE_BUILD_TYPE=Hardened
cmake --build build-hardened
./build-hardened/hack
```

---

## Platform-Specific Instructions

### Linux

**Standard build works on all distributions:**
```bash
cmake --preset=release && cmake --build build
```

### FreeBSD

```bash
# Install dependencies
pkg install cmake gcc ncurses

# Build (modern CMake)
cmake --preset=release && cmake --build build

# OR traditional if presets unsupported
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build
```

### OpenBSD

```bash
# Install dependencies  
pkg_add cmake gcc ncurses

# Build with explicit compiler paths
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \\
  -DCMAKE_C_COMPILER=/usr/local/bin/gcc
cmake --build build
./build/hack
```

### NetBSD

```bash
# Install dependencies
pkgin install cmake gcc ncurses

# Use pkgsrc paths for libraries
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \\
  -DCMAKE_PREFIX_PATH=/usr/pkg
cmake --build build
./build/hack
```

### macOS

```bash
# Install dependencies
brew install cmake ncurses

# Build (standard)
cmake --preset=release && cmake --build build
```

---

## IDE Integration

restoHack includes `CMakePresets.json` for modern IDE support.

### Visual Studio Code

1. Install the **CMake Tools** extension
2. Open the restoHack folder
3. Select a preset from the status bar (release/debug/hardened)
4. Build using `Ctrl+Shift+P` → "CMake: Build"

### CLion

1. Open the restoHack folder
2. CLion automatically detects and imports presets
3. Select preset from the configuration dropdown
4. Build using standard CLion build commands

### Qt Creator

1. File → Open File or Project → select `CMakeLists.txt`
2. Choose preset in project configuration dialog
3. Build using standard Qt Creator build commands

### Any IDE/Editor

All presets automatically generate `compile_commands.json` for:
- Language servers (clangd, ccls)
- Static analysis tools (clang-tidy, cppcheck)
- Code completion engines

---

## Development & Testing

### Memory Analysis with Valgrind

```bash
# Clean build without sanitizers (required for Valgrind)
cmake -S . -B build-memcheck -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZERS=OFF
cmake --build build-memcheck

# Run Valgrind
valgrind --tool=memcheck --leak-check=full ./build-memcheck/hack
```

### Static Analysis

```bash
# Build with compile commands
cmake --preset=debug

# Use generated compile_commands.json with tools:
clang-tidy --checks='*' src/*.c
cppcheck --project=build-debug/compile_commands.json
```

### Sanitizer Builds

**Address + Undefined Behavior Sanitizers:**
```bash
cmake --preset=debug  # Includes sanitizers by default
cmake --build build-debug

# Run with sanitizer options
ASAN_OPTIONS=detect_stack_use_after_return=1 ./build-debug/hack
```

**Memory Sanitizer (Clang only):**
```bash
cmake -S . -B build-msan -DCMAKE_BUILD_TYPE=Debug \\
  -DENABLE_SAVE_SANITIZERS=ON -DCMAKE_C_COMPILER=clang
cmake --build build-msan
./build-msan/hack
```

### Performance Profiling

```bash
# Build with symbols
cmake --preset=debug
cmake --build build-debug

# Profile with perf (Linux)
perf record -g ./build-debug/hack
perf report

# Profile with gprof
cmake -S . -B build-profile -DCMAKE_BUILD_TYPE=Debug \\
  -DCMAKE_C_FLAGS="-pg" -DCMAKE_EXE_LINKER_FLAGS="-pg"
cmake --build build-profile
./build-profile/hack
gprof build-profile/hack gmon.out > profile.txt
```

---

## Troubleshooting

### Common Issues

**"CMAKE_BUILD_TYPE not specified"**
- Solution: Always specify a build type or use presets

**"ncurses not found"**
- Ubuntu/Debian: `sudo apt install libncurses-dev`
- RedHat/Fedora: `sudo dnf install ncurses-devel`
- Arch: `sudo pacman -S ncurses`

**"Preset not supported"**
- Your CMake version is <3.19, use traditional commands instead
- Update CMake or use the "Traditional CMake" commands shown above

**Compiler warnings on older systems**
- This is expected - restoHack includes legacy 1984 code
- Warnings are intentionally not treated as errors for compatibility

### Clean Rebuild

```bash
# Remove all build artifacts
rm -rf build* && cmake --preset=release && cmake --build build
```

### Build Options

**Available CMake options:**
- `ENABLE_SANITIZERS` - Enable AddressSanitizer/UBSanitizer (Debug builds)
- `ENABLE_SAVE_DEBUG` - Enable save system debug logging
- `ENABLE_SAVE_VALIDATION` - Enable save file integrity checks (default: ON)
- `ENABLE_STRUCT_PACKING` - Enable struct packing for save compatibility (default: ON)

**Example:**
```bash
cmake -S . -B build-custom -DCMAKE_BUILD_TYPE=Release \\
  -DENABLE_SAVE_DEBUG=ON -DENABLE_SANITIZERS=OFF
```

### Getting Help

- **Game Issues:** See the original [README](../README.md) and [HISTORY_OF_HACK.md](HISTORY_OF_HACK.md)
- **Build Issues:** Check this document first, then open a GitHub issue
- **Development:** See [CODING_STANDARDS.md](CODING_STANDARDS.md) for contribution guidelines
- **Preservation Questions:** See [HISTORY_OF_HACK.md](HISTORY_OF_HACK.md) for project philosophy