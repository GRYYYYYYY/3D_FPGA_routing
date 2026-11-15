"""Rank-preserving whole-net grouping under a native connection-work budget."""

def select_cuts(candidates,size,start=0,*,connection_budget):
    assert type(size) is int and size>0 and type(start) is int and start>=0
    assert type(connection_budget) is int and connection_budget>0
    valid=[]
    for cut in candidates[start:]:
        pins=set(cut['pins']);queries=[q['pin'] for q in cut['ordered_queries']]
        assert pins and len(pins)==len(cut['pins'])
        assert len(queries)==len(set(queries)) and set(queries)==pins
        assert all(q['net']==cut['net'] for q in cut['ordered_queries'])
        assert cut['retained_crossing_sources'] and cut['removed_crossing_resources']>0
        valid.append(cut)
    selected=[];used=0;seen=set()
    for cut in valid:
        if cut['net'] in seen:continue
        cost=len(cut['ordered_queries'])
        if used+cost>connection_budget:continue
        selected.append(cut);used+=cost;seen.add(cut['net'])
        if len(selected)==size:break
    # An oversized single network is an atomic routing operation. Keep a
    # deterministic fallback when no complete cut fits rather than pruning a
    # subset of its crossing sinks or declaring an empty menu.
    if not selected and valid:selected=[valid[0]]
    return selected
