#!/usr/bin/env python3
"""Create a new evidence archive after the registered large-file audit terminates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, io, json, os, tarfile

P=Path(__file__).resolve().parent;ROOT=P.parents[1]
A=ROOT/'results/architecture_flow_20261027';B=A/'serial_strict_reexecution_20261103'
OUT=P/'build/dac2027-evidence-20261110.tar.gz'
summary_path=P/'build/deferred_file_integrity/summary.json'
if not summary_path.is_file():raise SystemExit('Deferred-file audit has not completed; archive not created')
summary=json.loads(summary_path.read_text());files=set()
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():files.add(p)
def tree(p):
 for f in Path(p).rglob('*'):
  if '__pycache__' not in f.parts:add(f)
# Full strict-study schedules, terminal case records, analysis and independent source scripts.
for name in ['execution_scripts','paired_width_cases','evaluation_cases','balance_cases','serial_cases','training_cases','evaluation_analysis','serial_analysis','balance_analysis','paired_width_analysis','training_analysis','parallel_continuation_v1']:
 tree(B/name)
for p in B.iterdir():
 if p.is_file() and p.suffix in {'.json','.md','.html','.csv'}:add(p)
for run in (B/'runs').iterdir():
 if not run.is_dir():continue
 for name in ['manifest.json','stdout.log','stderr.log','thread_syscalls.log','time.txt','pair_check.json','placement_check.json','off_equivalence.json','balance_audit.json']:
  add(run/name)
 for log in run.glob('*.log'):add(log)
 # The partition bridge records exact TCL, input/output digest, and partition logs.
 tree(run/'triton_evidence')
for f in ['requirements.json','benchmark_protocol.json','partition_balance_sensitivity_protocol.json','closure_archive_20261103.tar.gz','closure_archive_manifest_20261103.json','native_router_dependencies.json']:
 add(A/f)
for f in ['configs/sources.lock.json','benchmarks/beyond_flatland.lock.json','docs/github_snapshot_manifest_20261109.json']:
 add(ROOT/f)
for f in ['serial_candidate_artifacts_20261103.json','openroad_partition_serial_candidate.patch','run_serial_triton_bridge.py','a0_copied_submodules_verification.json','a0_nested_submodules_verification.json']:
 add(A/'single_thread_candidate_20261103'/f)
for d in ['data','figures','provenance']:
 tree(P/d)
for f in P.iterdir():
 if f.is_file() and f.name not in {'SHA256SUMS','delivery_manifest.json'}:add(f)
for f in [P/'build/main.pdf',P/'build/verification.json',summary_path,P/'build/deferred_file_integrity/results.jsonl',P/'build/deferred_file_integrity/registration.json']:
 add(f)
if OUT.exists():raise SystemExit('Evidence archive already exists; preserve it and choose a new version')
manifest=dict(utc=datetime.now(timezone.utc).isoformat(),file_count=len(files),deferred_file_audit_passed=summary['passed'],deferred_file_audit_failures=summary['failed'],scope='Strict-study receipts, failure and timeout logs, registered analyses, paper and exported source patches. Large RRG, packed netlists, route files and detailed per-net audits are retained at original shared-storage paths and bound by the included input-binding manifests; they are not copied into this archive. Prior study archive is included.',files={})
def stable_digest(p):
 h=hashlib.sha256();before=p.stat()
 with p.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 after=p.stat()
 if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise RuntimeError(f'File changed: {p}')
 return h.hexdigest()
with OUT.open('xb') as output:
 with tarfile.open(fileobj=output,mode='w:gz') as archive:
  for i,p in enumerate(sorted(files),1):
   name=str(p.relative_to(ROOT));digest=stable_digest(p);archive.add(p,arcname=name,recursive=False)
   if stable_digest(p)!=digest:raise RuntimeError(f'File changed while archiving: {p}')
   manifest['files'][name]=digest
   if i%1000==0:print('archived',i,'/',len(files),flush=True)
  blob=(json.dumps(manifest,indent=2)+'\n').encode();info=tarfile.TarInfo('DAC2027_EVIDENCE_MANIFEST.json');info.size=len(blob);archive.addfile(info,io.BytesIO(blob))
archive_sha=stable_digest(OUT)
receipt=dict(utc=datetime.now(timezone.utc).isoformat(),archive=str(OUT),archive_sha256=archive_sha,bytes=OUT.stat().st_size,file_count=len(files),audit_passed=summary['passed'],scope=manifest['scope'])
(P/'data/final_archive_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2),flush=True)
