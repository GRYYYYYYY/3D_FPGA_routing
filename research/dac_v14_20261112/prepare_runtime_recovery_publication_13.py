"""Prepare immutable GitHub API payload without touching the live Git index."""
import base64, hashlib, json, subprocess, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()
parent = git('rev-parse','origin/research/dac-snapshot-20261113')
assert parent == '6240af82534c1f261272c4cb5e916ab97ea7eaca'
base = git('rev-parse',parent+'^{tree}')
blobset = {line.split()[2] for line in git('ls-tree','-r',parent).splitlines() if line.split()[1]=='blob'}
snap = Path(read(D/'runtime_recovery_paper_binding_13.json')['snapshot'])
files = [repo/'README.md',repo/'docs/GitHub_runtime_recovery_20261116.md',repo/'docs/github_BNN_interleaved_registration_publication_receipt_20261116.json',repo/'docs/github_BNN_interleaved_registration_readback_20261116.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py','supervise_method_phase_v2.py','validate_method_phase_proc_race_02.py','reconcile_proc_race_20261116_01.py','prepare_unexecuted_successors_20261116_02.py','queue_robot_union_mechanism_02.py','verify_robot_union_mechanism_02.py','verify_robot_union_mechanism_02_v2.py','queue_robot_union_verification_recovery_01.py','queue_BNN_interleaved_timing_02.py','queue_BNN_interleaved_timing_03.py','update_proc_race_paper_12.py','seal_proc_race_paper_12.py','update_runtime_recovery_paper_13.py','seal_runtime_recovery_paper_13.py','proc_race_paper_binding_12.json','runtime_recovery_paper_binding_13.json','prepare_runtime_recovery_publication_13.py','paper/current_repair_main.tex','paper/current_repair_proc_race_12.tex','paper/current_repair_runtime_recovery_13.tex','paper/data/evidence_v14_ledger.json','confirmation_cp1_wheels_requirements.txt']]
files += list(D.glob('*cp1r*.py'))
for folder in [snap,D/'proc_race_paper_evidence_12',D/'runtime_recovery_paper_evidence_13',D/'method_phase_proc_race_validation_02',D/'execution_reconciliation_20261116_01',D/'CP1r1_packaging_failure_01',D/'confirmation_release_cp1r1_01',D/'confirmation_release_cp1r2_01']:
    files += [p for p in folder.rglob('*') if p.is_file()]
old_snap=Path(read(D/'proc_race_paper_binding_12.json')['snapshot'])
files += [old_snap/n for n in ['current_repair_main.tex','build/current_repair_main.pdf','build/build.log','claims_evidence.json','snapshot_binding.json']]
for name in ['portable_reduction_pair_01','clstm_input_contract_pair_02','robot_p1_input_contract_pair_02','cp1_cross_circuit_cohort_01','cp1r1_cross_circuit_cohort_01','cp1r2_cross_circuit_cohort_01','robot_union_mechanism_01','robot_union_mechanism_02','robot_union_verification_recovery_01','BNN_interleaved_timing_01','BNN_interleaved_timing_02','BNN_interleaved_timing_03']:
    root=D/name
    names=['plan.json','preflight.json','launch.json','comparison.json','results.json','active_child.json','conv_hls_comparison.json','tpu_ws_comparison.json','conv_hls_results.json','tpu_ws_results.json','supervision.json','measurement/completion.json','queue/registration.json','queue/status.json','queue/completion.json','queue/results.json','queue/execution_receipt.json','queue/verification.log','prepared_transaction_registration.json','union_request.txt','shared_only_domain.txt','transaction/completion.json','transaction/execution_registration.json','transaction/process_costs.json','transaction/registration.json']
    files += [root/n for n in names if (root/n).is_file()]
    files += list((root/'configs').glob('*.json')) if (root/'configs').exists() else []
    files += list(root.glob('*_config.json'))+list(root.glob('*_manifest.json'))+list(root.glob('*_runtime.json'))
scratch = Path(tempfile.mkdtemp(prefix='runtime-recovery-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
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
write(repo/'docs/github_runtime_recovery_prepared_20261116.json',info)
write(repo/'docs/github_runtime_recovery_manifest_20261116.json',manifest)
print(info)
