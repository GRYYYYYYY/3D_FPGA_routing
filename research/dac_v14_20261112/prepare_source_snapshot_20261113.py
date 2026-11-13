#!/usr/bin/env python3
"""Create independently apply-checked source patches without touching frozen repos."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];SRC=D/'src';VENDOR=Path(read(D/'origin.json')['source']);OUT=ROOT/'patches/snapshot_20261113'
def run(args,**kw):return subprocess.check_output(args,**kw).decode().strip()
def patch_component(repo,work,base,present,dest):
    gitdir=run(['git','-C',str(repo),'rev-parse','--absolute-git-dir']);objects=Path(gitdir)/'objects'
    with tempfile.TemporaryDirectory(prefix='fpga-source-snapshot-') as temporary:
        db=Path(temporary)/'objects.git';subprocess.run(['git','init','--bare','--quiet',str(db)],check=True)
        env=dict(os.environ,GIT_DIR=str(db),GIT_WORK_TREE=str(work),GIT_ALTERNATE_OBJECT_DIRECTORIES=str(objects));cmd=['git']
        subprocess.run(cmd+['read-tree',base],env=env,check=True)
        data=b''.join(p.encode()+b'\0' for p in sorted(present));subprocess.run(cmd+['add','-f','--pathspec-from-file=-','--pathspec-file-nul'],env=env,input=data,check=True)
        tree=run(cmd+['write-tree'],env=env)
        patch=subprocess.check_output(cmd+['diff','--cached','--binary','--no-ext-diff',base],env=env)
        dest.write_bytes(patch)
        names=run(cmd+['diff','--cached','--name-only','--diff-filter=ACM',base],env=env).splitlines();expected={p:sha(work/p) for p in names}
        subprocess.run(cmd+['read-tree',base],env=env,check=True)
        subprocess.run(cmd+['apply','--cached','--check',str(dest.resolve())],env=env,check=True)
        subprocess.run(cmd+['apply','--cached',str(dest.resolve())],env=env,check=True)
        restored=run(cmd+['write-tree'],env=env);assert tree==restored
        for p,h in expected.items():assert hashlib.sha256(subprocess.check_output(cmd+['show',':'+p],env=env)).hexdigest()==h
        return dict(base_commit=base,patch=str(dest.relative_to(ROOT)),patch_sha256=sha(dest),target_tree=tree,apply_restored_tree=restored,changed_files_sha256=expected,present_input_files=len(present),passed=True)
def main():
    OUT.mkdir(exist_ok=False);base=run(['git','-C',str(VENDOR),'rev-parse','HEAD']);assert base=='0b912334fdd83bb754b302146ac0d1ec9edc9a0e'
    records=run(['git','-C',str(VENDOR),'ls-tree','-r',base]).splitlines();modules={r.split('\t')[1]:r.split()[2] for r in records if r.startswith('160000 ')}
    paths=set(read(D/'baseline_source_sha256.json'));paths.update(read(D/'outside_native_stage_01/binding.json')['source_sha256'])
    present={p for p in paths if (SRC/p).is_file()};mainfiles={p for p in present if not any(p.startswith(m+'/') for m in modules)}
    result=dict(status='source_snapshot_apply_verified_not_pushed',upstream_url='https://github.com/verilog-to-routing/vtr-verilog-to-routing.git',main=patch_component(VENDOR,SRC,base,mainfiles,OUT/'architecture_outside_native.patch'),submodules={},source_stage='outside_native_stage_01',stage_binding_sha256=sha(D/'outside_native_stage_01/binding.json'))
    for module,commit in modules.items():
        files={p[len(module)+1:] for p in present if p.startswith(module+'/')}
        if not files:continue
        repo=VENDOR/module;head=run(['git','-C',str(repo),'rev-parse','HEAD']);assert head==commit,('submodule_head_diff',module,head,commit)
        result['submodules'][module]=patch_component(repo,SRC/module,commit,files,OUT/(module.rsplit('/',1)[-1]+'.patch'))
    write(OUT/'manifest.json',result);print(dict(main_changed=len(result['main']['changed_files_sha256']),submodule_changes={k:len(v['changed_files_sha256']) for k,v in result['submodules'].items()},passed=True))
if __name__=='__main__':main()
