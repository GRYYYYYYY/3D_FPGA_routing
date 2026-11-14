#!/usr/bin/env python3
"""Build an isolated read-only native timing observer, preserving frozen sources."""
import os,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

src=D/'reservation_workspace_02';out=D/'native_reservation_stage_04'
assert not src.exists() and not out.exists()
shutil.copytree(D/'reservation_workspace_01',src,symlinks=True,ignore=shutil.ignore_patterns('build','.git','__pycache__'))
header=src/'vpr/src/route/h3d_joint_native_repair.h';text=header.read_text();old='!trees.at(net)->find_by_isink(pin)';assert text.count(old)==2
text=text.replace(old,'!trees.at(net)->get_is_isink_reached().get(pin)');header.write_text(text)
write(D/'reservation_prune_index_recovery_01.json',dict(status='independent_fix_before_build',failed_native='pending_reservation_dev_02/A0_target_only_weighted_soft_reserve_on',failure='RouteTree::prune updates reached-bitset but does not clear sink pointer lookup; partial multi-sink pruning leaves a stale lookup entry',fix='Use the existing prune-maintained get_is_isink_reached().get(pin) for both pruned-tree membership checks; original unpruned copy continues supplying path nodes',old_stage='native_reservation_stage_03',new_stage='native_reservation_stage_04',existing_batch_unchanged=True,source_sha256={str(D/'reservation_workspace_01/vpr/src/route/route_tree.cpp'):sha(D/'reservation_workspace_01/vpr/src/route/route_tree.cpp'),str(D/'reservation_workspace_01/vpr/src/route/route_tree.h'):sha(D/'reservation_workspace_01/vpr/src/route/route_tree.h')}))
out.mkdir(exist_ok=False)
assert shutil.disk_usage(D).free>=80*1024**3
baseline=read(D/'timing_cone_stage_03/binding.json')
for name,h in baseline['source_sha256'].items():assert sha(D/'timing_cone_workspace_01'/name)==h,name
names=set(baseline['source_sha256'])|{'vpr/src/timing/h3d_native_timing_echo.h'}
bound={n:sha(src/n) for n in sorted(names)}
changed=[n for n in baseline['source_sha256'] if bound[n]!=baseline['source_sha256'][n]]
assert changed==['vpr/src/route/h3d_joint_native_repair.h'],changed
for n in names:
 target=out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/n,target)
all_sources={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file() and 'build' not in p.relative_to(src).parts and (p.suffix in ['.h','.hpp','.hxx','.c','.cpp','.cc','.cmake'] or p.name in ['Makefile','CMakeLists.txt'])}
write(out/'all_source_hashes.json',all_sources)
params='-DVPR_EXECUTION_ENGINE=serial -DTATUM_EXECUTION_ENGINE=serial -DVPR_ENABLE_INTERCHANGE=OFF -DVPR_USE_SERVER=OFF -DVTR_ENABLE_CAPNPROTO=OFF -DVPR_USE_EZGL=off -DVTR_IPO_BUILD=off -DVTR_ASSERT_LEVEL=2 -DWITH_ABC=OFF -DWITH_ODIN=OFF -DWITH_PARMYS=OFF -DWITH_MOSAIC=OFF -DWITH_BLIFEXPLORER=OFF'
cmd=['prlimit','--as='+str(64*1024**3),'--','make','-j8','vpr','CMAKE_PARAMS='+params]
write(out/'registration.json',dict(status='registered_before_build',workspace=str(src),command=cmd,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bound,all_sources_sha256=sha(out/'all_source_hashes.json'),question='Build disabled-by-default reservations of unprocessed critical target resources; release only own-net reserves during its search and clear all on success/rollback. Keep native Tdel/STA and final occupancy restoration.',limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),original_frozen_sources_unchanged=True))
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
assert b'VPR_JOINT_NATIVE_RESERVE_TARGETS' in (out/'bin/vpr').read_bytes()
write(out/'binding.json',dict(status='built_not_native_validated',source_sha256=bound,binary_sha256=sha(out/'bin/vpr'),all_source_manifest_sha256=sha(out/'all_source_hashes.json'),cmake_cache_sha256=sha(out/'CMakeCache.txt'),build_log_sha256=sha(out/'build.log'),qualification='Independent full source/build workspace; baseline untouched. Multi-sink prune/reached-bitset fix. Old stage03 source and running batch preserved. Requires regression reproducing the old assertion and a separately registered large-circuit recovery; no quality benefit claimed.'))
print(dict(status='built',stage=str(out),seconds=time.monotonic()-start),flush=True)
