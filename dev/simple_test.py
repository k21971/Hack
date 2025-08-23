#!/usr/bin/env python3
import subprocess
import sys

# Just run the game with a simple script and check exit code
cmd = ["./build-asan/hack", "-D"]
script = "n\n\n \n hjklhjkl\nQ\ny\n"

try:
    result = subprocess.run(cmd, input=script, text=True, capture_output=True, timeout=10)
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout[-200:]}")  # Last 200 chars
    print(f"Stderr: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")