"""Reuse existing raw admission after successful original CP1r6 verification."""
import argparse
import fcntl
import inspect
import textwrap
import time
import traceback
from pathlib import Path
import cp1r3_raw_admission_v1 as raw
from retained_prefix_workflow import D, read, write, sha
from recovery_prefix_v1 import Evidence, live_identity
from endpoint_timing_policy_streaming_v2 import compare

COHORT = D/'cp1r6_s38584_pair_01'
ROOT = D/'S38584_complete_admission_01'
OLD_ENTRY = """    supplement = SUPPLEMENT/'cases'/target['input']/target['arm']/'completion.json'
    supplemental = self.document(supplement)
    assert supplemental['passed'] and supplemental['original_frozen_result_unchanged']
    self.e.verify(supplemental['source_sha256'])
    replay = self.document(supplement.parent/'replayed_verifier/completion.json')
    assert replay['passed'] and replay['complete_configuration_verified']"""
NEW_ENTRY = """    replay = self.document(case/'completion.json')
    require_original_pass(original, replay)
    self.e.verify(replay['source_sha256'])"""


def require_original_pass(original, replay):
    assert original['status']=='complete_legal_verified'
    assert replay['passed'] is True and replay['complete_configuration_verified'] is True
    assert original['quality']=={k:replay[k] for k in ['CPD_ns','resources']}
    assert original['complete_seconds']==replay['complete_wall_seconds']


def audit_class():
    # Only replace the old supplemental-replay entry, never its scientific gates.
    source=textwrap.dedent(inspect.getsource(raw.Audit.case))
    assert source.count(OLD_ENTRY)==1
    revised=source.replace(OLD_ENTRY,NEW_ENTRY)
    assert revised.replace(NEW_ENTRY,OLD_ENTRY)==source
    namespace={**raw.__dict__,'ROOT':COHORT,'require_original_pass':require_original_pass}
    exec(compile(revised,str(Path(__file__).resolve())+'::original_case_entry','exec'),namespace)
    class OriginalPassedAudit(raw.Audit):
        pass
    OriginalPassedAudit.case=namespace['case']
    assert OriginalPassedAudit.state is raw.Audit.state
    assert OriginalPassedAudit.transaction is raw.Audit.transaction
    return OriginalPassedAudit


def state_chain(audit, case):
    flow=case/'flow'; repair=flow/'resource_flow/repair'
    done=audit.document(flow/'completion.json'); current=done['initial_state']; accepted=[]
    attempts=audit.document(repair/'attempts.json')
    for item in attempts:
        assert item['current_state']==current and current in audit.states
        tx=Path(item['transaction']); registration=audit.document(tx/'registration.json')
        progress=audit.document(tx/'progress.json')
        assert progress==item['roles'] and item['native_transaction_complete']
        assert all(r['state']==current for r in registration['roles'].values())
        role=item.get('accepted_role')
        if role:
            assert progress[role]['status']=='legal_evaluated'
            assert audit.document(tx/(role+'_decisions.json'))['resources_under_timing']['accepted']
            current=progress[role]['evaluation']
            assert current==item['committed_evaluation'] and current in audit.states
            accepted.append(item)
        else:
            assert 'committed_evaluation' not in item
            for name,row in progress.items():
                if row['status']=='legal_evaluated':
                    assert not audit.document(tx/(name+'_decisions.json'))['resources_under_timing']['accepted']
    assert accepted==audit.document(repair/'steps.json')
    assert current==done['resource_policy_final_state']==audit.document(repair/'completion.json')['final_state']
    assert current==audit.document(repair/'current_state.json')['state']
    current=done['timing_initial_state']; timing_steps=0
    for item in audit.document(flow/'timing/attempts.json'):
        assert item['before_state']==current and current in audit.states
        if item['accepted']:
            current=item['evaluation']; timing_steps+=1
            assert current in audit.states
    assert current==done['final_state']
    assert timing_steps==audit.document(flow/'timing/completion.json')['accepted_steps']
    return dict(passed=True,resource_attempts=len(attempts),resource_accepts=len(accepted),
                timing_accepts=timing_steps,all_states_in_raw_audited_set=True,
                terminal_handoff_verified_by_original_checker=True)


def prerequisites(e):
    plan=read(ROOT/'plan.json');e.bind(ROOT/'plan.json');e.verify(plan['source_sha256'])
    registration=read(COHORT/'queue/registration.json')
    assert not live_identity(registration['pid'],registration['start_ticks'])
    assert (COHORT/'queue/completion.json').exists()
    e.bind(COHORT/'queue/registration.json');e.bind(COHORT/'queue/completion.json')
    return plan


def role(arm):
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=ROOT/arm;out.mkdir(exist_ok=False);start=time.monotonic();e=Evidence()
        try:
            plan=prerequisites(e);target=plan['targets'][arm]
            original_path=COHORT/'s38584_results.json';e.bind(original_path);original=read(original_path)[arm]
            if original['status']!='complete_legal_verified':
                result=dict(passed=False,status='original_full_verification_not_passed',quality=None,
                    quality_admitted=False,original_status=original['status'],execution_ended=True,
                    timeout='timeout' in original['status'],infrastructure_error=None,legal_no_gain=None,
                    complete_algorithm_seconds=original['complete_seconds'],
                    reason='Original role does not pass full checker; preserve original cause, no automatic exception.')
            else:
                audit=audit_class()(plan['release'],e)
                result=audit.case(target,original,out)
                result['state_chain']=state_chain(audit,Path(target['case']))
                result['status']='original_full_and_additional_raw_admission_passed'
            e.unchanged()
        except Exception:
            error=traceback.format_exc();(out/'failure.log').write_text(error)
            result=dict(passed=False,status='raw_admission_requires_reconciliation',quality=None,
                        quality_admitted=False,legal_no_gain=None,error=error,infrastructure_error=None)
        result.update(arm=arm,complete_readonly_seconds=time.monotonic()-start,source_sha256=e.bound,
                      new_native_or_STA_calls=0,historical_receipts_rewritten=False,automatic_retry=False)
        write(out/'completion.json',result)


def pair():
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=ROOT/'pair';out.mkdir(exist_ok=False);start=time.monotonic();e=Evidence()
        try:
            plan=prerequisites(e);rows={}
            for arm in ['native','domain']:
                p=ROOT/arm/'completion.json';e.bind(p);rows[arm]=read(p)
            n,d=rows['native'],rows['domain']
            result=dict(passed=True,all_roles_accounted=True,matched_complete_quality_pair=False,
                        quality_admitted_roles=sum(bool(r.get('quality_admitted')) for r in rows.values()),
                        delta_domain_minus_native=None,formal_interleaved_time_ratio=None)
            if all(r.get('passed') and r.get('quality_admitted') for r in rows.values()):
                for arm,row in rows.items():
                    e.verify(row['source_sha256'])
                configs={arm:read(plan['targets'][arm]['config']) for arm in rows}
                assert {k for k in set(configs['native'])|set(configs['domain']) if configs['native'].get(k)!=configs['domain'].get(k)}=={'domain_mode','domain_feedback'}
                matched=all(n['initial'][k]==d['initial'][k] for k in ['route_body_sha256','packed_sha256','placed_sha256','vector_semantic_sha256','constraints_sha256'])
                matched=matched and n['graph_payload_sha256']==d['graph_payload_sha256']
                result['matched_complete_quality_pair']=matched
                if matched:
                    endpoints=compare(read(Path(n['final']['state'])/'endpoint_vector.json'),read(Path(d['final']['state'])/'endpoint_vector.json'))
                    assert endpoints['compatible'];write(out/'endpoint_changes.json',endpoints)
                    result.update(native_quality=n['quality'],domain_quality=d['quality'],
                        delta_domain_minus_native={**{k:d['quality']['resources'][k]-n['quality']['resources'][k] for k in raw.AXES},'CPD_ns':d['quality']['CPD_ns']-n['quality']['CPD_ns']},
                        paired_endpoint_summary={k:v for k,v in endpoints.items() if k!='changes'},
                        actual_complete_seconds={arm:r['complete_algorithm_seconds'] for arm,r in rows.items()},
                        descriptive_single_pair_time_ratio=d['complete_algorithm_seconds']/n['complete_algorithm_seconds'])
            result['status']='matched_full_quality_pair' if result['matched_complete_quality_pair'] else 'pair_not_admitted'
            e.unchanged()
        except Exception:
            error=traceback.format_exc();(out/'failure.log').write_text(error)
            result=dict(passed=False,status='pair_admission_requires_reconciliation',matched_complete_quality_pair=False,quality=None,error=error)
        result.update(complete_readonly_seconds=time.monotonic()-start,source_sha256=e.bound,
                      new_native_or_STA_calls=0,automatic_paper_update=False,historical_failures_preserved=True,
                      qualification='One distinct public mapped sequential s38584 circuit, new to current CP1 confirmation, with a fresh actual placement on the existing Hybrid-O architecture family. No unseen-input or new-architecture claim. Original full checks plus unchanged raw methods, explicit state chain and actual graph/root/vector pair. Whole per-arm commands only; audits separate. Any time ratio is descriptive N/D, not interleaved/statistical speedup.')
        write(out/'completion.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--role',choices=['native','domain','pair'],required=True)
    args=parser.parse_args()
    if args.role=='pair':pair()
    else:role(args.role)
