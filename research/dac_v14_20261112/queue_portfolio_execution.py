#!/usr/bin/env python3
"""Single-owner execution of registered portfolio actors after prior native work."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'portfolio_execution_dev_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'reservation_prune_recovery_dev_01';owner=read(prior/'queue/registration.json');reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
def live():
 p=Path('/proc')/str(owner['pid'])/'stat'
 try:s=p.read_text().split(') ',1)[1].split();return s[19]==owner['start_ticks'] and s[0]!='Z'
 except FileNotFoundError:return False
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),prior_owner=owner,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_automatic_portfolio_repair_v3.py']}))
write(q/'status.json',dict(status='waiting_for_previous_native_owner',prior_pid=owner['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not (prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior native owner terminal without completion; no launch'));raise SystemExit(2)
assert all(sha(p)==h for p,h in read(prior/'completion.json')['source_sha256'].items())
assert all(sha(p)==h for p,h in reg['source_sha256'].items());results={};extra_native=[];extra_plans=[];extra_portfolios=[];extra_queries=[];started=time.monotonic()
for name,role in reg['roles'].items():
 actor=b/name;command=[sys.executable,str(D/'run_automatic_portfolio_repair_v3.py'),'--initial-state',role['initial_state'],'--batch',str(actor),'--query-graph',str(D/'bnn_physical_query_graph_01'),'--audit-cache',str(D/'rr_audit_cache_bnn_01'),'--policy',role['policy'],'--budget-mode',role['budget_mode'],'--native-mode','execute','--fraction','.9']
 if role['resume_from']:command+=['--resume-from',role['resume_from']]
 for arg,paths in [('reuse-plan',role['plans']+list(map(str,extra_plans))),('reuse-portfolio',role['portfolios']+list(map(str,extra_portfolios))),('reuse-native-batch',role['native_history']+list(map(str,extra_native))),('reuse-query-batch',role['query_history']+list(map(str,extra_queries)))]:
  for path in paths:command+=['--'+arg,path]
 command+=['--reuse-exchange',str(D/'critical_owner_exchange_expansion_01/completion.json')];t=time.monotonic()
 with (b/(name+'.log')).open('w') as out:
  proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_portfolio_actor',actor=name,pid=proc.pid,command=command,observed_at=time.time()));code=proc.wait()
 results[name]=read(actor/'completion.json') if (actor/'completion.json').exists() else dict(passed=False,status='workflow_failed_preserved')
 results[name].update(returncode=code,complete_driver_process_seconds=time.monotonic()-t);write(b/'progress.json',results)
 extra_native+=list(actor.glob('round_*/proposal_*/transaction'));extra_plans+=list(actor.glob('round_*/feedback/proposal/plan.json'));extra_portfolios+=list(actor.glob('round_*/portfolio/portfolio.json'))+list(actor.glob('round_*/portfolio_with_exchange.json'));extra_queries+=list(actor.glob('round_*/feedback/capacity'))
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
write(b/'completion.json',dict(passed=all(x['passed'] for x in results.values()),roles=results,complete_shared_execution_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'progress.json',Path(__file__).resolve()]},qualification='Independent own-current-state native portfolio trajectories. Reused evidence creation/original routing/static cache preparation excluded from observed actor times; no cold algorithm speedup. Operator stops/failures do not complete the continuing research goal.'))
write(q/'completion.json',dict(returncode=0 if all(x['passed'] for x in results.values()) else 1))
