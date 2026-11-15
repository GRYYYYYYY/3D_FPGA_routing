"""Preregister connection predictions and model slack screen before native LOAD."""
import json,re,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_zero_rc_tree_delay_v1 import sink_delays
from bounded_route_perturbation_screen_v1 import screen
from run_native_scope_policy_v4 import run_dir

started=time.monotonic();out=D/'BNN_wire_composition_timing_prediction_01';out.mkdir(exist_ok=False)
intervention=D/'BNN_wire_timing_native_validation_01'
assert not (intervention/'candidate_evaluation/completion.json').exists()
assert not (intervention/'candidate_evaluation').exists(),'Prediction must precede actual LOAD start'
construction=D/'BNN_wire_timing_composition_01';proposal=read(construction/'completion.json')
validation=D/'terminal_wire_selector_merge_validation_01/completion.json';reference=read(validation)
assert reference['passed'] and all(sha(p)==h for p,h in reference['source_sha256'].items())
assert all(sha(p)==h for p,h in proposal['source_sha256'].items())
assert all(sha(construction/n)==h for n,h in proposal['artifact_sha256'].items())
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
  old=next(p for p in read(construction/'physical_sink_predictions.json') if p['net']==net and p['pin']==pin)
  assert old['before_s']==row['native_net_delay_s'] and old['after_s']==delay,'Current native float32 baseline or predicted arithmetic mismatch'
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
 run/'native_sta_frontier.jsonl',constraints,D/'BNN_terminal_wire_alternative_01/completion.json']
write(out/'completion.json',dict(passed=True,prediction_registered_before_native_LOAD=True,native_candidate_execution_existed=False,
 native_calls_new=0,state=str(state),original_CPD_s=vector['cpd_s'],connections=len(predictions),
 model_screen_passed=model['model_screen_passed'],native_FULL_STA_completed=False,
 complete_readonly_prediction_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in files},
 artifact_sha256={n:sha(out/n) for n in ['connection_predictions.json','slack_screen.json','selected_native_pin_rows.json']},
 qualification='Prospective predictions on the fixed terminal-wire/timing composition before actual native LOAD. All34 current affected sink delays match actual source native binary32 values exactly; four predict changes. The composed route and its full endpoint STA are unobserved. Conservative current-slack bounds include atom multiplicity. This model is not used by the eventual queue acceptance or candidate selection and does not relax any native gate. Legal archive/manuscript unchanged; not an independent circuit or new native result.'))
print(dict(passed=True,connections=len(predictions),model_screen_passed=model['model_screen_passed'],
 positive_edge_bound_ns=model['total_positive_timing_edge_perturbation_bound_s']*1e9,
 negative_edge_bound_ns=model['total_negative_timing_edge_perturbation_bound_s']*1e9,
 setup_checks=model['setup_checks'],hold_checks=model['hold_checks']),flush=True)
