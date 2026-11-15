"""Read-only cost/archive owner for the actual terminal cold domain case."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'complete_resource_timing_full_flow_01';out=root/'domain_archive_analysis';out.mkdir(exist_ok=False)
lock=(out/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
preflight=D/'BNN_domain_archive_postprocessing_preflight_01.json';assert read(preflight)['passed']
files=[Path(__file__).resolve(),preflight,*map(Path,read(preflight)['prepared_files'])]
hashes={str(f):sha(f) for f in files}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=hashes,native_calls=0,
    scope='Read-only actual completed domain cost, full legal-state archive and independent archive verification. Existing original pair reporter retains ownership of comparison.json. No native worker, slot acquisition, source mutation, input restoration or original experiment ownership transfer.'))
original=root/'queue';registered=read(original/'registration.json')
while not (original/'completion.json').exists():
    p=process_identity(registered['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==registered['start_ticks'])
    write(out/'status.json',dict(status='waiting_for_original_cold_pair_terminal',verified_predecessor_live=live))
    if not live:
        write(out/'completion.json',dict(passed=False,status='original_owner_ended_without_receipt',native_calls=0,
            qualification='Missing authoritative terminal receipt; do not infer native failure or restart any experiment.'))
        sys.exit(1)
    time.sleep(15)
assert all(sha(f)==h for f,h in hashes.items())
case=root/'bnn_domain';receipt=case/'completion.json'
if not receipt.exists() or not read(receipt)['passed']:
    measured=case/'measurement/completion.json'
    write(out/'completion.json',dict(passed=True,status='actual_domain_role_not_independently_closed_legal',
        native_calls=0,actual_domain_legal=False,archive=None,
        actual_failed_seconds=read(measured)['complete_command_wall_seconds'] if measured.exists() else None,
        original_case_results=read(original/'results.json') if (original/'results.json').exists() else None,
        source_sha256=hashes,
        qualification='Failure or missing legal case proof retained. No domain quality, new complete configuration or zero runtime invented. Native execution is never repeated for postprocessing.'))
    write(out/'status.json',dict(status='terminal',actual_domain_legal=False));sys.exit(0)
cost=D/'complete_BNN_domain_cost_analysis_01';archive=D/'multiobjective_complete_BNN_cold_pair_01'
commands=[('actual_disjoint_costs',[sys.executable,str(D/'analyze_complete_BNN_case_cost_v2.py'),
             '--case',str(case),'--output',str(cost)]),
          ('actual_domain_archive',[sys.executable,str(D/'archive_complete_BNN_domain_cold_v1.py'),
             '--case',str(case),'--parent',str(D/'multiobjective_complete_BNN_native_cold_01'),
             '--cost',str(cost),'--output',str(archive)]),
          ('independent_archive_verification',[sys.executable,str(D/'verify_complete_BNN_domain_archive_v1.py'),
             '--case',str(case),'--cost',str(cost),'--archive',str(archive),'--output',str(archive/'verification.json')])]
results=[]
for phase,command in commands:
    start=time.monotonic()
    with (out/(phase+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);p=process_identity(child.pid)
        write(out/'status.json',dict(status='running_readonly',phase=phase,pid=child.pid,start_ticks=p['start_ticks']))
        code=child.wait()
    results.append(dict(phase=phase,returncode=code,readonly_process_seconds=time.monotonic()-start))
    write(out/'results.json',results)
    if code:
        write(out/'completion.json',dict(passed=False,status='readonly_postprocessing_failed',phase=phase,
            native_calls=0,results=results,source_sha256=hashes,
            qualification='Actual native case remains immutable. Preserve partial analysis and logs, fork a corrected read-only parser if required, never rerun native merely to fix evidence.'))
        write(out/'status.json',dict(status='terminal',passed=False,failed_phase=phase));sys.exit(1)
assert read(archive/'verification.json')['passed'] and all(sha(f)==h for f,h in hashes.items())
write(out/'completion.json',dict(passed=True,status='actual_domain_cost_and_archive_verified',native_calls=0,
    actual_domain_legal=True,cost=str(cost),archive=str(archive),results=results,source_sha256=hashes,
    original_pair_comparison=str(root/'comparison.json') if (root/'comparison.json').exists() else None,
    qualification='All new quality/time/memory is from this actual closed case; only final carries whole cost. Original pair reporter/experiment ownership and all native queues unchanged. Read-only processing time is separate from measured algorithm wall. Paper/current-entry integration still requires review of actual comparison, archive and layout; this owner does not edit the manuscript or nominate a result from pending work.'))
write(out/'status.json',dict(status='terminal',passed=True))
