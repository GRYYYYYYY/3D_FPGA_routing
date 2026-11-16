"""Snapshot the original second-arm verifier and live successor without reruns."""
import hashlib, subprocess, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
repo=D.parents[1]
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent=='594c66d58adb6ada371a4b0c7030340b0a6b6043'
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
receipt=read(D/'BNN_timing03_domain0_receipt_01/completion.json')
assert receipt['passed'] and receipt['actual_complete_verifier_passed'] and not receipt['verifier_rerun']
assert receipt['complete_command_seconds']==9146.35149198398 and receipt['paired_domain_over_native_ratio'] is None
assert all(sha(p)==h for p,h in receipt['source_sha256'].items())
claim=read(D/'BNN_timing03_domain0_claim_binding_01.json');assert all(sha(p)==h for p,h in claim['source_sha256'].items())
priority=read(D/'confirmation_priority_handoff_02/plan.json')
assert all(sha(p)==h for p,h in priority['protected_source_sha256'].items())
files=[repo/n for n in ['README.md','docs/GitHub_BNN_timing03_domain0_20261116.md',
    'docs/github_input_seed_publication_receipt_20261116.json','docs/github_input_seed_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py',
    'snapshot_BNN_timing03_domain0_receipt_01.py','BNN_timing03_domain0_claim_binding_01.json','prepare_BNN_domain0_publication_25.py']]
files += [p for p in (D/'BNN_timing03_domain0_receipt_01').rglob('*') if p.is_file()]
case=D/'BNN_interleaved_timing_03/domain_0'
files += [case/n for n in ['completion.json','flow/completion.json','flow/stages.json','measurement/completion.json','environment_before.json','environment_after.json']]
files += [D/'BNN_interleaved_timing_03/queue/results.json']
for q in [D/'BNN_interleaved_timing_03/queue',*[Path(s['new_queue']) for s in priority['stages']]]:
    files += [q/n for n in ['registration.json','status.json','completion.json'] if (q/n).exists()]
for rel in ['queue/registration.json','measurement/registration.json','flow/registration.json','flow/active_child.json']:
    p=D/'BNN_interleaved_timing_03/domain_1'/rel
    if p.exists():files.append(p)
scratch=Path(tempfile.mkdtemp(prefix='BNN-timing03-domain0-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known={r.split()[2] for r in git('ls-tree','-r',parent).splitlines()};entries=[];manifest=[];reused=0
for f in sorted(set(files)):
    data=f.read_bytes();relative=str(f.relative_to(repo));dest=scratch/'files'/relative
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();entry=dict(path=relative,mode='100644',type='blob')
    if blob in known:entry['sha']=blob;reused+=1
    else:entry['content']=data.decode()
    entries.append(entry);manifest.append(dict(path=relative,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),
    payload_bytes=sum(x['bytes'] for x in manifest),reused_existing_blobs=reused,live_head=git('rev-parse','HEAD'),
    live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_BNN_timing03_domain0_prepared_20261116.json',info)
write(repo/'docs/github_BNN_timing03_domain0_manifest_20261116.json',manifest)
print(dict(info,payload_json_chars=len((scratch/'payload.json').read_text())))
