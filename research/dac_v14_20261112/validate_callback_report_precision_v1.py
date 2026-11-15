"""Diagnose completed failed guard without restarting or forging the old seal."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import load
from run_native_scope_policy_v4 import run_dir

root=D/'callback_report_precision_validation_01';root.mkdir(exist_ok=False)
actor=D/'complete_serial_fused_dev_01/delay_seed_paired/flow/repair'
worker=actor/'round_001/candidate_00/source_serialization_control'
reg=read(worker/'registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
rd=worker/'runs/state';m=read(rd/'manifest.json');source=Path(reg['source'])
old=read(source/'manifest.json')['metrics']['critical_path_ns'];reported=m['metrics']['critical_path_ns']
assert old!=reported and reported==float(format(old,'.6g'))
assert m['status']=='completed' and m['metrics']['native_full_check_passed']
before=load(rd/'native_sta_frontier.jsonl');after=load(rd/'candidate_restored/native_sta_frontier.jsonl')
state=Path(read(actor/'current_state.json')['state']);expected=read(state/'endpoint_vector.json')
for v in [after,expected]:assert all(before[k]==v[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert route_body(rd/'candidate/routed.route')==route_body(rd/'candidate_restored/routed.route')
for flag in ['candidate','candidate_restored']:
    assert (rd/flag/'native_state_gate.txt').read_text()==('candidate' if flag=='candidate' else 'restored_source')+' FULL fresh_STA actual_installed_trees\n'
assert (rd/'joint_native.log').read_text().splitlines()[-1].startswith('COMPLETE 1 0 0 ')
assert float(format(old*1.01,'.6g'))!=reported
files=[Path(__file__).resolve(),D/'run_serial_fused_seed_analysis_v3.py',D/'run_serial_fused_resource_repair_v2.py',worker/'registration.json',rd/'manifest.json',source/'manifest.json',state/'endpoint_vector.json',rd/'native_sta_frontier.jsonl',rd/'candidate_restored/native_sta_frontier.jsonl',rd/'candidate/routed.route',rd/'candidate_restored/routed.route',actor/'round_001/candidate_00/source_serialization_control.log',D/'complete_serial_fused_dev_01/queue/completion.json']
write(root/'completion.json',dict(passed=True,native_calls_new=0,source_full_precision_CPD_ns=old,printed_CPD_ns=reported,
    complete_vectors_exact=True,empty_control_native_order_and_restoration_exact=True,
    prior_full_flow_verification_passed=False,source_sha256={str(f):sha(f) for f in files},
    qualification='The existing native execution completed FULL and actual source/candidate/restored gates. The wrapper compared six-significant-digit report CPD against a full-precision callback manifest, suppressed vector capture, then dereferenced None. New wrapper compares report values at their actual report precision and independently captures full vectors; all acceptance and recovery vector comparisons stay exact with no epsilon. Actor now terminates as execution failure instead of testing later ranks after a controller failure. This separate read-only diagnosis does not overwrite failed receipts, invent an old input seal, publish a completed algorithm point or transfer partial elapsed time. Full corrected configuration requires its own fresh measured run.'))
print(dict(passed=True,native_calls_new=0,old_guard_false_alarm=True,full_vector_exact=True),flush=True)
