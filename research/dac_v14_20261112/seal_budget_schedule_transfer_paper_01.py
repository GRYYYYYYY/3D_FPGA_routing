"""Verify and snapshot the six-page C200-C201 manuscript against the new archive."""
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
for f in ['connection_budget_scope_probe_01/verification.json','complete_serial_lazy_transfer_dev_01/comparison.json','complete_serial_fused_dev_03/comparison.json','complete_serial_lazy_dev_01/comparison.json','lazy_resource_scheduling_validation_01/completion.json','complete_serial_transfer_dev_01/comparison.json','complete_serial_seed_policy_dev_01/comparison.json','direct_completed_roles_validation_01/completion.json','complete_serial_cache_comparison_01.json','Tf_fixed_seed_resource_closure_01.json','completed_seed_transfer_summary_02.json']:
    v=read(D/f);assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items())
p=D/'paper';archive=D/'multiobjective_budget_and_lazy_transfer_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==473
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_19.json')
assert projection['passed'] and projection['observations']==299 and projection['unique_quality_tuples']==183
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_budget_schedule_transfer_01/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
points=read(archive/'points.json')
tokens=['2061036','2061213','2061285','177','948.00','51.31','60.11','271.70','93.15','203.48','313.74','85.74','29.65','41.90','1.296','1.310','91.69','91.55','274.22','336.68','169486','148463','62.46','1.010','1.034','2.502','2.534','290.19','289.21','289.66','1.274','1.302','1.297','101.02','100.33','1804.56','legalcandidates','2061257','2.487','409.82','3755.45','473','2076038','6752.95','221.11','226.35','67.38','66.12','288.49','292.47','217214','2070629','217183','2061377','5046.61','7099.32','1721','Archive473','299BNN','183plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:t in text for t in tokens};assert all(checks.values()),checks
log=p/'build_budget_schedule_transfer_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C201 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C201.tex';assert not version.exists();shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186','C187','C188','C189','C190','C191','C192','C193','C194','C195','C196','C197','C198','C199','C200','C201'],pages=6,archive=str(archive),records=473,
    projection_observations=299,projection_coordinates=183,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),D/'verify_completed_seed_transfer_evidence_01.py',D/'feedback_exchange_candidates_validation_01/completion.json',D/'controller_feedback_closure_01.json',D/'connection_budget_scope_probe_01/verification.json',D/'complete_serial_lazy_transfer_dev_01/comparison.json',D/'complete_serial_fused_dev_03/comparison.json',D/'complete_serial_lazy_dev_01/comparison.json',D/'lazy_resource_scheduling_validation_01/completion.json',D/'complete_serial_transfer_dev_01/comparison.json',D/'complete_serial_seed_policy_dev_01/comparison.json',D/'direct_completed_roles_validation_01/completion.json',D/'complete_serial_pair_comparison_01.json',D/'complete_serial_cache_comparison_01.json',D/'Tf_fixed_seed_resource_closure_01.json',D/'completed_seed_transfer_summary_02.json',source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'points.json',archive/'complete_flow_summaries.json',
        p/'data/joint_quality_projection_binding_19.json',D/'completed_seed_transfer_summary_01.json',D/'R1_fixed_seed_resource_mechanism_01.json',pdf,log]},
    qualification='Six-page formal development manuscript, all current figures/tables and text checked against completed evidence. Prior C183/C186 snapshots preserved. Six completed roles on two circuits; R1/Tf native comparators pending. Tf final quality dominated by an existing strong-A0 point. Eleven complete current-binary configurations on three circuits bind actual quality/time/memory. Additional SPMV has zero eligible cuts and no intervention; both softmax controls save three SB and four wire at unchanged CPD, without extra domain quality gain. Prior known-circuit diagnostics preclude an unseen-test claim; broader repeated/seed/architecture confirmation remains outstanding. Fused callback complete313.74s is slower than289.21s independent-STA in this observation. ON-first acceptance schedule costs203.48s with identical committed trajectory and no inferred skipped OFF results. Lazy scheduling also preserves actual softmax states at271.70s versus336.68s; zero-scope SPMV has no observed benefit. Budget64 single-scope guided candidate yields new nondominated47SB/2061036wire point, native matched scope degrades to49SB;947.998s is shared imported scope time, not complete algorithm cost. All are single shared-host development observations. Legacy serial-cache costs remain separate. Direct scope preserves all16 legal candidates for three roles, fourth still live. Complete pooled-strategy time, native checkpoint recovery and broader confirmation remain outstanding.')
write(p/'budget_schedule_transfer_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_budget_schedule_transfer_20261115';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'budget_schedule_transfer_pdf_validation_01.json',
       p/'data/joint_quality_projection_19.pdf',p/'data/joint_quality_projection_19.png',
       p/'data/joint_quality_projection_19.csv',p/'data/joint_quality_projection_binding_19.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'budget_schedule_transfer_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',archive/'complete_flow_summaries.json',p/'data/joint_quality_projection_binding_19.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
