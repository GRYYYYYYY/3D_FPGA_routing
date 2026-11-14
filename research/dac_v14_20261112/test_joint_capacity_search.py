"""Check conflict branching against exhaustive tiny two-route path products."""
import itertools
import random
from joint_capacity_search import solve

rng = random.Random(731)
checked = 0
for trial in range(200):
    count = rng.randrange(4, 7)
    graph = {u: [] for u in range(count)}
    for u in graph:
        for v in graph:
            if u != v and rng.random() < .45:
                graph[u].append((v, rng.randrange(1, 5)))
    endpoints = [rng.sample(range(count), 2) for _ in range(2)]
    caps = [rng.choice([1, 1, 2]) for _ in range(count)]
    pools = {}
    for net, (source, sink) in enumerate(endpoints):
        pool = []
        def visit(path, cost):
            if path[-1] == sink:
                pool.append(dict(nodes=set(path), cost=cost, path=tuple(path)))
                return
            for node, weight in graph[path[-1]]:
                if node not in path:
                    visit(path + [node], cost + weight)
        visit([source], 0)
        pools[net] = sorted(pool, key=lambda p: (p['cost'], p['path']))
    if not all(pools.values()):
        continue
    feasible = [(max(a['cost'], b['cost']), a['cost'] + b['cost'])
                for a, b in itertools.product(pools[0], pools[1])
                if all(int(n in a['nodes']) + int(n in b['nodes']) <= caps[n] for n in range(count))]
    def query(net, forbidden):
        return next((p for p in pools[net] if not p['nodes'] & forbidden), None)
    result = solve({n: p[0] for n, p in pools.items()}, {n: {e[0]} for n, e in enumerate(endpoints)},
                   caps, query, max_states=10000)
    assert result['status'] == ('compatible' if feasible else 'infeasible'), (trial, result)
    if feasible:
        assert result['objective'] == min(feasible), (trial, result, min(feasible))
    checked += 1
assert checked >= 100
print(dict(passed=True, exhaustive_two_path_products=checked, randomized_graphs=200))
