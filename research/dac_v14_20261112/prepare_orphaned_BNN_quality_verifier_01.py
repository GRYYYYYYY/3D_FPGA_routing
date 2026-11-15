"""Preserve original quality gates and separate the actual orphaned time evidence."""
import ast,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from orphaned_flow_time_evidence_v1 import parse_gnu_time,recover_original_time
origin=D/'verify_complete_resource_timing_joint_stream_v1.py';source=origin.read_text()
target=D/'verify_orphaned_BNN_quality_v1.py';report=D/'orphaned_BNN_quality_preflight_01';report.mkdir(exist_ok=False)
assert not target.exists()
prefix=source.split('payload=dict(',1)[0]
old="p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();flow=root/'flow'"
new="p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();flow=root/'flow';output=a.output.resolve()\nfrom orphaned_flow_time_evidence_v1 import recover_original_time\nrecovered=recover_original_time(root);output.mkdir(parents=True,exist_ok=False)"
assert old in prefix;prefix=prefix.replace(old,new)
prefix=prefix.replace("measure=read(root/'measurement/completion.json');done=",'done=')
prefix=prefix.replace("assert measure['passed'] and measure['returncode']==0 and not measure['live_descendants_after_command_exit'] and done['passed']", "assert recovered['exit_status']==0 and done['passed']\nassert done['complete_driver_seconds']<=recovered['elapsed_seconds']+.1")
prefix=prefix.replace("root/'measurement/completion.json'","root/'measurement/gnu_time.txt'")
prefix=prefix.replace("root/'metadata_consumers.json'","output/'metadata_consumers.json'")
suffix='''
files += [D/'verify_complete_resource_timing_joint_stream_v1.py',D/'orphaned_flow_time_evidence_v1.py',D/'orphaned_BNN_quality_preflight_01/completion.json',*map(Path,recovered['source_sha256'])]
write(output/'original_time_evidence.json',recovered);files.append(output/'original_time_evidence.json')
payload=dict(passed=True,complete_configuration_quality_verified=True,complete_observer_measurement_available=False,
    initial_state=str(initial),resource_final_state=str(resource_final),final_state=str(final),
    CPD_ns=vector(final)['cpd_s']*1e9,resources=physical(final),resource_actual_work=resource_counts,
    resource_accepted_steps=rc['accepted_steps'],timing_accepted_steps=tc['accepted_steps'],timing_attempted_proposals=tc['attempted_proposals'],
    phase_binary_sha256=config['phase_binary_sha256'],GNU_time_elapsed_seconds=recovered['elapsed_seconds'],
    waited_process_RSS_high_water_kib=recovered['waited_process_RSS_high_water_kib'],sampled_tree_PSS_peak_kib=None,
    complete_observer_wall_seconds=None,observer_CPU_seconds=None,undisturbed_timing=False,VPR_calls_new=0,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Original full-flow quality gates preserved, including actual transactions, native FULL/STA, physical audits, decisions and own-flow metadata paths. Actual original GNU-time elapsed separately recovered; missing observer measurement is not reconstructed. Brief overlap and full PSS gap retained. Downstream equivalence against prior controls remains a separate requirement before a same-behavior engineering comparison. No original case or queue completion is overwritten.')
write(output/'completion.json',payload)
print({k:payload[k] for k in ['passed','CPD_ns','resources','GNU_time_elapsed_seconds','complete_observer_measurement_available']},flush=True)
'''
target.write_text(prefix+suffix);compile(target.read_text(),str(target),'exec')
start="assert done['external_history_allowed']";end="payload=dict("
old_gates=source[source.index(start):source.index(end)]
new_gates=prefix[prefix.index(start):]
normalized=new_gates.replace("root/'measurement/gnu_time.txt'","root/'measurement/completion.json'").replace("output/'metadata_consumers.json'","root/'metadata_consumers.json'")
assert ast.dump(ast.parse(old_gates),include_attributes=False)==ast.dump(ast.parse(normalized),include_attributes=False)
rows=[]
for rel in ['complete_resource_timing_full_flow_01/bnn_native','complete_BNN_joint_index_flow_01/bnn_native_joint_indexes']:
    p=D/rel/'measurement';actual=parse_gnu_time((p/'gnu_time.txt').read_text());observer=read(p/'completion.json')
    assert actual['exit_status']==0 and abs(actual['elapsed_seconds']-observer['complete_command_wall_seconds'])<1
    assert actual['waited_process_RSS_high_water_kib']==observer['waited_process_RSS_high_water_kib']
    rows.append(dict(source=str(p),GNU_elapsed_seconds=actual['elapsed_seconds'],observer_wall_seconds=observer['complete_command_wall_seconds'],RSS_exact=True))
bad=['', 'Exit status: 0\n', (p/'gnu_time.txt').read_text().replace('Exit status: 0','')]
for text in bad:
    try:parse_gnu_time(text)
    except AssertionError:pass
    else:raise AssertionError('Incomplete GNU-time record accepted')
case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
try:recover_original_time(case)
except AssertionError as exc:premature_rejection=str(exc)
else:raise AssertionError('Preflight expected original flow to remain unresolved; reconcile new terminal state')
r=subprocess.run([sys.executable,str(target),'--help'],capture_output=True,text=True);assert r.returncode==0
write(report/'completion.json',dict(passed=True,original_quality_gate_AST_preserved=True,actual_prior_time_parser_cases=rows,
    incomplete_time_records_rejected=3,premature_recovery_rejected=premature_rejection,CLI_help_passed=True,VPR_calls_new=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),origin,target,D/'orphaned_flow_time_evidence_v1.py']},
    qualification='Verifier preparation and actual prior GNU-time parser checks only; current original BNN quality/time result remains pending.'))
print(dict(passed=True,quality_gates_AST_preserved=True,prior_time_cases=len(rows),VPR_calls_new=0))
