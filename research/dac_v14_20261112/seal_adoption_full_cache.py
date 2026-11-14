#!/usr/bin/env python3
"""Seal completed adoption/cache evidence; keep the larger research goal active."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf));text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
checks={s:s in text for s in ['1.358316153998729','284.194','32.486','148445','24.796','3.310','29.172']};assert all(checks.values()),checks
log=paper/'build_adoption_full_cache_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
for p,h in read(D/'adoption_full_cache_summary_01.json')['source_sha256'].items():assert sha(p)==h,p
stage=D/'native_objective_stage_01';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
for n,h in binding['source_sha256'].items():assert sha(stage/'src'/n)==h==sha(D/'src'/n),n
v=read(paper/'data/evidence_v14_ledger_validation.json');assert v['status']=='passed' and v['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
write(paper/'adoption_full_cache_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),build_log_sha256=sha(log),scope='Build and PDF text checks; not visual layout or DAC page-limit certification.'))
snapshot=D/'paper_snapshots/current_sta_adoption_full_cache_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',log,paper/'adoption_full_cache_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
paths=[D/'seal_adoption_full_cache.py',D/'adoption_full_cache_summary_01.json',D/'native_objective_stage_01/binding.json',snapshot/'snapshot_binding.json',snapshot/'adoption_full_cache_pdf_validation_01.json',snapshot/'data/evidence_v14_ledger.json',snapshot/'data/evidence_v14_ledger_validation.json']
write(D/'adoption_full_cache_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_completed_plateau_adoption_factorial_and_full_graph_cache',source_sha256={str(p):sha(p) for p in paths},paper_snapshot=str(snapshot),paper_pages=len(reader.pages),public_snapshot='f7167bd',new_work_pushed=False,next_registered='spmv_timing_cone_sensitivity_experiment_01.json'))
h=read(D/'live_handoff.json');h.update(observed_at=time.time(),research_state='active_timing_cone_diagnostic_after_sealed_adoption_controls',previous_goal_turn_classification='progress')
h['latest_paper']=dict(pdf='paper/build/main.pdf',validation='paper/adoption_full_cache_pdf_validation_01.json',pdf_sha256=sha(pdf),pages=len(reader.pages),snapshot=str(snapshot),claims=['C103','C104','C105'])
h['latest_adoption_full_cache']=dict(summary='adoption_full_cache_summary_01.json',binding='adoption_full_cache_binding_01.json',physical_policy='current_sta_policy_native_spmv_A0_near_physical_01',strict_accepts=0,endpoint_accepts=1,CPD_ns=7.034697713237392,endpoint_setup_improved=2,endpoint_setup_regressed=0,endpoint_resources=dict(SB=1,CB=967,wirelength=148445),shared_controller_seconds=284.19381868466735,factorial='spmv_adoption_factorial_01',factorial_seconds=32.48578964918852,full_graph_cache='full_route_graph_cache_e695_01',full_graph_validation='full_route_graph_cache_validation_01',new_work_pushed=False)
for old in h.get('active_jobs',[]):
 assert (Path(old['batch'])/'completion.json').exists(),old
 h.setdefault('completed_job_history',[]).append(dict(old,status='completed',completion=str(Path(old['batch'])/'completion.json')))
h['active_jobs']=[];h['active_current_sta_batch']=dict(batch=None,terminal=True,qualification='Previously running physical-policy and missing-factorial cells are terminal. No native experiment currently running; research remains active with a concrete next diagnostic.')
h['next_actions']=[
 'Implement registeredspmv_timing_cone_sensitivity_experiment_01. Native source currentlyunchanged45bindings. h3d_native_sta_frontier.h emitsallpins/endpoints/domain-slacks butnotarrival/requirededges. vpr_api.cpp finalanalysis~1600 has analysis_delay_calc andtiming_info ready; tatum::write_echo(ostream,graph,constraints,delaycalc,analyzer) alreadyexists. Adddisabled-by-default envrequestedhighprecision(17digits)readonlyecho, freezeindependentobserverstage, preserve oldbinaries/results. Existingfilenamewrite_echo defaultstreamprecisioninsufficientforexacttieanalysis.',
 'BeforeC++changes/build readsrc/AGENTS.md anddoc/agents coding/build/codebase/testing asneeded; userexplicitlyauthorizesroutineimplementation/builds/experiments. Buildmake -j8 vpr fromsrcroot. Nevereditfrozennative_objective_stage_01; newobserverversionandbinarybindingsmustbeexplicit.',
 'DiagnoseacceptedSPMVplateau current_sta_policy_native_spmv_A0_near_physical_01/attempt_000/evaluation versus rejectedendpoint successorattempt_003/evaluation. Sameallsetup/hold/CPD;6997p1 nativephysicaldelay1.2286298645→1.0428040653ns andpinslack−6.905010341→−6.719184764ns. Actualreconvergentfanin notyetknown; mappingnamesaloneinsufficient. NewreadonlySTAexport isneededdiagnosticdata, notreroute/reportduplication.',
 '6008p12adoption2x2complete: weighted_soft andweighted_capacitynochange;physical_softfoundpathbutcapacityinfeasible,occupancyrestored,noFULLSTA;physical_capacitylegal7.639psgain2endpointsbetter0worse,strictrejectEPaccept. Reusedtwoexistingcells;twofreshcells32.486s,weightedhardexactcandidateFULLSTAreused. Do notrepeat.',
 'Physicalnear0.2policyterminal:strict0EP1,CPD7.034697713unchanged;EP1SB967CB148445wire vsA00SB967CB148463. Laterlegaljointendpointvectorunchangedreject; no subsequentCPDunlock.284.194sshared/nativecore0.290nested,3newtransactions;cachedcandidateaudit11.114s vsFULLSTA108.525sstilldominant.',
 'Full-routegraphcache exactrawmetadata29.172s extra build(parent33.122s). Threeexistingroutes evidence/allnon-timeaudit/resource/delayexact;invalidswitch/overcapnegativeerrorssame. ContemporaneousXMLunionevidence24.796s vs cacheload+evidence3.310s;componentonly. run_endpoint_state_analysis_cached.py prepared, notnative-exercisedbecausefactorialweightedhardexactreuseandphysicalsoftfailed. Canusethevalidatedadapterinnewdiagnosticwrapper while preservingnativeFULLSTA andoriginalauditors.',
 'PaperC103-C105/483sources snapshotcurrent_sta_adoption_full_cache_20261113sealed,newworklocalonlyafterf7167bd. Goalactive,nooveralltime/call/matrixstop.']
h['next_registered_not_implemented']='spmv_timing_cone_sensitivity_experiment_01.json'
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:f.write('\nAdoption/full-cache progress sealed: physical_capacity SPMVA0near0.2strict0EP1,CPD7.034697713unchanged,2setupimprovements0regressions,1SB967CB148445wire. Followingjoint6997p1actualdelay/localpinslackimprovebutallendpointsetup/hold/CPDsame;rejected. NoCPDunlock;284.194scomplete/core0.290nested. Sameinitial6008p12factorial:weightedhardnochange,physicalsoftfoundinfeasible/restored,physicalhardlegalplateau;twoexistingcellsreused,twofresh32.486s,nonewFULLSTAbecauseexactreuseorfailedtransaction. CompleteXMLmetadataadapterbuild29.172s extra;threefullrawgraph/audit/resourceequal,2illegalrouteerrorssame,graphaccess24.796→3.310scomponentmeasurement. CachedFULLSTAwrapperpreparedbutnotnativeused. Registeredreadonly17digitnative timing-cone echo toidentifydownstreammasking; noC++changesyet. PaperC103-C105483sourcessealedlocal,nopush. Allnativecontrollersandfactorialterminal;goalactive,concretenextdiagnostic,nooverallstop.\n')
print(dict(pages=len(reader.pages),sources=v['source_count'],links=v['local_link_count'],research='active',native_jobs='completed',next='timing_cone_sensitivity'))
