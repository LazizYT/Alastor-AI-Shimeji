#!/usr/bin/env python3
"""
Entry point for Alastor Shimeji Desktop AI Companion.
"""
import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.mascot import Shimeji

def main():
    app = Shimeji()

if __name__ == "__main__":
    main()
