#!/usr/bin/env python3
"""Build the independent queue with the unchanged native resource-domain kernel."""
import os,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
src=D/'domain_failure_release_workspace_01';out=D/'domain_failure_release_stage_01';out.mkdir(exist_ok=False);prep=read(D/'domain_failure_release_preparation_01.json');assert all(sha(p)==h for p,h in prep['source_sha256'].items());baseline=read(D/'native_repair_queue_stage_01/binding.json');names=set(baseline['source_sha256'])|{'vpr/src/route/h3d_joint_native_repair.h','vpr/src/base/h3d_analysis_queue.h'};bound={n:sha(src/n) for n in sorted(names)}
all_sources={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file() and 'build' not in p.relative_to(src).parts and (p.suffix in ['.h','.hpp','.hxx','.c','.cpp','.cc','.cmake'] or p.name in ['Makefile','CMakeLists.txt'])};write(out/'all_source_hashes.json',all_sources)
for n in names:
 target=out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/n,target)
params='-DVPR_EXECUTION_ENGINE=serial -DTATUM_EXECUTION_ENGINE=serial -DVPR_ENABLE_INTERCHANGE=OFF -DVPR_USE_SERVER=OFF -DVTR_ENABLE_CAPNPROTO=OFF -DVPR_USE_EZGL=off -DVTR_IPO_BUILD=off -DVTR_ASSERT_LEVEL=2 -DWITH_ABC=OFF -DWITH_ODIN=OFF -DWITH_PARMYS=OFF -DWITH_MOSAIC=OFF -DWITH_BLIFEXPLORER=OFF';cmd=['prlimit','--as='+str(64*1024**3),'--','make','-j8','vpr','CMAKE_PARAMS='+params];write(out/'registration.json',dict(status='registered_before_build',workspace=str(src),command=cmd,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bound,all_sources_sha256=sha(out/'all_source_hashes.json'),question='Does opt-in automatic per-net domain failure release preserve default search and actual occupancy/transaction recovery? Original analysis-only requests remain valid. This is engineering reuse, no new search primitive or acceptance.',qualification='Independent new build, never changes currently registered quality actors; defaults and native physical Tdel remain.',limits=dict(seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
started=time.monotonic();env=dict(os.environ,PWD=str(src));timeout=False
with (out/'build.log').open('w') as f:
 proc=subprocess.Popen(cmd,cwd=src,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=proc.wait(timeout=1800)
 except subprocess.TimeoutExpired:
  timeout=True;os.killpg(proc.pid,signal.SIGTERM)
  try:code=proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
write(out/'build_result.json',dict(returncode=code,timed_out=timeout,complete_build_seconds=time.monotonic()-started));assert code==0 and not timeout
assert all(sha(src/n)==h for n,h in all_sources.items());(out/'bin').mkdir();shutil.copy2(src/'build/vpr/vpr',out/'bin/vpr');shutil.copy2(src/'build/CMakeCache.txt',out/'CMakeCache.txt');assert b'VPR_JOINT_NATIVE_REQUEST' in(out/'bin/vpr').read_bytes()
write(out/'binding.json',dict(status='built_not_native_validated',source_sha256=bound,binary_sha256=sha(out/'bin/vpr'),all_source_manifest_sha256=sha(out/'all_source_hashes.json'),cmake_cache_sha256=sha(out/'CMakeCache.txt'),build_log_sha256=sha(out/'build.log'),qualification='Automatic domain-failure release built; default-off, tiny guided failure/free retry, mixed child isolation, and matched BNN candidate/STA equivalence pending. Build success is no QoR or runtime claim.'))
print(dict(status='built',seconds=time.monotonic()-started),flush=True)
