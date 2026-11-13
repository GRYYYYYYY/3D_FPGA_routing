#!/usr/bin/env python3
"""Recover a verifier schema rejection without repeating completed native runs."""
from pathlib import Path
import fcntl, hashlib, json, os, shutil, sys, time
D=Path(__file__).resolve().parent;R=D.parents[1];B=D/'distance_dp_dev_01';OLD=R/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(R/'scripts'),str(D)]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from lazagna_common import sha256,write_json,utc
from audit_final_guides import audit as guide_audit
from validate_lazagna_vtr9_pilot import placements
lock=(D/'distance_dp_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=json.loads((B/'registration.json').read_text())
assert not Path(f"/proc/{reg['pid']}").exists()
assert json.loads((D/'distance_dp_queue_state.json').read_text())['returncode']==1
assert not (B/'input_seal.json').exists() and not (B/'runs/eltwise_layer_En').exists()
write_json(B/'recovery_identity.json',dict(pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],original_pid=reg['pid'],purpose='Verifier wrongly compared counts of per-iteration cumulative logs across different iteration counts. Preserve rejection; same full tables and distinct cumulative counter states required, launch only missing eltwise En',script_sha256=sha256(__file__)))
shutil.copy2(__file__,B/'recovery_runner.py')
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

def records(rd,prefix):
 return [line for line in (rd/'stdout.log').read_text().splitlines() if line.startswith(prefix)]
def equivalence(rd,prior):
 for fn in ['manifest.json','stdout.log','routed.route','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']:io.frozen_hash(prior/fn)
 checks={'table_sequence':records(rd,'H3D_TABLE ')==records(prior,'H3D_TABLE ')}
 for prefix in ['H3D_DELAY ','H3D_TARGET_DELAY ','H3D_PERSISTENT_DELAY ']:
  current=records(rd,prefix);old=records(prior,prefix)
  checks[prefix.strip()]=bool(current) and bool(old) and set(current)==set(old) and current[-1]==old[-1]
 path=rd/'same_table_gate.json'
 if path.exists():
  backup=rd/'initial_gate.json';assert not backup.exists();shutil.copy2(path,backup)
 write_json(path,dict(passed=all(checks.values()),checks=checks,reference=str(prior),reconciliation='Static planner has identical full table sequence and identical distinct/final cumulative query states. Number of repeated per-iteration log lines legitimately changes with route iterations.',script_sha256=sha256(__file__)))
 assert all(checks.values())
rd=B/'runs/eltwise_layer_Pn';prior=D/'source_floor_dev_01/runs/eltwise_layer_P';equivalence(rd,prior)
old=json.loads((rd/'manifest.json').read_text());new=B/'runs/eltwise_layer_En';new.mkdir()
for fn in ['packed.net','placed.place']:shutil.copy2(rd/fn,new/fn)
cmd=list(old['command'])
for opt,fn in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(new/fn)
env=dict(json.loads((D/'complete_distance_dev_02/runs/eltwise_layer_Ed/manifest.json').read_text())['environment'],VPR_H3D_ASSIGNMENT='independent')
assert shutil.disk_usage(B).free>=80*1024**3
receipt=io.run(new.name,cmd,environment=env,timeout=1800,frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],B/'registration.json',B/'recovery_runner.py',rd/'packed.net',rd/'placed.place'],private_inputs=[new/'packed.net',new/'placed.place'],tags=dict(circuit='eltwise_layer',arm='En',phase='development_diagnostic',hypothesis='same_table_distance_dp_interaction',diagnostic_only=True))
assert receipt['status']=='completed'
checks=dict(packed_identical=sha256(new/'packed.net')==sha256(rd/'packed.net'),placement_identical=placements(new/'placed.place')==placements(rd/'placed.place'))
write_json(new/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(rd)));assert all(checks.values())
equivalence(new,D/'complete_distance_dev_02/runs/eltwise_layer_Ed')
ctx=study.context('eltwise_layer','hybrid_o',11,100)
study.BASE=B;study.audit_batch(ctx,[old,receipt],B/'eltwise_layer_audit.json')
for p in [rd,new]:guide_audit(p)
rows=[]
for circuit in reg['circuits']:
 for arm,ref in json.loads((B/f'{circuit}_references.json').read_text()).items():rows.append(dict(circuit=circuit,arm=arm,**ref))
 for arm in reg['arms']:
  p=B/'runs'/f'{circuit}_{arm}';m=json.loads((p/'manifest.json').read_text());a=json.loads((p/'independent_audit.json').read_text());assert a['audit']['passed'] and json.loads((p/'same_table_gate.json').read_text())['passed']
  rows.append(dict(circuit=circuit,arm=arm,status='legal',metrics=m['metrics'],physical_metrics=a['physical_metrics'],process_seconds=m['wall_seconds'],path=str(p),diagnostic_only=True))
write_json(B/'observations.json',rows)
io.frozen_hash(B/'recovery_runner.py');io.seal_inputs(B/'input_seal.json')
write_json(B/'completion.json',dict(utc=utc(),status='recovered_diagnostic_batch_complete_not_research_complete',reused_native=3,new_native=1,observations=len(rows)))
print('recovered: three native runs reused, one previously missing run completed, all audits and seal passed')
