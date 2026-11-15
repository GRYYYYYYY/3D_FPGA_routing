"""Read-only native receipt consumption with exact established route serialization."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from materialize_serial_fused_candidate_v3 import materialize
parent=D/'serial_fused_candidate_validation_02';closed=read(parent/'completion.json');assert closed['passed']
assert all(sha(f)==h for f,h in closed['source_sha256'].items())
root=D/'serial_fused_serialization_validation_01';root.mkdir(exist_ok=False);rows=[];files=[Path(__file__).resolve(),D/'materialize_serial_fused_candidate_v3.py',parent/'completion.json']
for row in closed['results']:
    tx=parent/f"transaction_{row['transaction']:02d}";name=row['role'];audit=Path(read(tx/(name+'_audit/analysis.json'))['candidate_route'])
    reference=Path(row['reference']);output=root/f"transaction_{row['transaction']:02d}_{name}"
    graph_cache=D/'complete_serial_seed_policy_dev_01/delay_seed_paired/flow/full_graph_cache'
    materialize(tx/name,output,graph_cache,audit)
    a,b=read(output/'endpoint_vector.json'),read(reference/'endpoint_vector.json')
    assert all(a[k]==b[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(output)/'routed.route')==route_body(run_dir(reference)/'routed.route')
    assert read(run_dir(output)/'independent_audit.json')['physical_metrics']==read(run_dir(reference)/'independent_audit.json')['physical_metrics']
    rows.append(dict(role=name,transaction=row['transaction'],reference=str(reference),actual=str(output),complete_vector_and_ordered_route_exact=True))
    files += [tx/name/'completion.json',tx/(name+'_audit/analysis.json'),output/'completion.json',reference/'completion.json']
write(root/'completion.json',dict(passed=True,native_calls_new=0,roles=rows,source_sha256={str(f):sha(f) for f in files},
    qualification='Same four actual callback observations: full physical tree equality includes edges/switches/terminal pins; output retains independently reconstructed transaction traversal order. Callback native DFS serialization remains separately bound. Complete vectors, physical metrics and persisted ordered route bodies match separate-LOAD references. No source identity/order is silently changed and no new native or full-flow timing is claimed.'))
print(dict(passed=True,roles=len(rows),native_calls_new=0),flush=True)
