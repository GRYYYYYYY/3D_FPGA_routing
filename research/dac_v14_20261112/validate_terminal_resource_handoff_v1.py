"""Exercise real positive/no-alternative handoffs and reject a foreign-flow candidate."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from terminal_resource_handoff_v1 import choose

out=D/'terminal_resource_handoff_validation_01';out.mkdir(exist_ok=False)
positive=D/'terminal_timing_envelope_policy_01/legacy_0_endpoint';flow=Path(read(positive/'completion.json')['actor']).parent
accepted=choose(flow,positive);assert accepted['changed'] and accepted['terminal_wire_commits']==1
row=read(positive/'completion.json');assert row['current_resources']['wirelength']-row['selected']['resources']['wirelength']==24
results=[]
for role in ['native','domain']:
 current=D/'complete_serial_additional_circuits_01'/('robot_rl_'+role)/'flow'
 selection=D/'robot_terminal_wire_transfer_01'/(role+'_endpoint')
 r=choose(current,selection);assert not r['changed'] and r['selected_resource_state']==read(current/'completion.json')['final_state'];results.append(r)
try:choose(current,positive)
except AssertionError:rejected=True
else:raise AssertionError('A historical foreign-flow observation escaped the handoff boundary')
files=[Path(__file__).resolve(),D/'terminal_resource_handoff_v1.py',D/'run_complete_resource_terminal_wire_timing_v1.py',D/'verify_complete_resource_terminal_wire_timing_v1.py',positive/'completion.json',flow/'completion.json',D/'terminal_timing_envelope_policy_01/verification.json',D/'robot_terminal_wire_transfer_01/completion.json']
write(out/'completion.json',dict(passed=True,actual_positive_handoff=accepted,actual_no_alternative_handoffs=results,foreign_flow_rejected=rejected,zero_native_execution=True,source_sha256={str(f):sha(f) for f in files},qualification='Actual independently audited endpoint-safe24wire improvement and two actual zero-eligible robot menus exercised. Different-flow selector evidence is explicitly rejected. Does not execute the new full algorithm or establish its downstream timing quality/cost. All originals unchanged.'))
print(dict(passed=True,positive_wire_saved=24,no_alternative_cases=2,foreign_flow_rejected=True,native_calls_new=0),flush=True)
