#!/usr/bin/env python3
"""
Eye Trainer Application - Quick Start Guide

This is a fully Python-based eye training application.
No C++ compilation needed!

Usage:
    python main.py
    
Or run this script directly:
    ./run.sh
"""

import sys
import subprocess
from pathlib import Path

def run_app():
    app_dir = Path(__file__).parent
    main_py = app_dir / "main.py"
    
    if not main_py.exists():
        print(f"Error: {main_py} not found!")
        return False
    
    print("Starting Eye Trainer application...")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, str(main_py)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Application exited with error: {e}")
        return False
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        return True

def main():
    if run_app():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
