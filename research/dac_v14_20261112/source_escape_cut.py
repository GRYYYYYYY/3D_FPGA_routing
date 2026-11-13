"""Capacitated bipartite matching and checkable Hall deficiency witnesses."""
from collections import deque


def match_cuts(neighbors, capacities):
    neighbors = {u: tuple(sorted(set(rs))) for u, rs in neighbors.items()}
    assert all(capacities[r] >= 0 for rs in neighbors.values() for r in rs)
    chosen = {}
    owners = {r: set() for rs in neighbors.values() for r in rs}
    for root in sorted(neighbors):
        queue, seen_u, parent_r = deque([root]), {root}, {}
        free = None
        while queue and free is None:
            u = queue.popleft()
            for r in neighbors[u]:
                if r in parent_r:
                    continue
                parent_r[r] = u
                if len(owners[r]) < capacities[r]:
                    free = r
                    break
                for v in sorted(owners[r]):
                    if v not in seen_u:
                        seen_u.add(v)
                        queue.append(v)
        if free is not None:
            r = free
            while True:
                u = parent_r[r]
                old = chosen.get(u)
                owners[r].add(u)
                chosen[u] = r
                if old is None:
                    break
                owners[old].remove(u)
                r = old
    unmatched = sorted(set(neighbors) - set(chosen))

    def witness(roots):
        reached_u, reached_r = set(roots), set()
        queue = deque(roots)
        while queue:
            u = queue.popleft()
            for r in neighbors[u]:
                if r in reached_r:
                    continue
                reached_r.add(r)
                for v in owners[r]:
                    if v not in reached_u:
                        reached_u.add(v)
                        queue.append(v)
        capacity = sum(capacities[r] for r in reached_r)
        assert len(reached_u) > capacity
        assert reached_r == {r for u in reached_u for r in neighbors[u]}
        return dict(nets=sorted(reached_u), resources=sorted(reached_r),
                    demand=len(reached_u), capacity=capacity, deficit=len(reached_u) - capacity)

    individual = []
    signatures = set()
    for u in unmatched:
        w = witness([u])
        sig = tuple(w['nets'])
        if sig not in signatures:
            individual.append(w)
            signatures.add(sig)
    return dict(matched=len(chosen), total=len(neighbors), assignments=chosen,
                unmatched=unmatched, aggregate_witness=witness(unmatched) if unmatched else None,
                witnesses=individual,
                qualification='Infeasible first-exit assignment is a necessary-cut obstruction. '
                              'Feasible matching does not establish routability.')
