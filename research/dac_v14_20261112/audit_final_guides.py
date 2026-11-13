#!/usr/bin/env python3
"""Verify final guide adoption independently from emitted route-tree traces."""
import csv,json,sys,re
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace,sha256

def audit(directory):
    d=Path(directory);nets=read_trace(d/'routed.route');rows=list(csv.DictReader((d/'h3d_final_guides.csv').open()))
    errors=[];seen=set();adopted=0
    for row in rows:
        net,pin=int(row['net']),int(row['pin']);key=net,pin
        if key in seen:errors.append(f'duplicate {key}')
        seen.add(key);trace=nets[net]['trace'];parents={};nodes={n.inode:n for n in trace}
        for a,b in zip(trace,trace[1:]):
            if a.switch!=-1:
                if b.inode in parents and parents[b.inode]!=a.inode:errors.append(f'multiple parents {key}')
                parents[b.inode]=a.inode
        targets=[n.inode for n in trace if n.kind=='SINK' and n.pin==pin]
        reached=bool(targets)
        crossings=set()
        if reached:
            child=targets[0];visited=set()
            if child!=int(row['sink']):errors.append(f'sink mismatch {key}')
            while child in parents:
                if child in visited:errors.append(f'cycle {key}');break
                visited.add(child);parent=parents[child]
                if nodes[parent].low[2]!=nodes[child].low[2]:crossings.add(parent)
                child=parent
            if child!=int(row['source']):errors.append(f'source mismatch {key}')
        preferred={int(x) for x in row['preferred'].split(';') if x}
        reported={int(x) for x in row['actual_crossings'].split(';') if x}
        match=bool(crossings & preferred);adopted+=match
        if crossings!=reported:errors.append(f'crossing mismatch {key}')
        if reached!=bool(int(row['routed'])) or match!=bool(int(row['adopted'])):errors.append(f'adoption mismatch {key}')
    logs=(d/'stdout.log').read_text();matches=re.findall(r'H3D_FINAL success=(\d+) guided=(\d+) routed=(\d+) adopted=(\d+)',logs)
    if len(matches)!=1:errors.append('missing/nonunique final summary')
    else:
        success,guided,routed,count=map(int,matches[0])
        if guided!=len(rows) or count!=adopted or routed!=sum(int(r['routed']) for r in rows):errors.append('summary mismatch')
    result=dict(passed=not errors,rows=len(rows),adopted=adopted,errors=errors,route_sha256=sha256(d/'routed.route'),trace_sha256=sha256(d/'h3d_final_guides.csv'),scope='Per-pin exact source/sink and original edge-encoding crossing identities on final emitted route. Graph legality remains checked separately; planned criticality is not final STA criticality.')
    (d/'final_guide_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if errors:raise AssertionError(result)
    return result
if __name__=='__main__':print(json.dumps(audit(sys.argv[1]),indent=2))
