"""Replay real current-state candidate menus, preserving complete cuts and serialization."""
from retained_prefix_workflow import D,read,write,sha
from current_resource_query_reduction_v1 import select_cuts
from current_resource_bundle_v2 import select_cuts as net_group,serialize_request
from current_resource_connection_budget_v1 import select_cuts as budget_group

out=D/'query_reduction_grouping_validation_01';assert not out.exists()
files=[D/n for n in ['current_resource_query_reduction_v1.py','current_resource_bundle_v2.py','current_resource_connection_budget_v1.py','validate_query_reduction_grouping_v1.py']]
rows=[]
for batch in ['stable_seed_transfer_dev_01','connection_budget_resource_dev_02']:
    for role in ['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native','bnn_A0_paired']:
        actor=D/batch/role;assert read(actor/'completion.json')['passed']
        for path in sorted(actor.glob('round_*/selection/candidates.json')):
            candidates=read(path);files.append(path)
            for rank in range(min(3,len(candidates))):
                selected=select_cuts(candidates,8,rank,connection_budget=64)
                full=net_group(candidates,8,rank);budget=budget_group(candidates,8,rank,connection_budget=64)
                assert selected in [full,budget] and len({c['net'] for c in selected})==len(selected)
                assert all(c in candidates[rank:] for c in selected)
                request,domain,queries=serialize_request(selected)
                assert len(queries)==sum(len(c['pins']) for c in selected)
                assert all(set(c['pins'])=={q['pin'] for q in queries if q['net']==c['net']} for c in selected)
                rows.append(dict(menu=str(path),rank=rank,full_queries=sum(len(c['ordered_queries']) for c in full),
                    budget_queries=sum(len(c['ordered_queries']) for c in budget),selected_queries=len(queries),
                    retains_full_group=selected==full,changes_hard_budget=selected!=budget))
first=next(r for r in rows if '/stable_seed_transfer_dev_01/bnn_A0_paired/round_004/' in r['menu'] and r['rank']==0)
large=next(r for r in rows if '/stable_seed_transfer_dev_01/bnn_A0_paired/round_006/' in r['menu'] and r['rank']==0)
assert (first['full_queries'],first['budget_queries'],first['selected_queries'])==(77,64,77)
assert (large['full_queries'],large['budget_queries'],large['selected_queries'])==(462,54,54)
assert select_cuts([],8,connection_budget=64)==[]
out.mkdir();write(out/'windows.json',rows)
write(out/'completion.json',dict(passed=True,actual_windows=len(rows),changes_from_hard_budget=sum(r['changes_hard_budget'] for r in rows),
    full_groups_retained=sum(r['retains_full_group'] for r in rows),first_divergence_menu=first,large_scope_menu=large,
    fixed_reduction_factor=2,native_calls=0,full_algorithm_registered=False,
    source_sha256={str(f):sha(f) for f in files},artifact_sha256={'windows.json':sha(out/'windows.json')},
    qualification='Development rule preserves K8 unless budget64 offers at least twofold fewer proposed queries. Replayed whole cuts, distinct networks and native serialization on actual menus; no circuit/net special cases. Threshold chosen after observing fragmentation, not held-out confirmation. It does not predict elapsed time or native quality; changed trajectories require actual matched native/domain experiments.'))
print(dict(passed=True,windows=len(rows),changes_from_hard_budget=sum(r['changes_hard_budget'] for r in rows),native_calls=0),flush=True)
