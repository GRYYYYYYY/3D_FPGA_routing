"""Retain the existing public phase-hash schema and include the whole-flow verifier."""
import argparse,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'standalone_unified_method_dev_03');a=p.parse_args()
base=D/'standalone_unified_method_dev_02';out=a.output.resolve();shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'unified_method_v2_manifest.json')
f=out/'run_complete_unified_method_v1.py';s=f.read_text();old="phase_names={'owner_coordination':'owner','resource':'resource','timing_repair':'timing_repair','timing_observer':'timing_observer'}";assert s.count(old)==1
s=s.replace(old,"phase_names={'owner_coordination':'owner','route_and_resource':'resource','timing_native_repair':'timing_repair','timing_candidate_STA':'timing_observer'}");f.write_text(s)
for name in ['verify_complete_unified_method_v1.py','measure_process_tree_v1.py']:shutil.copy2(D/name,out/name)
for f in out.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(out/'whole_flow_entry_changes.json',dict(prior_manifest_sha256=sha(base/'artifact_manifest.json'),unchanged_original_verifier_and_observer=True,original_phase_hash_field_names_retained=True,scientific_loops_or_workers_changed=False,full_method_frozen=False))
write(out/'artifact_manifest.json',dict(format='standalone_serial_resource_controller_development_v1',component_revision='complete_method_dev_03',full_method_frozen=False,native_controller_execution_validated=False,sha256={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()},qualification='Full original serial method and unchanged complete-flow verifier/measurement entry. Explicit four native phases and query engines; pending actual full native execution and confirmation.'))
print(dict(package=str(out),native_calls_new=0),flush=True)
