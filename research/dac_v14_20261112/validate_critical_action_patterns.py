#!/usr/bin/env python3
"""Check compressed grouping against every existing exhaustive subset and large DAGs."""
import collections,itertools,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from critical_action_patterns import patterns,evaluate
start=time.monotonic();ref=read(D/'critical_group_cover_reference_01/completion.json');assert ref['passed'];obs=read(D/'timing_cone_bnn_dev_02/completion.json');results={};files=[Path(__file__).resolve(),D/'critical_action_patterns.py',D/'critical_group_cover_reference_01/completion.json']
for arm,r in ref['results'].items():
 p=Path(obs['roles'][arm]['cone']);cone=read(p);files.append(p);compact=patterns(cone,r['actions'])
 assert compact['edge_paths']==r['winning_paths']
 for old in r['profiles']:
  chosen=[i for i,a in enumerate(r['actions']) if list(a['target']) in old['targets']]
  actual=evaluate(compact,r['actions'],chosen)
  for k in ['repair_connections','min_current_winning_path_gain_ns','all_current_paths_covered']:assert actual[k]==old[k],(arm,chosen,k,actual[k],old[k])
  distribution=collections.Counter(old['winning_path_gains_ns']);assert {x['gain_ns']:x['edge_paths'] for x in actual['gain_distribution']}==dict(distribution)
 results[arm]=dict(edge_paths=compact['edge_paths'],patterns=compact['distinct_patterns'],subsets_checked=len(r['profiles']))
# Forty diamonds have 2**40 edge paths. The same physical action maps to two
# serial timing nodes: counting it once is essential to avoid inflated benefit.
nodes=[0];fanins=[];edge=0;previous=0
for i in range(40):
 a,z,merge=3*i+1,3*i+2,3*i+3;nodes.extend([a,z,merge])
 for n,parents in [(a,[previous]),(z,[previous]),(merge,[a,z])]:
  choices=[]
  for parent in parents:choices.append(dict(source=parent,edge=edge));edge+=1
  fanins.append(dict(node=n,choices=choices,winning_edges=[p['edge'] for p in choices]))
 previous=merge
cone=dict(passed=True,cones={'0':dict(nodes=nodes,sources=[0],fanins=fanins,unresolved=[])},selected_endpoints=[dict(identity=[120,0,'synthetic_diamonds',0,0])])
actions=[dict(target=[1,1],atom_nodes=[3,6],donors=[],optimistic_gain_ns=.125),dict(target=[2,1],atom_nodes=[1],donors=[],optimistic_gain_ns=.25)]
p=patterns(cone,actions);assert p['edge_paths']==2**40 and p['distinct_patterns']==2
assert evaluate(p,actions,[0])['min_current_winning_path_gain_ns']==.125
assert not evaluate(p,actions,[1])['all_current_paths_covered']
assert evaluate(p,actions,[0,1])['min_current_winning_path_gain_ns']==.125
out=D/'critical_action_patterns_validation_01.json';assert not out.exists()
write(out,dict(passed=True,actual=results,synthetic=dict(nodes=len(nodes),edge_paths=p['edge_paths'],distinct_patterns=p['distinct_patterns'],duplicate_action_counted_once=True,partial_cover_rejected=True),source_sha256={str(p):sha(p) for p in files},complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Exact current-winning-DAG pattern/coverage checks. Proxy gain ignores post-repair competition and near-critical migration. Pattern counts can still grow exponentially in candidate actions, bounded by process resources; no global research stop or FPGA optimum claim. Existing registered cohorts unchanged.'))
print(results,'synthetic paths',p['edge_paths'],'patterns',p['distinct_patterns'],flush=True)
