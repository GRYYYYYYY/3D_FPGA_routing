#!/usr/bin/env python3
"""Compare complete physical tree edges, not only scalar connection delay."""
import sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
native=D/'native_current_sta_control_dev_03/R1_witness_audit/analysis.json'
reference=D/'current_sta_policy_R1_01/queries_000/analysis.json'
old={(r['net'],r['pin']):r for r in read(reference)['results']}
def canonical(path):
    traces=read_trace(path)
    return {net:(frozenset((a.inode,b.inode,a.switch) for a,b in zip(info['trace'],info['trace'][1:]) if a.switch!=-1),
                 frozenset((n.inode,n.pin) for n in info['trace'] if n.kind=='SINK')) for net,info in traces.items()}
rows=[];files=[Path(__file__),native,reference]
for r in read(native)['rows']:
    o=old[r['net'],r['pin']];a,b=Path(r['candidate_route']),Path(o['candidate_route'])
    rows.append(dict(net=r['net'],pin=r['pin'],native_pressure=r['pressure_attempts'],
         all_net_edges_switches_and_terminals_identical=canonical(a)==canonical(b),
         physical_seconds_native=r['physical_seconds'],physical_seconds_capacity=o['physical_seconds'],
         native_route=str(a),capacity_route=str(b)))
    files += [a,b]
write(D/'native_capacity_witness_equivalence_01.json',dict(passed=all(r['all_net_edges_switches_and_terminals_identical'] for r in rows),rows=rows,
    scope='These two strongR1 single-connection cases only. Confirms same realized routes after native congestion pressure adjustment, not general oracle equivalence.',
    conclusion='Do not attribute single-connection quality to a distinct hard-capacity mechanism here. Isolate joint selection, displaced-tree scope and scheduling next.',source_sha256={str(p):sha(p) for p in files}))
print(rows)
