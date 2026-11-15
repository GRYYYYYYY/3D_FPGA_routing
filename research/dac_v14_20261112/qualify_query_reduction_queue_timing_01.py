"""Keep paused-parent waiting time distinct from the child algorithm stopwatch."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'query_reduction_timing_qualification_01';root.mkdir(exist_ok=False)
queue=D/'query_reduction_resource_dev_01/queue/results.json';snapshot=root/'observed_queue_results.json'
snapshot.write_bytes(queue.read_bytes());observed=read(snapshot);rows=[]
files=[Path(__file__).resolve(),snapshot,D/'supervision_recovery_20261115_01/intervention.json',D/'supervision_recovery_20261115_01/completion.json']
for label in ['eltwise_A0_native','eltwise_A0_paired']:
    p=D/'query_reduction_resource_dev_01'/label/'completion.json';child=read(p);assert child['passed'] and observed[label]['passed']
    rows.append(dict(role=label,queue_parent_wait_seconds=observed[label]['actor_process_seconds'],
        child_reported_imported_workflow_seconds=child['complete_imported_algorithm_workflow_seconds'],
        final_CPD_s=child['final_CPD_s'],final_resources=child['final_resources'],
        complete_fresh_route_flow=False,parent_wait_contaminated_by_scheduler_pause=label=='eltwise_A0_native'))
    files.append(p)
assert rows[0]['queue_parent_wait_seconds']-rows[0]['child_reported_imported_workflow_seconds']>1000
write(root/'completion.json',dict(passed=True,rows=rows,queue_results_capture=str(queue),VPR_calls_new=0,
    source_sha256={str(f):sha(f) for f in files},qualification='Original queue field actor_process_seconds includes deferred parent wait return across its SIGSTOP, not just child execution. Retain original value; use explicitly labeled child internal imported-workflow stopwatch for that scope. Neither is fresh-route complete time or evidence of isolated statistical speedup; original BNN overlap and shared host remain. The live queue may append later roles; this snapshot captures only currently completed roles.'))
print(rows)
