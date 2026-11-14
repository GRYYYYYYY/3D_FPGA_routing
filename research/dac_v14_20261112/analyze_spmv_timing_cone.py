#!/usr/bin/env python3
"""Trace actual changed arrival tags to unchanged downstream native endpoints."""
import collections,json,math,struct,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_timing_echo import read_echo,data_reachable

def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def tag_index(g,kind):
    out=collections.defaultdict(dict)
    for (typ,entity,node,l,c),v in g['tags'].items():
        if typ==kind and entity=='node':out[node][l,c]=v
    return out
def main():
    start=time.monotonic();b=D/'timing_cone_spmv_dev_03';assert read(b/'completion.json')['passed']
    before=b/'plateau_on';after=b/'joint_on';br=Path(read(before/'completion.json')['run']);ar=Path(read(after/'completion.json')['run'])
    x=read_echo(br/'timing_graph.full_precision.echo');y=read_echo(ar/'timing_graph.full_precision.echo')
    assert x['nodes']==y['nodes'] and x['edges']==y['edges'] and x['constraints']==y['constraints']
    assert read(before/'endpoint_vector.json')['setup']==read(after/'endpoint_vector.json')['setup']
    assert read(before/'endpoint_vector.json')['hold']==read(after/'endpoint_vector.json')['hold']
    frontier=[json.loads(line) for line in (br/'native_sta_frontier.jsonl').open()]
    target=[r for r in frontier if r.get('type')=='pin' and (r['net'],r['pin'])==(6997,1)];assert len(target)==1
    roots={a['tnode_external'] for a in target[0]['atoms'] if a['tnode_external'] is not None};assert roots
    pinmap=collections.defaultdict(list)
    for r in frontier:
        if r.get('type')!='pin':continue
        for atom in r['atoms']:
            if atom['tnode_external'] is not None:pinmap[atom['tnode_external']].append(dict(net=r['net'],pin=r['pin'],driver=r['driver'],atom_name=atom['name'],native_pin_slack_s=r['setup_slack_s']))
    endpoints={r['node']:r for r in frontier if r.get('type')=='endpoint'}
    xa,ya=tag_index(x,'SETUP_DATA_ARRIVAL'),tag_index(y,'SETUP_DATA_ARRIVAL')
    xr,yr=tag_index(x,'SETUP_DATA_REQUIRED'),tag_index(y,'SETUP_DATA_REQUIRED')
    reachable=data_reachable(x,roots);changed={n for n in reachable if xa[n]!=ya[n]}
    assert roots&changed,'Selected pin has no actual arrival change; revisit mechanism'
    def same_delay(a,b):
        return a.keys()==b.keys() and all(a[k]==b[k] or (math.isnan(a[k]) and math.isnan(b[k])) for k in a)
    delay_changes=[dict(edge=e,edge_info=x['edges'][e],before=x['delays'][e],after=y['delays'][e]) for e in x['edges'] if not same_delay(x['delays'][e],y['delays'][e])]
    boundaries=[]
    for edge,e in x['edges'].items():
        u,v=e['src_node'],e['sink_node']
        if e['disabled'] or u not in changed or v not in reachable or v in changed or 'max_delay' not in x['delays'][edge]:continue
        proposals=[]
        for incoming in x['nodes'][v]['in_edges']:
            ie=x['edges'][incoming];source=ie['src_node']
            if ie['disabled'] or 'max_delay' not in x['delays'][incoming]:continue
            for domain in sorted(set(xa[source])&set(ya[source])):
                if domain not in xa[v] or domain not in ya[v]:continue
                pb=f32(xa[source][domain]+x['delays'][incoming]['max_delay']);pa=f32(ya[source][domain]+y['delays'][incoming]['max_delay'])
                proposals.append(dict(edge=incoming,source_node=source,domain=list(domain),before_arrival_plus_edge_s=pb,after_arrival_plus_edge_s=pa,before_gap_to_native_s=xa[v][domain]-pb,after_gap_to_native_s=ya[v][domain]-pa,before_native_max_attained=pb==xa[v][domain],after_native_max_attained=pa==ya[v][domain],routed_pin_mapping=pinmap.get(source,[])))
        domains={tuple(r['domain']) for r in proposals}
        consistency={str(domain):dict(before=max(r['before_arrival_plus_edge_s'] for r in proposals if tuple(r['domain'])==domain)==xa[v][domain],after=max(r['after_arrival_plus_edge_s'] for r in proposals if tuple(r['domain'])==domain)==ya[v][domain]) for domain in domains}
        boundaries.append(dict(changed_edge=edge,changed_source=u,merge_node=v,merge_type=x['nodes'][v]['type'],native_arrival_before={str(k):z for k,z in xa[v].items()},native_arrival_after={str(k):z for k,z in ya[v].items()},incoming=proposals,max_recurrence_verified=consistency,merge_pin_mapping=pinmap.get(v,[])))
    endpoint_rows=[dict(node=n,name=endpoints.get(n,{}).get('name'),arrival_changed=xa[n]!=ya[n],required_changed=xr[n]!=yr[n],setup_tags=endpoints.get(n,{}).get('setup_tags')) for n in sorted(reachable) if x['nodes'][n]['type']=='SINK']
    files=[Path(__file__).resolve(),D/'native_timing_echo.py',b/'completion.json',br/'timing_graph.full_precision.echo',ar/'timing_graph.full_precision.echo',br/'native_sta_frontier.jsonl',ar/'native_sta_frontier.jsonl',before/'endpoint_vector.json',after/'endpoint_vector.json']
    write(D/'spmv_timing_cone_analysis_01.json',dict(passed=True,topology_and_constraints_identical=True,selected_connection=dict(net=6997,pin=1,roots=sorted(roots)),changed_delay_edges=delay_changes,reachable_nodes=len(reachable),changed_arrival_nodes=sorted(changed),reachable_endpoints=endpoint_rows,masking_boundaries=boundaries,complete_analysis_seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in files},qualification='Actual native graph/tags and float32 max recurrence where explicitly verified. Reachability alone does not establish every arc is timing-critical. Alternative fanin gaps are current-state observations, not global routing bounds. No combined repair or quality improvement claimed.'))
    print(dict(delay_edges=len(delay_changes),reachable=len(reachable),changed_nodes=len(changed),endpoints=len(endpoint_rows),masking_boundaries=len(boundaries)),flush=True)

if __name__=='__main__':main()
