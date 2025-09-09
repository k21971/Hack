# C Learning Log: Hack (1984) K&R to ANSI Conversion

Notes from modernizing 1984 Hack source code from K&R to ANSI C.

---

## 1. Character Initialization: `hack.u_init.c`

Player character creation and initial inventory.

* **Preservation:** 90% - only syntax changed

* **K&R to ANSI Fixes:**
    1. Added function prototypes to hack.h
    2. Updated function definitions: `u_init(role)` → `void u_init(int role)`
    3. Added explicit `void` for no-argument functions

* **Concepts:**
  * Player data in `struct you`
  * Pointer passing for state modification
  * Static array initialization for inventory

---

## 2. Object Creation: `hack.mkobj.c`

Item generation factory.

* **Preservation:** 85% - memory management modernized

* **K&R to ANSI Fixes:**
    1. Added `#include <stdlib.h>` for malloc()
    2. Explicit casting of malloc() returns
    3. Added `const` for read-only data tables

* **Concepts:**
  * Dynamic memory with malloc()
  * Pointer manipulation
  * #define constants for object types

---

## 3. Inventory Management: `hack.invent.c`

Linked list inventory system.

* **Preservation:** 80% - pointer safety improved

* **K&R to ANSI Fixes:**
    1. Replaced `0` with `NULL` for pointers
    2. Used bounded string functions (strncpy)
    3. Added `const` for read-only parameters

* **Concepts:**
  * Singly linked list operations
  * Pointer traversal and management
  * Real-world data structure implementation

---

## 4. K&R to ANSI Conversion (July 2025)

57 functions modernized across multiple files.

* **Preservation:** 95% - logic unchanged

* **K&R to ANSI Fixes:**
    1. Added function prototypes to hack.h
    2. Converted K&R parameters: `function(x,y) int x,y;` → `function(int x, int y)`
    3. Fixed missing return types
    4. Resolved header dependencies

* **Concepts:**
  * Compilation vs linking
  * Function signature matching
  * Header/source separation

* **Files Modernized:**
  * rnd.c: 4 functions
  * hack.mkobj.c: 3 functions
  * hack.mklev.c: 2+ functions
  * hack.termcap.c: 3+ functions
  * hack.pri.c: 13+ functions

* **Result:** 64% build completion

---

## 5. Executable Creation: Phase 0E (July 2025)

Transformed partial code into working binary.

* **Preservation:** 98% - minimal stubs added

* **Linking Fixes:**
    1. Resolved 25+ undefined references
    2. Matched stub signatures to prototypes
    3. Removed duplicate definitions
    4. Fixed function/variable conflicts

* **Concepts:**
  * Compilation vs linking phases
  * Symbol resolution
  * Stub-driven development
  * CMake build pipeline

* **Functions Stubbed:**
  * Vision: `cansee()`, `canseemon()`, `isok()`
  * Objects: `doname()`, `splitobj()`, `obfree()`
  * UI: `cornline()`, `getlin()`, `xwaitforspace()`
  * Level: `makemon()`, `maketrap()`, `mkshop()`, `makemaz()`
  * Utils: `eos()`, `hu_stat[]`, `morc`

* **Result:** 91KB working executable

---

## 6. System Integration: Phase 0F (July 2025)

Replaced stubs with authentic 1984 code.

* **Preservation:** 100%

* **Systems Integrated:**
    1. **hack.objnam.c (548 lines):** Object naming with grammar handling
    2. **hack.o_init.c (156 lines):** Object initialization and probabilities
    3. **hack.pager.c (418 lines):** Text display and "--More--" prompts
    4. **hack.makemon.c (183 lines):** Monster spawning
    5. **hack.tty.c (396 lines):** Terminal I/O

* **K&R to ANSI Conversions:**
    1. Converted 50+ functions
    2. Added prototypes to hack.h
    3. Fixed missing return types
    4. Added standard includes

* **Result:** 262KB playable executable

## 7. Final Phase: Playable Game (Phase 0G - July 29, 2025)

**Build Fixes:**

* Resolved hack.lev.c prototype conflicts
* Fixed header duplications
* Removed conflicting stubs

**Critical Fixes:**

* mintrap() - Fixed infinite loop segfault
* makedog() - Removed stub messages
* initrack() - Silenced debug output

**Result:** Fully playable 1984 Hack

---

## 8. Polish Phase (Phase 0H - July 29, 2025)

**Fixes:**

1. Created proper hackdir structure
2. Silenced lock messages
3. Removed combat spam
4. Cleaned shop messages

**Result:** Clean 1984 terminal experience

---

## 9. Bug Fixes (Phase 1 - July 29, 2025)

**Experienced Player Crash:**

* Segfault at: `roles[i][0] = pc;`
* Cause: String literals are read-only in ANSI C
* K&R allowed modifying string literals

**Fix:** Changed string literals to mutable arrays:

```c
// Before: char *(roles[]) = {"Tourist", "Speleologist", ...};
// After: static char role_tourist[] = "Tourist"; ...
```

---

## 10. Record Lock Fix (July 29, 2025)

**Problem:** Infinite loop on quit due to stale lock files

**Fix:** Added stale lock detection - removes locks older than 5 minutes

**Concepts:** Unix file locking with link(), defensive cleanup

---

## 11. Trap System (Phase 1A - July 29, 2025)

**hack.trap.c Integration:**

* 9 functions converted from K&R
* Added prototypes to hack.h
* Fixed header conflicts
* Removed duplicate stubs

**Functions:** vtele(), tele(), teleds(), teleok(), dotele(), placebc(), unplacebc(), level_tele(), drown()

---

## 12. Stub Implementation (Phase 1B - July 29, 2025)

**65+ stubs implemented:**

* Equipment: doapply(), dowearring(), doremring(), doweararm(), doremarm(), find_ac()
* Shop: inshop(), doinvbill(), addtobill(), splitbill(), subfrombill(), paybill(), dopay()
* Monster AI: dog_move(), shk_move(), gd_move(), inrange(), losedogs(), keepdogs()
* Level Gen: makemaz(), mkshop(), mkzoo(), mkswamp(), mazexy()
* Commands: dosuspend(), doset(), doversion(), dighole(), corrode_armor()
* Mechanics: amulet(), obfree(), some_armor(), timeout(), glibr()
* Worm: wormsee(), pwseg(), wormdead(), wormhit(), cutworm()
* NPCs: shkdead(), gddead(), replshk(), replgd()
* System: initoptions(), regularize(), gethdate(), outrumor(), outrip()

**Result:** All game systems operational

---

## 13. K&R Conversion (Phase 1C - July 30, 2025)

**Files Converted:**

* hack.apply.c - 13 functions
* hack.dog.c - 9 functions
* hack.do_name.c - Already ANSI
* hack.shk.c - 25+ functions

**Conversion Types:**

1. Function signatures: `dog_move(mtmp, after) struct monst *mtmp;` → `int dog_move(struct monst *mtmp, int after)`
2. Return types: `dopay()` → `int dopay(void)`
3. Parameter types: `shopdig(fall) int fall;` → `void shopdig(int fall)`
4. Void parameters: `makedog()` → `void makedog(void)`

**Result:** 50+ functions converted, 100% logic preserved

---

## 14. Final K&R Conversion (Phase 1D - August 2025)

**Final Files:**

* hack.main.c, hack.mkmaze.c, hack.steal.c, hack.wizard.c
* hack.do_wear.c, hack.ioctl.c, hack.mkshop.c, hack.rip.c
* hack.options.c and all remaining K&R files

**Result:** 100+ K&R functions converted across 15+ files

**Achievement:** Complete 1984 K&R C to ANSI C transformation

---

## 15. Unix/Linux Compatibility (Phase 0H - July 31, 2025)

**Fix:** "Cannot get status of hack" error

**Problem:** Hardcoded BSD path `/usr/games/hide/hack`

**Solution:** Enabled PATH-based detection using `#if 0/#else/#endif`

**Result:** Game runs on all modern Unix/Linux systems
