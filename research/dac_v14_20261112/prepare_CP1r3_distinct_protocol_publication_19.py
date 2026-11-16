"""Snapshot the actual deferred confirmation protocol, not unexecuted results."""
import hashlib,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1]
def git(*a):return subprocess.check_output(['git','-c','gc.auto=0',*a],cwd=repo).decode().strip()
parent=git('rev-parse','origin/research/dac-snapshot-20261113');assert parent=='62bf1d80ed8e9ef96282f9d1899180b05ef66eca'
files=[repo/n for n in ['README.md','docs/GitHub_CP1r3_distinct_protocol_20261116.md','docs/github_mechanism_selection_publication_receipt_20261116.json','docs/github_mechanism_selection_readback_20261116.json']]
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'select_new_circuit_inputs_02.py','verify_cp1r3_candidate_placement_01.py','generate_cp1r3_cohort_driver_01.py','cp1r3_confirmation_cohort_v1.py',
    'activate_cp1r3_distinct_input_cohort_01.py','package_cp1r3_public_source_01.py','preregister_cp1r3_distinct_input_cohort_01.py',
    'queue_cp1r3_distinct_input_cohort_01.py','seal_cp1r3_distinct_cohort_outcomes_01.py','validate_cp1r3_cohort_administration_01.py',
    'cp1r3_cohort_administration_revision_01.json','prepare_CP1r3_distinct_protocol_publication_19.py']]
for folder in ['cp1r3_distinct_input_cohort_01','cp1r3_cohort_administration_validation_01','independent_input_candidates_02']:
    files += [f for f in (D/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.stat().st_size<1_000_000]
scratch=Path(tempfile.mkdtemp(prefix='CP1r3-distinct-protocol-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
entries=[];manifest=[]
for f in sorted(set(files)):
    data=f.read_bytes();rel=str(f.relative_to(repo));dest=scratch/'files'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();entries.append(dict(path=rel,mode='100644',type='blob',content=data.decode()))
    manifest.append(dict(path=rel,git_blob=blob,sha256=sha(dest),bytes=len(data)))
write(scratch/'payload.json',dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),entries=entries))
info=dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),scratch=str(scratch),selected_files=len(manifest),payload_bytes=sum(x['bytes'] for x in manifest),
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(repo/'.git/index'),remote_main=git('ls-remote','origin','refs/heads/main').split()[0])
write(repo/'docs/github_CP1r3_distinct_protocol_prepared_20261116.json',info);write(repo/'docs/github_CP1r3_distinct_protocol_manifest_20261116.json',manifest);print(info)
