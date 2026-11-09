#!/usr/bin/env python3
"""Resume the published artifact in checked byte ranges without losing progress."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://zenodo.org/records/19204522/files/pathSteiner.tar.gz?download=1"
SIZE = 3101706050
MD5 = "6fe5e7dab197601b059ab689977d8545"


def main():
    path = ROOT / "artifacts/sources/pathSteiner.tar.gz"
    lock = path.with_suffix(".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    failures = 0
    while path.stat().st_size < SIZE:
        offset = path.stat().st_size
        end = min(SIZE - 1, offset + 64 * 1024 * 1024 - 1)
        request = urllib.request.Request(URL + f"&range_start={offset}", headers={"Range": f"bytes={offset}-{end}", "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                if response.status != 206 or not match or int(match[1]) != offset or int(match[3]) != SIZE:
                    raise ValueError("Server did not return the requested, size-matched byte range")
                remaining = end - offset + 1
                with path.open("ab") as output:
                    while remaining:
                        chunk = response.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise EOFError("Incomplete range; retained received prefix")
                        output.write(chunk)
                        remaining -= len(chunk)
            failures = 0
            print(json.dumps({"bytes": path.stat().st_size, "total": SIZE}), flush=True)
        except Exception as error:
            failures += 1
            print(json.dumps({"error": str(error), "retained_bytes": path.stat().st_size, "consecutive_failures": failures}), flush=True)
            if failures >= 10:
                raise
            time.sleep(min(30, failures * 3))
    digest = hashlib.md5()
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            sha.update(chunk)
    if path.stat().st_size != SIZE or digest.hexdigest() != MD5:
        raise ValueError("Published artifact checksum does not match")
    record = {"url": URL, "bytes": SIZE, "published_md5": MD5, "verified_md5": digest.hexdigest(), "sha256": sha.hexdigest()}
    path.with_suffix(".verified.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
