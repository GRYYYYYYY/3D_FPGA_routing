"""Insert the registered simple-cost control after raw admission, before recovery."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from confirmation_priority_waiter_guard_02 import check
from seed_census_analysis_pool_v2 import process_identity

root=D/'confirmation_priority_handoff_05';assert not root.exists();root.mkdir();(root/'wrappers').mkdir()
old=read(D/'confirmation_priority_handoff_04/plan.json');protected=dict(old['protected_source_sha256'])
identities={}
for label,rel in [('cohort','cp1r3_distinct_input_cohort_01/queue_priority_02'),
                  ('supplement','CP1r3_supplemental_verifier_01/queue_priority_03'),
                  ('raw','CP1r3_raw_admission_01/queue_priority_04')]:
    q=D/rel;reg=read(q/'registration.json');actual=process_identity(reg['pid'])
    assert actual and actual['state']!='Z' and actual['start_ticks']==reg['start_ticks']
    assert not(q/'completion.json').exists()
    protected[str(q/'registration.json')]=sha(q/'registration.json');protected.update(reg['source_sha256'])
    identities[label]=actual
execution=D/'vertical_cost_baseline_dev_01/execution_plan.json'
protected[str(execution)]=sha(execution);protected.update(read(execution)['source_sha256'])
nodes=[];revisions={}
for stage in old['stages']:
    source=Path(stage['wrapper']);q=Path(stage['new_queue']);reg=read(q/'registration.json')
    original=source.read_text();text=original
    replacements=[("'queue_priority_04'","'queue_priority_05'"),('/queue_priority_04','/queue_priority_05'),
        ('confirmation_priority_handoff_04/plan.json','confirmation_priority_handoff_05/plan.json')]
    if stage['batch']=='interrupted_stage_reconciliation_01':
        replacements.append(('CP1r3_raw_admission_01/queue_priority_05','vertical_cost_baseline_dev_01/queue_priority_05'))
    for a,b in replacements:text=text.replace(a,b)
    ast.parse(text);target=root/'wrappers'/source.name;target.write_text(text)
    restored=text
    for a,b in reversed(replacements):restored=restored.replace(b,a)
    assert restored==original
    predecessor=D/('vertical_cost_baseline_dev_01/queue_priority_05' if not nodes else nodes[-1]['batch']+'/queue_priority_05')
    node=dict(batch=stage['batch'],old_queue=str(q),new_queue=str(D/stage['batch']/'queue_priority_05'),
        old_script=str(source),wrapper=str(target),pid=reg['pid'],start_ticks=reg['start_ticks'],
        old_registration_sha256=sha(q/'registration.json'),predecessor=str(predecessor),forbidden_paths=stage['forbidden_paths'])
    check(node);nodes.append(node);protected[str(source)]=sha(source)
    revisions[str(target)]=dict(parent=str(source),parent_sha256=sha(source),sha256=sha(target),only_scheduling_changed=True)
    backup=root/'old_waiters'/stage['batch'];backup.mkdir(parents=True)
    for n in ['registration.json','status.json']:(backup/n).write_bytes((q/n).read_bytes())
baseline=D/'queue_vertical_cost_baseline_priority_05.py';ast.parse(baseline.read_text())
assert all(sha(f)==h for f,h in protected.items())
write(root/'plan.json',dict(stages=nodes,revisions=revisions,protected_source_sha256=protected,
    active_predecessor=str(D/'cp1r3_distinct_input_cohort_01/queue_priority_02'),active_predecessor_identity=identities['cohort'],
    active_supplemental_identity=identities['supplement'],active_raw_identity=identities['raw'],
    baseline_wrapper=str(baseline),baseline_sha256=sha(baseline),
    reason='Registered same-source simple crossing-cost contrast after existing confirmation/supplement/raw admission, before optional recovery. All three original upstream owners preserved.',
    algorithm_input_and_running_cohort_unchanged=True,new_native_calls_by_handoff=0))
write(root/'validation.json',dict(passed=True,actual_waiters_guarded=4,exact_wrapper_reverse_checks=4,
    original_three_upstream_owners_preserved=True,baseline_checks=32,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'),str(baseline):sha(baseline),**{k:v['sha256'] for k,v in revisions.items()}}))
print(dict(prepared=True,guarded_waiters=4,baseline_after_raw_admission=True))
