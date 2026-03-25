# src/meta/build_info.py
# Module to generate build information for the RAG Agent Kit application.

import json
import subprocess
from datetime import datetime, timezone

# Get the current git commit hash
def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"

# Generate build information dictionary
def build_info() -> dict:
    return {
        "version": "0.1.0",
        "commit": get_git_commit(),
        "build_time": datetime.now(timezone.utc).isoformat() + "Z"
    }

# Write build information to a JSON file
def write_build_info(path: str = "BUILD_INFO.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build_info(), f, indent=2)
