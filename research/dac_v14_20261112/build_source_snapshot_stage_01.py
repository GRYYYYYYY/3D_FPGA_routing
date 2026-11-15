"""Build a private single-TU source-snapshot variant from frozen link inputs."""
import os,resource,shlex,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
out=D/'source_snapshot_stage_01';out.mkdir(exist_ok=False);(out/'bin').mkdir();start=time.monotonic()
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
old=D/'native_resource_census_workspace_01';stage=D/'native_resource_census_stage_01';binding=read(stage/'binding.json')
assert sha(stage/'bin/vpr')==binding['binary_sha256']
for n,h in binding['source_sha256'].items():assert sha(old/n)==h,n
source=old/'vpr/src/base/vpr_api.cpp';text=source.read_text()
needle='        h3d_joint_native_repair::run_if_requested(net_list, vpr_setup.RouterOpts, is_flat, candidate_observer);'
assert text.count(needle)==1
patch='''        // Optional same-invocation serialization of the real loaded source.
        // Initial FULL/STA and source frontier already ran; no replacement,
        // search or second analysis is implied by this print-only observation.
        const char* source_snapshot = std::getenv("VPR_JOINT_NATIVE_SOURCE_LOADED_EXPORT");
        if (!candidate_directory.empty() && source_snapshot && std::string(source_snapshot) == "1") {
            const std::string directory = candidate_directory + "_source";
            h3d_candidate_observer::ScopedOutputPaths paths(directory);
            print_route(net_list, vpr_setup.FileNameOpts.PlaceFile.c_str(), (directory + "/routed.route").c_str(), is_flat);
            std::ofstream receipt(directory + "/native_state_gate.txt");
            receipt << "loaded_source serialized_before_transaction initial_FULL initial_STA actual_installed_trees\\n";
            receipt.close();
            if (!receipt) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot write loaded source snapshot gate");
        }
'''
patched=out/'vpr_api.cpp';patched.write_text(text.replace(needle,patch+needle))
flags_file=old/'build/vpr/CMakeFiles/libvpr.dir/flags.make'
flags={line.split(' = ',1)[0]:line.split(' = ',1)[1] for line in flags_file.read_text().splitlines() if ' = ' in line}
obj=out/'vpr_api.cpp.o';compile_cmd=['/usr/bin/c++',*shlex.split(flags['CXX_DEFINES']),*shlex.split(flags['CXX_INCLUDES']),*shlex.split(flags['CXX_FLAGS']),'-o',str(obj),'-c',str(patched)]
link_file=old/'build/vpr/CMakeFiles/vpr.dir/link.txt';tokens=shlex.split(link_file.read_text());wd=old/'build/vpr';base_archive=wd/'libvpr.a';archive=out/'libvpr.a'
assert subprocess.check_output(['ar','t',str(base_archive)],text=True).splitlines().count('vpr_api.cpp.o')==1
link_cmd=[tokens[0]];i=1;inputs=[Path(__file__).resolve(),stage/'binding.json',source,patched,flags_file,link_file,base_archive,wd/'CMakeFiles/libvpr.dir/src/base/vpr_api.cpp.o']
while i<len(tokens):
 t=tokens[i]
 if t=='-o':link_cmd+=['-o',str(out/'bin/vpr')];i+=2;continue
 if t=='libvpr.a':link_cmd.append(str(archive))
 elif not t.startswith('-'):
  f=Path(t) if Path(t).is_absolute() else (wd/t).resolve();assert f.exists();link_cmd.append(str(f));inputs.append(f)
 else:link_cmd.append(t)
 i+=1
hashes={str(f):sha(f) for f in inputs}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,compile_command=compile_cmd,link_command=link_cmd,baseline_binary_sha256=binding['binary_sha256'],qualification='Private single-translation-unit rebuild, replacing exactly the vpr_api.cpp.o archive member. All other frozen objects and link inputs remain explicitly bound. Adds opt-in same-invocation pretransaction route serialization; existing source/candidate/restored FULL/STA/search/acceptance unchanged. Build is upstream development cost, not algorithm runtime. Native equivalence and complete performance are unproven until actual validation.'))
with (out/'build.log').open('w') as log:
 code=subprocess.run(compile_cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800).returncode
 assert code==0,'private compile failed'
 shutil.copy2(base_archive,archive)
 code=subprocess.run(['ar','r',str(archive),str(obj)],stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;assert code==0
 code=subprocess.run(link_cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode;assert code==0
assert subprocess.check_output(['ar','p',str(archive),'vpr_api.cpp.o'])==obj.read_bytes()
assert all(sha(f)==h for f,h in hashes.items())
write(out/'binding.json',dict(status='built_not_native_validated',binary_sha256=sha(out/'bin/vpr'),source_sha256=hashes,registration_sha256=sha(out/'registration.json'),private_object_sha256=sha(obj),private_archive_sha256=sha(archive),build_log_sha256=sha(out/'build.log'),complete_build_seconds=time.monotonic()-start,baseline_binary_sha256=binding['binary_sha256'],qualification='Opt-in source snapshot build only. No correctness, speedup or full-flow claim before default-equivalence, same-process ordered restoration and candidate validation. Original workspace, binary and live-bound scripts untouched.'))
print(dict(built=True,binary=str(out/'bin/vpr'),seconds=time.monotonic()-start),flush=True)
