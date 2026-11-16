"""Add replay guards to resource/timing transactions; preserve algorithm bodies."""
import ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,write,sha

runtime=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
root=D/'interrupted_stage_adapter_01';root.mkdir(exist_ok=False)
ext=root/'runtime_extension';ext.mkdir()
bootstrap="import os,sys\nsys.path.insert(0,os.environ['H3D_RECOVERY_RUNTIME'])\n"
changes={}
def transform(parent,target,replacements):
    original=(runtime/parent).read_text();text=original
    for old,new in replacements:
        assert text.count(old)==1,(parent,old)
        text=text.replace(old,new)
    text=bootstrap+text;ast.parse(text)
    restored=text[len(bootstrap):]
    for old,new in reversed(replacements):
        assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==original
    (ext/target).write_text(text)
    changes[target]=dict(parent=str(runtime/parent),parent_sha256=sha(runtime/parent),
        source_sha256=sha(ext/target),replacements=replacements,reversible_to_parent=True)

common=[
    ('from phase_supervision import run_phase','from phase_supervision import run_phase\nfrom same_actor_stage_reuse_v1 import StageReuse'),
    ('p=argparse.ArgumentParser();',"p=argparse.ArgumentParser();p.add_argument('--resume-plan',type=Path,required=True);"),
    ('def invoke(script,args,tag):',"stage_reuse=StageReuse(a.resume_plan,b)\ndef invoke(script,args,tag):\n replay_started=time.monotonic()\n if stage_reuse.consume(script,args,tag):\n  costs.append(dict(tag=tag,status='audited_same_actor_stage_reused',complete_process_seconds=time.monotonic()-replay_started,native_calls_new=0,creation_cost_borrowed=False));write(b/'process_costs.json',costs);return True"),
    ("assert all(sha(path)==h for path,h in read(b/'execution_registration.json')['source_sha256'].items())", "assert all(sha(path)==h for path,h in read(b/'execution_registration.json')['source_sha256'].items())\nstage_reuse.finish()"),
]
old="native_reused=hit is not None,native_calls_new=0 if hit is not None else 1,native_core_seconds_new=0. if hit is not None else audit['native_transaction_seconds'],reused_creation_native_core_seconds=audit['native_transaction_seconds'] if hit is not None else None"
flag="(b/(name+'_native_stage_reuse.json')).exists()"
new=f"native_reused=hit is not None or {flag},native_calls_new=0 if hit is not None or {flag} else 1,native_core_seconds_new=0. if hit is not None or {flag} else audit['native_transaction_seconds'],reused_creation_native_core_seconds=audit['native_transaction_seconds'] if hit is not None or {flag} else None"
transform('run_serial_lazy_resource_transactions_stream_v1.py','resume_resource_transaction.py',common+[(old,new)])
transform('run_registered_independent_stream_transactions_v1.py','resume_timing_transaction.py',common)
for name in ['same_actor_stage_reuse_v1.py','recovery_prefix_v1.py']:
    ast.parse((D/name).read_text());shutil.copy2(D/name,ext/name)
write(root/'revision.json',dict(passed=True,bootstrap=bootstrap,revisions=changes,
    algorithm_remainder_byte_identical=True,acceptance_selection_and_stage_order_changed=False,
    requires_actual_serial_audit_and_sealed_per_case_admission=True,new_native_calls=0,
    qualification='Development transaction adapters only. Hooks consume exact same-actor audited native/physical/domain stages, reject partial candidate STA and permit genuinely unexecuted work. All frozen audit/STA/acceptance bodies remain. No full-flow dispatch, queue activation or behavior-equivalence claim yet.'))
print(dict(passed=True,transaction_adapters=2,new_native_calls=0,full_flow_dispatch_implemented=False))
