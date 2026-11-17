"""Adversarial parser/identity checks; no graph, live STA, or native replay."""
import ast
import copy
import json
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from cp1r3_raw_admission_v1 import parse_request, parse_native, vector_digest, Audit
from observation_timing_identity_v2 import check

out = D/'CP1r3_raw_admission_validation_01'; out.mkdir(exist_ok=False)
passed = []; failures = []


def reject(name, fn):
    try:fn()
    except (AssertionError,ValueError,IndexError,KeyError):passed.append(name)
    else:failures.append(name)


role = dict(fixed_target_paths=False,removed_pins={'4':[1,2]},queries=[
    dict(net=4,pin=2,raw_criticality=.2),dict(net=4,pin=1,raw_criticality=.7)])
request = '1\n4 2 1 2\n0\n2\n4 2 0.2\n4 1 0.7\n'
expected = parse_request(request,role)
valid = ['MODE weighted_soft\n','ATTEMPT 4 2 1 1 1\n','QUERY 4 2 1 0.19 8 3 0.1\n',
         'ATTEMPT 4 1 1 1 1\n','QUERY 4 1 1 0.69 7 4 0.2\n','COMPLETE 1 2 2 0.4 occupancy_restored\n']
assert parse_native(valid,expected)['success']; passed.append('successful_complete_request')
failed = ['ATTEMPT 4 2 1 0 0\n','QUERY 4 2 0 0.19 8 3 0.1\n','COMPLETE 0 0 2 0.1 occupancy_restored\n']
assert not parse_native(failed,expected)['success']; passed.append('honest_failed_prefix_retained')
for name,text in [
    ('trailing_bytes',request+'unexpected\n'),('truncated_request',request.rsplit('\n',2)[0]+'\n'),
    ('query_reordered',request.replace('4 2 0.2\n4 1 0.7','4 1 0.7\n4 2 0.2')),
    ('criticality_changed',request.replace('0.7','0.6')),('criticality_nan',request.replace('0.7','nan')),
    ('duplicate_pin',request.replace('4 2 1 2','4 2 1 1')),('wrong_restore_scope',request.replace('4 2 1 2','4 2 1 3')),
    ('protected_path_unparsed',request.replace('\n0\n','\n1\n')),('query_count_wrong',request.replace('\n2\n','\n3\n'))]:
    reject(name,lambda text=text:parse_request(text,role))
for name,lines in [
    ('missing_complete',valid[:-1]),('rows_after_complete',valid+['MODE weighted_soft\n']),
    ('wrong_complete_count',valid[:-1]+['COMPLETE 1 1 2 0.4 occupancy_restored\n']),
    ('wrong_total_count',valid[:-1]+['COMPLETE 1 2 3 0.4 occupancy_restored\n']),
    ('failed_as_success',failed[:-1]+['COMPLETE 1 0 2 0.1 occupancy_restored\n']),
    ('success_as_failure',valid[:-1]+['COMPLETE 0 2 2 0.4 occupancy_restored\n']),
    ('missing_occupancy_restore',valid[:-1]+['COMPLETE 1 2 2 0.4 no_restore\n']),
    ('unknown_attempt_target',[valid[0],'ATTEMPT 7 1 1 1 1\n',*valid[2:]]),
    ('negative_time',[line.replace('0.4 occupancy','-0.4 occupancy') for line in valid]),
    ('wrong_query_order',[valid[0],valid[1],valid[4],valid[3],valid[2],valid[5]]),
    ('unknown_log_row',['UNKNOWN 3\n',*valid]),
    ('failure_followed_by_query',failed[:-1]+[valid[4],'COMPLETE 0 1 2 0.4 occupancy_restored\n'])]:
    reject(name,lambda lines=lines:parse_native(lines,expected))
v = dict(cpd_s=1.23456789e-8,setup={'a':.5},hold={'a':.2},endpoint_ids=[[1,2,'pin']],constraints_sha256='c')
assert vector_digest(v) == vector_digest(dict(v,endpoint_ids=[(1,2,'pin')]))
for key,value in [('cpd_s',v['cpd_s']+1e-18),('setup',{'a':.50000001}),('hold',{'a':-.1}),
                  ('endpoint_ids',[[1,3,'pin']]),('constraints_sha256','other')]:
    changed=copy.deepcopy(v);changed[key]=value
    assert vector_digest(v)!=vector_digest(changed);passed.append('vector_detects_'+key)
    assert not check(12.3457,12.3457,v,changed)['passed'];passed.append('exact_identity_rejects_'+key)
assert check(12.3457,12.3457,v,v)['passed'];passed.append('display_rounding_only')

# Existing completed native transaction metadata: inspect only small request,
# registration and schema files while another role owns the serial slot.
cohort = read(D/'cp1r3_distinct_input_cohort_01/plan.json')
case = Path(cohort['inputs'][0]['workspace'])/'native'; flow=case/'flow'
requests=0; source={}; schemas=[]
for path in sorted(flow.rglob('registration.json')):
    data=read(path)
    if 'roles' not in data:continue
    assert path.stat().st_size<1024**2;source[str(path)]=sha(path)
    for name,r in data['roles'].items():
        p=Path(r['request']);assert p.stat().st_size<1024**2
        parse_request(p.read_text(),r);source[str(p)]=sha(p);requests+=1
        wr=read(path.parent/name/'registration.json');assert all(k in wr for k in ['pid','start_ticks'])
        assert {'seed_order','domain_failure_release','crossing_reuse_enabled'} <= r.keys()
for path in sorted(flow.rglob('endpoint_vector.json')):
    state=path.parent;done=read(state/'completion.json');source[str(state/'completion.json')]=sha(state/'completion.json')
    assert done['passed'] and done['route_body_sha256'] and Path(done['run']).is_relative_to(state)
    if done['status']=='standalone_candidate_materialization_terminal':
        assert not (state/'input_seal.json').exists() and done['consumed_already_executed_worker_receipt']
        assert read(state/'runs/state/analysis_gate.json')['native_candidate_FULL_fresh_STA']
    else:
        assert read(state/'input_seal.json')['passed']
    schemas.append(done['status'])
script=D/'cp1r3_raw_admission_v1.py';tree=ast.parse(script.read_text());compile(tree,str(script),'exec')
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in
    ['Popen','run','system','execv','execve','unlink','rmtree','rename','replace'] for n in ast.walk(tree))
assert not failures,failures
write(out/'validation.json',dict(passed=True,checks=passed,completed_native_request_schemas_checked=requests,
    endpoint_state_metadata_schemas=dict(__import__('collections').Counter(schemas)),
    actual_full_raw_admission_performed=False,new_native_or_STA_calls=0,large_route_graph_STA_read=False,
    no_process_launcher_or_destructive_calls=True,
    source_sha256={str(script):sha(script),str(Path(__file__).resolve()):sha(Path(__file__).resolve()),**source},
    qualification='Adversarial complete-request/failed-prefix and exact-vector tests plus small existing schema checks. This is implementation validation, not scientific role admission. Actual raw-byte and STA audits wait for the original cohort and frozen-check replay.'))
print(dict(passed=True,checks=len(passed),actual_request_schemas=requests,state_schemas=len(schemas),full_raw_admission=False))
