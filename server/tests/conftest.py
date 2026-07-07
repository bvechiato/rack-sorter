import os
import sys

# Ensure the `server` package root is on sys.path so tests can import `repository` and `service`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
