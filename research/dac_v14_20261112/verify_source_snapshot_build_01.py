"""Record build provenance and executable smoke checks without claiming native QoR."""
import difflib,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
stage=D/'source_snapshot_stage_01';binding=read(stage/'binding.json');reg=read(stage/'registration.json')
p=process_identity(reg['pid']);assert not p or p['state']=='Z' or p['start_ticks']!=reg['start_ticks']
assert all(sha(f)==h for f,h in binding['source_sha256'].items())
assert sha(stage/'bin/vpr')==binding['binary_sha256']
assert sha(stage/'vpr_api.cpp.o')==binding['private_object_sha256']
old=D/'native_resource_census_workspace_01';base=D/'native_resource_census_stage_01';baseline=read(base/'binding.json');all_sources=read(base/'all_source_hashes.json')
assert sha(base/'all_source_hashes.json')==baseline['all_source_manifest_sha256']
assert all(sha(old/n)==h for n,h in all_sources.items())
assert sha(base/'bin/vpr')==baseline['binary_sha256']
before=(old/'vpr/src/base/vpr_api.cpp').read_text();after=(stage/'vpr_api.cpp').read_text()
needle='        h3d_joint_native_repair::run_if_requested(net_list, vpr_setup.RouterOpts, is_flat, candidate_observer);'
start=after.index('        // Optional same-invocation serialization of the real loaded source.')
end=after.index(needle,start)
assert after[:start]+after[end:]==before
patch=after[start:end];assert 'std::string(source_snapshot) == "1"' in patch and '!candidate_directory.empty()' in patch
assert patch.index('print_route')<patch.index('std::ofstream receipt')
assert 'load_net_delay_from_routing' not in patch and 'run_if_requested' not in patch
patchfile=stage/'source_snapshot.patch';patchfile.write_text(''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='frozen/vpr/src/base/vpr_api.cpp',tofile='private/vpr_api.cpp')))
result=subprocess.run([str(stage/'bin/vpr'),'--help'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
assert result.returncode==0 and 'VPR FPGA Placement and Routing.' in result.stdout
(stage/'verified_help_smoke.log').write_text(result.stdout)
compiler=Path('/usr/bin/c++').resolve();version=subprocess.check_output([str(compiler),'--version'],text=True)
write(stage/'build_verification.json',dict(passed=True,build_only=True,native_route_validation=False,default_and_candidate_equivalence_verified=False,full_algorithm_performance_verified=False,all_frozen_source_files_unchanged=len(all_sources),original_binary_unchanged=True,optin_delta_is_one_print_only_block=True,compiler=str(compiler),compiler_sha256=sha(compiler),compiler_version=version,help_smoke_returncode=result.returncode,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),stage/'binding.json',stage/'registration.json',base/'all_source_hashes.json',base/'binding.json',stage/'vpr_api.cpp',patchfile,stage/'verified_help_smoke.log']},qualification='Only private vpr_api.cpp.o rebuilt, all other frozen link objects retained. Strict opt-in print_route snapshot runs after original source FULL/STA and before repair, saving/restoring routing identity through the existing RAII guard. Candidate/restored FULL and new STA remain. Build/executable check is not candidate validation or speed evidence; registered fresh-route complete configuration must establish actual complete-state equivalence and cost.'))
print(dict(passed=True,frozen_sources_unchanged=len(all_sources),native_validation_pending=True),flush=True)
