"""Integrate actual composition and release-ablation outcomes, keeping cost scopes explicit."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
parent_path = D / 'routing_position_paper_binding_05.json'
parent = read(parent_path)
old = (p / 'current_repair_main.tex').read_text()
assert old == (Path(parent['snapshot']) / 'current_repair_main.tex').read_text()
root = D / 'native_ablation_paper_evidence_06'
root.mkdir(exist_ok=False)
composition_path = D / 'BNN_wire_timing_native_validation_01/verification.json'
release_path = D / 'robot_domain_release_ablation_01/verification.json'
c = read(composition_path)
r = read(release_path)
o = c['outcome']
assert c['passed'] and o['status'] == 'legal_evaluated' and o['policy_accepted']
assert o['structural_counts_match_actual'] and o['all_34_predicted_connection_delays_exact']
assert o['resources'] == dict(wirelength=2059607, SB_pairs=82, CB_sources=5062)
assert r['passed'] and r['actual_status'] == 'transaction_failed_rolled_back'
assert r['matched_source_request_cuts_weights_binary_and_seed'] and r['only_domain_failure_release_flag_changed']
assert r['all_original_source_bytes_and_full_vector_restored'] and r['no_domain_release_executed']
assert len(r['actual_queries']) == 1 and len(r['actual_attempts']) == 9
assert c['complete_single_configuration_seconds'] is None and not c['committed_to_original_actor']
assert not r['committed_to_original_actor']

new = old.replace('Unified complete-result table.', 'Unified results: complete configurations and scoped ablations.')
new = new.replace('$^{*}$Original GNU-time, 1-s precision; observer lost, brief overlap, no complete PSS.',
    '$^{*}$Original GNU-time, 1-s precision; observer lost, brief overlap, no complete PSS. '
    '$^{\\dagger}$Fixed imported-scope cost only; comparison starts at that component\'s source, not initial routing.')
anchor = 'Softmax lazy+snapshot D&8.975747&169486/3/713&256.54&2.456&29/0/0\\\\\\hline'
assert anchor in new
component_rows = [
    dict(label='BNN composite', status='legal_evaluated', CPD_ns=o['CPD_ns'], resources=o['resources'],
        time_seconds=c['actual_imported_candidate_evaluation_seconds'], PSS_GiB=c['actual_sampled_tree_PSS_peak_kib']/1024**2,
        setup_improved=2, setup_regressed=0, increased_hold_violations=0, scope='fixed_imported_candidate_LOAD', receipt=str(composition_path)),
    dict(label='Robot no-release', status=r['actual_status'], quality=None, time_seconds=r['complete_workflow_seconds'],
        PSS_GiB=None, scope='fixed_imported_transaction', receipt=str(release_path))]
rows = ('\n\\multicolumn{6}{l}{Fixed imported-scope components (not complete configurations)}\\\\\n'
    f"BNN composite$^{{\\dagger}}$&{o['CPD_ns']:.6f}&2059607/82/5062&{component_rows[0]['time_seconds']:.2f}&{component_rows[0]['PSS_GiB']:.3f}&2/0/0\\\\\n"
    f"Robot no-release$^{{\\dagger}}$ (rollback)&--&--&{r['complete_workflow_seconds']:.2f}&--&--\\\\\\hline")
new = new.replace(anchor, anchor + rows)
new = new.replace('Table~\\ref{tab:completecost} binds each complete time to its own final route.',
    'The first 22 rows of Table~\\ref{tab:completecost} bind complete times to their own outputs; the last two are fixed-scope components.')
new = new.replace('Other rows are complete resource-repair configurations;',
    'The other full-flow rows are complete resource-repair configurations;')
prefix = next(x for x in old.splitlines() if x.startswith('Separate BNN resource prefixes'))
group = next(x for x in old.splitlines() if x.startswith('A 64-connection budget reduces'))
new = new.replace(prefix, 'Resource-prefix combinations also expose wire/vertical tradeoffs, but exclude upstream routing and preparation costs; those local trajectories remain in the supplement.')
pending = 'A separately constructed BNN 2059607-wire composition remains pending its own native LOAD/FULL/STA; its structural prediction is not yet a legal measured quality point.'
assert pending in new
new = new.replace(pending, 'A preregistered three-net composition now passes native FULL/STA and independent physical checks: 2059607 wire,82 SB,5062 CB at 13.228145690 ns, saving 24 wire from its source. Two setup components improve without regression; all 34 predicted connection delays match exactly. Its 217.95 s is imported-candidate validation, not a complete flow or an independent input.')
pending_release = 'The same-source release-only ablation remains queued, so native ablation outcomes and owner-scope gains on robot are not claimed.'
assert pending_release in new
new = new.replace(pending_release, 'Disabling only release in the same 23-connection transaction fails on its first connection after nine attempts; source bytes and the full endpoint vector are restored exactly. This native ablation supports release as an operational enabler. The separate cut audit establishes the conditional obstruction; owner-scope gains remain pending.')
new = new.replace(group, 'Batch grouping is not a reliable cost proxy. K 8 and budget64 execute the same 2722-query multiset in 18 versus 32 transactions, taking 7099.32/10568.53 s. A completed factor-two proposed-query heuristic takes 10308.49 s at the same CPD/SB/CB as K 8. These historical imported observations do not show a cost benefit or statistical speedup; detailed trajectories remain in the supplement.')
new = new.replace('The 671-record archive includes', 'The 671-record historical archive includes')
new = new.replace('Initial failures remain outside legal-quality counts and inside cohort denominators.',
    'The two new scoped table rows are outside those archive counts; failed transactions have no candidate quality. Initial failures remain inside cohort denominators.')
source = p / 'current_repair_native_ablation_06.tex'
assert not source.exists()
source.write_text(new)
(root / 'moved_local_detail.tex').write_text('% Previous main paragraphs retained verbatim.\n' + prefix + '\n\n' + group + '\n')
write(root / 'scoped_component_rows.json', component_rows)
files = [Path(__file__).resolve(), parent_path, source, composition_path, release_path,
    D/'BNN_wire_timing_native_validation_01/plan.json', D/'BNN_wire_timing_native_validation_01/actual_prediction_checks.json',
    D/'BNN_wire_timing_native_validation_01/measurement/completion.json', D/'BNN_wire_timing_native_validation_01/candidate_evaluation/completion.json',
    D/'robot_domain_release_ablation_01/plan.json', D/'robot_domain_release_ablation_01/transaction/completion.json',
    D/'unexecuted_recovery_20261115_01/queue/BNN_execution_receipt.json', D/'unexecuted_recovery_20261115_01/queue/robot_execution_receipt.json',
    D/'query_reduction_resource_dev_01/bnn_A0_paired/completion.json', D/'stable_seed_transfer_dev_01/bnn_A0_paired/completion.json',
    root/'scoped_component_rows.json', root/'moved_local_detail.tex']
write(root / 'edit_registration.json', dict(parent=str(parent_path), source=str(source), source_sha256={str(f):sha(f) for f in files},
    actual_new_native_experiments=2, new_independent_inputs=0, complete_configuration_rows=22, scoped_component_rows=2,
    qualification='Actual native composition legality and single-flag robot rollback, not whole-method universal benefits. '
        'One legal imported candidate and one failed transaction remain separate from the historical671-record archive. '
        'No old complete time is attached to the composed candidate. Existing full-flow measurements and9references retained.'))
print(dict(source=str(source), component_rows=2, complete_rows=22))
