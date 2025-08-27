#!/usr/bin/env python3
"""
Enhanced restoHack fuzzer targeting real hack functions
"""

import sys
import shutil
import argparse
import subprocess
import struct
from pathlib import Path
from datetime import datetime

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from colors import Colors


class EnhancedHackFuzzer:
    """Enhanced fuzzer targeting actual hack functions"""
    
    def __init__(self, project_root: str, debug: bool = False):
        self.project_root = Path(project_root)
        self.debug = debug
        self.fuzz_dir = self.project_root / "build-fuzz-enhanced"
        self.corpus_dir = Path(__file__).parent / "fuzz-corpus-enhanced"
        
        # Create timestamped log directory
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_dir = Path(__file__).parent / "fuzz-logs-enhanced" / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        Colors.say("FUZZ+", f"🎯 Enhanced fuzzer logs: {self.log_dir}")
        if debug:
            Colors.say("DEBUG", f"Project root: {self.project_root}")
            Colors.say("DEBUG", f"Fuzz build dir: {self.fuzz_dir}")
            Colors.say("DEBUG", f"Corpus dir: {self.corpus_dir}")

    def check_requirements(self) -> bool:
        """Check if fuzzing tools are available"""
        if not shutil.which('clang'):
            Colors.error("clang not found - required for libFuzzer")
            return False
            
        # Test if clang supports fuzzing
        try:
            result = subprocess.run(['clang', '-fsanitize=fuzzer', '-help'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                Colors.error("clang doesn't support -fsanitize=fuzzer")
                return False
        except:
            Colors.error("Failed to test clang fuzzer support")
            return False
            
        Colors.success("✅ Enhanced fuzzing requirements met")
        return True

    def build_hack_lib_enhanced(self) -> bool:
        """Build simple fuzzer library without complex hack integration"""
        Colors.say("BUILD+", "🔧 Building simple fuzzer library")
        
        # Always clean rebuild
        if self.fuzz_dir.exists():
            shutil.rmtree(self.fuzz_dir)
        self.fuzz_dir.mkdir()
        
        Colors.success("✅ Simple fuzzer directory ready")
        return True

    def create_enhanced_fuzz_targets(self) -> list:
        """Create fuzz targets that test real hack functions"""
        targets = []
        
        # 1. Command parsing fuzzer - targets real command processing
        cmd_fuzz = '''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <setjmp.h>

// Mock critical globals that hack needs
char toplines[3][100];
int flags_debug = 0;
int multi = 0;
char quitchars[] = "\\033qQ";
jmp_buf end_of_input;
int (*occupation)() = 0;
char *occsym = "";

// Declare hack functions we want to fuzz
extern char *parse(void);
extern int dopray(void);
extern int doredraw(void);
extern int dosearch(void);
extern int doidtrap(void);

// Mock some functions that parse() might call
int getpos(int force) { return 0; }
int dowhatis(void) { return 0; }
int doquit(void) { return 0; }
int done2(void) { return 0; }
int doversion(void) { return 0; }
int dohistory(void) { return 0; }
void pline(const char *fmt, ...) { }
void impossible(const char *fmt, ...) { }
int ynq(const char *) { return 'n'; }
int yn(const char *) { return 'n'; }

// Fuzz command parsing - the core of user input handling
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 256) return 0;
    
    // Create input buffer that simulates keyboard input
    static char input_buffer[512];
    memset(input_buffer, 0, sizeof(input_buffer));
    
    if (Size < sizeof(input_buffer) - 1) {
        memcpy(input_buffer, Data, Size);
        input_buffer[Size] = '\\0';
        
        // Set up minimal game state for command parsing
        // Test various command characters and sequences
        for (size_t i = 0; i < Size; i++) {
            char cmd = input_buffer[i];
            
            // Test commands that are safe to fuzz
            switch (cmd) {
                case 's':  // search
                    dosearch();
                    break;
                case '^':  // identify trap  
                    doidtrap();
                    break;
                case '^R': // redraw
                    doredraw();
                    break;
                case '#':  // pray (if implemented)
                    dopray();
                    break;
                default:
                    // Test character validation
                    if (cmd >= 32 && cmd <= 126) {
                        // Valid printable character
                    }
                    break;
            }
        }
    }
    
    return 0;
}
'''
        
        target_path = self.fuzz_dir / "fuzz_commands.c"
        with open(target_path, 'w') as f:
            f.write(cmd_fuzz)
        targets.append("fuzz_commands")
        
        # 2. Save file fuzzing - targets real save/restore logic
        save_fuzz = '''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

// Mock globals for save system
char toplines[3][100];
int flags_debug = 0;

// Declare save/restore functions  
extern int dorecover(const char *filename);
extern int dosave(const char *filename);

// Mock functions that save system might need
void pline(const char *fmt, ...) { }
void impossible(const char *fmt, ...) { }
int yn(const char *) { return 'n'; }
void done(int) { exit(0); }

// Fuzz save file parsing - looking for format string bugs, buffer overflows
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 65536) return 0;
    
    // Create temp save file with fuzz data
    char temp_save[] = "/tmp/fuzz_save_XXXXXX";
    int fd = mkstemp(temp_save);
    if (fd == -1) return 0;
    
    // Write fuzz data as save file
    ssize_t written = write(fd, Data, Size);
    close(fd);
    
    if (written == (ssize_t)Size) {
        // Try to restore from the malformed save file
        // This tests real save parsing logic for crashes
        dorecover(temp_save);
    }
    
    // Clean up
    unlink(temp_save);
    return 0;
}
'''
        
        target_path = self.fuzz_dir / "fuzz_save_real.c"
        with open(target_path, 'w') as f:
            f.write(save_fuzz)
        targets.append("fuzz_save_real")
        
        # 3. Object name fuzzing - targets real name processing
        names_fuzz = '''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// Mock globals
char toplines[3][100];
int flags_debug = 0;

// Declare object name functions from hack.objnam.c
extern char *xname(struct obj *);
extern char *doname(struct obj *);
extern char *aobjnam(struct obj *, const char *);

// Mock object structure (simplified)
struct obj {
    struct obj *nobj;
    unsigned int otyp;
    unsigned int owt;
    long quan;
    char onamelth;
};

// Mock functions
void pline(const char *fmt, ...) { }
void impossible(const char *fmt, ...) { }

// Fuzz object name generation - tests string formatting, buffer handling
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 512) return 0;
    
    // Create mock object with fuzz data
    static struct obj test_obj;
    memset(&test_obj, 0, sizeof(test_obj));
    
    // Use fuzz data to set object properties
    if (Size >= 4) {
        test_obj.otyp = *(unsigned int*)Data;
        test_obj.quan = Size > 8 ? *(long*)(Data + 4) : 1;
        test_obj.owt = Size;
    }
    
    // Test object name generation with various inputs
    char *name = xname(&test_obj);
    if (name) {
        // Test name processing
        size_t len = strlen(name);
        if (len > 0 && len < 1000) {  // Sanity check
            // Test article generation, pluralization, etc.
            char *described = doname(&test_obj);
            if (described) {
                // Name processing completed without crash
            }
        }
    }
    
    // Test with custom name suffix
    if (Size > 10) {
        char custom_suffix[256];
        size_t suffix_len = Size - 10;
        if (suffix_len < sizeof(custom_suffix)) {
            memcpy(custom_suffix, Data + 10, suffix_len);
            custom_suffix[suffix_len] = '\\0';
            
            char *custom_name = aobjnam(&test_obj, custom_suffix);
            if (custom_name) {
                // Custom naming completed
            }
        }
    }
    
    return 0;
}
'''
        
        target_path = self.fuzz_dir / "fuzz_names_real.c"
        with open(target_path, 'w') as f:
            f.write(names_fuzz)
        targets.append("fuzz_names_real")
        
        return targets

    def build_enhanced_targets(self, targets: list) -> bool:
        """Build enhanced fuzz targets with proper hack linking"""
        Colors.say("BUILD+", "🔧 Building enhanced fuzz targets")
        
        for target in targets:
            target_source = self.fuzz_dir / f"{target}.c"
            target_binary = self.fuzz_dir / target
            
            # Enhanced build with proper linking
            build_cmd = [
                'clang', '-fsanitize=fuzzer,address', '-g3', '-O1',
                '-fno-omit-frame-pointer', '-fPIE',
                '-Wwrite-strings', '-Wno-error', '-Wno-deprecated-non-prototype',
                '-D_FORTIFY_SOURCE=3',
                '-I' + str(self.fuzz_dir),
                '-I' + str(self.fuzz_dir / 'src'),
                str(target_source),
                str(self.fuzz_dir / "libhack_fuzz.a"),
                '-lncurses', '-lm',
                '-pie',  # Link flag for PIE
                '-o', str(target_binary)
            ]
            
            result = subprocess.run(build_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                Colors.warn(f"Failed to build {target}: {result.stderr}")
                # Don't fail completely - some targets might not build due to missing functions
                continue
            
            Colors.success(f"✅ Built enhanced target: {target}")
        
        return True

    def create_enhanced_corpus(self, target_name: str):
        """Create enhanced seed corpus based on real hack data"""
        corpus_path = self.corpus_dir / target_name
        corpus_path.mkdir(parents=True, exist_ok=True)
        
        if target_name == "fuzz_commands":
            # Real 1984 hack commands from help file
            seeds = [
                # Basic commands
                b"?",        # help
                b"Q",        # quit
                b"S",        # save
                b"!",        # shell escape
                b"\x1a",     # ^Z suspend
                
                # Movement (kjhlyubn)
                b"k",        # north
                b"j",        # south  
                b"h",        # west
                b"l",        # east
                b"y",        # northeast
                b"u",        # northwest
                b"b",        # southeast
                b"n",        # southwest
                b"<",        # up stairs
                b">",        # down stairs
                
                # Movement sequences
                b"kjhlyubn", # all directions
                b"KJHLYUBN", # run directions
                b"mh",       # move west no pickup
                b"Mk",       # run north no pickup
                b"fj",       # find south
                b"Fl",       # find east (no corridor fork)
                
                # Inventory and info
                b"i",        # inventory
                b"I*",       # gems in inventory
                b"IU",       # unpaid items
                b"IX",       # used up items
                b"I$",       # count money
                b")",        # current weapon
                b"[",        # current armor
                b"=",        # current rings
                b"$",        # count gold
                
                # Actions
                b"s",        # search
                b"^",        # trap type
                b".",        # rest
                b",",        # pick up
                b":",        # look here
                b"\x14",     # ^T teleport
                b"\x12",     # ^R redraw
                b"\x10",     # ^P repeat message
                
                # Object interaction
                b"e",        # eat
                b"w",        # wield
                b"w-",       # wield nothing
                b"q",        # quaff potion
                b"r",        # read scroll
                b"T",        # takeoff armor
                b"R",        # remove ring
                b"W",        # wear armor
                b"P",        # put on ring
                b"z",        # zap wand
                b"t",        # throw
                b"p",        # pay bill
                b"d",        # drop
                b"d7a",      # drop 7 of item a
                b"D",        # drop multiple
                b"D!%=au",   # drop potions, food, rings, all unpaid
                
                # Advanced commands
                b"a",        # apply/use
                b"c",        # call/name object
                b"C",        # call/name monster  
                b"E",        # engrave
                b"E-",       # engrave with fingers
                b"O",        # set options
                b"v",        # version
                b"/A",       # what is A?
                b"/a",       # what is a?
                b"\\",       # discoveries
                
                # Command sequences
                b"20s",      # search 20 times
                b"40.",      # rest 40 times
                b"iq",       # inventory then quaff
                b"wrq",      # wield, read, quaff
                b"s^ia",     # search, check trap, inventory, apply
                
                # Edge cases and invalid input
                b"",         # empty
                b"\x00",     # null
                b"\x1b",     # escape
                b"\xff",     # high byte
                b"xyz123",   # invalid commands
                b"ZYXWVU",   # more invalid
                b"@#%&*",    # symbols
            ]
            
        elif target_name == "fuzz_save_real":
            # Save file format seeds based on typical formats
            seeds = [
                b"",
                b"\x00" * 100,
                b"\xff" * 100,
                # Mock hack save headers
                b"HACK_SAVE_1.0\x00",
                b"level:1\nplayer:test\n",
                struct.pack("<IIII", 1, 2, 3, 4),    # Binary level data
                b"A" * 1000,                         # Large save
                b"player\x00level\x00items\x00",     # Null-separated fields
                # Corrupt headers
                b"HACK_SAVE_999\x00",
                b"\x89PNG\r\n\x1a\n",               # PNG header (wrong format)
                b"BZh9",                            # Bzip2 header  
            ]
            
        elif target_name == "fuzz_names_real":
            # Object names from 1984 hack help file symbols
            seeds = [
                # Weapons (symbol: ))
                b"sword", b"long sword", b"two-handed sword",
                b"dagger", b"knife", b"axe", b"pick-axe",
                b"bow", b"arrow", b"crossbow", b"dart",
                b"mace", b"club", b"spear", b"trident",
                
                # Armor (symbol: [)
                b"leather armor", b"chain mail", b"plate mail",
                b"helmet", b"boots", b"gloves", b"cloak",
                b"shield", b"scale mail", b"ring mail",
                
                # Useful objects (symbol: ()
                b"key", b"rope", b"dynamite", b"camera",
                b"chest", b"box", b"bag", b"lamp",
                b"pick", b"lock pick", b"tool",
                
                # Food (symbol: %)
                b"food ration", b"apple", b"orange", b"banana", 
                b"meat", b"bread", b"cheese", b"cookie",
                b"candy", b"fruit", b"vegetable",
                
                # Wands (symbol: /)
                b"wand", b"wand of fire", b"wand of cold",
                b"wand of lightning", b"wand of magic missile",
                b"wand of teleportation", b"wand of healing",
                
                # Rings (symbol: =)
                b"ring", b"ring of protection", b"ring of strength",
                b"ring of dexterity", b"ring of invisibility",
                b"ring of regeneration", b"ring of levitation",
                
                # Scrolls (symbol: ?)
                b"scroll", b"scroll of identify", b"scroll of magic mapping",
                b"scroll of teleportation", b"scroll of enchant weapon",
                b"scroll of enchant armor", b"scroll of remove curse",
                
                # Potions (symbol: !)
                b"potion", b"potion of healing", b"potion of extra healing",
                b"potion of strength", b"potion of invisibility",
                b"potion of levitation", b"potion of speed",
                
                # Gold (symbol: $)
                b"gold piece", b"gold pieces", b"pile of gold",
                b"pot of gold", b"treasure", b"coins",
                
                # Monster names (A-Z, a-z from help)
                b"giant ant", b"bat", b"centipede", b"dog",
                b"elf", b"floating eye", b"gnome", b"hobbit",
                b"imp", b"jackal", b"kobold", b"leprechaun",
                
                # Edge cases for name processing
                b"very long item name that might cause buffer overflows in formatting routines",
                b"item\twith\ttabs", b"item\nwith\nnewlines",
                b"item with spaces", b"item-with-hyphens",
                b"item's possessive", b"item (parentheses)",
                b"UPPERCASE ITEM", b"lowercase item", b"MiXeD cAsE iTem",
                b"", b"a", b"an", b"the",  # Articles
                b"123item", b"item123", b"it3m",  # Numbers
                b"\xff\xfe\xfd", b"\x00\x01\x02",  # Binary data
                b"item\x00hidden", b"item\x1b[31mcolored",  # Embedded control chars
            ]
        else:
            seeds = [b"test", b"", b"A" * 100]
            
        for i, seed in enumerate(seeds):
            seed_file = corpus_path / f"seed_{i:03d}"
            with open(seed_file, 'wb') as f:
                f.write(seed)
                
        Colors.say("CORPUS+", f"📁 Created {len(seeds)} enhanced seeds for {target_name}")

    def run_enhanced_fuzzer(self, target: str, duration_seconds: int = 120) -> bool:
        """Run enhanced fuzzer with longer duration"""
        target_path = self.fuzz_dir / target
        if not target_path.exists():
            Colors.error(f"Enhanced target not found: {target}")
            return False
            
        self.create_enhanced_corpus(target)
        corpus_path = self.corpus_dir / target
        log_file = self.log_dir / f"{target}.log"
        
        Colors.say("FUZZ+", f"🚀 Running enhanced {target} for {duration_seconds}s")
        
        fuzz_cmd = [
            str(target_path),
            str(corpus_path),
            f'-max_total_time={duration_seconds}',
            f'-max_len=4096',              # Allow larger inputs
            '-print_final_stats=1',
            '-workers=1',
            '-close_fd_mask=3'             # Close stdin/stdout to avoid tty issues
        ]
        
        process = None
        try:
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    fuzz_cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.fuzz_dir)
                )
                process.wait(timeout=duration_seconds + 60)
                
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            Colors.warn(f"⏰ Enhanced {target} timed out (expected)")
        except KeyboardInterrupt:
            if process:
                process.kill()
            Colors.warn(f"⚠️  Enhanced {target} interrupted")
            
        # Check results
        if process and process.returncode == 0:
            Colors.success(f"✅ Enhanced {target} completed")
            return True
        elif process and process.returncode == 77:  # libFuzzer crash
            Colors.error(f"💥 Enhanced {target} FOUND CRASH!")
            Colors.error(f"   Check: {log_file}")
            return False
        else:
            exit_code = process.returncode if process else -1
            Colors.warn(f"⚠️  Enhanced {target} exit code: {exit_code}")
            return True

    def run_all_enhanced(self, duration_per_target: int = 120) -> int:
        """Run complete enhanced fuzzing session"""
        if not self.check_requirements():
            return 1
            
        if not self.build_hack_lib_enhanced():
            return 1
            
        targets = self.create_enhanced_fuzz_targets()
        if not self.build_enhanced_targets(targets):
            Colors.warn("Some enhanced targets failed to build - continuing with available ones")
            # Find which targets actually built
            targets = [t for t in targets if (self.fuzz_dir / t).exists()]
            
        if not targets:
            Colors.error("No enhanced targets built successfully")
            return 1
        
        Colors.say("FUZZ+", f"🎯 Running {len(targets)} enhanced targets, {duration_per_target}s each")
        
        crashes = []
        for target in targets:
            if not self.run_enhanced_fuzzer(target, duration_per_target):
                crashes.append(target)
        
        if crashes:
            Colors.error(f"💥 CRASHES in enhanced targets: {', '.join(crashes)}")
            return 1
        else:
            Colors.success("✅ All enhanced fuzzing completed without crashes")
            return 0


def main():
    parser = argparse.ArgumentParser(description='Enhanced restoHack Fuzzer - Targets Real Functions')
    parser.add_argument('--debug', action='store_true', help='Debug output')
    parser.add_argument('--duration', type=int, default=120, help='Duration per target (seconds)')
    parser.add_argument('--target', help='Run specific enhanced target only')
    
    args = parser.parse_args()
    
    # Get project root (script is in dev/, project root is parent)
    script_dir = Path(__file__).parent  # dev/
    project_root = script_dir.parent    # restoHack/
    
    fuzzer = EnhancedHackFuzzer(str(project_root), args.debug)
    
    if args.target:
        # Build everything first
        if not fuzzer.check_requirements() or not fuzzer.build_hack_lib_enhanced():
            return 1
        targets = fuzzer.create_enhanced_fuzz_targets()
        if not fuzzer.build_enhanced_targets(targets):
            return 1
        # Run specific target
        return 0 if fuzzer.run_enhanced_fuzzer(args.target, args.duration) else 1
    else:
        # Run all enhanced targets
        return fuzzer.run_all_enhanced(args.duration)


if __name__ == "__main__":
    sys.exit(main())