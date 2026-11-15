"""Verify actual fresh-route measurement entry, with explicit repair coverage."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'fresh_route_entry_preflight_01';reg=read(root/'registration.json')
actual=process_identity(reg['pid'])
assert not actual or actual['state']=='Z' or actual['start_ticks']!=reg['start_ticks']
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
flow=read(root/'flow/completion.json');measure=read(root/'measurement/completion.json')
assert flow['passed'] and measure['passed'] and measure['returncode']==0
assert flow['repair_started'] is False and flow['complete_route_plus_repair_passed'] is False
assert not measure['live_descendants_after_command_exit'] and measure['missing_memory_observations']==0
assert all(sha(p)==h for p,h in flow['source_sha256'].items())
initial=Path(flow['initial_state']);closed=read(initial/'completion.json')
assert closed['passed'] and closed['initial_route_imported'] is False
assert all(sha(p)==h for p,h in closed['source_sha256'].items())
rd=Path(closed['run']);manifest=read(rd/'manifest.json')
assert manifest['metrics']['native_full_check_passed'] and manifest['metrics']['routing_success_reported']
assert '--route' in manifest['command'] and '--analysis' in manifest['command']
assert Path(manifest['command'][manifest['command'].index('--route_file')+1])==rd/'routed.route'
assert all(sha(rd/n)==manifest['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
selection=read(root/'selection/completion.json');assert selection['passed'] and selection['candidate_scopes']==0
assert read(root/'selection/candidates.json')==[]
for cache in ['graph_audit_cache','full_graph_cache']:assert read(root/'flow'/cache/'completion.json')['passed']
files=[Path(__file__).resolve(),root/'registration.json',root/'flow/completion.json',root/'measurement/completion.json',
       root/'selection/completion.json',root/'selection/candidates.json',initial/'completion.json',rd/'manifest.json',rd/'independent_audit.json']
write(root/'completion.json',dict(passed=True,fresh_route_entry_passed=True,complete_route_plus_repair_passed=False,
    route_calls=1,repair_calls=0,eligible_resource_cuts=0,
    complete_entry_wall_seconds=measure['complete_command_wall_seconds'],
    waited_process_RSS_high_water_kib=measure['waited_process_RSS_high_water_kib'],
    sampled_tree_RSS_peak_kib=measure['sampled_tree_RSS_peak_kib'],sampled_tree_PSS_peak_kib=measure['sampled_tree_PSS_peak_kib'],
    sample_interval_seconds=measure['sample_interval_seconds'],observer_CPU_seconds=measure['observer_CPU_seconds'],
    initial_CPD_s=flow['initial_CPD_s'],physical_metrics=audit['physical_metrics'],
    source_sha256={str(p):sha(p) for p in files},
    qualification='Supplemental entry preflight concurrent with existing research pool, not an exclusive cost comparison. Fresh tiny route has zero eligible resource cuts, so even its future full driver run cannot validate nonempty candidate search on this input. Actual route/FULLSTA/physical and sampler interfaces pass. Repair startup/final seals and nonempty eltwise repair still require the queued complete flow; no cost/quality splicing.'))
print(dict(passed=True,fresh_entry_seconds=measure['complete_command_wall_seconds'],eligible_cuts=0,complete_flow_claim=False),flush=True)
