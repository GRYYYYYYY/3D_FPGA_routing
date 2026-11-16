"""Publish the concrete post-audit preparation registration, without experiment results."""
import hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*a):return subprocess.check_output(['git','-c','gc.auto=0',*a],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='ef6ca1259b4e67301039a95930bd9e1abb022688'
files=[repo/n for n in ['README.md','docs/GitHub_cohort_mechanism_20261116.md','docs/github_cohort_mechanism_publication_receipt_20261116.json','docs/github_cohort_mechanism_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py','prepare_confirmation_release_cp1r3.py','queue_confirmation_release_cp1r3_01.py','prepare_precision_registration_publication_16.py','confirmation_release_cp1r3_01/plan.json','confirmation_release_cp1r3_01/queue/registration.json','confirmation_release_cp1r3_01/queue/status.json']]
scratch=Path(tempfile.mkdtemp(prefix='precision-registration-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[]
for f in files:
    data=f.read_bytes();rel=str(f.relative_to(repo));dest=scratch/'files'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();entries.append(dict(path=rel,mode='100644',type='blob',content=data.decode()))
    manifest.append(dict(path=rel,git_blob=blob,sha256=sha(dest),bytes=len(data)))
payload=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries);write(scratch/'payload.json',payload)
info=dict(parent=parent,base_tree=payload['base_tree'],scratch=str(scratch),selected_files=len(files),payload_bytes=sum(x['bytes'] for x in manifest),live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_precision_registration_prepared_20261116.json',info);write(repo/'docs/github_precision_registration_manifest_20261116.json',manifest);print(info)
