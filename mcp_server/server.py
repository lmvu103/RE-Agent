import os
import sys

# Ultimate fix for ModuleNotFoundError on any environment
# Get the absolute directory where server.py resides
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add it to the front of sys.path so Python finds 'pyrestoolbox_mcp'
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from pyrestoolbox_mcp import mcp
except ImportError as e:
    # If it still fails, print the path for debugging on Cloud Stderr
    print(f"DEBUG: Current sys.path = {sys.path}", file=sys.stderr)
    print(f"DEBUG: I am here: {current_dir}", file=sys.stderr)
    print(f"DEBUG: Contents of current_dir: {os.listdir(current_dir)}", file=sys.stderr)
    raise e

if __name__ == "__main__":
    mcp.run()
