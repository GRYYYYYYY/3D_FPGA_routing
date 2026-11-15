"""Validate the correction for integer-second GNU-time hour formatting."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from orphaned_flow_time_evidence_v2 import parse_gnu_time,recover_original_time
out=D/'orphaned_BNN_time_resolution_validation_01';out.mkdir(exist_ok=False)
case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
actual=recover_original_time(case);driver=read(case/'flow/completion.json')['complete_driver_seconds']
assert actual['elapsed_text']=='2:00:47' and actual['display_resolution_seconds']==1
assert actual['elapsed_seconds']==7247 and actual['elapsed_seconds']<driver<=actual['elapsed_seconds']+actual['display_resolution_seconds']
assert not driver<=actual['elapsed_seconds']-1+actual['display_resolution_seconds']
tiny=D/'fresh_route_entry_preflight_01/measurement/gnu_time.txt';t=parse_gnu_time(tiny.read_text());assert t['display_resolution_seconds']==.01
before=(D/'verify_orphaned_BNN_quality_v1.py').read_text();after=(D/'verify_orphaned_BNN_quality_v2.py').read_text()
start="assert done['external_history_allowed']";end='files += [D/'
assert ast.dump(ast.parse(before[before.index(start):before.index(end)]),include_attributes=False)==ast.dump(ast.parse(after[after.index(start):after.index(end)]),include_attributes=False)
files=[Path(__file__).resolve(),D/'orphaned_flow_time_evidence_v2.py',D/'verify_orphaned_BNN_quality_v2.py',
    D/'orphaned_BNN_quality_analysis_01/completion.json',D/'orphaned_BNN_quality_analysis_01/verification.log',case/'flow/completion.json',case/'measurement/gnu_time.txt',tiny]
write(out/'completion.json',dict(passed=True,quality_gate_AST_unchanged=True,actual_GNU_time_seconds=actual['elapsed_seconds'],
    actual_display_resolution_seconds=actual['display_resolution_seconds'],actual_driver_seconds=driver,
    fractional_GNU_time_resolution_seconds=t['display_resolution_seconds'],shortened_time_rejected=True,
    original_failed_receipt_preserved=True,VPR_calls_new=0,source_sha256={str(f):sha(f) for f in files},
    qualification='Time-format resolution correction only. Hour-formatted GNU time has no fractional digits in this actual receipt; driver stopwatch is finer. Missing observer measurement remains missing.'))
print(dict(passed=True,original_quality_gates_unchanged=True,actual_GNU_seconds=7247,display_resolution_seconds=1))
