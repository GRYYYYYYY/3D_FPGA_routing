#!/usr/bin/env python3
"""Append actual BNN observations to sealed archive without rerunning old work."""
import collections,csv,functools,hashlib,json,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

start=time.monotonic();parent=D/'multiobjective_archive_01';out=D/'multiobjective_archive_02';out.mkdir(exist_ok=False)
old=read(parent/'completion.json');assert old['passed']
assert all(sha(parent/n)==h for n,h in old['artifact_sha256'].items())
points=read(parent/'points.json');files={str(parent/'completion.json'):sha(parent/'completion.json'),str(parent/'points.json'):sha(parent/'points.json'),str(Path(__file__).resolve()):sha(__file__)}
@functools.lru_cache(None)
def digest(p):return sha(p)
def bind(p):
 p=Path(p).resolve();files[str(p)]=digest(str(p));return files[str(p)]
def load(p):bind(p);return read(p)
def option(cmd,name,default=None):return cmd[cmd.index(name)+1] if name in cmd else default
def key(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
observations=load(D/'timing_cone_bnn_dev_02/completion.json');direct=load(D/'bnn_direct_repair_dev_01/completion.json')
assert observations['passed'] and direct['passed']
states=[(Path(r['state']),arm,'current_initial_observation') for arm,r in observations['roles'].items()]
states += [(Path(r['evaluation']),'Tf_repair_'+mode,'bnn_direct_repair_dev_01') for mode,r in direct['roles'].items()]
write(out/'registration.json',dict(status='registered_before_extraction',parent=str(parent),new_states=[dict(state=str(s),arm=a,batch=b) for s,a,b in states],
 rule='Append every completed BNN initial and matched direct-repair state, including quality-dominated outcomes. Keep old points intact except recomputed dominance annotations. No native calls, no historical reruns or hybrid quality/runtime points.',
 quality_dimensions=['CPD_ns','wirelength','SB_pairs','CB_sources'],timing='New observation/controller/core times are explicitly not standalone algorithm runtime.'))
for state,arm,batch in states:
 c=load(state/'completion.json');assert c['passed'];run=Path(c['run']);m=load(run/'manifest.json');cmd=m['command']
 assert m['status']=='completed' and m['metrics']['native_full_check_passed']
 for n in ['packed.net','placed.place','routed.route']:assert bind(run/n)==m['outputs'][n]['sha256']
 audit=load(run/'independent_audit.json');assert audit['audit']['passed'];phys=audit['physical_metrics']
 graph=Path(option(cmd,'--read_rr_graph'));arch=Path(cmd[1]);blif=Path(cmd[2]);binary=Path(cmd[0])
 for p in [graph,arch,blif,binary]:assert bind(p)==m['shared_inputs'][str(p)]['sha256']
 sdc=option(cmd,'--sdc_file')
 if sdc:sdc_identity=bind(Path(sdc))
 else:
  assert 'Setting default timing constraints:' in (run/'stdout.log').read_text();sdc_identity='native_generated_default_from_bound_netlist'
 identity=dict(architecture=digest(str(arch)),graph=digest(str(graph)),netlist=digest(str(blif)),packed=digest(str(run/'packed.net')),placed=digest(str(run/'placed.place')),clock_modeling=option(cmd,'--clock_modeling','default'),sdc=sdc_identity,seed=option(cmd,'--seed'))
 v=load(state/'endpoint_vector.json');cpd=v['cpd_s']*1e9
 p=dict(id=str(run.relative_to(D)),arm=arm,circuit=blif.stem,batch=batch,state=str(state),status='legal',physical_identity=identity,quality_cohort=key(identity),
  run_manifest=str(run/'manifest.json'),binary_sha256=digest(str(binary)),route_sha256=digest(str(run/'routed.route')),route_body_sha256=route_body(run/'routed.route'),command=cmd,environment=m.get('environment'),
  convergence=option(cmd,'--router_max_convergence_count','native_default'),opportunity='existing_or_repaired_route_observation',CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='full native endpoint-vector seconds converted to ns',
  wirelength=phys['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=phys['sb_pairs_used'],CB_sources=phys['cb_crossing_output_sources_used'],SB_net_occupancy=phys['sb_pair_net_occupancy'],CB_net_occupancy=phys['cb_crossing_output_source_net_occupancy'],iterations=m['metrics'].get('iterations'),
  complete_single_configuration_seconds=None,analysis_only_native_seconds=m['wall_seconds'],timing_cohort=None,observation_workflow=c['timing'],shared_research_workflow=None,
  audit_provenance=str(run/'independent_audit.json'),unknowns=['Complete single-configuration algorithm runtime; observation, repair core and shared multi-arm workflow are distinct scopes'])
 if batch=='bnn_direct_repair_dev_01':
  p['shared_research_workflow']=dict(batch=str(D/batch),seconds=direct['complete_orchestrator_seconds'],scope='shared two-arm diagnostic, not point algorithm runtime')
  p['native_repair_core_seconds']=direct['roles'][arm.removeprefix('Tf_repair_')]['native_core_seconds']
 assert not any(x['id']==p['id'] for x in points);points.append(p)

def dominates(a,b,with_time=False,interval=True):
 names=['wirelength','SB_pairs','CB_sources']+(['complete_single_configuration_seconds'] if with_time else [])
 if any(a[k] is None or b[k] is None or a[k]>b[k] for k in names):return False
 equal_route=a['route_body_sha256']==b['route_body_sha256'] and a['binary_sha256']==b['binary_sha256']
 if interval and not equal_route:
  if a['CPD_interval_ns'][1]>b['CPD_interval_ns'][0]:return False
  strict=a['CPD_interval_ns'][1]<b['CPD_interval_ns'][0]
 else:
  if a['CPD_ns']>b['CPD_ns']:return False
  strict=a['CPD_ns']<b['CPD_ns']
 return strict or any(a[k]<b[k] for k in names)
for b in points:
 b.update(quality_dominated_by=[],nominal_quality_dominated_by=[],matched_time_dominated_by=[])
 for a in points:
  if a['id']==b['id'] or a['quality_cohort']!=b['quality_cohort']:continue
  if dominates(a,b):b['quality_dominated_by'].append(a['id'])
  if dominates(a,b,interval=False):b['nominal_quality_dominated_by'].append(a['id'])
  if a['timing_cohort'] and a['timing_cohort']==b['timing_cohort'] and a['convergence']==b['convergence'] and dominates(a,b,True):b['matched_time_dominated_by'].append(a['id'])
 b['archive_retained']=not b['quality_dominated_by'];b['quality_status']='dominated' if b['quality_dominated_by'] else 'uncertain_due_to_CPD_precision' if b['nominal_quality_dominated_by'] else 'nondominated_in_collected_population'
write(out/'points.json',points)
fields=['id','arm','circuit','status','CPD_ns','wirelength','SB_pairs','CB_sources','convergence','complete_single_configuration_seconds','analysis_only_native_seconds','quality_status','timing_cohort']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p[k] for k in fields} for p in points)
new=points[-len(states):];weighted=next(p for p in new if p['arm']=='Tf_repair_weighted_soft');physical=next(p for p in new if p['arm']=='Tf_repair_physical_capacity')
assert weighted['id'] in physical['quality_dominated_by'] and weighted['complete_single_configuration_seconds'] is None
write(out/'completion.json',dict(passed=True,parent=str(parent),points=len(points),new_points=len(states),counts_by_quality_status=dict(collections.Counter(p['quality_status'] for p in points)),
 source_sha256=files,artifact_sha256={n:sha(out/n) for n in ['registration.json','points.json','points.csv']},native_calls=0,complete_process_seconds=time.monotonic()-start,
 validation='Actual exact-state native weighted repair dominates physical-capacity repair in four quality dimensions, not a full-cost superiority claim. Parent records inherited through sealed payload checks; no repeated native runs.',
 qualification='Descriptive state archive including strong baselines and unequal opportunities; not per-circuit cherry-picked confirmation. Unknown complete runtime prevents five-dimensional dominance conclusions.'))
print(dict(points=len(points),new_points=len(states),weighted_status=weighted['quality_status'],physical_status=physical['quality_status']),flush=True)
