"""Prepare immutable GitHub API payload without touching the live Git index."""
import base64, hashlib, json, subprocess, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent = git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent == '87e98d683a2b67b97a80895819e446db4f4df20d'
base = git('rev-parse',parent+'^{tree}')
blobset = {line.split()[2] for line in git('ls-tree','-r',parent).splitlines() if line.split()[1]=='blob'}
snap=Path(read(D/'CP1r2_pair_paper_binding_14.json')['snapshot'])
files=[repo/'README.md',repo/'docs/GitHub_CP1r2_first_pair_20261116.md',repo/'docs/github_runtime_recovery_publication_receipt_20261116.json',repo/'docs/github_runtime_recovery_readback_20261116.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py','CP1r2_pair_paper_binding_14.json','update_CP1r2_pair_paper_14.py','seal_CP1r2_pair_paper_14.py','prepare_CP1r2_pair_publication_14.py','paper/current_repair_main.tex','paper/current_repair_CP1r2_pair_14.tex','paper/data/evidence_v14_ledger.json','cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json','cp1r2_cross_circuit_cohort_01/conv_hls_results.json','cp1r2_cross_circuit_cohort_01/queue/status.json']]
files += [f for folder in [snap,D/'CP1r2_pair_paper_evidence_14',D/'cp1r2_cross_circuit_cohort_01/conv_hls_native_evidence_01'] for f in folder.rglob('*') if f.is_file()]
scratch = Path(tempfile.mkdtemp(prefix='CP1r2-first-pair-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
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
write(repo/'docs/github_CP1r2_first_pair_prepared_20261116.json',info)
write(repo/'docs/github_CP1r2_first_pair_manifest_20261116.json',manifest)
print(info)
