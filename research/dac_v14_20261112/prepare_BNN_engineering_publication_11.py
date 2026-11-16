"""Prepare immutable GitHub API payload without touching the live Git index."""
import base64, hashlib, json, subprocess, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent = git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent == '7fb0552ff881088c960e37cbf1a2b6a07a258441'
base = git('rev-parse',parent+'^{tree}')
blobset = {line.split()[2] for line in git('ls-tree','-r',parent).splitlines() if line.split()[1]=='blob'}
snap = Path(read(D/'BNN_engineering_paper_binding_11.json')['snapshot'])
r = D/'complete_BNN_domain_engineering_01'; c = r/'bnn_domain_closed_stream'
files = [repo/'README.md',repo/'docs/GitHub_BNN_engineering_complete_20261116.md',
    repo/'docs/github_complete_tradeoff_paper_publication_receipt_20261116.json',repo/'docs/github_complete_tradeoff_paper_readback_20261116.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'BNN_engineering_paper_binding_11.json','update_BNN_engineering_paper_11.py','seal_BNN_engineering_paper_11.py',
    'prepare_BNN_engineering_publication_11.py','paper/current_repair_main.tex','paper/current_repair_BNN_engineering_11.tex','paper/data/evidence_v14_ledger.json']]
files += [f for root in [snap,D/'BNN_engineering_paper_evidence_11'] for f in root.rglob('*') if f.is_file()]
files += [r/n for n in ['plan.json','admission.json','comparison.json','domain_downstream_equivalence.json','historical_domain_final_endpoints.json',
    'historical_native_final_endpoints.json','queue/registration.json','queue/results.json','queue/completion.json','queue/status.json']]
files += [c/n for n in ['config.json','completion.json','metadata_consumers.json','measurement/completion.json','flow/completion.json',
    'flow/resource_flow/completion.json','flow/resource_flow/repair/completion.json','flow/timing/completion.json']]
scratch = Path(tempfile.mkdtemp(prefix='BNN-engineering-complete-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[]; binaries={}; manifest=[]
for f in sorted(set(files)):
    assert f.is_file(),f
    data=f.read_bytes(); rel=str(f.relative_to(repo))
    dst=scratch/'files'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    entry=dict(path=rel,mode='100644',type='blob')
    if blob in blobset: entry['sha']=blob
    else:
        try: entry['content']=data.decode('utf-8')
        except UnicodeDecodeError:
            entry['sha']=blob;binaries[blob]=base64.b64encode(data).decode()
    entries.append(entry)
    manifest.append(dict(path=rel,git_blob=blob,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
payload=dict(parent=parent,base_tree=base,entries=entries,binaries=binaries)
write(scratch/'payload.json',payload)
info=dict(parent=parent,base_tree=base,scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),
    payload_json_bytes=(scratch/'payload.json').stat().st_size,live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),
    remote_main=git('ls-remote','origin','refs/heads/main').split()[0],unique_new_binary_blobs=len(binaries))
write(repo/'docs/github_BNN_engineering_complete_prepared_20261116.json',info)
write(repo/'docs/github_BNN_engineering_complete_manifest_20261116.json',manifest)
print(info)
