"""Check new bookkeeping boundaries against real old timeouts, without native work."""
import hashlib,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from cp1r3_confirmation_cohort_v1 import classify_actual_initial_failure,verify_copy_source,InputAdmissionError

root=D/'cp1r3_cohort_administration_validation_01';root.mkdir(exist_ok=False)
revision=read(D/'cp1r3_cohort_administration_revision_01.json');text=Path(revision['source']).read_text()
assert sha(revision['source'])==revision['source_sha256']
for old,new in reversed(revision['changes']):assert text.count(new)==1;text=text.replace(new,old)
assert text==Path(revision['parent']).read_text() and sha(revision['parent'])==revision['parent_sha256']
cohort=D/'cp1r2_cross_circuit_cohort_01';previous=read(cohort/'tpu_ws_results.json');files=[Path(__file__).resolve(),D/'cp1r3_cohort_administration_revision_01.json',Path(revision['source'])]
for arm,row in previous.items():
    run=Path(row['case'])/'flow/resource_flow/initial/runs/state';m=read(run/'manifest.json')
    assert m['execution_status']=='timeout' and classify_actual_initial_failure(m,(run/'stdout.log').read_text())=='initial_routing_execution_timeout'
    assert classify_actual_initial_failure(m,(run/'stdout.log').read_text(),True)!='initial_routing_execution_timeout'
    assert row['quality'] is None;files += [run/'manifest.json',run/'stdout.log']
with tempfile.TemporaryDirectory(prefix='cp1r3-cohort-admission-') as folder:
    p=Path(folder)/'bytes';p.write_bytes(b'exact selected input\n');record=dict(bytes=p.stat().st_size,sha256=sha(p));verify_copy_source(p,record)
    p.write_bytes(b'changed selected input\n')
    try:verify_copy_source(p,record)
    except InputAdmissionError:pass
    else:raise AssertionError('Changed source was admitted')
    p.unlink()
    try:verify_copy_source(p,record)
    except InputAdmissionError:pass
    else:raise AssertionError('Missing source was admitted')
names=['activate_cp1r3_distinct_input_cohort_01.py','package_cp1r3_public_source_01.py','queue_cp1r3_distinct_input_cohort_01.py','seal_cp1r3_distinct_cohort_outcomes_01.py']
for name in names:compile((D/name).read_text(),name,'exec');files.append(D/name)
write(root/'completion.json',dict(passed=True,parent_administration_exact_reversible=True,actual_previous_timeout_roles=2,
    already_legal_root_not_reclassified_initial_timeout=True,changed_or_missing_input_rejected=True,
    source_syntax_checked=True,new_native_calls=0,actual_CP1r3_admission_or_execution=False,
    source_sha256={str(f):sha(f) for f in files},qualification='Bookkeeping/protocol preparation tests only. Actual CP1r3 source, public reconstruction, fixed checker, physical provisioning and native outcomes remain deferred; no confirmation or QoR claim.'))
print(dict(passed=True,actual_old_timeouts=2,source_changes_are_administration_only=True,new_native_calls=0))
