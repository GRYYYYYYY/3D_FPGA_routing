#!/usr/bin/env python3
"""Seal completed SPMV/cache studies and preserve the running near-endpoint batch."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
checks={s:s in text for s in ['7.034697713237392','376.123','82.888','148591','148463','33.122','4.873','4.872']};assert all(checks.values()),checks
log=paper/'build_spmv_cache_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
for p,h in read(D/'spmv_cache_progress_summary_01.json')['source_sha256'].items():assert sha(p)==h,p
stage=D/'native_objective_stage_01';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
for n,h in binding['source_sha256'].items():assert sha(stage/'src'/n)==h==sha(D/'src'/n),n
v=read(paper/'data/evidence_v14_ledger_validation.json');assert v['status']=='passed' and v['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
write(paper/'spmv_cache_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),build_log_sha256=sha(log),scope='Build and PDF text checks; not visual layout or DAC page-limit certification.'))
snapshot=D/'paper_snapshots/current_sta_spmv_cache_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files += [pdf,paper/'build/main.log',log,paper/'spmv_cache_pdf_validation_01.json',paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
paths=[D/'seal_spmv_cache_progress.py',D/'spmv_cache_progress_summary_01.json',D/'native_objective_stage_01/binding.json',snapshot/'snapshot_binding.json',snapshot/'spmv_cache_pdf_validation_01.json',snapshot/'data/evidence_v14_ledger.json',snapshot/'data/evidence_v14_ledger_validation.json']
write(D/'spmv_cache_progress_binding_01.json',dict(passed=True,research_complete=False,quality_promoted=False,status='sealed_completed_SPMV_and_candidate_graph_cache_studies',source_sha256={str(p):sha(p) for p in paths},paper_snapshot=str(snapshot),paper_pages=len(reader.pages),public_snapshot='f7167bd',new_work_pushed=False,next_registered='spmv_near_endpoint_cache_experiment_01.json',pending_study='current_sta_policy_native_spmv_A0_near_01; unfinished results excluded'))
h=read(D/'live_handoff.json');h.update(observed_at=time.time(),research_state='active_SPMV_near_endpoint_with_validated_candidate_audit_cache',previous_goal_turn_classification='progress')
h['latest_paper']=dict(pdf='paper/build/main.pdf',validation='paper/spmv_cache_pdf_validation_01.json',pdf_sha256=sha(pdf),pages=len(reader.pages),snapshot=str(snapshot),claims=['C101','C102'])
h['latest_spmv_cache']=dict(summary='spmv_cache_progress_summary_01.json',binding='spmv_cache_progress_binding_01.json',R1_final_cpd_ns=7.034697713237392,A0_same_CPD=True,above_A0_quality_not_proven=True,R1_setup_better=49,R1_setup_worse=0,R1_resources=dict(SB=2,CB=967,wirelength=148591),A0_resources=dict(SB=0,CB=967,wirelength=148463),R1_complete_controller_seconds=376.12286188825965,A0_complete_controller_seconds=82.8878218010068,Tf_exact_reuse=True,cache='rr_audit_cache_e695_dev_01',cache_validation='rr_audit_cache_validation_01',new_work_pushed=False)
for old in h.get('active_jobs',[]):
 if (Path(old['batch'])/'completion.json').exists():h.setdefault('completed_job_history',[]).append(dict(old,status='completed',completion=str(Path(old['batch'])/'completion.json')))
b=D/'current_sta_policy_native_spmv_A0_near_01';reg=read(b/'registration.json');terminal=(b/'completion.json').exists()
owner=Path('/proc')/str(reg['pid']);live=owner.exists() and owner.joinpath('stat').read_text().split(') ',1)[1].split()[19]==reg['start_ticks']
h['active_jobs']=[] if terminal else [dict(batch=str(b),registration=str(b/'registration.json'),pid=reg['pid'],start_ticks=reg['start_ticks'],status='running' if live else 'owner_missing_inspect_before_restart',tool_session=60283,source='unmodified sealed SPMV A0 with0.2ns selector')]
h['active_current_sta_batch']=dict(batch=b.name,session_id=60283,pid=reg['pid'],start_ticks=reg['start_ticks'],terminal=terminal,owner_verified_live=live,observed_at=time.time())
h['next_actions']=[
 'Continue existing current_sta_policy_native_spmv_A0_near_01/session60283. Inspect PID/start ticks or terminal completion before any restart. 0.2ns selector17connections vs0/0.05ns6connections. Both exact policies start same pristineA0; v4 uses validated cached candidate audit. Current running outcomes excluded from completed paper claims.',
 'CompletedSPMV R1 two automatic accepts6008p12 then6395p2+blocker6394p2:7.045986461→7.038347682→7.034697713ns,49setupbetter0worse,2SB967CB148591wire. Equals A0CPD butworse resources thanA0 zeroSB967CB148463. A0 worst-only0accept,82.888s. R1 shared376.123s/nativecore0.296s nested,2transactions4searches.',
 'R1/Tf OBSERVED states actually haveidentical actualinputs/normalizedcommands/completevectors; priorhandoffclaimofconfigdifferencewasunverifiedandcorrectedbyspmv_R1_Tf_exact_reuse_identity_01.json. Tf explicitcontrollerreuse51.354s,0newnative;notindependentsample. Threeinitialobservations37.988s actuallyran.',
 'Candidategraphcache built33.122s, actualXML/node/edge/switch digest bound, rehashes XML+payloads eachload; noRC substitution. CachedTfaccepted/R1rejected audits4.873/4.872scomplete, exactfullroutebytes+fields;6negativecontrolsrejected. ThirdSPMVauditinternal3.270s,nofullchildtime. Do notclaimformalpairedspeedratio fromhistoricalXMLtimes.',
 'Nextoverheadtarget: run_endpoint_state_analysis.py still calls flatland_benchmark.audit_batch afterFULLSTA, costing~23s XMLscan. Existing scripts/check_route.py read_graph_evidence requires switch_types/node_types/z_fanin/out andfullnodefields notallpresentincurrentcache. Extendindependentcacheversionandmatchallgraph-evidence/audit/metrics againstsealedruns beforeintegration; do notskipnativeFULLSTA orphysicalchecks. No native reroutes for metadata validation.',
 'No causaluniqueengineclaim; defaultnative plusdynamicselection/conflictscope alreadyworks. PriorfixedterminaleltwiseSOURCE-onlycut narrowslocalpotential,notglobalSTAoptimum. Continueothermechanisms/circuits as evidence warrants.',
 'PaperC101-C102/469sources sealed snapshotcurrent_sta_spmv_cache_20261113; allpostf7167bdworklocalnotpushed. NativeC++45bindingsunchanged. Goalactive,nooveralltime/call/matrixstop.']
h['next_registered_not_implemented']='current_sta_state_reuse_experiment_01.json (remaining FULL/STA physical-audit cache extension)'
write(D/'live_handoff.json',h)
with (D/'RESEARCH_LOG.md').open('a') as f:f.write('\nSPMV/cache progress sealed: R1 strict+endpoint both2accepts6008p12 then6395p2+6394p2,7.045986461→7.038347682→7.034697713ns;49setupbetter0worse,2SB967CB148591wire,376.123s/core0.296snested. SameCPDasA0,butA0zeroSB967CB148463wire;A0worst-only0accept82.888s. ObservedR1/Tfactualinputs/nativeconfigs/vectorsidentical(corrects priorunverifiedhandoffdifference);Tf51.354s exactreuse0newnative,notindependentsample. XML-boundcachebuild33.122s;cachedacceptedTf/rejectedR1fullaudit4.873/4.872s,routebyte/fieldsequivalent;6negativecontrolsreject. SPMVthirdcandidateequivalent3.270sinternalonly. v4 changesonlycandidateauditor; FULL/STA/queryauditsunchanged. ActiveSPMVA0near0.2ns17connections(twoexactpolicies),session60283;freshcurrentSTA/cachedcandidateaudit. CompleteclaimsC101-C102469sources sealedlocal,noGitHubpush. Goalactive.\n')
print(dict(pages=len(reader.pages),sources=v['source_count'],links=v['local_link_count'],near_terminal=terminal,near_owner_live=live,near_pid=reg['pid']))
