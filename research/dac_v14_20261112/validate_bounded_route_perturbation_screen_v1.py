"""Synthetic compound-path/atom/unknown guards; no circuit QoR evidence."""
from pathlib import Path
from retained_prefix_workflow import D,write,sha
from bounded_route_perturbation_screen_v1 import screen

out=D/'bounded_route_perturbation_screen_validation_01';out.mkdir(exist_ok=False)
v=dict(cpd_s=1e-8,metrics=dict(least_slack_s=-1e-8),setup={'[1,1,"synthetic",0,0]':-1e-8},hold={'[1,1,"synthetic",0,0]':1e-9})
def rows(count,setup_gap=80e-12,hold_slack=80e-12,multiplicity=1):
 result={(1,0):dict(atoms=[dict(tnode_external=0)])}
 for pin in range(1,count+1):
  slack=-1e-8+setup_gap
  result[1,pin]=dict(driver=0,ignored=0,**{'global':0},route_tree_present=1,setup_slack_s=slack,
   atoms=[dict(tnode_external=pin*10+i,setup_tags=[dict(launch=0,capture=0,slack_s=slack)],
               hold_tags=[dict(launch=0,capture=0,slack_s=hold_slack)]) for i in range(multiplicity)])
 return result
cases={}
x=screen(v,rows(2),[dict(net=1,pin=p,before_s=1e-9,after_s=1.06e-9) for p in [1,2]],fixed_zero_rc=True,single_zero_clock_constraints=True)
assert x['supported'] and not x['model_no_worst_setup_degradation'];cases['positive_changes_share_path_budget']=x
x=screen(v,rows(2),[dict(net=1,pin=p,before_s=1e-9,after_s=.94e-9) for p in [1,2]],fixed_zero_rc=True,single_zero_clock_constraints=True)
assert x['supported'] and not x['model_no_new_or_increased_hold_violation'];cases['negative_changes_share_hold_budget']=x
x=screen(v,rows(1,multiplicity=2),[dict(net=1,pin=1,before_s=1e-9,after_s=1.06e-9)],fixed_zero_rc=True,single_zero_clock_constraints=True)
assert not x['model_screen_passed'] and x['changed_connections'][0]['atom_edge_multiplicity_upper_bound']==2;cases['multiple_atom_receiver_bound']=x
x=screen(v,rows(1,setup_gap=1e-9,hold_slack=1e-9),[dict(net=1,pin=1,before_s=1e-9,after_s=1.06e-9)],fixed_zero_rc=True,single_zero_clock_constraints=True)
assert x['model_screen_passed'];cases['available_combined_margin']=x
x=screen(v,rows(1),[dict(net=1,pin=1,before_s=1e-9,after_s=1.06e-9)],fixed_zero_rc=False,single_zero_clock_constraints=True)
assert not x['supported'] and not x['model_screen_passed'];cases['unsupported_RC_abstains']=x
unknown=rows(1);unknown[1,1]['atoms'][0]['hold_tags']=[]
x=screen(v,unknown,[dict(net=1,pin=1,before_s=1e-9,after_s=.94e-9)],fixed_zero_rc=True,single_zero_clock_constraints=True)
assert not x['supported'] and not x['model_screen_passed'];cases['unknown_hold_tags_abstain']=x
write(out/'cases.json',cases)
write(out/'completion.json',dict(passed=True,synthetic_cases=len(cases),native_calls_new=0,
 source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'bounded_route_perturbation_screen_v1.py']},
 artifact_sha256={'cases.json':sha(out/'cases.json')},
 qualification='Synthetic compound-path and unknown-coverage controls for a conservative model. These are not benchmarks, native timing observations, circuit samples or evidence that a new proposal passes actual FULL/STA. Frozen acceptance does not call this model.'))
print(dict(passed=True,synthetic_cases=len(cases)),flush=True)
