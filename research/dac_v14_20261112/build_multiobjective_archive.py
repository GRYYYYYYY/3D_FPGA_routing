#!/usr/bin/env python3
"""Provenance-preserving legal-route archive; no routing and no hybrid points."""
import collections,csv,functools,hashlib,json,math,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body

start=time.monotonic();out=D/'multiobjective_archive_01';out.mkdir(exist_ok=False)
files={};points=[];failures=[]
@functools.lru_cache(None)
def digest(path):return sha(path)
def bind(path):
 path=Path(path).resolve();files[str(path)]=digest(str(path));return files[str(path)]
def load(path):bind(path);return read(path)
def option(cmd,name,default=None):return cmd[cmd.index(name)+1] if name in cmd else default
def key(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()

formal=load(D/'formal_timing_01/observations.json')
sources=[]
for row in formal:sources.append((Path(row['path']),row['arm'],'formal_timing_01',None))
for circuit in ['eltwise','spmv','softmax','bnn']:
 for path in sorted((D/f'native_reconvergence_{circuit}_dev_01/runs').glob('*/manifest.json')):
  arm=path.parent.name.rsplit('_',1)[-1]
  if arm in ['A0','R1','Tf']:sources.append((path.parent,arm,path.parents[2].name,None))
states=set(D.glob('current_sta_policy_native_*/attempt_*/evaluation/completion.json'))
states.update(D.glob('native_endpoint_spmv_dev_01/*/completion.json'))
states.update(D.glob('native_endpoint_vector_dev_01/*/completion.json'))
for name in ['successor_native_controls_01/weighted_soft_evaluation/completion.json']:
 if (D/name).exists():states.add(D/name)
for state in sorted(states):
 c=load(state)
 if c.get('passed') and c.get('run') and (state.parent/'endpoint_vector.json').exists():
  sources.append((Path(c['run']),'repair_or_observed_state',state.parent.name,state.parent))
 else:failures.append(dict(path=str(state),status=c.get('status'),passed=c.get('passed'),reason='not a complete legal endpoint state'))
write(out/'registration.json',dict(status='registered_before_extraction',question='Which existing legal A0/R1/U/Tf and repair states survive a joint CPD/wire/SB/CB archive, and which time comparisons are actually matched?',
 population='All45 formal-timing repeats; strong A0/R1/Tf native-reconvergence runs in4 available circuits; every completed native-policy candidate evaluation plus initial exact endpoint states. Explicit development archive, not a circuit-wise best-configuration confirmation sample.',
 sources=[dict(run=str(p),label=a,batch=b,state=None if s is None else str(s)) for p,a,b,s in sources],
 dimensions=['CPD_ns','wirelength','SB_pairs','CB_sources'],time_dimension='Only same formal timing cohort, convergence setting and complete route+analysis process. Repair single-configuration algorithm total is unknown; native analysis-only times excluded.',
 dominance='Conservative interval dominance for six-significant-digit CPD reports, exact for endpoint-vector CPD. All dimensions no worse and at least one strictly better; overlapping CPD uncertainty retained. Descriptive state archive across opportunity levels is not causal algorithm evidence.',
 retention='Final candidates are distinct from intermediate transaction states. No existing acceptance decision is changed. Unknown cost never equals zero.',native_calls=0,source_sha256={str(Path(__file__).resolve()):sha(__file__)}))

seen=set()
for run,arm,batch,state in sources:
 run=run.resolve()
 if str(run) in seen:continue
 seen.add(str(run));m=load(run/'manifest.json');cmd=m['command'];metrics=m.get('metrics',{})
 if m['status']!='completed' or not metrics.get('native_full_check_passed'):
  failures.append(dict(path=str(run),status=m['status'],reason='native FULL not complete'));continue
 for n in ['packed.net','placed.place','routed.route']:
  assert bind(run/n)==m['outputs'][n]['sha256'],(run,n)
 if (run/'independent_audit.json').exists():
  audit=load(run/'independent_audit.json');assert audit['audit']['passed'];physical=audit['physical_metrics'];audit_source=str(run/'independent_audit.json')
 else:
  reuse=load(run/'quality_reuse.json');assert reuse['passed'] and all(reuse['checks'].values())
  ref=Path(reuse['reference']['path']);assert bind(ref/'manifest.json')==reuse['reference']['manifest_sha256'];assert bind(ref/'independent_audit.json')==reuse['reference']['independent_audit_sha256']
  assert route_body(run/'routed.route')==reuse['reference']['route_body_sha256']==route_body(ref/'routed.route')
  for n in ['packed.net','placed.place']:assert bind(run/n)==bind(ref/n)
  assert all(digest(p)==h for p,h in reuse['physical_inputs'].items())
  physical=reuse['reference']['physical_metrics'];audit_source=str(run/'quality_reuse.json')
 graph=Path(option(cmd,'--read_rr_graph'));arch=Path(cmd[1]);blif=Path(cmd[2]);binary=Path(cmd[0])
 for p in [graph,arch,blif,binary]:assert bind(p)==m['shared_inputs'][str(p)]['sha256']
 sdc=option(cmd,'--sdc_file');clock=option(cmd,'--clock_modeling','default')
 if sdc:sdc_identity=bind(Path(sdc))
 else:
  text=(run/'stdout.log').read_text();assert 'Setting default timing constraints:' in text
  sdc_identity='native_generated_default_from_bound_netlist'
 identity=dict(architecture=digest(str(arch)),graph=digest(str(graph)),netlist=digest(str(blif)),
  packed=digest(str(run/'packed.net')),placed=digest(str(run/'placed.place')),clock_modeling=clock,sdc=sdc_identity,seed=option(cmd,'--seed'))
 cpd=metrics['critical_path_ns'];half=0.5*10**(math.floor(math.log10(abs(cpd)))-5)
 interval=[cpd-half,cpd+half];precision='native six-significant-digit printed ns';observation_seconds=None
 if state:
  vector=load(state/'endpoint_vector.json');cpd=vector['cpd_s']*1e9;interval=[cpd,cpd];precision='full native endpoint-vector seconds converted to ns';observation_seconds=load(state/'completion.json')['timing']
 has_route='--route' in cmd
 controller=next((p for p in run.parents if p.name.startswith('current_sta_policy_native_')),None)
 workflow=None
 if controller and (controller/'completion.json').exists():
  c=load(controller/'completion.json');workflow=dict(batch=str(controller),seconds=c.get('complete_orchestrator_seconds'),scope='shared policy research workflow, historical query/native reuse may apply; not point algorithm runtime')
 p=dict(id=str(run.relative_to(D)),arm=arm,circuit=blif.stem,batch=batch,state=None if state is None else str(state),status='legal',
  physical_identity=identity,quality_cohort=key(identity),run_manifest=str(run/'manifest.json'),binary_sha256=digest(str(binary)),
  route_sha256=digest(str(run/'routed.route')),route_body_sha256=route_body(run/'routed.route'),command=cmd,environment=m.get('environment'),
  convergence=option(cmd,'--router_max_convergence_count','native_default'),opportunity='initial_route' if has_route else 'existing_or_repaired_route_observation',
  CPD_ns=cpd,CPD_interval_ns=interval,CPD_precision=precision,wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'],
  SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],iterations=metrics.get('iterations'),
  complete_single_configuration_seconds=m['wall_seconds'] if has_route else None,analysis_only_native_seconds=None if has_route else m['wall_seconds'],
  timing_cohort='formal_timing_01' if batch=='formal_timing_01' else None,observation_workflow=observation_seconds,shared_research_workflow=workflow,
  audit_provenance=audit_source,unknowns=[] if has_route else ['complete standalone repair algorithm time including failures, source construction, replacement, FULL/STA and rollback'],
  quality_dominated_by=[],nominal_quality_dominated_by=[],matched_time_dominated_by=[])
 points.append(p)

def dominates(a,b,with_time=False,interval=True):
 names=['wirelength','SB_pairs','CB_sources']
 if with_time:names.append('complete_single_configuration_seconds')
 if any(a[k] is None or b[k] is None or a[k]>b[k] for k in names):return False
 equal_route=a['route_body_sha256']==b['route_body_sha256'] and a['binary_sha256']==b['binary_sha256']
 if interval and not equal_route:
  if a['CPD_interval_ns'][1]>b['CPD_interval_ns'][0]:return False
  cstrict=a['CPD_interval_ns'][1]<b['CPD_interval_ns'][0]
 else:
  if a['CPD_ns']>b['CPD_ns']:return False
  cstrict=a['CPD_ns']<b['CPD_ns']
 return cstrict or any(a[k]<b[k] for k in names)
for b in points:
 for a in points:
  if a['id']==b['id'] or a['quality_cohort']!=b['quality_cohort']:continue
  if dominates(a,b):b['quality_dominated_by'].append(a['id'])
  if dominates(a,b,interval=False):b['nominal_quality_dominated_by'].append(a['id'])
  if a['timing_cohort'] and a['timing_cohort']==b['timing_cohort'] and a['convergence']==b['convergence'] and dominates(a,b,True):b['matched_time_dominated_by'].append(a['id'])
 b['archive_retained']=not b['quality_dominated_by']
 b['quality_status']='dominated' if b['quality_dominated_by'] else 'uncertain_due_to_CPD_precision' if b['nominal_quality_dominated_by'] else 'nondominated_in_collected_population'
write(out/'points.json',points);write(out/'failures_or_incomplete.json',failures)
fields=['id','arm','circuit','status','CPD_ns','wirelength','SB_pairs','CB_sources','iterations','convergence','complete_single_configuration_seconds','analysis_only_native_seconds','quality_status','timing_cohort']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p[k] for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,points=len(points),quality_cohorts=len({p['quality_cohort'] for p in points}),retained=sum(p['archive_retained'] for p in points),
 counts_by_quality_status=dict(collections.Counter(p['quality_status'] for p in points)),failures_or_incomplete=len(failures),source_sha256=files,
 artifact_sha256={n:sha(out/n) for n in ['registration.json','points.json','points.csv','failures_or_incomplete.json']},native_calls=0,complete_process_seconds=time.monotonic()-start,
 qualification='All rows are actual complete run/observation points. No best-quality value is paired with a different-run runtime. Across opportunity levels quality dominance is descriptive, not a fair algorithm comparison. Missing complete repair time precludes five-dimensional superiority. CPD precision uncertainty is retained rather than rounded away.'))
print(dict(points=len(points),retained=sum(p['archive_retained'] for p in points),seconds=time.monotonic()-start),flush=True)
