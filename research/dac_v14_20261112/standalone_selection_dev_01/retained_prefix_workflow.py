"""Portable exact serialization/identity helpers; no historical admission state."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')

def route_body(path):
    digest = hashlib.sha256()
    started = False
    with Path(path).open('rb') as stream:
        for line in stream:
            if line.startswith(b'Net '):
                started = True
            if started:
                digest.update(line)
    assert started
    return digest.hexdigest()
