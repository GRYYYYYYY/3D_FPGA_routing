#!/usr/bin/env python3
"""Export the two exact private TU variants as reviewed overlays of the verified Census source."""
import difflib,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/dac_v14_20261112';OUT=ROOT/'patches/snapshot_20261115_verified'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
OUT.mkdir(exist_ok=False)
base_manifest=ROOT/'patches/snapshot_20261114_verified/manifest.json';prior=json.loads(base_manifest.read_text());base=prior['stages']['native_resource_census_stage_01']
assert sha(ROOT/base['patch'])==base['patch_sha256']
workspace=D/'native_resource_census_workspace_01'
for name,h in base['changed_files_sha256'].items():assert sha(workspace/name)==h
records={}
for stage_name in ['source_snapshot_stage_01','crossing_source_stage_01']:
 stage=D/stage_name;binding=json.loads((stage/'binding.json').read_text());variants={};normalizations=[]
 raw=stage/'vpr_api.cpp';data=raw.read_text();assert sha(raw)==binding['source_sha256'][str(raw)]
 raw_target=OUT/'exact_built_sources'/stage_name/'vpr_api.cpp';raw_target.parent.mkdir(parents=True);raw_target.write_bytes(raw.read_bytes())
 if stage_name=='crossing_source_stage_01':
  header=stage/'h3d_joint_native_repair.h';assert sha(header)==binding['source_sha256'][str(header)]
  literal='#include "'+str(header)+'"';assert data.count(literal)==1
  data=data.replace(literal,'#include "h3d_joint_native_repair.h"')
  variants['vpr/src/route/h3d_joint_native_repair.h']=header.read_bytes()
  (raw_target.parent/header.name).write_bytes(header.read_bytes())
  normalizations.append(dict(kind='include_path_only',original_include=str(header),portable_include='h3d_joint_native_repair.h',header_exact_sha256=sha(header),qualification='Private build used an absolute include pointing at this exact header. Portable overlay places those identical bytes at the normal route header path; no algorithm code is changed.'))
 variants['vpr/src/base/vpr_api.cpp']=data.encode();patch=''
 for name,value in sorted(variants.items()):
  original=(workspace/name).read_bytes();patch+=''.join(difflib.unified_diff(original.decode().splitlines(True),value.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 patch_path=OUT/(stage_name+'.patch');patch_path.write_text(patch)
 with tempfile.TemporaryDirectory(prefix='vpr-private-overlay-check-') as temp:
  dest=Path(temp)
  for name in variants:
   p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((workspace/name).read_bytes())
  subprocess.run(['git','apply','--check',str(patch_path)],cwd=dest,check=True,capture_output=True)
  subprocess.run(['git','apply',str(patch_path)],cwd=dest,check=True,capture_output=True)
  assert all((dest/name).read_bytes()==value for name,value in variants.items())
 records[stage_name]=dict(passed=True,parent_patch=base['patch'],parent_patch_sha256=base['patch_sha256'],overlay_patch=str(patch_path.relative_to(ROOT)),overlay_patch_sha256=sha(patch_path),portable_target_files_sha256={n:hashlib.sha256(v).hexdigest() for n,v in variants.items()},exact_built_source_files={str(p.relative_to(ROOT)):sha(p) for p in raw_target.parent.iterdir()},normalizations=normalizations,stage_binding_sha256=sha(stage/'binding.json'),original_binary_sha256=binding['binary_sha256'],roundtrip_applied_to_exact_baseline_files=True,binary_rebuild_performed=False)
write(OUT/'manifest.json',dict(passed=True,upstream=prior['upstream'],base_commit=prior['base_commit'],baseline_manifest=str(base_manifest.relative_to(ROOT)),baseline_manifest_sha256=sha(base_manifest),overlays=records,qualification='Apply the verified20261114Census base patch first, then exactly one private overlay. Exact original built TU/header bytes and binary identities are retained separately. Crossing-source overlay normalizes one machine-specific include path only. Delta application and target bytes are verified; no rebuild or bitwise binary reproduction is claimed. Live source/build directories and processes are untouched.'))
print(json.dumps({'passed':True,'overlays':list(records),'live_sources_unchanged':True}))
