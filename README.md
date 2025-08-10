# restoHack: Bringing 1984 Hack Back from the Dead

**restoHack** is a full-blooded resurrection of *Hack*, the 1984 roguelike that spawned *NetHack*.
Not a remake. Not a reboot. This is *software preservation with a blowtorch and a scalpel*.

The goal: make the original code compile, run, and dungeon-crawl exactly as it did when floppy was King.

Think resto-mod: the soul stays vintage, the internals get a precision rebuild.

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

your choice of helper

```bash
yay -S restohack
```

```bash
paru -S restohack
```

### Prebuilt Static Binary (Linux)

```bash
mkdir -p ~/Games/restoHack
mv ~/Downloads/restoHack-static-20250808-linux-x86_64.tar.gz ~/Games/restoHack/
cd ~/Games/restoHack
tar -xzf restoHack-static-20250808-linux-x86_64.tar.gz
./run-hack.sh
```

Runs anywhere—no ncurses or extra libs needed.

---

## Building from Source

**Requirements:** `git`, `cmake`, a C compiler (`gcc` or `clang`), plus `ncurses` or `termcap`.

### Standard Source Build (Release)

The default method for a stable, optimized build:

```bash
git clone https://github.com/Critlist/restoHack.git
cd restoHack
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .
./hack
```

### Development Build (Debug)

For hacking on the code, with debug symbols and optional sanitizers:

```bash
git clone https://github.com/Critlist/restoHack.git
cd restoHack
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
cmake --build .
./hack
```

### Clean Rebuild

Wipes prior build artifacts before rebuilding:

```bash
rm -rf build && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .
./hack
```


---

## Recent Fixes

* **Modern Locking** – Replaced `link()` locks with `flock()` for clean recovery.
* **NetBSD/pkgsrc Builds** – Fixed curses detection and RNG seeding via CMake feature checks.
* **Tombstone Crash** – Fixed segfault in RIP screen by patching buffer overflow in name centering.

---

## Preservation Philosophy

Fix what breaks, preserve what works. The original 1984 gameplay, balance, and feel remain untouched—only the infrastructure has been made reliable for modern systems.

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
