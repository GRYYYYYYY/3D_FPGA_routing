#!/usr/bin/env python3
"""Apply the current resource selector to existing matched strong small-circuit states."""
import resource,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_crossing_share_selector_v2 import select
from full_route_graph_cache import FullRouteGraphCache
from run_native_scope_policy_v4 import run_dir
b=D/'resource_transfer_census_02';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));states={}
for circuit,prefix in [('spmv','native_endpoint_spmv_dev_01'),('eltwise','native_endpoint_vector_dev_01')]:
 for arm in ['A0','R1','Tf']:
  state=D/prefix/arm
  if (state/'completion.json').exists() and read(state/'completion.json')['passed']:states[circuit+'_'+arm]=state
states['eltwise_Tf']=D/'joint_endpoint_diagnostics_01/Tf'
assert len(states)==6 and all(read(p/'completion.json')['passed'] for p in states.values())
files=[Path(__file__).resolve(),D/'current_crossing_share_selector_v2.py',D/'resource_opportunity_census.py',D/'current_crossing_share_selector_validation_02/completion.json']
for state in states.values():files += [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'independent_audit.json',run_dir(state)/'routed.route']
write(b/'registration.json',dict(status='before_current_state_census',states={k:str(v) for k,v in states.items()},source_sha256={str(p):sha(p) for p in files},question='Does the mechanism have resource-release opportunities on strong A0/R1/Tf outside the BNN development circuit, or is the current retained-crossing selector structurally inactive there?',native_calls=0,route_calls=0,qualification='Read-only existing-source census; no algorithm quality or formal timing claim. Empty selector population is local to crossing-sharing, not a reason to terminate wirelength/timing/other-resource research.'))
caches={};results={}
for name,state in states.items():
 rd=run_dir(state);m=read(rd/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);digest=m['shared_inputs'][str(graph)]['sha256']
 if digest not in caches:
  directory=D/'full_route_graph_cache_e695_01';assert read(directory/'completion.json')['graph_sha256']==digest;caches[digest]=FullRouteGraphCache(graph,directory)
 candidates=select(state,caches[digest],b/name);c=read(b/name/'completion.json');results[name]=dict(state=str(state),CPD_ns=read(state/'endpoint_vector.json')['cpd_s']*1e9,resources=c['actual_resources'],multi_crossing_nets=c['multi_crossing_nets'],candidate_scopes=len(candidates),selected=None if not candidates else {k:candidates[0][k] for k in ['net','pins','removed_crossing_resources','minimum_margin_s']});write(b/'progress.json',results);print(name,results[name],flush=True)
assert all(sha(p)==h for p,h in read(b/'registration.json')['source_sha256'].items());write(b/'completion.json',dict(passed=True,rows=results,native_calls=0,route_calls=0,complete_census_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in [b/'registration.json',*[b/n/'completion.json' for n in results]]},qualification='Same current structural/slack rank on six existing sealed states. Potential scopes are not feasible final savings; every replacement still needs native capacity, physical audit and full STA. A0/R1/Tf initial versions remain separate, no per-circuit history-best point selection.'))
