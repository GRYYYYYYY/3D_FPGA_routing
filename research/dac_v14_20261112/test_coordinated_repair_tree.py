"""Independent path preservation checks for multi-sink pruning and reattachment."""
import random
from coordinated_repair_tree import nodes,prefixes,prune_sinks,attach,downstream_pins
rng=random.Random(73429)
for case in range(1000):
    n=rng.randrange(3,90);edges={i:(rng.randrange(i),0,rng.randrange(6)*1e-10) for i in range(1,n)}
    parents={e[0] for e in edges.values()};leaves=sorted(set(range(n))-parents)
    tree=dict(root=0,edges=edges,sinks=dict(enumerate(leaves,1)))
    removed={p for p in tree['sinks'] if rng.randrange(2)}
    kept=prune_sinks(tree,removed);before=prefixes(tree);after=prefixes(kept)
    expected={0}
    for p,sink in tree['sinks'].items():
        path=[];u=sink
        while u:
            path.append(u);u=edges[u][0]
        if p not in removed:
            expected.update(path);assert before[sink]==after[sink]
            assert all(kept['edges'][v]==edges[v] for v in path)
    assert expected==nodes(kept)
    resource=rng.randrange(n)
    wanted=[]
    for p,sink in tree['sinks'].items():
        path={sink};u=sink
        while u:u=edges[u][0];path.add(u)
        if resource in path:wanted.append(p)
    assert downstream_pins(tree,resource)==sorted(wanted)
    new=attach(kept,999,n+1,[0,n,n+1],[1,1],[0.,1e-10])
    assert prefixes(new)[n+1]==1e-10 and all(new['edges'][v]==e for v,e in kept['edges'].items())
    try:attach(kept,999,n+1,[0,n,0,n+1],[1]*3,[0.]*3)
    except AssertionError:pass
    else:raise AssertionError('Repeated-node cycle accepted')
print('PASS1000 randomized multi-sink pruning, unchanged-path, ancestry and attachment cases')
