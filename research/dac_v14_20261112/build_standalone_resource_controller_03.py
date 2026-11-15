"""Normalize explicit phase-file paths before deriving a same-flow config."""
import argparse,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'standalone_resource_controller_dev_03');a=p.parse_args();out=a.output.resolve();base=D/'standalone_resource_controller_dev_02'
shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__'));(out/'artifact_manifest.json').rename(out/'resource_controller_v2_manifest.json')
f=out/'controller_runtime.py';s=f.read_text();old='   target[key]=p;files.append(p)';assert s.count(old)==1;s=s.replace(old,"   target[key]=p;files.append(p);cfg[group][key]=dict(row,path=str(p))");f.write_text(s);compile(s,str(f),'exec')
write(out/'resource_controller_v3_changes.json',dict(prior_manifest_sha256=sha(base/'artifact_manifest.json'),change='Normalize phase/physical paths after validating them, so a derived config under a new output directory cannot reinterpret relative input paths.',scientific_state_machine_or_worker_changes=False,full_method_frozen=False))
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',component_revision=3,full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()},qualification='Revision2 resource-stage component with normalized explicit path handoff. Full current-STA timing portfolio/outer method and actual native execution equivalence remain pending.'))
print(dict(package=str(out),native_calls_new=0),flush=True)
