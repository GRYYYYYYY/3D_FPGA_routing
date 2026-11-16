"""Reconcile the two receipts that closed during manuscript07 compilation."""
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p = D/'paper'
parent_path = D/'complete_input_paper_binding_07.json'
parent = read(parent_path)
old = (p/'current_repair_main.tex').read_text()
assert old == (Path(parent['snapshot'])/'current_repair_main.tex').read_text()
baseline = D/'BNN_terminal_wire_qualified_comparison_02/completion.json'
whole = D/'standalone_whole_method_check_01/completion.json'
b,w = read(baseline),read(whole)
assert b['passed'] and b['resource_prefix_exact'] and b['single_change_attribution_available']
assert b['terminal_minus_baseline_resources'] == dict(wirelength=-24,SB_pairs=0,CB_sources=0)
assert b['endpoint_summary']['setup_improved'] == 2 and b['endpoint_summary']['setup_regressed'] == 0
assert b['complete_cost_comparison']['descriptive_GNU_seconds_difference'] == 104
assert w['passed'] and w['whole_method_executed_and_verified'] and not w['full_method_frozen']
e = D/'qualified_complete_paper_evidence_08'
e.mkdir(exist_ok=False)
for name in ['completion.json','rows.json']:shutil.copy2(D/'complete_input_paper_evidence_07'/name,e/name)
changes = {
    'It is the same BNN input; baseline-prefix and final-vector attribution require their separate audit, not scalar coincidence.':
    'The separate audit confirms identical resource-prefix states, requests and native work, with 24 fewer final wire and two setup improvements without regression. Matched GNU-time is 7351/7247 s (+104 s); the old observer/PSS loss and overlap remain. This same-input tradeoff is not acceleration.',
    'Whole-controller confirmation remains pending; the explicit-SDC pair below uses the earlier integration version. Complete frozen-controller confirmation remains pending.':
    'The complete packaged flow also runs outside the project on an existing tiny input (101.43 s), with no accepted repair. Positive integrated mechanism paths and frozen-controller confirmation remain pending; the SDC pair uses the earlier integration version.'}
new = old
for a,c in changes.items():assert new.count(a)==1;new=new.replace(a,c)
source=p/'current_repair_qualified_inputs_08.tex'
assert not source.exists();source.write_text(new)
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    complete_attempt_rows=27,scoped_component_rows=2,initial_failure_rows=4,
    sources_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,e/'completion.json',e/'rows.json',baseline,whole]},
    exact_replacements=changes,qualification='No added table rows or native calls. Reconcile newly closed baseline and whole-entry checks without changing registered experiments.'))
print(dict(source=str(source),new_native_calls=0))
