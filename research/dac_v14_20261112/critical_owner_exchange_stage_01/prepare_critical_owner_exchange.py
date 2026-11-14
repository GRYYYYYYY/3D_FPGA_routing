#!/usr/bin/env python3
"""Register native controls for dependency-closure expansion and path adoption."""
import collections,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir,input_identity
p=D/'critical_owner_exchange_expansion_01/completion.json';exp=read(p);assert exp['passed'] and all(sha(path)==h for path,h in exp['source_sha256'].items())
proof=D/'conditional_distance_certificate_validation_01.json';assert read(proof)['passed'];assert all(sha(path)==h for path,h in read(proof)['source_sha256'].items())
state=Path(exp['input_state']);source=run_dir(state);anchor=D/'timing_cone_bnn_dev_01/Tf';assert input_identity(source)==input_identity(run_dir(anchor));v=read(state/'endpoint_vector.json');av=read(anchor/'endpoint_vector.json');assert v['constraints_sha256']==av['constraints_sha256']
f=D/'bnn_automatic_trajectories_dev_02/Tf_strict/step_001/feedback';op=read(f/'owners/completion.json');cone=read(f/'cone.json');assert Path(op['input_state'])==state
physical=read(run_dir(anchor)/'independent_audit.json')['physical_metrics'];budget=dict(CPD_s=av['cpd_s'],wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'])
b=D/'critical_owner_exchange_dev_01';b.mkdir(exist_ok=False);roles={};pins={}
for line in (source/'native_sta_frontier.jsonl').open():
 row=json.loads(line)
 if row.get('type')=='pin' and not row['driver']:pins[row['net'],row['pin']]=row
files=[Path(__file__).resolve(),p,proof,D/'run_registered_exchange_transactions.py',D/'audit_native_objective_presets.py',D/'native_objective_stage_01/binding.json',D/'fixed_anchor_acceptance.py',anchor/'completion.json',anchor/'endpoint_vector.json',run_dir(anchor)/'independent_audit.json',state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'native_sta_frontier.jsonl',f/'owners/completion.json',f/'cone.json']
for index,r in enumerate(exp['rows']):
 assert r['critical_core_paths_compatible'];target=tuple(r['target']);witness=next(x for x in op['rows'] if tuple(x['target'])==target);critical=set(next(x for x in read(D/'critical_owner_exchange_query_01/completion.json')['rows'] if x['target']==r['target'])['critical_owners'])
 settings=[('minimal_preset_weighted','old_removed_pins',True,'weighted_soft','target_first'),('expanded_preset_weighted','expanded_removed_pins',True,'weighted_soft','target_first'),('expanded_free_weighted','expanded_removed_pins',False,'weighted_soft','target_first'),('expanded_preset_physical','expanded_removed_pins',True,'physical_capacity','target_first'),('expanded_owner_first_weighted','expanded_removed_pins',False,'weighted_soft','owner_first')]
 for name,field,preset,objective,order in settings:
  name=f'{index:03d}_'+name;removed={int(n):sorted(ps) for n,ps in r[field].items()};allpins={(n,pin) for n,ps in removed.items() for pin in ps};owner_queries=sorted(k for k in allpins if k[0] in critical);other_queries=sorted(allpins-{target}-set(owner_queries));ordered=owner_queries+other_queries if preset else ([target]+owner_queries+other_queries if order=='target_first' else owner_queries+[target]+other_queries)
  assert set(ordered)==allpins-({target} if preset else set()) and len(ordered)==len(set(ordered))
  request=b/(name+'.txt');preset_paths=[]
  with request.open('w') as out:
   out.write(str(len(removed))+'\n')
   for n,ps in sorted(removed.items()):out.write(' '.join(map(str,[n,len(ps),*ps]))+'\n')
   out.write(('1\n' if preset else '0\n'))
   if preset:
    path=witness['relaxed_suffix_nodes'];switches=witness['relaxed_suffix_switches'];out.write(f'{target[0]} {target[1]} {len(switches)}\n')
    for u,z,sw in zip(path,path[1:],switches):out.write(f'{u} {z} {sw}\n')
    preset_paths=[dict(net=target[0],pin=target[1],nodes=path,switches=switches,source=str(f/'owners/completion.json'))]
   out.write(str(len(ordered))+'\n')
   for n,pin in ordered:
    row=pins[n,pin];assert not row['global'] and not row['ignored'];out.write(f"{n} {pin} {row['setup_criticality_raw']:.17g}\n")
  bound={str(p):sha(p) for p in [*files,request]};roles[name]=dict(state=str(state),source=str(source),request=str(request),baseline='Tf_current',scope=name,objective=objective,fixed_target_paths=preset,preset_paths=preset_paths,targets=[list(target)]+[list(k) for k in owner_queries if k in {(z['net'],z['pin']) for z in cone['routed_connections']}],removed_pins={str(n):ps for n,ps in removed.items()},queries=[dict(net=n,pin=pin,raw_criticality=pins[n,pin]['setup_criticality_raw'],slack_s=pins[n,pin]['setup_slack_s']) for n,pin in ordered],original_budget=budget,source_sha256=bound,order=order,selection='Current target/critical owner from audited conflicts; expanded noncritical pins from actual descendant branches. No net-ID whitelist.')
  files.append(request)
write(b/'registration.json',dict(status='registered_before_native',roles=roles,anchor_state=str(anchor),source_sha256={str(p):sha(p) for p in files},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 question='Can an automatically expanded critical-owner/noncritical-release transaction turn a fixed-target185.826ps optimistic gain into legal final timing/resource improvement? Is the outcome caused by expanded scope, adopting the queried target path, scheduling, or cost/capacity treatment?',
 controls='Minimal versus expanded preset weighted isolates closure extent. Expanded free weighted gives native search the same full-device domain, removed trees, selection, one acceptance opportunity and a wider target-path choice; preset fixes the prequeried witness. Expanded owner-first weighted isolates schedule against free target-first. Physical preset changes cost/capacity treatment together, not a pure capacity ablation.',
 gates='All original state/occupancy restoration, explicit preset edges/switches, retained branches/terminals, real resource capacities, complete native FULL/STA and exact fixed-root-budget decisions remain mandatory.',
 qualification='Independent current repaired-state mechanism diagnosis, not a pristine-start general algorithm evaluation. Kernel is existing native search; algorithmic claims concern dependency closure, path adoption and scheduling, not a new search primitive. No expected local gain is accepted without final whole checks. Current registered actors/reservation/static batch remain unchanged.'))
print(dict(roles=len(roles),connections={name:sum(map(len,r['removed_pins'].values())) for name,r in roles.items()}))
