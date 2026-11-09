#!/usr/bin/env python3
"""Package reviewable source, experiment definitions and compact final evidence.

Large external source trees, binaries, XML RRGs, raw routes and per-net audits
remain in this workspace and are identified by their run manifests and hashes.
"""
import datetime
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    analysis = json.loads((ROOT / "results/analysis.json").read_text())
    queue = json.loads((ROOT / "results/final_validation_queue.json").read_text())
    if analysis["provisional"] or queue["stage"] != "ready_for_final_analysis":
        raise RuntimeError("Only final checked evidence can be packaged")
    files = [ROOT / "README.md", ROOT / ".gitignore"]
    for directory in ["scripts", "tests", "configs", "docs", "patches", "LICENSES"]:
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files.extend((ROOT / "benchmarks").glob("*.json"))
    files.extend(p for p in (ROOT / "results").glob("*") if p.is_file() and p.suffix in (".json", ".csv") and p.name != "delivery_manifest.json")
    files.extend((ROOT / "results/tiny_exact_congestion").glob("*"))
    files.extend((ROOT / "results/runs").glob("*/manifest.json"))
    files.extend((ROOT / "artifacts/bin").glob("*/manifest.json"))
    files.extend((ROOT / "artifacts/bin").glob("*/changes.patch"))
    files.extend((ROOT / "artifacts/bin").glob("*/FLUTE-LICENSE.txt"))
    files.extend(p for p in (ROOT / "artifacts/bin").glob("*/new_sources/**/*") if p.is_file())
    files.append(ROOT / "artifacts/python-environment.txt")
    files.extend((ROOT / "artifacts/sources").glob("*.json"))
    files = sorted(set(p for p in files if p.is_file()))
    index = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "runs": len(analysis["rows"]),
             "scope": __doc__, "files": [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": digest(p)} for p in files]}
    destination = ROOT / "artifacts/h3d-native3d-research.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, str(path.relative_to(ROOT)))
        archive.writestr("PACKAGE_MANIFEST.json", json.dumps(index, indent=2) + "\n")
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
    result = {"path": str(destination), "sha256": digest(destination), "bytes": destination.stat().st_size,
              "files": len(files), "runs": len(analysis["rows"]), "provisional": False}
    (ROOT / "results/delivery_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
