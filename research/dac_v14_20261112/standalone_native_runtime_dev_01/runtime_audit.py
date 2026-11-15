"""Unchanged physical audit functions with caller-supplied batch and graph."""
from collections import Counter
from pathlib import Path
import json
import check_route as cr
from xml_records import records
from runtime_common import sha256,utc,write_json
BASE=None
def read(path):return json.loads(Path(path).read_text())
def physical_route_metrics(route_path,evidence):
    sb,cb=Counter(),Counter();wirelength=0;crossing_edges=Counter()
    for net in cr.read_trace(route_path).values():
        trace=net['trace'];used={n.inode for n in trace};sb_net=set();cb_net=set()
        for n in used:
            meta=evidence['nodes'][n]
            if meta['kind'] in ('CHANX','CHANY') and meta['direction']!='NONE':
                wirelength += 1+abs(meta['high'][0]-meta['low'][0])+abs(meta['high'][1]-meta['low'][1])
        for a,b in zip(trace,trace[1:]):
            if a.switch==-1 or a.low[2]==b.low[2]:continue
            crossing_edges[a.kind+'->'+b.kind]+=1
            if a.kind=='OPIN':cb_net.add(a.inode)
            else:
                assert a.kind=='CHANX' and evidence['nodes'][a.inode]['direction']=='NONE'
                sb_net.add(a.inode)
        sb.update(sb_net);cb.update(cb_net)
    return dict(planar_wirelength_excluding_sb_half_nodes=wirelength,
        sb_pairs_used=len(sb),sb_pair_net_occupancy=sum(sb.values()),
        cb_crossing_output_sources_used=len(cb),cb_crossing_output_source_net_occupancy=sum(cb.values()),
        actual_crossing_edge_traversals=dict(crossing_edges),
        qualification='CB edges share source OPIN and destination channel capacity; no independent per-edge via count')

def audit_batch(ctx, receipts, output):
    cr.graph_records=records
    if Path(output).exists(): raise FileExistsError(output)
    legal=[];failed=[]
    for result in receipts:
        m=result.get('metrics',{})
        if result['status']=='completed' and m.get('native_full_check_passed') and m.get('routing_success_reported'):
            legal.append(BASE/'runs'/result['name'])
        else:failed.append(dict(name=result['name'],status=result['status'],metrics=m))
    graph=ctx['fixture']['original_graph'];rows=[]
    if legal:
        evidence=cr.batch_graph_evidence(graph,[d/'routed.route' for d in legal])
        for d in legal:
            result=cr.audit(graph,d/'routed.route',graph_evidence=evidence)
            pair=read(d/'pair_check.json');assert pair['passed']
            physical=physical_route_metrics(d/'routed.route',evidence) if result['passed'] else None
            write_json(d/'independent_audit.json',dict(utc=utc(),audit=result,physical_metrics=physical))
            assert result['passed'],(d,result['errors'])
            rows.append(dict(name=d.name,passed=True,metrics=read(d/'manifest.json')['metrics'],physical_metrics=physical))
    summary=dict(utc=utc(),passed=True,registered_route_count=len(receipts),legal_count=len(rows),
        failed_count=len(failed),legal=rows,failed=failed,graph_sha256=sha256(graph))
    write_json(output,summary)
    return summary
