"""Check a single-net local minimum against an actual global cut-attaining route."""
import json, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace

start = time.monotonic()
global_path = D/'BNN_vertical_cut_bound_01/completion.json'
local_path = D/'R1_local_escape_owner_diagnostic_01/completion.json'
excess_path = D/'R1_last_vertical_excess_diagnostic_01/completion.json'
global_cut, local, excess = [read(p) for p in [global_path, local_path, excess_path]]
assert all(p['passed'] for p in [global_cut, local, excess])
assert local['state'] == excess['state']
assert local['single_net_crossing_reduction_impossible_with_other_routes_frozen']
assert local['minimum_distinct_crossing_resources_for_net_with_other_routes_frozen'] == 2
state = Path(local['state'])
run = run_dir(state)
reference_path = D/'BNN_vertical_cut_bound_01/fixed_terminals_and_crossings.jsonl'
reference = {r['net']: r for r in map(json.loads, reference_path.open())}
seen, mismatches, positive_excess = set(), [], []
current_sum = mandatory_sum = 0
for row in stream_trace(run/'routed.route'):
    trace = row['trace']
    if not trace:
        continue
    net = row['net']
    assert net not in seen and net in reference
    seen.add(net)
    endpoints = sorted({(p.pin, p.inode) for p in trace if p.kind == 'SINK'})
    ref = reference[net]
    source_equal = trace[0].inode == ref['source']
    sinks_equal = endpoints == sorted(map(tuple, ref['sinks']))
    if not source_equal or not sinks_equal:
        mismatches.append(dict(net=net, SOURCE_exact=source_equal, SINK_mapping_exact=sinks_equal))
    need = int(len({trace[0].low[2]} | {p.low[2] for p in trace if p.kind == 'SINK'}) > 1)
    assert need == ref['required_crossings']
    cb, sb = set(), set()
    for a, b in zip(trace, trace[1:]):
        if a.switch != -1 and a.low[2] != b.low[2]:
            if a.kind == 'OPIN':
                cb.add(a.inode)
            else:
                sb.add(tuple(sorted([a.inode, b.inode])))
    actual = len(cb)+len(sb)
    assert actual >= need
    current_sum += actual
    mandatory_sum += need
    if actual > need:
        positive_excess.append(dict(net=net, actual=actual, minimum_from_terminal_layers=need))
assert seen == reference.keys()
assert current_sum == 5104 and mandatory_sum == global_cut['SB_plus_CB_lower_bound'] == 5103
assert positive_excess == [dict(net=31767, actual=2, minimum_from_terminal_layers=1)]
out = D/'R1_single_net_vertical_local_minimum_01'
out.mkdir(exist_ok=False)
write(out/'RR_terminal_mapping_differences.json', mismatches)
files = [Path(__file__).resolve(), global_path, local_path, excess_path, reference_path,
         state/'completion.json', run/'manifest.json', run/'routed.route', run/'independent_audit.json']
write(out/'completion.json', dict(passed=True, native_calls_new=0, counted_nets=len(seen),
    current_total_vertical_resources=current_sum, terminal_layer_lower_bound=mandatory_sum,
    exact_SOURCE_SINK_RR_mapping_matches_cut_attaining_reference=not mismatches,
    mapping_mismatches=len(mismatches), unique_positive_excess_net=31767,
    single_net_total_vertical_improvement_impossible_at_current_state=True,
    same_fixed_RR_terminal_problem_has_observed_lower_total_vertical_resources=not mismatches,
    source_sha256={str(f): sha(f) for f in files},
    artifact_sha256={'RR_terminal_mapping_differences.json': sha(out/'RR_terminal_mapping_differences.json')},
    complete_read_only_seconds=time.monotonic()-start,
    qualification='Every other counted net already attains its own terminal-layer crossing lower bound. The unique excess net attains its capacity-conditioned2resource minimum with all other routes frozen. Therefore no single-net reroute can strictly reduce total occupied SB+CB while preserving current terminal mapping and all other routes. Exact RR SOURCE/SINK comparison determines whether the observed5103resource reference is a global counterexample for the same fixed-terminal problem; a mapping mismatch would bar that stronger claim. This is not a proof of CPD/wire optimality, global Pareto optimality, or existence of a joint move within original separate SB/CB envelopes. Read-only certificate cost, not measured repair speedup.'))
print(dict(passed=True, counted_nets=len(seen), mapping_mismatches=len(mismatches),
           single_net_local_minimum=5104, actual_reference_total=5103), flush=True)
