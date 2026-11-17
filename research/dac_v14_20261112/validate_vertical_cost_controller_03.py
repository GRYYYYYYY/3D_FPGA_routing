"""Adversarial zero/failure controller fixtures; no actual solver/graph work."""
import copy
import json
import tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_vertical_cost_baseline_v2 import WEIGHTS, execute, clean_environment
from vertical_cost_evidence_v2 import BaselineAudit
from recovery_prefix_v1 import Evidence

out=D/'vertical_cost_controller_validation_03';assert not out.exists()
tests=[]
def reject(name,fn):
    try:fn()
    except (AssertionError,ValueError):tests.append(dict(test=name,passed=True));return
    raise AssertionError(name)

class FakeRunner:
    def __init__(self,path,outcomes):self.b=path;self.roles={};self.calls=[];self.outcomes=outcomes
    def arm(self,name,*args):
        self.calls.append(name);row=self.outcomes[name]
        if isinstance(row,Exception):raise row
        return copy.deepcopy(row)

with tempfile.TemporaryDirectory(prefix='vertical-cost-controller-') as temp:
    temp=Path(temp)
    zero_pass=dict(status='legal_evaluated',verification_status='passed',quality_admitted=True)
    for label,zero,calls in [('zero_mismatch',dict(status='legal_evaluated',verification_status='infrastructure_error'),1),
                            ('zero_timeout',dict(status='timeout'),1),
                            ('zero_exception',RuntimeError('fixture'),1),
                            ('all_processed',zero_pass,4)]:
        p=temp/label;p.mkdir()
        states={n:dict(status='transaction_failed_rolled_back',verification_status='passed',quality_admitted=False,rollback_verified=True) for n in WEIGHTS}
        states['weight_0']=zero
        r=FakeRunner(p,states);execute(r,{},'fixture')
        assert len(r.calls)==calls and list(r.roles)==list(WEIGHTS)
        if calls==1:assert all(r.roles[n]['status']=='not_executed_zero_equivalence_not_passed' for n in list(WEIGHTS)[1:])
        tests.append(dict(test=label,passed=True))
    p=temp/'positive_errors';p.mkdir()
    states={'weight_0':zero_pass,'weight_05':dict(status='timeout'),
        'weight_1':RuntimeError('fixture'),'weight_2':dict(status='legal_evaluated',verification_status='passed',quality_admitted=True,accepted=False)}
    r=FakeRunner(p,states);assert execute(r,{},'fixture') and len(r.calls)==4
    assert r.roles['weight_05']['status']=='timeout' and r.roles['weight_1']['status']=='infrastructure_error'
    assert r.roles['weight_2']['quality_admitted'] and not r.roles['weight_2']['accepted']
    tests.append(dict(test='positive_error_continues_and_no_gain_retained',passed=True))
    worker=temp/'worker';run=worker/'runs/state';restored=run/'candidate_restored';candidate=run/'candidate'
    restored.mkdir(parents=True);candidate.mkdir()
    vector=dict(cpd_s=1.,setup={},hold={},endpoint_ids=[],constraints_sha256='fixture')
    write(worker/'completion.json',dict(passed=True,checks={'native_FULL':True,'source_restored':True}))
    write(worker/'registration.json',dict(source_sha256={},pid=-1,start_ticks='0'))
    write(worker/'candidate_exports.json',dict(passed=True,candidate_gate_present=False,candidate=str(candidate),restored=str(restored)))
    write(worker/'endpoint_vector.json',vector)
    (restored/'native_state_gate.txt').write_text('restored_source FULL fresh_STA actual_installed_trees\n')
    stdout='H3D_ACTUAL_STATE_BEGIN restored_source\nCompleted routing consistency check successfully.\nH3D_ACTUAL_STATE_COMPLETE restored_source\n'
    (run/'stdout.log').write_text(stdout)
    audit=object.__new__(BaselineAudit);audit.e=Evidence()
    audit.vector=lambda path:__import__('cp1r3_raw_admission_v1').vector_digest(vector)
    audit.tree=lambda path:{'fixture':1}
    vectors,trees,exports=audit.callbacks(worker,False)
    assert set(vectors)==set(trees)=={'restored'}
    tests.append(dict(test='rollback_requires_only_actual_restored_state',passed=True))
    reject('failed_search_cannot_claim_candidate',lambda:audit.callbacks(worker,True))
    (candidate/'native_state_gate.txt').write_text('candidate FULL fresh_STA actual_installed_trees\n')
    reject('unexpected_candidate_gate_rejected',lambda:audit.callbacks(worker,False))
    (candidate/'native_state_gate.txt').unlink()
    # Fresh evidence object after intentionally changing fixture stdout.
    (run/'stdout.log').write_text(stdout.replace('Completed routing consistency check successfully.','incomplete'))
    audit.e=Evidence();reject('missing_restored_FULL_rejected',lambda:audit.callbacks(worker,False))

env=clean_environment(dict(PATH='/usr/bin',VPR_JOINT_NATIVE_OBJECTIVE='bad',VPR_H3D_MODE='bad',
                          VPR_UNKNOWN_HOOK='bad',LD_PRELOAD='bad',LD_AUDIT='bad',LD_LIBRARY_PATH='bad',OMP_NUM_THREADS='90'))
assert not any(k.startswith('VPR_') or k.startswith('LD_') for k in env)
assert env['OMP_NUM_THREADS']==env['OPENBLAS_NUM_THREADS']==env['MKL_NUM_THREADS']=='1'
tests.append(dict(test='all_inherited_VPR_and_loader_hooks_removed',passed=True))
assert list(WEIGHTS.values())==[0.,.5,1.,2.]
out.mkdir()
write(out/'completion.json',dict(passed=True,checks=len(tests),tests=tests,solver_or_STA_calls=0,
    actual_byte_or_source_control_audit_executed=False,actual_zero_equivalence_executed=False,
    source_sha256={str(D/n):sha(D/n) for n in ['validate_vertical_cost_controller_03.py',
        'run_vertical_cost_baseline_v2.py','vertical_cost_evidence_v2.py']},
    qualification='Synthetic controller branch and callback-gate fixtures, not physical tree/STA/source equivalence evidence.'))
print(dict(passed=True,checks=len(tests)))
