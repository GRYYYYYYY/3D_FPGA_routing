#!/usr/bin/env python3
"""One owner: preserve original-native cohort, then new paired resource integration."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'pooled_resource_repair_dev_01';b.mkdir(exist_ok=False);q=b/'queue';q.mkdir();lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prior=D/'native_extra_opportunity_bnn_01';owner=read(prior/'queue/registration.json');assert read(D/'current_crossing_share_selector_validation_02/completion.json')['passed'];proof=D/'pool_state_evaluator_bnn_01/completion.json';assert read(proof)['passed'];fast=Path(read(D/'R1_strict_portfolio_summary_01.json')['final_state']);files=[Path(__file__).resolve(),D/'run_pooled_resource_repair.py',D/'native_analysis_pool_v2.py',D/'pool_state_evaluator.py',D/'current_crossing_share_selector_v2.py',D/'current_crossing_share_selector_validation_02/completion.json',proof,prior/'registration.json',prior/'queue/registration.json',D/'R1_strict_portfolio_summary_01.json'];bound={str(p):sha(p) for p in files}
roots=dict(R1_fast=fast,A0_native8=prior/'A0_observation',R1_native8=prior/'R1_observation');write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],prior_owner=owner,after=str(prior),roots={k:str(p) for k,p in roots.items()},source_sha256=bound,question='Current-STA slack-bearing crossing release after timing repair and after stronger native convergence, using paired native equal-opportunity controls and a persistent complete-STA backend.',qualification='Independent integration version; no current source/input/acceptance switch. Failed local actors do not terminate remaining roots or continuous research. Two accepted moves and three examined current scopes are a local integration probe, not the overall research budget.'))
def live():
 try:s=(Path('/proc')/str(owner['pid'])/'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==owner['start_ticks']
 except FileNotFoundError:return False
write(q/'status.json',dict(status='waiting_for_original_native_opportunity_owner',prior_pid=owner['pid'],observed_at=time.time()))
while live():time.sleep(15)
assert (prior/'completion.json').exists(),'Missing prior terminal receipt: diagnose; do not resubmit';results={}
for name,state in roots.items():
 assert all(sha(p)==h for p,h in bound.items())
 if not (state/'completion.json').exists() or not read(state/'completion.json')['passed']:
  results[name]=dict(status='necessary_initial_observation_missing',initial_state=str(state));write(b/'progress.json',results);continue
 command=[sys.executable,str(D/'run_pooled_resource_repair.py'),'--initial-state',str(state),'--batch',str(b/name)]
 with (b/(name+'.log')).open('w') as out:
  proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_pooled_resource_actor',actor=name,pid=proc.pid,start_ticks=(Path('/proc')/str(proc.pid)/'stat').read_text().split(') ',1)[1].split()[19],observed_at=time.time()));code=proc.wait()
 results[name]=dict(status='terminal',returncode=code,passed=code==0,completion=str(b/name/'completion.json'));write(b/'progress.json',results)
write(q/'completion.json',dict(passed=all(r.get('passed',False) for r in results.values()),actors=results,qualification='Independent local resource integration terminal, not overall research completion. Failure evidence preserved and remaining registered actors were not cancelled.'))
