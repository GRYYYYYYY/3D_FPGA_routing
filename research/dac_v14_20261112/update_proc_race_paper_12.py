"""Integrate five infrastructure interruptions without inventing complete quality."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent_path=D/'BNN_engineering_paper_binding_11.json'
parent=read(parent_path);previous=Path(parent['snapshot'])
p=D/'paper';e=D/'proc_race_paper_evidence_12'
assert not e.exists();e.mkdir()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
receipt=D/'execution_reconciliation_20261116_01/completion.json'
actual=read(receipt);assert actual['passed'] and len(actual['attempts'])==5
old=(previous/'current_repair_main.tex').read_text();new=old
labels=['Reduction N','Reduction D','CLSTM corrected N','CLSTM corrected D','Robot p1 corrected N']
rows=[]
for label,r in zip(labels,actual['attempts']):
    assert r['quality'] is None and r['actual_initial_legal'] and not r['complete_method_verified']
    rows.append(f"{label} (sup.)&--&--&{r['failed_attempt_seconds']:.2f}&{r['sampled_PSS_kib']/1048576:.3f}&--"+r'\\')
anchor=r'\multicolumn{6}{l}{Fixed imported-scope components (not complete configurations)}\\'
assert new.count(anchor)==1
new=new.replace(anchor,'\n'.join(rows)+'\n'+r'\hline'+'\n'+anchor)
new=new.replace('Failed roles remain in the denominator.', 'Failed roles remain in the denominator. Sup.: supervision interruption, cost to failure only; no complete quality.')
new=new.replace('The first 32 rows of Table~\\ref{tab:completecost} retain complete attempts, including four routing and four input-loading failures. The last two rows are scoped components;',
    'Table~\\ref{tab:completecost} retains 32 complete attempts (four routing and four loading failures), five supervision-interrupted attempts and two scoped components;')
new=new.replace('Eight failed attempts retain costs in the table and have no quality deltas.',
    'Eight failed and five supervision-interrupted attempts retain costs in the table without quality deltas.')
new=new.replace('Ten new complete attempts and two scoped rows are outside those counts.',
    'Ten new complete attempts, five interrupted attempts and two scoped rows are outside those counts.')
start=new.index('CLSTM and robot-p1 each fail both roles while loading packing')
end=new.index('\n\nApplicable graphs',start)
new=new[:start]+r'''The original CLSTM/robot-p1 pairs fail loading because a template omitted the packing's constant-net flag. Corrected CLSTM N/D and robot-p1 N now reach legal initial routes, as do reduction N/D. All five later stop on a supervisor's vanished-process read, not congestion or a scientific negative. Their partial trajectories remain in the supplement; the table reports failed-attempt costs, not complete quality. Original receipts remain intact. CP1r1 changes only this process-lifecycle handler and release seals; real-process cleanup tests pass. The original prospective conv-hls/tpu cohort is re-registered before outcomes under CP1r1; full confirmation remains pending.'''+new[end:]
new=new.replace('CP1 now freezes the independently packaged core and input contract.',
    'CP1 freezes the core/input contract; CP1r1 adds the supervision-only correction described below.')
new=new.replace('CP1 fixes source/dependency and phase-binary hashes, mechanism triggers, candidate order, root envelopes and terminal policy.',
    'CP1/CP1r1 fix source/dependency and phase-binary hashes, mechanism triggers, order, root envelopes and terminal policy.')
new=new.replace('Every time binds one command/output. Cold preparation and reusable indexes are different modes. Shared-host concurrency/caches are uncontrolled; stable matched arms require interleaved repetitions including failures. Recovery, cores and research validation stay separate from complete cost.','Times bind individual commands/outputs. Cold and reusable-index modes differ. Shared-host activity/caches remain uncontrolled; matched interleaved repetitions retain failures. Recovery, cores and research validation are separate costs.')
new=new.replace("Applicable graphs here are two-layer edge-encoded Hybrid-O, SB-only and CB-only. Flat routing, CHANZ, general multilayer devices and broad timing-constrained application suites remain unconfirmed. One altered robot placement with declared SDC adds a no-gain case, not broad placement robustness. CB-only's 982 crossing nets saturate the 982-source terminal lower bound; this says nothing about wire or CPD optimality. No-cut, equal-quality, worse-quality and initial-failure inputs remain part of the scope statement.",'Applicability is limited to two-layer edge-encoded Hybrid-O/SB-only/CB-only. Flat routing, CHANZ, general multilayer and broad constrained application suites remain unconfirmed. The altered robot placement adds one no-gain input. CB-only attains its 982-source terminal bound, without wire/CPD optimality.')
new=new.replace('Independent input identity binds netlist, architecture, actual placement, constraints and initial trees. Seeds producing identical trees add no starts; routing starts and placements are counted separately. Cohorts are registered before outcomes and retain failures. BNN defaults and the robot benchmark SDC~\\cite{vprsdc} do not establish external application requirements.','Independent inputs bind netlist, architecture, actual placement, constraints and initial trees. Identical-tree seeds add no starts. Prospective cohorts retain failures; BNN defaults and robot benchmark SDC~\\cite{vprsdc} establish no external application requirement.')
new=new.replace('Acceptance-ordered execution skips an optional native diagnostic only after the domain candidate passes full resource acceptance. On eltwise it preserves every executed candidate and selected state, reducing 64 to 32 queries and 101 to 51 attempts; whole time is 203.48 versus 289.21 s. Softmax also preserves execution with 271.70 versus 336.68 s. With no eligible cut, SPMV skips no work and takes 93.15 versus 91.55 s. Unexecuted diagnostics have no imputed metrics.','After full domain-candidate acceptance, lazy execution skips optional native diagnostics. Eltwise preserves states/candidates with 64$\\to$32 queries,101$\\to$51 attempts and 203.48 versus 289.21 s. Softmax preserves execution at 271.70 versus 336.68 s. SPMV has no cut or skipped work:93.15 versus91.55 s. Skipped diagnostics have no imputed metrics.')
source=p/'current_repair_proc_race_12.tex';source.write_text(new)
write(e/'interrupted_rows.json',dict(rows=rows,attempts=actual['attempts'],
    new_complete_method_outputs=0,new_independent_complete_evidence=0,
    initial_legal_evidence_only=True,partial_metrics_not_used_in_main_table=True))
files=[parent_path,receipt,source,Path(__file__).resolve(),e/'interrupted_rows.json',
       D/'confirmation_release_cp1r1_01/completion.json',D/'cp1r1_cross_circuit_cohort_01/preflight.json']
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    original_table_rows=34,new_interrupted_rows=5,total_table_rows=39,
    complete_attempt_rows=32,interrupted_attempt_rows=5,scoped_rows=2,
    new_complete_method_outputs=0,source_sha256={str(f):sha(f) for f in files}))
print(dict(source=str(source),rows=39,new_complete_outputs=0))
