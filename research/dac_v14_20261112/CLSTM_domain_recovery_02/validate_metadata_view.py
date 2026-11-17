"""Actual small metadata and rejection guards for the bounded empty-receipt view."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = ROOT.parent
RUNTIME = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3/runtime')
sys.path[:0] = [str(RUNTIME), str(ROOT/'runtime_extension'), str(D)]
import audited_empty_supervision_view_v1 as view
from recovery_prefix_v1 import Evidence
from same_actor_stage_reuse_v1 import audit_record_gate

case_path = D/'CLSTM_domain_empty_supervision_audit_02/audit.json'
case = json.loads(case_path.read_text())
inventory = json.loads((D/'interrupted_stage_reconciliation_01/inventory.json').read_text())
row = next(r for r in inventory['rows'] if (r['pair'], r['arm']) == ('clstm_input_contract_pair_02','domain'))
tx = Path(row['transaction'])
bad = tx/'reuse_on_native_supervision.json'
plan = dict(pair=case['pair'], arm=case['arm'], original_role='reuse_on',
            original_transaction=str(tx), original_resource_actor=str(tx.parents[1]),
            empty_supervision_identity_exception=dict(exact_empty_path=str(bad),
                historical_failed_summary=str(D/'interrupted_stage_reconciliation_01/completion.json')))
audited = case['source_sha256']
rows = []


def check(name, action, rejection=False):
    try:
        action()
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        assert rejection, (name, repr(error))
        rows.append(dict(name=name, passed=True, rejected=type(error).__name__))
    else:
        assert not rejection, name
        rows.append(dict(name=name, passed=True))


def evaluate(c=case, p=plan, mapping=audited):
    evidence = Evidence()
    result = view.supervision_identity_view(bad, p, c, evidence, mapping)
    assert set(result) == {'supervisor','child'}
    assert 'returncode' not in result and 'passed' not in result
    assert all(stat[2] < 1024*1024 for stat in evidence.stats.values())
    evidence.unchanged()
    return result


check('actual_source_stage_gate', lambda:audit_record_gate(plan, {'rows':[case]}, case, tx))
check('actual_empty_receipt_only_original_dead_identities', evaluate)
active = tx/'reuse_on_native_supervision.active.json'
check('ordinary_valid_JSON_unchanged', lambda: (
    view.supervision_identity_view(active,plan,case,Evidence(),audited) == json.loads(active.read_text())) or (_ for _ in ()).throw(AssertionError()))
fixture = ROOT/'metadata_view_fixture'
fixture.mkdir(exist_ok=False)
other = fixture/'other_empty.json'
other.write_bytes(b'')
check('other_empty_JSON_still_rejected', lambda:view.supervision_identity_view(other,plan,case,Evidence(),audited), True)
c = copy.deepcopy(case);c['complete_candidate_admitted']=True
check('candidate_admission_cannot_be_inherited', lambda:evaluate(c=c), True)
c = copy.deepcopy(case);c['supervision_corroboration']['original_supervisor_exit_status']='completed'
check('fabricated_historical_exit_rejected', lambda:evaluate(c=c), True)
c = copy.deepcopy(case);c['stages']['exact_complete_ordered_native_request']['successful_queries']=22
check('incomplete_request_rejected', lambda:evaluate(c=c), True)
mapping = dict(audited);mapping[str(bad)]='0'*64
check('changed_empty_receipt_binding_rejected', lambda:evaluate(mapping=mapping), True)
p = copy.deepcopy(plan);p['empty_supervision_identity_exception']['historical_failed_summary']=str(other)
check('unbound_historical_summary_rejected', lambda:evaluate(p=p), True)
original_live = view.live_identity
try:
    view.live_identity = lambda pid,ticks:True
    check('live_original_identity_rejected', evaluate, True)
finally:
    view.live_identity = original_live
c = copy.deepcopy(case);c['stages']['candidate_STA']['completed']=True
check('existing_partial_STA_cannot_enter_reuse_gate', lambda:audit_record_gate(plan,{'rows':[c]},c,tx),True)
for name in ['completion.json','registration.json','input_seal.json']:
    assert (tx/'reuse_on'/name).is_file()
assert bad.read_bytes()==b''
output = ROOT/'validation.json'
assert not output.exists()
source = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
    Path(__file__).resolve(), ROOT/'adapter_revision.json',case_path,
    ROOT/'runtime_extension/audited_empty_supervision_view_v1.py',
    ROOT/'runtime_extension/same_actor_stage_reuse_v1.py']}
output.write_text(json.dumps(dict(passed=True, tests=len(rows), rows=rows,
    original_empty_receipt_and_failure_unchanged=True, native_or_STA_calls=0,
    graph_or_raw_vector_reads=0, actual_full_stage_adoption_executed=False,
    candidate_or_full_method_admitted=False, source_sha256=source,
    qualification='Actual bounded source-audit/identity metadata and new rejection guards only. Reversible unchanged dispatch/prefix bodies retain previous validation. Heavy byte closure and adoption require the registered serial owner.'),indent=2)+'\n')
print(json.dumps(dict(passed=True,tests=len(rows),native_calls=0)))
