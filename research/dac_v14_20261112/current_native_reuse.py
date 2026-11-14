"""Exact native request/state/objective reuse, separate from fresh acceptance."""
from pathlib import Path
from retained_prefix_workflow import D,read,sha,route_body
from run_native_scope_policy_v4 import run_dir

def match(role,batches):
 for batch in batches:
  batch=Path(batch)
  if not (batch/'registration.json').exists():continue
  reg=read(batch/'registration.json')
  for name,old in reg.get('roles',{}).items():
   if old.get('objective')!=role['objective'] or old.get('fixed_target_paths') or old.get('state')!=role['state'] or old.get('source')!=role['source']:continue
   if sha(old['request'])!=sha(role['request']):continue
   decision=batch/(name+'_decisions.json');native=batch/name/'completion.json';audit=batch/(name+'_audit/analysis.json')
   if not decision.exists() or not native.exists() or not audit.exists():continue
   nc=read(native);ac=read(audit)
   if not nc['passed'] or not ac.get('passed') or not ac.get('candidate_route'):continue
   evaluation=batch/(name+'_evaluation')
   if not (evaluation/'completion.json').exists():
    p=batch/'progress.json'
    if not p.exists():continue
    row=read(p).get(name,{})
    if row.get('status')!='legal_evaluated':continue
    evaluation=Path(row['evaluation'])
   ec=read(evaluation/'completion.json');assert ec['passed']
   for p,h in old['source_sha256'].items():assert sha(p)==h
   nr=run_dir(batch/name);manifest=read(nr/'manifest.json');binary=Path(manifest['command'][0]);assert sha(binary)==read(D/'native_objective_stage_01/binding.json')['binary_sha256']
   if float(manifest['environment'].get('VPR_CURRENT_STA_NATIVE_PRESSURE_START',1.))!=float(role.get('pressure_start',1.)):continue
   er=run_dir(evaluation);em=read(er/'manifest.json');assert em['metrics']['native_full_check_passed'] and read(er/'independent_audit.json')['audit']['passed']
   for n in ['packed.net','placed.place','routed.route']:assert sha(er/n)==em['outputs'][n]['sha256']
   assert sha(ac['candidate_route'])==ac['candidate_sha256'] and route_body(ac['candidate_route'])==route_body(er/'routed.route')
   assert read(Path(role['state'])/'endpoint_vector.json')['constraints_sha256']==read(evaluation/'endpoint_vector.json')['constraints_sha256']
   return dict(evaluation=str(evaluation),batch=str(batch),role=name,native_core_seconds=ac['native_transaction_seconds'],
    source_sha256={str(p):sha(p) for p in [batch/'registration.json',Path(old['request']),native,audit,evaluation/'completion.json',decision,er/'manifest.json',er/'independent_audit.json']},
    qualification='Reuse exact state-path/request bytes/objective/native binary and completed legal evaluation. Fresh policy acceptance uses this workflow current resources and original anchor. Historical creation time is excluded and remains attached to its original run.')
 return None

def failed_match(role,batches):
 """Reuse only a completed deterministic native capacity failure, not a timeout."""
 for batch in map(Path,batches):
  if not (batch/'registration.json').exists():continue
  for name,old in read(batch/'registration.json').get('roles',{}).items():
   if old.get('objective')!=role['objective'] or old.get('fixed_target_paths') or old.get('state')!=role['state'] or old.get('source')!=role['source']:continue
   if sha(old['request'])!=sha(role['request']):continue
   nc=batch/name/'completion.json';ac=batch/(name+'_audit/analysis.json')
   if not nc.exists() or not ac.exists():continue
   audit=read(ac)
   if not read(nc)['passed'] or not audit.get('passed') or audit.get('status')!='native_transaction_failed_no_candidate':continue
   for p,h in old['source_sha256'].items():assert sha(p)==h
   run=run_dir(batch/name);m=read(run/'manifest.json');assert sha(m['command'][0])==read(D/'native_objective_stage_01/binding.json')['binary_sha256']
   if float(m['environment'].get('VPR_CURRENT_STA_NATIVE_PRESSURE_START',1.))!=float(role.get('pressure_start',1.)):continue
   log=run/'joint_native.log';last=log.read_text().splitlines()[-1].split();assert last[0]=='COMPLETE' and last[1]=='0' and last[-1]=='occupancy_restored'
   return dict(batch=str(batch),role=name,status='identical_completed_native_failure',source_sha256={str(p):sha(p) for p in [batch/'registration.json',nc,ac,log]},qualification='Same state/request/objective/binary failed with occupancy restored. Process failures, missing output and timeouts are never treated as numerical failure reuse.')
 return None
