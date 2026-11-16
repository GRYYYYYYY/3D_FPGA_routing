"""Snapshot selected research files without changing the live index or branch."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

base = Path(__file__).resolve().parents[1]
D = base/'research/dac_v14_20261112'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
write = lambda p,v: p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
binding = read(D/'qualified_complete_paper_binding_08.json')
assert len(binding['visual_review']) and binding['visual_review']['passed']
assert all(sha(Path(p)) == h for p,h in binding['source_sha256'].items())
parent = '612b764586afd32e236d615e3b73cfcf088b19de'
branch = 'research/dac-snapshot-20261113'
git = lambda *args: subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=base,text=True).strip()
assert git('ls-remote','origin','refs/heads/'+branch).split()[0] == parent
assert subprocess.run(['git','merge-base','--is-ancestor','9734eee',parent],cwd=base).returncode == 0
scratch = Path(tempfile.mkdtemp(prefix='complete-inputs-publication-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
selected = [base/'README.md',base/'docs/GitHub_complete_inputs_progress_20261116.md',Path(__file__).resolve()]
selected += [D/n for n in ['CURRENT_STATUS.md','CURRENT_STATUS.json','refresh_current_status_20261114.py','render_current_status_md_v1.py',
    'audit_complete_input_rows_07.py','update_complete_input_paper_07.py','seal_complete_input_paper_07.py','complete_input_paper_binding_07.json',
    'paper/current_repair_main.tex','paper/current_repair_complete_inputs_07.tex',
    'paper/current_repair_qualified_inputs_08.tex','qualified_complete_paper_binding_08.json','update_qualified_complete_paper_08.py','seal_qualified_complete_paper_08.py',
    'BNN_terminal_wire_qualified_comparison_02/completion.json','BNN_terminal_wire_qualified_comparison_02/resource_prefix.json','BNN_terminal_wire_qualified_comparison_02/final_endpoints.json',
    'BNN_terminal_wire_qualified_comparison_02/analysis/completion.json','standalone_whole_method_check_01/completion.json','standalone_whole_method_check_01/queue/completion.json',
    'unified_input_integration_01/comparison.json','unified_input_integration_01/queue/results.json','unified_input_integration_01/queue/completion.json',
    'unified_input_integration_01/analysis/completion.json','unified_input_integration_01/robot_50MHz.sdc',
    'unified_input_integration_01/measurement_environment_note_01.json',
    'audit_attention_initial_failure_pair_01.py','attention_initial_failure_pair_01/completion.json','attention_initial_failure_pair_01/queue_results_at_analysis.json',
    'publication_housekeeping_20261116_01/intervention.json','publication_housekeeping_20261116_01/verification.json',
    'standalone_native_observation_equivalence_01/completion.json','standalone_native_observation_equivalence_01/queue/completion.json',
    'prepare_portable_reduction_pair_01.py','admit_portable_reduction_pair_01.py','queue_portable_reduction_pair_01.py',
    'run_portable_reduction_pair_01.py','compare_portable_reduction_pair_01.py']]
for role in ['attention_native','attention_domain','robot_s23_SDC_native','robot_s23_SDC_domain']:
    case = D/'unified_input_integration_01'/role
    selected += [case/'config.json',case/'measurement/completion.json']
    if (case/'completion.json').exists():selected.append(case/'completion.json')
for rel in ['complete_input_paper_evidence_07','qualified_complete_paper_evidence_08','portable_reduction_pair_01']:
    selected.extend(sorted((D/rel).glob('*.json')))
for rel in ['standalone_transaction_native_check_01/completion.json','standalone_transaction_native_check_01/queue/completion.json']:
    if (D/rel).exists():selected.append(D/rel)
snap = Path(binding['snapshot'])
selected += [snap/n for n in ['current_repair_main.tex','IEEEtran.cls','build/current_repair_main.pdf','build/build.log','claims_evidence.json','snapshot_binding.json','data/complete_table_rows.json','data/scoped_component_rows.json','data/new_complete_input_rows.json','data/joint_quality_projection_34.pdf']]
files = {}
for source in dict.fromkeys(selected):
    assert source.is_file(),source
    rel = str(source.relative_to(base))
    target = scratch/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    payload = target.read_bytes()
    digest = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
    files[rel] = dict(sha256=sha(target),bytes=len(payload),mode='100644',git_blob=digest)
metadata = dict(parent=parent,base_tree=git('rev-parse',parent+'^{tree}'),branch=branch,
    live_head=git('rev-parse','HEAD'),live_index_sha256=sha(base/'.git/index'),
    remote_main_before=git('ls-remote','origin','refs/heads/main').split()[0],scratch=str(scratch),files=files,
    public_evidence_base='9734eee',research_complete=False,
    qualification='Selected manuscript, receipts and continuation records; no full raw-data backup. No live index, checkout or experimental source replacement.')
manifest = base/'docs/github_complete_inputs_manifest_20261116.json'
write(manifest,metadata)
target=scratch/manifest.relative_to(base);target.parent.mkdir(exist_ok=True);shutil.copy2(manifest,target)
payload=target.read_bytes()
files[str(manifest.relative_to(base))]=dict(sha256=sha(target),bytes=len(payload),mode='100644',git_blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest())
write(base/'docs/github_complete_inputs_prepared_20261116.json',metadata)
print(json.dumps(dict(scratch=str(scratch),files=len(files),bytes=sum(v['bytes'] for v in files.values()),parent=parent)))
