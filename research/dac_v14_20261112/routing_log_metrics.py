"""Read the last completed VPR routing iteration, including failed routes."""
import re
NUMBER=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
ROW=re.compile(r'^\s*(\d+)\s+'+NUMBER+r'\s+'+NUMBER+r'\s+\d+\s+'+NUMBER+r'\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*'+NUMBER+r'%\)\s+')
def last_iteration(lines):
    found=None;in_table=False
    for line in lines:
        if line.startswith('Iter ') and 'Overused RR Nodes' in line:in_table=True
        if not in_table:continue
        match=ROW.match(line)
        if match:found=dict(iteration=int(match[1]),rerouted_nets=int(match[2]),rerouted_connections=int(match[3]),overused_rr_nodes=int(match[4]))
    return found
