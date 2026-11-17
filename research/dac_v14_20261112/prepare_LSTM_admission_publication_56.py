"""Snapshot terminal LSTM admission and the 06-derived author-review manuscript."""
import base64
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo=D.parents[1]
parent='c304f2bb79a6636c1abeef7c758856791b8a15e5'
branch='research/dac-snapshot-20261113'
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
assert git('ls-remote','origin','refs/heads/'+branch).split()[0]==parent
assert git('rev-parse','HEAD')=='b132a1d13eec8351cfcdc371bfc03611f678291b'
assert sha(repo/'.git/index')=='fa24adce1cf6f0f4b5da3210992aaac9eeae18b08c42df414aed562490d7574c'
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,parent],cwd=repo,check=True)
for name in ['submission_candidate_01','submission_narrative_02','submission_narrative_03',
             'submission_narrative_04','submission_narrative_05','submission_narrative_06','submission_narrative_07']:
    proof=read(D/name/'verification.json');assert proof['passed'] and proof['pages']==6
    assert all(sha(p)==h for p,h in proof['source_sha256'].items())
for path in [D/'LSTM_domain_whole_admission_03/execution_plan.json',D/'CP1r3_supplemental_verifier_03/plan.json',
             D/'vertical_cost_baseline_dev_01/execution_plan.json']:
    assert all(sha(p)==h for p,h in read(path)['source_sha256'].items())
decision=read(D/'LSTM_domain_whole_admission_03/admission_decision.json')
assert decision['formal_complete_time_ratio'] is None and decision['original_failed_candidate_remains_failed']
files=[repo/'README.md',repo/'docs/GitHub_LSTM_admission_submission_20261117.md',
       repo/'docs/github_GEMM_LSTM_submission_publication_receipt_20261117.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py',
    'render_current_status_md_v1.py','lstm_failed_scope_audit_v1.py','cp1r3_supplemental_verifier_v3.py',
    'audit_lstm_domain_raw_03.py','match_lstm_admitted_pair_03.py','queue_lstm_domain_whole_admission_03.py',
    'validate_lstm_domain_whole_admission_03.py','finalize_LSTM_submission_07.py','prepare_LSTM_admission_publication_56.py']]
for name in ['LSTM_domain_whole_admission_03','LSTM_domain_whole_scope_reconciliation_01',
             'CP1r3_supplemental_verifier_03','submission_narrative_07']:
    files += [p for p in (D/name).rglob('*') if p.is_file()
              and p.name not in ['memory_samples.jsonl','owner.lock']
              and (not p.is_relative_to(D/'submission_narrative_07/build')
                   or p.name in ['main.pdf','build_receipt.json','text_check.json','contact_sheet.jpg','table_page_4.png','table_page_5.png'])]
scratch=Path(tempfile.mkdtemp(prefix='LSTM-admission56-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known={line.split()[2] for line in git('ls-tree','-r',parent).splitlines()}
entries=[];manifest=[];binaries={}
for path in sorted(set(files)):
    assert path.stat().st_size<3_000_000,(path,path.stat().st_size)
    data=path.read_bytes();relative=str(path.relative_to(repo));target=scratch/'files'/relative
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=relative,mode='100644',type='blob')
    if blob in known:entry['sha']=blob
    else:
        try:entry['content']=data.decode('utf-8')
        except UnicodeDecodeError:
            entry['sha']=blob;binaries[blob]=dict(sha=blob,content=base64.b64encode(data).decode(),source=relative)
    entries.append(entry);manifest.append(dict(path=relative,git_blob=blob,sha256=sha(target),bytes=len(data)))
payload=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries,binary_uploads=list(binaries.values()))
write(scratch/'payload.json',payload)
info=dict(parent=parent,base_tree=payload['base_tree'],scratch=str(scratch),files=len(manifest),
          bytes=sum(r['bytes'] for r in manifest),payload_chars=len((scratch/'payload.json').read_text()),
          binary_blobs=len(binaries),live_head=git('rev-parse','HEAD'),index_sha256=sha(repo/'.git/index'),
          remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_LSTM_admission56_prepared_20261117.json',info)
write(repo/'docs/github_LSTM_admission56_manifest_20261117.json',manifest)
print(info,flush=True)
