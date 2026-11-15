"""Verify and snapshot the six-page C195-C196 manuscript against the new archive."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

from verify_completed_seed_transfer_evidence_01 import verify_evidence
verify_evidence()
pair=read(D/'complete_serial_pair_comparison_01.json');assert pair['passed'] and pair['initial_ordered_route_and_full_vector_exact']
assert all(sha(f)==h for f,h in pair['source_sha256'].items())
assert pair['paired_minus_native_resources']==dict(wirelength=164,SB_pairs=-2,CB_sources=-3)
for f in ['complete_serial_seed_policy_dev_01/comparison.json','direct_completed_roles_validation_01/completion.json','complete_serial_cache_comparison_01.json','Tf_fixed_seed_resource_closure_01.json','completed_seed_transfer_summary_02.json']:
    v=read(D/f);assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items())
p=D/'paper';archive=D/'multiobjective_complete_seed_policy_02'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==453
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_16.json')
assert projection['passed'] and projection['observations']==297 and projection['unique_quality_tuples']==181
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_complete_seed_policy_01/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
points=read(archive/'points.json')
tokens=['290.19','289.21','289.66','1.274','1.302','1.297','101.02','100.33','1804.56','legalcandidates','2061257','2.487','409.82','3755.45','453','2076038','6752.95','221.11','226.35','67.38','66.12','288.49','292.47','217214','2070629','217183','2061377','5046.61','7099.32','1721','Archive453','297BNN','181plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:t in text for t in tokens};assert all(checks.values()),checks
log=p/'build_complete_seed_policy_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C196 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C196.tex';assert not version.exists();shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186','C187','C188','C189','C190','C191','C192','C193','C194','C195','C196'],pages=6,archive=str(archive),records=453,
    projection_observations=297,projection_coordinates=181,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),D/'verify_completed_seed_transfer_evidence_01.py',D/'feedback_exchange_candidates_validation_01/completion.json',D/'controller_feedback_closure_01.json',D/'complete_serial_seed_policy_dev_01/comparison.json',D/'direct_completed_roles_validation_01/completion.json',D/'complete_serial_pair_comparison_01.json',D/'complete_serial_cache_comparison_01.json',D/'Tf_fixed_seed_resource_closure_01.json',D/'completed_seed_transfer_summary_02.json',source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'points.json',archive/'complete_flow_summaries.json',
        p/'data/joint_quality_projection_binding_16.json',D/'completed_seed_transfer_summary_01.json',D/'R1_fixed_seed_resource_mechanism_01.json',pdf,log]},
    qualification='Six-page formal development manuscript, all current figures/tables and text checked against completed evidence. Prior C183/C186 snapshots preserved. Six completed roles on two circuits; R1/Tf native comparators pending. Tf final quality dominated by an existing strong-A0 point. Three complete current-binary explicit-seed configurations bind actual quality/time/memory. Legacy serial-cache costs remain separate. Direct scope preserves all16 legal candidates for three roles, fourth still live. Complete pooled-strategy time, native checkpoint recovery and broader confirmation remain outstanding.')
write(p/'complete_seed_policy_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_complete_seed_policy_20261115';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'complete_seed_policy_pdf_validation_01.json',
       p/'data/joint_quality_projection_16.pdf',p/'data/joint_quality_projection_16.png',
       p/'data/joint_quality_projection_16.csv',p/'data/joint_quality_projection_binding_16.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'complete_seed_policy_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',archive/'complete_flow_summaries.json',p/'data/joint_quality_projection_binding_16.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
