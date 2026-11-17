"""Publish reviewed narrative and bounded evidence without staging live work."""
import base64
import hashlib
import tempfile
import subprocess
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo=D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent='291c55a7cf43edd868c8049ec331a4530029b4dd'
assert git('ls-remote','origin','refs/heads/research/dac-snapshot-20261113').split()[0]==parent
assert git('rev-parse','HEAD')=='b132a1d13eec8351cfcdc371bfc03611f678291b'
assert sha(repo/'.git/index')=='fa24adce1cf6f0f4b5da3210992aaac9eeae18b08c42df414aed562490d7574c'
for name in ['submission_narrative_02','submission_candidate_01']:
    proof=read(D/name/'verification.json')
    assert proof['passed'] and proof['pages']==6
    assert all(sha(p)==h for p,h in proof['source_sha256'].items())
for name in ['confirmation_priority_handoff_02','confirmation_priority_handoff_03','confirmation_priority_handoff_04']:
    assert all(sha(p)==h for p,h in read(D/name/'plan.json')['protected_source_sha256'].items())
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
files=[repo/'README.md',repo/'docs/GitHub_submission_source_export_20261117.md',repo/'docs/github_closing_menu_inputs_publication_receipt_20261117.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py','export_submission_narrative_01.py','prepare_submission_export_publication_40.py']]
files += [p for p in (D/'submission_narrative_export_01').rglob('*') if p.is_file()]
assert read(D/'submission_narrative_export_01/completion.json')['passed']
scratch=Path(tempfile.mkdtemp(prefix='submission-source-export-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known={line.split()[2] for line in git('ls-tree','-r',parent).splitlines()}
entries=[];manifest=[];binaries={}
for p in sorted(set(files)):
    data=p.read_bytes();relative=str(p.relative_to(repo))
    target=scratch/'files'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=relative,mode='100644',type='blob')
    if blob in known:entry['sha']=blob
    else:
        try:
            if p.suffix in ['.pdf','.png','.zip']:raise ValueError('binary')
            entry['content']=data.decode('utf-8')
        except (UnicodeDecodeError,ValueError):
            entry['sha']=blob;binaries[blob]=dict(sha=blob,content=base64.b64encode(data).decode(),source=relative)
    entries.append(entry);manifest.append(dict(path=relative,git_blob=blob,sha256=sha(target),bytes=len(data)))
payload=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries,binary_uploads=list(binaries.values()))
write(scratch/'payload.json',payload)
info=dict(parent=parent,base_tree=payload['base_tree'],scratch=str(scratch),files=len(manifest),
    bytes=sum(x['bytes'] for x in manifest),payload_chars=len((scratch/'payload.json').read_text()),
    binary_blobs=len(binaries),live_head=git('rev-parse','HEAD'),index_sha256=sha(repo/'.git/index'),
    remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_submission_export_prepared_20261117.json',info)
write(repo/'docs/github_submission_export_manifest_20261117.json',manifest)
print(info)
