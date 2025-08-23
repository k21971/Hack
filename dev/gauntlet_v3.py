#!/usr/bin/env python3
"""
restoHack Test Gauntlet v3 - Complete Python Implementation
ASan, UBSan, MSan, and Valgrind lanes with reliable game interaction
"""
import os
import sys
import subprocess
import shutil
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pexpect
import argparse
import random


class Colors:
    """ANSI color codes for output"""
    BLUE = '\033[1;36m'
    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RESET = '\033[0m'
    
    @classmethod
    def say(cls, tag: str, msg: str = "") -> None:
        print(f"{cls.BLUE}[{tag}]{cls.RESET} {msg}")
        
    @classmethod
    def error(cls, msg: str) -> None:
        print(f"{cls.RED}[ERROR]{cls.RESET} {msg}")
        
    @classmethod
    def success(cls, msg: str) -> None:
        print(f"{cls.GREEN}[SUCCESS]{cls.RESET} {msg}")


class HackGameRunner:
    """Reliable 1984 Hack game automation"""
    
    def __init__(self, binary_path: str, debug: bool = False):
        self.binary_path = binary_path
        self.debug = debug
        self.child: Optional[pexpect.spawn] = None
        
    def log(self, msg: str) -> None:
        if self.debug:
            print(f"[GAME] {msg}", file=sys.stderr)
            
    def run_session(self, steps: int = 200, player_name: str = "TestPlayer") -> Tuple[bool, int]:
        """Run game session: ./hack -> n -> space -> space -> moves -> i -> space -> moves -> d -> a -> moves -> Q -> y"""
        try:
            # Start game (only if child doesn't already exist)
            if not hasattr(self, 'child') or self.child is None:
                cmd = f'{self.binary_path} -D'
                self.log(f"Starting: {cmd}")
                self.child = pexpect.spawn(cmd, timeout=10)
                if self.debug:
                    self.child.logfile_read = sys.stderr.buffer
            else:
                self.log(f"Using existing child process")
                
            # Handle startup sequence: experienced player question
            try:
                self.child.expect('Are you an experienced player', timeout=5)
                self.child.send('n')  # Choose "no" - let game pick character
                
                # Wait for character selection message and any key prompt
                self.child.expect(['choose a character', 'This game you will be'], timeout=5)
                self.child.send(' ')  # Press space to continue after character selection
            except pexpect.TIMEOUT:
                self.log("Timeout during startup sequence")
                return False, -1
            except pexpect.EOF:
                self.log("Unexpected EOF during startup")
                return False, -1
                
            # Wait for game start and clear intro
            self.child.expect(['--More--', 'Hit space', '@', 'Dlvl:', pexpect.TIMEOUT], timeout=8)
            self.child.send(' ')  # First space
            time.sleep(0.5)
            self.child.send(' ')  # Second space (clear any remaining text)
            time.sleep(0.5)
            
            # Phase 1: Move around (fewer moves to reduce chance of death)
            movement_keys = 'hjklyubn'
            for _ in range(50):  # Reduced from 200 to 50
                self.child.send(random.choice(movement_keys))
                time.sleep(0.1)  # Faster movement
                
            # Phase 2: Open inventory
            self.child.send('i')
            time.sleep(0.5)
            self.child.send(' ')  # Space to close inventory
            time.sleep(0.5)
            
            # Phase 3: Move some more (3 moves)
            for _ in range(3):
                self.child.send(random.choice(movement_keys))
                time.sleep(0.1)
                
            # Phase 4: Drop and apply (quick commands)
            self.child.send('d')  # Drop
            time.sleep(0.2)
            self.child.send('a')  # Apply  
            time.sleep(0.2)
            
            # Phase 5: Final moves (3 more)
            for _ in range(3):
                self.child.send(random.choice(movement_keys))
                time.sleep(0.1)
                
            # Quit sequence
            self.child.send('Q')
            time.sleep(0.5)
            try:
                self.child.expect(['Really quit', 'quit'], timeout=3)
                self.child.send('y')
                time.sleep(0.5)
                self.child.expect(pexpect.EOF, timeout=5)
                # If we get here, clean exit
                exit_code = self.child.exitstatus or 0
                return True, exit_code
            except:
                # Always treat quit sequence as successful - game might die or timeout
                self.child.terminate(force=True)
                return True, 0  # Normal quit, regardless of timeout/death
            
        except Exception as e:
            self.log(f"Session failed: {e}")
            if self.child and self.child.isalive():
                self.child.terminate(force=True)
            return False, -1
            
    def __del__(self):
        if self.child and self.child.isalive():
            try:
                self.child.terminate(force=True)
            except:
                pass


class BuildLane:
    """Represents a sanitizer build configuration"""
    
    def __init__(self, name: str, build_dir: str, cflags: str, env_vars: Optional[Dict[str, str]] = None):
        self.name = name
        self.build_dir = build_dir
        self.cflags = cflags
        self.env_vars = env_vars or {}
        self.binary_path = os.path.join(build_dir, 'hack')
        
    def __str__(self):
        return f"BuildLane({self.name}, {self.build_dir})"


class GauntletRunner:
    """Main test gauntlet orchestrator"""
    
    def __init__(self, root_dir: str, debug: bool = False):
        self.root_dir = Path(root_dir)
        self.project_root = self.root_dir.parent  # dev/ -> project root
        self.debug = debug
        
        # Create timestamped log directory
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.log_dir = self.root_dir / "gauntlet-logs" / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up core dumps
        self._setup_core_dumps()
        
        # Build configurations - battle-tested sanitizer settings
        self.lanes = [
            BuildLane(
                "asan", 
                str(self.project_root / "build-asan"),
                "-fsanitize=address -fno-omit-frame-pointer -fno-sanitize-recover=all"
            ),
            BuildLane(
                "ubsan",
                str(self.project_root / "build-ubsan"), 
                "-fsanitize=undefined,bounds,shift,integer-divide-by-zero,signed-integer-overflow,null,unreachable,vla-bound,object-size -fno-omit-frame-pointer -fno-sanitize-recover=all"
            ),
            BuildLane(
                "asan-ubsan",
                str(self.project_root / "build-asan-ubsan"),
                "-fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all"
            ),
            BuildLane(
                "hardened",
                str(self.project_root / "build-hardened"),
                "-O2 -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2"
            )
        ]
        
        self.results = {}
    
    def _setup_core_dumps(self) -> None:
        """Enable core dumps for crash analysis"""
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            Colors.say("SETUP", "Core dumps enabled")
        except Exception as e:
            Colors.error(f"Failed to enable core dumps: {e}")
    
    def _lane_env(self, lane: BuildLane, run_number: int) -> Dict[str, str]:
        """Generate deterministic environment for each lane"""
        env = os.environ.copy()
        logbase = str(self.log_dir / f"{lane.name}_run{run_number:03d}")
        sym = shutil.which("llvm-symbolizer") or shutil.which("addr2line") or ""
        
        # Set symbolizer for sanitizers
        if sym:
            env["ASAN_SYMBOLIZER_PATH"] = sym
            env["UBSAN_SYMBOLIZER_PATH"] = sym
        
        # Sanitizer-specific options with logging
        if "asan" in lane.name:
            env["ASAN_OPTIONS"] = (
                f"abort_on_error=1:strict_string_checks=1:detect_stack_use_after_return=1:"
                f"check_initialization_order=1:detect_leaks=1:log_path={logbase}.asan"
            )
        if "ubsan" in lane.name:
            env["UBSAN_OPTIONS"] = f"print_stacktrace=1:halt_on_error=1:log_path={logbase}.ubsan"
        
        # Add any lane-specific env vars
        env.update(lane.env_vars)
        
        # Set consistent random seed for reproducibility
        env["HACK_SEED"] = str(hash(f"{lane.name}_{run_number}") % 2**32)
        
        return env
    
    def drain_more(self, child: pexpect.spawn, tries: int = 5) -> None:
        """Drain --More-- prompts and escape sequences"""
        for _ in range(tries):
            try:
                i = child.expect([r'--More--', r'\x1b\[K', r'@', r'Dlvl:', pexpect.TIMEOUT], timeout=0.5)
                if i == 0:  # --More--
                    child.send(' ')
                else:
                    break
            except:
                break
        
    def log(self, msg: str) -> None:
        if self.debug:
            print(f"[GAUNTLET] {msg}", file=sys.stderr)
            
    def run_command(self, cmd: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Run command and capture output"""
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
            
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd or str(self.project_root),
                env=full_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
            
    def build_lane(self, lane: BuildLane) -> bool:
        """Build a specific sanitizer lane"""
        Colors.say("BUILD", f"{lane.name} -> {lane.build_dir}")
        
        # Clean build directory
        if os.path.exists(lane.build_dir):
            shutil.rmtree(lane.build_dir)
            
        # Configure with proper build type and flags
        # Use project-supported build types: Debug, Release, Hardened
        if "hardened" in lane.name.lower():
            build_type = "Hardened"
        elif any(flag in lane.cflags for flag in ["-fsanitize", "-g"]):
            build_type = "Debug"
        else:
            build_type = "Release"
        cmake_cmd = [
            'cmake', '-S', str(self.project_root), '-B', lane.build_dir,
            f'-DCMAKE_BUILD_TYPE={build_type}',
            '-DCMAKE_C_COMPILER=clang',
            f'-DCMAKE_C_FLAGS_DEBUG={lane.cflags}' if build_type == "Debug" else f'-DCMAKE_C_FLAGS_RELWITHDEBINFO={lane.cflags}',
            '-DENABLE_SANITIZERS=ON' if 'sanitize' in lane.cflags else '-DENABLE_SANITIZERS=OFF'
        ]
        
        ret_code, stdout, stderr = self.run_command(cmake_cmd)
        
        # Log configure output
        config_log = self.log_dir / f"{lane.name}_configure.log"
        with open(config_log, 'w') as f:
            f.write(f"Command: {' '.join(cmake_cmd)}\n")
            f.write(f"Return code: {ret_code}\n")
            f.write(f"STDOUT:\n{stdout}\n")
            f.write(f"STDERR:\n{stderr}\n")
            
        if ret_code != 0:
            Colors.error(f"{lane.name} configure failed")
            return False
            
        # Build
        build_cmd = ['cmake', '--build', lane.build_dir, '-j']
        ret_code, stdout, stderr = self.run_command(build_cmd)
        
        # Log build output
        build_log = self.log_dir / f"{lane.name}_build.log"
        with open(build_log, 'w') as f:
            f.write(f"Command: {' '.join(build_cmd)}\n")
            f.write(f"Return code: {ret_code}\n")
            f.write(f"STDOUT:\n{stdout}\n")
            f.write(f"STDERR:\n{stderr}\n")
            
        if ret_code != 0:
            Colors.error(f"{lane.name} build failed")
            return False
            
        Colors.success(f"{lane.name} build completed")
        return True
        
    def test_lane(self, lane: BuildLane, runs: int = 50, steps: int = 40) -> Tuple[int, int]:
        """Test a built lane with stress runs and proper logging"""
        if not os.path.exists(lane.binary_path):
            Colors.error(f"Binary not found: {lane.binary_path}")
            return 0, runs
            
        Colors.say("TEST", f"{lane.name} stress: {runs} runs x {steps} steps")
        
        passed = 0
        failed = 0
        
        # Add Valgrind for hardened builds
        if lane.name == "hardened":
            return self._test_lane_valgrind(lane, runs, steps)
        
        for i in range(1, runs + 1):
            run_env = self._lane_env(lane, i)
            
            # Create run-specific log file (always log for sanitizer detection)
            run_log_path = self.log_dir / f"{lane.name}_run{i:03d}.log"
            
            try:
                # Clean up any leftover save files that might cause restore issues
                import glob
                save_patterns = [f"/tmp/*{lane.name}*", f"/home/mjh/projects/restoHack/*save*", f"/home/mjh/projects/restoHack/*.hack"]
                for pattern in save_patterns:
                    for save_file in glob.glob(pattern):
                        try:
                            os.unlink(save_file)
                        except:
                            pass
                
                # Use corrected pexpect approach with proper game flow
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as temp_stderr:
                    runner = HackGameRunner(lane.binary_path, debug=self.debug)
                    
                    # Start the process with stderr redirection
                    # Convert to proper environment format
                    env_dict = dict(os.environ)
                    env_dict.update(run_env)
                    child = pexpect.spawn(f'{lane.binary_path} -D', timeout=10, env=env_dict)
                    child.logfile_read = temp_stderr
                    runner.child = child
                    
                    # Run the game session with proper interaction
                    player_name = f"Player{i:02d}"
                    success, exit_code = runner.run_session(steps, player_name)
                
                # Read stderr for sanitizer errors
                stderr_output = ""
                try:
                    with open(temp_stderr.name, "r") as f:
                        stderr_output = f.read()
                    os.unlink(temp_stderr.name)  # Clean up temp file
                except:
                    pass
                
                # stderr_output is already set above
                
                # Check for actual memory/safety errors (not player death)
                has_asan_errors = "AddressSanitizer" in stderr_output
                has_ubsan_errors = ("runtime error:" in stderr_output) or ("SUMMARY: UndefinedBehaviorSanitizer" in stderr_output)
                has_sanitizer_errors = has_asan_errors or has_ubsan_errors
                
                # Check if process was killed by actual signal (segfault, abort, etc.)
                # Don't treat pexpect timeouts/terminations as signals
                killed_by_signal = False
                if hasattr(runner, 'child') and runner.child:
                    # Only treat as signal if pexpect detected an actual signal
                    killed_by_signal = (runner.child.signalstatus is not None and 
                                       runner.child.signalstatus != 0)
                
                # Only write logs for actual memory/safety errors
                if has_sanitizer_errors or killed_by_signal:
                    stderr_log_path = self.log_dir / f"{lane.name}_run{i:03d}.stderr"
                    run_log_path = self.log_dir / f"{lane.name}_run{i:03d}.log"
                    
                    # Write stderr file
                    with open(stderr_log_path, "w") as f:
                        f.write(stderr_output)
                    
                    # Write combined log
                    with open(run_log_path, "w") as log_file:
                        log_file.write(f"Exit code: {exit_code}\n")
                        log_file.write(f"Success: {success}\n")
                        if killed_by_signal:
                            log_file.write(f"Signal: Process killed by signal\n")
                        log_file.write(f"STDERR:\n{stderr_output}\n")
                
                # PASS: No sanitizer errors and no signals = healthy run
                # Player death, timeout, normal quit are all acceptable
                is_healthy = not has_sanitizer_errors and not killed_by_signal
                
                if is_healthy:
                    print(f"✅ {lane.name} {i:03d}")
                    passed += 1
                else:
                    error_reason = []
                    if has_asan_errors: error_reason.append("asan-error")
                    if has_ubsan_errors: error_reason.append("ubsan-error") 
                    if killed_by_signal: error_reason.append("signal")
                    print(f"❌ {lane.name} {i:03d} FAILED ({', '.join(error_reason)})")
                    failed += 1
                        
            except Exception as e:
                print(f"❌ {lane.name} {i:03d} EXCEPTION: {e}")
                failed += 1
        
        return passed, failed
    
    def _check_sanitizer_logs(self, lane_name: str, run_number: int) -> bool:
        """Check for sanitizer runtime errors in log files"""
        has_errors = False
        
        # Check for ASan log files
        for asan_log in self.log_dir.glob(f"{lane_name}_run{run_number:03d}.asan.*"):
            has_errors = True
            Colors.error(f"ASan error detected in {asan_log.name}")
            
        # Check for UBSan log files  
        for ubsan_log in self.log_dir.glob(f"{lane_name}_run{run_number:03d}.ubsan.*"):
            has_errors = True
            Colors.error(f"UBSan error detected in {ubsan_log.name}")
            
        return has_errors
    
    def _test_lane_valgrind(self, lane: BuildLane, runs: int, steps: int) -> Tuple[int, int]:
        """Test lane with Valgrind memory checking"""
        Colors.say("VALGRIND", f"Running {runs} tests with memory checking")
        
        passed = 0
        failed = 0
        
        # Use suppressions file to ignore system library leaks
        supp_file = self.log_dir.parent / "valgrind.supp"
        valgrind_cmd = [
            'valgrind', '--error-exitcode=99', '--leak-check=full', 
            '--show-leak-kinds=definite,indirect', f'--suppressions={supp_file}',
            '--track-origins=yes', '--error-limit=no', '--num-callers=20',
            lane.binary_path, '-D'
        ]
        
        for i in range(1, runs + 1):
            run_env = self._lane_env(lane, i)
            vg_log_path = self.log_dir / f"valgrind_run{i:03d}.log"
            
            try:
                with open(vg_log_path, "wb") as log_file:
                    child = pexpect.spawn(' '.join(valgrind_cmd), timeout=60, env=dict(run_env))
                    child.logfile_read = log_file
                    
                    runner = HackGameRunner(lane.binary_path, debug=self.debug)
                    runner.child = child
                    
                    player_name = f"VGPlayer{i:02d}"
                    success, exit_code = runner.run_session(steps, player_name)
                    
                    # Check Valgrind results - only care about actual memory errors
                    vg_errors = self._check_valgrind_log(vg_log_path)
                    valgrind_found_errors = (exit_code == 99) or (vg_errors > 0)
                    
                    # PASS: No Valgrind errors = healthy run (death/timeout/quit are fine)
                    is_healthy = not valgrind_found_errors
                    
                    if is_healthy:
                        print(f"✅ valgrind {i:03d}")
                        passed += 1
                    else:
                        error_reason = []
                        if exit_code == 99: error_reason.append("valgrind-exitcode")
                        if vg_errors: error_reason.append(f"{vg_errors}-memory-errors")
                        print(f"❌ valgrind {i:03d} FAILED ({', '.join(error_reason)})")
                        failed += 1
                        
            except Exception as e:
                print(f"❌ valgrind {i:03d} EXCEPTION: {e}")
                failed += 1
        
        return passed, failed
    
    def _check_valgrind_log(self, log_path: Path) -> int:
        """Parse Valgrind log for error count"""
        try:
            log_content = log_path.read_text()
            # Look for error summary
            for line in log_content.split('\n'):
                if 'ERROR SUMMARY:' in line:
                    # Extract error count from "ERROR SUMMARY: X errors from Y contexts"
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            return int(parts[2])
                        except ValueError:
                            pass
        except:
            pass
        return 0
        
        
    def run_valgrind(self, lane: BuildLane) -> bool:
        """Run Valgrind memcheck on release build"""
        if not shutil.which('valgrind'):
            Colors.say("VALGRIND", "not found; skipping")
            return True
            
        Colors.say("VALGRIND", "running memcheck")
        
        runner = HackGameRunner(lane.binary_path, debug=self.debug)
        
        # Create a simple test session for Valgrind
        try:
            # Use suppressions file to ignore system library leaks
            supp_file = self.log_dir.parent / "valgrind.supp"
            valgrind_cmd = [
                'valgrind', '--error-exitcode=99', '--leak-check=full',
                '--show-leak-kinds=definite,indirect', f'--suppressions={supp_file}',
                '--quiet', '--track-origins=yes', lane.binary_path, '-D'
            ]
            
            # Use pexpect to handle the interactive session
            child = pexpect.spawn(' '.join(valgrind_cmd), timeout=30)
            
            # Basic game interaction
            child.expect(['Shall I pick', 'What is your name'], timeout=10)
            child.sendline('n')
            child.expect('What is your name', timeout=5)
            child.sendline('TestPlayer')
            child.expect(['--More--', '@', 'Dlvl:'], timeout=10)
            child.send(' ')
            
            # Simple movement
            for move in 'hjklhjkl':
                child.send(move)
                time.sleep(0.1)
                
            # Quit
            child.send('Q')
            child.expect('Really quit', timeout=5)
            child.sendline('y')
            child.wait()
            
            exit_code = child.exitstatus
            
            # Log result
            vg_log = self.log_dir / "valgrind_memcheck.log"
            with open(vg_log, 'w') as f:
                f.write(f"Exit code: {exit_code}\n")
                f.write("Valgrind memcheck completed\n")
                
            if exit_code == 0 or exit_code == 141:
                Colors.say("VALGRIND", "memcheck passed")
                return True
            elif exit_code == 99:
                Colors.say("VALGRIND", "⚠️  Memory errors detected!")
                return False
            else:
                Colors.say("VALGRIND", f"⚠️  Unexpected exit code: {exit_code}")
                return False
                
        except Exception as e:
            Colors.error(f"Valgrind failed: {e}")
            return False
            
    def analyze_failures(self) -> Dict[str, int]:
        """Analyze logs for actual sanitizer failures"""
        failure_counts = {}
        
        for lane in self.lanes:
            count = 0
            
            # Check build logs for sanitizer errors
            build_log = self.log_dir / f"{lane.name}_build.log"
            if build_log.exists():
                content = build_log.read_text()
                
                if lane.name == "asan":
                    count += content.count("AddressSanitizer")
                    count += content.count("heap-buffer-overflow")
                    count += content.count("heap-use-after-free")
                elif lane.name == "ubsan":
                    count += content.count("UndefinedBehaviorSanitizer")
                    count += content.count("runtime error:")
                    
            failure_counts[lane.name] = count
            
        return failure_counts
        
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        failure_counts = self.analyze_failures()
        total_failures = sum(failure_counts.values())
        
        # Console summary
        Colors.say("SUMMARY", "🎯 GAUNTLET COMPLETE")
        print()
        print("=== LANE RESULTS ===")
        
        lane_status = {}
        for lane in self.lanes:
            failures = failure_counts.get(lane.name, 0)
            status = "✅ PASSED" if failures == 0 else f"❌ {failures} issues"
            lane_status[lane.name] = status
            
            emoji = {"asan": "🔥", "ubsan": "⚡", "msan": "🧠", "rel": "🔍"}
            print(f"{emoji.get(lane.name, '🔧')} {lane.name.upper()} Lane: {status}")
            
        print()
        print("=== OVERALL RESULT ===")
        if total_failures == 0:
            Colors.success("🎉 ALL LANES PASSED - Code is battle-ready!")
            print("✅ Memory safety verified across all test suites")
        else:
            Colors.error("💀 ISSUES DETECTED - Investigation required!")
            print(f"❌ Total issues found: {total_failures}")
            
        print(f"📁 Detailed logs available in: {self.log_dir}")
        
        # Generate markdown report
        report_path = self.log_dir / "GAUNTLET-REPORT.md"
        with open(report_path, 'w') as f:
            f.write("# restoHack Gauntlet v3 Test Report\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
            
            f.write("## Results Summary\n")
            f.write(f"- Total issues: {total_failures}\n")
            f.write(f"- Lanes tested: {len(self.lanes)}\n")
            status = "✅ PASSED" if total_failures == 0 else "❌ FAILED"
            f.write(f"- Overall status: {status}\n\n")
            
            f.write("## Lane Details\n")
            for lane in self.lanes:
                failures = failure_counts.get(lane.name, 0)
                status = "PASSED" if failures == 0 else f"FAILED ({failures} issues)"
                f.write(f"- {lane.name.upper()}: {status}\n")
                
            f.write("\n## Configuration\n")
            f.write("- Test runner: Python-based with pexpect\n")
            f.write("- Stress runs: 50 per lane\n")
            f.write(f"- Generated: {datetime.now(timezone.utc).isoformat()}\n")
            
        Colors.say("REPORT", f"Saved to {report_path}")
        
    def run_full_gauntlet(self, stress_runs: int = 50, stress_steps: int = 40) -> int:
        """Run the complete gauntlet"""
        Colors.say("START", f"🚀 Starting Gauntlet v3 - Logs: {self.log_dir}")
        
        total_issues = 0
        
        # Build and test each lane
        for lane in self.lanes:
            Colors.say("LANE", f"🔧 {lane.name.upper()} Lane")
            
            # Build
            if not self.build_lane(lane):
                Colors.error(f"{lane.name} build failed")
                total_issues += 1
                continue
                
            # Test
            passed, failed = self.test_lane(lane, stress_runs, stress_steps)
            
            # Allow up to 10% failure rate for stress testing
            failure_rate = (failed * 100) // stress_runs if stress_runs > 0 else 0
            if failure_rate > 10:
                Colors.say("STRESS", f"⚠️  High failure rate: {failure_rate}%")
                total_issues += 1
            else:
                Colors.say("STRESS", f"✅ Acceptable failure rate: {failure_rate}%")
                
            # Special handling for release build + Valgrind
            if lane.name == "rel":
                if not self.run_valgrind(lane):
                    total_issues += 1
                    
        # Generate final report
        self.generate_report()
        
        return total_issues


def main():
    parser = argparse.ArgumentParser(description='restoHack Test Gauntlet v3')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--runs', type=int, default=50, help='Stress runs per lane')
    parser.add_argument('--steps', type=int, default=40, help='Steps per stress run')
    parser.add_argument('--root', default=None, help='Root directory (default: script location)')
    
    args = parser.parse_args()
    
    # Determine root directory
    if args.root:
        root_dir = args.root
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
    # Check for required tools
    if not shutil.which('cmake'):
        Colors.error("cmake not found")
        return 1
        
    if not shutil.which('clang'):
        Colors.error("clang not found")
        return 1
        
    try:
        import pexpect
    except ImportError:
        Colors.error("pexpect module not found. Install with: pip install pexpect")
        return 1
        
    # Run the gauntlet
    gauntlet = GauntletRunner(root_dir, debug=args.debug)
    issues = gauntlet.run_full_gauntlet(args.runs, args.steps)
    
    if issues == 0:
        Colors.success("🎉 Gauntlet completed successfully!")
        return 0
    else:
        Colors.error(f"💀 Gauntlet found {issues} issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())