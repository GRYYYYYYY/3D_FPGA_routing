#!/usr/bin/env python3
"""Run actual native repairs; reuse candidate FULL/STA only after exact proof."""
import os,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import decide

b=D/'current_sta_near_native_dev_01';reg=read(b/'registration.json');started=time.monotonic();costs=[];results={}
write(b/'runner_registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 source_sha256={str(p):sha(p) for p in [Path(__file__),D/'compare_native_candidate_reference.py',D/'run_joint_native_state_analysis_v2.py',D/'audit_joint_native_repair_v2.py',D/'run_endpoint_state_analysis.py',b/'registration.json']}))
def invoke(script,arguments,tag):
 command=[sys.executable,str(D/script),*arguments];t=time.monotonic();timed_out=False
 with (b/(tag+'.log')).open('w') as f:
  proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,command=command,returncode=code,timed_out=timed_out,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
 return code==0 and not timed_out
for role,r in reg['roles'].items():
 assert all(sha(p)==h for p,h in r['source_sha256'].items())
 ok=invoke('run_joint_native_state_analysis_v2.py',['--source',r['source'],'--batch',str(b/role),'--native-cases',r['request']],role+'_native')
 if ok:ok=invoke('compare_native_candidate_reference.py',['--batch',str(b),'--role',role],role+'_equivalence')
 if not ok:
  results[role]=dict(status='native_or_equivalence_failed');write(b/'progress.json',results);continue
 eq=read(b/(role+'_reference_equivalence.json'))
 if eq['identical']:
  evaluation=Path(eq['reused_state']);audit=eq;reused=True
 else:
  ok=invoke('audit_joint_native_repair_v2.py',['--batch',str(b),'--role',role],role+'_audit')
  if not ok:
   results[role]=dict(status='audit_failed');write(b/'progress.json',results);continue
  audit=read(b/(role+'_audit')/'analysis.json')
  if not audit['candidate_route']:
   results[role]=dict(status='transaction_failed_rolled_back');write(b/'progress.json',results);continue
  evaluation=b/(role+'_evaluation');reused=False
  ok=invoke('run_endpoint_state_analysis.py',['--source',r['source'],'--batch',str(evaluation),'--candidate-route',audit['candidate_route']],role+'_evaluation')
  if not ok:
   results[role]=dict(status='evaluation_failed');write(b/'progress.json',results);continue
 before=read(Path(r['state'])/'endpoint_vector.json');after=read(evaluation/'endpoint_vector.json')
 decisions={p:decide(p,before,after,True) for p in ['strict','endpoint_vector']};write(b/(role+'_decision.json'),decisions)
 results[role]=dict(status='legal_candidate',evaluation_state=str(evaluation),reused_candidate_FULL_STA=reused,cpd_ns=after['cpd_s']*1e9,
  native_queries=len(audit['queries']),native_attempts=len(audit['attempts']),native_transaction_seconds=audit['native_transaction_seconds'],
  decisions={p:dict(accepted=d['accepted'],reason=d['reason'],setup_improved=d['comparison']['setup_improved'],setup_regressed=d['comparison']['setup_regressed']) for p,d in decisions.items()})
 write(b/'progress.json',results);print(role,results[role],flush=True)
write(b/'completion.json',dict(status='comparison_terminal',roles=results,complete_orchestrator_seconds=time.monotonic()-started,
 all_roles_completed=len(results)==len(reg['roles']) and all(r['status']=='legal_candidate' for r in results.values()),
 qualification='Native searches are new; identical completed physical candidates reuse previously certified FULL/STA with exact-tree proof. Reused evaluation costs are excluded from incremental time and must be included for independent cold-start algorithm timing.',
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'runner_registration.json',b/'process_costs.json',*b.glob('*_decision.json'),*b.glob('*_reference_equivalence.json')]}))
