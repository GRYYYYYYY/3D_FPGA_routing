#!/usr/bin/env python3
"""Create a review branch via a private index; never push or change checkout."""
import hashlib,os,subprocess,tempfile,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1]
def git(args,**kw):return subprocess.check_output(['git']+args,cwd=ROOT,**kw)
def main():
    manifest=ROOT/'docs/github_snapshot_manifest_20261113.json';r=read(manifest);assert r['verified_visibility']=='public'
    paths=list(r['selected_files'])+['docs/github_snapshot_manifest_20261113.json','docs/github_snapshot_paths_20261113.txt'];paths=sorted(set(paths))
    for p,v in r['selected_files'].items():assert sha(ROOT/p)==v['sha256'],p
    parent=git(['rev-parse','HEAD']).decode().strip();assert parent=='b132a1d13eec8351cfcdc371bfc03611f678291b'
    with tempfile.TemporaryDirectory(prefix='fpga-git-review-index-') as tmp:
        index=Path(tmp)/'index';env=dict(os.environ,GIT_INDEX_FILE=str(index));subprocess.run(['git','read-tree',parent],cwd=ROOT,env=env,check=True)
        data=b''.join((':(literal)'+p).encode()+b'\0' for p in paths);subprocess.run(['git','-c','core.autocrlf=false','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],cwd=ROOT,env=env,input=data,check=True)
        tree=git(['write-tree'],env=env).decode().strip();staged=git(['ls-files','--stage','-z'],env=env);objects={}
        for entry in staged.split(b'\0'):
            if not entry:continue
            fields,path=entry.split(b'\t',1);objects[path.decode()]=fields.split()[1].decode()
        ids=[objects[p] for p in paths];raw=git(['cat-file','--batch'],input=('\n'.join(ids)+'\n').encode());offset=0
        for p in paths:
            end=raw.index(b'\n',offset);header=raw[offset:end].split();size=int(header[2]);body=raw[end+1:end+1+size];assert hashlib.sha256(body).hexdigest()==sha(ROOT/p),('staged_blob_mismatch',p);offset=end+2+size
        assert offset==len(raw)
        message=Path(tmp)/'message.txt';message.write_text('Preserve DAC routing development evidence through native outside-DP verification\n\nSave apply-verified main-source patch, protocols, selected sealed results, both paper sources and timing breakdowns. Outside DP has no observed QoR gain; transaction and best-state checks pass. Raw large data remain on shared storage. This is a local review snapshot; public publication scope is pending.\n')
        commit=git(['commit-tree',tree,'-p',parent,'-F',str(message)],env=env).decode().strip();branch='research/dac-snapshot-20261113'
        if subprocess.run(['git','show-ref','--verify','--quiet','refs/heads/'+branch],cwd=ROOT).returncode==0:raise RuntimeError('Review branch exists; do not overwrite it')
        subprocess.run(['git','update-ref','refs/heads/'+branch,commit,'0'*40],cwd=ROOT,check=True)
    assert git(['rev-parse','HEAD']).decode().strip()==parent
    receipt=dict(passed=True,status='local_review_commit_created_not_pushed',created_at=time.time(),branch=branch,commit=commit,parent=parent,tree=tree,files_added_or_updated=len(paths),selected_payload_bytes=r['selected_bytes'],manifest_sha256=sha(manifest),all_selected_staged_blobs_verified=True,working_branch_unchanged=True,remote='GRYYYYYYY/3D_FPGA_routing',verified_remote_visibility='public',publication_scope_pending=True,qualification='New local branch only. User asked status/ETA; public release of unpublished manuscript/detailed evidence requires scope choice. No remote push/ref/repo-visibility mutation. Main checkout/index left unchanged; raw large data stay on shared storage.')
    write(D/'github_local_review_commit_20261113.json',receipt);write(ROOT/'docs/github_local_review_commit_20261113.json',receipt);print({k:receipt[k] for k in ['status','branch','commit','files_added_or_updated','selected_payload_bytes']})
if __name__=='__main__':main()
