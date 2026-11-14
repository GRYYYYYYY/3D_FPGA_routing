#!/usr/bin/env python3
"""Strict parser for the existing Tatum echo format; no timing approximations."""
import collections,hashlib,re
from pathlib import Path

def read_echo(path):
    nodes={};edges={};delays={};tags={};constraints=[];section=None;record=None;duplicate_tags=0
    sections=[]
    def finish():
        nonlocal record
        if record is None:return
        kind,idx,fields=record;target=nodes if kind=='node' else edges
        assert idx not in target,(kind,idx)
        assert set(fields)==({'type','in_edges','out_edges'} if kind=='node' else {'type','src_node','sink_node','disabled'}),(kind,idx,fields)
        target[idx]=fields;record=None
    for raw in Path(path).open():
        line=raw.strip().removesuffix('\\').strip()
        if not line:continue
        if line in ['timing_graph:','timing_constraints:','delay_model:','analysis_result:']:
            finish();section=line[:-1];sections.append(section);continue
        assert section is not None,'Data before section'
        if section=='timing_graph':
            key,value=line.split(':',1);value=value.strip()
            if key in ['node','edge']:
                finish();record=(key,int(value),{});continue
            assert record is not None
            if key in ['in_edges','out_edges']:value=list(map(int,value.split()))
            elif key in ['src_node','sink_node']:value=int(value)
            elif key=='disabled':assert value in ['true','false'];value=value=='true'
            assert key not in record[2];record[2][key]=value
        elif section=='timing_constraints':constraints.append(line)
        elif section=='delay_model':
            fields=dict(re.findall(r'(\w+):\s+(\S+)',line));idx=int(fields.pop('edge'))
            assert idx not in delays;delays[idx]={k:float(v) for k,v in fields.items()}
            assert set(delays[idx]) in [{'min_delay','max_delay'},{'setup_time','hold_time'}]
        else:
            f=dict(re.findall(r'(\w+):\s+(\S+)',line));kind='node' if 'node' in f else 'edge'
            key=(f['type'],kind,int(f[kind]),int(f['launch_domain']),int(f['capture_domain']))
            value=float(f['time'])
            if key in tags:assert tags[key]==value;duplicate_tags+=1
            tags[key]=value
    finish();assert sections==['timing_graph','timing_constraints','delay_model','analysis_result'],sections
    assert nodes and edges and tags and set(edges)==set(delays)
    assert set(nodes)==set(range(len(nodes))) and set(edges)==set(range(len(edges)))
    for idx,e in edges.items():
        assert idx in nodes[e['src_node']]['out_edges'] and idx in nodes[e['sink_node']]['in_edges']
    for idx,n in nodes.items():
        assert len(n['in_edges'])==len(set(n['in_edges'])) and len(n['out_edges'])==len(set(n['out_edges']))
        assert all(edges[e]['sink_node']==idx for e in n['in_edges']) and all(edges[e]['src_node']==idx for e in n['out_edges'])
    assert all((idx in nodes if kind=='node' else idx in edges) for typ,kind,idx,l,c in tags)
    return dict(nodes=nodes,edges=edges,delays=delays,tags=tags,constraints=constraints,constraints_text_sha256=hashlib.sha256('\n'.join(constraints).encode()).hexdigest(),duplicate_equal_tags=duplicate_tags)

def node_tags(graph,node,kind):
    return {(l,c):v for (typ,entity,idx,l,c),v in graph['tags'].items() if typ==kind and entity=='node' and idx==node}

def data_reachable(graph,roots):
    """Follow enabled data arcs without crossing sequential setup/hold edges."""
    seen=set(roots);todo=list(roots)
    while todo:
        n=todo.pop()
        if graph['nodes'][n]['type']=='SINK':continue
        for edge in graph['nodes'][n]['out_edges']:
            e=graph['edges'][edge]
            if e['disabled'] or 'max_delay' not in graph['delays'][edge]:continue
            if graph['nodes'][e['sink_node']]['type']=='CPIN':continue
            if e['sink_node'] not in seen:seen.add(e['sink_node']);todo.append(e['sink_node'])
    return seen
