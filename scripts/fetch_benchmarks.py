#!/usr/bin/env python3
"""Fetch the 20 published Beyond-Flatland Koios BLIFs at an immutable commit."""

from collections import Counter
import concurrent.futures
import json
from pathlib import Path
import re
import tarfile
import urllib.request

from check_route import sha256

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "84ba44acf1bad597bc5a9d1f615415870e178a86"
REPO = "IY2002/Beyond-Flatland"
DEST = ROOT / "benchmarks/downloads/beyond_flatland"


def fetch_one(item):
    name = item["name"]
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.blif\.tar\.gz", name):
        raise ValueError(f"Unexpected benchmark file: {name}")
    archive = DEST / name
    url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/Benchmarks/{name}"
    if not archive.exists():
        temporary = archive.with_suffix(".partial")
        with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        temporary.rename(archive)
    blifs = []
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.endswith(".blif"):
                continue
            # Read only file bytes and choose our own safe destination path.
            path = DEST / Path(member.name).name
            with tar.extractfile(member) as stream:
                content = stream.read()
            path.write_bytes(content)
            models = Counter(re.findall(rb"^\.subckt\s+(\S+)", content, re.MULTILINE))
            blifs.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                          "bytes": len(content), "subckt_models": {k.decode(): v for k, v in models.items()}})
    if len(blifs) != 1:
        raise ValueError(f"Expected exactly one BLIF in {name}, found {len(blifs)}")
    return {"archive": str(archive.relative_to(ROOT)), "url": url,
            "archive_sha256": sha256(archive), "files": blifs}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    api = f"https://api.github.com/repos/{REPO}/contents/Benchmarks?ref={COMMIT}"
    with urllib.request.urlopen(api, timeout=60) as response:
        listing = json.load(response)
    items = [item for item in listing if item["name"].endswith(".blif.tar.gz")]
    if len(items) != 20:
        raise ValueError(f"Expected published 20-circuit set, found {len(items)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch_one, items))
    result = {"repository": f"https://github.com/{REPO}", "commit": COMMIT,
              "files": sorted(records, key=lambda r: r["archive"]),
              "note": "Original benchmark bytes; compatibility with a native CHANZ architecture must be checked before use."}
    (ROOT / "benchmarks/beyond_flatland.lock.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"downloaded": len(records), "bytes": sum(r["files"][0]["bytes"] for r in records)}))


if __name__ == "__main__":
    main()
