"""Port the existing serial unified resource controller, retaining its state machine."""
import argparse,ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=D/'standalone_resource_controller_dev_01');args=parser.parse_args();out=args.output.resolve();shutil.copytree(D/'standalone_transactions_dev_02',out,ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'transaction_component_manifest.json')
origins={}
def save(name,text,note):
 compile(text,name,'exec');(out/name).write_text(text);origins[name]=dict(origin=str(D/name),origin_sha256=sha(D/name) if (D/name).exists() else None,transformation=note)
def same_loop(name,kind):
 old=next(n for n in ast.parse((D/name).read_text()).body if isinstance(n,kind));new=next(n for n in ast.parse((out/name).read_text()).body if isinstance(n,kind));assert ast.dump(old)==ast.dump(new),name
 return True
for name in ['current_crossing_share_selector_v2.py','current_escape_owner_selector_v1.py','state_resource_assurance.py','native_resources_from_receipt.py','resource_policy_scheduling_v1.py','terminal_resource_handoff_v1.py','select_terminal_resource_alternative_v2.py']:
 shutil.copy2(D/name,out/name);origins[name]=dict(origin=str(D/name),origin_sha256=sha(D/name),transformation='byte_exact')
# Only these three helpers are imported; no historical main or directory scans.
names={'run_dir','native_config','input_identity'};tree=ast.parse((D/'run_native_scope_policy_v4.py').read_text());helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
save('run_native_scope_policy_v4.py','import json\nfrom pathlib import Path\nfrom retained_prefix_workflow import read,sha\n'+'\n\n'.join(ast.unparse(n) for n in helpers)+'\n','three_function_AST_exact')
save('resource_native_reuse.py','def free_match(role,batches):\n    assert not batches, "No historical result reuse in the unified controller"\n    return None\n','Original full-flow callers require empty batches; same no-hit semantics, historical scanner not imported')
# Preserve worker scientific execution/audit/STA/sealing tails exactly.
for name in ['run_serial_seed_resource_state_analysis_stream_v1.py','run_serial_census_state_analysis_stream_v1.py','run_crossing_source_seed_analysis_v1.py']:
 original=(D/name).read_text();s=original.replace('D, read, write, sha, require_formal_terminal, route_body','D, read, write, sha, route_body')
 start=s.index('ROOT = D.parents[1]');end=s.index('\n\ndef main():',start)
 s=s[:start]+'import runtime_io as io\nimport runtime_audit as study\nfrom controller_runtime import admit_worker,package_files\n'+s[end:]
 s=s.replace('parser = argparse.ArgumentParser()',"parser = argparse.ArgumentParser()\n    parser.add_argument('--inputs',type=Path,required=True)",1)
 s=s.replace('    require_formal_terminal()',"    config, paths, cache, portable_command = admit_worker(args.inputs,args.source,args.batch)")
 start=s.index('    stage = D / ');end=s.index('    manifest =',start);s=s[:start]+s[end:]
 start=s.index('    b.mkdir(exist_ok=False)');end=s.index('    files =',start)
 s=s[:start]+"    io.configure(b,paths['binary'])\n"+s[end:]
 start=s.index('    files =');end=s.index('    hashes =',start)
 s=s[:start]+'''    files = [*package_files(),args.inputs.resolve(),*paths.values(),source/'manifest.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'independent_audit.json',route,graph]
    for key in ['native_cases','crossing_domain','explicit_crossings','expected_loaded_source_route']:
        value=getattr(args,key,None)
        if value:files.append(value.resolve())
    for directory in [cache.directory,cache.g.directory]:
        files += [directory/'completion.json',*[directory/n for n in read(directory/'completion.json')['payload_sha256']]]
    if hasattr(args,'full_graph_cache'):assert args.full_graph_cache.resolve()==cache.directory
'''+s[end:]
 s=s.replace("cmd[0] = str(b / 'bin/vpr')","cmd[0] = str(paths['binary'])")
 pos=s.index('    env = ');s=s[:pos]+"    assert cmd==portable_command, 'Admitted command differs from the actual source-derived command'\n"+s[pos:]
 # The native execution and scientific gate body is untouched, including source audit reuse.
 oldtail=original[original.index('    result = io.run'):original.index("\n\nif __name__")];newtail=s[s.index('    result = io.run'):s.index("\n\nif __name__")]
 assert ast.dump(ast.parse('def check():\n'+oldtail))==ast.dump(ast.parse('def check():\n'+newtail)),name
 save(name,s,'Portable explicit admission/runtime binding; native execution through complete scientific audit/STA/seal tail AST exact')
# Original owner preparation checks and deterministic request code stay intact.
name='current_owner_transaction_v1.py';s=(D/name).read_text().replace('from endpoint_timing_policy_streaming_v2 import compare','from endpoint_timing_policy_streaming_v2 import compare\nfrom controller_runtime import package_files')
start=s.index('    files = [');end=s.index('    for s in [state,root_state]:',start)
s=s[:start]+'''    files = [*package_files(), selection/'completion.json',selection/'groups.json',selection/'certificates.json',cache/'completion.json',audit_cache/'completion.json']
'''+s[end:];save(name,s,'Only dependency/provenance file list replaced by immutable package files')
# Both transaction schedulers retain original arm loop including skip/reuse/acceptance.
for name in ['run_serial_lazy_resource_transactions_stream_v1.py','run_joint_crossing_source_transactions_v2.py']:
 s=(D/name).read_text().replace('from run_native_scope_policy_v4 import input_identity,native_config,run_dir','from run_native_scope_policy_v4 import input_identity,native_config,run_dir\nfrom controller_runtime import package_files,worker_descriptor')
 start=s.index('selector_files=');end=s.index("assert not (b/'execution_registration.json')",start)
 s=s[:start]+"assert reg['current_resource_selector_after_commit'], 'Resource controller owns selector reentry'\nselector_files=package_files()\n"+s[end:]
 s=s.replace(" command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'",''' if script in ['run_serial_seed_resource_state_analysis_stream_v1.py','run_serial_census_state_analysis_stream_v1.py','run_crossing_source_seed_analysis_v1.py']:
  source=Path(args[args.index('--source')+1]);phase='owner' if script=='run_crossing_source_seed_analysis_v1.py' else 'resource'
  descriptor=worker_descriptor(reg['runtime_config'],source,reg['full_graph_cache'],phase,b/(tag+'_inputs.json'))
  args=[*args,'--inputs',descriptor]
 command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed' ''')
 s=s.replace("if a.selector=='compact':assert all(sha(path)==h for path,h in read(D/'compact_cone_benchmark_01/completion.json')['source_sha256'].items())\n",'')
 save(name,s,'Provenance/package admission and explicit worker descriptor injection only; original arm loop AST exact')
 assert same_loop(name,ast.For)
# Original unified while loop is preserved, including rank windows, owner escalation,
# immutable root, selected arm and post-owner current resource reselection.
name='run_unified_resource_repair_v1.py';s=(D/name).read_text().replace('from current_owner_transaction_v1 import prepare as prepare_owner','from current_owner_transaction_v1 import prepare as prepare_owner\nfrom controller_runtime import package_files,admit_controller')
s=s.replace("p=argparse.ArgumentParser();","p=argparse.ArgumentParser();p.add_argument('--runtime-config',type=Path,required=True);",1)
start=s.index(';files=[');end=s.index(';bindings=',start)
s=s[:start]+";files=[*package_files(),a.runtime_config.resolve(),initial/'completion.json',initial/'endpoint_vector.json',r/'routed.route',r/'manifest.json',r/'independent_audit.json',cache_dir/'completion.json'];files += admit_controller(a.runtime_config,initial,cache_dir)"+s[end:]
s=s.replace("assert read(D/'lazy_resource_scheduling_validation_01/completion.json')['passed']",'assert all(sha(path)==h for path,h in bindings.items())')
s=s.replace(" assert not a.assert_no_native_work, 'Read-only preflight encountered a candidate requiring native execution'",''' assert not a.assert_no_native_work, 'Read-only preflight encountered a candidate requiring native execution'
 registered=read(tx/'registration.json');registered['runtime_config']=str(a.runtime_config.resolve());registered['source_sha256'][str(a.runtime_config.resolve())]=sha(a.runtime_config);write(tx/'registration.json',registered)''')
save(name,s,'Only explicit controller admission/dependency lists and subprocess config propagation changed; original complete resource/owner while loop AST exact')
assert same_loop(name,ast.While)
write(out/'controller_source_provenance.json',dict(files=origins,unified_resource_while_AST_exact=True,resource_arm_loop_AST_exact=True,owner_arm_loop_AST_exact=True,source_audit_reuse_retained=True,full_method_frozen=False,native_execution_equivalence_validated=False,remaining='Initial route and current STA timing portfolio orchestration remain to be ported; terminal selectors copied exact. No actual relocated native controller run yet.'))
print(dict(package=str(out),resource_state_machine_AST_exact=True,native_calls_new=0),flush=True)

shutil.copy2(D/'portable_controller_runtime_v1.py',out/'controller_runtime.py')
for f in out.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in out.iterdir() if f.is_file()},qualification='Original serial lazy resource/owner controller and backend scientific loops retained, portable explicit phase/input/runtime binding. Initial-route and timing portfolio top-level still pending; not the persistent-pool or snapshot backend. No execution equivalence or equal cost claim yet.'))
