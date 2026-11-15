"""Preserve both rejected whole-net alternatives and reproduced seed roots."""
import copy, csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate

parent = D / 'multiobjective_seed19_complete_01'
out = D / 'multiobjective_R1_whole_net_probe_01'
assert not out.exists()
pc = read(parent / 'completion.json')
assert pc['passed'] and all(sha(parent / n) == h for n, h in pc['artifact_sha256'].items())
proof_path = D / 'R1_whole_net_residual_probe_01/verification.json'
proof = read(proof_path)
assert proof['passed'] and all(sha(p) == h for p, h in proof['source_sha256'].items())
seed_path = D / 'complete_serial_seed_transfer_01/comparison.json'
seed = read(seed_path)
assert seed['passed'] and all(sha(p) == h for p, h in seed['source_sha256'].items())
points = read(parent / 'points.json')
origin = next(p for p in points if p.get('state') == proof['source_state'])
files = [Path(__file__).resolve(), parent / 'completion.json', parent / 'points.json',
         proof_path, seed_path, D / 'pareto_archive_dimensions.py']
for p in points:
    if p.get('batch_full_path', '').startswith(str(D / 'complete_serial_seed_transfer_01') + '/'):
        role = Path(p['batch_full_path']).name
        s = seed['results'][role]
        assert s['same_initial_state_as_seed11'] and s['trajectory_exact_when_root_reproduced']
        p.update(root_independence='reproduces_seed11_exact_initial_and_complete_actual_trajectory',
                 root_independence_evidence=str(seed_path), independent_circuit_sample_added=False,
                 initial_router_seed=19, reference_router_seed=11)
added = []
for name, r in proof['roles'].items():
    state = Path(r['state'])
    rd = run_dir(state)
    m = read(rd / 'manifest.json')
    assert m['metrics']['native_full_check_passed']
    metrics = read(rd / 'independent_audit.json')['physical_metrics']
    ident = str(rd.relative_to(D))
    assert not any(p['id'] == ident for p in points)
    row = {k: copy.deepcopy(origin[k]) for k in ['circuit', 'physical_identity', 'quality_cohort', 'initial_routing_convergence']}
    row.update(id=ident, arm='R1_whole_net_' + name, batch='R1_whole_net_residual_probe_01',
               batch_full_path=str(D / 'R1_whole_net_residual_probe_01'), state=str(state),
               source_state=proof['source_state'], status='legal',
               record_kind='sealed_legal_rejected_whole_net_development_candidate',
               actor_final_selected=False, actor_terminal_claim=False, transition_committed=False,
               policy_accepted=False, actual_transition_policy='resources_under_timing_SB_CB_only',
               run_manifest=str(rd / 'manifest.json'), binary_sha256=sha(m['command'][0]),
               final_STA_binary_sha256=sha(m['command'][0]), route_sha256=sha(rd / 'routed.route'),
               route_body_sha256=read(state / 'completion.json')['route_body_sha256'],
               command=m['command'], environment=m.get('environment'),
               convergence='completed_two_role_whole_net_development_probe',
               opportunity='Same actual completed R1 source; all four sinks of the unique excess net rebuilt. Two query orders; old one-pin controls reused only as scientific references. Original vertical-only policy unchanged.',
               CPD_ns=r['CPD_ns'], CPD_interval_ns=[r['CPD_ns']] * 2,
               CPD_precision='Full-precision native endpoint vector', **r['resources'],
               SB_net_occupancy=metrics['sb_pair_net_occupancy'], CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],
               complete_single_configuration_seconds=None, timing_cohort=None,
               shared_imported_probe_seconds=proof['complete_shared_imported_scope_seconds'],
               native_core_seconds=r['native_core_seconds'], query_order=r['query_order'],
               cost_scope='Shared two-role imported scope including source serialization/checks, not per-arm standalone or complete algorithm cost.',
               audit_provenance=str(rd / 'independent_audit.json'), verification=str(proof_path),
               full_endpoint_vector_unchanged=r['vector_exact'], acceptance=r['decisions'])
    assert not r['decisions']['resources_under_timing']['accepted']
    points.append(row)
    added.append(ident)
    files += [state / 'completion.json', state / 'endpoint_vector.json', rd / 'manifest.json', rd / 'independent_audit.json']
annotate(points)
out.mkdir()
write(out / 'points.json', points)
write(out / 'probe_and_root_summary.json', dict(passed=True, probe=proof, seed_repetition=seed,
      qualification='Every legal rejected whole-net result and prior observation retained; original actor final remains historically selected but may now be quality dominated. Reproduced seed19 roots explicitly add no independent samples. No missing complete cost filled from shared component time.'))
fields = ['id', 'arm', 'circuit', 'CPD_ns', 'wirelength', 'SB_pairs', 'CB_sources',
          'quality_status', 'candidate_retention', 'record_kind', 'actor_final_selected', 'complete_single_configuration_seconds']
with (out / 'points.csv').open('w') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows({k: p.get(k) for k in fields} for p in points)
write(out / 'completion.json', dict(passed=True, records=len(points), parent=str(parent), added=added,
      native_calls=0, source_sha256={str(f): sha(f) for f in files},
      artifact_sha256={n: sha(out / n) for n in ['points.json', 'points.csv', 'probe_and_root_summary.json']}))
print(dict(passed=True, records=len(points), added=2, new_independent_roots=0), flush=True)
