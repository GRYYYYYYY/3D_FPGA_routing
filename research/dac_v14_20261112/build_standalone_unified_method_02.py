"""Protect all original serial method phase trees, including detached native workers."""
import argparse,ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'standalone_unified_method_dev_02');a=p.parse_args()
base=D/'standalone_unified_method_dev_01';out=a.output.resolve();shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'unified_method_v1_manifest.json')
shutil.copy2(D/'portable_phase_supervision_v1.py',out/'phase_supervision.py')
s=(D/'supervise_component_process_v1.py').read_text()
s=s.replace("p.add_argument('--seconds',type=float,required=True)","p.add_argument('--seconds',type=float)")
s=s.replace('assert a.seconds>0 and not a.receipt.exists()',"assert (a.seconds is None or a.seconds>0) and not a.receipt.exists()")
s=s.replace('if time.monotonic()-start>=a.seconds:', 'if a.seconds is not None and time.monotonic()-start>=a.seconds:')
s=s.replace(" start=time.monotonic();child=subprocess.Popen",''' def interrupted(signum,frame):
  raise InterruptedError('Phase supervisor received signal '+str(signum))
 signal.signal(signal.SIGTERM,interrupted)
 signal.signal(signal.SIGINT,interrupted)
 start=time.monotonic();child=subprocess.Popen''')
s=s.replace(' finally:\n  killed=kill_owned();code=child.wait()'," except InterruptedError as error:\n  reason=str(error)\n finally:\n  signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)\n  killed=kill_owned();code=child.wait()")
(out/'supervise_method_phase.py').write_text(s)
checks={}
def replace_invoke(name,newblock):
    f=out/name;s=f.read_text();tree=ast.parse(s)
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='invoke')
    lines=s.splitlines(True);block=''.join(lines[node.lineno-1:node.end_lineno]);oldblock=block
    start=block.index(' with ')
    # Replace the complete child process block, retaining all original cost and
    # success/failure decisions below it. Guard settings remain phase-local.
    end=block.index(" if code and status==",start) if " if code and status==" in block else block.index(' costs.append',start)
    block=block[:start]+newblock+block[end:]
    s=s.replace(oldblock,block);s='from phase_supervision import run_phase\n'+s
    f.write_text(s)
for name in ['run_serial_lazy_resource_transactions_stream_v1.py','run_joint_crossing_source_transactions_v2.py','run_registered_independent_stream_transactions_v1.py']:
    replace_invoke(name," proc,code,status=run_phase(command,b,tag,reg['limits']['child_seconds'])\n")
replace_invoke('run_complete_flow_critical_portfolio_stream_v1.py'," proc,code,status=run_phase(command,b,tag,None if script=='run_registered_independent_stream_transactions_v1.py' else 1800)\n")
replace_invoke('run_unified_resource_repair_v1.py'," proc,code,status=run_phase(cmd,b,tag,None)\n")

# The two outer coordinators have identical phase bookkeeping but different
# argument names/indentation; replace only their invoke functions.
for name,indent,arg,tvar in [('run_complete_unified_resource_flow_v1.py','    ','name','begin'),('run_complete_unified_method_v1.py','','tag','t')]:
    f=out/name;s=f.read_text();node=next(n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef) and n.name=='invoke')
    lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=[indent+line+'\n' for line in f'''def invoke({arg},command,timeout=1800):
 {tvar}=time.monotonic()
 child,code,status=run_phase(command,b,{arg},timeout)
 stages.append(dict(phase={arg},status=status,returncode=code,complete_process_seconds=time.monotonic()-{tvar}));write(b/'stages.json',stages)
 if status=='timeout':raise TimeoutError({arg})
 assert code==0,({arg},code)
'''.splitlines()]
    s='from phase_supervision import run_phase\n'+''.join(lines);f.write_text(s)

for name,kind in [('run_complete_flow_critical_portfolio_stream_v1.py',ast.While),('run_unified_resource_repair_v1.py',ast.While),('run_serial_lazy_resource_transactions_stream_v1.py',ast.For),('run_joint_crossing_source_transactions_v2.py',ast.For),('run_registered_independent_stream_transactions_v1.py',ast.For)]:
    def loop(path):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,kind))
    assert ast.dump(loop(D/name))==ast.dump(loop(out/name));checks[name]=True
for f in out.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(out/'phase_supervision_changes.json',dict(prior_manifest_sha256=sha(base/'artifact_manifest.json'),original_scientific_loops_AST_exact=checks,phase_guards='Original per-child durations retained; complete resource/timing/controller phases have no total time cap. Private subreaper cleans detached native descendants on guard failure.',queued_versions_changed=False,native_execution_validated=False,overhead='Included in actual end-to-end time; no cost equivalence assumed'))
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',component_revision='complete_method_dev_02',full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()},qualification='Full serial method development port with private per-phase subreapers. Actual complete native execution and confirmation still pending.'))
print(dict(package=str(out),loops=checks,native_calls_new=0),flush=True)
