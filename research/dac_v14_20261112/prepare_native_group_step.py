#!/usr/bin/env python3
"""Turn a current-state group proposal into a native transaction without stale targets."""
import argparse,collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir,input_identity
p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--anchor-state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--objective',choices=['weighted_soft','weighted_capacity','physical_capacity'],default='weighted_soft');a=p.parse_args()
plan=read(a.plan);assert plan['passed'] and all(sha(p)==h for p,h in plan['source_sha256'].items())
b=a.output.resolve();b.mkdir(exist_ok=False);state=Path(plan['source_state']);source=run_dir(state);anchor=a.anchor_state.resolve();arun=run_dir(anchor)
assert read(state/'completion.json')['passed'] and read(anchor/'completion.json')['passed'] and input_identity(source)==input_identity(arun)
current_vector=read(state/'endpoint_vector.json');original=read(anchor/'endpoint_vector.json');assert current_vector['constraints_sha256']==original['constraints_sha256']
if not plan['repair_pins']:
 write(b/'no_transaction.json',dict(status='no_strict_CPD_group_in_current_proposal_class',state=str(state),anchor_state=str(anchor),native_calls=0,qualification='No native transaction submitted. This is an operator scope result, not research completion or rejection of resource/near-critical mechanisms.'));raise SystemExit(0)
removed=collections.defaultdict(set)
for n,pin in plan['repair_pins']:removed[n].add(pin)
request=b/'candidate.txt';queries=plan['ordered_queries'];assert {(q['net'],q['pin']) for q in queries}==set(map(tuple,plan['repair_pins'])) and len(queries)==len(plan['repair_pins'])
with request.open('w') as f:
 f.write(str(len(removed))+'\n')
 for n,pins in sorted(removed.items()):f.write(' '.join(map(str,[n,len(pins),*sorted(pins)]))+'\n')
 f.write('0\n'+str(len(queries))+'\n')
 for q in queries:f.write(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\n")
physical=read(arun/'independent_audit.json');assert physical['audit']['passed'];r=physical['physical_metrics'];budget=dict(CPD_s=original['cpd_s'],wirelength=r['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=r['sb_pairs_used'],CB_sources=r['cb_crossing_output_sources_used'])
files=[Path(__file__).resolve(),a.plan,state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'native_sta_frontier.jsonl',anchor/'completion.json',anchor/'endpoint_vector.json',arun/'independent_audit.json',request,D/'run_registered_native_transactions_v3.py',D/'fixed_anchor_acceptance.py',D/'fixed_anchor_acceptance_validation_01.json',D/'compact_selector_stage_01/binding.json']
bindings={str(p.resolve()):sha(p) for p in files}
role=dict(state=str(state),source=str(source),request=str(request),objective=a.objective,fixed_target_paths=False,targets=plan['selection']['targets'],removed_pins={str(n):sorted(ps) for n,ps in removed.items()},scope='automatic_current_group',baseline='current',queries=queries,original_budget=budget,source_sha256=bindings)
write(b/'registration.json',dict(status='registered_before_native',roles={'current_group':role},anchor_state=str(anchor),question='Execute the freshly planned group on its actual current state and compare each policy using original design budgets plus current-state progress.',
 source_sha256=bindings,limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),qualification='Only this current-state step is registered. Native execution requires independent queue ownership; no batch was launched by preparation. Earlier states remain immutable; original budgets never roll forward.'))
print(dict(queries=len(queries),targets=role['targets'],anchor=str(anchor),state=str(state)),flush=True)
