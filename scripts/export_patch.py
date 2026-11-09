#!/usr/bin/env python3
"""Export tracked modifications and new source files without staging/committing."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/vtr"
DEST = ROOT / "patches/vtr-h3d.patch"


def main():
    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=SOURCE)
    names = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=SOURCE)
    for name in names.decode().strip("\0").split("\0"):
        if not name:
            continue
        result = subprocess.run(["git", "diff", "--no-index", "--binary", "--", "/dev/null", name],
                                cwd=SOURCE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 1:
            raise RuntimeError(result.stderr.decode())
        patch += result.stdout
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(patch)
    print(f"Wrote {len(patch)} bytes to {DEST}")


if __name__ == "__main__":
    main()
