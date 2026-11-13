#!/usr/bin/env python3
"""Check every evidence archive member against its embedded SHA-256 manifest."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, tarfile
P=Path(__file__).resolve().parent
archive=P/'build/dac2027-evidence-20261110.tar.gz'
receipt=json.loads((P/'data/final_archive_receipt.json').read_text())
def digest(stream):
    h=hashlib.sha256()
    for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
with archive.open('rb') as stream: outer=digest(stream)
if outer != receipt['archive_sha256']: raise RuntimeError('Archive digest differs from receipt')
actual={};manifest=None
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        if not member.isfile(): raise RuntimeError(f'Unexpected archive member: {member.name}')
        f=tar.extractfile(member)
        if member.name=='DAC2027_EVIDENCE_MANIFEST.json':
            if manifest is not None: raise RuntimeError('Duplicate embedded manifest')
            manifest=json.load(f)
        else:
            if member.name in actual: raise RuntimeError(f'Duplicate: {member.name}')
            actual[member.name]=digest(f)
if manifest is None or actual != manifest['files'] or len(actual) != receipt['file_count']:
    raise RuntimeError('Archive member hashes or coverage do not match manifest and receipt')
result=dict(utc=datetime.now(timezone.utc).isoformat(),passed=True,archive_sha256=outer,
            verified_files=len(actual),deferred_audit_passed=manifest['deferred_file_audit_passed'],scope=manifest['scope'])
out=P/'data/final_archive_verification.json'
if out.exists(): raise RuntimeError('Existing verification receipt preserved')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
