"""Stage exact controller continuation hooks; never patch a frozen runtime."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

runtime=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
root=D/'robot_p1_prefix_recovery_01';assert not root.exists();root.mkdir();ext=root/'runtime_extension';ext.mkdir()
bootstrap="import os,sys\nsys.path.insert(0,os.environ['H3D_RECOVERY_RUNTIME'])\n"
revisions={}
def transform(name,target,replacements):
    original=(runtime/name).read_text();text=original;changes=[]
    for old,new in replacements:
        assert text.count(old)==1,(name,old)
        text=text.replace(old,new);changes.append([old,new])
    text=bootstrap+text;ast.parse(text)
    restored=text[len(bootstrap):]
    for old,new in reversed(changes):assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==original,'Recovery hooks changed unregistered algorithm bytes'
    (ext/target).write_text(text);revisions[target]=dict(parent=str(runtime/name),parent_sha256=sha(runtime/name),source_sha256=sha(ext/target),replacements=changes,reversible_to_parent=True)

transform('run_unified_resource_repair_v1.py','resume_resource_controller.py',[
 ('from controller_runtime import package_files,admit_controller','from controller_runtime import package_files,admit_controller\nfrom recovery_prefix_v1 import Prefix'),
 ("p=argparse.ArgumentParser();", "p=argparse.ArgumentParser();p.add_argument('--resume-plan',type=Path,required=True);"),
 ('current=initial;steps=[];attempts=[];costs=[];seen=set();stop=None',"prefix=Prefix(a.resume_plan,b)\ncurrent,steps,attempts=prefix.initialize_controller(b,initial,anchor,limits,a)\ncosts=[];seen=set();stop=None"),
 ("cmd=[sys.executable,str(D/backend),'--batch',str(tx)]", "cmd=[sys.executable,str(D/backend),'--batch',str(tx)]\n if backend=='run_serial_lazy_resource_transactions_stream_v1.py':cmd=[sys.executable,str(Path(__file__).with_name('resume_resource_transaction.py')),'--batch',str(tx),'--resume-plan',str(a.resume_plan.resolve())]"),
 ("cuts=select(current,cache,rd/'selection')", "cuts=prefix.selection(current,cache,rd/'selection',select);reused_selection=prefix.reused_selection"),
 ("print(dict(accepted_steps=len(steps),CPD_ns=v['cpd_s']*1e9),flush=True)", "prefix.finish(b)\nprint(dict(accepted_steps=len(steps),CPD_ns=v['cpd_s']*1e9),flush=True)")])
transform('run_serial_lazy_resource_transactions_stream_v1.py','resume_resource_transaction.py',[
 ('from phase_supervision import run_phase','from phase_supervision import run_phase\nfrom recovery_prefix_v1 import consume_completed_worker'),
 ("p=argparse.ArgumentParser();", "p=argparse.ArgumentParser();p.add_argument('--resume-plan',type=Path,required=True);"),
 ('def invoke(script,args,tag):', "def invoke(script,args,tag):\n replay_start=time.monotonic()\n if consume_completed_worker(a.resume_plan,b,tag,args):\n  costs.append(dict(tag=tag,status='recovered_completed_native_no_execution',complete_process_seconds=time.monotonic()-replay_start,native_calls_new=0));write(b/'process_costs.json',costs);return True"),
 ('native_reused=hit is not None,native_calls_new=0 if hit is not None else 1,native_core_seconds_new=0. if hit is not None else audit[\'native_transaction_seconds\'],reused_creation_native_core_seconds=audit[\'native_transaction_seconds\'] if hit is not None else None', "native_reused=hit is not None or (b/(name+'_native_recovery.json')).exists(),native_calls_new=0 if hit is not None or (b/(name+'_native_recovery.json')).exists() else 1,native_core_seconds_new=0. if hit is not None or (b/(name+'_native_recovery.json')).exists() else audit['native_transaction_seconds'],reused_creation_native_core_seconds=audit['native_transaction_seconds'] if hit is not None or (b/(name+'_native_recovery.json')).exists() else None")])
for name in ['recovery_prefix_v1.py','run_robot_prefix_recovery_01.py']:
    src=D/name;assert src.exists();ast.parse(src.read_text());shutil.copy2(src,ext/name)
write(root/'controller_revision.json',dict(passed=True,baseline_runtime=str(runtime),revisions=revisions,
    algorithm_remainder_byte_identical=True,root_limits_acceptance_and_terminal_rules_changed=False,
    qualification='Only explicit prefix initialization, completed current-selector/native-worker consumption, cost labels and backend routing are added. Physical/domain audit and candidate FULL/STA continue through frozen workers. Original files and all controller loop/acceptance bodies remain unchanged.'))
print(dict(staged=str(ext),files=4,native_calls_new=0))
