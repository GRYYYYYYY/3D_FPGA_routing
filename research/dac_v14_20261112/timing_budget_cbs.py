"""Conflict splitting with exact per-agent physical costs and slack-offset budgets."""
import heapq,itertools,time

def solve(initial,fixed,capacities,offsets,query,max_states=256,timeout_seconds=900):
    order=sorted(initial);started=time.monotonic();serial=itertools.count();events=[]
    def admitted(agent,path):return path is not None and path['cost']+offsets[agent]<0.
    def priority(paths):return max(paths[n]['cost']+offsets[n] for n in order),sum(paths[n]['cost'] for n in order)
    if not all(admitted(n,initial[n]) for n in order):return dict(status='infeasible_budget',expanded=0,events=[],reason='Individual exact minimum cannot meet strict proxy budget')
    constraints={n:frozenset() for n in order};queue=[(priority(initial),next(serial),constraints,initial)];seen={tuple((n,()) for n in order)};expanded=0
    while queue:
        if expanded>=max_states or time.monotonic()-started>=timeout_seconds:return dict(status='limit',expanded=expanded,events=events,lower_objective=queue[0][0])
        lower,_,constraints,paths=heapq.heappop(queue);expanded+=1;owners={}
        for n,path in paths.items():
            assert fixed[n]<=path['nodes'] and not path['nodes']&constraints[n]
            for node in path['nodes']:owners.setdefault(node,[]).append(n)
        conflict=next((node for node in sorted(owners) if len(owners[node])>capacities[node]),None)
        if conflict is None:return dict(status='compatible',expanded=expanded,events=events,paths=paths,objective=lower,constraints={n:sorted(v) for n,v in constraints.items()})
        branches=[]
        for n in sorted(owners[conflict]):
            if conflict in fixed[n]:continue
            child=dict(constraints);child[n]=child[n]|{conflict};key=tuple((net,tuple(sorted(child[net]))) for net in order)
            if key in seen:continue
            seen.add(key);replacement=query(n,child[n]);ok=admitted(n,replacement)
            branches.append(dict(net=n,forbidden=sorted(child[n]),budget_feasible=ok,physical_cost=None if replacement is None else replacement['cost'],proxy_score=None if replacement is None else replacement['cost']+offsets[n]))
            if not ok:continue
            updated=dict(paths);updated[n]=replacement;heapq.heappush(queue,(priority(updated),next(serial),child,updated))
        events.append(dict(node=conflict,owners=sorted(owners[conflict]),capacity=capacities[conflict],lower_objective=lower,branches=branches))
    return dict(status='infeasible_budget',expanded=expanded,events=events,reason='All exact conflict branches exhausted under strict proxy budgets; outside-net occupancy was relaxed')
