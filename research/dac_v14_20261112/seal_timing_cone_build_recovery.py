#!/usr/bin/env python3
"""Bind successful existing build output after a packaging-path failure; no rebuild."""
import shutil
from retained_prefix_workflow import D,read,write,sha
src=D/'timing_cone_workspace_01';out=D/'timing_cone_stage_02';r=read(out/'build_result.json')
assert r['returncode']==0 and not r['timed_out'];assert not (out/'binding.json').exists()
assert all(sha(src/n)==h for n,h in read(out/'all_source_hashes.json').items())
baseline=read(D/'native_objective_stage_01/binding.json');assert all(sha(D/'src'/n)==h for n,h in baseline['source_sha256'].items())
binary=src/'build/vpr/vpr';assert binary.is_file()
shutil.copy2(binary,out/'bin/vpr');shutil.copy2(src/'build/CMakeCache.txt',out/'CMakeCache.txt')
assert b'VPR_H3D_FINAL_TIMING_ECHO' in (out/'bin/vpr').read_bytes()
write(out/'recovery_receipt.json',dict(passed=True,compiled_binary=str(binary),binary_sha256=sha(binary),native_calls=0,new_build_calls=0,source_sha256={str(p):sha(p) for p in [D/'seal_timing_cone_build_recovery.py',out/'packaging_failure.json',out/'build_result.json',out/'build.log']}))
write(out/'binding.json',dict(status='built_not_native_validated',source_sha256=read(out/'registration.json')['source_sha256'],binary_sha256=sha(out/'bin/vpr'),all_source_manifest_sha256=sha(out/'all_source_hashes.json'),cmake_cache_sha256=sha(out/'CMakeCache.txt'),build_log_sha256=sha(out/'build.log'),recovery_receipt_sha256=sha(out/'recovery_receipt.json'),qualification='Compilation succeeded; actual build/vpr/vpr recovered without rebuild. Original frozen source/binaries unchanged. Off/on native validation pending.'))
print(dict(passed=True,binary_sha256=sha(binary),new_build_calls=0))
