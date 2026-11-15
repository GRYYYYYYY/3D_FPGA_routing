"""Check recorded old/current routes against the actual changed fixed owners."""
import collections,json
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from resource_opportunity_census import stream_trace
from run_native_scope_policy_v4 import run_dir

out=D/'cold_native_extra_retry_diagnostic_01';out.mkdir(exist_ok=False)
actors=[D/'completed_resource_timing_dev_01/native',D/'complete_resource_timing_full_flow_01/bnn_native/flow/timing']
protocol=read(D/'native_timing_protocol_identity_analysis_01/completion.json');assert protocol['passed']
round_number=1
transactions=[p/f'round_{round_number:03d}/proposal_01/transaction' for p in actors]
roles=[read(p/'registration.json')['roles']['current_group'] for p in transactions]
assert roles[0]['queries']==roles[1]['queries'] and roles[0]['removed_pins']==roles[1]['removed_pins']
# Select the observed divergent query without benchmark IDs in the algorithm.
divergence=protocol['rounds'][round_number]['query_differences'];assert len(divergence)==1
net,pin=divergence[0]['old']['net'],divergence[0]['old']['pin']
fixed_differences=set(protocol['rounds'][round_number]['source_actual_physical_different_nets'])-set(map(int,roles[0]['removed_pins']))
node_table=np.load(D/'rr_audit_cache_bnn_01/nodes.npy',mmap_mode='r')
logs=[run_dir(tx/'current_group')/'joint_native.log' for tx in transactions]
def unpack(path):
 nodes={};pins={};attempts=[]
 for line in path.read_text().splitlines():
  v=line.split()
  if v[0]=='NODE' and int(v[1])==net:
   nodes[int(v[2])]=(int(v[3]),int(v[4]));
   if int(v[5])>0:pins[int(v[5])]=int(v[2])
  elif v[0]=='ATTEMPT' and int(v[1])==net and int(v[2])==pin:attempts.append(dict(pressure=float(v[3]),found=bool(int(v[4])),feasible=bool(int(v[5]))))
 def route(p):
  path=[pins[p]];edges=[]
  while nodes[path[-1]][0]>=0:
   up,switch=nodes[path[-1]];edges.append((up,path[-1],switch));path.append(up)
  return dict(nodes=path[::-1],edges=edges[::-1])
 return pins,route,attempts
parsed=[unpack(path) for path in logs];paths=[entry[1](pin) for entry in parsed]
wanted=set(paths[0]['nodes'])|set(paths[1]['nodes']);owners=[collections.defaultdict(list),collections.defaultdict(list)]
files=[Path(__file__).resolve(),D/'native_timing_protocol_identity_analysis_01/completion.json',D/'rr_audit_cache_bnn_01/completion.json',D/'rr_audit_cache_bnn_01/nodes.npy',*logs]
for i,role in enumerate(roles):
 source=Path(role['source']);seen=set()
 for row in stream_trace(source/'routed.route'):
  if row['net'] not in fixed_differences:continue
  for u in wanted&{x.inode for x in row['trace']}:owners[i][u].append(row['net'])
  seen.add(row['net'])
  if seen==fixed_differences:break
 assert seen==fixed_differences
 files += [transactions[i]/'registration.json',source/'routed.route',source/'manifest.json']
conflicts=[dict(node=u,capacity=int(node_table[u,0]),cold_fixed_owners=owners[1][u],old_fixed_owners=owners[0][u])
 for u in paths[0]['nodes'] if len(owners[1][u])>=int(node_table[u,0]) and int(node_table[u,0])==1]
common_pins=sorted(set(parsed[0][0])&set(parsed[1][0]));other_path_differences=[p for p in common_pins if p!=pin and parsed[0][1](p)!=parsed[1][1](p)]
write(out/'paths.json',dict(target_net=net,target_pin=pin,old=paths[0],cold=paths[1]))
write(out/'completion.json',dict(passed=True,native_calls_new=0,target_net=net,target_pin=pin,
 fixed_owner_differences_outside_scope=sorted(fixed_differences),old_path_unit_capacity_conflicts_in_cold_source=conflicts,
 old_path_excluded_by_actual_cold_fixed_owners=bool(conflicts),other_target_sink_paths_different=other_path_differences,
 old_target_attempts=parsed[0][2],cold_target_attempts=parsed[1][2],
 source_sha256={str(p):sha(p) for p in files},artifact_sha256={'paths.json':sha(out/'paths.json')},
 qualification='Observed divergent query selected from actual recorded native protocols, not a new route or causal injection. Only changed fixed-owner nets outside the registered scope are checked here; unit-capacity conflict with such a fixed owner is sufficient to exclude the old path in the cold source. A missing conflict would not establish feasibility because all other occupancy/retained branches remain. Capacity>1 classes are never inferred full from one owner. This can disprove a serialization-only explanation, not prove minimum wire, that an extra retry is uniquely necessary, or that any joint owner repair improves the final result. Existing source/native/full-STA records remain immutable.'))
print(dict(passed=True,net=net,pin=pin,conflicts=conflicts,other_pin_path_differences=other_path_differences,
 old_attempts=parsed[0][2],cold_attempts=parsed[1][2]),flush=True)
