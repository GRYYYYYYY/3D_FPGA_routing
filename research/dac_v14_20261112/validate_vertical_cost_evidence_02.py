"""Small adversarial checks for zero-equivalence; no native or graph access."""
import ast
import copy
import datetime
import json
from pathlib import Path
from retained_prefix_workflow import D, write, sha
from vertical_cost_evidence_v1 import semantic_native, assert_zero_identity
from cp1r3_raw_admission_v1 import parse_request, parse_native

out=D/'vertical_cost_evidence_validation_02';assert not out.exists()
tests=[]
def reject(label,fn):
    try:fn()
    except (AssertionError,ValueError):tests.append(dict(test=label,passed=True));return
    raise AssertionError('Guard failed: '+label)

base=dict(source={'graph':'g','root':'r'},config='same',request=[(1,2,.5)],
    native_decisions=[['QUERY','1','2','1','.5','3','4']],restored_vector='v',
    restored_tree={'r':[1,2]},candidate_tree={'r':[1,3]},candidate_vector='c',
    resources={'SB':1},policies={'accepted':False})
assert_zero_identity(base,copy.deepcopy(base));tests.append(dict(test='exact_success',passed=True))
for key in base:
    other=copy.deepcopy(base);other[key]=None
    reject('changed_'+key,lambda other=other:assert_zero_identity(base,other))
other=copy.deepcopy(base);other.pop('candidate_tree')
reject('missing_evidence',lambda:assert_zero_identity(base,other))
a='MODE weighted_soft\nQUERY 1 2 1 .5 3 4 0.01\nATTEMPT 1 2 1 1 1\nCOMPLETE 1 1 1 0.1 occupancy_restored\n'
b=a.replace('0.01','9.2').replace('1 0.1 occupancy','1 80 occupancy')
assert semantic_native(a)==semantic_native(b)
tests.append(dict(test='elapsed_only_excluded',passed=True))
for label,other in [('query_result',a.replace('QUERY 1 2 1','QUERY 1 2 0')),
                    ('attempt',a.replace('ATTEMPT 1 2 1 1 1','ATTEMPT 1 2 1 0 1')),
                    ('criticality',a.replace('.5','.4'))]:
    assert semantic_native(a)!=semantic_native(other);tests.append(dict(test=label+'_retained',passed=True))
reject('nonfinite_elapsed',lambda:semantic_native(a.replace('0.01','nan')))
role=json.loads((D/'vertical_cost_baseline_dev_01/reference_role.json').read_text())
request=(D/'vertical_cost_baseline_dev_01/request.txt').read_text()
parsed=parse_request(request,role);assert len(parsed)==25
tests.append(dict(test='registered_full25_request',passed=True))
reject('request_trailing',lambda:parse_request(request+'extra\n',role))
reject('request_missing',lambda:parse_request('\n'.join(request.splitlines()[:-1])+'\n',role))
assert parse_native(a.splitlines(),[(1,2,.5)])['success']
reject('missing_complete',lambda:parse_native(a.splitlines()[:-1],[(1,2,.5)]))
reject('trailing_native',lambda:parse_native(a.splitlines()+['MODE weighted_soft'],[(1,2,.5)]))
for name in ['vertical_cost_evidence_v1.py','build_vertical_cost_baseline_01.py']:
    ast.parse((D/name).read_text())
out.mkdir()
write(out/'completion.json',dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    tests=tests,count=len(tests),new_native_or_STA_calls=0,actual_source_control_audit_executed=False,
    actual_zero_weight_equivalence_executed=False,build_executed=False,
    source_sha256={str(D/n):sha(D/n) for n in ['vertical_cost_evidence_v1.py','validate_vertical_cost_evidence_02.py',
        'vertical_cost_baseline_dev_01/reference_role.json','vertical_cost_baseline_dev_01/request.txt']},
    qualification='Parser and equivalence guards only; full actual-byte, raw-STA, tree, source-control and zero-weight audits remain serial execution gates.'))
print(dict(passed=True,checks=len(tests)))
