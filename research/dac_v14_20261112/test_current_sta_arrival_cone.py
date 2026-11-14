"""Scheduling correctness: tied fanins, disabled arcs and unknown recurrences."""
import copy
from current_sta_arrival_cone import trace, f32
from retained_prefix_workflow import D,write,sha

def fixture():
    g=dict(nodes={0:dict(type='SOURCE',in_edges=[]),1:dict(type='SOURCE',in_edges=[]),
                  2:dict(type='OPIN',in_edges=[0,1]),3:dict(type='SINK',in_edges=[2])},
           edges={0:dict(src_node=0,sink_node=2,disabled=False),1:dict(src_node=1,sink_node=2,disabled=False),
                  2:dict(src_node=2,sink_node=3,disabled=False)},
           delays={0:dict(max_delay=1.),1:dict(max_delay=1.),2:dict(max_delay=1.)},tags={})
    for node,a in [(0,1.),(1,1.),(2,2.),(3,3.)]:g['tags'][('SETUP_DATA_ARRIVAL','node',node,0,-1)]=a
    return g

g=fixture();r=trace(g,[3],0);assert r['edges']==[0,1,2] and r['sources']==[0,1] and not r['unresolved']
g=fixture();g['tags'][('SETUP_DATA_ARRIVAL','node',1,0,-1)]=.5
r=trace(g,[3],0);assert r['edges']==[0,2] and r['sources']==[0]
g=fixture();g['edges'][1]['disabled']=True;r=trace(g,[3],0);assert r['edges']==[0,2]
g=fixture();g['tags'][('SETUP_DATA_ARRIVAL','node',2,0,-1)]=4.
assert trace(g,[3],0)['unresolved']
assert trace(fixture(),[3],1)['unresolved']
# A double-precision sum is not a native float32 max; small deltas may round away.
g=fixture();g['delays'][0]['max_delay']=1.+2**-24
assert f32(1.+g['delays'][0]['max_delay'])==2.
assert trace(g,[3],0)['edges']==[0,1,2]
write(D/'current_sta_arrival_cone_validation_01.json',dict(passed=True,
 checks=['all exact tied winning fanins retained','nonwinning fanin excluded','disabled arc excluded',
         'unreproduced recurrence marked unknown','missing launch domain marked unknown','native float32 addition reproduced'],
 source_sha256={str(D/n):sha(D/n) for n in ['current_sta_arrival_cone.py','test_current_sta_arrival_cone.py']},
 qualification='Synthetic scheduling semantics tests; real SPMV graph and source-distance evidence are separately recorded. No native rerun.'))
print('6 scheduling semantics checks passed')
