#!/usr/bin/env python3
"""Build the pinned headless VPR through its Makefile and archive the binary."""

import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import time

from check_route import sha256

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ["-DVPR_USE_EZGL=off", "-DVPR_USE_SERVER=OFF", "-DWITH_PARMYS=ON",
          "-DWITH_MOSAIC=OFF", "-DSLANG_SYSTEMVERILOG=OFF", "-DWITH_ABC=OFF",
          "-DVTR_IPO_BUILD=off", "-DVPR_ENABLE_INTERCHANGE=ON"]


def capture(command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Artifact name, e.g. baseline or h3d")
    parser.add_argument("--jobs", type=int, default=16)
    parser.add_argument("--archive-existing", action="store_true", help="Record a build already completed with these flags")
    args = parser.parse_args()
    if not args.name.replace("-", "").replace("_", "").isalnum():
        parser.error("name must contain letters, digits, hyphens or underscores")
    lock = json.loads((ROOT / "configs/sources.lock.json").read_text())
    source = ROOT / lock["vtr"]["path"]
    if capture(["git", "rev-parse", "HEAD"], source) != lock["vtr"]["commit"]:
        raise RuntimeError("VTR commit does not match sources.lock.json")
    diff = capture(["git", "diff", "--binary"], source)
    status = capture(["git", "status", "--porcelain"], source)
    if args.name == "baseline" and status:
        raise RuntimeError("A baseline must have an unmodified source tree")
    destination = ROOT / "artifacts" / "bin" / args.name
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / "manifest.json").exists():
        raise RuntimeError(f"Refusing to overwrite archived build: {destination}")
    log = ROOT / "logs" / f"vtr-{args.name}-build.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    # Upstream's wrapper derives SOURCE_DIR from the inherited PWD variable,
    # which subprocess(cwd=...) alone does not update. Set its explicit input.
    command = ["make", f"-j{args.jobs}", "vpr", "SOURCE_DIR=" + str(source), "CMAKE_PARAMS=" + " ".join(PARAMS)]
    started = time.monotonic()
    if not args.archive_existing:
        with log.open("w") as stream:
            subprocess.run(command, cwd=source, stdout=stream, stderr=subprocess.STDOUT, check=True)
    binary = source / "build/vpr/vpr"
    if not binary.is_file():
        raise RuntimeError(f"Missing compiled executable: {binary}")
    shutil.copy2(binary, destination / "vpr")
    shutil.copy2(source / "build/CMakeCache.txt", destination / "CMakeCache.txt")
    if (source / "vpr/src/route/h3d_flute.cpp").exists():
        shutil.copy2(ROOT / "LICENSES/FLUTE-BSD3.txt", destination / "FLUTE-LICENSE.txt")
    (destination / "changes.patch").write_text(diff)
    # Include untracked new files in the review artifact without staging them.
    untracked = capture(["git", "ls-files", "--others", "--exclude-standard"], source)
    new_source_hashes = {}
    for name in untracked.splitlines():
        relative = Path(name)
        target = destination / "new_sources" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
        new_source_hashes[name] = sha256(target)
    result = {"schema": 1, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "commit": lock["vtr"]["commit"], "source_status": status,
              "command": command, "cwd": str(source), "binary_sha256": sha256(destination / "vpr"),
              "patch_sha256": sha256(destination / "changes.patch"),
              "new_source_sha256": new_source_hashes,
              "cache_sha256": sha256(destination / "CMakeCache.txt"),
              "compiler": capture(["g++", "--version"]).splitlines()[0],
              "cmake": capture(["cmake", "--version"]).splitlines()[0],
              "submodules": capture(["git", "submodule", "status"], source),
              "build_wall_seconds": None if args.archive_existing else time.monotonic() - started,
              "log": str(log), "archived_existing_build": args.archive_existing}
    (destination / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
