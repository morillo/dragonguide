#!/usr/bin/env python3
"""Accidental secret / API key scanner.

Can be run standalone or integrated into a pre-commit hook to prevent committing
api keys to source control.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# High-fidelity regexes for API keys and tokens
PATTERNS = {
    "Gemini API Key (AIza...)": r"AIzaSy[A-Za-z0-9_-]{33}",
    "YouTube API Key": r"AIzaSy[A-Za-z0-9_-]{33}",
    "Generic API Key Assignment": r"(api[-_]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9-_]{16,}['\"]",
}

def scan_files() -> bool:
    found_secrets = False
    # Only scan relevant files, ignoring virtual environments, caches, and dotfiles
    ignore_dirs = {".venv", ".git", "__pycache__", "cache", ".pytest_cache", "egg-info", "kit_temp"}
    
    for path in ROOT.rglob("*"):
        if any(part in path.parts for part in ignore_dirs):
            continue
        if path.name.startswith(".env") or path.suffix == ".json" or not path.is_file():
            continue
        # Skip this script itself
        if path.name == "secret_scanner.py":
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # ignore binary files
            
        for line_num, line in enumerate(content.splitlines(), 1):
            for name, regex in PATTERNS.items():
                match = re.search(regex, line, re.IGNORECASE)
                if match:
                    # Ignore comment patterns in code that explain regexes or examples
                    if "AIzaSy" in line and ("regex" in line or "example" in line or "dummy" in line):
                        continue
                    print(f"⚠️ [SECRET DETECTED] {path.relative_to(ROOT)}:L{line_num} "
                          f"matches '{name}': {match.group(0)}")
                    found_secrets = True

    return found_secrets

if __name__ == "__main__":
    print("🚀 Scanning workspace for accidental API keys or secrets...")
    if scan_files():
        print("❌ Secrets found! Please remove them before committing.")
        sys.exit(1)
    else:
        print("✅ No secrets detected. Codebase is clean!")
        sys.exit(0)
