"""Publish mechanism-context evidence and six reviewed pages, preserving live work."""
import base64,hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*a):return subprocess.check_output(['git','-c','gc.auto=0',*a],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='dc1f70983464ee40884fb072a30494be8c9ba0f1'
base=git('rev-parse',parent+'^{tree}');blobset={line.split()[2] for line in git('ls-tree','-r',parent).splitlines() if line.split()[1]=='blob'}
snap=Path(read(D/'mechanism_trigger_paper_binding_16.json')['snapshot'])
files=[repo/n for n in ['README.md','docs/GitHub_mechanism_selection_20261116.md','docs/github_prefix_recovery_publication_receipt_20261116.json','docs/github_prefix_recovery_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'build_mechanism_selection_evidence_01.py','verify_release_coverage_01.py','recommend_current_mechanisms_v1.py','validate_mechanism_triage_01.py','validate_mechanism_triage_02.py',
    'update_mechanism_trigger_paper_16.py','seal_mechanism_trigger_paper_16.py','mechanism_trigger_paper_binding_16.json','prepare_mechanism_selection_publication_18.py',
    'paper/current_repair_main.tex','paper/current_repair_mechanism_triggers_16.tex','paper/data/evidence_v14_ledger.json']]
folders=[snap,*[D/n for n in ['mechanism_trigger_paper_evidence_16','mechanism_selection_evidence_01','release_coverage_01','mechanism_triage_validation_01','mechanism_triage_validation_02']]]
for folder in folders:files += [f for f in folder.rglob('*') if f.is_file() and '__pycache__' not in f.parts]
scratch=Path(tempfile.mkdtemp(prefix='mechanism-selection-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];binaries={};manifest=[]
for f in sorted(set(files)):
    data=f.read_bytes();rel=str(f.relative_to(repo));dest=scratch/'files'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();entry=dict(path=rel,mode='100644',type='blob')
    if blob in blobset:entry['sha']=blob
    else:
        try:entry['content']=data.decode('utf-8')
        except UnicodeDecodeError:entry['sha']=blob;binaries[blob]=base64.b64encode(data).decode()
    entries.append(entry);manifest.append(dict(path=rel,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=base,entries=entries,binaries=binaries))
info=dict(parent=parent,base_tree=base,scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),payload_json_bytes=(scratch/'payload.json').stat().st_size,live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0],unique_new_binary_blobs=len(binaries))
write(repo/'docs/github_mechanism_selection_prepared_20261116.json',info);write(repo/'docs/github_mechanism_selection_manifest_20261116.json',manifest);print(info)
