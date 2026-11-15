"""Replay sealed current selectors and reconcile actual native query workload."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_resource_bundle_v2 import select_cuts as original,serialize_request
from current_resource_connection_budget_v1 import select_cuts

out=D/'connection_budget_grouping_validation_01';out.mkdir(exist_ok=False)
files=[Path(__file__).resolve(),D/'current_resource_bundle_v2.py',D/'current_resource_connection_budget_v1.py',D/'run_connection_budget_resource_repair_v1.py']
rows=[];costs=[]
for name in ['stable_seed_transfer_dev_01/bnn_A0_paired','stable_seed_transfer_recovery_01/bnn_R1_paired',
             'stable_seed_transfer_dev_01/eltwise_A0_paired']:
    actor=D/name;terminal=read(actor/'completion.json');assert terminal['passed'];files.append(actor/'completion.json')
    for f in sorted(actor.glob('round_*/selection/candidates.json')):
        candidates=read(f);seal=read(f.parent/'completion.json');assert seal['passed']
        assert seal['source_sha256'][str(f.resolve())]==sha(f)
        for rank in range(3):
            old=original(candidates,8,rank);new=select_cuts(candidates,8,rank,connection_budget=64)
            assert select_cuts(candidates,8,rank,connection_budget=10**9)==old
            if new:
                request,domain,queries=serialize_request(new)
                assert len(queries)<=64 or (len(new)==1 and len(new[0]['ordered_queries'])>64)
                assert all(c in candidates[rank:] for c in new)
                assert all(set(c['pins'])=={q['pin'] for q in c['ordered_queries']} for c in new)
            rows.append(dict(actor=name,round=f.parents[1].name,rank=rank,
                old_nets=len(old),old_connections=sum(len(c['ordered_queries']) for c in old),
                new_nets=len(new),new_connections=sum(len(c['ordered_queries']) for c in new),
                selected_complete_cuts=[dict(net=c['net'],pins=c['pins']) for c in new],changed=old!=new))
        files += [f,f.parent/'completion.json']
    for receipt in sorted(actor.glob('round_*/candidate_*/*worker_receipt.json')):
        r=read(receipt);assert r['passed'];log=Path(r['native_directory'])/'joint_native.log'
        assert r['artifact_sha256'][str(log)]==sha(log)
        lines=[l.split() for l in log.read_text().splitlines()];queries=[l for l in lines if l[0]=='QUERY'];complete=lines[-1]
        assert complete[0]=='COMPLETE' and complete[1]=='1' and int(complete[2])==int(complete[3])==len(queries)
        costs.append(dict(actor=name,receipt=str(receipt),queries=len(queries),
            query_seconds=sum(float(q[-1]) for q in queries),native_transaction_seconds=float(complete[-2]),
            native_child_seconds=r['native_child_seconds']))
        files += [receipt,log]
# Budget arithmetic must preserve indivisible cuts, rank windows and later
# smaller cuts of an oversized network; malformed query membership fails.
def cut(net,n):
    return dict(net=net,pins=list(range(1,n+1)),ordered_queries=[dict(net=net,pin=p,raw_criticality=.5) for p in range(1,n+1)],retained_crossing_sources=[1],removed_crossing_resources=1)
assert select_cuts([cut(1,80),cut(1,3),cut(2,4)],8,connection_budget=8)==[cut(1,3),cut(2,4)]
assert select_cuts([cut(1,80),cut(2,90)],8,connection_budget=8)==[cut(1,80)]
assert select_cuts([],8,connection_budget=8)==[]
assert select_cuts([cut(1,2),cut(2,2)],8,1,connection_budget=8)==[cut(2,2)]
bad=cut(1,3);bad['ordered_queries'].pop()
try:select_cuts([bad],8,connection_budget=8)
except AssertionError:pass
else:raise AssertionError('Partial cut accepted')
write(out/'selection_replay.json',rows);write(out/'native_workload.json',costs)
write(out/'completion.json',dict(passed=True,selection_windows=len(rows),changed_windows=sum(r['changed'] for r in rows),
    connection_budget=64,native_calls=0,actual_native_receipts=len(costs),
    checks=['unbounded_equals_original','whole_cuts_only','exact_query_membership','fixed_budget_or_single_atomic_fallback','distinct_selected_nets','rank_window_preserved','smaller_later_cut_of_skipped_net_allowed','malformed_partial_query_rejected'],
    source_sha256={str(f):sha(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['selection_replay.json','native_workload.json']},
    qualification='Replay on sealed old current states and actual historical native log costs. New grouping changes later states; query counts are not runtime predictions or final resource/CPD results. No old/native workflow source modified. New whole native/FULLSTA trajectories required.'))
print(dict(passed=True,windows=len(rows),changed=sum(r['changed'] for r in rows),native_calls=0),flush=True)
