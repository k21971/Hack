# restoHack Build Instructions

## Quick Start

**Just want to play?** Download a pre-built binary from [Releases](https://github.com/Critlist/restoHack/releases).

**Building from source:**

```bash
git clone https://github.com/Critlist/restoHack.git
cd restoHack
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/hack
```

## Requirements

- CMake (≥3.16)
- C compiler (gcc or clang)
- ncurses library

**Install dependencies:**

- **Ubuntu/Debian:** `sudo apt install cmake build-essential libncurses-dev`
- **Fedora/RHEL:** `sudo dnf install cmake gcc ncurses-devel`
- **Arch:** `sudo pacman -S cmake gcc ncurses`
- **macOS:** `brew install cmake ncurses`
- **FreeBSD:** `pkg install cmake gcc ncurses`

## Build Types

```bash
# Release (optimized for playing)
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Debug (with sanitizers for development)
cmake -B build-debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build-debug

# RelWithDebInfo (production servers with debug symbols)
cmake -B build-server -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build-server
```

## Platform Notes

### macOS

Xcode Command Line Tools required. Install with: `xcode-select --install`

### OpenBSD

```bash
pkg_add cmake gcc ncurses
cmake -B build -DCMAKE_C_COMPILER=/usr/local/bin/gcc
cmake --build build
```

### Static Binary

Download from releases or build on Alpine/musl with `-DCMAKE_EXE_LINKER_FLAGS="-static"`

## Troubleshooting

**ncurses not found:** Install development package (see Requirements)

**Old CMake:** Update or use traditional syntax:

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make
```

**Clean rebuild:** `rm -rf build && cmake -B build && cmake --build build`

## Development

The project uses standard CMake with presets for modern IDEs (VSCode, CLion, etc).

For contributing, see [CODING_STANDARDS.md](CODING_STANDARDS.md).
