#!/usr/bin/env python3
"""
restoHack Reliable Game Runner - Python-based input generation
Replaces unreliable bash keystroke injection with proper PTY handling
"""
import pexpect
import sys
import random
import time
import argparse
import os
from typing import Optional, List, Tuple

class HackGameRunner:
    """Reliable 1984 Hack game automation with state-aware input"""
    
    def __init__(self, binary_path: str, debug: bool = False):
        self.binary_path = binary_path
        self.debug = debug
        self.child: Optional[pexpect.spawn] = None
        
        # Game interaction patterns
        self.movement_keys = 'hjkl'
        self.safe_commands = '.Ls?'
        self.directions = ['north', 'south', 'east', 'west', 'up', 'down']
        
    def log(self, msg: str) -> None:
        """Debug logging"""
        if self.debug:
            print(f"[DEBUG] {msg}", file=sys.stderr)
            
    def start_game(self, player_name: str = "TestPlayer") -> bool:
        """Start hack game and handle initial setup"""
        try:
            # Start game in debug mode for consistent behavior
            cmd = f'{self.binary_path} -D'
            self.log(f"Starting: {cmd}")
            
            self.child = pexpect.spawn(cmd, timeout=10)
            if self.debug:
                self.child.logfile_read = sys.stderr.buffer
                
            # Handle character selection prompt
            patterns = [
                'Shall I pick a character',
                'shall I pick a character', 
                'pick a character',
                'What is your name'
            ]
            
            index = self.child.expect(patterns + [pexpect.TIMEOUT, pexpect.EOF], timeout=5)
            
            if index < 3:  # Character selection prompt
                self.log("Got character selection prompt")
                self.child.sendline('n')  # New character
                
                # Wait for name prompt
                self.child.expect(['What is your name', 'name'], timeout=5)
                self.log("Got name prompt")
                self.child.sendline(player_name)
                
            elif index == 3:  # Direct name prompt
                self.log("Got direct name prompt")
                self.child.sendline(player_name)
                
            else:
                self.log("Timeout or EOF during startup")
                return False
                
            # Wait for game to start (look for common game prompts)
            startup_patterns = [
                '--More--',
                'Hit space to continue',
                '@',  # Player symbol visible
                'Dlvl:',  # Status line
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(startup_patterns, timeout=10)
            if index < 4:
                self.log("Game started successfully")
                if index in [0, 1]:  # More prompt
                    self.child.send(' ')  # Advance past intro
                return True
            else:
                self.log("Game startup timeout")
                return False
                
        except Exception as e:
            self.log(f"Startup failed: {e}")
            return False
            
    def send_safe_input(self, keys: str, expect_response: bool = True) -> bool:
        """Send input and optionally wait for game response"""
        try:
            if not self.child:
                return False
                
            self.log(f"Sending: {repr(keys)}")
            self.child.send(keys)
            
            if expect_response:
                # Give game time to process and respond
                time.sleep(0.1)
                
            return True
            
        except Exception as e:
            self.log(f"Input send failed: {e}")
            return False
            
    def do_random_movements(self, count: int = 10) -> bool:
        """Perform random movement commands"""
        for i in range(count):
            move = random.choice(self.movement_keys)
            if not self.send_safe_input(move):
                return False
            time.sleep(0.05)  # Brief pause between moves
        return True
        
    def do_safe_commands(self, count: int = 5) -> bool:
        """Execute safe game commands"""
        commands = ['i', '/', '.', 'L', 's']  # inventory, search, rest, look, save
        
        for i in range(min(count, len(commands))):
            cmd = commands[i]
            self.log(f"Executing command: {cmd}")
            
            if not self.send_safe_input(cmd):
                return False
                
            # Some commands need confirmation
            if cmd == 's':  # Save command
                try:
                    # Look for save prompt and respond
                    index = self.child.expect(['Save', 'save', pexpect.TIMEOUT], timeout=2)
                    if index < 2:
                        self.child.sendline('y')
                except:
                    pass
                    
            time.sleep(0.2)  # Wait for command to complete
            
        return True
        
    def quit_game(self, force: bool = False) -> bool:
        """Reliably quit the game"""
        try:
            if not self.child:
                return True
                
            self.log("Attempting to quit game")
            
            # Try normal quit sequence
            self.child.send('Q')
            
            quit_patterns = [
                'Really quit',
                'really quit', 
                'quit',
                'Goodbye',
                pexpect.EOF,
                pexpect.TIMEOUT
            ]
            
            index = self.child.expect(quit_patterns, timeout=3)
            
            if index < 3:  # Got quit confirmation prompt
                self.log("Got quit confirmation")
                self.child.sendline('y')
                self.child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=5)
                
            elif index == 3:  # Already quit
                self.log("Game already quit")
                
            else:  # Timeout or EOF
                if force:
                    self.log("Force terminating game")
                    self.child.terminate(force=True)
                    
            return True
            
        except Exception as e:
            self.log(f"Quit failed: {e}")
            if force and self.child:
                try:
                    self.child.terminate(force=True)
                except:
                    pass
            return False
            
    def run_session(self, steps: int = 50, player_name: str = "TestPlayer") -> Tuple[bool, int]:
        """Run a complete game session"""
        try:
            # Start the game
            if not self.start_game(player_name):
                return False, -1
                
            self.log(f"Running {steps} step game session")
            
            # Distribute steps across different activities
            movement_steps = max(1, steps // 2)
            command_steps = max(1, steps // 4)
            
            # Do random movements
            if not self.do_random_movements(movement_steps):
                self.log("Movement phase failed")
                
            # Do safe commands  
            if not self.do_safe_commands(command_steps):
                self.log("Command phase failed")
                
            # Fill remaining steps with mixed actions
            remaining = steps - movement_steps - command_steps
            for _ in range(remaining):
                if random.random() < 0.7:  # 70% movement
                    self.send_safe_input(random.choice(self.movement_keys))
                else:  # 30% other actions
                    self.send_safe_input(random.choice(self.safe_commands))
                time.sleep(0.05)
                
            # Clean exit
            self.quit_game()
            
            # Get exit code
            if self.child and self.child.isalive():
                self.child.wait()
                
            exit_code = self.child.exitstatus if self.child else 0
            self.log(f"Session completed with exit code: {exit_code}")
            
            return True, exit_code
            
        except Exception as e:
            self.log(f"Session failed: {e}")
            self.quit_game(force=True)
            return False, -1
            
    def __del__(self):
        """Cleanup"""
        if self.child and self.child.isalive():
            try:
                self.child.terminate(force=True)
            except:
                pass


def run_stress_test(binary_path: str, runs: int = 50, steps: int = 40, debug: bool = False) -> Tuple[int, int]:
    """Run multiple game sessions for stress testing"""
    passed = 0
    failed = 0
    
    print(f"🎮 Running {runs} stress test sessions ({steps} steps each)")
    
    for i in range(1, runs + 1):
        runner = HackGameRunner(binary_path, debug=debug)
        player_name = f"Player{i:02d}"
        
        success, exit_code = runner.run_session(steps, player_name)
        
        # Accept normal exit codes (0 = normal, 141 = SIGPIPE)
        if success and (exit_code == 0 or exit_code == 141):
            print(f"✅ Session {i}")
            passed += 1
        else:
            print(f"❌ Session {i} FAILED (exit={exit_code})")
            failed += 1
            
        # Brief pause between sessions
        time.sleep(0.1)
        
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return passed, failed


def main():
    parser = argparse.ArgumentParser(description='Reliable Hack game runner')
    parser.add_argument('binary', help='Path to hack binary')
    parser.add_argument('--runs', type=int, default=50, help='Number of test runs')
    parser.add_argument('--steps', type=int, default=40, help='Steps per session')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--single', action='store_true', help='Run single session only')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.binary):
        print(f"Error: Binary not found: {args.binary}", file=sys.stderr)
        return 1
        
    if args.single:
        # Single session test
        runner = HackGameRunner(args.binary, debug=args.debug)
        success, exit_code = runner.run_session(args.steps)
        print(f"Single session: {'✅ PASSED' if success else '❌ FAILED'} (exit={exit_code})")
        return 0 if success else 1
    else:
        # Stress test
        passed, failed = run_stress_test(args.binary, args.runs, args.steps, args.debug)
        
        # Allow up to 10% failure rate
        failure_rate = (failed * 100) // args.runs
        if failure_rate <= 10:
            print(f"✅ Stress test PASSED (failure rate: {failure_rate}%)")
            return 0
        else:
            print(f"❌ Stress test FAILED (failure rate: {failure_rate}%)")
            return 1


if __name__ == '__main__':
    sys.exit(main())