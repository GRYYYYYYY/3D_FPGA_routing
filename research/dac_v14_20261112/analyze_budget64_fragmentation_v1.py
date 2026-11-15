"""Bind first actual grouping divergence and disjoint whole imported cost components."""
import collections,hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

out=D/'budget64_fragmentation_analysis_01';assert not out.exists()
roots=[D/b/'bnn_A0_paired' for b in ['stable_seed_transfer_dev_01','connection_budget_resource_dev_02']]
files=[Path(__file__).resolve()];memo={}
def state(s):
    s=Path(s)
    if str(s) not in memo:
        c=read(s/'completion.json');r=run_dir(s);m=read(r/'manifest.json');v=read(s/'endpoint_vector.json')
        assert c['passed'] and m['metrics']['native_full_check_passed']
        assert sha(r/'routed.route')==m['outputs']['routed.route']['sha256']
        memo[str(s)]=dict(route=route_body(r/'routed.route'),vector=hashlib.sha256(json.dumps({k:v[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']},sort_keys=True).encode()).hexdigest())
        files.extend([s/'completion.json',s/'endpoint_vector.json',r/'manifest.json',r/'routed.route'])
    return memo[str(s)]
attempts=[read(r/'attempts.json') for r in roots];closed=[read(r/'completion.json') for r in roots]
assert all(x['passed'] for x in closed)
prefix=[]
for a,b in zip(*attempts):
    same_source=state(a['current_state'])==state(b['current_state'])
    if a['bundle_removed_pins']!=b['bundle_removed_pins']:
        assert same_source
        divergence=dict(round=a['round'],same_source_full_vector_and_ordered_route=True,
            full_removed_pins=a['bundle_removed_pins'],budget_removed_pins=b['bundle_removed_pins'])
        break
    assert same_source
    for role in a['pair']:
        assert a['pair'][role]['status']==b['pair'][role]['status']=='legal_evaluated'
        assert state(a['pair'][role]['evaluation'])==state(b['pair'][role]['evaluation'])
    prefix.append(a['round'])
assert prefix==[0,1,2,3] and divergence['round']==4
divergence.update(full_connections=sum(map(len,divergence['full_removed_pins'].values())),budget_connections=sum(map(len,divergence['budget_removed_pins'].values())))
assert divergence['full_connections']==77 and divergence['budget_connections']==64
rows=[];query_bags=[]
for root,ats,c in zip(roots,attempts,closed):
    bag=collections.Counter();roles=0;core=0
    for a in ats:
        for role,result in a['pair'].items():
            assert result['status']=='legal_evaluated';roles+=1;core+=result['native_core_seconds']
            for net,pins in a['bundle_removed_pins'].items():
                for pin in pins:bag[(role,net,pin)]+=1
    query_bags.append(bag);groups=collections.defaultdict(float)
    for row in read(root/'process_costs.json'):
        tag=row['tag'];parts=tag.split('_',2)
        cat=parts[2] if len(parts)>2 and parts[0].isdigit() and parts[1].isdigit() else (tag.split('_',1)[1] if tag.split('_',1)[0].isdigit() else tag)
        cat=cat.removeprefix('reuse_off_').removeprefix('reuse_on_');groups[cat]+=row['complete_process_seconds']
    unclassified=c['complete_imported_algorithm_workflow_seconds']-sum(groups.values());assert unclassified>=-1e-6
    rows.append(dict(actor=str(root),actual_transactions=roles,actual_queries=sum(bag.values()),core_query_seconds=core,
        complete_imported_seconds=c['complete_imported_algorithm_workflow_seconds'],disjoint_process_seconds=dict(groups),
        unclassified_driver_seconds=unclassified,quality=c['final_resources']))
    files += [root/'completion.json',root/'registration.json',root/'attempts.json',root/'process_costs.json']
assert [r['actual_queries'] for r in rows]==[2722,2722]
assert [r['actual_transactions'] for r in rows]==[18,32]
out.mkdir()
write(out/'completion.json',dict(passed=True,exact_common_accepted_prefix_rounds=prefix,first_divergence=divergence,
    trajectories=rows,query_role_net_pin_multisets_equal=query_bags[0]==query_bags[1],
    native_calls_new=0,source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},
    qualification='Actual same-source first divergence; exact prior source/candidate full vectors and ordered trees. Total query count equality does not imply identical downstream requests/states or search effort. Costs partition actual recorded process intervals plus driver residual; native QUERY core is nested and not added again. Shared-host observations do not identify causal runtime magnitude. Supports testing a query-reduction gate before splitting groups, not a demonstrated better algorithm.'))
print(dict(passed=True,prefix=prefix,first_divergence_connections=[77,64],actual_transactions=[18,32],actual_queries=[2722,2722],query_multisets_equal=query_bags[0]==query_bags[1]),flush=True)
