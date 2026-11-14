#!/usr/bin/env python3
"""Seal completed eltwise actors without publishing pending BNN/cohort results."""
import time
import shutil
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import process_identity

b = D / 'uniform_feedback_resource_dev_01'
rows = {}
files = [Path(__file__).resolve(), b / 'queue/registration.json']
for arm in ['native_only', 'feedback']:
    actor = b / ('eltwise_A0_' + arm + '_K8')
    c = read(actor / 'completion.json')
    assert c['passed'] and all(sha(p) == h for p, h in c['source_sha256'].items())
    assert read(actor / 'evaluation_context/input_seal.json')['passed'] and read(actor / 'pool/completion.json')['passed']
    domain_rows = [read(f) for f in sorted(actor.glob('round_*/candidate_*/reuse_on_domain_audit.json'))]
    rows[arm] = dict(completion=str(actor / 'completion.json'), CPD_ns=c['final_CPD_s'] * 1e9,
        resources=c['final_resources'], accepted_steps=c['accepted_steps'], attempted_scopes=c['attempted_scopes'],
        whole_imported_workflow_seconds=c['complete_imported_algorithm_workflow_seconds'],
        actual_domain_bundle_sizes=[len(x['initial_domain_nets']) for x in domain_rows],
        released_queries=[q for x in domain_rows for q in x['released_queries']])
    files.extend([actor / 'completion.json', actor / 'evaluation_context/input_seal.json', actor / 'pool/completion.json'])
old = read(D / 'resource_schedule_cohort_binding_01.json')['rows']['eltwise_A0_bundle4']['paired']
assert rows['feedback']['CPD_ns'] == old['CPD_ns']
assert rows['feedback']['resources']['wirelength'] == old['resources']['wirelength']
assert rows['feedback']['resources']['CB_sources'] == old['resources']['CB_sources']
assert rows['feedback']['resources']['SB_pairs'] == old['resources']['SB_pairs'] - 1
assert rows['feedback']['released_queries'] == []
out = D / 'uniform_feedback_eltwise_prefix_01.json'
write(out, dict(passed=True, rows=rows, feedback_quality_dominates_old_paired_K4=True,
    delta_from_old_K4=dict(CPD_s=0, wirelength=0, SB_pairs=-1, CB_sources=0),
    feedback_release_triggered=False, native_calls_for_this_binding=0, route_calls_for_this_binding=0,
    source_sha256={str(p): sha(p) for p in [*files, D / 'resource_schedule_cohort_binding_01.json']},
    qualification='Two independently sealed own-current actors from a pristine strong native eltwise A0 root. Same K8 cap; actual available domain bundles have6 then3 nets, not fabricated8. Guided domains never failed here, so new gain is not attributed to failure-release. These completed actors do not certify pending BNN actors/cohort, cold runtime or broad confirmation. New complete observations remain preserved pending next archive revision.'))
history = D / 'continuation_history' / ('uniform_eltwise_prefix_' + str(time.time_ns()))
history.mkdir()
phase = read(b / 'queue/status.json')
state = process_identity(phase['pid'])
for name in ['CONTINUATION.json', 'live_handoff.json']:
    path = D / name
    shutil.copy2(path, history / name)
    x = read(path)
    x['latest_uniform_feedback_resource']['completed_eltwise_prefix'] = str(out)
    x['latest_uniform_feedback_resource']['completed_eltwise_quality'] = rows
    x['latest_uniform_feedback_resource']['fresh_phase'] = phase
    x['latest_uniform_feedback_resource']['fresh_phase_live'] = bool(state and state['state'] != 'Z' and state['start_ticks'] == phase['start_ticks'])
    x['next_actions'].insert(0, 'Completed uniform K8 eltwise prefix is independently sealed: native217050/26SB/968CB; paired217214/24SB/965CB, same6.018101128546505ns. Paired quality-dominates old K4 by1SB with wire/CB/CPD equal. No native domain release triggered in this circuit (actual bundles6then3), so do not credit fallback. Preserve pending BNN root trajectories and append all fully sealed observations at next archive revision; no fake new quality point for automatic BNN validation of an already known route.')
    write(path, x)
print(rows, flush=True)
