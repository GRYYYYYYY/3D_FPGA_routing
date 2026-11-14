#!/usr/bin/env python3
"""Check route streaming, shared crossing accounting and slack-unknown protection."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resource_opportunity_census import stream_trace,tree_data,release_scope,pin_screen,TraceNode
from check_route import read_trace
fixture=D/'reservation_multisink_regression_01/initial/routed.route';original=read_trace(fixture);streamed={r['net']:dict(name=r['name'],trace=r['trace']) for r in stream_trace(fixture)};assert streamed==original
metadata={}
for n,kind,z in [(0,'SOURCE',0),(1,'OPIN',0),(2,'CHANX',1),(3,'SINK',1),(4,'CHANX',1),(5,'SINK',1)]:metadata[n]=dict(kind=kind,low=(0,0,z),high=(0,0,z),direction='INC_DIR' if kind=='CHANX' else 'NONE')
def node(n,sw,pin=None):
 m=metadata[n];return TraceNode(n,m['kind'],m['low'],m['high'],sw,pin)
t=tree_data([node(0,0),node(1,1),node(2,0),node(3,-1,1),node(1,1),node(4,0),node(5,-1,2)],metadata.__getitem__);one=release_scope(t,[1],metadata.__getitem__);both=release_scope(t,[1,2],metadata.__getitem__)
assert one['released_CB']==[] and one['released_wire']==1 and set(one['released_nodes'])=={2,3};assert both['released_CB']==[1] and both['released_wire']==2;assert t['layer_cut_reference']==1 and not t['excursions']
sta={1:dict(slack_s=-8e-9,criticality=.8,ignored=0,**{'global':0}),2:dict(slack_s='+inf',criticality=0,ignored=0,**{'global':0})};assert pin_screen([1],sta,-10e-9,.2e-9)['eligible'];assert not pin_screen([1,2],sta,-10e-9,.2e-9)['eligible'];sta[2]['slack_s']=-9.9e-9;assert not pin_screen([1,2],sta,-10e-9,.2e-9)['eligible']
# Same-layer terminals can have a real outward-and-return excursion.
metadata[2]['direction']='NONE';metadata[4].update(low=(0,0,0),high=(0,0,0),direction='NONE');metadata[5].update(low=(0,0,0),high=(0,0,0));t=tree_data([node(0,0),node(1,1),node(2,0),node(4,0),node(5,-1,1)],metadata.__getitem__)
# A CHANX crossing source must be the nonplanar half-node.

assert t["layer_cut_reference"]==0 and len(t["excursions"])==1 and t["SB"]=={2} and t["CB"]=={1}
scope=release_scope(t,[1],metadata.__getitem__);assert scope["released_SB"]==[2] and scope["released_CB"]==[1]
write(D/"resource_census_validation_01.json",dict(passed=True,stream_matches_reference=True,shared_CB_retained_until_last_branch=True,unknown_and_nearcritical_pins_protected=True,pure_return_excursion_detected=True,native_calls=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/"resource_opportunity_census.py",fixture,D/"resource_census_validation_failure_01.py"]},initial_test_error="Synthetic return crossing used a planar CHANX instead of a NONE half-node; corrected fixture, no actual graph or algorithm relaxed."))
print(dict(passed=True,checks=5))
