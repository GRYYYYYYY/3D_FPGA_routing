#!/usr/bin/env python3
"""Run registered joint controls; every child and failed candidate is accounted."""
import argparse,os,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import decide
parser=argparse.ArgumentParser();parser.add_argument('--batch',type=Path,required=True);args=parser.parse_args()
b=args.batch.resolve();reg=read(b/'registration.json');start=time.monotonic();costs=[];results={}
write(b/'runner_registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 source_sha256={str(p):sha(p) for p in [Path(__file__),D/'run_joint_native_state_analysis_v2.py',D/'audit_joint_native_repair_v2.py',D/'joint_native_repair_stage_02/binding.json',b/'registration.json']}))
def invoke(cmd,tag):
 t=time.monotonic();timed_out=False
 with (b/(tag+'.log')).open('w') as f:
  proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,command=cmd,returncode=code,timed_out=timed_out,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
 return code==0 and not timed_out
for role,r in reg['roles'].items():
 assert all(sha(p)==h for p,h in r['source_sha256'].items())
 ok=invoke([sys.executable,str(D/'run_joint_native_state_analysis_v2.py'),'--source',r['source'],'--batch',str(b/role),'--native-cases',r['request']],role+'_native')
 if not ok:
  results[role]=dict(status='native_integration_failed');write(b/'progress.json',results);break
 ok=invoke([sys.executable,str(D/'audit_joint_native_repair_v2.py'),'--batch',str(b),'--role',role],role+'_audit')
 if not ok:
  results[role]=dict(status='audit_failed');write(b/'progress.json',results);break
 audit=read(b/(role+'_audit')/'analysis.json')
 if not audit['candidate_route']:
  results[role]=dict(status='transaction_failed_rolled_back');write(b/'progress.json',results);continue
 evaluated=b/(role+'_evaluation')
 ok=invoke([sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',r['source'],'--batch',str(evaluated),'--candidate-route',audit['candidate_route']],role+'_evaluation')
 if not ok:
  results[role]=dict(status='candidate_evaluation_failed');write(b/'progress.json',results);continue
 before=read(Path(r['state'])/'endpoint_vector.json');after=read(evaluated/'endpoint_vector.json')
 decisions={p:decide(p,before,after,True) for p in ['strict','endpoint_vector']}
 write(b/(role+'_decision.json'),decisions)
 results[role]=dict(status='legal_candidate',cpd_ns=after['cpd_s']*1e9,decisions={p:dict(accepted=d['accepted'],reason=d['reason'],setup_improved=d['comparison']['setup_improved'],setup_regressed=d['comparison']['setup_regressed']) for p,d in decisions.items()},
   native_queries=len(audit['queries']),native_attempts=len(audit['attempts']),changed_connections=len(audit['changed_delays']))
 write(b/'progress.json',results);print(role,results[role],flush=True)
write(b/'completion.json',dict(status='comparison_terminal',roles=results,complete_orchestrator_seconds=time.monotonic()-start,
 all_roles_completed=len(results)==len(reg['roles']) and all(x['status']=='legal_candidate' for x in results.values()),
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'runner_registration.json',b/'process_costs.json',*b.glob('*_decision.json')]}))
