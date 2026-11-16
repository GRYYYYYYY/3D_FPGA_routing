"""Group infrastructure failures in the main table; keep all per-arm records."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent_path=D/'proc_race_paper_binding_12.json';parent=read(parent_path)
previous=Path(parent['snapshot']);p=D/'paper';e=D/'runtime_recovery_paper_evidence_13'
assert not e.exists();e.mkdir()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
receipts=[D/'execution_reconciliation_20261116_01/completion.json',D/'CP1r1_packaging_failure_01/completion.json']
records=[read(f) for f in receipts];assert all(r['passed'] for r in records)
old=(previous/'current_repair_main.tex').read_text();new=old
old_rows=read(D/'proc_race_paper_evidence_12/interrupted_rows.json')['rows']
rows=[]
for label,r in zip(['Supervision interrupted (5 arms)','Guard launch failed (4 arms)'],records):
    attempts=r['attempts'];seconds=[a['failed_attempt_seconds'] for a in attempts];mem=[a['sampled_PSS_kib']/1048576 for a in attempts]
    assert all(a['quality'] is None for a in attempts)
    rows.append(f"{label}&--&--&{min(seconds):.2f}--{max(seconds):.2f}&{min(mem):.3f}--{max(mem):.3f}&--"+r'\\')
assert new.count('\n'.join(old_rows))==1
new=new.replace('\n'.join(old_rows),'\n'.join(rows))
new=new.replace('Sup.: supervision interruption, cost to failure only; no complete quality.',
    'Grouped infrastructure failures report time/PSS ranges; per-arm receipts are supplementary. No complete quality is assigned.')
new=new.replace('five supervision-interrupted attempts and two scoped components;',
    'five supervision-interrupted and four pre-native launch failures (two grouped rows), and two scoped components;')
new=new.replace('Eight failed and five supervision-interrupted attempts retain costs in the table without quality deltas.',
    'Initial/input failures and grouped infrastructure failures retain costs without quality deltas.')
new=new.replace('Ten new complete attempts, five interrupted attempts and two scoped rows are outside those counts.',
    'Ten new complete attempts, five interruptions, four launch failures and two scoped components are outside those counts.')
start=new.index('The original CLSTM/robot-p1 pairs fail loading')
end=new.index('\n\nApplicability',start)
new=new[:start]+r'''The original CLSTM/robot-p1 pairs fail loading after a template omits the packing's constant-net flag. Corrected CLSTM N/D and robot-p1 N reach legal initial routes, as do reduction N/D. All five later stop on a supervisor's vanished-process read. Four subsequent conv-hls/tpu attempts fail before VPR because the CP1r1 package loses the guard's executable bit. These are infrastructure failures, not congestion or scientific negatives. Partial trajectories and per-arm costs remain supplementary. CP1r2 repairs supervision, preserves/checks guard permissions and passes actual guard tests before and after public-source reconstruction. Algorithms, input selection and rules stay fixed; complete confirmation remains pending.'''+new[end:]
new=new.replace('CP1r1 adds the supervision-only correction described below.', 'CP1r2 adds the runtime corrections below.')
new=new.replace('CP1/CP1r1 fix','CP1/CP1r2 fix')
source=p/'current_repair_runtime_recovery_13.tex';source.write_text(new)
write(e/'failure_groups.json',dict(rows=rows,groups=records,individual_attempts=9,
    main_grouped_rows=2,new_complete_method_outputs=0,new_independent_complete_evidence=0))
files=[parent_path,*receipts,source,Path(__file__).resolve(),e/'failure_groups.json',
    D/'confirmation_release_cp1r2_01/completion.json',D/'confirmation_release_cp1r2_01/guard_execution.json',
    D/'confirmation_release_cp1r2_01/public_source_reconstruction.json',D/'cp1r2_cross_circuit_cohort_01/preflight.json']
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    original_table_rows=39,main_table_rows=36,complete_attempt_rows=32,
    infrastructure_attempts=9,infrastructure_grouped_rows=2,scoped_rows=2,
    new_complete_method_outputs=0,source_sha256={str(f):sha(f) for f in files}))
print(dict(source=str(source),main_rows=36,additional_complete_results=0))
