#!/usr/bin/env python3
"""Package only the paper workspace, retaining earlier versioned archives."""
from pathlib import Path
import argparse, datetime, hashlib, json, re, tarfile

P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--version',required=True,help='e.g. 20261110-v2; existing archives are never overwritten')
args=parser.parse_args()
if not re.fullmatch(r'\d{8}(?:-v\d+)?',args.version):
    parser.error('version must be YYYYMMDD or YYYYMMDD-vN')
archive=P/'build'/f'dac2027-draft-{args.version}.tar.gz'
if archive.exists():
    parser.error(f'already exists: {archive}')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
verification=json.loads((P/'build/verification.json').read_text())
assert verification['status']=='passed' and all(c['passed'] for c in verification['checks'])
for name,sha in verification['reviewed_artifacts_sha256'].items():
    assert digest(P/name)==sha, f'changed since verification: {name}'
files=[p for p in P.iterdir() if p.is_file() and (p.suffix in ['.md','.py','.sh','.tex','.cls','.txt'] or p.name=='.gitignore')]
files += [p for directory in ['data','figures'] for p in (P/directory).iterdir() if p.is_file() and p.suffix in ['.json','.jsonl','.csv','.pdf','.png']]
files += [p for p in (P/'provenance').iterdir() if p.is_file() and p.suffix in ['.patch','.py','.md','.txt']]
files += [P/'build/main.pdf',P/'build/verification.json']
files += [p for p in (P/'build/deferred_file_integrity').glob('*') if p.is_file()]
files=sorted(files)
remaining=['DP causal control remains unexecuted','full per-pin physical audit and clean-environment bit reproduction unavailable','final per-connection guide-adoption trace unavailable','author/COI and registration metadata','final author review at later submission milestones']
archive_verification=P/'data/final_archive_verification.json'
if not archive_verification.is_file() or not json.loads(archive_verification.read_text()).get('passed'):
    remaining.insert(0,'independent evidence archive readback verification pending')
manifest=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),version=args.version,purpose='DAC2027 manuscript and audit receipts; separate evidence archive retains logs',body_pages=6,references_pages=1,abstract_words=verification['abstract_words'],checks_passed=len(verification['checks']),visual_review='All seven pages reviewed previously; updated mechanism page inspected again. No clipping/overfull boxes; IEEE Times fonts embedded.',experiment_changes='none; all deliverables in independent paper/dac2027',file_count=len(files)+2,remaining=remaining,compiler=dict(name='Tectonic',version='0.17.0',class_name='IEEEtran',class_version='1.8b',class_source='https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/IEEEtran.cls'),source_archive=str(archive.relative_to(P)))
manifest_path=P/'delivery_manifest.json'
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
files.append(manifest_path)
sums={str(p.relative_to(P)):digest(p) for p in files}
checksum=P/'SHA256SUMS'
checksum.write_text(''.join(f'{sha}  {name}\n' for name,sha in sorted(sums.items())))
files.append(checksum)
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(files):tar.add(p,arcname='dac2027/'+str(p.relative_to(P)),recursive=False)
with tarfile.open(archive,'r:gz') as tar:
    assert len(tar.getmembers())==manifest['file_count']
    for name,sha in sums.items():
        assert hashlib.sha256(tar.extractfile('dac2027/'+name).read()).hexdigest()==sha,name
print(json.dumps(dict(archive=str(archive),files=manifest['file_count'],bytes=archive.stat().st_size,sha256=digest(archive),checks=manifest['checks_passed']),indent=2))
