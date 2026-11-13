#!/usr/bin/env python3
"""Recover a verifier schema rejection without repeating completed native runs."""
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
assert not Path(f"/proc/{reg['pid']}").exists()
assert json.loads((D/'estimate_trace_queue_state.json').read_text())['returncode']==1
assert not (B/'input_seal.json').exists() and not (B/'runs/eltwise_layer_Rq').exists()
write_json(B/'recovery_identity.json',dict(pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],original_pid=reg['pid'],purpose='Verifier schema compatibility; retain failed check, reuse completed native executions, launch only previously missing eltwise Rq',script_sha256=sha256(__file__)))
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
def body(rd):
 text=(rd/'routed.route').read_text();assert 'Net ' in text
 return hashlib.sha256(text[text.index('Net '):].encode()).hexdigest()
def canonical(rd):
 rows=[]
 for line in records(rd,'H3D_PERSISTENT_DELAY '):
  r={k:int(v) for k,v in (x.split('=') for x in line.split()[1:])}
  assert r.get('retain',1)==1 and r.get('discards',0)==0
  if 'live_states' in r:assert 0<=r['live_states']<=r['slots']
  for k in ['retain','discards','live_states']:r.pop(k,None)
  rows.append(r)
 return rows

def equivalence(rd,prior):
 for fn in ['manifest.json','stdout.log','routed.route','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']:io.frozen_hash(prior/fn)
 assert json.loads((prior.parent.parent/'input_seal.json').read_text())['passed']
 m=json.loads((rd/'manifest.json').read_text());pm=json.loads((prior/'manifest.json').read_text())
 checks=dict(route_body=body(rd)==body(prior),metrics=all(m['metrics'][k]==pm['metrics'][k] for k in ['critical_path_ns','wirelength','iterations']),tables=records(rd,'H3D_TABLE ')==records(prior,'H3D_TABLE '),guides=sha256(rd/'h3d_final_guides.csv')==sha256(prior/'h3d_final_guides.csv'),persistent_common_fields=canonical(rd)==canonical(prior))
 for prefix in ['H3D_TARGET_DELAY ','H3D_SELECTED_DELAY ','H3D_REVERSE_TARGETS ']:checks[prefix.strip()]=records(rd,prefix)==records(prior,prefix)
 for fn in ['packed.net','placed.place']:assert sha256(rd/fn)==sha256(prior/fn)
 path=rd/'estimate_equivalence.json'
 if path.exists():
  backup=rd/'estimate_equivalence_initial_schema_rejection.json';assert not backup.exists();shutil.copy2(path,backup)
 write_json(path,dict(passed=all(checks.values()),checks=checks,reference=str(prior),schema_reconciliation='Old persistent log predates retain/discards/live_states. All common per-iteration counters exact; retain1/discards0 asserted and new live_states within slots. Original raw-string rejection retained separately.',recovery_script_sha256=sha256(__file__)))
 assert all(checks.values())
rd=B/'runs/eltwise_layer_P';prior=D/'persistent_expansion_dev_01/runs/eltwise_layer_P';equivalence(rd,prior)
old=json.loads((rd/'manifest.json').read_text());new=B/'runs/eltwise_layer_Rq';new.mkdir()
for fn in ['packed.net','placed.place']:shutil.copy2(rd/fn,new/fn)
cmd=list(old['command'])
for opt,fn in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(new/fn)
env=dict(old['environment'],VPR_H3D_REVERSE_RERANK='1')
assert shutil.disk_usage(B).free>=80*1024**3
receipt=io.run(new.name,cmd,environment=env,timeout=1800,frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],B/'registration.json',B/'recovery_runner.py',rd/'packed.net',rd/'placed.place'],private_inputs=[new/'packed.net',new/'placed.place'],tags=dict(circuit='eltwise_layer',arm='Rq',phase='development_diagnostic',hypothesis='estimate_error_without_decision_changes'))
assert receipt['status']=='completed'
checks=dict(packed_identical=sha256(new/'packed.net')==sha256(rd/'packed.net'),placement_identical=placements(new/'placed.place')==placements(rd/'placed.place'))
write_json(new/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(rd)));assert all(checks.values())
equivalence(new,D/'reverse_rerank_expansion_dev_01/runs/eltwise_layer_Rq')
study.BASE=B;study.audit_batch(study.context('eltwise_layer','hybrid_o',11,100),[old,receipt],B/'eltwise_layer_audit.json')
for p in [rd,new]:guide_audit(p)
rows=[]
for circuit in reg['circuits']:
 for arm,ref in json.loads((B/f'{circuit}_references.json').read_text()).items():rows.append(dict(circuit=circuit,arm=arm,**ref))
 for arm in reg['arms']:
  p=B/'runs'/f'{circuit}_{arm}';m=json.loads((p/'manifest.json').read_text());a=json.loads((p/'independent_audit.json').read_text());assert a['audit']['passed'] and json.loads((p/'estimate_equivalence.json').read_text())['passed']
  rows.append(dict(circuit=circuit,arm=arm,status='legal',metrics=m['metrics'],physical_metrics=a['physical_metrics'],process_seconds=m['wall_seconds'],path=str(p),diagnostic_only=True))
write_json(B/'observations.json',rows)
io.frozen_hash(B/'recovery_runner.py');io.seal_inputs(B/'input_seal.json')
write_json(B/'completion.json',dict(utc=utc(),status='recovered_diagnostic_batch_complete_not_research_complete',reused_native=3,new_native=1,observations=len(rows)))
print('recovered: three native runs reused, one previously missing run completed, all audits and seal passed')
