#!/usr/bin/env python3
"""Fail when a flow-relevant change does not update docs/flows/README.md.

This is a change-coupling check, not a diagram validator: if a PR touches the
API surface or the client contract, it must also touch the flow README.

Usage:
    python3 scripts/check_flows.py --diff-base origin/main
    python3 scripts/check_flows.py --diff-base "$BASE" --allow-missing-docs
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DOC = "docs/flows/README.md"

# Files that can change a user-visible flow or the API contract. Update this
# list only when the project layout changes.
FLOW_PATHS = (
    "server/api/",
    "server/main.py",
    "client/src/api.ts",
)


def changed_files(base: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        text=True,
        stderr=subprocess.STDOUT,
    )
    return [line for line in output.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff-base",
        required=True,
        help="git ref to diff against, e.g. origin/main or a PR base SHA",
    )
    parser.add_argument(
        "--allow-missing-docs",
        action="store_true",
        help="warn instead of fail when flow docs are missing",
    )
    args = parser.parse_args()

    if not Path(DOC).exists():
        print(f"ERROR: {DOC} does not exist", file=sys.stderr)
        return 1

    try:
        changed = changed_files(args.diff_base)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: could not diff against {args.diff_base}: {exc}", file=sys.stderr)
        return 1

    if DOC in changed:
        print("Flow docs updated.")
        return 0

    touched = sorted(path for path in changed if path.startswith(FLOW_PATHS))
    if not touched:
        print("No flow-relevant changes.")
        return 0

    message = (
        "flow-relevant files changed ("
        + ", ".join(touched)
        + f") but {DOC} was not updated"
    )
    if args.allow_missing_docs:
        print(f"WARNING: {message}", file=sys.stderr)
        return 0

    print(f"ERROR: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
