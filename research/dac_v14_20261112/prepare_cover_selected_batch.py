#!/usr/bin/env python3
"""Register smaller current-path covering scopes using a uniform proxy rule."""
import collections,json,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
b=D/'bnn_cover_selected_dev_01';b.mkdir(exist_ok=False);policy=read(D/'critical_group_cover_policy_01.json');ref=read(D/'critical_group_cover_reference_01/completion.json');assert ref['passed']
assert read(D/'fixed_anchor_acceptance_validation_01.json')['passed'] and read(D/'compact_cone_benchmark_01/completion.json')['passed']
roles={};reuse={};files=[Path(__file__).resolve(),D/'critical_group_cover_policy_01.json',D/'critical_group_cover_reference_01/completion.json',D/'run_registered_native_transactions_v3.py',D/'fixed_anchor_acceptance.py',D/'fixed_anchor_acceptance_validation_01.json',D/'compact_selector_stage_01/binding.json']
obs=read(D/'timing_cone_bnn_dev_02/completion.json')
for arm,s in policy['selections'].items():
 state=Path(ref['results'][arm]['source_state']);source=run_dir(state);selected=s['selected'];targets=list(map(tuple,selected['targets']));pins=list(map(tuple,selected['repair_pins']));removed=collections.defaultdict(set)
 assert len(pins)==selected['repair_connections'] and set(targets)<=set(pins)
 for net,pin in pins:removed[net].add(pin)
 sta={}
 for line in (source/'native_sta_frontier.jsonl').open():
  p=json.loads(line)
  if p.get('type')=='pin' and not p['driver']:sta[p['net'],p['pin']]=p
 ordered=sorted(targets,key=lambda x:(sta[x]['setup_slack_s'],x))+[x for x in sorted(pins) if x not in targets]
 request=b/(arm+'.txt')
 with request.open('w') as f:
  f.write(str(len(removed))+'\n')
  for n,ps in sorted(removed.items()):f.write(' '.join(map(str,[n,len(ps),*sorted(ps)]))+'\n')
  f.write('0\n'+str(len(ordered))+'\n')
  for n,pin in ordered:f.write(f"{n} {pin} {sta[n,pin]['setup_criticality_raw']:.17g}\n")
 v=read(state/'endpoint_vector.json');p=read(source/'independent_audit.json')['physical_metrics'];anchor=dict(CPD_s=v['cpd_s'],wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'])
 sourcefiles=[state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'native_sta_frontier.jsonl',request];files+=sourcefiles
 role=dict(state=str(state),source=str(source),request=str(request),objective='weighted_soft',fixed_target_paths=False,targets=targets,removed_pins={str(n):sorted(ps) for n,ps in removed.items()},scope='cover90',baseline=arm,queries=[dict(net=n,pin=pin,slack_s=sta[n,pin]['setup_slack_s'],raw_criticality=sta[n,pin]['setup_criticality_raw']) for n,pin in ordered],original_budget=anchor,source_sha256={str(p):sha(p) for p in sourcefiles})
 if arm=='R1':
  old=read(D/'bnn_release_joint_dev_01/registration.json')['roles']['R1_target_only_weighted_soft']
  assert sha(request)==sha(old['request']) and role['state']==old['state'] and role['queries']==old['queries'] and role['original_budget']==old['original_budget']
  old_dec=D/'bnn_release_joint_dev_01/R1_target_only_weighted_soft_decisions.json';assert read(old_dec)['strict']['accepted']
  reuse[arm]=dict(status='exact_request_source_scope_and_budget_reused',decision=str(old_dec),evaluation=str(D/'bnn_release_joint_dev_01/R1_target_only_weighted_soft_evaluation'),new_native_calls=0)
  files += [old_dec,D/'bnn_release_joint_dev_01/registration.json']
 else:roles[arm+'_cover90_weighted_soft']=role
write(b/'registration.json',dict(status='registered_before_native',roles=roles,reused_controls=reuse,selector_fraction=.9,
 question='Does a smaller uniform current-winning-path covering group preserve timing gain with fewer modified branches or resources than all-positive-group repair?',
 controls='Tf13 vs existingTf16; A014 vs already queuedA029; R1 identical2query request reuses its completed native result. Same nativeweighted backend, full-device search and original constraints; no forced paths. Compact successor selection and fixed-anchor current-step comparisons are independently validated.',
 qualification='Development proxy selection, not confirmation. Real capacity competition/near-critical migration may defeat proxy gains. New arms not yet submitted to native queue; preserve both existing registered cohorts. Current-path coverage is a necessary strict-CPD proxy, not a global filter for resource or endpoint-vector opportunities.',
 source_sha256={str(p):sha(p) for p in files},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
print({k:len(v['queries']) for k,v in roles.items()},reuse,flush=True)
