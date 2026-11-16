"""Cross-input mechanism prerequisites and policy counterexamples from sealed metadata.

No graph mapping, route/STA parsing, native calls or remeasurement. These are
retrospective development observations, not new independent confirmation trials.
"""
import csv,hashlib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'mechanism_selection_evidence_01';assert not out.exists();out.mkdir()
binding=D/'cohort_mechanism_paper_binding_15.json';snapshot=Path(read(binding)['snapshot'])
row_paths=[snapshot/'data'/n for n in ['complete_table_rows.json','new_complete_input_rows.json','input_failure_rows.json']]
rows={r['label']:r for p in row_paths for r in read(p)}
pairs=read(D/'complete_tradeoff_paper_evidence_10/paired_complete_deltas.json')
sources=[Path(__file__).resolve(),binding,*row_paths,D/'complete_tradeoff_paper_evidence_10/paired_complete_deltas.json']
def bind(p):
    p=Path(p).resolve();sources.append(p);return sha(p)
def case_of(row):return Path(row['case']) if 'case' in row else Path(row['receipt']).parent
def feature(case):
    flow=case/'flow';actor=flow/'resource_flow/repair' if (flow/'resource_flow/repair').exists() else flow/'repair'
    initial=actor.parent/'initial';reg=read(actor/'registration.json');selected=actor/'round_000/selection/completion.json'
    s=read(selected);assert s['passed'];cuts=selected.parent/'candidates.json'
    begin=read(initial/'completion.json');assert begin['passed'];run=Path(begin['run']);m=read(run/'manifest.json')
    assert m['status']=='completed' and m['metrics']['native_full_check_passed']
    command=m['command'];graph=command[command.index('--read_rr_graph')+1]
    identity=dict(architecture=m['shared_inputs'][command[1]]['sha256'],circuit=m['shared_inputs'][command[2]]['sha256'],
        graph=m['shared_inputs'][graph]['sha256'],packed=m['outputs']['packed.net']['sha256'],
        placement=m['outputs']['placed.place']['sha256'],constraints=s['constraints_sha256'])
    owner=actor/'round_000/owner_selection/completion.json';owner_groups=None
    if owner.exists():
        o=read(owner);assert o['passed'];owner_groups=o.get('eligible_joint_groups');bind(owner)
    audits=[];release_count=0
    for p in sorted(actor.glob('round_*/candidate_*/reuse_on_domain_audit.json')):
        a=read(p);assert a['passed'];released=a.get('released_queries')
        audits.append(dict(receipt=str(p),enabled=a.get('enabled'),release_evidence_available=released is not None,
            released_query_count=None if released is None else len(released)))
        if released is not None:release_count+=len(released)
        bind(p)
    for p in [actor/'registration.json',actor/'completion.json',initial/'completion.json',run/'manifest.json',selected,cuts]:bind(p)
    return dict(case=str(case),actor=str(actor),declared_physical_identity=identity,
        declared_initial_route_body_sha256=begin['route_body_sha256'],
        initial_selector_candidates_sha256=sha(cuts),initial_STA_eligible_sharing_scopes=s['candidate_scopes'],
        initial_multi_crossing_nets=s['multi_crossing_nets'],current_margin_screen_s=s['minimum_margin_s'],
        initial_CPD_s=s['CPD_s'],fixed_CPD_limit_s=reg['anchor']['CPD_s'],
        fixed_CPD_headroom_ratio=reg['anchor']['CPD_s']/s['CPD_s'],fixed_resource_limits=reg.get('resource_limits'),
        owner_backend_enabled=reg.get('owner_escalation'),initial_observed_eligible_owner_groups=owner_groups,
        release_audit_rows=audits,observed_released_queries=release_count,
        qualification='Existing passed metadata/declared digests; raw graph/routes/full STA are not rehashed here. Missing owner or release evidence is unknown, never zero.')
records=[]
for pair in pairs:
    n=rows[pair['native']['label']];d=rows[pair['domain']['label']]
    nf,df=feature(case_of(n)),feature(case_of(d))
    assert nf['declared_physical_identity']==df['declared_physical_identity']
    assert nf['declared_initial_route_body_sha256']==df['declared_initial_route_body_sha256']
    assert nf['initial_selector_candidates_sha256']==df['initial_selector_candidates_sha256']
    assert nf['fixed_CPD_limit_s']==df['fixed_CPD_limit_s'] and nf['fixed_resource_limits']==df['fixed_resource_limits']
    delta=pair['delta'];vertical_gain=delta['SB_pairs']<=0 and delta['CB_sources']<=0 and (delta['SB_pairs']<0 or delta['CB_sources']<0)
    records.append(dict(label=pair['label'],evidence_kind='historical_complete_development_pair',native=nf,domain=df,
        final_native=pair['native']['quality'],final_domain=pair['domain']['quality'],domain_minus_native=delta,
        complete_seconds=dict(native=pair['native']['seconds'],domain=pair['domain']['seconds']),
        relative_vertical_count_benefit=vertical_gain,universal_gain_claim=False))
cp=D/'cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json';c=read(cp);bind(cp)
nf,df=[feature(Path(c['results'][a]['case'])) for a in ['native','domain']]
assert nf['declared_physical_identity']==df['declared_physical_identity']
assert nf['initial_selector_candidates_sha256']==df['initial_selector_candidates_sha256']
records.append(dict(label='Conv-hls CP1r2',evidence_kind='prospective_fixed_version_no_op_pair',native=nf,domain=df,
    final_native=c['results']['native']['quality'],final_domain=c['results']['domain']['quality'],
    domain_minus_native=c['matched_comparison']['delta_domain_minus_native'],
    complete_seconds={a:c['results'][a]['complete_seconds'] for a in ['native','domain']},relative_vertical_count_benefit=False,universal_gain_claim=False))
by_label={r['label']:r for r in records};strict=by_label['Eltwise SB'];relaxed=by_label['Eltwise SB 102%']
assert strict['native']['declared_initial_route_body_sha256']==relaxed['native']['declared_initial_route_body_sha256']
assert strict['native']['declared_physical_identity']==relaxed['native']['declared_physical_identity']
assert strict['native']['initial_selector_candidates_sha256']==relaxed['native']['initial_selector_candidates_sha256']
assert strict['native']['fixed_resource_limits']==relaxed['native']['fixed_resource_limits']
assert strict['native']['fixed_CPD_headroom_ratio']==1.0 and abs(relaxed['native']['fixed_CPD_headroom_ratio']-1.02)<1e-14
counterexample=dict(passed=True,labels=[strict['label'],relaxed['label']],same_physical_input=True,same_initial_route_body=True,
    same_initial_STA_screen_and_48_scope_bytes=True,same_absolute_wire_SB_CB_limits=True,
    strict_CPD_limit_s=strict['native']['fixed_CPD_limit_s'],relaxed_CPD_limit_s=relaxed['native']['fixed_CPD_limit_s'],
    strict_domain_minus_native=strict['domain_minus_native'],relaxed_domain_minus_native=relaxed['domain_minus_native'],
    conclusion='Initial crossing/slack-screen descriptors alone cannot distinguish this observed domain tradeoff: policy timing envelope differs. Include the declared objective and fixed remaining timing/resource budgets; applicability is not final-benefit prediction. This is the same physical input, not independent replication.')
identities={tuple(sorted(r['native']['declared_physical_identity'].items())) for r in records}
zero=[r['label'] for r in records if r['native']['initial_STA_eligible_sharing_scopes']==0]
eligible=[r['label'] for r in records if r['native']['initial_STA_eligible_sharing_scopes']>0]
gain=[r['label'] for r in records if r['relative_vertical_count_benefit']]
assert len(records)==10 and len(identities)==9
assert len(zero)==4 and len(eligible)==6 and len(gain)==4
failures=[]
for label,r in rows.items():
    if '(initial fail)' in label or '(load fail)' in label:
        failures.append(dict(label=label,outcome_class='initial_routing_failed' if '(initial fail)' in label else 'input_loading_failed',
            quality=None,sharing_eligibility=None,owner_eligibility=None,complete_seconds=r.get('complete_seconds',r.get('time_seconds'))))
tpu=D/'cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json';bind(tpu)
for arm,row in read(tpu)['outcomes']['tpu_ws']['arms'].items():
    assert row['classification']=='initial_routing_execution_timeout'
    failures.append(dict(label='TPU CP1r2 '+arm,outcome_class=row['classification'],quality=None,sharing_eligibility=None,owner_eligibility=None,complete_seconds=row['complete_attempt_seconds']))
assert len(failures)==10
write(out/'pairs.json',records);write(out/'timing_envelope_counterexample.json',counterexample);write(out/'no_legal_root_attempts.json',failures)
with (out/'overview.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['configuration','initial_eligible_sharing_scopes','CPD_limit_over_initial','domain_minus_native_wire','SB','CB','CPD_ns','time_seconds','observed_release_queries','owner_initial_groups'])
    for r in records:
        delta=r['domain_minus_native'];w.writerow([r['label'],r['native']['initial_STA_eligible_sharing_scopes'],r['native']['fixed_CPD_headroom_ratio'],delta['wirelength'],delta['SB_pairs'],delta['CB_sources'],delta['CPD_ns'],r['complete_seconds']['domain']-r['complete_seconds']['native'],r['domain']['observed_released_queries'],r['domain']['initial_observed_eligible_owner_groups']])
write(out/'completion.json',dict(passed=True,complete_configuration_pairs=10,declared_distinct_physical_identities=9,
    zero_initial_sharing_scope_pairs=zero,positive_initial_sharing_scope_pairs=eligible,relative_vertical_gain_configuration_pairs=gain,
    no_legal_root_attempts_retained=10,CPD_policy_counterexample=True,new_native_calls=0,new_independent_inputs=0,new_full_method_results=0,
    complete_method_versions_uniform=False,source_sha256={str(p):sha(p) for p in sorted(set(sources))},
    artifact_sha256={n:sha(out/n) for n in ['pairs.json','overview.csv','timing_envelope_counterexample.json','no_legal_root_attempts.json']},
    qualification='Retrospective metadata extraction over all nine published development comparison configurations plus the closed fixed-version conv-hls pair. Configuration counts are not independent trials; SB strict/102% share one physical input. Selection counts establish screened applicability only. Versions, owner opportunities and policy envelopes differ; four vertical trades among six applicable configurations is descriptive, not a success probability or generalization estimate. Failed/timeout roots retain unknown eligibility, never zero. No new experiment, raw-input revalidation, optimized overhead or complete-controller superiority.'))
print(dict(passed=True,pairs=10,declared_physical_identities=9,zero_scope_pairs=zero,eligible_pairs=len(eligible),relative_vertical_trades=len(gain),new_native_calls=0))
