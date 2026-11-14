#!/usr/bin/env python3
"""Matched native controls for new endpoint-policy accepted near-critical repairs."""
import json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_selector import select

study=D/'current_sta_policy_R1_near_01';done=read(study/'completion.json');assert done['status']=='policy_pass_terminal'
events=read(study/'decisions.json');accepted=[r for r in events if r['policy']=='endpoint_vector' and r.get('decision',{}).get('accepted')]
assert accepted,'No distinct accepted near-critical opportunity to control'
b=D/'current_sta_near_native_dev_01';b.mkdir(exist_ok=False);roles={}
for i,event in enumerate(accepted):
 assert event['candidate']['kind']=='single_capacity' and len(event['candidate']['targets'])==1
 target=event['candidate']['targets'][0];net,pin=target['net'],target['pin'];state=Path(event['source_state']);source=Path(read(state/'completion.json')['run'])
 selection=select(source/'native_sta_frontier.jsonl',.2);row=next(r for r in selection['targets'] if (r['net'],r['pin'])==(net,pin))
 role=f'endpoint_step_{i:03d}';request=b/(role+'.txt')
 request.write_text(f"1\n{net} 1 {pin}\n0\n1\n{net} {pin} {row['raw_criticality']:.17g}\n")
 files=[Path(__file__),study/'registration.json',study/'completion.json',study/'decisions.json',state/'completion.json',state/'endpoint_vector.json',source/'manifest.json',source/'routed.route',source/'native_sta_frontier.jsonl',request]
 roles[role]=dict(state=str(state),source=str(source),request=str(request),fixed_target_paths=False,removed_pins={str(net):[pin]},targets=[[net,pin]],order='one_current_STA_selected_sink',
  queries=[dict(net=net,pin=pin,slack_s=row['slack_s'],raw_criticality=row['raw_criticality'])],capacity_reference=event['evaluated_state'],
  source_sha256={str(p):sha(p) for p in files})
write(b/'registration.json',dict(status='registered_before_native',roles=roles,
 hypothesis='Near-window endpoint improvements may come from selector and extra single-sink opportunities rather than a distinct capacity-search algorithm.',
 controls='Each role begins from exactly the capacity branch state before its accepted step. Same single-sink pruning, all other branches retained, full-device range, native transformed current criticality, native occupancy update and identical FULL/STA acceptance. No preset capacity path.',
 qualification='Matched-state per-step causal controls, not an autonomous native trajectory after divergence. If native agrees, selector/opportunities are the demonstrated difference. No cold-start formal timing or cross-circuit inference.',
 source_sha256={str(p):sha(p) for p in [Path(__file__),study/'completion.json',study/'decisions.json']}))
print(dict(roles=list(roles)),flush=True)
