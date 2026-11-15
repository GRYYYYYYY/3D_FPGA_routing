"""Relocate the original complete serial method without replacing its scientific loops.

This builds a development artifact. Actual native equivalence and confirmation
are separate experiments; neither build success nor AST equality establishes them.
"""
import argparse,ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'standalone_unified_method_dev_01');a=p.parse_args()
out=a.output.resolve();base=D/'standalone_resource_controller_dev_03'
shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'resource_controller_v3_manifest.json')
origins={};checks={}
def save(name,s,note):
    compile(s,name,'exec');(out/name).write_text(s)
    origins[name]=dict(origin_sha256=sha(D/name) if (D/name).exists() else None,transformation=note)
def replace(s,old,new):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new)
def loop_exact(name,kind):
    def loop(path):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,kind))
    assert ast.dump(loop(D/name))==ast.dump(loop(out/name)),name
    checks[name]=kind.__name__+'_AST_exact'

names='audit_current_cone_queries audit_native_objective_cached compact_timing_cone conditional_distance_certificate critical_action_patterns current_group_feedback_cold_v1 current_native_reuse_resource current_proposal_portfolio current_query_case_cache current_rejection_feedback_v1 current_sta_arrival_cone current_sta_arrival_cone_compact derive_current_release_opportunities expand_critical_owner_scope explicit_envelope_timing_policy make_current_exchange_portfolio_v2 make_current_proposal_portfolio native_problem_identity native_timing_echo_v2 plan_current_critical_group prepare_native_group_step_v2 query_critical_owner_exchange query_current_protected_critical run_complete_flow_critical_portfolio_stream_v1 run_complete_unified_method_v1 run_current_cone_capacity_queries_cold_v1 run_current_graph_relaxed_queries_cold_v1 run_registered_independent_stream_transactions_v1 select_critical_action_group'.split()
for stem in names:
    name=stem+'.py';s=(D/name).read_text()
    s=s.replace("sys.path.insert(0,str(D.parents[1]/'scripts'));",'').replace("sys.path.insert(0,str(D.parents[1]/'scripts'))\n",'')
    save(name,s,'Original code; remove historical scripts-directory injection where present')

# The original frontier helper functions have no implicit driver or history input.
name='run_native_frontier_queries.py';tree=ast.parse((D/name).read_text());wanted={'fingerprint','groups','write_cases','make_case'}
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted];assert len(functions)==4
save(name,'import collections,hashlib,json\n'+'\n\n'.join(ast.unparse(n) for n in functions)+'\n','Four scientific helper functions AST exact; historical main not part of the method')

f=out/'controller_runtime.py';s=f.read_text()
s=replace(s,"assert set(cfg['phase_binaries'])=={'resource','owner'}","assert set(cfg['phase_binaries']) in [{'resource','owner'},{'resource','owner','timing_repair','timing_observer'}]")
s=replace(s," for group,target in [('physical_files',physical),('phase_binaries',binaries)]:"," for group,target in [('physical_files',physical),('phase_binaries',binaries),('query_engines',{}),('query_validations',{})]:")
s=replace(s,"for key,row in cfg[group].items():","for key,row in cfg.get(group,{}).items():")
s=s.replace("if group=='phase_binaries':assert os.access(p,os.X_OK)","if group in ['phase_binaries','query_engines']:assert os.access(p,os.X_OK)")
save(f.name,s,'Accept explicitly bound four-phase method and two query engines; resource-only callers remain supported')
shutil.copy2(D/'portable_timing_runtime_v1.py',out/'timing_runtime.py')

# These queries retain actual graph/state/output seals and exact same-actor cache
# keys. Only implicit development driver/proof paths are replaced.
for name,kind in [('run_current_cone_capacity_queries_cold_v1.py','capacity'),('run_current_graph_relaxed_queries_cold_v1.py','relaxed'),('query_critical_owner_exchange.py','capacity'),('query_current_protected_critical.py','capacity')]:
    s=(out/name).read_text();s='from timing_runtime import query_driver,query_validation,runtime_files\nfrom controller_runtime import package_files\n'+s
    old="D/'current_sta_"+('queries' if kind=='capacity' else 'relaxed')+"_01/critical_capacity_driver'"
    s=replace(s,old,"query_driver('"+kind+"')")
    s=replace(s,"assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']",'assert driver.is_file() # query_driver verified explicit binary hash')
    s=s.replace("assert read(D/'current_query_case_cache_validation_01/completion.json')['passed']","package_files()")
    s=s.replace(",D/'current_query_case_cache_validation_01/completion.json'",'')
    s=s.replace("str(driver.parent/'unit_validation.json'):sha(driver.parent/'unit_validation.json')","str(query_validation()):sha(query_validation())")
    # Bind explicit runtime and package admission to every query registration.
    token='bindings={str(p):sha(p) for p in files}' if 'bindings={str(p):sha(p) for p in files}' in s else 'bound={str(p):sha(p) for p in files}'
    s=replace(s,token,'files += [*package_files(),*runtime_files()]\n'+token)
    save(name,s,'Explicit query engine/runtime/proof binding; original cases, same-actor reuse, path/occupancy audits unchanged')

name='current_native_reuse_resource.py';s=(out/name).read_text();s='from timing_runtime import binary as phase_binary\n'+s
assert s.count("read(D/'resource_domain_stage_01/binding.json')['binary_sha256']")==2
s=s.replace("read(D/'resource_domain_stage_01/binding.json')['binary_sha256']","sha(phase_binary('timing_repair'))")
save(name,s,'Original exact success/failure reuse checks; expected binary comes from explicit runtime')

name='prepare_native_group_step_v2.py';s=(out/name).read_text();s='from controller_runtime import package_files\nfrom timing_runtime import runtime_files\n'+s
s=s.replace("D/'run_registered_native_transactions_v3.py'","D/'run_registered_independent_stream_transactions_v1.py'")
s=s.replace(",D/'fixed_anchor_acceptance_validation_01.json',D/'compact_selector_stage_01/binding.json'",'')
s=replace(s,'bindings={str(p.resolve()):sha(p) for p in files}','files += [*package_files(),*runtime_files()]\nbindings={str(p.resolve()):sha(p) for p in files}')
save(name,s,'Original current/anchor problem identity and ordered request; package/runtime provenance replaces development proof lookup')

for name in ['run_independent_resource_state_analysis_stream_v1.py','run_independent_timing_cone_analysis_stream_v1.py']:
    original=(D/name).read_text();s=original.replace('D, read, write, sha, require_formal_terminal, route_body','D, read, write, sha, route_body')
    start=s.index('ROOT = D.parents[1]');end=s.index('\n\ndef main():',start)
    s=s[:start]+'import runtime_io as io\nimport runtime_audit as study\nfrom controller_runtime import admit_worker,package_files\n'+s[end:]
    s=replace(s,'parser = argparse.ArgumentParser()',"parser = argparse.ArgumentParser()\n    parser.add_argument('--inputs',type=Path,required=True)")
    s=s.replace("    assert read(D/'full_route_graph_cache_validation_01/completion.json')['passed']\n",'')
    s=replace(s,'    require_formal_terminal()',"    config, paths, cache, portable_command = admit_worker(args.inputs,args.source,args.batch)")
    start=s.index('    stage = D / ');end=s.index('    manifest =',start);s=s[:start]+s[end:]
    start=s.index('    b.mkdir(exist_ok=False)');end=s.index('    hashes =',start)
    s=s[:start]+'''    io.configure(b,paths['binary'])
    files = [*package_files(),args.inputs.resolve(),*paths.values(),source/'manifest.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'independent_audit.json',route,graph]
    if getattr(args,'native_cases',None):files.append(args.native_cases.resolve())
    if getattr(args,'crossing_domain',None):
        assert args.native_cases is not None
        files.append(args.crossing_domain.resolve())
    for directory in [cache.directory,cache.g.directory]:
        files += [directory/'completion.json',*[directory/n for n in read(directory/'completion.json')['payload_sha256']]]
    if hasattr(args,'full_graph_cache'):assert args.full_graph_cache.resolve()==cache.directory
'''+s[end:]
    s=replace(s,"cmd[0] = str(b / 'bin/vpr')","cmd[0] = str(paths['binary'])")
    pos=s.index('    env = ');s=s[:pos]+"    assert cmd==portable_command, 'Admitted and actual source-derived command differ'\n"+s[pos:]
    start='    result = io.run';end="\n\nif __name__"
    assert ast.dump(ast.parse('def check():\n'+original[original.index(start):original.index(end)]))==ast.dump(ast.parse('def check():\n'+s[s.index(start):s.index(end)])),name
    checks[name]='Native execution / FULL / physical audit / STA / seal tail AST exact'
    save(name,s,'Explicit worker admission/runtime; scientific native tail AST exact')

name='run_registered_independent_stream_transactions_v1.py';s=(out/name).read_text()
s='from controller_runtime import package_files,worker_descriptor\nfrom timing_runtime import runtime_files,KEY\n'+s
start=s.index('selector_files=');end=s.index("assert not (b/'execution_registration.json')",start)
s=s[:start]+"selector_files=[*package_files(),*runtime_files(),a.audit_cache/'completion.json',a.full_graph_cache/'completion.json']\n"+s[end:]
s=replace(s," command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'",''' if script in ['run_independent_resource_state_analysis_stream_v1.py','run_independent_timing_cone_analysis_stream_v1.py']:
  source=Path(args[args.index('--source')+1]);phase='timing_repair' if script=='run_independent_resource_state_analysis_stream_v1.py' else 'timing_observer'
  descriptor=worker_descriptor(os.environ[KEY],source,a.full_graph_cache,phase,b/(tag+'_inputs.json'))
  args=[*args,'--inputs',descriptor]
 command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed' ''')
s=replace(s,"if a.selector=='compact':assert all(sha(path)==h for path,h in read(D/'compact_cone_benchmark_01/completion.json')['source_sha256'].items())\n",'')
save(name,s,'Explicit worker descriptor injection and package admission; original transaction arm loop')
loop_exact(name,ast.For)

name='run_complete_flow_critical_portfolio_stream_v1.py';s=(out/name).read_text()
s='from timing_runtime import admit_timing\n'+s
s=replace(s,'p=argparse.ArgumentParser()',"p=argparse.ArgumentParser();p.add_argument('--runtime-config',type=Path,required=True)")
start=s.index("assert read(initial/'completion.json')['passed'];proof=");end=s.index('def resources(',start)
s=s[:start]+"assert read(initial/'completion.json')['passed']\nruntime_bindings=admit_timing(a.runtime_config,initial,a.full_graph_cache)\n"+s[end:]
s=s.replace(",D/'current_exchange_portfolio_validation_02.json'",'').replace(',proof,initial/',',initial/')
s=s.replace("assert read(D/'current_exchange_portfolio_validation_02.json')['passed']\n",'').replace("assert read(D/'explicit_envelope_timing_policy_validation_01.json')['passed']\n",'')
s=s.replace(",D/'explicit_envelope_timing_policy_validation_01.json'",'')
s=replace(s,'bindings={str(p):sha(p) for p in files};write(', 'files += runtime_bindings\nbindings={str(p):sha(p) for p in files};write(')
save(name,s,'Explicit phase runtime admitted before first feedback; original portfolio and all reuse/feedback/acceptance logic')
loop_exact(name,ast.While)

name='run_complete_unified_method_v1.py';s=(out/name).read_text()
s='from controller_runtime import package_files,worker_descriptor\nfrom timing_runtime import activate\n'+s
s=replace(s,"assert config['phase_binary_sha256']['owner_coordination']==sha(D/'crossing_source_stage_01/bin/vpr')",'''base_runtime=Path(config['phase_runtime_config']).resolve()
runtime_spec,physical,binaries,runtime_files=activate(base_runtime)
phase_names={'owner_coordination':'owner','resource':'resource','timing_repair':'timing_repair','timing_observer':'timing_observer'}
assert set(config['phase_binary_sha256'])==set(phase_names)
assert all(config['phase_binary_sha256'][key]==sha(binaries[value]) for key,value in phase_names.items())''')
s=replace(s,"assert all(sha(f)==h for f,h in files.items())\nwrite(b/'registration.json'","files.update({str(f):sha(f) for f in [*package_files(),base_runtime,*runtime_files]})\nassert all(sha(f)==h for f,h in files.items())\nwrite(b/'registration.json'")
s=replace(s,"resource_done=read(resource_flow/'completion.json');assert resource_done['passed']","resource_done=read(resource_flow/'completion.json');assert resource_done['passed']\nphase_runtime=resource_flow/'phase_runtime.json';activate(phase_runtime)")
s=replace(s,"handoff=b/'timing_initial'","handoff=b/'timing_initial'\nhandoff_inputs=worker_descriptor(phase_runtime,run_dir(resource_final),resource_flow/'full_graph_cache','resource',b/'timing_handoff_inputs.json')")
s=replace(s,"D/'run_serial_census_state_analysis_stream_v1.py','--source'","D/'run_serial_census_state_analysis_stream_v1.py','--inputs',handoff_inputs,'--source'")
s=replace(s,"D/'run_complete_flow_critical_portfolio_stream_v1.py','--initial-state'","D/'run_complete_flow_critical_portfolio_stream_v1.py','--runtime-config',phase_runtime,'--initial-state'")
save(name,s,'Complete original outer phase order; explicit admitted binaries and freshly generated cache descriptor')

write(out/'unified_method_source_provenance.json',dict(files=origins,AST_checks=checks,prior_manifest_sha256=sha(base/'artifact_manifest.json'),full_method_frozen=False,native_execution_equivalence_validated=False,qualification='Development port. Scientific loops and worker tails retained. Runtime binding and process supervision have measurable costs; no equal-runtime claim.'))
for f in out.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',component_revision='complete_method_dev_01',full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()},qualification='Original serial complete resource/owner/terminal-wire/current-STA controller dependency port. Actual end-to-end execution and confirmation still pending.'))
print(dict(package=str(out),files=len(list(out.iterdir())),AST_checks=checks,native_calls_new=0),flush=True)
