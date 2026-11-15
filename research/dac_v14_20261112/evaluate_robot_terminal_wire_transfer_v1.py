"""Apply the unchanged two-mode selector to the newly completed robot pair."""
import os
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from select_terminal_resource_alternative_v2 import select
from seed_census_analysis_pool_v2 import process_identity

out=D/'robot_terminal_wire_transfer_01';out.mkdir(exist_ok=False)
proof=D/'terminal_timing_envelope_policy_01/verification.json';assert read(proof)['passed']
cohort=D/'complete_serial_additional_circuits_01';r=read(cohort/'comparison.json');assert r['passed']
files=[Path(__file__).resolve(),D/'select_terminal_resource_alternative_v2.py',proof,cohort/'comparison.json'];bindings={str(f):sha(f) for f in files}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],modes=['endpoint','fixed_timing'],case_selection='Both actual newly completed robot_rl native/domain menus; failed conv_layer roles have no legal initial state and remain failed in the four-role cohort.',source_sha256=bindings,native_calls=0,qualification='Additional known-menu transfer of the unchanged global modes. Observations already produced by the original vertical-only policy; not a fresh routing experiment or prospective full-algorithm confirmation.'))
results=[]
for role in ['native','domain']:
 for mode in ['endpoint','fixed_timing']:
  actor=cohort/('robot_rl_'+role)/'flow/repair';p=select(actor,out/(role+'_'+mode),mode)
  results.append(dict(role=role,mode=mode,current_resources=p['current_resources'],candidates=p['actual_same_source_candidates'],eligible=p['eligible_candidates'],selected=p['selected']))
  print(dict(role=role,mode=mode,candidates=p['actual_same_source_candidates'],eligible=p['eligible_candidates'],selected=None if p['selected'] is None else p['selected']['resources']),flush=True)
assert all(sha(f)==h for f,h in bindings.items())
write(out/'results.json',results);write(out/'completion.json',dict(passed=True,closed_menus=2,mode_evaluations=4,all_registered_transfer_roles=4,initial_route_failures_without_selector_input=2,native_calls_new=0,new_legal_observations=0,source_sha256=bindings,artifact_sha256={'results.json':sha(out/'results.json')},qualification='Both same frozen modes applied to both successful robot menus; original actors unchanged and failed conv_layer denominator retained. Every alternative is an already executed actual candidate; no whole-time borrowing, new sample or speedup is inferred.'))
