"""Conflict-based selection of individually shortest fixed-tree extensions.

Only selected net trees compete here. Background nets are restored later, and
native STA remains authoritative. The lexicographic objective is maximum local
source-to-sink delay then total local delay, not final circuit CPD.
"""
import heapq
import itertools
import time


def solve(initial, fixed, capacity, query, max_states=128, timeout_seconds=900):
    """Split a capacity conflict into per-net forbidden-node constraints.

    Each query must return the exact cheapest feasible path for that net under
    its accumulated forbidden set, or None for proved infeasibility. A fixed
    tree node cannot be forbidden on its owning net. A limit is unknown, never
    an infeasibility proof. Paths contain complete retained-tree node sets.
    """
    order = sorted(initial)
    serial = itertools.count()
    def priority(paths):
        costs = [paths[n]['cost'] for n in order]
        return max(costs), sum(costs)
    constraints = {n: frozenset() for n in order}
    queue = [(priority(initial), next(serial), constraints, initial)]
    seen = {tuple((n, tuple()) for n in order)}
    expanded, events = 0, []
    started = time.monotonic()
    while queue:
        if expanded >= max_states or time.monotonic() - started >= timeout_seconds:
            return dict(status='limit', expanded=expanded, events=events, lower_objective=queue[0][0])
        lower, _, constraints, paths = heapq.heappop(queue)
        owners = {}
        for n, path in paths.items():
            assert fixed[n] <= path['nodes'] and not path['nodes'] & constraints[n]
            for node in path['nodes']:
                owners.setdefault(node, []).append(n)
        conflict = next((node for node in sorted(owners) if len(owners[node]) > capacity[node]), None)
        expanded += 1
        if conflict is None:
            return dict(status='compatible', expanded=expanded, events=events, paths=paths,
                        objective=lower, constraints={n: sorted(v) for n, v in constraints.items()})
        branches = []
        for n in sorted(owners[conflict]):
            if conflict in fixed[n]:
                continue
            child = dict(constraints)
            child[n] = child[n] | {conflict}
            key = tuple((net, tuple(sorted(child[net]))) for net in order)
            if key in seen:
                continue
            seen.add(key)
            replacement = query(n, child[n])
            branches.append(dict(net=n, forbidden=sorted(child[n]), feasible=replacement is not None))
            if replacement is None:
                continue
            updated = dict(paths)
            updated[n] = replacement
            heapq.heappush(queue, (priority(updated), next(serial), child, updated))
        events.append(dict(node=conflict, owners=sorted(owners[conflict]), capacity=capacity[conflict],
                           objective=lower, branches=branches))
    return dict(status='infeasible', expanded=expanded, events=events)
