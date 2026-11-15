"""Locate divergence using actual native KEEP/NODE/QUERY/ATTEMPT records."""
import collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from complete_flow_equivalence_v1 import equal_state
from actual_route_tree_identity import tree_identity
from run_native_scope_policy_v4 import run_dir,native_config

out=D/'native_timing_protocol_identity_analysis_01';out.mkdir(exist_ok=False)
actors=[D/'completed_resource_timing_dev_01/native',D/'complete_resource_timing_full_flow_01/bnn_native/flow/timing']
registrations=[read(p/'registration.json') for p in actors]
initial=[Path(r['initial_state']) for r in registrations]
source_identity=equal_state(*initial)
trees=[tree_identity(run_dir(s)/'routed.route') for s in initial]
assert trees[0].keys()==trees[1].keys()
different={net for net in trees[0] if trees[0][net]!=trees[1][net]}
initial_different=sorted(different)
files=[Path(__file__).resolve(),D/'actual_route_tree_identity.py',D/'complete_flow_equivalence_v1.py',D/'run_native_scope_policy_v4.py']
for actor,state in zip(actors,initial):files += [actor/'registration.json',actor/'completion.json',state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'routed.route']

def parse(path):
 keep=collections.defaultdict(list);nodes=collections.defaultdict(list);queries=[];attempts=[]
 for line in path.read_text().splitlines():
  v=line.split()
  if v[0]=='KEEP':keep[int(v[1])].append((int(v[2]),float(v[3]),int(v[4])))
  elif v[0]=='NODE':nodes[int(v[1])].append((int(v[2]),int(v[3]),int(v[4]),int(v[5]),float(v[6])))
  elif v[0]=='QUERY':queries.append(dict(net=int(v[1]),pin=int(v[2]),feasible=bool(int(v[3])),criticality=float(v[4]),pushes=int(v[5]),pops=int(v[6])))
  elif v[0]=='ATTEMPT':attempts.append((int(v[1]),int(v[2]),float(v[3]),int(v[4]),int(v[5])))
 return dict(keep=keep,nodes=nodes,queries=queries,attempts=attempts)

rounds=[]
for i in range(3):
 txs=[p/f'round_{i:03d}/proposal_01/transaction' for p in actors]
 roles=[read(tx/'registration.json')['roles']['current_group'] for tx in txs]
 workers=[tx/'current_group' for tx in txs]
 manifests=[read(run_dir(w)/'manifest.json') for w in workers]
 logs=[run_dir(w)/'joint_native.log' for w in workers];data=list(map(parse,logs))
 audits=[read(tx/'current_group_audit/analysis.json') for tx in txs]
 assert all(x['passed'] and x['candidate_route'] for x in audits)
 assert all(read(w/'completion.json')['passed'] for w in workers)
 common_keys=['objective','queries','removed_pins','fixed_target_paths']
 config_checks={key:roles[0].get(key)==roles[1].get(key) for key in common_keys}
 config_checks.update(request_bytes_exact=sha(roles[0]['request'])==sha(roles[1]['request']),
  native_binary_exact=sha(manifests[0]['command'][0])==sha(manifests[1]['command'][0]),
  native_options_exact=native_config(run_dir(workers[0]))==native_config(run_dir(workers[1])))
 stable_keys=['VPR_JOINT_NATIVE_OBJECTIVE','VPR_CURRENT_STA_NATIVE_PRESSURE_START','VPR_JOINT_NATIVE_REUSE_CROSSINGS','VPR_H3D_MODE','VPR_JOINT_NATIVE_SEED_ORDER','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']
 config_checks['semantic_environment_exact']=all(manifests[0]['environment'].get(k)==manifests[1]['environment'].get(k) for k in stable_keys)
 keep_sets=[{net:sorted(rows) for net,rows in d['keep'].items()} for d in data]
 keep_order_diff=[net for net in data[0]['keep'] if data[0]['keep'][net]!=data[1]['keep'].get(net)]
 seed_order_diff=[net for net in data[0]['keep'] if [r for r in data[0]['keep'][net] if r[2]]!=[r for r in data[1]['keep'].get(net,[]) if r[2]]]
 source_diff=sorted(different);node_differences=[]
 assert data[0]['nodes'].keys()==data[1]['nodes'].keys()
 for net in data[0]['nodes']:
  # Node delay metadata is separately observable; physical identity compares
  # inode/parent/switch/pin, independent of output traversal order.
  a,b=[sorted(row[:4] for row in d['nodes'][net]) for d in data]
  if a!=b:different.add(net);node_differences.append(net)
  else:different.discard(net)
 qdiff=[dict(index=j,old=a,cold=b) for j,(a,b) in enumerate(zip(data[0]['queries'],data[1]['queries'])) if a!=b]
 rounds.append(dict(round=i,input_configuration_checks=config_checks,source_actual_physical_different_nets=source_diff,
  retained_node_delay_expandability_sets_exact=keep_sets[0]==keep_sets[1],retained_iteration_order_different_nets=keep_order_diff,
  initial_reexpandable_iteration_order_different_nets=seed_order_diff,
  native_query_rows_without_runtime_exact=data[0]['queries']==data[1]['queries'],query_differences=qdiff,
  old_attempts=len(data[0]['attempts']),cold_attempts=len(data[1]['attempts']),attempts_exact=data[0]['attempts']==data[1]['attempts'],
  different_replacement_physical_nets=sorted(node_differences),after_actual_physical_different_nets=sorted(different)))
 for tx,w,log,role in zip(txs,workers,logs,roles):files += [tx/'registration.json',tx/'current_group_audit/analysis.json',w/'completion.json',run_dir(w)/'manifest.json',log,Path(role['request'])]
write(out/'rounds.json',rounds)
write(out/'completion.json',dict(passed=True,native_calls_new=0,initial_source_state_comparison=source_identity,
 initial_source_physical_different_nets=initial_different,final_source_physical_different_nets=sorted(different),rounds=rounds,
 source_sha256={str(p):sha(p) for p in files},artifact_sha256={'rounds.json':sha(out/'rounds.json')},
 qualification='Actual native protocols, not a new search or injected cause test. KEEP records pruned node/prefix-delay/re_expand values and their iteration order; it is not a direct heap-seed insertion trace. NODE records reconstruct actual private replacement edges/switches/terminals; unchanged other nets follow the already passed independent scope gates. QUERY elapsed seconds excluded, actual pushes/pops/retries retained. Matching observable options and source physical trees narrows hypotheses but does not establish serialization-only causality, hidden native-state equivalence or an improvement from a new seed policy. Existing cold/imported results and all costs remain distinct; no native rerun.'))
print(dict(passed=True,initial=source_identity,initial_physical_diff=initial_different,rounds=rounds),flush=True)
