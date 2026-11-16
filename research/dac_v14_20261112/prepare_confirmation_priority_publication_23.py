"""Snapshot applied scheduling priority and actual readonly complete-request proof."""
import hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='a897348abf54e0852611382e845848a2df4a6191'
for ref in ['9734eee','279bdb4']:subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
files=[repo/n for n in ['README.md','docs/GitHub_confirmation_priority_20261116.md','docs/github_BNN_timing03_native0_publication_receipt_20261116.json','docs/github_BNN_timing03_native0_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'prepare_confirmation_priority_handoff_02.py','confirmation_priority_waiter_guard_02.py','validate_confirmation_priority_handoff_02.py',
    'apply_confirmation_priority_handoff_02.py','cp1r3_priority_cohort_02.py','audit_interrupted_complete_requests_01.py',
    'interrupted_recovery_outcomes_01/DRAFT_STATUS.json','prepare_confirmation_priority_publication_23.py']]
priority=read(D/'confirmation_priority_handoff_02/plan.json');receipt=read(D/'confirmation_priority_handoff_02/completion.json');assert receipt['passed']
assert all(sha(p)==h for p,h in priority['protected_source_sha256'].items())
for path,row in priority['revisions'].items():assert sha(path)==row['sha256']
request=read(D/'interrupted_complete_request_audit_01/completion.json');assert request['passed'] and not request['full_stage_admission_passed']
assert all(sha(p)==h for p,h in request['source_sha256'].items())
for folder in ['confirmation_priority_handoff_02','interrupted_complete_request_audit_01']:
    files += [p for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
for node in priority['stages']:
    for q in [Path(node['old_queue']),Path(node['new_queue'])]:
        files += [q/name for name in ['registration.json','status.json','completion.json'] if (q/name).exists()]
scratch=Path(tempfile.mkdtemp(prefix='confirmation-priority-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[]
for f in sorted(set(files)):
    data=f.read_bytes();relative=str(f.relative_to(repo));dest=scratch/'files'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entries.append(dict(path=relative,mode='100644',type='blob',content=data.decode()));manifest.append(dict(path=relative,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_confirmation_priority_prepared_20261116.json',info);write(repo/'docs/github_confirmation_priority_manifest_20261116.json',manifest);print(info)
