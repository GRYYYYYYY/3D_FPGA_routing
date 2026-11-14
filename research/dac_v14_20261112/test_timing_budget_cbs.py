"""Exhaustive independent path-product check of budget and offset-aware conflict splitting."""
import collections,itertools,random
from timing_budget_cbs import solve

rng=random.Random(2913)
for trial in range(200):
    agents=range(rng.randrange(2,4));resources=range(6);caps={r:rng.randrange(1,3) for r in resources};offsets={a:-rng.randrange(3,13) for a in agents};fixed={a:{6+a} for a in agents}
    caps.update({6+a:1 for a in agents});pools={}
    for a in agents:pools[a]=sorted([dict(nodes=fixed[a]|set(rng.sample(list(resources),rng.randrange(1,4))),cost=rng.randrange(1,13),tag=k) for k in range(4)],key=lambda p:(p['cost'],p['tag']))
    feasible=[]
    for paths in itertools.product(*[pools[a] for a in agents]):
        used=collections.Counter(node for p in paths for node in p['nodes'])
        if all(p['cost']+offsets[a]<0 for a,p in zip(agents,paths)) and all(c<=caps[n] for n,c in used.items()):feasible.append((max(p['cost']+offsets[a] for a,p in zip(agents,paths)),sum(p['cost'] for p in paths)))
    def query(a,forbidden):return next((p for p in pools[a] if not p['nodes']&forbidden),None)
    r=solve({a:pools[a][0] for a in agents},fixed,caps,offsets,query,max_states=10000)
    assert (r['status']=='compatible')==bool(feasible),(trial,r,feasible)
    if feasible:assert r['objective']==min(feasible)
print(dict(passed=True,independent_exhaustive_path_products=200))
