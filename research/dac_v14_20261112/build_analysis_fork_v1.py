#!/usr/bin/env python3
"""Build an isolated pre-route native analysis fork observer, preserving all active versions."""
import os,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

src=D/'analysis_fork_workspace_01';out=D/'analysis_fork_stage_01';out.mkdir(exist_ok=False)
assert shutil.disk_usage(D).free>=80*1024**3
baseline=read(D/'timing_cone_stage_03/binding.json')
for name,h in baseline['source_sha256'].items():assert sha(D/'timing_cone_workspace_01'/name)==h,name
names=set(baseline['source_sha256'])|{'vpr/src/timing/h3d_native_timing_echo.h','vpr/src/base/h3d_analysis_fork.h'}
bound={n:sha(src/n) for n in sorted(names)}
changed=[n for n in baseline['source_sha256'] if bound[n]!=baseline['source_sha256'][n]]
assert sorted(changed)==['vpr/src/base/vpr_api.cpp'],changed
for n in names:
 target=out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/n,target)
all_sources={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file() and 'build' not in p.relative_to(src).parts and (p.suffix in ['.h','.hpp','.hxx','.c','.cpp','.cc','.cmake'] or p.name in ['Makefile','CMakeLists.txt'])}
write(out/'all_source_hashes.json',all_sources)
params='-DVPR_EXECUTION_ENGINE=serial -DTATUM_EXECUTION_ENGINE=serial -DVPR_ENABLE_INTERCHANGE=OFF -DVPR_USE_SERVER=OFF -DVTR_ENABLE_CAPNPROTO=OFF -DVPR_USE_EZGL=off -DVTR_IPO_BUILD=off -DVTR_ASSERT_LEVEL=2 -DWITH_ABC=OFF -DWITH_ODIN=OFF -DWITH_PARMYS=OFF -DWITH_MOSAIC=OFF -DWITH_BLIFEXPLORER=OFF'
cmd=['prlimit','--as='+str(64*1024**3),'--','make','-j8','vpr','CMAKE_PARAMS='+params]
write(out/'registration.json',dict(status='registered_before_build',workspace=str(src),command=cmd,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bound,all_sources_sha256=sha(out/'all_source_hashes.json'),question='Amortize packing, placement and RRG load across private serial native FULLSTA workers forked before route loading and pin synchronization. Every child performs the entire existing route LOAD, FULL check, pin synchronization, physical delay recomputation and STA. Parent state is isolated by copy-on-write; child failure must not contaminate the next worker.',limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),original_frozen_sources_unchanged=True))
start=time.monotonic();env=dict(os.environ,PWD=str(src));timeout=False
with (out/'build.log').open('w') as f:
 process=subprocess.Popen(cmd,cwd=src,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=process.wait(timeout=1800)
 except subprocess.TimeoutExpired:
  timeout=True;os.killpg(process.pid,signal.SIGTERM)
  try:code=process.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);code=process.wait()
write(out/'build_result.json',dict(returncode=code,timed_out=timeout,complete_build_seconds=time.monotonic()-start))
assert code==0 and not timeout,'Preserve failed build for diagnosis'
assert all(sha(src/n)==h for n,h in all_sources.items())
assert all(sha(D/'timing_cone_workspace_01'/n)==h for n,h in baseline['source_sha256'].items())
(out/'bin').mkdir();shutil.copy2(src/'build/vpr/vpr',out/'bin/vpr');shutil.copy2(src/'build/CMakeCache.txt',out/'CMakeCache.txt')
assert b'VPR_H3D_ANALYSIS_FORK_MANIFEST' in (out/'bin/vpr').read_bytes()
write(out/'binding.json',dict(status='built_not_native_validated',source_sha256=bound,binary_sha256=sha(out/'bin/vpr'),all_source_manifest_sha256=sha(out/'all_source_hashes.json'),cmake_cache_sha256=sha(out/'CMakeCache.txt'),build_log_sha256=sha(out/'build.log'),qualification='Independent full source/build workspace; baseline untouched. Pre-route-load copy-on-write analysis worker equivalence, native pin synchronization, child failure isolation and full-precision STA pending. No quality change intended or speedup claimed by build success.'))
print(dict(status='built',stage=str(out),seconds=time.monotonic()-start),flush=True)
