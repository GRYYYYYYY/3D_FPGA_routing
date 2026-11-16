"""Publish the first real verified timing observation; preserve unfinished ratios."""
import hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='37a69a7c9e64b9e2dc95dbb3933b81cec89d7339'
files=[repo/n for n in ['README.md','docs/GitHub_BNN_timing03_first_native_20261116.md','docs/github_interrupted_flow_publication_receipt_20261116.json','docs/github_interrupted_flow_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'validate_interrupted_entrypoint_startup_01.py','snapshot_BNN_timing03_native0_receipt_01.py','snapshot_BNN_timing03_native0_receipt_02.py',
    'BNN_timing03_native0_receipt_01/failure.json','BNN_timing03_native0_receipt_01/failed_snapshot_source.py','prepare_BNN_timing03_native0_publication_22.py']]
for folder in ['BNN_timing03_native0_receipt_02','interrupted_entrypoint_startup_01']:
    files += [p for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
case=D/'BNN_interleaved_timing_03/native_0'
files += [case/n for n in ['completion.json','config.json','measurement/completion.json','flow/completion.json','flow/stages.json','flow/resource_flow/stages.json','metadata_consumers.json','environment_before.json','environment_after.json']]
receipt=read(D/'BNN_timing03_native0_receipt_02/completion.json');assert receipt['passed'] and receipt['paired_domain_over_native_ratio'] is None
assert all(sha(p)==h for p,h in receipt['source_sha256'].items())
assert read(D/'interrupted_entrypoint_startup_01/completion.json')['passed']
scratch=Path(tempfile.mkdtemp(prefix='BNN-timing03-native0-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[]
for f in sorted(set(files)):
    data=f.read_bytes();relative=str(f.relative_to(repo));dest=scratch/'files'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entries.append(dict(path=relative,mode='100644',type='blob',content=data.decode()));manifest.append(dict(path=relative,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_BNN_timing03_native0_prepared_20261116.json',info);write(repo/'docs/github_BNN_timing03_native0_manifest_20261116.json',manifest);print(info)
