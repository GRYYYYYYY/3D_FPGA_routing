#!/usr/bin/env python3
"""Compare matching size to exhaustive small capacitated assignments."""
import functools
import random
from source_escape_cut import match_cuts


def brute(adj, caps):
    keys = sorted(adj)
    rs = sorted(caps)
    index = {r: i for i, r in enumerate(rs)}

    @functools.lru_cache(None)
    def go(i, available):
        if i == len(keys):
            return 0
        best = go(i + 1, available)
        for r in adj[keys[i]]:
            j = index[r]
            if available[j]:
                c = list(available)
                c[j] -= 1
                best = max(best, 1 + go(i + 1, tuple(c)))
        return best
    return go(0, tuple(caps[r] for r in rs))


rng = random.Random(20261113)
cases = [({0: [0], 1: [0], 2: [0]}, {0: 2}),
         ({0: [0, 1], 1: [0], 2: [1]}, {0: 1, 1: 2}),
         ({0: [], 1: [0]}, {0: 0})]
for _ in range(500):
    nr, nu = rng.randrange(1, 6), rng.randrange(1, 8)
    caps = {r: rng.randrange(3) for r in range(nr)}
    adj = {u: [r for r in caps if rng.random() < .5] for u in range(nu)}
    cases.append((adj, caps))
for adj, caps in cases:
    result = match_cuts(adj, caps)
    assert result['matched'] == brute(adj, caps)
    for w in result['witnesses']:
        neighbors = {r for u in w['nets'] for r in adj[u]}
        assert neighbors == set(w['resources'])
        assert len(w['nets']) > sum(caps[r] for r in neighbors)
print(f'PASS {len(cases)} capacitated instances against exhaustive assignments')
