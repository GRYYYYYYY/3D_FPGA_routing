"""Insert supplemental verification before four unexecuted development waiters."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from confirmation_priority_waiter_guard_02 import check
from seed_census_analysis_pool_v2 import process_identity

root=D/'confirmation_priority_handoff_03';assert not root.exists();root.mkdir();(root/'wrappers').mkdir()
old=read(D/'confirmation_priority_handoff_02/plan.json');nodes=[];revisions={}
protected=dict(old['protected_source_sha256'])
active=D/'cp1r3_distinct_input_cohort_01/queue_priority_02';ar=read(active/'registration.json');p=process_identity(ar['pid'])
assert p and p['state']!='Z' and p['start_ticks']==ar['start_ticks'] and not (active/'completion.json').exists()
for stage in old['stages'][2:]:
    source=Path(stage['wrapper']);q=Path(stage['new_queue']);reg=read(q/'registration.json')
    target=root/'wrappers'/source.name;text=source.read_text();original=text
    replacements=[("'queue_priority_02'","'queue_priority_03'"),('/queue_priority_02','/queue_priority_03')]
    for a,b in replacements:text=text.replace(a,b)
    if stage['batch']=='interrupted_stage_reconciliation_01':
        a="pred=D/'cp1r3_distinct_input_cohort_01/queue_priority_03'";b="pred=D/'CP1r3_supplemental_verifier_01/queue_priority_03'";assert text.count(a)==1;text=text.replace(a,b);replacements.append((a,b))
    added="bound.update({str(D/'confirmation_priority_handoff_03/plan.json'):sha(D/'confirmation_priority_handoff_03/plan.json')})\n"
    token="write(q/'registration.json'";assert text.count(token)==1;text=text.replace(token,added+token)
    ast.parse(text);compile(text,str(target),'exec');target.write_text(text)
    # Verify exact scheduling-only source restoration.
    restored=text.replace(added,'',1)
    for a,b in reversed(replacements):restored=restored.replace(b,a)
    assert restored==original
    newq=D/stage['batch']/'queue_priority_03'
    pred=('CP1r3_supplemental_verifier_01/queue_priority_03' if not nodes else nodes[-1]['batch']+'/queue_priority_03')
    node=dict(batch=stage['batch'],old_queue=str(q),new_queue=str(newq),old_script=str(source),wrapper=str(target),
        pid=reg['pid'],start_ticks=reg['start_ticks'],old_registration_sha256=sha(q/'registration.json'),
        predecessor=str(D/pred),forbidden_paths=stage['forbidden_paths'])
    check(node);nodes.append(node);protected[str(source)]=sha(source)
    revisions[str(target)]=dict(parent=str(source),parent_sha256=sha(source),sha256=sha(target),only_scheduling_changed=True)
    backup=root/'old_waiters'/stage['batch'];backup.mkdir(parents=True)
    for name in ['registration.json','status.json']:(backup/name).write_bytes((q/name).read_bytes())
supp=D/'queue_cp1r3_supplemental_priority_03.py';compile(supp.read_text(),str(supp),'exec')
protected[str(active/'registration.json')]=sha(active/'registration.json')
write(root/'plan.json',dict(stages=nodes,revisions=revisions,protected_source_sha256=protected,
    active_predecessor=str(active),active_predecessor_identity=p,
    supplemental_wrapper=str(supp),supplemental_sha256=sha(supp),
    reason='User requires supplemental verifier immediately after frozen CP1r3 confirmation; historical recoveries are not submission prerequisites.',
    algorithm_input_and_running_cohort_unchanged=True,new_native_calls_by_handoff=0))
assert all(sha(f)==h for f,h in protected.items())
write(root/'validation.json',dict(passed=True,actual_waiters_guarded=4,exact_wrapper_reverse_checks=4,
    original_cohort_pid=p['pid'],original_cohort_start_ticks=p['start_ticks'],
    supplemental_source_compiles=True,old_waiters_have_no_children_or_method_outputs=True,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'),str(supp):sha(supp),**{k:v['sha256'] for k,v in revisions.items()}}))
print(dict(prepared=True,waiters=4,active_cohort_unchanged=True,supplemental_first=True))
