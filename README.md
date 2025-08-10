# restoHack: Bringing 1984 Hack Back from the Dead

**restoHack** is a modern resurrection of *Hack*, the legendary 1984 roguelike that paved the way for *NetHack*. This isn't a reimagining. This is preservation with a blowtorch and a scalpel. The goal: get the original code compiling, running, and dungeon-crawling like it did back when floppy disks were king, but on a 2025 toolchain.

Think of it as a resto-mod. The soul stays vintage. The internals? Cleaned, modernized, and ready to play in 2025.

---


<h3 align="Left">Screenshots</h3>
<p align="center"><em>Luck and death, in that order.</em></p>

<p align="center">
  <a href="https://github.com/Critlist/restoHack/releases">
    <img src="docs/media/FullMoon.png" alt="Full moon event" width="420"/>
  </a>
  <a href="https://github.com/Critlist/restoHack/releases">
    <img src="docs/media/Tombstone.png" alt="Tombstone" width="420"/>
  </a>
</p>

---

## Features & Highlights

* **Modern Build System.** CMake replaces Makefiles. Works clean on modern Linux, macOS, and BSD with automated setup.
* **100% Authentic Systems.** Over a dozen real systems integrated from original source. No rewrites, just restorations.
* **Complete K&R Modernization** Entire codebase converted to ANSI C; ~250 functions updated and prototyped. Completed Aug, 6 2025.
* **Fixed Unix/Linux Compatibility.** Resolved hardcoded BSD paths and file system issues for modern systems.
* **Playable 259KB Executable.** Tiny, tight, and true to the original with full save/load functionality.

> **Note:** Currently only tested on Arch Linux. While CMake enables portability, cross-platform build behavior has not yet been verified on macOS or BSD. Feedback and patches welcome.

---

## Installation

### Download Pre-built Release (Recommended)

**Running the Static Binary (Linux)**

A prebuilt static binary is available for Linux x86_64.

**1. Download the release tarball:**
[restoHack-static-20250808-linux-x86_64.tar.gz](https://github.com/Critlist/restoHack/releases/download/v1.0.2/restoHack-static-20250808-linux-x86_64.tar.gz)

**2. Move the tarball to a clean folder (recommended):**
```bash
mkdir -p ~/Games/restoHack
mv ~/Downloads/restoHack-static-20250808-linux-x86_64.tar.gz ~/Games/restoHack/
cd ~/Games/restoHack
```

**3. Extract the tarball:**
```bash
tar -xzf restoHack-static-20250808-linux-x86_64.tar.gz
```

**4. Run the Game:**
```bash
./run-hack.sh
```

The static binary runs on any Linux system without dependencies - no need to install ncurses or other libraries!

---

## Building from Source

**Requirements:** `git`, `cmake`, and a C compiler (`gcc` or `clang`). Plus `ncurses` or `termcap` library.

### Quick Start

```bash
# Clone the repo
git clone https://github.com/Critlist/restoHack.git
cd restoHack

# Build with CMake
mkdir build && cd build
cmake ..
cmake --build .

# Run the game (always from build directory)
./hack
```

### Clean Build

```bash
rm -rf build && mkdir build && cd build
cmake .. && cmake --build .
./hack
```

### Troubleshooting

**"Game in progress" error?**

```bash
rm -f hackdir/<username>.* hackdir/save/*  
./hack
```

**Lock file issues?**

```bash
cmake --build . --target clean-all
cmake --build .
./hack
```

**Missing libraries on Ubuntu/Debian:**

```bash
sudo apt install libncurses-dev cmake build-essential
```

**Missing libraries on macOS:**

```bash
brew install cmake
xcode-select --install
```

### Advanced Options

**Enable debugging/sanitizers:**

```bash
cmake -DENABLE_SANITIZERS=ON ..
cmake --build .
```

**Cross-platform notes:**

* Curses is detected automatically via CMake - no hardcoded termcap linking
* RNG seeding uses feature detection, preferring arc4random, srandomdev, or getentropy when available, falling back to time-based seed
* Linux: Uses `ncurses` (auto-detected)
* macOS: Uses system `ncurses`  
* NetBSD: Uses `libcurses` with delay_output support
* All platforms require POSIX-compatible system

---

## Recent Fixes & Improvements

### **Modern Locking System (v1.0.1)**

* **Fixed:** Replaced unreliable 1984 `link()`-based locking with modern [`flock()`](https://man7.org/linux/man-pages/man2/flock.2.html) system
* **Result:** Eliminates stale lock files, "game in progress" hangs, and filesystem compatibility issues
* **Benefit:** Automatic cleanup on process death - no more manual `rm hackdir/*` needed
* **Compatibility:** Preserves 100% authentic 1984 gameplay while providing modern reliability

### **NetBSD/pkgsrc Build Compatibility (v1.0.3)**

* **Fixed:** Build failures on NetBSD/pkgsrc due to curses library detection and RNG seeding
* **Result:** Universal build compatibility across Linux, NetBSD, macOS using feature detection
* **Technical:** Replaced OS-specific `#ifdef` with CMake feature detection, proper curses linking, resolved function name conflicts

### **Tombstone Display Fix**

* **Fixed:** Segfault in death screen (`hack.rip.c`) caused by buffer overflow in name centering
* **Result:** RIP screen now displays properly on all systems with any username length
* **Technical:** Updated read-only string literals to writable arrays for modern compiler compatibility

---

## Preservation Philosophy

restoHack balances historical authenticity with modern reliability. While committed to preserving the authentic 1984 gameplay experience, the project implements targeted fixes for issues that would prevent modern users from enjoying the game.

**Philosophy:** Fix what breaks, preserve what works. All modern additions are clearly documented and maintain 100% compatibility with original game mechanics, balance, and feel. No modern game features have been added - only infrastructure improvements for contemporary systems.

---

## Gameplay

Hack is a classic terminal roguelike. You’re the `@`, out to snatch the Amulet of Yendor from the Mazes of Menace. Expect monsters, magic, inventory micromanagement, and permadeath. Movement is `hjkl` (Vi), commands are arcane, and survival is unlikely.

And yes, it’s meant to be that way.

---

## Project Goals

* Build a Fully Playable Hack. All original systems integrated, no rewrites.
* Preserve the Code, Not Rewrite It. K\&R syntax cleaned, logic untouched.
* Keep the Terminal Sacred. No GUI. No fluff. Just pure ASCII.

---

## Project Status: Mission Accomplished

### Core Game Systems (100% Complete)

* Character creation (Tourist, Wizard, Fighter, Caveman, etc.)
* Full inventory and object systems with authentic item generation
* Equipment and armor tracking with cursed/blessed mechanics
* Terminal display and control with full termcap support
* Dungeon and level generation with maze algorithms
* Message system and UI with authentic "More--" paging
* Save/load system with proper exit handling
* Combat system with authentic damage calculations
* Monster AI including pets, shopkeepers, and guards
* Magic system with potions, scrolls, and wands
* Shop system with authentic billing mechanics

### Technical Achievements (100% Complete)

* Complete K\&R to ANSI C conversion (entire codebase modernized; approx. 230–260 functions updated)
* Perfect build system with CMake replacing vintage Makefiles
* Modern signal handling for common Unix window environments (Hyprland, Wayland, X11). Note: no known issues here, but see the lock file section for edge-case process death behavior.
* Memory safety with proper cleanup routines Issues" for details on edge-case failures and suggested workarounds.

### Gameplay Status

**Fully Playable and Stable**

* Start as any character class → Explore procedural dungeons → Fight monsters → Collect treasure → Save and resume → Die gloriously in authentic ASCII
* Thoroughly tested. Rock-solid stability.
* 100% Authentic. Complete original 1984 code preserved, only syntax modernized.
* Performance optimized. Efficient execution on modern hardware.

---

## Contributing

Bug fixes, portability patches, build improvements, packaging help — all welcome. Want to port it to Plan 9? Go nuts. Just respect the code.

Open issues. Submit PRs. Document your non-original changes. That’s the rule.

---

## License

3-Clause BSD. Do what you want, just don’t sue us. See `LICENSE`.
