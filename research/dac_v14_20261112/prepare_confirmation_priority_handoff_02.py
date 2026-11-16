"""Prepare a scheduling-only handoff; leave every fixed experiment source intact."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'confirmation_priority_handoff_02';root.mkdir(exist_ok=False);scripts=root/'wrappers';scripts.mkdir()
stages=[
    ('confirmation_release_cp1r3_01','queue_confirmation_release_cp1r3_01.py','BNN_interleaved_timing_03/queue',
        [("done['status']=='registered_empty_query_replay_terminal'","done['status']=='registered_interleaved_timing_terminal'"),
         ('waiting_for_registered_empty_query_fixture_validation','waiting_for_original_balanced_BNN_timing')]),
    ('cp1r3_distinct_input_cohort_01','queue_cp1r3_distinct_input_cohort_01.py','confirmation_release_cp1r3_01/queue_priority_02',
        [('from cp1r3_confirmation_cohort_v1 import ROOT,execute','from cp1r3_priority_cohort_02 import ROOT,execute'),
         ("previous['status']=='registered_development_recovery_terminal'","previous['status']=='registered_CP1r3_packaging_terminal'"),
         ('waiting_for_registered_robot_prefix_recovery','waiting_for_priority_CP1r3_packaging')]),
    ('interrupted_stage_reconciliation_01','queue_interrupted_stage_reconciliation_01.py','cp1r3_distinct_input_cohort_01/queue_priority_02',[]),
    ('robot_p1_prefix_recovery_01','queue_robot_prefix_recovery_01.py','interrupted_stage_reconciliation_01/queue_priority_02',
        [("assert previous['passed'] and previous['status']=='registered_CP1r3_packaging_terminal'", "assert previous['status'] in ['registered_readonly_stage_audit_terminal','reconciliation_required']"),
         ('waiting_for_registered_CP1r3_preparation','waiting_for_priority_readonly_four_arm_audit')]),
    ('interrupted_flow_recovery_01','queue_interrupted_full_flow_recovery_01.py','robot_p1_prefix_recovery_01/queue_priority_02',[]),
    ('empty_query_patch_validation_01','queue_empty_query_patch_validation_01.py','interrupted_flow_recovery_01/queue_priority_02',
        [("assert done['passed'] and done['status']=='registered_interleaved_timing_terminal'", "assert done['status']=='registered_four_arm_recovery_terminal'"),
         ('waiting_for_registered_BNN_interleaved_timing03','waiting_for_priority_confirmation_and_recoveries')]),
]
forbidden={
    'confirmation_release_cp1r3_01':['completion.json'],
    'cp1r3_distinct_input_cohort_01':['plan.json','activation_cost.json','comparison.json'],
    'interrupted_stage_reconciliation_01':['completion.json'],
    'robot_p1_prefix_recovery_01':['flow','measurement','supervision.json','result.json'],
    'interrupted_flow_recovery_01':['results.json'],
    'empty_query_patch_validation_01':['completion.json'],
}
revisions={};nodes=[];protected={}
admin=D/'cp1r3_confirmation_cohort_v1.py';original=admin.read_text();old="ROOT/'queue/status.json'";new="ROOT/'queue_priority_02/status.json'";count=original.count(old);assert count==2
target=D/'cp1r3_priority_cohort_02.py';assert not target.exists();target.write_text(original.replace(old,new));ast.parse(target.read_text())
assert target.read_text().replace(new,old)==original
revisions[str(target)]=dict(parent=str(admin),parent_sha256=sha(admin),sha256=sha(target),replacements=[[old,new,count]],only_status_destination_changed=True)
protected[str(admin)]=sha(admin)
for batch,filename,pred,extra in stages:
    source=D/filename;text=source.read_text();changes=[]
    token="q=ROOT/'queue'" if "q=ROOT/'queue'" in text else "q=root/'queue'"
    replacements=[(token,token.replace("'queue'","'queue_priority_02'"))]
    if 'pred=Path(protocol[\'predecessor\'])' in text:oldpred="pred=Path(protocol['predecessor'])"
    elif 'pred=Path(plan[\'predecessor\'])' in text:oldpred="pred=Path(plan['predecessor'])"
    else:oldpred="predecessor=Path(plan['predecessor'])"
    var=oldpred.split('=')[0];replacements.append((oldpred,var+"=D/"+repr(pred)))
    replacements+=extra
    for old,new in replacements:
        assert text.count(old)==1,(filename,old);text=text.replace(old,new);changes.append([old,new,1])
    # Bind the new administration sources in addition to the original fixed
    # protocol. No algorithm/configuration source in that protocol is edited.
    tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bound' for t in n.targets))
    lines=text.splitlines(keepends=True);position=sum(len(line) for line in lines[:node.end_lineno])
    added="bound.update({str(D/'confirmation_priority_handoff_02/plan.json'):sha(D/'confirmation_priority_handoff_02/plan.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())"+( ",str(D/'cp1r3_priority_cohort_02.py'):sha(D/'cp1r3_priority_cohort_02.py')" if batch=='cp1r3_distinct_input_cohort_01' else '')+"})\n"
    text=text[:position]+added+text[position:]
    bootstrap="from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[2]))\n"
    text=bootstrap+text;ast.parse(text)
    wrapper=scripts/filename;wrapper.write_text(text)
    restored=text[len(bootstrap):].replace(added,'',1)
    for old,new,count in reversed(changes):assert restored.count(new)==count;restored=restored.replace(new,old,count)
    assert restored==source.read_text()
    revisions[str(wrapper)]=dict(parent=str(source),parent_sha256=sha(source),sha256=sha(wrapper),replacements=changes,added_source_binding=added,bootstrap=bootstrap,reversible_to_parent=True)
    q=D/batch/'queue';reg=read(q/'registration.json');status=read(q/'status.json');live=process_identity(reg['pid'])
    assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks'] and status['status'].startswith('waiting')
    assert not (q/'completion.json').exists() and not (D/batch/'queue_priority_02').exists()
    snapshot=root/'old_waiters'/batch;snapshot.mkdir(parents=True)
    for name in ['registration.json','status.json']:(snapshot/name).write_bytes((q/name).read_bytes())
    protected[str(source)]=sha(source);protected[str(q/'registration.json')]=sha(q/'registration.json')
    for name in ['protocol.json','plan.json']:
        if (D/batch/name).exists():protected[str(D/batch/name)]=sha(D/batch/name)
    nodes.append(dict(batch=batch,old_queue=str(q),new_queue=str(D/batch/'queue_priority_02'),old_script=str(source),wrapper=str(wrapper),
        pid=reg['pid'],start_ticks=reg['start_ticks'],old_registration_sha256=sha(q/'registration.json'),predecessor=str(D/pred),
        forbidden_paths=[str(D/batch/name) for name in forbidden[batch]],original_status_snapshot=str(snapshot/'status.json')))
for name in ['prepare_confirmation_release_cp1r3.py','activate_cp1r3_distinct_input_cohort_01.py','package_cp1r3_public_source_01.py',
    'seal_cp1r3_distinct_cohort_outcomes_01.py','admit_interrupted_flow_recovery_01.py','run_interrupted_full_flow_recovery_v1.py','audit_interrupted_stages_01.py']:
    protected[str(D/name)]=sha(D/name)
active=D/'BNN_interleaved_timing_03/queue';reg=read(active/'registration.json');p=process_identity(reg['pid']);assert p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
write(root/'plan.json',dict(passed=True,status='prepared_scheduling_handoff_not_yet_applied',public_evidence_base='9734eee',preserve_followup='279bdb4',
    reason='User explicitly prioritizes already registered CP1r3 three-input/six-role confirmation before development recovery. Preserve running balanced BNN without interruption.',
    active_predecessor=str(active),active_predecessor_identity=p,stages=nodes,revisions=revisions,protected_source_sha256=protected,
    independent_input_interpretation='Two distinct LSTM/DLA-like.small circuit/netlists not yet confirmed by current method, plus an already known eltwise circuit on an already known SB-only architecture with an actual different placement. Third source is neither a new circuit nor a new architecture family; six roles are not six samples. Actual byte/root admission still required.',
    unchanged='All original experiment protocols, selected inputs, fixed CP1r3 algorithm/version/configuration/acceptance rules, source packages and actual method scripts. Only predecessor scheduling, queue/status destinations and administration provenance change.',
    actual_native_calls_new=0,actual_execution_handoff_applied=False,research_complete=False))
print(dict(passed=True,waiting_owners=len(nodes),new_wrapper_sources=7,algorithm_or_input_changes=False))
