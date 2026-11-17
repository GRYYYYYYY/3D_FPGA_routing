"""Insert supplemental verification before four unexecuted development waiters."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from confirmation_priority_waiter_guard_02 import check
from seed_census_analysis_pool_v2 import process_identity

root=D/'confirmation_priority_handoff_04';assert not root.exists();root.mkdir();(root/'wrappers').mkdir()
old=read(D/'confirmation_priority_handoff_03/plan.json');nodes=[];revisions={}
protected=dict(old['protected_source_sha256'])
active=D/'cp1r3_distinct_input_cohort_01/queue_priority_02';ar=read(active/'registration.json');p=process_identity(ar['pid'])
assert p and p['state']!='Z' and p['start_ticks']==ar['start_ticks'] and not (active/'completion.json').exists()
for stage in old['stages']:
    source=Path(stage['wrapper']);q=Path(stage['new_queue']);reg=read(q/'registration.json')
    target=root/'wrappers'/source.name;text=source.read_text();original=text
    replacements=[("'queue_priority_03'","'queue_priority_04'"),('/queue_priority_03','/queue_priority_04')]
    for a,b in replacements:text=text.replace(a,b)
    if stage['batch']=='interrupted_stage_reconciliation_01':
        a="pred=D/'CP1r3_supplemental_verifier_01/queue_priority_04'";b="pred=D/'CP1r3_raw_admission_01/queue_priority_04'";assert text.count(a)==1;text=text.replace(a,b);replacements.append((a,b))
    added="bound.update({str(D/'confirmation_priority_handoff_04/plan.json'):sha(D/'confirmation_priority_handoff_04/plan.json')})\n"
    token="write(q/'registration.json'";assert text.count(token)==1;text=text.replace(token,added+token)
    ast.parse(text);compile(text,str(target),'exec');target.write_text(text)
    # Verify exact scheduling-only source restoration.
    restored=text.replace(added,'',1)
    for a,b in reversed(replacements):restored=restored.replace(b,a)
    assert restored==original
    newq=D/stage['batch']/'queue_priority_04'
    pred=('CP1r3_raw_admission_01/queue_priority_04' if not nodes else nodes[-1]['batch']+'/queue_priority_04')
    node=dict(batch=stage['batch'],old_queue=str(q),new_queue=str(newq),old_script=str(source),wrapper=str(target),
        pid=reg['pid'],start_ticks=reg['start_ticks'],old_registration_sha256=sha(q/'registration.json'),
        predecessor=str(D/pred),forbidden_paths=stage['forbidden_paths'])
    check(node);nodes.append(node);protected[str(source)]=sha(source)
    revisions[str(target)]=dict(parent=str(source),parent_sha256=sha(source),sha256=sha(target),only_scheduling_changed=True)
    backup=root/'old_waiters'/stage['batch'];backup.mkdir(parents=True)
    for name in ['registration.json','status.json']:(backup/name).write_bytes((q/name).read_bytes())
supp=D/'queue_cp1r3_raw_admission_priority_04.py';compile(supp.read_text(),str(supp),'exec')
protected[str(active/'registration.json')]=sha(active/'registration.json')
sq=D/'CP1r3_supplemental_verifier_01/queue_priority_03';sr=read(sq/'registration.json');sp=process_identity(sr['pid'])
assert sp and sp['state']!='Z' and sp['start_ticks']==sr['start_ticks'] and not (sq/'completion.json').exists()
protected[str(sq/'registration.json')]=sha(sq/'registration.json')
protected.update(sr['source_sha256'])
write(root/'plan.json',dict(stages=nodes,revisions=revisions,protected_source_sha256=protected,
    active_predecessor=str(active),active_predecessor_identity=p,active_supplemental_identity=sp,
    supplemental_wrapper=str(supp),supplemental_sha256=sha(supp),
    reason='Complete remaining raw admission immediately after the already queued original-check supplement, before historical recovery. Preserve both original cohort and supplemental owners.',
    algorithm_input_and_running_cohort_unchanged=True,new_native_calls_by_handoff=0))
assert all(sha(f)==h for f,h in protected.items())
write(root/'validation.json',dict(passed=True,actual_waiters_guarded=4,exact_wrapper_reverse_checks=4,
    original_cohort_pid=p['pid'],original_cohort_start_ticks=p['start_ticks'],
    supplemental_source_compiles=True,old_waiters_have_no_children_or_method_outputs=True,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'),str(supp):sha(supp),**{k:v['sha256'] for k,v in revisions.items()}}))
print(dict(prepared=True,waiters=4,active_cohort_unchanged=True,supplemental_first=True))
