"""Preregister connection predictions and model slack screen before native LOAD."""
import json,re,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_zero_rc_tree_delay_v1 import sink_delays
from bounded_route_perturbation_screen_v1 import screen
from run_native_scope_policy_v4 import run_dir

started=time.monotonic();out=D/'R1_BFS_native_timing_prediction_01';out.mkdir(exist_ok=False)
intervention=D/'partial_escape_owner_intervention_01'
assert not (intervention/'BFS_candidate_evaluation/completion.json').exists()
assert not (intervention/'BFS_candidate_evaluation').exists(),'Prediction must precede actual LOAD start'
construction=D/'R1_escape_owner_BFS_candidate_01';proposal=read(construction/'completion.json')
validation=D/'R1_native_float32_route_delay_validation_01/completion.json';reference=read(validation)
assert reference['passed'] and reference['state']==proposal['state'] and reference['mismatches']==0
assert all(sha(p)==h for p,h in reference['source_sha256'].items())
state=Path(proposal['state']);run=run_dir(state);vector=read(state/'endpoint_vector.json')
wanted=set(proposal['affected_nets']);pins={}
for line in (run/'native_sta_frontier.jsonl').open():
 if not line.startswith('{"type":"pin","net":'):continue
 net=int(line.split(',',3)[1].split(':')[1])
 if net not in wanted:continue
 row=json.loads(line);pins[net,row['pin']]=row
predictions=[]
for net,tree in read(construction/'transaction_trees.json').items():
 net=int(net);predicted=sink_delays(tree,audited_zero_rc=True)
 for pin,delay in predicted.items():
  row=pins[net,pin]
  predictions.append(dict(net=net,pin=pin,sink=int(tree['sinks'][str(pin)]),before_s=row['native_net_delay_s'],after_s=delay,
    delta_s=delay-row['native_net_delay_s']))
constraints=run/'native_sta_frontier.jsonl.constraints.echo';text=constraints.read_text()
clock_domains=re.findall(r'type: CLOCK domain: (\d+) ',text)
setups=re.findall(r'type: SETUP_CONSTRAINT launch_domain: (\d+) capture_domain: (\d+) capture_node: (-?\d+) constraint: ([^\s]+)',text)
holds=re.findall(r'type: HOLD_CONSTRAINT launch_domain: (\d+) capture_domain: (\d+) capture_node: (-?\d+) constraint: ([^\s]+)',text)
supported_constraints=(clock_domains==['0'] and setups==[('0','0','-1','0')] and holds==[('0','0','-1','0')])
assert sha(constraints)==vector['constraints_sha256']
model=screen(vector,pins,predictions,fixed_zero_rc=True,single_zero_clock_constraints=supported_constraints)
write(out/'connection_predictions.json',predictions);write(out/'slack_screen.json',model)
write(out/'selected_native_pin_rows.json',list(pins.values()))
files=[Path(__file__).resolve(),D/'native_zero_rc_tree_delay_v1.py',D/'bounded_route_perturbation_screen_v1.py',validation,
 construction/'completion.json',construction/'transaction_trees.json',state/'completion.json',state/'endpoint_vector.json',
 run/'native_sta_frontier.jsonl',constraints,intervention/'queue/registration.json']
write(out/'completion.json',dict(passed=True,prediction_registered_before_native_LOAD=True,native_candidate_execution_existed=False,
 native_calls_new=0,state=str(state),original_CPD_s=vector['cpd_s'],connections=len(predictions),
 model_screen_passed=model['model_screen_passed'],native_FULL_STA_completed=False,
 complete_readonly_prediction_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in files},
 artifact_sha256={n:sha(out/n) for n in ['connection_predictions.json','slack_screen.json','selected_native_pin_rows.json']},
 qualification='Prospective predictions on the already fixed complete BFS proposal, before its actual native LOAD. Native-compatible float32 connection model was exact over all230693current R1 sinks; this new route and its full endpoint STA are unobserved. Conservative current-slack bounds include atom multiplicity. This model is not used by the frozen queue acceptance or candidate selection and does not relax any native gate. Legal archive/manuscript unchanged; not an independent circuit or new native result.'))
print(dict(passed=True,connections=len(predictions),model_screen_passed=model['model_screen_passed'],
 positive_edge_bound_ns=model['total_positive_timing_edge_perturbation_bound_s']*1e9,
 negative_edge_bound_ns=model['total_negative_timing_edge_perturbation_bound_s']*1e9,
 setup_checks=model['setup_checks'],hold_checks=model['hold_checks']),flush=True)
