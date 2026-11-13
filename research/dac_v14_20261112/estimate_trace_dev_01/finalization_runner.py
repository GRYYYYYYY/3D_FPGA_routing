#!/usr/bin/env python3
"""Finalize independent audits without any new native run."""
from pathlib import Path
import fcntl, hashlib, json, os, shutil, sys, time
D=Path(__file__).resolve().parent;R=D.parents[1];B=D/'estimate_trace_dev_01';OLD=R/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(R/'scripts'),str(D)]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from lazagna_common import sha256,write_json,utc
from audit_final_guides import audit as guide_audit
from validate_lazagna_vtr9_pilot import placements
lock=(D/'estimate_trace_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=json.loads((B/'registration.json').read_text())
assert not (B/'input_seal.json').exists()
for mp in (B/'runs').glob('*/manifest.json'):assert json.loads(mp.read_text())['status']=='completed'
assert len(list((B/'runs').glob('*/manifest.json')))==4
write_json(B/'finalization_identity.json',dict(pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],purpose='Audit-only finalization after context BASE initialization error; no native run launched',script_sha256=sha256(__file__)))
shutil.copy2(__file__,B/'finalization_runner.py')
io.BASE=B
# Reconstruct and finally rehash every declared input, not just the last run.
for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
for rel,h in reg['source_sha256'].items():io.frozen_hash(B/'source'/Path(rel).name,h)
for mp in (B/'runs').glob('*/manifest.json'):
 m=json.loads(mp.read_text());assert m['status']=='completed'
 for p,record in m['shared_inputs'].items():io.frozen_hash(p,record['sha256'])
 for f,h in m['private_input_sha256'].items():assert sha256(f)==h
 for f,record in m['outputs'].items():assert sha256(mp.parent/f)==record['sha256']
for c in reg['circuits']:
 refs=json.loads((B/f'{c}_references.json').read_text())
 for ref in refs.values():
  p=Path(ref['path']);io.frozen_hash(p/'manifest.json',ref['manifest_sha256'])
  m=json.loads((p/'manifest.json').read_text())
  for inp,h in m['shared_inputs'].items():io.frozen_hash(inp,h['sha256'])
  for fn in ['packed.net','placed.place','routed.route','independent_audit.json']:
   if (p/fn).exists():io.frozen_hash(p/fn)

for mp in (B/'runs').glob('*/manifest.json'):
 rd=mp.parent;eq=json.loads((rd/'estimate_equivalence.json').read_text());assert eq['passed']
 prior=Path(eq['reference']);assert json.loads((prior.parent.parent/'input_seal.json').read_text())['passed']
 for fn in ['manifest.json','stdout.log','routed.route','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']:io.frozen_hash(prior/fn)
 for fn in ['packed.net','placed.place']:assert sha256(rd/fn)==sha256(prior/fn)
 io.frozen_hash(rd/'estimate_equivalence.json')
ctx=study.context('eltwise_layer','hybrid_o',11,100)
study.BASE=B
receipts=[json.loads((B/'runs'/f'eltwise_layer_{a}'/'manifest.json').read_text()) for a in ['P','Rq']]
study.audit_batch(ctx,receipts,B/'eltwise_layer_audit.json')
for a in ['P','Rq']:guide_audit(B/'runs'/f'eltwise_layer_{a}')
rows=[]
for circuit in reg['circuits']:
 for arm,ref in json.loads((B/f'{circuit}_references.json').read_text()).items():rows.append(dict(circuit=circuit,arm=arm,**ref))
 for arm in reg['arms']:
  p=B/'runs'/f'{circuit}_{arm}';m=json.loads((p/'manifest.json').read_text());a=json.loads((p/'independent_audit.json').read_text());assert a['audit']['passed'] and json.loads((p/'estimate_equivalence.json').read_text())['passed']
  rows.append(dict(circuit=circuit,arm=arm,status='legal',metrics=m['metrics'],physical_metrics=a['physical_metrics'],process_seconds=m['wall_seconds'],path=str(p),diagnostic_only=True))
write_json(B/'observations.json',rows)
io.frozen_hash(B/'recovery_runner.py');io.frozen_hash(B/'finalization_runner.py');io.seal_inputs(B/'input_seal.json')
write_json(B/'completion.json',dict(utc=utc(),status='recovered_diagnostic_batch_complete_not_research_complete',reused_native=3,new_native=1,observations=len(rows)))
print('finalized without any new native run: all four routes, audits, equivalence and seal passed')
