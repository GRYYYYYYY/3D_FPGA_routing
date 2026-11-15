"""Verify fresh complete transfer flows with legal rejects and real rollbacks."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from multiobjective_acceptance_v2 import decide

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
a = p.parse_args()
root = a.root.resolve()
structural = read(root / 'completion.json')
assert structural['passed'] and structural['complete_configuration_verified']
assert all(sha(f) == h for f, h in structural['source_sha256'].items())
config, flow = read(root / 'config.json'), read(root / 'flow/completion.json')
actor = root / 'flow/repair'
reg = read(actor / 'registration.json')
assert config['seed_order'] == reg['seed_order'] == 'delay_rr_id'
assert config['domain_feedback'] == reg['domain_feedback'] == (config['domain_mode'] == 'paired')
assert reg['local_probe'] == dict(accepted_steps=0, rank_windows=3)
assert not reg['reuse_native_batches']
assert reg['resource_limits']['wirelength'] == (reg['anchor']['wirelength']*1001+999)//1000
assert all(reg['resource_limits'][k] == reg['anchor'][k] for k in ['SB_pairs', 'CB_sources'])
binary = read(D / 'native_resource_census_stage_01/binding.json')['binary_sha256']
files = [Path(__file__).resolve(), root/'completion.json', root/'config.json', root/'flow/completion.json', actor/'registration.json', actor/'attempts.json']
counts = dict(optional_native_skipped=0, native_transactions=0, queries=0, search_attempts=0,
              domain_releases=0, legal_candidates=0, rolled_back_search_failures=0)
def axes(state):
    audit = read(run_dir(state) / 'independent_audit.json')
    assert audit['audit']['passed']
    m = audit['physical_metrics']
    return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'], SB_pairs=m['sb_pairs_used'], CB_sources=m['cb_crossing_output_sources_used'])
current = Path(flow['initial_state'])
assert read(current/'endpoint_vector.json')['cpd_s'] == reg['anchor']['CPD_s']
for attempt in read(actor/'attempts.json'):
    assert Path(attempt['current_state']) == current
    tx = Path(attempt['transaction'])
    roles, progress = read(tx/'registration.json')['roles'], read(tx/'progress.json')
    files += [tx/'registration.json', tx/'completion.json', tx/'progress.json']
    for name, role in roles.items():
        assert role['state'] == str(current)
        assert role['original_budget'] == reg['anchor'] and role['fixed_resource_limits'] == reg['resource_limits']
        assert role['seed_order'] == config['seed_order']
        assert role['domain_failure_release'] == (role['crossing_reuse_enabled'] and config['domain_feedback'])
        row = progress[name]
        if row['status'] == 'not_executed_domain_candidate_accepted':
            assert name == 'reuse_off' and progress['reuse_on']['status'] == 'legal_evaluated'
            assert progress['reuse_on']['policies']['resources_under_timing']['accepted']
            assert not (tx/name).exists() and row['acceptance_evaluated'] is False
            counts['optional_native_skipped'] += 1
            continue
        worker = tx/name
        closed = read(worker/'completion.json')
        assert closed['passed']
        manifest = read(run_dir(worker)/'manifest.json')
        assert sha(manifest['command'][0]) == binary
        env = manifest['environment']
        assert env['VPR_JOINT_NATIVE_SEED_ORDER'] == config['seed_order']
        assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE'] == ('1' if role['domain_failure_release'] else '0')
        before, restored = read(current/'endpoint_vector.json'), read(worker/'endpoint_vector.json')
        assert all(before[k] == restored[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256'])
        assert route_body(run_dir(worker)/'routed.route') == route_body(run_dir(current)/'routed.route')
        audit = read(tx/(name+'_audit/analysis.json'))
        assert audit['passed']
        counts['native_transactions'] += 1
        counts['queries'] += len(audit['queries'])
        counts['search_attempts'] += len(audit['attempts'])
        domain = read(tx/(name+'_domain_audit.json'))
        assert domain['passed']
        counts['domain_releases'] += len(domain.get('released_queries', []))
        if row['status'] == 'transaction_failed_rolled_back':
            assert not audit.get('candidate_route') and not row['accepted']
            counts['rolled_back_search_failures'] += 1
        else:
            assert row['status'] == 'legal_evaluated' and not row['native_reused']
            state = Path(row['evaluation'])
            c = read(state/'completion.json')
            m = read(run_dir(state)/'manifest.json')
            assert c['passed'] and m['metrics']['native_full_check_passed'] and sha(m['command'][0]) == binary
            after, resource = read(state/'endpoint_vector.json'), axes(state)
            assert resource == row['resources'] and after['cpd_s'] == row['cpd_s']
            expected = decide('resources_under_timing', before, after, axes(current), resource,
                cpd_limit_s=reg['anchor']['CPD_s'], resource_limits=reg['resource_limits'],
                native_valid=True, transaction_complete=True, resource_objectives=('SB_pairs', 'CB_sources'))
            assert expected == read(tx/(name+'_decisions.json'))['resources_under_timing']
            assert expected['accepted'] == row['policies']['resources_under_timing']['accepted']
            counts['legal_candidates'] += 1
            files += [state/'completion.json', state/'endpoint_vector.json', run_dir(state)/'manifest.json', run_dir(state)/'independent_audit.json', tx/(name+'_decisions.json')]
        files += [worker/'completion.json', worker/'endpoint_vector.json', run_dir(worker)/'manifest.json', tx/(name+'_audit/analysis.json'), tx/(name+'_domain_audit.json')]
    winner = next((n for n in ['reuse_on', 'reuse_off'] if progress.get(n, {}).get('status') == 'legal_evaluated' and progress[n]['policies']['resources_under_timing']['accepted']), None)
    assert attempt.get('accepted_role') == winner
    if winner:
        assert attempt['committed_evaluation'] == progress[winner]['evaluation']
        current = Path(progress[winner]['evaluation'])
assert str(current) == flow['final_state']
payload = dict(structural)
payload.update(seed_order=config['seed_order'], domain_mode=config['domain_mode'], domain_failure_release=config['domain_feedback'],
    one_binary_sha256=binary, actual_native_work=counts, structural_verification=str(root/'completion.json'),
    source_sha256={str(f): sha(f) for f in files},
    qualification='Actual complete fresh-route own-current fixed-policy native/domain configuration. All legal candidates, rejects, native search failures with verified source restoration, and explicit unexecuted OFF controls are counted without invented candidate quality. Every legal resource decision recomputed under immutable original root envelopes; final state follows actual committed successors. One frozen binary routes/repairs/evaluates. Graph indexes/new route/all real searches/checks/rollback are in the actual measured command. Known-circuit prospective policy transfer, not an unseen benchmark claim or statistical speedup; each failed pipeline retains its cost/denominator separately.')
write(root/'explicit_policy_verification.json', payload)
print({k: payload[k] for k in ['passed', 'CPD_ns', 'resources', 'complete_wall_seconds', 'actual_native_work']}, flush=True)
