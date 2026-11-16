"""Publish narrower prior-art wording and attribution map; preserve live jobs/index."""
import base64, hashlib, subprocess, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo=D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent=='4d85fd65c7089b9e2b7d7a6a809fbddd5377a283'
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
binding=read(D/'sharing_prior_art_paper_binding_18.json');assert binding['passed'] and binding['pages']==6
assert all(sha(p)==h for p,h in binding['source_sha256'].items())
snapshot=Path(binding['snapshot']);seal=read(snapshot/'snapshot_binding.json')
assert all(sha(snapshot/p)==h for p,h in seal['files'].items())
assert sha(D/'paper/current_repair_main.tex')==sha(snapshot/'current_repair_main.tex')
files=[repo/n for n in ['README.md','docs/GitHub_sharing_prior_art_20261116.md',
    'docs/github_BNN_timing03_domain0_publication_receipt_20261116.json','docs/github_BNN_timing03_domain0_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py',
    'update_sharing_prior_art_paper_18.py','seal_sharing_prior_art_paper_18.py','BNN_timing03_domain0_claim_binding_01.json',
    'prepare_sharing_prior_art_publication_26.py','sharing_prior_art_paper_binding_18.json','paper/current_repair_main.tex',
    'paper/current_repair_sharing_prior_art_18.tex','paper/data/evidence_v14_ledger.json']]
for folder in ['sharing_prior_art_paper_evidence_18','BNN_timing03_domain0_receipt_01']:
    files += [p for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [p for p in snapshot.rglob('*') if p.is_file()]
priority=read(D/'confirmation_priority_handoff_02/plan.json')
assert all(sha(p)==h for p,h in priority['protected_source_sha256'].items())
files += [Path(k).resolve() for k in read(D/'sharing_prior_art_paper_evidence_18/evidence_scope_bindings.json')['source_sha256']]
files.append(repo/'docs/github_sharing_prior_art_prepare_failure_01_20261116.json')
for q in [D/'BNN_interleaved_timing_03/queue',*[Path(x['new_queue']) for x in priority['stages']]]:
    files += [q/n for n in ['registration.json','status.json','completion.json'] if (q/n).exists()]
known={row.split()[2] for row in git('ls-tree','-r',parent).splitlines()}
scratch=Path(tempfile.mkdtemp(prefix='sharing-prior-art-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[];binaries={};reused=0
for f in sorted(set(files)):
    data=f.read_bytes();relative=str(f.relative_to(repo));dest=scratch/'files'/relative
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=relative,mode='100644',type='blob')
    if blob in known:
        entry['sha']=blob;reused+=1
    else:
        try:entry['content']=data.decode('utf-8')
        except UnicodeDecodeError:
            entry['sha']=blob
            binaries.setdefault(blob,dict(sha=blob,content=base64.b64encode(data).decode(),bytes=len(data)))
    entries.append(entry)
    manifest.append(dict(path=relative,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
write(scratch/'binary_payload.json',list(binaries.values()))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),
    payload_bytes=sum(x['bytes'] for x in manifest),reused_existing_blobs=reused,new_binary_blobs=len(binaries),
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_sharing_prior_art_prepared_20261116.json',info)
write(repo/'docs/github_sharing_prior_art_manifest_20261116.json',manifest)
print(dict(info,payload_json_chars=len((scratch/'payload.json').read_text()),binary_json_chars=len((scratch/'binary_payload.json').read_text())))
