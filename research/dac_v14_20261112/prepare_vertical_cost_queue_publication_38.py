"""Snapshot the actual registered queue and its development evidence."""
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

repo=D.parents[1]
def git(*a):return subprocess.check_output(['git','-c','gc.auto=0',*a],cwd=repo).decode().strip()
parent='bd949b916c5139c2bab799da35935b9decbf5a53'
assert git('ls-remote','origin','refs/heads/research/dac-snapshot-20261113').split()[0]==parent
assert read(D/'confirmation_priority_handoff_05/completion.json')['passed']
plan=read(D/'confirmation_priority_handoff_05/plan.json');assert all(sha(f)==h for f,h in plan['protected_source_sha256'].items())
for n in ['submission_candidate_01','submission_narrative_02']:
    assert all(sha(f)==h for f,h in read(D/n/'verification.json')['source_sha256'].items())
files=[repo/n for n in ['README.md','docs/GitHub_vertical_cost_queue_20261117.md',
    'docs/github_dependency_narrative_publication_receipt_20261117.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py',
 'render_current_status_md_v1.py','vertical_cost_evidence_v1.py','vertical_cost_evidence_v2.py',
 'run_vertical_cost_baseline_v2.py','validate_vertical_cost_evidence_01.py','validate_vertical_cost_evidence_02.py',
 'validate_vertical_cost_evidence_04.py','validate_vertical_cost_controller_03.py','prepare_vertical_cost_backend_01.py',
 'prepare_confirmation_priority_handoff_05.py','apply_confirmation_priority_handoff_05.py',
 'queue_vertical_cost_baseline_priority_05.py','prepare_vertical_cost_queue_publication_38.py']]
for n in ['vertical_cost_baseline_dev_01','vertical_cost_evidence_validation_01','vertical_cost_evidence_validation_02',
 'vertical_cost_evidence_validation_04','vertical_cost_controller_validation_03','LSTM_round012_rejection_01','confirmation_priority_handoff_05']:
    files += [f for f in (D/n).rglob('*') if f.is_file() and f.suffix!='.lock' and '__pycache__' not in f.parts]
for n in ['interrupted_stage_reconciliation_01','robot_p1_prefix_recovery_01','interrupted_flow_recovery_01','empty_query_patch_validation_01']:
    for q in ['queue_priority_04','queue_priority_05']:
        files += [f for f in (D/n/q).glob('*.json') if f.is_file()]
scratch=Path(tempfile.mkdtemp(prefix='vertical-cost-queue-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[];known={l.split()[2] for l in git('ls-tree','-r',parent).splitlines()}
for p in sorted(set(files)):
    assert p.stat().st_size<4*1024**2
    data=p.read_bytes();rel=str(p.relative_to(repo));target=scratch/'files'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=rel,mode='100644',type='blob')
    if blob in known:entry['sha']=blob
    else:entry['content']=data.decode('utf-8')
    entries.append(entry);manifest.append(dict(path=rel,git_blob=blob,sha256=sha(target),bytes=len(data)))
payload=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries)
write(scratch/'payload.json',payload)
info=dict(parent=parent,base_tree=payload['base_tree'],scratch=str(scratch),files=len(manifest),bytes=sum(x['bytes'] for x in manifest),
 payload_chars=len((scratch/'payload.json').read_text()),live_head=git('rev-parse','HEAD'),index_sha256=sha(repo/'.git/index'),
 remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_vertical_cost_queue_prepared_20261117.json',info)
write(repo/'docs/github_vertical_cost_queue_manifest_20261117.json',manifest);print(info)
