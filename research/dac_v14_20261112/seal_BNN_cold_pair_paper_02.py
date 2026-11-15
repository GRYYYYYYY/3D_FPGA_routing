import unicodedata
"""Verify and snapshot the six-page C218 manuscript against the new archive."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

from verify_completed_seed_transfer_evidence_01 import verify_evidence
verify_evidence()
import runpy
runpy.run_path(str(D/'verify_revalidated_native_checkpoint_archive_01.py'))
runpy.run_path(str(D/'verify_complete_BNN_native_archive_01.py'))
pair=read(D/'complete_serial_pair_comparison_01.json');assert pair['passed'] and pair['initial_ordered_route_and_full_vector_exact']
assert all(sha(f)==h for f,h in pair['source_sha256'].items())
assert pair['paired_minus_native_resources']==dict(wirelength=164,SB_pairs=-2,CB_sources=-3)
for f in ['multiobjective_complete_BNN_cold_pair_01/verification.json','complete_resource_timing_full_flow_01/bnn_domain/completion.json','complete_resource_timing_full_flow_01/comparison.json','complete_BNN_domain_cost_analysis_01/completion.json','cold_domain_wire_delta_analysis_01/completion.json','BNN_terminal_wire_alternative_01/completion.json','terminal_wire_selector_merge_validation_01/completion.json','BNN_complete_cache_boundary_01/completion.json','complete_resource_timing_full_flow_01/bnn_native/completion.json','complete_BNN_native_cost_analysis_01/completion.json','R1_native_float32_route_delay_validation_01/completion.json','R1_single_net_vertical_local_minimum_01/completion.json','R1_local_minimum_artifact_validation_01.json','R1_local_escape_owner_diagnostic_01/completion.json','current_escape_owner_selector_validation_01/completion.json','R1_crossing_source_probe_01/verification.json','native_checkpoint_adapter_v2_replay_01/completion.json','complete_serial_timing_budget_01/comparison.json','complete_serial_source_snapshot_01/comparison_v2.json','R1_whole_net_residual_probe_01/verification.json','complete_serial_seed_transfer_01/comparison.json','budget47_current_timing_composition_01/comparison.json','BNN_vertical_cut_bound_01/completion.json','budget47_first_timing_transfer_validation_01/completion.json','budget47_native_timing_terminal_validation_01/completion.json','census_completed_roles_validation_02/completion.json','multiobjective_complete_BNN_cold_pair_01/completion.json','cb_terminal_cut_bound_01/completion.json','complete_serial_architecture_transfer_01/comparison.json','lazy_real_fallback_validation_01/completion.json','connection_budget_scope_probe_01/verification.json','complete_serial_lazy_transfer_dev_01/comparison.json','complete_serial_fused_dev_03/comparison.json','complete_serial_lazy_dev_01/comparison.json','lazy_resource_scheduling_validation_01/completion.json','complete_serial_transfer_dev_01/comparison.json','complete_serial_seed_policy_dev_01/comparison.json','direct_completed_roles_validation_02/completion.json','complete_serial_cache_comparison_01.json','Tf_fixed_seed_resource_closure_01.json','completed_seed_transfer_summary_02.json']:
    v=read(D/f);assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items())
cold_pair=read(D/'complete_resource_timing_full_flow_01/comparison.json')
assert cold_pair['passed'] and cold_pair['execution_cohort_all_legal'] and cold_pair['successful_legal_roles']==2
cp=cold_pair['pair'];assert cp['quality_comparison_available'] and all(cp['initial_state_comparison'].values())
assert cp['domain_minus_native_resources']==dict(wirelength=1786,SB_pairs=-39,CB_sources=-2)
assert cp['domain_minus_native_CPD_ns']==0 and cp['four_axis_quality_relation']=='tradeoff'
assert cp['final_endpoint_comparison']['setup_improved']==534 and cp['final_endpoint_comparison']['setup_regressed']==803
assert cp['final_endpoint_comparison']['hold_violation_regressions']==0
native,domain=[read(D/'complete_resource_timing_full_flow_01'/role/'completion.json') for role in ['bnn_native','bnn_domain']]
assert domain['resources']==dict(wirelength=2061417,SB_pairs=43,CB_sources=5060)
assert domain['resource_accepted_steps']==9 and domain['timing_accepted_steps']==3
assert domain['resource_actual_work']['native_transactions']==9 and domain['resource_actual_work']['skipped_OFF']==9
assert native['missing_memory_observations']==30 and domain['missing_memory_observations']==26
assert format(domain['complete_wall_seconds'],'.2f')=='9754.31'
assert format(domain['sampled_tree_PSS_peak_kib']/1048576,'.3f')=='11.063'
assert format(domain['complete_wall_seconds']-native['complete_wall_seconds'],'.2f')=='1821.07'
actual_cost=read(D/'complete_BNN_domain_cost_analysis_01/summary.json')
assert actual_cost['complete_wall_seconds']==domain['complete_wall_seconds']
assert abs(sum(actual_cost['disjoint_category_seconds'].values())-domain['complete_wall_seconds'])<1e-8
assert actual_cost['nested_diagnostics_not_added_to_wall']['native_search_workers']==12
assert actual_cost['nested_diagnostics_not_added_to_wall']['actual_candidate_LOADs']==12
assert format(actual_cost['nested_diagnostics_not_added_to_wall']['actual_native_search_core_seconds'],'.2f')=='1209.00'
assert all(row['byte_exact_same_command_payloads'] for row in actual_cost['metadata_runtime_aliases'])
p=D/'paper';archive=D/'multiobjective_complete_BNN_cold_pair_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==568
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
projection=read(p/'data/joint_quality_projection_binding_30.json')
assert projection['passed'] and projection['observations']==338 and projection['unique_quality_tuples']==200
assert all(sha(path)==h for path,h in projection['source_sha256'].items())
assert all(sha(p/'data'/n)==h for n,h in projection['artifact_sha256'].items())
pdf=p/'build_BNN_cold_pair_01/current_repair_main.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==6
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
text=unicodedata.normalize('NFKC',text)
points=read(archive/'points.json')
arch=read(D/'complete_serial_architecture_transfer_01/comparison.json')
assert arch['execution_cohort_all_legal'] and arch['registered_roles']==arch['successful_legal_roles']==4
new={p['batch']:p for p in points if p.get('actor_final_selected') and p.get('batch_full_path','').startswith(str(D/'complete_serial_architecture_transfer_01'))}
assert new['sb_native']['id'] in new['sb_domain']['quality_dominated_by']
assert all(new[k]['actual_native_work']['native_transactions']==0 for k in ['cb_native','cb_domain'])
tokens=['2061417','9754.31','11.063','1786','1821.07','534','803','2976.18','2580.96','1908.54','941.32','1209.00','1268.81','30/26missingreads','2059567','twosetup-componentimprovements','Itquality-dominatestheselectedresourceterminal','Timingcontinuationremainsunvalidated','Six timingaudits'.replace(' ',''),'legacymetadataaliases','staticdependencies','2059631','7933.25','11.055','2349.50','1644.44','1800.02','941.91','39.98','934.74','230693','10.235','fourknowncircuits','5104','78450','583.59','2068956','2074463','2068928','2074388','single-netlocalminimum','Alleightsame-layerOPINexits','995','227583','448.09','581.65','133.56','1.218','6.161295154','280.37','33.37','8.85','1.300','64queries/101attempts','5614.05','287.44','210.39','271.79','273.18','2070609','917.93','seed11to19','Twenty-fourconfigurations','2061072','313','173','3008.02','210.48','5103','2061076','3056.67','210.01','Allthreetimingrequests','2061249','313wire','1418.13','88.87','88.48','allthirty-fourlegal','2061072','2061627','Both47-SBtimingmenusarelocalterminals','6307.79','thirty-fourlegalcandidates','unit-capacityOPIN','verticallowerbound','227439','227459','212511','424.59','533.57','74.15','72.46','108.98','6.114032391','0.740','1.271','1.282','2061036','2061213','2061285','177','948.00','51.31','60.11','271.70','93.15','203.48','313.74','85.74','29.65','41.90','1.296','1.310','91.69','91.55','274.22','336.68','169486','148463','62.46','1.010','1.034','2.502','2.534','290.19','289.21','289.66','1.274','1.302','1.297','101.02','100.33','1804.56','legalcandidates','2061257','2.487','409.82','3755.45','568','2076038','6752.95','217214','2070629','217183','2061377','5046.61','7099.32','1721','Archive568','338BNN','200plotted','7.638334','550','799','434.52','450.11','3093.90']
for arm in ['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']:
    point=next(x for x in points if x['arm']==arm)
    assert point['quality_status']=='nondominated_in_collected_population'
    tokens += [format(point['CPD_ns'],'.6f'),str(point['wirelength'])]
checks={t:(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-',''))) for t in tokens};assert all(checks.values()),checks
log=p/'build_BNN_cold_pair_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
source=p/'current_repair_main.tex'
assert 'experiment is queued' not in source.read_text()
assert '| C218 |' in (p/'claims_evidence.md').read_text()
version=p/'data/manuscript_versions/current_repair_C218.tex'
if version.exists():assert sha(version)==sha(source),'Existing unsealed source version must match exactly'
else:shutil.copy2(source,version)
binding=dict(passed=True,claims=['C186','C187','C188','C189','C190','C191','C192','C193','C194','C195','C196','C200','C198','C199','C200','C201','C202','C203','C204','C205','C206','C207','C208','C209','C210','C211','C212','C213','C214','C215','C216','C217','C218'],pages=6,archive=str(archive),records=568,
    projection_observations=338,projection_coordinates=200,numerical_text_checks=checks,
    source_sha256={str(x):sha(x) for x in [Path(__file__).resolve(),D/'multiobjective_complete_BNN_cold_pair_01/verification.json',D/'complete_resource_timing_full_flow_01/bnn_domain/completion.json',D/'complete_resource_timing_full_flow_01/comparison.json',D/'complete_BNN_domain_cost_analysis_01/completion.json',D/'complete_BNN_domain_cost_analysis_01/summary.json',D/'cold_domain_wire_delta_analysis_01/completion.json',D/'BNN_terminal_wire_alternative_01/completion.json',D/'terminal_wire_selector_merge_validation_01/completion.json',D/'BNN_complete_cache_boundary_01/completion.json',D/'verify_complete_BNN_native_archive_01.py',D/'complete_resource_timing_full_flow_01/bnn_native/completion.json',D/'complete_BNN_native_cost_analysis_01/completion.json',D/'complete_BNN_native_cost_analysis_01/summary.json',D/'R1_native_float32_route_delay_validation_01/completion.json',D/'verify_revalidated_native_checkpoint_archive_01.py',D/'R1_single_net_vertical_local_minimum_01/completion.json',D/'R1_local_minimum_artifact_validation_01.json',D/'R1_local_escape_owner_diagnostic_01/completion.json',D/'current_escape_owner_selector_validation_01/completion.json',D/'R1_crossing_source_probe_01/verification.json',D/'native_checkpoint_adapter_v2_replay_01/completion.json',D/'complete_serial_timing_budget_01/comparison.json',D/'native_checkpoint_representation_diagnostic_01/completion.json',D/'native_chain_queue_failure_reconciliation_01/completion.json',D/'complete_serial_source_snapshot_01/comparison_v2.json',D/'R1_whole_net_residual_probe_01/verification.json',D/'complete_serial_seed_transfer_01/comparison.json',D/'verify_completed_seed_transfer_evidence_01.py',D/'budget47_current_timing_composition_01/comparison.json',D/'BNN_vertical_cut_bound_01/completion.json',D/'budget47_first_timing_transfer_validation_01/completion.json',D/'budget47_native_timing_terminal_validation_01/completion.json',D/'multiobjective_budget47_complete_pair_01/phase_terminal_updates.json',D/'census_completed_roles_validation_02/completion.json',D/'multiobjective_R1_whole_net_probe_01/probe_and_root_summary.json',D/'feedback_exchange_candidates_validation_01/completion.json',D/'controller_feedback_closure_01.json',D/'cb_terminal_cut_bound_01/completion.json',D/'complete_serial_architecture_transfer_01/comparison.json',D/'lazy_real_fallback_validation_01/completion.json',D/'connection_budget_scope_probe_01/verification.json',D/'complete_serial_lazy_transfer_dev_01/comparison.json',D/'complete_serial_fused_dev_03/comparison.json',D/'complete_serial_lazy_dev_01/comparison.json',D/'lazy_resource_scheduling_validation_01/completion.json',D/'complete_serial_transfer_dev_01/comparison.json',D/'complete_serial_seed_policy_dev_01/comparison.json',D/'direct_completed_roles_validation_02/completion.json',D/'complete_serial_pair_comparison_01.json',D/'complete_serial_cache_comparison_01.json',D/'Tf_fixed_seed_resource_closure_01.json',D/'completed_seed_transfer_summary_02.json',source,version,p/'claims_evidence.md',
        archive/'completion.json',archive/'complete_domain_case_summary.json',archive/'points.json',D/'multiobjective_R1_whole_net_probe_01/probe_and_root_summary.json',
        p/'data/joint_quality_projection_binding_30.json',D/'completed_seed_transfer_summary_01.json',D/'R1_fixed_seed_resource_mechanism_01.json',pdf,log]},
    qualification='Six-page C218: actual cold BNN native/domain pair closed, exact fresh ordered roots/full vectors and explicit common physical inputs/phase binaries. Equal13.228145689936355ns; native2059631wire/82SB/5062CB/7933.245508622378s versus domain2061417/43/5060/9754.312096122652s,1786wire/1821.0665875002742s for39SB/2CB,534setupimprovements/803regressions/no increased hold violation. Actual PSS11.055/11.063GiB with30/26missing reads;9domain resource commits/9ON/9OFFomissions and3timing commits;12native workers/12candidate LOADs. Domain disjoint native wrappers2976.18/candidate2580.96/selection1908.54/indexes941.32s, nested native transactions1209.00s; observer1268.81s separate. Legacy metadata aliases are explicit additional static dependencies; consumed payloads equal own-command generation. Historical imported native/domain points have4/28lesswire but unknown full costs; no splice. New14actual domain states added to parent554,568observations/338BNN/200coordinates,24complete configurations/4known circuits/3vertical families. Only each actual final has its own whole cost; old quality/time retained. Existing terminal2059567wire alternative is already archived, not an extra observation. Pending32SB and2059607constructed proposals remain excluded until their own native gates. R1/Tf native recovery and broader known-circuit/engineering queues remain active. No statistical speedup, independent root sample, one-factor domain attribution or equal-work claim. Research active, local/unpushed')
write(p/'BNN_cold_pair_pdf_validation_01.json',binding)
snapshot=D/'paper_snapshots/current_BNN_cold_pair_20261115';snapshot.mkdir(exist_ok=False)
files=[source,p/'IEEEtran.cls',p/'claims_evidence.md',p/'BNN_cold_pair_pdf_validation_01.json',
       p/'data/joint_quality_projection_30.pdf',p/'data/joint_quality_projection_30.png',
       p/'data/joint_quality_projection_30.csv',p/'data/joint_quality_projection_binding_30.json']
payload={}
for f in files:
    rel=f.relative_to(p);target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,target);payload[str(rel)]=sha(target)
target=snapshot/'build/current_repair_main.pdf';target.parent.mkdir();shutil.copy2(pdf,target)
payload[str(target.relative_to(snapshot))]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    source_version=str(version),focused_manuscript='current_repair_main.tex',public_reference='7b2834743007b36ce5890320e15a0ffa7dea1eb3',new_work_pushed=False))
binding.update(snapshot=str(snapshot),pdf=str(target),new_work_pushed=False,complete_research=False)
write(D/'BNN_cold_pair_paper_binding_01.json',binding)
ledger=read(p/'data/evidence_v14_ledger.json')
for f in [source,version,archive/'completion.json',D/'multiobjective_R1_whole_net_probe_01/probe_and_root_summary.json',p/'data/joint_quality_projection_binding_30.json']:
    ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
print(dict(passed=True,pages=6,pdf=str(target)),flush=True)
