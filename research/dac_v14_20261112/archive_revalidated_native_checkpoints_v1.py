"""Preserve independently sealed LOAD observations without closing old actors."""
import copy, csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from pareto_archive_dimensions import annotate

parent = D/'multiobjective_SB_fixed_budget_01'
out = D/'multiobjective_revalidated_native_checkpoints_01'
assert not out.exists()
pc = read(parent/'completion.json')
assert pc['passed'] and all(sha(parent/n) == h for n, h in pc['artifact_sha256'].items())
replay_path = D/'native_checkpoint_adapter_v2_replay_01/completion.json'
replay = read(replay_path)
assert replay['passed']
points = read(parent/'points.json')
origin = next(p for p in points if p['id'] == 'native_extra_opportunity_bnn_01/runs/R1')
files = [Path(__file__).resolve(), parent/'completion.json', parent/'points.json', replay_path,
         D/'pareto_archive_dimensions.py']
hashed = {}
def checked(p):
    p = str(Path(p).resolve())
    if p not in hashed:
        hashed[p] = sha(p)
    return hashed[p]
for p, h in replay['source_sha256'].items():
    assert checked(p) == h, p
added, summaries = [], []
for name, item in replay['roles'].items():
    failed = D/'native_checkpoint_recovery_01'/name
    pool = read(failed/'pool/completion.json')
    context = read(failed/'evaluation_context/completion.json')
    seal = read(failed/'evaluation_context/input_seal.json')
    assert pool['passed'] and context['passed'] and seal['passed']
    for receipt in [pool, context, seal]:
        assert all(checked(p) == h for p, h in receipt['source_sha256'].items())
    pending = item['pending_candidate']
    for kind, state in [('checkpoint', failed/'initial'), ('pending_candidate', Path(pending['evaluation']))]:
        closed = read(state/'completion.json')
        assert closed['passed'] and closed['requires_final_input_seal'] == str(failed/'evaluation_context/input_seal.json')
        assurance = require_publication_proof(state)
        rd = run_dir(state)
        m = read(rd/'manifest.json')
        assert m['metrics']['native_full_check_passed']
        assert all(checked(rd/n) == m['outputs'][n]['sha256'] for n in ['packed.net', 'placed.place', 'routed.route'])
        cmd = m['command']
        actual_identity = dict(architecture=checked(cmd[1]), graph=checked(cmd[cmd.index('--read_rr_graph')+1]),
            netlist=checked(cmd[2]), packed=checked(rd/'packed.net'), placed=checked(rd/'placed.place'),
            clock_modeling=cmd[cmd.index('--clock_modeling')+1],
            sdc='native_generated_default_from_bound_netlist', seed=cmd[cmd.index('--seed')+1])
        assert '--sdc_file' not in cmd and actual_identity == origin['physical_identity']
        metrics = assurance['physical_metrics']
        vector = read(state/'endpoint_vector.json')
        ident = str(rd.relative_to(D))
        assert not any(p['id'] == ident for p in points)
        row = {k: copy.deepcopy(origin[k]) for k in ['circuit', 'physical_identity', 'quality_cohort', 'initial_routing_convergence']}
        row.update(id=ident, arm=name+'_revalidated_'+kind, batch=name,
            batch_full_path=str(failed), state=str(state), source_state=None,
            status='legal', record_kind='sealed_revalidated_'+kind+'_of_unclosed_native_actor',
            actor_final_selected=False, actor_terminal_claim=False, transition_committed=False,
            historical_accepted_checkpoint_steps=item['checkpoint_steps'],
            policy_accepted_if_resumed=pending['accepted'] if kind == 'pending_candidate' else None,
            run_manifest=str(rd/'manifest.json'), binary_sha256=checked(cmd[0]), final_STA_binary_sha256=checked(cmd[0]),
            route_sha256=checked(rd/'routed.route'), route_body_sha256=route_body(rd/'routed.route'),
            command=cmd, environment=m.get('environment'),
            CPD_ns=vector['cpd_s']*1e9, CPD_interval_ns=[vector['cpd_s']*1e9]*2,
            CPD_precision='Exact current sealed native LOAD endpoint vector',
            wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'], SB_pairs=metrics['sb_pairs_used'],
            CB_sources=metrics['cb_crossing_output_sources_used'], SB_net_occupancy=metrics['sb_pair_net_occupancy'],
            CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],
            convergence='interrupted_native_menu_awaits_registered_recovery',
            opportunity='Actual original native-only checkpoint or already executed pending candidate revalidated by a separate sealed LOAD/context; no completed native menu or new search.',
            complete_single_configuration_seconds=None, timing_cohort=None,
            new_native_calls_for_archival=0, full_native_trajectory_cost=None,
            actual_revalidation_observation_timing=closed['timing'],
            audit_provenance=assurance['evidence'], resource_assurance_kind=assurance['assurance_kind'],
            independent_physical_audit_reused_for_exact_route=closed['physical_audit_reused'],
            new_independent_physical_audit_executed=not closed['physical_audit_reused'],
            actual_revalidation_context_seal=str(failed/'evaluation_context/input_seal.json'),
            original_interrupted_pool_seal_fabricated=False,
            original_controller_terminal_passed=False, verification=str(replay_path))
        if kind == 'pending_candidate':
            row.update(acceptance=pending['decision'], source_state=str(failed/'initial'))
        points.append(row)
        added.append(ident)
        summaries.append(dict(arm=row['arm'], state=str(state), CPD_ns=row['CPD_ns'],
            resources={k: row[k] for k in ['wirelength', 'SB_pairs', 'CB_sources']},
            kind=kind, policy_accepted_if_resumed=row['policy_accepted_if_resumed'],
            transition_committed=False, native_menu_terminal=False,
            physical_audit_reused=closed['physical_audit_reused']))
        files += [state/'completion.json', state/'endpoint_vector.json', rd/'manifest.json',
                  rd/'routed.route', Path(assurance['evidence'])]
    files += [failed/'pool/completion.json', failed/'evaluation_context/completion.json', failed/'evaluation_context/input_seal.json']
annotate(points)
for s in summaries:
    row = next(p for p in points if p['state'] == s['state'])
    s['quality_status'] = row['quality_status']
out.mkdir()
write(out/'points.json', points)
write(out/'checkpoint_and_pending_summary.json', dict(passed=True, observations=summaries,
    qualification='Actual sealed checkpoint/pending LOAD observations, not completed native trajectories or new independent samples. Fresh native FULL/STA and successful independent context seals come from controller01 despite its later list/tuple comparison assertion. Physical audits reused for exact checkpoint bytes are labeled; pending LOAD physical audits actually executed. Replay02 creates no new search/LOAD or actor commit and changes no numerical tolerance. Interrupted original pool seals and full costs remain unknown.'))
fields = ['id', 'arm', 'circuit', 'CPD_ns', 'wirelength', 'SB_pairs', 'CB_sources', 'quality_status',
          'record_kind', 'actor_final_selected', 'actor_terminal_claim', 'complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows({k: p.get(k) for k in fields} for p in points)
write(out/'completion.json', dict(passed=True, records=len(points), parent=str(parent), added=added,
    native_calls=0, source_sha256={str(f): checked(f) for f in files},
    artifact_sha256={n: sha(out/n) for n in ['points.json', 'points.csv', 'checkpoint_and_pending_summary.json']}))
print(dict(passed=True, records=len(points), observations=summaries), flush=True)
