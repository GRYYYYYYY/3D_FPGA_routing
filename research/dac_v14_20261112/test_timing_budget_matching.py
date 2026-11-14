"""Check bottleneck results against independent exhaustive allocations with capacities."""
import collections,itertools,random
from timing_budget_matching import bottleneck

rng=random.Random(1913);checked=0
for trial in range(300):
    na=rng.randrange(2,5);nr=rng.randrange(2,6);caps={r:rng.randrange(0,3) for r in range(nr)}
    matrix={a:{r:rng.randrange(0,10) for r in range(nr) if rng.random()<.75} for a in range(na)};offset={a:rng.randrange(-10,4) for a in matrix}
    feasible=[]
    for pick in itertools.product(*[matrix[a] for a in range(na)]):
        count=collections.Counter(pick)
        if all(v<=caps[r] for r,v in count.items()):feasible.append(max(matrix[a][r]+offset[a] for a,r in enumerate(pick)))
    got=bottleneck(matrix,caps,offset)
    assert (got['status']=='optimal')==bool(feasible),(trial,got,feasible)
    if feasible:assert got['objective']==min(feasible)
    checked+=1
print(dict(passed=True,independent_exhaustive_assignments=checked))
