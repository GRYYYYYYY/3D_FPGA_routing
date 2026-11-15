import unicodedata
"""Verify and snapshot the six-page C211 manuscript against the new archive."""
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
for f in ['R1_whole_net_residual_probe_01/verification.json','complete_serial_seed_transfer_01/comparison.json','budget47_current_timing_composition_01/comparison.json','BNN_vertical_cut_bound_01/completion.json','budget47_first_timing_transfer_validation_01/completion.json','budget47_native_timing_terminal_validation_01/completion.json','census_completed_roles_validation_02/completion.json','multiobjective_R1_whole_net_probe_01/completion.json','cb_terminal_cut_bound_01/completion.json','complete_serial_architecture_transfer_01/comparison.json','lazy_real_fallback_validation_01/completion.json','connection_budget_scope_probe_01/verification.json','complete_serial_lazy_transfer_dev_01/comparison.json','complete_serial_fused_dev_03/comparison.json','complete_serial_lazy_dev_01/comparison.json','lazy_resource_scheduling_validation_01/completion.json','complete_serial_transfer_dev_01/comparison.json','complete_serial_seed_policy_dev_01/comparison.json','direct_completed_roles_validation_02/completion.json','complete_serial_cache_comparison_01.json','Tf_fixed_seed_resource_closure_01.json','completed_seed_transfer_summary_02.json']:
    v=read(D/f);assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items())
p=D/'paper';archive=D/'multiobjective_R1_whole_net_probe_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==513
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_25.json')
assert projection['passed'] and projection['observations']==307 and projection['unique_quality_tuples']==190
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_closed_controls_02/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
text=unicodedata.normalize('NFKC',text)
points=read(archive/'points.json')
arch=read(D/'complete_serial_architecture_transfer_01/comparison.json')
assert arch['execution_cohort_all_legal'] and arch['registered_roles']==arch['successful_legal_roles']==4
new={p['batch']:p for p in points if p.get('actor_final_selected') and p.get('batch_full_path','').startswith(str(D/'complete_serial_architecture_transfer_01'))}
assert new['sb_native']['id'] in new['sb_domain']['quality_dominated_by']
assert all(new[k]['actual_native_work']['native_transactions']==0 for k in ['cb_native','cb_domain'])
tokens=['5614.05','287.44','210.39','271.79','273.18','2070609','917.93','seed11to19','Nineteenconfigurations','2061072','313','173','3008.02','210.48','5103','2061076','3056.67','210.01','Allthreetimingrequests','2061249','313wire','1418.13','88.87','88.48','allthirty-fourlegal','2061072','2061627','Both47-SBtimingmenusarelocalterminals','6307.79','thirty-fourlegalcandidates','unit-capacityOPIN','verticallowerbound','227439','227459','212511','424.59','533.57','74.15','72.46','108.98','6.114032391','0.740','1.271','1.282','2061036','2061213','2061285','177','948.00','51.31','60.11','271.70','93.15','203.48','313.74','85.74','29.65','41.90','1.296','1.310','91.69','91.55','274.22','336.68','169486','148463','62.46','1.010','1.034','2.502','2.534','290.19','289.21','289.66','1.274','1.302','1.297','101.02','100.33','1804.56','legalcandidates','2061257','2.487','409.82','3755.45','513','2076038','6752.95','221.11','226.35','67.38','66.12','288.49','292.47','217214','2070629','217183','2061377','5046.61','7099.32','1721','Archive513','307BNN','190plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-',''))) for t in tokens};assert all(checks.values()),checks
log=p/'build_closed_controls_02.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C211 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C211.tex'
if version.exists():assert sha(version)==sha(source),'Existing unsealed source version must match exactly'
else:shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186','C187','C188','C189','C190','C191','C192','C193','C194','C195','C196','C197','C198','C199','C200','C201','C202','C203','C204','C205','C206','C207','C208','C209','C210','C211'],pages=6,archive=str(archive),records=513,
    projection_observations=307,projection_coordinates=190,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),D/'R1_whole_net_residual_probe_01/verification.json',D/'complete_serial_seed_transfer_01/comparison.json',D/'verify_completed_seed_transfer_evidence_01.py',D/'budget47_current_timing_composition_01/comparison.json',D/'BNN_vertical_cut_bound_01/completion.json',D/'budget47_first_timing_transfer_validation_01/completion.json',D/'budget47_native_timing_terminal_validation_01/completion.json',D/'multiobjective_budget47_complete_pair_01/phase_terminal_updates.json',D/'census_completed_roles_validation_02/completion.json',archive/'probe_and_root_summary.json',D/'feedback_exchange_candidates_validation_01/completion.json',D/'controller_feedback_closure_01.json',D/'cb_terminal_cut_bound_01/completion.json',D/'complete_serial_architecture_transfer_01/comparison.json',D/'lazy_real_fallback_validation_01/completion.json',D/'connection_budget_scope_probe_01/verification.json',D/'complete_serial_lazy_transfer_dev_01/comparison.json',D/'complete_serial_fused_dev_03/comparison.json',D/'complete_serial_lazy_dev_01/comparison.json',D/'lazy_resource_scheduling_validation_01/completion.json',D/'complete_serial_transfer_dev_01/comparison.json',D/'complete_serial_seed_policy_dev_01/comparison.json',D/'direct_completed_roles_validation_02/completion.json',D/'complete_serial_pair_comparison_01.json',D/'complete_serial_cache_comparison_01.json',D/'Tf_fixed_seed_resource_closure_01.json',D/'completed_seed_transfer_summary_02.json',source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'points.json',archive/'probe_and_root_summary.json',
        p/'data/joint_quality_projection_binding_25.json',D/'completed_seed_transfer_summary_01.json',D/'R1_fixed_seed_resource_mechanism_01.json',pdf,log]},
    qualification='Six-page C211 formal development manuscript;513archive observations,307BNN/190qualitycoordinates. Four native-census roles/34legal candidates exactly match direct full vectors/ordered trees/requests/domains/decisions and all counter fields; all selected finals own independent/context seals. Direct/native-count imported BNN-paired6307.79/5614.05s, not cold time or statistical speedup. Four seed19 complete configurations reproduce seed11 initial/full actual trajectories, add no independent roots;19actual complete configurations remain on3known circuits/3vertical families. R1 full-four-sink current-criticality/pin-ID probes each save20wire with unchanged complete endpoint vector/CPD/33SB/5071CB and preserve actual CB+SB excursion; physical trees differ, both rejected by original vertical-only rule, no actor commit.917.93s shared imported scope includes serialization/checks, not standalone or cold cost. Both47SB local timing menus terminal, guided2061076wire versus localnative2061249 at13.228145690ns/47SB/5060CB; guided lowwire2061072 intermediate retained. First-step177wire advantage becomes173, later physical trees differ despite equal requests/delay/endpoint changes. Native/guided timing phases3056.67/3008.02s plus source reobservations210.01/210.48s exclude resourceprefix/initialroute/querygraph preparation, not cold full algorithm cost.5103fixed-terminal BNN cut bound attained by43SB/5060CB; conditionalSB>=43atCB<=5060; not wire/CPD/placement optimum. Frozen histories, all legal rejects/failures preserved. R1/Tf-native recovery and registered source-snapshot/SB102percent/full fresh BNN cost flows continue without predicted results. Research active, no new work pushed.')
write(p/'closed_controls_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_closed_controls_20261115';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'closed_controls_pdf_validation_01.json',
       p/'data/joint_quality_projection_25.pdf',p/'data/joint_quality_projection_25.png',
       p/'data/joint_quality_projection_25.csv',p/'data/joint_quality_projection_binding_25.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'closed_controls_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',archive/'probe_and_root_summary.json',p/'data/joint_quality_projection_binding_25.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
