#!/usr/bin/env python3
"""Autonomous strict/fixed-resource continuations after the preserved native pilot."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'strong_A0_timing_trajectories_01';b.mkdir(exist_ok=False);q=b/'queue';q.mkdir();lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);pilot=D/'strong_native_A0_timing_pilot_01';owner=read(pilot/'registration.json');assert read(D/'strong_A0_native_reuse_validation_01/completion.json')['passed'];source=D/'native_extra_opportunity_bnn_01/A0_observation';screen=D/'strong_native_A0_timing_screen_01';files=[Path(__file__).resolve(),D/'run_independent_critical_portfolio.py',D/'run_registered_independent_transactions.py',D/'current_native_reuse_resource.py',D/'current_group_feedback_cached.py',D/'run_current_graph_relaxed_queries_v2.py',D/'run_independent_resource_state_analysis.py',D/'run_independent_timing_cone_analysis.py',D/'strong_A0_native_reuse_validation_01/completion.json',screen/'completion.json',source/'completion.json',pilot/'registration.json'];bound={str(p):sha(p) for p in files};write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],prior_pilot=owner,after=str(pilot),source_state=str(source),source_sha256=bound,policies=dict(strict=dict(budget_mode='legacy'),fixed_vertical=dict(policy='timing_under_resources',budget_mode='vertical_fixed_wire_0p1')),question='Can the automatically selected critical repair continue from the strongest low-resource native A0 point, retaining its wire/SB/CB advantage; how do strict CPD and fixed vertical plus0.1% wire policies diverge?',qualification='Independent concurrent single-VPR chain starts only after its original two-role pilot is terminal. Other quality/backend/bundle jobs are preserved. This chain owns at most one native VPR, with the serial main chain at most two, preserving the default at-most-three native concurrency condition. Development process costs under concurrent load, not formal timing. Both policies begin at the same sealed strong A0 source and independently recompute current STA/targets. Exact same-source/query/binary native results can be reused; acceptance always fresh. Local operator exhaustion never ends continuous research.'))
def live():
 try:s=Path('/proc',str(owner['pid']),'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==owner['start_ticks']
 except FileNotFoundError:return False
write(q/'status.json',dict(status='waiting_for_original_timing_pilot',prior_pid=owner['pid'],observed_at=time.time()))
while live():time.sleep(15)
assert (pilot/'completion.json').exists(),'Pilot owner terminal without receipt; inspect, no duplicate';results={};finished=[]
for name,policy,budget in [('strict','strict','legacy'),('fixed_vertical','timing_under_resources','vertical_fixed_wire_0p1')]:
 assert all(sha(p)==h for p,h in bound.items());command=[sys.executable,str(D/'run_independent_critical_portfolio.py'),'--initial-state',str(source),'--batch',str(b/name),'--query-graph',str(D/'bnn_physical_query_graph_01'),'--audit-cache',str(D/'rr_audit_cache_bnn_01'),'--policy',policy,'--budget-mode',budget,'--reuse-plan',str(screen/'feedback/proposal/plan.json'),'--reuse-native-batch',str(pilot),'--reuse-query-batch',str(screen/'feedback/capacity')]
 for prior in finished:
  for plan in prior.glob('round_*/feedback/proposal/plan.json'):command+=['--reuse-plan',str(plan)]
  for menu in prior.glob('round_*/portfolio/portfolio.json'):command+=['--reuse-portfolio',str(menu)]
  for tx in prior.glob('round_*/proposal_*/transaction'):command+=['--reuse-native-batch',str(tx)]
  for query in prior.glob('round_*/feedback/capacity'):command+=['--reuse-query-batch',str(query)]
  for exchange in prior.glob('round_*/exchange_expansion/completion.json'):command+=['--reuse-exchange',str(exchange)]
 with (b/(name+'.log')).open('w') as out:
  proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_own_current_timing_policy',actor=name,pid=proc.pid,start_ticks=Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],observed_at=time.time()));code=proc.wait()
 results[name]=dict(passed=code==0,returncode=code,completion=str(b/name/'completion.json'));write(b/'progress.json',results)
 if code==0:finished.append(b/name)
write(q/'completion.json',dict(passed=all(r['passed'] for r in results.values()),roles=results,qualification='Independent own-current trajectory outcomes; no research stop. All failed/rejected legal candidates and concurrent-load process times preserved; no borrowed U or cold whole-algorithm time.'))
