"""Clarify objective-specific triggers and measured release coverage; no new trials."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
parent_path=D/'cohort_mechanism_paper_binding_15.json';parent=read(parent_path);previous=Path(parent['snapshot'])
p=D/'paper';e=D/'mechanism_trigger_paper_evidence_16';assert not e.exists();e.mkdir()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
matrix=D/'mechanism_selection_evidence_01/completion.json';coverage=D/'release_coverage_01/completion.json';triage=D/'mechanism_triage_validation_02/completion.json'
assert all(read(f)['passed'] for f in [matrix,coverage,triage])
assert read(coverage)['BNN_resource_guided_roles']==9 and read(coverage)['BNN_audited_release_events']==0
example=D/'mechanism_selection_evidence_01/timing_envelope_counterexample.json';assert read(example)['passed']
t=(previous/'current_repair_main.tex').read_text();old=t;changes=[]
a=t.index('Crossing redundancy enables sharing;');b=t.index('\n',a)
replacement='Crossing redundancy enables sharing. Timing-owner expansion needs a positive capacity-conflicting delay witness; resource-owner expansion instead uses avoidable crossings and slack-eligible target/owner cuts. Fixed envelopes remain decisive. These are development triggers, not validated benefit predictors. Failed search releases only the affected net. R1 owner benefits come from expanded scope. CP1 fixes the core/input contract; CP1r2 corrects runtime issues. Four automatic robot-p1 owner commits/reentries are verified only on a partial development path; positive complete-controller benefits remain unconfirmed. Development runs are not retroactively confirmation.'
changes.append([t[a:b],replacement]);t=t[:a]+replacement+t[b:]
a=t.index('Matched domain controls fix source, request, scope and objective;');b=t.index('\n',a)
replacement='Matched domain controls fix source, request, scope and objective; each arm reselects after divergence. All nine BNN guided resource roles have passed audits and zero release events, as do eltwise/softmax. Their observed gains cannot be credited to executed release. Robot has five release events across three roles; its matched release-off ablations below provide the actual counterfactual. Events alone do not establish a whole-flow treatment effect.'
changes.append([t[a:b],replacement]);t=t[:a]+replacement+t[b:]
anchor='The envelope is development-derived, not an external application requirement or unseen-test result.';assert t.count(anchor)==1
replacement=anchor+' Both settings share the same initial trees and all 48 initial candidate records: changed timing budget, not different initial redundancy, permits this trade.'
changes.append([anchor,replacement]);t=t.replace(anchor,replacement)
source=p/'current_repair_mechanism_triggers_16.tex';source.write_text(t)
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),changes=changes,main_table_rows=43,
    new_independent_inputs=0,new_native_calls=0,new_full_method_results=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,matrix,coverage,triage,example]}))
print(dict(source=str(source),rows_unchanged=43,new_native_calls=0))
