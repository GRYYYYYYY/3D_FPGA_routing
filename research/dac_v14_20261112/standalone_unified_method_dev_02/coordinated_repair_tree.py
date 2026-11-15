"""Tree operations for isolated coordinated route transactions."""
import collections


def from_trace(trace, switches):
    root=trace[0].inode;edges={};sinks={}
    for a,b in zip(trace,trace[1:]):
        if a.switch==-1:continue
        value=(a.inode,a.switch,switches[a.switch])
        assert b.inode not in edges or edges[b.inode]==value
        edges[b.inode]=value
    for node in trace:
        if node.kind=='SINK':
            assert node.pin is not None
            assert node.pin not in sinks or sinks[node.pin]==node.inode
            sinks[node.pin]=node.inode
    tree=dict(root=root,edges=edges,sinks=sinks)
    assert nodes(tree)=={n.inode for n in trace}
    prefixes(tree)
    return tree


def nodes(tree):return {tree['root']}|set(tree['edges'])


def prefixes(tree):
    children=collections.defaultdict(list)
    for v,(u,sw,w) in tree['edges'].items():children[u].append((v,w))
    values={tree['root']:0.};stack=[tree['root']]
    while stack:
        u=stack.pop()
        for v,w in children[u]:
            assert v not in values and w>=0
            values[v]=values[u]+w;stack.append(v)
    assert set(values)==nodes(tree)
    return values


def prune_sinks(tree, pins):
    """Keep the union of paths to all other terminals, plus the real source."""
    assert set(pins)<=set(tree['sinks'])
    keep={tree['root']};remaining={p:s for p,s in tree['sinks'].items() if p not in pins}
    for sink in remaining.values():
        node=sink;visited=set()
        while node!=tree['root']:
            assert node not in visited;visited.add(node);keep.add(node)
            node=tree['edges'][node][0]
        keep.add(node)
    pruned=dict(root=tree['root'],edges={v:e for v,e in tree['edges'].items() if v in keep},sinks=remaining)
    assert nodes(pruned)==keep
    prefixes(pruned)
    return pruned


def attach(tree, pin, sink, forward, switches, weights):
    """Attach a simple suffix with exactly one intersection with the kept tree."""
    assert pin not in tree['sinks'] and forward[-1]==sink
    assert len(switches)==len(weights)==len(forward)-1
    assert len(set(forward))==len(forward)
    assert set(forward)&nodes(tree)=={forward[0]}
    edges=dict(tree['edges'])
    for u,v,sw,w in zip(forward,forward[1:],switches,weights):edges[v]=(u,sw,w)
    result=dict(root=tree['root'],edges=edges,sinks={**tree['sinks'],pin:sink})
    prefixes(result)
    return result


def downstream_pins(tree, resource):
    result=[]
    for pin,sink in tree['sinks'].items():
        node=sink;visited=set()
        while True:
            assert node not in visited;visited.add(node)
            if node==resource:result.append(pin);break
            if node==tree['root']:break
            node=tree['edges'][node][0]
    return sorted(result)


def serialize(tree, metadata):
    children=collections.defaultdict(list)
    for v,(u,sw,w) in tree['edges'].items():
        assert sw is not None;children[u].append((v,sw))
    sink_pins={s:p for p,s in tree['sinks'].items()};assert len(sink_pins)==len(tree['sinks'])
    lines=[];seen=set()
    def emit(node,sw):
        m=metadata[node];xyz=lambda p:'('+','.join(map(str,p))+')'
        label='Class:' if m['kind'] in ['SOURCE','SINK'] else 'Pin:' if m['kind'] in ['IPIN','OPIN'] else 'Track:'
        line=f"Node:\t{node}\t{m['kind']} {xyz(m['low'])}"
        if m['low']!=m['high']:line+=' to '+xyz(m['high'])
        line+=f"  {label} {m['ptc']}  Switch: {sw}"
        if m['kind']=='SINK':line+=f' Net_pin_index: {sink_pins[node]}'
        lines.append(line+'\n')
    # Explicit stack avoids recursion limits on long legal route trees.
    stack=[('visit',tree['root'],None)]
    while stack:
        action,node,sw=stack.pop()
        if action=='emit':emit(node,sw);continue
        assert node not in seen;seen.add(node)
        if not children[node]:emit(node,-1)
        for child,switch in reversed(sorted(children[node])):
            stack.append(('visit',child,None));stack.append(('emit',node,switch))
    assert seen==nodes(tree)
    return ''.join(lines)
