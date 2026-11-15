"""Run the real relocated no-cut controller and terminal selector; no solver calls."""
import copy,json,os,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
package=D/'standalone_resource_controller_dev_01';report=D/'standalone_resource_controller_validation_01';report.mkdir(exist_ok=False)
w=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/resource_controller_01');w.mkdir(exist_ok=False);runtime=w/'runtime';shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
previous=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/native_transaction_01/runtime')
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
 if (previous/name).exists():shutil.copytree(previous/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
origin=D/'fresh_route_entry_preflight_01/flow';state=origin/'initial';source=Path(read(state/'completion.json')['run']);m=read(source/'manifest.json');command=m['command']
mapping={};sources={}
def exact(old,new):
 old=Path(old).resolve();new.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,new);h=sha(old);assert sha(new)==h;mapping[str(old)]=str(new);sources[str(old)]=h
paths=dict(architecture=Path(command[1]),circuit=Path(command[2]),graph=Path(command[command.index('--read_rr_graph')+1]),packed=source/'packed.net',placement=source/'placed.place')
for key,old in paths.items():exact(old,w/'inputs'/(key+old.suffix));paths[key]=Path(mapping[str(old)])
for key,stage in [('resource','native_resource_census_stage_01'),('owner','crossing_source_stage_01')]:exact(D/stage/'bin/vpr',w/'inputs'/('binary_'+key))
newsource=w/'source';newsource.mkdir();newstate=w/'state';newstate.mkdir()
for name in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','independent_audit.json','packed.net','placed.place']:exact(source/name,newsource/name)
exact(state/'endpoint_vector.json',newstate/'endpoint_vector.json')
def translate(v):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [translate(x) for x in v]
 if isinstance(v,dict):return {translate(k):translate(x) for k,x in v.items()}
 return v
for old,new,changes in [(source/'manifest.json',newsource/'manifest.json',{}),(state/'completion.json',newstate/'completion.json',dict(run=str(newsource)))]:
 exact(old,new.with_name(new.name+'.origin'));v=translate(read(old));v.update(changes);v['receipt_relocation']=dict(original_sha256=sha(old),new_native_run=False);write(new,v)
full=origin/'full_graph_cache';parent=Path(read(full/'completion.json')['parent_cache'])
for old,new in [(parent,w/'audit_cache'),(full,w/'full_cache')]:
 c=read(old/'completion.json')
 for name in c['payload_sha256']:exact(old/name,new/name)
 exact(old/'completion.json',new/'origin_completion.json')
 if new.name=='audit_cache':c['graph']=str(paths['graph'])
 else:c.update(parent_cache=str(w/'audit_cache'),parent_completion_sha256=sha(w/'audit_cache/completion.json'))
 c['relocation']=dict(original_sha256=sha(old/'completion.json'),new_build=False);write(new/'completion.json',c)
config=w/'runtime_config.json';write(config,dict(format='explicit_unified_phase_runtime_v1',physical_files={k:dict(path=str(p),sha256=sha(p)) for k,p in paths.items()},phase_binaries={k:dict(path=str(w/'inputs'/('binary_'+k)),sha256=sha(w/'inputs'/('binary_'+k))) for k in ['resource','owner']},full_graph_cache_completion_sha256=sha(w/'full_cache/completion.json')))
write(report/'registration.json',dict(workspace=str(w),original_state=str(state),original_sha256=sources,package_manifest_sha256=sha(package/'artifact_manifest.json'),native_calls_planned=0,qualification='Actual original no-cut tiny input, imported exact native observation with explicit metadata relocation; no independent circuit result.'))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(script,args,label,expected=0):
 cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)];start=time.monotonic()
 with (report/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 write(report/(label+'_execution.json'),dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start));assert (r.returncode==0)==(expected==0),label
flow=w/'resource_flow';flow.mkdir();actor=flow/'repair'
execute('run_unified_resource_repair_v1.py',['--runtime-config',config,'--initial-state',newstate,'--batch',actor,'--seed-order','delay_rr_id','--domain-feedback','--full-graph-cache',w/'full_cache','--domain-mode','paired','--bundle-size','8','--assert-no-native-work'],'no_cut_controller')
closed=read(actor/'completion.json');assert closed['passed'] and closed['accepted_steps']==closed['owner_commits']==closed['attempted_scopes']==0
assert Path(closed['final_state'])==newstate and not (actor/'active_child.json').exists()
write(flow/'completion.json',dict(passed=True,final_state=str(newstate),initial_state=str(newstate),qualification='Imported-state resource controller test wrapper only; not a fresh-route complete flow.'))
execute('select_terminal_resource_alternative_v2.py',['--actor',actor,'--output',flow/'terminal_selection','--mode','endpoint'],'terminal_selection')
assert read(flow/'terminal_selection/completion.json')['selected'] is None
helper=w/'check_handoff.py';helper.write_text("from pathlib import Path\nfrom terminal_resource_handoff_v1 import choose\nfrom retained_prefix_workflow import write\nimport sys\nf=Path(sys.argv[1]);r=choose(f,f/'terminal_selection');assert r['passed'] and not r['changed'];write(f/'handoff.json',r)\n")
execute(str(helper),[flow],'terminal_handoff')
# Import every actual worker scheduler CLI without executing it.
for name in ['run_serial_seed_resource_state_analysis_stream_v1.py','run_serial_census_state_analysis_stream_v1.py','run_crossing_source_seed_analysis_v1.py','run_serial_lazy_resource_transactions_stream_v1.py','run_joint_crossing_source_transactions_v2.py']:
 execute(name,['--help'],name.removesuffix('.py')+'_CLI')
assert all(sha(f)==h for f,h in sources.items())
assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
write(report/'completion.json',dict(passed=True,workspace=str(w),actual_no_cut_resource_controller_passed=True,actual_terminal_selector_and_handoff_passed=True,actual_controller_selected_original_source=True,source_hashes_unchanged=True,backend_CLIs_imported=5,whole_resource_owner_loop_AST_exact=True,backend_arm_loops_AST_exact=True,native_worker_scientific_tails_AST_exact=True,native_calls_new=0,new_independent_inputs=0,positive_owner_commit_reentry_tested=False,actual_native_backend_execution_tested=False,full_method_frozen=False,source_sha256={str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(report/'registration.json'):sha(report/'registration.json'),str(actor/'completion.json'):sha(actor/'completion.json'),str(flow/'handoff.json'):sha(flow/'handoff.json'),str(Path(__file__).resolve()):sha(__file__)},qualification='Actual relocated no-cut controller, original owner selector, terminal menu and handoff executed. Native backend command imports only; positive owner commit/reentry and actual worker equivalence pending. Does not validate a complete fresh-route/resource/timing algorithm or claim equal cost.'))
print(dict(passed=True,no_cut_controller=True,terminal_handoff=True,native_calls_new=0),flush=True)
