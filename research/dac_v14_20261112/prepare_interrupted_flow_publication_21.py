"""Snapshot actual implemented/queued four-arm continuations without new results."""
import hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='279bdb4d2793471bf7b0434e249c4672daabaae3'
files=[repo/n for n in ['README.md','docs/GitHub_interrupted_flow_dispatch_20261116.md','docs/github_interrupted_stage_publication_receipt_20261116.json','docs/github_interrupted_stage_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'same_actor_stage_reuse_v1.py','same_actor_timing_prefix_v1.py','generate_interrupted_stage_adapters_01.py','validate_same_actor_stage_reuse_01.py',
    'prepare_interrupted_flow_dispatch_01.py','run_interrupted_full_flow_recovery_v1.py','admit_interrupted_flow_recovery_01.py',
    'queue_interrupted_full_flow_recovery_01.py','validate_interrupted_flow_dispatch_01.py','preregister_interrupted_full_flow_recovery_01.py','prepare_interrupted_flow_publication_21.py']]
for folder in ['interrupted_stage_adapter_01','interrupted_flow_recovery_01']:
    files += [p for p in (D/folder).rglob('*') if p.is_file() and p.name not in ['owner.lock','owner.log'] and '__pycache__' not in p.parts]
protocol=read(D/'interrupted_flow_recovery_01/protocol.json');assert all(sha(p)==h for p,h in protocol['source_sha256'].items())
scratch=Path(tempfile.mkdtemp(prefix='interrupted-flow-dispatch-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[]
for f in sorted(set(files)):
    data=f.read_bytes();relative=str(f.relative_to(repo));dest=scratch/'files'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entries.append(dict(path=relative,mode='100644',type='blob',content=data.decode()));manifest.append(dict(path=relative,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_interrupted_flow_prepared_20261116.json',info);write(repo/'docs/github_interrupted_flow_manifest_20261116.json',manifest);print(info)
