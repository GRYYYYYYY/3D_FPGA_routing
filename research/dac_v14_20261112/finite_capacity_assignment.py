"""Whole-path finite-pool feasibility with fixed-owner reservations and MRV.

A negative result concerns the supplied paths only; alternative RR paths may
exist. A returned assignment is an explicit selected-tree capacity witness.
"""
import collections,time

def solve(pools,fixed,capacities,max_states=100000,timeout_seconds=60):
    start=time.monotonic();count=collections.Counter(node for nodes in fixed.values() for node in nodes);states=0;cuts=[];limited=False
    if any(c>capacities[n] for n,c in count.items()):return dict(status='fixed_capacity_infeasible',states=0)
    additions={a:[p['nodes']-fixed[a] for p in paths] for a,paths in pools.items()}
    def search(remaining,chosen):
        nonlocal states,limited
        if states>=max_states or time.monotonic()-start>=timeout_seconds:limited=True;return None
        states+=1
        if not remaining:return chosen
        available={a:[i for i,extra in enumerate(additions[a]) if all(count[n]<capacities[n] for n in extra)] for a in remaining}
        if any(not ids for ids in available.values()):return None
        mandatory=collections.Counter()
        for a,ids in available.items():mandatory.update(set.intersection(*(additions[a][i] for i in ids)))
        conflict=next((n for n in sorted(mandatory) if count[n]+mandatory[n]>capacities[n]),None)
        if conflict is not None:
            if len(cuts)<100:cuts.append(dict(resource=conflict,reserved=count[conflict],mandatory_agents=mandatory[conflict],capacity=capacities[conflict]))
            return None
        agent=min(remaining,key=lambda a:(len(available[a]),a))
        for i in available[agent]:
            extra=additions[agent][i]
            for n in extra:count[n]+=1
            result=search(remaining-{agent},dict(chosen,**{str(agent):i}))
            for n in extra:count[n]-=1
            if result is not None:return result
            if limited:return None
        return None
    chosen=search(set(pools),{})
    return dict(status='compatible' if chosen is not None else 'limit' if limited else 'finite_pool_infeasible',states=states,assignment=None if chosen is None else {int(n):i for n,i in chosen.items()},mandatory_cuts=cuts,seconds=time.monotonic()-start)
