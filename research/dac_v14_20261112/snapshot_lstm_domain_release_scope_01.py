"""Preserve one actual release-containing accepted transaction, without replay."""
import time
from pathlib import Path
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

out=D/'LSTM_domain_release_scope_01';assert not out.exists();started=time.monotonic()
base=Path(read(D/'cp1r3_distinct_input_cohort_01/plan.json')['inputs'][0]['workspace'])
repair=base/'domain/flow/resource_flow/repair';tx=repair/'round_002/candidate_00';role='reuse_on'
closed=read(tx/'completion.json');decision=read(tx/(role+'_decisions.json'))
domain=read(tx/(role+'_domain_audit.json'));evaluated=read(tx/(role+'_evaluation/completion.json'))
assert closed['passed'] and domain['passed'] and evaluated['passed'] and all(evaluated['checks'].values())
assert decision['resources_under_timing']['accepted'] and domain['released_queries']==[[2896,3]]
assert 2896 in domain['initial_domain_nets'] and 2896 not in domain['final_domain_nets']
assert set(domain['initial_domain_nets'])-set(domain['final_domain_nets'])=={2896}
assert closed['roles']['reuse_off']['status']=='not_executed_domain_candidate_accepted'
assert not (tx/'reuse_off').exists()
step=next(x for x in read(repair/'steps.json') if x['transaction']==str(tx))
assert step['accepted_role']==role and step['committed_evaluation']==str(tx/(role+'_evaluation'))
worker=tx/role;registration=read(worker/'registration.json');identity=process_identity(registration['pid'])
assert not identity or identity['state']=='Z' or identity['start_ticks']!=registration['start_ticks']
log=worker/'runs/state/joint_native.log';assert log.stat().st_size<4*1024**2
log_sha=sha(log);events=[];before=[];after=[];released=False;queries=[];complete=None
for line in log.read_text().splitlines():
    fields=line.split();assert fields and complete is None
    if fields[0]=='DOMAIN_RELEASE':
        assert fields[1:]==['2896','3'] and not released;released=True;events.append(line)
    elif fields[0]=='ATTEMPT' and fields[1:3]==['2896','3']:
        assert len(fields)==6;(after if released else before).append(fields);events.append(line)
    elif fields[0]=='QUERY':
        queries.append((int(fields[1]),int(fields[2])))
        if fields[1:3]==['2896','3']:events.append(line)
    elif fields[0]=='COMPLETE':complete=fields;events.append(line)
assert len(before)==9 and all(x[5]=='0' for x in before)
assert len(after)==2 and [x[5] for x in after]==['0','1']
assert complete[:4]==['COMPLETE','1','8','8'] and complete[-1]=='occupancy_restored'
roles=read(tx/'registration.json')['roles'];assert queries==[(q['net'],q['pin']) for q in roles[role]['queries']]
assert sha(log)==log_sha
sources=[Path(__file__).resolve(),tx/'registration.json',tx/'completion.json',tx/(role+'_decisions.json'),
    tx/(role+'_domain_audit.json'),tx/(role+'_audit/analysis.json'),tx/'process_costs.json',
    worker/'registration.json',worker/'completion.json',worker/'runs/state/manifest.json',
    tx/(role+'_evaluation/completion.json'),Path(roles[role]['request']),Path(roles[role]['crossing_domain'])]
assert all(p.stat().st_size<4*1024**2 for p in sources)
out.mkdir();snapshots=out/'receipts';snapshots.mkdir();origins=[]
for i,p in enumerate(sources):
    data=p.read_bytes();target=snapshots/f'{i:03d}_{p.name}';target.write_bytes(data)
    assert sha(target)==sha(p);origins.append(dict(original=str(p),snapshot=str(target),sha256=sha(target)))
(out/'actual_release_log_excerpt.txt').write_text('\n'.join(events)+'\n')
write(out/'original_accepted_step.json',step)
result=closed['roles'][role];comparison=decision['strict']['comparison']
write(out/'completion.json',dict(passed=True,kind='existing_scoped_transaction_evidence',observed_at=datetime.now(timezone.utc).isoformat(),
    is_complete_algorithm_result=False,transaction=str(tx),round=2,accepted=True,
    original_candidate_checks=evaluated['checks'],original_physical_and_domain_audits_passed=True,
    released_net=2896,trigger_pin=3,failed_restricted_attempts=9,post_release_attempts=2,
    exact_registered_query_order_verified=True,complete_queries=8,occupancy_restored=True,
    CPD_ns=result['cpd_s']*1e9,resources=result['resources'],
    source_to_candidate_resource_delta=decision['resources_under_timing']['resource_delta'],
    endpoint_delta_summary={k:v for k,v in comparison.items() if k!='changes'},
    complete_transaction_seconds=closed['complete_orchestrator_seconds'],nested_native_core_seconds=result['native_core_seconds'],
    owner_coordination=False,unrestricted_fallback_not_executed=True,matched_no_release_counterfactual_available=False,
    complete_method_cost=None,paired_method_ratio=None,new_independent_verified_pairs=0,
    paper_benefit_claims_authorized=False,new_native_or_STA_calls=0,raw_full_vectors_or_graph_reverified=False,
    complete_snapshot_and_log_audit_seconds=time.monotonic()-started,
    original_log_sha256=log_sha,original_log=str(log),receipt_origins=origins,
    source_sha256={r['snapshot']:r['sha256'] for r in origins},
    qualification='Original registered domain transaction passed candidate FULL/STA/physical/input gates and was accepted under its fixed root envelope. A bounded existing-log audit confirms failed restricted searches, per-net release, later search success and exact complete query order. Release is observed in this accepted transaction, but the seven-SB delta belongs to the entire eight-query group; no matched no-release counterfactual or capacity-infeasibility proof exists. Endpoint regressions are retained. This snapshot does not rerun raw vector/graph audits, cure the native whole-verifier failure, complete the domain method or admit a paper benefit. Transaction/core costs are nested and cannot be assembled into complete cost.'))
print(dict(passed=True,accepted=True,resources=result['resources'],release=[2896,3],
    transaction_seconds=closed['complete_orchestrator_seconds'],whole_method_result=False))
