"""Independent v5 full-vector trajectory; reuse known transactions, then reselect."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

q=D/'rejection_feedback_controller_dev_01/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
proof=D/'current_rejection_feedback_validation_01/completion.json'
assert read(proof)['passed'] and all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
old=D/'low_resource_dual_timing_02/endpoint';reg=read(old/'registration.json')
assert read(old/'completion.json')['passed'] and read(old/'completion.json')['accepted_steps']==0
caps=D/'low_resource_dual_timing_02/absolute_limits.json'
assert read(caps)==reg['fixed_absolute_limits']
output=q.parent/'endpoint'
command=[sys.executable,str(D/'run_independent_critical_portfolio_v5.py'),
    '--initial-state',reg['initial_state'],'--batch',str(output),
    '--query-graph',str(D/'bnn_physical_query_graph_01'),'--audit-cache',str(D/'rr_audit_cache_bnn_01'),
    '--policy','endpoint_under_resources','--budget-mode','explicit_absolute','--fixed-limits',str(caps),
    '--fraction',str(reg['fraction']),'--reuse-plan',str(old/'round_000/feedback/proposal/plan.json'),
    '--reuse-portfolio',str(old/'round_000/portfolio_with_exchange.json')]
native=list(old.glob('round_*/proposal_*/transaction'))+[D/'vector_feedback_subset_native_recovery_01/transaction']
for path in native:command+=['--reuse-native-batch',str(path)]
for actor in [old,D/'low_resource_dual_timing_02/strict',D/'completed_resource_timing_dev_01/native',D/'completed_resource_timing_dev_01/paired']:
    for path in actor.glob('round_*/feedback/capacity'):command+=['--reuse-query-batch',str(path)]
for path in old.glob('round_*/exchange_expansion/completion.json'):command+=['--reuse-exchange',str(path)]
files=[Path(__file__).resolve(),D/'run_independent_critical_portfolio_v5.py',D/'current_rejection_feedback_v1.py',
       proof,old/'completion.json',old/'registration.json',caps]
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    command=command,source_sha256={str(p):sha(p) for p in files},source_state=reg['initial_state'],
    fixed_resource_limits=read(caps),fixed_order='Original action portfolio, current-owner exchange, then same-state rejected-aggregate donor filtering with tied-path coverage; fresh selection after each accept.',
    controls='Same original independent45SB input, native weighted objective, exact full-vector rule and immutable budgets. Reuse six old proposals and known feedback transaction only on exact state/request/objective/binary identity.',
    limits=dict(this_serial_VPR=1,other_registered_pool_parent_plus_child=2,combined_VPR_maximum=3),
    qualification='New development controller, not a changed old batch. Known-result reuse verifies integration but is not an independent sample or timing speedup. Further accepted states require actual FULL/STA and physical checks.'))
started=time.monotonic()
with (q/'endpoint.log').open('w') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    write(q/'status.json',dict(status='running',pid=process.pid,start_ticks=process_identity(process.pid)['start_ticks'],case='endpoint',command=command))
    code=process.wait()
receipt=output/'completion.json'
passed=code==0 and receipt.exists() and read(receipt)['passed']
write(q/'completion.json',dict(passed=passed,returncode=code,completion=str(receipt),
    complete_controller_process_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None))
write(q/'status.json',dict(status='terminal',passed=passed))
