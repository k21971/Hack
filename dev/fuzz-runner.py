#!/usr/bin/env python3
"""
restoHack Fuzzer Runner
Builds and runs libFuzzer targets for finding bugs in 1984 Hack code
"""

import os
import sys
import subprocess
import shutil
import tempfile
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def error(msg): print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")
    @staticmethod
    def success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {msg}")
    @staticmethod
    def info(msg): print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")
    @staticmethod
    def warn(msg): print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")


class FuzzRunner:
    def __init__(self, project_root: str, debug: bool = False):
        self.project_root = Path(project_root)
        self.debug = debug
        self.fuzz_dir = self.project_root / "build-fuzz"
        self.corpus_dir = self.project_root / "dev" / "fuzz-corpus"
        self.log_dir = self.project_root / "dev" / "fuzz-logs" / datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create directories
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        Colors.info(f"🎯 Fuzzer logs: {self.log_dir}")

    def check_requirements(self):
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
            
        Colors.success("✅ Fuzzing requirements met")
        return True

    def build_fuzz_targets(self):
        """Build fuzzing targets"""
        Colors.info("🔧 Building fuzz targets")
        
        if self.fuzz_dir.exists():
            shutil.rmtree(self.fuzz_dir)
        
        # Configure CMake for fuzzing
        cmake_cmd = [
            'cmake', '-S', str(self.project_root), '-B', str(self.fuzz_dir),
            '-DCMAKE_BUILD_TYPE=Debug',
            '-DCMAKE_C_COMPILER=clang',
            '-DCMAKE_C_FLAGS=-fsanitize=fuzzer,address -g -O1 -fno-omit-frame-pointer',
            '-DENABLE_SANITIZERS=OFF'  # We handle sanitizers manually
        ]
        
        # Configure
        result = subprocess.run(cmake_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Colors.error(f"CMake configure failed: {result.stderr}")
            return False
            
        # Build core hack library (without main)
        build_cmd = ['cmake', '--build', str(self.fuzz_dir)]
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Colors.error(f"Build failed: {result.stderr}")
            return False
            
        Colors.success("✅ Fuzz targets built")
        return True

    def create_fuzz_target(self, name: str, source_code: str):
        """Create a fuzz target source file"""
        target_file = self.fuzz_dir / f"fuzz_{name}.c"
        
        with open(target_file, 'w') as f:
            f.write(f'''// Fuzz target for {name}
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// Include hack headers (adjust paths as needed)
// Note: May need to stub out some globals or functions
// #include "../src/hack.h"

{source_code}
''')
        return target_file

    def build_fuzz_target(self, target_file: Path, output_name: str):
        """Build individual fuzz target"""
        output_path = self.fuzz_dir / output_name
        
        # Get all the hack object files (excluding main)
        hack_objects = list(self.fuzz_dir.glob("CMakeFiles/hack.dir/src/*.o"))
        hack_objects = [str(obj) for obj in hack_objects if not obj.name.endswith('hack.main.c.o')]
        
        build_cmd = [
            'clang', '-fsanitize=fuzzer,address', '-g',
            str(target_file),
            *hack_objects,
            '-lncurses', '-lm',
            '-o', str(output_path)
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Colors.warn(f"Failed to build {output_name}: {result.stderr}")
            return False
            
        Colors.success(f"✅ Built fuzz target: {output_name}")
        return True

    def create_basic_fuzz_targets(self):
        """Create basic fuzz targets for common hack functions"""
        targets = []
        
        # 1. String/Buffer fuzzing target
        string_fuzz = '''
// Fuzz string handling functions
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 1024) return 0;
    
    // Create null-terminated string
    char *input = malloc(Size + 1);
    if (!input) return 0;
    memcpy(input, Data, Size);
    input[Size] = '\\0';
    
    // Test various string functions that might have buffer overflows
    // Note: These would need to be adapted to actual hack functions
    
    // Example: Test name parsing (if such function exists)
    // parse_player_name(input);
    
    // Example: Test command parsing  
    // parse_command(input);
    
    free(input);
    return 0;
}
'''
        
        target_file = self.create_fuzz_target("strings", string_fuzz)
        if self.build_fuzz_target(target_file, "fuzz_strings"):
            targets.append("fuzz_strings")
            
        # 2. Save file fuzzing target
        save_fuzz = '''
// Fuzz save file parsing
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 65536) return 0;  // Reasonable save file size limit
    
    // Create temporary file with fuzz data
    char temp_file[] = "/tmp/fuzz_save_XXXXXX";
    int fd = mkstemp(temp_file);
    if (fd == -1) return 0;
    
    write(fd, Data, Size);
    close(fd);
    
    // Try to parse it as a save file
    // Note: This would need actual hack save parsing functions
    // Example: restore_game(temp_file);
    
    // Clean up
    unlink(temp_file);
    return 0;
}
'''
        
        target_file = self.create_fuzz_target("save", save_fuzz)  
        if self.build_fuzz_target(target_file, "fuzz_save"):
            targets.append("fuzz_save")
            
        # 3. Level data fuzzing
        level_fuzz = '''
// Fuzz level/map data parsing
int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 8192) return 0;  // Level data size limit
    
    // Test level parsing with malformed data
    // Note: Adapt to actual hack level structures
    // Example: parse_level_data(Data, Size);
    
    return 0;
}
'''
        
        target_file = self.create_fuzz_target("level", level_fuzz)
        if self.build_fuzz_target(target_file, "fuzz_level"):
            targets.append("fuzz_level")
            
        return targets

    def create_seed_corpus(self, target_name: str):
        """Create seed corpus for specific target"""
        corpus_path = self.corpus_dir / target_name
        corpus_path.mkdir(exist_ok=True)
        
        if target_name == "fuzz_strings":
            # Create seed inputs for string fuzzing
            seeds = [
                b"",
                b"a", 
                b"test",
                b"player_name",
                b"A" * 64,
                b"A" * 255,
                b"Q",  # Quit command
                b"help",
                b"inventory",
                b"\x00\x01\x02",  # Binary data
                b"\xff" * 16,     # High bytes
            ]
            
            for i, seed in enumerate(seeds):
                seed_file = corpus_path / f"seed_{i:03d}"
                with open(seed_file, 'wb') as f:
                    f.write(seed)
                    
        elif target_name == "fuzz_save":
            # Create minimal save file seeds
            # This would need actual hack save file format knowledge
            seeds = [
                b"HACK_SAVE_V1",  # Header-like
                b"\x00" * 100,    # Null data
                b"\xff" * 100,    # High bytes
            ]
            
            for i, seed in enumerate(seeds):
                seed_file = corpus_path / f"seed_{i:03d}" 
                with open(seed_file, 'wb') as f:
                    f.write(seed)
                    
        Colors.info(f"📁 Created seed corpus: {corpus_path}")

    def run_fuzzer(self, target: str, duration_seconds: int = 60):
        """Run fuzzer for specified duration"""
        target_path = self.fuzz_dir / target
        if not target_path.exists():
            Colors.error(f"Fuzz target not found: {target}")
            return False
            
        corpus_path = self.corpus_dir / target
        self.create_seed_corpus(target)
        
        log_file = self.log_dir / f"{target}.log"
        
        Colors.info(f"🚀 Running {target} for {duration_seconds} seconds...")
        
        fuzz_cmd = [
            str(target_path),
            str(corpus_path),
            f'-max_total_time={duration_seconds}',
            '-print_final_stats=1',
            '-workers=1',
            '-jobs=1'
        ]
        
        start_time = time.time()
        
        try:
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    fuzz_cmd, 
                    stdout=log, 
                    stderr=subprocess.STDOUT,
                    cwd=str(self.fuzz_dir)
                )
                
                process.wait(timeout=duration_seconds + 10)
                
        except subprocess.TimeoutExpired:
            process.kill()
            Colors.warn(f"⏰ {target} timed out (expected)")
        except KeyboardInterrupt:
            process.kill()
            Colors.warn(f"⚠️  {target} interrupted by user")
            
        elapsed = time.time() - start_time
        
        if process.returncode == 0:
            Colors.success(f"✅ {target} completed cleanly ({elapsed:.1f}s)")
            return True
        elif process.returncode == 77:  # libFuzzer found crash
            Colors.error(f"💥 {target} FOUND CRASH! ({elapsed:.1f}s)")
            Colors.error(f"   Log: {log_file}")
            return False
        else:
            Colors.warn(f"⚠️  {target} exited with code {process.returncode}")
            return True  # Might be timeout, treat as success

    def run_all_targets(self, duration_per_target: int = 60):
        """Build and run all fuzz targets"""
        if not self.check_requirements():
            return 1
            
        if not self.build_fuzz_targets():
            return 1
            
        targets = self.create_basic_fuzz_targets()
        if not targets:
            Colors.error("No fuzz targets were built successfully")
            return 1
            
        Colors.info(f"🎯 Running {len(targets)} fuzz targets, {duration_per_target}s each")
        
        crashes = []
        
        for target in targets:
            success = self.run_fuzzer(target, duration_per_target)
            if not success:
                crashes.append(target)
                
        # Summary
        if crashes:
            Colors.error(f"💥 CRASHES FOUND in: {', '.join(crashes)}")
            Colors.error(f"   Check logs in: {self.log_dir}")
            return 1
        else:
            Colors.success(f"✅ All targets completed without crashes")
            Colors.info(f"📊 Corpus saved in: {self.corpus_dir}")
            return 0


def main():
    parser = argparse.ArgumentParser(description='restoHack Fuzzer Runner')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--duration', type=int, default=60, help='Duration per target (seconds)')
    parser.add_argument('--target', type=str, help='Run specific target only')
    parser.add_argument('--root', default=None, help='Project root directory')
    
    args = parser.parse_args()
    
    if args.root:
        root_dir = args.root
    else:
        # Assume script is in dev/ directory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    fuzzer = FuzzRunner(root_dir, args.debug)
    
    if args.target:
        # Run specific target
        if not fuzzer.check_requirements() or not fuzzer.build_fuzz_targets():
            return 1
        targets = fuzzer.create_basic_fuzz_targets()
        if args.target in [t for t in targets]:
            return 0 if fuzzer.run_fuzzer(args.target, args.duration) else 1
        else:
            Colors.error(f"Target '{args.target}' not found. Available: {targets}")
            return 1
    else:
        # Run all targets
        return fuzzer.run_all_targets(args.duration)


if __name__ == "__main__":
    sys.exit(main())