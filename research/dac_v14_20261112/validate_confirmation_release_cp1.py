"""Actual relocated admission, known failure regression and adversarial rule checks;0native calls."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'confirmation_release_cp1_01';release=Path(read(root/'preparation.json')['release'])
work=release.parent/'cp1_admission_validation_01';work.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('cp1_entry',release/'confirmation.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
project=D.parents[1];results=[]

def stage(label,plan_path):
    plan=read(plan_path);w=work/label;w.mkdir()
    cfg=[read(plan['cases'][a]) for a in ['native','domain']]
    original=Path(plan['physical_identity']['source_manifest'])
    source=w/'source_manifest.json';source.write_bytes(original.read_bytes())
    for arm,c in zip(['native','domain'],cfg):
        command=c['route_command']
        if '--routing_failure_predictor' not in command:command += ['--routing_failure_predictor','off']
        command[command.index('--route_file')+1]=str(w/'UNCREATED_OUTPUT')
        c['input_sha256'].update({str(p):sha(p) for p in [release/'release_manifest.json',release/'contract.json',source]})
        write(w/(arm+'.json'),c)
    return w

def call(w):return module.check(w/'native.json',w/'domain.json',w/'source_manifest.json',project)

def expect(w,label,mutation=None,accepted=False):
    directory=work/label;directory.mkdir()
    configs=[read(w/(a+'.json')) for a in ['native','domain']]
    source=directory/'source_manifest.json';source.write_bytes((w/'source_manifest.json').read_bytes())
    for c in configs:
        c['input_sha256'].pop(str(w/'source_manifest.json'))
        c['input_sha256'][str(source)]=sha(source)
    if mutation:mutation(configs,source)
    for a,c in zip(['native','domain'],configs):write(directory/(a+'.json'),c)
    try:
        result=call(directory)
    except (AssertionError,KeyError,ValueError,TypeError) as exc:
        assert not accepted,(label,repr(exc));results.append(dict(test=label,passed=True,rejected=True,error=str(exc)));return
    assert accepted,label+' unexpectedly admitted'
    results.append(dict(test=label,passed=True,rejected=False,receipt=result))

clstm=stage('clstm_corrected',D/'clstm_input_contract_pair_02/plan.json')
robot=stage('robot_p1_corrected',D/'robot_p1_input_contract_pair_02/plan.json')
for name,w in [('clstm_corrected',clstm),('robot_p1_corrected',robot)]:
    result=call(w);assert result['passed'] and result['merge_constant_generators']=='off'
    results.append(dict(test=name,passed=True,rejected=False,receipt=result))

def field(key,value):
    def mutate(cfg,source):
        for c in cfg:c[key]=value
    return mutate
def route_option(flag,value):
    def mutate(cfg,source):
        for c in cfg:
            c['route_command'][c['route_command'].index(flag)+1]=value
    return mutate
def missing_constant(cfg,source):
    for c in cfg:
        i=c['route_command'].index('--merge_constant_generators');del c['route_command'][i:i+2]
expect(clstm,'original_missing_constant_regression',missing_constant)
expect(robot,'robot_missing_constant_regression',missing_constant)
expect(clstm,'changed_timing_fraction',field('timing_fraction',.8))
expect(clstm,'disabled_owner',field('owner_escalation',False))
expect(clstm,'changed_terminal',field('final_state_policy','best_CPD_from_history'))
expect(clstm,'external_history',field('external_history_allowed',True))
expect(clstm,'imported_initial_route',field('initial_route_imported',True))
expect(clstm,'bool_as_integer',field('initial_route_imported',0))
expect(clstm,'extra_unregistered_policy',field('accepted_step_cap',1))
expect(clstm,'unequal_convergence',lambda c,s:c[1]['route_command'].__setitem__(c[1]['route_command'].index('--router_max_convergence_count')+1,'4'))
expect(clstm,'changed_both_convergence',route_option('--router_max_convergence_count','4'))
expect(clstm,'changed_failure_predictor',route_option('--routing_failure_predictor','safe'))
expect(clstm,'changed_phase_hash',field('phase_binary_sha256',{}))
expect(clstm,'missing_release_binding',lambda cfg,s:[c['input_sha256'].pop(str(release/'release_manifest.json')) for c in cfg])
expect(clstm,'duplicate_merge_option',lambda cfg,s:[c['route_command'].extend(['--merge_constant_generators','off']) for c in cfg])
expect(clstm,'swapped_arms',lambda cfg,s:cfg.reverse())
def wrong_packing(cfg,source):
    m=read(source);m['outputs']['packed.net']['sha256']='0'*64;write(source,m)
    for c in cfg:c['input_sha256'][str(source)]=sha(source)
expect(clstm,'wrong_packed_identity',wrong_packing)
def source_flag_changed(cfg,source):
    m=read(source);i=m['command'].index('--merge_constant_generators');del m['command'][i:i+2];write(source,m)
    for c in cfg:c['input_sha256'][str(source)]=sha(source)
expect(clstm,'changed_packing_interpretation',source_flag_changed)

# Execute the actual CLI from outside both source project and release directory.
base=['/usr/bin/python3',str(release/'confirmation.py'),'check','--native',str(clstm/'native.json'),
      '--domain',str(clstm/'domain.json'),'--packing-manifest',str(clstm/'source_manifest.json'),'--forbid-prefix',str(project)]
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME']};env['PYTHONDONTWRITEBYTECODE']='1'
actual=subprocess.run(base,cwd=work,env=env,text=True,capture_output=True,check=True)
assert json.loads(actual.stdout)['passed'];results.append(dict(test='actual_outside_project_CLI',passed=True,native_calls=0))
imports=subprocess.run(['/usr/bin/python3','-c',"import sys;sys.path.insert(0,sys.argv[1]);import numpy,lxml.etree;print(numpy.__version__);print(lxml.etree.LXML_VERSION);print(numpy.__file__);print(lxml.etree.__file__)",str(release/'runtime')],cwd=work,env=env,text=True,capture_output=True,check=True)
assert imports.stdout.splitlines()[:2]==['2.2.6','(6, 1, 3, 0)']
assert all(str(release/'runtime') in s for s in imports.stdout.splitlines()[2:])
results.append(dict(test='actual_bundled_extension_imports',passed=True,output=imports.stdout))

# Stop at the real exec boundary, without manufacturing a native result.
case=work/'dry_launch';old_argv=sys.argv;old_cwd=Path.cwd();old_exec=module.os.execv;observed=[];saved_env=dict(os.environ)
try:
    module.os.execv=lambda binary,command:observed.append((binary,command))
    sys.argv=[str(release/'confirmation.py'),'run-arm','--native',str(clstm/'native.json'),'--domain',str(clstm/'domain.json'),
       '--packing-manifest',str(clstm/'source_manifest.json'),'--forbid-prefix',str(project),'--arm','native','--case',str(case)]
    module.main()
finally:
    module.os.execv=old_exec;sys.argv=old_argv;os.chdir(old_cwd);os.environ.clear();os.environ.update(saved_env)
assert len(observed)==1 and observed[0][1][1]==str(release/'runtime/guarded_entry.py')
assert '--script' in observed[0][1] and str(release/'runtime/run_complete_unified_method_v1.py') in observed[0][1]
assert sha(case/'config.json')==sha(clstm/'native.json') and read(case/'confirmation_input.json')['measured_entry']
assert not (case/'flow').exists()
results.append(dict(test='actual_measured_launch_boundary_intercepted',passed=True,native_calls=0,command=observed[0][1],not_native_execution=True))
write(root/'validation.json',dict(passed=True,tests=len(results),results=results,native_calls=0,large_input_hashes_or_copies=0,
    actual_new_native_confirmation_results=0,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),release/'release_manifest.json',release/'confirmation.py',release/'contract.json',clstm/'native.json',clstm/'domain.json',clstm/'source_manifest.json',robot/'native.json',robot/'domain.json',robot/'source_manifest.json']},
    qualification='Real relocated CLI and bundled imports, regression of actual input-loading bug, adversarial fixed-rule admission and intercepted launch boundary. Core execution evidence comes from byte-identical prior actual runtime; no new native result or positive integrated-path proof is fabricated.'))
print(dict(passed=True,tests=len(results),native_calls=0))
