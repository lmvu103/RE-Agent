#!/usr/bin/env python3
import os
import sys

# Hardcoded fix for Streamlit Cloud to find the tech source code
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from pyrestoolbox_mcp import mcp

if __name__ == "__main__":
    mcp.run()
