# restoHack: Bringing 1984 Hack Back from the Dead

**restoHack** is a full-blooded resurrection of *Hack*, the 1984 roguelike that spawned *NetHack*.
Not a remake. Not a reboot. This is *software preservation with a blowtorch and a scalpel*.

The goal: make the original code compile, run, and dungeon-crawl exactly as it did when floppy was King.

Think resto-mod: the soul stays vintage, the internals get a precision rebuild.

**Philosophy**: "Fix what breaks, preserve what works" - authentic 1984 gameplay with modern build system and safety improvements.

📜 **[Read the Complete History of Hack →](docs/HISTORY_OF_HACK.md)**  
*From Rogue (1980) to NetHack's rise, through decades of digital decay, to restoHack's 2025 resurrection*

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

## Features

* **Modern Build System** – CMake replaces Makefiles. Clean builds on Linux, FreeBSD, and other Unix systems.
* **Authentic Systems** – Over a dozen original systems restored from source, untouched in design.
* **Complete K\&R Modernization** – Entire codebase converted to ANSI C (\~250 functions updated).
* **Unix/Linux Fixes** – No more hardcoded BSD paths or FS quirks.
* **Cross-Platform Verified** – Works on Linux (glibc/musl) & FreeBSD; CI-tested.
* **Tiny Executable** – 479KB of pure roguelike, with save/load intact.

> **Tested on:** Arch, Alpine, FreeBSD 14.2.
> macOS support pending. Arch users can install via the AUR.

---

## Installation

### Arch Linux (AUR)

```bash
yay -S restohack
```

### Hybrid Binary+Source Tarball

Download from [Releases](https://github.com/Critlist/restoHack/releases) and extract:

```bash
mkdir -p ~/Games/restohack
cd ~/Games/restohack
tar -xzf restoHack-static-YYYYMMDD-linux-x86_64.tar.gz
```

## Install & Build

**Requirements:** `git`, `cmake`, a C compiler, `ncurses`

```bash
git clone https://github.com/Critlist/restoHack.git
cd restoHack
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/hack
```

**Alternative** (if your system supports CMake presets):

```bash
cmake --preset=release && cmake --build build
```

---

## Quick Demo (Linux)

If you just want to try it immediately without building from source:

```bash
./run-hack.sh
```

*(static binary, no dependencies required)*

**For BSD systems, development builds, IDE integration, and troubleshooting:** see [**📋 Build Instructions**](docs/BUILD.md)

---

## Work in Progress

**Current Development: v1.1 - Hardening and Safety**

The current work-in-progress focuses on introducing comprehensive hardening and safety parameters that the original 1984 code lacked. This version emphasizes stability improvements including:

* Enhanced memory safety and bounds checking
* Improved error handling and recovery mechanisms  
* Compiler warning elimination and code hardening
* Environment-specific adaptations for varying systems
* Robust input validation and sanitization

⚠️ **RELAX, MAN, IT COMPILES!**  
This was the guiding philosophy of 1984. While undoubtedly brilliant, the original *Hack* was held together with duct tape, raw `struct` dumps, and a healthy dose of ’80s-era K&R magic.  
Stability was a suggestion, not a guarantee.

* Version **1.1** looks to fix that: modern hardening, memory safety, and input validation — while keeping the authentic 1984 gameplay intact.

---

## Recent Fixes

* **Modern Locking** – Replaced `link()` locks with `flock()` for clean recovery.
* **NetBSD/pkgsrc Builds** – Fixed curses detection and RNG seeding via CMake feature checks.
* **Tombstone Crash** – Fixed segfault in RIP screen by patching buffer overflow in name centering.

---

## Preservation Philosophy

Fix what breaks, preserve what works. The original 1984 gameplay, balance, and feel remain untouched—only the infrastructure has been made reliable for modern systems.

---

## Source Code Provenance

### Authenticity and Chain of Custody

**restoHack** is built from **verified original source code** with complete provenance documentation:

#### **Primary Source: FreeBSD 4.10 Games Collection**

The original 1984 Hack source code was preserved in the FreeBSD games collection, which maintained Andries Brouwer's final **Hack 1.0.3** release from 1985. This represents the canonical version of historical Hack.

#### **Source Recovery Process**

Our preservation methodology ensures authenticity:

* **Automated retrieval**: [`docs/historical/original-source/download_hack.sh`](docs/historical/original-source/download_hack.sh)

* **Documentation**: Complete chain of custody from 1984 → FreeBSD → restoHack
* **Integrity**: Every original file preserved unchanged in `docs/historical/original-source/`

#### **Modernization Documentation**

Every change from the original 1984 code is meticulously documented:

```c
/**
 * MODERN ADDITION (2025): Brief description
 * WHY: Problem being solved
 * HOW: Technical implementation
 * PRESERVES: Original 1984 behavior maintained
 * ADDS: Modern functionality provided
 */
```

### Historical Context

Hack 1.0.3 represents:

* **Andries Brouwer's masterpiece**: The mathematical peak of 1980s roguelike design
* **The bridge**: Between Rogue's simplicity and NetHack's complexity
* **Software archaeology**: A preserved artifact of computing history
* **Gaming heritage**: The foundation of an entire genre

For the complete story of Hack's creation, evolution, abandonment, and resurrection, see **[The Complete History of Hack](docs/HISTORY_OF_HACK.md)**.

---

## Gameplay

You’re the `@`, diving into the Mazes of Menace to steal the Amulet of Yendor.
Expect monsters, magic, cursed loot, and permadeath. Controls are Vi-style (`hjkl`). Survival is… unlikely.

---

## Contributing

Bug fixes, portability patches, packaging help—welcome.
Want to port to Plan 9? Go for it. Just document changes and respect the code.

---

## License

3-Clause BSD. Do what you want, just don’t sue us. See `LICENSE`.
