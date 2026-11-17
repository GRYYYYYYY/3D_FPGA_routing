"""Existing-stage observation: distinguish finite coverage from changed fresh routing."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,collections
from retained_prefix_workflow import D,read,write,sha,route_body
C=D/'cp1r6_clma_io_pair_01';plan=read(C/'plan.json');F=Path(plan['inputs'][0]['workspace'])/'native/flow/resource_flow';state=F/'initial';run=Path(read(state/'completion.json')['run']);selection=F/'repair/round_000/selection/completion.json';sel=read(selection);assert sel['passed'];assert read(F/'repair/completion.json')['passed']
oldplan=read(D/'cp1r6_clma_pair_01/plan.json');oldstate=Path(oldplan['inputs'][0]['workspace'])/'native/flow/resource_flow/initial';oldrun=Path(read(oldstate/'completion.json')['run'])
oldrows=read(D/'CLMA_initial_scope_boundary_01/rows.json');targets={r['net']:r['name'] for r in oldrows};pins={r['net']:{p for s in r['scopes'] for p in s['pins']} for r in oldrows};obs=collections.defaultdict(list)
for line in (run/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r.get('type')=='pin' and r['net'] in targets and r['pin'] in pins[r['net']]:obs[r['net']].append(r)
coverage=[]
for net,name in targets.items():
 rows=obs[net];assert {r['pin'] for r in rows}==pins[net]
 finite=lambda x:isinstance(x,(float,int)) and math.isfinite(x)
 coverage.append(dict(net=net,name=name,observed_pins=len(rows),setup_slack_finite=sum(finite(r['setup_slack_s']) for r in rows),setup_slack_nonfinite=sum(not finite(r['setup_slack_s']) for r in rows),setup_slack_min_s=min((r['setup_slack_s'] for r in rows if finite(r['setup_slack_s'])),default=None),qualification='Same packed net/pin identifiers, but this is a newly routed tree; not a fixed-route constraint ablation.'))
vector=read(state/'endpoint_vector.json');counts={kind:dict(components=len(vector[kind]),finite=sum(isinstance(x,(float,int)) and math.isfinite(x) for x in vector[kind].values()),negative=sum(isinstance(x,(float,int)) and x<0 for x in vector[kind].values())) for kind in ['setup','hold']}
files=[Path(__file__).resolve(),selection,F/'repair/completion.json',state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'native_sta_frontier.jsonl.constraints.echo',D/'CLMA_initial_scope_boundary_01/rows.json',oldstate/'completion.json',D/'VTR_clma_io_input_01/registration.json']
raw=dict(observed_at=datetime.now(timezone.utc).isoformat(),stage='native_initial_and_resource_terminal',initial_FULL_STA_physical_passed=True,CPD_ns=sel['CPD_s']*1e9,resources=sel['actual_resources'],multi_crossing_nets=sel['multi_crossing_nets'],candidate_scopes=sel['candidate_scopes'],resource_accepted_steps=read(F/'repair/completion.json')['accepted_steps'],native_endpoint_counts=counts,former_unknown_net_pin_coverage=coverage,previous_initial_route_body_sha256=route_body(oldrun/'routed.route'),current_initial_route_body_sha256=route_body(run/'routed.route'),same_actual_initial_tree=route_body(oldrun/'routed.route')==route_body(run/'routed.route'),same_physical_inputs_except_SDC=all(sha(run/name)==sha(oldrun/name) for name in ['packed.net','placed.place']),new_independent_input=False,full_arm_admission_pending=True,full_pair_admission_pending=True,new_native_or_STA_calls=0,source_sha256={str(p):sha(p) for p in files},qualification='Preregistered I/O coverage became finite for the old target pins, but fresh routing also changed and removed prior redundancy. Thus this new initial-stage observation cannot establish that coverage alone unlocks the same old groups or that domain improves the complete flow. All quality remains stage-scoped until whole/pair admission.')
write(C/'native_initial_coverage_01.json',raw);print({k:raw[k] for k in ['CPD_ns','resources','native_endpoint_counts','former_unknown_net_pin_coverage','same_actual_initial_tree']})
