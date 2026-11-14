#!/usr/bin/env python3
"""Parser tests for exact tags, adjacency, disabled arcs and incomplete exports."""
import tempfile
from pathlib import Path
from native_timing_echo_v2 import read_echo,data_reachable,node_tags

fixture='''timing_graph:
 node: 0
 type: SOURCE
 in_edges:
 out_edges: 0
 node: 1
 type: SOURCE
 in_edges:
 out_edges: 1
 node: 2
 type: SINK
 in_edges: 0 1
 out_edges:
 edge: 0
 type: INTERCONNECT
 src_node: 0
 sink_node: 2
 disabled: false
 edge: 1
 type: INTERCONNECT
 src_node: 1
 sink_node: 2
 disabled: true
timing_constraints:
 type: CLOCK domain: 0 name: "clk"
delay_model:
 edge: 0 min_delay: 8.569782938838699e-10 max_delay: 8.569782938838699e-10
 edge: 1 min_delay: 8.493392933406341e-10 max_delay: 8.493392933406341e-10
analysis_result:
 type: SETUP_DATA_ARRIVAL node: 0 launch_domain: 0 capture_domain: -1 time: 0
 type: SETUP_DATA_ARRIVAL node: 2 launch_domain: 0 capture_domain: -1 time: 8.569782938838699e-10
 type: SETUP_DATA_REQUIRED node: 2 launch_domain: 0 capture_domain: 0 time: 0
 type: SETUP_SLACK node: 2 launch_domain: 0 capture_domain: 0 slack: -8.569782938838699e-10
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'test.echo';p.write_text(fixture);g=read_echo(p)
 assert g['delays'][0]['max_delay']-g['delays'][1]['max_delay']==7.639000543235852e-12
 assert node_tags(g,2,'SETUP_DATA_ARRIVAL')=={(0,-1):8.569782938838699e-10}
 assert data_reachable(g,[0])=={0,2} and data_reachable(g,[1])=={1}
 cases=[fixture.replace('slack: -8.569782938838699e-10','time: -8.569782938838699e-10'),fixture.replace('in_edges: 0 1','in_edges: 1'),fixture.split('analysis_result:')[0],fixture+' type: SETUP_DATA_ARRIVAL node: 2 launch_domain: 0 capture_domain: -1 time: 1\n']
 for bad in cases:
  p.write_text(bad)
  try:read_echo(p)
  except AssertionError:pass
  else:raise AssertionError('Malformed echo accepted')
print('Passed exact-precision, reciprocal adjacency, disabled-reachability and4 malformed-export controls')
