"""Build full-flow prefix dispatch beside frozen and registered robot sources."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
root=D/'interrupted_flow_recovery_01';root.mkdir(exist_ok=False);ext=root/'runtime_extension';ext.mkdir()
previous=D/'interrupted_stage_adapter_01';assert read(previous/'validation.json')['passed']
for p in (previous/'runtime_extension').glob('*.py'):shutil.copy2(p,ext/p.name)
shutil.copy2(D/'same_actor_timing_prefix_v1.py',ext/'same_actor_timing_prefix_v1.py')
revisions={};bootstrap="import os,sys\nsys.path.insert(0,os.environ['H3D_RECOVERY_RUNTIME'])\n"
def transform(source,target,replacements,prefix=''):
    original=Path(source).read_text();text=original
    for old,new in replacements:
        assert text.count(old)==1,(str(source),old);text=text.replace(old,new)
    text=prefix+text;ast.parse(text);restored=text[len(prefix):]
    for old,new in reversed(replacements):
        assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==original
    (ext/target).write_text(text)
    revisions[target]=dict(parent=str(source),parent_sha256=sha(source),source_sha256=sha(ext/target),bootstrap=prefix,replacements=replacements,reversible_to_parent=True)

robot=read(D/'robot_p1_prefix_recovery_01/controller_revision.json')['revisions']['resume_resource_controller.py']
replacements=[tuple(x) for x in robot['replacements']]
replacements=[(a,b.replace('from recovery_prefix_v1 import Prefix','from same_actor_resource_prefix_v2 import Prefix')) for a,b in replacements]
transform(parent/'run_unified_resource_repair_v1.py','resume_resource_controller.py',replacements,bootstrap)
old="audit=read(self.plan['existing_trace_audit']);assert audit['passed'] and audit['existing_reload_exact_identity']['passed']\n        self.evidence.verify(audit['source_sha256'])"
new="""audit_path=Path(self.plan['stage_audit']);summary_path=Path(self.plan['stage_audit_summary'])
        self.evidence.bind(audit_path,self.plan['stage_audit_sha256']);self.evidence.bind(summary_path,self.plan['stage_audit_summary_sha256'])
        audit=read(audit_path);summary=read(summary_path)
        assert audit['passed'] and audit in summary['rows']
        assert (audit['pair'],audit['arm'])==(self.plan['pair'],self.plan['arm'])
        assert Path(audit['source_state']).resolve()==Path(self.current['state']).resolve()
        assert audit['stages']['native_source_control']['exact_observation']['passed']"""
transform(D/'recovery_prefix_v1.py','same_actor_resource_prefix_v2.py',[(old,new)])
assertion="assert not (a.resume_from or a.reuse_plan or a.reuse_portfolio or a.reuse_native_batch or a.reuse_query_batch or a.reuse_exchange),'Complete flow accepts no external trajectory/query/candidate history'"
transform(parent/'run_complete_flow_critical_portfolio_stream_v1.py','resume_timing_controller.py',[
    ('from timing_runtime import admit_timing','from timing_runtime import admit_timing\nfrom same_actor_timing_prefix_v1 import TimingPrefix'),
    ('p=argparse.ArgumentParser();',"p=argparse.ArgumentParser();p.add_argument('--resume-plan',type=Path,required=True);"),
    ('bindings={str(p):sha(p) for p in files};',"files += [a.resume_plan.resolve()]\nbindings={str(p):sha(p) for p in files};"),
    (assertion,"timing_prefix=TimingPrefix(a.resume_plan,initial,anchor,fixed_limits,a)"),
    ('command=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic();status=\'completed\'',"command=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic();status='completed'\n if script=='run_registered_independent_stream_transactions_v1.py':command=[sys.executable,str(Path(__file__).with_name('resume_timing_transaction.py')),'--resume-plan',str(a.resume_plan.resolve()),*map(str,args)]"),
    ("print(dict(accepted_steps=len(accepted),attempted_proposals=len(attempts)","timing_prefix.finish(b)\nprint(dict(accepted_steps=len(accepted),attempted_proposals=len(attempts)")],bootstrap)

# Seal replay evidence in each transaction completion, in addition to its
# ordinary registration/progress/decisions. Parent bodies remain reversible.
for name in ['resume_resource_transaction.py','resume_timing_transaction.py']:
    transform(previous/'runtime_extension'/name,name,[('paths=[',"paths=[*b.glob('*_stage_reuse.json'),*b.glob('stage_reuse_*.json'),")])
write(root/'dispatch_revision.json',dict(passed=True,revisions=revisions,
    transaction_parent_revision=str(previous/'revision.json'),algorithm_bodies_reversible=True,
    original_robot_sources_and_frozen_versions_changed=False,new_native_calls=0,
    qualification='Resource/timing dispatch and same-prefix verification only; requires the actual serial audit and per-case source/plan seal before execution. Full-flow assembly and activation are separate.'))
print(dict(passed=True,dispatch_sources=len(revisions),new_native_calls=0))
