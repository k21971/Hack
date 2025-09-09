#!/usr/bin/env python3
"""
Test runner for sanitizer lanes
"""

import os
import sys  
import time
import glob
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Dict

import pexpect

from .colors import Colors
from .game_runner import HackGameRunner
from .build_lanes import BuildLane


class TestRunner:
    """Runs tests for individual sanitizer lanes"""
    
    def __init__(self, log_dir: Path, debug: bool = False, enhanced_mode: bool = False):
        self.log_dir = log_dir
        self.debug = debug
        self.enhanced_mode = enhanced_mode
        self._setup_core_dumps()
        
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
        
    def test_lane(self, lane: BuildLane, runs: int = 50, steps: int = 40) -> Tuple[int, int]:
        """Test a built lane with stress runs and proper logging"""
        if not os.path.exists(lane.binary_path):
            Colors.error(f"Binary not found: {lane.binary_path}")
            return 0, runs
            
        Colors.say("TEST", f"{lane.name} stress: {runs} runs x {steps} steps")
        
        passed = 0
        failed = 0
        
        for i in range(1, runs + 1):
            run_env = self._lane_env(lane, i)
            
            try:
                # Clean up any leftover save files that might cause restore issues
                save_patterns = [f"/tmp/*{lane.name}*", f"/home/mjh/projects/restoHack/*save*", f"/home/mjh/projects/restoHack/*.hack"]
                for pattern in save_patterns:
                    for save_file in glob.glob(pattern):
                        try:
                            os.unlink(save_file)
                        except:
                            pass
                
                # Use corrected pexpect approach with proper game flow
                with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as temp_stderr:
                    runner = HackGameRunner(lane.binary_path, debug=self.debug, enhanced_mode=self.enhanced_mode)
                    
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