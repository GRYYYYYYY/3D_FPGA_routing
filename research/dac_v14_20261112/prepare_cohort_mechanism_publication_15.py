"""Snapshot selected reviewable artifacts for GitHub; preserve live index/HEAD."""
import base64,hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent=='2af7efba60334445903bd4b3d2f9195650dfe189'
base=git('rev-parse',parent+'^{tree}');blobset={line.split()[2] for line in git('ls-tree','-r',parent).splitlines() if line.split()[1]=='blob'}
snap=Path(read(D/'cohort_mechanism_paper_binding_15.json')['snapshot'])
files=[repo/'README.md',repo/'docs/GitHub_cohort_mechanism_20261116.md',repo/'docs/github_CP1r2_first_pair_publication_receipt_20261116.json',repo/'docs/github_CP1r2_first_pair_readback_20261116.json']
names=['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
 'seal_CP1r2_cohort_outcomes_01.py','cohort_mechanism_paper_binding_15.json','update_cohort_mechanism_paper_15.py','tighten_cohort_mechanism_paper_15.py','finalize_cohort_layout_15.py','seal_cohort_mechanism_paper_15.py','prepare_cohort_mechanism_publication_15.py',
 'paper/current_repair_main.tex','paper/current_repair_cohort_mechanism_15.tex','paper/data/evidence_v14_ledger.json',
 'cp1r2_cross_circuit_cohort_01/comparison.json','cp1r2_cross_circuit_cohort_01/tpu_ws_comparison.json','cp1r2_cross_circuit_cohort_01/tpu_ws_results.json',
 'robot_union_mechanism_02/verification_v2.json','robot_union_mechanism_02/transaction/completion.json','robot_union_mechanism_02/transaction/process_costs.json','robot_union_mechanism_02/measurement/completion.json','robot_union_mechanism_02/supervision.json',
 'audit_robot_owner_reentry_02.py','queue_robot_owner_reentry_audit_02.py','observation_timing_identity_v1.py','observation_timing_identity_v2.py','prepare_observation_precision_patch_02.py',
 'prepare_empty_query_patch_01.py','replay_empty_query_worker_01.py','validate_empty_query_patch_01.py','queue_empty_query_patch_validation_01.py']
files += [D/n for n in names]
folders=[snap,D/'cohort_mechanism_paper_evidence_15',D/'cp1r2_cross_circuit_cohort_01/terminal_evidence_01',D/'cp1r2_cross_circuit_cohort_01/tpu_ws_native_timeout_evidence_01',D/'robot_owner_reentry_audit_01',D/'robot_owner_reentry_audit_02',D/'observation_timing_identity_validation_02',D/'observation_precision_patch_02',D/'empty_query_patch_01',D/'empty_query_patch_validation_01']
for folder in folders:
    for f in folder.rglob('*'):
        if f.is_file() and '__pycache__' not in f.parts and f.stat().st_size<4_000_000:files.append(f)
for batch in ['cp1r2_cross_circuit_cohort_01','robot_union_mechanism_02','robot_union_verification_recovery_01','BNN_interleaved_timing_03']:
    for f in (D/batch/'queue').glob('*'):
        if f.is_file() and f.stat().st_size<100_000:files.append(f)
scratch=Path(tempfile.mkdtemp(prefix='cohort-mechanism-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];binaries={};manifest=[]
for f in sorted(set(files)):
    assert f.is_file(),f
    data=f.read_bytes();rel=str(f.relative_to(repo));dst=scratch/'files'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();entry=dict(path=rel,mode='100644',type='blob')
    if blob in blobset:entry['sha']=blob
    else:
        try:entry['content']=data.decode('utf-8')
        except UnicodeDecodeError:entry['sha']=blob;binaries[blob]=base64.b64encode(data).decode()
    entries.append(entry);manifest.append(dict(path=rel,git_blob=blob,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=base,entries=entries,binaries=binaries))
info=dict(parent=parent,base_tree=base,scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),payload_json_bytes=(scratch/'payload.json').stat().st_size,
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0],unique_new_binary_blobs=len(binaries))
write(repo/'docs/github_cohort_mechanism_prepared_20261116.json',info);write(repo/'docs/github_cohort_mechanism_manifest_20261116.json',manifest);print(info)
