"""Disjoint actual wall decomposition and nested diagnostics for sealed BNN native."""
import argparse,collections,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=argparse.ArgumentParser();p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.case.resolve();closed=read(root/'completion.json');assert closed['passed'] and closed['complete_configuration_verified']
out=a.output.resolve();out.mkdir(exist_ok=False)
measure=read(root/'measurement/completion.json');stages=read(root/'flow/stages.json');rs=read(root/'flow/resource_flow/stages.json')
resource=root/'flow/resource_flow/repair';timing=root/'flow/timing'
files=[Path(__file__).resolve(),root/'completion.json',root/'measurement/completion.json',root/'measurement/memory_samples.jsonl',
 root/'flow/stages.json',root/'flow/resource_flow/stages.json',resource/'attempts.json',resource/'process_costs.json',timing/'attempts.json',timing/'process_costs.json']
leaf=collections.defaultdict(float);rows=[];native_process=eval_native=eval_audit=eval_prepare=search_core=0.;worker_count=evaluation_count=0;unknown_search_core=[]

def add(category,seconds,source,tag):
 assert seconds>=0,(source,tag,seconds)
 leaf[category]+=seconds;rows.append(dict(category=category,seconds=seconds,source=str(source),tag=tag))

def transaction(parent_seconds,tx):
 global native_process,eval_native,eval_audit,eval_prepare,search_core,worker_count,evaluation_count
 path=tx/'process_costs.json';costs=read(path);assert all(x['status']=='completed' for x in costs)
 total=sum(x['complete_process_seconds'] for x in costs);assert total<=parent_seconds
 for row in costs:
  tag,seconds=row['tag'],row['complete_process_seconds']
  if tag.endswith('_native'):
   category='native_worker_wrappers';name=tag[:-len('_native')];worker=read(tx/name/'completion.json');assert worker['passed']
   native_process+=worker['timing']['native_process_seconds'];worker_count+=1
   audit=read(tx/(name+'_audit/analysis.json'));assert audit['passed']
   core=audit.get('native_transaction_seconds')
   if core is None:
    from run_native_scope_policy_v4 import run_dir
    protocol=run_dir(tx/name)/'joint_native.log'
    if protocol.exists():
     last=protocol.read_text().splitlines()[-1].split();assert last[0]=='COMPLETE' and last[-1]=='occupancy_restored';core=float(last[4]);files.append(protocol)
   if core is None:unknown_search_core.append(str(tx/name))
   else:assert core>=0;search_core+=core
   files.extend([tx/name/'completion.json',tx/(name+'_audit/analysis.json')])
  elif tag.endswith('_FULL_STA'):
   category='candidate_LOAD_FULL_STA_wrappers';name=tag[:-len('_FULL_STA')];evaluation=read(tx/(name+'_evaluation/completion.json'));assert evaluation['passed']
   t=evaluation['timing'];eval_native+=t['native_process_seconds'];eval_audit+=t['independent_audit_seconds'];eval_prepare+=t['preparation_seconds'];evaluation_count+=1
   files.append(tx/(name+'_evaluation/completion.json'))
  elif tag.endswith('_domain_audit'):category='domain_audits'
  elif tag.endswith('_audit'):category='scope_capacity_audits'
  else:category='selection_queries_plans'
  add(category,seconds,path,tag)
 add('controller_and_startup_overhead',parent_seconds-total,path,'parent_minus_children')
 files.append(path)

for row in read(resource/'process_costs.json'):
 if row['tag'].endswith('_serial_native_transaction'):
  prefix=row['tag'].split('_');tx=resource/f'round_{int(prefix[0]):03d}'/f'candidate_{int(prefix[1]):02d}'
  transaction(row['complete_process_seconds'],tx)
 else:add('selection_queries_plans',row['complete_process_seconds'],resource/'process_costs.json',row['tag'])
resource_children=sum(x['complete_process_seconds'] for x in read(resource/'process_costs.json'))
resource_stage=next(x['complete_process_seconds'] for x in rs if x['phase']=='resource_repair')
add('controller_and_startup_overhead',resource_stage-resource_children,resource/'process_costs.json','resource_actor_minus_children')
for row in rs:
 if row['phase'] in ['build_audit_cache','build_full_cache']:add('graph_index_construction',row['complete_process_seconds'],root/'flow/resource_flow/stages.json',row['phase'])
 elif row['phase']=='fresh_route_and_materialization':add('fresh_route_and_materialization',row['complete_process_seconds'],root/'flow/resource_flow/stages.json',row['phase'])
resource_outer=next(x['complete_process_seconds'] for x in stages if x['phase']=='fresh_route_and_complete_resource')
add('controller_and_startup_overhead',resource_outer-sum(x['complete_process_seconds'] for x in rs),root/'flow/resource_flow/stages.json','resource_flow_minus_stages')
for row in read(timing/'process_costs.json'):
 if row['tag'].endswith('_native'):
  prefix=row['tag'].split('_');tx=timing/f'round_{int(prefix[0]):03d}'/f'proposal_{int(prefix[1]):02d}'/'transaction'
  transaction(row['complete_process_seconds'],tx)
 else:add('selection_queries_plans',row['complete_process_seconds'],timing/'process_costs.json',row['tag'])
timing_stage=next(x['complete_process_seconds'] for x in stages if x['phase']=='complete_current_STA_timing')
add('controller_and_startup_overhead',timing_stage-sum(x['complete_process_seconds'] for x in read(timing/'process_costs.json')),timing/'process_costs.json','timing_actor_minus_children')
for row in stages:
 if row['phase']=='build_physical_query_graph':add('graph_index_construction',row['complete_process_seconds'],root/'flow/stages.json',row['phase'])
 elif row['phase']=='resource_final_handoff_FULL_STA':add('resource_final_handoff_FULL_STA',row['complete_process_seconds'],root/'flow/stages.json',row['phase'])
wall=measure['complete_command_wall_seconds']
add('controller_and_startup_overhead',wall-sum(x['complete_process_seconds'] for x in stages),root/'flow/stages.json','outer_wall_minus_stages')
assert abs(sum(leaf.values())-wall)<1e-8
peak=None
for line in (root/'measurement/memory_samples.jsonl').open():
 sample=__import__('json').loads(line)
 if peak is None or sample['sum_PSS_kib']>peak['sum_PSS_kib']:peak=sample
assert peak['sum_PSS_kib']==measure['sampled_tree_PSS_peak_kib']
phase_total=sum(x['complete_process_seconds'] for x in stages);unassigned=wall-phase_total
prefix=0.;certain=[]
for row in stages:
 if prefix+unassigned<peak['elapsed_seconds']<prefix+row['complete_process_seconds']:certain.append(row['phase'])
 prefix+=row['complete_process_seconds']
with (out/'disjoint_wall.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['category','seconds','source','tag']);w.writeheader();w.writerows(rows)
# Record actual immutable metadata consumers, including legacy external aliases.
metadata=[]
for path in timing.rglob('analysis.json'):
 data=read(path)
 if 'graph_cache' in data:
  directory=Path(data['graph_cache']['cache_completion']).parent
  metadata.append(dict(kind='scope_audit',receipt=str(path),directory=str(directory),within_case=directory.resolve().is_relative_to(root/'flow')));files.append(path)
for path in timing.rglob('full_graph_cache_receipt.json'):
 data=read(path)
 for kind,entry in [('full',data),('audit_parent',data['parent'])]:
  directory=Path(entry['cache_completion']).parent
  metadata.append(dict(kind=kind,receipt=str(path),directory=str(directory),within_case=directory.resolve().is_relative_to(root/'flow')))
 files.append(path)
verified={}
for row in metadata:
 kind='full' if row['kind']=='full' else 'audit'
 directory=Path(row['directory']);key=str(directory),kind
 if key not in verified:
  own=root/'flow/resource_flow'/('full_graph_cache' if kind=='full' else 'graph_audit_cache')
  source,target=read(directory/'completion.json'),read(own/'completion.json')
  assert source['graph_sha256']==target['graph_sha256']
  pairs={}
  for name,digest in source['payload_sha256'].items():
   assert sha(directory/name)==digest==sha(own/name)==target['payload_sha256'][name]
   pairs[name]=digest;files.extend([directory/name,own/name])
  verified[key]=pairs;files.extend([directory/'completion.json',own/'completion.json'])
 row['byte_exact_same_command_payloads']=verified[key]
write(out/'metadata_runtime_aliases.json',metadata)
write(out/'summary.json',dict(passed=True,complete_wall_seconds=wall,disjoint_category_seconds=dict(leaf),
 disjoint_category_percent={k:v/wall*100 for k,v in leaf.items()},disjoint_sum_seconds=sum(leaf.values()),
 nested_diagnostics_not_added_to_wall=dict(native_worker_process_seconds=native_process,candidate_LOAD_native_process_seconds=eval_native,
 candidate_LOAD_independent_audit_seconds=eval_audit,candidate_LOAD_preparation_seconds=eval_prepare,
 actual_native_search_core_seconds=search_core if not unknown_search_core else None,actual_native_search_core_seconds_known_sum=search_core,unknown_search_core_workers=unknown_search_core,native_search_workers=worker_count,actual_candidate_LOADs=evaluation_count),
 phase_seconds={x['phase']:x['complete_process_seconds'] for x in stages},peak_PSS_sample=peak,metadata_runtime_aliases=metadata,
 peak_sample_timestamp_inside_phase_despite_total_outer_overhead=certain,
 observer_CPU_seconds=measure['observer_CPU_seconds'],observer_CPU_fraction_of_one_core_during_wall=measure['observer_CPU_seconds']/wall,
 source_sha256={str(p):sha(p) for p in files},
 qualification='Actual timing metadata cache aliases are explicitly recorded and each consumed payload checked byte-exact to own-command generation; external aliases remain static runtime dependencies. Disjoint child wall intervals replace their parent intervals; parent-minus-child residuals remain explicit, so nested native core/LOAD/audit diagnostics are never added again. This actual case output and measured command belong together. Historical imported native/domain points have unknown complete cost and cannot inherit this time. Peak PSS is sampled summed tree memory, not an exact instantaneous/individual-process peak. Timestamp phase attribution uses total unassigned outer overhead as a conservative boundary uncertainty; within-sample read skew remains. Observer CPU is separate, not added/subtracted from wall or calibrated away. Index-only or fused evaluation time savings cannot be inferred by deleting measured components: required native STA/check work still exists and needs actual new full-flow measurement.'))
write(out/'completion.json',dict(passed=True,native_calls_new=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'completion.json']},
 artifact_sha256={n:sha(out/n) for n in ['summary.json','disjoint_wall.csv','metadata_runtime_aliases.json']}))
print(dict(passed=True,wall=wall,categories=dict(leaf),nested_search_core_seconds=search_core,peak_phase=certain),flush=True)
