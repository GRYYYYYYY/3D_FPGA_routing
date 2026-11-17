"""Snapshot the real failure and read-only diagnosis without staging live work."""
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

repo=D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()

parent=git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent=='5ab74de45190ae224f54bb78a4b4db6b34d575bb'
assert git('ls-remote','origin','refs/heads/research/dac-snapshot-20261113').split()[0]==parent
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
binding=read(D/'CP1r3_lstm_native_failure_claim_binding_01.json')
assert binding['passed'] and not binding['paper_benefit_claims_authorized'] and binding['quality'] is None
assert all(sha(p)==h for p,h in binding['source_sha256'].items())
priority=read(D/'confirmation_priority_handoff_02/plan.json')
assert all(sha(p)==h for p,h in priority['protected_source_sha256'].items())
files=[repo/n for n in ['README.md','docs/GitHub_research_status_20261117.md',
    'docs/github_CP1r3_native_failure_publication_receipt_20261117.json',
    'docs/github_CP1r3_native_failure_readback_20261117.json',
    'docs/github_balanced_cost_paper_publication_receipt_20261116.json',
    'docs/github_balanced_cost_paper_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py',
    'render_current_status_md_v1.py','audit_lstm_first_scope_mechanism_01.py','verify_cp1r3_native_failure_publication_30.py','audit_CP1r3_lstm_native_binding_failure_01.py',
    'snapshot_CP1r3_lstm_native_resource_phase_01.py','owner_registration_transition_v1.py',
    'cp1r3_supplemental_verifier_v1.py','validate_cp1r3_supplemental_verifier_01.py',
    'seal_cp1r3_native_failure_claims_01.py','CP1r3_lstm_native_failure_claim_binding_01.json',
    'prepare_research_status_publication_31.py']]
for directory in [D/'LSTM_first_scope_mechanism_audit_01',D/'research_status_snapshot_20261117_01',D/'CP1r3_lstm_native_binding_failure_audit_01',D/'CP1r3_lstm_native_resource_phase_01',
                  D/'CP1r3_supplemental_verifier_01',D/'CP1r3_supplemental_verifier_validation_01']:
    assert not (directory/'cases').exists()
    files += [p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
for stage in priority['stages']:
    queue=Path(stage['new_queue'])
    files += [queue/n for n in ['registration.json','status.json','completion.json'] if (queue/n).exists()]
scratch=Path(tempfile.mkdtemp(prefix='research-status-20261117-',
    dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known={row.split()[2] for row in git('ls-tree','-r',parent).splitlines()}
entries=[];manifest=[];reused=0
for source in sorted(set(files)):
    assert source.stat().st_size<4*1024**2
    data=source.read_bytes();relative=str(source.relative_to(repo))
    target=scratch/'files'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=relative,mode='100644',type='blob')
    if blob in known:entry['sha']=blob;reused+=1
    else:entry['content']=data.decode('utf-8')
    entries.append(entry);manifest.append(dict(path=relative,git_blob=blob,sha256=sha(target),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries,binary_uploads=[]))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),
    payload_bytes=sum(x['bytes'] for x in manifest),reused_existing_blobs=reused,novel_binary_blobs=0,
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),
    remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_research_status_prepared_20261117.json',info)
write(repo/'docs/github_research_status_manifest_20261117.json',manifest)
print(dict(info,payload_json_chars=len((scratch/'payload.json').read_text())))
