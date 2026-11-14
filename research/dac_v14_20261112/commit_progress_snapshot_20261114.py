"""Create an isolated snapshot commit from frozen files; do not push or alter the live index."""
import hashlib
import os
from pathlib import Path
import subprocess
from retained_prefix_workflow import D,read,write,sha

ROOT=D.parents[1];gitdir=Path(subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=ROOT,text=True).strip())
out=gitdir/'progress_snapshot_20261114';prep=read(out/'preparation.json');assert prep['passed']
assert not prep['possible_sensitive_paths']
payload=out/'payload';parent=prep['parent'];branch='refs/heads/research/dac-snapshot-20261113'
assert subprocess.check_output(['git','rev-parse',branch],cwd=ROOT,text=True).strip()==parent
original_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
original_index=sha(gitdir/'index')
mp=ROOT/'docs/github_progress_manifest_20261114.json';manifest=read(mp)
readme=subprocess.check_output(['git','show',parent+':README.md'],cwd=ROOT)
notice=('> **2026-11-14 research progress:** [snapshot guide](docs/GitHub_progress_20261114.md), '
        '[current manuscript](research/dac_v14_20261112/paper_snapshots/current_strict_terminal_vector_feedback_20261114/build/current_repair_main.pdf), '
        '[335-observation joint archive](research/dac_v14_20261112/multiobjective_complete_resource_timing_01/points.csv). '
        'Research is ongoing; imported/recovery timings are separate from complete cold algorithm time.\n\n').encode()
extras={'README.md':notice+readme,str(Path(__file__).resolve().relative_to(ROOT)):Path(__file__).read_bytes()}
for rel,data in extras.items():
    target=payload/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    manifest['selected_files'][rel]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),reason='publication navigation or isolated commit procedure',source_mtime_ns=None)
manifest['selected_count']=len(manifest['selected_files']);manifest['selected_bytes']=sum(x['bytes'] for x in manifest['selected_files'].values())
write(mp,manifest);write(payload/mp.relative_to(ROOT),manifest)
paths=sorted(manifest['selected_files'])+[str(mp.relative_to(ROOT))]
(out/'paths.txt').write_text('\n'.join(paths)+'\n')
for rel,record in manifest['selected_files'].items():assert sha(payload/rel)==record['sha256'],rel
env=dict(os.environ,GIT_DIR=str(gitdir),GIT_WORK_TREE=str(payload),GIT_INDEX_FILE=str(out/'index'))
subprocess.run(['git','read-tree',parent],env=env,cwd=payload,check=True)
subprocess.run(['git','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=b''.join(p.encode()+b'\0' for p in paths),env=env,cwd=payload,check=True)
entries=subprocess.check_output(['git','ls-files','--stage','-z'],env=env,cwd=payload).split(b'\0')
objects={}
for entry in entries:
    if not entry:continue
    meta,path=entry.split(b'\t',1);mode,oid,stage=meta.split();assert stage==b'0'
    objects[path.decode()]=oid.decode()
expected=dict(manifest['selected_files']);expected[str(mp.relative_to(ROOT))]=dict(sha256=sha(mp))
batch=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for rel,record in expected.items():
    batch.stdin.write((objects[rel]+'\n').encode());batch.stdin.flush()
    header=batch.stdout.readline().split();assert len(header)==3 and header[1]==b'blob',(rel,header)
    remaining=int(header[2]);digest=hashlib.sha256()
    while remaining:
        data=batch.stdout.read(min(1024*1024,remaining));assert data;digest.update(data);remaining-=len(data)
    assert batch.stdout.read(1)==b'\n'
    assert digest.hexdigest()==record['sha256'],rel
batch.stdin.close();assert batch.wait()==0
tree=subprocess.check_output(['git','write-tree'],env=env,cwd=payload,text=True).strip()
message=out/'commit_message.txt'
message.write_text('Publish current STA repair, Pareto evidence and recovery progress\n\n'
    'Preserve 335 legal observations, strong native controls, current manuscript and detailed evidence, '
    'the new feedback transaction receipts, and explicit interrupted/recovered experiment status. '
    'Add independently apply-checked resource-domain, seed-order and native-census source overlays.\n\n'
    'Large raw data remain on the server with a scope manifest. Running experiments are untouched. '
    'No cold algorithm timing or overall research completion is claimed.\n')
commit=subprocess.check_output(['git','commit-tree',tree,'-p',parent,'-F',str(message)],cwd=ROOT,text=True).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==original_head
assert sha(gitdir/'index')==original_index
subprocess.run(['git','update-ref',branch,commit,parent],cwd=ROOT,check=True)
changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=ROOT,text=True).splitlines()
receipt=dict(passed=True,status='local_snapshot_commit_verified_not_yet_pushed',branch=branch,commit=commit,parent=parent,tree=tree,
    selected_files=len(paths),selected_payload_bytes=manifest['selected_bytes'],changed_files=len(changed),
    all_selected_staged_blobs_sha256_verified=True,live_index_unchanged=True,live_HEAD_unchanged=True,
    raw_data_backup_complete=False,research_complete=False,manifest_sha256=sha(mp))
write(ROOT/'docs/github_progress_local_commit_20261114.json',receipt)
print(receipt,flush=True)
