"""Compare fixed-tree/MRV pruning against exhaustive full-node assignments."""
import collections,itertools,random
from finite_capacity_assignment import solve
rng=random.Random(3913)
for trial in range(300):
    agents=range(rng.randrange(2,5));nodes=range(7);caps={n:rng.randrange(1,4) for n in nodes};fixed={a:set(rng.sample(list(nodes),rng.randrange(0,2))) for a in agents}
    pools={a:[dict(nodes=fixed[a]|set(rng.sample(list(nodes),rng.randrange(1,4)))) for _ in range(rng.randrange(1,5))] for a in agents}
    feasible=False
    for combo in itertools.product(*pools.values()):
        c=collections.Counter(n for path in combo for n in path['nodes'])
        if all(v<=caps[n] for n,v in c.items()):feasible=True;break
    r=solve(pools,fixed,caps)
    assert (r['status']=='compatible')==feasible,(trial,r,feasible)
    if feasible:
        c=collections.Counter(n for a,i in r['assignment'].items() for n in pools[a][i]['nodes']);assert all(v<=caps[n] for n,v in c.items())
print(dict(passed=True,independent_exhaustive_products=300))
