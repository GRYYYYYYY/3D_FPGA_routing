"""Wait on the existing candidate LOAD, then test preregistered predictions.

No native calls and no experiment ownership transfer or acceptance changes.
"""
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import compare

prediction=D/'R1_BFS_native_timing_prediction_01';out=prediction/'analysis';out.mkdir(exist_ok=False)
lock=(out/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
proof=read(prediction/'completion.json');assert proof['passed'] and proof['prediction_registered_before_native_LOAD']
intervention=D/'partial_escape_owner_intervention_01';q=intervention/'queue';original=read(q/'registration.json')
files=[Path(__file__).resolve(),prediction/'completion.json',prediction/'connection_predictions.json',prediction/'slack_screen.json',
 q/'registration.json',D/'bounded_route_perturbation_screen_validation_01/completion.json']
hashes={str(p):sha(p) for p in files}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,
 scope='Read-only prospective prediction validation after the already registered LOAD; no new native worker or policy change.'))
case=intervention/'BFS_candidate_evaluation';completed=case/'completion.json'
while not completed.exists():
 actual=process_identity(original['pid']);live=bool(actual and actual['state']!='Z' and actual['start_ticks']==original['start_ticks'])
 write(out/'status.json',dict(status='waiting_for_fixed_BFS_candidate_actual_LOAD',verified_original_owner_live=live))
 if (q/'completion.json').exists() or not live:
  write(out/'completion.json',dict(passed=False,comparison_available=False,reason='Original owner terminal or ended before candidate LOAD receipt; native predictions remain unvalidated',native_calls_new=0,source_sha256=hashes))
  write(out/'status.json',dict(status='terminal',passed=False));sys.exit(1)
 time.sleep(15)
assert all(sha(p)==h for p,h in hashes.items())
closed=read(completed)
if not closed['passed']:
 write(out/'completion.json',dict(passed=False,comparison_available=False,actual_native_gate_passed=False,
  reason='Actual native candidate gate failed; no legal endpoint/model outcome inferred',actual_completion=str(completed),
  native_calls_new=0,source_sha256=dict(hashes,**{str(completed):sha(completed)})))
 write(out/'status.json',dict(status='terminal',passed=False));sys.exit(1)
assert all(sha(p)==h for p,h in proof['source_sha256'].items())
assert all(sha(prediction/n)==h for n,h in proof['artifact_sha256'].items())
assert all(closed['checks'].values()) and read(case/'input_seal.json')['passed']
run=run_dir(case);manifest=read(run/'manifest.json')
proposal=read(D/'R1_escape_owner_BFS_candidate_01/completion.json')
assert sha(run/'routed.route')==proposal['candidate_sha256']
assert sha(manifest['command'][0])==read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']
expected={(r['net'],r['pin']):r for r in read(prediction/'connection_predictions.json')}
nets={net for net,pin in expected};actual_rows={}
for line in (run/'native_sta_frontier.jsonl').open():
 if not line.startswith('{"type":"pin","net":'):continue
 net=int(line.split(',',3)[1].split(':')[1])
 if net not in nets:continue
 row=json.loads(line)
 if not row['driver']:actual_rows[net,row['pin']]=row
assert actual_rows.keys()==expected.keys()
checks=[dict(net=key[0],pin=key[1],predicted_s=predicted['after_s'],actual_native_s=actual_rows[key]['native_net_delay_s'],
 exact_native_connection_match=predicted['after_s']==actual_rows[key]['native_net_delay_s']) for key,predicted in expected.items()]
before=read(Path(proof['state'])/'endpoint_vector.json');after=read(case/'endpoint_vector.json')
endpoints=compare(before,after);model=read(prediction/'slack_screen.json')
actual_safe=endpoints['compatible'] and after['cpd_s']<=before['cpd_s'] and endpoints['hold_violation_regressions']==0
connection_exact=all(c['exact_native_connection_match'] for c in checks)
passed=connection_exact and (not model['model_screen_passed'] or actual_safe)
files += [completed,case/'input_seal.json',case/'endpoint_vector.json',run/'manifest.json',run/'routed.route',run/'native_sta_frontier.jsonl']
write(out/'connection_comparison.json',checks)
write(out/'completion.json',dict(passed=passed,comparison_available=True,native_calls_new=0,
 exact_native_connection_predictions=connection_exact,connections=len(checks),model_screen_passed=model['model_screen_passed'],
 actual_native_gate_passed=True,actual_CPD_s=after['cpd_s'],original_CPD_s=before['cpd_s'],
 actual_no_CPD_degradation_or_increased_hold_violation=actual_safe,endpoint_comparison=endpoints,
 actual_native_candidate=str(case),used_for_original_acceptance=False,committed_to_original_actor=False,
 source_sha256={str(p):sha(p) for p in files},artifact_sha256={'connection_comparison.json':sha(out/'connection_comparison.json')},
 qualification='Prospectively fixed five connection-delay predictions tested against one actual new native LOAD; other target branches remain controls. Actual FULL/freshSTA, independent physical audit and sealed inputs are required before comparison. Exact connection-delay agreement is not complete endpoint-vector equality; setup components may trade. Model screen never controls the frozen acceptance. Failure remains a counterexample or unavailable gate outcome, without any native rerun or source relabeling. One known circuit/proposal, not independent confirmation or runtime evidence.'))
write(out/'status.json',dict(status='terminal',passed=passed))
print(dict(passed=passed,exact_connections=connection_exact,actual_safe=actual_safe),flush=True)
