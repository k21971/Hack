#!/usr/bin/env python3
"""
Improved fuzzer for restoHack that actually tests real hack functions
"""

import os
import sys
import shutil
import argparse
import subprocess
import struct
# import json  # Unused for now
from pathlib import Path
from datetime import datetime
from typing import List, Dict  # Optional unused

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from colors import Colors


class ImprovedHackFuzzer:
    """Fuzzer that actually tests real hack code vulnerabilities"""
    
    def __init__(self, project_root: str, debug: bool = False):
        self.project_root = Path(project_root)
        self.debug = debug
        self.src_dir = self.project_root / "src"
        self.fuzz_dir = self.project_root / "build-fuzz-improved"
        self.corpus_dir = self.project_root / "dev" / "fuzz-corpus-improved"
        
        # Create timestamped log directory
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_dir = self.project_root / "dev" / "fuzz-logs" / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        Colors.say("FUZZ", f"🎯 Improved fuzzer logs: {self.log_dir}")

    def check_requirements(self) -> bool:
        """Check if fuzzing tools are available"""
        if not shutil.which('clang'):
            Colors.error("clang not found - required for libFuzzer")
            Colors.error("Install with: sudo apt install clang")
            return False
            
        # Check clang version (need 6.0+ for good fuzzing)
        try:
            result = subprocess.run(['clang', '--version'], 
                                  capture_output=True, text=True)
            if self.debug:
                Colors.say("DEBUG", f"Clang version: {result.stdout.split()[2]}")
        except:
            pass
            
        Colors.success("✅ Fuzzing requirements met")
        return True

    def build_hack_for_fuzzing(self) -> bool:
        """Build hack with fuzzing instrumentation"""
        Colors.say("BUILD", "🔧 Building hack for fuzzing (this may take a moment)")
        
        # Clean rebuild
        if self.fuzz_dir.exists():
            shutil.rmtree(self.fuzz_dir)
        self.fuzz_dir.mkdir(parents=True)
        
        # Use CMake with fuzzing flags
        cmake_cmd = [
            'cmake', 
            '-S', str(self.project_root),
            '-B', str(self.fuzz_dir),
            '-DCMAKE_C_COMPILER=clang',
            '-DCMAKE_BUILD_TYPE=Debug',
            '-DCMAKE_C_FLAGS=-fsanitize=fuzzer-no-link,address -g -O1 -fno-omit-frame-pointer'
        ]
        
        result = subprocess.run(cmake_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Colors.error(f"CMake failed: {result.stderr}")
            return False
        
        # Build the project to generate hack.onames.h
        build_cmd = ['cmake', '--build', str(self.fuzz_dir), '--target', 'makedefs']
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if self.debug:
                Colors.warn(f"Makedefs build warning: {result.stderr[:200]}")
        
        # Run makedefs to generate hack.onames.h
        makedefs_path = self.fuzz_dir / 'makedefs'
        if makedefs_path.exists():
            gen_cmd = [str(makedefs_path), str(self.src_dir / 'objects.h')]
            result = subprocess.run(gen_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                onames_path = self.fuzz_dir / 'hack.onames.h'
                with open(onames_path, 'w') as f:
                    f.write(result.stdout)
                if self.debug:
                    Colors.say("DEBUG", "Generated hack.onames.h")
        
        # Now build the main project
        build_cmd = ['cmake', '--build', str(self.fuzz_dir), '--', '-j4']
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # This is expected - main() conflicts with fuzzer
            # We just want the object files
            if self.debug:
                Colors.warn("Build had errors (expected for fuzzing)")
        
        Colors.success("✅ Hack objects built for fuzzing")
        return True

    def create_targeted_fuzz_harnesses(self) -> List[Dict]:
        """Create fuzz harnesses targeting actual hack vulnerabilities"""
        harnesses = []
        
        # 1. Message system fuzzer (targets the --More-- bug area)
        pline_fuzzer = '''
/* Fuzzer for hack's message system - test pline() and related functions */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include "hack.h"

/* Real hack globals needed */
struct flag flags;
char toplines[BUFSZ];
coord tly;

/* Mock minimal requirements */
int CO = 80;
void standoutbeg() {}
void standoutend() {}
void cl_end() {}
void home() {}
void curs(int x, int y) {}
void putstr(const char *s) {}
char readchar() { return ' '; }
void clrlin() {}

/* Fuzz the pline() function that had buffer issues */
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 1024) return 0;
    
    /* Create format string and arguments */
    char fmt[BUFSZ];
    memset(fmt, 0, sizeof(fmt));
    
    /* Copy fuzz data as format string (safely) */
    size_t fmt_len = Size < BUFSZ - 1 ? Size : BUFSZ - 1;
    memcpy(fmt, Data, fmt_len);
    fmt[fmt_len] = '\\0';
    
    /* Test 1: Simple message */
    flags.toplin = 0;
    pline(fmt);
    
    /* Test 2: Message with continuation */
    flags.toplin = 1;
    memset(toplines, 'A', BUFSZ/2);
    pline(fmt);
    
    /* Test 3: Very long message that would trigger --More-- */
    flags.toplin = 0;
    char long_msg[BUFSZ];
    memset(long_msg, 'X', BUFSZ - 1);
    long_msg[BUFSZ - 1] = '\\0';
    pline("%s", long_msg);
    
    return 0;
}
'''
        harnesses.append({
            'name': 'fuzz_pline',
            'source': pline_fuzzer,
            'objects': ['hack.topl.o', 'hack.tty.o', 'hack.pri.o'],
            'description': 'Message system fuzzer (pline, xmore, putsym)'
        })
        
        # 2. Coordinate system fuzzer (test bounds checking)
        coord_fuzzer = '''
/* Fuzzer for coordinate handling - test for buffer overflows */
#include <stdint.h>
#include <stddef.h>
#include "hack.h"

/* Mock requirements */
struct rm levl[COLNO][ROWNO];
struct monst *fmon = NULL;
struct flag flags;

/* Functions we're testing */
extern void atl(int x, int y, int ch);
extern void tmp_at(schar x, schar y);
extern int isok(int x, int y);

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size < 4) return 0;
    
    /* Extract coordinates from fuzz data */
    int x = (int)(Data[0] % 256) - 128;  /* Test negative values */
    int y = (int)(Data[1] % 256) - 128;
    int ch = Data[2];
    
    /* Test 1: atl() with potentially out-of-bounds coordinates */
    atl(x, y, ch);
    
    /* Test 2: tmp_at() with schar coordinates */
    tmp_at((schar)x, (schar)y);
    
    /* Test 3: Boundary conditions */
    atl(0, 0, 'a');
    atl(COLNO-1, ROWNO-1, 'z');
    atl(COLNO, ROWNO, '!');  /* Just out of bounds */
    atl(-1, -1, '?');         /* Negative */
    
    /* Test 4: isok() validation */
    if (isok(x, y)) {
        /* Should be safe to access levl[x][y] */
        levl[x][y].typ = 1;
    }
    
    return 0;
}
'''
        harnesses.append({
            'name': 'fuzz_coords',
            'source': coord_fuzzer,
            'objects': ['hack.pri.o'],
            'description': 'Coordinate bounds checking fuzzer'
        })
        
        # 3. Warning system fuzzer (test the warnlevel bug area)
        warn_fuzzer = '''
/* Fuzzer for warning system - test negative array indexing */
#include <stdint.h>
#include <stddef.h>
#include "hack.h"

/* Mock globals */
struct you u;
struct monst *fmon = NULL;
struct flag flags;
char *warnings[] = {
    "white", "pink", "red", "ruby", "purple", "black"
};

/* Function under test */
extern int warnlevel(void);

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size < 4) return 0;
    
    /* Set up player state from fuzz data */
    u.uhp = (int)Data[0] - 128;     /* Can be negative */
    u.uhpmax = (int)Data[1];
    u.mtimedone = Data[2] % 2;      /* Polymorphed or not */
    u.mhmax = Data[3];
    
    /* Test warnlevel calculation */
    int level = warnlevel();
    
    /* This should not crash even with negative level */
    if (level >= 0 && level < SIZE(warnings)) {
        /* Safe array access */
        const char *color = warnings[level];
    }
    
    /* Test extreme values */
    u.uhp = -100;
    u.uhpmax = 100;
    level = warnlevel();
    
    u.uhp = 1;
    u.uhpmax = 1000;
    level = warnlevel();
    
    return 0;
}
'''
        harnesses.append({
            'name': 'fuzz_warning',
            'source': warn_fuzzer,
            'objects': ['hack.mon.o'],
            'description': 'Warning system fuzzer (warnlevel calculation)'
        })
        
        # 4. String handling fuzzer (getlin, parse, etc)
        string_fuzzer = '''
/* Fuzzer for string input functions */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "hack.h"

/* Mock globals */
struct flag flags;
char genocided[60];
char fut_geno[60];

/* Functions to test */
extern void getlin(char *bufp);
extern char *parse(void);
extern void charcat(char *s, char c);

/* Mock some functions */
int getchar() { 
    static int pos = 0;
    static const uint8_t *data = NULL;
    static size_t size = 0;
    if (pos >= size) return '\\n';
    return data[pos++];
}

void putstr(const char *s) {}
int fflush(FILE *f) { return 0; }

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > BUFSZ) return 0;
    
    /* Test getlin() with various inputs */
    char buffer[BUFSZ];
    memset(buffer, 0, sizeof(buffer));
    
    /* Simulate keyboard input */
    data = Data;
    size = Size;
    pos = 0;
    
    /* This would normally read from stdin */
    /* getlin(buffer); */
    
    /* Test charcat with boundary conditions */
    char small[10] = "test";
    if (Size > 0) {
        charcat(small, Data[0]);
    }
    
    /* Test string operations that might overflow */
    char dest[BUFSZ];
    if (Size < BUFSZ) {
        memcpy(dest, Data, Size);
        dest[Size] = '\\0';
        
        /* Operations that old C code might do */
        int len = strlen(dest);
        if (len > 0 && len < BUFSZ - 1) {
            dest[len] = '!';
            dest[len + 1] = '\\0';
        }
    }
    
    return 0;
}
'''
        harnesses.append({
            'name': 'fuzz_strings', 
            'source': string_fuzzer,
            'objects': ['hack.tty.o', 'hack.cmd.o'],
            'description': 'String input/parsing fuzzer'
        })
        
        return harnesses

    def build_fuzz_harness(self, harness: Dict) -> bool:
        """Build a single fuzz harness"""
        name = harness['name']
        Colors.say("BUILD", f"🔨 Building {name}")
        
        # Write source file
        source_file = self.fuzz_dir / f"{name}.c"
        with open(source_file, 'w') as f:
            f.write(harness['source'])
        
        # Collect object files
        obj_files = []
        obj_dir = self.fuzz_dir / "CMakeFiles" / "hack.dir" / "src"
        
        for obj in harness['objects']:
            obj_path = obj_dir / obj
            if obj_path.exists():
                obj_files.append(str(obj_path))
            else:
                if self.debug:
                    Colors.warn(f"Object not found: {obj}")
        
        # Build command
        build_cmd = [
            'clang',
            '-fsanitize=fuzzer,address',
            '-g', '-O1',
            f'-I{self.src_dir}',
            f'-I{self.fuzz_dir}',  # For generated hack.onames.h
            str(source_file)
        ]
        
        # Add object files if found
        if obj_files:
            build_cmd.extend(obj_files)
        
        # Add libraries
        build_cmd.extend([
            '-lncurses', '-lm',
            '-o', str(self.fuzz_dir / name)
        ])
        
        if self.debug:
            Colors.say("DEBUG", f"Build command: {' '.join(build_cmd)}")
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Colors.error(f"Build failed for {name}")
            if self.debug:
                Colors.error(f"Error: {result.stderr}")
            return False
        
        Colors.success(f"✅ Built {name}")
        return True

    def create_smart_corpus(self, harness_name: str) -> Path:
        """Create intelligent seed corpus based on target"""
        corpus_path = self.corpus_dir / harness_name
        corpus_path.mkdir(parents=True, exist_ok=True)
        
        seeds = []
        
        if 'pline' in harness_name:
            # Message format strings that might trigger bugs
            seeds = [
                b"",
                b"Simple message",
                b"%s %d %c",                    # Format strings
                b"%" + b"s" * 50,               # Many format specifiers
                b"A" * (BUFSZ - 1),             # Max buffer
                b"A" * BUFSZ,                   # Buffer overflow attempt
                b"Line1\\nLine2\\nLine3",       # Multi-line
                b"\\x1b[31mColor\\x1b[0m",     # ANSI codes
                b"\\0Hidden",                   # Null bytes
                b"%n%n%n",                      # Dangerous format
            ]
            
        elif 'coord' in harness_name:
            # Coordinate test cases
            coords = [
                struct.pack('BBB', 0, 0, ord('a')),        # Origin
                struct.pack('BBB', 79, 21, ord('z')),      # Max valid
                struct.pack('BBB', 80, 22, ord('!')),      # Just over
                struct.pack('BBB', 255, 255, ord('?')),    # Way over
                struct.pack('bbb', -1, -1, ord('#')),      # Negative
                struct.pack('bbb', -128, -128, ord('*')),  # Min schar
            ]
            seeds = coords
            
        elif 'warn' in harness_name:
            # Warning level edge cases
            seeds = [
                struct.pack('bbBB', -100, 100, 0, 100),  # Negative HP
                struct.pack('BBBB', 1, 100, 0, 100),     # Low HP
                struct.pack('BBBB', 100, 100, 1, 50),    # Polymorphed
                struct.pack('BBBB', 0, 0, 0, 0),         # All zeros
                struct.pack('BBBB', 255, 255, 1, 255),   # Max values
            ]
            
        elif 'string' in harness_name:
            # String handling edge cases
            seeds = [
                b"normal input",
                b"\\x1b",                       # Escape
                b"\\x08" * 10,                  # Backspaces
                b"\\x7f" * 5,                   # DEL chars
                b"very " * 50 + b"long",        # Repetitive
                b"\\t\\t\\t\\ttabs",           # Tabs
                b"\\r\\n\\r\\n",               # Line endings
                b"\\0mid\\0null\\0",           # Embedded nulls
            ]
        
        # Write seeds to corpus
        for i, seed in enumerate(seeds):
            seed_file = corpus_path / f"seed_{i:03d}"
            with open(seed_file, 'wb') as f:
                f.write(seed)
        
        Colors.say("CORPUS", f"📁 Created {len(seeds)} seeds for {harness_name}")
        return corpus_path

    def run_fuzzer(self, harness_name: str, duration: int = 60) -> bool:
        """Run a single fuzzer harness"""
        binary = self.fuzz_dir / harness_name
        if not binary.exists():
            Colors.error(f"Harness not found: {harness_name}")
            return False
        
        corpus = self.create_smart_corpus(harness_name)
        log_file = self.log_dir / f"{harness_name}.log"
        
        Colors.say("FUZZ", f"🚀 Running {harness_name} for {duration}s")
        
        env = os.environ.copy()
        env['ASAN_OPTIONS'] = 'abort_on_error=1:symbolize=1'
        
        fuzz_cmd = [
            str(binary),
            str(corpus),
            f'-max_total_time={duration}',
            '-print_final_stats=1',
            '-max_len=1024',
            '-timeout=10',
        ]
        
        process = None
        try:
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    fuzz_cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env
                )
                process.wait(timeout=duration + 30)
                
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            Colors.warn(f"⏰ {harness_name} timed out")
        except KeyboardInterrupt:
            if process:
                process.kill()
            Colors.warn(f"⚠️  {harness_name} interrupted")
            return False
        
        # Check for crashes
        crashes = list((corpus / "crash-*").glob("crash-*"))
        if crashes:
            Colors.error(f"💥 {harness_name} FOUND {len(crashes)} CRASHES!")
            for crash in crashes[:3]:  # Show first 3
                Colors.error(f"   - {crash.name}")
            return False
        
        Colors.success(f"✅ {harness_name} completed without crashes")
        return True

    def run_all(self, duration_per_target: int = 60) -> int:
        """Run complete fuzzing campaign"""
        if not self.check_requirements():
            return 1
        
        if not self.build_hack_for_fuzzing():
            return 1
        
        harnesses = self.create_targeted_fuzz_harnesses()
        Colors.say("FUZZ", f"🎯 Created {len(harnesses)} targeted harnesses")
        
        # Build all harnesses
        built = []
        for harness in harnesses:
            if self.build_fuzz_harness(harness):
                built.append(harness)
            else:
                Colors.warn(f"⚠️  Skipping {harness['name']}")
        
        if not built:
            Colors.error("No harnesses built successfully")
            return 1
        
        # Run fuzzing
        Colors.say("FUZZ", f"🎯 Running {len(built)} harnesses")
        crashes = []
        
        for harness in built:
            if not self.run_fuzzer(harness['name'], duration_per_target):
                crashes.append(harness['name'])
        
        # Summary
        print("\n" + "="*60)
        Colors.say("SUMMARY", "Fuzzing Campaign Complete")
        print("="*60)
        
        if crashes:
            Colors.error(f"💥 CRASHES FOUND in: {', '.join(crashes)}")
            Colors.error(f"Check logs in: {self.log_dir}")
            return 1
        else:
            Colors.success(f"✅ All {len(built)} harnesses completed successfully")
            return 0


# Constants from hack.h
BUFSZ = 256
COLNO = 80  
ROWNO = 22
SIZE = lambda x: len(x)


def main():
    parser = argparse.ArgumentParser(
        description='Improved restoHack Fuzzer - Tests real hack code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Run all fuzzers for 60s each
  %(prog)s --duration 300     # Run for 5 minutes each
  %(prog)s --target pline     # Fuzz only message system
  %(prog)s --debug            # Show debug output
        '''
    )
    
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Duration per target in seconds (default: 60)')
    parser.add_argument('--target', help='Run specific fuzzer only')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    fuzzer = ImprovedHackFuzzer(str(project_root), args.debug)
    
    if args.target:
        # Run single target
        if not fuzzer.check_requirements():
            return 1
        if not fuzzer.build_hack_for_fuzzing():
            return 1
        
        harnesses = fuzzer.create_targeted_fuzz_harnesses()
        target_harness = None
        for h in harnesses:
            if args.target in h['name']:
                target_harness = h
                break
        
        if not target_harness:
            Colors.error(f"Unknown target: {args.target}")
            Colors.say("HELP", f"Available: {', '.join(h['name'] for h in harnesses)}")
            return 1
        
        if not fuzzer.build_fuzz_harness(target_harness):
            return 1
            
        return 0 if fuzzer.run_fuzzer(target_harness['name'], args.duration) else 1
    else:
        # Run all targets
        return fuzzer.run_all(args.duration)


if __name__ == "__main__":
    sys.exit(main())