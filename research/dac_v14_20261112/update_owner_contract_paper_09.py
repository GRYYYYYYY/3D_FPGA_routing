"""Integrate owner tradeoff, invalid-input denominators and the fixed CP1 source."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';parent_path=D/'qualified_complete_paper_binding_08.json';parent=read(parent_path)
old=(p/'current_repair_main.tex').read_text();assert old==(Path(parent['snapshot'])/'current_repair_main.tex').read_text()
e=D/'owner_contract_paper_evidence_09';e.mkdir(exist_ok=False)
owner_path=D/'robot_owner_scope_pair_01/verification.json';owner=read(owner_path)
assert owner['passed'] and owner['new_independent_physical_inputs']==0
a,b=[owner['outcomes'][k] for k in ['target_only','target_plus_owner']]
assert all(x['status']=='legal_evaluated' and not x['committed_to_original_actor'] for x in [a,b])
assert all(not x['resource_policy_decision']['accepted'] for x in [a,b])
assert not a['all_policies']['endpoint_vector']['accepted'] and b['all_policies']['endpoint_vector']['accepted']
paired=owner['paired_comparison']
assert paired['CPD_delta_ns']==0 and paired['resource_deltas']==dict(wirelength=12,SB_pairs=0,CB_sources=1)
delta=paired['endpoint_comparison'];assert delta['setup_improved']==31 and delta['setup_regressed']==delta['hold_violation_regressions']==0
assert read(D/'confirmation_release_cp1_01/completion.json')['passed']
assert read(D/'confirmation_release_cp1_01/archive_relocation.json')['passed']
files=[Path(__file__).resolve(),parent_path,owner_path,D/'robot_owner_scope_pair_01/plan.json',
       D/'confirmation_release_cp1_01/completion.json',D/'confirmation_release_cp1_01/archive_relocation.json',D/'confirmation_release_cp1_01/contract.json']
failures=[]
for name,label,oldname in [('clstm_input_contract_pair_02','CLSTM','portable_clstm_pair_01'),('robot_p1_input_contract_pair_02','Robot p1','portable_robot_p1_pair_01')]:
    proof_path=D/name/'failure_reclassification.json';proof=read(proof_path);assert proof['passed']
    comparison=read(D/oldname/'comparison.json');files += [proof_path,D/oldname/'comparison.json']
    for arm in ['native','domain']:
        row=proof['roles'][arm];assert row['corrected_status']=='input_netlist_compatibility_failed' and not row['routing_started'] and row['quality'] is None
        measurement_path=Path(comparison['results'][arm]['measurement']);m=read(measurement_path)
        assert m['complete_command_wall_seconds']==row['complete_seconds'] and not m['live_descendants_after_command_exit']
        failures.append(dict(label=label+' '+arm[0].upper()+' (load fail)',quality=None,CPD_ns=None,resources=None,
            time_seconds=row['complete_seconds'],PSS_GiB=m['sampled_tree_PSS_peak_kib']/1048576,
            missing_memory_observations=m['missing_memory_observations'],endpoint_summary=None,
            status=row['corrected_status'],routing_started=False,receipt=str(proof_path),measurement=str(measurement_path)))
        files.append(measurement_path)
new=old
def replace(a,b):
    global new
    assert new.count(a)==1,a
    new=new.replace(a,b)
replace('\\textbf{Controller contract (integration target)}','\\textbf{CP1 fixed controller contract}')
replace('The resource--timing pipeline and individual owner/release controls have actual executions; their fully integrated automatic confirmation controller is not yet frozen.',
    'CP1 fixes executable source, input interpretation and these rules. Independent complete confirmation and positive integrated branch coverage remain pending.')
start='The general selection hypothesis uses crossing redundancy'
paragraph=next(s for s in new.splitlines() if s.startswith(start))
replace(paragraph,'Crossing redundancy enables sharing; capacity obstruction justifies an owner proposal; current slack screens complete cuts. Failed search triggers local release, not global infeasibility. Scoped owner effects differ: R1 reduces vertical counts, while robot below trades extra resources for endpoint gains. CP1 now freezes the independently packaged core and input contract. Outside-project observation, a known R1 owner transaction and an existing tiny whole flow pass; positive automatic owner reentry, positive integrated timing feedback and independent confirmation remain unverified. Existing development runs are not retroactively confirmation.')
replace("not initial routing.}","not initial routing. $^{\\ddagger}$Owner-minus-target deltas; time/PSS cover the shared imported pair.}")
anchor='\\multicolumn{6}{l}{Fixed imported-scope components (not complete configurations)}\\\\'
extra='\n'.join(f"{r['label']}&--&--&{r['time_seconds']:.2f}&{r['PSS_GiB']:.3f}&--\\\\" for r in failures)
replace(anchor,extra+'\\hline\n'+anchor)
composition_row=next(s for s in new.splitlines() if s.startswith('BNN composite$'))
replace(composition_row,'')
line=next(s for s in new.splitlines() if s.startswith('Robot no-release$'))
replacement=line.replace('\\\\\\hline','\\\\')+'\n'+f"Robot owner $\\Delta^{{\\ddagger}}$&0&+12/0/+1&{owner['complete_imported_pair_seconds']:.2f}&{owner['measurement']['sampled_tree_PSS_peak_kib']/1048576:.3f}&31/0/0\\\\\\hline"
replace(line,replacement)
replace('The first 27 rows of Table~\\ref{tab:completecost} report complete attempts, including four initial failures; the last two are scoped components.',
    'The first 31 rows of Table~\\ref{tab:completecost} retain complete attempts, including four routing and four input-loading failures. The last two rows are scoped components; the owner row reports paired deltas and shared cost.')
replace('The separate cut audit establishes the conditional obstruction; owner-scope gains remain pending.',
    'The cut audit establishes the conditional obstruction; the matched owner test below separates coordination.')
old_owner=next(s for s in new.splitlines() if s.startswith('A two-connection alternative spends'))
replace(old_owner,'In a same-source robot contrast, both searches are unrestricted with release disabled. Target-only yields 251173 wire,10 SB,653 CB; adding one owner yields 251185,10,654 at equal 13.354624073 ns. The added scope improves 31 setup components without regression but spends 12 wire/one CB. Endpoint acceptance permits it; fixed-resource acceptance rejects both, and neither is committed. The shared imported pair costs 155.10 s, not a cold flow. A capacity witness therefore motivates a proposal, not a resource-saving guarantee; smaller R1 alternatives remain in the supplement.')
replace('The five new complete attempts and two scoped rows are outside those historical counts.',
    'The nine new complete attempts and two scoped rows are outside those historical counts.')
anchor='Applicable graphs here are two-layer edge-encoded Hybrid-O, SB-only and CB-only.'
replace(anchor,'CLSTM and robot-p1 each fail both roles while loading packing, before routing: an input template omitted the historical constant-net interpretation flag, producing an unknown-net error. These are input-compatibility failures, not congestion or repair failures. CP1 binds that interpretation and rejects mismatched commands; corrected development executions remain queued.\n\n'+anchor)
paragraph=next(s for s in new.splitlines() if s.startswith('The next confirmation artifact must be independently executable'))
replace(paragraph,'CP1 fixes source/dependency and phase-binary hashes, mechanism triggers, candidate order, root envelopes and terminal policy. Its native arm has matching selection, owner and convergence opportunities. Future input cohorts must bind their configuration before outcomes; changes require a new release. Paired domain/release treatment does not isolate its two mechanisms.')
source=p/'current_repair_owner_contract_09.tex';assert not source.exists();source.write_text(new)
write(e/'input_failure_rows.json',failures)
no_release=next(r for r in read(Path(parent['snapshot'])/'data/scoped_component_rows.json') if r['label']=='Robot no-release')
scope=dict(label='Robot owner delta',CPD_delta_ns=0,resources_delta=paired['resource_deltas'],endpoint_reference='target_plus_owner minus target_only',
    setup_improved=31,setup_regressed=0,hold_violation_regressions=0,
    shared_imported_pair_seconds=owner['complete_imported_pair_seconds'],PSS_GiB=owner['measurement']['sampled_tree_PSS_peak_kib']/1048576,
    not_per_candidate_cost=True,receipt=str(owner_path))
write(e/'scoped_component_rows.json',[no_release,scope])
write(e/'moved_composition_row.json',dict(row=composition_row,prior_scoped_rows=str(Path(parent['snapshot'])/'data/scoped_component_rows.json'),qualification='The fixed BNN composition remains in prose and supplementary receipts; its complete terminal flow remains in the main table.'))
files += [source,e/'input_failure_rows.json',e/'scoped_component_rows.json']
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    complete_attempt_rows=31,scoped_component_rows=2,initial_routing_failure_rows=4,input_loading_failure_rows=4,
    new_native_calls=0,source_sha256={str(f):sha(f) for f in files},
    qualification='Actual owner-scope tradeoff, separate invalid-input denominator, and fixed prospective CP1 source. No independent confirmation outcomes or full positive-path claim.31complete attempts include8failures; shared owner pair cost is not assigned to either candidate.'))
print(dict(source=str(source),complete_attempt_rows=31,scoped_rows=2,new_native_calls=0))
