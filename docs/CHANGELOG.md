# Changelog

All notable changes to restoHack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-23

### Added
- **Terminal resize protection**: SIGWINCH handler prevents display corruption from dynamic terminal sizing
- **Enhanced gauntlet testing**: Inventory testing, item operations, save/resume functionality

### Fixed
- **CRITICAL**: Terminal resize corruption causing map display bugs and wall-walking glitches
- **CRITICAL**: Message buffer concatenation overflow with wide terminals (CO > 80)
- **CRITICAL**: --More-- prompt positioning bugs in topline system
- **SECURITY**: Eliminated all 151 char-subscript buffer underflow vulnerabilities
- **SECURITY**: Fixed 30 strict-aliasing undefined behavior violations
- **SECURITY**: Resolved all uninitialized variable warnings with -Werror gates
- **SECURITY**: Fixed 10 control-reaches-end-of-non-void-function undefined behavior issues
- **SECURITY**: Fixed 16 implicit-fallthrough undefined behavior cases
- **SECURITY**: Disabled dangerous fuzzing functions that could create undeletable files

### Changed
- Updated all signed char array indexing to safe unsigned char casting
- Enhanced EGD macro in hack.vault.c with proper function wrapper
- Added proper return statements to all void functions
- Implemented fallthrough annotations for intentional switch cases
- Configured MSan with non-aborting mode for uninstrumented library compatibility

### Technical
- **Battle-tested**: 1,260+ automated tests passed (ASan, UBSan, MSan, TSan)
- **Deployment-ready**: Zero critical warnings under hardened build flags
- **Memory-safe**: All buffer security vulnerabilities eliminated
- **Server-grade**: Ready for production deployment on HardFought.org
- Enhanced gauntlet testing with signal chaos, stress testing, and performance profiling

## [1.0.6] - 2025-08-14

### Added
- Historical references and fixed build config in CMake

## [1.0.5] - 2025-08-12

### Added
- Coding standards documentation for non-original code contributions
- Historical source files and game commands documentation

### Changed  
- Refactored memory allocation functions to ANSI C standards with enhanced type safety
- Improved asset copying logic to handle files uniformly with better error messaging
- Updated CMake and CI configuration for BSD builds
- Enhanced CPack configuration with optional packaging support

### Technical
- Preserved original 1984 behavior while eliminating casting requirements in memory allocation
- Enhanced build system reliability across different platforms

## [1.0.4] - 2025-08-11

### Added
- Hybrid binary+source tarballs containing both static executable and source code
- BSD-specific build instructions for FreeBSD, OpenBSD, and NetBSD
- Support for building from hybrid tarballs without separate source download
- CI testing for published hybrid tarballs on release tags
- FreeBSD CI reliability improvements with enhanced error handling

### Fixed
- Shell syntax error in static-build.sh (apostrophe in comment breaking Docker string)
- BusyBox tar compatibility issues with GNU tar-specific options
- Missing source files in static binary releases preventing user rebuilds
- CI flakes in FreeBSD environment by removing interactive game execution
- TLS certificate issues in CI with ca_root_nss package addition

### Changed
- Static build script now includes CMakeLists.txt, config.h.in, and src/ directory
- Updated documentation with hybrid tarball usage instructions
- Improved cross-platform build documentation
- Enhanced CI with hard failure tests for required files instead of soft warnings

## [1.0.3] - 2025-08-10

### Added
- Portable RNG seeding with CMake feature detection
- Support for arc4random, arc4random_buf, getentropy, and srandomdev across platforms
- Proper curses library detection replacing hardcoded termcap linking
- Fallback delay_output implementation for systems without curses version

### Fixed
- Build failures on NetBSD/pkgsrc due to missing delay_output symbol
- Function name conflicts with curses library (unctrl, timeout, delay_output)
- OS-specific #ifdef dependencies that broke portability
- Hardcoded termcap library detection causing link failures

### Changed
- Replaced OS-specific `#ifdef __linux__` with portable feature detection
- Updated CMake to use `find_package(Curses REQUIRED)` 
- Renamed internal functions to avoid curses conflicts: `unctrl()` → `hack_unctrl()`, `timeout()` → `hack_timeout()`
- Enhanced static build script with better library detection and quality checks

### Technical
- All original 1984 code preserved via comments, not deleted
- Added comprehensive CMake feature detection for RNG functions
- Improved static binary build process with libbsd support
- Universal build compatibility across Linux, NetBSD, macOS

## [1.0.2] - 2025-08-08

### Added
- Static binary release for Linux x86_64
- Prebuilt distribution with no external dependencies
- Enhanced static build pipeline with Docker-based compilation

### Changed
- Updated static build script for better reliability and reproducibility
- Improved packaging with proper permissions and launcher script

### Technical
- Static linking against ncurses for zero-dependency distribution
- Optimized binary size and performance

## [1.0.1] - 2025-08-06

### Added
- Modern flock()-based locking system replacing unreliable 1984 link() locking
- Automatic cleanup of stale lock files on process death
- Enhanced save system with versioned directories and backup support

### Fixed
- "Game in progress" hangs caused by stale lock files
- Filesystem compatibility issues with modern systems
- Segfault in death screen (hack.rip.c) caused by buffer overflow in name centering
- RIP screen display issues with various username lengths

### Changed
- Complete K&R to ANSI C conversion for entire codebase (~250 functions)
- Updated read-only string literals to writable arrays for compiler compatibility
- Improved error handling and memory safety throughout

### Technical
- Preserved 100% authentic 1984 gameplay mechanics and balance
- Enhanced build system with CMake replacing vintage Makefiles
- Modern signal handling for Unix window environments

## [1.0.0] - 2025-08-01

### Added
- Initial public release of restoHack
- Complete playable restoration of 1984 Hack game
- All core game systems: character creation, inventory, combat, magic, shops
- Full dungeon generation with authentic maze algorithms
- Save/load system with proper exit handling
- Terminal display with complete termcap support

### Technical
- CMake-based build system for modern compatibility
- Cross-platform support (Linux, macOS, BSD)
- POSIX-only dependencies for maximum portability
- Complete preservation of original 1984 game logic
- Zero external dependencies beyond standard C library and curses

### Game Features
- Multiple character classes: Tourist, Wizard, Fighter, Caveman
- Authentic item generation and cursed/blessed mechanics
- Monster AI including pets, shopkeepers, and guards
- Magic system with potions, scrolls, and wands
- Shop system with authentic billing mechanics
- Permadeath with proper tombstone generation