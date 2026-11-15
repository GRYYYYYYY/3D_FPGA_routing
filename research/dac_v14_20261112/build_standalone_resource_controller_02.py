"""Add explicit fresh-route entry; remove one remaining historical proof lookup."""
import argparse,ast,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'standalone_resource_controller_dev_02');a=p.parse_args();out=a.output.resolve()
base=D/'standalone_resource_controller_dev_01';shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__'));(out/'artifact_manifest.json').rename(out/'resource_controller_v1_manifest.json')
f=out/'run_serial_census_state_analysis_stream_v1.py';s=f.read_text();old="    assert read(D/'full_route_graph_cache_validation_01/completion.json')['passed']\n";assert s.count(old)==1;s=s.replace(old,'');f.write_text(s)
# The live descriptor already verifies XML, cache completion and all payload hashes.
name='run_complete_unified_resource_flow_v1.py';s=(D/name).read_text();start=s.index('ROOT=D.parents[1]');end=s.index('\n\ndef main():',start)
s=s[:start]+'''import runtime_io as io
import runtime_audit as study
from controller_runtime import package_files,configuration
from observe import FIXED,OPTIONAL_FIXED,OTHER,PATH_OPTIONS


def admit_route(config,base_config):
    cfg,physical,binaries,files=configuration(base_config)
    cmd=list(config['route_command']);assert Path(cmd[0]).resolve()==binaries['resource']
    args=cmd[3:];options={};i=0
    while i<len(args):
        key=args[i];assert key not in options
        if key in ['--route','--analysis']:options[key]=None;i+=1;continue
        assert key in FIXED.keys()|OPTIONAL_FIXED.keys()|OTHER|PATH_OPTIONS.keys()
        assert i+1<len(args);options[key]=args[i+1];i+=2
    assert '--route' in options and '--analysis' in options
    assert all(options.get(k)==v for k,v in FIXED.items())
    assert all(options[k]==v for k,v in OPTIONAL_FIXED.items() if k in options)
    assert {'--device','--route_chan_width','--seed'}<=options.keys()
    for key,value in [('architecture',cmd[1]),('circuit',cmd[2]),('graph',options['--read_rr_graph']),('packed',options['--net_file']),('placement',options['--place_file'])]:
        assert Path(value).resolve()==physical[key]
    assert ('sdc' in physical)==('--sdc_file' in options)
    if 'sdc' in physical:assert Path(options['--sdc_file']).resolve()==physical['sdc']
    assert options['--route_file'] not in config['input_sha256'],'Route output placeholder must not be an imported input'
    return cfg,physical,binaries,files
'''+s[end:]
s=s.replace("    binary=D/'native_resource_census_stage_01/bin/vpr'\n    assert sha(binary)==read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']", "    base_runtime=Path(config['phase_runtime_config']).resolve()\n    runtime_spec,physical,binaries,runtime_files=admit_route(config,base_runtime)\n    files.update({str(f):sha(f) for f in [*package_files(),base_runtime,*runtime_files]})\n    binary=binaries['resource']")
s=s.replace("    io.BASE=b/'initial';io.BASE.mkdir();rd=io.BASE/'runs/state';rd.mkdir(parents=True)","    io.configure(b/'initial',binary);rd=io.BASE/'runs/state';rd.mkdir(parents=True)")
start=s.index('    # Resolve this binary');end=s.index('    static=[',start);s=s[:start]+s[end:]
s=s.replace("    repair=b/'repair'","    runtime_spec['full_graph_cache_completion_sha256']=sha(full/'completion.json')\n    phase_runtime=b/'phase_runtime.json';write(phase_runtime,runtime_spec)\n    repair=b/'repair'")
s=s.replace("command=[sys.executable,D/'run_unified_resource_repair_v1.py','--initial-state'","command=[sys.executable,D/'run_unified_resource_repair_v1.py','--runtime-config',phase_runtime,'--initial-state'")
compile(s,name,'exec');(out/name).write_text(s)
# Native route execution through initial quality/physical/STA seal is unchanged.
original=(D/name).read_text();start='    result=io.run(';end="    stages.append(dict(phase='fresh_route_and_materialization'"
for text in [original,s]:assert start in text and end in text
assert ast.dump(ast.parse('def check():\n'+original[original.index(start):original.index(end)]))==ast.dump(ast.parse('def check():\n'+s[s.index(start):s.index(end)]))
write(out/'resource_controller_v2_changes.json',dict(prior_manifest_sha256=sha(base/'artifact_manifest.json'),removed_obsolete_historical_proof_lookup=True,actual_cache_and_package_validation_retained=True,new_fresh_route_entry=name,initial_native_quality_audit_STA_seal_AST_exact=True,prior_resource_owner_loop_unchanged=True,remaining='Complete current-STA timing portfolio and outer complete-method wrapper still not ported. All actual native execution equivalence remains unvalidated.',full_method_frozen=False))
for f in out.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',component_revision=2,full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()},qualification='Original serial lazy resource/owner state machine, original native scientific tails, terminal selection, and explicit fresh initial routing/cache-build entry. Current-STA timing portfolio and complete outer controller pending. New runtime binding and package admission costs explicit; no execution or cost equivalence claim.'))
print(dict(package=str(out),initial_native_scientific_tail_AST_exact=True,native_calls_new=0),flush=True)
