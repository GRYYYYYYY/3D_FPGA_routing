"""Verify same-execution fresh routing, all repair attempts, wall and memory."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity

import argparse
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--cache-mode',choices=['build_inside_flow','reusable_graph_only'],required=True);args=p.parse_args()
root=args.root.resolve();reg=read(root/'queue/registration.json')
actual=process_identity(reg['pid']);assert not actual or actual['state']=='Z' or actual['start_ticks']!=reg['start_ticks']
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
measure=read(root/'measurement/completion.json');flow=read(root/'flow/completion.json')
assert measure['passed'] and measure['returncode']==0 and flow['passed']
assert not measure['live_descendants_after_command_exit']
config=read(root/'config.json');assert config['initial_route_imported'] is False
assert config['cache_mode']==args.cache_mode and config['domain_mode'] in ['unrestricted','paired']
assert all(sha(p)==h for p,h in config['input_sha256'].items())
assert all(sha(p)==h for p,h in flow['source_sha256'].items())
if args.cache_mode=='build_inside_flow':
    for cache in ['graph_audit_cache','full_graph_cache']:assert read(root/'flow'/cache/'completion.json')['passed']
else:assert read(Path(config['full_graph_cache'])/'completion.json')['passed']
repair=root/'flow/repair';terminal=read(repair/'completion.json')
assert terminal['passed'] and terminal['operator_stop']=='no_admissible_candidate_in_registered_current_scope_probe'
assert all(sha(p)==h for p,h in terminal['source_sha256'].items())
attempts=read(repair/'attempts.json');steps=read(repair/'steps.json')
assert len(steps)==terminal['accepted_steps']>0
for attempt in attempts:
    assert attempt['native_transaction_complete'], 'An execution/audit failure cannot establish menu exhaustion'
    tx=Path(attempt['transaction']);c=read(tx/'completion.json');assert c['passed']
    assert all(sha(p)==h for p,h in c['source_sha256'].items())
    assert all(r['status'] in ['legal_evaluated','transaction_failed_rolled_back'] for r in c['roles'].values())
    assert all(not r.get('native_reused',False) for r in c['roles'].values())
initial,final=map(Path,[flow['initial_state'],flow['final_state']])
assert terminal['initial_state']==str(initial) and terminal['final_state']==str(final)
assert steps[-1]['committed_evaluation']==str(final)
for state in [initial,final]:
    c=read(state/'completion.json');assert c['passed']
    rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
    assert read(rd/'independent_audit.json')['audit']['passed']
    assert all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
v0,v1=[read(s/'endpoint_vector.json') for s in [initial,final]]
assert v0['constraints_sha256']==v1['constraints_sha256'] and v1['cpd_s']<=v0['cpd_s']
assert flow['final_CPD_s']==terminal['final_CPD_s']==v1['cpd_s']
axes=read(run_dir(final)/'independent_audit.json')['physical_metrics']
resources=dict(wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'])
assert resources==flow['final_resources']==terminal['final_resources']
stages=read(root/'flow/stages.json');assert all(s['status']=='completed' for s in stages)
assert [s['phase'] for s in stages]==(['build_audit_cache','build_full_cache'] if args.cache_mode=='build_inside_flow' else [])+['fresh_route_and_materialization','resource_repair']
payload=dict(passed=True,complete_configuration_verified=True,cache_mode=config['cache_mode'],initial_state=str(initial),final_state=str(final),
    CPD_ns=v1['cpd_s']*1e9,resources=resources,accepted_steps=len(steps),attempted_scopes=len(attempts),
    complete_wall_seconds=measure['complete_command_wall_seconds'],
    waited_process_RSS_high_water_kib=measure['waited_process_RSS_high_water_kib'],
    sampled_tree_RSS_peak_kib=measure['sampled_tree_RSS_peak_kib'],sampled_tree_PSS_peak_kib=measure['sampled_tree_PSS_peak_kib'],
    missing_memory_observations=measure['missing_memory_observations'],observer_CPU_seconds=measure['observer_CPU_seconds'],sample_interval_seconds=measure['sample_interval_seconds'],
    stages=stages,route_body_sha256=route_body(run_dir(final)/'routed.route'),backend=flow['backend'],
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'config.json',root/'measurement/completion.json',root/'flow/completion.json',repair/'completion.json',initial/'completion.json',final/'completion.json',root/'queue/registration.json']},
    qualification='One actual fresh-process serial configuration on eltwise, graph indexes either built within the command or explicitly supplied as graph-only preprocessing, according to cache_mode, no imported route or external native/query result reuse. Explicit config seed order and optional domain failure release; one current Census binary for initial routing, native repair and actual installed-candidate FULL/fresh STA. Independent empty source serialization controls are algorithm work inside the measured command. Legacy human-readable strong_A0_fast labels in transaction records do not identify the input; the bound config and actual initial-state path do. Concurrent research/shared host and uncontrolled OS cache prevent an exclusive speedup or cold-storage claim. Packing/placement generation is upstream. Quality and full time/memory belong to this exact output; not transferable to other backends or outputs. Sampled tree RSS/PSS may miss transient peaks and include the explicitly reported missing-memory observation count.')
write(root/'completion.json',payload)
write(root/'queue/completion.json',dict(passed=True,completion=str(root/'completion.json'),source_sha256={str(root/'completion.json'):sha(root/'completion.json')}))
write(root/'queue/status.json',dict(status='terminal',passed=True))
print({k:payload[k] for k in ['passed','CPD_ns','resources','complete_wall_seconds','accepted_steps','attempted_scopes']},flush=True)
