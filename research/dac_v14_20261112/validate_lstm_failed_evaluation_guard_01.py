"""Small negative tests for the exact ctime exception; no experiment payloads."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, write, sha
from audit_lstm_failed_evaluation_01 import exact_metadata_failure

paths=[f'/synthetic/input_{i}' for i in range(5)]
prior=dict(inputs={p:dict(passed=True,sha256='a'*64,stat_identity=[1,i,50,100,200]) for i,p in enumerate(paths)})
seal=copy.deepcopy(prior);seal['passed']=False
for p in paths:seal['inputs'][p].update(passed=False,stat_identity=[*prior['inputs'][p]['stat_identity'][:4],201])
reg=dict(source_sha256={p:'a'*64 for p in paths})
expected={p:dict(failed_final_seal=copy.deepcopy(seal['inputs'][p]),prior_successful_seal=copy.deepcopy(prior['inputs'][p])) for p in paths}
assert exact_metadata_failure(seal,reg,prior,expected)
mutations=[
 ('successful_seal',lambda s,r,p,e:s.update(passed=True)),
 ('byte_change',lambda s,r,p,e:s['inputs'][paths[0]].update(sha256='b'*64)),
 ('missing_registration',lambda s,r,p,e:r['source_sha256'].__setitem__(paths[0],'b'*64)),
 ('inode_change',lambda s,r,p,e:s['inputs'][paths[0]]['stat_identity'].__setitem__(1,999)),
 ('size_change',lambda s,r,p,e:s['inputs'][paths[0]]['stat_identity'].__setitem__(2,999)),
 ('mtime_change',lambda s,r,p,e:s['inputs'][paths[0]]['stat_identity'].__setitem__(3,999)),
 ('no_ctime_change',lambda s,r,p,e:s['inputs'][paths[0]]['stat_identity'].__setitem__(4,200)),
 ('different_ctime_from_incident',lambda s,r,p,e:s['inputs'][paths[0]]['stat_identity'].__setitem__(4,202)),
 ('extra_seal_failure',lambda s,r,p,e:s['inputs'].__setitem__('/unexpected',copy.deepcopy(s['inputs'][paths[0]]))),
 ('one_failure_hidden',lambda s,r,p,e:s['inputs'][paths[0]].update(passed=True)),
 ('prior_failed',lambda s,r,p,e:p['inputs'][paths[0]].update(passed=False)),
 ('missing_incident_path',lambda s,r,p,e:e.pop(paths[0])),
]
rows=[]
for name,mutate in mutations:
 s,r,p,e=copy.deepcopy((seal,reg,prior,expected));mutate(s,r,p,e)
 try:exact_metadata_failure(s,r,p,e)
 except (AssertionError,KeyError):rows.append(dict(case=name,rejected=True))
 else:raise AssertionError(name)
out=D/'LSTM_retention_metadata_incident_01/development_guard_validation.json'
assert not out.exists()
write(out,dict(passed=True,positive_checks=1,negative_checks=len(rows),cases=rows,
 source_sha256={str(D/n):sha(D/n) for n in ['audit_lstm_failed_evaluation_01.py','validate_lstm_failed_evaluation_guard_01.py']},
 actual_raw_audit_performed=False,actual_native_or_STA_calls=0,queued=False,
 qualification='Only synthetic exception guards. Full request/raw STA/physical/actual byte audit remains unexecuted, requires original cohort and registered raw audit termination plus the shared serial slot. No existing result is newly admitted.'))
print(dict(passed=True,negative_checks=len(rows),actual_raw_audit_performed=False))
