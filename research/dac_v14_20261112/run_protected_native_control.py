#!/usr/bin/env python3
"""Evaluate automatically generated protected-prefix scope with native free paths."""
import argparse,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import decide

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--opportunity',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
state=a.state.resolve();source=Path(read(state/'completion.json')['run']);b=a.batch.resolve();b.mkdir(exist_ok=False);op=read(a.opportunity)
files=[Path(__file__),a.opportunity,a.opportunity.parent/'candidate_binding.json',state/'completion.json',state/'endpoint_vector.json',D/'native_objective_stage_01/binding.json',*[D/n for n in ['prepare_native_scope_request.py','run_native_objective_state_analysis.py','audit_native_objective.py','run_endpoint_state_analysis.py','endpoint_timing_policy.py']]]
bindings={str(p):sha(p) for p in files};calls=[]
write(b/'registration.json',dict(status='registered_before_work',state=str(state),opportunity=str(a.opportunity),pid=os.getpid(),
 question='Can protection of the current near-critical victim prefix avoid the observed CPD regression while preserving the two target improvements?',
 objective='weighted_soft',acceptance_policies=['strict','endpoint_vector'],source_sha256=bindings,limits=dict(seconds_per_child=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
def invoke(script,args,tag):
 assert shutil.disk_usage(D).free>=80*1024**3
 t=time.monotonic();cmd=[sys.executable,str(D/script),*map(str,args)];status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=1800);status='completed' if code==0 else 'failed'
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 calls.append(dict(tag=tag,command=cmd,status=status,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',calls)
 assert status=='completed',(script,status)
work=b/'transaction'
invoke('prepare_native_scope_request.py',['--state',state,'--opportunity',a.opportunity,'--batch',work,'--scope','conflict'],'scope')
scope=read(work/'registration.json')['roles']['candidate']
for pin in op['protected_pins']:assert pin['pin'] not in scope['removed_pins'].get(str(pin['net']),[]),'Generated scope would release protected sink'
write(b/'protected_scope_check.json',dict(passed=True,protected_pins=op['protected_pins'],scope_registration_sha256=sha(work/'registration.json'),qualification='Protected pins remain connected; native pruning must preserve their complete existing prefixes. All retained edges checked in candidate audit.'))
invoke('run_native_objective_state_analysis.py',['--source',source,'--batch',work/'candidate','--native-cases',work/'candidate.txt','--objective','weighted_soft'],'native')
invoke('audit_native_objective.py',['--batch',work,'--role','candidate'],'audit')
audit=read(work/'candidate_audit/analysis.json');candidate=audit.get('candidate_route');decisions={};evaluated=None;reused=False
if candidate:
 if route_body(candidate)==route_body(source/'routed.route'):
  evaluated=state;reused=True
 else:
  evaluated=b/'evaluation';invoke('run_endpoint_state_analysis.py',['--source',source,'--batch',evaluated,'--candidate-route',candidate],'evaluation')
 assert read(evaluated/'completion.json')['passed']
 decisions={name:decide(name,read(state/'endpoint_vector.json'),read(evaluated/'endpoint_vector.json'),True,evaluated==state) for name in ['strict','endpoint_vector']}
 write(b/'decisions.json',decisions)
for name in ['strict','endpoint_vector']:
 current=evaluated if decisions.get(name,{}).get('accepted') else state
 write(b/(name+'_current.json'),dict(state=str(current),cpd_s=read(current/'endpoint_vector.json')['cpd_s']))
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(status='protected_native_control_terminal',passed=True,evaluated_state=None if evaluated is None else str(evaluated),reused_FULL_STA=reused,
 native_transaction_succeeded=bool(candidate),accepted={name:q['accepted'] for name,q in decisions.items()},
 complete_orchestrator_seconds=time.monotonic()-start,complete_child_process_seconds=sum(r['complete_process_seconds'] for r in calls),
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',b/'protected_scope_check.json',work/'candidate_audit/analysis.json',*[b/(name+'_current.json') for name in ['strict','endpoint_vector']],*([b/'decisions.json'] if candidate else [])]},
 qualification='Complete control from scope preparation onward. Earlier protected-prefix queries and CBS measured separately; no summed claim of a whole adaptive-study runtime. No historical U times.'))
print(dict(candidate=str(evaluated),decisions={name:(q['accepted'],q['comparison']['cpd_after_s'],q['comparison']['setup_regressed']) for name,q in decisions.items()}),flush=True)
